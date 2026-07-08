#!/usr/bin/env python
"""
inspect_training.py  -  the inspection we never did: do the HSTempty TRAINING arcs
actually look like real arcs, or are many of them single 'blobs' (source landed off
the caustic -> not strongly lensed but still labelled with a theta_E)?

For a random sample of training images it measures, at the labelled Einstein radius,
the AZIMUTHAL COVERAGE = fraction of angles around the ring that carry real flux.
  high coverage  -> a genuine arc/ring
  low  coverage  -> a blob / point source / non-lens (injection contamination)
Then montages training images and, for comparison, real SLACS subtracted arcs.

Usage:
  python inspect_training.py --train lensed_hstempty.h5 --labels labels_train_singleband.h5 \
      --real real_slacs_residual_v2.h5 --pixscale 0.05 --k 2000
"""
import argparse
import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def azimuthal_coverage(im, tE_pix, pixscale, nang=36, dr=3.0):
    H = im.shape[0]
    cen = (H - 1) / 2.0
    yy, xx = np.mgrid[0:H, 0:H]
    r = np.hypot(xx - cen, yy - cen)
    th = (np.degrees(np.arctan2(yy - cen, xx - cen)) + 360) % 360
    outer = r > (2.5 / pixscale)
    bg_med = np.median(im[outer]) if outer.sum() > 20 else 0.0
    bg_sig = np.std(im[outer]) if outer.sum() > 20 else (im.std() + 1e-9)
    thr = bg_med + 3 * bg_sig
    ring = np.abs(r - tE_pix) < dr
    if ring.sum() < nang:
        return 0.0, (im.max() - bg_med) / (bg_sig + 1e-9)
    bins = (th[ring] / (360.0 / nang)).astype(int)
    vals = im[ring]
    covered = 0
    for b in range(nang):
        m = bins == b
        if m.any() and vals[m].max() > thr:
            covered += 1
    return covered / nang, (im.max() - bg_med) / (bg_sig + 1e-9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="lensed_hstempty.h5")
    ap.add_argument("--labels", default="labels_train_singleband.h5")
    ap.add_argument("--real", default="real_slacs_residual_v2.h5")
    ap.add_argument("--pixscale", type=float, default=0.05)
    ap.add_argument("--k", type=int, default=2000)
    ap.add_argument("--out", default="inspect_training.png")
    args = ap.parse_args()

    # labels: kappa_index -> theta_E
    with h5py.File(args.labels, "r") as h:
        lk = next(k for k in h.keys() if "kappa" in k.lower() and "index" in k.lower())
        lt = next(k for k in h.keys() if "theta" in k.lower() or k.lower() in ("tE", "te"))
        kidx = np.asarray(h[lk]).astype(int)
        tE = np.asarray(h[lt]).astype(float)
    lab = dict(zip(kidx, tE))

    with h5py.File(args.train, "r") as h:
        ik = "lensed" if "lensed" in h else list(h.keys())[0]
        N = h[ik].shape[0]
        tk = next((k for k in h.keys() if "kappa" in k.lower() and "index" in k.lower()), None)
        k = min(args.k, N)
        sel = np.sort(np.random.choice(N, k, replace=False))
        imgs = h[ik][sel]
        kk = np.asarray(h[tk])[sel].astype(int) if tk else None
    imgs = imgs[:, 0] if imgs.ndim == 4 else imgs

    tEs = np.array([lab.get(int(kk[i]), np.nan) if kk is not None else np.nan
                    for i in range(len(imgs))])
    have = np.isfinite(tEs)
    cov = np.zeros(len(imgs))
    snr = np.zeros(len(imgs))
    for i in range(len(imgs)):
        if not have[i]:
            continue
        cov[i], snr[i] = azimuthal_coverage(imgs[i], tEs[i] / args.pixscale, args.pixscale)

    c = cov[have]
    print(f"\nInspected {have.sum()} training images.")
    print(f"  azimuthal coverage at theta_E:  median={np.median(c):.2f}  "
          f"mean={c.mean():.2f}")
    print(f"  fraction with coverage < 0.15 (blob / non-arc):  {np.mean(c < 0.15):.1%}")
    print(f"  fraction with coverage < 0.30 (weak/partial arc): {np.mean(c < 0.30):.1%}")
    print(f"  fraction with coverage > 0.60 (clear ring/arc):   {np.mean(c > 0.60):.1%}")
    print(f"  peak SNR: median={np.median(snr[have]):.0f}  p5={np.percentile(snr[have],5):.0f}\n")

    # montage: 8 worst-coverage + 4 typical training, then 4 real SLACS
    idx_have = np.where(have)[0]
    worst = idx_have[np.argsort(cov[idx_have])[:8]]
    typ = idx_have[np.argsort(np.abs(cov[idx_have] - np.median(c)))[:4]]
    with h5py.File(args.real, "r") as h:
        rimg = np.asarray(h["images"])[:4]
        rt = np.asarray(h["theta_E_pub"])[:4] if "theta_E_pub" in h else [np.nan] * 4
    rimg = rimg[:, 0] if rimg.ndim == 4 else rimg

    fig, axes = plt.subplots(4, 4, figsize=(13, 13))
    panels = ([("train low-cov", i) for i in worst] +
              [("train typical", i) for i in typ] +
              [("REAL SLACS", j) for j in range(4)])
    for ax, (tag, i) in zip(axes.ravel(), panels):
        if tag == "REAL SLACS":
            im = rimg[i]; title = f"REAL {i}  tE={float(rt[i]):.2f}"
        else:
            im = imgs[i]; title = f"{tag}\ntE={tEs[i]:.2f} cov={cov[i]:.2f}"
        s = np.percentile(np.abs(im), 99.5) + 1e-9
        ax.imshow(np.arcsinh(im / s), cmap="gray", origin="lower")
        ax.set_title(title, fontsize=8)
        ax.axis("off")
    fig.suptitle("Rows 1-2: worst-coverage TRAINING arcs (blob check). "
                 "Row 3: typical TRAINING. Row 4: REAL SLACS.", fontsize=11)
    fig.tight_layout()
    fig.savefig(args.out, dpi=110)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
