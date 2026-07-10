#!/usr/bin/env python
"""Pre-download timm pretrained weights on the LOGIN node (compute nodes may
lack internet); they land in the shared ~/.cache and are read by SLURM jobs."""
import timm

for n in ("convnextv2_nano.fcmae_ft_in22k_in1k", "resnet50.a1_in1k"):
    m = timm.create_model(n, pretrained=True, in_chans=1, num_classes=0)
    print(n, "cached OK, num_features =", m.num_features)
