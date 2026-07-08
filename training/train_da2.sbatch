#!/bin/bash
#SBATCH --job-name=lf_train_da2
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_train_da2_%j.out

# DA-v2 (style-statistics MMD, pre-registered in DECISIONS_LOG 2026-07-07).
# Env: ALPHA, MODE (style/embed), WARMUP, EPOCHS, LR, CKPT, INIT (optional).
set -e
: "${ALPHA:?}" "${CKPT:?}"
MODE=${MODE:-style}
WARMUP=${WARMUP:-0}
EPOCHS=${EPOCHS:-40}
LR=${LR:-1e-3}
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

EXTRA=""
if [ -n "$INIT" ]; then EXTRA="--init_ckpt $INIT"; fi

$PY train_cnn_paltas.py \
    --train_file /home/user/nurkyz/einstein_cnn/train_hybrid_100k_v2.h5 \
    --val_file   /home/user/nurkyz/einstein_cnn/val_hybrid_5k_v2.h5 \
    --epochs "$EPOCHS" --batch_size 64 --lr "$LR" --nll --norm asinh \
    --min_theta_e 0.4 --augment \
    --da_pool /home/user/nurkyz/einstein_cnn/real_dapool_images.h5 \
    --da_weight "$ALPHA" --da_mode "$MODE" --da_warmup "$WARMUP" $EXTRA \
    --out_ckpt "$CKPT"
echo TRAIN_DONE
