#!/usr/bin/env python
"""
compact_source_test.py  -- Brian's 12.06 recipe
Filter the source dataset to half-light radius r_half < threshold (default 0.15"),
pair each with a RANDOM lens (kappa map), run the forward operator, and test Model 3's
theta_E on COMPACT vs NORMAL sources. This probes the CNN's core value: LensFusion
under-magnifies compact sources, and the CNN is meant to constrain theta_E there.

Clean SIMULATION test (no domain gap) -> M3 is valid here.

Writes: brian_run/compact_source_test.png  + prints the numbers.
"""
import os, sys, argparse, numpy as np, h5py, torch
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from train_cnn_m3 import normalize_images, EinsteinCNNScale

sys.path.insert(0, "/home/user/ckwan1/ml_project/strong-lensing-sampling/forward_operator")
from physical_model import PhysicalModel


def r_half_arcsec(img, pix_scale):
    """Half-light radius (paper Eq.21): radius enclosing half the total flux,
    about the flux-weighted centroid. Returned in arcsec."""
    a = np.clip(img, 0, None); tot = a.sum()
    if tot <= 0: return np.nan
    y, x = np.indices(a.shape)
    cy, cx = (y*a).sum()/tot, (x*a).sum()/tot
    r = np.hypot(y-cy, x-cx).ravel()
    order = np.argsort(r)
    csum = np.cumsum(a.ravel()[order])
    rh_px = r[order][np.searchsorted(csum, 0.5*tot)]
    return rh_px * pix_scale


def theta_E_hard(kappa, fov):
    """kappa_bar(<theta_E)=1, azimuthally averaged about centre. arcsec."""
    n = kappa.shape[-1]; pix = fov/(n-1)
    y, x = np.indices((n, n)); cy = cx = (n-1)/2
    r = np.hypot(y-cy, x-cx).ravel()*pix
    k = kappa.ravel()
    order = np.argsort(r); r_s, k_s = r[order], k[order]
    # mean convergence within radius
    csum = np.cumsum(k_s)
    counts = np.arange(1, len(k_s)+1)
    kbar = csum/counts
    below = np.where(kbar >= 1.0)[0]
    if len(below) == 0: return np.nan
    return r_s[below[-1]]


def parse():
    p = argparse.ArgumentParser()
    p.add_argument("--ckpt", default="einstein_cnn_m3.pt")
    p.add_argument("--source_file",
                   default="/home/user/ckwan1/ml_project/strong_lensing_dataset/source/galaxies_testset.h5")
    p.add_argument("--kappa_file",
                   default="/home/user/ckwan1/ml_project/strong_lensing_dataset/kappa_light/test_camera_complete.h5")
    p.add_argument("--repo_root", default="/home/user/ckwan1/ml_project/strong-lensing-sampling")
    p.add_argument("--rhalf_thresh", type=float, default=0.15)
    p.add_argument("--fov", type=float, default=6.4)
    p.add_argument("--src_fov", type=float, default=2.0)
    p.add_argument("--n", type=int, default=600)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--outdir", default="brian_run")
    return p.parse_args()


def main():
    a = parse(); os.makedirs(a.outdir, exist_ok=True)
    rng = np.random.default_rng(a.seed); torch.manual_seed(a.seed)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    src_scale = a.src_fov/(127)

    ck = torch.load(a.ckpt, map_location=dev)
    net = EinsteinCNNScale(channels=tuple(ck["channels"])).to(dev)
    net.load_state_dict(ck["state_dict"]); net.eval()

    with h5py.File(a.source_file) as f:
        src_all = f["galaxies"][:a.n].astype("float32")
    with h5py.File(a.kappa_file) as f:
        kap_all = f["kappa"][:a.n].astype("float32")
        if kap_all.ndim == 4: kap_all = kap_all[:, 0]

    # measure r_half for each source (in source-plane arcsec)
    rh = np.array([r_half_arcsec(s, src_scale) for s in src_all])
    # pair each source with a RANDOM lens
    lens_idx = rng.integers(0, len(kap_all), size=len(src_all))

    model = PhysicalModel(pixels=128, src_pixels=128, kappa_pixels=128,
                          image_fov=a.fov, src_fov=a.src_fov, kappa_fov=a.fov,
                          lens_light_fov=a.fov, method="fft",
                          kappa_interp_mode="deflection").to(dev).eval()

    preds, gts = [], []
    img_scale = a.fov/127
    with torch.no_grad():
        for i in range(0, len(src_all), 64):
            sb = torch.from_numpy(src_all[i:i+64]).unsqueeze(1).to(dev)
            kb = torch.from_numpy(kap_all[lens_idx[i:i+64]]).unsqueeze(1).to(dev)
            arc = model.lens_source(sb, kb).squeeze(1).cpu().numpy()
            x = normalize_images(arc, ck["norm"], ck["asinh_a"])
            x = torch.from_numpy(x).unsqueeze(1).to(dev)
            s = torch.full((len(x), 1), (img_scale-ck["scale_mean"])/ck["scale_std"],
                           dtype=torch.float32, device=dev)
            preds.append(net(x, s).cpu().numpy())
            for j in range(kb.shape[0]):
                gts.append(theta_E_hard(kap_all[lens_idx[i+j]], a.fov))
    preds = np.concatenate(preds); gts = np.array(gts)

    ok = np.isfinite(preds) & np.isfinite(gts) & (gts > 0) & np.isfinite(rh)
    preds, gts, rh = preds[ok], gts[ok], rh[ok]
    fr = 100*(preds-gts)/gts
    compact = rh < a.rhalf_thresh
    normal = ~compact

    def summ(m, name):
        if m.sum() == 0: print(f"  {name}: (none)"); return
        f = fr[m]
        print(f"  {name:18s} N={m.sum():4d} | median {np.median(f):+.1f}% | "
              f"16-84 [{np.percentile(f,16):+.1f},{np.percentile(f,84):+.1f}] | "
              f"MAE {np.mean(np.abs(preds[m]-gts[m])):.3f}\" | "
              f">15% fail: {100*np.mean(np.abs(f)>15):.0f}%")
    print(f"\n=== Model 3 on compact vs normal sources (r_half cut = {a.rhalf_thresh}\") ===")
    print(f"r_half range {rh.min():.3f}-{rh.max():.3f}\"  ;  {compact.sum()} compact / {normal.sum()} normal")
    summ(normal, "NORMAL src"); summ(compact, "COMPACT src")

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    ax[0].scatter(gts[normal], preds[normal], s=8, alpha=.5, label="normal")
    ax[0].scatter(gts[compact], preds[compact], s=10, alpha=.7, color="crimson", label="compact r_half<%.2f\""%a.rhalf_thresh)
    lim = [min(gts.min(), preds.min()), max(gts.max(), preds.max())]
    ax[0].plot(lim, lim, 'k--', lw=.8); ax[0].set_xlabel("true theta_E [\"]"); ax[0].set_ylabel("CNN theta_E [\"]")
    ax[0].legend(); ax[0].set_title("M3 theta_E: compact vs normal")
    ax[1].scatter(rh, fr, s=8, alpha=.5); ax[1].axvline(a.rhalf_thresh, color='crimson', ls='--')
    ax[1].axhline(0, color='k', lw=.5); ax[1].set_xlabel("source r_half [\"]"); ax[1].set_ylabel("frac err [%]")
    ax[1].set_title("error vs source compactness")
    out = os.path.join(a.outdir, "compact_source_test.png")
    fig.savefig(out, dpi=120, bbox_inches="tight"); print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
