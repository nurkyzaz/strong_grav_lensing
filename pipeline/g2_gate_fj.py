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
mag = np.array([float(r["stamp_mag"]) for r in rows])
th = np.array([float(r["theta_E"]) for r in rows])
rho_sim, _ = spearmanr(mag, th)

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
