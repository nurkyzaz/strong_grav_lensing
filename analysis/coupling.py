"""Is the source physically coupled to the deflector? Test the claim 'small/faint
deflector never has an arc as bright as itself' in REAL Q1, and compare our sim.
Measures, vs theta_E: deflector mag, arc mag, contrast(arc-defl), and the fraction
with arc >= deflector (contrast<0)."""
import csv
import glob

import h5py
import numpy as np
from scipy.stats import spearmanr

# ---------- REAL ----------
D = "/home/user/nurkyz/cosmos_acs/q1_slde/"
mass = {r["id_str"]: r for r in csv.DictReader(open(D + "modeling_lens_mass.csv"))}
mag = {r["id_str"]: r for r in csv.DictReader(open(D + "modeling_mge_magnitude.csv"))}
th, dm, am = [], [], []
for i in set(mass) & set(mag):
    try:
        t = float(mass[i]["einstein_radius_median_pdf"])
        d = float(mag[i]["vis_lens_magnitude_ab_median_pdf"])
        a = float(mag[i]["vis_lensed_source_magnitude_ab_median_pdf"])
        if 0.1 < t < 4 and 15 < d < 25 and 18 < a < 28:
            th.append(t); dm.append(d); am.append(a)
    except (ValueError, KeyError):
        pass
th, dm, am = map(np.array, (th, dm, am))
ct = am - dm


def report(tag, th, dm, am, ct):
    print("\n=== %s (N=%d) ===" % (tag, len(th)))
    print("  rho(deflector_mag, theta_E) = %+.2f   rho(arc_mag, theta_E) = %+.2f"
          % (spearmanr(dm, th)[0], spearmanr(am, th)[0]))
    print("  frac with arc BRIGHTER than deflector (contrast<0): %.2f" % (ct < 0).mean())
    for lo, hi in ((0.3, 0.7), (0.7, 1.0), (1.0, 1.4), (1.4, 2.5)):
        m = (th > lo) & (th <= hi)
        if m.sum() >= 3:
            print("  theta %.1f-%.1f (N=%3d): defl %.1f  arc %.1f  contrast %+.2f "
                  "(arc<defl frac %.2f)"
                  % (lo, hi, m.sum(), np.median(dm[m]), np.median(am[m]),
                     np.median(ct[m]), (ct[m] < 0).mean()))


report("REAL Euclid Q1", th, dm, am, ct)

# ---------- SIM ----------
import sys
P = sys.argv[1] if len(sys.argv) > 1 else "/home/user/nurkyz/paltas_g5cosmos_fj7"
EH = sys.argv[2] if len(sys.argv) > 2 else "euclid.h5"
with h5py.File(P + "/" + EH, "r") as f:
    sdm = f["deflector_mag"][:]
    sth = f["theta_E"][:]
sam = np.array([25.94 - 2.5 * np.log10(max(float(np.load(fn).sum()), 1e-9))
                for fn in sorted(glob.glob(P + "/sub/image_*.npy"))])
n = min(len(sdm), len(sam))
sdm, sth, sam = sdm[:n], sth[:n], sam[:n]
report("SIM (%s)" % P.split("/")[-1], sth, sdm, sam, sam - sdm)
print("  accepted theta_E q25/50/75 = %s | REAL 0.70/0.88/1.13"
      % np.round(np.percentile(sth, [25, 50, 75]), 2))
