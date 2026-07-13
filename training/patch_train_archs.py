#!/usr/bin/env python
"""Add 'convnextv2' (FCMAE-pretrained ConvNeXt V2 nano) and 'resnet50'
(LEMON-comparable backbone, IN1k-pretrained) to train_cnn_paltas.py via a
timm wrapper that keeps the (image, scale) conditioning interface.
Backup .bak_archs. Approved by Nurkyz 2026-07-10 (timm install + ResNet-50)."""
import os
import shutil

F = os.path.expanduser("~/einstein_cnn/train_cnn_paltas.py")
src = open(F).read()
if "TimmScale" in src:
    raise SystemExit("already patched")

CLS = '''

class TimmScale(nn.Module):
    """Pretrained timm backbone (grayscale stem auto-adapted from RGB weights)
    + the same scale-conditioning pattern as EinsteinCNNScale: the arcsinh
    peak-scale scalar is concatenated to pooled features before the head.
    convnextv2 = ConvNeXt V2 nano, FCMAE pretraining (arXiv:2301.00808,
    professor + Nurkyz 2026-07-10); resnet50 = the LEMON-comparable backbone."""
    NAMES = {"convnextv2": "convnextv2_nano.fcmae_ft_in22k_in1k",
             "resnet50": "resnet50.a1_in1k"}

    def __init__(self, arch, out_dim=1):
        super().__init__()
        import timm
        self.backbone = timm.create_model(self.NAMES[arch], pretrained=True,
                                          in_chans=1, num_classes=0)
        nf = self.backbone.num_features
        self.head = nn.Sequential(nn.Linear(nf + 1, 256), nn.ReLU(),
                                  nn.Linear(256, out_dim))

    def forward(self, x, s):
        return self.head(torch.cat([self.backbone(x), s], dim=1))


def build_model(arch, out_dim):'''

A1 = "def build_model(arch, out_dim):"
A2 = '    raise ValueError(f"unknown arch {arch}")'
A3 = 'choices=["resnet", "inceptionnext"]'
for a in (A1, A2, A3):
    if a not in src:
        raise SystemExit("anchor missing: %r — abort, inspect manually" % a)

shutil.copy(F, F + ".bak_archs")
src = src.replace(A1, CLS, 1)
src = src.replace(A2, '''    if arch in ("convnextv2", "resnet50"):
        return TimmScale(arch, out_dim)
''' + A2, 1)
src = src.replace(A3, 'choices=["resnet", "inceptionnext", "convnextv2", "resnet50"]', 1)
open(F, "w").write(src)
print("patched train_cnn_paltas.py (backup .bak_archs): +TimmScale, +choices")
