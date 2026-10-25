import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np
import pandas as pd
import pytest
from nyayalens.features import wilson_ci, build_features, MIN_TRIALS
from nyayalens.detect import robust_z, detect, logit_matrix
from nyayalens.stability import bootstrap_flags

PROC = ROOT / "data/processed"

@pytest.fixture(scope="module")
def feats():
    return pd.read_csv(PROC / "features_2023.csv")

def test_wilson_zero_successes():
    lo, hi = wilson_ci(0, 30)
    assert lo == 0 and hi == pytest.approx(3.8416 / 33.8416, abs=1e-4)

def test_wilson_symmetric_and_empty():
    lo, hi = wilson_ci(50, 100)
    assert lo + hi == pytest.approx(1.0, abs=1e-9)
    lo, hi = wilson_ci(0, 0)
    assert np.isnan(lo) and np.isnan(hi)

def test_robust_z_centres_on_median():
    X = np.array([[1.0], [2.0], [3.0], [4.0], [100.0]])
    z = robust_z(X)
    assert z[2, 0] == 0 and abs(z[4, 0]) > 3.5

def test_features_only_detail_rows_and_threshold(feats):
    assert set(feats.row_type) == {"detail"}
    assert (feats.analysis_set == (feats.trials_completed >= MIN_TRIALS)).all()

def test_murder_conviction_rate(feats):
    r = feats[(feats.table == "IPC") & (feats.sl_code.astype(str) == "1")].iloc[0]
    assert r.conviction_rate == pytest.approx(310 / 686)
    assert r.conviction_rate_lo < r.conviction_rate < r.conviction_rate_hi

def test_insufficient_heads_never_flagged(feats):
    res = pd.read_csv(PROC / "final_results_2023.csv")
    assert len(res) == int(feats.analysis_set.sum())
    assert (res.trials_completed >= MIN_TRIALS).all()

def test_detection_is_reproducible(feats):
    a, b = detect(feats), detect(feats)
    assert (a.flag_if == b.flag_if).all() and (a.flag_lof == b.flag_lof).all()

def test_bootstrap_frequencies_valid(feats):
    a = detect(feats)
    f = bootstrap_flags(a, n_boot=5)
    assert ((f >= 0) & (f <= 1)).all().all() and len(f) == len(a)

def test_final_results_consistent():
    res = pd.read_csv(PROC / "final_results_2023.csv")
    assert set(res.tier) <= {"Strong", "Moderate", "Watch", "Typical"}
    assert res.explanation.str.contains("completed trials").all()
    strong = res[res.tier == "Strong"]
    assert (strong.n_methods >= 2).all() and (strong.stab_consensus >= 0.8).all()
