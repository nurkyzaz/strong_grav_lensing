#!/usr/bin/env python
"""GEN4-G2: merge the deflector libraries (new lrg2_v1 + old v6 train/val)
into ONE stamps file with a unified id namespace + unified kinematics CSV
(origin column kept for the G4 val split)."""
import csv
import numpy as np
import h5py

LIBS = [("deflector_stamps_lrg2_v1.h5", "g1_kinematics_v1.csv", "new"),
        ("deflector_stamps_lrg_v6_train.h5", "g1_kinematics_old_train.csv", "old_train"),
        ("deflector_stamps_lrg_v6_val.h5", "g1_kinematics_old_val.csv", "old_val")]
OUT_H5 = "deflector_stamps_g4_all.h5"
OUT_CSV = "g2_kinematics_unified.csv"

stamps, rows, off = [], [], 0
for h5fn, csvfn, origin in LIBS:
    with h5py.File(h5fn, "r") as f:
        st = f["stamps"][:]
    kin = {int(r["stamp_id"]): r for r in csv.DictReader(open(csvfn))}
    for i in range(len(st)):
        r = dict(kin.get(i, {}))
        r["stamp_id"] = off + i
        r["origin"] = origin
        rows.append(r)
    stamps.append(st.astype("float32"))
    off += len(st)
    print("%s: %d stamps (origin=%s)" % (h5fn, len(st), origin))

allst = np.concatenate(stamps)
with h5py.File(OUT_H5, "w") as f:
    f.create_dataset("stamps", data=allst)
    f.create_dataset("src_index", data=np.arange(len(allst)))
fields = ["stamp_id", "origin", "name", "src_index", "sigma_v", "sigma_err",
          "z_l", "mag", "re_arcsec", "q", "pa_deg", "prom", "flag_arcy"]
with open(OUT_CSV, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
print("unified: %s (%d stamps) + %s" % (OUT_H5, len(allst), OUT_CSV))
