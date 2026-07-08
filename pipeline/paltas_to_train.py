#!/usr/bin/env python
"""
paltas_to_train.py
Convert a paltas run (image_data.h5 + metadata.csv) into the format train_cnn_m3.py reads:
  'lensed'   [N,128,128] float32   raw electrons (apply normalize_images at train time)
  'theta_E'  [N] float32           SIE Einstein radius (arcsec) -- SAME convention as SLACS b_SIE
  'image_fov'[N] float32           6.4 (so existing arcsec reconstruction is consistent)

paltas writes images as key 'data'; the label is metadata column
'main_deflector_parameters_theta_E'. No kappa_index here -> theta_E is per-image directly,
so point train_cnn_m3.py at the 'theta_E' key instead of joining labels by kappa_index.

Usage:
  python paltas_to_train.py --run ~/simct_paltas --out simct_paltas_train.h5 --fov 6.4
  python paltas_to_train.py --run ~/simct_paltas --preview 8     # sanity-check first
"""
import argparse, os
import numpy as np, h5py, pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="paltas save_folder (has image_data.h5 + metadata.csv)")
    ap.add_argument("--out", default="simct_paltas_train.h5")
    ap.add_argument("--fov", type=float, default=6.4)
    ap.add_argument("--label_col", default="main_deflector_parameters_theta_E")
    ap.add_argument("--preview", type=int, default=0)
    args = ap.parse_args()

    with h5py.File(os.path.join(args.run, "image_data.h5"), "r") as f:
        imgs = f["data"][:].astype("float32")
    meta = pd.read_csv(os.path.join(args.run, "metadata.csv"))
    if args.label_col not in meta.columns:
        cand = [c for c in meta.columns if "theta_E" in c]
        raise SystemExit(f"{args.label_col} not in metadata. theta_E-like columns: {cand}")
    theta = meta[args.label_col].to_numpy("float32")
    assert len(imgs) == len(theta), f"{len(imgs)} images vs {len(theta)} labels"
    print(f"{len(imgs)} images | theta_E median {np.median(theta):.2f}\" "
          f"range [{theta.min():.2f},{theta.max():.2f}]")

    if args.preview:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 4, figsize=(12, 6))
        for j in range(min(args.preview, 8)):
            im = imgs[j]; v = np.arcsinh((im - np.median(im)) / (np.std(im) + 1e-8))
            ax.flat[j].imshow(v, origin="lower", cmap="gray")
            ax.flat[j].set_title(f"theta_E={theta[j]:.2f}\"", fontsize=8)
            ax.flat[j].axis("off")
        fig.suptitle("paltas SIMCT -- compare to previews/slacs/*.png")
        fig.savefig("paltas_preview.png", dpi=110, bbox_inches="tight")
        print("wrote paltas_preview.png"); return

    with h5py.File(args.out, "w") as f:
        f.create_dataset("lensed", data=imgs)
        f.create_dataset("theta_E", data=theta)
        f.create_dataset("image_fov", data=np.full(len(imgs), args.fov, "float32"))
        f.attrs["note"] = "paltas SIMCT: real COSMOS sources + Sersic lens light, ACS F814W; theta_E=SIE"
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
