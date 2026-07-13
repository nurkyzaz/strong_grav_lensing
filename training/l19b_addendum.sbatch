#!/bin/bash
#SBATCH --job-name=l19b
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=00:40:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_l19b_%j.out

# EVAL #19 addendum (same diagnostic event): the arch-controlled cell —
# G4-trained r50_3 on the real-op benchmark, to split training-data effect
# from the cnv2-vs-r50 frozen-pick difference.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn
for M in g4_r50_s1 g4_r50_s2 g4_r50_s3 ; do
  for SAMPLE in euclid_slacs_images_g3 euclid_s4tm_images_g3 ; do
    $PY predict_real_lenses_paltas.py --ckpt ${M}.pt --real ${SAMPLE}.h5 \
        --tta --outdir brian_run --out preds_l19_${M}_${SAMPLE}.csv
  done
done
echo L19B_DONE
