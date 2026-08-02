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

PATH B deflector light (2026-07-09, P1 rewrite): a real elliptical stamp is
pasted as the foreground lens light. It is scaled by TOTAL FLUX to a draw from
the real empirical deflector magnitude prior (lens_light_empirical.csv, ZP 25.94),
Re-matched to the stamp's own half-light radius so the (mag, size) pair stays
physical. This REPLACES the earlier peak/sky matching, which -- because library
stamps span ~30x in concentration -- left total deflector flux uncontrolled and
produced 13.5-22.1 mag deflectors (tiny blobs and 2.6-mag-too-bright monsters with
hard edges). With magnitude scaling the peak/sky gate becomes an EMERGENT check.

Usage:
    python hybrid_combine.py --run ~/paltas_pilot200c_nonoise \
        --empty empty_cutouts.h5 --real ~/einstein_cnn/real_slacs_images.h5 \
        --out ~/einstein_cnn/hybrid200.h5 --seed 4
Also writes an h5 with keys lensed/theta_E/image_fov (same as paltas_npy_to_train.py)
plus per-image provenance (cutout_index, target_rms, topup_sigma, deflector_index,
deflector_mag = the actual magnitude drawn).
"""
import argparse
import glob
import os

import h5py
import numpy as np
import pandas as pd

THETA_COL = "main_deflector_parameters_theta_E"
PIXSCALE = 0.05  # arcsec/px (both 128px and 256px LRG stamps: 6.4/128 = 12.8/256)


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


def central_peak_over_sky(img, box=10):
    """Central peak / sky-RMS, matching the gate's 'lens peak/sky' definition.
    Kept as a DIAGNOSTIC only now (P1): the deflector is no longer scaled to it,
    so the gate's peak/sky agreement is an emergent validation, not a tautology."""
    n = img.shape[0]
    c = n // 2
    sky = robust_sky(img)
    if not np.isfinite(sky) or sky <= 0:
        return np.nan
    peak = img[c - box:c + box, c - box:c + box].max()
    lvl = np.median(np.concatenate([img[:16, :16].ravel(), img[-16:, -16:].ravel()]))
    return (peak - lvl) / sky


def half_light_radius_px(st):
    """Circular half-light radius [px] of a background-subtracted stamp."""
    n = st.shape[0]
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c).ravel()
    f = np.clip(st.ravel(), 0, None)
    order = np.argsort(r)
    cum = np.cumsum(f[order])
    if cum[-1] <= 0:
        return np.nan
    k = int(np.searchsorted(cum, 0.5 * cum[-1]))
    k = min(k, len(order) - 1)
    return float(r[order][k])


def aperture_flux(st, r_px):
    """Positive flux of a stamp within a central circular aperture of r_px.
    The aperture (r=2" = 40 px) sits well inside even the 128-px stamps, so
    this is robust to frame truncation AND to the wing-stripping of the 128-px
    corner-bg libraries — unlike the stamp TOTAL, which depends on both."""
    n = st.shape[0]
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    mask = np.hypot(yy - c, xx - c) <= r_px
    return float(np.clip(st, 0, None)[mask].sum())


