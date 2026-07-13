#!/bin/bash
#SBATCH --job-name=g3_pilot
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g3_pilot.out

# GEN4-G3 PILOT A (ONE change: real ACS->VIS matching kernel in euclidise,
# Q1 GRID-PSF-VIS target; Tukey-0.3 photutils kernel; flux-conservation and
# point-source smoke already verified). Population recipe identical to the
# G4 generation. Gates vs the RE-DERIVED benchmark euclid_slacs_images_g3.h5
# (same operator both sides). 600 renders, fresh seeds 880/881/230/231.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1/6] manifest (1400 rows for 600 renders) ..."
$PY g2_make_manifest.py --kine g2_kinematics_unified.csv --n 1400 --seed 880 \
    --out g3_manifest_pilot.csv

echo "[2/6] render 600 (seed 881) ..."
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST=/home/user/nurkyz/cosmos_acs/tiles/g3_manifest_pilot.csv
$PY run_paltas_pilot.py config_lensfusion_acs_g2.py \
    /home/user/nurkyz/paltas_g3_pilot --n 600 --seed 881

echo "[3/6] join + combine ..."
$PY g2_join_assign.py /home/user/nurkyz/paltas_g3_pilot g3_manifest_pilot.csv g3_assign_pilot.csv
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_g3_pilot \
    --empty empty_cutouts_expanded_screened.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_dapool_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/g3_pilot_native.h5 \
    --deflector_stamps deflector_stamps_g4_all.h5 \
    --deflector_manifest g3_assign_pilot.csv --deflector_jitter 1.0 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 230

cd /home/user/nurkyz/einstein_cnn
echo "[4/6] euclidise (REAL PSF operator) + select ..."
$PY euclidise.py --inp g3_pilot_native.h5 --out g3_pilot_euclid.h5 --seed 231
$PY euclidise_arcs.py /home/user/nurkyz/paltas_g3_pilot /home/user/nurkyz/paltas_g3_pilot_euclid
$PY arc_visibility_select.py --arcs /home/user/nurkyz/paltas_g3_pilot_euclid \
    --sim g3_pilot_euclid.h5 --out g3_pilot_selected.h5 \
    --thresh 0.7 --min_extent 150

echo "[5/6] gates (vs the G3 re-derived benchmark) ..."
cd /home/user/nurkyz/cosmos_acs/tiles
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/g3_pilot_selected.h5 \
    --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images_g3.h5 \
    --csv /home/user/nurkyz/einstein_cnn/failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_g3_pilot/metadata.csv \
    --out gate_g3_pilot.png
$PY g2_gate_fj.py g3_assign_pilot.csv
cd /home/user/nurkyz/einstein_cnn
$PY reb_report.py g3_pilot_selected.h5 g3_pilot

echo "[6/6] side-by-sides ..."
cd /home/user/nurkyz/cosmos_acs/tiles
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images_g3.h5 \
    --sim /home/user/nurkyz/einstein_cnn/g3_pilot_selected.h5 --n 8 --seed 5 \
    --out real_vs_sim_G3.png
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/euclid_slacs_images_g3.h5 \
    --sim /home/user/nurkyz/einstein_cnn/g3_pilot_small_theta.h5 --n 8 --seed 6 \
    --out real_vs_sim_G3_smalltheta.png
echo "G3_PILOT_DONE"
