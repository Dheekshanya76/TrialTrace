"""Phase 2: outcome rates with Wilson confidence intervals.

Only 'detail' rows are analysed (never parents/subtotals), so nothing is double counted.
A head is 'reliable' when at least MIN_TRIALS trials were completed; heads below that
are reported as 'insufficient data' and never flagged.
"""
import numpy as np
import pandas as pd

MIN_TRIALS = 30

# feature -> (numerator column, denominator column, readable label)
FEATURE_SPEC = {
    "conviction_rate": ("convicted", "trials_completed", "conviction rate"),
    "discharge_share": ("discharged", "trials_completed", "discharge share"),
    "pendency_rate": ("pending_end", "total_for_trial", "pendency rate"),
    "without_trial_share": ("disposed_without_trial", "disposed_by_courts", "share of cases ended without trial"),
}
FEATS = list(FEATURE_SPEC)


def wilson_ci(k, n, z=1.96):
    """Wilson score interval for a proportion k/n (vectorised). NaN where n = 0."""
    k, n = np.asarray(k, float), np.asarray(n, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        p = k / n
        denom = 1 + z**2 / n
        centre = (p + z**2 / (2 * n)) / denom
        half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
        lo, hi = np.clip(centre - half, 0, 1), np.clip(centre + half, 0, 1)
    return np.where(n > 0, lo, np.nan), np.where(n > 0, hi, np.nan)


def build_features(df):
    """Return one row per detail crime head with rates, CIs and an analysis_set flag."""
    d = df[df.row_type == "detail"].copy().reset_index(drop=True)
    for f, (num, den, _) in FEATURE_SPEC.items():
        with np.errstate(divide="ignore", invalid="ignore"):
            d[f] = np.where(d[den] > 0, d[num] / d[den], np.nan)
        d[f + "_lo"], d[f + "_hi"] = wilson_ci(d[num], d[den])
    with np.errstate(divide="ignore", invalid="ignore"):
        d["compound_withdraw_share"] = np.where(
            d.disposed_by_courts > 0, (d.compounded + d.withdrawn) / d.disposed_by_courts, np.nan)
    d["analysis_set"] = d.trials_completed >= MIN_TRIALS
    d["status"] = np.where(d.analysis_set, "analysed", "insufficient data")
    return d
