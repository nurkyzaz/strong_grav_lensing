#!/bin/bash
#SBATCH --job-name=lf_euc_selREB
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/euc_sel_pilot_reb.out

# REBALANCE pilot (plan section 2b; ONLY change vs the production euclid_sel
# recipe = theta_E pre-selection prior oc 1/pass -> post-selection ~flat).
# Final production recipe otherwise: HighSB + Newton mags + SLACS-z, jitter
# 1px, EXPANDED screened backdrops, selection (0.7, 150). 600 renders for
# per-bin statistics at small theta_E.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[0/5] generate 600 ARC-ONLY renders (REBALANCED theta_E, seed 711) ..."
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
$PY run_paltas_pilot.py config_lensfusion_acs_pathb_euclid.py \
    /home/user/nurkyz/paltas_euc_selREB_pilot --n 600 --seed 711

echo "[1/5] combine (production flags) ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_euc_selREB_pilot \
    --empty /home/user/nurkyz/cosmos_acs/tiles/empty_cutouts_expanded_screened.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_dapool_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/euc_sel_pilot_native_REB.h5 \
    --deflector_stamps deflector_stamps_lrg_v6_train.h5 --deflector_augment \
    --deflector_jitter 1.0 \
    --deflector_mag_csv lens_light_empirical.csv \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 214

cd /home/user/nurkyz/einstein_cnn
echo "[2/5] euclidise composed + arcs ..."
$PY euclidise.py --inp euc_sel_pilot_native_REB.h5 --out euc_sel_pilot_euclid_REB.h5 --seed 215
$PY euclidise_arcs.py /home/user/nurkyz/paltas_euc_selREB_pilot /home/user/nurkyz/paltas_euc_selREB_pilot_euclid

echo "[3/5] selection at the PRODUCTION thresholds (0.7, 150) ..."
$PY arc_visibility_select.py --arcs /home/user/nurkyz/paltas_euc_selREB_pilot_euclid \
    --sim euc_sel_pilot_euclid_REB.h5 --out euc_sel_pilot_selected_REB.h5 \
    --thresh 0.7 --min_extent 150

echo "[4/5] gate + rebalance report ..."
$PY gate_stage0.py --sim euc_sel_pilot_selected_REB.h5 \
    --real euclid_slacs_images.h5 \
    --csv failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_euc_selREB_pilot/metadata.csv \
    --out gate_euc_sel_pilot_REB.png
$PY reb_report.py euc_sel_pilot_selected_REB.h5 reb_pilot

echo "[5/5] side-by-sides for Nurkyz (all + small-theta focus) ..."
cd /home/user/nurkyz/cosmos_acs/tiles
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/euc_sel_pilot_selected_REB.h5 --n 8 --seed 5 \
    --out real_vs_sim_euc_REB.png
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/reb_pilot_small_theta.h5 --n 8 --seed 6 \
    --out real_vs_sim_euc_REB_smalltheta.png
echo "EUC_SEL_PILOT_REB_DONE"
