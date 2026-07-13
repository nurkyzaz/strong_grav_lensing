#!/usr/bin/env python
"""G3-2: extract the mean Euclid VIS PSF from the Q1 GRID-PSF-VIS product.

HDU1 = 19200^2 sparse canvas of PSF stamps at 0.1"/px; HDU2 = stamp positions.
Output: vis_psf_q1.npy (mean stamp, unit sum, 0.1"/px) + a x2 bilinearly
upsampled 0.05"/px version for matching-kernel work + provenance JSON +
diagnostics (FWHM, ellipticity, radial profile vs the 0.16" Gaussian).
"""
import json

import numpy as np
from astropy.io import fits
from scipy.ndimage import zoom

FN = "/home/user/nurkyz/g3_scratch/grid_psf_vis_102044185.fits"
hdul = fits.open(FN, memmap=True)
tab = hdul[2].data
print("stamp table columns:", tab.names)
img = hdul[1].data

# infer per-stamp box from nearest-neighbour spacing of the first rows
cols = {n.lower(): n for n in tab.names}
xk = next(cols[k] for k in cols if k in ("x", "x_center", "xpos", "x_centre"))
yk = next(cols[k] for k in cols if k in ("y", "y_center", "ypos", "y_centre"))
xs = np.asarray(tab[xk], dtype="float64")
ys = np.asarray(tab[yk], dtype="float64")
print("n stamps:", len(xs), "x range", xs.min(), xs.max())

HALF = 16   # 3.2" box at 0.1"/px — generous for a 0.16" FWHM PSF
acc = np.zeros((2 * HALF + 1, 2 * HALF + 1), dtype="float64")
used = 0
sel = np.random.default_rng(3).choice(len(xs), size=min(4000, len(xs)),
                                      replace=False)
for i in sel:
    cx, cy = int(round(xs[i])) - 1, int(round(ys[i])) - 1   # FITS 1-based
    if not (HALF < cx < 19200 - HALF and HALF < cy < 19200 - HALF):
        continue
    st = np.asarray(img[cy - HALF:cy + HALF + 1, cx - HALF:cx + HALF + 1],
                    dtype="float64")
    s = st.sum()
    if s <= 0 or not np.isfinite(st).all():
        continue
    if st.max() != st[HALF, HALF]:      # mis-centred / overlapping stamp
        continue
    acc += st / s
    used += 1
print("stacked %d stamps" % used)
psf = acc / acc.sum()

# diagnostics
yy, xx = np.mgrid[-HALF:HALF + 1, -HALF:HALF + 1]
r = np.hypot(xx, yy)
half_max = psf.max() / 2
fwhm_px = 2 * np.sqrt((psf > half_max).sum() / np.pi)
print("FWHM ~ %.2f px = %.3f arcsec (Gaussian model was 0.16)"
      % (fwhm_px, fwhm_px * 0.1))
q11 = (psf * xx * xx).sum(); q22 = (psf * yy * yy).sum(); q12 = (psf * xx * yy).sum()
e = np.hypot(q11 - q22, 2 * q12) / (q11 + q22)
print("ellipticity |e| = %.3f" % e)
prof = [psf[(r >= b) & (r < b + 1)].mean() for b in range(HALF)]
g = np.exp(-0.5 * (r * 0.1 / (0.16 / 2.355)) ** 2); g /= g.sum()
gprof = [g[(r >= b) & (r < b + 1)].mean() for b in range(HALF)]
print("radial profile (real vs gaussian0.16):")
for b in range(0, 10):
    print("  r=%2d px  %.3e  vs  %.3e" % (b, prof[b], gprof[b]))

np.save("/home/user/nurkyz/cosmos_acs/tiles/vis_psf_q1.npy",
        psf.astype("float64"))
up = zoom(psf, 2.0, order=1)
up /= up.sum()
np.save("/home/user/nurkyz/cosmos_acs/tiles/vis_psf_q1_50mas.npy",
        up.astype("float64"))
json.dump(dict(source="EUC_MER_GRID-PSF-VIS_TILE102044185 (Q1, IRSA)",
               n_stacked=int(used), fwhm_arcsec=float(fwhm_px * 0.1),
               ellipticity=float(e), pix="0.1 (native) / 0.05 (upsampled)"),
          open("/home/user/nurkyz/cosmos_acs/tiles/vis_psf_q1_provenance.json",
               "w"), indent=2)
print("wrote vis_psf_q1.npy (33px @0.1\") + vis_psf_q1_50mas.npy + provenance")
