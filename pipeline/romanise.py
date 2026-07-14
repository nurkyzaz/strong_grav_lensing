#!/usr/bin/env python
"""G5c 'romanise' operator (euclidise.py pattern): native GEN4 renders
(128px @ 0.05", HST-calibrated e-/s, ACS PSF) -> Roman Rung-0-like F106
images (final 128px training grid via the same zoom convention as Path A).

Steps per image:
  1. convolve with acs2roman_f106_kernel.npy (PSF match on the 0.05 grid)
  2. flux scale x FLUX_FACTOR (HST e-/s F814W -> Roman DN/s F106; single
     global factor, band-proxy DISCLOSED; pilot gate tunes it vs Rung 0
     peak/sky quantiles 7/32/149)
  3. exact rebin 0.05->0.11: crop 638px-equiv (6.38"), upsample x5
     (order=0, /25) to 0.01, block-sum 11 -> 58px @ 0.11"
  4. + SKY_DN_S, Poisson at T_EFF (1080 s matches the measured Rung 0
     skyRMS 0.0205 at sky 0.454 DN/s; their L2 mosaics are dither-averaged
     so T_eff > single 610 s exposure), sky NOT re-subtracted (Rung 0
     images carry their sky)
  5. bilinear zoom 58 -> 128 px (Path A / G5b grid convention)
Tunables via env: LF_ROM_FLUX (default 1.0), LF_ROM_SKY (0.454),
LF_ROM_TEFF (1080)."""
import argparse
import os

import h5py
import numpy as np
from scipy.ndimage import zoom
from scipy.signal import fftconvolve

KERNEL = np.load(os.path.expanduser("~/cosmos_acs/tiles/acs2roman_f106_kernel.npy"))
FLUX = float(os.environ.get("LF_ROM_FLUX", "1.0"))
SKY = float(os.environ.get("LF_ROM_SKY", "0.454"))
TEFF = float(os.environ.get("LF_ROM_TEFF", "1080"))


def romanise(img, rng, add_noise=True):
    f = fftconvolve(img, KERNEL, mode="same") * FLUX
    n = f.shape[0]
    # exact rational rebin: 0.05*11 = 0.11*5 -> upsample x5 to 0.01, block 11
    m = (n * 5 // 11) * 11 // 5               # ensure divisibility after x5
    f = f[:m, :m]
    up = np.repeat(np.repeat(f, 5, 0), 5, 1) / 25.0          # 0.01" grid
    k = (up.shape[0] // 11) * 11
    up = up[:k, :k]
    rb = up.reshape(k // 11, 11, k // 11, 11).sum(axis=(1, 3))  # 0.11" grid
    dn = rb + SKY
    if add_noise:
        counts = np.clip(dn, 0, None) * TEFF
        dn = rng.poisson(counts).astype("float64") / TEFF
    return zoom(dn, 128.0 / rb.shape[0], order=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--image_key", default=None)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--no_noise", action="store_true")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    CH = 2000
    with h5py.File(a.inp, "r") as fi, h5py.File(a.out, "w") as fo:
        key = a.image_key or ("images" if "images" in fi else "lensed")
        n = fi[key].shape[0]
        dset = fo.create_dataset(key, shape=(n, 128, 128), dtype="float32")
        for k in fi.keys():
            if k != key:
                v = fi[k][()] if fi[k].shape == () else fi[k][:]
                fo.create_dataset(k, data=v)
        for i in range(0, n, CH):
            block = fi[key][i:i + CH]
            if block.ndim == 4:
                block = block[:, 0]
            dset[i:i + CH] = np.stack([
                romanise(im.astype("float64"), rng, add_noise=not a.no_noise)
                for im in block]).astype("float32")
            if (i // CH) % 10 == 0:
                print("  %d/%d" % (i, n), flush=True)
    print("wrote %s: %d images (FLUX %.3g SKY %.3g TEFF %.0f)" % (a.out, n, FLUX, SKY, TEFF))


if __name__ == "__main__":
    main()
