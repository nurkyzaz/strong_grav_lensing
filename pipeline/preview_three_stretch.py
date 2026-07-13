#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
preview_three_stretch.py -- render the same images under three display
stretches (linear / percentile clip / asinh). Most historical "blob" and
"missing lens light" scares were display-stretch artifacts; this makes them
impossible.

Input: either a paltas run folder (image_*.npy) or an h5 with key 'lensed'
(or 'data'). Writes three PNGs next to the input:
    preview_linear.png, preview_pclip.png, preview_asinh.png

Usage:
    python preview_three_stretch.py ~/paltas_pilot200 --n 16 --seed 0
    python preview_three_stretch.py ~/einstein_cnn/real_slacs_images.h5 --n 16
"""
import argparse
import glob
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def robust_sky(img):
    """Sigma-clipped std of the four 16x16 corner boxes (median across boxes)."""
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


def load_images(path):
    path = os.path.expanduser(path)
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, 'image_*.npy')))
        if not files:
            sys.exit('No image_*.npy in {0}'.format(path))
        return np.stack([np.load(f) for f in files]), path
    import h5py
    with h5py.File(path, 'r') as h5:
        for key in ('lensed', 'data', 'images'):
            if key in h5:
                return np.array(h5[key]), os.path.dirname(path) or '.'
        # fall back: first 3-D dataset
        for key in h5.keys():
            if getattr(h5[key], 'ndim', 0) == 3:
                print('Using h5 key "{0}"'.format(key))
                return np.array(h5[key]), os.path.dirname(path) or '.'
    sys.exit('No 3-D image dataset found in {0}'.format(path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='paltas run folder or h5 file')
    parser.add_argument('--n', type=int, default=16)
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()

    imgs, outdir = load_images(args.path)
    imgs = np.squeeze(imgs)
    rng = np.random.RandomState(args.seed)
    idx = rng.choice(len(imgs), size=min(args.n, len(imgs)), replace=False)
    sel = imgs[idx]

    ncol = 4
    nrow = int(np.ceil(len(sel) / float(ncol)))

    def panel(fname, title, transform, per_image_scale):
        fig, axes = plt.subplots(nrow, ncol, figsize=(3 * ncol, 3 * nrow))
        axes = np.atleast_1d(axes).ravel()
        for ax in axes:
            ax.axis('off')
        for k, im in enumerate(sel):
            disp = transform(im)
            vmin, vmax = per_image_scale(disp)
            axes[k].imshow(disp, origin='lower', cmap='gray',
                           vmin=vmin, vmax=vmax)
            axes[k].set_title('#{0}'.format(idx[k]), fontsize=8)
        fig.suptitle(title)
        fig.tight_layout()
        out = os.path.join(outdir, fname)
        fig.savefig(out, dpi=110)
        plt.close(fig)
        print('wrote {0}'.format(out))

    panel('preview_linear.png', 'linear (full range)',
          lambda im: im,
          lambda d: (d.min(), d.max()))
    panel('preview_pclip.png', 'percentile clip [1, 99.5]',
          lambda im: im,
          lambda d: (np.percentile(d, 1), np.percentile(d, 99.5)))
    panel('preview_asinh.png', 'asinh(img / sky_rms)',
          lambda im: np.arcsinh(im / max(robust_sky(im), 1e-12)),
          lambda d: (np.percentile(d, 1), np.percentile(d, 99.9)))

    print('Read all three: a lens invisible in linear but bright in asinh = '
          'stretch artifact, not a config bug.')


if __name__ == '__main__':
    main()
