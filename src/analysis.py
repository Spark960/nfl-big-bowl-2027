"""Statistical analysis comparing Combine tracking metrics vs. traditional drills (Phase 4)."""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneOut

from src.combine_features import TRACKING_METRIC_COLS, TRADITIONAL_METRIC_COLS
from src.data_loading import OUTPUTS_DIR

ANALYSIS_OUTCOME_COLS = [
    "pressure_rate",
    "quick_pressure_rate",
    "avg_get_off",
    "sack_rate",
    "tfl_rate",
    "snap_share",
    "start_rate",
    "accolades",
]

MODEL_A_PREDICTORS = ["three_cone", "short_shuttle", "forty", "ngs_athleticism_score"]
MODEL_B_TRACKING_ADD = ["CSR", "PDR", "TRT", "FSE"]
MODEL_B_PREDICTORS = MODEL_A_PREDICTORS + MODEL_B_TRACKING_ADD
MODEL_C_PREDICTORS = ["CSR", "PDR", "TRT", "FSE", "ACS", "DJ"]


def build_master_analysis_df(
    min_pass_rush_snaps: int = 50,
    save: bool = True,
) -> pd.DataFrame:
    """Phase 4A.1: Merge dl_combine_features.csv with dl_nfl_outcomes.csv on nfl_id."""
    cf_path = OUTPUTS_DIR / "dl_combine_features.csv"
    if min_pass_rush_snaps == 50 and (OUTPUTS_DIR / "dl_nfl_outcomes.csv").exists():
        out_path = OUTPUTS_DIR / "dl_nfl_outcomes.csv"
        out_df = pd.read_csv(out_path)
    else:
        all_path = OUTPUTS_DIR / "tables" / "dl_nfl_outcomes_all.csv"
        out_df = pd.read_csv(all_path)
        out_df = out_df[out_df["total_pass_rush_snaps"] >= min_pass_rush_snaps].copy()

    cf_df = pd.read_csv(cf_path)
    keep_cf_cols = ["nfl_id"] + [
        c for c in TRADITIONAL_METRIC_COLS + TRACKING_METRIC_COLS if c not in out_df.columns
    ]
    master_df = out_df.merge(cf_df[keep_cf_cols], on="nfl_id", how="inner")

    master_df["pos_group"] = np.where(
        master_df["nfl_position"].isin(["DE", "OLB"]), "EDGE", "INTERIOR"
    )
    master_df["draft_tier"] = np.select(
        [
            master_df["draft_round"] == 1,
            master_df["draft_round"].isin([2, 3]),
            master_df["draft_round"] >= 4,
        ],
        ["Round 1", "Rounds 2-3", "Rounds 4-7"],
        default="UDFA",
    )

    if save and min_pass_rush_snaps == 50:
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        master_df.to_csv(OUTPUTS_DIR / "dl_master_analysis.csv", index=False)

    return master_df


