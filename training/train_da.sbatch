#!/bin/bash
#SBATCH --job-name=lf_train_da
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_train_da_%j.out

# MASTER_PLAN D4: sim-to-real MMD domain adaptation training (env: ALPHA).
# Identical to the v2 reference recipe + MMD alignment to the 104-image
# benchmark-disjoint real pool (triple-checked disjoint, see DECISIONS_LOG).
set -e
: "${ALPHA:?}"
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

$PY train_cnn_paltas.py \
    --train_file /home/user/nurkyz/einstein_cnn/train_hybrid_100k_v2.h5 \
    --val_file   /home/user/nurkyz/einstein_cnn/val_hybrid_5k_v2.h5 \
    --epochs 40 --batch_size 64 --lr 1e-3 --nll --norm asinh \
    --min_theta_e 0.4 --augment \
    --da_pool /home/user/nurkyz/einstein_cnn/real_dapool_images.h5 \
    --da_weight "$ALPHA" \
    --out_ckpt "/home/user/nurkyz/einstein_cnn/einstein_cnn_da_a${ALPHA}.pt"
echo TRAIN_DONE
