import sys, numpy as np, h5py, torch
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0,"/home/user/ckwan1/ml_project/strong-lensing-sampling/forward_operator")
from physical_model import PhysicalModel
KAP="/home/user/ckwan1/ml_project/strong_lensing_dataset/kappa_light/train_camera_complete.h5"
SRC="/home/user/ckwan1/ml_project/strong_lensing_dataset/source/galaxies_testset.h5"
dev="cuda" if torch.cuda.is_available() else "cpu"
fk=h5py.File(KAP); fs=h5py.File(SRC); kap=fk["kappa"]; gal=fs["galaxies"]

def render(idx, src_fov=1.0):
    m=PhysicalModel(pixels=128,src_pixels=128,kappa_pixels=128,image_fov=6.4,src_fov=src_fov,
        kappa_fov=6.4,lens_light_fov=6.4,method="fft",kappa_interp_mode="deflection").to(dev).eval()
    k=torch.from_numpy(kap[idx][None,None].astype("float32")).to(dev)
    s=torch.from_numpy(gal[idx][None,None].astype("float32")).to(dev)
    with torch.no_grad(): return m.lens_source(s,k).squeeze().cpu().numpy()

y,x=np.indices((128,128)); r=np.hypot(y-63.5,x-63.5)
core=r<8           # central ~0.8" radius
ring=(r>=8)&(r<55) # the arc region
print("fraction of arc flux sitting in the central <0.8\" core, 20 systems:")
fr=[]
for i in range(20):
    a=np.clip(render(i),0,None)
    f=a[core].sum()/(a.sum()+1e-9); fr.append(f)
    print(f"  idx {i:2d}: core/total = {f*100:5.1f}%   (core peak {a[core].max():.3g}, arc peak {a[ring].max():.3g})")
print(f"median core fraction = {np.median(fr)*100:.1f}%")

fig,ax=plt.subplots(2,4,figsize=(13,7))
for j,idx in enumerate([0,1,3,5,8,11,14,17]):
    a=render(idx); v=np.arcsinh(np.clip(a,0,None)/(a.max()*0.05+1e-8))
    ax.flat[j].imshow(v,origin="lower",cmap="gray")
    c=plt.Circle((63.5,63.5),8,fill=False,color='r',lw=0.8); ax.flat[j].add_patch(c)
    ax.flat[j].set_title(f"idx{idx}",fontsize=9); ax.flat[j].set_xticks([]); ax.flat[j].set_yticks([])
fig.suptitle("Arc only (no lens light). Red circle = central-image region we'd mask")
plt.savefig("diag_centre.png",dpi=110,bbox_inches="tight"); print("wrote diag_centre.png")
