#!/bin/bash
#SBATCH --job-name=lf_smoke_comp
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/smoke_companions.out

# Self-contained companion-injection smoke (resilient: runs on a compute node,
# survives SSH/internet loss). Builds the real source-stamp library, generates
# 200 v2-config images, injects real companions, previews + verifies the
# companion-count distribution vs real SLACS. Stops for Nurkyz inspection.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1/5] building real source-stamp library ..."
$PY build_source_stamps.py --tiles_dir . --out source_stamps.h5 --n 6000

echo "[2/5] generating 200 noiseless paltas images (v2 config) ..."
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
$PY run_paltas_pilot.py config_lensfusion_acs_nonoise.py \
    /home/user/nurkyz/paltas_smoke_comp --n 200 --seed 77

echo "[3/5] hybrid combine WITH real companion injection ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_smoke_comp \
    --empty empty_cutouts_4k.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/smoke_companions.h5 \
    --companion_stamps source_stamps.h5 --seed 78

echo "[4/5] three-stretch preview ..."
$PY preview_three_stretch.py /home/user/nurkyz/einstein_cnn/smoke_companions.h5 --n 16

echo "[5/5] verify companion-count distribution vs real ..."
$PY characterize_field2.py

rm -f /home/user/nurkyz/paltas_smoke_comp/image_*.npy
echo "SMOKE_COMP_DONE"
