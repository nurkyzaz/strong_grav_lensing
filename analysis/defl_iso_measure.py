"""Deflector VISIBLE isophotal radius [arcsec] in the euclidised domain: radius
where the azimuthally-averaged deflector SB falls to sky+2sigma. SIM deflector-
only (arg) vs REAL Q1 eval cutouts (central deflector; arc is at larger radius so
the isophotal drop of the CORE is measurable)."""
import sys

import h5py
import numpy as np

SIMH = sys.argv[1]
REALQ1 = "/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5"
PIX = 0.10  # euclidised arcsec/px


def sky(im, s=14):
    c = np.concatenate([im[:s, :s].ravel(), im[:s, -s:].ravel(),
                        im[-s:, :s].ravel(), im[-s:, -s:].ravel()])
    return np.median(c), 1.4826 * np.median(np.abs(c - np.median(c)))


def iso_radius(im):
    sk, rms = sky(im)
    g = im - sk
    n = im.shape[0]
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c)
    rb = r.astype(int)
    prof = np.array([g[rb == k].mean() if (rb == k).any() else -1e9
                     for k in range(int(r.max()) + 1)])
    thr = 2 * rms
    # first radius (moving out from centre) where the profile drops below 2 sigma
    below = np.where(prof < thr)[0]
    if len(below) == 0:
        return None
    return below[0] * PIX


def dist(h5, key_try=("lensed", "images")):
    with h5py.File(h5, "r") as f:
        k = next(x for x in key_try if x in f)
        ims = f[k][:].astype(float)
    v = [iso_radius(im) for im in ims]
    v = np.array([x for x in v if x is not None])
    return v


sv = dist(SIMH)
rv = dist(REALQ1)
print("Deflector VISIBLE isophotal radius [arcsec] (SB > sky+2sigma):")
print("  SIM  (deflector-only) q25/50/75 = %s (N=%d)"
      % (np.round(np.percentile(sv, [25, 50, 75]), 2), len(sv)))
print("  REAL (Q1 cutout core) q25/50/75 = %s (N=%d)"
      % (np.round(np.percentile(rv, [25, 50, 75]), 2), len(rv)))
