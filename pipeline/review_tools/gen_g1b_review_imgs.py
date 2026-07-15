# Per-stamp asinh thumbnails for the G1b deflector library (779 stamps) +
# manifest.json for the HTML grid reviewer.
import json
import os

import h5py
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fn = os.path.expanduser("~/einstein_cnn/real_lrgdefl2b_images_256.h5")
OUT = os.path.expanduser("~/cosmos_acs/tiles/g1b_review_imgs")
os.makedirs(OUT, exist_ok=True)

f = h5py.File(fn, "r")
key = "images" if "images" in f else list(f.keys())[0]
ims = f[key]
names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]]
n = len(names)
print("N stamps:", n)

manifest = []
for i, nm in enumerate(names):
    im = np.squeeze(ims[i]).astype(float)
    sky = np.median(np.concatenate([im[:16, :16].ravel(), im[-16:, -16:].ravel()]))
    rms = max(1.4826 * np.median(np.abs(im[:16, :16] - sky)), 1e-9)
    fig, ax = plt.subplots(figsize=(1.6, 1.6))
    ax.imshow(np.arcsinh((im - sky) / (3 * rms)), origin="lower", cmap="gray")
    ax.axis("off")
    fn_out = "%s.png" % nm
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig(os.path.join(OUT, fn_out), dpi=70)
    plt.close()
    manifest.append(dict(id=nm, img=fn_out))
    if i % 100 == 0:
        print("  %d/%d" % (i, n), flush=True)

json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"))
print("wrote manifest.json (%d entries) to %s" % (len(manifest), OUT))
