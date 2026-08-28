#!/bin/bash
#SBATCH --job-name=g5cos_fj9
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5cosmos_fj9_pilot.out
# GEN5 fj9: PHYSICS coupling fix (GEN5_REALISM_PLAN #7). Source offset ABSOLUTE
# (beta uniform-in-area r_max 0.7, independent of theta_E) instead of theta-scaled
# -> restores the magnification-theta coupling: small-theta lenses get larger
# beta/theta_E -> lower mu -> fainter arcs (real rho(arc,theta)~-0.11; theta-scaling
# gave +0.05, small-theta arcs too bright vs deflector). Carries all matched knobs:
# FJ mag0 21.39 + faint-tail clip [19.2,23.4], edge-smooth 1.5, mag_cut 2.0,
# selection sky-SNR floor 7.6. Validates coupling + completeness + accepted theta_E.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5cosmos_fj9
M=/home/user/nurkyz/paltas_g5_c21_pilot/manifest_match_abs.csv
Q1REAL=/home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5
mkdir -p "$P"
cd "$TILES"
export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST="$M"
export LF_SB_CUT=21.5
export LF_SRC_ABSMAG=-24.5
export LF_MIN_FLUX_RADIUS=1.0
export LF_MIN_SIZE_PX=8
export LF_MAG_CUT=2.0
$PY run_paltas_pilot.py config_lensfusion_acs_g5cosmos.py "$P/sub" --n 240 --seed 991
$PY g2_join_assign.py "$P/sub" "$M" "$P/assign.csv"
$PY hybrid_combine.py --run "$P/sub" --empty empty_cutouts_expanded_screened.h5 \
    --real "$EC/real_dapool_images.h5" \
    --out "$P/native.h5" --seed 992 \
    --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
    --deflector_manifest "$P/assign.csv" --deflector_jitter 1.0 \
    --deflector_fj --fj_mag0 21.39 --fj_slope 4.5 --fj_theta0 0.88 --fj_scatter 1.15 \
    --fj_mag_min 19.2 --fj_mag_max 23.4 --deflector_edgesmooth 1.5 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 0 --companion_rate_hi 3 --companion_flux_pct 35 \
    --companion_rmin 30 --companion_area_uniform --arc_poisson
cd "$EC"
export LF_EUC_SKY_SCALE=2.2 LF_EUC_NOISE_CORR=0.45
$PY euclidise.py --inp "$P/native.h5" --out "$P/euclid.h5" --seed 995
$PY euclidise_arcs.py "$P/sub" "$P/sub_arcs"
$PY arc_visibility_select.py --arcs "$P/sub_arcs" --sim "$P/euclid.h5" \
    --out "$P/euclid_sel.h5" --thresh 6 --min_extent 100 --min_sky_snr 7.6
cd "$TILES"
echo "=== COUPLING + theta_E ==="
$PY coupling.py "$P" euclid.h5 || true
echo "=== MORPHOLOGY ==="
$PY sim_arc_morph.py "$P" || true
echo "=== PHOTOMETRY ==="
$PY measure_phot.py "$P" || true
$PY ar0_arc_gate.py --sim "$P/euclid_sel.h5" --real "$Q1REAL" --n 80 --tag fj9 || echo AR0NZ
echo G5COSMOS_FJ9_DONE
