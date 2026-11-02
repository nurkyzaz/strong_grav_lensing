#!/usr/bin/env python
"""Lightweight masked-autoencoder (MAE-style) self-supervised pretraining on the
Rung 1 lens images (labels NOT used). Randomly masks patches, reconstructs the
image with a resnet50 encoder + small conv decoder (MSE on masked pixels), and
saves the encoder to transfer into train_cnn_rung1.py via --init_backbone.

Honest expectation: the subhalo signal is below the noise, so the encoder learns
source/galaxy morphology, not the subhalo cue -> likely little classification
gain. Run for completeness / best-practice coverage.

    python rung1_ssl_pretrain.py --train_file <labeled>.h5 --limit 60000 \
        --epochs 12 --out rung1_ssl_encoder.pt
"""
import argparse
import os
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from train_cnn_rung1 import index_dataset, Rung1H5Dataset  # noqa: E402
import timm  # noqa: E402


class ConvDecoder(nn.Module):
    def __init__(self, in_ch, out_ch=3, out_hw=91):
        super().__init__()
        self.out_hw = out_hw

        def up(i, o):
            return nn.Sequential(nn.ConvTranspose2d(i, o, 4, 2, 1),
                                 nn.BatchNorm2d(o), nn.ReLU(True))
        self.net = nn.Sequential(up(in_ch, 512), up(512, 256), up(256, 128),
                                 up(128, 64), up(64, 32))
        self.head = nn.Conv2d(32, out_ch, 3, padding=1)

    def forward(self, x):
        x = self.head(self.net(x))
        return F.interpolate(x, size=(self.out_hw, self.out_hw),
                             mode="bilinear", align_corners=False)


class MAE(nn.Module):
    def __init__(self, in_chans=3, out_hw=91):
        super().__init__()
        self.encoder = timm.create_model("resnet50.a1_in1k", pretrained=True,
                                         in_chans=in_chans, num_classes=0,
                                         global_pool="")            # spatial map
        self.decoder = ConvDecoder(self.encoder.num_features, in_chans, out_hw)

    def forward(self, x):
        return self.decoder(self.encoder(x))


def mask_patches(x, patch=16, ratio=0.5):
    B, C, H, W = x.shape
    pm = (torch.rand(B, 1, H // patch + 1, W // patch + 1,
                     device=x.device) < ratio).float()
    m = F.interpolate(pm, size=(H, W), mode="nearest")             # 1 = masked
    return x * (1 - m), m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train_file", required=True)
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--num_workers", type=int, default=4)
    ap.add_argument("--out", default="rung1_ssl_encoder.pt")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    dev = torch.device(args.device)
    gn, uids, _ = index_dataset(args.train_file, with_labels=False, limit=args.limit)
    ds = Rung1H5Dataset(args.train_file, gn, uids, None, "asinh", 1.0)
    dl = DataLoader(ds, batch_size=args.batch_size, shuffle=True,
                    num_workers=args.num_workers, drop_last=True,
                    persistent_workers=args.num_workers > 0)
    print(f"[ssl] {len(ds)} images | {args.epochs} epochs | device={dev}", flush=True)

    model = MAE(3, out_hw=91).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    for ep in range(1, args.epochs + 1):
        model.train(); run = 0.0; nb = 0
        for img, _, _ in dl:
            img = img.to(dev)
            mi, m = mask_patches(img)
            rec = model(mi)
            loss = (((rec - img) ** 2) * m).sum() / (m.sum() * img.shape[1] + 1e-8)
            opt.zero_grad(); loss.backward(); opt.step()
            run += loss.item(); nb += 1
        print(f"epoch {ep:3d} | masked_recon_mse {run/nb:.4f}", flush=True)
    torch.save({"backbone_state": model.encoder.state_dict(), "arch": "resnet50"},
               args.out)
    print(f"[done] saved SSL encoder -> {args.out}")


if __name__ == "__main__":
    main()
