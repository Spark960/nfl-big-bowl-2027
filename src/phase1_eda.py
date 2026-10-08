"""Phase 0 & Phase 1 EDA execution script following docs/08_execution_plan.md."""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.data_loading import (
    DATA_DIR,
    DL_LINED_UP_POSITIONS,
    DL_POSITIONS,
    OUTPUTS_DIR,
    load_career_successes,
    load_combine_results,
    load_combine_tracking,
    load_game_tracking,
    load_games,
    load_player_play,
    load_players,
)
from src.utils import frame_angular_change


def run_phase1a() -> pd.DataFrame:
    """Phase 1A: Identify DL player cohort and save outputs/dl_roster_master.csv."""
    print("\n=== PHASE 1A: IDENTIFY PLAYER COHORT ===")
    dl_players = load_players(dl_only=True)
    pos_counts = dl_players["nfl_position"].value_counts().to_dict()
    edge_count = dl_players["nfl_position"].isin(["DE", "OLB"]).sum()
    interior_count = dl_players["nfl_position"].isin(["DT", "NT"]).sum()
    print(
        f"1A.1 DL Cohort: {len(dl_players)} players "
        f"(Edge DE+OLB={edge_count}, Interior DT+NT={interior_count}) -> {pos_counts}"
    )

    combine_res = load_combine_results(nfl_ids=dl_players["nfl_id"])
    combine_cols_to_drop = [c for c in ["draft_year"] if c in combine_res.columns]
    roster = dl_players.merge(
        combine_res.drop(columns=combine_cols_to_drop), on="nfl_id", how="left"
    )

    key_combine_cols = [
        "forty",
        "ten_yd_split",
        "three_cone",
        "short_shuttle",
        "vertical",
        "broad_jump",
        "ngs_athleticism_score",
    ]
    print("1A.2 Traditional Combine metric availability (out of 118 DL players):")
    for col in key_combine_cols:
        non_null = roster[col].notna().sum()
        nulls = roster[col].isna().sum()
        print(
            f"  {col:25s}: {non_null:3d} present, {nulls:3d} null (opt-out rate: {100*nulls/len(roster):.1f}%)"
        )

    target_drills = [
        "SKILL_DRILLS_DL",
        "THREE_CONE_DRILL",
        "SHORT_SHUTTLE",
        "FORTY_YARD_DASH",
    ]
    ct_all = load_combine_tracking(drill_types=target_drills)
    print("1A.3 Unique nfl_id in combine_tracking.csv by drill_type:")
    for dt in target_drills:
        all_ids = ct_all[ct_all["drill_type"] == dt]["nfl_id"].dropna().nunique()
        dl_ids = (
            ct_all[
                (ct_all["drill_type"] == dt)
                & (ct_all["nfl_id"].isin(dl_players["nfl_id"]))
            ]["nfl_id"]
            .dropna()
            .nunique()
        )
        print(f"  {dt:20s}: {all_ids:3d} total prospects | {dl_ids:3d} in DL cohort")

    dl_in_any_tracking = (
        ct_all[ct_all["nfl_id"].isin(dl_players["nfl_id"])]["nfl_id"].dropna().nunique()
    )
    print(f"  Total DL cohort players in combine_tracking: {dl_in_any_tracking}/{len(dl_players)}")

    for dt in target_drills:
        ids_in_dt = set(
            ct_all[ct_all["drill_type"] == dt]["nfl_id"].dropna().astype(int)
        )
        roster[f"has_tracking_{dt.lower()}"] = roster["nfl_id"].isin(ids_in_dt)

    career = load_career_successes(nfl_ids=dl_players["nfl_id"])
    roster = roster.merge(career, on="nfl_id", how="left")
    print(
        f"1A.4 Joined career outcomes: avg defensive snaps = {roster['career_defensive_snaps'].mean():.1f}, "
        f"avg starts = {roster['career_games_started'].mean():.1f}"
    )

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUTS_DIR / "dl_roster_master.csv"
    roster.to_csv(out_path, index=False)
    print(f"1A.5 Saved master roster ({roster.shape[0]} rows, {roster.shape[1]} cols) -> {out_path}")
    return roster


