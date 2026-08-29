#!/usr/bin/env python3
"""Ablation bar chart: full-sample SLACS R^2 for each single-ingredient-removed
variant (paper Table 4). Shows that removing real empty-sky backdrops
('Gaussian noise') is catastrophic, i.e. real background structure dominates.
Writes paper/figures/ablation.png. Values are the paper's canonical ablation
results (real-unit hybrid recipe).
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# (label, SLACS R2) from Table 4
variants = [
    ("Full recipe",            +0.27),
    ("Broad ePSF pool",        +0.22),
    ("Gaussian PSF",           -0.46),
    ("Skewed $\\theta_E$ prior", -0.52),
    ("Gaussian noise\n(no real backdrops)", -5.10),
]
labels = [v[0] for v in variants]
r2 = np.array([v[1] for v in variants])
YCLIP = -1.6  # clip the catastrophic bar for readability

fig, ax = plt.subplots(figsize=(5.2, 3.4))
colors = ["tab:green" if x > 0 else "tab:red" for x in r2]
disp = np.clip(r2, YCLIP, None)
bars = ax.barh(range(len(labels)), disp, color=colors, alpha=0.85)
ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels, fontsize=9)
ax.invert_yaxis()
ax.axvline(0, color="k", lw=0.8)
ax.set_xlabel("full-sample SLACS $R^2$")
ax.set_xlim(YCLIP, 0.6)
for i, x in enumerate(r2):
    if x <= YCLIP:
        ax.text(YCLIP + 0.03, i, f"{x:+.2f} (off scale)", va="center",
                ha="left", color="white", fontsize=8, fontweight="bold")
    else:
        ax.text(x + (0.02 if x > 0 else -0.02), i, f"{x:+.2f}", va="center",
                ha="left" if x > 0 else "right", fontsize=8)
ax.set_title("Remove one realism ingredient (SLACS)")
fig.tight_layout()
fig.savefig("paper/figures/ablation.png", dpi=200)
print("wrote paper/figures/ablation.png")
