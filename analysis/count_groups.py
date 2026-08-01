#!/usr/bin/env python
"""Quantify DA-pool contamination: count multi-peak (galaxy group/pair)
systems and arc-visibility, vs the benchmark. A galaxy-galaxy lens should
have ONE dominant central deflector; multiple comparable bright peaks =
group/cluster-scale = wrong deflector class for our SIE/PEMD sim."""
import os

import h5py
import numpy as np
from scipy.ndimage import maximum_filter, gaussian_filter

HERE = os.path.dirname(os.path.abspath(__file__))


def robust_sky(img, s=16):
    v = np.concatenate([img[:s, :s].ravel(), img[:s, -s:].ravel(),
                        img[-s:, :s].ravel(), img[-s:, -s:].ravel()])
    for _ in range(3):
        m, sd = v.mean(), v.std()
        v = v[np.abs(v - m) < 3 * sd]
        if len(v) < 10:
            break
    return v.std() + 1e-9


def load(path):
    with h5py.File(path, "r") as f:
        key = "images" if "images" in f else "lensed"
        imgs = f[key][:].astype("float32")
        names = ([n.decode() if isinstance(n, bytes) else str(n)
                  for n in f["names"][:]] if "names" in f else None)
    if imgs.ndim == 4:
        imgs = imgs[:, 0]
    return imgs, names


def count_bright_peaks(img, sky):
    """Count distinct bright peaks (candidate galaxies) in the central region,
    each > 30*sky and separated by >8 px. Proxy for group/pair multiplicity."""
    n = img.shape[0]
    c = n // 2
    sm = gaussian_filter(img, 2.0)
    reg = sm[c - 40:c + 40, c - 40:c + 40]
    mx = maximum_filter(reg, size=9)
    peaks = (reg == mx) & (reg > 30 * sky)
    ys, xs = np.where(peaks)
    # greedy dedup within 8px
    kept = []
    order = np.argsort(-reg[ys, xs])
    for i in order:
        p = (ys[i], xs[i])
        if all(np.hypot(p[0] - q[0], p[1] - q[1]) > 8 for q in kept):
            kept.append(p)
    return len(kept)


def summarize(path, label):
    imgs, names = load(path)
    npk = []
    for img in imgs:
        sky = robust_sky(img)
        npk.append(count_bright_peaks(img, sky))
    npk = np.array(npk)
    print(f"\n=== {label} (N={len(imgs)}) ===")
    print(f"  single-peak (clean deflector): {int((npk==1).sum())} "
          f"({100*(npk==1).mean():.0f}%)")
    print(f"  2 peaks (pair):                {int((npk==2).sum())} "
          f"({100*(npk==2).mean():.0f}%)")
    print(f"  3+ peaks (group/cluster):      {int((npk>=3).sum())} "
          f"({100*(npk>=3).mean():.0f}%)")
    if names is not None:
        grp = [names[i] for i in np.where(npk >= 3)[0]]
        if grp:
            print(f"  group/cluster systems: {grp[:15]}")
    return npk


summarize(os.path.join(HERE, "real_dapool_images.h5"), "DA POOL")
for b, lab in [("real_slacs_images.h5", "BENCHMARK SLACS"),
               ("real_s4tm_images.h5", "BENCHMARK S4TM")]:
    bp = os.path.expanduser(f"~/code/LensFusion/audit/{b}")
    if os.path.exists(bp):
        summarize(bp, lab)
