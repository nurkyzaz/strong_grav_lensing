"""Is our deflector light too COMPACT (small visible envelope) vs real, even
though half-light Re 'matches'? Measure R50, R90, and the concentration R90/R50
(pixscale-free) for real deflector-light models (sersic_lens_light.fits) vs our
rendered deflector stamps (post mig_scale zoom + FJ). Real ellipticals are de
Vaucouleurs (n~4.4) -> extended wings -> high R90/R50; a compact core is low."""
import csv
import glob
import os

import h5py
import numpy as np
from scipy.ndimage import zoom as ndi_zoom
from astropy.io import fits


def radii(im, fracs=(0.5, 0.9)):
    im = np.nan_to_num(np.clip(im, 0, None))
    t = im.sum()
    if t <= 0:
        return None
    n = im.shape[0]
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c).ravel()
    o = np.argsort(r)
    cum = np.cumsum(im.ravel()[o])
    return [float(r[o][np.searchsorted(cum, f * t)]) for f in fracs]


# real deflector-light model (noise-free), recentre on peak
rr = []
for d in sorted(glob.glob(
        "/home/user/nurkyz/cosmos_acs/q1_slde/lens/lens/*/result/sersic_lens_light.fits")):
    with fits.open(d) as h:
        im = np.asarray(h[0].data, float)
    # crop a window around the peak so a neighbour doesn't dominate
    py, px = np.unravel_index(np.nanargmax(np.nan_to_num(im)), im.shape)
    w = 60
    sub = im[max(0, py - w):py + w, max(0, px - w):px + w]
    v = radii(sub)
    if v and v[0] > 0.5:
        rr.append(v)
rr = np.array(rr)

# sim rendered deflector stamps (post mig_scale)
P = "/home/user/nurkyz/paltas_g5cosmos_fj13"
rows = list(csv.DictReader(open(P + "/assign.csv")))
with h5py.File("/home/user/nurkyz/cosmos_acs/tiles/deflector_stamps_lrg2b_raw.h5", "r") as f:
    key = "stamps" if "stamps" in f else list(f.keys())[0]
    stamps = f[key][:]
sr = []
for r in rows:
    sc = float(r.get("mig_scale", 1.0) or 1.0)
    st = stamps[int(r["stamp_id"])].astype(float)
    z = ndi_zoom(st, sc, order=1) if sc != 1.0 else st
    v = radii(z)
    if v and v[0] > 0.5:
        sr.append(v)
sr = np.array(sr)

print("Deflector light profile (R in px; R90/R50 is pixscale-free concentration):")
print("           R50 q25/50/75    R90 q25/50/75    R90/R50 q25/50/75")
print("  REAL  %s   %s   %s" % (
    np.round(np.percentile(rr[:, 0], [25, 50, 75]), 1),
    np.round(np.percentile(rr[:, 1], [25, 50, 75]), 1),
    np.round(np.percentile(rr[:, 1] / rr[:, 0], [25, 50, 75]), 2)))
print("  SIM   %s   %s   %s" % (
    np.round(np.percentile(sr[:, 0], [25, 50, 75]), 1),
    np.round(np.percentile(sr[:, 1], [25, 50, 75]), 1),
    np.round(np.percentile(sr[:, 1] / sr[:, 0], [25, 50, 75]), 2)))
print("  (N real %d, sim %d)" % (len(rr), len(sr)))
