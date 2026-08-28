#!/usr/bin/env python3
"""
Publication figures for the LensCNN paper. Run from repo root or anywhere:
    python3 paper/figures/make_figures.py
All inputs are local (verified 2026-08-03). Outputs land in paper/figures/.

Figures
  fig_realism_real_vs_sim.png : real Euclid Q1 lenses (top) vs GEN5 simulated
        lenses (bottom), identical asinh stretch -> "our sims look like real lenses".
  fig_cao_comparison.png      : our GEN4 native CNN vs TinyLensGPU (Cao et al. 2025),
        same 63 SLACS, Bolton 2008 b_SIE GT. Predicted-vs-true (+ error bars) + error CDF.
  fig_lemon_comparison.png    : our Euclid-arm CNN vs LEMON (Busillo et al. 2026) on the
        29 shared Euclidised SLACS, Bolton GT. Predicted-vs-true (+ error bars) + error CDF.
  fig_benchmark_gallery.png   : native-HST real benchmark gallery (SLACS + S4TM) with theta_E.
"""
import csv, os
import numpy as np
import h5py
import matplotlib.pyplot as plt

# ---- locate repo root (this file is paper/figures/make_figures.py) ----
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = HERE
def R(*p): return os.path.join(ROOT, *p)

C_OURS, C_CAO, C_LEMON = "#d1495b", "#3a7ca5", "#7a5c99"  # red / blue / purple
plt.rcParams.update({"font.size": 11, "axes.grid": True,
                     "grid.alpha": 0.22, "grid.linewidth": 0.6,
                     "figure.dpi": 140})


# ============================ helpers ============================
def sky_rms(img):
    """Robust sky RMS from a sigma-clipped estimate (MAD of the outer frame)."""
    b = np.concatenate([img[:8].ravel(), img[-8:].ravel(),
                        img[:, :8].ravel(), img[:, -8:].ravel()])
    med = np.median(b)
    mad = np.median(np.abs(b - med))
    s = 1.4826 * mad
    return s if s > 0 else (np.std(b) + 1e-8)


def show_asinh(ax, img, title=None, color="k", q=99.5):
    img = np.asarray(img, float)
    if img.ndim == 3:
        img = img[0]
    s = sky_rms(img)
    x = np.arcsinh((img - np.median(img)) / s)
    vmax = np.percentile(x, q)
    ax.imshow(x, cmap="gray", origin="lower", vmin=np.percentile(x, 2), vmax=vmax)
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    if title:
        ax.set_title(title, fontsize=8.5, color=color, pad=2)


def load_preds(fn):
    d = {}
    for r in csv.DictReader(open(fn)):
        d[r["name"]] = r
    return d


def metrics(pred, gt):
    fe = (pred - gt) / gt
    ss_res = np.sum((pred - gt) ** 2)
    ss_tot = np.sum((gt - gt.mean()) ** 2)
    nmad = 1.4826 * np.median(np.abs(fe - np.median(fe))) * np.median(gt)
    return dict(r2=1 - ss_res / ss_tot, medabs=np.median(np.abs(fe)) * 100,
                medbias=np.median(fe) * 100, nmad=nmad,
                rmse=np.sqrt(np.mean((pred - gt) ** 2)),
                f15=(np.abs(fe) > 0.15).mean() * 100)


def cdf(x):
    xs = np.sort(np.abs(x)) * 100
    return xs, np.arange(1, len(xs) + 1) / len(xs) * 100


def scatter_panel(ax, gt, pred, sig, color, label, marker="o"):
    ax.errorbar(gt, pred, yerr=sig, fmt=marker, ms=5, color=color, ecolor=color,
                elinewidth=0.7, capsize=0, alpha=0.85, mfc=color, mec="white",
                mew=0.4, zorder=4, label=label)


