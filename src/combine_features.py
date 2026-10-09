"""Combine tracking feature engineering (Phase 2)."""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.data_loading import (
    OUTPUTS_DIR,
    load_combine_results,
    load_combine_tracking,
    load_players,
)
from src.utils import angular_rate, detect_turn_events

TRACKING_METRIC_COLS = ["CSR", "PDR", "TRT", "FSE", "ACS", "DJ"]
TRADITIONAL_METRIC_COLS = [
    "forty",
    "ten_yd_split",
    "three_cone",
    "short_shuttle",
    "vertical",
    "broad_jump",
    "ngs_athleticism_score",
]


def prepare_combine_tracking(nfl_ids: Optional[ pd.Series | list[int] | set[int] ] = None) -> pd.DataFrame:
    """Load and chronologically sort PLAYER frames from combine_tracking.csv for the DL cohort."""
    if nfl_ids is None:
        nfl_ids = load_players(dl_only=True)["nfl_id"]
    ct = load_combine_tracking(nfl_ids=nfl_ids, entity_type="PLAYER")
    ct["time_dt"] = pd.to_datetime(ct["time"], format="ISO8601")
    ct = ct.sort_values(["event_id", "nfl_id", "time_dt"]).reset_index(drop=True)
    ct["frame_idx"] = ct.groupby(["event_id", "nfl_id"]).cumcount()
    return ct


def compute_turn_metrics_for_attempt(
    attempt_df: pd.DataFrame,
    threshold: float = 30.0,
    min_total_angle: float = 45.0,
    min_turn_speed: float = 1.3,
    ref_entry_speed: float = 4.8,
    dt: float = 0.1,
) -> list[dict]:
    """Compute per-turn CSR, PDR, TRT, and DJ for all detected turns in a single attempt.

    Parameters
    ----------
    attempt_df : pd.DataFrame
        Chronologically sorted frames for a single attempt containing columns `s` and `dir`.
    threshold : float
        Minimum angular rate (deg/s) for turn frame detection.
    min_total_angle : float
        Minimum cumulative angle change (degrees) for a valid turn event.
    min_turn_speed : float
        Minimum speed (yd/s) during active cornering frames.
    ref_entry_speed : float
        Reference pass-rush approach speed floor (yd/s) so low-speed approaches do not
        artificially inflate the CSR ratio.
    dt : float
        Frame interval in seconds (0.1s for 10 Hz tracking).
    """
    events = detect_turn_events(
        attempt_df,
        threshold=threshold,
        min_total_angle=min_total_angle,
        min_turn_speed=min_turn_speed,
        dt=dt,
    )
    if not events:
        return []

    s = attempt_df["s"].to_numpy(dtype=float)
    moving = np.where(s > 0.5)[0]
    sw, ew = int(moving[0]), int(moving[-1])

    rate = angular_rate(attempt_df["dir"], dt=dt).fillna(0.0).to_numpy(dtype=float)
    ddir2 = np.diff(rate, prepend=rate[0]) / dt
    ds = np.diff(s, prepend=s[0])

    results: list[dict] = []
    for ev in events:
        st, ed = ev["start_frame"], ev["end_frame"]
        raw_entry_s = float(np.mean(s[st - 3 : st]))
        entry_s = max(raw_entry_s, ref_entry_speed)

        turn_s = s[st : ed + 1]
        min_s = float(np.min(turn_s))
        min_idx = st + int(np.argmin(turn_s))

        # 2B.1 Cornering Speed Retention (CSR)
        csr = min_s / entry_s

        # 2B.2 Peak Deceleration Rate (PDR): min frame-to-frame delta_s entering/during turn
        pdr = float(np.min(ds[max(sw, st - 3) : ed + 1]))

        # 2B.3 Turn Recovery Time (TRT): seconds from min(s) frame until s >= 0.9 * entry_speed
        target_s = 0.9 * entry_s
        post_s = s[min_idx : ew + 1]
        rec_hits = np.where(post_s >= target_s)[0]
        trt = float(rec_hits[0] * dt) if len(rec_hits) > 0 else float(len(post_s) * dt)

        # 2B.6 Directional Jerk (DJ): std dev of second derivative of dir during turn
        dj = float(np.std(ddir2[st : ed + 1]))

        results.append(
            {
                **ev,
                "entry_speed": entry_s,
                "min_speed": min_s,
                "CSR": csr,
                "PDR": pdr,
                "TRT": trt,
                "DJ": dj,
            }
        )
    return results


