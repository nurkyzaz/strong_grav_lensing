#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_paltas_pilot.py -- generate a paltas dataset with paltas 0.1.1, logging the
acceptance rate (which stock generate.py does not report) and avoiding the
pandas .append() call that crashes on pandas >= 2.0.

Output format is identical to stock paltas 0.1.1 generate.py:
    <out>/image_0000000.npy ... image_NNNNNNN.npy   (one 2-D array each)
    <out>/metadata.csv                               (one row per image)
    <out>/<config filename>                          (copy of the config used)

Usage (run from the directory containing acs_psf.npy, i.e. ~/cosmos_acs/tiles):
    python run_paltas_pilot.py config_lensfusion_acs.py ~/paltas_pilot200 --n 200 --seed 1
"""
import argparse
import os
import shutil
import sys

import numpy as np
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='paltas config .py file')
    parser.add_argument('out', help='output folder')
    parser.add_argument('--n', type=int, default=200,
                        help='number of ACCEPTED images to generate')
    parser.add_argument('--seed', type=int, default=0,
                        help='numpy global seed (use a different seed per shard)')
    parser.add_argument('--max-tries-factor', type=int, default=50,
                        help='abort if tries exceed n * this factor '
                             '(guards against a mag_cut that rejects everything)')
    args = parser.parse_args()

    np.random.seed(args.seed)

    out = os.path.expanduser(args.out)
    if not os.path.exists(out):
        os.makedirs(out)
    shutil.copy(os.path.abspath(args.config), out)

    from paltas.Configs.config_handler import ConfigHandler
    handler = ConfigHandler(args.config)

    # Report whether a magnification cut is active (Stage 0.3 gate).
    mag_cut = getattr(handler, 'mag_cut', None)
    if mag_cut is None:
        print('WARNING: no mag_cut in this config -> acceptance will be 1.0 '
              'and unlensed blob geometries WILL enter the dataset.')
    else:
        print('mag_cut active: total magnification >= {0}'.format(mag_cut))

    rows = []
    n_done = 0
    tries = 0
    max_tries = args.n * args.max_tries_factor
    report_every = max(1, args.n // 10)

    while n_done < args.n:
        tries += 1
        if tries > max_tries:
            print('ABORT: {0} tries for {1} accepted images. '
                  'mag_cut is rejecting almost everything -- the source-position '
                  'prior and theta_E prior are probably mismatched. '
                  'Do NOT scale this up; investigate the config.'.format(
                      tries, n_done))
            sys.exit(1)

        image, metadata = handler.draw_image(new_sample=True)
        if image is None:
            continue

        np.save(os.path.join(out, 'image_%07d' % n_done), image)
        rows.append(dict(metadata))
        n_done += 1
        if n_done % report_every == 0:
            print('  {0}/{1} accepted  (acceptance so far: {2:.3f})'.format(
                n_done, args.n, float(n_done) / tries))

    df = pd.DataFrame(rows)
    df = df.reindex(sorted(df.columns), axis=1)
    df.to_csv(os.path.join(out, 'metadata.csv'), index=None)

    acc = float(n_done) / tries
    print('DONE: {0} images in {1}'.format(n_done, out))
    print('ACCEPTANCE RATE: {0:.3f}  ({1} tries)'.format(acc, tries))
    if mag_cut is not None and acc > 0.999:
        print('WARNING: acceptance ~1.0 despite mag_cut -- either the cut is '
              'very loose or every draw is strongly lensed. Inspect previews.')
    if acc < 0.2:
        print('NOTE: acceptance < 0.2 is wasteful; consider tightening the '
              'source-position prior rather than loosening mag_cut.')


if __name__ == '__main__':
    main()
