#!/usr/bin/env python
"""Same-estimator arc-prominence comparison, Euclidised real vs selected sims
(Nurkyz 2026-07-09: 'sim arcs look brighter than real').

Prominence := max of the (1.5px-smoothed, azimuthal-median-subtracted)
residual within the arc annulus r in [0.4", 2.6"], divided by the robust sigma
of the same residual map outside the annulus. Computed IDENTICALLY on real
Euclidised SLACS images and on the selected sim images (no arc render used) --
gate-style same-estimator comparison. Companions/noise enter both sides alike.
"""
import sys
import numpy as np
import h5py
from scipy.ndimage import gaussian_filter

PIX = 0.05  # upsampled Euclid grid


def prominence(img):
    """Brightest EXTENDED residual feature in the arc annulus, in units of the
    residual noise: connected components >= 300 px only (arc scale; compact
    companions/stars excluded by construction)."""
    from scipy.ndimage import label
    n = img.shape[0]
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.hypot(yy - c, xx - c)
    rbin = rr.astype(int)
    s = gaussian_filter(img.astype("float64"), 1.5)
    prof = np.zeros(rbin.max() + 1)
    for k in range(rbin.max() + 1):
        m = rbin == k
        if m.any():
            prof[k] = np.median(s[m])
    resid = s - prof[rbin]
    ann = (rr >= 0.4 / PIX) & (rr <= 2.6 / PIX)
    out = (rr > 2.6 / PIX)
    mad = np.median(np.abs(resid[out] - np.median(resid[out]))) * 1.4826
    if mad <= 0:
        return np.nan
    det = (resid > 3.0 * mad) & ann
    lab, nl = label(det)
    best = 0.0
    for i in range(1, nl + 1):
        m = lab == i
        if m.sum() >= 300:
            best = max(best, float(resid[m].max() / mad))
    return best


for path, key in [(sys.argv[1], None), (sys.argv[2], None)]:
    with h5py.File(path, "r") as f:
        k = "images" if "images" in f else "lensed"
        imgs = f[k][:]
    if imgs.ndim == 4:
        imgs = imgs[:, 0]
    vals = np.array([prominence(x) for x in imgs])
    vals = vals[np.isfinite(vals)]
    print("%-45s N=%3d  median %.2f  16-84%% [%.2f, %.2f]  95%% %.2f  max %.2f"
          % (path.split("/")[-1], len(vals), np.median(vals),
             np.percentile(vals, 16), np.percentile(vals, 84),
             np.percentile(vals, 95), vals.max()))
