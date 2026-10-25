"""Phase 4: bootstrap stability, explanations, final tiers."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pandas as pd
from nyayalens.explain import add_explanations, assign_tier
from nyayalens.stability import bootstrap_flags

out = ROOT / "data/processed"
a = pd.read_csv(out / "detection_2023.csv")
a = a.join(bootstrap_flags(a, n_boot=100))
a = assign_tier(add_explanations(a))
a.to_csv(out / "final_results_2023.csv", index=False)
print(a.tier.value_counts().to_dict())
cols = ["table", "sl_code", "crime_head", "trials_completed", "n_methods", "stab_consensus", "stab_z", "tier"]
print(a[a.tier != "Typical"].sort_values(["tier", "stab_consensus"], ascending=[True, False])[cols].to_string(index=False))
