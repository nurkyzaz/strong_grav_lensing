#!/bin/bash
#SBATCH --job-name=l1_arbitrate
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=00:30:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_l1_arbitrate_%j.out

# L1 arbitration - sim-val ONLY (no benchmark contact).
~/miniconda3/envs/Stronglensing/bin/python ~/einstein_cnn/l1_arbitrate.py
