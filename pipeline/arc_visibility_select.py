#!/usr/bin/env python
"""R1.2b: arc-visibility SELECTION for the Euclid arm.

Computes the v2 arc-SNR metric (peak smoothed arc flux over the azimuthal
residual fluctuation at the arc radius) in the EUCLIDISED domain and writes
the subset of images passing --thresh to a new h5 (all aligned datasets
subset identically; per-image arc_snr stored).

Justification (logged 2026-07-09): matches the training selection function to
the evaluated population — real Euclid/grade-A lens samples are discovery-
selected for visible arcs. This is selection, not flux distortion (v0 lesson).
"""
import argparse
import glob
import os
import numpy as np
import h5py
from scipy.ndimage import gaussian_filter

ap = argparse.ArgumentParser()
ap.add_argument("--arcs", required=True, help="folder of EUCLIDISED noiseless arc npys")
ap.add_argument("--sim", required=True, help="EUCLIDISED composed h5 (same order)")
ap.add_argument("--out", required=True)
ap.add_argument("--thresh", type=float, default=2.5,
                help="keep images with arc SNR > this. 2.5 = EUCLID-domain eye "
                     "calibration (2026-07-09, Nurkyz panels: visible 7.0/8.4, "
                     "invisible <=1.3, borderline ~2); the native 0.7 does NOT "
                     "transfer -- glare raises the eye threshold")
ap.add_argument("--min_extent", type=float, default=300.0,
                help="also require arc footprint (>=0.5 peak) area >= this "
                     "[px on the upsampled grid] -- rejects compact knots that "
                     "pass SNR but do not LOOK like arcs (Nurkyz 2026-07-09)")
ap.add_argument("--min_sky_snr", type=float, default=0.0,
                help="C48: ALSO require the real-comparable arc S/N "
                     "(max arc-only pixel / composite sky-RMS, = real Q1's "
                     "vis_max_lensed_source_signal_to_noise_ratio) to exceed this. "
                     "Real Q1 q25=7.6. The existing --thresh metric (arc peak / "
                     "azimuthal-residual MAD) passes DIFFUSE BLOBS: their peak is "
                     "low but the deflector-subtracted residual is smooth, so the "
                     "ratio passes. Diffuse blobs have LOW peak/sky, so this floor "
                     "drops them and keeps peaked arcs. 0 = off.")
a = ap.parse_args()


def _sky_rms(im, s=14):
    cc = np.concatenate([im[:s, :s].ravel(), im[:s, -s:].ravel(),
                         im[-s:, :s].ravel(), im[-s:, -s:].ravel()])
    return 1.4826 * np.median(np.abs(cc - np.median(cc)))


files = sorted(glob.glob(os.path.join(os.path.expanduser(a.arcs), "image_*.npy")))
with h5py.File(os.path.expanduser(a.sim), "r") as f:
    sim = f["lensed"][:].astype("float64")
    others = {k: (f[k][()] if f[k].shape == () else f[k][:])
              for k in f.keys() if k != "lensed"}
assert len(files) == len(sim), "%d arcs vs %d composed" % (len(files), len(sim))

n = sim.shape[1]
c = n // 2
yy, xx = np.mgrid[0:n, 0:n]
rr = np.hypot(yy - c, xx - c)
rbin = rr.astype(int)

snrs, extents, sky_snrs = [], [], []
for fn, comp in zip(files, sim):
    arc = np.load(fn).astype("float64")
    arc_s = gaussian_filter(arc, 1.5)
    pk = arc_s.max()
    rms = _sky_rms(comp)
    sky_snrs.append(float(np.nanmax(arc) / rms) if rms > 0 else 0.0)
    if pk <= 0:
        snrs.append(0.0)
        extents.append(0)
        continue
    fp = arc_s > 0.5 * pk
    extents.append(int(fp.sum()))
    rest_s = gaussian_filter(comp - arc, 1.5)
    prof = np.zeros(rbin.max() + 1)
    for k in range(rbin.max() + 1):
        m = rbin == k
        if m.any():
            prof[k] = np.median(rest_s[m])
    resid = rest_s - prof[rbin]
    ann = (rr >= rr[fp].min() - 3) & (rr <= rr[fp].max() + 3) & (~fp)
    loc = resid[ann]
    mad = np.median(np.abs(loc - np.median(loc))) * 1.4826
    snrs.append(float(arc_s[fp].max() / mad) if mad > 0 else 0.0)
snrs = np.array(snrs)
extents = np.array(extents)
sky_snrs = np.array(sky_snrs)
keep = (snrs > a.thresh) & (extents >= a.min_extent) & (sky_snrs >= a.min_sky_snr)

with h5py.File(os.path.expanduser(a.out), "w") as fo:
    fo.create_dataset("lensed", data=sim[keep].astype("float32"))
    fo.create_dataset("arc_snr", data=snrs[keep].astype("float32"))
    fo.create_dataset("arc_sky_snr", data=sky_snrs[keep].astype("float32"))
    fo.create_dataset("arc_extent", data=extents[keep].astype("float32"))
    for k, v in others.items():
        v = np.asarray(v)
        fo.create_dataset(k, data=v[keep] if v.shape[:1] == (len(sim),) else v)

th = np.asarray(others.get("theta_E"))
print("selection: %d/%d pass (%.0f%%) at arc SNR > %.2f AND extent >= %.0f px "
      "AND sky-SNR >= %.1f" %
      (keep.sum(), len(sim), 100 * keep.mean(), a.thresh, a.min_extent, a.min_sky_snr))
print("  sky-SNR (real-metric) of all: q25/50/75 = %s ; real Q1 7.6/10.5/15.4"
      % np.round(np.percentile(sky_snrs, [25, 50, 75]), 1))
for t in (1.5, 2.0, 2.5, 3.0, 4.0):
    print("  pass at SNR>%.1f (with extent cut): %.2f  (SNR only: %.2f)"
          % (t, ((snrs > t) & (extents >= a.min_extent)).mean(), (snrs > t).mean()))
print("  extent: median %d px  16-84%% [%d, %d]; extent-cut alone removes %.2f"
      % (np.median(extents), *np.percentile(extents, [16, 84]).astype(int),
         (extents < a.min_extent).mean()))
if th is not None and th.shape[:1] == (len(sim),):
    print("theta_E survivors: range [%.2f, %.2f] median %.2f; "
          "fraction in 0.7-1.7 band: %.2f (pre-selection %.2f)"
          % (th[keep].min(), th[keep].max(), np.median(th[keep]),
             ((th[keep] >= 0.7) & (th[keep] <= 1.7)).mean(),
             ((th >= 0.7) & (th <= 1.7)).mean()))
    for lo, hi in ((0.45, 0.8), (0.8, 1.2), (1.2, 1.7), (1.7, 2.3)):
        m = (th > lo) & (th <= hi)
        if m.sum():
            print("  theta_E %.2f-%.2f: pass %.2f (N=%d)"
                  % (lo, hi, keep[m].mean(), m.sum()))
