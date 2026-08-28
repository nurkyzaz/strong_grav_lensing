"""Same arc-morphology metric as real_arc_morph.py, on our sim lensed-source
renders (sub/image_*.npy). Join theta_E from assign.csv to infer sim pixscale."""
import csv
import glob
import sys

import numpy as np
from scipy.ndimage import gaussian_filter, label

P = sys.argv[1]


def arc_morph(im, thr_frac=0.25, nbin=180):
    im = np.nan_to_num(np.clip(im, 0, None))
    n = im.shape[0]
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c)
    ph = (np.degrees(np.arctan2(yy - c, xx - c)) + 360) % 360
    if im.sum() <= 0:
        return None
    pk = im > 0.25 * im.max()
    r_arc = float((r[pk] * im[pk]).sum() / im[pk].sum())
    if r_arc < 2:
        return None
    band = (r > r_arc - 0.35 * r_arc) & (r < r_arc + 0.35 * r_arc)
    prof = np.zeros(nbin)
    bidx = (ph / (360 / nbin)).astype(int) % nbin
    for b in range(nbin):
        m = band & (bidx == b)
        prof[b] = im[m].sum() if m.any() else 0.0
    if prof.max() <= 0:
        return None
    ps = gaussian_filter(prof, 2, mode="wrap")
    above = ps > thr_frac * ps.max()
    lab, nseg = label(above)
    if nseg > 1 and above[0] and above[-1]:
        nseg -= 1
    return dict(r_arc=r_arc, completeness=float(above.mean()), n_knots=int(nseg))


th = {}
try:
    for r in csv.DictReader(open(P + "/assign.csv")):
        th[int(r["file_row"])] = float(r.get("theta_E", 0) or 0)
except FileNotFoundError:
    pass

files = sorted(glob.glob(P + "/sub/image_*.npy"))
comp, kn, ra, thv = [], [], [], []
for i, f in enumerate(files):
    m = arc_morph(np.load(f))
    if m is None:
        continue
    comp.append(m["completeness"]); kn.append(m["n_knots"]); ra.append(m["r_arc"])
    thv.append(th.get(i, np.nan))
comp, kn, ra, thv = map(np.array, (comp, kn, ra, thv))
good = np.isfinite(thv) & (thv > 0.1)
ps = np.nanmedian(thv[good] / ra[good]) if good.any() else np.nan
print("SIM arc morphology (%s, N=%d)\n" % (P.split("/")[-1], len(comp)))
print("  arc completeness  q25/50/75 = %s   | REAL 0.26/0.43/0.68"
      % np.round(np.percentile(comp, [25, 50, 75]), 2))
print("  n_knots           q25/50/75 = %s   | REAL 1/2/2"
      % np.round(np.percentile(kn, [25, 50, 75]), 1))
print("  arc_radius [px]   q25/50/75 = %s"
      % np.round(np.percentile(ra, [25, 50, 75]), 1))
print("  -> inferred sim pixscale = %.4f arcsec/px" % ps)
print("  full-ring frac (>0.8):   %.2f   | REAL 0.17" % (comp > 0.8).mean())
print("  partial-arc frac (<0.5): %.2f   | REAL 0.61" % (comp < 0.5).mean())
