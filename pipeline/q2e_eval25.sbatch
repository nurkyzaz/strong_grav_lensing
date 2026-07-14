#!/bin/bash
#SBATCH --job-name=q2e_eval25
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_q2e_eval25_%j.out

# ⛔ EVAL #25 (Nurkyz go 2026-07-14): texture-FIXED re-run of the Q2e board —
# zoom(order=1) preprocessing (the euclidise training convention; #24 used
# blocky repeat/4 = the found bug), factor translated 11.4/4 = 2.85 (same
# frozen absolute calibration). Same frozen lens set, same pre-registered
# rows. Interpretation rule (pre-registered at the #24 forensics): if #25 ≈
# #24 the texture bug was immaterial and the population finding stands; if
# #25 improves materially, #24's negative headline is retracted as a
# preprocessing artifact and #25 becomes the Q2e number.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/q1_slde
$PY q2e_eval.py --conv zoom --build
$PY q2e_eval.py --conv zoom --predict
$PY q2e_eval.py --conv zoom --report
echo EVAL25_DONE
