#!/bin/bash
#SBATCH --job-name=lf_abltrain
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=/home/user/nurkyz/paltas_abl/slurm_train_%j.out

# Parameterized ablation training (env: TRAIN_H5, VAL_H5, CKPT).
# Identical recipe to the v2 reference model (NLL head, 40 epochs, augment).
set -e
: "${TRAIN_H5:?}" "${VAL_H5:?}" "${CKPT:?}"
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

$PY train_cnn_paltas.py --train_file "$TRAIN_H5" --val_file "$VAL_H5" \
    --epochs 40 --batch_size 64 --lr 1e-3 --nll --norm asinh \
    --min_theta_e 0.4 --augment --out_ckpt "$CKPT"
echo TRAIN_DONE
