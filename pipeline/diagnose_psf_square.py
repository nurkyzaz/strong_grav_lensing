#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
diagnose_psf_square.py -- test whether the central square artifact is the
truncated support of the pixel PSF kernel.

Mechanism being tested: convolution with a finite kernel spreads light only
within the kernel's support. A very bright, sharply peaked lens core therefore
produces a kernel-shaped plateau of scattered light with a hard step exactly
at the kernel's half-width. Arcs are too faint for their own step to show.

Method: render the SAME draw (same seed; PSF parameters are constants, so the
random sequence is identical) noiselessly under (P) the config's pixel PSF and
(G) a Gaussian PSF, and measure the brightness step across the kernel-edge
radius in both. A large step in P and none in G confirms the diagnosis; the
PNG shows it visually (P / G / P-G difference).

Run from ~/cosmos_acs/tiles:
    python diagnose_psf_square.py config_lensfusion_acs.py --n 2 --seed 0
Writes: psf_square_diagnostic.png
"""
import argparse
import importlib.util
import os
import sys
import tempfile

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

VARIANT_TEMPLATE = '''
import sys, copy
sys.path.insert(0, {srcdir!r})
from {modname} import *   # noqa
config_dict = copy.deepcopy(config_dict)
no_noise = True
{extra}
'''


def band_profile(img):
    """Mean brightness vs radius, averaged over 9-px bands along the four
    axis directions from the image center."""
    c = img.shape[0] // 2
    b = 4
    profs = [img[c - b:c + b + 1, c:].mean(axis=0),
             img[c - b:c + b + 1, :c + 1][:, ::-1].mean(axis=0),
             img[c:, c - b:c + b + 1].mean(axis=1),
             img[:c + 1, c - b:c + b + 1][::-1].mean(axis=1)]
    L = min(len(p) for p in profs)
    return np.mean([p[:L] for p in profs], axis=0)


def edge_discontinuity(diff_img, half):
    """Second-difference (discontinuity) of the P-G difference image's band
    profile at the kernel-edge radius, vs a smooth control region outside.
    The same-draw difference cancels the lens/arc structure, isolating the
    PSF effect; a real support truncation shows a sharp spike at `half`."""
    p = band_profile(diff_img)
    if half + 16 >= len(p):
        return np.nan, np.nan
    d2 = np.abs(p[:-2] - 2 * p[1:-1] + p[2:])
    # allow +-1 px slop on the edge location
    edge = d2[max(half - 2, 0):half + 1].max()
    control = np.median(d2[half + 5:half + 15])
    return edge, control


def draw_n(config_path, n, seed):
    from paltas.Configs.config_handler import ConfigHandler
    np.random.seed(seed)
    handler = ConfigHandler(config_path)
    out, tries = [], 0
    while len(out) < n and tries < 60 * n:
        tries += 1
        img, meta = handler.draw_image(new_sample=True)
        if img is not None:
            out.append(img)
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('--n', type=int, default=2)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--half', type=int, default=None,
                        help='override the edge radius to inspect '
                             '(use the OLD kernel half-width after '
                             'applying fix_psf_kernel.py)')
    args = parser.parse_args()

    srcdir = os.path.dirname(os.path.abspath(args.config)) or '.'
    modname = os.path.splitext(os.path.basename(args.config))[0]

    # read the kernel from the config module itself
    spec = importlib.util.spec_from_file_location(modname, args.config)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    psf_params = mod.config_dict.get('psf', {}).get('parameters', {})
    kernel = psf_params.get('kernel_point_source', None)
    if kernel is None:
        sys.exit('This config uses psf_type={0} with no pixel kernel -- the '
                 'square cannot be PSF-support truncation. Send me the '
                 'config psf block.'.format(psf_params.get('psf_type')))
    kernel = np.asarray(kernel)
    ksize = min(kernel.shape)
    half = args.half if args.half is not None else ksize // 2
    border = np.concatenate([kernel[0, :], kernel[-1, :],
                             kernel[:, 0], kernel[:, -1]])
    print('pixel PSF kernel: shape {0}, edge_max/peak = {1:.2e}, '
          'edge_median/peak = {2:.2e}'.format(
              kernel.shape, border.max() / kernel.max(),
              np.median(border) / kernel.max()))
    print('expected square half-width: {0} px ({1:.2f}") -> full width '
          '{2} px'.format(half, half * 0.05, 2 * half))

    tmpdir = tempfile.mkdtemp()
    variants = {}
    for tag, extra in [
            ('P pixel PSF', ''),
            ('G gaussian PSF',
             "config_dict['psf'] = {'parameters': "
             "{'psf_type': 'GAUSSIAN', 'fwhm': 0.10}}\n")]:
        path = os.path.join(tmpdir, 'variant_{0}.py'.format(tag[0]))
        with open(path, 'w') as f:
            f.write(VARIANT_TEMPLATE.format(srcdir=srcdir, modname=modname,
                                            extra=extra))
        print('rendering variant {0} ...'.format(tag))
        variants[tag[0]] = draw_n(path, args.n, args.seed)

    nP, nG = len(variants['P']), len(variants['G'])
    n = min(nP, nG)
    if n == 0:
        sys.exit('No accepted draws; check mag_cut / config.')

    fig, axes = plt.subplots(3, n, figsize=(3.2 * n, 10))
    axes = np.atleast_2d(axes.reshape(3, n))
    edges, controls = [], []
    for i in range(n):
        imP, imG = variants['P'][i], variants['G'][i]
        e, ctl = edge_discontinuity(imP - imG, half)
        edges.append(e)
        controls.append(ctl)
        for r, (im, ttl) in enumerate([(imP, 'pixel PSF'),
                                       (imG, 'gaussian PSF'),
                                       (imP - imG, 'difference P-G')]):
            ax = axes[r, i]
            ax.axis('off')
            disp = np.arcsinh(im / max(np.std(im[:12, :12]), 1e-9))
            ax.imshow(disp, origin='lower', cmap='gray',
                      vmin=np.percentile(disp, 1),
                      vmax=np.percentile(disp, 99.7))
            if i == 0:
                ax.set_title(ttl, fontsize=10, loc='left')
    fig.suptitle('PSF-square diagnostic (noiseless, same draws)')
    fig.tight_layout()
    fig.savefig('psf_square_diagnostic.png', dpi=120)
    print('wrote psf_square_diagnostic.png')

    e_med = np.median(edges)
    c_med = np.median(controls)
    ratio = e_med / max(c_med, 1e-30)
    print('\nsupporting number -- discontinuity of the P-G profile at radius '
          '{0} px, relative to the smooth region outside: {1:.1f}'.format(
              half, ratio))
    print('(truncated kernels typically give >~8-10 here; but an arc landing '
          'near the control radii can swing this either way, so treat it as '
          'supporting evidence only)')
    print('\nTHE TWO DECISIVE CHECKS ARE:')
    print('  1. WIDTH MATCH: the kernel is {0}x{0} px -> predicted square '
          'width {1} px = {2:.2f}". Measure the square in your '
          'preview_pclip.png (it spans FULL WIDTH {1} px if this diagnosis '
          'is right).'.format(ksize, 2 * half, 2 * half * 0.05))
    print('  2. VISUAL: in psf_square_diagnostic.png the square must be '
          'present under the pixel PSF, absent under the Gaussian PSF, and '
          'crisp in the difference panel.')
    print('If both hold -> confirmed; run fix_psf_kernel.py. If either '
          'fails, send me the PNG and the printed numbers.')
    print('After fixing, re-run this script with --half {0} on the new '
          'config: the square outline at that radius should be gone from '
          'the difference panel.'.format(half))


if __name__ == '__main__':
    main()
