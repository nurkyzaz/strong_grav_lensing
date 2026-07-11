#!/bin/bash
#SBATCH --job-name=g3_member
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_g3_%j.out

# G3 grid member. Env: ARCH, SEED, LR, CKPT, EPOCHS (default 40), LIMIT (opt).
set -e
: "${ARCH:?}" "${SEED:?}" "${LR:?}" "${CKPT:?}"
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn
EXTRA=""
if [ -n "${LIMIT}" ]; then EXTRA="--train_limit ${LIMIT}"; fi
$PY train_cnn_paltas.py --arch "$ARCH" --seed "$SEED" --lr "$LR" $EXTRA \
    --train_file /home/user/nurkyz/einstein_cnn/train_g3_100k.h5 \
    --val_file   /home/user/nurkyz/einstein_cnn/val_g3_5k.h5 \
    --epochs "${EPOCHS:-40}" --batch_size 64 --nll --norm asinh \
    --min_theta_e 0.4 --augment --out_ckpt "$CKPT"
echo TRAIN_DONE "$CKPT"
