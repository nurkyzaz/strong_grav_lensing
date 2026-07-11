#!/usr/bin/env python
"""G4: split the unified deflector catalogue into train/val stamp sets.
Val = the 8 legacy val-origin stamps + every 8th NEW stamp by sigma_v rank
(sigma_v-spanning) -> ~20 val stamps; train = the rest. Stamp ids stay in the
UNIFIED namespace (both manifests draw from deflector_stamps_g4_all.h5)."""
import csv

rows = list(csv.DictReader(open("g2_kinematics_unified.csv")))
new = sorted([r for r in rows if r["origin"] == "new" and r["sigma_v"]],
             key=lambda r: float(r["sigma_v"]))
val_ids = {int(r["stamp_id"]) for r in rows if r["origin"] == "old_val"}
val_ids |= {int(r["stamp_id"]) for r in new[::8]}
tr, va = [], []
for r in rows:
    (va if int(r["stamp_id"]) in val_ids else tr).append(r)
for fn, rs in (("g4_kine_train.csv", tr), ("g4_kine_val.csv", va)):
    with open(fn, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rs:
            w.writerow(r)
    sv = [float(r["sigma_v"]) for r in rs if r["sigma_v"]]
    print("%s: %d stamps, sigma_v [%.0f, %.0f]" % (fn, len(rs), min(sv), max(sv)))
