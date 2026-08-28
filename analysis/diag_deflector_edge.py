"""Diagnose the abrupt deflector edge on the flagged cards: for each file_row,
pull its stamp_id from assign.csv, load the raw stamp, replicate the FJ path
(mig_scale zoom + total-flux normalization), and report the flux at the stamp
BOUNDARY relative to the peak -- a high edge/peak ratio = hard truncation."""
import csv

import h5py
import numpy as np
from scipy.ndimage import zoom as ndi_zoom

ASSIGN = "/home/user/nurkyz/paltas_g5cosmos_fj/assign.csv"
STAMPS = "/home/user/nurkyz/cosmos_acs/tiles/deflector_stamps_lrg2b_raw.h5"
FLAG = [104, 84, 69, 63, 39, 10, 227, 237]

rows = {int(r["file_row"]): r for r in csv.DictReader(open(ASSIGN))}
with h5py.File(STAMPS, "r") as f:
    key = "stamps" if "stamps" in f else list(f.keys())[0]
    stamps = f[key]
    for fr in FLAG:
        r = rows[fr]
        sid = int(r["stamp_id"])
        sc = float(r.get("mig_scale", 1.0) or 1.0)
        st = stamps[sid].astype(np.float64)
        raw_edge = np.concatenate([st[0], st[-1], st[:, 0], st[:, -1]])
        raw_ratio = np.median(np.abs(raw_edge)) / max(st.max(), 1e-9)
        z = ndi_zoom(st, sc, order=1) if sc != 1.0 else st
        edge = np.concatenate([z[0], z[-1], z[:, 0], z[:, -1]])
        # inner border of a centered 128 crop (what actually shows if z>128)
        print("fr=%3d sid=%3d th=%.2f mig_scale=%.3f stampR=%dpx zoomR=%dpx | "
              "RAW edge/peak=%.4f  min>0 frac=%.2f"
              % (fr, sid, float(r["theta_E"]), sc, st.shape[0], z.shape[0],
                 raw_ratio, (st > 0).mean()))
