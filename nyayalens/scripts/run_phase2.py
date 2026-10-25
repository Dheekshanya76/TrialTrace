"""Phase 2: features + Wilson CIs."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pandas as pd
from nyayalens.features import build_features

out = ROOT / "data/processed"
f = build_features(pd.read_csv(out / "court_disposal_2023_metro.csv"))
f.to_csv(out / "features_2023.csv", index=False)
print(f.groupby(["table", "status"]).size().unstack(fill_value=0))
