#!/usr/bin/env python
"""Evaluate a Model-2 checkpoint on the unseen-halo test set (varied FOV).
Reuses the TRAIN scale-normalization stored in the checkpoint."""
import argparse, torch
from torch.utils.data import DataLoader
from train_cnn_m2 import LensedScaleDataset, EinsteinCNNScale, evaluate

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image_file", default="lensed_test_m2.h5")
    ap.add_argument("--label_file", default="labels_test.h5")
    ap.add_argument("--ckpt", default="einstein_cnn_m2.pt")
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--min_theta_e", type=float, default=0.5)
    ap.add_argument("--max_theta_e", type=float, default=2.5)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    device = torch.device(args.device)

    ckpt = torch.load(args.ckpt, map_location=device)
    ds = LensedScaleDataset(args.image_file, args.label_file,
                            pixels=ckpt.get("pixels", 128),
                            min_theta_e=args.min_theta_e, max_theta_e=args.max_theta_e,
                            scale_stats=(ckpt["scale_mean"], ckpt["scale_std"]))
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=False)
    model = EinsteinCNNScale(channels=tuple(ckpt.get("channels", (32, 64, 128, 256)))).to(device)
    model.load_state_dict(ckpt["state_dict"])
    mae, frac, r2, (p16, p84) = evaluate(model, loader, device)
    print(f"[TEST m2] n={len(ds)} | MAE {mae:.4f} arcsec | median frac {frac:.2f}% | "
          f"R2 {r2:.3f} | 16-84% [{p16:+.1f}%,{p84:+.1f}%]")

if __name__ == "__main__":
    main()
