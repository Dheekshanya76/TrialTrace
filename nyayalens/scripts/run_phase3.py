"""Phase 3: robust z-score, Isolation Forest, LOF + sensitivity."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pandas as pd
from nyayalens.detect import detect, sensitivity

out = ROOT / "data/processed"
f = pd.read_csv(out / "features_2023.csv")
a = detect(f)
a.to_csv(out / "detection_2023.csv", index=False)
s = sensitivity(f)
s.to_csv(out / "sensitivity_summary.csv", index=False)
print(s.to_string(index=False))
print("\nflag counts:", a[["flag_z", "flag_if", "flag_lof"]].sum().to_dict())
print("n_methods distribution:", a.n_methods.value_counts().sort_index().to_dict())
