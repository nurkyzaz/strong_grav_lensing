#!/bin/bash
#SBATCH --job-name=lf_smoke_c2
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/smoke_companions2.out

# Tuned companion-injection smoke (brighter stamps, higher rate). Stamp library
# already built (source_stamps.h5). Resilient SLURM job.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
$PY run_paltas_pilot.py config_lensfusion_acs_nonoise.py \
    /home/user/nurkyz/paltas_smoke_comp2 --n 200 --seed 88

$PY hybrid_combine.py --run /home/user/nurkyz/paltas_smoke_comp2 \
    --empty empty_cutouts_4k.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/smoke_companions2.h5 \
    --companion_stamps source_stamps.h5 \
    --companion_rate_lo 8 --companion_rate_hi 30 --companion_flux_pct 55 --seed 89

$PY preview_three_stretch.py /home/user/nurkyz/einstein_cnn/smoke_companions2.h5 --n 16
SMOKE_H5=/home/user/nurkyz/einstein_cnn/smoke_companions2.h5 $PY characterize_field2.py

rm -f /home/user/nurkyz/paltas_smoke_comp2/image_*.npy
echo "SMOKE_COMP2_DONE"
