#!/bin/bash
#SBATCH --job-name=rung1_train
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_rung1_train_%j.out

# Steps 1-2 of docs/RUNG1_PLAN.md: train ONE CDM-subhalo binary classifier.
# Parameterized by env; submit it 3x (SEED=0/1/2) to build the ensemble, and
# again with ARCH=convnextv2 for a second backbone.
#
# Required:  TRAIN_H5   labeled Rung 1 file
# Optional:  IMAGE_KEY / LABEL_KEY  (auto-detected if unset; see rung1_inspect)
#            ARCH=resnet50|convnextv2 (default resnet50)
#            SEED (default 0), EPOCHS (default 40), CKPT (default derived)
#
#   TRAIN_H5=~/cosmos_acs/roman_dc/roman_data_challenge_rung_1_v_3_0.h5 \
#   ARCH=resnet50 SEED=0 sbatch pipeline/rung1_train.sbatch
set -e
: "${TRAIN_H5:?set TRAIN_H5=/path/to/labeled.h5}"
ARCH="${ARCH:-resnet50}"
SEED="${SEED:-0}"
EPOCHS="${EPOCHS:-40}"
CKPT="${CKPT:-/home/user/nurkyz/cosmos_acs/roman_dc/rung1_${ARCH}_s${SEED}.pt}"
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

# keys are optional -- the script auto-detects when the flag is omitted
IMG_FLAG=""; [ -n "${IMAGE_KEY:-}" ] && IMG_FLAG="--image_key ${IMAGE_KEY}"
LAB_FLAG=""; [ -n "${LABEL_KEY:-}" ] && LAB_FLAG="--label_key ${LABEL_KEY}"

$PY train_cnn_rung1.py --train_file "$TRAIN_H5" $IMG_FLAG $LAB_FLAG \
    --arch "$ARCH" --in_chans 3 --epochs "$EPOCHS" --batch_size 64 \
    --lr 1e-3 --norm asinh --augment --seed "$SEED" --out_ckpt "$CKPT"
echo "RUNG1_TRAIN_DONE $CKPT"
