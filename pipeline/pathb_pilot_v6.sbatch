#!/bin/bash
#SBATCH --job-name=lf_pathb_pilot6
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/pathb_pilot_v6.out

# PATH B pilot v6 (2026-07-09, P3): change vs pilot v5 = (a) dihedral
# augmentation ON (--deflector_augment: rot90 x k + optional flip per paste;
# aperture flux is rotation-invariant so P1b scaling is unaffected; theta_E
# label untouched -- arcs render separately), (b) deflector library = the
# 41-stamp TRAIN split (deflector_stamps_lrg_v6_train.h5; 8 val-only stamps
# reserved in ..._val.h5, mirroring the val-disjoint PSF-kernel pattern).
# Bundled as the single P3 step per PATHB_IMPROVEMENT_PLAN (augmentation is
# label- and photometry-neutral). Expect gates unchanged vs v5.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1/6] generate 200 ARC-ONLY images (seed 111, identical to pilots v3/v4/v4b) ..."
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
$PY run_paltas_pilot.py config_lensfusion_acs_pathb_nonoise.py \
    /home/user/nurkyz/paltas_pathb_pilot_v6 --n 200 --seed 111

echo "[2/6] combine: APERTURE-mag-scaled real LRG deflector + companions + backdrop + noise ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_pathb_pilot_v6 \
    --empty empty_cutouts_4k.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/pathb_pilot_v6.h5 \
    --deflector_stamps deflector_stamps_lrg_v6_train.h5 --deflector_augment --deflector_mag_csv lens_light_empirical.csv \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 112

echo "[3/6] three-stretch preview ..."
$PY preview_three_stretch.py /home/user/nurkyz/einstein_cnn/pathb_pilot_v6.h5 --n 16

echo "[4/6] realism gate ..."
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v6.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --csv failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_pathb_pilot_v6/metadata.csv \
    --out gate_pathb_pilot_v6.png

echo "[5/6] real-vs-sim side-by-side ..."
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v6.h5 --n 8 --seed 5 \
    --out real_vs_pathb_pilot_v6run.png

echo "[6/6] radial profile compare (shape + absolute brightness) ..."
$PY radial_profile_compare.py --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v6.h5 \
    --lib deflector_stamps_lrg_v6_train.h5 --label "SIM pilot v6" \
    --out /home/user/nurkyz/cosmos_acs/tiles/radial_profile_v6.png

rm -f /home/user/nurkyz/paltas_pathb_pilot_v6/image_*.npy
echo "PATHB_PILOT_V6_DONE"
