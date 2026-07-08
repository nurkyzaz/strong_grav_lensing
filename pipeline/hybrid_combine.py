#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
hybrid_combine.py -- Stage 1.3 (DEFAULT training-set design, ruling
2026-07-05): combine NOISELESS paltas renders with REAL empty COSMOS ACS
F814W cutouts, then top up with Gaussian noise so each image's sky RMS is a
draw from the REAL SLACS per-cutout sky-RMS distribution.

    hybrid = paltas_noiseless (e-/s) + real_empty_cutout (e-/s, median-subtracted)
             + N(0, sigma_topup)  where
    sigma_topup^2 = max(target_rms^2 - cutout_rms^2, 0),
    target_rms ~ empirical distribution of robust_sky(real SLACS cutouts).

Unit compatibility (verified 2026-07-05): both terms are drizzled ACS F814W
electrons/s on the same 0.05"/px grid, zeropoint 25.94 (harvest_empty_cutouts.py
resampled + median-subtracted; paltas output_ab_zeropoint = 25.94).
Approximation, stated: no Poisson noise on the lensed flux itself; acceptable
in the sky-dominated regime (matches MASTER_PLAN 1.3; state in the paper).

Usage:
    python hybrid_combine.py --run ~/paltas_pilot200c_nonoise \
        --empty empty_cutouts.h5 --real ~/einstein_cnn/real_slacs_images.h5 \
        --out ~/einstein_cnn/hybrid200.h5 --seed 4
