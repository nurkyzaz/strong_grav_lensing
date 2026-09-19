#!/usr/bin/env python
"""Step 0 for Roman Data Challenge Rung 1: print the structure of a challenge
HDF5 so we can confirm the group/attr layout the train/predict scripts rely on.

The real layout (from view_rung_1_dataset.ipynb) is a per-lens GROUP hierarchy,
not a flat image cube:

    images/
      strong_lens_00000000/           (attrs: substructure, uid, theta_e, ...)
        exposure_00000000_F106        (91, 91) float, MJy/sr
        exposure_00000000_F129
        exposure_00000000_F158
      strong_lens_00000001/
      ...

  * label = group.attrs['substructure'][0]  -> 'True' / 'False'
  * id    = group.attrs['uid'][0]           -> '00000000'
  * bands = F106, F129, F158  (10.01" FOV, 0.11"/pix -> 91x91)

This reports the root attrs, the number of lenses, the exposure shape/dtype and
per-band pixel ranges, and the substructure class balance over a sample. Works
on the unlabeled file too (which has no 'substructure' attr).

    python inspect_rung1_h5.py roman_data_challenge_rung_1_v_3_0.h5 --sample 400
"""
import argparse
import h5py
import numpy as np

BANDS = ["F106", "F129", "F158"]


def attr0(group, name, default=None):
    """mejiro stores each attr as [value, description]; return the value."""
    if name not in group.attrs:
        return default
    v = group.attrs[name]
    v = v[0] if np.ndim(v) > 0 else v
    if isinstance(v, bytes):
        v = v.decode()
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("h5_path")
    ap.add_argument("--sample", type=int, default=400,
                    help="lenses to sample for label balance + pixel stats")
    args = ap.parse_args()

    with h5py.File(args.h5_path, "r") as f:
        print(f"=== {args.h5_path} ===")
        print("root attrs:")
        for k, v in f.attrs.items():
            print(f"  {k}: {v}")

        if "images" not in f:
            print("\n!! no 'images' group -- unexpected layout; top-level keys:",
                  list(f.keys()))
            return
        g = f["images"]
        names = list(g.keys())
        n_total = len(names)
        print(f"\nimages/: {n_total} lens groups")
        print("first 5:", names[:5])

        # structure of the first lens
        first = g[names[0]]
        uid0 = attr0(first, "uid")
        print(f"\nfirst lens '{names[0]}' uid={uid0}")
        print("  datasets:", list(first.keys()))
        for b in BANDS:
            key = f"exposure_{uid0}_{b}"
            if key in first:
                d = first[key]
                print(f"    {key}: shape={d.shape} dtype={d.dtype}")
        print("  attrs:", {k: attr0(first, k) for k in
                           ("substructure", "theta_e", "z_lens", "z_source",
                            "sigma_sub", "log_mlow", "log_mhigh")})

        # sample for label balance + per-band pixel ranges
        n = min(args.sample, n_total)
        idx = np.linspace(0, n_total - 1, n).astype(int)
        labels, has_sub_attr = [], ("substructure" in first.attrs)
        band_stats = {b: [] for b in BANDS}
        missing = 0
        for i in idx:
            grp = g[names[i]]
            uid = attr0(grp, "uid")
            if has_sub_attr:
                labels.append(str(attr0(grp, "substructure")))
            for b in BANDS:
                key = f"exposure_{uid}_{b}"
                if key in grp:
                    arr = grp[key][:]
                    band_stats[b].append((float(arr.min()), float(np.median(arr)),
                                          float(arr.max())))
                else:
                    missing += 1

        print(f"\n--- sample of {n} lenses ---")
        if has_sub_attr:
            uq, ct = np.unique(labels, return_counts=True)
            print("substructure balance:", dict(zip(uq.tolist(), ct.tolist())),
                  "  <-- LABEL (binary)")
        else:
            print("no 'substructure' attr -> this is the UNLABELED set")
        if missing:
            print(f"!! {missing} expected exposures missing (band naming?)")
        for b in BANDS:
            s = np.array(band_stats[b])
            if len(s):
                print(f"  {b}: min~{s[:,0].mean():+.4g}  median~{s[:,1].mean():+.4g}"
                      f"  max~{s[:,2].mean():+.4g}   (units MJy/sr)")

    print("\nFor train/predict: image key = per-group 'exposure_<uid>_<band>',")
    print("label attr = 'substructure' (True/False), id attr = 'uid'.")
    print("These are already the defaults in train_cnn_rung1.py / predict_rung1.py.")


if __name__ == "__main__":
    main()
