#!/usr/bin/env python
"""Better circle overlay: asinh display (so arcs show under bright lens light) and the
theta_E ring centred on the LENS (kappa-map centroid), not the image centre. Also draws
the image-centre ring (white dotted) for reference, so you can SEE which centre the arc
follows. Reads kappa maps from --kappa_file by kappa_index to find the lens centre."""
import argparse, h5py, numpy as np, torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from train_cnn_m3 import EinsteinCNNScale, load_theta_pixels, normalize_images

def lens_center(kappa):
    """convergence-weighted centroid (pixels), robust-ish for off-centre halos."""
    m = np.clip(kappa, 0, None).astype("float64")
    y, x = np.indices(m.shape)
    s = m.sum() + 1e-12
    return (x * m).sum() / s, (y * m).sum() / s   # (cx, cy)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image_file", required=True)
    ap.add_argument("--kappa_file",
                    default="/home/user/ckwan1/ml_project/strong_lensing_dataset/"
                            "kappa_light/test_camera_complete.h5")
    ap.add_argument("--label_file", default="labels_test.h5")
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--out", default="diag_circles.png")
    ap.add_argument("--n_panels", type=int, default=16)
    ap.add_argument("--only_bright", action="store_true",
                    help="show the brightest-centre (most lens light) images")
    ap.add_argument("--pixels", type=int, default=128)
    ap.add_argument("--min_theta_e", type=float, default=0.5)
    ap.add_argument("--max_theta_e", type=float, default=2.5)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    device = torch.device(args.device)

    ckpt = torch.load(args.ckpt, map_location=device)
    norm = ckpt.get("norm", "minmax"); asinh_a = float(ckpt.get("asinh_a", 1.0))
    s_mean, s_std = ckpt["scale_mean"], ckpt["scale_std"]

    with h5py.File(args.image_file, "r") as f:
        raw = f["lensed"][:].astype("float32")
        kidx = f["kappa_index"][:].astype("int64")
        fov = (f["image_fov"][:].astype("float32") if "image_fov" in f
               else np.full(len(raw), 7.68, dtype="float32"))
    lut = load_theta_pixels(args.label_file)
    true = lut[kidx] * (fov / (args.pixels - 1))
    keep = (true >= args.min_theta_e) & (true <= args.max_theta_e)
    raw, true, fov, kidx = raw[keep], true[keep], fov[keep], kidx[keep]

    imgs = normalize_images(raw, norm, asinh_a)
    scale = ((fov/(args.pixels-1) - s_mean) / s_std).astype("float32")
    model = EinsteinCNNScale(channels=tuple(ckpt.get("channels", (32,64,128,256)))).to(device)
    model.load_state_dict(ckpt["state_dict"]); model.eval()
    preds = []
    with torch.no_grad():
        for i in range(0, len(imgs), 256):
            x = torch.from_numpy(imgs[i:i+256]).unsqueeze(1).to(device)
            s = torch.from_numpy(scale[i:i+256]).unsqueeze(1).to(device)
            preds.append(model(x, s).cpu().numpy())
    pred = np.concatenate(preds)

    if args.only_bright:
        p99 = np.percentile(raw.reshape(len(raw), -1), 99, axis=1)
        sel = np.argsort(p99)[-args.n_panels:][::-1]
    else:
        sel = rng.choice(len(raw), size=min(args.n_panels, len(raw)), replace=False)

    with h5py.File(args.kappa_file, "r") as f:
        kds = f["kappa"]
        centers = {int(j): lens_center(kds[int(kidx[j])].astype("float32")) for j in sel}

    g = int(np.ceil(np.sqrt(len(sel))))
    fig, axes = plt.subplots(g, g, figsize=(3.0*g, 3.0*g))
    for ax in np.ravel(axes): ax.axis('off')
    for ax, j in zip(np.ravel(axes), sel):
        disp = np.arcsinh(raw[j] / asinh_a)
        ax.imshow(disp, cmap='gray', origin='lower')
        pa = (args.pixels - 1) / fov[j]
        cx, cy = centers[int(j)]
        ax.add_patch(plt.Circle((cx, cy), true[j]*pa, color='lime', fill=False, lw=1.6))
        ax.add_patch(plt.Circle((cx, cy), pred[j]*pa, color='red', fill=False, lw=1.1, ls='--'))
        ax.add_patch(plt.Circle((63.5,63.5), true[j]*pa, color='white', fill=False, lw=0.8, ls=':'))
        ax.plot([cx],[cy], '+', color='cyan', ms=8, mew=1.5)
        ax.set_title(f'true {true[j]:.2f}/pred {pred[j]:.2f}"  FOV{fov[j]:.1f}', fontsize=8)
        ax.axis('off')
    fig.suptitle("green=true@lens-centre  red=pred@lens-centre  white:=true@image-centre  +=lens centre")
    plt.tight_layout(); plt.savefig(args.out, dpi=110); plt.close()
    off = np.array([np.hypot(centers[int(j)][0]-63.5, centers[int(j)][1]-63.5) for j in sel])
    print(f"[circles] wrote {args.out} | lens-centre offset from image centre: "
          f"median {np.median(off):.1f} px, max {off.max():.1f} px")

if __name__ == "__main__":
    main()