Also writes <out_dir>/hybrid_preview_source .npy folder? No -- writes an h5
with keys lensed/theta_E/image_fov (same as paltas_npy_to_train.py) plus
per-image provenance (cutout_index, target_rms, topup_sigma).
"""
import argparse
import glob
import os

import h5py
import numpy as np
import pandas as pd

THETA_COL = "main_deflector_parameters_theta_E"


def robust_sky(img, s=16):
    corners = [img[:s, :s], img[:s, -s:], img[-s:, :s], img[-s:, -s:]]
    stds = []
    for c in corners:
        v = c.ravel()
        for _ in range(3):
            m, sd = v.mean(), v.std()
            v = v[np.abs(v - m) < 3 * sd]
            if len(v) < 10:
                break
        stds.append(v.std() if len(v) else np.nan)
    return np.nanmedian(stds)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True, help="paltas NOISELESS run folder")
    p.add_argument("--empty", required=True, help="empty_cutouts.h5")
    p.add_argument("--real", required=True,
                   help="real SLACS h5 (sky-RMS target distribution ONLY)")
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=4)
    p.add_argument("--no-backdrop", action="store_true",
                   help="ablation A2: skip the real empty-cutout backdrop and "
                        "use pure Gaussian noise at the SAME per-image target "
                        "RMS draws (isolates the real-backdrop ingredient)")
    p.add_argument("--companion_stamps", default=None,
                   help="h5 of real COMPANION source stamps (build_source_stamps.py) "
                        "to inject as field neighbours (Nurkyz 2026-07-07: real "
                        "lenses have ~10 companions/img, sims ~0)")
    p.add_argument("--companion_rate_lo", type=float, default=6.0,
                   help="per-image companion count ~ Poisson(U[lo,hi])")
    p.add_argument("--companion_rate_hi", type=float, default=30.0)
    p.add_argument("--companion_flux_pct", type=float, default=50.0,
                   help="keep only stamps brighter than this flux percentile")
    p.add_argument("--companion_rmin", type=int, default=18,
                   help="min radius [px] for a companion (protect lens+arc)")
    p.add_argument("--companion_rmax", type=int, default=62)
    p.add_argument("--deflector_stamps", default=None,
                   help="PATH B: h5 of REAL elliptical deflector-light cutouts "
                        "(build_deflector_stamps.py), pasted centred as the "
                        "foreground lens light; requires the arc-only Path B config")
    p.add_argument("--deflector_mag_csv", default="lens_light_empirical.csv",
                   help="CSV with a 'mag' column of real SLACS deflector total "
                        "magnitudes; each stamp is rescaled to a draw from it")
    p.add_argument("--zeropoint", type=float, default=25.94)
    p.add_argument("--deflector_jitter", type=float, default=2.0,
                   help="centre jitter [px] of pasted deflector vs mass centre")
    args = p.parse_args()

    rng = np.random.default_rng(args.seed)
    run = os.path.expanduser(args.run)

    deflectors = None
    defl_mags = None
    if args.deflector_stamps:
        with h5py.File(os.path.expanduser(args.deflector_stamps), "r") as f:
            deflectors = f["stamps"][:].astype("float32")
        mc = os.path.expanduser(args.deflector_mag_csv)
        if not os.path.isabs(mc):
            mc = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.deflector_mag_csv)
        defl_mags = pd.read_csv(mc)["mag"].values.astype("float32")
        print(f"deflector library: {deflectors.shape}; brightness-matched to "
              f"{len(defl_mags)} real SLACS deflector mags (median {np.median(defl_mags):.2f})")

    companions = None
    comp_p = None
    if args.companion_stamps:
        with h5py.File(os.path.expanduser(args.companion_stamps), "r") as f:
            companions = f["stamps"][:].astype("float32")
        flux = companions.reshape(len(companions), -1).sum(1)
        # keep only the brighter tail (faint COSMOS sources fall below the
        # detection floor once pasted; real detectable companions are bright)
        if args.companion_flux_pct > 0:
            thr = np.percentile(flux, args.companion_flux_pct)
            keep = flux >= thr
            companions = companions[keep]; flux = flux[keep]
        # sample brighter stamps more often (prob proportional to flux)
        comp_p = flux / flux.sum()
        print(f"companion stamps: {companions.shape} (kept flux>=p{args.companion_flux_pct}) "
              f"rate~Poisson(U[{args.companion_rate_lo},{args.companion_rate_hi}]) "
              f"flux-weighted, r in [{args.companion_rmin},{args.companion_rmax}]px")

    files = sorted(glob.glob(os.path.join(run, "image_*.npy")))
    if not files:
        raise SystemExit(f"no image_*.npy in {run}")
    meta = pd.read_csv(os.path.join(run, "metadata.csv"))
    theta = meta[THETA_COL].values
    if len(theta) != len(files):
        raise SystemExit(f"metadata rows {len(theta)} != images {len(files)}")

    with h5py.File(os.path.expanduser(args.empty), "r") as f:
        key = "cutouts" if "cutouts" in f else list(f.keys())[0]
        empty = f[key][:]
    if empty.ndim == 4:
        empty = empty[:, 0]
    print(f"empty cutouts: {empty.shape} from key '{key}'")

    with h5py.File(os.path.expanduser(args.real), "r") as f:
        rk = "images" if "images" in f else "lensed"
        R = f[rk][:]
    if R.ndim == 4:
        R = R[:, 0]
    real_rms = np.array([robust_sky(r) for r in R])
    real_rms = real_rms[np.isfinite(real_rms) & (real_rms > 0)]
    print(f"real sky-RMS targets: N={len(real_rms)} median={np.median(real_rms):.5f} "
          f"16-84%=[{np.percentile(real_rms,16):.5f}, {np.percentile(real_rms,84):.5f}]")

    N = len(files)
    n_px = np.load(files[0]).shape[0]
    out = os.path.expanduser(args.out)
    fo = h5py.File(out, "w")
    d_img = fo.create_dataset("lensed", (N, n_px, n_px), dtype="float32")
    fo.create_dataset("theta_E", data=theta.astype("float64"))
    fo.create_dataset("image_fov", data=np.full(N, 6.4))
    d_cut = fo.create_dataset("cutout_index", (N,), dtype="int64")
    d_tgt = fo.create_dataset("target_rms", (N,), dtype="float32")
    d_top = fo.create_dataset("topup_sigma", (N,), dtype="float32")
    d_ncomp = fo.create_dataset("n_companions", (N,), dtype="int32")
    d_defl = fo.create_dataset("deflector_index", (N,), dtype="int64")
    d_dmag = fo.create_dataset("deflector_mag", (N,), dtype="float32")
    fo.attrs["note"] = ("hybrid: noiseless paltas + real empty COSMOS cutout + "
                        "Gaussian topup to real SLACS sky-RMS draw"
                        + ("; + real companion-source injection" if companions is not None else "")
                        + ("; PATH B real elliptical deflector light" if deflectors is not None else ""))
    fo.attrs["run"] = run
    fo.attrs["seed"] = args.seed

    def inject_companions(img):
        """Paste N real source stamps at random field positions (outside the
        central lens/arc radius). Returns the count actually placed."""
        rate = rng.uniform(args.companion_rate_lo, args.companion_rate_hi)
        n = int(rng.poisson(rate))
        sp = companions.shape[1]; h = sp // 2
        placed = 0
        for _ in range(n):
            r = rng.uniform(args.companion_rmin, args.companion_rmax)
            ang = rng.uniform(0, 2 * np.pi)
            cy = int(round(n_px / 2 + r * np.sin(ang)))
            cx = int(round(n_px / 2 + r * np.cos(ang)))
            y0, x0 = cy - h, cx - h
            if y0 < 0 or x0 < 0 or y0 + sp > n_px or x0 + sp > n_px:
                continue
            st = companions[rng.choice(len(companions), p=comp_p)]
            img[y0:y0 + sp, x0:x0 + sp] += st
            placed += 1
        return placed

    def inject_deflector(sim):
        """PATH B: paste one real elliptical, brightness-matched to a random
        real-SLACS deflector magnitude, centred (with jitter) on the mass
        centre. Returns (stamp_index, target_mag)."""
        di = int(rng.integers(len(deflectors)))
        st = deflectors[di]
        tmag = float(rng.choice(defl_mags))
        f_target = 10.0 ** ((args.zeropoint - tmag) / 2.5)
        cur = st.sum()
        st = st * (f_target / cur) if cur > 0 else st
        sp = st.shape[0]
        jy = int(round(rng.uniform(-args.deflector_jitter, args.deflector_jitter)))
        jx = int(round(rng.uniform(-args.deflector_jitter, args.deflector_jitter)))
        # place the stamp centre at (n_px/2 + jitter); stamp is 128 = full frame
        y0 = (n_px - sp) // 2 + jy
        x0 = (n_px - sp) // 2 + jx
        ys, xs = max(0, y0), max(0, x0)
        ye, xe = min(n_px, y0 + sp), min(n_px, x0 + sp)
        sy, sx = ys - y0, xs - x0
        sim[ys:ye, xs:xe] += st[sy:sy + (ye - ys), sx:sx + (xe - xs)]
        return di, tmag

    skipped_topup = 0
    ncomp_all = []
    for i, fn in enumerate(files):
        sim = np.load(fn).astype("float32")
        target = float(rng.choice(real_rms))
        nc = 0
        di, dmag = -1, 0.0
        if deflectors is not None:
            di, dmag = inject_deflector(sim)
        if args.no_backdrop:
            # A2 variant: same noise AMPLITUDE distribution, no real structure
            ci = -1
            top = target
            img = sim + rng.normal(0.0, top, sim.shape).astype("float32")
        else:
            ci = int(rng.integers(len(empty)))
            cut = empty[ci].astype("float32")
            cut_rms = robust_sky(cut)
            if not np.isfinite(cut_rms):
                cut_rms = 0.0
            top = float(np.sqrt(max(target**2 - cut_rms**2, 0.0)))
            if top == 0.0:
                skipped_topup += 1
            img = sim + cut
            if companions is not None:
                nc = inject_companions(img)
            img = img + rng.normal(0.0, top, sim.shape).astype("float32")
        d_img[i] = img
        d_cut[i] = ci
        d_tgt[i] = target
        d_top[i] = top
        d_ncomp[i] = nc
        d_defl[i] = di
        d_dmag[i] = dmag
        ncomp_all.append(nc)

    fo.close()
    msg = f"wrote {out}: lensed ({N}, {n_px}, {n_px}); topup skipped: {skipped_topup}/{N}"
    if companions is not None:
        msg += f"; injected companions/img median {int(np.median(ncomp_all))} mean {np.mean(ncomp_all):.1f}"
    print(msg)


if __name__ == "__main__":
    main()