def run_phase1b(roster: pd.DataFrame) -> pd.DataFrame:
    """Phase 1B: Understand Combine tracking frame structure and generate diagnostic plots."""
    print("\n=== PHASE 1B: COMBINE TRACKING FRAME STRUCTURE ===")
    dl_ids = set(roster["nfl_id"])

    # Load entire combine_tracking once to check BALL frames linked by event_id as well as nfl_id
    ct_full = load_combine_tracking()
    dl_event_ids = set(ct_full[ct_full["nfl_id"].isin(dl_ids)]["event_id"])
    ct_dl = ct_full[ct_full["event_id"].isin(dl_event_ids)].copy()
    print(
        f"1B.1 Loaded {len(ct_dl):,d} combine tracking frames across {len(dl_event_ids):,d} attempts "
        f"for {ct_dl['nfl_id'].dropna().nunique()} DL players"
    )

    # 1B.6 Separate PLAYER vs BALL across all combine tracking & DL attempts
    print("\n1B.6 Entity type breakdown across entire combine_tracking.csv:")
    print(ct_full.groupby(["drill_type", "entity_type"]).size().unstack(fill_value=0).to_string())
    print("\n1B.6 Entity type breakdown within DL player event_ids:")
    print(ct_dl.groupby(["drill_type", "drill_name", "entity_type"]).size().unstack(fill_value=0).to_string())

    ct_player = ct_dl[(ct_dl["entity_type"] == "PLAYER") & (ct_dl["nfl_id"].isin(dl_ids))].copy()
    ct_player["time_dt"] = pd.to_datetime(ct_player["time"], format="ISO8601")
    ct_player = ct_player.sort_values(["event_id", "nfl_id", "time_dt"]).reset_index(drop=True)

    ct_player["dt"] = ct_player.groupby(["event_id", "nfl_id"])["time_dt"].diff().dt.total_seconds()
    ct_player["frame_idx"] = ct_player.groupby(["event_id", "nfl_id"]).cumcount()
    ct_player["step_xy"] = np.hypot(
        ct_player.groupby(["event_id", "nfl_id"])["x"].diff(),
        ct_player.groupby(["event_id", "nfl_id"])["y"].diff(),
    ).fillna(0.0)
    ct_player["dir_change"] = (
        ct_player.groupby(["event_id", "nfl_id"], group_keys=False)["dir"]
        .apply(frame_angular_change)
    )
    ct_player["abs_dir_change"] = ct_player["dir_change"].abs()

    # Mark active drill window per attempt (between first and last frame where s > 0.5 yd/s)
    def _in_active_window(s_series: pd.Series) -> pd.Series:
        moving = s_series > 0.5
        if not moving.any():
            return pd.Series(False, index=s_series.index)
        first_idx = moving.idxmax()
        last_idx = moving[::-1].idxmax()
        mask = pd.Series(False, index=s_series.index)
        mask.loc[first_idx:last_idx] = True
        return mask

    ct_player["in_drill_window"] = (
        ct_player.groupby(["event_id", "nfl_id"], group_keys=False)["s"]
        .apply(_in_active_window)
    )
    ct_player["active_abs_dir_change"] = np.where(
        ct_player["in_drill_window"], ct_player["abs_dir_change"], 0.0
    )

    dt_valid = ct_player["dt"].dropna()
    pct_10hz = 100.0 * (np.isclose(dt_valid, 0.1, atol=0.01)).mean()
    print(
        f"\n1B.3 Sampling check: {pct_10hz:.2f}% of frame intervals are 0.10s "
        f"(median dt={dt_valid.median():.3f}s, min={dt_valid.min():.3f}s, max={dt_valid.max():.3f}s)"
    )

    # 1B.2 Catalog every drill_name that DL players participate in
    attempt_stats = (
        ct_player.groupby(["drill_type", "drill_name", "event_id", "nfl_id"])
        .agg(
            n_frames=("s", "size"),
            max_speed=("s", "max"),
            active_turn_frames_15=("active_abs_dir_change", lambda s: (s > 15.0).sum()),
            active_turn_frames_30=("active_abs_dir_change", lambda s: (s > 30.0).sum()),
            net_displacement=(
                "x",
                lambda s: float(
                    np.hypot(
                        s.iloc[-1] - s.iloc[0],
                        ct_player.loc[s.index, "y"].iloc[-1] - ct_player.loc[s.index, "y"].iloc[0],
                    )
                ),
            ),
            path_length=("step_xy", "sum"),
        )
        .reset_index()
    )
    attempt_stats["sinuosity"] = attempt_stats["path_length"] / attempt_stats["net_displacement"].clip(lower=0.5)

    catalog = (
        attempt_stats.groupby(["drill_type", "drill_name"])
        .agg(
            total_frames=("n_frames", "sum"),
            unique_players=("nfl_id", "nunique"),
            total_attempts=("event_id", "count"),
            avg_frames_per_attempt=("n_frames", "mean"),
            avg_path_yards=("path_length", "mean"),
            avg_max_speed=("max_speed", "mean"),
            avg_active_turns_gt15deg=("active_turn_frames_15", "mean"),
            avg_active_turns_gt30deg=("active_turn_frames_30", "mean"),
            avg_sinuosity=("sinuosity", "mean"),
        )
        .reset_index()
        .sort_values(["drill_type", "total_frames"], ascending=[True, False])
    )
    print("\n1B.2 DL Drill Catalog (PLAYER frames):")
    print(catalog.to_string(index=False))

    tables_dir = OUTPUTS_DIR / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    catalog.to_csv(tables_dir / "dl_drill_catalog.csv", index=False)

    figures_dir = OUTPUTS_DIR / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    sample_drills = [
        "THREE_CONE_DRILL",
        "SHORT_SHUTTLE",
        "PASS_RUSH_DRILL",
        "RUN_THE_HOOP_DRILL",
        "FOUR_BAG_AGILITY_DRILL",
        "FORTY_YARD_DASH",
    ]
    player_drill_coverage = (
        ct_player[ct_player["drill_name"].isin(sample_drills)]
        .groupby("nfl_id")["drill_name"]
        .nunique()
        .sort_values(ascending=False)
    )
    sample_player_ids = list(player_drill_coverage.head(3).index)
    name_map = roster.set_index("nfl_id")["display_name"].to_dict()
    print(
        "\n1B.3 Sample players selected for trajectory & speed profile plots:",
        [(int(pid), name_map.get(pid, str(pid))) for pid in sample_player_ids],
    )

    # Helper to pick one of the 3 sample players for each drill panel so all 3 are showcased
    def _select_sample_attempt(dname: str, panel_idx: int) -> pd.DataFrame:
        preferred_pid = sample_player_ids[panel_idx % len(sample_player_ids)]
        sub = ct_player[(ct_player["drill_name"] == dname) & (ct_player["nfl_id"] == preferred_pid)]
        if sub.empty:
            sub = ct_player[
                (ct_player["drill_name"] == dname)
                & (ct_player["nfl_id"].isin(sample_player_ids))
            ]
        if sub.empty:
            sub = ct_player[ct_player["drill_name"] == dname]
        first_ev = sub["event_id"].iloc[0]
        return sub[sub["event_id"] == first_ev]

    # Plot 1B.3: Trajectories (x vs y colored by speed s) for sample drills
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    for idx, (ax, dname) in enumerate(zip(axes.flat, sample_drills)):
        ev_df = _select_sample_attempt(dname, idx)
        pid = int(ev_df["nfl_id"].iloc[0])
        pname = name_map.get(pid, f"ID {pid}")

        sc = ax.scatter(
            ev_df["x"],
            ev_df["y"],
            c=ev_df["s"],
            cmap="plasma",
            s=35,
            edgecolors="none",
        )
        ax.plot(ev_df["x"], ev_df["y"], color="gray", alpha=0.4, linewidth=1)
        ax.scatter(ev_df["x"].iloc[0], ev_df["y"].iloc[0], color="green", s=80, marker="^", label="Start")
        ax.scatter(ev_df["x"].iloc[-1], ev_df["y"].iloc[-1], color="red", s=80, marker="s", label="End")
        ax.set_title(f"{dname}\n({pname})", fontsize=10, fontweight="bold")
        ax.set_xlabel("x (yards)")
        ax.set_ylabel("y (yards)")
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(True, alpha=0.3)
        plt.colorbar(sc, ax=ax, label="Speed (yd/s)", fraction=0.046, pad=0.04)
    axes[0, 0].legend(loc="best", fontsize=8)
    fig.suptitle("Phase 1B.3: Sample DL Combine Drill Trajectories (Colored by Speed)", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(figures_dir / "phase1b_sample_trajectories.png", dpi=150)
    plt.close(fig)

    # Plot 1B.4: Speed profiles (s vs frame index) with sharp direction changes marked
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    for idx, (ax, dname) in enumerate(zip(axes.flat, sample_drills)):
        ev_df = _select_sample_attempt(dname, idx)
        pid = int(ev_df["nfl_id"].iloc[0])
        pname = name_map.get(pid, f"ID {pid}")

        ax.plot(ev_df["frame_idx"], ev_df["s"], color="#1f77b4", linewidth=2, label="Speed (yd/s)")
        turns_30 = ev_df[ev_df["active_abs_dir_change"] > 30.0]
        turns_15 = ev_df[(ev_df["active_abs_dir_change"] > 15.0) & (ev_df["active_abs_dir_change"] <= 30.0)]
        if not turns_15.empty:
            ax.scatter(
                turns_15["frame_idx"],
                turns_15["s"],
                color="orange",
                s=40,
                zorder=4,
                label="|Δdir| 15–30°/frame",
            )
        if not turns_30.empty:
            ax.scatter(
                turns_30["frame_idx"],
                turns_30["s"],
                color="crimson",
                s=55,
                zorder=5,
                label="|Δdir| > 30°/frame",
            )
        ax.set_title(f"{dname}\n({pname})", fontsize=10, fontweight="bold")
        ax.set_xlabel("Frame Index (0.10s / frame)")
        ax.set_ylabel("Speed s (yd/s)")
        ax.grid(True, alpha=0.3)
    axes[0, 0].legend(loc="best", fontsize=8)
    fig.suptitle("Phase 1B.4: Speed Profiles & Sharp Direction Changes Across Drills", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(figures_dir / "phase1b_speed_profiles.png", dpi=150)
    plt.close(fig)

    # Plot 1B.5: 3-cone and short shuttle `dir` and `|Δdir|` + `s` over time
    fig, axes = plt.subplots(2, 2, figsize=(14, 8), sharex="col")
    for col_idx, dname in enumerate(["THREE_CONE_DRILL", "SHORT_SHUTTLE"]):
        ev_df = _select_sample_attempt(dname, col_idx).copy()
        pid = int(ev_df["nfl_id"].iloc[0])
        pname = name_map.get(pid, f"ID {pid}")
        t_sec = ev_df["frame_idx"] * 0.1

        ax_top = axes[0, col_idx]
        ax_top.plot(t_sec, ev_df["dir"], "o-", color="#2ca02c", markersize=4, alpha=0.8, label="Raw dir (°)")
        ax_top.set_ylabel("Direction dir (degrees)", color="#2ca02c")
        ax_top.set_title(f"{dname} — {pname}", fontsize=11, fontweight="bold")
        ax_top.grid(True, alpha=0.3)

        ax_top_r = ax_top.twinx()
        ax_top_r.plot(t_sec, ev_df["s"], "--", color="#1f77b4", linewidth=1.8, label="Speed s (yd/s)")
        ax_top_r.set_ylabel("Speed s (yd/s)", color="#1f77b4")

        ax_bot = axes[1, col_idx]
        ax_bot.plot(t_sec, ev_df["active_abs_dir_change"], "o-", color="crimson", markersize=4, label="|Δdir|/frame (active drill window)")
        ax_bot.axhline(30.0, color="black", linestyle=":", linewidth=1.2, label="30°/frame threshold")
        ax_bot.axhline(15.0, color="orange", linestyle=":", linewidth=1.2, label="15°/frame threshold")
        ax_bot.set_xlabel("Time (seconds)")
        ax_bot.set_ylabel("|Δdir| per frame (deg)")
        ax_bot.legend(loc="upper right", fontsize=8)
        ax_bot.grid(True, alpha=0.3)

    fig.suptitle("Phase 1B.5: Direction (dir) Signal Quality & Turn Identification in 3-Cone and Shuttle", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(figures_dir / "phase1b_dir_over_time.png", dpi=150)
    plt.close(fig)

    return ct_player


def run_phase1c(roster: pd.DataFrame) -> pd.DataFrame:
    """Phase 1C: Understand NFL Game Data Structure."""
    print("\n=== PHASE 1C: NFL GAME DATA STRUCTURE ===")
    dl_ids = set(roster["nfl_id"])

    # 1C.1 Load player_play.csv filtered to our DL nfl_ids
    pp_all_dl = load_player_play(nfl_ids=dl_ids)
    print(f"1C.1 Total plays for DL cohort in player_play.csv: {len(pp_all_dl):,d} across {pp_all_dl['nfl_id'].nunique()} players")
    print("  lined_up_position breakdown for DL cohort:")
    print(" ", pp_all_dl["lined_up_position"].value_counts(dropna=False).to_dict())

    # Note critical EDA discovery: player_play.csv uses 'EDGE' and 'INTERIOR_LINE' (plus occasional 'OLB')
    pp_dl = pp_all_dl[pp_all_dl["lined_up_position"].isin(DL_LINED_UP_POSITIONS)].copy()
    print(
        f"  Filtered to lined_up_position in {DL_LINED_UP_POSITIONS}: "
        f"{len(pp_dl):,d} plays across {pp_dl['nfl_id'].nunique()} players"
    )

    # 1C.2 Count pass rush snaps vs run defense snaps per player
    pp_dl["is_pass_rush"] = pp_dl["player_get_off"].notna()
    player_snaps = (
        pp_dl.groupby("nfl_id")
        .agg(
            total_dl_snaps=("play_id", "count"),
            pass_rush_snaps=("is_pass_rush", "sum"),
            pressures=("time_to_pressure", lambda s: s.notna().sum()),
            hurries=("time_to_qb_hurry", lambda s: s.notna().sum()),
            sacks=("sack", lambda s: (s.fillna(0) > 0).sum()),
            quick_pressures=("quick_pressure", lambda s: (s.fillna(0) > 0).sum()),
            tfls=("tackle_for_loss", lambda s: (s.fillna(0) > 0).sum()),
            avg_get_off=("player_get_off", "mean"),
        )
        .reset_index()
    )
    player_snaps["run_or_other_snaps"] = (
        player_snaps["total_dl_snaps"] - player_snaps["pass_rush_snaps"]
    )
    player_snaps["pass_rush_ratio"] = (
        player_snaps["pass_rush_snaps"] / player_snaps["total_dl_snaps"]
    )
    player_snaps["pressure_rate"] = (
        player_snaps["pressures"] / player_snaps["pass_rush_snaps"].replace(0, np.nan)
    )

    snap_summary = roster[["nfl_id", "display_name", "nfl_position", "draft_year"]].merge(
        player_snaps, on="nfl_id", how="left"
    )
    for c in ["total_dl_snaps", "pass_rush_snaps", "run_or_other_snaps", "pressures", "hurries", "sacks", "quick_pressures", "tfls"]:
        snap_summary[c] = snap_summary[c].fillna(0).astype(int)
    snap_summary["pass_rush_ratio"] = snap_summary["pass_rush_ratio"].fillna(0.0)

    print(
        f"\n1C.2 Pass rush vs run/other snaps across {len(pp_dl):,d} DL plays: "
        f"{pp_dl['is_pass_rush'].sum():,d} pass rush ({100*pp_dl['is_pass_rush'].mean():.1f}%), "
        f"{(~pp_dl['is_pass_rush']).sum():,d} run/other ({100*(~pp_dl['is_pass_rush']).mean():.1f}%)"
    )

    # 1C.3 Check availability of key defensive metrics
    pr_plays = pp_dl[pp_dl["is_pass_rush"]]
    metrics_to_check = [
        "player_get_off",
        "time_to_pressure",
        "time_to_qb_hurry",
        "sack",
        "quick_pressure",
        "tackle_for_loss",
    ]
    print("\n1C.3 Key Defensive Metric Availability (All DL plays vs Pass Rush plays):")
    for m in metrics_to_check:
        all_nn = pp_dl[m].notna().sum()
        all_pos = (pp_dl[m].fillna(0) > 0).sum()
        pr_nn = pr_plays[m].notna().sum()
        pr_pos = (pr_plays[m].fillna(0) > 0).sum()
        print(
            f"  {m:20s}: non-null {all_nn:6,d}/{len(pp_dl):,d} ({100*all_nn/len(pp_dl):5.1f}%), >0: {all_pos:5,d} ({100*all_pos/len(pp_dl):5.2f}%) | "
            f"on pass rush: non-null {pr_nn:6,d}/{len(pr_plays):,d} ({100*pr_nn/len(pr_plays):5.1f}%), "
            f">0 count: {pr_pos:5,d} ({100*pr_pos/len(pr_plays):5.2f}%)"
        )

    print("\n  Sample size by minimum pass rush snap threshold:")
    for thresh in [1, 25, 30, 50, 75, 100, 150]:
        n_qual = (snap_summary["pass_rush_snaps"] >= thresh).sum()
        by_yr = (
            snap_summary[snap_summary["pass_rush_snaps"] >= thresh]
            .groupby("draft_year")
            .size()
            .to_dict()
        )
        print(f"    >= {thresh:3d} pass rush snaps: {n_qual:3d} / {len(snap_summary)} DL players (by draft_year: {by_yr})")

    snap_summary.to_csv(OUTPUTS_DIR / "tables" / "dl_snap_summary.csv", index=False)

    # 1C.4 Peek at game_tracking_2023.csv for 2 specific pass rush plays by known edge rushers
    games_2023 = set(load_games().query("season == 2023")["game_id"])
    edge_2023_plays = pp_dl[
        (pp_dl["game_id"].isin(games_2023))
        & (pp_dl["is_pass_rush"])
        & (pp_dl["time_to_pressure"].notna())
        & (pp_dl["sack"].fillna(0) >= 1.0)
        & (pp_dl["lined_up_position"] == "EDGE")
    ].merge(roster[["nfl_id", "display_name", "nfl_position"]], on="nfl_id")

    # Select 2 distinct known edge rushers (e.g. Will Anderson + another top edge rusher)
    sample_plays = (
        edge_2023_plays.sort_values("time_to_pressure")
        .drop_duplicates(subset=["nfl_id"])
        .head(2)
    )
    print("\n1C.4 Selected 2 sample 2023 pass rush sack plays:")
    for _, row in sample_plays.iterrows():
        print(
            f"  Player: {row['display_name']} ({row['nfl_position']}, nfl_id={row['nfl_id']}) | "
            f"game_id={row['game_id']}, play_id={row['play_id']} | "
            f"get_off={row['player_get_off']:.3f}s, time_to_pressure={row['time_to_pressure']:.3f}s"
        )

    gt_sample = load_game_tracking(
        seasons=(2023,),
        game_ids=sample_plays["game_id"].unique(),
        play_ids=sample_plays["play_id"].unique(),
        nfl_ids=sample_plays["nfl_id"].unique(),
    )
    gt_sample["time_dt"] = pd.to_datetime(gt_sample["time"], format="ISO8601")
    gt_sample = gt_sample.sort_values(["game_id", "play_id", "nfl_id", "time_dt"]).reset_index(drop=True)

    # Plot 1C.4: Rush path trajectory and s, a, dir, o over time for the 2 sample plays
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    for row_idx, (_, play_row) in enumerate(sample_plays.iterrows()):
        gid, pid, nid = int(play_row["game_id"]), int(play_row["play_id"]), int(play_row["nfl_id"])
        pname = play_row["display_name"]
        pf = gt_sample[
            (gt_sample["game_id"] == gid)
            & (gt_sample["play_id"] == pid)
            & (gt_sample["nfl_id"] == nid)
        ].copy()
        pf["t_sec"] = (pf["time_dt"] - pf["time_dt"].iloc[0]).dt.total_seconds()
        pf["dt"] = pf["time_dt"].diff().dt.total_seconds()

        events_in_play = pf[pf["event"].notna()][["t_sec", "event"]].to_dict("records")
        print(
            f"  Play frames={len(pf)} (10Hz check median dt={pf['dt'].median():.3f}s), "
            f"Event sequence for {pname} (game {gid}, play {pid}): {events_in_play}"
        )

        ax_xy = axes[row_idx, 0]
        sc = ax_xy.scatter(pf["x"], pf["y"], c=pf["s"], cmap="plasma", s=40)
        ax_xy.plot(pf["x"], pf["y"], color="gray", alpha=0.4)
        for ev in pf[pf["event"].notna()].itertuples():
            ax_xy.scatter(ev.x, ev.y, s=90, marker="*", edgecolor="black", zorder=5)
            ax_xy.annotate(
                ev.event,
                (ev.x, ev.y),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=8,
                fontweight="bold",
            )
        ax_xy.set_title(f"{pname} — Rush Path (game {gid}, play {pid})", fontsize=10, fontweight="bold")
        ax_xy.set_xlabel("x (yards)")
        ax_xy.set_ylabel("y (yards)")
        ax_xy.set_aspect("equal", adjustable="datalim")
        ax_xy.grid(True, alpha=0.3)
        plt.colorbar(sc, ax=ax_xy, label="Speed s (yd/s)", fraction=0.046, pad=0.04)

        ax_sig = axes[row_idx, 1]
        ax_sig.plot(pf["t_sec"], pf["s"], label="Speed s (yd/s)", color="#1f77b4", linewidth=2)
        ax_sig.plot(pf["t_sec"], pf["a"], label="Accel a (yd/s²)", color="#ff7f0e", linewidth=1.5)
        for ev in pf[pf["event"].notna()].itertuples():
            ax_sig.axvline(ev.t_sec, color="crimson", linestyle="--", alpha=0.7)
            ax_sig.text(ev.t_sec + 0.05, ax_sig.get_ylim()[1] * 0.82, ev.event, fontsize=8, color="crimson")
        ax_sig.set_xlabel("Time from play tracking start (seconds)")
        ax_sig.set_ylabel("Speed (yd/s) / Accel (yd/s²)")
        ax_sig.set_title(f"{pname} — In-Game Kinematics (s, a, dir, o)", fontsize=10, fontweight="bold")
        ax_sig.grid(True, alpha=0.3)

        ax_ang = ax_sig.twinx()
        ax_ang.plot(pf["t_sec"], pf["dir"], ":", color="#2ca02c", alpha=0.85, label="Motion dir (°)")
        ax_ang.plot(pf["t_sec"], pf["o"], "-.", color="#9467bd", alpha=0.85, label="Body orient o (°)")
        ax_ang.set_ylabel("Angle (degrees, 0–360)")

        lines1, labels1 = ax_sig.get_legend_handles_labels()
        lines2, labels2 = ax_ang.get_legend_handles_labels()
        ax_sig.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=7)

    fig.suptitle("Phase 1C.4: Sample In-Game Pass Rush Trajectories & 10 Hz Tracking Signals", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUTPUTS_DIR / "figures" / "phase1c_game_rush_samples.png", dpi=150)
    plt.close(fig)

    return snap_summary


if __name__ == "__main__":
    roster_df = run_phase1a()
    ct_df = run_phase1b(roster_df)
    snaps_df = run_phase1c(roster_df)
    print("\nPhase 1 execution completed successfully.")
