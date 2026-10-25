"""Phase 1: parse both PDFs, validate, write clean CSV + validation reports."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nyayalens.parse import load_all
from nyayalens.validate import check_identities, check_rates, check_hierarchy

raw, out = ROOT / "data/raw", ROOT / "data/processed"
df = load_all(raw / "ncrb2023_table18B1_ipc_court_disposal_metro.pdf",
              raw / "ncrb2023_table18B3_sll_court_disposal_metro.pdf")
df.to_csv(out / "court_disposal_2023_metro.csv", index=False)

report = {"identities": check_identities(df), "rates": check_rates(df), "hierarchy": check_hierarchy(df)}
for k, v in report.items():
    v.to_csv(out / f"validation_{k}.csv", index=False)

import pandas as pd
n_agg = int(df.row_type.isin(["parent", "subtotal", "grand_total"]).sum())
summary = pd.DataFrame([
    {"check": "Column formulas (6 identities per row)", "comparisons": 6 * len(df), "failures": len(report["identities"])},
    {"check": "Published conviction and pendency rates vs recomputed", "comparisons": 2 * len(df), "failures": len(report["rates"])},
    {"check": "Parents, subtotals and grand totals vs sum of parts (18 count columns)", "comparisons": 18 * n_agg, "failures": len(report["hierarchy"])},
])
summary.to_csv(out / "validation_summary.csv", index=False)

print(df.groupby(["table", "row_type"]).size().unstack(fill_value=0))
d = df[df.row_type == "detail"]
print("\nDetail rows:", len(d), "| with >=30 completed trials:", int((d.trials_completed >= 30).sum()))
print("Failed checks:", {k: len(v) for k, v in report.items()})
