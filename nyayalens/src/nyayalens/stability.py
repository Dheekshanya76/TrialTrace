"""Phase 4b: bootstrap stability.

Observed counts are noisy (especially for small heads). We re-draw each head's outcomes
from the observed proportions (multinomial / binomial with the observed totals), re-run
all detectors, and record how often each head is flagged. A head that stays flagged in
>= 80% of re-draws is a stable finding; one that flips is likely small-count noise.
"""
import numpy as np
import pandas as pd
from .detect import logit_matrix, run_detectors


def _resample(a, rng):
    r = a.copy()
    out = np.zeros((len(a), 3))
    for i, row in enumerate(a.itertuples()):
        n = int(row.trials_completed)
        p = np.array([row.convicted, row.discharged, row.acquitted], float) / n
        out[i] = rng.multinomial(n, p)
    r["convicted"], r["discharged"] = out[:, 0], out[:, 1]
    r["pending_end"] = rng.binomial(a.total_for_trial.astype(int), a.pending_end / a.total_for_trial)
    r["disposed_without_trial"] = rng.binomial(a.disposed_by_courts.astype(int),
                                               a.disposed_without_trial / a.disposed_by_courts)
    return r


def bootstrap_flags(a, n_boot=100, contamination=0.10, seed=42, n_trees=100):
    """a: analysis-set frame. Returns per-head flag frequencies."""
    rng = np.random.default_rng(seed)
    counts = np.zeros((len(a), 4))
    for b in range(n_boot):
        res = run_detectors(logit_matrix(_resample(a, rng)), contamination, seed + b, n_trees)
        fz, fi, fl = res["flag_z"], res["flag_if"], res["flag_lof"]
        counts += np.column_stack([fz, fi, fl, (fz.astype(int) + fi + fl) >= 2])
    freq = counts / n_boot
    return pd.DataFrame(freq, columns=["stab_z", "stab_if", "stab_lof", "stab_consensus"], index=a.index)
