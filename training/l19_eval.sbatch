#!/bin/bash
#SBATCH --job-name=l19_eval
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=01:30:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_l19_eval_%j.out

# EVAL #19 — operator 2x2 cross-diagnostic (Nurkyz "do 1 then 2" ruling,
# 2026-07-12; count 19; report immediately). Off-diagonal cells only:
#   G4 frozen primary (cnv2_3) on the _g3 (real-op) benchmark;
#   G3 frozen primary (r50_3) on the legacy (gauss-op) benchmark.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn
for M in g4_cnv2_s1 g4_cnv2_s2 g4_cnv2_s3 ; do
  for SAMPLE in euclid_slacs_images_g3 euclid_s4tm_images_g3 ; do
    $PY predict_real_lenses_paltas.py --ckpt ${M}.pt --real ${SAMPLE}.h5 \
        --tta --outdir brian_run --out preds_l19_${M}_${SAMPLE}.csv
  done
done
for M in g3_r50_s1 g3_r50_s2 g3_r50_s3 ; do
  for SAMPLE in euclid_slacs_images euclid_s4tm_images ; do
    $PY predict_real_lenses_paltas.py --ckpt ${M}.pt --real ${SAMPLE}.h5 \
        --tta --outdir brian_run --out preds_l19_${M}_${SAMPLE}.csv
  done
done
$PY l19_tables.py
echo EVAL19_DONE
