import sys, numpy as np, h5py, torch
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, "/home/user/ckwan1/ml_project/strong-lensing-sampling/forward_operator")
from physical_model import PhysicalModel

KAP = "/home/user/ckwan1/ml_project/strong_lensing_dataset/kappa_light/train_camera_complete.h5"
SRC = "/home/user/ckwan1/ml_project/strong_lensing_dataset/source/galaxies_testset.h5"
dev = "cuda" if torch.cuda.is_available() else "cpu"

def centroid(a):
    a = np.clip(a, 0, None); s = a.sum()
    if s == 0: return (np.nan, np.nan)
    y, x = np.indices(a.shape)
    return (float((y*a).sum()/s), float((x*a).sum()/s))

def fwhm_px(a):  # rough size: count pixels above half-max
    a = np.clip(a, 0, None)
    return int((a > 0.5*a.max()).sum())

fk = h5py.File(KAP); fs = h5py.File(SRC)
print("kappa keys:", list(fk.keys()))
for k in fk.keys():
    try: print(f"  {k}: shape={fk[k].shape} dtype={fk[k].dtype}")
    except Exception: pass
kap = fk["kappa"]; ll = fk["lens_light"]; gal = fs["galaxies"]
print("lens_light ndim/shape:", ll.ndim, ll.shape)

# render the arc for index 0 at fov=6.4 (what we use)
m = PhysicalModel(pixels=128, src_pixels=128, kappa_pixels=128,
                  image_fov=6.4, src_fov=2.0, kappa_fov=6.4, lens_light_fov=6.4,
                  method="fft", kappa_interp_mode="deflection").to(dev).eval()
i = 0
k0 = torch.from_numpy(kap[i:i+1].astype("float32")).unsqueeze(1).to(dev)
s0 = torch.from_numpy(gal[i:i+1].astype("float32")).unsqueeze(1).to(dev)
with torch.no_grad():
    arc = m.lens_source(s0, k0).squeeze().cpu().numpy()
ll0 = np.asarray(ll[i], dtype="float32")
if ll0.ndim == 3: ll0 = ll0[0]
k0n = kap[i].astype("float32")
if k0n.ndim == 3: k0n = k0n[0]

with h5py.File("empty_cutouts.h5") as fe:
    emp = fe["empty"][0].astype("float32")
    emp_attrs = dict(fe.attrs)

for name, a in [("kappa", k0n), ("arc(lens_source)", arc), ("lens_light", ll0), ("empty_cutout", emp)]:
    print(f"{name:18s} shape={a.shape} min={a.min():.3g} max={a.max():.3g} "
          f"centroid(y,x)={tuple(round(c,1) for c in centroid(a))} bright_px(>half-max)={fwhm_px(a)}")

print("\nempty_cutouts attrs:", emp_attrs)
print("CHECK: is lens_light centroid ~ (63,63)? is its bright_px tiny (compact core) or huge (puffball)?")

fig, ax = plt.subplots(1, 4, figsize=(16, 4))
for j,(name,a) in enumerate([("kappa",k0n),("arc",arc),("lens_light",ll0),("empty",emp)]):
    v = np.arcsinh(np.clip(a,0,None)/(np.median(np.abs(a-np.median(a)))*1.4826+1e-8))
    ax[j].imshow(v, origin="lower", cmap="gray"); ax[j].set_title(name); ax[j].axhline(63,color='r',lw=.3); ax[j].axvline(63,color='r',lw=.3)
plt.savefig("diag_ingredients.png", dpi=110, bbox_inches="tight")
print("wrote diag_ingredients.png")
