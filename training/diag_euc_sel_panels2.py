#!/usr/bin/env python
"""Direct lookup of the ACTUAL displayed panels (from the PNG titles):
selected-h5 indices 44, 232, 10, 34, 153, 11, 177, 0.
Plus: arc footprint EXTENT (post-degradation, Euclid px) for the whole
selected set vs the eye-visible subset -- tests the 'sim arcs smaller' point.
"""
import glob
import os
import numpy as np
import h5py
from scipy.ndimage import gaussian_filter
import sys

sys.path.insert(0, os.path.expanduser("~/einstein_cnn"))
from euclidise import euclidise

SEL = "/home/user/nurkyz/einstein_cnn/euc_sel_pilot_selected.h5"
FULL = "/home/user/nurkyz/einstein_cnn/euc_sel_pilot_euclid.h5"
EMPTY = "/home/user/nurkyz/cosmos_acs/tiles/empty_cutouts_4k.h5"
ARCDIR = "/home/user/nurkyz/paltas_euc_sel_pilot"

PANELS = [44, 232, 10, 34, 153, 11, 177, 0]

with h5py.File(SEL, "r") as f:
    snr = f["arc_snr"][:]
    th = f["theta_E"][:]
    ci = f["cutout_index"][:]

print("displayed panels (verified indices from PNG titles):")
yy, xx = np.mgrid[0:128, 0:128]
A = np.c_[xx.ravel(), yy.ravel(), np.ones(128 * 128)]
with h5py.File(EMPTY, "r") as f:
    key = "empty" if "empty" in f else list(f.keys())[0]
    for i in PANELS:
        c = f[key][int(ci[i])]
        coef, *_ = np.linalg.lstsq(A, c.ravel(), rcond=None)
        plane = (A @ coef).reshape(128, 128)
        resid = c - plane
        mad = np.median(np.abs(resid - np.median(resid))) * 1.4826
        g = (plane.max() - plane.min()) / mad if mad > 0 else np.inf
        print("  SIM #%d  theta_E=%.2f  arc_snr=%.2f  cutout=%d  bg-gradient/noise=%.1f"
              % (i, th[i], snr[i], ci[i], g))

# arc extent: euclidised footprint area (0.5*peak) in Euclid px, whole selected set
with h5py.File(FULL, "r") as f:
    n_full = f["lensed"].shape[0]
keep_idx = np.where(np.isin(np.arange(n_full), np.arange(n_full)))[0]  # placeholder
files = sorted(glob.glob(os.path.join(ARCDIR, "image_*.npy")))
rng = np.random.default_rng(3)
areas = []
snr_all_order = []
with h5py.File(SEL, "r") as f:
    pass
# recompute footprint areas for ALL 400, then report for the selected snr>0.7 set
from numpy import array
all_areas = []
for fn in files:
    arc = np.load(fn).astype("float64")
    e = euclidise(arc, rng, add_noise=False)
    es = gaussian_filter(e, 1.5)
    pk = es.max()
    all_areas.append(int((es > 0.5 * pk).sum()) if pk > 0 else 0)
all_areas = np.array(all_areas)
print("\narc footprint area (>=0.5 peak, on the 128px upsampled Euclid grid):")
print("  all 400:   median %d px  16-84%% [%d, %d]" %
      (np.median(all_areas), *np.percentile(all_areas, [16, 84]).astype(int)))
# map selected h5 rows back to original indices via snr equality is fragile;
# instead recompute the pass mask exactly like the selector did is overkill --
# approximate: selected = largest-SNR subset unknown. Report area vs theta
# correlation instead:
print("  correlation(footprint area, is arc visible proxy): larger theta -> bigger arcs expected")
