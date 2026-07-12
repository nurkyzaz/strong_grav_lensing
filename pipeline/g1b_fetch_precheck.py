#!/usr/bin/env python
"""G1b fetch precondition (COMMITMENTS C4 + phase-1 selection):
- crossmatch lrgdefl2b targets against known-lens compilations via VizieR
  (BELLS Brownstein+2012, SL2S Sonnenfeld+2013, SLACS XIII Auger+2009);
  network failure -> WARN and continue (visual prune is the backstop);
- keep ACS/WFC targets only (C3 UVIS resample not yet built);
- phase 1 = first 800 by the existing priority order (sigma_v>=250 first).
Writes lrgdefl2b_phase1.csv next to the labels file.
"""
import csv
import os

import numpy as np

EC = os.path.expanduser("~/einstein_cnn")
SRC = os.path.join(EC, "lrgdefl2b_labels.csv")
DST = os.path.join(EC, "lrgdefl2b_phase1.csv")

rows = list(csv.DictReader(open(SRC)))
print("targets in:", len(rows))
rows = [r for r in rows if "ACSWFC" in r["src_table"]]
print("ACS/WFC only (C3 defers UVIS):", len(rows))

lens_coords = []
try:
    from astroquery.vizier import Vizier
    v = Vizier(columns=["RAJ2000", "DEJ2000", "_RA", "_DE"], row_limit=-1)
    for cat in ("J/ApJ/744/41", "J/ApJ/777/98", "J/ApJ/705/1099"):
        try:
            tl = v.get_catalogs(cat)
            for t in tl:
                for ra_k, de_k in (("RAJ2000", "DEJ2000"), ("_RA", "_DE")):
                    if ra_k in t.colnames and de_k in t.colnames:
                        for x in t:
                            try:
                                lens_coords.append((float(x[ra_k]), float(x[de_k])))
                            except Exception:
                                pass
                        break
            print("  %s: cumulative lens coords %d" % (cat, len(lens_coords)))
        except Exception as e:
            print("  WARN %s failed: %s" % (cat, str(e)[:80]))
except Exception as e:
    print("WARN VizieR unavailable (%s) — visual prune is the backstop" % str(e)[:80])

if lens_coords:
    lr = np.radians(np.array([c[0] for c in lens_coords]))
    ld = np.radians(np.array([c[1] for c in lens_coords]))
    keep = []
    for r in rows:
        ra, de = np.radians(float(r["ra_deg"])), np.radians(float(r["dec_deg"]))
        sep = np.degrees(np.arccos(np.clip(
            np.sin(de) * np.sin(ld) + np.cos(de) * np.cos(ld) * np.cos(ra - lr),
            -1, 1))) * 3600.0
        if sep.min() > 5.0:
            keep.append(r)
    print("after known-lens crossmatch (5\"): %d (removed %d)"
          % (len(keep), len(rows) - len(keep)))
    rows = keep

rows = rows[:800]
with open(DST, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows:
        w.writerow(r)
print("wrote %s: %d phase-1 targets" % (DST, len(rows)))
print("G1B_PRECHECK_DONE")
