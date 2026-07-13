#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
diagnose_components.py -- render the SAME config in four variants to isolate
which component carries the central square artifact:

  A. full            : lens light + lensed source + noise   (what you saw)
  B. arc_only        : lensed source + noise (lens_light removed)
  C. arc_noiseless   : lensed source only (no lens light, no detector noise)
  D. unlensed_source : like C but theta_E forced to 1e-4 -> essentially
                       unlensed stamp. If the square appears here with
                       straight edges, it is the COSMOS stamp footprint
                       (stamp background noise), not a lensing artifact.

Also prints, for variant C: the median level INSIDE the central square region
vs. the detector sky RMS measured from variant B corners. If the stamp
plateau is comparable to or above the detector noise, the square is stamp
background noise standing above your (too-low) sky noise.

Run from ~/cosmos_acs/tiles:
    python diagnose_components.py config_lensfusion_acs.py --n 4 --seed 0
Writes: components_diagnostic.png in the current directory.
"""
import argparse
import importlib
import os
import sys
import tempfile

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


VARIANT_TEMPLATE = '''
import sys
sys.path.insert(0, {srcdir!r})
from {modname} import *   # noqa

{extra}
'''


def robust_sky(img):
    s = 16
    boxes = [img[:s, :s], img[:s, -s:], img[-s:, :s], img[-s:, -s:]]
    stds = []
    for b in boxes:
        x = b.ravel().astype(np.float64)
        for _ in range(5):
            m, sd = np.median(x), np.std(x)
            keep = np.abs(x - m) < 3 * sd
            if keep.all() or sd == 0:
                break
            x = x[keep]
        stds.append(np.std(x))
    return float(np.median(stds))


def make_variant(tmpdir, srcdir, modname, tag, extra):
    path = os.path.join(tmpdir, 'variant_{0}.py'.format(tag))
    with open(path, 'w') as f:
        f.write(VARIANT_TEMPLATE.format(srcdir=srcdir, modname=modname,
                                        extra=extra))
    return path


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
    if len(out) < n:
        print('WARNING: only {0}/{1} accepted for this variant'.format(
            len(out), n))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config')
    parser.add_argument('--n', type=int, default=4)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()

    srcdir = os.path.dirname(os.path.abspath(args.config)) or '.'
    modname = os.path.splitext(os.path.basename(args.config))[0]

    variants = [
        ('A full', ''),
        ('B arc_only',
         "config_dict = dict(config_dict)\n"
         "config_dict.pop('lens_light', None)\n"),
        ('C arc_noiseless',
         "config_dict = dict(config_dict)\n"
         "config_dict.pop('lens_light', None)\n"
         "no_noise = True\n"),
        ('D unlensed_src',
         "import copy\n"
         "config_dict = copy.deepcopy(config_dict)\n"
         "config_dict.pop('lens_light', None)\n"
         "config_dict['main_deflector']['parameters']['theta_E'] = 1e-4\n"
         "no_noise = True\n"
         "mag_cut = None\n"),
    ]

    tmpdir = tempfile.mkdtemp()
    results = {}
    for tag, extra in variants:
        path = make_variant(tmpdir, srcdir, modname, tag.split()[0], extra)
        print('rendering variant {0} ...'.format(tag))
        results[tag] = draw_n(path, args.n, args.seed)

    nrow = len(variants)
    ncol = args.n
    fig, axes = plt.subplots(nrow, ncol, figsize=(3 * ncol, 3 * nrow))
    axes = np.atleast_2d(axes)
    for r, (tag, _) in enumerate(variants):
        for c in range(ncol):
            ax = axes[r, c]
            ax.axis('off')
            imgs = results[tag]
            if c >= len(imgs):
                continue
            im = imgs[c]
            sky = max(robust_sky(im), 1e-12)
            disp = np.arcsinh(im / sky)
            ax.imshow(disp, origin='lower', cmap='gray',
                      vmin=np.percentile(disp, 1),
                      vmax=np.percentile(disp, 99.9))
            if c == 0:
                ax.set_ylabel(tag)
            ax.set_title(tag if c == 0 else '', fontsize=9, loc='left')
    fig.suptitle('component decomposition (asinh stretch per panel)')
    fig.tight_layout()
    fig.savefig('components_diagnostic.png', dpi=120)
    print('wrote components_diagnostic.png')

    # Quantify: stamp plateau (variant C center region, away from the galaxy)
    # vs detector sky RMS (variant B corners).
    if results.get('C arc_noiseless') and results.get('B arc_only'):
        plateau_levels, det_rms = [], []
        for imC, imB in zip(results['C arc_noiseless'], results['B arc_only']):
            n = imC.shape[0]
            c0 = n // 2
            ring = imC[c0 - 30:c0 + 30, c0 - 30:c0 + 30].copy()
            # exclude the bright arc pixels: keep the faint half
            vals = ring.ravel()
            vals = vals[vals < np.percentile(vals, 50)]
            plateau_levels.append(np.std(vals))
            det_rms.append(robust_sky(imB))
        print('\nstamp-noise std inside central region (variant C, faint '
              'half): median {0:.4g}'.format(np.median(plateau_levels)))
        print('detector sky RMS (variant B corners):            '
              'median {0:.4g}'.format(np.median(det_rms)))
        ratio = np.median(plateau_levels) / max(np.median(det_rms), 1e-30)
        print('ratio stamp/detector = {0:.2f}'.format(ratio))
        if ratio > 0.5:
            print('=> The COSMOS stamp background noise is comparable to or '
                  'above the detector noise. Expected fixes: (1) subtract + '
                  'apodize the stamp background (CleanCOSMOS patch), and '
                  '(2) Stage-1 noise calibration will raise detector noise '
                  'toward real SLACS levels, burying the residual.')
        else:
            print('=> Stamp noise is subdominant; if a square is still '
                  'visible, send me components_diagnostic.png before '
                  'changing anything.')


if __name__ == '__main__':
    main()
