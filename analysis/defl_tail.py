"""Does our FJ deflector-mag distribution have a fatter FAINT TAIL than real?
Compare full percentiles. And montage the highest-Re (diffuse) sim deflectors to
see if they render visibly."""
import csv

import h5py
import numpy as np

P = "/home/user/nurkyz/paltas_g5cosmos_fj7"
MAG = "/home/user/nurkyz/cosmos_acs/q1_slde/modeling_mge_magnitude.csv"

real = []
for r in csv.DictReader(open(MAG)):
    try:
        v = float(r["vis_lens_magnitude_ab_median_pdf"])
        if 15 < v < 26:
            real.append(v)
    except (ValueError, KeyError):
        pass
real = np.array(real)
with h5py.File(P + "/euclid.h5", "r") as f:
    sim = f["deflector_mag"][:]
pcts = [5, 10, 25, 50, 75, 90, 95, 99]
print("deflector VIS mag percentiles:")
print("  pct   ", " ".join("%5d" % p for p in pcts))
print("  REAL  ", " ".join("%5.1f" % v for v in np.percentile(real, pcts)))
print("  SIM   ", " ".join("%5.1f" % v for v in np.percentile(sim, pcts)))
print("  real max %.1f  sim max %.1f" % (real.max(), sim.max()))
print("\n  frac fainter than 22.5:  REAL %.2f  SIM %.2f"
      % ((real > 22.5).mean(), (sim > 22.5).mean()))
print("  frac fainter than 23.0:  REAL %.2f  SIM %.2f"
      % ((real > 23.0).mean(), (sim > 23.0).mean()))
