#!/bin/bash
#SBATCH --job-name=lf_qtrain_pb2
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:30:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_quicktrain_pathb_v2_%j.out

# P7 step 1 — QUICK-TRAIN SANITY (PATHB_IMPROVEMENT_PLAN P7.1): InceptionNeXt
# on a 20k subset, 10 epochs (~20 min GPU). Purpose: confirm the P1b brightness
# fix removed the Path-B-v1 sim-val collapse (v1 plateaued at 0.194" MAE;
# v3-parametric reference 0.064"). STOP RULE: if val MAE plateaus >= 0.15",
# do NOT proceed to full training or spend a benchmark eval — diagnose first.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

$PY train_cnn_paltas.py --arch inceptionnext \
    --train_file /home/user/nurkyz/einstein_cnn/train_hybrid_100k_pathb_v2.h5 \
    --val_file   /home/user/nurkyz/einstein_cnn/val_hybrid_5k_pathb_v2.h5 \
    --train_limit 20000 \
    --epochs 10 --batch_size 64 --lr 1e-3 --nll --norm asinh \
    --min_theta_e 0.4 --augment \
    --out_ckpt /home/user/nurkyz/einstein_cnn/einstein_cnn_pathb_v2_quicktrain.pt
echo QUICKTRAIN_DONE
