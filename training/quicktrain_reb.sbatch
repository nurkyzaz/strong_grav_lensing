#!/bin/bash
#SBATCH --job-name=qt_reb
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_qt_reb_%j.out

# REB quick-train sanity (20k subset, 10 epochs): 4 archs incl. the new
# pretrained pair; timm archs also probed at fine-tune LR 3e-4.
# Env: ARCH, LR, CKPT.
set -e
: "${ARCH:?}" "${LR:?}" "${CKPT:?}"
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

$PY train_cnn_paltas.py --arch "$ARCH" --lr "$LR" \
    --train_file /home/user/nurkyz/einstein_cnn/train_euclid_reb_100k.h5 \
    --val_file   /home/user/nurkyz/einstein_cnn/val_euclid_reb_5k.h5 \
    --train_limit 20000 --epochs 10 --batch_size 64 --nll --norm asinh \
    --min_theta_e 0.4 --augment --out_ckpt "$CKPT"
echo QT_DONE "$CKPT"
