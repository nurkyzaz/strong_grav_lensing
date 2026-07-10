#!/bin/bash
#SBATCH --job-name=lf_train_pb2
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_train_pathb_v2_%j.out

# P7 step 2 — Path B v2 FULL training (env: ARCH, CKPT). Dataset: P1b aperture
# scaling + 256px library v6 (train split) + dihedral augment + DA-pool noise.
# Selection on sim-val ONLY. Submit for both architectures:
#   sbatch --export=ALL,ARCH=inceptionnext,CKPT=einstein_cnn_pathb_v2_inceptionnext.pt train_pathb_v2.sbatch
#   sbatch --export=ALL,ARCH=resnet,CKPT=einstein_cnn_pathb_v2_resnet.pt train_pathb_v2.sbatch
set -e
: "${ARCH:?}" "${CKPT:?}"
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

$PY train_cnn_paltas.py --arch "$ARCH" \
    --train_file /home/user/nurkyz/einstein_cnn/train_hybrid_100k_pathb_v2.h5 \
    --val_file   /home/user/nurkyz/einstein_cnn/val_hybrid_5k_pathb_v2.h5 \
    --epochs 40 --batch_size 64 --lr 1e-3 --nll --norm asinh \
    --min_theta_e 0.4 --augment --out_ckpt "$CKPT"
echo TRAIN_DONE
