#!/usr/bin/env python
"""Show lensed images with the TRUE theta_E ring (green), using an aggressive DISPLAY
stretch (separate from the model) so faint arcs show even under bright lens light.
No model/checkpoint needed."""
import argparse, h5py, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from train_cnn_m3 import load_theta_pixels

def lens_center(kappa):
    m = np.clip(kappa, 0, None).astype("float64")
    y, x = np.indices(m.shape)
    s = m.sum() + 1e-12
    return (x * m).sum() / s, (y * m).sum() / s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image_file", required=True)
    ap.add_argument("--kappa_file",
                    default="/home/user/ckwan1/ml_project/strong_lensing_dataset/"
                            "kappa_light/test_camera_complete.h5")
    ap.add_argument("--label_file", default="labels_test.h5")
    ap.add_argument("--out", default="show_arcs.png")
    ap.add_argument("--n_panels", type=int, default=16)
    ap.add_argument("--only_bright", action="store_true")
    ap.add_argument("--only_faint", action="store_true")
    ap.add_argument("--disp_a", type=float, default=0.05,
                    help="display asinh softening; SMALLER = more aggressive (arc brighter)")
    ap.add_argument("--disp_clip_pct", type=float, default=99.0,
                    help="saturate above this percentile so the bright lens centre clips")
    ap.add_argument("--pixels", type=int, default=128)
    ap.add_argument("--min_theta_e", type=float, default=0.5)
    ap.add_argument("--max_theta_e", type=float, default=2.5)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    with h5py.File(args.image_file, "r") as f:
        raw = f["lensed"][:].astype("float32")
        kidx = f["kappa_index"][:].astype("int64")
        fov = (f["image_fov"][:].astype("float32") if "image_fov" in f
               else np.full(len(raw), 7.68, dtype="float32"))
    lut = load_theta_pixels(args.label_file)
    true = lut[kidx] * (fov / (args.pixels - 1))
    keep = (true >= args.min_theta_e) & (true <= args.max_theta_e)
    raw, true, fov, kidx = raw[keep], true[keep], fov[keep], kidx[keep]

    p99 = np.percentile(raw.reshape(len(raw), -1), 99, axis=1)
    if args.only_bright:
        sel = np.argsort(p99)[-args.n_panels:][::-1]
    elif args.only_faint:
        sel = np.argsort(p99)[:args.n_panels]
    else:
        sel = rng.choice(len(raw), size=min(args.n_panels, len(raw)), replace=False)

    with h5py.File(args.kappa_file, "r") as f:
        kds = f["kappa"]
        centers = {int(j): lens_center(kds[int(kidx[j])].astype("float32")) for j in sel}

    g = int(np.ceil(np.sqrt(len(sel))))
    fig, axes = plt.subplots(g, g, figsize=(3.0*g, 3.0*g))
    for ax in np.ravel(axes): ax.axis('off')
    for ax, j in zip(np.ravel(axes), sel):
        disp = np.arcsinh(raw[j] / args.disp_a)
        vmax = np.percentile(disp, args.disp_clip_pct)
        ax.imshow(disp, cmap='gray', origin='lower', vmin=disp.min(), vmax=vmax)
        pa = (args.pixels - 1) / fov[j]
        cx, cy = centers[int(j)]
        ax.add_patch(plt.Circle((cx, cy), true[j]*pa, color='lime', fill=False, lw=1.6))
        ax.set_title(f'theta_E {true[j]:.2f}"  FOV{fov[j]:.1f}', fontsize=8); ax.axis('off')
    fig.suptitle(f"true theta_E ring (green) | display asinh a={args.disp_a}, clip {args.disp_clip_pct}%")
    plt.tight_layout(); plt.savefig(args.out, dpi=110); plt.close()
    print(f"[show] wrote {args.out}")

if __name__ == "__main__":
    main()
