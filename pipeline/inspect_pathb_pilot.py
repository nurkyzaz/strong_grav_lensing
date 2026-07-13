#!/usr/bin/env python
"""Diagnose a Path B pilot h5. P1-aware: deflector_mag now stores the actual
drawn TOTAL magnitude, so we compare it directly against the empirical prior and
re-derive peak/sky + edge-step as EMERGENT (not matched) quantities.

Usage: python inspect_pathb_pilot.py <pilot.h5> [lib.h5]
"""
import sys
import h5py
import numpy as np

PILOT = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/user/nurkyz/einstein_cnn/pathb_pilot_v4.h5"
LIB = sys.argv[2] if len(sys.argv) > 2 else \
    "/home/user/nurkyz/cosmos_acs/tiles/deflector_stamps_lrg_v3.h5"
REAL = "/home/user/nurkyz/einstein_cnn/real_slacs_images.h5"
CSV = "/home/user/nurkyz/cosmos_acs/tiles/lens_light_empirical.csv"


def robust_sky(img, s=16):
    corners = np.concatenate([img[:s, :s].ravel(), img[:s, -s:].ravel(),
                              img[-s:, :s].ravel(), img[-s:, -s:].ravel()])
    med = np.median(corners)
    mad = np.median(np.abs(corners - med))
    return med, 1.4826 * mad


with h5py.File(PILOT, "r") as f:
    imgs = f["lensed"][:]
    didx = f["deflector_index"][:]
    dmag = f["deflector_mag"][:]        # P1: actual magnitude drawn
    theta = f["theta_E"][:]

n = imgs.shape[1]
c = n // 2
yy, xx = np.mgrid[0:n, 0:n]
r = np.hypot(yy - c, xx - c)

print("=== deflector magnitude USED (P1: total-flux scaling) ===")
used = dmag[dmag > 0]
print("used mag: median %.2f  16-84%% [%.2f, %.2f]  min %.2f max %.2f  N=%d"
      % (np.median(used), np.percentile(used, 16), np.percentile(used, 84),
         used.min(), used.max(), len(used)))
import csv as _csv
with open(CSV) as fh:
    rows = list(_csv.DictReader(fh))
pm = np.array([float(x["mag"]) for x in rows])
print("prior mag: median %.2f  16-84%% [%.2f, %.2f]  min %.2f max %.2f"
      % (np.median(pm), np.percentile(pm, 16), np.percentile(pm, 84),
         pm.min(), pm.max()))

# emergent peak/sky + edge step
psky, edge = [], []
for i in range(len(imgs)):
    med, sky = robust_sky(imgs[i])
    im = imgs[i] - med
    peak = im[c - 10:c + 10, c - 10:c + 10].max()
    psky.append(peak / max(sky, 1e-9))
    ring = im[(r >= 52) & (r <= 60)].mean()
    corner = im[r > 78].mean()
    edge.append((ring - corner) / max(sky, 1e-9))
psky = np.array(psky); edge = np.array(edge)
print("\n=== EMERGENT peak/sky (no longer matched) ===")
print("sim peak/sky: median %.0f  16-84%% [%.0f, %.0f]  (real band 492-1798)"
      % (np.median(psky), np.percentile(psky, 16), np.percentile(psky, 84)))
print("\n=== edge step (ring[52-60]-corner[>78]) in sky-sigma ===")
print("sim: median %.2f  16-84%% [%.2f, %.2f]  max %.2f  (n>10sigma: %d)"
      % (np.median(edge), np.percentile(edge, 16), np.percentile(edge, 84),
         edge.max(), int((edge > 10).sum())))

with h5py.File(REAL, "r") as f:
    rimg = f["images"][:] if "images" in f else f[list(f.keys())[0]][:]
if rimg.ndim == 4:
    rimg = rimg[:, 0]
rsteps = []
for i in range(len(rimg)):
    med, sky = robust_sky(rimg[i])
    im = rimg[i] - med
    ring = im[(r >= 52) & (r <= 60)].mean()
    corner = im[r > 78].mean()
    rsteps.append((ring - corner) / max(sky, 1e-9))
rsteps = np.array(rsteps)
print("REAL edge step: median %.2f  16-84%% [%.2f, %.2f]  max %.2f"
      % (np.median(rsteps), np.percentile(rsteps, 16),
         np.percentile(rsteps, 84), rsteps.max()))

# the 8 preview panels (same indices side_by_side seed 5 selects)
print("\n=== the 8 preview panels ===")
for i in [37, 196, 8, 29, 129, 9, 150, 0]:
    if i < len(imgs):
        print("SIM #%3d  th_E=%.2f  stamp=%2d  mag=%.2f  peak/sky=%5.0f  edge=%.2f sigma"
              % (i, theta[i], didx[i], dmag[i], psky[i], edge[i]))
