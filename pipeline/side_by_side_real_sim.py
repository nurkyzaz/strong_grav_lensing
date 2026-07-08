#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Side-by-side visual: real SLACS benchmark cutouts (top rows) vs current
paltas pilot images (bottom rows), SAME asinh(img/sky_rms) stretch on both,
so the comparison cannot be a display artifact. Read-only.

    python side_by_side_real_sim.py --real ~/einstein_cnn/real_slacs_images.h5 \
        --sim ~/einstein_cnn/pilot200b.h5 --n 8 --out real_vs_sim.png
"""
import argparse
import os

import h5py
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def robust_sky(img, s=16):
    corners = [img[:s, :s], img[:s, -s:], img[-s:, :s], img[-s:, -s:]]
    stds = []
    for c in corners:
        v = c.ravel()
        for _ in range(3):
            m, sd = v.mean(), v.std()
            v = v[np.abs(v - m) < 3 * sd]
            if len(v) < 10:
                break
        stds.append(v.std() if len(v) else np.nan)
    return np.nanmedian(stds)


def stretch(img):
    sky = robust_sky(img)
    if not np.isfinite(sky) or sky <= 0:
        sky = np.std(img[:16, :16]) or 1.0
    return np.arcsinh(img / sky)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--real", required=True)
    p.add_argument("--sim", required=True)
    p.add_argument("--n", type=int, default=8)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default="real_vs_sim.png")
    args = p.parse_args()

    rng = np.random.default_rng(args.seed)

    with h5py.File(os.path.expanduser(args.real), "r") as f:
        key = "images" if "images" in f else "lensed"
        R = f[key][:]
        names = ([n.decode() if isinstance(n, bytes) else str(n)
                  for n in f["names"][:]] if "names" in f else None)
    if R.ndim == 4:
        R = R[:, 0]
    ri = rng.choice(len(R), size=min(args.n, len(R)), replace=False)

    with h5py.File(os.path.expanduser(args.sim), "r") as f:
        S = f["lensed"][:]
        th = f["theta_E"][:] if "theta_E" in f else None
    si = rng.choice(len(S), size=min(args.n, len(S)), replace=False)

    n = args.n
    fig, axes = plt.subplots(4, n // 2, figsize=(2.2 * n // 2, 9.5))
    for j in range(n):
        ax = axes[j // (n // 2)][j % (n // 2)]
        ax.imshow(stretch(R[ri[j]]), cmap="gray", origin="lower")
        title = names[ri[j]] if names else f"real #{ri[j]}"
        ax.set_title(f"REAL {title}", fontsize=7, color="darkorange")
        ax.axis("off")
    for j in range(n):
        ax = axes[2 + j // (n // 2)][j % (n // 2)]
        ax.imshow(stretch(S[si[j]]), cmap="gray", origin="lower")
        t = f" th_E={th[si[j]]:.2f}" if th is not None else ""
        ax.set_title(f"SIM #{si[j]}{t}", fontsize=7, color="steelblue")
        ax.axis("off")
    fig.suptitle(f"Real SLACS (top 2 rows) vs {os.path.basename(args.sim)} "
                 "(bottom 2 rows) -- identical asinh(img/sky_rms) stretch",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(args.out, dpi=130)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
