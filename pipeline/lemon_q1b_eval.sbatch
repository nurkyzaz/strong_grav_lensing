#!/bin/bash
#SBATCH --job-name=lemon_q1b_eval
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_lemon_q1b_%j.out

# ⛔ Q1b eval (Nurkyz LEMON head-to-head, count logged): 29 non-SLACS lenses
# (12 EEL + 5 COSMOS + 12 ACS, 1 excluded for a confirmed bad chip-gap
# cutout), native + Euclid domain, same G4n/G4 ensembles as SLACS-29.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn
for SUB in EEL COSMOS ACS; do
  for S in 1 2 3; do
    $PY predict_real_lenses_paltas.py --ckpt g4n_cnv2_s${S}.pt \
        --real real_LEMON${SUB}_frozen.h5 --tta \
        --outdir brian_run --out preds_lemonq1b_g4n_cnv2_s${S}_${SUB}_native.csv
    $PY predict_real_lenses_paltas.py --ckpt g4_cnv2_s${S}.pt \
        --real euclid_LEMON${SUB}_frozen.h5 --tta \
        --outdir brian_run --out preds_lemonq1b_g4_cnv2_s${S}_${SUB}_euclid.csv
  done
done
echo LEMON_Q1B_EVAL_DONE
