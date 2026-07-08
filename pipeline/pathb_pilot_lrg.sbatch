#!/bin/bash
#SBATCH --job-name=lf_pathb_pilot
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/pathb_pilot.out

# PATH B pilot (real non-lens LRG deflector light). Build LRG deflector library
# -> 200 ARC-ONLY images -> inject real deflector + companions + backdrop +
# noise -> gate + side-by-side + preview. STOP for inspection (200-image rule).
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1/6] build LRG deflector library ..."
$PY build_deflector_from_lrg.py --out deflector_stamps_lrg.h5

echo "[2/6] generate 200 ARC-ONLY images (no parametric lens light) ..."
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
$PY run_paltas_pilot.py config_lensfusion_acs_pathb_nonoise.py \
    /home/user/nurkyz/paltas_pathb_pilot --n 200 --seed 111

echo "[3/6] combine: real LRG deflector light + companions + backdrop + noise ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_pathb_pilot \
    --empty empty_cutouts_4k.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/pathb_pilot.h5 \
    --deflector_stamps deflector_stamps_lrg.h5 --deflector_mag_csv lens_light_empirical.csv \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 112

echo "[4/6] three-stretch preview ..."
$PY preview_three_stretch.py /home/user/nurkyz/einstein_cnn/pathb_pilot.h5 --n 16

echo "[5/6] realism gate ..."
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/pathb_pilot.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --csv failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_pathb_pilot/metadata.csv \
    --out gate_pathb_pilot.png

echo "[6/6] real-vs-sim side-by-side ..."
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/pathb_pilot.h5 --n 8 --seed 5 \
    --out real_vs_pathb_pilot.png

rm -f /home/user/nurkyz/paltas_pathb_pilot/image_*.npy
echo "PATHB_PILOT_DONE"
