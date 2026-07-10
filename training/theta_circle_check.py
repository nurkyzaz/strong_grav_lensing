#!/usr/bin/env python
"""Overlay the TRUE theta_E circle on the 8 sim panels shown in
real_vs_train_euclid_reb.png (Nurkyz: 'one arc looks misplaced'). Same
diagnostic that settled #81435: the label IS the ray-tracing input, so the
arc must sit on the circle (up to the <=0.1" mass/light jitter); a feature
off the circle is a companion, not the arc."""
import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PIX = 0.05
IDX = [83086, 34563, 12048, 30660, 47344, 13298, 82608, 80643]
F = "/home/user/nurkyz/einstein_cnn/train_euclid_reb_100k.h5"

with h5py.File(F, "r") as f:
    imgs = np.stack([f["lensed"][i] for i in IDX])
    th = np.array([f["theta_E"][i] for i in IDX])

fig, axes = plt.subplots(2, 4, figsize=(16, 8.5))
for ax, img, t, i in zip(axes.ravel(), imgs, th, IDX):
    sky = np.median(np.abs(img - np.median(img))) * 1.4826
    ax.imshow(np.arcsinh(img / max(sky, 1e-9)), cmap="gray", origin="lower")
    c = img.shape[0] / 2 - 0.5
    for r_off, col in ((0.0, "cyan"),):
        circ = plt.Circle((c, c), t / PIX, fill=False, color=col, lw=1.2, ls="--")
        ax.add_patch(circ)
    ax.set_title("SIM #%d  theta_E=%.2f\" (circle)" % (i, t), fontsize=10)
    ax.axis("off")
fig.suptitle("theta_E-circle overlay on the 8 displayed REB sims — arc must lie on the dashed circle", fontsize=12)
fig.tight_layout()
fig.savefig("/home/user/nurkyz/einstein_cnn/theta_circle_check_REB.png", dpi=130)
print("wrote theta_circle_check_REB.png")
