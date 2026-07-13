import h5py, numpy as np, torch
from torch.utils.data import Dataset

def theta_pix_lookup(label_pix_h5):
    """Array indexed by kappa_index -> theta_E in pixels (fixed per kappa map)."""
    with h5py.File(label_pix_h5,"r") as f:
        tp   = f["theta_E_pixels"][:]
        kidx = f["kappa_index"][:]
    lut = np.zeros(int(kidx.max())+1, dtype=np.float32)
    lut[kidx] = tp
    return lut

class LensedScaleDataset(Dataset):
    """
    Model-2 dataset. Stays aligned under filtering:
    one boolean mask applied to images, scale, AND labels together;
    labels looked up by kappa_index (NEVER by row position).
    """
    def __init__(self, image_h5, theta_pix_by_kidx,
                 min_theta_e=0.5, min_mag=None, npix=128,
                 scale_stats=None):
        with h5py.File(image_h5,"r") as f:
            images = f["lensed"][:]                 # [N,128,128]
            kidx   = f["kappa_index"][:]            # [N]
            fov    = f["image_fov"][:]              # [N]  (per-image FOV: new in model 2)
            mag    = f["mag_proxy"][:] if "mag_proxy" in f else None
        theta_pix = theta_pix_by_kidx[kidx]         # [N], pixels
        pix_scale = fov / (npix - 1)                # [N], arcsec/px
        theta_arc = theta_pix * pix_scale           # [N], arcsec  (linear in scale)

        keep = theta_arc >= min_theta_e             # non-lens cut (label-based)
        if (min_mag is not None) and (mag is not None):
            keep = keep & (mag >= min_mag)          # magnification "visible arc" cut
        # ---- apply the SAME mask to everything together ----
        self.images    = images[keep]
        self.theta_arc = theta_arc[keep].astype(np.float32)
        self.pix_scale = pix_scale[keep].astype(np.float32)
        self.kidx      = kidx[keep]                 # kept for traceability/debugging

        if scale_stats is None:                     # normalize the scalar input
            self.s_mean = float(self.pix_scale.mean())
            self.s_std  = float(self.pix_scale.std() + 1e-8)
        else:
            self.s_mean, self.s_std = scale_stats   # reuse train stats on test set

    def stats(self): return (self.s_mean, self.s_std)
    def __len__(self): return len(self.images)
    def __getitem__(self, i):
        img   = torch.from_numpy(self.images[i]).float().unsqueeze(0)   # [1,128,128]
        s     = (self.pix_scale[i] - self.s_mean) / self.s_std
        scale = torch.tensor([s], dtype=torch.float32)                  # [1]
        y     = torch.tensor(self.theta_arc[i], dtype=torch.float32)    # arcsec
        return img, scale, y
