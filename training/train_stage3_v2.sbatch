#!/bin/bash
#SBATCH --job-name=lf_train_v2
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_train_v2_%j.out

# Stage-3 v2 (audit bundle, 2026-07-06): m3-architecture ResNet with the
# (mu, log sigma^2) Gaussian-NLL head, on the v2 dataset (theta_E U[0.45,2.3],
# 88 real ePSF kernels). Selection on val_hybrid_5k_v2.h5 only.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

$PY train_cnn_paltas.py \
    --train_file /home/user/nurkyz/einstein_cnn/train_hybrid_100k_v2.h5 \
    --val_file   /home/user/nurkyz/einstein_cnn/val_hybrid_5k_v2.h5 \
    --epochs 40 --batch_size 64 --lr 1e-3 --nll --norm asinh \
    --min_theta_e 0.4 --augment \
    --out_ckpt /home/user/nurkyz/einstein_cnn/einstein_cnn_paltas_v2.pt

echo TRAIN_DONE
