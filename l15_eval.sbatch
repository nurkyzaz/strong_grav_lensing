#!/bin/bash
#SBATCH --job-name=l15_eval
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=01:30:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_l15_eval_%j.out

# ⛔ EVAL #15 (Nurkyz present, running count 15). 12 members x 2 Euclidised
# benchmark files, TTA, via the SAME predict script as eval #14 (identical
# preprocessing), then the l15_tables.py combiner with frozen l1_recal.json.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

for M in einstein_cnn_euclid_sel_inceptionnext \
         einstein_cnn_euclid_sel_inceptionnext_s1 \
         einstein_cnn_euclid_sel_inceptionnext_s2 \
         einstein_cnn_euclid_sel_inceptionnext_s3 \
         einstein_cnn_euclid_sel_inceptionnext_s4 \
         einstein_cnn_euclid_sel_inceptionnext_tinit \
         einstein_cnn_euclid_sel_resnet \
         einstein_cnn_euclid_sel_resnet_s1 \
         einstein_cnn_euclid_sel_resnet_s2 \
         einstein_cnn_euclid_sel_resnet_s3 \
         einstein_cnn_euclid_sel_resnet_s4 \
         einstein_cnn_euclid_sel_resnet_tinit ; do
  for SAMPLE in euclid_slacs_images euclid_s4tm_images ; do
    $PY predict_real_lenses_paltas.py --ckpt ${M}.pt --real ${SAMPLE}.h5 \
        --tta --outdir brian_run --out preds_l15_${M}_${SAMPLE}.csv
  done
done

$PY l15_tables.py
echo EVAL15_DONE
