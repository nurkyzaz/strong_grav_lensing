#!/usr/bin/env python3
"""
Figure 3 + Table: per-lens comparison of our CNN (native-HST ensemble) against
TinyLensGPU (Cao et al. 2025) on the 63 SLACS lenses, with Bolton et al. (2008)
b_SIE as the common ground truth.

Cao's per-lens predictions were provided by X. Cao (priv. comm., 2026) in
cao_joint_table.csv:
    thetaE_lens_l / _m / _u = 99.73% CI lower / median / upper (TinyLensGPU)
    bSIE                    = Bolton et al. (2008) SIE Einstein radius (GT)
Our predictions: results/preds_pathb_v2_ensemble_real_slacs.csv
    theta_E_pred_arcsec +/- theta_E_sigma_arcsec (NLL uncertainty head).

Outputs (in paper_figures/):
    figure3_cao_comparison.png / .pdf
    ../results/cao_cnn_perlens_comparison.csv
    cao_comparison_metrics.md
"""
import csv
import os
import numpy as np
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------- load ----------
ours, cao = {}, {}
with open(os.path.join(ROOT, "results/preds_pathb_v2_ensemble_real_slacs.csv")) as f:
    for r in csv.DictReader(f):
        ours[r["name"]] = r
with open(os.path.join(ROOT, "cao_joint_table.csv")) as f:
    for r in csv.DictReader(f):
        cao[r["lens_name"]] = r

names = sorted(ours)
gt      = np.array([float(cao[n]["bSIE"]) for n in names])
cnn     = np.array([float(ours[n]["theta_E_pred_arcsec"]) for n in names])
cnn_sig = np.array([float(ours[n]["theta_E_sigma_arcsec"]) for n in names])
tl      = np.array([float(cao[n]["thetaE_lens_m"]) for n in names])
tl_lo   = np.array([float(cao[n]["thetaE_lens_l"]) for n in names])
tl_hi   = np.array([float(cao[n]["thetaE_lens_u"]) for n in names])

fe_cnn = (cnn - gt) / gt
fe_tl  = (tl  - gt) / gt


def stats(pred):
    fe = (pred - gt) / gt
    ss_res = np.sum((pred - gt) ** 2)
    ss_tot = np.sum((gt - gt.mean()) ** 2)
    return dict(
        med_bias=np.median(fe) * 100,
        med_abs=np.median(np.abs(fe)) * 100,
        mean_abs=np.mean(np.abs(fe)) * 100,
        mae=np.mean(np.abs(pred - gt)),
        rmse=np.sqrt(np.mean((pred - gt) ** 2)),
        r2=1 - ss_res / ss_tot,
        f15=(np.abs(fe) > 0.15).mean() * 100,
        f30=(np.abs(fe) > 0.30).mean() * 100,
    )


s_cnn, s_tl = stats(cnn), stats(tl)

# ---------- write per-lens CSV ----------
csv_out = os.path.join(ROOT, "results/cao_cnn_perlens_comparison.csv")
with open(csv_out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["lens", "bSIE_GT", "cnn_thetaE", "cnn_sigma", "cnn_fracerr_pct",
                "tinylens_median", "tinylens_lo9973", "tinylens_hi9973", "tinylens_fracerr_pct"])
    for i, n in enumerate(names):
        w.writerow([n, f"{gt[i]:.3f}", f"{cnn[i]:.3f}", f"{cnn_sig[i]:.3f}",
                    f"{fe_cnn[i]*100:+.1f}", f"{tl[i]:.3f}", f"{tl_lo[i]:.3f}",
                    f"{tl_hi[i]:.3f}", f"{fe_tl[i]*100:+.1f}"])

# ---------- metrics markdown ----------
md = os.path.join(ROOT, "paper_figures/cao_comparison_metrics.md")
with open(md, "w") as f:
    f.write("| metric | Our CNN ensemble | TinyLensGPU (Cao 2025) |\n")
    f.write("|---|---|---|\n")
    rows = [
        ("median frac. error (bias)", f"{s_cnn['med_bias']:+.1f}%", f"{s_tl['med_bias']:+.1f}%"),
        ("median \\|frac. error\\|",    f"{s_cnn['med_abs']:.1f}%",  f"{s_tl['med_abs']:.1f}%"),
        ("mean \\|frac. error\\|",      f"{s_cnn['mean_abs']:.1f}%", f"{s_tl['mean_abs']:.1f}%"),
        ("MAE (arcsec)",              f"{s_cnn['mae']:.3f}",       f"{s_tl['mae']:.3f}"),
        ("RMSE (arcsec)",             f"{s_cnn['rmse']:.3f}",      f"{s_tl['rmse']:.3f}"),
        ("R^2",                       f"{s_cnn['r2']:+.2f}",       f"{s_tl['r2']:+.2f}"),
        ("catastrophic >15%",         f"{s_cnn['f15']:.0f}%",      f"{s_tl['f15']:.0f}%"),
        ("catastrophic >30%",         f"{s_cnn['f30']:.0f}%",      f"{s_tl['f30']:.0f}%"),
    ]
    for r in rows:
        f.write(f"| {r[0]} | {r[1]} | {r[2]} |\n")

