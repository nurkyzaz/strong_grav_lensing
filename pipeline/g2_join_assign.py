#!/usr/bin/env python
"""GEN4-G2: recover the manifest row for every ACCEPTED render (mag_cut
rejections skip rows) by exact theta_E match, verify with e1, and write the
combine assignment (file_row -> stamp_id, dihedral_k) plus the accepted-rows
manifest for gates/labels.
Usage: g2_join_assign.py <run_dir> <manifest.csv> <assign_out.csv>"""
import csv
import sys
import numpy as np
import pandas as pd

run, mfn, out = sys.argv[1], sys.argv[2], sys.argv[3]
meta = pd.read_csv(run.rstrip("/") + "/metadata.csv")
man = pd.read_csv(mfn)
th_m = man["theta_E"].values
e1_m = man["mass_e1"].values

rows = []
used = set()
for i, (th, e1) in enumerate(zip(
        meta["main_deflector_parameters_theta_E"].values,
        meta["main_deflector_parameters_e1"].values)):
    cand = np.where(np.abs(th_m - th) < 1e-5)[0]
    cand = [c for c in cand if c not in used and abs(e1_m[c] - e1) < 1e-5]
    assert cand, "no manifest match for image %d (theta %.6f)" % (i, th)
    c = cand[0]
    used.add(c)
    r = man.iloc[c]
    row = dict(file_row=i, manifest_row=int(c), stamp_id=int(r["stamp_id"]),
               dihedral_k=int(r["dihedral_k"]), theta_E=th,
               stamp_mag=float(r["stamp_mag"]),
               sigma_v_used=float(r["sigma_v_used"]), z_l=float(r["z_l"]),
               z_source=float(r["z_source"]))
    # C21/AR3: carry migration + multipole columns when the manifest has them
    for col in ("z_l_new", "mig_scale", "mig_sb", "stamp_mag_mig",
                "mult3_a", "mult3_phi", "mult4_a", "mult4_phi"):
        if col in man.columns:
            row[col] = float(r[col])
    rows.append(row)

with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows:
        w.writerow(r)
th = np.array([r["theta_E"] for r in rows])
print("assigned %d/%d renders to manifest rows (1:1 verified); theta med %.3f"
      % (len(rows), len(meta), np.median(th)))