# ===================== Figure: real vs simulated =====================
def fig_real_vs_sim():
    real_fn = R("_local/reviews/q1_real_review/raw/q1_slde_eval_f2p85_zoom.h5")
    sim_fn = R("_local/reviews/g5cosmos_fj8_review/raw/euclid_sel.h5")
    if not (os.path.exists(real_fn) and os.path.exists(sim_fn)):
        print("  [skip real_vs_sim] missing", real_fn, "or", sim_fn)
        return
    rng = np.random.default_rng(7)
    with h5py.File(real_fn, "r") as f:
        rimg = f["images"][:]; rth = f["theta_E_pub"][:]
    with h5py.File(sim_fn, "r") as f:
        simg = f["lensed"][:]; sth = f["theta_E"][:]
        ssnr = f["arc_snr"][:] if "arc_snr" in f else np.ones(len(simg))
    # real: pick a spread of theta_E in [0.6,1.6] with finite images
    rok = np.where(np.isfinite(rth) & (rth > 0.55) & (rth < 1.7))[0]
    rsel = rng.choice(rok, size=8, replace=False)
    rsel = rsel[np.argsort(rth[rsel])]
    # sim: prefer visible arcs (arc_snr), varied theta_E
    sok = np.where(np.isfinite(sth) & (ssnr > np.percentile(ssnr, 45)))[0]
    ssel = rng.choice(sok, size=8, replace=False)
    ssel = ssel[np.argsort(sth[ssel])]

    fig, axes = plt.subplots(4, 4, figsize=(9.2, 9.8))
    for j, idx in enumerate(rsel):
        ax = axes[j // 4, j % 4]
        show_asinh(ax, rimg[idx], rf"REAL Euclid Q1  $\theta_E$={rth[idx]:.2f}$^{{\prime\prime}}$", C_OURS)
    for j, idx in enumerate(ssel):
        ax = axes[2 + j // 4, j % 4]
        show_asinh(ax, simg[idx], rf"SIM (GEN5)  $\theta_E$={sth[idx]:.2f}$^{{\prime\prime}}$", C_CAO)
    fig.suptitle("Real Euclid Q1 lenses (top) vs. our GEN5 simulated lenses (bottom)\n"
                 "identical asinh(img / sky-RMS) stretch",
                 fontsize=12.5, y=0.99)
    # divider line between real block and sim block
    fig.subplots_adjust(hspace=0.28, wspace=0.06, top=0.9, bottom=0.02,
                        left=0.02, right=0.98)
    y = 0.5 * (axes[1, 0].get_position().y0 + axes[2, 0].get_position().y1)
    fig.add_artist(plt.Line2D([0.03, 0.97], [y, y], color="0.6", lw=1.0,
                              ls="--", transform=fig.transFigure))
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"fig_realism_real_vs_sim.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print("  wrote fig_realism_real_vs_sim.png/.pdf")


# ===================== Figure: Cao comparison =====================
def fig_cao():
    ours = load_preds(R("results/preds_l21_ens_real_slacs_images.csv"))
    cao = {r["lens_name"]: r for r in csv.DictReader(open(R("cao_joint_table.csv")))}
    names = sorted(set(ours) & set(cao))
    gt = np.array([float(cao[n]["bSIE"]) for n in names])
    cnn = np.array([float(ours[n]["theta_E_pred_arcsec"]) for n in names])
    csg = np.array([float(ours[n]["theta_E_sigma_arcsec"]) for n in names])
    tl = np.array([float(cao[n]["thetaE_lens_m"]) for n in names])
    tlo = np.array([float(cao[n]["thetaE_lens_l"]) for n in names])
    thi = np.array([float(cao[n]["thetaE_lens_u"]) for n in names])
    sc, st = metrics(cnn, gt), metrics(tl, gt)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.4, 5.7))
    lim = [0.2, 3.4]
    a1.plot(lim, lim, "k--", lw=1, zorder=1, label="1:1")
    a1.fill_between(lim, [0.95 * x for x in lim], [1.05 * x for x in lim],
                    color="0.5", alpha=0.12, zorder=0, label="±5%")
    a1.errorbar(gt, tl, yerr=[tl - tlo, thi - tl], fmt="s", ms=4.5, color=C_CAO,
                ecolor=C_CAO, elinewidth=0.7, capsize=0, alpha=0.7, mfc=C_CAO,
                mec="white", mew=0.4, zorder=3, label="TinyLensGPU (Cao 2025), 99.73% CI")
    scatter_panel(a1, gt, cnn, csg, C_OURS, "Our GEN4 CNN, ±1σ")
    a1.set_xlim(lim); a1.set_ylim(lim); a1.set_aspect("equal")
    a1.set_xlabel(r"Bolton et al. 2008  $\theta_E$ ($b_{\rm SIE}$)  [arcsec]")
    a1.set_ylabel(r"predicted $\theta_E$  [arcsec]")
    a1.set_title(f"Predicted vs. true $\\theta_E$  ({len(names)} SLACS)")
    a1.legend(loc="upper left", fontsize=8.5, framealpha=0.95)

    xc, yc = cdf((cnn - gt) / gt); xt, yt = cdf((tl - gt) / gt)
    a2.step(xc, yc, where="post", color=C_OURS, lw=2.4,
            label=f"Our GEN4 CNN  (median {sc['medabs']:.1f}%, R²={sc['r2']:+.2f})")
    a2.step(xt, yt, where="post", color=C_CAO, lw=2.4,
            label=f"TinyLensGPU  (median {st['medabs']:.1f}%, R²={st['r2']:+.2f})")
    for xv, lab in [(5, "5%"), (15, "15%")]:
        a2.axvline(xv, color="0.5", ls=":" if xv == 5 else "--", lw=1)
        a2.text(xv, 4, lab, color="0.4", fontsize=8, rotation=90, va="bottom", ha="right")
    a2.set_xlim(0, 60); a2.set_ylim(0, 100)
    a2.set_xlabel(r"$|\theta_E$ fractional error$|$  [%]")
    a2.set_ylabel("cumulative fraction of lenses  [%]")
    a2.set_title("Error distribution (lower-right = more accurate)")
    a2.legend(loc="lower right", fontsize=9, framealpha=0.95)
    fig.suptitle("Our CNN (GEN4, native HST) vs. TinyLensGPU (Cao et al. 2025) — "
                 f"same {len(names)} SLACS, Bolton 2008 GT", fontsize=12.5, y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"fig_cao_comparison.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote fig_cao_comparison.png/.pdf  (ours R²={sc['r2']:+.2f}, Cao R²={st['r2']:+.2f})")


