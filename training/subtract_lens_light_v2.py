#!/usr/bin/env python
"""
subtract_lens_light_v2.py  -- FREE CENTRE + core mask.
v1 fixed the Sersic centre at the image centre; the real lens is offset 1-3 px, which
left a bright/dark DIPOLE (+ an oversubtracted core dot) in every residual. v2 fits the
centre (cx,cy) as free parameters and zeroes a tiny central disk the PSF core corrupts.
Output: real_slacs_residual_v2.h5 + residual_v2_previews/.
"""
import argparse, os, numpy as np, h5py
from scipy.optimize import least_squares
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt


def q_phi_from_e(e1, e2):
    e = min(np.hypot(e1, e2), 0.95); return (1 - e) / (1 + e), 0.5 * np.arctan2(e2, e1)


def sersic(p, xx, yy):
    logIe, Re, n, e1, e2, bkg, cx, cy = p
    q, phi = q_phi_from_e(e1, e2)
    X = xx - cx; Y = yy - cy
    Xr = X * np.cos(phi) + Y * np.sin(phi); Yr = -X * np.sin(phi) + Y * np.cos(phi)
    r = np.sqrt(q * Xr**2 + Yr**2 / q) + 1e-6
    bn = 2 * n - 1/3 + 4/(405 * n) + 46/(25515 * n**2)
    return np.exp(logIe) * np.exp(-bn * ((r / Re)**(1 / n) - 1)) + bkg


def centroid_inner(img, rad=10):
    H, W = img.shape; yy, xx = np.indices(img.shape); c = (H - 1) / 2
    r = np.hypot(xx - c, yy - c); m = np.where(r < rad, np.clip(img, 0, None), 0.0)
    s = m.sum() + 1e-9; return (xx * m).sum() / s, (yy * m).sum() / s


def fit_and_subtract(img, n_iter=4, clip=2.5, core_mask=3.0):
    H, W = img.shape; yy, xx = np.indices(img.shape).astype("float64")
    cx0, cy0 = centroid_inner(img)
    peak = np.percentile(img[np.isfinite(img)], 99.5)
    p = [np.log(max(peak, 1e-3)), 8.0, 4.0, 0.0, 0.0, float(np.median(img)), cx0, cy0]
    lo = [np.log(1e-4), 2.0, 0.8, -0.7, -0.7, -abs(peak), cx0 - 5, cy0 - 5]
    hi = [np.log(peak * 10 + 1), 45, 8, 0.7, 0.7, abs(peak) + 1, cx0 + 5, cy0 + 5]
    mask = np.isfinite(img)
    for _ in range(n_iter):
        m = mask.ravel()
        try:
            sol = least_squares(lambda q: (sersic(q, xx, yy) - img).ravel()[m], p,
                                bounds=(lo, hi), method="trf", max_nfev=500)
            p = sol.x
        except Exception:
            break
        resid = img - sersic(p, xx, yy)
        s = np.std(resid[mask]); mask = np.isfinite(img) & (resid < clip * s)
    resid = img - sersic(p, xx, yy)
    rcen = np.hypot(xx - p[6], yy - p[7])
    resid[rcen < core_mask] = 0.0          # kill the PSF-core dot
    return resid


def asinh_disp(img, soft=0.02, lo=1.0, hi=99.7):
    fin = img[np.isfinite(img)]
    if fin.size == 0: return np.zeros_like(img)
    vlo, vhi = np.percentile(fin, [lo, hi])
    x = np.clip((img - vlo) / max(vhi - vlo, 1e-9), 0, None)
    x = np.arcsinh(x / soft); h2 = np.percentile(x[np.isfinite(x)], 99.7)
    return np.nan_to_num(np.clip(x, 0, h2) / (h2 + 1e-9))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", default="real_slacs_images.h5")
    ap.add_argument("--out", default="real_slacs_residual_v2.h5")
    args = ap.parse_args()
    os.makedirs("residual_v2_previews", exist_ok=True)
    with h5py.File(args.images, "r") as f:
        images = f["images"][:]; names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]]
        theta_pub = f["theta_E_pub"][:]; q_pub = f["q_pub"][:] if "q_pub" in f else np.full(len(images), np.nan)
        attrs = dict(f.attrs)
    res = np.zeros_like(images)
    for i in range(len(images)):
        r = fit_and_subtract(images[i, 0]); res[i, 0] = r
        fig, ax = plt.subplots(1, 2, figsize=(5, 2.6))
        ax[0].imshow(asinh_disp(images[i, 0]), origin="lower", cmap="gray"); ax[0].set_title("raw", fontsize=7)
        ax[1].imshow(asinh_disp(r), origin="lower", cmap="gray"); ax[1].set_title("lens-sub v2", fontsize=7)
        for a in ax: a.set_xticks([]); a.set_yticks([])
        fig.suptitle(names[i], fontsize=8); fig.tight_layout()
        fig.savefig(f"residual_v2_previews/{names[i]}.png", dpi=110); plt.close(fig)
    with h5py.File(args.out, "w") as f:
        f.create_dataset("images", data=res.astype("float32"))
        f.create_dataset("names", data=np.array(names, dtype="S32"))
        f.create_dataset("theta_E_pub", data=theta_pub.astype("float32"))
        f.create_dataset("q_pub", data=q_pub.astype("float32"))
        for k, v in attrs.items(): f.attrs[k] = v
    print(f"wrote {args.out} + residual_v2_previews/. EYEBALL: is the dipole gone, arc cleaner?")


if __name__ == "__main__":
    main()
