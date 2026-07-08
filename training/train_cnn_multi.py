#!/usr/bin/env python
"""Phase 1b multi-output: theta_E (arcsec), e1, e2, lens-centre offset (dx,dy px).
v2 FIX: orientation-aware augmentation. Flips/rot90 transform the IMAGE *and* the
orientation-dependent labels (e1,e2,dx,dy); theta_E is invariant. Without this, --augment
silently forces e1/e2/centre R2 -> 0. Standardisation is applied in the train/eval loop so
raw labels can be transformed first.
Validated label transforms (col=x, row=y):
  flip x (dims=-1): e2->-e2, dx->-dx     flip y (dims=-2): e2->-e2, dy->-dy
  rot90 (per step): e1->-e1, e2->-e2, (dx,dy)->(dy,-dx)
"""
import argparse, h5py, numpy as np, torch, torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split
from train_cnn_m3 import load_theta_pixels, normalize_images, ResidualBlock

PIX_CENTER = 63.5
TARGETS = ["theta_E", "e1", "e2", "dx", "dy"]

def load_ellip(ellip_file):
    with h5py.File(ellip_file, "r") as f:
        kidx = f["kappa_index"][:].astype("int64")
        cols = {k: f[k][:].astype("float32") for k in
                ("e1_fit","e2_fit","cx","cy","rms_fit","ok_fit")}
    n = int(kidx.max()) + 1
    out = {k: np.full(n, np.nan, dtype="float32") for k in cols}
    for k in cols: out[k][kidx] = cols[k]
    return out

class MultiDataset(Dataset):
    def __init__(self, image_file, label_file, ellip_file, pixels=128,
                 min_theta_e=0.5, max_theta_e=2.5, norm="asinh", asinh_a=1.0,
                 rms_cut=0.2, stats=None):
        with h5py.File(image_file, "r") as f:
            images = f["lensed"][:].astype("float32")
            kidx   = f["kappa_index"][:].astype("int64")
            fov = (f["image_fov"][:].astype("float32") if "image_fov" in f
                   else np.full(len(images), 7.68, dtype="float32"))
        lut = load_theta_pixels(label_file)
        theta_arc = lut[kidx] * (fov / (pixels - 1))
        pix_scale = fov / (pixels - 1)
        keep = (theta_arc >= min_theta_e) & (theta_arc <= max_theta_e) & np.isfinite(theta_arc)
        images, theta_arc, pix_scale, kidx = images[keep], theta_arc[keep], pix_scale[keep], kidx[keep]

        E = load_ellip(ellip_file)
        e1, e2 = E["e1_fit"][kidx], E["e2_fit"][kidx]
        dx, dy = E["cx"][kidx] - PIX_CENTER, E["cy"][kidx] - PIX_CENTER
        rms, ok = E["rms_fit"][kidx], E["ok_fit"][kidx]
        valid = (ok == 1.0) & np.isfinite(e1) & (rms <= rms_cut)
        for a in (e1, e2, dx, dy): a[~valid] = 0.0

        self.images = normalize_images(images, norm, asinh_a)
        self.Y = np.stack([theta_arc, e1, e2, dx, dy], axis=1).astype("float32")  # RAW
        self.pix_scale = pix_scale; self.valid = valid.astype("float32")

        if stats is None:
            s_mean = float(pix_scale.mean()); s_std = float(pix_scale.std() + 1e-8)
            ymean = np.zeros(5, "float32"); ystd = np.ones(5, "float32")
            ymean[0], ystd[0] = self.Y[:,0].mean(), self.Y[:,0].std() + 1e-8
            for c in (1,2,3,4):
                ymean[c], ystd[c] = self.Y[valid,c].mean(), self.Y[valid,c].std() + 1e-8
        else:
            s_mean, s_std, ymean, ystd = stats
        self.s_mean, self.s_std, self.ymean, self.ystd = s_mean, s_std, ymean, ystd
        print(f"[data] kept {int(keep.sum())} | ellip valid {valid.mean()*100:.1f}% (rms<={rms_cut})")

    def stats(self): return (self.s_mean, self.s_std, self.ymean, self.ystd)
    def __len__(self): return len(self.images)
    def __getitem__(self, i):
        img = torch.from_numpy(self.images[i]).unsqueeze(0)
        s = torch.tensor([(self.pix_scale[i]-self.s_mean)/self.s_std], dtype=torch.float32)
        return img, s, torch.from_numpy(self.Y[i]), torch.tensor(self.valid[i])

