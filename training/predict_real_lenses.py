#!/usr/bin/env python
"""
predict_real_lenses.py  (+ --peak flux rescale)
Run Model 3 over real lens cutouts and write a predicted-theta_E list.

m3 was trained on SIM flux (image peak ~20). Real cutouts are raw e-/s (peak ~205),
and asinh(image/a) is nonlinear, so feeding raw flux biases predictions LOW. Use
--peak 20 to rescale each cutout into the sim regime BEFORE normalization (matches
how m3 was trained). --peak 0 (default) keeps the old raw behaviour.

Writes: <outdir>/<out>  (columns: name, theta_E_pred_arcsec[, theta_E_pub_arcsec])
"""
import os, argparse, numpy as np, h5py, torch, csv
from train_cnn_m3 import normalize_images, EinsteinCNNScale


def parse():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", default="einstein_cnn_m3.pt")
    p.add_argument("--slacs", default="real_slacs_images.h5", help="RAW cutouts h5")
    p.add_argument("--image_key", default="images")
    p.add_argument("--fov", type=float, default=6.4)
    p.add_argument("--peak", type=float, default=0.0,
                   help="rescale each image so its central peak = this value "
                        "(20 matches m3 sim flux; 0 = off / raw)")
    p.add_argument("--outdir", default="brian_run")
    p.add_argument("--out", default="theta_E_for_brian.csv")
    return p.parse_args()


def rescale_peak(imgs, peak):
    """Per-image: scale so the robust central peak == `peak`. Central region +
    99.9th percentile dodges corner stars / single-pixel cosmic-ray spikes."""
    n = imgs.shape[-1]
    c, r = n // 2, n // 3
    central = imgs[:, c - r:c + r, c - r:c + r].reshape(len(imgs), -1)
    pk = np.percentile(central, 99.9, axis=1).reshape(-1, 1, 1)
    return (imgs * (peak / (pk + 1e-8))).astype("float32")


def main():
    a = parse(); os.makedirs(a.outdir, exist_ok=True)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    ck = torch.load(a.ckpt, map_location=dev)
    net = EinsteinCNNScale(channels=tuple(ck["channels"])).to(dev)
    net.load_state_dict(ck["state_dict"]); net.eval()

    with h5py.File(a.slacs) as f:
        ik = a.image_key if a.image_key in f else list(f.keys())[0]
        imgs = f[ik][:].astype("float32")
        names = [n.decode() if isinstance(n, bytes) else str(n)
                 for n in f["names"][:]] if "names" in f else [f"lens_{i}" for i in range(len(imgs))]
        pub = f["theta_E_pub"][:].astype("float32") if "theta_E_pub" in f else None
    if imgs.ndim == 4:
        imgs = imgs[:, 0]

    if a.peak > 0:
        imgs = rescale_peak(imgs, a.peak)
        print(f"rescaled each cutout to central peak = {a.peak} (sim-matched flux)")
    else:
        print("WARNING: --peak 0 (raw e-/s). m3 was trained on peak~20 sim flux; "
              "raw flux biases predictions LOW. Use --peak 20 for a matched baseline.")

    x = normalize_images(imgs, ck["norm"], ck["asinh_a"])
    x = torch.from_numpy(x).unsqueeze(1).to(dev)
    img_scale = a.fov / 127
    s = torch.full((len(x), 1), (img_scale - ck["scale_mean"]) / ck["scale_std"],
                   dtype=torch.float32, device=dev)
    with torch.no_grad():
        pred = net(x, s).cpu().numpy().reshape(-1)

    path = os.path.join(a.outdir, a.out)
    with open(path, "w", newline="") as fo:
        w = csv.writer(fo)
        hdr = ["name", "theta_E_pred_arcsec"] + (["theta_E_pub_arcsec"] if pub is not None else [])
        w.writerow(hdr)
        for i, nm in enumerate(names):
            w.writerow([nm, f"{pred[i]:.4f}"] + ([f"{pub[i]:.4f}"] if pub is not None else []))
    print(f"wrote {path}  ({len(names)} lenses)")
    print(f"theta_E_pred: min {pred.min():.2f}  median {np.median(pred):.2f}  max {pred.max():.2f}")


if __name__ == "__main__":
    main()
