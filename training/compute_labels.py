#!/usr/bin/env python
"""
compute_labels.py
=================
Compute Einstein-radius (theta_E) LABELS for the kappa maps, for the CNN project.

theta_E is defined by the mean-convergence condition  kappa_bar(< theta_E) = 1,
implemented by LensFusion's einstein_radius_hard. It depends ONLY on the kappa map
(not on the source or the lensed image). The label for a lensed image with
kappa_index = i is simply theta_E[i].

These labels are the "answer key" used to TRAIN the CNN:
    train the CNN so that   CNN(lensed_image_i)  ->  theta_E[i]
Once trained, the CNN predicts theta_E from a lensed image alone (no kappa needed),
which is what you need for real telescope data where kappa is unknown.

----------------------------------------------------------------------------------
CRITICAL — pixel_scale must MATCH the image generation.
  The kappa-plane pixel scale is   kappa_fov / (pixels - 1).
  With kappa_fov=7.68, pixels=128  ->  7.68/127 ~ 0.0605 arcsec/px.
  This is the SAME FOV question flagged in generate_lensed_images.py. Whatever
  Brian confirms, use the matching value here, or the labels will not correspond
  to the arcs in the images. Override with --pixel_scale if Brian specifies one.
----------------------------------------------------------------------------------

NOTE ON THE FUNCTION:
  einstein_radius_hard below is a VERBATIM copy of
      strong-lensing-sampling/utils/utils.py : einstein_radius_hard
  copied here because importing utils.py directly drags in cores/PIL/imageio/etc.
  The script first TRIES to import the canonical version from the repo; only if
  that fails does it use this copy. If Brian changes the original, re-sync this.
"""

import os
import sys
import argparse

import h5py
import numpy as np
import torch

os.environ.setdefault("MPLBACKEND", "Agg")  # headless, in case import pulls matplotlib


# ----------------------------------------------------------------------------------
# Verbatim copy of utils.utils.einstein_radius_hard (fallback only).
# ----------------------------------------------------------------------------------
def _vendored_einstein_radius_hard(kappa_bhw, pixel_scale, eps=1e-12):
    B, H, W = kappa_bhw.shape
    device, dtype = kappa_bhw.device, kappa_bhw.dtype
    ps = float(pixel_scale)
    K = kappa_bhw.clamp_min(0)

    HALF = 10
    y0 = torch.arange(H, device=device, dtype=dtype)
    x0 = torch.arange(W, device=device, dtype=dtype)
    YY, XX = torch.meshgrid(y0, x0, indexing='ij')

    cy = (H - 1) / 2.0
    cx = (W - 1) / 2.0
    win_mask = (YY >= cy - HALF) & (YY <= cy + HALF) & (XX >= cx - HALF) & (XX <= cx + HALF)
    win_mask = win_mask.unsqueeze(0)

    neg_inf = torch.finfo(dtype).min
    K_win = torch.where(win_mask, K, torch.as_tensor(neg_inf, device=device, dtype=dtype))
    idx_flat = K_win.view(B, -1).argmax(dim=1)
    y_c = (idx_flat // W).to(dtype)
    x_c = (idx_flat % W).to(dtype)

    dx = XX.view(1, H, W) - x_c.view(B, 1, 1)
    dy = YY.view(1, H, W) - y_c.view(B, 1, 1)
    r_arc = torch.sqrt(dx * dx + dy * dy) * ps

    P = H * W
    r_flat = r_arc.view(B, P)
    k_flat = K.view(B, P)

    idx = torch.argsort(r_flat, dim=1)
    r_sorted = r_flat.gather(1, idx)
    k_sorted = k_flat.gather(1, idx)

    k_cum = torch.cumsum(k_sorted, dim=1)
    n = torch.arange(1, P + 1, device=device, dtype=dtype).view(1, P)
    k_bar = k_cum / n

    ge1 = (k_bar >= 1.0)
    j = ge1.sum(dim=1)
    j_hi = torch.clamp(j, max=P - 1)
    j_lo = torch.clamp(j_hi - 1, min=0)

    def g(t, ind):
        return t.gather(1, ind.view(-1, 1)).squeeze(1)

    r0 = g(r_sorted, j_lo); r1 = g(r_sorted, j_hi)
    m0 = g(k_bar, j_lo); m1 = g(k_bar, j_hi)

    denom = (m1 - m0).clamp_min(eps)
    frac = ((1.0 - m0) / denom).clamp(0.0, 1.0)
    r_star = r0 + frac * (r1 - r0)

    never_reach = (j == 0)
    always_above = (j == P)
    r_max = r_sorted[:, -1]
    r_star = torch.where(never_reach, torch.zeros_like(r_star), r_star)
    r_star = torch.where(always_above, r_max, r_star)
    return r_star


def get_einstein_fn(repo_root):
    """Prefer the canonical function from the repo; fall back to the vendored copy."""
    try:
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)
        from utils.utils import einstein_radius_hard  # canonical
        return einstein_radius_hard, "repo (utils.utils)"
    except Exception as e:
        print(f"[warn] could not import canonical einstein_radius_hard ({type(e).__name__}: {e})")
        print("[warn] using the vendored verbatim copy instead.")
        return _vendored_einstein_radius_hard, "vendored copy"


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo_root",
                   default="/home/user/ckwan1/ml_project/strong-lensing-sampling")
    p.add_argument("--kappa_file",
                   default="/home/user/ckwan1/ml_project/strong_lensing_dataset/"
                           "kappa_light/train_camera_complete.h5")
    p.add_argument("--out_file", default="labels_train_singleband.h5")
    p.add_argument("--n", type=int, default=None, help="limit number of kappa maps (default: all)")
    p.add_argument("--batch_size", type=int, default=256)
    p.add_argument("--pixels", type=int, default=128)
    p.add_argument("--kappa_fov", type=float, default=7.68,
                   help="kappa-plane FOV in arcsec; pixel_scale derived from this")
    p.add_argument("--pixel_scale", type=float, default=None,
                   help="override arcsec/pixel directly (else kappa_fov/(pixels-1))")
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return p.parse_args()


