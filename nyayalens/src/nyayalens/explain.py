"""Phase 4a: plain-English explanations and final tiers."""
import numpy as np
import pandas as pd
from .features import FEATS, FEATURE_SPEC

DRIVER_Z = 2.0   # a feature is called out when |z| >= 2


def peer_medians(a):
    return {f: float(np.nanmedian(a[f])) for f in FEATS}


def _pct(x):
    return f"{x * 100:.0f}%" if x >= 0.995 or x < 0.0005 or x >= 0.1 else f"{x * 100:.1f}%"


def top_drivers(row, k=2):
    zs = {f: row[f"z_{f}"] for f in FEATS}
    return [f for f in sorted(zs, key=lambda f: -abs(zs[f]))[:k] if abs(zs[f]) >= DRIVER_Z]


def explain_row(row, med):
    drivers = top_drivers(row)
    n = int(row.trials_completed)
    if not drivers:
        return f"No feature deviates strongly from peers (based on {n:,} completed trials)."
    parts = []
    for f in drivers:
        label = FEATURE_SPEC[f][2]
        z, v = row[f"z_{f}"], row[f]
        word = "far " if abs(z) >= 3.5 else ""
        direction = "above" if z > 0 else "below"
        clear = not (row[f + "_lo"] <= med[f] <= row[f + "_hi"])
        parts.append(f"{label} is {_pct(v)} (95% CI {_pct(row[f + '_lo'])} to {_pct(row[f + '_hi'])}), "
                     f"{word}{direction} the peer median of {_pct(med[f])}"
                     + ("" if clear else "; interval overlaps the median"))
    return "; ".join(parts) + f". Based on {n:,} completed trials."


def add_explanations(a):
    med = peer_medians(a)
    a = a.copy()
    a["main_driver"] = [(top_drivers(r, 1) or [None])[0] for _, r in a.iterrows()]
    a["ci_clear"] = [
        isinstance(d, str) and not (r[d + "_lo"] <= med[d] <= r[d + "_hi"])
        for d, (_, r) in zip(a.main_driver, a.iterrows())]
    a["explanation"] = [explain_row(r, med) for _, r in a.iterrows()]
    return a


def assign_tier(a):
    """Strong: >=2 methods agree, stable in >=80% of re-draws, and the main driver's CI clears the median.
    Moderate: >=2 methods agree, stable in 50-80%, or robust z flagged and stable >=80%.
    Watch: flagged by one method. Typical: not flagged."""
    a = a.copy()
    strong = (a.n_methods >= 2) & (a.stab_consensus >= 0.8) & a.ci_clear
    moderate = ((a.n_methods >= 2) & (a.stab_consensus >= 0.5)) | (a.flag_z & (a.stab_z >= 0.8))
    a["tier"] = np.select([strong, moderate, a.n_methods >= 1], ["Strong", "Moderate", "Watch"], "Typical")
    return a
