#!/usr/bin/env python
"""
test_external_lens.py
Predict theta_E for an external lens FITS (e.g. Brian's bells0201 / slacs1627 / slacs0252)
with any checkpoint. Resamples to 0.05"/px and center-crops/pads to 128 px (6.4").

  raw image + raw-trained model (m3, reads through lens light):
    python test_external_lens.py --fits bells0201_data.fits --native_pixscale 0.04 --ckpt einstein_cnn_m3.pt --save_png
  crude lens-subtract + HSTempty model:
    python test_external_lens.py --fits slacs1627_data.fits --native_pixscale 0.05 --ckpt einstein_cnn_hstempty.pt --subtract --save_png
"""
import argparse, os, numpy as np, torch
from astropy.io import fits
from scipy.ndimage import zoom
from train_cnn_m3 import normalize_images, EinsteinCNNScale


def azimuthal_subtract(img):
    """Quick-and-dirty lens removal: subtract the circularly-symmetric profile
    about the brightest pixel. NOT PyAutoLens quality -- a sanity stopgap only."""
    cy, cx = np.unravel_index(np.argmax(img), img.shape)
    y, x = np.indices(img.shape)
    r = np.hypot(y - cy, x - cx).astype(int)
    prof = np.bincount(r.ravel(), img.ravel()) / np.maximum(np.bincount(r.ravel()), 1)
    return img - prof[r]


def center_to(img, n=128):
    h, w = img.shape
    out = np.zeros((n, n), img.dtype)
    y0, x0 = max((h - n)//2, 0), max((w - n)//2, 0)
    cy, cx = max((n - h)//2, 0), max((n - w)//2, 0)
    hh, ww = min(h, n), min(w, n)
    out[cy:cy+hh, cx:cx+ww] = img[y0:y0+hh, x0:x0+ww]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fits", required=True)
    ap.add_argument("--native_pixscale", type=float, required=True)
    ap.add_argument("--ckpt", default="einstein_cnn_hstempty.pt")
    ap.add_argument("--subtract", action="store_true", help="crude azimuthal lens removal first")
    ap.add_argument("--save_png", action="store_true")
    a = ap.parse_args()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    ck = torch.load(a.ckpt, map_location=dev)

    d = np.nan_to_num(fits.getdata(a.fits).astype("float32"))
    if a.subtract:
        d = azimuthal_subtract(d)
    d = zoom(d, a.native_pixscale / 0.05, order=1)   # -> 0.05"/px
    d = center_to(d, 128)

    x = normalize_images(d[None], ck.get("norm", "asinh"), ck.get("asinh_a", 1.0))
    x = torch.from_numpy(x).unsqueeze(1).to(dev)
    smean, sstd = float(ck["scale_mean"]), float(ck["scale_std"])
    pix = 6.4 / 127
    s_val = 0.0 if sstd < 1e-4 else (pix - smean) / sstd   # 0 for single-FOV (HSTempty)
    s = torch.full((1, 1), s_val, dtype=torch.float32, device=dev)

    net = EinsteinCNNScale(channels=tuple(ck.get("channels", (32,64,128,256)))).to(dev)
    net.load_state_dict(ck["state_dict"]); net.eval()
    with torch.no_grad():
        p = float(net(x, s))
    print(f"{os.path.basename(a.fits):24s} ckpt={os.path.basename(a.ckpt):26s} "
          f"subtract={a.subtract!s:5s} -> theta_E = {p:.3f}\"")

    if a.save_png:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        rs = 1.4826*np.median(np.abs(d-np.median(d)))+1e-8
        plt.imshow(np.arcsinh(d/rs), origin="lower", cmap="gray")
        plt.title(f"{os.path.basename(a.fits)}  pred theta_E={p:.2f}\"")
        out = a.fits.replace(".fits", "_input.png")
        plt.savefig(out, dpi=110, bbox_inches="tight"); print("  wrote", out)


if __name__ == "__main__":
    main()
