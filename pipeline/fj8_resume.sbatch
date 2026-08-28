#!/bin/bash
#SBATCH --job-name=fj8
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/fj8_resume.out
# Re-composite the EXISTING fj7 render (no re-render) with the two data-driven fixes:
#   C47 FJ faint-tail clip [19.2, 23.4] -> removes deflectors fainter than real ever
#       is (real max 23.4); fixes the "invisible deflector" images (NOT a noise issue
#       -- sky RMS already matches real).
#   C48 selection sky-SNR floor 7.6 (= real Q1 arc-SNR q25): drops diffuse-blob
#       "arcs" (low peak/sky) that the azimuthal-residual metric passed.
# Deflector FJ + edge-smooth + offset all UNCHANGED (morphology already matched).
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5cosmos_fj7
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
cd "$TILES"
$PY hybrid_combine.py --run "$P/sub" --empty empty_cutouts_expanded_screened.h5 \
    --real "$EC/real_dapool_images.h5" \
    --out "$P/native_fj8.h5" --seed 982 \
    --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
    --deflector_manifest "$P/assign.csv" --deflector_jitter 1.0 \
    --deflector_fj --fj_mag0 21.39 --fj_slope 4.5 --fj_theta0 0.88 --fj_scatter 1.15 \
    --fj_mag_min 19.2 --fj_mag_max 23.4 \
    --deflector_edgesmooth 1.5 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 0 --companion_rate_hi 3 --companion_flux_pct 35 \
    --companion_rmin 30 --companion_area_uniform --arc_poisson
cd "$EC"
export LF_EUC_SKY_SCALE=2.2 LF_EUC_NOISE_CORR=0.45
$PY euclidise.py --inp "$P/native_fj8.h5" --out "$P/euclid_fj8.h5" --seed 985
$PY arc_visibility_select.py --arcs "$P/sub_arcs" --sim "$P/euclid_fj8.h5" \
    --out "$P/euclid_sel_fj8.h5" --thresh 6 --min_extent 100 --min_sky_snr 7.6
cd "$TILES"
$PY ar0_arc_gate.py --sim "$P/euclid_sel_fj8.h5" --real "$Q1REAL" --n 80 --tag fj8 || echo AR0NZ
echo FJ8_DONE
