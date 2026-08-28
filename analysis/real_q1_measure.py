"""Measure the real Euclid Q1 distributions (PyAutoLens modeling) that GEN5 must
match -- the same physical quantities matched in GEN4. Joins by id_str."""
import csv

import numpy as np


def load(path):
    return {r["id_str"]: r for r in csv.DictReader(open(path)) if r.get("id_str")}


def col(d, ids, name):
    out = []
    for i in ids:
        try:
            v = float(d[i][name])
            if np.isfinite(v):
                out.append(v)
        except (KeyError, ValueError):
            pass
    return np.array(out)


def q(name, x, unit="", lo=None, hi=None):
    if lo is not None:
        x = x[(x > lo) & (x < hi)]
    if len(x) == 0:
        print("  %-34s N=0" % name)
        return
    print("  %-34s N=%3d  q25/50/75 = %7.3f /%7.3f /%7.3f  %s"
          % (name, len(x), *np.percentile(x, [25, 50, 75]), unit))


D = "/home/user/nurkyz/cosmos_acs/q1_slde/"
mass = load(D + "modeling_lens_mass.csv")
mag = load(D + "modeling_mge_magnitude.csv")
ser = load(D + "modeling_lens_sersic.csv")
ids = sorted(set(mass) & set(mag))
print("REAL EUCLID Q1 (N joined mass+mag = %d)\n" % len(ids))

print("MASS / GEOMETRY:")
q("theta_E [arcsec]", col(mass, ids, "einstein_radius_median_pdf"), "", 0.1, 4)
e1 = col(mass, ids, "ell_comps_0_median_pdf"); e2 = col(mass, ids, "ell_comps_1_median_pdf")
q("|ell_comps| (mass)", np.hypot(e1, e2) if len(e1) == len(e2) else e1)
g1 = col(mass, ids, "shear_gamma_1_median_pdf"); g2 = col(mass, ids, "shear_gamma_2_median_pdf")
q("|shear gamma|", np.hypot(g1, g2) if len(g1) == len(g2) else g1)

print("\nPHOTOMETRY (VIS AB):")
q("deflector mag", col(mag, ids, "vis_lens_magnitude_ab_median_pdf"), "", 15, 25)
q("LENSED source (ARC) mag", col(mag, ids, "vis_lensed_source_magnitude_ab_median_pdf"), "", 18, 28)
q("unlensed source mag", col(mag, ids, "vis_source_magnitude_ab_median_pdf"), "", 18, 30)
q("total magnification", col(mag, ids, "vis_total_magnification_median_pdf"), "", 0, 50)
q("arc S/N (max lensed src)", col(mag, ids, "vis_max_lensed_source_signal_to_noise_ratio"), "", 0, 1e4)

# arc-minus-deflector mag (contrast): positive = arc fainter than deflector
dm = []
for i in ids:
    try:
        a = float(mag[i]["vis_lensed_source_magnitude_ab_median_pdf"])
        d = float(mag[i]["vis_lens_magnitude_ab_median_pdf"])
        if np.isfinite(a) and np.isfinite(d):
            dm.append(a - d)
    except (KeyError, ValueError):
        pass
q("ARC - DEFLECTOR mag (contrast)", np.array(dm), "(+ = arc fainter)", -5, 8)

print("\nDEFLECTOR LIGHT (Sersic):")
ids2 = sorted(set(ser) & set(mag))
q("effective_radius [arcsec]", col(ser, ids2, "effective_radius_median_pdf"), "", 0.05, 5)
q("sersic_index", col(ser, ids2, "sersic_index_median_pdf"), "", 0.3, 10)
se1 = col(ser, ids2, "ell_comps_0_median_pdf"); se2 = col(ser, ids2, "ell_comps_1_median_pdf")
ell = np.hypot(se1, se2) if len(se1) == len(se2) else se1
qax = (1 - ell) / (1 + ell)
q("axis ratio q (light)", qax[np.isfinite(qax)])
