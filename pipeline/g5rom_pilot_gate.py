#!/usr/bin/env python
"""G5c pilot gate: romanised pilot images vs the measured Rung 0 F106
targets. PASS/FAIL per stat + suggested FLUX_FACTOR + three-stretch
previews. Targets measured 2026-07-14 on 400 Rung 0 systems (raw grid):
sky 0.454 DN/s, skyRMS 0.0205, peak/sky q10/50/90 = 7/32/149. NOTE the
pilot images are on the 128px zoomed grid (same convention as the Path A
training data), so we compare against Rung 0 stats recomputed on that SAME
grid here — apples to apples."""
import os

import h5py
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

P = os.path.expanduser("~/paltas_g5rom_pilot")
EC = os.path.expanduser("~/einstein_cnn")


def stats(im):
    k = 12
    c = np.concatenate([im[:k, :k].ravel(), im[:k, -k:].ravel(),
                        im[-k:, :k].ravel(), im[-k:, -k:].ravel()])
    sky = np.median(c)
    rms = 1.4826 * np.median(np.abs(c - sky))
    return sky, rms, (np.percentile(im, 99.9) - sky) / max(rms, 1e-9)


def dist(fn, key, n=400):
    with h5py.File(fn, "r") as f:
        ims = f[key][:n]
    return np.array([stats(np.squeeze(im).astype(float)) for im in ims])


# Rung 0 reference ON THE SAME 128px zoomed grid (Path A training file)
ref = dist(os.path.join(EC, "train_rung0_f106.h5"), "lensed")
pil = dist(os.path.join(P, "roman_pilot.h5"), "lensed")
print("%-12s %10s %10s %22s" % ("", "sky med", "skyRMS med", "peak/sky q10/50/90"))
for tag, d in (("RUNG0-128", ref), ("PILOT", pil)):
    print("%-12s %10.4f %10.4f %8.0f %6.0f %6.0f"
          % (tag, np.median(d[:, 0]), np.median(d[:, 1]),
             *np.percentile(d[:, 2], [10, 50, 90])))
ok_sky = 0.8 < np.median(pil[:, 0]) / np.median(ref[:, 0]) < 1.25
ok_rms = 0.7 < np.median(pil[:, 1]) / np.median(ref[:, 1]) < 1.4
r_ps = np.median(pil[:, 2]) / np.median(ref[:, 2])
ok_ps = 0.5 < r_ps < 2.0
print("[%s] sky level   (ratio %.2f)" % ("PASS" if ok_sky else "FAIL",
                                          np.median(pil[:, 0]) / np.median(ref[:, 0])))
print("[%s] sky RMS     (ratio %.2f)" % ("PASS" if ok_rms else "FAIL",
                                          np.median(pil[:, 1]) / np.median(ref[:, 1])))
print("[%s] peak/sky    (ratio %.2f) -> suggested LF_ROM_FLUX multiplier ~ %.2f"
      % ("PASS" if ok_ps else "FAIL", r_ps, 1.0 / max(r_ps, 1e-9)))

with h5py.File(os.path.join(P, "roman_pilot.h5"), "r") as f:
    ims = f["lensed"][:12]
fig, axes = plt.subplots(3, 12, figsize=(24, 7))
for j, im in enumerate(ims):
    im = np.squeeze(im).astype(float)
    sky = np.median(im[:12, :12])
    rms = max(np.std(im[:12, :12]), 1e-9)
    for r, dat in enumerate((im, np.clip(im, np.percentile(im, 1), np.percentile(im, 99)),
                             np.arcsinh((im - sky) / rms))):
        axes[r][j].imshow(dat, origin="lower", cmap="gray")
        axes[r][j].axis("off")
plt.suptitle("G5c Path-B pilot: romanised GEN4 renders (linear/pct/asinh)")
plt.tight_layout()
plt.savefig(os.path.join(P, "g5rom_pilot_preview.png"), dpi=110)
print("preview written: %s" % os.path.join(P, "g5rom_pilot_preview.png"))
