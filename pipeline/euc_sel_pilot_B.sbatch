#!/bin/bash
#SBATCH --job-name=lf_euc_selB
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/euc_sel_pilot_B.out

# R1.2b pilot B (2026-07-09, option B): HIGH-SURFACE-BRIGHTNESS source
# selection (config_lensfusion_acs_pathb_euclid.py, SB <= 21 mag/arcsec^2,
# Newton et al. 2011 SLACS-source-population anchored; 7808/56062 catalog
# galaxies pass). ONLY change vs pilot v2 = the source population; screened
# backdrops + SNR>2.5 + extent>=300 selection unchanged. KEY READOUT: the
# per-theta_E pass fractions (v2: 2%/6%/15%/34%) must rise, especially at
# small theta_E, for the full run to be affordable and balanced.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[0/4] generate 400 ARC-ONLY renders (HIGH-SB sources, seed 311, npys kept) ..."
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
$PY run_paltas_pilot.py config_lensfusion_acs_pathb_euclid.py \
    /home/user/nurkyz/paltas_euc_selB_pilot --n 400 --seed 311

echo "[1/4] combine with SCREENED backdrop pool ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_euc_selB_pilot \
    --empty empty_cutouts_4k_screened.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_dapool_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/euc_sel_pilot_native_B.h5 \
    --deflector_stamps deflector_stamps_lrg_v6_train.h5 --deflector_augment \
    --deflector_mag_csv lens_light_empirical.csv \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 212

cd /home/user/nurkyz/einstein_cnn
echo "[2/4] euclidise composed ..."
$PY euclidise.py --inp euc_sel_pilot_native_B.h5 --out euc_sel_pilot_euclid_B.h5 --seed 213

echo "[3/4] selection (SNR>2.5, extent>=300) ..."
$PY arc_visibility_select.py --arcs /home/user/nurkyz/paltas_euc_sel_pilot_euclid \
    --sim euc_sel_pilot_euclid_B.h5 --out euc_sel_pilot_selected_B.h5 \
    --thresh 2.5 --min_extent 300

echo "[4/4] gate + side-by-side vs EUCLIDISED benchmark ..."
cd /home/user/nurkyz/cosmos_acs/tiles
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/euc_sel_pilot_selected_B.h5 \
    --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --csv failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_euc_selB_pilot/metadata.csv \
    --out gate_euc_sel_pilot_B.png
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/euc_sel_pilot_selected_B.h5 --n 8 --seed 5 \
    --out real_vs_sim_euc_selected_B.png
echo "EUC_SEL_PILOT_B_DONE"