# ===================== Figure: LEMON comparison =====================
def fig_lemon():
    rows = [r for r in csv.DictReader(open(R("lemon_comparison_package/combined_comparison.csv")))
            if r["subsample"] == "SLACS"]
    lem_sig = {r["system"]: float(r["LEMON_uncertainty_arcsec"])
               for r in csv.DictReader(open(R("lemon_comparison_package/lemon_predictions.csv")))
               if r["subsample"] == "SLACS"}
    our_e = load_preds(R("results/preds_l17_ens_euclid_slacs_images.csv"))
    names = [r["system"] for r in rows]
    gt = np.array([float(r["ground_truth"]) for r in rows])
    lem = np.array([float(r["LEMON_pred"]) for r in rows])
    our = np.array([float(r["our_pred"]) for r in rows])
    lsg = np.array([lem_sig.get(n, np.nan) for n in names])
    osg = np.array([float(our_e[n]["theta_E_sigma_arcsec"]) if n in our_e else np.nan for n in names])
    sc, sl = metrics(our, gt), metrics(lem, gt)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.4, 5.7))
    lim = [0.3, 2.6]
    a1.plot(lim, lim, "k--", lw=1, zorder=1, label="1:1")
    a1.fill_between(lim, [0.95 * x for x in lim], [1.05 * x for x in lim],
                    color="0.5", alpha=0.12, zorder=0, label="±5%")
    a1.errorbar(gt, lem, yerr=lsg, fmt="^", ms=5, color=C_LEMON, ecolor=C_LEMON,
                elinewidth=0.7, capsize=0, alpha=0.75, mfc=C_LEMON, mec="white",
                mew=0.4, zorder=3, label="LEMON (Busillo 2026), ±1σ")
    scatter_panel(a1, gt, our, osg, C_OURS, "Our CNN (Euclid arm), ±1σ")
    a1.set_xlim(lim); a1.set_ylim(lim); a1.set_aspect("equal")
    a1.set_xlabel(r"Bolton et al. 2008  $\theta_E$ ($b_{\rm SIE}$)  [arcsec]")
    a1.set_ylabel(r"predicted $\theta_E$  [arcsec]")
    a1.set_title(f"Predicted vs. true $\\theta_E$  ({len(names)} shared SLACS)")
    a1.legend(loc="upper left", fontsize=8.5, framealpha=0.95)

    xc, yc = cdf((our - gt) / gt); xl, yl = cdf((lem - gt) / gt)
    a2.step(xc, yc, where="post", color=C_OURS, lw=2.4,
            label=f"Our CNN  (median {sc['medabs']:.1f}%, R²={sc['r2']:+.2f})")
    a2.step(xl, yl, where="post", color=C_LEMON, lw=2.4,
            label=f"LEMON  (median {sl['medabs']:.1f}%, R²={sl['r2']:+.2f})")
    for xv, lab in [(5, "5%"), (15, "15%")]:
        a2.axvline(xv, color="0.5", ls=":" if xv == 5 else "--", lw=1)
        a2.text(xv, 4, lab, color="0.4", fontsize=8, rotation=90, va="bottom", ha="right")
    a2.set_xlim(0, 100); a2.set_ylim(0, 100)
    a2.set_xlabel(r"$|\theta_E$ fractional error$|$  [%]")
    a2.set_ylabel("cumulative fraction of lenses  [%]")
    a2.set_title("Error distribution (lower-right = more accurate)")
    a2.legend(loc="lower right", fontsize=9, framealpha=0.95)
    fig.suptitle("Our CNN vs. LEMON (Busillo et al. 2026) — 29 shared Euclidised SLACS, "
                 "Bolton 2008 GT", fontsize=12.5, y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"fig_lemon_comparison.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote fig_lemon_comparison.png/.pdf  (ours R²={sc['r2']:+.2f}, LEMON R²={sl['r2']:+.2f})")


