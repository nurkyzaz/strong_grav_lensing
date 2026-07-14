#!/usr/bin/env python
"""G5c: build the ACS->Roman-F106 PSF matching kernel, mirroring the
acs2vis recipe (photutils create_matching_kernel, Tukey window; source =
mean of the psf_bank_v2 extended ACS ePSFs; target = mejiro F106 PSF
(41px @ 0.11", detector-1 center) cubic-upsampled to the 0.05" grid).
Writes acs2roman_f106_kernel.npy + provenance json."""
import glob
import json
import os

import numpy as np
from photutils.psf.matching import create_matching_kernel, TukeyWindow
from scipy.ndimage import zoom

TILES = os.path.expanduser("~/cosmos_acs/tiles")

srcs = sorted(glob.glob(os.path.join(TILES, "psf_bank_v2/kernel_*_extended.npy")))
acs = np.mean([np.load(f) for f in srcs], axis=0)
acs = acs / acs.sum()
print("source: mean of %d ACS ePSFs, shape %s" % (len(srcs), acs.shape))

f106 = np.load(os.path.join(TILES, "roman_psf_F106.npy")).astype(float)
f106 = np.clip(f106, 0, None)
f106 = f106 / f106.sum()                      # mejiro kernel sum was 1.22
tgt = zoom(f106, 0.11 / 0.05, order=3)        # 41px@0.11 -> ~90px@0.05
tgt = np.clip(tgt, 0, None)
if tgt.shape[0] % 2 == 0:
    tgt = tgt[:-1, :-1]
n = acs.shape[0]
c = tgt.shape[0] // 2
h = n // 2
if tgt.shape[0] >= n:
    tgt = tgt[c - h:c + h + 1, c - h:c + h + 1]
else:
    pad = (n - tgt.shape[0]) // 2
    tgt = np.pad(tgt, pad)
tgt = tgt / tgt.sum()
print("target: F106 on 0.05 grid, shape %s" % (tgt.shape,))

kern = create_matching_kernel(acs, tgt, window=TukeyWindow(alpha=0.3))
resid = float(np.abs(np.fft.fftshift(np.fft.ifft2(
    np.fft.fft2(acs) * np.fft.fft2(np.fft.ifftshift(kern)))).real - tgt).sum())
np.save(os.path.join(TILES, "acs2roman_f106_kernel.npy"), kern)
json.dump(dict(method="photutils create_matching_kernel, TukeyWindow(0.3)",
               source="mean of %d psf_bank_v2 extended ACS ePSFs" % len(srcs),
               target="mejiro F106_1_2044_2044_1_41.npy, clip>=0, renorm, "
                      "cubic x2.2 upsample to 0.05as",
               kernel_shape=list(kern.shape), kernel_sum=float(kern.sum()),
               conv_residual_L1=resid),
          open(os.path.join(TILES, "acs2roman_kernel_provenance.json"), "w"), indent=1)
print("kernel written: shape %s sum %.4f  conv-residual L1 %.4f"
      % (kern.shape, kern.sum(), resid))
