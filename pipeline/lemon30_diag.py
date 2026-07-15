# Diagnostic three-stretch on suspect ACS cutouts (flagged from the preview
# gallery: 221501 looks empty/artifact-dominated, 001426 looks inverted,
# 140339 and 122332 look off-center) before trusting the fetch.
import h5py
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

f = h5py.File("/home/user/nurkyz/einstein_cnn/real_LEMONACS_images.h5", "r")
names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]]
imgs = f["images"][:]

suspect = ["ACS_221501p12M135822p9", "ACS_001426p26M302255p9",
           "ACS_140339p94P541633p3", "ACS_122332p64M123940p3"]
fig, axes = plt.subplots(3, len(suspect), figsize=(5 * len(suspect), 13))
for j, nm in enumerate(suspect):
    i = names.index(nm)
    im = np.squeeze(imgs[i]).astype(float)
    print("%s: min %.4g max %.4g median %.4g std %.4g  frac_negative %.2f  frac_zero %.2f"
          % (nm, im.min(), im.max(), np.median(im), im.std(),
             (im < 0).mean(), (im == 0).mean()))
    sky = np.median(im[:12, :12])
    rms = max(1.4826 * np.median(np.abs(im[:12, :12] - sky)), 1e-9)
    for r, (stretch, dat) in enumerate((
            ("linear", im),
            ("pct1-99", np.clip(im, np.percentile(im, 1), np.percentile(im, 99))),
            ("asinh", np.arcsinh((im - sky) / max(rms, 1e-9))))):
        axes[r][j].imshow(dat, origin="lower", cmap="gray")
        axes[r][j].axis("off")
        if r == 0:
            axes[r][j].set_title(nm, fontsize=8)
plt.suptitle("Diagnostic 3-stretch: suspect LEMON ACS cutouts")
plt.tight_layout()
plt.savefig("/home/user/nurkyz/cosmos_acs/q1_slde/lemon30_acs_diag.png", dpi=120)
print("wrote lemon30_acs_diag.png")
