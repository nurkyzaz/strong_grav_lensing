#!/bin/bash
#SBATCH --job-name=lf_pathb_pilot7
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/pathb_pilot_v7.out

# PATH B pilot v7 (2026-07-09, P4): ONLY change vs pilot v6 = the sky-RMS
# noise targets are drawn from the benchmark-DISJOINT DA pool
# (real_dapool_images.h5, 104 cutouts) instead of the frozen benchmark SLACS
# file -- closes the last calibration-leakage objection. The gate still
# compares against benchmark SLACS (diagnostic readout, not a training input).
# EXPECTED: sim sky-RMS ratio rises toward ~1.2-1.3 of SLACS (the pool is
# S4TM-dominated and genuinely shallower; covers the S4TM noise regime =
# subsumes the pending S4TM noise-union fix). A marginal gate edge is to be
# REPORTED, not tuned away. Also runs the P5 arc-SNR metric (measurement
# only) on the kept noiseless npys before deleting them.
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[1/6] generate 200 ARC-ONLY images (seed 111, identical to pilots v3/v4/v4b) ..."
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
$PY run_paltas_pilot.py config_lensfusion_acs_pathb_nonoise.py \
    /home/user/nurkyz/paltas_pathb_pilot_v7 --n 200 --seed 111

echo "[2/6] combine: APERTURE-mag-scaled real LRG deflector + companions + backdrop + noise ..."
$PY hybrid_combine.py --run /home/user/nurkyz/paltas_pathb_pilot_v7 \
    --empty empty_cutouts_4k.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_dapool_images.h5 \
    --out /home/user/nurkyz/einstein_cnn/pathb_pilot_v7.h5 \
    --deflector_stamps deflector_stamps_lrg_v6_train.h5 --deflector_augment --deflector_mag_csv lens_light_empirical.csv \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --seed 112

echo "[3/6] three-stretch preview ..."
$PY preview_three_stretch.py /home/user/nurkyz/einstein_cnn/pathb_pilot_v7.h5 --n 16

echo "[4/6] realism gate ..."
$PY gate_stage0.py --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v7.h5 \
    --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --csv failure_features_slacs.csv \
    --meta /home/user/nurkyz/paltas_pathb_pilot_v7/metadata.csv \
    --out gate_pathb_pilot_v7.png

echo "[5/6] real-vs-sim side-by-side ..."
$PY side_by_side_real_sim.py --real /home/user/nurkyz/einstein_cnn/real_slacs_images.h5 \
    --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v7.h5 --n 8 --seed 5 \
    --out real_vs_pathb_pilot_v7run.png

echo "[6/6] radial profile compare (shape + absolute brightness) ..."
$PY radial_profile_compare.py --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v7.h5 \
    --lib deflector_stamps_lrg_v6_train.h5 --label "SIM pilot v7" \
    --out /home/user/nurkyz/cosmos_acs/tiles/radial_profile_v7.png

echo "[7/7] P5 arc-visibility metric (noiseless arc footprint vs composed image) ..."
$PY arc_snr_metric.py --run /home/user/nurkyz/paltas_pathb_pilot_v7 \
    --sim /home/user/nurkyz/einstein_cnn/pathb_pilot_v7.h5

rm -f /home/user/nurkyz/paltas_pathb_pilot_v7/image_*.npy
echo "PATHB_PILOT_V7_DONE"
