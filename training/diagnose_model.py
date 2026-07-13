#!/usr/bin/env python
"""Visual diagnostics for an Einstein-radius checkpoint (works for model 2 or 3).
Saves PNGs (headless) + a small preds .npz. Reuses the checkpoint's stored norm
(minmax for m2, asinh for m3), scale stats, and the theta_E[0.5,2.5] selection."""
import argparse, h5py, numpy as np, torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from train_cnn_m3 import EinsteinCNNScale, load_theta_pixels, normalize_images

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image_file", required=True)
    ap.add_argument("--label_file", default="labels_test.h5")
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--out_prefix", default="diag")
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
    print(f"[diag] ckpt norm={norm} asinh_a={asinh_a} scale_mean={s_mean:.5f} std={s_std:.5f}")

    with h5py.File(args.image_file, "r") as f:
        raw = f["lensed"][:].astype("float32")
        kidx = f["kappa_index"][:].astype("int64")
        fov = (f["image_fov"][:].astype("float32") if "image_fov" in f
               else np.full(len(raw), 7.68, dtype="float32"))
    lut = load_theta_pixels(args.label_file)
    theta_pix = lut[kidx]
    pix_scale = fov / (args.pixels - 1)
    true = theta_pix * pix_scale
    keep = (true >= args.min_theta_e) & (true <= args.max_theta_e)
    raw, true, pix_scale, fov, kidx = raw[keep], true[keep], pix_scale[keep], fov[keep], kidx[keep]
    print(f"[diag] kept {keep.sum()}/{len(keep)}")

    imgs = normalize_images(raw, norm, asinh_a)
    scale = ((pix_scale - s_mean) / s_std).astype("float32")
    model = EinsteinCNNScale(channels=tuple(ckpt.get("channels", (32,64,128,256)))).to(device)
    model.load_state_dict(ckpt["state_dict"]); model.eval()
    preds = []
    with torch.no_grad():
        for i in range(0, len(imgs), 256):
            x = torch.from_numpy(imgs[i:i+256]).unsqueeze(1).to(device)
            s = torch.from_numpy(scale[i:i+256]).unsqueeze(1).to(device)
            preds.append(model(x, s).cpu().numpy())
    pred = np.concatenate(preds)

    frac = 100 * (pred - true) / true
    abs_frac = np.abs(frac)
    medfrac = np.median(abs_frac)
    ss_res = np.sum((true - pred)**2); ss_tot = np.sum((true - true.mean())**2)
    r2 = 1 - ss_res/ss_tot
    out_frac = (abs_frac > 15).mean() * 100
    print(f"[diag] median frac {medfrac:.2f}% | R2 {r2:.3f} | >15% outliers {out_frac:.1f}%")

    np.savez(f"{args.out_prefix}_preds.npz", true=true, pred=pred, fov=fov,
             pix_scale=pix_scale, kappa_index=kidx, frac=frac)

    plt.figure(figsize=(6,6))
    plt.scatter(true, pred, s=3, alpha=0.4)
    plt.plot([0.4,2.6],[0.4,2.6],'r--',label='perfect')
    plt.xlabel('true theta_E (")'); plt.ylabel('pred theta_E (")')
    plt.title(f'{args.out_prefix}: pred vs true (med {medfrac:.2f}%, R2 {r2:.3f})')
    plt.axis('equal'); plt.xlim(0.4,2.6); plt.ylim(0.4,2.6)
    plt.grid(alpha=0.3); plt.legend(); plt.tight_layout()
    plt.savefig(f"{args.out_prefix}_scatter.png", dpi=130); plt.close()

    plt.figure(figsize=(7,4))
    plt.scatter(true, frac, s=3, alpha=0.4)
    plt.axhline(0, color='r', ls='--'); plt.ylim(-30,30)
    plt.xlabel('true theta_E (")'); plt.ylabel('frac error (%)')
    plt.title(f'{args.out_prefix}: bias vs theta_E'); plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(f"{args.out_prefix}_residual.png", dpi=130); plt.close()

    plt.figure(figsize=(7,4))
    plt.hist(abs_frac, bins=60, range=(0,50), density=True)
    plt.axvline(15, color='r', ls='--', label='15% bar')
    plt.xlabel('|frac err| (%)'); plt.ylabel('density')
    plt.title(f'{args.out_prefix}: >15% outliers = {out_frac:.1f}%')
    plt.legend(); plt.tight_layout()
    plt.savefig(f"{args.out_prefix}_outliers.png", dpi=130); plt.close()

    idx = rng.choice(len(raw), size=min(9, len(raw)), replace=False)
    fig, axes = plt.subplots(3,3, figsize=(11,11))
    for ax, j in zip(axes.ravel(), idx):
        ax.imshow(raw[j], cmap='gray', origin='lower')
        pa = (args.pixels - 1) / fov[j]
        ax.add_patch(plt.Circle((63.5,63.5), true[j]*pa, color='lime', fill=False, lw=1.5))
        ax.add_patch(plt.Circle((63.5,63.5), pred[j]*pa, color='red',  fill=False, lw=1.2, ls='--'))
        ax.set_title(f'true {true[j]:.2f} / pred {pred[j]:.2f}"  FOV {fov[j]:.1f}"', fontsize=9)
        ax.axis('off')
    fig.suptitle(f'{args.out_prefix}: green=true, red=pred theta_E circle')
    plt.tight_layout(); plt.savefig(f"{args.out_prefix}_circles.png", dpi=110); plt.close()

    p99 = np.percentile(raw.reshape(len(raw), -1), 99, axis=1)
    bright = np.argsort(p99)[-4:][::-1]
    fig, axes = plt.subplots(4,3, figsize=(10,13))
    for r, j in enumerate(bright):
        a_img = np.arcsinh(raw[j] / asinh_a)
        n_img = (a_img - a_img.mean()) / (a_img.std() + 1e-8)
        for c, (im, ttl) in enumerate([(raw[j],'raw'),(a_img,'asinh'),(n_img,'standardized')]):
            axes[r,c].imshow(im, cmap='gray', origin='lower')
            axes[r,c].set_title(f'{ttl} (p99={p99[j]:.2g})' if c==0 else ttl, fontsize=9)
            axes[r,c].axis('off')
    fig.suptitle(f'{args.out_prefix}: input stretch (a={asinh_a})')
    plt.tight_layout(); plt.savefig(f"{args.out_prefix}_norm.png", dpi=110); plt.close()

    print(f"[diag] wrote {args.out_prefix}_(scatter|residual|outliers|circles|norm).png "
          f"and {args.out_prefix}_preds.npz")

if __name__ == "__main__":
    main()
