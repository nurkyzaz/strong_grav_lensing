# Per-lens 3-stretch review thumbnails for the LEMON Q1b set (all 30, incl.
# the auto-flagged bad ACS cutout, for independent confirmation). Also
# writes a manifest.json for the HTML reviewer.
import json
import os

import h5py
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.expanduser("~/cosmos_acs/q1_slde/lemon_review_imgs")
os.makedirs(OUT, exist_ok=True)
EC = os.path.expanduser("~/einstein_cnn")

AUTOFLAG = {"ACS_221501p12M135822p9": "auto-flag: 62% zero-pixel field, looks like chip gap"}

manifest = []
for sub, label in (("EEL", "EEL"), ("COSMOS", "COSMOS"), ("ACS", "ACS")):
    with h5py.File(os.path.join(EC, "real_LEMON%s_images.h5" % sub), "r") as f:
        names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]]
        imgs = f["images"][:]
        gt = f["theta_E_pub"][:] if "theta_E_pub" in f else [0.0] * len(names)
    for i, nm in enumerate(names):
        im = np.squeeze(imgs[i]).astype(float)
        sky = np.median(im[:12, :12])
        rms = max(1.4826 * np.median(np.abs(im[:12, :12] - sky)), 1e-9)
        fig, axes = plt.subplots(1, 3, figsize=(9, 3.1))
        for ax, (stretch, dat) in zip(axes, (
                ("linear", im),
                ("pct1-99", np.clip(im, np.percentile(im, 1), np.percentile(im, 99))),
                ("asinh", np.arcsinh((im - sky) / rms)))):
            ax.imshow(dat, origin="lower", cmap="gray")
            ax.axis("off")
            ax.set_title(stretch, fontsize=8)
        plt.tight_layout(pad=0.3)
        fn = "%s.png" % nm
        plt.savefig(os.path.join(OUT, fn), dpi=95)
        plt.close()
        manifest.append(dict(id=nm, subsample=label, img=fn,
                             gt=float(gt[i]), autoflag=AUTOFLAG.get(nm, "")))
    print("%s: %d images" % (sub, len(names)))

json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
print("wrote manifest.json (%d entries) to %s" % (len(manifest), OUT))
