"""C40 FJ calibration: reproduce the CURRENT composited-deflector native flux
path (mig_scale zoom -> mig_sb -> deflector_flux_scale 2.5) that the user has
already eyeball-approved for brightness, so we set fj_mag0 to PRESERVE that
brightness level and only ADD the theta_E correlation. Also reports the current
rho(mag, theta_E) we are replacing (~ -0.41 migration accident)."""
import csv
import sys

import h5py
import numpy as np
from scipy.ndimage import zoom as ndi_zoom
from scipy.stats import spearmanr

ASSIGN = "/home/user/nurkyz/paltas_g5cosmos_matched/assign.csv"
STAMPS = "/home/user/nurkyz/cosmos_acs/tiles/deflector_stamps_lrg2b_raw.h5"
FLUX_SCALE = 2.5
ZP = 25.94

rows = list(csv.DictReader(open(ASSIGN)))
with h5py.File(STAMPS, "r") as f:
    key = "stamps" if "stamps" in f else list(f.keys())[0]
    stamps = f[key][:]

th, mg = [], []
for r in rows:
    sid = int(r["stamp_id"])
    sc = float(r.get("mig_scale", 1.0) or 1.0)
    sb = float(r.get("mig_sb", 1.0) or 1.0)
    t = float(r.get("theta_E", 0) or 0)
    if t <= 0:
        continue
    st = stamps[sid].astype(np.float64)
    if sc != 1.0:
        st = ndi_zoom(st, sc, order=1)
    tot = float(np.clip(st, 0, None).sum()) * sb * FLUX_SCALE
    if tot <= 0:
        continue
    th.append(t)
    mg.append(ZP - 2.5 * np.log10(tot))

th, mg = np.array(th), np.array(mg)
rho, _ = spearmanr(mg, th)
print("N=%d  CURRENT composited-deflector mag: q25/50/75 = %s"
      % (len(mg), np.round(np.percentile(mg, [25, 50, 75]), 2)))
print("CURRENT rho(deflector_mag, theta_E) = %+.2f (the migration-accident FJ)" % rho)

# median mag near the pivot theta (0.75-1.0)
m0 = (th > 0.75) & (th < 1.0)
if m0.sum() >= 5:
    print("median mag at theta 0.75-1.0 (pivot) = %.2f  (set fj_mag0 to this to "
          "PRESERVE brightness)" % np.median(mg[m0]))
print("REAL Q1 target: mag q25/50/75 = 20.35/21.39/22.14 ; rho ~ -0.47")

# forward-check: what does an FJ model with these params produce?
if len(sys.argv) > 1:
    mag0, slope, theta0, scat = [float(x) for x in sys.argv[1:5]]
    rng = np.random.default_rng(0)
    fj = mag0 - slope * np.log10(np.clip(th, 0.1, None) / theta0) + rng.normal(0, scat, len(th))
    rho_fj, _ = spearmanr(fj, th)
    print("\nFJ MODEL (mag0=%.2f slope=%.1f theta0=%.2f scat=%.2f): "
          "mag q25/50/75=%s  rho=%+.2f"
          % (mag0, slope, theta0, scat,
             np.round(np.percentile(fj, [25, 50, 75]), 2), rho_fj))
