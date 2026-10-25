import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import pytest
from nyayalens.parse import load_all, parent_code
from nyayalens.validate import check_identities, check_rates

@pytest.fixture(scope="module")
def df():
    raw = ROOT / "data/raw"
    return load_all(raw / "ncrb2023_table18B1_ipc_court_disposal_metro.pdf",
                    raw / "ncrb2023_table18B3_sll_court_disposal_metro.pdf")

def test_parent_code():
    assert parent_code("3.1A") == "3.1" and parent_code("10.1") == "10" and parent_code("10") is None

def test_known_values(df):
    r = df[(df.table == "IPC") & (df.sl_code == "1")].iloc[0]
    assert r.crime_head == "Murder" and r.total_for_trial == 9067 and r.convicted == 310
    s = df[(df.table == "SLL") & (df.sl_code == "30")].iloc[0]
    assert s.pending_end == 252871

def test_identities_hold(df):
    assert check_identities(df).empty

def test_published_rates_match(df):
    assert check_rates(df).empty

def test_has_detail_rows(df):
    assert (df.row_type == "detail").sum() > 150
