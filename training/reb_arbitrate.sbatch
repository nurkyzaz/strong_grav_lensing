#!/bin/bash
#SBATCH --job-name=reb_arbitrate
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=01:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_reb_arbitrate_%j.out

# REB grid arbitration — sim-val ONLY, TTA-consistent (no benchmark contact).
~/miniconda3/envs/Stronglensing/bin/python ~/einstein_cnn/reb_arbitrate.py
echo REB_ARBITRATE_DONE
