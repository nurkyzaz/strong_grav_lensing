#!/bin/bash
#SBATCH --job-name=lf_mergepb2
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/merge_gate_pathb_v2.out

set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1] merge shards ..."
$PY merge_hybrid_shards.py --shards /home/user/nurkyz/paltas_shards_pathb_v2 --train-max-id 80 \
    --train-out /home/user/nurkyz/einstein_cnn/train_hybrid_100k_pathb_v2.h5 \
    --val-out /home/user/nurkyz/einstein_cnn/val_hybrid_5k_pathb_v2.h5

echo "[2] merge train metadata ..."
$PY merge_shard_metadata.py --shards /home/user/nurkyz/paltas_shards_pathb_v2 --train-max-id 80 \
    --out /home/user/nurkyz/paltas_shards_pathb_v2/metadata_train_merged.csv

echo "[3] realism gate on the FULL merged train set ..."
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/train_hybrid_100k_pathb_v2.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --csv failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_shards_pathb_v2/metadata_train_merged.csv \
    --out gate_stage0_report_pathb_v2.png

echo "[4] side-by-side on merged ..."
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/train_hybrid_100k_pathb_v2.h5 --n 8 --seed 7 \
    --out real_vs_train_pathb_v2.png

echo "[5] radial profile on merged ..."
$PY radial_profile_compare.py --sim /home/user/nurkyz/einstein_cnn/train_hybrid_100k_pathb_v2.h5 \
    --lib deflector_stamps_lrg_v6_train.h5 --label "TRAIN pathb v2 (100k)" \
    --out /home/user/nurkyz/cosmos_acs/tiles/radial_profile_train_pathb_v2.png

rm -f /home/user/nurkyz/paltas_shards_pathb_v2/hybrid_shard_*.h5
echo "MERGE_GATE_PATHB_V2_DONE"
