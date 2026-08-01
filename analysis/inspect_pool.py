#!/usr/bin/env python
"""Diagnose the DA pool cutouts: render a gallery under three stretches and
compute objective quality metrics vs the benchmark SLACS cutouts.

Question being answered (Nurkyz 2026-07-07): are the 104 DA-pool cutouts
actually lenses with visible arcs, properly centred — or junk that would make
the MMD target distribution meaningless?"""
import os

import h5py
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))


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


def load(path):
    with h5py.File(path, "r") as f:
        key = "images" if "images" in f else "lensed"
        imgs = f[key][:].astype("float32")
        names = ([n.decode() if isinstance(n, bytes) else str(n)
                  for n in f["names"][:]] if "names" in f else None)
    if imgs.ndim == 4:
        imgs = imgs[:, 0]
    return imgs, names


def metrics(imgs):
    """Per-image quality proxies."""
    out = []
    n = imgs.shape[1]
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c)
    for img in imgs:
        sky = robust_sky(img)
        if not np.isfinite(sky) or sky <= 0:
            sky = np.std(img[:16, :16]) + 1e-9
        # central peak / sky (is there a lens galaxy at the centre?)
        central = img[c - 8:c + 8, c - 8:c + 8]
        peak_sky = central.max() / sky
        # "arc-ish" flux: significant pixels in the 0.5-2.0" annulus (10-40 px)
        ann = (r >= 10) & (r <= 40)
        arc_frac = float(np.mean(img[ann] > 3 * sky))
        # is the brightest central pixel actually near centre?
        cy, cx = np.unravel_index(
            np.argmax(img[c - 20:c + 20, c - 20:c + 20]), (40, 40))
        off = np.hypot(cy - 20, cx - 20)
        out.append((peak_sky, arc_frac, off, sky))
    return np.array(out)


def gallery(imgs, names, path, title, ncol=8, nrow=8):
    fig, axes = plt.subplots(nrow, ncol, figsize=(ncol * 1.5, nrow * 1.5))
    for i, ax in enumerate(axes.ravel()):
        if i >= len(imgs):
            ax.axis("off"); continue
        sky = robust_sky(imgs[i])
        if not np.isfinite(sky) or sky <= 0:
            sky = np.std(imgs[i][:16, :16]) + 1e-9
        ax.imshow(np.arcsinh(imgs[i] / sky), cmap="gray", origin="lower")
        nm = names[i] if names else str(i)
        ax.set_title(nm, fontsize=5)
        ax.axis("off")
    fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    print("wrote", path)


pool, pool_names = load(os.path.join(HERE, "real_dapool_images.h5"))
print(f"pool: {pool.shape}")
gallery(pool[:64], pool_names[:64] if pool_names else None,
        os.path.join(HERE, "dapool_gallery_1.png"), "DA pool 1-64 (asinh)")
gallery(pool[64:], pool_names[64:] if pool_names else None,
        os.path.join(HERE, "dapool_gallery_2.png"), "DA pool 65-104 (asinh)")

pm = metrics(pool)
print("\n=== DA POOL quality (N=%d) ===" % len(pool))
print(f"central peak/sky:  median {np.median(pm[:,0]):.0f}  "
      f"16-84% [{np.percentile(pm[:,0],16):.0f}, {np.percentile(pm[:,0],84):.0f}]")
print(f"arc-annulus >3sig frac: median {np.median(pm[:,1]):.3f}  "
      f"(fraction of images with >2% arc pixels: {np.mean(pm[:,1]>0.02):.2f})")
print(f"centre offset [px]: median {np.median(pm[:,2]):.1f}  "
      f"(fraction >5px off: {np.mean(pm[:,2]>5):.2f})")

# how many look empty / non-detections
empty = (pm[:, 0] < 20)
print(f"\nlikely EMPTY/faint (peak/sky < 20): {int(empty.sum())}/{len(pool)}")
if pool_names and empty.any():
    print("  ->", [pool_names[i] for i in np.where(empty)[0]])

# compare against benchmark SLACS
for bench in ["real_slacs_images.h5", "real_s4tm_images.h5"]:
    bp = os.path.expanduser(f"~/code/LensFusion/audit/{bench}")
    if not os.path.exists(bp):
        continue
    bimgs, _ = load(bp)
    bm = metrics(bimgs)
    print(f"\n=== BENCHMARK {bench} (N={len(bimgs)}) for reference ===")
    print(f"central peak/sky:  median {np.median(bm[:,0]):.0f}")
    print(f"arc-annulus frac:  median {np.median(bm[:,1]):.3f}  "
          f"(>2%: {np.mean(bm[:,1]>0.02):.2f})")
