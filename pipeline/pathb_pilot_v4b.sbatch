#!/bin/bash
#SBATCH --job-name=lf_pathb_pilot4b
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/pathb_pilot_v4b.out

# PATH B pilot v4b (2026-07-09, P1b): ONLY change vs pilot v4 = deflector
# scaling target is now the APERTURE magnitude (mag_aper, r=2" -- the flux
# actually measured inside the cutout) instead of the TOTAL magnitude.
# Measured v4 defect: forcing 100% of the total-mag flux into the 6.4" frame
# made sim deflectors 1.85x over-bright in-frame (real cutouts hold only ~54%
# of the total; the de Vauc wings live beyond the frame) -> huge halos, buried
# arcs, peak/sky 1405 vs real 994. Same v3 library, same seeds, same recipe.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1/6] generate 200 ARC-ONLY images (seed 111, identical to pilots v3/v4) ..."
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
$PY run_paltas_pilot.py config_lensfusion_acs_pathb_nonoise.py \
    /home/user/nurkyz/paltas_pathb_pilot_v4b --n 200 --seed 111

echo "[2/6] combine: APERTURE-mag-scaled real LRG deflector + companions + backdrop + noise ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_pathb_pilot_v4b \
    --empty empty_cutouts_4k.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/pathb_pilot_v4b.h5 \
    --deflector_stamps deflector_stamps_lrg_v3.h5 --deflector_mag_csv lens_light_empirical.csv \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 112

echo "[3/6] three-stretch preview ..."
$PY preview_three_stretch.py /home/user/nurkyz/einstein_cnn/pathb_pilot_v4b.h5 --n 16

echo "[4/6] realism gate ..."
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v4b.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --csv failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_pathb_pilot_v4b/metadata.csv \
    --out gate_pathb_pilot_v4b.png

echo "[5/6] real-vs-sim side-by-side ..."
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v4b.h5 --n 8 --seed 5 \
    --out real_vs_pathb_pilot_v4b.png

echo "[6/6] radial profile compare (shape + absolute brightness) ..."
$PY radial_profile_compare.py --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v4b.h5 \
    --lib deflector_stamps_lrg_v3.h5 --label "SIM pilot v4b" \
    --out /home/user/nurkyz/cosmos_acs/tiles/radial_profile_v4b.png

rm -f /home/user/nurkyz/paltas_pathb_pilot_v4b/image_*.npy
echo "PATHB_PILOT_V4B_DONE"
