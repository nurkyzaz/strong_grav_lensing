#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fix_psf_kernel.py -- remove the truncated-support square from a pixel PSF
kernel by EXTENDING its wings, not just tapering the edge.

Why extension and not a plain edge taper: the square artifact is the
DISCONTINUITY where the kernel support ends. A narrow taper replaces the step
with a ramp that is still far steeper than a real PSF's wing decline, so the
soft square survives (verified experimentally). Extension continues the wings
smoothly outward, which is what a real PSF does.

Method:
  1. fit the power-law slope alpha of the azimuthally-averaged wing profile
     in the outer annulus of the original kernel;
  2. on a larger grid (default 2x), keep the original kernel inside radius
     r0 = half-3; beyond r0, set k(r, theta) = k(r0, theta) * (r/r0)**alpha
     -- per-ANGLE continuation, so diffraction-spike structure is preserved;
  3. cosine-taper the outer few pixels of the new grid (wing values there are
     already tiny, so this taper is invisible);
  4. renormalize to the original total flux.

Note: this replaces the original kernel's corner pixels (beyond the inscribed
circle) with the wing model as well -- that is intentional, it is what removes
the square geometry.

Usage (from ~/cosmos_acs/tiles):
    python fix_psf_kernel.py acs_psf.npy --factor 2.0
Writes acs_psf_extended.npy, prints before/after stats and the exact command
to point the config at the new file.
"""
import argparse
import os

import numpy as np


def azimuthal_alpha(k, r0):
    """Power-law slope of the azimuthal-mean profile in [0.55*r0, r0]."""
    n = k.shape[0]
    c = n // 2
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c)
    sel = (r > 0.55 * r0) & (r <= r0) & (k > 0)
    if sel.sum() < 20:
        return -2.5
    lr = np.log(r[sel])
    lf = np.log(k[sel])
    A = np.vstack([lr, np.ones_like(lr)]).T
    alpha = np.linalg.lstsq(A, lf, rcond=None)[0][0]
    return float(np.clip(alpha, -5.0, -1.0))


def bilinear(k, y, x):
    """Bilinear sample of k at float coordinates (y, x)."""
    n0, n1 = k.shape
    y = np.clip(y, 0, n0 - 1.001)
    x = np.clip(x, 0, n1 - 1.001)
    y0 = np.floor(y).astype(int)
    x0 = np.floor(x).astype(int)
    dy = y - y0
    dx = x - x0
    return (k[y0, x0] * (1 - dy) * (1 - dx) + k[y0 + 1, x0] * dy * (1 - dx)
            + k[y0, x0 + 1] * (1 - dy) * dx + k[y0 + 1, x0 + 1] * dy * dx)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('kernel', help='input PSF .npy (e.g. acs_psf.npy)')
    parser.add_argument('--factor', type=float, default=2.0,
                        help='linear size factor for the new grid (default 2)')
    parser.add_argument('--taper', type=int, default=6,
                        help='cosine taper width at the NEW far edge (px)')
    parser.add_argument('--out', default=None)
    args = parser.parse_args()

    k = np.load(args.kernel).astype(float)
    if k.ndim != 2 or k.shape[0] != k.shape[1]:
        raise SystemExit('Expected a square 2-D kernel, got {0}'.format(k.shape))
    n = k.shape[0]
    c = n // 2
    total = k.sum()
    r0 = c - 3
    alpha = azimuthal_alpha(k, r0)
    border = np.concatenate([k[0, :], k[-1, :], k[:, 0], k[:, -1]])
    print('input : shape {0}, sum {1:.6g}, edge_max/peak {2:.2e}, '
          'wing slope alpha = {3:.2f}'.format(k.shape, total,
                                              border.max() / k.max(), alpha))

    m = int(round(n * args.factor))
    if m % 2 == 0:
        m += 1
    cm = m // 2
    yy, xx = np.mgrid[0:m, 0:m]
    dy = (yy - cm).astype(float)
    dx = (xx - cm).astype(float)
    r = np.hypot(dy, dx)

    k2 = np.zeros((m, m))
    inner = r <= r0
    # inside r0: copy the original kernel (same pixel offsets)
    k2[inner] = bilinear(k, dy[inner] + c, dx[inner] + c)
    # outside r0: per-angle power-law continuation from the r0 circle
    outer = ~inner
    scale_y = dy[outer] / np.maximum(r[outer], 1e-9) * r0 + c
    scale_x = dx[outer] / np.maximum(r[outer], 1e-9) * r0 + c
    boundary_vals = np.maximum(bilinear(k, scale_y, scale_x), 0)
    k2[outer] = boundary_vals * (r[outer] / r0) ** alpha

    # taper the far edge of the NEW grid
    w = args.taper

    def taper(npix):
        t = np.ones(npix)
        if w > 0 and npix > 2 * w:
            ramp = 0.5 * (1 - np.cos(np.pi * np.arange(w) / float(w)))
            t[:w] = ramp
            t[-w:] = ramp[::-1]
        return t
    k2 *= taper(m)[:, None] * taper(m)[None, :]

    k2 *= total / k2.sum()
    border2 = np.concatenate([k2[0, :], k2[-1, :], k2[:, 0], k2[:, -1]])
    print('output: shape {0}, sum {1:.6g}, edge_max/peak {2:.2e}, value at '
          'old edge radius now smooth (no support boundary)'.format(
              k2.shape, k2.sum(), border2.max() / k2.max()))

    out = args.out or (os.path.splitext(args.kernel)[0] + '_extended.npy')
    np.save(out, k2)
    print('wrote {0}'.format(out))
    print('\nPoint the config at it:')
    print("    grep -n '{0}' config_lensfusion_acs.py".format(
        os.path.basename(args.kernel)))
    print("    sed -i 's/{0}/{1}/' config_lensfusion_acs.py".format(
        os.path.basename(args.kernel), os.path.basename(out)))
    print('Then validate VISUALLY: re-run the smoke test + '
          'preview_three_stretch.py (square should be gone), and '
          'diagnose_psf_square.py --half {0} (no square outline at the old '
          'radius in the difference panel). Note: with a {1}x{1} kernel each '
          'draw convolves a bigger kernel -- generation gets somewhat '
          'slower; that is expected.'.format(c - 3 + 3, m))
    print('\nCaveats (flagged, not hidden): wings beyond the original '
          'support are a power-law MODEL, not data; spike structure is '
          'continued in angle but its detailed shape beyond r0 is '
          'approximate. If far-wing realism ever matters, replace with a '
          'genuinely larger ACS PSF stamp (ask Sam).')


if __name__ == '__main__':
    main()
