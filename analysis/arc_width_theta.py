"""Task 1: is our arc WIDTH (thickness) too large vs real, esp. at small theta_E?
Measure radial FWHM of the arc [arcsec] vs theta_E, real (source_light.fits,
0.095"/px) vs sim (sub_arcs euclidised, 0.1"/px). Arc width ~ source angular size;
if sim >> real at small theta, sources are too large -> add a max-size cut."""
import csv
import glob
import os

import h5py
import numpy as np
from astropy.io import fits


def arc_radial_fwhm(im, pixscale):
    im = np.nan_to_num(np.clip(im, 0, None))
    if im.sum() <= 0:
        return None, None
    n = im.shape[0]
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c)
    pk = im > 0.25 * im.max()
    r_arc = float((r[pk] * im[pk]).sum() / im[pk].sum())
    if r_arc < 2:
        return None, None
    # radial profile summed azimuthally, FWHM around r_arc
    rb = r.astype(int)
    prof = np.array([im[rb == k].sum() if (rb == k).any() else 0
                     for k in range(int(r.max()) + 1)])
    if prof.max() <= 0:
        return None, None
    half = 0.5 * prof.max()
    above = np.where(prof > half)[0]
    if len(above) == 0:
        return None, None
    fwhm_px = above.max() - above.min() + 1
    return fwhm_px * pixscale, r_arc * pixscale


# real
D = "/home/user/nurkyz/cosmos_acs/q1_slde/"
thE = {r["id_str"]: r for r in csv.DictReader(open(D + "modeling_lens_mass.csv"))}
rw, rt = [], []
for d in sorted(glob.glob(D + "lens/lens/*/result/source_light.fits")):
    ids = os.path.basename(os.path.dirname(os.path.dirname(d)))
    t = thE.get(ids, {}).get("einstein_radius_median_pdf")
    if not t:
        continue
    with fits.open(d) as h:
        w, _ = arc_radial_fwhm(np.asarray(h[0].data, float), 0.095)
    if w:
        rw.append(w); rt.append(float(t))
rw, rt = np.array(rw), np.array(rt)

# sim
import sys as _sys; P = _sys.argv[1] if len(_sys.argv)>1 else "/home/user/nurkyz/paltas_g5cosmos_fj11"
th = {int(r["file_row"]): float(r.get("theta_E", 0) or 0)
      for r in csv.DictReader(open(P + "/assign.csv"))}
sw, st = [], []
for i, f in enumerate(sorted(glob.glob(P + "/sub_arcs/image_*.npy"))):
    w, _ = arc_radial_fwhm(np.load(f).astype(float), 0.10)
    if w and i in th:
        sw.append(w); st.append(th[i])
sw, st = np.array(sw), np.array(st)

print("Arc radial FWHM [arcsec] vs theta_E:")
print("  theta-bin      REAL width (N)     SIM width (N)")
for lo, hi in ((0.3, 0.7), (0.7, 1.0), (1.0, 1.4), (1.4, 2.5)):
    rm = (rt > lo) & (rt <= hi); sm = (st > lo) & (st <= hi)
    print("  %.1f-%.1f      %.2f (N=%3d)      %.2f (N=%3d)"
          % (lo, hi, np.median(rw[rm]) if rm.sum() else -1, rm.sum(),
             np.median(sw[sm]) if sm.sum() else -1, sm.sum()))
print("  OVERALL       %.2f              %.2f" % (np.median(rw), np.median(sw)))
