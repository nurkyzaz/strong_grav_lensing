#!/usr/bin/env python
"""Model 2: predict theta_E in ARCSEC from a varied-FOV lensed image PLUS the
angular pixel scale fed in as a scalar. Labels joined by kappa_index (alignment-safe);
"visible arc" selection = theta_E RANGE cut [min,max] in arcsec (matches LensFusion)."""
import argparse, h5py, numpy as np, torch, torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split

PIX_SCALE_M1 = 7.68 / 127  # 0.0605"/px, model-1 fixed scale (fallback conversion)

def load_theta_pixels(label_file):
    with h5py.File(label_file, "r") as f:
        kidx = f["kappa_index"][:].astype("int64")
        if "theta_E_pixels" in f:
            tp = f["theta_E_pixels"][:].astype("float32")
        elif "theta_E" in f:
            tp = f["theta_E"][:].astype("float32") / PIX_SCALE_M1
        else:
            raise ValueError("label file needs 'theta_E_pixels' or 'theta_E'")
    lut = np.full(int(kidx.max()) + 1, np.nan, dtype="float32")
    lut[kidx] = tp
    return lut

class LensedScaleDataset(Dataset):
    def __init__(self, image_file, label_file, pixels=128,
                 min_theta_e=0.5, max_theta_e=2.5, normalize=True, scale_stats=None):
        with h5py.File(image_file, "r") as f:
            images = f["lensed"][:].astype("float32")
            kidx   = f["kappa_index"][:].astype("int64")
            fov = (f["image_fov"][:].astype("float32") if "image_fov" in f
                   else np.full(len(images), 7.68, dtype="float32"))
        lut = load_theta_pixels(label_file)
        if kidx.max() >= len(lut) or np.isnan(lut[kidx]).any():
            raise ValueError("some images have no label; run compute_labels over ALL maps")

        theta_pix = lut[kidx]
        pix_scale = fov / (pixels - 1)
        theta_arc = theta_pix * pix_scale

        keep = (theta_arc >= min_theta_e) & (theta_arc <= max_theta_e)
        n0 = len(images)
        images, theta_arc, pix_scale, kidx = (images[keep], theta_arc[keep],
                                              pix_scale[keep], kidx[keep])
        print(f"[data] kept {int(keep.sum())}/{n0} after theta_E in "
              f"[{min_theta_e},{max_theta_e}] arcsec (post-zoom label)")

        if normalize:
            mn = images.min(axis=(1, 2), keepdims=True)
            mx = images.max(axis=(1, 2), keepdims=True)
            images = (images - mn) / (mx - mn + 1e-8)

        if scale_stats is None:
            self.s_mean = float(pix_scale.mean()); self.s_std = float(pix_scale.std() + 1e-8)
        else:
            self.s_mean, self.s_std = scale_stats
        self.images, self.theta_arc, self.pix_scale, self.kidx = images, theta_arc, pix_scale, kidx

    def stats(self): return (self.s_mean, self.s_std)
    def __len__(self): return len(self.images)
    def __getitem__(self, i):
        img = torch.from_numpy(self.images[i]).unsqueeze(0)
        s = torch.tensor([(self.pix_scale[i] - self.s_mean) / self.s_std], dtype=torch.float32)
        y = torch.tensor(self.theta_arc[i], dtype=torch.float32)
        return img, s, y

def augment_batch(img):
    if torch.rand(1).item() < 0.5: img = torch.flip(img, dims=[-1])
    if torch.rand(1).item() < 0.5: img = torch.flip(img, dims=[-2])
    k = int(torch.randint(0, 4, (1,)).item())
    if k: img = torch.rot90(img, k, dims=[-2, -1])
    return img

class ResidualBlock(nn.Module):
    def __init__(self, in_ch, out_ch, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_ch, out_ch, 3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_ch)
        self.conv2 = nn.Conv2d(out_ch, out_ch, 3, 1, 1, bias=False)
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
        return self.relu(out + self.shortcut(x))

