#!/bin/bash
#SBATCH --job-name=lf_euc_v2j1
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/euc_sel_pilot_v2j1.out

# R1.2b pilot B2 (2026-07-09): ONLY change vs pilot B = deflector paste jitter
# 2px -> 1px (--deflector_jitter 1.0). Nurkyz spotted arcs not centered on the
# lens light; measured: mass N(0,0.05") + paste U(+-0.10") gave typical
# mass-light offsets ~0.09" (tail 0.3") vs real SLACS alignment <~0.05"
# (Bolton 2008). 1px paste keeps the Stage-2a decoupling with a realistic
# amplitude. Same seed-311 renders reused.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1/4] recombine with jitter 1px ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_euc_sel_pilot \
    --empty empty_cutouts_4k_screened.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_dapool_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/euc_sel_pilot_native_v2j1.h5 \
    --deflector_stamps deflector_stamps_lrg_v6_train.h5 --deflector_augment \
    --deflector_jitter 1.0 \
    --deflector_mag_csv lens_light_empirical.csv \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 212

cd /home/user/nurkyz/einstein_cnn
echo "[2/4] euclidise composed + arcs ..."
$PY euclidise.py --inp euc_sel_pilot_native_v2j1.h5 --out euc_sel_pilot_euclid_v2j1.h5 --seed 213
$PY euclidise_arcs.py /home/user/nurkyz/paltas_euc_sel_pilot /home/user/nurkyz/paltas_euc_sel_pilot_euclid

echo "[3/4] selection ..."
$PY arc_visibility_select.py --arcs /home/user/nurkyz/paltas_euc_sel_pilot_euclid \
    --sim euc_sel_pilot_euclid_v2j1.h5 --out euc_sel_pilot_selected_v2j1.h5 \
    --thresh 2.5 --min_extent 300

echo "[4/4] side-by-side ..."
cd /home/user/nurkyz/cosmos_acs/tiles
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/euc_sel_pilot_selected_v2j1.h5 --n 8 --seed 5 \
    --out real_vs_sim_euc_selected_v2j1.png
echo "EUC_SEL_PILOT_V2J1_DONE"
