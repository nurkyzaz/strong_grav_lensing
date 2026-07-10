#!/usr/bin/env python
"""Add the GEN4-NET 'logpolar' architecture to train_cnn_paltas.py
(P6, Nurkyz 2026-07-10: task-specific net). Backup .bak_logpolar."""
import os
import shutil

F = os.path.expanduser("~/einstein_cnn/train_cnn_paltas.py")
src = open(F).read()
if "LogPolarScale" in src:
    raise SystemExit("already patched")

CLS = '''

class LogPolarScale(nn.Module):
    """GEN4-NET (P6): task-specific theta_E architecture.
    Polar branch: the image is resampled to (r, phi) around the centre, so a
    ring becomes a horizontal line whose ROW IS theta_E -- radius estimation
    turns into 1-D localization, rotation invariance comes free from phi
    pooling, and no stride ever destroys radial resolution (strides act on
    phi only). Cartesian branch: small strided CNN for global context incl.
    deflector photometry (the Faber-Jackson light->mass channel). Fusion with
    the peak-scale scalar -> out_dim head (2 = Gaussian NLL)."""

    def __init__(self, out_dim=1, n_r=64, n_phi=96, r_min=1.5, r_max=62.0, img=128):
        super().__init__()
        self.out_dim = out_dim
        rr = torch.linspace(r_min, r_max, n_r)
        pp = torch.linspace(0, 2 * float(np.pi), n_phi + 1)[:-1]
        c = (img - 1) / 2.0
        gx = (c + rr[:, None] * torch.cos(pp[None, :])) / (img - 1) * 2 - 1
        gy = (c + rr[:, None] * torch.sin(pp[None, :])) / (img - 1) * 2 - 1
        self.register_buffer("pgrid", torch.stack([gx, gy], dim=-1).unsqueeze(0))

        def blk(i, o, s):
            return nn.Sequential(
                nn.Conv2d(i, o, 3, stride=(1, s), padding=1,
                          padding_mode="circular", bias=False),
                nn.BatchNorm2d(o), nn.ReLU(inplace=True))
        self.polar = nn.Sequential(blk(1, 32, 2), blk(32, 64, 2),
                                   blk(64, 64, 2), blk(64, 64, 2))
        self.radial = nn.Sequential(
            nn.Conv1d(64, 64, 5, padding=2), nn.ReLU(inplace=True),
            nn.Conv1d(64, 64, 5, padding=2), nn.ReLU(inplace=True))
        self.cart = nn.Sequential(
            nn.Conv2d(1, 16, 7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(16), nn.ReLU(inplace=True),
            nn.Conv2d(16, 32, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(32), nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, 3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(64), nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1))
        self.head = nn.Sequential(nn.Linear(64 * 2 + 64 + 1, 128),
                                  nn.ReLU(inplace=True), nn.Linear(128, out_dim))

    def forward(self, x, s):
        b = x.shape[0]
        pol = torch.nn.functional.grid_sample(
            x, self.pgrid.expand(b, -1, -1, -1), align_corners=True)
        f = self.polar(pol)          # [b, 64, n_r, n_phi/16]
        f = f.mean(dim=3)            # phi pooling -> [b, 64, n_r]
        f = self.radial(f)
        rad = torch.cat([f.mean(dim=2), f.max(dim=2).values], dim=1)
        cart = self.cart(x).flatten(1)
        return self.head(torch.cat([rad, cart, s], dim=1))


def build_model(arch, out_dim):'''

A1 = "def build_model(arch, out_dim):"
A2 = '    if arch in ("convnextv2", "resnet50"):'
A3 = 'choices=["resnet", "inceptionnext", "convnextv2", "resnet50"]'
for a in (A1, A2, A3):
    if a not in src:
        raise SystemExit("anchor missing: %r" % a)
shutil.copy(F, F + ".bak_logpolar")
src = src.replace(A1, CLS, 1)
src = src.replace(A2, '''    if arch == "logpolar":
        return LogPolarScale(out_dim=out_dim)
''' + A2, 1)
src = src.replace(A3, 'choices=["resnet", "inceptionnext", "convnextv2", "resnet50", "logpolar"]', 1)
open(F, "w").write(src)
print("patched: +LogPolarScale (backup .bak_logpolar)")
