#!/bin/bash
#SBATCH --job-name=g2_pilot
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g2_pilot.out

# GEN4-G2 PILOT: manifest-driven self-consistent population, 600 renders.
# Chain: merge libs -> manifest -> render (manifest config) -> join ->
# combine (manifest mode, native amplitude) -> euclidise -> select (0.7,150)
# -> gates (stage0 + NEW FJ gate) + flatness report + side-by-sides.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[0/7] merge libraries ..."
$PY g2_merge_libs.py

echo "[1/7] manifest (1400 rows for 600 renders) ..."
$PY g2_make_manifest.py --kine g2_kinematics_unified.csv --n 1400 --seed 811 \
    --out g2_manifest_pilot.csv

echo "[2/7] render 600 (manifest config, seed 812) ..."
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST=/home/user/nurkyz/cosmos_acs/tiles/g2_manifest_pilot.csv
$PY run_paltas_pilot.py config_lensfusion_acs_g2.py \
    /home/user/nurkyz/paltas_g2_pilot --n 600 --seed 812

echo "[3/7] join renders to manifest ..."
$PY g2_join_assign.py /home/user/nurkyz/paltas_g2_pilot g2_manifest_pilot.csv g2_assign_pilot.csv

echo "[4/7] combine (manifest mode) ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_g2_pilot \
    --empty empty_cutouts_expanded_screened.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_dapool_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/g2_pilot_native.h5 \
    --deflector_stamps deflector_stamps_g4_all.h5 \
    --deflector_manifest g2_assign_pilot.csv --deflector_jitter 1.0 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 216

cd /home/user/nurkyz/einstein_cnn
echo "[5/7] euclidise + select ..."
$PY euclidise.py --inp g2_pilot_native.h5 --out g2_pilot_euclid.h5 --seed 217
$PY euclidise_arcs.py /home/user/nurkyz/paltas_g2_pilot /home/user/nurkyz/paltas_g2_pilot_euclid
$PY arc_visibility_select.py --arcs /home/user/nurkyz/paltas_g2_pilot_euclid \
    --sim g2_pilot_euclid.h5 --out g2_pilot_selected.h5 \
    --thresh 0.7 --min_extent 150

echo "[6/7] gates ..."
cd /home/user/nurkyz/cosmos_acs/tiles
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/g2_pilot_selected.h5 \
    --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --csv /home/user/nurkyz/einstein_cnn/failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_g2_pilot/metadata.csv \
    --out gate_g2_pilot.png
$PY g2_gate_fj.py g2_assign_pilot.csv
cd /home/user/nurkyz/einstein_cnn
$PY reb_report.py g2_pilot_selected.h5 g2_pilot

echo "[7/7] side-by-sides ..."
cd /home/user/nurkyz/cosmos_acs/tiles
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/g2_pilot_selected.h5 --n 8 --seed 5 \
    --out real_vs_sim_G2.png
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/g2_pilot_small_theta.h5 --n 8 --seed 6 \
    --out real_vs_sim_G2_smalltheta.png
echo "G2_PILOT_DONE"
