"""Measure real Euclid Q1 ARC MORPHOLOGY from the PyAutoLens image-plane
lensed-source model (source_light.fits: deflector-free, noise-free). Per lens:
  - arc_radius_px : radius of the azimuthally-brightest annulus (the ring)
  - completeness  : fraction of azimuth (0-360) with arc flux > 0.25*peak
  - n_knots       : distinct azimuthal peaks (star-forming clumps / images)
Join theta_E from the mass CSV -> infer the source_light pixel scale
(arc_radius_px * pixscale ~ theta_E) and report distributions.
beta itself is not parametric (pixelized source); completeness is the observable
that beta/theta_E controls, so we match THAT."""
import csv
import glob
import os

import numpy as np
from astropy.io import fits
from scipy.ndimage import gaussian_filter, label

ROOT = "/home/user/nurkyz/cosmos_acs/q1_slde/lens/lens"
MASS = "/home/user/nurkyz/cosmos_acs/q1_slde/modeling_lens_mass.csv"
thE = {r["id_str"]: r for r in csv.DictReader(open(MASS))}


def arc_morph(im, thr_frac=0.25, nbin=180):
    im = np.nan_to_num(np.clip(im, 0, None))
    n = im.shape[0]
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c)
    ph = (np.degrees(np.arctan2(yy - c, xx - c)) + 360) % 360
    if im.sum() <= 0:
        return None
    # arc radius = flux-weighted mean radius of the bright pixels
    pk = im > 0.25 * im.max()
    r_arc = float((r[pk] * im[pk]).sum() / im[pk].sum())
    if r_arc < 2:
        return None
    band = (r > r_arc - 0.35 * r_arc) & (r < r_arc + 0.35 * r_arc)
    # azimuthal flux profile in the arc annulus
    prof = np.zeros(nbin)
    bidx = (ph / (360 / nbin)).astype(int) % nbin
    for b in range(nbin):
        m = band & (bidx == b)
        prof[b] = im[m].sum() if m.any() else 0.0
    if prof.max() <= 0:
        return None
    ps = gaussian_filter(prof, 2, mode="wrap")
    above = ps > thr_frac * ps.max()
    completeness = above.mean()
    # count azimuthal segments (knots/images), wrap-aware
    lab, nseg = label(above)
    if nseg > 1 and above[0] and above[-1]:
        nseg -= 1                                   # merge wrap seam
    return dict(r_arc=r_arc, completeness=float(completeness), n_knots=int(nseg))


rows = []
for d in sorted(glob.glob(ROOT + "/*/result/source_light.fits")):
    ids = os.path.basename(os.path.dirname(os.path.dirname(d)))
    with fits.open(d) as h:
        im = np.asarray(h[0].data, float)
    m = arc_morph(im)
    if m is None:
        continue
    t = thE.get(ids, {}).get("einstein_radius_median_pdf")
    m["theta_E"] = float(t) if t else np.nan
    rows.append(m)

comp = np.array([r["completeness"] for r in rows])
kn = np.array([r["n_knots"] for r in rows])
ra = np.array([r["r_arc"] for r in rows])
th = np.array([r["theta_E"] for r in rows])
good = np.isfinite(th) & (th > 0.1)
pixscale = np.nanmedian(th[good] / ra[good])
print("REAL Euclid Q1 arc morphology (source_light.fits, N=%d)\n" % len(rows))
print("  arc completeness (frac of ring)  q25/50/75 = %s"
      % np.round(np.percentile(comp, [25, 50, 75]), 2))
print("  n_knots (azimuthal segments)     q25/50/75 = %s"
      % np.round(np.percentile(kn, [25, 50, 75]), 1))
print("  arc_radius [px]                  q25/50/75 = %s"
      % np.round(np.percentile(ra, [25, 50, 75]), 1))
print("  -> inferred source_light pixscale = %.4f arcsec/px "
      "(arc_radius*ps ~ theta_E)" % pixscale)
print("  completeness histogram (0-1 in 0.2 bins):",
      np.round(np.histogram(comp, bins=5, range=(0, 1))[0] / len(comp), 2))
print("  full-ring fraction (completeness>0.8):  %.2f" % (comp > 0.8).mean())
print("  partial-arc fraction (completeness<0.5): %.2f" % (comp < 0.5).mean())