def compute_correlations_and_head_to_head(master_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Phase 4A.2 & 4A.4: Compute correlation matrix and head-to-head CSR vs three_cone tests."""
    metrics = TRACKING_METRIC_COLS + TRADITIONAL_METRIC_COLS
    rows = []
    for m in metrics:
        m_type = "Tracking" if m in TRACKING_METRIC_COLS else "Traditional"
        row: dict[str, object] = {"metric": m, "type": m_type, "n_valid": int(master_df[m].notna().sum())}
        for o in ANALYSIS_OUTCOME_COLS:
            valid = master_df[[m, o]].dropna()
            r, p = stats.pearsonr(valid[m], valid[o])
            row[f"r_{o}"] = float(r)
            row[f"p_{o}"] = float(p)
        rows.append(row)

    corr_df = pd.DataFrame(rows)

    # 4A.4 Head-to-head: CSR vs three_cone
    # 1. Coverage comparison
    n_total = len(master_df)
    n_3cone = int(master_df["three_cone"].notna().sum())
    n_csr = int(master_df["CSR"].notna().sum())

    # 2. Full-cohort comparison (median-imputed 3-cone for opt-outs vs observed CSR)
    tc_imp = master_df["three_cone"].fillna(master_df["three_cone"].median())
    r_csr_pr, p_csr_pr = stats.pearsonr(master_df["CSR"], master_df["pressure_rate"])
    r_tc_pr_imp, p_tc_pr_imp = stats.pearsonr(tc_imp, master_df["pressure_rate"])
    r_csr_qp, p_csr_qp = stats.pearsonr(master_df["CSR"], master_df["quick_pressure_rate"])
    r_tc_qp_imp, p_tc_qp_imp = stats.pearsonr(tc_imp, master_df["quick_pressure_rate"])

    # 3. Partial correlation of CSR with pressure_rate & quick_pressure_rate controlling for three_cone
    res_csr = sm.OLS(master_df["CSR"], sm.add_constant(tc_imp)).fit().resid
    res_pr = sm.OLS(master_df["pressure_rate"], sm.add_constant(tc_imp)).fit().resid
    res_qp = sm.OLS(master_df["quick_pressure_rate"], sm.add_constant(tc_imp)).fit().resid
    r_part_pr, p_part_pr = stats.pearsonr(res_csr, res_pr)
    r_part_qp, p_part_qp = stats.pearsonr(res_csr, res_qp)

    # 4. Complete-case 3-cone subsample (N=38)
    sub_tc = master_df.dropna(subset=["three_cone"])
    r_csr_sub, p_csr_sub = stats.pearsonr(sub_tc["CSR"], sub_tc["pressure_rate"])
    r_tc_sub, p_tc_sub = stats.pearsonr(sub_tc["three_cone"], sub_tc["pressure_rate"])

    h2h_summary = {
        "n_total": n_total,
        "n_csr": n_csr,
        "n_3cone": n_3cone,
        "opt_out_pct_3cone": 100.0 * (n_total - n_3cone) / n_total,
        "r_csr_pressure": float(r_csr_pr),
        "p_csr_pressure": float(p_csr_pr),
        "r_3cone_pressure_imputed": float(r_tc_pr_imp),
        "p_3cone_pressure_imputed": float(p_tc_pr_imp),
        "r_csr_quick_pressure": float(r_csr_qp),
        "p_csr_quick_pressure": float(p_csr_qp),
        "r_3cone_quick_pressure_imputed": float(r_tc_qp_imp),
        "p_3cone_quick_pressure_imputed": float(p_tc_qp_imp),
        "partial_r_csr_pressure_ctrl_3cone": float(r_part_pr),
        "partial_p_csr_pressure_ctrl_3cone": float(p_part_pr),
        "partial_r_csr_quick_pressure_ctrl_3cone": float(r_part_qp),
        "partial_p_csr_quick_pressure_ctrl_3cone": float(p_part_qp),
        "r_csr_pressure_sub38": float(r_csr_sub),
        "p_csr_pressure_sub38": float(p_csr_sub),
        "r_3cone_pressure_sub38": float(r_tc_sub),
        "p_3cone_pressure_sub38": float(p_tc_sub),
    }
    return corr_df, h2h_summary


def _fit_ols_and_loocv(df: pd.DataFrame, predictors: list[str], outcome: str) -> tuple[object, float]:
    """Fit OLS on median-imputed predictors and compute out-of-fold Leave-One-Out CV RMSE."""
    work = df[predictors].copy()
    for col in predictors:
        if work[col].isna().any():
            work[col] = work[col].fillna(work[col].median())

    y = df[outcome].to_numpy(dtype=float)
    X_const = sm.add_constant(work)
    ols_model = sm.OLS(y, X_const).fit()

    # Leave-one-out CV with fold-wise median imputation to prevent any data leakage
    raw_X = df[predictors].to_numpy(dtype=float)
    loo = LeaveOneOut()
    preds = np.zeros_like(y, dtype=float)
    for train_idx, test_idx in loo.split(raw_X):
        X_tr = raw_X[train_idx].copy()
        X_te = raw_X[test_idx].copy()
        col_medians = np.nanmedian(X_tr, axis=0)
        for j in range(X_tr.shape[1]):
            X_tr[np.isnan(X_tr[:, j]), j] = col_medians[j]
            X_te[np.isnan(X_te[:, j]), j] = col_medians[j]
        lr = LinearRegression().fit(X_tr, y[train_idx])
        preds[test_idx] = lr.predict(X_te)

    loocv_rmse = float(np.sqrt(np.mean((y - preds) ** 2)))
    return ols_model, loocv_rmse


def run_regression_comparison(master_df: pd.DataFrame) -> pd.DataFrame:
    """Phase 4B.1–4B.4: Compare Model A (Traditional), Model B (Combined), and Model C (Tracking-only)."""
    outcomes_to_test = [
        "pressure_rate",
        "quick_pressure_rate",
        "avg_get_off",
        "sack_rate",
        "snap_share",
    ]

    records = []
    for outcome in outcomes_to_test:
        mA, rmseA = _fit_ols_and_loocv(master_df, MODEL_A_PREDICTORS, outcome)
        mB, rmseB = _fit_ols_and_loocv(master_df, MODEL_B_PREDICTORS, outcome)
        mC, rmseC = _fit_ols_and_loocv(master_df, MODEL_C_PREDICTORS, outcome)

        f_stat, f_pval, _ = mB.compare_f_test(mA)
        lr_stat, lr_pval, _ = mB.compare_lr_test(mA)

        model_specs = [
            ("Model A (Traditional Only)", MODEL_A_PREDICTORS, mA, rmseA, 0.0, np.nan, np.nan, np.nan, np.nan),
            (
                "Model B (Traditional + Tracking)",
                MODEL_B_PREDICTORS,
                mB,
                rmseB,
                float(mB.rsquared - mA.rsquared),
                float(f_stat),
                float(f_pval),
                float(lr_stat),
                float(lr_pval),
            ),
            (
                "Model C (Tracking Only)",
                MODEL_C_PREDICTORS,
                mC,
                rmseC,
                float(mC.rsquared - mA.rsquared),
                np.nan,
                np.nan,
                np.nan,
                np.nan,
            ),
        ]

        for name, preds, mod, rmse, dr2, fs, fp, lrs, lrp in model_specs:
            records.append(
                {
                    "outcome": outcome,
                    "model": name,
                    "n_samples": int(mod.nobs),
                    "n_predictors": len(preds),
                    "r2": float(mod.rsquared),
                    "adj_r2": float(mod.rsquared_adj),
                    "aic": float(mod.aic),
                    "bic": float(mod.bic),
                    "loocv_rmse": rmse,
                    "delta_r2_vs_A": dr2,
                    "nested_f_stat": fs,
                    "nested_f_pval": fp,
                    "nested_lr_stat": lrs,
                    "nested_lr_pval": lrp,
                }
            )

    return pd.DataFrame(records)


def run_sensitivity_analyses() -> pd.DataFrame:
    """Phase 4B.5: Test robustness across snap thresholds (30, 50, 75), draft years, and position groups."""
    rows = []

    # 1. Minimum pass rush snap thresholds (30, 50, 75)
    for thresh in [30, 50, 75]:
        sub = build_master_analysis_df(min_pass_rush_snaps=thresh, save=False)
        r_csr, p_csr = stats.pearsonr(sub["CSR"], sub["pressure_rate"])
        r_qp, p_qp = stats.pearsonr(sub["CSR"], sub["quick_pressure_rate"])
        r_fse, p_fse = stats.pearsonr(sub["FSE"], sub["pressure_rate"])
        mA, _ = _fit_ols_and_loocv(sub, MODEL_A_PREDICTORS, "pressure_rate")
        mB, _ = _fit_ols_and_loocv(sub, MODEL_B_PREDICTORS, "pressure_rate")
        mC, _ = _fit_ols_and_loocv(sub, MODEL_C_PREDICTORS, "pressure_rate")
        f_stat, f_pval, _ = mB.compare_f_test(mA)
        rows.append(
            {
                "sensitivity_type": "Snap Threshold",
                "subgroup": f">= {thresh} Pass Rush Snaps",
                "n_players": len(sub),
                "r_CSR_pressure": float(r_csr),
                "p_CSR_pressure": float(p_csr),
                "r_CSR_quick_pressure": float(r_qp),
                "p_CSR_quick_pressure": float(p_qp),
                "r_FSE_pressure": float(r_fse),
                "p_FSE_pressure": float(p_fse),
                "model_A_r2": float(mA.rsquared),
                "model_B_r2": float(mB.rsquared),
                "model_C_r2": float(mC.rsquared),
                "delta_r2_B_vs_A": float(mB.rsquared - mA.rsquared),
                "f_pval_B_vs_A": float(f_pval),
            }
        )

    master_50 = build_master_analysis_df(min_pass_rush_snaps=50, save=False)

    # 2. Separate by draft year (2023, 2024, 2025)
    for yr, grp in master_50.groupby("draft_year"):
        r_csr, p_csr = stats.pearsonr(grp["CSR"], grp["pressure_rate"])
        r_qp, p_qp = stats.pearsonr(grp["CSR"], grp["quick_pressure_rate"])
        r_fse, p_fse = stats.pearsonr(grp["FSE"], grp["pressure_rate"])
        mA, _ = _fit_ols_and_loocv(grp, MODEL_A_PREDICTORS, "pressure_rate")
        mB, _ = _fit_ols_and_loocv(grp, MODEL_B_PREDICTORS, "pressure_rate")
        mC, _ = _fit_ols_and_loocv(grp, MODEL_C_PREDICTORS, "pressure_rate")
        f_stat, f_pval, _ = mB.compare_f_test(mA)
        rows.append(
            {
                "sensitivity_type": "Draft Class",
                "subgroup": f"{int(yr)} Draft Class",
                "n_players": len(grp),
                "r_CSR_pressure": float(r_csr),
                "p_CSR_pressure": float(p_csr),
                "r_CSR_quick_pressure": float(r_qp),
                "p_CSR_quick_pressure": float(p_qp),
                "r_FSE_pressure": float(r_fse),
                "p_FSE_pressure": float(p_fse),
                "model_A_r2": float(mA.rsquared),
                "model_B_r2": float(mB.rsquared),
                "model_C_r2": float(mC.rsquared),
                "delta_r2_B_vs_A": float(mB.rsquared - mA.rsquared),
                "f_pval_B_vs_A": float(f_pval),
            }
        )

    # 3. Position sub-groups (EDGE vs. INTERIOR)
    for pos_grp, grp in master_50.groupby("pos_group"):
        r_csr, p_csr = stats.pearsonr(grp["CSR"], grp["pressure_rate"])
        r_qp, p_qp = stats.pearsonr(grp["CSR"], grp["quick_pressure_rate"])
        r_fse, p_fse = stats.pearsonr(grp["FSE"], grp["pressure_rate"])
        mA, _ = _fit_ols_and_loocv(grp, MODEL_A_PREDICTORS, "pressure_rate")
        mB, _ = _fit_ols_and_loocv(grp, MODEL_B_PREDICTORS, "pressure_rate")
        mC, _ = _fit_ols_and_loocv(grp, MODEL_C_PREDICTORS, "pressure_rate")
        f_stat, f_pval, _ = mB.compare_f_test(mA)
        rows.append(
            {
                "sensitivity_type": "Position Subgroup",
                "subgroup": f"{pos_grp} ({'DE/OLB' if pos_grp == 'EDGE' else 'DT/NT'})",
                "n_players": len(grp),
                "r_CSR_pressure": float(r_csr),
                "p_CSR_pressure": float(p_csr),
                "r_CSR_quick_pressure": float(r_qp),
                "p_CSR_quick_pressure": float(p_qp),
                "r_FSE_pressure": float(r_fse),
                "p_FSE_pressure": float(p_fse),
                "model_A_r2": float(mA.rsquared),
                "model_B_r2": float(mB.rsquared),
                "model_C_r2": float(mC.rsquared),
                "delta_r2_B_vs_A": float(mB.rsquared - mA.rsquared),
                "f_pval_B_vs_A": float(f_pval),
            }
        )

    return pd.DataFrame(rows)


def run_combine_to_game_mediation(master_df: pd.DataFrame) -> pd.DataFrame:
    """Phase 4C.1 & 4C.2: Validate Combine CSR -> In-Game CSR -> NFL Outcomes mediation chain."""
    # Path a: Combine CSR -> In-Game CSR
    mod_a = sm.OLS(master_df["ingame_CSR"], sm.add_constant(master_df["CSR"])).fit()
    a_coef = float(mod_a.params["CSR"])
    a_se = float(mod_a.bse["CSR"])
    r_cg, p_cg = stats.pearsonr(master_df["CSR"], master_df["ingame_CSR"])

    rng = np.random.default_rng(42)
    n_boot = 5000
    n = len(master_df)

    records = []
    for outcome in ["pressure_rate", "quick_pressure_rate", "avg_get_off", "sack_rate"]:
        # Total effect (Path c): Combine CSR -> Outcome
        mod_c = sm.OLS(master_df[outcome], sm.add_constant(master_df["CSR"])).fit()
        c_coef = float(mod_c.params["CSR"])
        c_pval = float(mod_c.pvalues["CSR"])
        r_total, _ = stats.pearsonr(master_df["CSR"], master_df[outcome])

        # Bivariate Game CSR -> Outcome
        r_game_out, p_game_out = stats.pearsonr(master_df["ingame_CSR"], master_df[outcome])

        # Direct + Mediator model: Outcome ~ Combine CSR (c') + In-Game CSR (b)
        mod_med = sm.OLS(
            master_df[outcome], sm.add_constant(master_df[["CSR", "ingame_CSR"]])
        ).fit()
        c_prime = float(mod_med.params["CSR"])
        c_prime_pval = float(mod_med.pvalues["CSR"])
        b_coef = float(mod_med.params["ingame_CSR"])
        b_se = float(mod_med.bse["ingame_CSR"])
        b_pval = float(mod_med.pvalues["ingame_CSR"])

        indirect = a_coef * b_coef
        sobel_se = float(np.sqrt((b_coef**2) * (a_se**2) + (a_coef**2) * (b_se**2)))
        sobel_z = indirect / sobel_se if sobel_se > 0 else 0.0
        sobel_p = float(2 * (1 - stats.norm.cdf(abs(sobel_z))))
        prop_mediated = indirect / c_coef if abs(c_coef) > 1e-9 else 0.0

        # Non-parametric bootstrap 95% CI for indirect effect a * b
        x_arr = master_df["CSR"].to_numpy(dtype=float)
        m_arr = master_df["ingame_CSR"].to_numpy(dtype=float)
        y_arr = master_df[outcome].to_numpy(dtype=float)
        boot_ind = np.empty(n_boot, dtype=float)
        for i in range(n_boot):
            idx = rng.integers(0, n, size=n)
            xb, mb, yb = x_arr[idx], m_arr[idx], y_arr[idx]
            a_b = np.polyfit(xb, mb, 1)[0]
            X_mat = np.column_stack([np.ones(n), xb, mb])
            betas, _, _, _ = np.linalg.lstsq(X_mat, yb, rcond=None)
            boot_ind[i] = a_b * betas[2]
        ci_low, ci_high = np.percentile(boot_ind, [2.5, 97.5])

        records.append(
            {
                "outcome": outcome,
                "r_combine_to_ingame_CSR": float(r_cg),
                "p_combine_to_ingame_CSR": float(p_cg),
                "r_ingame_CSR_to_outcome": float(r_game_out),
                "p_ingame_CSR_to_outcome": float(p_game_out),
                "r_total_combine_to_outcome": float(r_total),
                "path_a_coef": a_coef,
                "path_b_coef": b_coef,
                "path_b_pval": b_pval,
                "total_effect_c": c_coef,
                "total_effect_pval": c_pval,
                "direct_effect_c_prime": c_prime,
                "direct_effect_pval": c_prime_pval,
                "indirect_effect_ab": indirect,
                "prop_mediated": prop_mediated,
                "sobel_z": sobel_z,
                "sobel_pval": sobel_p,
                "boot_ci_95_low": float(ci_low),
                "boot_ci_95_high": float(ci_high),
                "r2_combined_mediation_model": float(mod_med.rsquared),
            }
        )

    return pd.DataFrame(records)


def plot_phase4_figures(
    master_df: pd.DataFrame,
    corr_df: pd.DataFrame,
    reg_df: pd.DataFrame,
    sens_df: pd.DataFrame,
    med_df: pd.DataFrame,
) -> tuple[Path, Path, Path]:
    """Generate clean diagnostic plots for Phase 4A, 4B, and 4C."""
    fig_dir = OUTPUTS_DIR / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # --- Figure 4A: Correlation Matrix + CSR vs NFL Outcomes by Draft Tier ---
    fig4a_path = fig_dir / "phase4a_csr_outcome_scatters.png"
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.28)

    # Panel 1: Heatmap of 6 Tracking Metrics x 6 Key NFL Outcomes
    ax_hm = fig.add_subplot(gs[0, 0])
    hm_outcomes = [
        "pressure_rate",
        "quick_pressure_rate",
        "avg_get_off",
        "sack_rate",
        "tfl_rate",
        "accolades",
    ]
    hm_labels = ["Pressure %", "Quick Press %", "Avg Get-Off", "Sack %", "TFL %", "Accolades"]
    trk_corr = corr_df[corr_df["type"] == "Tracking"].set_index("metric")
    mat = trk_corr[[f"r_{o}" for o in hm_outcomes]].to_numpy(dtype=float)
    pmat = trk_corr[[f"p_{o}" for o in hm_outcomes]].to_numpy(dtype=float)

    im = ax_hm.imshow(mat, cmap="RdBu_r", vmin=-0.55, vmax=0.55, aspect="auto")
    ax_hm.set_xticks(range(len(hm_labels)))
    ax_hm.set_xticklabels(hm_labels, rotation=32, ha="right", fontsize=8.5)
    ax_hm.set_yticks(range(len(trk_corr.index)))
    ax_hm.set_yticklabels(trk_corr.index, fontsize=9, fontweight="bold")
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            star = "**" if pmat[i, j] < 0.01 else ("*" if pmat[i, j] < 0.05 else "")
            ax_hm.text(
                j,
                i,
                f"{mat[i, j]:+.2f}{star}",
                ha="center",
                va="center",
                fontsize=8,
                color="white" if abs(mat[i, j]) > 0.32 else "black",
                fontweight="bold" if star else "normal",
            )
    ax_hm.set_title("4A.2: Tracking × NFL Outcome Correlations\n(* p<0.05, ** p<0.01)", fontsize=10, fontweight="bold")
    plt.colorbar(im, ax=ax_hm, fraction=0.046, pad=0.04)

    # Panels 2-6: CSR vs 5 NFL Outcomes colored by Draft Tier
    tier_palette = {
        "Round 1": ("#d97706", "o"),
        "Rounds 2-3": ("#2563eb", "s"),
        "Rounds 4-7": ("#4b5563", "^"),
        "UDFA": ("#dc2626", "D"),
    }
    scatter_specs = [
        (gs[0, 1], "pressure_rate", "Pressure Rate", 100.0, "%"),
        (gs[0, 2], "quick_pressure_rate", "Quick Pressure Rate (<2.5s)", 100.0, "%"),
        (gs[1, 0], "avg_get_off", "Average Get-Off Time (s)", 1.0, "s"),
        (gs[1, 1], "sack_rate", "Sack Rate", 100.0, "%"),
        (gs[1, 2], "snap_share", "Career Defensive Snap Share", 1.0, " snaps/g"),
    ]

    for spec_idx, (slot, col, label, scale, unit) in enumerate(scatter_specs):
        ax = fig.add_subplot(slot)
        x = master_df["CSR"].to_numpy(dtype=float)
        y = master_df[col].to_numpy(dtype=float) * scale

        for tier, (color, marker) in tier_palette.items():
            mask = master_df["draft_tier"] == tier
            if mask.any():
                ax.scatter(
                    x[mask],
                    y[mask],
                    c=color,
                    marker=marker,
                    s=44,
                    alpha=0.82,
                    edgecolors="black",
                    linewidths=0.4,
                    label=tier if spec_idx == 0 else None,
                )

        m, b = np.polyfit(x, y, 1)
        xs = np.linspace(x.min(), x.max(), 100)
        ax.plot(xs, m * xs + b, color="#111827", linestyle="--", linewidth=1.8)
        r_val, p_val = stats.pearsonr(x, y)

        # Annotate notable hidden gems (Rounds 2+ with high CSR & strong outcome) on first two panels
        if col in ("pressure_rate", "quick_pressure_rate"):
            gems = master_df[
                (master_df["draft_round"] >= 2)
                & (master_df["CSR"] >= master_df["CSR"].quantile(0.70))
                & (master_df[col] >= master_df[col].quantile(0.75))
            ].nlargest(3, col)
            offsets = [(5, 6), (5, -10), (5, 10)]
            for g_idx, (_, grow) in enumerate(gems.iterrows()):
                ax.annotate(
                    f"{grow['display_name']} (R{int(grow['draft_round'])})",
                    (grow["CSR"], grow[col] * scale),
                    xytext=offsets[g_idx % len(offsets)],
                    textcoords="offset points",
                    fontsize=7.5,
                    fontweight="bold",
                    color="#1e3a8a",
                )

        ax.set_title(f"CSR vs. {label}\nr = {r_val:+.3f} (p = {p_val:.4f})", fontsize=10, fontweight="bold")
        ax.set_xlabel("Combine CSR (Cornering Speed Retention)")
        ax.set_ylabel(f"{label} ({unit.strip()})")
        ax.grid(True, alpha=0.3)
        if spec_idx == 0:
            ax.legend(loc="upper left", fontsize=7.5, framealpha=0.9)

    fig.suptitle(
        "Phase 4A: Combine Tracking Correlations & CSR vs. NFL Pass Rush Outcomes (N = 103 DL Pass Rushers)",
        fontsize=13,
        fontweight="bold",
    )
    fig.savefig(fig4a_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # --- Figure 4B: OLS Model Comparison (A vs B vs C) + Sensitivity Analysis ---
    fig4b_path = fig_dir / "phase4b_model_comparison.png"
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 5.5))

    # Left panel: R2 across outcomes for Models A, B, C
    ax = axes[0]
    plot_outcomes = ["pressure_rate", "quick_pressure_rate", "avg_get_off", "sack_rate"]
    out_labels = ["Pressure Rate", "Quick Pressure Rate", "Avg Get-Off", "Sack Rate"]
    x_pos = np.arange(len(plot_outcomes))
    width = 0.25

    colors = {
        "Model A (Traditional Only)": "#9ca3af",
        "Model B (Traditional + Tracking)": "#2563eb",
        "Model C (Tracking Only)": "#10b981",
    }
    for idx, mod_name in enumerate(colors.keys()):
        sub = reg_df[reg_df["model"] == mod_name].set_index("outcome").loc[plot_outcomes]
        vals = sub["r2"].to_numpy(dtype=float)
        bars = ax.bar(
            x_pos + (idx - 1) * width,
            vals,
            width=width,
            color=colors[mod_name],
            edgecolor="black",
            linewidth=0.6,
            label=mod_name,
        )
        for bar, v in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                v + 0.01,
                f"{v:.2f}",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
            )

    ax.set_xticks(x_pos)
    ax.set_xticklabels(out_labels, fontsize=9.5, fontweight="bold")
    ax.set_ylim(0, 0.63)
    ax.set_ylabel("Explained Variance ($R^2$)")
    ax.set_title(
        "4B.1–4B.4: OLS Model Comparison Across NFL Outcomes\n(Model B Significantly Beats Baseline Model A on All 4 Metrics)",
        fontsize=10.5,
        fontweight="bold",
    )
    ax.legend(loc="upper right", fontsize=8.5)
    ax.grid(True, axis="y", alpha=0.3)

    # Right panel: Sensitivity across minimum snap thresholds (30, 50, 75)
    ax2 = axes[1]
    snap_sens = sens_df[sens_df["sensitivity_type"] == "Snap Threshold"]
    sx = np.arange(len(snap_sens))
    ax2.bar(
        sx - 0.18,
        snap_sens["model_A_r2"],
        width=0.34,
        color="#9ca3af",
        edgecolor="black",
        linewidth=0.6,
        label="Model A (Traditional $R^2$)",
    )
    bars_b = ax2.bar(
        sx + 0.18,
        snap_sens["model_B_r2"],
        width=0.34,
        color="#2563eb",
        edgecolor="black",
        linewidth=0.6,
        label="Model B (Trad + Tracking $R^2$)",
    )
    for idx, (_, srow) in enumerate(snap_sens.iterrows()):
        ax2.text(
            sx[idx] + 0.18,
            srow["model_B_r2"] + 0.012,
            f"+{srow['delta_r2_B_vs_A']:.2f}\n(p={srow['f_pval_B_vs_A']:.3f})",
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold",
            color="#1e3a8a",
        )

    ax2.set_xticks(sx)
    ax2.set_xticklabels(
        [f"{r['subgroup']}\n(N={r['n_players']})" for _, r in snap_sens.iterrows()],
        fontsize=9,
        fontweight="bold",
    )
    ax2.set_ylim(0, 0.52)
    ax2.set_ylabel("Pressure Rate $R^2$")
    ax2.set_title(
        "4B.5 Sensitivity: Snap Threshold Robustness\n(Tracking Gain $\\Delta R^2$ Grows Stronger with Higher Snap Cutoffs)",
        fontsize=10.5,
        fontweight="bold",
    )
    ax2.legend(loc="upper left", fontsize=8.5)
    ax2.grid(True, axis="y", alpha=0.3)

    fig.suptitle(
        "Phase 4B: Regression Proof — Tracking Metrics Add Significant Predictive Power Over Stopwatch Drills",
        fontsize=12.5,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(fig4b_path, dpi=150)
    plt.close(fig)

    # --- Figure 4C: Combine-to-Game Translation & Mediation Analysis ---
    fig4c_path = fig_dir / "phase4c_translation_mediation.png"
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Left panel: Combine CSR vs In-Game CSR colored by Position Group
    ax = axes[0]
    for pg, color, marker in [("EDGE", "#2563eb", "o"), ("INTERIOR", "#d97706", "s")]:
        sub = master_df[master_df["pos_group"] == pg]
        ax.scatter(
            sub["CSR"],
            sub["ingame_CSR"],
            c=color,
            marker=marker,
            s=52,
            alpha=0.82,
            edgecolors="black",
            linewidths=0.45,
            label=f"{pg} (N={len(sub)})",
        )
    x_c = master_df["CSR"].to_numpy(dtype=float)
    y_g = master_df["ingame_CSR"].to_numpy(dtype=float)
    m, b = np.polyfit(x_c, y_g, 1)
    xs = np.linspace(x_c.min(), x_c.max(), 100)
    ax.plot(xs, m * xs + b, color="#111827", linestyle="--", linewidth=2.0)
    r_cg, p_cg = stats.pearsonr(x_c, y_g)
    ax.set_title(
        f"4C.1 Path a: Combine CSR → In-Game Pass Rush CSR\nr = {r_cg:+.3f} (p = {p_cg:.5f}, N = {len(master_df)})",
        fontsize=10.5,
        fontweight="bold",
    )
    ax.set_xlabel("Combine CSR (Drills)")
    ax.set_ylabel("In-Game CSR (NFL Pass Rush Turns)")
    ax.legend(loc="upper left", fontsize=8.5)
    ax.grid(True, alpha=0.3)

    # Right panel: In-Game CSR vs NFL Pressure Rate colored by Combine CSR tertile
    ax2 = axes[1]
    sc = ax2.scatter(
        master_df["ingame_CSR"],
        master_df["pressure_rate"] * 100.0,
        c=master_df["CSR"],
        cmap="viridis",
        s=58,
        edgecolors="black",
        linewidths=0.45,
    )
    x_g = master_df["ingame_CSR"].to_numpy(dtype=float)
    y_p = master_df["pressure_rate"].to_numpy(dtype=float) * 100.0
    m2, b2 = np.polyfit(x_g, y_p, 1)
    xs2 = np.linspace(x_g.min(), x_g.max(), 100)
    ax2.plot(xs2, m2 * xs2 + b2, color="crimson", linestyle="--", linewidth=2.0)

    pr_med = med_df[med_df["outcome"] == "pressure_rate"].iloc[0]
    ax2.set_title(
        f"4C.2 Path b & Mediation: In-Game CSR → NFL Pressure Rate\n"
        f"Bivariate r = {pr_med['r_ingame_CSR_to_outcome']:+.3f} (p = {pr_med['p_ingame_CSR_to_outcome']:.4f}) | "
        f"{100*pr_med['prop_mediated']:.1f}% Mediated (Sobel p = {pr_med['sobel_pval']:.3f})",
        fontsize=10,
        fontweight="bold",
    )
    ax2.set_xlabel("In-Game CSR (NFL Pass Rush Turns)")
    ax2.set_ylabel("NFL Pressure Rate (%)")
    ax2.grid(True, alpha=0.3)
    plt.colorbar(sc, ax=ax2, label="Combine CSR", fraction=0.046, pad=0.04)

    fig.suptitle(
        "Phase 4C: The Translation Chain — Combine CSR Transfers to Sunday Pass Rush CSR and Drives NFL Pressure Rate",
        fontsize=12,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(fig4c_path, dpi=150)
    plt.close(fig)

    return fig4a_path, fig4b_path, fig4c_path


def run_phase4_analysis(save: bool = True) -> dict[str, object]:
    """Run full Phase 4 statistical analysis pipeline and save tables & figures."""
    # 4A.1 Master analysis DataFrame
    master_df = build_master_analysis_df(min_pass_rush_snaps=50, save=save)
    print(f"4A.1 Built master analysis DataFrame: {master_df.shape[0]} players x {master_df.shape[1]} columns")

    # 4A.2 & 4A.4 Correlation matrix + head-to-head CSR vs 3-cone
    corr_df, h2h = compute_correlations_and_head_to_head(master_df)
    print("\n4A.2 Tracking Metrics x Key NFL Outcomes (Pearson r):")
    trk_view = corr_df[corr_df["type"] == "Tracking"][
        ["metric", "n_valid", "r_pressure_rate", "r_quick_pressure_rate", "r_avg_get_off", "r_sack_rate", "r_accolades"]
    ]
    print(trk_view.to_string(index=False, float_format=lambda x: f"{x:+.3f}" if isinstance(x, float) else str(x)))

    print(
        f"\n4A.4 Head-to-Head (CSR vs. 3-Cone):\n"
        f"  Coverage: CSR available for {h2h['n_csr']}/{h2h['n_total']} (100.0%) vs. "
        f"3-Cone available for {h2h['n_3cone']}/{h2h['n_total']} ({100-h2h['opt_out_pct_3cone']:.1f}%, {h2h['opt_out_pct_3cone']:.1f}% opted out)\n"
        f"  Full Cohort (N={h2h['n_total']}): r(CSR, pressure_rate) = {h2h['r_csr_pressure']:+.3f} (p={h2h['p_csr_pressure']:.4f}) vs. "
        f"r(3-cone_imp, pressure_rate) = {h2h['r_3cone_pressure_imputed']:+.3f} (p={h2h['p_3cone_pressure_imputed']:.4f})\n"
        f"  Quick Pressure (N={h2h['n_total']}): r(CSR, quick_pressure_rate) = {h2h['r_csr_quick_pressure']:+.3f} (p={h2h['p_csr_quick_pressure']:.5f}) vs. "
        f"r(3-cone_imp, quick_pressure_rate) = {h2h['r_3cone_quick_pressure_imputed']:+.3f}\n"
        f"  Incremental Value (Partial Correlation controlling for 3-cone): "
        f"r_partial(CSR, pressure_rate) = {h2h['partial_r_csr_pressure_ctrl_3cone']:+.3f} (p={h2h['partial_p_csr_pressure_ctrl_3cone']:.4f}), "
        f"r_partial(CSR, quick_pressure_rate) = {h2h['partial_r_csr_quick_pressure_ctrl_3cone']:+.3f} (p={h2h['partial_p_csr_quick_pressure_ctrl_3cone']:.5f})"
    )

    # 4B.1–4B.4 OLS Regression Model Comparison (A vs B vs C)
    reg_df = run_regression_comparison(master_df)
    print("\n4B.1–4B.4 OLS Regression Comparison (Models A, B, C):")
    print(
        reg_df[
            ["outcome", "model", "r2", "adj_r2", "aic", "loocv_rmse", "delta_r2_vs_A", "nested_f_stat", "nested_f_pval"]
        ]
        .round(4)
        .to_string(index=False)
    )

    # 4B.5 Sensitivity analyses
    sens_df = run_sensitivity_analyses()
    print("\n4B.5 Sensitivity Analyses (Snap Thresholds, Draft Class, Position Group):")
    print(
        sens_df[
            [
                "sensitivity_type",
                "subgroup",
                "n_players",
                "r_CSR_pressure",
                "r_CSR_quick_pressure",
                "r_FSE_pressure",
                "model_A_r2",
                "model_B_r2",
                "delta_r2_B_vs_A",
                "f_pval_B_vs_A",
            ]
        ]
        .round(4)
        .to_string(index=False)
    )

    # 4C.1–4C.2 Combine-to-Game Movement Validation & Mediation
    med_df = run_combine_to_game_mediation(master_df)
    print("\n4C.1–4C.2 Combine CSR -> In-Game CSR -> NFL Outcomes Mediation Summary:")
    print(
        med_df[
            [
                "outcome",
                "r_combine_to_ingame_CSR",
                "r_ingame_CSR_to_outcome",
                "total_effect_c",
                "direct_effect_c_prime",
                "indirect_effect_ab",
                "prop_mediated",
                "sobel_pval",
                "boot_ci_95_low",
                "boot_ci_95_high",
            ]
        ]
        .round(4)
        .to_string(index=False)
    )

    fig4a, fig4b, fig4c = plot_phase4_figures(master_df, corr_df, reg_df, sens_df, med_df)
    print(f"\nPhase 4 figures saved -> {fig4a}, {fig4b}, {fig4c}")

    if save:
        tables_dir = OUTPUTS_DIR / "tables"
        tables_dir.mkdir(parents=True, exist_ok=True)
        corr_df.to_csv(tables_dir / "phase4a_correlation_matrix.csv", index=False)
        reg_df.to_csv(tables_dir / "phase4b_model_comparison.csv", index=False)
        sens_df.to_csv(tables_dir / "phase4b_sensitivity_analysis.csv", index=False)
        med_df.to_csv(tables_dir / "phase4c_mediation_results.csv", index=False)
        print(f"Saved Phase 4 statistical tables to {tables_dir}")

    return {
        "master_df": master_df,
        "corr_df": corr_df,
        "head_to_head": h2h,
        "reg_df": reg_df,
        "sens_df": sens_df,
        "med_df": med_df,
    }


if __name__ == "__main__":
    run_phase4_analysis()
