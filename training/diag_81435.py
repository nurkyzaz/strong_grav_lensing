#!/usr/bin/env python
"""Diagnose train image #81435 (Nurkyz: 'arc seems misplaced').
1. Provenance: theta_E, arc_snr, arc_extent, shard, deflector, backdrop.
2. Azimuthal-residual map: radius of the brightest extended feature vs theta_E
   (arc should sit near theta_E, modulated by the +-0.25" source offset:
   allowed arc radii roughly [theta_E-0.25, theta_E+0.25] + PSF width).
3. Zoomed panel with theta_E circle overlay saved for visual check.
Also: same measurement for 200 RANDOM train images -> population statistic
(is the arc-radius vs theta_E relation healthy overall, or is 81435 an outlier
or a systemic bug?).
"""
import numpy as np
import h5py
from scipy.ndimage import gaussian_filter, label
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

H5 = "/home/user/nurkyz/einstein_cnn/train_euclid_sel_100k.h5"
IDX = 81435
PIX = 0.05

with h5py.File(H5, "r") as f:
    img = f["lensed"][IDX].astype("float64")
    th = float(f["theta_E"][IDX])
    snr = float(f["arc_snr"][IDX])
    ext = float(f["arc_extent"][IDX])
    shard = int(f["shard"][IDX])
    dmag = float(f["deflector_mag"][IDX]) if "deflector_mag" in f else np.nan
    n_all = f["lensed"].shape[0]

n = img.shape[0]
c = n // 2
yy, xx = np.mgrid[0:n, 0:n]
rr = np.hypot(yy - c, xx - c)
rbin = rr.astype(int)


def arc_feature_radius(im):
    s = gaussian_filter(im, 1.5)
    prof = np.zeros(rbin.max() + 1)
    for k in range(rbin.max() + 1):
        m = rbin == k
        if m.any():
            prof[k] = np.median(s[m])
    resid = s - prof[rbin]
    out = rr > 2.6 / PIX
    mad = np.median(np.abs(resid[out] - np.median(resid[out]))) * 1.4826
    ann = (rr >= 0.3 / PIX) & (rr <= 2.6 / PIX)
    det = (resid > 3.0 * mad) & ann
    lab, nl = label(det)
    best, bestr = 0.0, np.nan
    for i in range(1, nl + 1):
        m = lab == i
        if m.sum() >= 150:
            pk = resid[m].max()
            if pk > best:
                best = pk
                # flux-weighted radius of the feature
                bestr = float((rr[m] * resid[m]).sum() / resid[m].sum()) * PIX
    return bestr, best / mad if mad > 0 else np.nan


r81, p81 = arc_feature_radius(img)
print("IMG %d: theta_E=%.2f arc_snr=%.1f extent=%.0f shard=%d defl_mag=%.2f"
      % (IDX, th, snr, ext, shard, dmag))
print("brightest extended feature: radius %.2f arcsec (prominence %.1f)"
      % (r81, p81))
print("allowed arc-radius band for theta_E=%.2f with source offset 0.25: "
      "[%.2f, %.2f] (+~0.16 PSF)" % (th, th - 0.25, th + 0.25))

# population check on 200 random images
rng = np.random.default_rng(3)
idxs = np.sort(rng.choice(n_all, 200, replace=False))
with h5py.File(H5, "r") as f:
    ths = f["theta_E"][idxs]
    imgs = f["lensed"][idxs]
devs = []
for t, im in zip(ths, imgs):
    r, _ = arc_feature_radius(im.astype("float64"))
    if np.isfinite(r):
        devs.append(r - t)
devs = np.array(devs)
print("population (N=%d valid): feature_radius - theta_E: median %+.2f\" "
      "16-84%% [%+.2f, %+.2f]; |dev|>0.5\": %.0f%%"
      % (len(devs), np.median(devs), np.percentile(devs, 16),
         np.percentile(devs, 84), 100 * (np.abs(devs) > 0.5).mean()))

# zoomed overlay
corners = np.concatenate([img[:16, :16].ravel(), img[-16:, -16:].ravel()])
med = np.median(corners)
mad = np.median(np.abs(corners - med)) * 1.4826
fig, ax = plt.subplots(figsize=(6, 6))
ax.imshow(np.arcsinh((img - med) / mad), cmap="gray", origin="lower")
for rad, colr, lbl in ((th, "cyan", "theta_E"),
                       (th - 0.25, "yellow", None), (th + 0.25, "yellow", None)):
    ax.add_patch(plt.Circle((c, c), rad / PIX, fill=False, color=colr,
                            lw=1.2, ls="--" if colr == "yellow" else "-"))
ax.set_title("train #%d  theta_E=%.2f  arc_snr=%.1f (cyan=theta_E, "
             "yellow=+-0.25 source-offset band)" % (IDX, th, snr), fontsize=9)
ax.axis("off")
fig.tight_layout()
fig.savefig("/home/user/nurkyz/cosmos_acs/tiles/diag_81435.png", dpi=120)
print("wrote diag_81435.png")
