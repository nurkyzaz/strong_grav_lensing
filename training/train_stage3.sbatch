#!/bin/bash
#SBATCH --job-name=lf_train_v1
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_train_%j.out

# Stage 3 (CLAUDE.md 2026-07-06): train the m3-architecture scale-conditioned
# ResNet on the Stage-2 paltas hybrid dataset. Selection on val_hybrid_5k.h5
# ONLY (seed+kernel disjoint from train). No real-lens file touched.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

$PY train_cnn_paltas.py \
    --train_file /home/user/nurkyz/einstein_cnn/train_hybrid_100k.h5 \
    --val_file   /home/user/nurkyz/einstein_cnn/val_hybrid_5k.h5 \
    --epochs 40 --batch_size 64 --lr 1e-3 --loss huber --norm asinh \
    --augment --out_ckpt /home/user/nurkyz/einstein_cnn/einstein_cnn_paltas_v1.pt

echo TRAIN_DONE
