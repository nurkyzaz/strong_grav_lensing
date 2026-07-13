#!/usr/bin/env python
"""
test_hstempty_slacs.py
======================
Run an HSTempty checkpoint on the real, lens-subtracted SLACS lenses and report the
same metrics as the sim test (median frac, 16-84%, R2 [coeff of determination], MAE),
plus a scatter PNG.

Reuses train_cnn_m3's normalize_images + EinsteinCNNScale so the input normalization
matches training EXACTLY. The scale-conditioning input is fed as the stored scale_mean
(so the normalized scale is exactly 0 -- correct for the single-FOV HSTempty model).

Usage:
  python test_hstempty_slacs.py --ckpt einstein_cnn_hstempty.pt --slacs real_slacs_residual_v2.h5
"""
import argparse
import numpy as np, h5py, torch
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from train_cnn_m3 import normalize_images, EinsteinCNNScale


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="einstein_cnn_hstempty.pt")
    ap.add_argument("--slacs", default="real_slacs_residual_v2.h5")
    ap.add_argument("--image_key", default="images", help="try 'residual' if 'images' missing")
    ap.add_argument("--label_key", default="theta_E_pub")
    ap.add_argument("--out", default="hstempty_slacs.png")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    device = torch.device(args.device)

    ckpt = torch.load(args.ckpt, map_location=device)
    with h5py.File(args.slacs, "r") as f:
        keys = list(f.keys())
        ikey = args.image_key if args.image_key in f else ("residual" if "residual" in f else None)
        if ikey is None:
            raise SystemExit(f"no image key '{args.image_key}' in {args.slacs}; keys present: {keys}")
        imgs = f[ikey][:].astype("float32")
        names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]] if "names" in f else None
        gt = f[args.label_key][:].astype("float32")
    if imgs.ndim == 4:  # [N,1,128,128] -> [N,128,128]
        imgs = imgs[:, 0]

    # same input normalization as training
    x = normalize_images(imgs, ckpt.get("norm", "asinh"), ckpt.get("asinh_a", 1.0))
    x = torch.from_numpy(x).unsqueeze(1).to(device)
    # single-FOV model: feed scale = scale_mean so the normalized scale is exactly 0
    s = torch.zeros(len(x), 1, dtype=torch.float32, device=device)

    model = EinsteinCNNScale(channels=tuple(ckpt.get("channels", (32, 64, 128, 256)))).to(device)
    model.load_state_dict(ckpt["state_dict"]); model.eval()
    with torch.no_grad():
        pred = model(x, s).cpu().numpy()

    valid = gt > 0
    P, T = pred[valid], gt[valid]
    fr = 100 * (P - T) / T
    ss_res = np.sum((T - P) ** 2); ss_tot = np.sum((T - T.mean()) ** 2)
    R2 = float(1 - ss_res / (ss_tot + 1e-12))
    print(f"[HSTempty on real SLACS] N={len(P)} | median frac {np.median(fr):+.1f}% | "
          f"16-84% [{np.percentile(fr,16):+.1f},{np.percentile(fr,84):+.1f}] | "
          f"R2 {R2:.2f} | MAE {np.mean(np.abs(P-T)):.3f}\"")

    import os
    base = os.path.splitext(os.path.basename(args.slacs))[0]
    np.savetxt(base + "_preds.csv", np.column_stack([gt.astype(float), np.asarray(pred).reshape(-1).astype(float)]), delimiter=",", header="theta_true,theta_pred", comments="")
    print("wrote", base + "_preds.csv")
    plt.figure(figsize=(5, 5))
    plt.scatter(T, P, s=18)
    lim = [0.4, 2.6]; plt.plot(lim, lim, "k--", lw=1)
    plt.xlim(lim); plt.ylim(lim)
    plt.xlabel("Bolton SIE theta_E [\"]"); plt.ylabel("CNN theta_E [\"]")
    plt.title(f"HSTempty | median {np.median(fr):+.1f}%  R2={R2:.2f}\n"
              f"caveat: kappa_bar=1 labels vs SIE -> partly definitional offset")
    plt.tight_layout(); plt.savefig(args.out, dpi=120)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
