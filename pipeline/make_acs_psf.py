#!/usr/bin/env python
"""
make_acs_psf.py
===============
Build a realistic HST ACS/WFC F814W PSF to convolve the arcs with (replacing the
clean Gaussian FWHM=0.09" used in the sim-only generator).

Two modes:
  --mode empirical  : extract bright isolated stars from a COSMOS tile and build an
                      effective PSF (photutils EPSFBuilder). Most realistic.
  --mode moffat     : parametric Moffat (broader wings than a Gaussian). Use this to
                      unblock if photutils misbehaves; refine to empirical later.

Output: a normalized [size,size] float32 kernel saved as .npy, on the 0.05"/px grid.
ALWAYS open the saved .npy and eyeball it before trusting it.
"""
import argparse
import numpy as np


def moffat(size, fwhm_pix, beta=3.0):
    alpha = fwhm_pix / (2 * np.sqrt(2 ** (1 / beta) - 1))
    c = size // 2
    y, x = np.mgrid[:size, :size]
    k = (1 + ((x - c) ** 2 + (y - c) ** 2) / alpha ** 2) ** (-beta)
    return (k / k.sum()).astype(np.float32)


def empirical(mosaic, size):
    from astropy.io import fits
    from astropy.stats import sigma_clipped_stats
    from astropy.table import Table
    from astropy.nddata import NDData
    from photutils.detection import DAOStarFinder
    from photutils.psf import extract_stars, EPSFBuilder

    with fits.open(mosaic, memmap=True) as h:
        data = next(x.data for x in h if x.data is not None and x.data.ndim == 2).astype(np.float32)
    data = np.nan_to_num(data)
    _, med, std = sigma_clipped_stats(data, sigma=3.0)
    finder = DAOStarFinder(fwhm=3.0, threshold=20 * std)
    src = finder(data - med)
    if src is None or len(src) < 10:
        raise RuntimeError("too few star candidates; use --mode moffat")
    src = src[src["flux"] > np.percentile(src["flux"], 90)]  # bright, likely stars
    tbl = Table()
    tbl["x"] = src["xcentroid"]; tbl["y"] = src["ycentroid"]
    stars = extract_stars(NDData(data - med), tbl, size=size)
    epsf, _ = EPSFBuilder(oversampling=1, maxiters=8, progress_bar=False)(stars)
    psf = np.asarray(epsf.data, dtype=np.float32)
    psf[psf < 0] = 0
    return psf / psf.sum()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["empirical", "moffat"], default="moffat")
    p.add_argument("--mosaic", help="a COSMOS *_sci.fits tile (required for empirical)")
    p.add_argument("--out", default="acs_psf.npy")
    p.add_argument("--size", type=int, default=25)
    p.add_argument("--pixel_scale", type=float, default=0.05)
    p.add_argument("--fwhm_arcsec", type=float, default=0.10, help="moffat only")
    a = p.parse_args()
    if a.mode == "empirical":
        if not a.mosaic:
            raise SystemExit("--mode empirical needs --mosaic <tile_sci.fits>")
        psf = empirical(a.mosaic, a.size)
    else:
        psf = moffat(a.size, a.fwhm_arcsec / a.pixel_scale)
    np.save(a.out, psf)
    print(f"wrote {a.out}  shape={psf.shape}  mode={a.mode}  sum={psf.sum():.4f}")


if __name__ == "__main__":
    main()