def main():
    args = parse_args()
    device = torch.device(args.device)

    pixel_scale = args.pixel_scale if args.pixel_scale is not None \
        else args.kappa_fov / (args.pixels - 1)

    einstein_fn, src = get_einstein_fn(args.repo_root)
    print(f"[labels] using einstein_radius_hard from: {src}")
    print(f"[labels] pixel_scale = {pixel_scale:.6f} arcsec/px "
          f"(kappa_fov={args.kappa_fov}, pixels={args.pixels})")

    fk = h5py.File(args.kappa_file, "r")
    kappa_ds = fk["kappa"]                          # [Nk, H, W]
    Nk = kappa_ds.shape[0]
    N = Nk if args.n is None else min(args.n, Nk)

    theta = np.zeros(N, dtype="float32")
    with torch.no_grad():
        for start in range(0, N, args.batch_size):
            end = min(start + args.batch_size, N)
            kap = torch.from_numpy(kappa_ds[start:end].astype("float32")).to(device)  # [b,H,W]
            theta[start:end] = einstein_fn(kap, pixel_scale).cpu().numpy()
            if (start // args.batch_size) % 10 == 0:
                print(f"  {end}/{N}")
    fk.close()

    # ---- save labels aligned by kappa index ----
    fout = h5py.File(args.out_file, "w")
    fout.create_dataset("theta_E", data=theta)                       # [N] arcsec
    fout.create_dataset("kappa_index", data=np.arange(N, dtype="int64"))
    fout.attrs["pixel_scale"] = pixel_scale
    fout.attrs["kappa_fov"] = args.kappa_fov
    fout.attrs["pixels"] = args.pixels
    fout.attrs["kappa_file"] = args.kappa_file
    fout.attrs["definition"] = "kappa_bar(<theta_E)=1 (einstein_radius_hard)"
    fout.close()

    # ---- sanity report ----
    n_zero = int((theta == 0).sum())
    valid = theta[theta > 0]
    print("\n========== LABEL SANITY REPORT ==========")
    print(f"  total maps         : {N}")
    print(f"  theta_E == 0       : {n_zero}  ({100*n_zero/N:.1f}%)  "
          f"<- weak lens / kappa_bar never reaches 1")
    if valid.size:
        p16, p50, p84 = np.percentile(valid, [16, 50, 84])
        print(f"  valid (>0)         : {valid.size}")
        print(f"  min / max          : {valid.min():.3f} / {valid.max():.3f} arcsec")
        print(f"  mean / median      : {valid.mean():.3f} / {p50:.3f} arcsec")
        print(f"  16-84% interval    : [{p16:.3f}, {p84:.3f}] arcsec")
        frac_data = 100 * np.mean((valid >= 0.5) & (valid <= 2.5))
        frac_obs = 100 * np.mean((valid >= 0.7) & (valid <= 1.7))
        print(f"  in 0.5-2.5 (data)  : {frac_data:.1f}%")
        print(f"  in 0.7-1.7 (obs)   : {frac_obs:.1f}%")
        if p50 < 0.1 or p50 > 5.0:
            print("  *** WARNING: median far outside expected range "
                  "-> pixel_scale is probably wrong. ***")
    print("=========================================")
    print(f"[labels] saved -> {args.out_file}")


if __name__ == "__main__":
    main()
