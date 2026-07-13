#!/usr/bin/env python
"""Fix merge_hybrid_shards.py provenance drop (bug logged at eval #14): carry
ALL per-image 1-D provenance/label columns through the merge, with native
dtypes. Backup .bak_prov."""
import os
import shutil

F = os.path.expanduser("~/cosmos_acs/tiles/merge_hybrid_shards.py")
OLD = '''        with h5py.File(paths[0], "r") as f0:
            opt_keys = [k for k in ("arc_snr", "arc_extent") if k in f0]
        d_opt = {k: fo.create_dataset(k, (n_total,), dtype="float32")
                 for k in opt_keys}'''
NEW = '''        with h5py.File(paths[0], "r") as f0:
            # 2026-07-10 fix (bug logged at eval #14): carry ALL 1-D per-image
            # provenance/label columns (deflector_*, mass_e1/e2, n_companions,
            # target_rms, arc_snr/extent, ...) with their native dtypes.
            _explicit = {"lensed", "theta_E", "image_fov", "cutout_index",
                         "topup_sigma", "shard"}
            opt_keys = [k for k in f0.keys()
                        if k not in _explicit and f0[k].ndim == 1
                        and f0[k].shape[0] == f0["lensed"].shape[0]]
            _dtypes = {k: f0[k].dtype for k in opt_keys}
        d_opt = {k: fo.create_dataset(k, (n_total,), dtype=_dtypes[k])
                 for k in opt_keys}'''

src = open(F).read()
if "_explicit" in src:
    print("already patched")
elif OLD not in src:
    raise SystemExit("anchor block not found — merge_hybrid_shards.py changed; abort")
else:
    shutil.copy(F, F + ".bak_prov")
    open(F, "w").write(src.replace(OLD, NEW, 1))
    print("patched merge_hybrid_shards.py (backup .bak_prov)")
