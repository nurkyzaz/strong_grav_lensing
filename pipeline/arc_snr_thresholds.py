#!/usr/bin/env python
"""P5: arc SNR v2 distribution with EYE-CALIBRATED thresholds.
Calibration from the v7 side-by-side panels (same images, judged visually):
h5 29 (clear Einstein ring) = 1.83; 37/196/8 (faint-but-visible) = 0.7-1.4;
129/150 (invisible) = 0.16. So 'visible by eye' is roughly SNR >~ 0.7."""
import glob
import os
import h5py
import numpy as np
from scipy.ndimage import gaussian_filter

RUN = os.path.expanduser("~/paltas_arcs_seed111_keep")
SIM = os.path.expanduser("~/einstein_cnn/pathb_pilot_v7.h5")

files = sorted(glob.glob(os.path.join(RUN, "image_*.npy")))
with h5py.File(SIM, "r") as f:
    sim = f["lensed"][:]

n = sim.shape[1]
c = n // 2
yy, xx = np.mgrid[0:n, 0:n]
rr = np.hypot(yy - c, xx - c)
rbin = rr.astype(int)

snrs = []
for fn, comp in zip(files, sim):
    arc = np.load(fn).astype("float64")
    arc_s = gaussian_filter(arc, 1.5)
    pk = arc_s.max()
    if pk <= 0:
        snrs.append(0.0)
        continue
    fp = arc_s > 0.5 * pk
    rest_s = gaussian_filter(comp.astype("float64") - arc, 1.5)
    prof = np.zeros(rbin.max() + 1)
    for k in range(rbin.max() + 1):
        m = rbin == k
        if m.any():
            prof[k] = np.median(rest_s[m])
    resid = rest_s - prof[rbin]
    r_lo, r_hi = rr[fp].min() - 3, rr[fp].max() + 3
    ann = (rr >= r_lo) & (rr <= r_hi) & (~fp)
    loc = resid[ann]
    mad = np.median(np.abs(loc - np.median(loc))) * 1.4826
    snrs.append(float(arc_s[fp].max() / mad) if mad > 0 else 0.0)

snrs = np.array(snrs)
print("N=%d  median %.2f" % (len(snrs), np.median(snrs)))
for t in (0.5, 0.7, 1.0, 1.5, 1.83, 3.0):
    print("fraction arc SNR > %.2f: %.2f" % (t, (snrs > t).mean()))
np.save(os.path.expanduser("~/cosmos_acs/tiles/arc_snr_v7.npy"), snrs)
print("saved arc_snr_v7.npy")
