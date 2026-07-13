#!/usr/bin/env python
"""
diagnose_real_slacs.py
----------------------
Overlay published vs predicted theta_E rings on each real cutout, so we can SEE why
a lens succeeds or fails (clean ring vs faint arc vs bright neighbour vs lens-light).
Reads real_slacs_images.h5 + a predictions CSV from test_real_slacs.py.
  green ring  = published theta_E (SIE bSIE)
  red ring    = CNN theta_E (kappa_bar=1)
"""
import argparse, numpy as np, h5py, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle


def asinh_disp(img, soft=0.02, lo=1.0, hi=99.7):
    fin = img[np.isfinite(img)]
    if fin.size == 0: return np.zeros_like(img)
    vlo, vhi = np.percentile(fin, [lo, hi])
    x = np.clip((img - vlo) / max(vhi - vlo, 1e-9), 0, None)
    x = np.arcsinh(x / soft)
    hi2 = np.percentile(x[np.isfinite(x)], 99.7)
    return np.nan_to_num(np.clip(x, 0, hi2) / (hi2 + 1e-9))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", default="real_slacs_images.h5")
    ap.add_argument("--csv", default="real_peak20.csv")
    ap.add_argument("--out", default="diagnose_real_slacs.png")
    args = ap.parse_args()

    with h5py.File(args.images, "r") as f:
        images = f["images"][:]
        names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]]
        theta_pub = f["theta_E_pub"][:].astype("float32")
        box = float(f.attrs.get("box_arcsec", 6.4))
    pixels = images.shape[-1]
    pix = box / (pixels - 1)
    cen = (pixels - 1) / 2.0

    df = pd.read_csv(args.csv).set_index("name")
    N = len(images); ncol = 5; nrow = int(np.ceil(N / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(2.6 * ncol, 2.6 * nrow))
    axes = np.atleast_1d(axes).ravel()

    for i in range(N):
        ax = axes[i]
        ax.imshow(asinh_disp(images[i, 0]), origin="lower", cmap="gray")
        tp = theta_pub[i]
        pr = float(df.loc[names[i], "theta_E_pred"]) if names[i] in df.index else np.nan
        ax.add_patch(Circle((cen, cen), tp / pix, fill=False, ec="lime", lw=1.3, alpha=0.9))
        if np.isfinite(pr):
            ax.add_patch(Circle((cen, cen), pr / pix, fill=False, ec="red", lw=1.3, alpha=0.9, ls="--"))
        fe = 100 * (pr - tp) / tp if np.isfinite(pr) else np.nan
        ax.set_title(f"{names[i]}\npub {tp:.2f} / pred {pr:.2f} ({fe:+.0f}%)", fontsize=7)
        ax.set_xticks([]); ax.set_yticks([])
    for j in range(N, len(axes)): axes[j].axis("off")
    fig.suptitle("green = published theta_E (SIE) | red dashed = CNN theta_E (kappa_bar=1)", fontsize=10)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(args.out, dpi=120)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
