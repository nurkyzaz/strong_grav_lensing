#!/bin/bash
#SBATCH --job-name=lf_euc_sel
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/pathb_pilot_euclid_sel.out

# R1.2b PILOT (2026-07-09): arc-visibility-SELECTED Euclid training arm.
# 400 arc-only renders (fresh seed 211, npys KEPT for the selection metric)
# -> final pathb combine recipe -> Euclidise composed + arcs -> select
# arc SNR > 0.7 (eye-visible calibration) -> gate vs the EUCLIDISED benchmark.
# Premise validated: euclid-model error vs post-degradation arc SNR rho=-0.57;
# lowest quartile 84% failure with prior-pull, highest 18%.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1/6] generate 400 ARC-ONLY renders (seed 211, npys kept) ..."
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
$PY run_paltas_pilot.py config_lensfusion_acs_pathb_nonoise.py \
    /home/user/nurkyz/paltas_euc_sel_pilot --n 400 --seed 211

echo "[2/6] combine (final pathb recipe) ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_euc_sel_pilot \
    --empty empty_cutouts_4k.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_dapool_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/euc_sel_pilot_native.h5 \
    --deflector_stamps deflector_stamps_lrg_v6_train.h5 --deflector_augment \
    --deflector_mag_csv lens_light_empirical.csv \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 212

cd /home/user/nurkyz/einstein_cnn
echo "[3/6] euclidise composed ..."
$PY euclidise.py --inp euc_sel_pilot_native.h5 --out euc_sel_pilot_euclid.h5 --seed 213
echo "[4/6] euclidise arc renders (no noise) ..."
$PY euclidise_arcs.py /home/user/nurkyz/paltas_euc_sel_pilot /home/user/nurkyz/paltas_euc_sel_pilot_euclid

echo "[5/6] arc-visibility selection ..."
$PY arc_visibility_select.py --arcs /home/user/nurkyz/paltas_euc_sel_pilot_euclid \
    --sim euc_sel_pilot_euclid.h5 --out euc_sel_pilot_selected.h5 --thresh 0.7

echo "[6/6] gate vs EUCLIDISED benchmark ..."
cd /home/user/nurkyz/cosmos_acs/tiles
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/euc_sel_pilot_selected.h5 \
    --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --csv failure_features_slacs.csv \
    --out gate_euc_sel_pilot.png
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/euc_sel_pilot_selected.h5 --n 8 --seed 5 \
    --out real_vs_sim_euc_selected.png

rm -f /home/user/nurkyz/paltas_euc_sel_pilot/image_*.npy
rm -rf /home/user/nurkyz/paltas_euc_sel_pilot_euclid
echo "EUC_SEL_PILOT_DONE"
