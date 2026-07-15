# Combine the per-lens preview PNGs (already asinh-stretched, red cross at
# centre, from fetch_real_lens_images.py) into 3 gallery pages for a quick
# visual pass before trusting the fetch.
import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

EC = os.path.expanduser("~/einstein_cnn/previews")
OUT = os.path.expanduser("~/cosmos_acs/q1_slde")  # reuse an inspection dir

for sub in ("lemoneel", "lemoncosmos", "lemonacs"):
    files = sorted(glob.glob(os.path.join(EC, sub, "*.png")))
    n = len(files)
    cols = min(n, 7)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(3 * cols, 3 * rows))
    axes = axes.reshape(rows, cols) if rows > 1 else axes.reshape(1, cols)
    for i, fn in enumerate(files):
        r, c = divmod(i, cols)
        img = mpimg.imread(fn)
        axes[r][c].imshow(img)
        axes[r][c].axis("off")
        axes[r][c].set_title(os.path.basename(fn).replace(".png", ""), fontsize=7)
    for i in range(n, rows * cols):
        r, c = divmod(i, cols)
        axes[r][c].axis("off")
    plt.suptitle("%s pilot30 fetch previews (N=%d)" % (sub, n))
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "lemon30_gallery_%s.png" % sub), dpi=110)
    plt.close()
    print("wrote lemon30_gallery_%s.png (%d systems)" % (sub, n))
