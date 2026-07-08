#!/bin/bash
#SBATCH --job-name=lf_smoke_c3
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/smoke_companions3.out

# Companion smoke v3: rebuild stamp library with artifact rejection (reject
# cosmic-ray/trail elongated sources) + edge apodization, then re-run smoke.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1/5] rebuild clean stamp library ..."
$PY build_source_stamps.py --tiles_dir . --out source_stamps_clean.h5 --n 6000

echo "[2/5] generate 200 v2-config images ..."
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
$PY run_paltas_pilot.py config_lensfusion_acs_nonoise.py \
    /home/user/nurkyz/paltas_smoke_comp3 --n 200 --seed 91

echo "[3/5] inject clean companions ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_smoke_comp3 \
    --empty empty_cutouts_4k.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/smoke_companions3.h5 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 92

echo "[4/5] preview ..."
$PY preview_three_stretch.py /home/user/nurkyz/einstein_cnn/smoke_companions3.h5 --n 16

echo "[5/5] verify ..."
SMOKE_H5=/home/user/nurkyz/einstein_cnn/smoke_companions3.h5 $PY characterize_field2.py

rm -f /home/user/nurkyz/paltas_smoke_comp3/image_*.npy
echo "SMOKE_COMP3_DONE"
