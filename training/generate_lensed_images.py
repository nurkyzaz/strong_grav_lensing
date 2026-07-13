#!/usr/bin/env python
"""
generate_lensed_images.py
=========================
Generate mock SINGLE-BAND lensed images (source + lens mass only, NO lens light)
for the Einstein-radius CNN project (Phase 1).

It uses LensFusion's OWN forward operator (forward_operator/physical_model.py ->
PhysicalModel) so the mocks are fully consistent with the diffusion pipeline.
Nothing here is re-implemented physics.

Per-image pipeline:
    source (COSMOS)  +  kappa (IllustrisTNG)
        --A(s, kappa)-->  lensed arcs            (ray tracing)
        --PSF convolution-->  clean image        (Gaussian PSF, FWHM in arcsec)
        + Gaussian noise(sigma_N)  -->  noisy image   <-- CNN INPUT

The Einstein-radius LABEL is NOT computed here. It depends only on the kappa map,
and is produced separately with utils/utils.py:einstein_radius_hard. Each output
image stores its 'kappa_index' so the label can be joined later by index:
    label[i] = einstein_radius_hard(kappa[kappa_index[i]])

----------------------------------------------------------------------------------
FLAG FOR BRIAN (please confirm):
  * FOV / pixel scale. PhysicalModel defaults are
        image_fov = 7.68 arcsec, src_fov = 3.0, kappa_fov = 7.68
    -> image-plane pixel scale = 7.68 / (128-1) ~ 0.0605 arcsec/px.
    The project notes say 0.05 arcsec/px. The pixel scale is NOT a free parameter;
    it follows from the FOV. Are these the FOVs the kappa maps / sources were
    prepared with? If the data assumes a different FOV, change --image_fov etc.
  * redshift. The kappa HDF5 stores redshift=0.1 (snapshot 91), but the lensing
    normalization "pretends" z_lens=0.5. This script does NOT touch redshift; the
    kappa maps are used as-is (already normalized). Confirm that's what you want.
  * amplitude. forward() uses source amplitude = 1.0 (sources already in [0,1]).
    No source_gt_amp / lens_light_gt_amp scaling is applied (that lives at the
    operator level, not in PhysicalModel). Add later if needed.
  * noise. Gaussian, sigma_N = 0.01, added AFTER PSF convolution (matches the mock
    construction y = PSF*A(s,k) + N(0, sigma^2)).
----------------------------------------------------------------------------------
"""

import os
import sys
import argparse

import h5py
import numpy as np
import torch


def load_physical_model_class(repo_root):
    """Import LensFusion's PhysicalModel without triggering package __init__."""
    fwd_dir = os.path.join(repo_root, "forward_operator")
    if fwd_dir not in sys.path:
        sys.path.insert(0, fwd_dir)
    from physical_model import PhysicalModel  # noqa: E402
    return PhysicalModel


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    # paths
    p.add_argument("--repo_root",
                   default="/home/user/ckwan1/ml_project/strong-lensing-sampling")
    p.add_argument("--kappa_file",
                   default="/home/user/ckwan1/ml_project/strong_lensing_dataset/"
                           "kappa_light/train_camera_complete.h5")
    p.add_argument("--source_file",
                   default="/home/user/ckwan1/ml_project/strong_lensing_dataset/"
                           "source/galaxies_testset.h5")
    p.add_argument("--out_file", default="lensed_train_singleband.h5")
    # how much / how fast
    p.add_argument("--n", type=int, default=None,
                   help="number of images to generate (default: all kappa maps)")
    p.add_argument("--batch_size", type=int, default=64)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--device",
                   default="cuda" if torch.cuda.is_available() else "cpu")
    # physics / conventions (see FLAG FOR BRIAN above)
    p.add_argument("--pixels", type=int, default=128)
    p.add_argument("--image_fov", type=float, default=7.68)
    p.add_argument("--src_fov", type=float, default=3.0)
    p.add_argument("--kappa_fov", type=float, default=7.68)
    p.add_argument("--psf_fwhm", type=float, default=0.09,
                   help="PSF FWHM in ARCSEC")
    p.add_argument("--psf_cutout", type=int, default=19,
                   help="PSF kernel size in pixels (paper uses 19x19)")
    p.add_argument("--sigma_n", type=float, default=0.01,
                   help="Gaussian noise rms added after PSF convolution")
    return p.parse_args()


