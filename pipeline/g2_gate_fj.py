#!/usr/bin/env python
"""GEN4-G2 gate: the light-theta_E correlation (Faber-Jackson channel) in the
TRAINING draws must match the REAL benchmark relation — the whole point of the
overhaul. PASS = same sign and |rho_sim - rho_real| < 0.25.
Usage: g2_gate_fj.py <assign.csv> [--select selected.h5]"""
import csv
import sys
import numpy as np
from scipy.stats import spearmanr

assign = sys.argv[1]
rows = list(csv.DictReader(open(assign)))
# C21: a z-migrated assignment carries stamp_mag_mig = the APPARENT mag the
# render actually shows; that is the mag the FJ channel must be judged on
# (the pre-migration mag correlates with the stamp's ORIGINAL z, not the
# rendered system). Reference rho_real is still the SLACS relation --
# directional yardstick only for the migrated population (disclosed).
migrated = "stamp_mag_mig" in rows[0]
magkey = "stamp_mag_mig" if migrated else "stamp_mag"
mag = np.array([float(r[magkey]) for r in rows])
th = np.array([float(r["theta_E"]) for r in rows])
rho_sim, _ = spearmanr(mag, th)
if migrated:
    print("FJ gate (C21 mode): using MIGRATED apparent mags")

real_mag, real_th = {}, {}
for r in csv.DictReader(open("/home/user/nurkyz/cosmos_acs/tiles/lens_light_empirical.csv")):
    real_mag[r["name"]] = float(r["mag"])
for r in csv.DictReader(open("/home/user/nurkyz/einstein_cnn/real_lens_labels.csv")):
    if r["name"] in real_mag and r["survey"] == "SLACS" and float(r["theta_E_pub"]) > 0:
        real_th[r["name"]] = float(r["theta_E_pub"])
names = sorted(real_th)
rho_real, _ = spearmanr([real_mag[n] for n in names], [real_th[n] for n in names])

ok = (np.sign(rho_sim) == np.sign(rho_real)) and abs(rho_sim - rho_real) < 0.25
print("FJ gate: rho_sim(mag, theta_E) = %+.2f | rho_real (N=%d SLACS) = %+.2f -> %s"
      % (rho_sim, len(names), rho_real, "PASS" if ok else "FAIL"))
sys.exit(0 if ok else 1)
