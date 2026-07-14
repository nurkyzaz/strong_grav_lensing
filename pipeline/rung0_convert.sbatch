#!/bin/bash
#SBATCH --job-name=rung0_conv
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_rung0_conv_%j.out

# G5 Path A data prep: Rung 0 labeled -> train/val (f106 + 3band, 128px),
# unlabeled -> eval h5s; previews + gate stats printed.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/roman_dc
$PY rung0_to_train.py --labeled
$PY rung0_to_train.py --unlabeled
echo RUNG0_CONVERT_DONE
