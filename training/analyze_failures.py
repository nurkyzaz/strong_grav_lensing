#!/usr/bin/env python
"""
analyze_failures.py
Turn "R2<0" into a finding: WHICH lenses m3 fails on, and WHAT predicts failure.

Reads a predictions CSV (name, theta_E_pred_arcsec, theta_E_pub_arcsec) + the matching
cutout h5, computes per-lens image features, and correlates failure (|frac err|>15%)
with each. Outputs a feature table, diagnostic plots, and a gallery of the worst cases.

Features per lens:
  theta_E_pub      published SIE Einstein radius ["]
  frac_err         100*(pred-pub)/pub  [%]   (signed; <0 = under-prediction)
  peak_flux        robust central peak [e-/s] (lens brightness)
  sky_rms          sigma-clipped background RMS [e-/s]
  core_snr         peak_flux / sky_rms        (how bright the lens is vs noise)
  arc_contrast     asymmetry of the Einstein-ring annulus / sky_rms
                   (high => a visible, azimuthally-localised arc; low => buried/smooth)
  r_half_arcsec    half-light radius of the central galaxy ["] (compactness)
  n_neighbors      bright blobs off-centre (crowding)

Usage:
  python analyze_failures.py --preds brian_run/theta_E_slacs_peak20.csv --images real_slacs_images.h5 --tag slacs
  python analyze_failures.py --preds brian_run/theta_E_s4tm_peak20.csv  --images real_s4tm_images.h5  --tag s4tm
"""
import argparse, os
import numpy as np, pandas as pd, h5py
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import ndimage

try:
    from astropy.stats import sigma_clipped_stats
    def _skyrms(a):
        return float(sigma_clipped_stats(a, sigma=3.0, maxiters=5)[2])
except Exception:
    def _skyrms(a):
        m = np.median(a)
        for _ in range(5):
            s = np.std(a[np.abs(a - m) < 3 * np.std(a) + 1e-9])
            m = np.median(a[np.abs(a - m) < 3 * s + 1e-9])
        return float(s)

try:
    from scipy.stats import spearmanr
    def corr(x, y):
        return spearmanr(x, y, nan_policy="omit").correlation
except Exception:
    def corr(x, y):
        return float(np.corrcoef(np.argsort(np.argsort(x)), np.argsort(np.argsort(y)))[0, 1])


