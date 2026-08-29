#!/usr/bin/env python3
"""E1 figure (R1): the CNN vs the sigma_v->theta_E label relation, both against
b_SIE on the SLACS benchmark. The CNN (filled) tracks the 1:1 line far more
tightly than the sigma_v->theta_E SIS relation (open), showing the network reads
the lensing geometry rather than a luminosity-sigma_v proxy.
Writes paper/figures/labelnoise.png.
"""
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

C_KMS, OM, OL, ARCSEC = 299792.458, 0.3, 0.7, 206264.806

def Dc(z, n=2000):
    zg = np.linspace(0, z, n); y = 1.0 / np.sqrt(OM * (1 + zg) ** 3 + OL)
    return np.sum((y[1:] + y[:-1]) * 0.5 * np.diff(zg))

def theta_sis(sig, zl, zs):
    return 4 * np.pi * (sig / C_KMS) ** 2 * (1 - Dc(zl) / Dc(zs)) * ARCSEC

def nmad(x): return 1.4826 * np.median(np.abs(x - np.median(x)))

# label relation
kin = {r["name"]: r for r in csv.DictReader(open("tables/slacs_benchmark_kinematics.csv"))}
# CNN predictions
cnn = {r["name"]: float(r["theta_E_pred_arcsec"])
       for r in csv.DictReader(open("results/preds_l21_ens_real_slacs_images.csv"))}

names = [n for n in kin if n in cnn]
b = np.array([float(kin[n]["b_SIE_arcsec"]) for n in names])
tsis = np.array([theta_sis(float(kin[n]["sigma_v_kms"]), float(kin[n]["z_l"]),
                           float(kin[n]["z_s"])) for n in names])
pred = np.array([cnn[n] for n in names])

fig, ax = plt.subplots(figsize=(4.8, 4.6))
lo, hi = 0.4, 2.0
ax.plot([lo, hi], [lo, hi], "k--", lw=1, label="1:1")
ax.scatter(b, tsis, s=34, facecolors="none", edgecolors="tab:orange", lw=1.3,
           label=fr"$\sigma_v\!\to\!\theta_E$ (SIS): NMAD {nmad(tsis-b):.2f}$^{{\prime\prime}}$")
ax.scatter(b, pred, s=26, color="tab:blue", alpha=0.85,
           label=fr"CNN: NMAD {nmad(pred-b):.2f}$^{{\prime\prime}}$")
ax.set_xlabel(r"true $\theta_E$ = Bolton $b_{\rm SIE}$ [arcsec]")
ax.set_ylabel(r"predicted $\theta_E$ [arcsec]")
ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
ax.legend(frameon=False, fontsize=8.5, loc="upper left")
ax.set_title(f"CNN vs the label relation (N={len(names)} SLACS)")
fig.tight_layout()
fig.savefig("paper/figures/labelnoise.png", dpi=200)
print(f"wrote paper/figures/labelnoise.png  N={len(names)}")
print(f"  sigma_v->theta_E NMAD={nmad(tsis-b):.3f}, CNN NMAD={nmad(pred-b):.3f}")
