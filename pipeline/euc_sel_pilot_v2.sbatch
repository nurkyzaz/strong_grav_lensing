#!/bin/bash
#SBATCH --job-name=lf_euc_sel2
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/euc_sel_pilot_v2.out

# R1.2b pilot v2 (2026-07-09, after Nurkyz's visual verdict on pilot v1):
# fixes, reusing the SAME 400 seed-211 arc renders (still on disk):
# 1. backdrop pool SCREENED for gradient outliers (real-95% threshold 2.85;
#    SIM #11's cutout was 10.6x noise -> the 'abrupt edge');
# 2. selection threshold recalibrated IN-DOMAIN: SNR > 2.5 (Euclid glare;
#    native 0.7 does not transfer -- her invisible panels were 0.7-1.9);
# 3. NEW extent criterion: arc footprint >= 300 px (upsampled grid) so
#    compact knots that pass SNR but don't look like arcs are rejected.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1/4] recombine with SCREENED backdrop pool ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_euc_sel_pilot \
    --empty empty_cutouts_4k_screened.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_dapool_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/euc_sel_pilot_native_v2.h5 \
    --deflector_stamps deflector_stamps_lrg_v6_train.h5 --deflector_augment \
    --deflector_mag_csv lens_light_empirical.csv \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 212

cd /home/user/nurkyz/einstein_cnn
echo "[2/4] euclidise composed ..."
$PY euclidise.py --inp euc_sel_pilot_native_v2.h5 --out euc_sel_pilot_euclid_v2.h5 --seed 213

echo "[3/4] selection (SNR>2.5, extent>=300) ..."
$PY arc_visibility_select.py --arcs /home/user/nurkyz/paltas_euc_sel_pilot_euclid \
    --sim euc_sel_pilot_euclid_v2.h5 --out euc_sel_pilot_selected_v2.h5 \
    --thresh 2.5 --min_extent 300

echo "[4/4] gate + side-by-side vs EUCLIDISED benchmark ..."
cd /home/user/nurkyz/cosmos_acs/tiles
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/euc_sel_pilot_selected_v2.h5 \
    --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --csv failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_euc_sel_pilot/metadata.csv \
    --out gate_euc_sel_pilot_v2.png
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/euc_sel_pilot_selected_v2.h5 --n 8 --seed 5 \
    --out real_vs_sim_euc_selected_v2.png
echo "EUC_SEL_PILOT_V2_DONE"
