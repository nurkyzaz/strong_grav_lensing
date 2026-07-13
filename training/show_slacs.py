#!/usr/bin/env python
"""
show_slacs.py  -  eyeball check that the real SLACS cutouts are genuine, centered,
and on the right scale. Draws each image with an asinh (high-contrast) stretch so
faint arcs become visible, and overlays a red circle at the PUBLISHED Einstein
radius. If these are real correctly-prepared lenses you should see: a bright central
galaxy, and a faint arc/ring sitting near the red circle.

Usage:
  python show_slacs.py --h5 real_slacs_images.h5 --pixscale 0.05 --n 16
"""
import argparse
import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h5", default="real_slacs_images.h5")
    ap.add_argument("--pixscale", type=float, default=0.05)
    ap.add_argument("--n", type=int, default=16)
    ap.add_argument("--out", default="show_slacs.png")
    args = ap.parse_args()

    with h5py.File(args.h5, "r") as h:
        key = "images" if "images" in h else list(h.keys())[0]
        imgs = np.asarray(h[key]).astype(float)
        names = ([n.decode() if isinstance(n, bytes) else str(n) for n in h["names"][:]]
                 if "names" in h else [str(i) for i in range(len(imgs))])
        tE = (np.asarray(h["theta_E_pub"], float) if "theta_E_pub" in h
              else np.full(len(imgs), np.nan))
    if imgs.ndim == 4:
        imgs = imgs[:, 0]

    n = min(args.n, len(imgs))
    cols = 4
    rows = int(np.ceil(n / cols))
    H = imgs.shape[1]
    cen = (H - 1) / 2.0

    fig, axes = plt.subplots(rows, cols, figsize=(3.2 * cols, 3.3 * rows))
    for ax, i in zip(np.atleast_1d(axes).ravel(), range(n)):
        im = imgs[i]
        # asinh stretch scaled to the image's own bright tail -> faint arcs show up
        s = np.percentile(im, 99.5)
        disp = np.arcsinh(im / (s + 1e-9))
        ax.imshow(disp, cmap="gray", origin="lower",
                  vmin=np.percentile(disp, 5), vmax=np.percentile(disp, 99.8))
        if np.isfinite(tE[i]):
            r_pix = tE[i] / args.pixscale
            ax.add_patch(plt.Circle((cen, cen), r_pix, fill=False, color="r", lw=1.2))
        ax.set_title(f"{names[i]}   theta_E={tE[i]:.2f}\"", fontsize=9)
        ax.axis("off")
    for ax in np.atleast_1d(axes).ravel()[n:]:
        ax.axis("off")
    fig.suptitle("Real SLACS cutouts (asinh stretch). Red = published Einstein radius.\n"
                 "Expect a bright central galaxy + a faint arc near the red circle.",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(args.out, dpi=110)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
