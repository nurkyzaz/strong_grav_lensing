#!/bin/bash
#SBATCH --job-name=g5cos_ff
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5cosmos_fullfix.out
# GEN5-COSMOS FULL FIX-LIST (Nurkyz): SB cut 21.5, min_flux_radius 1.0,
# minimum_size 8, z-DEPENDENT cosmological dimming (source_absolute_magnitude
# -24 -> apparent ~24.5), deflector_sharpen 1.5, companion 2-9, sky 2.2.
# 120 renders for the rating gallery.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5cosmos_fullfix
M=/home/user/nurkyz/paltas_g5_c21_pilot/manifest_pilot.csv
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
mkdir -p "$P"
cd "$TILES"
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST="$M"
export LF_SB_CUT=21.5
export LF_SRC_ABSMAG=-24.0
export LF_MIN_FLUX_RADIUS=1.0
export LF_MIN_SIZE_PX=8
$PY run_paltas_pilot.py config_lensfusion_acs_g5cosmos.py "$P/sub" --n 120 --seed 951
$PY g2_join_assign.py "$P/sub" "$M" "$P/assign.csv"
$PY hybrid_combine.py --run "$P/sub" --empty empty_cutouts_expanded_screened.h5 \
    --real "$EC/real_dapool_images.h5" \
    --out "$P/native.h5" --seed 952 \
    --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
    --deflector_manifest "$P/assign.csv" --deflector_jitter 1.0 \
    --deflector_sharpen 1.5 --deflector_sharpen_sigma 1.5 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 2 --companion_rate_hi 9 --companion_flux_pct 35 --arc_poisson
cd "$EC"; export LF_EUC_SKY_SCALE=2.2
$PY euclidise.py --inp "$P/native.h5" --out "$P/euclid.h5" --seed 955
$PY euclidise_arcs.py "$P/sub" "$P/sub_euclid_arcs"
$PY arc_visibility_select.py --arcs "$P/sub_euclid_arcs" --sim "$P/euclid.h5" \
    --out "$P/euclid_sel.h5" --thresh 0.8 --min_extent 150 || echo SELECT_NOTE
cd "$TILES"
echo "--- stage0 + AR0 vs real ---"
$PY gate_stage0.py --sim "$P/euclid.h5" --real "$Q1REAL" --csv failure_features_slacs.csv \
    --meta "$P/sub/metadata.csv" --out "$P/gate.png" || echo GATE_NZ
$PY ar0_arc_gate.py --sim "$P/euclid.h5" --real "$Q1REAL" --n 120 --tag g5cos_ff || echo AR0_NZ
$PY side_by_side_real_sim.py --real "$Q1REAL" --sim "$P/euclid.h5" --n 8 --seed 5 \
    --out "$P/sbs_fullfix.png"
echo "G5COSMOS_FULLFIX_DONE"
