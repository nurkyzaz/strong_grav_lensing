#!/bin/bash
#SBATCH --job-name=lf_euc_selC2
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/euc_sel_pilot_C2.out

# R1.2b pilot C (2026-07-09, E2): ONLY change vs pilot B2 = source REDSHIFT
# prior z_source ~ truncnorm(0.65, 0.15, [0.3,1.1]) matching the SLACS source
# population (Bolton 2008) instead of fixed z=1.5. (1+z)^4 SB dimming had our
# arcs ~1.8 mag/arcsec^2 fainter than the real population -- the lever for the
# still-weak small-theta_E selection pass (B2: 6%/14% below 1.2"). Fresh
# renders required (seed 511): z changes source appearance.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[0/4] generate 400 ARC-ONLY renders (high-SB + SLACS-z sources, seed 511) ..."
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
$PY run_paltas_pilot.py config_lensfusion_acs_pathb_euclid.py \
    /home/user/nurkyz/paltas_euc_selC2_pilot --n 400 --seed 511

echo "[1/4] combine (jitter 1px, screened pool) ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_euc_selC2_pilot \
    --empty empty_cutouts_4k_screened.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_dapool_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/euc_sel_pilot_native_C2.h5 \
    --deflector_stamps deflector_stamps_lrg_v6_train.h5 --deflector_augment \
    --deflector_jitter 1.0 \
    --deflector_mag_csv lens_light_empirical.csv \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 212

cd /home/user/nurkyz/einstein_cnn
echo "[2/4] euclidise composed + arcs ..."
$PY euclidise.py --inp euc_sel_pilot_native_C2.h5 --out euc_sel_pilot_euclid_C2.h5 --seed 213
$PY euclidise_arcs.py /home/user/nurkyz/paltas_euc_selC2_pilot /home/user/nurkyz/paltas_euc_selC2_pilot_euclid

echo "[3/4] selection ..."
$PY arc_visibility_select.py --arcs /home/user/nurkyz/paltas_euc_selC2_pilot_euclid \
    --sim euc_sel_pilot_euclid_C2.h5 --out euc_sel_pilot_selected_C2.h5 \
    --thresh 2.5 --min_extent 300

echo "[4/4] side-by-side ..."
cd /home/user/nurkyz/cosmos_acs/tiles
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/euc_sel_pilot_selected_C2.h5 --n 8 --seed 5 \
    --out real_vs_sim_euc_selected_C2.png
echo "EUC_SEL_PILOT_C2_DONE"
