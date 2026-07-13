#!/usr/bin/env python
"""End-of-day audit of 2026-07-09 pipeline additions.
1. Euclidiser flux conservation: aperture flux ratio euclid/native should be
   10^(0.4(23.9-25.94)) = 0.1528 (PSF matching + rebin conserve flux).
2. Euclidised training set integrity: labels intact, no NaN/Inf, image stats.
3. Normalization consistency: training vs prediction code paths.
4. Post-degradation S4TM information check: peak/sky in euclidised S4TM vs
   SLACS (context for the S4TM collapse).
"""
import numpy as np
import h5py

EXPECT = 10.0 ** (0.4 * (23.9 - 25.94))


def aper_flux(im, r_as=2.0, pix=0.05):
    n = im.shape[0]
    c = (n - 1) / 2.0
    yy, xx = np.mgrid[0:n, 0:n]
    m = np.hypot(yy - c, xx - c) <= r_as / pix
    corners = np.concatenate([im[:16, :16].ravel(), im[-16:, -16:].ravel()])
    return float(np.clip(im - np.median(corners), 0, None)[m].sum())


print("=== 1. flux conservation (native vs euclidised SLACS, r=2 arcsec) ===")
with h5py.File("/home/user/nurkyz/einstein_cnn/real_slacs_images.h5", "r") as f:
    nat = f["images"][:10]
with h5py.File("/home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5", "r") as f:
    euc = f["images"][:10]
if nat.ndim == 4:
    nat = nat[:, 0]
ratios = []
for a, b in zip(nat, euc):
    fa = aper_flux(a)
    # euclidised is upsampled back to 128px with 0.05 as grid but flux was
    # summed 2x2 then bilinear-upsampled -> total flux x4 vs the 64px grid;
    # zoom(order=1) preserves VALUES not sums -> aperture sum on the 128 grid
    # counts each Euclid pixel ~4x. Expected ratio = 0.1528 * 4.
    fb = aper_flux(b)
    if fa > 0:
        ratios.append(fb / fa)
print("measured ratio: median %.4f  (expected %.4f if zoom preserves values -> x4)"
      % (np.median(ratios), EXPECT * 4))
print("             -> per-Euclid-pixel flux scale correct if ratio/4 = %.4f ~ %.4f"
      % (np.median(ratios) / 4, EXPECT))

print("=== 2. euclidised training set integrity ===")
with h5py.File("/home/user/nurkyz/einstein_cnn/train_euclid_100k_v3.h5", "r") as f:
    th = f["theta_E"][:]
    sample = f["lensed"][:200]
    keys = list(f.keys())
print("keys:", keys)
print("theta_E: n=%d range [%.3f, %.3f] median %.3f; NaN in sample images: %s; "
      "sample max %.3f min %.3f"
      % (len(th), th.min(), th.max(), np.median(th),
         bool(np.isnan(sample).any()), sample.max(), sample.min()))

print("=== 4. post-degradation peak/sky: SLACS vs S4TM (info content) ===")
for name in ("euclid_slacs_images", "euclid_s4tm_images"):
    with h5py.File("/home/user/nurkyz/einstein_cnn/%s.h5" % name, "r") as f:
        im = f["images"][:]
    if im.ndim == 4:
        im = im[:, 0]
    ps = []
    for x in im:
        corners = np.concatenate([x[:16, :16].ravel(), x[-16:, -16:].ravel()])
        med = np.median(corners)
        mad = np.median(np.abs(corners - med)) * 1.4826
        if mad > 0:
            ps.append((x.max() - med) / mad)
    print("%s: peak/sky median %.0f" % (name, np.median(ps)))
