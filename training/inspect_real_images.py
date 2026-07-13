#!/usr/bin/env python
"""
inspect_real_images.py
Report exactly what is inside the real-lens HDF5 file(s) on the cluster, so you can
answer precisely: is there a noise map? what's the FOV / pixel scale? what units?

Usage:
    python inspect_real_images.py                       # auto-find real_*slacs*.h5 here
    python inspect_real_images.py real_slacs_images.h5  # a specific file
    python inspect_real_images.py *.h5
"""
import sys
import os
import glob
import numpy as np
import h5py

NOISE_HINTS = ("noise", "weight", "wht", "sigma", "err", "var", "ivar",
               "rms", "invvar", "inv_var")
PIX_HINTS = ("pixscale", "pixel_scale", "pix_scale", "cdelt", "pixscale_arcsec")
FOV_HINTS = ("box_arcsec", "fov", "box", "fov_arcsec")


def dec(v):
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    if isinstance(v, np.ndarray) and v.dtype.kind in ("S", "O"):
        return [dec(x) for x in v[:3]]
    return v


def walk(h5, prefix=""):
    out = []
    for k in h5.keys():
        obj = h5[k]
        path = f"{prefix}/{k}".lstrip("/")
        if isinstance(obj, h5py.Group):
            out += walk(obj, path)
        else:
            out.append((path, obj))
    return out


def summarize(path):
    print("=" * 72)
    print("FILE:", path, f"  ({os.path.getsize(path)/1e6:.2f} MB)")
    with h5py.File(path, "r") as f:
        if dict(f.attrs):
            print("root attrs:", {k: dec(v) for k, v in f.attrs.items()})

        dsets = walk(f)
        noise_keys, img_key, pix_val, fov_val = [], None, None, None

        print("datasets:")
        for p, o in dsets:
            print(f"  {p:22s} shape={str(o.shape):22s} dtype={o.dtype}")
            kl = p.lower()
            if any(h in kl for h in NOISE_HINTS):
                noise_keys.append(p)
            if (img_key is None) and ("image" in kl or len(o.shape) == 4):
                img_key = p
            if (pix_val is None) and any(h in kl for h in PIX_HINTS):
                try:
                    pix_val = float(np.array(o).ravel()[0])
                except Exception:
                    pass
            if (fov_val is None) and any(h in kl for h in FOV_HINTS):
                try:
                    fov_val = float(np.array(o).ravel()[0])
                except Exception:
                    pass

        # pixscale / fov can also live in attrs
        for k, v in f.attrs.items():
            kl = k.lower()
            if pix_val is None and any(h in kl for h in PIX_HINTS):
                pix_val = float(v)
            if fov_val is None and any(h in kl for h in FOV_HINTS):
                fov_val = float(v)

        # image stats
        N = H = W = None
        if img_key is not None:
            arr = np.asarray(f[img_key])
            if arr.ndim == 4:
                N, _, H, W = arr.shape
            elif arr.ndim == 3:
                N, H, W = arr.shape
            finite = np.isfinite(arr)
            vals = arr[finite]
            print(f"\nimage key '{img_key}': N={N} H={H} W={W}")
            print(f"  value range [{vals.min():.4g}, {vals.max():.4g}]  "
                  f"median {np.median(vals):.4g}  mean {vals.mean():.4g}")
            print(f"  NaN/inf pixels: {(~finite).sum()}")
            unit = ("normalized [-1,1]-ish" if vals.min() >= -1.5 and vals.max() <= 1.5
                    else "raw flux (e-/s)-like" if vals.max() > 2 else "unclear")
            print(f"  -> looks like: {unit}")

        # labels / names
        for cand in ("theta_E_pub", "theta_E", "thetaE", "theta"):
            if cand in f:
                t = np.asarray(f[cand], float)
                print(f"\ntheta labels '{cand}': N={len(t)} "
                      f"median {np.median(t):.2f}\" range [{t.min():.2f},{t.max():.2f}]\"")
                break
        for cand in ("names", "name", "ids"):
            if cand in f:
                print(f"names sample: {dec(np.asarray(f[cand]))}")
                break

        if pix_val is None and fov_val is not None and W:
            pix_val = fov_val / W
        if fov_val is None and pix_val is not None and W:
            fov_val = pix_val * W

        # ---- the line that answers Brian ----
        print("\n" + "-" * 72)
        print("ANSWERS:")
        print(f"  N cutouts        : {N}")
        print(f"  cutout grid      : {H} x {W} px" if H else "  cutout grid      : ?")
        print(f"  pixel scale      : {pix_val:.4f} arcsec/px" if pix_val else
              "  pixel scale      : NOT stored in file")
        print(f"  field of view    : {fov_val:.2f} arcsec (square)" if fov_val else
              "  field of view    : NOT stored in file")
        print(f"  noise/weight map : {'YES -> ' + str(noise_keys) if noise_keys else 'NO (not in this file)'}")
        print("-" * 72)


def main():
    args = sys.argv[1:]
    if not args:
        args = sorted(glob.glob("real_*slacs*.h5")) or sorted(glob.glob("*.h5"))
    if not args:
        sys.exit("no .h5 files found here -- pass a path explicitly")
    for p in args:
        for g in sorted(glob.glob(p)):
            summarize(g)


if __name__ == "__main__":
    main()
