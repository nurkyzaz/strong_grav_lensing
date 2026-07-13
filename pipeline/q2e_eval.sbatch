#!/bin/bash
#SBATCH --job-name=q2e_eval24
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_q2e_eval24_%j.out

# ⛔ Q2e = EVAL #24 (Nurkyz-authorized 2026-07-13, disconnected-safe):
# frozen normalization x11.4 no-pedestal; Q2d audit + previews in --build;
# 6 members (G4 cnv2_3 + g4ar r50_3), TTA; pre-registered report rows.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/q1_slde
$PY q2e_eval.py --build
$PY q2e_eval.py --predict
$PY q2e_eval.py --report
echo EVAL24_DONE
