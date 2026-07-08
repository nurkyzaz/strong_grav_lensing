#!/usr/bin/env python
"""
test_real_slacs.py  (multi-output, corrected)
---------------------------------------------
Run the MULTI-OUTPUT checkpoint on the real SLACS cutouts, matching training EXACTLY:
    raw cutout (e/s)
      -> flux_rescale (--flux_norm knob; asinh is tuned to sim flux units)
      -> train_cnn_m3.normalize_images(asinh)        [repo function, byte-for-byte]
      -> EinsteinCNNMulti(image, standardized_scalar) [scalar via scale_mean/scale_std]
      -> un-standardize outputs via ymean/ystd
Outputs:
  <prefix>.csv                  full table (theta_E, e1, e2, q, ...)
  <prefix>_theta_for_brian.csv  two columns (name, theta_E_pred) for Brian's regularizer
  <prefix>.png                  scatter: CNN kappa_bar=1 vs published SIE bSIE

theta_E is the deliverable (no convention ambiguity). Ellipticity is a BONUS check:
|e|=hypot(e1,e2) vs published (1-q)/(1+q) -- CONFIRM the convention against
ellipticity_labels.py before quoting that number.
Expect a systematic theta_E offset (SIE bSIE vs our kappa_bar=1) on top of the sim-to-real gap.
"""
import argparse, numpy as np, h5py, torch, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from train_cnn_multi import EinsteinCNNMulti
from train_cnn_m3 import normalize_images


def flux_rescale(img, mode):
    finite = img[np.isfinite(img)]
    if finite.size == 0 or mode == "none":
        return np.nan_to_num(img)
    if mode == "sum":
        s = finite.sum()
        return np.nan_to_num(img / s if s > 0 else img)
    p = np.percentile(finite, 99.5); p = p if p > 0 else 1.0
    target = 20.0 if mode == "peak20" else 1.0    # peak20 ~ matches sim lens-light amp
    return np.nan_to_num(img / p * target)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="einstein_cnn_multi_m3.pt")
    ap.add_argument("--images", default="real_slacs_images.h5")
    ap.add_argument("--flux_norm", default="peak20", choices=["peak20", "peak1", "sum", "none"])
    ap.add_argument("--out_prefix", default="real_slacs_result")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()
    device = torch.device(args.device)

    ck = torch.load(args.ckpt, map_location=device)
    if int(ck.get("n_out", 5)) != 5:
        raise SystemExit("This expects the MULTI-output checkpoint (n_out=5).")
    scale_mean, scale_std = float(ck["scale_mean"]), float(ck["scale_std"])
    ymean = ck["ymean"].cpu().numpy() if torch.is_tensor(ck["ymean"]) else np.asarray(ck["ymean"])
    ystd  = ck["ystd"].cpu().numpy()  if torch.is_tensor(ck["ystd"])  else np.asarray(ck["ystd"])
    asinh_a, norm = float(ck.get("asinh_a", 1.0)), ck.get("norm", "asinh")

    model = EinsteinCNNMulti(channels=tuple(ck["channels"]), n_out=int(ck["n_out"])).to(device)
    model.load_state_dict(ck["state_dict"]); model.eval()

    with h5py.File(args.images, "r") as f:
        images = f["images"][:]                       # [N,1,128,128] raw flux
        names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]]
        theta_pub = f["theta_E_pub"][:].astype("float32")
        q_pub = (f["q_pub"][:].astype("float32") if "q_pub" in f
                 else np.full(len(images), np.nan, "float32"))
        box = float(f.attrs.get("box_arcsec", 6.4))
    pixels = images.shape[-1]
    pix_scale = box / (pixels - 1)                    # training convention fov/(pixels-1)
    s_std = (pix_scale - scale_mean) / scale_std
    print(f"[scalar] pix_scale={pix_scale:.5f}\"/px -> standardized {s_std:+.3f} "
          f"(train mean {scale_mean:.4f} std {scale_std:.4f})")

    raw = np.stack([flux_rescale(images[i, 0], args.flux_norm) for i in range(len(images))])
    X = normalize_images(raw, norm, asinh_a)          # [N,128,128] EXACT training preprocessing
    Xt = torch.from_numpy(X).unsqueeze(1).to(device)
    St = torch.full((len(images), 1), float(s_std), dtype=torch.float32, device=device)
    with torch.no_grad():
        pred = model(Xt, St).cpu().numpy() * ystd + ymean   # un-standardize -> physical
    theta_pred, e1, e2 = pred[:, 0], pred[:, 1], pred[:, 2]
    e_mag = np.hypot(e1, e2)
    e_pub = (1 - q_pub) / (1 + q_pub)

    frac = 100 * (theta_pred - theta_pub) / theta_pub
    res = pd.DataFrame({"name": names, "theta_E_pub": theta_pub, "theta_E_pred": theta_pred,
                        "frac_err_%": frac, "q_pub": q_pub, "e_pred": e_mag, "e_pub": e_pub,
                        "e1_pred": e1, "e2_pred": e2})
    res.to_csv(f"{args.out_prefix}.csv", index=False)
    res[["name", "theta_E_pred"]].to_csv(f"{args.out_prefix}_theta_for_brian.csv", index=False)

    med = np.median(frac); p16, p84 = np.percentile(frac, [16, 84])
    mae = np.mean(np.abs(theta_pred - theta_pub))
    ss, st = np.sum((theta_pred - theta_pub) ** 2), np.sum((theta_pub - theta_pub.mean()) ** 2)
    r2 = 1 - ss / st if st > 0 else float("nan")
    print(f"\n=== SLACS theta_E  (flux_norm={args.flux_norm}, N={len(theta_pred)}) ===")
    print(res[["name", "theta_E_pub", "theta_E_pred", "frac_err_%"]].to_string(index=False))
    print(f"\nMAE {mae:.3f}\"  median frac {med:+.1f}%  16-84% [{p16:+.1f},{p84:+.1f}]  R2 {r2:.3f}")
    print("(nonzero median expected: SIE bSIE vs our kappa_bar=1 definition offset.)")
    ok = np.isfinite(e_pub)
    if ok.sum() > 3:
        er2 = 1 - np.sum((e_pub[ok] - e_mag[ok]) ** 2) / np.sum((e_pub[ok] - e_pub[ok].mean()) ** 2)
        print(f"ellipticity |e| vs (1-q)/(1+q): R2 {er2:.2f} (N={int(ok.sum())}) "
              f"-- BONUS; confirm |e| convention vs ellipticity_labels.py before quoting.")

    lim = [min(theta_pub.min(), theta_pred.min()) * 0.9, max(theta_pub.max(), theta_pred.max()) * 1.1]
    plt.figure(figsize=(5, 5)); plt.plot(lim, lim, "k--", lw=1, label="y = x")
    plt.scatter(theta_pub, theta_pred, s=28, alpha=0.8)
    plt.xlabel(r"published $\theta_E$ (SIE bSIE) [arcsec]")
    plt.ylabel(r"CNN $\theta_E$ ($\bar\kappa=1$) [arcsec]")
    plt.title(f"Real SLACS  flux_norm={args.flux_norm}  med={med:+.1f}%\n"
              "SIE vs kappa_bar=1 offset expected", fontsize=9)
    plt.xlim(lim); plt.ylim(lim); plt.legend(); plt.tight_layout()
    plt.savefig(f"{args.out_prefix}.png", dpi=130)
    print(f"\nwrote {args.out_prefix}.csv, {args.out_prefix}_theta_for_brian.csv, {args.out_prefix}.png")


if __name__ == "__main__":
    main()
