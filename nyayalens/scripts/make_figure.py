"""Static results figure for the README."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
a = pd.read_csv(ROOT / "data/processed/final_results_2023.csv")
colors = {"Strong": "#C00000", "Moderate": "#E8830C", "Watch": "#1D4FBF", "Typical": "#B8B8B8"}
fig, ax = plt.subplots(figsize=(8.5, 5.5))
for t in ["Typical", "Watch", "Moderate", "Strong"]:
    s = a[a.tier == t]
    ax.scatter(s.conviction_rate * 100, s.pendency_rate * 100, s=20 + s.trials_completed ** 0.5 * 2,
               c=colors[t], alpha=0.75, label=f"{t} ({len(s)})", edgecolors="white", linewidths=0.5)
for _, r in a[a.tier == "Strong"].iterrows():
    ax.annotate(r.crime_head[:28], (r.conviction_rate * 100, r.pendency_rate * 100), fontsize=7,
                xytext=(-4, 6), textcoords="offset points", ha="right")
ax.set_xlabel("Conviction rate (%)")
ax.set_ylabel("Pendency rate (%)")
ax.set_title("Court outcomes by crime head, metropolitan cities, 2023 (97 heads with 30+ completed trials)", fontsize=9)
ax.legend(title="Tier", fontsize=8)
ax.grid(alpha=0.25)
fig.tight_layout()
fig.savefig(ROOT / "docs/figures/anomaly_map.png", dpi=150)
