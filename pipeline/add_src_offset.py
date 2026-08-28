"""Add a source-plane offset (beta) to an EXISTING manifest in place (preserves
the approved theta_E / e1e2 / shear / multipole / migration columns exactly).

Two modes:
  theta   (C41): beta = theta_E * U(lo,hi)   -- pins beta/theta_E constant.
  absolute(C49): beta = sqrt(U(0,1)) * r_max -- uniform IN AREA, INDEPENDENT of
          theta_E (a random background-galaxy position). This is the PHYSICAL
          prior: small-theta lenses then get larger beta/theta_E -> lower
          magnification -> fainter/partial arcs, reproducing the real Q1
          coupling rho(arc_mag, theta_E)~-0.11 that theta-scaling destroys
          (it gave rho +0.05 -> small-theta arcs too bright vs the deflector).
          mag_cut then selects the arc-producing subset.

Usage:
  theta:    add_src_offset.py IN OUT lo hi [seed]
  absolute: add_src_offset.py IN OUT absolute r_max [seed]
"""
import csv
import sys

import numpy as np

INP, OUT = sys.argv[1], sys.argv[2]
if len(sys.argv) > 3 and sys.argv[3] == "absolute":
    MODE = "absolute"
    R_MAX = float(sys.argv[4])
    SEED = int(sys.argv[5]) if len(sys.argv) > 5 else 941
else:
    MODE = "theta"
    LO = float(sys.argv[3]) if len(sys.argv) > 3 else 0.35
    HI = float(sys.argv[4]) if len(sys.argv) > 4 else 0.75
    SEED = int(sys.argv[5]) if len(sys.argv) > 5 else 941

rng = np.random.default_rng(SEED)
rows = list(csv.DictReader(open(INP)))
for r in rows:
    t = float(r["theta_E"])
    if MODE == "absolute":
        beta = R_MAX * float(np.sqrt(rng.uniform(0, 1)))   # uniform in area
    else:
        beta = t * float(rng.uniform(LO, HI))
    phi = float(rng.uniform(0, 2 * np.pi))
    r["source_cx"] = round(beta * np.cos(phi), 6)
    r["source_cy"] = round(beta * np.sin(phi), 6)

fn = list(rows[0].keys())
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fn)
    w.writeheader()
    w.writerows(rows)

th = np.array([float(r["theta_E"]) for r in rows])
beta = np.hypot([float(r["source_cx"]) for r in rows],
                [float(r["source_cy"]) for r in rows])
frac = beta / th
print("wrote %d rows -> %s  (mode=%s)" % (len(rows), OUT, MODE))
print("  beta [arcsec]      q25/50/75 = %s" % np.round(np.percentile(beta, [25, 50, 75]), 3))
print("  beta/theta_E       q25/50/75 = %s" % np.round(np.percentile(frac, [25, 50, 75]), 3))
