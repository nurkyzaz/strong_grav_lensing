#!/bin/bash
#SBATCH --job-name=g5b_zeroshot
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_g5b_zeroshot_%j.out

# G5b zero-shot baseline: existing G4/g4ar models on the Rung 0 challenge-val
# 1000 (labeled, public GT — logged baseline, not a frozen-benchmark ⛔).
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/roman_dc
$PY g5b_zeroshot.py --build
$PY g5b_zeroshot.py --predict
$PY g5b_zeroshot.py --report
echo G5B_ZEROSHOT_DONE
