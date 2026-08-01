#!/usr/bin/env python
"""Measure a GEN5 pilot h5 against the real-Q1 targets (Phase 1 loop).

Reports the two Phase-0/Phase-1 target metrics for any pilot euclid h5:
  - field companions (detected, same estimator as phase0_characterize)
  - deflector Re (arcsec)
  - arc smoothness (n_beads / roughness / duty_cycle, from arc_smoothness)
Real-Q1 reference targets (measured): field comp med 2 / frac>4 8%;
deflector Re 0.56"; n_beads med 2 / roughness 0.72 / duty 0.31.

Usage: python analysis/measure_pilot.py <pilot.h5> [img_key] [theta_key]
"""
import sys

import h5py
import numpy as np
from scipy.ndimage import gaussian_filter, label

from arc_smoothness import smoothness  # same dir

PIX = 0.05
REAL = dict(comp_med=2, comp_frac4=8, re=0.56, beads=2, rough=0.72, duty=0.31)


def _sky(img, s=12):
    c = np.concatenate([img[:s, :s].ravel(), img[:s, -s:].ravel(),
                        img[-s:, :s].ravel(), img[-s:, -s:].ravel()])
    return np.median(c), max(1.4826 * np.median(np.abs(c - np.median(c))), 1e-9)


def analyze_companions(img, theta_pub):
    """Detected field-companion count + deflector Re("), same recipe as
    analysis/phase0_characterize.py. Returns (ncomp, re_as) or (None, None)."""
    n = img.shape[0]
    cframe = (n - 1) / 2.0
    sky, rms = _sky(img)
    g = img.astype(float) - sky
    gs = gaussian_filter(g, 1.2)
    lab, nlab = label(gs > 4 * rms)
    yy, xx = np.mgrid[0:n, 0:n]
    blobs = []
    for i in range(1, nlab + 1):
        m = lab == i
        if m.sum() < 5:
            continue
        blobs.append(dict(peak=float(gs[m].max()), cy=yy[m].mean(), cx=xx[m].mean(),
                          r=float(np.hypot(yy[m].mean() - cframe, xx[m].mean() - cframe))))
    if not blobs:
        return None, None
    defl = min(sorted(blobs, key=lambda b: -b["peak"])[:3], key=lambda b: b["r"])
    cy, cx = defl["cy"], defl["cx"]
    rr = np.hypot(yy - cy, xx - cx)
    within = rr < 30
    f = np.clip(g, 0, None) * within
    order = np.argsort(rr[within])
    cum = np.cumsum(f[within][order])
    re_px = float(rr[within][order][np.searchsorted(cum, 0.5 * cum[-1])]) if cum[-1] > 0 else np.nan
    rE = theta_pub / PIX
    if not (2.0 < rE < 0.48 * n):
        rE = 0.3 * n
    r_in, r_out = 0.55 * rE, 1.5 * rE
    ncomp = 0
    for b in blobs:
        if b is defl:
            continue
        br = np.hypot(b["cy"] - cy, b["cx"] - cx)
        if br > r_out or br < r_in * 0.5:
            ncomp += 1
    return ncomp, re_px * PIX


def measure(path, ikey, tkey):
    f = h5py.File(path, "r")
    ims = f[ikey][:]
    th = f[tkey][:] if tkey in f else np.full(len(ims), np.nan)
    comp, re_as, beads, rough, duty = [], [], [], [], []
    for i, im in enumerate(ims):
        im = np.asarray(im, float)
        c, r = analyze_companions(im, float(th[i]))
        if c is not None:
            comp.append(c)
            re_as.append(r)
        s = smoothness(im, float(th[i]))
        if s["n_beads"] != "":
            beads.append(s["n_beads"])
            rough.append(s["roughness"])
            duty.append(s["duty_cycle"])
    comp = np.array(comp, float)
    print("\n== %s (N=%d) ==" % (path.split("/")[-1], len(ims)))
    print("  field companions: q10/50/90 = %s  frac>4 = %d%%   [real: 2 / 8%%]"
          % (np.percentile(comp, [10, 50, 90]).astype(int), int(100 * (comp > 4).mean())))
    print("  deflector Re:     med %.3f\"                       [real: 0.56\"]"
          % np.nanmedian(re_as))
    print("  arc n_beads:      med %.1f                          [real: 2]"
          % np.median(beads))
    print("  arc roughness:    med %.2f                         [real: 0.72]"
          % np.median(rough))
    print("  arc duty_cycle:   med %.2f                         [real: 0.31]"
          % np.median(duty))


if __name__ == "__main__":
    p = sys.argv[1]
    ikey = sys.argv[2] if len(sys.argv) > 2 else "lensed"
    tkey = sys.argv[3] if len(sys.argv) > 3 else "theta_E"
    measure(p, ikey, tkey)
