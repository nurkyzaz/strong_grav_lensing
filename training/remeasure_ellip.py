#!/usr/bin/env python
"""
remeasure_ellip.py
------------------
Re-measure theta_E + ellipticity for a multi-output checkpoint on a test set,
reusing the EXACT training pipeline (train_cnn_multi.MultiDataset / evaluate_multi /
fmt) so preprocessing, the standardized scalar input, and output un-standardization
all match training. No preprocessing is re-implemented here.

Run it on lensed_test_m3.h5 (with lens light) AND lensed_test.h5 (arc-only, no lens
light): comparing the ellipticity R2 between the two IS the lens-light ablation.
"""
import argparse, numpy as np, torch
from torch.utils.data import DataLoader
from train_cnn_multi import MultiDataset, EinsteinCNNMulti, evaluate_multi, fmt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--image_file", required=True)
    ap.add_argument("--label_file", default="labels_test.h5")
    ap.add_argument("--ellip_file", default="ellip_test.h5")
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    device = torch.device(args.device)

    ck = torch.load(args.ckpt, map_location=device)
    ymean = ck["ymean"].cpu().numpy() if torch.is_tensor(ck["ymean"]) else np.asarray(ck["ymean"], dtype="float32")
    ystd  = ck["ystd"].cpu().numpy()  if torch.is_tensor(ck["ystd"])  else np.asarray(ck["ystd"],  dtype="float32")
    stats = (float(ck["scale_mean"]), float(ck["scale_std"]),
             ymean.astype("float32"), ystd.astype("float32"))

    # MultiDataset with stats=... reuses the checkpoint's training statistics
    ds = MultiDataset(args.image_file, args.label_file, args.ellip_file,
                      norm=ck.get("norm", "asinh"), asinh_a=ck.get("asinh_a", 1.0),
                      stats=stats)
    model = EinsteinCNNMulti(channels=tuple(ck["channels"]), n_out=ck["n_out"]).to(device)
    model.load_state_dict(ck["state_dict"]); model.eval()

    res = evaluate_multi(model, DataLoader(ds, batch_size=args.batch_size), device, ymean, ystd)
    print(f"\n=== {args.ckpt}  on  {args.image_file}  (N kept printed above) ===")
    print(fmt(res))
    if "e1" in res:
        r = 0.5 * (res["e1"][1] + res["e2"][1])
        verdict = ("REAL signal" if r > 0.5 else
                   "WEAK/partial" if r > 0.2 else "FAILED (~mean predictor)")
        print(f"   mean ellipticity R2 = {r:.2f}  -> {verdict}")
    print("   (sanity: theta frac should be ~2-3%; if it's wild, the label_file "
          "doesn't match this image set's kappa maps.)")


if __name__ == "__main__":
    main()
