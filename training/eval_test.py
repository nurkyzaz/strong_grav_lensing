import argparse, numpy as np, torch
from torch.utils.data import DataLoader
from train_cnn import LensedDataset, EinsteinCNN, evaluate
ap = argparse.ArgumentParser()
ap.add_argument("--image_file", required=True)
ap.add_argument("--label_file", required=True)
ap.add_argument("--ckpt", default="einstein_cnn.pt")
ap.add_argument("--min_theta_e", type=float, default=0.5)
ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
a = ap.parse_args()
ds = LensedDataset(a.image_file, a.label_file, min_theta_e=a.min_theta_e)
loader = DataLoader(ds, batch_size=128, shuffle=False)
model = EinsteinCNN().to(a.device)
model.load_state_dict(torch.load(a.ckpt, map_location=a.device))
mae, frac, r2, preds, trues = evaluate(model, loader, a.device)
d = 100 * (preds - trues) / trues
print(f"TEST  n={len(ds)}  MAE={mae:.4f}\"  median_frac={frac:.1f}%  R2={r2:.3f}")
print(f"  16-84% frac interval = [{np.percentile(d,16):.1f}%, {np.percentile(d,84):.1f}%]")
