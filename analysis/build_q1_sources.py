#!/usr/bin/env python
"""GEN5 C37 — clean the PyAutoLens delensed Q1 source-plane reconstructions into a
usable source-stamp library.

Per lens dir (~/cosmos_acs/q1_slde/lens/lens/<id>/result/):
  source_reconstruction.fits (201x201, source-plane) + _noise_map.fits
Cleaning:
  1. SNR = src / noise ; mask = SNR > SNR_MIN
  2. dilate the mask (connect nearby star-forming knots), label, KEEP only the
     component containing the flux peak -> removes the disconnected triangulation
     / regularization artifacts PyAutoLens sprays across the source plane
  3. crop to a fixed STAMP px window centred on the flux centroid (native source-
     plane pixel scale preserved for later re-lensing)
Screen out: no real source (low peak SNR), too diffuse (fills the frame = bad
model), or too tiny.
Outputs: q1_sources_clean.h5 (sources/names/flux/re_px/peaksnr) + before/after
montage + a cleaned montage.
"""
import glob
import os

import numpy as np
from astropy.io import fits
from scipy.ndimage import binary_dilation, center_of_mass, label
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = "/home/user/nurkyz/cosmos_acs/q1_slde/lens/lens"
OUTDIR = "/home/user/nurkyz/cosmos_acs/q1_slde"
STAMP = 121          # output stamp size (native source-plane px)
SNR_MIN = 2.5        # per-pixel significance for the source mask
PEAK_SNR_MIN = 6.0   # a real source must have a confident peak
MAX_FILL = 0.35      # kept-source area / frame -> reject bad/diffuse models
MIN_AREA = 12        # px


def load(p):
    try:
        d = fits.getdata(p)
        return np.asarray(d, float) if d is not None else None
    except Exception:
        return None


def clean_one(src, noise):
    noise = np.where((noise > 0) & np.isfinite(noise), noise, np.inf)
    src = np.nan_to_num(src)
    snr = src / noise
    peaksnr = float(np.nanmax(snr))
    if peaksnr < PEAK_SNR_MIN:
        return None, "low_peak_snr", peaksnr
    mask = snr > SNR_MIN
    if mask.sum() < MIN_AREA:
        return None, "too_small", peaksnr
    # dilate to bridge multi-knot sources, then keep the peak's component
    dil = binary_dilation(mask, iterations=2)
    lab, n = label(dil)
    py, px = np.unravel_index(np.argmax(snr), snr.shape)
    comp = lab[py, px]
    keep = (lab == comp) & mask
    area = int(keep.sum())
    if area < MIN_AREA:
        return None, "too_small", peaksnr
    if area / src.size > MAX_FILL:
        return None, "too_diffuse", peaksnr
    cleaned = src * keep
    # crop STAMP window centred on the flux centroid
    cy, cx = center_of_mass(cleaned)
    cy, cx = int(round(cy)), int(round(cx))
    h = STAMP // 2
    out = np.zeros((STAMP, STAMP), np.float32)
    y0, y1 = cy - h, cy + h + 1
    x0, x1 = cx - h, cx + h + 1
    sy0, sx0 = max(0, -y0), max(0, -x0)
    yy0, xx0 = max(0, y0), max(0, x0)
    yy1, xx1 = min(src.shape[0], y1), min(src.shape[1], x1)
    out[sy0:sy0 + (yy1 - yy0), sx0:sx0 + (xx1 - xx0)] = cleaned[yy0:yy1, xx0:xx1]
    return out, "ok", peaksnr


def half_light_px(im):
    f = np.clip(im, 0, None)
    tot = f.sum()
    if tot <= 0:
        return np.nan
    n = im.shape[0]
    yy, xx = np.mgrid[0:n, 0:n]
    cy, cx = center_of_mass(f)
    rr = np.hypot(yy - cy, xx - cx)
    order = np.argsort(rr.ravel())
    cum = np.cumsum(f.ravel()[order])
    return float(rr.ravel()[order][np.searchsorted(cum, 0.5 * tot)])


