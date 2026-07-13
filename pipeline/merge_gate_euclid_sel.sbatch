#!/bin/bash
#SBATCH --job-name=lf_mergeeuc
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/merge_gate_euclid_sel.out

set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1] merge shards ..."
$PY merge_hybrid_shards.py --shards /home/user/nurkyz/paltas_shards_euclid --train-max-id 80 \
    --train-out /home/user/nurkyz/einstein_cnn/train_euclid_sel_100k.h5 \
    --val-out /home/user/nurkyz/einstein_cnn/val_euclid_sel_5k.h5

echo "[2] merge train metadata ..."
$PY merge_shard_metadata.py --shards /home/user/nurkyz/paltas_shards_euclid --train-max-id 80 \
    --out /home/user/nurkyz/paltas_shards_euclid/metadata_train_merged.csv

echo "[3] realism gate on the FULL merged train set ..."
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/train_euclid_sel_100k.h5 \
    --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --csv failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_shards_euclid/metadata_train_merged.csv \
    --out gate_stage0_report_euclid_sel.png

echo "[4] side-by-side on merged ..."
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/train_euclid_sel_100k.h5 --n 8 --seed 7 \
    --out real_vs_train_euclid_sel.png

echo "[5] radial profile on merged ..."
$PY radial_profile_compare.py --sim /home/user/nurkyz/einstein_cnn/train_euclid_sel_100k.h5 \
    --lib deflector_stamps_lrg_v6_train.h5 --label "TRAIN euclid-sel" \
    --out /home/user/nurkyz/cosmos_acs/tiles/radial_profile_train_euclid_sel.png

rm -f /home/user/nurkyz/paltas_shards_euclid/hybrid_shard_*.h5
echo "MERGE_GATE_EUCLID_SEL_DONE"
