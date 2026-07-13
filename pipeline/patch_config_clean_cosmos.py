#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
patch_config_clean_cosmos.py -- one-shot patch for config_lensfusion_acs.py.

Why: paltas's COSMOSCatalog loads raw COSMOS stamps with NO background
subtraction (verified in Sources/cosmos.py: image_and_metadata just np.load's
the stamp, optionally smooths). The stamps keep their own HST sky noise, and
lenstronomy's INTERPOL renders zero outside the stamp footprint -- so the
stamp appears as a sharp-edged noisy rectangle standing above the detector
sky. That is the "square in the middle" artifact.

Fix: CleanCOSMOS subclass that (1) subtracts a sigma-clipped border-median
background from each stamp and (2) cosine-apodizes the outer few stamp pixels
so any residual edge fades smoothly to zero.

Run diagnose_components.py FIRST and confirm the square lives in the
source-only variants before applying this.

Usage:
    python patch_config_clean_cosmos.py config_lensfusion_acs.py
"""
import argparse
import difflib
import re
import shutil
import sys

CLASS_DEF = '''

class CleanCOSMOS(COSMOSCatalog):
    """COSMOSCatalog with per-stamp background subtraction + edge
    apodization. Raw COSMOS stamps keep their own HST sky noise;
    INTERPOL renders zero outside the stamp, so against low detector
    noise the stamp footprint shows as a sharp bright rectangle.
    Subtracting the border-median background and tapering the edges
    removes the footprint while preserving the galaxy itself.
    Caveat: border subtraction can clip a small amount of real galaxy
    wing flux; negligible for a training prior."""
    APOD_PIX = 6  # cosine-taper width at each stamp edge (stamp pixels)

    def image_and_metadata(self, catalog_i):
        img, meta = super(CleanCOSMOS, self).image_and_metadata(catalog_i)
        img = np.array(img, dtype=float, copy=True)
        # background: sigma-clipped median of a 3-px border frame
        b = 3
        border = np.concatenate([
            img[:b, :].ravel(), img[-b:, :].ravel(),
            img[:, :b].ravel(), img[:, -b:].ravel()])
        x = border
        for _ in range(5):
            m, sd = np.median(x), np.std(x)
            keep = np.abs(x - m) < 3 * sd
            if keep.all() or sd == 0:
                break
            x = x[keep]
        img -= np.median(x)
        # cosine apodization of the outer APOD_PIX pixels on each edge
        w = self.APOD_PIX

        def taper(npix):
            t = np.ones(npix)
            if w > 0 and npix > 2 * w:
                ramp = 0.5 * (1 - np.cos(np.pi * np.arange(w) / float(w)))
                t[:w] = ramp
                t[-w:] = ramp[::-1]
            return t
        img *= taper(img.shape[0])[:, None]
        img *= taper(img.shape[1])[None, :]
        return img, meta

'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='path to config_lensfusion_acs.py')
    args = parser.parse_args()

    with open(args.config) as f:
        original = f.read()
    text = original

    if 'class CleanCOSMOS' in text:
        sys.exit('CleanCOSMOS already present -- nothing to do.')
    if 'import numpy as np' not in text:
        sys.exit('ABORT: config does not import numpy as np; add that first.')
    if re.search(r'from paltas\.Sources\.cosmos import .*COSMOSCatalog', text) \
            is None and 'COSMOSCatalog' not in text:
        sys.exit('ABORT: config does not appear to use COSMOSCatalog.')

    m = re.search(r'^config_dict\s*=\s*\{', text, flags=re.M)
    if m is None:
        sys.exit('ABORT: could not find "config_dict = {".')
    text = text[:m.start()] + CLASS_DEF.lstrip('\n') + '\n' + text[m.start():]

    pattern = re.compile(
        r"((['\"])source\2\s*:\s*\{.*?(['\"])class\3\s*:\s*)COSMOSCatalog",
        flags=re.S)
    text, nsub = pattern.subn(r'\1CleanCOSMOS', text, count=1)
    if nsub != 1:
        sys.exit("ABORT: could not find 'class': COSMOSCatalog inside the "
                 "'source' block (found {0} matches). Switch the source "
                 "class to CleanCOSMOS manually.".format(nsub))

    backup = args.config + '.bak2'
    shutil.copy(args.config, backup)
    with open(args.config, 'w') as f:
        f.write(text)

    diff = difflib.unified_diff(
        original.splitlines(True), text.splitlines(True),
        fromfile=backup, tofile=args.config)
    sys.stdout.writelines(diff)
    print('\nPatched. Backup at {0}'.format(backup))


if __name__ == '__main__':
    main()
