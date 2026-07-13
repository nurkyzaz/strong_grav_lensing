#!/bin/bash
#SBATCH --job-name=lf_pathb_pilot3
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/pathb_pilot_v3.out

# PATH B pilot v3 (2026-07-09): deflector library rebuilt with NO opacity ramp
# (natural wings, undistorted profile), neighbour replacement, trail/chip-edge
# rejection, and a 7-stamp visual prune. Same arc/companion/backdrop recipe as
# the previous pilot (one change at a time: only the deflector library differs).
# Library deflector_stamps_lrg_v3.h5 is built BEFORE this job (with --drop);
# NOT rebuilt here so the file matches the inspected preview exactly.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1/5] generate 200 ARC-ONLY images (same seed 111 as previous pilot for A/B) ..."
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
$PY run_paltas_pilot.py config_lensfusion_acs_pathb_nonoise.py \
    /home/user/nurkyz/paltas_pathb_pilot_v3 --n 200 --seed 111

echo "[2/5] combine: v3 real LRG deflector light + companions + backdrop + noise ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_pathb_pilot_v3 \
    --empty empty_cutouts_4k.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/pathb_pilot_v3.h5 \
    --deflector_stamps deflector_stamps_lrg_v3.h5 --deflector_mag_csv lens_light_empirical.csv \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 112

echo "[3/5] three-stretch preview ..."
$PY preview_three_stretch.py /home/user/nurkyz/einstein_cnn/pathb_pilot_v3.h5 --n 16

echo "[4/5] realism gate ..."
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v3.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --csv failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_pathb_pilot_v3/metadata.csv \
    --out gate_pathb_pilot_v3.png

echo "[5/5] real-vs-sim side-by-side ..."
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v3.h5 --n 8 --seed 5 \
    --out real_vs_pathb_pilot_v3run.png

rm -f /home/user/nurkyz/paltas_pathb_pilot_v3/image_*.npy
echo "PATHB_PILOT_V3_DONE"
