"""NFL play-level and career outcome aggregation and in-game rush path extraction (Phase 3)."""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.combine_features import compute_turn_metrics_for_attempt
from src.data_loading import (
    DL_LINED_UP_POSITIONS,
    OUTPUTS_DIR,
    load_career_successes,
    load_game_tracking,
    load_player_play,
    load_players,
)

PASS_RUSH_END_EVENTS = {
    "pass_forward",
    "qb_sack",
    "qb_strip_sack",
    "qb_scramble",
    "pass_shovel",
    "qb_spike",
    "qb_kneel",
    "run",
    "handoff",
    "tackle",
    "out_of_bounds",
}

NFL_OUTCOME_COLS = [
    "pressure_rate",
    "quick_pressure_rate",
    "avg_get_off",
    "sack_rate",
    "tfl_rate",
    "total_pass_rush_snaps",
    "total_defensive_snaps",
    "snap_share",
    "start_rate",
    "accolades",
]


def load_dl_player_plays(roster_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Phase 3A.1 & 3A.2: Load player_play.csv for the DL cohort and classify pass rush vs run defense."""
    if roster_df is None:
        roster_path = OUTPUTS_DIR / "dl_roster_master.csv"
        roster_df = pd.read_csv(roster_path) if roster_path.exists() else load_players(dl_only=True)

    pp = load_player_play(
        nfl_ids=roster_df["nfl_id"],
        lined_up_positions=DL_LINED_UP_POSITIONS,
    )
    # 3A.2 Primary classification: player_get_off is non-null on pass rush snaps
    pp["is_pass_rush"] = pp["player_get_off"].notna()
    # Alternative classifications for documentation & comparison
    pp["is_pass_rush_alt_blitz"] = pp["blitzing"].fillna(False).astype(bool)
    pp["is_pass_rush_alt_sack_col"] = pp["sack"].notna()
    return pp


def aggregate_play_outcomes(
    pp_df: pd.DataFrame,
    roster_df: pd.DataFrame,
) -> pd.DataFrame:
    """Phase 3A.3 & 3A.5: Compute per-player play-level aggregates and merge career outcomes."""
    all_agg = (
        pp_df.groupby("nfl_id")
        .agg(
            total_defensive_snaps=("play_id", "count"),
            total_pass_rush_snaps=("is_pass_rush", "sum"),
            tfls=("tackle_for_loss", lambda s: float(s.fillna(0.0).sum())),
        )
        .reset_index()
    )

    pr_df = pp_df[pp_df["is_pass_rush"]]
    pr_agg = (
        pr_df.groupby("nfl_id")
        .agg(
            pressures=("time_to_pressure", lambda s: int(s.notna().sum())),
            hurries=("time_to_qb_hurry", lambda s: int(s.notna().sum())),
            quick_pressures=("quick_pressure", lambda s: float(s.fillna(0.0).sum())),
            sacks=("sack", lambda s: float(s.fillna(0.0).sum())),
            sack_plays=("sack", lambda s: int((s.fillna(0.0) > 0).sum())),
            avg_get_off=("player_get_off", "mean"),
            avg_time_to_pressure=("time_to_pressure", "mean"),
        )
        .reset_index()
    )

    base_cols = [
        c
        for c in [
            "nfl_id",
            "display_name",
            "nfl_position",
            "draft_year",
            "draft_round",
            "draft_overall_pick",
        ]
        if c in roster_df.columns
    ]
    df = (
        roster_df[base_cols]
        .merge(all_agg, on="nfl_id", how="left")
        .merge(pr_agg, on="nfl_id", how="left")
    )

    for int_col in ["total_defensive_snaps", "total_pass_rush_snaps", "pressures", "hurries", "sack_plays"]:
        df[int_col] = df[int_col].fillna(0).astype(int)
    for flt_col in ["tfls", "quick_pressures", "sacks"]:
        df[flt_col] = df[flt_col].fillna(0.0).astype(float)

    pr_denom = df["total_pass_rush_snaps"].replace(0, np.nan)
    def_denom = df["total_defensive_snaps"].replace(0, np.nan)

    # 3A.3 Core rate formulas
    df["pressure_rate"] = df["pressures"] / pr_denom
    df["quick_pressure_rate"] = df["quick_pressures"] / pr_denom
    df["sack_rate"] = df["sacks"] / pr_denom
    df["tfl_rate"] = df["tfls"] / def_denom

    # 3A.5 Merge with player_career_successes.csv
    career = load_career_successes(nfl_ids=roster_df["nfl_id"])
    df = df.merge(career, on="nfl_id", how="left")

    games_active_denom = df["career_games_active"].replace(0, np.nan)
    df["snap_share"] = (df["career_defensive_snaps"] / games_active_denom).fillna(0.0)
    df["start_rate"] = (df["career_games_started"] / games_active_denom).fillna(0.0)
    df["accolades"] = (
        df["ap_all_pro_1st_team"].fillna(0)
        + df["ap_all_pro_2nd_team"].fillna(0)
        + df["pro_bowl_original_ballot"].fillna(0)
    ).astype(int)

    return df


def select_top_pass_rush_plays(
    pp_df: pd.DataFrame,
    top_k: int = 5,
    fallback_k: int = 10,
) -> pd.DataFrame:
    """Phase 3B.1: Identify top pass rush plays per DL player (lowest time_to_pressure or sack)."""
    pr = pp_df[pp_df["is_pass_rush"]].copy()
    pr["has_pressure"] = pr["time_to_pressure"].notna().astype(int)
    pr["has_sack"] = (pr["sack"].fillna(0.0) > 0).astype(int)

    pr_sorted = pr.sort_values(
        ["nfl_id", "has_pressure", "has_sack", "time_to_pressure", "player_get_off"],
        ascending=[True, False, False, True, True],
    )
    pr_sorted["play_rank"] = pr_sorted.groupby("nfl_id").cumcount() + 1

    keep_cols = [
        "game_id",
        "play_id",
        "nfl_id",
        "play_rank",
        "lined_up_position",
        "player_get_off",
        "time_to_pressure",
        "sack",
        "quick_pressure",
        "play_description",
    ]
    return pr_sorted[pr_sorted["play_rank"] <= max(top_k, fallback_k)][keep_cols].copy()


def extract_rush_window(play_df: pd.DataFrame, max_rush_frames: int = 30) -> pd.DataFrame:
    """Phase 3B.3: Extract frames between ball_snap and pass_forward/qb_sack (capped at 3.0s pocket rush window)."""
    evs = play_df["event"].fillna("")
    snap_idx = np.where(evs == "ball_snap")[0]
    start_i = int(snap_idx[0]) if len(snap_idx) > 0 else 0

    end_candidates = np.where(evs.iloc[start_i + 1 :].isin(PASS_RUSH_END_EVENTS))[0]
    if len(end_candidates) > 0:
        end_i = min(start_i + 1 + int(end_candidates[0]), start_i + max_rush_frames - 1)
    else:
        end_i = min(len(play_df) - 1, start_i + max_rush_frames - 1)

    win = play_df.iloc[start_i : end_i + 1].copy().reset_index(drop=True)
    win["rush_frame_idx"] = np.arange(len(win))
    return win


def build_game_rush_paths_and_ingame_csr(
    pp_df: pd.DataFrame,
    top_k: int = 5,
    fallback_k: int = 10,
    cache_path: Optional[Path] = None,
    use_cache: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Phase 3B.1–3B.4: Extract top pass rush paths from game_tracking_*.csv and compute in-game CSR."""
    if cache_path is None:
        cache_path = OUTPUTS_DIR / "dl_game_rush_paths.pkl"

    top_plays_all = select_top_pass_rush_plays(pp_df, top_k=top_k, fallback_k=fallback_k)
    top5_plays = top_plays_all[top_plays_all["play_rank"] <= top_k].copy()
    print(
        f"3B.1 Identified {len(top5_plays):,d} top-{top_k} pass rush plays across "
        f"{top5_plays['nfl_id'].nunique()} DL players "
        f"(pressures={(top5_plays['time_to_pressure'].notna()).sum()}, "
        f"sacks={(top5_plays['sack'].fillna(0) > 0).sum()})"
    )

    loaded_from_cache = False
    if use_cache and cache_path.exists():
        cached = pd.read_pickle(cache_path)
        if isinstance(cached, dict) and "all_candidate_frames" in cached:
            gt_all = cached["all_candidate_frames"]
            loaded_from_cache = True
            print(f"3B.2 Loaded {len(gt_all):,d} cached game tracking frames from {cache_path}")

    if not loaded_from_cache:
        keys = top_plays_all[["game_id", "play_id", "nfl_id"]].drop_duplicates()
        gt_raw = load_game_tracking(
            seasons=(2023, 2024, 2025),
            game_ids=keys["game_id"].unique(),
            play_ids=keys["play_id"].unique(),
            nfl_ids=keys["nfl_id"].unique(),
        )
        gt_all = gt_raw.merge(
            top_plays_all,
            on=["game_id", "play_id", "nfl_id"],
            how="inner",
        )
        gt_all["time_dt"] = pd.to_datetime(gt_all["time"], format="ISO8601")
        gt_all = gt_all.sort_values(["game_id", "play_id", "nfl_id", "time_dt"]).reset_index(drop=True)
        print(
            f"3B.2 Loaded {len(gt_all):,d} frames across "
            f"{gt_all[['game_id', 'play_id', 'nfl_id']].drop_duplicates().shape[0]:,d} plays "
            f"from game_tracking_2023..2025.csv"
        )

    # 3B.3 Extract frames between ball_snap and pass_forward/qb_sack (<=3.0s pocket rush window) and compute in-game CSR
    rush_windows_top5: list[pd.DataFrame] = []
    turn_rows: list[dict] = []
    fallback_turn_rows: list[dict] = []

    for (gid, pid, nid, prank), grp in gt_all.groupby(
        ["game_id", "play_id", "nfl_id", "play_rank"], sort=False
    ):
        rw = extract_rush_window(grp, max_rush_frames=30)
        if prank <= top_k:
            rush_windows_top5.append(rw)

        tms = compute_turn_metrics_for_attempt(rw)
        for tm in tms:
            turn_rows.append(
                {
                    "game_id": int(gid),
                    "play_id": int(pid),
                    "nfl_id": int(nid),
                    "play_rank": int(prank),
                    **tm,
                }
            )
        if not tms:
            for tm_fb in compute_turn_metrics_for_attempt(rw, min_total_angle=35.0):
                fallback_turn_rows.append(
                    {
                        "game_id": int(gid),
                        "play_id": int(pid),
                        "nfl_id": int(nid),
                        "play_rank": int(prank),
                        **tm_fb,
                    }
                )

    rush_paths_df = pd.concat(rush_windows_top5, ignore_index=True)
    turns_all_df = pd.DataFrame(turn_rows)
    turns_fb_df = pd.DataFrame(fallback_turn_rows)

    # Primary: median across top-5 plays (>=45° turns); fallback: ranks 6-10 (>=45° turns), then >=35° turns for remaining 3 players
    turns_top5 = turns_all_df[turns_all_df["play_rank"] <= top_k]
    p_top5 = (
        turns_top5.groupby("nfl_id")[["CSR", "PDR", "TRT", "DJ"]]
        .median()
        .add_prefix("ingame_")
    )
    p_top5_cnt = turns_top5.groupby("nfl_id").size().rename("ingame_turns_count")

    p_all = (
        turns_all_df.groupby("nfl_id")[["CSR", "PDR", "TRT", "DJ"]]
        .median()
        .add_prefix("ingame_")
    )
    p_all_cnt = turns_all_df.groupby("nfl_id").size().rename("ingame_turns_count")

    p_fb = (
        turns_fb_df.groupby("nfl_id")[["CSR", "PDR", "TRT", "DJ"]]
        .median()
        .add_prefix("ingame_")
    )
    p_fb_cnt = turns_fb_df.groupby("nfl_id").size().rename("ingame_turns_count")

    ingame_metrics = p_top5.combine_first(p_all).combine_first(p_fb).reset_index()
    ingame_counts = (
        p_top5_cnt.combine_first(p_all_cnt).combine_first(p_fb_cnt).fillna(0).astype(int).reset_index()
    )
    ingame_df = ingame_metrics.merge(ingame_counts, on="nfl_id", how="left")

    print(
        f"3B.3 Extracted {len(rush_paths_df):,d} active pass-rush window frames (ball_snap -> throw/sack, <=3.0s) "
        f"across {len(rush_windows_top5)} top-{top_k} plays; computed in-game CSR for "
        f"{ingame_df['nfl_id'].nunique()} / {top5_plays['nfl_id'].nunique()} active DL players "
        f"({len(turns_top5)} primary turns in top-{top_k}, {len(turns_all_df)} across top-{fallback_k})"
    )

    payload = {
        "rush_paths_df": rush_paths_df,
        "top5_plays_meta": top5_plays,
        "ingame_turns_df": turns_all_df,
        "ingame_player_metrics": ingame_df,
        "all_candidate_frames": gt_all,
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    pd.to_pickle(payload, cache_path)
    print(f"3B.4 Saved extracted game rush paths & in-game turn metrics -> {cache_path}")

    return ingame_df, rush_paths_df, payload


def plot_phase3_diagnostics(
    outcomes_50_df: pd.DataFrame,
    rush_paths_df: pd.DataFrame,
    turns_df: pd.DataFrame,
) -> tuple[Path, Path]:
    """Generate Phase 3 diagnostic plots: outcome distributions and Combine-to-Game CSR validation."""
    fig_dir = OUTPUTS_DIR / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. Phase 3A Outcome Distributions (N = 103 DL players with >= 50 pass rush snaps)
    dist_path = fig_dir / "phase3a_outcome_distributions.png"
    plot_cols = [
        ("pressure_rate", "Pressure Rate (pressures / rush snaps)", "#1f77b4"),
        ("quick_pressure_rate", "Quick Pressure Rate (<2.5s)", "#ff7f0e"),
        ("avg_get_off", "Avg Get-Off Time (seconds)", "#2ca02c"),
        ("sack_rate", "Sack Rate (sacks / rush snaps)", "#d62728"),
        ("tfl_rate", "TFL Rate (TFLs / defensive snaps)", "#9467bd"),
        ("snap_share", "Career Snap Share (def snaps / game)", "#8c564b"),
        ("start_rate", "Career Start Rate (starts / game)", "#e377c2"),
        ("ingame_CSR", "In-Game Pass Rush CSR", "#17becf"),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(16, 7.5))
    for ax, (col, label, color) in zip(axes.flat, plot_cols):
        vals = outcomes_50_df[col].dropna()
        ax.hist(vals, bins=18, color=color, edgecolor="white", alpha=0.85)
        ax.axvline(
            vals.median(),
            color="black",
            linestyle="--",
            linewidth=1.5,
            label=f"Median: {vals.median():.3f}",
        )
        ax.set_title(label, fontsize=9.5, fontweight="bold")
        ax.set_ylabel("Players")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.25)

    fig.suptitle(
        f"Phase 3A: NFL Outcome Metric Distributions (N = {len(outcomes_50_df)} DL Players with >= 50 Pass Rush Snaps)",
        fontsize=12.5,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(dist_path, dpi=150)
    plt.close(fig)

    # 2. Phase 3B Combine CSR vs In-Game CSR + Sample Extracted Game Rush Paths
    val_path = fig_dir / "phase3b_ingame_csr_validation.png"
    features_path = OUTPUTS_DIR / "dl_combine_features.csv"
    features_df = pd.read_csv(features_path)
    merged = outcomes_50_df.merge(features_df[["nfl_id", "CSR", "FSE"]], on="nfl_id", how="inner")

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2))

    # Panel 1: Combine CSR vs In-Game CSR scatter
    ax0 = axes[0]
    sub_m = merged.dropna(subset=["CSR", "ingame_CSR"])
    r_val = sub_m["CSR"].corr(sub_m["ingame_CSR"])
    r_pr = sub_m["ingame_CSR"].corr(sub_m["pressure_rate"])
    edge_mask = sub_m["nfl_position"].isin(["DE", "OLB"])
    ax0.scatter(
        sub_m.loc[edge_mask, "CSR"],
        sub_m.loc[edge_mask, "ingame_CSR"],
        color="#1f77b4",
        alpha=0.8,
        s=45,
        label=f"Edge (DE/OLB, n={edge_mask.sum()})",
    )
    ax0.scatter(
        sub_m.loc[~edge_mask, "CSR"],
        sub_m.loc[~edge_mask, "ingame_CSR"],
        color="#ff7f0e",
        alpha=0.8,
        s=45,
        marker="s",
        label=f"Interior (DT/NT, n={(~edge_mask).sum()})",
    )
    m_slope, m_int = np.polyfit(sub_m["CSR"], sub_m["ingame_CSR"], 1)
    x_line = np.linspace(sub_m["CSR"].min(), sub_m["CSR"].max(), 50)
    ax0.plot(
        x_line,
        m_slope * x_line + m_int,
        color="crimson",
        linewidth=2,
        label=f"OLS fit (r = {r_val:.3f}; vs PR r = {r_pr:.3f})",
    )
    ax0.set_title(
        f"Combine CSR vs. In-Game Pass Rush CSR\n(N = {len(sub_m)}, Pearson r = {r_val:.3f})",
        fontsize=10.5,
        fontweight="bold",
    )
    ax0.set_xlabel("Combine Cornering Speed Retention (CSR)")
    ax0.set_ylabel("In-Game Pass Rush CSR")
    ax0.legend(loc="lower right", fontsize=8)
    ax0.grid(True, alpha=0.3)

    # Panels 2 & 3: Two sample extracted in-game pass rush paths (one high-CSR Edge rusher, one lower-CSR rusher)
    top_turns = (
        turns_df[turns_df["play_rank"] <= 5]
        .merge(
            outcomes_50_df[["nfl_id", "display_name", "nfl_position", "pressure_rate"]],
            on="nfl_id",
            how="inner",
        )
    )
    high_csr_play = (
        top_turns[
            (top_turns["nfl_position"].isin(["DE", "OLB"]))
            & (top_turns["CSR"].between(0.72, 0.94))
            & (top_turns["total_angle_change"] >= 55.0)
        ]
        .sort_values("pressure_rate", ascending=False)
        .head(1)
    )
    low_csr_play = (
        top_turns[
            (top_turns["nfl_position"].isin(["DE", "OLB"]))
            & (top_turns["CSR"].between(0.32, 0.48))
            & (top_turns["total_angle_change"] >= 55.0)
        ]
        .sort_values("pressure_rate", ascending=True)
        .head(1)
    )
    sample_plays = pd.concat([high_csr_play, low_csr_play], ignore_index=True)

    for idx, (_, trow) in enumerate(sample_plays.iterrows()):
        ax = axes[idx + 1]
        gid, pid, nid = int(trow["game_id"]), int(trow["play_id"]), int(trow["nfl_id"])
        pname = trow["display_name"]
        pos = trow["nfl_position"]
        rw = rush_paths_df[
            (rush_paths_df["game_id"] == gid)
            & (rush_paths_df["play_id"] == pid)
            & (rush_paths_df["nfl_id"] == nid)
        ]
        play_turns = turns_df[
            (turns_df["game_id"] == gid)
            & (turns_df["play_id"] == pid)
            & (turns_df["nfl_id"] == nid)
        ]

        x = rw["x"].to_numpy()
        y = rw["y"].to_numpy()
        s = rw["s"].to_numpy()

        ax.plot(x, y, color="gray", alpha=0.45, linewidth=1.5, label="Rush Path (snap -> end)")
        sc = ax.scatter(x, y, c=s, cmap="viridis", s=38, vmin=0.5, vmax=7.5, zorder=3)
        for t_idx, (_, tev) in enumerate(play_turns.iterrows()):
            st, ed = int(tev["start_frame"]), int(tev["end_frame"])
            ax.plot(
                x[st : ed + 1],
                y[st : ed + 1],
                color="crimson",
                linewidth=3.0,
                zorder=4,
                label="In-Game Turn" if t_idx == 0 else None,
            )
            ax.scatter(
                x[st : ed + 1],
                y[st : ed + 1],
                color="crimson",
                s=55,
                edgecolors="black",
                linewidths=0.6,
                zorder=5,
            )

        last_ev = rw["event"].iloc[-1]
        end_ev = str(last_ev) if pd.notna(last_ev) and str(last_ev) != "ball_snap" else "3.0s_window_end"
        ax.scatter(x[0], y[0], color="limegreen", s=85, marker="^", edgecolor="black", zorder=6, label="ball_snap")
        ax.scatter(x[-1], y[-1], color="gold", s=95, marker="*", edgecolor="black", zorder=6, label=end_ev)
        tier_label = "High In-Game CSR" if idx == 0 else "Low In-Game CSR"
        ax.set_title(
            f"{tier_label}: {pname} ({pos})\nGame {gid}, Play {pid} | Turn CSR = {trow['CSR']:.2f} ({trow['total_angle_change']:.0f}°)",
            fontsize=9.5,
            fontweight="bold",
        )
        ax.set_xlabel("x (yards)")
        ax.set_ylabel("y (yards)")
        ax.set_aspect("equal", adjustable="datalim")
        ax.legend(loc="best", fontsize=7.5)
        ax.grid(True, alpha=0.3)
        plt.colorbar(sc, ax=ax, label="Speed (yd/s)", fraction=0.046, pad=0.04)

    fig.suptitle(
        "Phase 3B: Combine-to-Game CSR Translation & Extracted Pass Rush Windows (<= 3.0s Post-Snap)",
        fontsize=12.5,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(val_path, dpi=150)
    plt.close(fig)

    return dist_path, val_path


def build_nfl_outcomes(
    roster_df: Optional[pd.DataFrame] = None,
    min_pass_rush_snaps: int = 50,
    use_cache: bool = True,
    save: bool = True,
) -> pd.DataFrame:
    """Run full Phase 3 pipeline: play-level aggregation, career outcomes, in-game CSR, and save outputs."""
    if roster_df is None:
        roster_path = OUTPUTS_DIR / "dl_roster_master.csv"
        roster_df = pd.read_csv(roster_path) if roster_path.exists() else load_players(dl_only=True)

    # 3A.1 & 3A.2 Load and classify DL plays
    pp_df = load_dl_player_plays(roster_df)
    n_pr = int(pp_df["is_pass_rush"].sum())
    n_run = int((~pp_df["is_pass_rush"]).sum())
    n_blitz = int(pp_df["is_pass_rush_alt_blitz"].sum())
    n_sack_col = int(pp_df["is_pass_rush_alt_sack_col"].sum())
    print(
        f"3A.1-2 Loaded {len(pp_df):,d} DL plays across {pp_df['nfl_id'].nunique()} players:\n"
        f"  Primary pass rush (player_get_off notna): {n_pr:,d} ({100*n_pr/len(pp_df):.1f}%) | "
        f"Run/coverage: {n_run:,d} ({100*n_run/len(pp_df):.1f}%)\n"
        f"  Alternative definitions -> blitzing==True: {n_blitz:,d} ({100*n_blitz/len(pp_df):.1f}%), "
        f"sack notna: {n_sack_col:,d} ({100*n_sack_col/len(pp_df):.1f}%)"
    )

    # 3A.3 & 3A.5 Per-player aggregates + career outcomes
    outcomes_all = aggregate_play_outcomes(pp_df, roster_df)

    # 3B.1–3B.4 Game tracking rush paths & in-game CSR
    ingame_df, rush_paths_df, payload = build_game_rush_paths_and_ingame_csr(
        pp_df, top_k=5, fallback_k=10, use_cache=use_cache
    )
    outcomes_all = outcomes_all.merge(ingame_df, on="nfl_id", how="left")
    outcomes_all["ingame_turns_count"] = outcomes_all["ingame_turns_count"].fillna(0).astype(int)

    # 3A.4 Apply minimum pass rush snap threshold (default >= 50) & report sensitivity counts
    print("\n3A.4 Minimum pass rush snap threshold sensitivity summary:")
    for thresh in [30, 50, 75]:
        qual = outcomes_all[outcomes_all["total_pass_rush_snaps"] >= thresh]
        excl = outcomes_all[outcomes_all["total_pass_rush_snaps"] < thresh]
        excl_by_yr = excl.groupby("draft_year").size().to_dict()
        qual_by_yr = qual.groupby("draft_year").size().to_dict()
        print(
            f"  Threshold >= {thresh:2d} snaps: {len(qual):3d}/118 retained {qual_by_yr} | "
            f"{len(excl):2d} excluded {excl_by_yr}"
        )

    outcomes_filtered = outcomes_all[
        outcomes_all["total_pass_rush_snaps"] >= min_pass_rush_snaps
    ].copy().reset_index(drop=True)

    print(f"\n3A.3-5 Summary statistics of NFL outcomes (N = {len(outcomes_filtered)}, >= {min_pass_rush_snaps} pass rush snaps):")
    summary_cols = NFL_OUTCOME_COLS + ["ingame_CSR", "ingame_PDR", "ingame_TRT", "ingame_DJ"]
    print(outcomes_filtered[summary_cols].describe().round(3).to_string())

    dist_path, val_path = plot_phase3_diagnostics(
        outcomes_filtered, rush_paths_df, payload["ingame_turns_df"]
    )
    print(f"\nPhase 3 diagnostic figures saved -> {dist_path}, {val_path}")

    # 3A.6 Save outputs/dl_nfl_outcomes.csv (filtered to >=50 snaps) and unfiltered table for Phase 4B.5 sensitivity
    if save:
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        tables_dir = OUTPUTS_DIR / "tables"
        tables_dir.mkdir(parents=True, exist_ok=True)

        out_csv = OUTPUTS_DIR / "dl_nfl_outcomes.csv"
        outcomes_filtered.to_csv(out_csv, index=False)

        all_csv = tables_dir / "dl_nfl_outcomes_all.csv"
        outcomes_all.to_csv(all_csv, index=False)
        print(
            f"3A.6 Saved filtered NFL outcomes ({outcomes_filtered.shape[0]} rows, {outcomes_filtered.shape[1]} cols) -> {out_csv}\n"
            f"     Saved full 118-player table (for Phase 4B.5 threshold sensitivity) -> {all_csv}"
        )

    return outcomes_filtered


if __name__ == "__main__":
    build_nfl_outcomes()
