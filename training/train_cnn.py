#!/usr/bin/env python
"""Train a ResNet CNN to predict Einstein radius theta_E from a lensed image.
Joins labels by kappa_index (not row position) and filters non-lenses by label."""
import argparse
import h5py
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split


class LensedDataset(Dataset):
    def __init__(self, image_file, label_file, normalize=True,
                 min_peak_snr=None, min_bright_pix=None, min_theta_e=None):
        with h5py.File(image_file, "r") as f:
            images = f["lensed"][:].astype("float32")
            kappa_index = f["kappa_index"][:].astype("int64")
            peak_snr = f["peak_snr"][:].astype("float32") if "peak_snr" in f else None
            n_bright = f["n_bright_pix"][:].astype("int64") if "n_bright_pix" in f else None

        with h5py.File(label_file, "r") as f:
            theta = f["theta_E"][:].astype("float32")
            label_kidx = f["kappa_index"][:].astype("int64")
        lut = np.full(int(label_kidx.max()) + 1, np.nan, dtype="float32")
        lut[label_kidx] = theta
        labels = lut[kappa_index]
        if np.isnan(labels).any():
            raise ValueError(f"{int(np.isnan(labels).sum())} images have no label. "
                             f"Run compute_labels.py over ALL kappa maps (no --n).")

        keep = np.ones(len(images), dtype=bool)
        keep &= (labels > 0)
        if min_theta_e is not None:
            keep &= (labels >= min_theta_e)
        if min_peak_snr is not None:
            if peak_snr is None:
                raise ValueError("--min_peak_snr set but image file has no 'peak_snr'")
            keep &= (peak_snr >= min_peak_snr)
        if min_bright_pix is not None:
            if n_bright is None:
                raise ValueError("--min_bright_pix set but image file has no 'n_bright_pix'")
            keep &= (n_bright >= min_bright_pix)
        n_before = len(images)
        images, labels, kappa_index = images[keep], labels[keep], kappa_index[keep]
        print(f"[data] cut: kept {int(keep.sum())}/{n_before} "
              f"(min_theta_e={min_theta_e}, min_peak_snr={min_peak_snr})")

        if normalize:
            mn = images.min(axis=(1, 2), keepdims=True)
            mx = images.max(axis=(1, 2), keepdims=True)
            images = (images - mn) / (mx - mn + 1e-8)
        self.images, self.labels, self.kappa_index = images, labels, kappa_index

    def __len__(self):
        return len(self.images)

    def __getitem__(self, i):
        return torch.from_numpy(self.images[i]).unsqueeze(0), torch.tensor(self.labels[i])


class ResidualBlock(nn.Module):
    def __init__(self, in_ch, out_ch, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_ch, out_ch, 3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_ch)
        self.conv2 = nn.Conv2d(out_ch, out_ch, 3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_ch)
        self.relu = nn.ReLU(inplace=True)
        self.shortcut = nn.Sequential()
        if stride != 1 or in_ch != out_ch:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, 1, stride=stride, bias=False),
                nn.BatchNorm2d(out_ch))

    def forward(self, x):
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out = out + self.shortcut(x)
        return self.relu(out)


class EinsteinCNN(nn.Module):
    def __init__(self, channels=(32, 64, 128, 256)):
        super().__init__()
        c0, c1, c2, c3 = channels
        self.stem = nn.Sequential(
            nn.Conv2d(1, c0, 7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(c0), nn.ReLU(inplace=True))
        self.layer1 = nn.Sequential(ResidualBlock(c0, c0), ResidualBlock(c0, c0))
        self.layer2 = nn.Sequential(ResidualBlock(c0, c1, stride=2), ResidualBlock(c1, c1))
        self.layer3 = nn.Sequential(ResidualBlock(c1, c2, stride=2), ResidualBlock(c2, c2))
        self.layer4 = nn.Sequential(ResidualBlock(c2, c3, stride=2), ResidualBlock(c3, c3))
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.head = nn.Linear(c3, 1)

    def forward(self, x):
        x = self.stem(x)
        x = self.layer1(x); x = self.layer2(x); x = self.layer3(x); x = self.layer4(x)
        x = self.gap(x).flatten(1)
        return self.head(x).squeeze(1)


def evaluate(model, loader, device):
    model.eval()
    preds, trues = [], []
    with torch.no_grad():
        for img, y in loader:
            preds.append(model(img.to(device)).cpu().numpy())
            trues.append(y.numpy())
    preds = np.concatenate(preds); trues = np.concatenate(trues)
    mae = np.mean(np.abs(preds - trues))
    nz = trues > 0
    frac = 100 * np.median(np.abs(preds[nz] - trues[nz]) / trues[nz]) if nz.any() else float("nan")
    ss_res = np.sum((trues - preds) ** 2); ss_tot = np.sum((trues - trues.mean()) ** 2)
    return mae, frac, 1 - ss_res / ss_tot, preds, trues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image_file", default="lensed_train_singleband.h5")
    ap.add_argument("--label_file", default="labels_train_singleband.h5")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--val_frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out_ckpt", default="einstein_cnn.pt")
    ap.add_argument("--min_theta_e", type=float, default=None)
    ap.add_argument("--min_peak_snr", type=float, default=None)
    ap.add_argument("--min_bright_pix", type=int, default=None)
    args = ap.parse_args()

    torch.manual_seed(args.seed); np.random.seed(args.seed)
    device = torch.device(args.device)

    full = LensedDataset(args.image_file, args.label_file,
                         min_theta_e=args.min_theta_e,
                         min_peak_snr=args.min_peak_snr,
                         min_bright_pix=args.min_bright_pix)
    n_val = int(len(full) * args.val_frac); n_train = len(full) - n_val
    train_set, val_set = random_split(full, [n_train, n_val],
                                      generator=torch.Generator().manual_seed(args.seed))
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=args.batch_size, shuffle=False)
    print(f"[data] train={n_train}  val={n_val}  device={device}")

    model = EinsteinCNN().to(device)
    print(f"[model] params={sum(p.numel() for p in model.parameters())/1e6:.2f}M")
    loss_fn = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    best = float("inf")
    for epoch in range(1, args.epochs + 1):
        model.train(); running = 0.0
        for img, y in train_loader:
            img, y = img.to(device), y.to(device)
            optimizer.zero_grad()
            loss = loss_fn(model(img), y)
            loss.backward(); optimizer.step()
            running += loss.item() * img.size(0)
        val_mae, val_frac, val_r2, _, _ = evaluate(model, val_loader, device)
        print(f"epoch {epoch:3d} | train_mse {running/n_train:.4f} | "
              f"val_MAE {val_mae:.4f} | val_frac {val_frac:.1f}% | val_R2 {val_r2:.3f}")
        if val_mae < best:
            best = val_mae
            torch.save(model.state_dict(), args.out_ckpt)
    print(f"\n[done] best val MAE = {best:.4f} -> {args.out_ckpt}")


if __name__ == "__main__":
    main()