def quantile_ranks(x):
    """Fractional ranks in (0,1] robust to NaN (NaN -> median before ranking).
    Used for RANK-based Re-matching: the measured stamp half-light radius is
    systematically ~2x smaller than the Bolton effective radius (outskirt
    smoothing + bg subtraction strip the de Vaucouleurs wings), so absolute
    arcsec matching would bias the drawn magnitudes faint. Ranks are
    scale-invariant -> the drawn-magnitude MARGINAL stays equal to the prior
    while big-for-its-population stamps still lean brighter."""
    x = np.asarray(x, dtype="float64").copy()
    if np.isnan(x).any():
        x[np.isnan(x)] = np.nanmedian(x)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x))
    ranks[order] = (np.arange(len(x)) + 0.5) / len(x)
    return ranks


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run", required=True, help="paltas NOISELESS run folder")
    p.add_argument("--empty", required=True, help="empty_cutouts.h5")
    p.add_argument("--real", required=True,
                   help="real h5 supplying the sky-RMS target distribution ONLY "
                        "(use the benchmark-disjoint DA pool once P4 lands)")
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=4)
    p.add_argument("--arc_poisson", action="store_true",
                   help="AR1: Poisson shot noise on the noiseless arc render "
                        "(exposure --arc_exptime); default OFF until pilot-gated")
    p.add_argument("--arc_exptime", type=float, default=675.0,
                   help="calibrated e-/s exposure for --arc_poisson")
    p.add_argument("--arc_flux_scale", type=float, default=1.0,
                   help="GEN5 C36: multiply the noiseless lensed-source (arc) by "
                        "this factor BEFORE Poisson+combine = physically brightening "
                        "the source (arc surface brightness scales linearly with "
                        "source flux). 1.0 = unchanged. Used to test/calibrate the "
                        "source luminosity-function evolution the dimming omits.")
    p.add_argument("--deflector_flux_scale", type=float, default=1.0,
                   help="C39: multiply the deflector stamp flux to raise its "
                        "brightness/peak WITHOUT sharpening (unsharp compactifies "
                        "the large-diffuse deflectors real Q1 has). 1.0=off; keeps "
                        "the diffuse extent + the sigma_v->theta_E FJ channel.")
    p.add_argument("--deflector_sharpen", type=float, default=0.0,
                   help="GEN5 C37: unsharp-mask strength on the deflector stamp to "
                        "raise the central peak/concentration (real HST stamps carry "
                        "the HST PSF; euclidise adds the Euclid PSF -> soft core vs "
                        "real Q1 single-PSF). 0=off; ~1 typical. Roughly flux-"
                        "preserving (high-pass has ~zero sum). Calibrate to real "
                        "deflector peak/sky ~172.")
    p.add_argument("--deflector_sharpen_sigma", type=float, default=1.5,
                   help="unsharp gaussian sigma [px] for --deflector_sharpen")
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
    p.add_argument("--companion_area_uniform", action="store_true",
                   help="C38: place companions uniform per unit AREA (real field "
                        "statistics; default OFF keeps the legacy uniform-in-r "
                        "draw so GEN4 reproduces exactly)")
    p.add_argument("--companion_rmin", type=int, default=18,
                   help="min radius [px] for a companion (protect lens+arc)")
    p.add_argument("--companion_rmax", type=int, default=62)
    p.add_argument("--deflector_stamps", default=None,
                   help="PATH B: h5 of REAL elliptical deflector-light cutouts "
                        "(build_deflector_from_lrg.py), pasted centred as the "
                        "foreground lens light; requires the arc-only Path B config")
    p.add_argument("--deflector_manifest", default=None,
                   help="GEN4-G2 assignment csv (file_row,stamp_id,dihedral_k): "
                        "paste EXACTLY that stamp/orientation at NATIVE amplitude")
    p.add_argument("--deflector_mag_csv", default="lens_light_empirical.csv",
                   help="CSV with 'mag'/'mag_aper'/'re' columns of real SLACS "
                        "deflectors; each stamp's flux within the measurement "
                        "aperture is scaled to an Re-matched mag_aper draw")
    p.add_argument("--deflector_aper_arcsec", type=float, default=2.0,
                   help="radius [arcsec] of the aperture mag_aper was measured "
                        "in (build_lens_light_prior.py used r=2\"); scaling "
                        "matches IN-APERTURE flux, so the out-of-frame de Vauc "
                        "wing flux is NOT stuffed into the frame (P1b fix)")
    p.add_argument("--deflector_mag_jitter", type=float, default=0.2,
                   help="uniform +/- jitter [mag] added to each magnitude draw")
    p.add_argument("--deflector_re_sigma", type=float, default=0.4,
                   help="Gaussian kernel width [arcsec] for Re-matching mag rows to stamps")
    p.add_argument("--deflector_augment", action="store_true",
                   help="P3: random dihedral (rot90 x k + optional flip) per paste")
    p.add_argument("--zeropoint", type=float, default=25.94)
    p.add_argument("--deflector_jitter", type=float, default=2.0,
                   help="centre jitter [px] of pasted deflector vs mass centre")
    args = p.parse_args()

    rng = np.random.default_rng(args.seed)
    run = os.path.expanduser(args.run)

    deflectors = None
    defl_mags = None
    defl_re = None
    stamp_re = None
    stamp_re_rank = None
    csv_re_rank = None
    if args.deflector_stamps:
        with h5py.File(os.path.expanduser(args.deflector_stamps), "r") as f:
            deflectors = f["stamps"][:].astype("float32")
        mc = os.path.expanduser(args.deflector_mag_csv)
        if not os.path.isabs(mc):
            mc = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.deflector_mag_csv)
        csv = pd.read_csv(mc)
        defl_mags = csv["mag"].values.astype("float32")
        if "mag_aper" not in csv:
            raise SystemExit("deflector_mag_csv needs a 'mag_aper' column "
                             "(aperture-based scaling, P1b)")
        defl_mags_aper = csv["mag_aper"].values.astype("float32")
        defl_re = csv["re"].values.astype("float32") if "re" in csv else None
        stamp_re = np.array([half_light_radius_px(s) * PIXSCALE for s in deflectors],
                            dtype="float32")
        aper_r_px = args.deflector_aper_arcsec / PIXSCALE
        stamp_aper_flux = np.array([aperture_flux(s, aper_r_px) for s in deflectors],
                                   dtype="float32")
        print(f"deflector library: {deflectors.shape}; APERTURE-flux "
              f"(r={args.deflector_aper_arcsec} arcsec) scaled to the real "
              f"empirical mag_aper prior (ZP {args.zeropoint}) -- in-frame flux "
              f"matches real cutouts instead of stuffing the full TOTAL into "
              f"the frame")
        print(f"  stamp Re [arcsec]: median {np.nanmedian(stamp_re):.2f} "
              f"16-84%=[{np.nanpercentile(stamp_re,16):.2f}, {np.nanpercentile(stamp_re,84):.2f}]")
        print(f"  prior mag (TOTAL): median {np.median(defl_mags):.2f} "
              f"16-84%=[{np.percentile(defl_mags,16):.2f}, {np.percentile(defl_mags,84):.2f}]")
        print(f"  prior mag_aper (scaling target): median {np.median(defl_mags_aper):.2f} "
              f"16-84%=[{np.percentile(defl_mags_aper,16):.2f}, {np.percentile(defl_mags_aper,84):.2f}]")
        if defl_re is not None:
            stamp_re_rank = quantile_ranks(stamp_re)
            csv_re_rank = quantile_ranks(defl_re)
            print(f"  prior Re [arcsec]: median {np.median(defl_re):.2f} "
                  f"16-84%=[{np.percentile(defl_re,16):.2f}, {np.percentile(defl_re,84):.2f}] "
                  f"-> RANK-matched draws (marginal preserved; scale offset noted)")
        else:
            print("  no 're' column in CSV -> magnitude drawn without Re-matching")

    companions = None
    comp_p = None
    if args.companion_stamps:
        with h5py.File(os.path.expanduser(args.companion_stamps), "r") as f:
            companions = f["stamps"][:].astype("float32")
        flux = companions.reshape(len(companions), -1).sum(1)
        if args.companion_flux_pct > 0:
            thr = np.percentile(flux, args.companion_flux_pct)
            keep = flux >= thr
            companions = companions[keep]; flux = flux[keep]
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
    # DIAGNOSTIC ONLY (P1): real deflector peak/sky -- no longer used for scaling.
    real_peaksky = np.array([central_peak_over_sky(r) for r in R])
    real_peaksky = real_peaksky[np.isfinite(real_peaksky) & (real_peaksky > 0)]
    print(f"real deflector peak/sky (diagnostic): N={len(real_peaksky)} "
          f"median={np.median(real_peaksky):.0f} "
          f"16-84%=[{np.percentile(real_peaksky,16):.0f}, {np.percentile(real_peaksky,84):.0f}]")

    N = len(files)
    n_px = np.load(files[0]).shape[0]
    out = os.path.expanduser(args.out)
    fo = h5py.File(out, "w")
    d_img = fo.create_dataset("lensed", (N, n_px, n_px), dtype="float32")
    fo.create_dataset("theta_E", data=theta.astype("float64"))
    # aux-head labels (2026-07-10, plan 2b): mass ellipticity from paltas
    # metadata (same row order as theta_E). Labels only -- images unchanged.
    for _c in ("e1", "e2"):
        _col = "main_deflector_parameters_" + _c
        if _col in meta.columns:
            fo.create_dataset("mass_" + _c, data=meta[_col].values.astype("float64"))
        else:
            print("WARNING: %s not in metadata -- mass_%s label skipped" % (_col, _c))
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
                        + ("; PATH B real elliptical deflector light (magnitude-scaled)"
                           if deflectors is not None else ""))
    fo.attrs["run"] = run
    fo.attrs["seed"] = args.seed

    def inject_companions(img, dim=1.0):
        """dim: GEN5 z-migration SB factor (Nurkyz fix 2026-07-22) — the
        companion field must dim with the migrated scene, else native-
        brightness COSMOS companions outshine the dimmed central deflector."""
        rate = rng.uniform(args.companion_rate_lo, args.companion_rate_hi)
        n = int(rng.poisson(rate))
        sp = companions.shape[1]; h = sp // 2
        placed = 0
        for _ in range(n):
            if args.companion_area_uniform:
                # C38 (Nurkyz eyeball 2026-08-02): uniform per unit AREA like real
                # field galaxies (uniform-in-r piles density ~1/r onto the arc)
                r = np.sqrt(rng.uniform(args.companion_rmin ** 2,
                                        args.companion_rmax ** 2))
            else:
                r = rng.uniform(args.companion_rmin, args.companion_rmax)
            ang = rng.uniform(0, 2 * np.pi)
            cy = int(round(n_px / 2 + r * np.sin(ang)))
            cx = int(round(n_px / 2 + r * np.cos(ang)))
            y0, x0 = cy - h, cx - h
            if y0 < 0 or x0 < 0 or y0 + sp > n_px or x0 + sp > n_px:
                continue
            st = companions[rng.choice(len(companions), p=comp_p)]
            img[y0:y0 + sp, x0:x0 + sp] += st * dim
            placed += 1
        return placed

    g2_assign = None
    if args.deflector_manifest:
        import csv as _csv
        g2_assign = {}
        n_mig = 0
        for r in _csv.DictReader(open(args.deflector_manifest)):
            # C21 z-migration: optional per-row (angular shrink, SB dim)
            sc = float(r.get("mig_scale", 1.0) or 1.0)
            sb = float(r.get("mig_sb", 1.0) or 1.0)
            if sc != 1.0 or sb != 1.0:
                n_mig += 1
            g2_assign[int(r["file_row"])] = (int(r["stamp_id"]),
                                             int(r["dihedral_k"]), sc, sb)
        print("G2 manifest mode: %d assignments, native amplitude, no mag draw"
              % len(g2_assign)
              + ("; C21 z-migration on %d rows (zoom by D_A ratio, "
                 "(1+z)^4 SB dimming)" % n_mig if n_mig else ""))

    def inject_deflector_g2(sim, i):
        """GEN4-G2: the assigned real galaxy at its own brightness
        (C21: optionally z-migrated — shrunk and Tolman-dimmed)."""
        di, k, mig_scale, mig_sb = g2_assign[i]
        st = deflectors[di]
        st = np.rot90(st, k % 4)
        if k >= 4:
            st = np.fliplr(st)
        st = np.ascontiguousarray(st).copy()
        if mig_scale != 1.0 or mig_sb != 1.0:
            from scipy.ndimage import zoom as _ndi_zoom
            st = _ndi_zoom(st, mig_scale, order=1) * mig_sb
        if args.deflector_flux_scale != 1.0:  # C39: brighten WITHOUT compactifying
            st = st * args.deflector_flux_scale  # (preserves diffuse extent + FJ)
        if args.deflector_sharpen > 0:  # C37: raise the central peak (double-PSF fix)
            from scipy.ndimage import gaussian_filter as _gf
            st = np.clip(st + args.deflector_sharpen
                         * (st - _gf(st, args.deflector_sharpen_sigma)), 0, None)
        sp = st.shape[0]
        jy = int(round(rng.uniform(-args.deflector_jitter, args.deflector_jitter)))
        jx = int(round(rng.uniform(-args.deflector_jitter, args.deflector_jitter)))
        if sp >= n_px:
            c0 = (sp - n_px) // 2
            # clamp: a z-migrated stamp can land at exactly n_px, where the
            # jitter would push the crop window out of bounds
            y0 = min(max(c0 + jy, 0), sp - n_px)
            x0 = min(max(c0 + jx, 0), sp - n_px)
            sim += st[y0:y0 + n_px, x0:x0 + n_px]
        else:
            y0 = (n_px - sp) // 2 + jy
            x0 = (n_px - sp) // 2 + jx
            ys, xs = max(y0, 0), max(x0, 0)
            ye, xe = min(y0 + sp, n_px), min(x0 + sp, n_px)
            sim[ys:ye, xs:xe] += st[ys - y0:ye - y0, xs - x0:xe - x0]
        mag_native = args.zeropoint - 2.5 * np.log10(max(float(np.clip(st, 0, None).sum()), 1e-9))
        return di, mag_native

    def inject_deflector(sim):
        """PATH B (P1b): paste one real elliptical scaled so its flux WITHIN the
        r=2" measurement aperture equals an Re-matched mag_aper draw from the
        empirical prior. Total-flux scaling (P1) put the galaxy's ENTIRE flux
        inside the 6.4" frame while real cutouts only hold ~54% of it (rest is
        de Vauc wing beyond the frame) -> sim deflectors were 1.85x over-bright
        in-frame (measured, pilot v4), burying arcs. Centred with jitter; if the
        stamp is larger than the frame, the CENTRE crop is pasted (jitter shifts
        the crop window) so no opacity edge can exist.
        Returns (stamp_index, total_magnitude_drawn)."""
        di = int(rng.integers(len(deflectors)))
        st = deflectors[di]
        ap = float(stamp_aper_flux[di])
        if ap <= 0:
            return di, 0.0
        # RANK-matched joint (mag, Re) draw: correlates size<->brightness while
        # keeping the drawn-magnitude marginal equal to the prior (robust to the
        # stamp-vs-Bolton Re scale offset). sigma in rank space (0..1).
        if csv_re_rank is not None:
            w = np.exp(-0.5 * ((csv_re_rank - stamp_re_rank[di]) / 0.3) ** 2)
            sw = w.sum()
            j = int(rng.choice(len(defl_mags), p=(w / sw))) if sw > 0 else int(rng.integers(len(defl_mags)))
        else:
            j = int(rng.integers(len(defl_mags)))
        jit = float(rng.uniform(-args.deflector_mag_jitter,
                                args.deflector_mag_jitter))
        mag_draw = float(defl_mags[j]) + jit          # TOTAL mag (provenance)
        mag_ap_draw = float(defl_mags_aper[j]) + jit  # same row+jitter, aperture mag
        flux_target = 10.0 ** (-0.4 * (mag_ap_draw - args.zeropoint))
        st = st * (flux_target / ap)
        if args.deflector_augment:
            st = np.rot90(st, int(rng.integers(4)))
            if rng.random() < 0.5:
                st = np.fliplr(st)
            st = np.ascontiguousarray(st)
        sp = st.shape[0]
        jy = int(round(rng.uniform(-args.deflector_jitter, args.deflector_jitter)))
        jx = int(round(rng.uniform(-args.deflector_jitter, args.deflector_jitter)))
        if sp >= n_px:
            # stamp bigger than frame: paste the CENTRE n_px crop (jitter shifts window)
            c0 = (sp - n_px) // 2
            oy, ox = c0 + jy, c0 + jx
            oy = min(max(oy, 0), sp - n_px)
            ox = min(max(ox, 0), sp - n_px)
            sim += st[oy:oy + n_px, ox:ox + n_px]
        else:
            y0 = (n_px - sp) // 2 + jy
            x0 = (n_px - sp) // 2 + jx
            ys, xs = max(0, y0), max(0, x0)
            ye, xe = min(n_px, y0 + sp), min(n_px, x0 + sp)
            sy, sx = ys - y0, xs - x0
            sim[ys:ye, xs:xe] += st[sy:sy + (ye - ys), sx:sx + (xe - xs)]
        return di, mag_draw

    skipped_topup = 0
    ncomp_all = []
    dmag_all = []
    for i, fn in enumerate(files):
        sim = np.load(fn).astype("float32")
        if args.arc_flux_scale != 1.0:
            sim = sim * args.arc_flux_scale  # C36: brighten the lensed source
        if args.arc_poisson:
            # AR1: arc-only shot noise (deflector stamp + backdrop carry their
            # own real noise; render here is the noiseless lensed source)
            counts = np.clip(sim, 0, None) * args.arc_exptime
            sim = (rng.poisson(counts).astype("float32") / args.arc_exptime
                   + np.minimum(sim, 0.0))
        target = float(rng.choice(real_rms))
        nc = 0
        di, dmag = -1, 0.0
        if deflectors is not None:
            if g2_assign is not None:
                di, dmag = inject_deflector_g2(sim, i)
            else:
                di, dmag = inject_deflector(sim)
            dmag_all.append(dmag)
        if args.no_backdrop:
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
                comp_dim = (g2_assign[i][3]
                            if (g2_assign is not None and i in g2_assign)
                            else 1.0)
                nc = inject_companions(img, dim=comp_dim)
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
    if deflectors is not None and dmag_all:
        used = np.array(dmag_all)
        used = used[used > 0]
        if len(used):
            msg += (f"; deflector mag used median {np.median(used):.2f} "
                    f"16-84%=[{np.percentile(used,16):.2f}, {np.percentile(used,84):.2f}]")
    if companions is not None:
        msg += f"; injected companions/img median {int(np.median(ncomp_all))} mean {np.mean(ncomp_all):.1f}"
    print(msg)


if __name__ == "__main__":
    main()