def main():
    args = parse_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = torch.device(args.device)

    PhysicalModel = load_physical_model_class(args.repo_root)

    # ---- build the LensFusion forward operator ----
    model = PhysicalModel(
        pixels=args.pixels,
        src_pixels=args.pixels,
        kappa_pixels=args.pixels,
        image_fov=args.image_fov,
        src_fov=args.src_fov,
        kappa_fov=args.kappa_fov,
        method="fft",
        kappa_interp_mode="deflection",
    ).to(device)
    model.eval()

    # ---- build the PSF once (shared across all images) ----
    # psf_models() computes the Gaussian over arcsec coords -> FWHM is in arcsec.
    psf = model.psf_models(args.psf_fwhm, cutout_size=args.psf_cutout).to(device)

    # ---- open data ----
    fk = h5py.File(args.kappa_file, "r")
    fs = h5py.File(args.source_file, "r")

    kappa_ds = fk["kappa"]        # [Nk, 128, 128] physical kappa
    Nk = kappa_ds.shape[0]
    N = Nk if args.n is None else min(args.n, Nk)

    # sources are small; load all into RAM for fast random access
    src_all = fs["galaxies"][:].astype("float32")   # [Ns, 128, 128] in [0,1]
    Ns = src_all.shape[0]

    has_subid = "subhalo_id" in fk
    has_camera = "camera" in fk

    # each lensed image i uses kappa[i] paired with a RANDOM source
    src_choice = np.random.randint(0, Ns, size=N)

    # ---- output file ----
    fout = h5py.File(args.out_file, "w")
    d_img = fout.create_dataset("lensed", (N, args.pixels, args.pixels), dtype="float32")
    d_kidx = fout.create_dataset("kappa_index", (N,), dtype="int64")
    d_sidx = fout.create_dataset("source_index", (N,), dtype="int64")
    if has_subid:
        d_subid = fout.create_dataset("subhalo_id", (N,), dtype="int64")
    if has_camera:
        d_cam = fout.create_dataset("camera", (N,), dtype=h5py.string_dtype())

    # record exactly how these were generated (helps Brian review)
    for k, v in vars(args).items():
        fout.attrs[k] = v if isinstance(v, (int, float, str)) else str(v)
    fout.attrs["note"] = "source+kappa only, NO lens light; label via einstein_radius_hard(kappa[kappa_index])"

    print(f"[generate] {N} images | device={device} | "
          f"fov(img/src/kap)={args.image_fov}/{args.src_fov}/{args.kappa_fov} "
          f"| psf_fwhm={args.psf_fwhm}\" | sigma_n={args.sigma_n}")

    with torch.no_grad():
        for start in range(0, N, args.batch_size):
            end = min(start + args.batch_size, N)

            # kappa read sequentially (fast); add channel dim -> [b,1,H,W]
            kap = torch.from_numpy(kappa_ds[start:end].astype("float32")).unsqueeze(1).to(device)

            sidx = src_choice[start:end]
            src = torch.from_numpy(src_all[sidx]).unsqueeze(1).to(device)

            clean = model.forward(src, kap, psf)                 # [b,1,H,W] PSF-convolved arcs
            noisy = clean + torch.randn_like(clean) * args.sigma_n

            d_img[start:end] = noisy.squeeze(1).cpu().numpy()
            d_kidx[start:end] = np.arange(start, end)
            d_sidx[start:end] = sidx
            if has_subid:
                d_subid[start:end] = fk["subhalo_id"][start:end]
            if has_camera:
                d_cam[start:end] = fk["camera"][start:end]

            if (start // args.batch_size) % 20 == 0:
                print(f"  {end}/{N}")

    fout.close(); fk.close(); fs.close()
    print(f"[generate] done -> {args.out_file}")


if __name__ == "__main__":
    main()
