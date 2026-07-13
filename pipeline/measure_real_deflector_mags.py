#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
measure_real_deflector_mags.py -- Stage 1.2: derive the lens-light apparent-
magnitude prior directly from the 62 real SLACS cutouts by aperture
photometry, instead of guessing.

Assumptions (both printed, both checkable):
  * cutout pixel units are electrons/s (ACS drizzled _drc products);
  * ACS/WFC F814W AB zeropoint (default 25.94, override with --zeropoint).

Caveat (printed): the aperture includes arc light, which biases the deflector
magnitude slightly BRIGHT. For SLACS the deflector dominates the aperture
flux, so this is a small effect -- and for a training prior, a slightly wide
bright tail is harmless.

Usage:
    python measure_real_deflector_mags.py --real ~/einstein_cnn/real_slacs_images.h5
"""
import argparse
import os
import sys

import h5py
import numpy as np


def robust_sky_level_and_rms(img):
    """Sigma-clipped MEAN level and std of four 16x16 corner boxes."""
    s = 16
    boxes = [img[:s, :s], img[:s, -s:], img[-s:, :s], img[-s:, -s:]]
    levels, stds = [], []
    for b in boxes:
        x = b.ravel().astype(np.float64)
        for _ in range(5):
            m, sd = np.median(x), np.std(x)
            keep = np.abs(x - m) < 3 * sd
            if keep.all() or sd == 0:
                break
            x = x[keep]
        levels.append(np.mean(x))
        stds.append(np.std(x))
    return float(np.median(levels)), float(np.median(stds))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--real', required=True, help='real_slacs_images.h5')
    parser.add_argument('--zeropoint', type=float, default=25.94,
                        help='AB zeropoint for the pixel units (default 25.94)')
    parser.add_argument('--aperture-arcsec', type=float, default=2.0,
                        help='photometry aperture radius (default 2.0")')
    parser.add_argument('--pixscale', type=float, default=0.05)
    args = parser.parse_args()

    with h5py.File(os.path.expanduser(args.real), 'r') as h5:
        imgs = None
        for key in ('images', 'lensed', 'data'):
            if key in h5:
                imgs = np.squeeze(np.array(h5[key]))
                break
        if imgs is None:
            for key in h5.keys():
                if getattr(h5[key], 'ndim', 0) >= 3:
                    imgs = np.squeeze(np.array(h5[key]))
                    print('Using key "{0}"'.format(key))
                    break
        names = np.array(h5['names']) if 'names' in h5 else None
    if imgs is None:
        sys.exit('No image dataset found.')

    n = imgs.shape[1]
    r_pix = args.aperture_arcsec / args.pixscale
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.sqrt((xx - n / 2.0) ** 2 + (yy - n / 2.0) ** 2)
    ap = rr < r_pix
    npix = int(ap.sum())

    mags = []
    for i, im in enumerate(imgs):
        sky_level, _ = robust_sky_level_and_rms(im)
        flux = float(im[ap].sum() - sky_level * npix)
        if flux <= 0:
            print('  image {0}: non-positive aperture flux, skipped'.format(i))
            continue
        mags.append(args.zeropoint - 2.5 * np.log10(flux))
    mags = np.array(mags)

    print('ASSUMED: pixels in electrons/s, AB zeropoint {0:.2f}, aperture '
          'r={1:.1f}" -- verify units against the BUNIT of the original _drc '
          'files if in doubt.'.format(args.zeropoint, args.aperture_arcsec))
    print('CAVEAT: aperture includes arc light -> deflector mags slightly '
          'bright-biased (small for SLACS).')
    print('N = {0} deflectors'.format(len(mags)))
    print('apparent F814W mag: median {0:.2f}   16-84%: [{1:.2f}, {2:.2f}]   '
          'full range: [{3:.2f}, {4:.2f}]'.format(
              np.median(mags), np.percentile(mags, 16),
              np.percentile(mags, 84), mags.min(), mags.max()))

    lo = np.floor((mags.min() - 0.3) * 10) / 10.0
    hi = np.ceil((mags.max() + 0.3) * 10) / 10.0
    print('\nSUGGESTED paltas 0.1.1 lens_light magnitude prior '
          '(APPARENT convention):')
    print("    'magnitude': uniform(loc={0:.1f}, scale={1:.1f}).rvs,".format(
        lo, hi - lo))
    print('(uniform over [{0:.1f}, {1:.1f}], i.e. the observed range padded '
          'by 0.3 mag on each side)'.format(lo, hi))


if __name__ == '__main__':
    main()
