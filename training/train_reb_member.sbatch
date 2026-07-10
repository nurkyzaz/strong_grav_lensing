#!/bin/bash
#SBATCH --job-name=reb_member
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_reb_%j.out

# REB full-training grid member (plan 2b; quick-train-informed LRs:
# convnextv2 -> 3e-4, others 1e-3). Env: ARCH, SEED, LR, CKPT.
set -e
: "${ARCH:?}" "${SEED:?}" "${LR:?}" "${CKPT:?}"
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

$PY train_cnn_paltas.py --arch "$ARCH" --seed "$SEED" --lr "$LR" \
    --train_file /home/user/nurkyz/einstein_cnn/train_euclid_reb_100k.h5 \
    --val_file   /home/user/nurkyz/einstein_cnn/val_euclid_reb_5k.h5 \
    --epochs 40 --batch_size 64 --nll --norm asinh \
    --min_theta_e 0.4 --augment --out_ckpt "$CKPT"
echo TRAIN_DONE "$CKPT"
