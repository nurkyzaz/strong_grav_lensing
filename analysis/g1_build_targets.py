#!/usr/bin/env python
"""GEN4-G1a: build the expansion target list.
MAST: ACS/WFC F814W observations from the SLACS-lineage PIs (Bolton, Treu,
Koopmans, Brownstein) -> unique pointings; exclude the frozen benchmark, the
current 84 LRGDEFL targets, and duplicates; SDSS-crossmatch each remaining
pointing for clean sigma_v; write lrgdefl2_labels.csv in the fetch script's
format (name, ra_deg, dec_deg, theta_E_pub, q_pub, survey, src_table).
"""
import csv
import os
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.mast import Observations
from astroquery.sdss import SDSS

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = "/Users/nurkyz/Desktop/LensFusion"
OUT = os.path.join(HERE, "lrgdefl2_labels.csv")

# --- exclusion coordinates: benchmark + current LRGDEFL
excl = []
for fn in (os.path.join(PROJ, "real_lens_labels.csv"),):
    for r in csv.DictReader(open(fn)):
        excl.append((float(r["ra_deg"]), float(r["dec_deg"])))
excl = SkyCoord([e[0] for e in excl] * u.deg, [e[1] for e in excl] * u.deg)
print("exclusion list: %d coords (benchmark + LRGDEFL + everything in labels)" % len(excl))

# --- MAST pointings
point = []
for pi in ("Bolton", "Treu", "Koopmans", "Brownstein"):
    try:
        obs = Observations.query_criteria(obs_collection="HST",
                                          instrument_name="ACS/WFC",
                                          filters="F814W",
                                          proposal_pi="*%s*" % pi)
        for o in obs:
            point.append((float(o["s_ra"]), float(o["s_dec"]),
                          str(o["target_name"]), str(o["proposal_id"])))
        print("PI %s: %d F814W ACS observations" % (pi, len(obs)))
    except Exception as e:
        print("PI %s failed: %s" % (pi, str(e)[:80]))

# --- dedupe pointings (5") and drop exclusions (5")
cat = SkyCoord([p[0] for p in point] * u.deg, [p[1] for p in point] * u.deg)
keep_idx = []
used = np.zeros(len(point), bool)
for i in range(len(point)):
    if used[i]:
        continue
    d = cat[i].separation(cat).arcsec
    grp = np.where(d < 5.0)[0]
    used[grp] = True
    keep_idx.append(i)
print("unique pointings: %d" % len(keep_idx))
cand = []
for i in keep_idx:
    if cat[i].separation(excl).arcsec.min() > 5.0:
        cand.append(point[i])
print("after exclusions: %d" % len(cand))

# --- SDSS sigma_v crossmatch
rows = []
for k, (ra, dec, tname, prop) in enumerate(cand):
    try:
        t = SDSS.query_region(SkyCoord(ra * u.deg, dec * u.deg),
                              radius=3 * u.arcsec, spectro=True,
                              specobj_fields=["z", "velDisp", "velDispErr",
                                              "class", "zWarning"])
        if t is None or not len(t):
            continue
        b = t[0]
        vd, ve, z = float(b["velDisp"]), float(b["velDispErr"]), float(b["z"])
        if not (50 < vd < 450 and ve > 0 and z > 0.02):
            continue
        co = SkyCoord(ra * u.deg, dec * u.deg)
        name = "G4" + co.to_string("hmsdms", precision=0).replace(" ", "")[0:18]
        rows.append(dict(name="G4_%04d" % len(rows), ra_deg="%.5f" % ra,
                         dec_deg="%.5f" % dec, theta_E_pub="0.0", q_pub="0.0",
                         survey="LRGDEFL2",
                         src_table="prop%s_vd%.0f_ve%.0f_z%.3f" % (prop, vd, ve, z)))
    except Exception:
        pass
    if (k + 1) % 50 == 0:
        print("  crossmatched %d/%d, kept %d" % (k + 1, len(cand), len(rows)))

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["name", "ra_deg", "dec_deg", "theta_E_pub",
                                      "q_pub", "survey", "src_table"])
    w.writeheader()
    for r in rows:
        w.writerow(r)
vd = np.array([float(r["src_table"].split("_vd")[1].split("_")[0]) for r in rows])
print("\nFINAL TARGET LIST: %d galaxies with clean sigma_v -> %s" % (len(rows), OUT))
if len(rows):
    print("sigma_v: median %.0f, 16-84%% [%.0f, %.0f]; >250 km/s: %d (the high-theta tail)"
          % (np.median(vd), np.percentile(vd, 16), np.percentile(vd, 84),
             (vd > 250).sum()))
print("G1_TARGETS_DONE")