def augment_multi(img, y):
    """Orientation-aware. img (B,1,H,W); y RAW (B,5)=[theta,e1,e2,dx,dy]."""
    img = img.clone(); y = y.clone()
    for b in range(img.size(0)):
        e1, e2, dx, dy = (y[b,1].item(), y[b,2].item(), y[b,3].item(), y[b,4].item())
        im = img[b]
        if torch.rand(1).item() < 0.5:
            im = torch.flip(im, [-1]); e2 = -e2; dx = -dx
        if torch.rand(1).item() < 0.5:
            im = torch.flip(im, [-2]); e2 = -e2; dy = -dy
        k = int(torch.randint(0, 4, (1,)).item())
        for _ in range(k):
            im = torch.rot90(im, 1, [-2, -1]); e1 = -e1; e2 = -e2; dx, dy = dy, -dx
        img[b] = im; y[b,1], y[b,2], y[b,3], y[b,4] = e1, e2, dx, dy
    return img, y

class EinsteinCNNMulti(nn.Module):
    def __init__(self, channels=(32,64,128,256), n_out=5):
        super().__init__()
        c0,c1,c2,c3 = channels
        self.stem = nn.Sequential(nn.Conv2d(1,c0,7,2,3,bias=False), nn.BatchNorm2d(c0), nn.ReLU(True))
        self.layer1 = nn.Sequential(ResidualBlock(c0,c0), ResidualBlock(c0,c0))
        self.layer2 = nn.Sequential(ResidualBlock(c0,c1,2), ResidualBlock(c1,c1))
        self.layer3 = nn.Sequential(ResidualBlock(c1,c2,2), ResidualBlock(c2,c2))
        self.layer4 = nn.Sequential(ResidualBlock(c2,c3,2), ResidualBlock(c3,c3))
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.head = nn.Sequential(nn.Linear(c3+1,128), nn.ReLU(True), nn.Linear(128,n_out))
    def forward(self, x, scale):
        x = self.stem(x); x = self.layer1(x); x = self.layer2(x); x = self.layer3(x); x = self.layer4(x)
        x = self.gap(x).flatten(1); x = torch.cat([x, scale], dim=1)
        return self.head(x)

def evaluate_multi(model, loader, device, ymean, ystd):
    model.eval(); P=[]; Y=[]; M=[]
    with torch.no_grad():
        for img, s, y, m in loader:
            P.append(model(img.to(device), s.to(device)).cpu().numpy())
            Y.append(y.numpy()); M.append(m.numpy())
    P=np.concatenate(P); Yu=np.concatenate(Y); M=np.concatenate(M).astype(bool)
    Pu = P*ystd + ymean
    pt, yt = Pu[:,0], Yu[:,0]
    res = {"theta": (float(np.mean(np.abs(pt-yt))),
                     float(100*np.median(np.abs(pt-yt)/yt)),
                     float(1 - np.sum((yt-pt)**2)/np.sum((yt-yt.mean())**2)),
                     *[float(v) for v in np.percentile(100*(pt-yt)/yt, [16,84])])}
    if M.sum() > 5:
        for ci,name in [(1,"e1"),(2,"e2")]:
            pe, ye = Pu[M,ci], Yu[M,ci]
            res[name] = (float(np.mean(np.abs(pe-ye))),
                         float(1 - np.sum((ye-pe)**2)/np.sum((ye-ye.mean())**2)))
        res["center"] = (float(np.mean(np.abs(Pu[M,3]-Yu[M,3]))),
                         float(np.mean(np.abs(Pu[M,4]-Yu[M,4]))),
                         float(np.median(np.hypot(Pu[M,3]-Yu[M,3], Pu[M,4]-Yu[M,4]))))
    return res

