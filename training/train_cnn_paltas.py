#!/usr/bin/env python
"""Stage 3: train the m3-style scale-conditioned ResNet on the Stage-2 paltas
hybrid dataset (train_hybrid_100k.h5 / val_hybrid_5k.h5).

Architecture, asinh input normalization, Huber loss, Adam, and flip/rotation
augmentation are all kept IDENTICAL to train_cnn_m3.py (MASTER_PLAN 3.1: the
only required change is reading theta_E per-image directly -- no kappa_index
join, no theta_E**2 reweighting, both hazards are gone with paltas labels).

Model selection uses the DEDICATED val_hybrid_5k.h5 (seed- and PSF-kernel-
disjoint from every train shard) instead of a random split of train, per
MASTER_PLAN 3.4 -- the frozen 62+40 real-lens benchmark is untouched here.

Point-estimate head only for this first run (no Gaussian-NLL uncertainty
head yet, per MASTER_PLAN 3.3's own escape clause: verify the base pipeline
trains cleanly on the brand-new dataset before adding complexity).
"""
import argparse
import h5py
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader


def normalize_images(images, norm, asinh_a):
    """Per-image. 'asinh' compresses a bright lens centre while keeping the
    arc distinguishable from noise; 'minmax' is the old model-1/2 behaviour."""
    if norm == "asinh":
        x = np.arcsinh(images / asinh_a)
        mn = x.mean(axis=(1, 2), keepdims=True)
        sd = x.std(axis=(1, 2), keepdims=True) + 1e-8
        return ((x - mn) / sd).astype("float32")
    elif norm == "minmax":
        mn = images.min(axis=(1, 2), keepdims=True)
        mx = images.max(axis=(1, 2), keepdims=True)
        return ((images - mn) / (mx - mn + 1e-8)).astype("float32")
    raise ValueError(f"unknown norm {norm}")


class HybridLensDataset(Dataset):
    def __init__(self, h5_path, pixels=128, min_theta_e=0.5, max_theta_e=2.5,
                 norm="asinh", asinh_a=1.0, scale_stats=None, limit=None):
        with h5py.File(h5_path, "r") as f:
            n_avail = f["lensed"].shape[0]
            n = n_avail if limit is None else min(limit, n_avail)
            images = f["lensed"][:n].astype("float32")
            theta = f["theta_E"][:n].astype("float32")
            fov = (f["image_fov"][:n].astype("float32") if "image_fov" in f
                   else np.full(n, 6.4, dtype="float32"))

        keep = (theta >= min_theta_e) & (theta <= max_theta_e)
        n0 = len(images)
        images, theta, fov = images[keep], theta[keep], fov[keep]
        print(f"[data] {h5_path}: kept {int(keep.sum())}/{n0} in "
              f"[{min_theta_e},{max_theta_e}] arcsec | norm={norm} (a={asinh_a})")

        pix_scale = fov / (pixels - 1)
        images = normalize_images(images, norm, asinh_a)

        if scale_stats is None:
            self.s_mean = float(pix_scale.mean())
            self.s_std = float(pix_scale.std())
            if self.s_std < 1e-6:
                # fixed-FOV dataset: scale input is degenerate. Use std=1 so
                # s == 0 exactly at train AND predict (audit 2026-07-06: the
                # old +1e-8 floor made inference feed s=+0.09 through
                # never-trained weights; effect measured negligible, fixed
                # anyway).
                self.s_std = 1.0
        else:
            self.s_mean, self.s_std = scale_stats
        self.images, self.theta, self.pix_scale = images, theta, pix_scale

    def stats(self):
        return (self.s_mean, self.s_std)

    def __len__(self):
        return len(self.images)

    def __getitem__(self, i):
        img = torch.from_numpy(self.images[i]).unsqueeze(0)
        s = torch.tensor([(self.pix_scale[i] - self.s_mean) / self.s_std],
                         dtype=torch.float32)
        y = torch.tensor(self.theta[i], dtype=torch.float32)
        return img, s, y


