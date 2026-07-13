#!/bin/bash
#SBATCH --job-name=ar1_pilot
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/ar1_pilot.out

# AR1 PILOT (ONE change vs the g3b recipe: --arc_poisson in hybrid_combine;
# manifest WITHOUT shear coupling). Gates: stage0 + FJ + flatness + AR0 arc
# gate + side-by-side, all vs the _g3 benchmark. Seeds 930/931/240/241.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

$PY g2_make_manifest.py --kine g2_kinematics_unified.csv --n 1400 --seed 930 \
    --out ar1_manifest_pilot.csv
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST=/home/user/nurkyz/cosmos_acs/tiles/ar1_manifest_pilot.csv
$PY run_paltas_pilot.py config_lensfusion_acs_g2.py \
    /home/user/nurkyz/paltas_ar1_pilot --n 600 --seed 931
$PY g2_join_assign.py /home/user/nurkyz/paltas_ar1_pilot ar1_manifest_pilot.csv ar1_assign_pilot.csv
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_ar1_pilot \
    --empty empty_cutouts_expanded_screened.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_dapool_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/ar1_pilot_native.h5 \
    --deflector_stamps deflector_stamps_g4_all.h5 \
    --deflector_manifest ar1_assign_pilot.csv --deflector_jitter 1.0 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 \
    --seed 240 --arc_poisson

cd /home/user/nurkyz/einstein_cnn
$PY euclidise.py --inp ar1_pilot_native.h5 --out ar1_pilot_euclid.h5 --seed 241
$PY euclidise_arcs.py /home/user/nurkyz/paltas_ar1_pilot /home/user/nurkyz/paltas_ar1_pilot_euclid
$PY arc_visibility_select.py --arcs /home/user/nurkyz/paltas_ar1_pilot_euclid \
    --sim ar1_pilot_euclid.h5 --out ar1_pilot_selected.h5 \
    --thresh 0.8 --min_extent 150

cd /home/user/nurkyz/cosmos_acs/tiles
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/ar1_pilot_selected.h5 \
    --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images_g3.h5 \
    --csv /home/user/nurkyz/einstein_cnn/failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_ar1_pilot/metadata.csv \
    --out gate_ar1_pilot.png
$PY g2_gate_fj.py ar1_assign_pilot.csv
$PY ar0_arc_gate.py --sim /home/user/nurkyz/einstein_cnn/ar1_pilot_selected.h5 \
    --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images_g3.h5 \
    --n 400 --tag ar1_pilot
cd /home/user/nurkyz/einstein_cnn
$PY reb_report.py ar1_pilot_selected.h5 ar1_pilot
cd /home/user/nurkyz/cosmos_acs/tiles
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images_g3.h5 \
    --sim /home/user/nurkyz/einstein_cnn/ar1_pilot_selected.h5 --n 8 --seed 5 \
    --out real_vs_sim_AR1.png
echo "AR1_PILOT_DONE"
