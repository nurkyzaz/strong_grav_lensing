"""Problem 1 diagnosis. Compute arc S/N the SAME way real Q1 does
(vis_max_lensed_source_signal_to_noise_ratio = max lensed-source pixel / sky
noise), on the ARC-ONLY euclidised render (sub_arcs), for all fj7 images. Split
by selection pass/fail, compare to real Q1 (7.6/10.5/15.4). Also dump a montage
of FAILED images to see if arcs are actually present."""
import glob
import os

import h5py
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

P = "/home/user/nurkyz/paltas_g5cosmos_fj7"
with h5py.File(P + "/euclid.h5", "r") as f:
    comp = f["lensed"][:].astype(float)
    th = f["theta_E"][:]
with h5py.File(P + "/euclid_sel.h5", "r") as f:
    sel_th = set(np.round(f["theta_E"][:], 6).tolist())
arc_files = sorted(glob.glob(P + "/sub_arcs/image_*.npy"))


def sky_rms(im, s=14):
    c = np.concatenate([im[:s, :s].ravel(), im[:s, -s:].ravel(),
                        im[-s:, :s].ravel(), im[-s:, -s:].ravel()])
    return 1.4826 * np.median(np.abs(c - np.median(c)))


n = min(len(comp), len(arc_files))
snr = np.zeros(n)
for i in range(n):
    arc = np.load(arc_files[i]).astype(float)
    rms = sky_rms(comp[i])
    snr[i] = np.nanmax(arc) / rms if rms > 0 else 0.0
sel = np.array([round(float(th[i]), 6) in sel_th for i in range(n)])


def q(x):
    return np.round(np.percentile(x, [25, 50, 75]), 1)


print("fj7 arc S/N (max arc-only / sky_rms; = real Q1 metric)  N=%d" % n)
print("  ALL      q25/50/75 =", q(snr))
print("  SELECTED q25/50/75 =", q(snr[sel]), " (N=%d)" % sel.sum())
print("  FAILED   q25/50/75 =", q(snr[~sel]), " (N=%d)" % (~sel).sum())
print("  REAL Q1  q25/50/75 =  7.6/10.5/15.4")
for t in (7.6, 10.5, 15.4):
    print("  frac of ALL with real-metric S/N > %.1f : %.2f  (N=%d)"
          % (t, (snr > t).mean(), (snr > t).sum()))

# montage of FAILED images (composite), asinh
fail_idx = np.where(~sel)[0][:30]
cols = 6
rows = (len(fail_idx) + cols - 1) // cols
fig, ax = plt.subplots(rows, cols, figsize=(cols * 2, rows * 2))
ax = np.atleast_1d(ax).ravel()
for a in ax:
    a.axis("off")
for j, i in enumerate(fail_idx):
    im = comp[i]
    a = np.arcsinh(np.clip(im - np.percentile(im, 40), 0, None) / (3 * sky_rms(im)))
    ax[j].imshow(a / max(a.max(), 1e-9), cmap="gray", origin="lower")
    ax[j].set_title("#%d snr=%.1f" % (i, snr[i]), fontsize=7)
fig.suptitle("fj7 FAILED-selection images (do they have arcs?)", fontsize=11)
fig.tight_layout()
fig.savefig(P + "/failed_montage.png", dpi=85)
print("saved failed_montage.png")
