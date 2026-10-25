"""Integrity checks on the parsed NCRB tables.

NCRB prints the formulas in the column headers, so every row must satisfy
them. We also check published rates and that parents equal the sum of children.
"""
import numpy as np
import pandas as pd
from .parse import COUNT_COLS

IDENTITIES = {
    "Col5 = Col3 + Col4": lambda d: d.total_for_trial == d.pending_prev + d.sent_for_trial,
    "Col11 = Col6..10": lambda d: d.disposed_without_trial == d[["abated", "withdrawn", "compounded", "plea_bargain", "quashed"]].sum(axis=1),
    "Col15 = Col13 + Col14": lambda d: d.convicted == d.conv_prev_year + d.conv_current_year,
    "Col18 = Col15+16+17": lambda d: d.trials_completed == d.convicted + d.discharged + d.acquitted,
    "Col19 = Col11 + Col18": lambda d: d.disposed_by_courts == d.disposed_without_trial + d.trials_completed,
    "Col20 = Col5 - Col19": lambda d: d.pending_end == d.total_for_trial - d.disposed_by_courts,
}


def check_identities(df):
    """One row per (crime head, failed identity)."""
    out = []
    for name, f in IDENTITIES.items():
        for _, r in df[~f(df)].iterrows():
            out.append({"check": name, "table": r.table, "sl_code": r.sl_code, "crime_head": r.crime_head})
    return pd.DataFrame(out, columns=["check", "table", "sl_code", "crime_head"])


def check_rates(df, tol=0.051):
    """Published conviction/pendency rates vs recomputation from the counts."""
    conv = np.where(df.trials_completed > 0, df.convicted / df.trials_completed.replace(0, np.nan) * 100, np.nan)
    pend = np.where(df.total_for_trial > 0, df.pending_end / df.total_for_trial.replace(0, np.nan) * 100, np.nan)
    out = []
    for label, calc, pub in [("conviction_rate", conv, df.conviction_rate_pub), ("pendency_pct", pend, df.pendency_pct_pub)]:
        p = pub.to_numpy()
        bad = (np.abs(calc - p) > tol) | (np.isnan(calc) != np.isnan(p))
        for i in np.where(bad)[0]:
            out.append({"check": label, "table": df.table.iloc[i], "sl_code": df.sl_code.iloc[i],
                        "crime_head": df.crime_head.iloc[i], "published": p[i], "recomputed": calc[i]})
    return pd.DataFrame(out, columns=["check", "table", "sl_code", "crime_head", "published", "recomputed"])


def check_hierarchy(df):
    """Parents = sum of children; subtotals = sum of their top-level heads;
    grand total = sum of all top-level heads."""
    out = []
    def cmp(t, level, parent_row, exp):
        for c in COUNT_COLS:
            if exp[c] != parent_row[c]:
                out.append({"table": t, "level": level, "column": c, "reported": parent_row[c], "sum_of_parts": exp[c]})
    for t, d in df.groupby("table"):
        coded = d[d.sl_code.notna()]
        for pc, kids in coded.groupby("parent_code"):
            parent = coded[coded.sl_code == pc]
            if not parent.empty:
                cmp(t, f"parent {pc}", parent.iloc[0], kids[COUNT_COLS].sum())
        top = coded[coded.parent_code.isna()]
        for _, sub in d[d.row_type == "subtotal"].iterrows():
            cmp(t, f"subtotal {sub.crime_head}", sub, top[top.group == sub.crime_head][COUNT_COLS].sum())
        cmp(t, "grand total", d[d.row_type == "grand_total"].iloc[0], top[COUNT_COLS].sum())
    return pd.DataFrame(out, columns=["table", "level", "column", "reported", "sum_of_parts"])