def features(img, theta_E, px):
    n = img.shape[-1]; c = n // 2
    yy, xx = np.indices(img.shape)
    rr = np.hypot(yy - c, xx - c)
    sky = _skyrms(img)
    core = img[c - n // 3:c + n // 3, c - n // 3:c + n // 3]
    peak = float(np.percentile(core, 99.9))
    # arc proxy: asymmetry in the Einstein-ring annulus
    rE = max(theta_E / px, 3.0)
    ann = img[(rr > rE - 2) & (rr < rE + 2)]
    arc_contrast = float((np.percentile(ann, 90) - np.percentile(ann, 50)) / (sky + 1e-9)) \
        if ann.size > 8 else np.nan
    # half-light radius within central aperture
    ap = rr < (n // 3)
    f = np.clip(img - np.median(img), 0, None)
    order = np.argsort(rr[ap])
    cum = np.cumsum(f[ap][order]); tot = cum[-1] + 1e-9
    r_half = float(rr[ap][order][np.searchsorted(cum, 0.5 * tot)] * px)
    # neighbours: bright blobs off-centre
    mask = img > (np.median(img) + 5 * sky)
    lab, nlab = ndimage.label(mask)
    nb = 0
    for k in range(1, nlab + 1):
        ys, xs = np.where(lab == k)
        if 3 <= len(ys) <= 300:
            d = np.hypot(ys.mean() - c, xs.mean() - c) * px
            if 1.0 < d < 3.0:
                nb += 1
    return dict(peak_flux=peak, sky_rms=sky, core_snr=peak / (sky + 1e-9),
                arc_contrast=arc_contrast, r_half_arcsec=r_half, n_neighbors=nb)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preds", required=True)
    ap.add_argument("--images", required=True)
    ap.add_argument("--tag", default="run")
    ap.add_argument("--fail_thresh", type=float, default=15.0)
    ap.add_argument("--topn", type=int, default=12)
    args = ap.parse_args()

    d = pd.read_csv(args.preds)
    with h5py.File(args.images) as f:
        names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]]
        imgs = f["images"][:].astype("float32")
        px = float(f.attrs.get("pixscale_arcsec", 0.05))
    if imgs.ndim == 4:
        imgs = imgs[:, 0]
    idx = {nm: i for i, nm in enumerate(names)}

    rows = []
    for _, r in d.iterrows():
        nm = str(r["name"])
        if nm not in idx or "theta_E_pub_arcsec" not in d.columns:
            continue
        pub = float(r["theta_E_pub_arcsec"]); pred = float(r["theta_E_pred_arcsec"])
        if pub <= 0:
            continue
        fr = 100 * (pred - pub) / pub
        feat = features(imgs[idx[nm]], pub, px)
        rows.append(dict(name=nm, theta_E_pub=pub, theta_E_pred=pred,
                         frac_err=fr, abs_frac=abs(fr),
                         fail=int(abs(fr) > args.fail_thresh), **feat))
    F = pd.DataFrame(rows)
    out_csv = f"failure_features_{args.tag}.csv"
    F.to_csv(out_csv, index=False)

    feats = ["theta_E_pub", "peak_flux", "core_snr", "arc_contrast", "r_half_arcsec", "n_neighbors"]
    print(f"\n=== {args.tag}: N={len(F)}  failures(|frac|>{args.fail_thresh:.0f}%)="
          f"{F.fail.sum()} ({100*F.fail.mean():.0f}%) ===")
    print("Spearman corr of |frac err| with each feature (|rho|>~0.3 is a real driver):")
    for c in feats:
        print(f"  {c:16s} rho = {corr(F[c], F.abs_frac):+.2f}")
    # failure rate by theta_E tertile
    F["thirds"] = pd.qcut(F.theta_E_pub, 3, labels=["low θ_E", "mid θ_E", "high θ_E"])
    print("\nfailure rate by theta_E tertile:")
    for g, sub in F.groupby("thirds", observed=True):
        print(f"  {g:9s} [{sub.theta_E_pub.min():.2f}-{sub.theta_E_pub.max():.2f}\"]  "
              f"fail {100*sub.fail.mean():3.0f}%  median frac {sub.frac_err.median():+.0f}%")

    # diagnostic plots
    fig, ax = plt.subplots(2, 2, figsize=(11, 9))
    cols = np.where(F.fail.values, "tab:red", "tab:blue")
    ax[0, 0].scatter(F.theta_E_pub, F.frac_err, c=cols, s=22)
    ax[0, 0].axhline(0, ls="--", c="k", lw=.8); ax[0, 0].axhline(15, ls=":", c="grey")
    ax[0, 0].axhline(-15, ls=":", c="grey")
    ax[0, 0].set_xlabel("true theta_E [\"]"); ax[0, 0].set_ylabel("frac err [%]")
    ax[0, 0].set_title("error vs theta_E (red=fail)")
    ax[0, 1].scatter(F.arc_contrast, F.abs_frac, c=cols, s=22)
    ax[0, 1].set_xlabel("arc_contrast (ring asymmetry / sky)"); ax[0, 1].set_ylabel("|frac err| [%]")
    ax[0, 1].set_title("error vs arc visibility")
    ax[1, 0].scatter(F.core_snr, F.abs_frac, c=cols, s=22)
    ax[1, 0].set_xlabel("core SNR (peak/sky)"); ax[1, 0].set_ylabel("|frac err| [%]")
    ax[1, 0].set_title("error vs lens brightness")
    ax[1, 1].scatter(F.r_half_arcsec, F.abs_frac, c=cols, s=22)
    ax[1, 1].set_xlabel("half-light radius [\"]"); ax[1, 1].set_ylabel("|frac err| [%]")
    ax[1, 1].set_title("error vs compactness")
    plt.tight_layout(); plt.savefig(f"failure_diagnostics_{args.tag}.png", dpi=120)

    # gallery of worst cases
    worst = F.sort_values("abs_frac", ascending=False).head(args.topn)
    cols_g = 4; rows_g = -(-len(worst) // cols_g)
    fig, ax = plt.subplots(rows_g, cols_g, figsize=(cols_g * 2.6, rows_g * 2.6))
    for a in np.atleast_1d(ax).ravel(): a.axis("off")
    for a, (_, r) in zip(np.atleast_1d(ax).ravel(), worst.iterrows()):
        im = imgs[idx[r["name"]]]
        s = np.arcsinh((im - np.median(im)) / (np.std(im) + 1e-8))
        a.imshow(s, origin="lower", cmap="gray")
        a.set_title(f"{r['name']}\ntrue {r.theta_E_pub:.2f} pred {r.theta_E_pred:.2f} "
                    f"({r.frac_err:+.0f}%)", fontsize=7)
    plt.tight_layout(); plt.savefig(f"failure_gallery_{args.tag}.png", dpi=120)
    print(f"\nwrote {out_csv}, failure_diagnostics_{args.tag}.png, failure_gallery_{args.tag}.png")


if __name__ == "__main__":
    main()
