#!/bin/bash
#SBATCH --job-name=lf_train_v3
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_train_v3_%j.out

# Stage-3 v3 training (env: ARCH). Companion-injected dataset, NLL head, 40 ep.
set -e
: "${ARCH:?}" "${CKPT:?}"
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

$PY train_cnn_paltas.py --arch "$ARCH" \
    --train_file /home/user/nurkyz/einstein_cnn/train_hybrid_100k_v3.h5 \
    --val_file   /home/user/nurkyz/einstein_cnn/val_hybrid_5k_v3.h5 \
    --epochs 40 --batch_size 64 --lr 1e-3 --nll --norm asinh \
    --min_theta_e 0.4 --augment --out_ckpt "$CKPT"
echo TRAIN_DONE
