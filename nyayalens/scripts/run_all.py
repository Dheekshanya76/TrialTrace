"""Run the whole pipeline: parse -> features -> detection -> stability/explanations."""
import subprocess, sys
from pathlib import Path
here = Path(__file__).parent
for s in ["run_phase1.py", "run_phase2.py", "run_phase3.py", "run_phase4.py", "make_figure.py"]:
    print(f"\n=== {s} ===")
    subprocess.run([sys.executable, str(here / s)], check=True)