def augment_batch(img):
    if torch.rand(1).item() < 0.5:
        img = torch.flip(img, dims=[-1])
    if torch.rand(1).item() < 0.5:
        img = torch.flip(img, dims=[-2])
    k = int(torch.randint(0, 4, (1,)).item())
    if k:
        img = torch.rot90(img, k, dims=[-2, -1])
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
    """out_dim=1: point estimate (m3-compatible). out_dim=2: (mu, log sigma^2)
    Gaussian-NLL head (MASTER_PLAN 3.3) -- per-lens error bars + Phase-2
    weighting; same backbone either way."""

    def __init__(self, channels=(32, 64, 128, 256), out_dim=1):
        super().__init__()
        c0, c1, c2, c3 = channels
        self.out_dim = out_dim
        self.stem = nn.Sequential(
            nn.Conv2d(1, c0, 7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(c0), nn.ReLU(inplace=True))
        self.layer1 = nn.Sequential(ResidualBlock(c0, c0), ResidualBlock(c0, c0))
        self.layer2 = nn.Sequential(ResidualBlock(c0, c1, 2), ResidualBlock(c1, c1))
        self.layer3 = nn.Sequential(ResidualBlock(c1, c2, 2), ResidualBlock(c2, c2))
        self.layer4 = nn.Sequential(ResidualBlock(c2, c3, 2), ResidualBlock(c3, c3))
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.head = nn.Sequential(nn.Linear(c3 + 1, 128), nn.ReLU(inplace=True),
                                  nn.Linear(128, out_dim))

    def features(self, x):
        """Latent embedding (post-GAP, pre-head) — the MMD alignment layer,
        following Agarwal, Ciprijanovic & Nord 2025 (arXiv:2411.03334)."""
        x = self.stem(x)
        x = self.layer1(x); x = self.layer2(x); x = self.layer3(x); x = self.layer4(x)
        return self.gap(x).flatten(1)

    def style_stats(self, x):
        """Shallow STYLE statistics: per-channel spatial mean+std of layer1
        and layer2 feature maps. Captures low-level domain style (noise
        texture, PSF, background structure) while excluding the deep
        label-carrying representation — the DA-v2 alignment target after
        DA-v1's label-shift failure (DECISIONS_LOG 2026-07-07)."""
        h = self.stem(x)
        h = self.layer1(h)
        s1 = torch.cat([h.mean(dim=(2, 3)), h.std(dim=(2, 3))], dim=1)
        h = self.layer2(h)
        s2 = torch.cat([h.mean(dim=(2, 3)), h.std(dim=(2, 3))], dim=1)
        return torch.cat([s1, s2], dim=1)

    def forward(self, x, scale):
        f = self.features(x)
        out = self.head(torch.cat([f, scale], dim=1))
        return out.squeeze(1) if self.out_dim == 1 else out


def gaussian_nll(out, y):
    """out: [B,2] = (mu, log sigma^2). Clamped logvar for stability."""
    mu, logvar = out[:, 0], out[:, 1].clamp(-10.0, 3.0)
    return (0.5 * (logvar + (y - mu) ** 2 / torch.exp(logvar))).mean()


def mmd2_multikernel(f_s, f_t, scales=(0.25, 0.5, 1.0, 2.0, 4.0)):
    """Multi-kernel RBF MMD^2 between source and target embeddings, with the
    median-distance heuristic setting the base bandwidth (detached)."""
    n_s, n_t = len(f_s), len(f_t)
    f = torch.cat([f_s, f_t], dim=0)
    d2 = torch.cdist(f, f) ** 2
    with torch.no_grad():
        base = d2.flatten().median().clamp_min(1e-6)
    k = sum(torch.exp(-d2 / (base * s)) for s in scales) / len(scales)
    k_ss = k[:n_s, :n_s]
    k_tt = k[n_s:, n_s:]
    k_st = k[:n_s, n_s:]
    return k_ss.mean() + k_tt.mean() - 2 * k_st.mean()


class RealPoolSampler:
    """Serves random, dihedral-augmented batches from the small unlabeled real
    pool (benchmark-DISJOINT by construction, see build_da_pool.py). Images
    get the identical asinh normalization as the training set."""

    def __init__(self, h5_path, norm, asinh_a, seed=0):
        with h5py.File(h5_path, "r") as f:
            key = "images" if "images" in f else "lensed"
            imgs = f[key][:].astype("float32")
        if imgs.ndim == 4:
            imgs = imgs[:, 0]
        self.x = torch.from_numpy(normalize_images(imgs, norm, asinh_a))
        self.g = torch.Generator().manual_seed(seed)
        print(f"[da] real pool: {len(self.x)} images from {h5_path}")

    def batch(self, n, device):
        idx = torch.randint(0, len(self.x), (n,), generator=self.g)
        b = self.x[idx].unsqueeze(1).clone()
        if torch.rand(1, generator=self.g).item() < 0.5:
            b = torch.flip(b, dims=[-1])
        k = int(torch.randint(0, 4, (1,), generator=self.g).item())
        if k:
            b = torch.rot90(b, k, dims=[-2, -1])
        return b.to(device)


# =========================================================================
# InceptionNeXt backbone (arXiv:2303.16900), self-contained (no timm),
# adapted for 1-channel 128px input + scale conditioning + optional NLL head.
# Faithful to the official sail-sg/inceptionnext modules.
# =========================================================================
class InceptionDWConv2d(nn.Module):
    """Inception depthwise conv: identity + small square + two orthogonal
    band branches, split along the channel dim."""
    def __init__(self, in_ch, square_k=3, band_k=11, branch_ratio=0.125):
        super().__init__()
        gc = int(in_ch * branch_ratio)
        self.dwconv_hw = nn.Conv2d(gc, gc, square_k, padding=square_k // 2, groups=gc)
        self.dwconv_w = nn.Conv2d(gc, gc, (1, band_k), padding=(0, band_k // 2), groups=gc)
        self.dwconv_h = nn.Conv2d(gc, gc, (band_k, 1), padding=(band_k // 2, 0), groups=gc)
        self.split = (in_ch - 3 * gc, gc, gc, gc)

    def forward(self, x):
        x_id, x_hw, x_w, x_h = torch.split(x, self.split, dim=1)
        return torch.cat([x_id, self.dwconv_hw(x_hw), self.dwconv_w(x_w),
                          self.dwconv_h(x_h)], dim=1)


class ConvMlp(nn.Module):
    def __init__(self, in_f, hidden_f, act=nn.GELU):
        super().__init__()
        self.fc1 = nn.Conv2d(in_f, hidden_f, 1)
        self.act = act()
        self.fc2 = nn.Conv2d(hidden_f, in_f, 1)

    def forward(self, x):
        return self.fc2(self.act(self.fc1(x)))


class MetaNeXtBlock(nn.Module):
    def __init__(self, dim, mlp_ratio=4, ls_init=1e-6):
        super().__init__()
        self.token_mixer = InceptionDWConv2d(dim)
        self.norm = nn.BatchNorm2d(dim)
        self.mlp = ConvMlp(dim, int(mlp_ratio * dim))
        self.gamma = nn.Parameter(ls_init * torch.ones(dim)) if ls_init else None

    def forward(self, x):
        shortcut = x
        x = self.token_mixer(x)
        x = self.norm(x)
        x = self.mlp(x)
        if self.gamma is not None:
            x = x * self.gamma.reshape(1, -1, 1, 1)
        return x + shortcut


class MetaNeXtStage(nn.Module):
    def __init__(self, in_ch, out_ch, ds_stride, depth, mlp_ratio):
        super().__init__()
        if ds_stride > 1:
            self.downsample = nn.Sequential(
                nn.BatchNorm2d(in_ch),
                nn.Conv2d(in_ch, out_ch, ds_stride, stride=ds_stride))
        else:
            self.downsample = nn.Identity()
        self.blocks = nn.Sequential(
            *[MetaNeXtBlock(out_ch, mlp_ratio) for _ in range(depth)])

    def forward(self, x):
        return self.blocks(self.downsample(x))


class InceptionNeXtScale(nn.Module):
    """InceptionNeXt with a scale-conditioned regression head (θ_E).
    out_dim: 1 point estimate (m3-compatible) or 2 (mu, log sigma^2) NLL."""
    def __init__(self, depths=(2, 2, 6, 2), dims=(48, 96, 192, 384),
                 mlp_ratios=(4, 4, 4, 3), out_dim=1):
        super().__init__()
        self.out_dim = out_dim
        self.stem = nn.Sequential(
            nn.Conv2d(1, dims[0], kernel_size=4, stride=4),
            nn.BatchNorm2d(dims[0]))
        stages = []
        prev = dims[0]
        for i in range(len(depths)):
            stages.append(MetaNeXtStage(prev, dims[i], ds_stride=2 if i > 0 else 1,
                                        depth=depths[i], mlp_ratio=mlp_ratios[i]))
            prev = dims[i]
        self.stages = nn.Sequential(*stages)
        self.norm = nn.BatchNorm2d(prev)
        self.head = nn.Sequential(nn.Linear(prev + 1, 128), nn.GELU(),
                                  nn.Linear(128, out_dim))

    def features(self, x):
        x = self.stem(x)
        x = self.stages(x)
        x = self.norm(x)
        return x.mean((2, 3))

    def forward(self, x, scale):
        f = self.features(x)
        out = self.head(torch.cat([f, scale], dim=1))
        return out.squeeze(1) if self.out_dim == 1 else out


def build_model(arch, out_dim):
    if arch == "resnet":
        return EinsteinCNNScale(out_dim=out_dim)
    if arch == "inceptionnext":
        return InceptionNeXtScale(out_dim=out_dim)
    raise ValueError(f"unknown arch {arch}")


def evaluate(model, loader, device):
    model.eval(); preds, trues = [], []
    with torch.no_grad():
        for img, s, y in loader:
            out = model(img.to(device), s.to(device))
            if out.ndim == 2:
                out = out[:, 0]  # NLL head: use mu
            preds.append(out.cpu().numpy())
            trues.append(y.numpy())
    preds = np.concatenate(preds); trues = np.concatenate(trues)
    mae = float(np.mean(np.abs(preds - trues)))
    frac = float(100 * np.median(np.abs(preds - trues) / trues))
    p16, p84 = np.percentile(100 * (preds - trues) / trues, [16, 84])
    ss_res = np.sum((trues - preds) ** 2); ss_tot = np.sum((trues - trues.mean()) ** 2)
    return mae, frac, float(1 - ss_res / ss_tot), (float(p16), float(p84))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_file", default="/home/user/nurkyz/einstein_cnn/train_hybrid_100k.h5")
    ap.add_argument("--val_file", default="/home/user/nurkyz/einstein_cnn/val_hybrid_5k.h5")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out_ckpt", default="einstein_cnn_paltas_v1.pt")
    ap.add_argument("--min_theta_e", type=float, default=0.4)
    ap.add_argument("--max_theta_e", type=float, default=2.5)
    ap.add_argument("--loss", choices=["mse", "huber"], default="huber")
    ap.add_argument("--arch", choices=["resnet", "inceptionnext"], default="resnet",
                    help="backbone: resnet (m3 baseline) or inceptionnext "
                         "(arXiv:2303.16900)")
    ap.add_argument("--nll", action="store_true",
                    help="train (mu, log sigma^2) Gaussian-NLL head instead of "
                         "a point estimate (MASTER_PLAN 3.3)")
    ap.add_argument("--da_pool", default=None,
                    help="h5 of UNLABELED real images (benchmark-disjoint) for "
                         "sim-to-real MMD domain adaptation (MASTER_PLAN D4)")
    ap.add_argument("--da_weight", type=float, default=1.4,
                    help="alpha_UDA: weight of the MMD loss (1.4 follows "
                         "Agarwal et al. 2025)")
    ap.add_argument("--da_mode", choices=["embed", "style"], default="embed",
                    help="embed: MMD on the post-GAP semantic embedding (DA-v1, "
                         "fails under label shift); style: MMD on shallow "
                         "per-channel mean/std stats (DA-v2, label-shift-robust)")
    ap.add_argument("--da_warmup", type=int, default=0,
                    help="epochs of linear ramp-up for the DA weight")
    ap.add_argument("--init_ckpt", default=None,
                    help="fine-tune from this checkpoint instead of scratch")
    ap.add_argument("--norm", choices=["asinh", "minmax"], default="asinh")
    ap.add_argument("--asinh_a", type=float, default=1.0)
    ap.add_argument("--augment", action="store_true", default=True)
    ap.add_argument("--train_limit", type=int, default=None,
                    help="load only first N train images (smoke test)")
    ap.add_argument("--val_limit", type=int, default=None,
                    help="load only first N val images (smoke test)")
    args = ap.parse_args()

    torch.manual_seed(args.seed); np.random.seed(args.seed)
    device = torch.device(args.device)

    train_set = HybridLensDataset(args.train_file, min_theta_e=args.min_theta_e,
                                  max_theta_e=args.max_theta_e, norm=args.norm,
                                  asinh_a=args.asinh_a, limit=args.train_limit)
    val_set = HybridLensDataset(args.val_file, min_theta_e=args.min_theta_e,
                                max_theta_e=args.max_theta_e, norm=args.norm,
                                asinh_a=args.asinh_a, scale_stats=train_set.stats(),
                                limit=args.val_limit)
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True,
                              num_workers=2, drop_last=True)
    val_loader = DataLoader(val_set, batch_size=args.batch_size, shuffle=False,
                            num_workers=2)
    print(f"[data] train={len(train_set)} val={len(val_set)} device={device} | "
          f"scale_norm mean {train_set.s_mean:.5f} std {train_set.s_std:.5f}")

    out_dim = 2 if args.nll else 1
    model = build_model(args.arch, out_dim).to(device)
    if args.init_ckpt:
        ick = torch.load(args.init_ckpt, map_location=device)
        model.load_state_dict(ick["state_dict"])
        print(f"[model] fine-tuning from {args.init_ckpt}")
    print(f"[model] arch={args.arch} "
          f"params={sum(p.numel() for p in model.parameters())/1e6:.2f}M "
          f"| head={'gaussian-NLL (mu, logvar)' if args.nll else 'point estimate'}")
    if args.nll:
        loss_fn = gaussian_nll
    else:
        loss_fn = nn.MSELoss() if args.loss == "mse" else nn.SmoothL1Loss()
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)

    pool = None
    if args.da_pool:
        pool = RealPoolSampler(args.da_pool, args.norm, args.asinh_a, seed=args.seed)

    best = float("inf")
    for epoch in range(1, args.epochs + 1):
        model.train(); running = 0.0; running_mmd = 0.0; nb = 0
        for img, s, y in train_loader:
            if args.augment:
                img = augment_batch(img)
            img, s, y = img.to(device), s.to(device), y.to(device)
            opt.zero_grad()
            if pool is not None:
                alpha = args.da_weight * (min(epoch / args.da_warmup, 1.0)
                                          if args.da_warmup > 0 else 1.0)
                real_batch = pool.batch(img.size(0), device)
                if args.da_mode == "style":
                    task = loss_fn(model(img, s), y)
                    mmd = mmd2_multikernel(model.style_stats(img),
                                           model.style_stats(real_batch))
                else:
                    f_sim = model.features(img)
                    out = model.head(torch.cat([f_sim, s], dim=1))
                    if model.out_dim == 1:
                        out = out.squeeze(1)
                    task = loss_fn(out, y)
                    mmd = mmd2_multikernel(f_sim, model.features(real_batch))
                loss = task + alpha * mmd
                running_mmd += mmd.item(); nb += 1
            else:
                task = loss_fn(model(img, s), y)
                loss = task
            loss.backward(); opt.step()
            running += task.item() * img.size(0)
        sched.step()
        mae, frac, r2, (p16, p84) = evaluate(model, val_loader, device)
        da_str = f" | mmd {running_mmd/max(nb,1):.4f}" if pool is not None else ""
        print(f"epoch {epoch:3d} | train_{args.loss} {running/len(train_set):.4f}{da_str} | "
              f"val_MAE {mae:.4f} | val_frac {frac:.2f}% | val_R2 {r2:.3f} | "
              f"16-84% [{p16:+.1f},{p84:+.1f}]", flush=True)
        if mae < best:
            best = mae
            torch.save({"state_dict": model.state_dict(),
                        "scale_mean": train_set.s_mean, "scale_std": train_set.s_std,
                        "channels": (32, 64, 128, 256), "pixels": 128,
                        "arch": args.arch,
                        "out_dim": out_dim, "nll": args.nll,
                        "da_pool": args.da_pool, "da_weight": args.da_weight,
                        "da_mode": args.da_mode, "init_ckpt": args.init_ckpt,
                        "norm": args.norm, "asinh_a": args.asinh_a,
                        "train_file": args.train_file, "val_file": args.val_file},
                       args.out_ckpt)
    print(f"\n[done] best val MAE = {best:.4f} arcsec -> {args.out_ckpt}")


if __name__ == "__main__":
    main()
