#!/bin/bash
#SBATCH --job-name=g5_c21
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5_c21_pilot.out

# GEN5 (C21) z-MIGRATION PILOT v2 (2026-07-22, post-Nurkyz-review fixes:
# source arcs dimmed DL+K from Newton z_ref, companions dimmed by mig_sb;
# theta_E/label/AR3 scaling VERIFIED correct in v1) — ONE regen carries,
# per the 07-14
# endgame ruling: AR3 isophote-anchored multipoles + z-migration + C15a/b
# (in manifest) + C10 sidecar HARD GATE + AR1 arc-Poisson + AR2 coupled
# shear + C14 AR0 arc gate. Library = the 488-stamp G1b build STANDALONE
# (Nurkyz ruling 2026-07-22). q-scatter still ad-hoc (C2 fit = named
# prerequisite before FULL generation; data source Zenodo 6104823).
# Gates: FJ + stage0 vs REAL Q1 (frozen f2p85_zoom) + AR0 vs Q1 +
# romanise -> Rung 0 stats gate + side-by-sides. NO full generation here.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5_c21_pilot
mkdir -p "$P"
cd "$TILES"

$PY g5_make_manifest.py --kine g1b_kinematics_v1.csv --n 1400 --seed 950 \
    --tmin 0.15 --tmax 3.70 --couple_shear --out "$P/manifest_pilot.csv"

# C10 HARD GATE: no sidecar / multipoles OFF / migration OFF => abort
$PY c10_check.py "$P/manifest_pilot.csv" --require multipoles z_migration \
    fj_channel c15a_sigma_norm c15b_intrinsic_scatter gamma_coupling

export LF_PSF_KERNEL=psf_bank_v2/kernel_00_extended.npy
export LF_G2_MANIFEST="$P/manifest_pilot.csv"
$PY run_paltas_pilot.py config_lensfusion_acs_g5.py "$P/sub_pilot" --n 200 --seed 951 \
    2>&1 | tee "$P/render.log"
grep -q "GEN5 SOURCE DIMMING ACTIVE" "$P/render.log" || {
    echo "GEN5 GATE FAIL: source-dimming banner missing from render log"; exit 1; }
$PY g2_join_assign.py "$P/sub_pilot" "$P/manifest_pilot.csv" "$P/assign_pilot.csv"

$PY hybrid_combine.py --run "$P/sub_pilot" --empty empty_cutouts_expanded_screened.h5 \
    --real "$EC/real_dapool_images.h5" \
    --out "$P/native_pilot.h5" --seed 952 \
    --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
    --deflector_manifest "$P/assign_pilot.csv" --deflector_jitter 1.0 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 \
    --arc_poisson

$PY g2_gate_fj.py "$P/assign_pilot.csv"

# --- Euclid arm: gate vs the REAL Q1 population (frozen #25 convention) ---
cd "$EC"
$PY euclidise.py --inp "$P/native_pilot.h5" --out "$P/euclid_pilot.h5" --seed 954
cd "$TILES"
# --csv is a required legacy arg (SLACS sky_rms overlay panel — ignore that
# panel; the sim-vs-real Q1 stats + asinh overlay are the gate here)
$PY gate_stage0.py --sim "$P/euclid_pilot.h5" \
    --real /home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5 \
    --csv failure_features_slacs.csv \
    --meta "$P/sub_pilot/metadata.csv" \
    --out "$P/gate_q1_stats.png" || echo "GATE_Q1_NONZERO (read the numbers)"
$PY ar0_arc_gate.py --sim "$P/euclid_pilot.h5" \
    --real /home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5 \
    --n 200 --tag g5_c21_q1 || echo "AR0_Q1_NONZERO (read the numbers)"
$PY side_by_side_real_sim.py \
    --real /home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5 \
    --sim "$P/euclid_pilot.h5" --n 8 --seed 5 \
    --out "$P/real_vs_sim_q1.png"

# --- Roman arm: romanise at the sky-matched FLUX, Rung 0 stats gate ---
export LF_ROM_FLUX=0.09
$PY romanise.py --inp "$P/native_pilot.h5" --out "$P/roman_pilot.h5" --seed 953
export LF_G5ROM_DIR="$P"
$PY g5rom_pilot_gate.py || echo "ROM_GATE_NONZERO (read the numbers)"

echo "GEN5_C21_PILOT_DONE"
