#!/usr/bin/env python
"""R1.2b final tune: scan (SNR, extent) selection thresholds on pilot D and
compare each selected subset's arc-prominence distribution against the REAL
Euclidised SLACS distribution (16/50/84 pct: 24.8 / 90.6 / 240.4). The right
selection reproduces the real population's faint edge instead of imposing a
stricter floor than the actual SLACS discovery selection."""
import glob
import os
import numpy as np
import h5py
from scipy.ndimage import gaussian_filter, label

ARCDIR = os.path.expanduser("~/paltas_euc_selD_pilot_euclid")
SIM = os.path.expanduser("~/einstein_cnn/euc_sel_pilot_euclid_D.h5")
REAL = (24.80, 90.56, 240.40)  # real 16/50/84 prominence

files = sorted(glob.glob(os.path.join(ARCDIR, "image_*.npy")))
with h5py.File(SIM, "r") as f:
    sim = f["lensed"][:].astype("float64")
    theta = f["theta_E"][:].astype("float32")

n = sim.shape[1]
c = n // 2
yy, xx = np.mgrid[0:n, 0:n]
rr = np.hypot(yy - c, xx - c)
rbin = rr.astype(int)
ann_r = (rr >= 0.4 / 0.05) & (rr <= 2.6 / 0.05)
out_r = rr > 2.6 / 0.05

snrs, extents, proms = [], [], []
for fn, comp in zip(files, sim):
    arc = np.load(fn).astype("float64")
    arc_s = gaussian_filter(arc, 1.5)
    pk = arc_s.max()
    s = gaussian_filter(comp, 1.5)
    prof = np.zeros(rbin.max() + 1)
    for k in range(rbin.max() + 1):
        m = rbin == k
        if m.any():
            prof[k] = np.median(s[m])
    resid_full = s - prof[rbin]
    mad_out = np.median(np.abs(resid_full[out_r] - np.median(resid_full[out_r]))) * 1.4826
    # prominence (same estimator as the real-side comparison)
    det = (resid_full > 3.0 * mad_out) & ann_r
    lab, nl = label(det)
    best = 0.0
    for i in range(1, nl + 1):
        m = lab == i
        if m.sum() >= 300:
            best = max(best, float(resid_full[m].max() / mad_out))
    proms.append(best)
    # selection metrics (v2 arc SNR + extent)
    if pk <= 0:
        snrs.append(0.0)
        extents.append(0)
        continue
    fp = arc_s > 0.5 * pk
    extents.append(int(fp.sum()))
    rest_s = gaussian_filter(comp - arc, 1.5)
    prof2 = np.zeros(rbin.max() + 1)
    for k in range(rbin.max() + 1):
        m = rbin == k
        if m.any():
            prof2[k] = np.median(rest_s[m])
    resid = rest_s - prof2[rbin]
    ann = (rr >= rr[fp].min() - 3) & (rr <= rr[fp].max() + 3) & (~fp)
    loc = resid[ann]
    mad = np.median(np.abs(loc - np.median(loc))) * 1.4826
    snrs.append(float(arc_s[fp].max() / mad) if mad > 0 else 0.0)

snrs = np.array(snrs)
extents = np.array(extents)
proms = np.array(proms)

print("REAL prominence 16/50/84: %.1f / %.1f / %.1f" % REAL)
print("scan: t_snr x min_extent -> pass | selected prominence 16/50/84 | per-theta_E pass")
bins = [(0.45, 0.8), (0.8, 1.2), (1.2, 1.7), (1.7, 2.3)]
for t in (0.7, 1.0, 1.25, 1.5, 2.0, 2.5):
    for ext in (150, 200, 300):
        keep = (snrs > t) & (extents >= ext)
        if keep.sum() < 10:
            continue
        p = np.percentile(proms[keep], [16, 50, 84])
        pb = " ".join("%.2f" % ((keep & (theta > lo) & (theta <= hi)).sum() /
                                max(((theta > lo) & (theta <= hi)).sum(), 1))
                      for lo, hi in bins)
        print("snr>%.2f ext>=%d: pass %.2f | prom %5.1f/%5.1f/%5.1f | bins %s"
              % (t, ext, keep.mean(), p[0], p[1], p[2], pb))
