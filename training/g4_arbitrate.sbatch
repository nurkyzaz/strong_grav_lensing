#!/bin/bash
#SBATCH --job-name=g4_arbitrate
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=01:30:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_g4_arbitrate_%j.out
~/miniconda3/envs/Stronglensing/bin/python ~/einstein_cnn/g4_arbitrate.py
echo G4_ARBITRATE_DONE
