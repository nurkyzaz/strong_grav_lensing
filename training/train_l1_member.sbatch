#!/bin/bash
#SBATCH --job-name=l1_member
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_l1_%j.out

# L1 deep-ensemble member (IMPROVEMENT_PIVOT_PLAN Stage L1).
# Env: ARCH (inceptionnext|resnet), SEED, CKPT (output name), INIT (optional
# native checkpoint for E5 transfer-init; empty = scratch).
# Same recipe as train_euclid_sel.sbatch (jobs 47425/47426), only seed/init vary.
set -e
: "${ARCH:?}" "${SEED:?}" "${CKPT:?}"
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

EXTRA=""
if [ -n "${INIT}" ]; then EXTRA="--init_ckpt ${INIT}"; fi

$PY train_cnn_paltas.py --arch "$ARCH" --seed "$SEED" $EXTRA \
    --train_file /home/user/nurkyz/einstein_cnn/train_euclid_sel_100k.h5 \
    --val_file   /home/user/nurkyz/einstein_cnn/val_euclid_sel_5k.h5 \
    --epochs 40 --batch_size 64 --lr 1e-3 --nll --norm asinh \
    --min_theta_e 0.4 --augment --out_ckpt "$CKPT"
echo TRAIN_DONE "$CKPT"
