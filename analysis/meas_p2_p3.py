"""Problem 2 (sky-noise) + Problem 3 (deflector Re) distributions vs real Q1."""
import csv
import glob

import h5py
import numpy as np
from scipy.ndimage import zoom as ndi_zoom

TILES = "/home/user/nurkyz/cosmos_acs/tiles/"
P = "/home/user/nurkyz/paltas_g5cosmos_fj7"
REALQ1 = "/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5"


def sky_rms(im, s=14):
    c = np.concatenate([im[:s, :s].ravel(), im[:s, -s:].ravel(),
                        im[-s:, :s].ravel(), im[-s:, -s:].ravel()])
    return 1.4826 * np.median(np.abs(c - np.median(c)))


def hlr_px(st):
    st = np.clip(st, 0, None)
    tot = st.sum()
    if tot <= 0:
        return np.nan
    n = st.shape[0]
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c).ravel()
    order = np.argsort(r)
    cum = np.cumsum(st.ravel()[order])
    return float(r[order][np.searchsorted(cum, 0.5 * tot)])


# ---- Problem 2: sky RMS ----
with h5py.File(P + "/euclid.h5", "r") as f:
    sim = f["lensed"][:].astype(float)
sim_rms = np.array([sky_rms(im) for im in sim])
with h5py.File(REALQ1, "r") as f:
    key = "images" if "images" in f else list(f.keys())[0]
    real = f[key][:].astype(float)
real_rms = np.array([sky_rms(im) for im in real])
print("=== PROBLEM 2: sky RMS (e-/s per Euclid px) ===")
print("  SIM  q05/25/50/75/95/max = %s"
      % np.round(np.percentile(sim_rms, [5, 25, 50, 75, 95]).tolist() + [sim_rms.max()], 4))
print("  REAL q05/25/50/75/95/max = %s"
      % np.round(np.percentile(real_rms, [5, 25, 50, 75, 95]).tolist() + [real_rms.max()], 4))
print("  SIM frac above REAL 95th (%.4f): %.2f ; above REAL max (%.4f): %.2f"
      % (np.percentile(real_rms, 95), (sim_rms > np.percentile(real_rms, 95)).mean(),
         real_rms.max(), (sim_rms > real_rms.max()).mean()))

# ---- Problem 3: deflector Re (rendered) ----
SIM_PIXSCALE = 0.0457   # native render arcsec/px (from arc_radius/theta_E)
rows = {int(r["file_row"]): r for r in csv.DictReader(open(P + "/assign.csv"))}
with h5py.File(TILES + "deflector_stamps_lrg2b_raw.h5", "r") as f:
    key = "stamps" if "stamps" in f else list(f.keys())[0]
    stamps = f[key][:]
re_rend, re_lib = [], []
for fr, r in rows.items():
    sid = int(r["stamp_id"]); sc = float(r.get("mig_scale", 1.0) or 1.0)
    st = stamps[sid].astype(float)
    re_lib.append(hlr_px(st) * SIM_PIXSCALE)                      # library native (no zoom)
    z = ndi_zoom(st, sc, order=1) if sc != 1.0 else st
    re_rend.append(hlr_px(z) * SIM_PIXSCALE)
re_rend = np.array(re_rend); re_lib = np.array(re_lib)
print("\n=== PROBLEM 3: deflector half-light radius [arcsec] ===")
print("  RENDERED (mig-zoomed) q25/50/75 = %s ; frac>0.94 (diffuse): %.2f"
      % (np.round(np.nanpercentile(re_rend, [25, 50, 75]), 2), np.nanmean(re_rend > 0.94)))
print("  LIBRARY  (pre-zoom)   q25/50/75 = %s"
      % np.round(np.nanpercentile(re_lib, [25, 50, 75]), 2))
print("  REAL Q1 (Sersic Re)   q25/50/75 = 0.47/0.68/0.94 ; real frac>0.94 ~0.25")
