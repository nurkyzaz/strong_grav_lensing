#!/bin/bash
#SBATCH --job-name=lf_euclidise
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=04:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/euclidise_train_v3.out

# R1.2 step 2: Euclidise the v3 dataset (our benchmark-best recipe) with the
# reimplemented HST2EUCLID recipe, then QUICK-TRAIN sanity (20k/10ep,
# InceptionNeXt = the v3-winning arch) on the Euclidised domain.
# Full training is a separate decision after the quick-train numbers.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

echo "[1/3] euclidise train (100k) ..."
$PY euclidise.py --inp train_hybrid_100k_v3.h5 --out train_euclid_100k_v3.h5 --seed 71
echo "[2/3] euclidise val (5k) ..."
$PY euclidise.py --inp val_hybrid_5k_v3.h5 --out val_euclid_5k_v3.h5 --seed 72

echo "[3/3] quick-train sanity on the Euclidised domain ..."
$PY train_cnn_paltas.py --arch inceptionnext \
    --train_file train_euclid_100k_v3.h5 --val_file val_euclid_5k_v3.h5 \
    --train_limit 20000 --epochs 10 --batch_size 64 --lr 1e-3 --nll \
    --norm asinh --min_theta_e 0.4 --augment \
    --out_ckpt einstein_cnn_euclid_quicktrain.pt
echo EUCLIDISE_TRAIN_V3_DONE
