#!/usr/bin/env python
"""AR0 — the arc-realism gate: quantitative sim-vs-real ARC morphology
comparison, same estimator both sides (the gate_stage0 philosophy applied to
the arc annulus instead of the whole image).

Per image (needs theta_E: label for sim, published b_SIE for real):
  1. subtract the azimuthal median at each radius (kills the smooth deflector),
  2. in the annulus r in [0.6, 1.4] * theta_E, measure on the residual:
     - arc_contrast : max 20-deg-sector mean / robust sky sigma
     - asym90       : fraction of positive annulus flux in the brightest 90 deg
     - n_knots      : connected residual peaks > 2.5 sigma (min 4 px) in annulus
     - arc_width    : radial FWHM of the residual at the brightest azimuth [px]
  3. report sim-vs-real medians + 16-84% and a PASS/FLAG per metric
     (PASS = sim median inside real 16-84 band; baseline-recording run).

Usage:
  ar0_arc_gate.py --sim train_g3b_100k.h5 --real euclid_slacs_images_g3.h5 \
      --labels real_lens_labels.csv --n 500 --tag euclid_g3
"""
import argparse
import csv
import os

import h5py
import numpy as np
from scipy import ndimage

ap = argparse.ArgumentParser()
ap.add_argument("--sim", required=True)
ap.add_argument("--real", required=True)
ap.add_argument("--labels", default=os.path.expanduser("~/einstein_cnn/real_lens_labels.csv"))
ap.add_argument("--n", type=int, default=500)
ap.add_argument("--tag", default="ar0")
ap.add_argument("--pix", type=float, default=0.05)
a = ap.parse_args()


def metrics(img, theta_pix):
    if img.ndim == 3:
        img = img[0]
    n = img.shape[0]
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c)
    phi = np.degrees(np.arctan2(yy - c, xx - c)) % 360.0
    # robust sky from the image corners (r > 0.45 n)
    sky = img[r > 0.45 * n]
    lo, med_s, hi = np.percentile(sky, [16, 50, 84])
    sig = max((hi - lo) / 2.0, 1e-9)
    # azimuthal-median radial model -> residual
    rb = np.clip(r.astype(int), 0, n // 2)
    prof = np.array([np.median(img[rb == k]) if (rb == k).any() else 0.0
                     for k in range(n // 2 + 1)])
    resid = img - prof[rb]
    ann = (r >= 0.6 * theta_pix) & (r <= 1.4 * theta_pix)
    if ann.sum() < 40:
        return None
    # 20-deg sector means
    sect = np.array([resid[ann & (phi >= p) & (phi < p + 20)].mean()
                     if (ann & (phi >= p) & (phi < p + 20)).any() else 0.0
                     for p in range(0, 360, 20)])
    contrast = sect.max() / sig
    # brightest 90 deg window (sliding over the 18 sectors, window 4-5 sectors)
    pos = np.clip(resid[ann], 0, None).sum()
    best90 = 0.0
    for s0 in range(18):
        w = [(s0 + k) % 18 for k in range(5)]
        m = ann & np.isin((phi // 20).astype(int), w)
        best90 = max(best90, np.clip(resid[m], 0, None).sum())
    asym90 = best90 / max(pos, 1e-9)
    # knots
    lab, nl = ndimage.label((resid > 2.5 * sig) & ann)
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, nl + 1))
    n_knots = int((sizes >= 4).sum())
    # radial width at brightest azimuth
    p0 = 20 * int(np.argmax(sect))
    m = (phi >= p0) & (phi < p0 + 20)
    rr = np.arange(int(0.3 * theta_pix), int(min(1.8 * theta_pix, n // 2)))
    rad = np.array([resid[m & (rb == k)].mean() if (m & (rb == k)).any() else 0.0
                    for k in rr])
    if rad.max() <= 0:
        width = np.nan
    else:
        above = rad > rad.max() / 2.0
        width = float(above.sum())
    return contrast, asym90, n_knots, width


def collect(fn, thetas, nmax, key_pref=("images", "lensed")):
    out = []
    with h5py.File(fn, "r") as f:
        key = next(k for k in key_pref if k in f)
        n = f[key].shape[0]
        idx = (np.arange(n) if n <= nmax else
               np.random.default_rng(3).choice(n, nmax, replace=False))
        idx = np.sort(idx)
        for i in idx:
            th = thetas[i] if hasattr(thetas, "__len__") else thetas
            if not np.isfinite(th) or th <= 0:
                continue
            m = metrics(f[key][i].astype("float64"), th / a.pix)
            if m is not None:
                out.append(m)
    return np.array(out)


# real: theta_E_pub is carried inside the benchmark h5 (verified); fall back
# to the labels CSV via names if ever absent
with h5py.File(a.real, "r") as f:
    if "theta_E_pub" in f:
        th_real = f["theta_E_pub"][:].astype("float64")
    else:
        names = [x.decode() if isinstance(x, bytes) else str(x)
                 for x in f["names"][:]]
        lab = {r["name"]: float(r["theta_E_pub"])
               for r in csv.DictReader(open(a.labels))}
        th_real = np.array([lab.get(nm, np.nan) for nm in names])
real = collect(a.real, th_real, 10 ** 9)

with h5py.File(a.sim, "r") as f:
    th_sim = f["theta_E"][:]
sim = collect(a.sim, th_sim, a.n)

print("AR0 arc gate [%s]  sim n=%d  real n=%d" % (a.tag, len(sim), len(real)))
labels = ("arc_contrast", "asym90", "n_knots", "arc_width_px")
for k, name in enumerate(labels):
    rs = real[:, k][np.isfinite(real[:, k])]
    ss = sim[:, k][np.isfinite(sim[:, k])]
    r16, r50, r84 = np.percentile(rs, [16, 50, 84])
    s50 = np.median(ss)
    verdict = "PASS" if r16 <= s50 <= r84 else "FLAG"
    print("  %-14s sim med %6.2f | real med %6.2f [%.2f, %.2f]  -> %s"
          % (name, s50, r50, r16, r84, verdict))
print("AR0_DONE")
