#!/bin/bash
#SBATCH --job-name=l0_simval
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=00:20:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_l0_simval_%j.out

# L0 sim-val bias forensics (B4). Sim-val only - NOT a benchmark evaluation.
~/miniconda3/envs/Stronglensing/bin/python ~/einstein_cnn/l0_simval_bias.py