def fmt(res):
    t = res["theta"]
    s = f"theta MAE {t[0]:.4f} frac {t[1]:.2f}% R2 {t[2]:.3f} [{t[3]:+.1f},{t[4]:+.1f}]"
    if "e1" in res:
        s += f" | e1 MAE {res['e1'][0]:.3f} R2 {res['e1'][1]:.2f} | e2 MAE {res['e2'][0]:.3f} R2 {res['e2'][1]:.2f}"
        s += f" | centre MAE ({res['center'][0]:.2f},{res['center'][1]:.2f})px med {res['center'][2]:.2f}px"
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image_file", default="lensed_train_m3.h5")
    ap.add_argument("--label_file", default="labels_train_singleband.h5")
    ap.add_argument("--ellip_file", default="ellip_train.h5")
    ap.add_argument("--test_image_file", default=None)
    ap.add_argument("--test_label_file", default=None)
    ap.add_argument("--test_ellip_file", default=None)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--val_frac", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out_ckpt", default="einstein_cnn_multi.pt")
    ap.add_argument("--norm", choices=["asinh","minmax"], default="asinh")
    ap.add_argument("--asinh_a", type=float, default=1.0)
    ap.add_argument("--rms_cut", type=float, default=0.2)
    ap.add_argument("--w_theta", type=float, default=1.0)
    ap.add_argument("--w_ellip", type=float, default=0.5)
    ap.add_argument("--w_center", type=float, default=0.3)
    ap.add_argument("--augment", action="store_true", help="orientation-aware flips+rot90")
    args = ap.parse_args()
    torch.manual_seed(args.seed); np.random.seed(args.seed)
    device = torch.device(args.device)

    full = MultiDataset(args.image_file, args.label_file, args.ellip_file,
                        norm=args.norm, asinh_a=args.asinh_a, rms_cut=args.rms_cut)
    n_val = int(len(full)*args.val_frac); n_train = len(full)-n_val
    tr, va = random_split(full, [n_train, n_val],
                          generator=torch.Generator().manual_seed(args.seed))
    tl = DataLoader(tr, batch_size=args.batch_size, shuffle=True)
    vl = DataLoader(va, batch_size=args.batch_size, shuffle=False)
    ymean_t = torch.tensor(full.ymean, device=device); ystd_t = torch.tensor(full.ystd, device=device)
    wcol = torch.tensor([args.w_theta, args.w_ellip, args.w_ellip,
                         args.w_center, args.w_center], device=device)
    print(f"[data] train={n_train} val={n_val} device={device} | augment={args.augment}")

    model = EinsteinCNNMulti().to(device)
    print(f"[model] params={sum(p.numel() for p in model.parameters())/1e6:.2f}M | targets={TARGETS}")
    huber = nn.SmoothL1Loss(reduction="none")
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)

    best = float("inf")
    for epoch in range(1, args.epochs+1):
        model.train(); running = 0.0
        for img, s, y, m in tl:
            if args.augment: img, y = augment_multi(img, y)
            img, s, y, m = img.to(device), s.to(device), y.to(device), m.to(device)
            y_std = (y - ymean_t) / ystd_t
            opt.zero_grad()
            l = huber(model(img, s), y_std) * wcol
            mask = torch.ones_like(l); mask[:,1:] = m.unsqueeze(1)
            loss = (l*mask).sum() / mask.sum()
            loss.backward(); opt.step()
            running += loss.item()*img.size(0)
        sched.step()
        res = evaluate_multi(model, vl, device, full.ymean, full.ystd)
        print(f"epoch {epoch:3d} | train {running/n_train:.4f} | {fmt(res)}")
        if res["theta"][1] < best:
            best = res["theta"][1]
            torch.save({"state_dict": model.state_dict(),
                        "scale_mean": full.s_mean, "scale_std": full.s_std,
                        "ymean": full.ymean, "ystd": full.ystd,
                        "channels": (32,64,128,256), "pixels": 128, "n_out": 5,
                        "targets": TARGETS, "norm": args.norm, "asinh_a": args.asinh_a}, args.out_ckpt)
    print(f"\n[done] best val theta frac = {best:.2f}% -> {args.out_ckpt}")

    if args.test_image_file:
        test = MultiDataset(args.test_image_file, args.test_label_file, args.test_ellip_file,
                            norm=args.norm, asinh_a=args.asinh_a, rms_cut=args.rms_cut,
                            stats=full.stats())
        ck = torch.load(args.out_ckpt, map_location=device)
        model.load_state_dict(ck["state_dict"])
        res = evaluate_multi(model, DataLoader(test, batch_size=args.batch_size),
                             device, full.ymean, full.ystd)
        print(f"[TEST] {fmt(res)}")

if __name__ == "__main__":
    main()
