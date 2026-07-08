#!/usr/bin/env python
"""
build_masked_slacs.py  -  remove the central lens-galaxy light from the RAW SLACS
cutouts WITHOUT subtraction, so the images resemble HSTempty's training distribution
(an arc on empty sky). Then test the HSTempty checkpoint on the result.

Method (no label leak -- mask radius is FIXED, not derived from theta_E):
  1. background bg = robust median of the outer ring (r > bg_r arcsec)
  2. subtract bg so the sky sits near 0 (HSTempty cutouts are median-subtracted)
  3. weight w(r): 0 inside r0, smooth cosine ramp to 1 over [r0, r0+taper]
  4. masked = w * (img - bg)   -> central galaxy replaced by ~0 sky, arc preserved

Writes masked_slacs.h5 (same keys as the input) + a masked_preview.png to eyeball.

Usage:
  python build_masked_slacs.py --in real_slacs_images.h5 --out masked_slacs.h5 \
       --r0 0.6 --taper 0.2 --pixscale 0.05
"""
import argparse
import numpy as np
import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def build_mask(H, r0_px, taper_px):
    cen = (H - 1) / 2.0
    yy, xx = np.mgrid[0:H, 0:H]
    r = np.hypot(xx - cen, yy - cen)
    w = np.clip((r - r0_px) / max(taper_px, 1e-6), 0, 1)
    w = 0.5 - 0.5 * np.cos(np.pi * w)        # smoothstep 0->1
    return r, w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="real_slacs_images.h5")
    ap.add_argument("--out", default="masked_slacs.h5")
    ap.add_argument("--r0", type=float, default=0.6, help="mask radius in arcsec (FIXED)")
    ap.add_argument("--taper", type=float, default=0.2, help="ramp width in arcsec")
    ap.add_argument("--bg_r", type=float, default=2.5, help="background estimated beyond this radius")
    ap.add_argument("--pixscale", type=float, default=0.05)
    ap.add_argument("--no_bgsub", action="store_true")
    args = ap.parse_args()

    with h5py.File(args.inp, "r") as h:
        imgs = np.asarray(h["images"]).astype("float32")
        names = np.asarray(h["names"]) if "names" in h else None
        extra = {k: np.asarray(h[k]) for k in h.keys() if k not in ("images",)}
    sh = imgs.shape
    arr = imgs[:, 0] if imgs.ndim == 4 else imgs
    H = arr.shape[1]

    r, w = build_mask(H, args.r0 / args.pixscale, args.taper / args.pixscale)
    outer = r > (args.bg_r / args.pixscale)

    out = np.empty_like(arr)
    for i, im in enumerate(arr):
        bg = np.median(im[outer]) if (not args.no_bgsub and outer.sum() > 20) else 0.0
        out[i] = w * (im - bg)

    out = out[:, None] if imgs.ndim == 4 else out
    with h5py.File(args.out, "w") as h:
        h.create_dataset("images", data=out.astype("float32"))
        for k, v in extra.items():
            h.create_dataset(k, data=v)
    print(f"wrote {args.out}  shape={out.shape}  r0={args.r0}\"  taper={args.taper}\"")

    # preview: 6 before/after pairs, asinh stretch
    arr_disp = arr if imgs.ndim != 4 else imgs[:, 0]
    out_disp = out[:, 0] if imgs.ndim == 4 else out
    n = min(6, len(arr_disp))
    fig, axes = plt.subplots(2, n, figsize=(2.6 * n, 5.4))
    for j in range(n):
        for row, (img, lab) in enumerate([(arr_disp[j], "raw"), (out_disp[j], "masked")]):
            ax = axes[row, j]
            s = np.percentile(np.abs(img), 99.5) + 1e-9
            ax.imshow(np.arcsinh(img / s), cmap="gray", origin="lower")
            ax.add_patch(plt.Circle(((H - 1) / 2, (H - 1) / 2),
                                    args.r0 / args.pixscale, fill=False, color="r", lw=1))
            nm = (names[j].decode() if (names is not None and isinstance(names[j], bytes))
                  else (str(names[j]) if names is not None else str(j)))
            ax.set_title(f"{nm} [{lab}]", fontsize=8)
            ax.axis("off")
    fig.suptitle(f"Lens-light masking (r0={args.r0}\"). Top raw, bottom masked.", fontsize=11)
    fig.tight_layout()
    fig.savefig("masked_preview.png", dpi=110)
    print("wrote masked_preview.png")


if __name__ == "__main__":
    main()