def asinh(im):
    im = np.nan_to_num(im)
    p = np.percentile(im, 99.7)
    a = np.arcsinh(np.clip(im, 0, None) / max(p / 20, 1e-9))
    return a / max(a.max(), 1e-9)


dirs = sorted(glob.glob(os.path.join(ROOT, "*/result")))
kept, names, flux, re_px, snrs = [], [], [], [], []
raw_keep, reasons = [], {}
for d in dirs:
    src = load(os.path.join(d, "source_reconstruction.fits"))
    noise = load(os.path.join(d, "source_reconstruction_noise_map.fits"))
    if src is None or noise is None or np.nansum(np.abs(src)) == 0:
        reasons["empty"] = reasons.get("empty", 0) + 1
        continue
    out, why, ps = clean_one(src, noise)
    reasons[why] = reasons.get(why, 0) + 1
    if out is None:
        continue
    kept.append(out)
    names.append(os.path.basename(os.path.dirname(d)))
    flux.append(float(out.sum()))
    re_px.append(half_light_px(out))
    snrs.append(ps)
    raw_keep.append(src)

kept = np.array(kept, np.float32)
print("input dirs: %d | KEPT: %d" % (len(dirs), len(kept)))
print("reasons:", reasons)
print("half-light Re [native px] q25/50/75 = %s"
      % np.round(np.nanpercentile(re_px, [25, 50, 75]), 1))
print("peak SNR q25/50/75 = %s" % np.round(np.percentile(snrs, [25, 50, 75]), 1))

with h5py.File(os.path.join(OUTDIR, "q1_sources_clean.h5"), "w") as f:
    f["sources"] = kept
    f["names"] = np.array(names, dtype="S64")
    f["flux"] = np.array(flux, np.float32)
    f["re_px"] = np.array(re_px, np.float32)
    f["peak_snr"] = np.array(snrs, np.float32)
    f.attrs["stamp_px"] = STAMP
    f.attrs["note"] = "PyAutoLens delensed Q1 source-plane reconstructions, cleaned"
print("wrote", os.path.join(OUTDIR, "q1_sources_clean.h5"))

# before/after montage (8 lenses)
fig, ax = plt.subplots(4, 4, figsize=(12, 12))
for k in range(8):
    r = raw_keep[k]
    ax[k // 4 * 2][k % 4].imshow(asinh(r), cmap="magma", origin="lower")
    ax[k // 4 * 2][k % 4].set_title("RAW %s" % names[k][:18], fontsize=7)
    ax[k // 4 * 2][k % 4].axis("off")
    ax[k // 4 * 2 + 1][k % 4].imshow(asinh(kept[k]), cmap="magma", origin="lower")
    ax[k // 4 * 2 + 1][k % 4].set_title("CLEAN Re=%.0fpx" % re_px[k], fontsize=7)
    ax[k // 4 * 2 + 1][k % 4].axis("off")
fig.suptitle("Q1 delensed sources: RAW (rows 1,3) vs CLEANED (rows 2,4)", fontsize=12)
fig.tight_layout()
fig.savefig(os.path.join(OUTDIR, "q1_sources_beforeafter.png"), dpi=90)

# cleaned-only montage (16)
fig2, ax2 = plt.subplots(4, 4, figsize=(12, 12))
for k, a in enumerate(ax2.ravel()):
    if k < len(kept):
        a.imshow(asinh(kept[k]), cmap="magma", origin="lower")
        a.set_title("%s Re=%.0f" % (names[k][:16], re_px[k]), fontsize=7)
    a.axis("off")
fig2.suptitle("Q1 CLEANED source library (%d sources)" % len(kept), fontsize=12)
fig2.tight_layout()
fig2.savefig(os.path.join(OUTDIR, "q1_sources_clean_montage.png"), dpi=90)
print("wrote montages")
