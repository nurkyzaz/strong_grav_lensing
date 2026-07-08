#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
gate_stage0.py -- the numeric realism gate for a pilot dataset, plus the
Stage-1.1 noise-calibration suggestion.

Computes, with IDENTICAL definitions on sim and real (so the comparison is
internally consistent and does not depend on any older script's conventions):

  1. grid check (shape)
  2. sky RMS       : sigma-clipped std of four 16x16 corner boxes, median
  3. lens peak/sky : max of central 24x24 box / sky RMS
  4. theta_E label histogram (from metadata.csv) -- flatness / range
  5. normalized-domain overlay: histogram of asinh(img / sky_rms) pixels and
     the median radial profile of asinh-normalized images, sim vs real.
     This is the single cheapest domain-gap detector: if these do not
     overlap, the CNN sees the gap before you train anything.
  6. exposure-time suggestion: sky-limited scaling
     t_new ~ t_current * (RMS_sim / RMS_real)^2

Usage:
    python gate_stage0.py \
        --sim  ~/einstein_cnn/pilot200.h5 \
        --real ~/einstein_cnn/real_slacs_images.h5 \
        --csv  failure_features_slacs.csv \
        --meta ~/paltas_pilot200/metadata.csv \
        --out  ~/einstein_cnn/gate_stage0_report.png
"""
import argparse
import os
import sys

import h5py
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Targets measured from the real SLACS cutouts (project standing numbers).
PEAK_SKY_TARGET = (93.0, 197.0)


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


def peak_over_sky(img, sky):
    c = img.shape[0] // 2
    core = img[c - 12:c + 12, c - 12:c + 12]
    return float(core.max() / max(sky, 1e-12))


def load_h5_images(path, prefer=('lensed', 'images', 'data')):
    with h5py.File(os.path.expanduser(path), 'r') as h5:
        for key in prefer:
            if key in h5:
                return np.squeeze(np.array(h5[key]))
        for key in h5.keys():
            if getattr(h5[key], 'ndim', 0) >= 3:
                print('Using key "{0}" from {1}'.format(key, path))
                return np.squeeze(np.array(h5[key]))
    sys.exit('No image dataset found in {0}'.format(path))


def radial_profile(img, nbins=60):
    n = img.shape[0]
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.sqrt((xx - n / 2.0) ** 2 + (yy - n / 2.0) ** 2)
    edges = np.linspace(0, n / 2.0, nbins + 1)
    prof = np.zeros(nbins)
    for i in range(nbins):
        m = (r >= edges[i]) & (r < edges[i + 1])
        prof[i] = np.median(img[m]) if m.any() else np.nan
    centers = 0.5 * (edges[:-1] + edges[1:])
    return centers, prof


def verdict(name, value, lo, hi, unit=''):
    ok = (value >= lo) and (value <= hi)
    tag = 'PASS ' if ok else 'CHECK'
    print('  [{0}] {1}: {2:.3g}{3}   (target {4:.3g} - {5:.3g})'.format(
        tag, name, value, unit, lo, hi))
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sim', required=True, help='pilot training h5')
    parser.add_argument('--real', required=True, help='real_slacs_images.h5')
    parser.add_argument('--csv', required=True,
                        help='failure_features_slacs.csv (sky_rms column)')
    parser.add_argument('--meta', required=True,
                        help='metadata.csv from the pilot run')
    parser.add_argument('--out', default='gate_stage0_report.png')
    args = parser.parse_args()

    sim = load_h5_images(args.sim)
    real = load_h5_images(args.real)
    meta = pd.read_csv(os.path.expanduser(args.meta))
    feats = pd.read_csv(os.path.expanduser(args.csv))

    print('=== 1. Grid ===')
    print('  sim  {0}   real {1}'.format(sim.shape, real.shape))
    if sim.shape[1:] != (128, 128):
        print('  [CHECK] sim images are not 128x128 -- fix before anything else.')

    print('=== 2. Sky RMS (same estimator on both) ===')
    sky_sim = np.array([robust_sky(im) for im in sim])
    sky_real = np.array([robust_sky(im) for im in real])
    med_sim, med_real = np.median(sky_sim), np.median(sky_real)
    print('  sim : median {0:.4g}  [16-84%: {1:.4g}, {2:.4g}]'.format(
        med_sim, np.percentile(sky_sim, 16), np.percentile(sky_sim, 84)))
    print('  real: median {0:.4g}  [16-84%: {1:.4g}, {2:.4g}]'.format(
        med_real, np.percentile(sky_real, 16), np.percentile(sky_real, 84)))
    if 'sky_rms' in feats.columns:
        print('  real (csv sky_rms column): median {0:.4g}  -- if this differs a lot '
              'from the value above, the two estimators differ; trust the '
              'same-estimator comparison for the gate.'.format(
                  feats['sky_rms'].median()))
    ratio = med_sim / max(med_real, 1e-30)
    verdict('sky RMS ratio sim/real', ratio, 0.8, 1.25)

    print('=== 3. Lens peak / sky (same definition on both) ===')
    ps_sim = np.array([peak_over_sky(im, s) for im, s in zip(sim, sky_sim)])
    ps_real = np.array([peak_over_sky(im, s) for im, s in zip(real, sky_real)])
    print('  sim : median {0:.1f}  [16-84%: {1:.1f}, {2:.1f}]'.format(
        np.median(ps_sim), np.percentile(ps_sim, 16), np.percentile(ps_sim, 84)))
    print('  real: median {0:.1f}  [16-84%: {1:.1f}, {2:.1f}]  '
          '(project target band {3:.0f}-{4:.0f})'.format(
              np.median(ps_real), np.percentile(ps_real, 16),
              np.percentile(ps_real, 84), PEAK_SKY_TARGET[0], PEAK_SKY_TARGET[1]))
    # Gate: sim median inside the real 16-84 band (self-consistent definition).
    verdict('sim peak/sky median vs real 16-84 band', np.median(ps_sim),
            np.percentile(ps_real, 16), np.percentile(ps_real, 84))

    print('=== 4. theta_E labels ===')
    tcol = 'main_deflector_parameters_theta_E'
    if tcol in meta.columns:
        t = meta[tcol].values
        print('  range [{0:.3f}, {1:.3f}]  median {2:.3f}  '
              'fraction in benchmark band 0.7-1.7: {3:.2f}'.format(
                  t.min(), t.max(), np.median(t),
                  float(np.mean((t > 0.7) & (t < 1.7)))))
        verdict('theta_E min', t.min(), 0.0, 0.7)
        verdict('theta_E max', t.max(), 1.7, 5.0)
    else:
        print('  [CHECK] {0} not in metadata columns'.format(tcol))

    print('=== 5. Normalized-domain overlay (see PNG) ===')
    def norm_stack(stack, skies):
        return np.stack([np.arcsinh(im / max(s, 1e-12))
                         for im, s in zip(stack, skies)])
    nsim = norm_stack(sim, sky_sim)
    nreal = norm_stack(real, sky_real)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    # 5a. pixel histogram
    bins = np.linspace(-3, 9, 121)
    axes[0].hist(nsim.ravel(), bins=bins, histtype='step', density=True,
                 label='sim', color='C0')
    axes[0].hist(nreal.ravel(), bins=bins, histtype='step', density=True,
                 label='real SLACS', color='C1')
    axes[0].set_yscale('log')
    axes[0].set_xlabel('asinh(pixel / sky RMS)')
    axes[0].set_title('normalized pixel histogram')
    axes[0].legend()
    # 5b. median radial profile
    r_s, p_s = radial_profile(np.median(nsim, axis=0))
    r_r, p_r = radial_profile(np.median(nreal, axis=0))
    axes[1].plot(r_s * 0.05, p_s, label='sim', color='C0')
    axes[1].plot(r_r * 0.05, p_r, label='real SLACS', color='C1')
    axes[1].set_xlabel('radius [arcsec]')
    axes[1].set_ylabel('median asinh-normalized flux')
    axes[1].set_title('median radial profile')
    axes[1].legend()
    # 5c. peak/sky distributions
    pbins = np.linspace(0, max(np.percentile(ps_real, 99),
                               np.percentile(ps_sim, 99)), 40)
    axes[2].hist(ps_sim, bins=pbins, histtype='step', density=True,
                 label='sim', color='C0')
    axes[2].hist(ps_real, bins=pbins, histtype='step', density=True,
                 label='real SLACS', color='C1')
    axes[2].set_xlabel('lens peak / sky RMS')
    axes[2].set_title('peak/sky distribution')
    axes[2].legend()
    fig.tight_layout()
    out = os.path.expanduser(args.out)
    fig.savefig(out, dpi=130)
    print('  wrote {0}'.format(out))

    print('=== 6. Stage-1.1 exposure-time suggestion (sky-limited scaling) ===')
    tcols = [c for c in meta.columns if 'exposure_time' in c]
    if tcols:
        t_cur = float(meta[tcols[0]].iloc[0])
        t_new = t_cur * ratio ** 2
        print('  current exposure_time = {0:.0f}s; sky RMS ratio sim/real = '
              '{1:.3f}'.format(t_cur, ratio))
        print('  suggested exposure_time ~ {0:.0f}s  '
              '(then RE-RUN a pilot and RE-CHECK -- the scaling is only exact '
              'in the sky-limited regime; read noise and sky_brightness also '
              'move the answer)'.format(t_new))
    else:
        print('  exposure_time not found in metadata; ratio sim/real = '
              '{0:.3f}; scale exposure_time by {1:.3f} manually.'.format(
                  ratio, ratio ** 2))

    print('\nGate rule: proceed to full generation only when sky-RMS ratio, '
          'peak/sky, theta_E range all PASS and the three PNG overlays '
          'visually agree.')


if __name__ == '__main__':
    main()
