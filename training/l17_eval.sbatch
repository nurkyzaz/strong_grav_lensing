#!/bin/bash
#SBATCH --job-name=l17_eval
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_l17_eval_%j.out

# ⛔ EVAL #17 (pre-authorized by Nurkyz: "run the full chain to eval #17";
# running count 17; results reported to Nurkyz immediately).
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn
MEMBERS="g4_resnet_s1 g4_resnet_s2 g4_resnet_s3 g4_resnet_s4 g4_resnet_s5 g4_incnext_s1 g4_incnext_s2 g4_incnext_s3 g4_incnext_s4 g4_incnext_s5 g4_cnv2_s1 g4_cnv2_s2 g4_cnv2_s3 g4_r50_s1 g4_r50_s2 g4_r50_s3 g4_logpolar_s1"
for M in $MEMBERS ; do
  for SAMPLE in euclid_slacs_images euclid_s4tm_images ; do
    $PY predict_real_lenses_paltas.py --ckpt ${M}.pt --real ${SAMPLE}.h5 \
        --tta --outdir brian_run --out preds_l17_${M}_${SAMPLE}.csv
  done
done
$PY l17_tables.py
echo EVAL17_DONE
