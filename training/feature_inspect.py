#!/usr/bin/env python
"""
feature_inspect.py  -  answer Brian's request: 'inspect the cases where the model
fails and check what common image features affect the prediction.'

Correlates per-lens prediction and signed error against concrete image features
(lens-light proxy, total flux, arc flux, contrast, peak) and dumps a worst-case
montage. Run on the SAME h5 the predictions came from (raw is Brian's pipeline).

Usage:
  python feature_inspect.py --preds real_slacs_images_preds.csv \
                            --h5 real_slacs_images.h5 [--pixscale 0.05]

Needs a *_preds.csv with columns theta_true,theta_pred in h5 row order
(produced by test_hstempty_slacs.py after the CSV patch).
"""
import argparse
import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preds", required=True)
    ap.add_argument("--h5", required=True)
    ap.add_argument("--pixscale", type=float, default=0.05)
    ap.add_argument("--out", default="feature_inspect.png")
    args = ap.parse_args()

    a = np.genfromtxt(args.preds, delimiter=",", names=True)
    t = np.asarray(a["theta_true"], float)
    p = np.asarray(a["theta_pred"], float)
    err = 100.0 * (p - t) / t

    with h5py.File(args.h5, "r") as h:
        key = "images" if "images" in h else list(h.keys())[0]
        imgs = np.asarray(h[key]).astype(float)
        names = ([n.decode() if isinstance(n, bytes) else str(n) for n in h["names"][:]]
                 if "names" in h else [str(i) for i in range(len(imgs))])
    if imgs.ndim == 4:
        imgs = imgs[:, 0]

    H = imgs.shape[1]
    yy, xx = np.mgrid[0:H, 0:H]
    r = np.hypot(xx - (H - 1) / 2.0, yy - (H - 1) / 2.0)
    core = r < (0.5 / args.pixscale)               # central ~0.5" = lens-light proxy
    annulus = (r >= (0.5 / args.pixscale)) & (r < (1.7 / args.pixscale))

    feats = {}
    feats["core_flux"] = np.array([im[core].sum() for im in imgs])
    feats["arc_flux"] = np.array([im[annulus].sum() for im in imgs])
    feats["total_flux"] = np.array([im.sum() for im in imgs])
    feats["peak"] = np.array([im.max() for im in imgs])
    feats["core_frac"] = feats["core_flux"] / (feats["total_flux"] + 1e-9)
    feats["core_over_arc"] = feats["core_flux"] / (np.abs(feats["arc_flux"]) + 1e-9)

    print(f"\nN={len(t)}  pixscale={args.pixscale}\"/px")
    print(f"true median={np.median(t):.3f}  pred median={np.median(p):.3f}  "
          f"median frac={np.median(err):+.1f}%\n")
    print(f"{'feature':14s} {'corr(feat,pred)':>16s} {'corr(feat,signed_err)':>22s} "
          f"{'corr(feat,|err|)':>18s}")
    for name, v in feats.items():
        cp = np.corrcoef(v, p)[0, 1]
        ce = np.corrcoef(v, err)[0, 1]
        ca = np.corrcoef(v, np.abs(err))[0, 1]
        flag = "  <== strong" if max(abs(cp), abs(ce)) > 0.5 else ""
        print(f"{name:14s} {cp:>16.2f} {ce:>22.2f} {ca:>18.2f}{flag}")

    print("\nRead: a strong negative corr(core_flux, pred) means bright lens light "
          "pushes the prediction DOWN (the raw collapse). A strong corr(feature, |err|) "
          "names the image property that breaks the model.\n")

    # montage of the 8 worst by |err|
    order = np.argsort(-np.abs(err))[:8]
    fig, axes = plt.subplots(2, 4, figsize=(14, 7.5))
    for ax, i in zip(axes.ravel(), order):
        ax.imshow(np.arcsinh(imgs[i]), cmap="gray", origin="lower")
        c = plt.Circle(((H - 1) / 2, (H - 1) / 2), 0.5 / args.pixscale,
                       fill=False, color="r", lw=1)
        ax.add_patch(c)
        ax.set_title(f"{names[i]}\ntrue {t[i]:.2f}  pred {p[i]:.2f}  "
                     f"{err[i]:+.0f}%\ncore_frac {feats['core_frac'][i]:.2f}",
                     fontsize=9)
        ax.axis("off")
    fig.suptitle("Worst-8 failures (red = central 0.5\" lens-light region)", fontsize=12)
    fig.tight_layout()
    fig.savefig(args.out, dpi=120)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
