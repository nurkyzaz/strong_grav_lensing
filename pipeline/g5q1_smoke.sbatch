#!/bin/bash
#SBATCH --job-name=g5q1_smoke
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:40:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5q1_smoke.out
# GEN5 C37 smoke test: render 8 lensed images with the REAL Q1 delensed sources
# (config_lensfusion_acs_g5q1) to validate the Q1SourceCatalog integration and
# eyeball whether the arcs form sensibly. Reuses the existing pilot manifest.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5q1_smoke
M=/home/user/nurkyz/paltas_g5_c21_pilot/manifest_pilot.csv
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
mkdir -p "$P"
cd "$TILES"
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST="$M"
export LF_Q1_SRC=/home/user/nurkyz/cosmos_acs/q1_slde/q1_sources_smooth.h5
export LF_Q1_PIXSCALE=${LF_Q1_PIXSCALE:-0.05}
$PY run_paltas_pilot.py config_lensfusion_acs_g5q1.py "$P/sub" --n 8 --seed 951 \
    2>&1 | tee "$P/render.log"
grep -q "Q1 SOURCE LIBRARY ACTIVE" "$P/render.log" || { echo "FAIL: Q1 source banner missing"; exit 1; }
$PY g2_join_assign.py "$P/sub" "$M" "$P/assign.csv"
$PY hybrid_combine.py --run "$P/sub" --empty empty_cutouts_expanded_screened.h5 \
    --real "$EC/real_dapool_images.h5" \
    --out "$P/native.h5" --seed 952 \
    --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
    --deflector_manifest "$P/assign.csv" --deflector_jitter 1.0 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 2 --companion_rate_hi 9 --companion_flux_pct 35 --arc_poisson
cd "$EC"
export LF_EUC_SKY_SCALE=2.2
$PY euclidise.py --inp "$P/native.h5" --out "$P/euclid.h5" --seed 955
cd "$TILES"
$PY side_by_side_real_sim.py --real "$Q1REAL" --sim "$P/euclid.h5" \
    --n 8 --seed 5 --out "$P/real_vs_sim_g5q1_smoke.png"
echo "G5Q1_SMOKE_DONE (pixscale $LF_Q1_PIXSCALE)"
