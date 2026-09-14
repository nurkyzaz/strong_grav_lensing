#!/usr/bin/env python
"""Step 0 for Roman Data Challenge Rung 1: print the structure of a challenge
HDF5 so we can fill in the exact key names the train/predict scripts need.

The 11.8 GB labeled file (`roman_data_challenge_rung_1_v_3_0.h5`) and the
`view_rung_1_dataset.ipynb` example notebook are NOT in this repo -- they are
downloaded from Zenodo (doi:10.5281/zenodo.20249305 labeled;
doi:10.5281/zenodo.20249307 unlabeled). Run this on the machine that has the
download instead of reading the notebook by hand.

It reports, for every dataset in the file:
  - full key path, shape, dtype
  - for the image cube: inferred (N, bands, H, W) layout and per-band pixel
    stats (min / median / max) on a small sample
  - for any 0/1-looking column: the class balance (this is your label)
  - for any integer id-looking column: min/max (this is your submission ID)

Nothing here is Rung-1-specific beyond the candidate-name lists, so it also
works on the unlabeled file (which simply won't have a label column).

Usage:
    python inspect_rung1_h5.py /path/to/roman_data_challenge_rung_1_v_3_0.h5
    python inspect_rung1_h5.py /path/to/unlabeled.h5 --sample 512
"""
import argparse
import h5py
import numpy as np

# Best-guess key names, most likely first. The script auto-detects by shape
# too, so these are only used to LABEL what it finds, not to require it.
IMAGE_KEYS = ["lensed", "images", "image", "data", "cutouts", "x"]
LABEL_KEYS = ["label", "labels", "subhalo", "subhalos", "has_subhalos",
              "substructure", "y", "cdm", "class"]
ID_KEYS = ["ID", "id", "ids", "obj_id", "object_id", "index"]


def walk(f):
    """Yield (path, dataset) for every dataset in the file, recursively."""
    out = []

    def _visit(name, obj):
        if isinstance(obj, h5py.Dataset):
            out.append((name, obj))
    f.visititems(_visit)
    return out


def guess_role(name, dset):
    n = name.split("/")[-1].lower()
    shape = dset.shape
    if n in [k.lower() for k in IMAGE_KEYS] or (len(shape) >= 3):
        return "IMAGE?"
    if n in [k.lower() for k in LABEL_KEYS]:
        return "LABEL?"
    if n in [k.lower() for k in ID_KEYS]:
        return "ID?"
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("h5_path")
    ap.add_argument("--sample", type=int, default=256,
                    help="rows to sample for image/label stats")
    args = ap.parse_args()

    with h5py.File(args.h5_path, "r") as f:
        print(f"=== {args.h5_path} ===")
        if f.attrs:
            print("file attrs:", dict(f.attrs))
        datasets = walk(f)
        print(f"\n{len(datasets)} dataset(s):\n")
        for name, dset in datasets:
            role = guess_role(name, dset)
            print(f"  {name:24s} shape={str(dset.shape):22s} "
                  f"dtype={str(dset.dtype):10s} {role}")

        n_total = max((d.shape[0] for _, d in datasets), default=0)
        n = min(args.sample, n_total)
        print(f"\n--- stats on first {n} rows ---")

        for name, dset in datasets:
            shape = dset.shape
            # --- image cube: infer layout, per-band pixel stats ---
            if len(shape) >= 3:
                arr = dset[:n].astype("float32")
                if arr.ndim == 4 and arr.shape[1] in (1, 3, 4):
                    layout, bands = "(N,C,H,W)", arr.shape[1]
                    per_band = [arr[:, c] for c in range(bands)]
                elif arr.ndim == 4 and arr.shape[-1] in (1, 3, 4):
                    layout, bands = "(N,H,W,C)", arr.shape[-1]
                    per_band = [arr[..., c] for c in range(bands)]
                else:
                    layout, bands = "(N,H,W) single-band", 1
                    per_band = [arr]
                print(f"\n[{name}] layout {layout}  bands={bands}  "
                      f"H,W={shape[-2:] if layout != '(N,H,W,C)' else shape[1:3]}")
                for c, b in enumerate(per_band):
                    print(f"    band {c}: min {b.min():+.4g}  median "
                          f"{np.median(b):+.4g}  max {b.max():+.4g}  "
                          f"mean {b.mean():+.4g}")
                continue

            # --- 1-D columns: is it a binary label or an id? ---
            if len(shape) == 1:
                col = dset[:n]
                uniq = np.unique(col)
                if col.dtype.kind in "iub" and len(uniq) <= 10:
                    counts = {int(u): int((dset[:n] == u).sum()) for u in uniq}
                    print(f"\n[{name}] discrete, values {counts} "
                          f"(sample of {n})  <-- LABEL if this is 0/1")
                elif col.dtype.kind in "iu":
                    full = dset[:]
                    print(f"\n[{name}] integer  min {full.min()} max {full.max()} "
                          f"unique {len(np.unique(full))}  <-- ID if contiguous")
                else:
                    print(f"\n[{name}] float  min {col.min():.4g} "
                          f"max {col.max():.4g}")

    print("\nNow set these in train_cnn_rung1.py / predict_rung1.py:")
    print("  --image_key   the IMAGE? dataset above")
    print("  --label_key   the 0/1 LABEL? column above")
    print("  --id_key      the ID? column (or omit to use the row index)")
    print("Also open view_rung_1_dataset.ipynb once to confirm the required")
    print("submission COLUMN NAME and METRIC (AUC vs accuracy).")


if __name__ == "__main__":
    main()
