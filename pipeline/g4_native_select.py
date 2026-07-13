#!/usr/bin/env python
"""GEN4 Track-N: select native-arm rows matching the Euclid-arm selection.

Native and Euclidised composed h5 share pre-selection row order; the selected
Euclid shard carries (theta_E, mass_e1), unique per render at float64 precision
(the same identity g2_join_assign uses). Keep exactly those rows of the native
composed h5, and carry the Euclid arc_snr/arc_extent across (aligned by key)
so the native shard has the same aux columns as the Euclid one.

Usage: g4_native_select.py --native native_XX.h5 --euclid-sel sel_XX.h5 --out native_shard_XX.h5
"""
import argparse

import h5py
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--native", required=True, help="native composed h5 (pre-selection order)")
ap.add_argument("--euclid-sel", required=True, help="arc_visibility_select output for the SAME shard")
ap.add_argument("--out", required=True)
args = ap.parse_args()

with h5py.File(args.euclid_sel, "r") as f:
    sel_key = list(zip(f["theta_E"][:], f["mass_e1"][:]))
    sel_snr = f["arc_snr"][:]
    sel_ext = f["arc_extent"][:]
sel_map = {k: i for i, k in enumerate(sel_key)}
assert len(sel_map) == len(sel_key), "duplicate (theta_E, e1) keys in selected shard"

with h5py.File(args.native, "r") as f:
    nat_key = list(zip(f["theta_E"][:], f["mass_e1"][:]))
    keep = np.array([k in sel_map for k in nat_key])
    order = np.array([sel_map[k] for k in nat_key if k in sel_map])
    assert keep.sum() == len(sel_key), (
        "selection mismatch: %d matched vs %d selected" % (keep.sum(), len(sel_key)))
    with h5py.File(args.out, "w") as fo:
        for k in f.keys():
            v = f[k][()] if f[k].shape == () else f[k][:]
            fo.create_dataset(k, data=v[keep] if v.shape[:1] == (len(nat_key),) else v)
        # order[j] = index into the selected-Euclid arrays for output row j
        fo.create_dataset("arc_snr", data=sel_snr[order])
        fo.create_dataset("arc_extent", data=sel_ext[order])
print("native select: %d/%d rows kept -> %s" % (keep.sum(), len(nat_key), args.out))
