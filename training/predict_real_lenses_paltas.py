#!/usr/bin/env python
"""
predict_real_lenses_paltas.py -- Stage 4: run the paltas-hybrid-trained CNN
(einstein_cnn_paltas_v1.pt) over the frozen real-lens benchmark cutouts and
write a predicted-theta_E CSV for metrics_real.py.

Unlike predict_real_lenses.py (the OLD m3 script), this does NOT apply a
--peak flux rescale by default. m3 needed that hack because its training
data used an arbitrary/synthetic flux convention (sim peak ~20) divorced
from real cutouts' raw electrons/s (peak ~200) -- exactly the kind of
hand-tuning the 2026-07-02 paltas pivot was meant to eliminate. Our hybrid
training images ARE real-unit-calibrated (paltas HST zeropoint 25.94 +
real empty-cutout backdrops + noise matched to the real SLACS sky-RMS
distribution), verified by gate_stage0.py on the full 100k set (peak/sky
718 sim vs 492-1798 real band). So the default here is --peak 0 (raw,
no rescale) -- if that turns out wrong, the gate comparison was wrong, and
that itself is a finding worth having, not something to paper over with a
rescale flag.

Reads box_arcsec/pixscale from the real h5 itself rather than assuming
6.4"/0.05" (INSPECT, don't assume -- per CLAUDE.md).

Writes: <outdir>/<out> (columns: name, theta_E_pred_arcsec, theta_E_pub_arcsec)
"""
import os
import sys
import argparse
import csv

import numpy as np
import h5py
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_cnn_paltas import normalize_images, EinsteinCNNScale, build_model


def rescale_peak(imgs, peak):
    n = imgs.shape[-1]
    c, r = n // 2, n // 3
    central = imgs[:, c - r:c + r, c - r:c + r].reshape(len(imgs), -1)
    pk = np.percentile(central, 99.9, axis=1).reshape(-1, 1, 1)
    return (imgs * (peak / (pk + 1e-8))).astype("float32")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="einstein_cnn_paltas_v1.pt")
    ap.add_argument("--real", required=True, help="real_slacs_images.h5 or real_s4tm_images.h5")
    ap.add_argument("--image_key", default="images")
    ap.add_argument("--peak", type=float, default=0.0,
                    help="0 = raw (default, matches paltas's real-unit calibration); "
                        ">0 rescales each cutout's central peak to this value")
    ap.add_argument("--tta", action="store_true",
                    help="average over the 8 dihedral transforms (4 rotations x "
                         "flip) -- theta_E is invariant under all of them")
    ap.add_argument("--outdir", default="brian_run")
    ap.add_argument("--out", default="theta_E_pred.csv")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    ck = torch.load(args.ckpt, map_location=dev)
    out_dim = int(ck.get("out_dim", 1))
    arch = ck.get("arch", "resnet")
    net = build_model(arch, out_dim).to(dev)
    net.load_state_dict(ck["state_dict"]); net.eval()
    print(f"loaded arch={arch}")

    with h5py.File(args.real) as f:
        ik = args.image_key if args.image_key in f else list(f.keys())[0]
        imgs = f[ik][:].astype("float32")
        names = ([n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]]
                 if "names" in f else [f"lens_{i}" for i in range(len(imgs))])
        pub = f["theta_E_pub"][:].astype("float32") if "theta_E_pub" in f else None
        box_arcsec = float(f["box_arcsec"][()]) if "box_arcsec" in f else 6.4
        pixscale = float(f["pixscale"][()]) if "pixscale" in f else 0.05
    if imgs.ndim == 4:
        imgs = imgs[:, 0]
    print(f"{args.real}: N={len(imgs)}  box_arcsec={box_arcsec}  pixscale={pixscale}  "
          f"(training used image_fov=6.4, pixels=128 -> pix_scale={6.4/127:.6f})")

    if args.peak > 0:
        imgs = rescale_peak(imgs, args.peak)
        print(f"rescaled each cutout to central peak = {args.peak}")
    else:
        print("no flux rescale (--peak 0): training data is real-unit-calibrated, "
              "verified by gate_stage0.py peak/sky comparison on the full 100k set")

    x = normalize_images(imgs, ck["norm"], ck["asinh_a"])
    x = torch.from_numpy(x).unsqueeze(1).to(dev)
    img_scale = box_arcsec / (imgs.shape[-1] - 1)
    s = torch.full((len(x), 1), (img_scale - ck["scale_mean"]) / ck["scale_std"],
                   dtype=torch.float32, device=dev)

    def views(t):
        """The 8 dihedral transforms (theta_E-invariant)."""
        outs = []
        for flip in (False, True):
            tt = torch.flip(t, dims=[-1]) if flip else t
            for k in range(4):
                outs.append(torch.rot90(tt, k, dims=[-2, -1]))
        return outs

    mus, variances = [], []
    with torch.no_grad():
        for v in (views(x) if args.tta else [x]):
            out = net(v, s)
            if out_dim == 2:
                mus.append(out[:, 0].cpu().numpy())
                variances.append(np.exp(out[:, 1].clamp(-10, 3).cpu().numpy()))
            else:
                mus.append(out.cpu().numpy())
    mus = np.stack(mus)             # [n_views, N]
    pred = mus.mean(axis=0)
    # total sigma: mean aleatoric variance + variance across views (TTA spread)
    sigma = None
    if out_dim == 2:
        sigma = np.sqrt(np.stack(variances).mean(axis=0) + mus.var(axis=0))
    if args.tta:
        print(f"TTA over 8 dihedral views: mean per-lens view-spread "
              f"{mus.std(axis=0).mean():.4f}\"")

    path = os.path.join(args.outdir, args.out)
    with open(path, "w", newline="") as fo:
        w = csv.writer(fo)
        hdr = ["name", "theta_E_pred_arcsec"]
        hdr += ["theta_E_pub_arcsec"] if pub is not None else []
        hdr += ["theta_E_sigma_arcsec"] if sigma is not None else []
        w.writerow(hdr)
        for i, nm in enumerate(names):
            row = [nm, f"{pred[i]:.4f}"]
            row += [f"{pub[i]:.4f}"] if pub is not None else []
            row += [f"{sigma[i]:.4f}"] if sigma is not None else []
            w.writerow(row)
    print(f"wrote {path}  ({len(names)} lenses)")
    print(f"theta_E_pred: min {pred.min():.2f}  median {np.median(pred):.2f}  max {pred.max():.2f}")
    if sigma is not None:
        print(f"theta_E_sigma: median {np.median(sigma):.3f}\"  "
              f"(median sigma/pred = {np.median(sigma/pred)*100:.1f}%)")


if __name__ == "__main__":
    main()
