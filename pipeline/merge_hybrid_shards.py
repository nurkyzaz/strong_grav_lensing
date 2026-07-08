#!/usr/bin/env python
"""Merge Stage-2 hybrid shards into the final training/validation files.

    python merge_hybrid_shards.py --shards ~/paltas_shards \
        --train-out ~/einstein_cnn/train_hybrid_100k.h5 \
        --val-out ~/einstein_cnn/val_hybrid_5k.h5

Train = shards 00-19, val = shards 20-21 (disjoint seeds and PSF kernels).
Keeps per-image provenance (shard id -> which ePSF kernel; cutout index;
topup sigma). Verifies every shard's theta_E range before merging.
"""
import argparse
import glob
import os

import h5py
import numpy as np


def merge(paths, out):
    n_total = 0
    for p in paths:
        with h5py.File(p, "r") as f:
            n_total += f["lensed"].shape[0]
    with h5py.File(out, "w") as fo:
        d_img = fo.create_dataset("lensed", (n_total, 128, 128), dtype="float32")
        d_th = fo.create_dataset("theta_E", (n_total,), dtype="float64")
        d_fov = fo.create_dataset("image_fov", (n_total,), dtype="float64")
        d_sh = fo.create_dataset("shard", (n_total,), dtype="int16")
        d_cut = fo.create_dataset("cutout_index", (n_total,), dtype="int64")
        d_top = fo.create_dataset("topup_sigma", (n_total,), dtype="float32")
        w = 0
        for p in paths:
            sid = int(os.path.basename(p).split("_")[-1].split(".")[0])
            with h5py.File(p, "r") as f:
                n = f["lensed"].shape[0]
                th = f["theta_E"][:]
                assert 0.4 < th.min() and th.max() < 2.5, f"theta_E range bad in {p}"
                d_img[w:w + n] = f["lensed"][:]
                d_th[w:w + n] = th
                d_fov[w:w + n] = f["image_fov"][:]
                d_cut[w:w + n] = f["cutout_index"][:]
                d_top[w:w + n] = f["topup_sigma"][:]
                d_sh[w:w + n] = sid
            w += n
            print(f"  merged {os.path.basename(p)} ({n})")
        fo.attrs["note"] = "Stage-2 hybrid dataset; shard id maps to psf_bank kernel"
    print(f"wrote {out}: {n_total} images, "
          f"theta_E [{d_th is None}]")
    with h5py.File(out, "r") as f:
        th = f["theta_E"][:]
        print(f"  theta_E [{th.min():.3f}, {th.max():.3f}] median {np.median(th):.3f}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--shards", default=os.path.expanduser("~/paltas_shards"))
    p.add_argument("--train-out", required=True)
    p.add_argument("--val-out", required=True)
    p.add_argument("--train-max-id", type=int, default=20,
                   help="shard ids < this are train, >= are val "
                        "(v1 layout: 20; v2 sub-shard layout: 80)")
    args = p.parse_args()

    all_h5 = sorted(glob.glob(os.path.join(
        os.path.expanduser(args.shards), "hybrid_shard_*.h5")))
    train = [p for p in all_h5
             if int(os.path.basename(p).split("_")[-1].split(".")[0]) < args.train_max_id]
    val = [p for p in all_h5
           if int(os.path.basename(p).split("_")[-1].split(".")[0]) >= args.train_max_id]
    print(f"train shards: {len(train)}, val shards: {len(val)}")
    merge(train, os.path.expanduser(args.train_out))
    merge(val, os.path.expanduser(args.val_out))


if __name__ == "__main__":
    main()
