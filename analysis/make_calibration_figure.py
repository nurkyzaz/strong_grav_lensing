#!/usr/bin/env python3
"""Reliability diagram (reviewer concern R7): nominal vs empirical coverage of
the predicted uncertainty, before and after a global sigma-rescaling. Perfect
calibration lies on the diagonal; points below it mean the model is
over-confident. Writes paper/figures/calibration.png.
"""
import csv
import numpy as np
from scipy.special import erfinv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def load(path):
    p, g, s = [], [], []
    for r in csv.DictReader(open(path)):
        try:
            p.append(float(r["theta_E_pred_arcsec"]))
            g.append(float(r["theta_E_pub_arcsec"]))
            s.append(float(r["theta_E_sigma_arcsec"]))
        except (KeyError, ValueError):
            continue
    return map(np.asarray, (p, g, s))

nominal = np.linspace(0.02, 0.99, 60)
zc = np.sqrt(2) * erfinv(nominal)            # two-sided half-width in sigma units

fig, ax = plt.subplots(figsize=(4.6, 4.4))
ax.plot([0, 1], [0, 1], "k--", lw=1, label="perfect calibration")
styles = {
    "results/preds_l21_ens_real_slacs_images.csv": ("SLACS", "tab:blue"),
    "results/preds_l21_g4n_r50_s3_real_s4tm_images.csv": ("S4TM", "tab:red"),
}
for path, (lab, c) in styles.items():
    p, g, s = load(path)
    z = np.abs(p - g) / s
    emp = np.array([np.mean(z <= t) for t in zc])
    ax.plot(nominal, emp, "-", color=c, lw=2, label=f"{lab} (raw)")
    # recalibrate so 1-sigma coverage matches: k = z at nominal 0.683
    k = np.percentile(z, 68.3)
    zk = z / k
    empk = np.array([np.mean(zk <= t) for t in zc])
    ax.plot(nominal, empk, "--", color=c, lw=1.5, alpha=0.7,
            label=f"{lab} (recal. ×{k:.1f})")
ax.set_xlabel("nominal coverage")
ax.set_ylabel("empirical coverage")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.set_aspect("equal")
ax.legend(frameon=False, fontsize=8, loc="lower right")
ax.set_title("Uncertainty reliability")
fig.tight_layout()
fig.savefig("paper/figures/calibration.png", dpi=200)
print("wrote paper/figures/calibration.png")