def compute_player_turn_metrics(ct_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute per-player median CSR, PDR, TRT, and DJ across all non-sprint Combine drills."""
    turn_rows: list[dict] = []
    non_sprint = ct_df[ct_df["drill_type"] != "FORTY_YARD_DASH"]

    for (eid, nid, dname, dtype), grp in non_sprint.groupby(
        ["event_id", "nfl_id", "drill_name", "drill_type"], sort=False
    ):
        for tm in compute_turn_metrics_for_attempt(grp):
            turn_rows.append(
                {
                    "event_id": eid,
                    "nfl_id": int(nid),
                    "drill_type": dtype,
                    "drill_name": dname,
                    **tm,
                }
            )

    turns_df = pd.DataFrame(turn_rows)
    player_turns = (
        turns_df.groupby("nfl_id")[["CSR", "PDR", "TRT", "DJ"]]
        .median()
        .reset_index()
    )
    return player_turns, turns_df


def compute_fse_and_acs(ct_df: pd.DataFrame) -> pd.DataFrame:
    """Compute First-Step Explosion (FSE, 2B.4) and Acceleration Curve Shape (ACS, 2B.5)."""
    fse_rows: list[dict] = []
    acs_rows: list[dict] = []

    for (eid, nid, dtype, dname), grp in ct_df.groupby(
        ["event_id", "nfl_id", "drill_type", "drill_name"], sort=False
    ):
        s = grp["s"].to_numpy(dtype=float)
        a = grp["a"].to_numpy(dtype=float)
        onset_idx = np.where(s > 1.0)[0]
        f0 = max(0, int(onset_idx[0]) - 1) if len(onset_idx) > 0 else 0

        # 2B.4 First-Step Explosion (FSE): max(a) in first 5 frames (0.5s) from movement onset
        if dtype in ["FORTY_YARD_DASH", "SKILL_DRILLS_DL", "SKILL_DRILLS_LB"]:
            fse_rows.append(
                {
                    "event_id": eid,
                    "nfl_id": int(nid),
                    "drill_type": dtype,
                    "drill_name": dname,
                    "fse_raw": float(np.max(a[f0 : f0 + 5])),
                }
            )

        # 2B.5 Acceleration Curve Shape (ACS): mean(a[0:10]) / mean(a[10:20])
        if len(a) >= f0 + 20:
            early_accel = float(np.mean(a[f0 : f0 + 10]))
            late_accel = float(np.mean(a[f0 + 10 : f0 + 20]))
            if late_accel > 0.1:
                acs_rows.append(
                    {
                        "event_id": eid,
                        "nfl_id": int(nid),
                        "drill_type": dtype,
                        "ACS": early_accel / late_accel,
                    }
                )

    fse_df = pd.DataFrame(fse_rows)
    # Standardize across drill names onto the global FSE scale (yd/s^2) so 40-yard dash opt-outs are not biased
    d_mean = fse_df.groupby("drill_name")["fse_raw"].transform("mean")
    d_std = fse_df.groupby("drill_name")["fse_raw"].transform("std").replace(0, 1.0)
    fse_df["FSE"] = fse_df["fse_raw"].mean() + fse_df["fse_raw"].std() * (fse_df["fse_raw"] - d_mean) / d_std
    player_fse = fse_df.groupby("nfl_id")["FSE"].median().reset_index()

    acs_df = pd.DataFrame(acs_rows)
    # Primary source: FORTY_YARD_DASH (93 players); fallback: sprint/skill drills for the 25 40-yard dash opt-outs
    acs_40 = acs_df[acs_df["drill_type"] == "FORTY_YARD_DASH"].groupby("nfl_id")["ACS"].median()
    acs_all = acs_df.groupby("nfl_id")["ACS"].median()
    player_acs = acs_40.combine_first(acs_all).rename("ACS").reset_index()

    return player_fse.merge(player_acs, on="nfl_id", how="outer")


def validate_turn_detection_plots(
    ct_df: pd.DataFrame,
    roster_df: pd.DataFrame,
    out_path: Optional[Path] = None,
) -> Path:
    """Phase 2A.3: Plot sample drill trajectories & speed profiles with detected turns highlighted."""
    if out_path is None:
        out_path = OUTPUTS_DIR / "figures" / "phase2a_turn_validation.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sample_drills = [
        "THREE_CONE_DRILL",
        "SHORT_SHUTTLE",
        "PASS_RUSH_DRILL",
        "RUN_THE_HOOP_DRILL",
        "FOUR_BAG_AGILITY_DRILL",
        "BODY_CONTROL_DRILL",
    ]
    name_map = roster_df.set_index("nfl_id")["display_name"].to_dict()

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    for ax, dname in zip(axes.flat, sample_drills):
        sub = ct_df[ct_df["drill_name"] == dname]
        # Pick the first attempt that has at least 1 detected turn
        chosen_df = None
        chosen_turns = []
        for eid, grp in sub.groupby("event_id", sort=False):
            t_list = compute_turn_metrics_for_attempt(grp)
            if t_list:
                chosen_df = grp
                chosen_turns = t_list
                break
        if chosen_df is None:
            continue

        pid = int(chosen_df["nfl_id"].iloc[0])
        pname = name_map.get(pid, f"ID {pid}")
        x = chosen_df["x"].to_numpy()
        y = chosen_df["y"].to_numpy()
        s = chosen_df["s"].to_numpy()

        ax.plot(x, y, color="gray", alpha=0.45, linewidth=1.5, label="Path")
        sc = ax.scatter(x, y, c=s, cmap="viridis", s=28, zorder=3)

        for idx, tev in enumerate(chosen_turns):
            st, ed = tev["start_frame"], tev["end_frame"]
            ax.plot(
                x[st : ed + 1],
                y[st : ed + 1],
                color="crimson",
                linewidth=3.0,
                zorder=4,
                label="Detected Turn" if idx == 0 else None,
            )
            ax.scatter(
                x[st : ed + 1],
                y[st : ed + 1],
                color="crimson",
                s=50,
                edgecolors="black",
                linewidths=0.5,
                zorder=5,
            )

        mean_csr = np.mean([t["CSR"] for t in chosen_turns])
        ax.set_title(
            f"{dname}\n{pname} ({len(chosen_turns)} turns, CSR={mean_csr:.2f})",
            fontsize=9.5,
            fontweight="bold",
        )
        ax.set_xlabel("x (yards)")
        ax.set_ylabel("y (yards)")
        ax.set_aspect("equal", adjustable="datalim")
        ax.grid(True, alpha=0.3)
        plt.colorbar(sc, ax=ax, label="Speed (yd/s)", fraction=0.046, pad=0.04)

    axes[0, 0].legend(loc="best", fontsize=8)
    fig.suptitle(
        "Phase 2A.3: Turn Detection Validation Across 6 Combine Drills (Red = Detected Turn Window)",
        fontsize=12.5,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


def plot_combine_feature_diagnostics(features_df: pd.DataFrame) -> tuple[Path, Path]:
    """Phase 2C.2: Generate distribution histograms and correlation matrix plots."""
    fig_dir = OUTPUTS_DIR / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # 1. Histograms of the 6 tracking metrics
    dist_path = fig_dir / "phase2c_metric_distributions.png"
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    labels = {
        "CSR": "Cornering Speed Retention (CSR)",
        "PDR": "Peak Deceleration Rate (yd/s/frame)",
        "TRT": "Turn Recovery Time (seconds)",
        "FSE": "First-Step Explosion (yd/s²)",
        "ACS": "Acceleration Curve Shape (early/late)",
        "DJ": "Directional Jerk (deg/s²)",
    }
    colors = ["#1f77b4", "#d62728", "#ff7f0e", "#2ca02c", "#9467bd", "#8c564b"]
    for ax, col, color in zip(axes.flat, TRACKING_METRIC_COLS, colors):
        vals = features_df[col].dropna()
        ax.hist(vals, bins=18, color=color, edgecolor="white", alpha=0.85)
        ax.axvline(vals.median(), color="black", linestyle="--", linewidth=1.5, label=f"Median: {vals.median():.2f}")
        ax.set_title(labels[col], fontsize=10, fontweight="bold")
        ax.set_ylabel("Players")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.25)

    fig.suptitle("Phase 2C.2: Distributions of 6 Tracking-Derived Combine Metrics (N = 118 DL Prospects)", fontsize=12.5, fontweight="bold")
    fig.tight_layout()
    fig.savefig(dist_path, dpi=150)
    plt.close(fig)

    # 2. Correlation matrix heatmap (6 tracking + traditional Combine metrics)
    corr_path = fig_dir / "phase2c_correlation_matrix.png"
    all_cols = TRACKING_METRIC_COLS + TRADITIONAL_METRIC_COLS
    corr_mat = features_df[all_cols].corr()

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(corr_mat.values, cmap="coolwarm", vmin=-0.8, vmax=0.8)
    ax.set_xticks(range(len(all_cols)))
    ax.set_yticks(range(len(all_cols)))
    ax.set_xticklabels(all_cols, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(all_cols, fontsize=9)

    for i in range(len(all_cols)):
        for j in range(len(all_cols)):
            val = corr_mat.values[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=7.5, color="black")

    plt.colorbar(im, ax=ax, label="Pearson r", fraction=0.046, pad=0.04)
    ax.set_title("Phase 2C.2: Tracking Metrics vs. Traditional Combine Metrics Correlation Matrix", fontsize=11.5, fontweight="bold")
    fig.tight_layout()
    fig.savefig(corr_path, dpi=150)
    plt.close(fig)

    return dist_path, corr_path


def build_combine_features(
    roster_df: Optional[pd.DataFrame] = None,
    ct_df: Optional[pd.DataFrame] = None,
    save: bool = True,
) -> pd.DataFrame:
    """Run full Phase 2 pipeline: compute 6 tracking metrics, validate, merge with Combine results, and save."""
    if roster_df is None:
        roster_path = OUTPUTS_DIR / "dl_roster_master.csv"
        roster_df = pd.read_csv(roster_path) if roster_path.exists() else load_players(dl_only=True)

    if ct_df is None:
        ct_df = prepare_combine_tracking(roster_df["nfl_id"])

    # 2A.3 Validation plots
    val_plot_path = validate_turn_detection_plots(ct_df, roster_df)
    print(f"2A.3 Saved turn detection validation plot -> {val_plot_path}")

    # 2B.1, 2B.2, 2B.3, 2B.6 Turn metrics
    player_turns, turns_df = compute_player_turn_metrics(ct_df)
    print(
        f"2B.1-3,6 Extracted {len(turns_df):,d} high-speed turn events across "
        f"{player_turns['nfl_id'].nunique()}/{len(roster_df)} DL players"
    )

    # 2B.4, 2B.5 FSE & ACS
    player_burst = compute_fse_and_acs(ct_df)

    # 2C.1 Assemble 6 tracking metrics
    tracking_df = (
        roster_df[["nfl_id"]]
        .merge(player_turns, on="nfl_id", how="left")
        .merge(player_burst, on="nfl_id", how="left")
    )[["nfl_id"] + TRACKING_METRIC_COLS]

    # Handle any hypothetical edge-case NaNs with cohort median
    for col in TRACKING_METRIC_COLS:
        if tracking_df[col].isna().any():
            tracking_df[col] = tracking_df[col].fillna(tracking_df[col].median())

    # 2C.3 Merge with traditional Combine metrics
    combine_res = load_combine_results(nfl_ids=roster_df["nfl_id"])[
        ["nfl_id"] + TRADITIONAL_METRIC_COLS
    ]
    full_features = combine_res.merge(tracking_df, on="nfl_id", how="right")

    # 2C.2 Quality checks & plots
    null_counts = full_features[TRACKING_METRIC_COLS].isna().sum().to_dict()
    inf_counts = np.isinf(full_features[TRACKING_METRIC_COLS].to_numpy()).sum()
    print(f"2C.2 Quality check — Tracking NaNs: {null_counts}, Inf count: {int(inf_counts)}")
    print("\n2C.2 Summary statistics of 6 tracking metrics:")
    print(full_features[TRACKING_METRIC_COLS].describe().round(3).to_string())

    print("\n2C.2 Inter-correlation of 6 tracking metrics:")
    print(full_features[TRACKING_METRIC_COLS].corr().round(3).to_string())

    print("\n2C.2 Correlation of tracking metrics with traditional Combine metrics:")
    print(
        full_features[TRACKING_METRIC_COLS + TRADITIONAL_METRIC_COLS]
        .corr()
        .loc[TRACKING_METRIC_COLS, TRADITIONAL_METRIC_COLS]
        .round(3)
        .to_string()
    )

    dist_path, corr_path = plot_combine_feature_diagnostics(full_features)
    print(f"\n2C.2 Saved diagnostic plots -> {dist_path}, {corr_path}")

    # 2C.4 Save outputs/dl_combine_features.csv
    if save:
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        out_csv = OUTPUTS_DIR / "dl_combine_features.csv"
        full_features.to_csv(out_csv, index=False)
        print(f"2C.4 Saved Combine feature matrix ({full_features.shape[0]} rows, {full_features.shape[1]} cols) -> {out_csv}")

    return full_features


if __name__ == "__main__":
    build_combine_features()
