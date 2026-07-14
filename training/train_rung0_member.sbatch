#!/bin/bash
#SBATCH --job-name=rung0_member
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=08:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_rung0_%j.out

# G5 Path A member. Env: ARCH, SEED, LR, CKPT, VARIANT (f106|3band),
# EPOCHS (default 40), LIMIT (opt). theta range opened to the Rung 0
# population (0.16-3.6; 24% below the old 0.45 floor).
set -e
: "${ARCH:?}" "${SEED:?}" "${LR:?}" "${CKPT:?}" "${VARIANT:?}"
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn
IC=1
if [ "$VARIANT" = "3band" ]; then IC=3; fi
DP=${DATA_PREFIX:-rung0}
EXTRA=""
if [ -n "${LIMIT}" ]; then EXTRA="--train_limit ${LIMIT}"; fi
$PY train_cnn_paltas.py --arch "$ARCH" --seed "$SEED" --lr "$LR" $EXTRA \
    --train_file /home/user/nurkyz/einstein_cnn/train_${DP}_${VARIANT}.h5 \
    --val_file   /home/user/nurkyz/einstein_cnn/val_${DP}_${VARIANT}.h5 \
    --epochs "${EPOCHS:-40}" --batch_size 64 --nll --norm asinh \
    --min_theta_e 0.10 --max_theta_e 3.70 --in_chans "$IC" \
    --augment --out_ckpt "$CKPT"
echo TRAIN_DONE "$CKPT"
