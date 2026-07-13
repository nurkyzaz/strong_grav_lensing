#!/bin/bash
#SBATCH --job-name=lf_arcregen
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/regen_arcs_keep.out

# P5 support: regenerate the 200 seed-111 arc-only renders (identical to every
# pilot's step [1]) and KEEP the noiseless npys for arc-SNR metric iteration.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
$PY run_paltas_pilot.py config_lensfusion_acs_pathb_nonoise.py \
    /home/user/nurkyz/paltas_arcs_seed111_keep --n 200 --seed 111
echo "ARC_REGEN_DONE"
