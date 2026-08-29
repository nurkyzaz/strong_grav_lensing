#!/usr/bin/env python3
"""Confidence-gating trade-off figure (reviewer concern R7): failure rate vs
retained fraction, gating on predicted sigma. Reads the GEN4 SLACS/S4TM
prediction files and writes paper/figures/gating_tradeoff.png.
"""
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FAIL = 0.15

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

def curve(path):
    p, g, s = load(path)
    fe = np.abs(p - g) / g
    order = np.argsort(s)          # most confident (smallest sigma) first
    fe = fe[order]
    n = len(fe)
    fracs = np.arange(1, n + 1) / n
    fails = np.array([np.mean(fe[:k] > FAIL) for k in range(1, n + 1)])
    return fracs * 100, fails * 100

fig, ax = plt.subplots(figsize=(5.0, 3.6))
for path, lab, c in [
    ("results/preds_l21_ens_real_slacs_images.csv", "SLACS (62)", "tab:blue"),
    ("results/preds_l21_g4n_r50_s3_real_s4tm_images.csv", "S4TM (40)", "tab:red"),
]:
    x, y = curve(path)
    ax.plot(x, y, "-", color=c, lw=2, label=lab)
ax.axhline(15, ls=":", color="grey", lw=1)
ax.text(26, 15.6, "full-sample fail threshold", color="grey", fontsize=8)
ax.set_xlabel("retained most-confident fraction [%]")
ax.set_ylabel("failure rate (|frac. err| > 15%) [%]")
ax.set_xlim(20, 100)
ax.set_ylim(0, 18)
ax.legend(frameon=False, loc="upper left")
ax.set_title("Confidence gating on predicted $\\sigma$")
fig.tight_layout()
fig.savefig("paper/figures/gating_tradeoff.png", dpi=200)
print("wrote paper/figures/gating_tradeoff.png")
