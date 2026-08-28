"""Are the 'invisible-deflector' images high-noise or faint-deflector? And do the
diffuse-Re deflectors render visibly? Report per-image deflector mag / sky RMS /
peak-over-sky, and montage the highest-Re deflectors."""
import glob

import h5py
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

P = "/home/user/nurkyz/paltas_g5cosmos_fj7"
NAMED = [141, 170, 185, 213, 214]
with h5py.File(P + "/euclid.h5", "r") as f:
    comp = f["lensed"][:].astype(float)
    dmag = f["deflector_mag"][:]
    th = f["theta_E"][:]


def sky(im, s=14):
    c = np.concatenate([im[:s, :s].ravel(), im[:s, -s:].ravel(),
                        im[-s:, :s].ravel(), im[-s:, -s:].ravel()])
    return np.median(c), 1.4826 * np.median(np.abs(c - np.median(c)))


print("named 'invisible-deflector' images:  (real deflector VIS mag q75=22.1)")
print(" idx  defl_mag  sky_rms  peak/sky")
for i in NAMED:
    if i >= len(comp):
        continue
    sk, rms = sky(comp[i])
    cN = comp[i].shape[0] // 2
    core = comp[i][cN - 10:cN + 10, cN - 10:cN + 10].max()
    print("  %3d   %5.2f    %.4f    %5.1f" % (i, dmag[i], rms, (core - sk) / rms))
allsk = np.array([sky(im)[1] for im in comp])
print("\nsky RMS of named vs all: named median %.4f | all median %.4f"
      % (np.median([sky(comp[i])[1] for i in NAMED if i < len(comp)]), np.median(allsk)))
print("deflector mag of named:", np.round([dmag[i] for i in NAMED if i < len(comp)], 2))
print("all deflector mag q50/75/90 =",
      np.round(np.percentile(dmag, [50, 75, 90]), 2), "(real q75 22.1)")
faint = (dmag > 22.1).mean()
print("frac of ALL with deflector mag > real q75 22.1 (faint tail): %.2f" % faint)
