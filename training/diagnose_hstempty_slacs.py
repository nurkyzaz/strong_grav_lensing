#!/usr/bin/env python
"""
diagnose_hstempty_slacs.py
Separates the SLACS error into (a) a correctable systematic offset (definitional /
calibration) vs (b) real scatter (domain gap). Reports Pearson r, best-fit slope,
de-biased and calibrated R2, a per-lens table, and a montage of the worst lenses so
you can SEE whether the worst offenders are badly lens-subtracted.
"""
import argparse, numpy as np, h5py, torch
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from train_cnn_m3 import normalize_images, EinsteinCNNScale

CLEAN = ["J0029", "J0946", "J1032", "J1538", "J1420", "J2303"]  # worked zero-shot

def r2(p, t): return 1 - np.sum((t - p)**2) / (np.sum((t - t.mean())**2) + 1e-12)
def rstd(a): return 1.4826*np.median(np.abs(a-np.median(a)))+1e-8

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", default="einstein_cnn_hstempty.pt")
    ap.add_argument("--slacs", default="real_slacs_residual_v2.h5")
    ap.add_argument("--image_key", default="images")
    ap.add_argument("--out", default="diagnose_hstempty_slacs.png")
    a = ap.parse_args()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    ck = torch.load(a.ckpt, map_location=dev)
    with h5py.File(a.slacs) as f:
        ik = a.image_key if a.image_key in f else ("residual" if "residual" in f else list(f.keys())[0])
        imgs = f[ik][:].astype("float32")
        names = [n.decode() if isinstance(n, bytes) else str(n) for n in f["names"][:]] if "names" in f else [str(i) for i in range(len(imgs))]
        gt = f["theta_E_pub"][:].astype("float32")
    if imgs.ndim == 4: imgs = imgs[:, 0]
    m = gt > 0
    imgs, gt, names = imgs[m], gt[m], [names[i] for i in np.where(m)[0]]

    x = normalize_images(imgs, ck.get("norm", "asinh"), ck.get("asinh_a", 1.0))
    x = torch.from_numpy(x).unsqueeze(1).to(dev)
    s = torch.zeros(len(x), 1, dtype=torch.float32, device=dev)
    net = EinsteinCNNScale(channels=tuple(ck.get("channels", (32,64,128,256)))).to(dev)
    net.load_state_dict(ck["state_dict"]); net.eval()
    with torch.no_grad(): P = net(x, s).cpu().numpy()
    T = gt; fr = 100*(P-T)/T

    r = np.corrcoef(T, P)[0, 1]
    slope, inter = np.polyfit(T, P, 1)
    med = np.median(fr)
    Pdb = P / (1 + med/100)            # remove median offset only
    Pcal = (P - inter) / slope         # remove full best-fit line
    frdb = 100*(Pdb-T)/T

    print("="*64)
    print(f"N={len(P)}")
    print(f"RAW       median {med:+.1f}%  16-84 [{np.percentile(fr,16):+.1f},{np.percentile(fr,84):+.1f}]  R2 {r2(P,T):+.2f}  MAE {np.mean(np.abs(P-T)):.3f}\"")
    print(f"Pearson r (CNN vs Bolton)        = {r:+.2f}   <<< is there signal at all?")
    print(f"best fit  pred = {slope:.2f}*true {inter:+.2f}   (slope~1 tracks; <<1 = compressed/regress-to-mean)")
    print(f"DE-BIASED (remove median {med:+.0f}%)   R2 {r2(Pdb,T):+.2f}  16-84 [{np.percentile(frdb,16):+.1f},{np.percentile(frdb,84):+.1f}]")
    print(f"CALIBRATED (remove best-fit line)  R2 {r2(Pcal,T):+.2f}  MAE {np.mean(np.abs(Pcal-T)):.3f}\"")
    print("="*64)
    print("clean rings (worked zero-shot):")
    for i, n in enumerate(names):
        if any(n.startswith(c) for c in CLEAN):
            print(f"  {n:14s} Bolton {T[i]:.2f}  CNN {P[i]:.2f}  ({fr[i]:+.0f}%)")
    print("worst 8 by |frac| (eyeball these in the montage):")
    order = np.argsort(-np.abs(fr))
    for i in order[:8]:
        print(f"  {names[i]:14s} Bolton {T[i]:.2f}  CNN {P[i]:.2f}  ({fr[i]:+.0f}%)")

    fig, ax = plt.subplots(2, 4, figsize=(13, 7))
    for k, i in enumerate(order[:8]):
        v = np.arcsinh(imgs[i] / (rstd(imgs[i]) + 1e-8))
        ax.flat[k].imshow(v, origin="lower", cmap="gray")
        ax.flat[k].set_title(f"{names[i]}\nB {T[i]:.2f} / CNN {P[i]:.2f} ({fr[i]:+.0f}%)", fontsize=9)
        ax.flat[k].set_xticks([]); ax.flat[k].set_yticks([])
    fig.suptitle("Worst-error SLACS residuals -- look for bad lens subtraction / no clear arc")
    fig.savefig(a.out, dpi=120, bbox_inches="tight")
    print(f"wrote {a.out}")

if __name__ == "__main__":
    main()
