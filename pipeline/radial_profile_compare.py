#!/usr/bin/env python
"""Compare azimuthally-averaged radial profiles of sim-deflector light vs real
SLACS deflectors.

Panels 1-2 (peak-normalized, linear/log): profile SHAPE. If sim core is too
peaked / wings deficient vs real -> library construction artifact (128px
corner-bg subtraction strips de Vauc wings) -> P2 (256px refetch) fixes it.
Panel 3 (sky-RMS-normalized, ABSOLUTE, log): brightness realism. If sim sits
above real at all radii -> deflector over-bright in-frame (the P1 total-flux
bug, fixed by P1b aperture scaling). This panel moves with the scaling; the
peak-normed panels move with the library.
"""
import argparse
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--sim", required=True, help="pilot h5 (dataset 'lensed')")
ap.add_argument("--real", default="/home/user/nurkyz/einstein_cnn/real_slacs_images.h5")
ap.add_argument("--lib", default="/home/user/nurkyz/cosmos_acs/tiles/deflector_stamps_lrg_v3.h5")
ap.add_argument("--label", default="SIM", help="legend label for the sim curve")
ap.add_argument("--out", required=True)
args = ap.parse_args()


def radial_profile(img, c=64):
    n = img.shape[0]
    yy, xx = np.mgrid[0:n, 0:n]
    r = np.hypot(yy - c, xx - c).astype(int)
    prof = np.array([img[r == k].mean() if (r == k).any() else 0.0 for k in range(64)])
    return prof


def sky_stats(img):
    corners = np.concatenate([img[:16, :16].ravel(), img[-16:, -16:].ravel(),
                              img[:16, -16:].ravel(), img[-16:, :16].ravel()])
    med = np.median(corners)
    mad = np.median(np.abs(corners - med)) * 1.4826
    return med, mad


def norm_prof(img):
    med, _ = sky_stats(img)
    p = radial_profile(img - med)
    pk = p[:5].max()
    return p / pk if pk > 0 else p


def abs_prof(img):
    """Radial profile in units of the image's own sky RMS (absolute realism)."""
    med, mad = sky_stats(img)
    if not np.isfinite(mad) or mad <= 0:
        return None
    return radial_profile(img - med) / mad


with h5py.File(args.sim, "r") as f:
    sim = f["lensed"][:]
with h5py.File(args.real, "r") as f:
    real = f["images"][:] if "images" in f else f[list(f.keys())[0]][:]
if real.ndim == 4:
    real = real[:, 0]
with h5py.File(args.lib, "r") as f:
    lib = f["stamps"][:]
if lib.shape[1] != sim.shape[1]:
    c0 = (lib.shape[1] - sim.shape[1]) // 2
    lib = lib[:, c0:c0 + sim.shape[1], c0:c0 + sim.shape[1]]

sim_p = np.median([norm_prof(x) for x in sim], axis=0)
real_p = np.median([norm_prof(x) for x in real], axis=0)
lib_p = np.median([norm_prof(x) for x in lib], axis=0)
sim_a = np.median([q for q in (abs_prof(x) for x in sim) if q is not None], axis=0)
real_a = np.median([q for q in (abs_prof(x) for x in real) if q is not None], axis=0)

rr = np.arange(64) * 0.05
fig, ax = plt.subplots(1, 3, figsize=(18, 5))
for a in ax[:2]:
    a.plot(rr, real_p, "k-", lw=2, label="REAL SLACS (median)")
    a.plot(rr, sim_p, "r-", lw=2, label=args.label + " (median)")
    a.plot(rr, lib_p, "b--", lw=1.2, label="raw lib stamp (median)")
    a.axvspan(15 * 0.05, 45 * 0.05, color="orange", alpha=0.12, label="mid-radius")
    a.set_xlabel("radius [arcsec]")
    a.legend(fontsize=8)
ax[0].set_ylabel("peak-normalized flux")
ax[0].set_title("SHAPE (peak-normed, linear) -- library-driven")
ax[1].set_yscale("log")
ax[1].set_ylim(1e-4, 1.5)
ax[1].set_title("SHAPE (peak-normed, log)")
ax[2].plot(rr, real_a, "k-", lw=2, label="REAL SLACS (median)")
ax[2].plot(rr, sim_a, "r-", lw=2, label=args.label + " (median)")
ax[2].set_yscale("log")
ax[2].set_xlabel("radius [arcsec]")
ax[2].set_ylabel("flux / sky RMS")
ax[2].set_title("BRIGHTNESS (sky-normed, log) -- scaling-driven")
ax[2].legend(fontsize=8)
fig.suptitle("Deflector radial profile: sim vs real")
fig.tight_layout()
fig.savefig(args.out, dpi=110)

for label, p in [("REAL", real_p), (args.label, sim_p), ("raw lib", lib_p)]:
    print("%-12s peak-normed  r=0.25=%.3f  r=0.5=%.3f  r=1.0=%.3f  r=1.5=%.3f  r=2.0=%.3f"
          % (label, p[5], p[10], p[20], p[30], p[40]))
for label, p in [("REAL", real_a), (args.label, sim_a)]:
    print("%-12s sky-normed   r=0.25=%.1f  r=0.5=%.1f  r=1.0=%.1f  r=1.5=%.1f  r=2.0=%.1f"
          % (label, p[5], p[10], p[20], p[30], p[40]))
print("wrote " + args.out)