# ---------- figure ----------
C_CNN, C_TL = "#d1495b", "#3a7ca5"  # our red / their blue
plt.rcParams.update({"font.size": 11, "axes.grid": True,
                     "grid.alpha": 0.25, "grid.linewidth": 0.6})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.4, 5.7))

# --- panel A: predicted vs true ---
lim = [0.2, 3.4]
ax1.plot(lim, lim, "k--", lw=1, zorder=1, label="1:1")
ax1.fill_between(lim, [0.95 * x for x in lim], [1.05 * x for x in lim],
                 color="0.5", alpha=0.12, zorder=0, label="±5%")
# TinyLensGPU with 99.73% CI
ax1.errorbar(gt, tl, yerr=[tl - tl_lo, tl_hi - tl], fmt="s", ms=4.5,
             color=C_TL, ecolor=C_TL, elinewidth=0.7, capsize=0, alpha=0.75,
             mfc=C_TL, mec="white", mew=0.4, zorder=3,
             label="TinyLensGPU (Cao 2025), 99.73% CI")
# our CNN with sigma
ax1.errorbar(gt, cnn, yerr=cnn_sig, fmt="o", ms=5, color=C_CNN, ecolor=C_CNN,
             elinewidth=0.7, capsize=0, alpha=0.85, mfc=C_CNN, mec="white",
             mew=0.4, zorder=4, label="Our CNN ensemble, ±1σ")
ax1.set_xlim(lim); ax1.set_ylim(lim); ax1.set_aspect("equal")
ax1.set_xlabel(r"Bolton et al. 2008  $\theta_E$ ($b_{\rm SIE}$)  [arcsec]")
ax1.set_ylabel(r"predicted $\theta_E$  [arcsec]")
ax1.set_title(f"Predicted vs. true $\\theta_E$  (63 SLACS)")
ax1.legend(loc="upper left", fontsize=8.5, framealpha=0.95)

# --- panel B: CDF of |fractional error| ---
def cdf(x):
    xs = np.sort(np.abs(x)) * 100
    return xs, np.arange(1, len(xs) + 1) / len(xs) * 100

xc, yc = cdf(fe_cnn); xt, yt = cdf(fe_tl)
ax2.step(xc, yc, where="post", color=C_CNN, lw=2.2,
         label=f"Our CNN  (median {s_cnn['med_abs']:.1f}%, R²={s_cnn['r2']:+.2f})")
ax2.step(xt, yt, where="post", color=C_TL, lw=2.2,
         label=f"TinyLensGPU  (median {s_tl['med_abs']:.1f}%, R²={s_tl['r2']:+.2f})")
ax2.axvline(5, color="0.5", ls=":", lw=1)
ax2.axvline(15, color="0.5", ls="--", lw=1)
ax2.text(5, 4, "5%", color="0.4", fontsize=8, rotation=90, va="bottom", ha="right")
ax2.text(15, 4, "15%", color="0.4", fontsize=8, rotation=90, va="bottom", ha="right")
ax2.set_xlim(0, 60); ax2.set_ylim(0, 100)
ax2.set_xlabel(r"$|\theta_E$ fractional error$|$  [%]")
ax2.set_ylabel("cumulative fraction of lenses  [%]")
ax2.set_title("Error distribution (lower-right = more accurate)")
ax2.legend(loc="lower right", fontsize=9, framealpha=0.95)

fig.suptitle("Our CNN vs. TinyLensGPU (Cao et al. 2025) — same 63 SLACS, Bolton 2008 ground truth",
             fontsize=12.5, y=0.99)
fig.tight_layout(rect=[0, 0, 1, 0.97])
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(ROOT, f"paper_figures/figure3_cao_comparison.{ext}"),
                dpi=200, bbox_inches="tight")

print("Wrote figure3_cao_comparison.png/.pdf")
print("Wrote", csv_out)
print("\n=== metrics ===")
for r in rows:
    print(f"{r[0]:28s} CNN {r[1]:>8s}   TinyLensGPU {r[2]:>8s}")
