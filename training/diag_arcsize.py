import sys, numpy as np, h5py, torch
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0,"/home/user/ckwan1/ml_project/strong-lensing-sampling/forward_operator")
from physical_model import PhysicalModel
KAP="/home/user/ckwan1/ml_project/strong_lensing_dataset/kappa_light/train_camera_complete.h5"
SRC="/home/user/ckwan1/ml_project/strong_lensing_dataset/source/galaxies_testset.h5"
dev="cuda" if torch.cuda.is_available() else "cpu"
fk=h5py.File(KAP); fs=h5py.File(SRC); kap=fk["kappa"]; gal=fs["galaxies"]
def arc_px(a): a=np.clip(a,0,None); return int((a>0.5*a.max()).sum())

def render(idx, src_fov):
    m=PhysicalModel(pixels=128,src_pixels=128,kappa_pixels=128,image_fov=6.4,
        src_fov=src_fov,kappa_fov=6.4,lens_light_fov=6.4,method="fft",
        kappa_interp_mode="deflection").to(dev).eval()
    k=torch.from_numpy(kap[idx][None,None].astype("float32")).to(dev)
    s=torch.from_numpy(gal[idx][None,None].astype("float32")).to(dev)
    with torch.no_grad(): return m.lens_source(s,k).squeeze().cpu().numpy()

print("arc thickness (bright px > half-max), 20 systems, per src_fov:")
for sf in [2.0, 1.0, 0.5]:
    px=[arc_px(render(i, sf)) for i in range(20)]
    print(f"  src_fov={sf}: median bright_px={int(np.median(px))}  range[{min(px)},{max(px)}]")

fig,ax=plt.subplots(3,5,figsize=(15,9))
for r,sf in enumerate([2.0,1.0,0.5]):
    for c,idx in enumerate([0,3,5,8,11]):
        a=render(idx,sf); v=np.arcsinh(np.clip(a,0,None)/(a.max()*0.05+1e-8))
        ax[r,c].imshow(v,origin="lower",cmap="gray"); ax[r,c].set_xticks([]); ax[r,c].set_yticks([])
        if c==0: ax[r,c].set_ylabel(f"src_fov={sf}")
fig.suptitle("Arc thickness vs source size -- smaller src_fov => thinner, more SLACS-like arcs")
plt.savefig("diag_arcsize.png",dpi=110,bbox_inches="tight"); print("wrote diag_arcsize.png")
