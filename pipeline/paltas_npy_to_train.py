#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
paltas_npy_to_train.py -- convert a paltas 0.1.1 run folder
(image_XXXXXXX.npy + metadata.csv) into the training h5 format:

    lensed    [N, 128, 128] float32
    theta_E   [N]           float64   (SIE theta_E, from
                                       main_deflector_parameters_theta_E)
    image_fov [N]           float64   (all 6.4)

Usage:
    python paltas_npy_to_train.py --run ~/paltas_pilot200 --out ~/einstein_cnn/pilot200.h5
"""
import argparse
import glob
import os
import sys

import h5py
import numpy as np
import pandas as pd

THETA_COL = 'main_deflector_parameters_theta_E'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True, help='paltas output folder')
    parser.add_argument('--out', required=True, help='output .h5 path')
    parser.add_argument('--fov', type=float, default=6.4)
    args = parser.parse_args()

    run = os.path.expanduser(args.run)
    meta_path = os.path.join(run, 'metadata.csv')
    if not os.path.exists(meta_path):
        sys.exit('No metadata.csv in {0}'.format(run))
    meta = pd.read_csv(meta_path)

    if THETA_COL not in meta.columns:
        cands = [c for c in meta.columns if 'theta_E' in c]
        sys.exit('Column {0} not found. theta_E-like columns present: {1}'.format(
            THETA_COL, cands))

    files = sorted(glob.glob(os.path.join(run, 'image_*.npy')))
    if len(files) != len(meta):
        sys.exit('COUNT MISMATCH: {0} npy files vs {1} metadata rows. '
                 'Do not proceed -- labels would be misaligned.'.format(
                     len(files), len(meta)))

    # image_%07d naming + row order both follow generation order, so index i
    # in the sorted file list corresponds to metadata row i. Verify the naming
    # is contiguous to be safe.
    for i, f in enumerate(files):
        expect = 'image_%07d.npy' % i
        if os.path.basename(f) != expect:
            sys.exit('Non-contiguous file naming at index {0}: {1}. '
                     'Labels would be misaligned; aborting.'.format(i, f))

    first = np.load(files[0])
    if first.shape != (128, 128):
        print('WARNING: image shape is {0}, expected (128, 128). '
              'Check numpix / drizzle settings before training.'.format(first.shape))

    imgs = np.zeros((len(files),) + first.shape, dtype=np.float32)
    for i, f in enumerate(files):
        imgs[i] = np.load(f).astype(np.float32)

    theta = meta[THETA_COL].values.astype(np.float64)

    out = os.path.expanduser(args.out)
    with h5py.File(out, 'w') as h5:
        h5.create_dataset('lensed', data=imgs, compression='gzip')
        h5.create_dataset('theta_E', data=theta)
        h5.create_dataset('image_fov', data=np.full(len(files), args.fov))

    print('Wrote {0}: lensed {1}, theta_E [{2:.3f}, {3:.3f}] '
          '(median {4:.3f})'.format(out, imgs.shape, theta.min(), theta.max(),
                                    np.median(theta)))
    frac_low = float(np.mean(theta < 0.7))
    frac_high = float(np.mean(theta > 1.7))
    print('theta_E fraction below 0.7": {0:.2f}   above 1.7": {1:.2f}  '
          '(benchmark range should sit in the interior)'.format(frac_low, frac_high))


if __name__ == '__main__':
    main()
