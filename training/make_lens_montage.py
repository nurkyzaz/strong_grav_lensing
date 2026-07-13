#!/usr/bin/env python
"""
make_lens_montage.py
Render each real SLACS lens with its CNN-predicted and published theta_E, as:
  (a) one PNG per lens in brian_run/lens_pngs/   (easy to scp the whole folder)
  (b) one combined contact-sheet montage brian_run/all_lenses_montage.png
Draws a circle at the predicted theta_E radius so the geometry is visible.
"""
import os, numpy as np, h5py, torch, csv
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from train_cnn_m3 import normalize_images, EinsteinCNNScale

SLACS="real_slacs_images.h5"; CKPT="einstein_cnn_m3.pt"; FOV=6.4; PIX=0.05
OUT="brian_run"; PNGDIR=os.path.join(OUT,"lens_pngs"); os.makedirs(PNGDIR, exist_ok=True)
dev="cuda" if torch.cuda.is_available() else "cpu"

ck=torch.load(CKPT, map_location=dev)
net=EinsteinCNNScale(channels=tuple(ck["channels"])).to(dev); net.load_state_dict(ck["state_dict"]); net.eval()
with h5py.File(SLACS) as f:
    imgs=f["images"][:].astype("float32")
    if imgs.ndim==4: imgs=imgs[:,0]
    names=[n.decode() if isinstance(n,bytes) else str(n) for n in f["names"][:]] if "names" in f else [f"lens_{i}" for i in range(len(imgs))]
    pub=f["theta_E_pub"][:].astype("float32") if "theta_E_pub" in f else np.full(len(imgs),np.nan)

x=normalize_images(imgs, ck["norm"], ck["asinh_a"])
x=torch.from_numpy(x).unsqueeze(1).to(dev)
s=torch.full((len(x),1),(FOV/127-ck["scale_mean"])/ck["scale_std"],dtype=torch.float32,device=dev)
with torch.no_grad(): pred=net(x,s).cpu().numpy()

def stretch(a): 
    rs=1.4826*np.median(np.abs(a-np.median(a)))+1e-8
    return np.arcsinh(np.clip(a,0,None)/rs)

# (a) per-lens PNGs
for i,nm in enumerate(names):
    fig,ax=plt.subplots(figsize=(4,4))
    ax.imshow(stretch(imgs[i]), origin="lower", cmap="gray")
    cx=cy=imgs[i].shape[0]/2
    ax.add_patch(plt.Circle((cx,cy), pred[i]/PIX, fill=False, color="cyan", lw=1.2, label="CNN"))
    if np.isfinite(pub[i]):
        ax.add_patch(plt.Circle((cx,cy), pub[i]/PIX, fill=False, color="orange", lw=1.2, ls="--", label="pub"))
    ax.set_title(f"{nm}\nCNN {pred[i]:.2f}\"  pub {pub[i]:.2f}\"", fontsize=10)
    ax.set_xticks([]); ax.set_yticks([]); ax.legend(loc="lower right", fontsize=7)
    fig.savefig(os.path.join(PNGDIR,f"{nm}.png"), dpi=110, bbox_inches="tight"); plt.close(fig)

# (b) contact sheet
n=len(names); cols=8; rows=int(np.ceil(n/cols))
fig,ax=plt.subplots(rows,cols,figsize=(cols*2.1,rows*2.3))
for i in range(rows*cols):
    a=ax.flat[i]; a.set_xticks([]); a.set_yticks([])
    if i>=n: a.axis("off"); continue
    a.imshow(stretch(imgs[i]), origin="lower", cmap="gray")
    cx=cy=imgs[i].shape[0]/2
    a.add_patch(plt.Circle((cx,cy), pred[i]/PIX, fill=False, color="cyan", lw=0.8))
    if np.isfinite(pub[i]): a.add_patch(plt.Circle((cx,cy), pub[i]/PIX, fill=False, color="orange", lw=0.8, ls="--"))
    fr=100*(pred[i]-pub[i])/pub[i] if np.isfinite(pub[i]) and pub[i]>0 else np.nan
    a.set_title(f"{names[i]}\nC{pred[i]:.2f}/P{pub[i]:.2f} ({fr:+.0f}%)", fontsize=6)
fig.suptitle("Real SLACS: cyan = CNN theta_E, orange dashed = published", fontsize=12)
fig.savefig(os.path.join(OUT,"all_lenses_montage.png"), dpi=130, bbox_inches="tight")
print(f"wrote {n} PNGs -> {PNGDIR}/  and  {OUT}/all_lenses_montage.png")
