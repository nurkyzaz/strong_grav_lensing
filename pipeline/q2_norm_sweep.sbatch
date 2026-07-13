#!/bin/bash
#SBATCH --job-name=q2_norm_sweep
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_q2sweep_%j.out

# Q2c2 normalization sweep (Nurkyz ruling 2026-07-13). SUBMIT ONLY ON
# EXPLICIT GO-AHEAD — model passes on Q1 tuning subset are logged C18
# contacts. 12 combos x 3 members x 10 lenses, TTA. NOT the official eval.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/q1_slde
$PY q2_norm_sweep.py --build
$PY q2_norm_sweep.py --predict
$PY q2_norm_sweep.py --report
echo Q2SWEEP_DONE
