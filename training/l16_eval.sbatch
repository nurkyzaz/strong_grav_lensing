#!/bin/bash
#SBATCH --job-name=l16_eval
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=02:30:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_l16_eval_%j.out

# ⛔ EVAL #16 (submit ONLY on Nurkyz's go; running count 16). Members read
# from reb_recal.json; TTA via the standard predict script; then the
# pre-registered l16_tables.py.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn

# ALL 16 members predicted in the same pass; primary row = the frozen
# reb_recal.json variant; arch-ensembles are DERIVED columns (evals #14/#15
# precedent — no extra benchmark passes).
MEMBERS="reb_resnet_s1 reb_resnet_s2 reb_resnet_s3 reb_resnet_s4 reb_resnet_s5 reb_incnext_s1 reb_incnext_s2 reb_incnext_s3 reb_incnext_s4 reb_incnext_s5 reb_cnv2_s1 reb_cnv2_s2 reb_cnv2_s3 reb_r50_s1 reb_r50_s2 reb_r50_s3"
for M in $MEMBERS ; do
  for SAMPLE in euclid_slacs_images euclid_s4tm_images ; do
    $PY predict_real_lenses_paltas.py --ckpt ${M}.pt --real ${SAMPLE}.h5 \
        --tta --outdir brian_run --out preds_l16_${M}_${SAMPLE}.csv
  done
done
$PY l16_tables.py
echo EVAL16_DONE
