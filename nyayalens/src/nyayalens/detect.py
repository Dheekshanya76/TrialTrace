"""Phase 3: anomaly detection.

Main method: robust z-score (median / MAD) on logit-transformed rates.
Comparison methods: Isolation Forest and Local Outlier Factor.
All three see the same standardised feature matrix, so they are comparable.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from .features import FEATS, FEATURE_SPEC

Z_THRESHOLD = 3.5        # Iglewicz & Hoaglin modified z-score cut-off
CLIP = 8.0               # limit extreme z for the distance/tree based models


def logit_matrix(d):
    """Logit of each rate with a +0.5 continuity correction (handles 0% and 100%)."""
    cols = []
    for f in FEATS:
        num, den, _ = FEATURE_SPEC[f]
        p = (d[num].to_numpy(float) + 0.5) / (d[den].to_numpy(float) + 1.0)
        cols.append(np.log(p / (1 - p)))
    return np.column_stack(cols)


def robust_z(X):
    """Modified z-score per column: 0.6745 * (x - median) / MAD."""
    med = np.median(X, axis=0)
    mad = np.median(np.abs(X - med), axis=0)
    scale = np.where(mad > 0, mad / 0.6745, X.std(axis=0) + 1e-9)
    return (X - med) / scale


def run_detectors(X, contamination=0.10, seed=42, n_estimators=500):
    """Run the three detectors on logit matrix X. Returns a dict of arrays."""
    Z = robust_z(X)
    Zc = np.clip(Z, -CLIP, CLIP)
    n = len(X)
    iso = IsolationForest(n_estimators=n_estimators, contamination=contamination, random_state=seed)
    f_if = iso.fit_predict(Zc) == -1
    s_if = -iso.score_samples(Zc)
    lof = LocalOutlierFactor(n_neighbors=min(10, n - 1), contamination=contamination)
    f_lof = lof.fit_predict(Zc) == -1
    s_lof = -lof.negative_outlier_factor_
    zmax = np.abs(Z).max(axis=1)
    return {"z": Z, "z_max": zmax, "flag_z": zmax >= Z_THRESHOLD,
            "if_score": s_if, "flag_if": f_if, "lof_score": s_lof, "flag_lof": f_lof}


def detect(features, contamination=0.10, seed=42):
    """Run detection on the analysis set; returns the analysis-set frame with results."""
    a = features[features.analysis_set].copy().reset_index(drop=True)
    res = run_detectors(logit_matrix(a), contamination, seed)
    for i, f in enumerate(FEATS):
        a[f"z_{f}"] = res["z"][:, i]
    for k in ("z_max", "flag_z", "if_score", "flag_if", "lof_score", "flag_lof"):
        a[k] = res[k]
    a["n_methods"] = a[["flag_z", "flag_if", "flag_lof"]].sum(axis=1)
    return a


def sensitivity(features, levels=(0.05, 0.10, 0.15), seed=42):
    """How many heads each method flags at different contamination levels,
    and how much Isolation Forest / LOF agree with the robust z-score."""
    a = features[features.analysis_set].reset_index(drop=True)
    X = logit_matrix(a)
    rows = []
    for c in levels:
        r = run_detectors(X, c, seed)
        rows.append({"contamination": c, "flagged_robust_z": int(r["flag_z"].sum()),
                     "flagged_isolation_forest": int(r["flag_if"].sum()),
                     "flagged_lof": int(r["flag_lof"].sum()),
                     "if_and_z": int((r["flag_if"] & r["flag_z"]).sum()),
                     "lof_and_z": int((r["flag_lof"] & r["flag_z"]).sum()),
                     "if_and_lof": int((r["flag_if"] & r["flag_lof"]).sum())})
    return pd.DataFrame(rows)
