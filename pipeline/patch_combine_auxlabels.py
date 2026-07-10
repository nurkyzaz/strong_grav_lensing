#!/usr/bin/env python
"""Add mass_e1/mass_e2 label datasets to hybrid_combine.py output (aux-head
labels for L2; labels only — images unchanged). Backup .bak_auxlabels."""
import os
import shutil

F = os.path.expanduser("~/cosmos_acs/tiles/hybrid_combine.py")
ANCHOR = 'fo.create_dataset("theta_E", data=theta.astype("float64"))'
MARK = 'mass_e1'
ADD = '''fo.create_dataset("theta_E", data=theta.astype("float64"))
    # aux-head labels (2026-07-10, plan 2b): mass ellipticity from paltas
    # metadata (same row order as theta_E). Labels only -- images unchanged.
    for _c in ("e1", "e2"):
        _col = "main_deflector_parameters_" + _c
        if _col in meta.columns:
            fo.create_dataset("mass_" + _c, data=meta[_col].values.astype("float64"))
        else:
            print("WARNING: %s not in metadata -- mass_%s label skipped" % (_col, _c))'''

src = open(F).read()
if MARK in src:
    print("already patched")
elif ANCHOR not in src:
    raise SystemExit("ANCHOR not found — hybrid_combine.py changed; abort")
else:
    shutil.copy(F, F + ".bak_auxlabels")
    open(F, "w").write(src.replace(ANCHOR, ADD, 1))
    print("patched hybrid_combine.py (backup .bak_auxlabels)")