# ===================== Figure: benchmark gallery =====================
def fig_gallery():
    slacs_fn = R("real_slacs_images.h5")
    s4tm_fn = R("_local/reviews/audit/real_s4tm_images.h5")
    rng = np.random.default_rng(3)
    panels = []
    with h5py.File(slacs_fn, "r") as f:
        img = f["images"][:]; th = f["theta_E_pub"][:]; nm = f["names"][:]
        idx = rng.choice(len(img), 8, replace=False); idx = idx[np.argsort(th[idx])]
        for i in idx:
            n = nm[i].decode() if isinstance(nm[i], bytes) else str(nm[i])
            panels.append((img[i], f"SLACS {n}  $\\theta_E$={th[i]:.2f}$^{{\\prime\\prime}}$"))
    if os.path.exists(s4tm_fn):
        with h5py.File(s4tm_fn, "r") as f:
            img = f["images"][:]; th = f["theta_E_pub"][:]; nm = f["names"][:]
            idx = rng.choice(len(img), 8, replace=False); idx = idx[np.argsort(th[idx])]
            for i in idx:
                n = nm[i].decode() if isinstance(nm[i], bytes) else str(nm[i])
                panels.append((img[i], f"S4TM {n}  $\\theta_E$={th[i]:.2f}$^{{\\prime\\prime}}$"))
    ncol = 4; nrow = int(np.ceil(len(panels) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(9.2, 2.45 * nrow))
    for k, (im, t) in enumerate(panels):
        show_asinh(axes[k // ncol, k % ncol], im, t, "#333333")
    for k in range(len(panels), nrow * ncol):
        axes[k // ncol, k % ncol].axis("off")
    fig.suptitle("Frozen real benchmark: HST/ACS F814W SLACS (top) and S4TM (bottom) lenses",
                 fontsize=12.5, y=0.995)
    fig.subplots_adjust(hspace=0.28, wspace=0.06, top=0.94, bottom=0.02, left=0.02, right=0.98)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"fig_benchmark_gallery.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print("  wrote fig_benchmark_gallery.png/.pdf")


if __name__ == "__main__":
    print("Building paper figures ->", OUT)
    fig_real_vs_sim()
    fig_cao()
    fig_lemon()
    fig_gallery()
    print("done.")
