#!/usr/bin/env python
"""G3-2 final step: build the ACS->VIS PSF-matching kernel (the HST2EUCLID
method, photutils.create_matching_kernel + window), validate it, and save it
for the new euclidise operator.

source = mean of the 80 train-shard ACS ePSF kernels (0.05"/px, disclosed
         single-kernel approximation, same as their single TinyTim);
target = Q1 GRID-PSF-VIS mean stamp upsampled to 0.05"/px.
Validation: || source (x) K - target || / ||target||, kernel sum, and the
FWHM stats of the official per-stamp FWHM column (cross-check my estimate).
"""
import glob
import json

import numpy as np
from astropy.io import fits
from photutils.psf.matching import CosineBellWindow, create_matching_kernel
from scipy.ndimage import zoom
from scipy.signal import fftconvolve

# official per-stamp FWHM cross-check
tab = fits.open("/home/user/nurkyz/g3_scratch/grid_psf_vis_102044185.fits",
                memmap=True)[2].data
fw = np.asarray(tab["FWHM"], dtype="float64")
print("official FWHM column: median %.3f px (%.4f arcsec)  16-84%% [%.3f, %.3f] px"
      % (np.median(fw), np.median(fw) * 0.1, *np.percentile(fw, [16, 84])))


def centred(img, size):
    out = np.zeros((size, size))
    c = size // 2
    h = img.shape[0] // 2
    y0 = c - h
    out[y0:y0 + img.shape[0], y0:y0 + img.shape[1]] = img
    return out


SIZE = 67  # common odd grid @ 0.05"/px = 3.35"

# target: VIS PSF at 50 mas
vis = np.load("/home/user/nurkyz/cosmos_acs/tiles/vis_psf_q1.npy")
vis_up = zoom(vis, 2.0, order=3)
vis_up = np.clip(vis_up, 0, None)
if vis_up.shape[0] % 2 == 0:            # zoom of 33 -> 66; recentre to odd
    vis_up = vis_up[:-1, :-1]
    peak = np.unravel_index(vis_up.argmax(), vis_up.shape)
    print("vis_up shape", vis_up.shape, "peak at", peak)
vis_t = centred(vis_up / vis_up.sum(), SIZE)

# source: mean ACS ePSF over the train shards
ks = sorted(glob.glob(
    "/home/user/nurkyz/cosmos_acs/tiles/psf_bank_v2/kernel_*_extended.npy"))
print("ACS kernels found:", len(ks))
acc = None
for fn in ks[:80]:
    k = np.load(fn).astype("float64")
    k /= k.sum()
    kc = centred(k, SIZE) if k.shape[0] <= SIZE else None
    if kc is None:
        h = k.shape[0] // 2
        c0 = h - SIZE // 2
        kc = k[c0:c0 + SIZE, c0:c0 + SIZE]
        kc /= kc.sum()
    acc = kc if acc is None else acc + kc
acs = acc / acc.sum()

# FWHMs on the common grid
for name, p in (("ACS mean", acs), ("VIS Q1", vis_t)):
    a = (p > p.max() / 2).sum()
    print("%s FWHM ~ %.3f arcsec" % (name, 2 * np.sqrt(a / np.pi) * 0.05))

K = create_matching_kernel(acs, vis_t, window=CosineBellWindow(alpha=0.35))
print("kernel sum: %.6f  min: %.3e" % (K.sum(), K.min()))

conv = fftconvolve(acs, K, mode="same")
resid = np.linalg.norm(conv - vis_t) / np.linalg.norm(vis_t)
print("matching residual ||acs*K - vis||/||vis|| = %.4f" % resid)
# wing check at r = 0.2-0.4"
yy, xx = np.mgrid[-(SIZE//2):SIZE//2 + 1, -(SIZE//2):SIZE//2 + 1]
r = np.hypot(xx, yy) * 0.05
for lo, hi in ((0.15, 0.25), (0.25, 0.35), (0.35, 0.5)):
    m = (r >= lo) & (r < hi)
    print("  wings %0.2f-%0.2f\": conv %.3e  target %.3e" %
          (lo, hi, conv[m].mean(), vis_t[m].mean()))

np.save("/home/user/nurkyz/cosmos_acs/tiles/acs2vis_matching_kernel.npy",
        K.astype("float64"))
json.dump(dict(method="photutils create_matching_kernel, CosineBellWindow(0.35)",
               source="mean of 80 train psf_bank_v2 extended ACS ePSFs",
               target="Q1 GRID-PSF-VIS mean (4000 stamps), x2 cubic upsample",
               grid="67px @ 0.05 arcsec", residual=float(resid),
               kernel_sum=float(K.sum())),
          open("/home/user/nurkyz/cosmos_acs/tiles/acs2vis_kernel_provenance.json",
               "w"), indent=2)
print("wrote acs2vis_matching_kernel.npy + provenance")