class EinsteinCNNScale(nn.Module):
    def __init__(self, channels=(32, 64, 128, 256)):
        super().__init__()
        c0, c1, c2, c3 = channels
        self.stem = nn.Sequential(
            nn.Conv2d(1, c0, 7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(c0), nn.ReLU(inplace=True))
        self.layer1 = nn.Sequential(ResidualBlock(c0, c0), ResidualBlock(c0, c0))
        self.layer2 = nn.Sequential(ResidualBlock(c0, c1, 2), ResidualBlock(c1, c1))
        self.layer3 = nn.Sequential(ResidualBlock(c1, c2, 2), ResidualBlock(c2, c2))
        self.layer4 = nn.Sequential(ResidualBlock(c2, c3, 2), ResidualBlock(c3, c3))
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.head = nn.Sequential(nn.Linear(c3 + 1, 128), nn.ReLU(inplace=True), nn.Linear(128, 1))
    def forward(self, x, scale):
        x = self.stem(x)
        x = self.layer1(x); x = self.layer2(x); x = self.layer3(x); x = self.layer4(x)
        x = self.gap(x).flatten(1)
        x = torch.cat([x, scale], dim=1)
        return self.head(x).squeeze(1)

def evaluate(model, loader, device):
    model.eval(); preds, trues = [], []
    with torch.no_grad():
        for img, s, y in loader:
            preds.append(model(img.to(device), s.to(device)).cpu().numpy())
            trues.append(y.numpy())
    preds = np.concatenate(preds); trues = np.concatenate(trues)
    mae = float(np.mean(np.abs(preds - trues)))
    frac = float(100 * np.median(np.abs(preds - trues) / trues))
    p16, p84 = np.percentile(100 * (preds - trues) / trues, [16, 84])
    ss_res = np.sum((trues - preds) ** 2); ss_tot = np.sum((trues - trues.mean()) ** 2)
    return mae, frac, float(1 - ss_res / ss_tot), (float(p16), float(p84))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image_file", default="lensed_train_m2.h5")
    ap.add_argument("--label_file", default="labels_train_singleband.h5")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--val_frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out_ckpt", default="einstein_cnn_m2.pt")
    ap.add_argument("--min_theta_e", type=float, default=0.5)
    ap.add_argument("--max_theta_e", type=float, default=2.5)
    ap.add_argument("--loss", choices=["mse", "huber"], default="mse")
    ap.add_argument("--augment", action="store_true")
    args = ap.parse_args()

    torch.manual_seed(args.seed); np.random.seed(args.seed)
    device = torch.device(args.device)

    full = LensedScaleDataset(args.image_file, args.label_file,
                              min_theta_e=args.min_theta_e, max_theta_e=args.max_theta_e)
    n_val = int(len(full) * args.val_frac); n_train = len(full) - n_val
    train_set, val_set = random_split(full, [n_train, n_val],
                                      generator=torch.Generator().manual_seed(args.seed))
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True)
    val_loader   = DataLoader(val_set, batch_size=args.batch_size, shuffle=False)
    print(f"[data] train={n_train} val={n_val} device={device} | "
          f"scale_norm mean {full.s_mean:.5f} std {full.s_std:.5f}")

    model = EinsteinCNNScale().to(device)
    print(f"[model] params={sum(p.numel() for p in model.parameters())/1e6:.2f}M")
    loss_fn = nn.MSELoss() if args.loss == "mse" else nn.SmoothL1Loss()
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)

    best = float("inf")
    for epoch in range(1, args.epochs + 1):
        model.train(); running = 0.0
        for img, s, y in train_loader:
            if args.augment: img = augment_batch(img)
            img, s, y = img.to(device), s.to(device), y.to(device)
            opt.zero_grad()
            loss = loss_fn(model(img, s), y)
            loss.backward(); opt.step()
            running += loss.item() * img.size(0)
        sched.step()
        mae, frac, r2, (p16, p84) = evaluate(model, val_loader, device)
        print(f"epoch {epoch:3d} | train_{args.loss} {running/n_train:.4f} | "
              f"val_MAE {mae:.4f} | val_frac {frac:.2f}% | val_R2 {r2:.3f} | "
              f"16-84% [{p16:+.1f},{p84:+.1f}]")
        if mae < best:
            best = mae
            torch.save({"state_dict": model.state_dict(),
                        "scale_mean": full.s_mean, "scale_std": full.s_std,
                        "channels": (32, 64, 128, 256), "pixels": 128}, args.out_ckpt)
    print(f"\n[done] best val MAE = {best:.4f} arcsec -> {args.out_ckpt}")

if __name__ == "__main__":
    main()
