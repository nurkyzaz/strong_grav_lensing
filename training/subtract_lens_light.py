#!/usr/bin/env python
"""
subtract_lens_light.py
----------------------
Reveal the lensed arc in real cutouts by fitting & subtracting the smooth lens galaxy
(2D elliptical Sersic, centre = image centre), with the ARC MASKED OUT via iterative
sigma-clipping of positive residuals. Self-contained (numpy+scipy+h5py), same style as
ellipticity_labels.py. NOT a substitute for GALFIT/YattaLens -- a pragmatic first pass.

Output:
  real_slacs_residual.h5   (key 'images' = residual [N,1,128,128], carries names/labels/attrs)
  residual_previews/<name>.png  (asinh; EYEBALL these -- did the arc appear?)

Then run the CLEAN arc-only model on the residual:
  python test_real_slacs.py --ckpt einstein_cnn_multi_clean.pt \
         --images real_slacs_residual.h5 --flux_norm peak1 --out_prefix real_sub
"""
import argparse, os, numpy as np, h5py
from scipy.optimize import least_squares
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt


def q_phi_from_e(e1, e2):
    e = min(np.hypot(e1, e2), 0.95)
    return (1.0 - e) / (1.0 + e), 0.5 * np.arctan2(e2, e1)


def sersic(p, X, Y):
    logIe, Re, n, e1, e2, bkg = p
    q, phi = q_phi_from_e(e1, e2)
    Xr = X * np.cos(phi) + Y * np.sin(phi)
    Yr = -X * np.sin(phi) + Y * np.cos(phi)
    r = np.sqrt(q * Xr**2 + Yr**2 / q) + 1e-6
    bn = 2 * n - 1.0 / 3.0 + 4.0 / (405 * n) + 46.0 / (25515 * n**2)
    return np.exp(logIe) * np.exp(-bn * ((r / Re)**(1.0 / n) - 1.0)) + bkg


def fit_and_subtract(img, n_iter=4, clip=2.5):
    H, W = img.shape
    cx = cy = (H - 1) / 2.0
    yy, xx = np.indices(img.shape)
    X = (xx - cx).astype("float64"); Y = (yy - cy).astype("float64")
    peak = np.percentile(img[np.isfinite(img)], 99.5)
    p0 = [np.log(max(peak, 1e-3)), 8.0, 4.0, 0.0, 0.0, float(np.median(img))]
    lo = [np.log(1e-4), 2.0, 0.8, -0.7, -0.7, -abs(peak)]
    hi = [np.log(peak * 10 + 1), 45.0, 8.0, 0.7, 0.7, abs(peak) + 1]
    mask = np.isfinite(img)
    p = p0
    for _ in range(n_iter):
        m = mask.ravel()
        try:
            sol = least_squares(lambda q: (sersic(q, X, Y) - img).ravel()[m], p,
                                bounds=(lo, hi), method="trf", max_nfev=400)
            p = sol.x
        except Exception:
            break
        resid = img - sersic(p, X, Y)
        s = np.std(resid[mask])
        mask = np.isfinite(img) & (resid < clip * s)   # drop positive (arc) outliers
    return img - sersic(p, X, Y)


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
    ap.add_argument("--out", default="real_slacs_residual.h5")
    args = ap.parse_args()
    os.makedirs("residual_previews", exist_ok=True)
    with h5py.File(args.images, "r") as f:
        images = f["images"][:]; names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]]
        theta_pub = f["theta_E_pub"][:]; q_pub = f["q_pub"][:] if "q_pub" in f else np.full(len(images), np.nan)
        attrs = dict(f.attrs)
    res = np.zeros_like(images)
    for i in range(len(images)):
        r = fit_and_subtract(images[i, 0]); res[i, 0] = r
        fig, ax = plt.subplots(1, 2, figsize=(5, 2.6))
        ax[0].imshow(asinh_disp(images[i, 0]), origin="lower", cmap="gray"); ax[0].set_title("raw", fontsize=7)
        ax[1].imshow(asinh_disp(r), origin="lower", cmap="gray"); ax[1].set_title("lens-subtracted", fontsize=7)
        for a in ax: a.set_xticks([]); a.set_yticks([])
        fig.suptitle(names[i], fontsize=8); fig.tight_layout()
        fig.savefig(f"residual_previews/{names[i]}.png", dpi=110); plt.close(fig)
        print(f"  {names[i]}: subtracted")
    with h5py.File(args.out, "w") as f:
        f.create_dataset("images", data=res.astype("float32"))
        f.create_dataset("names", data=np.array(names, dtype="S32"))
        f.create_dataset("theta_E_pub", data=theta_pub.astype("float32"))
        f.create_dataset("q_pub", data=q_pub.astype("float32"))
        for k, v in attrs.items(): f.attrs[k] = v
    print(f"\nwrote {args.out} + residual_previews/. EYEBALL previews: did arcs appear?")


if __name__ == "__main__":
    main()
