#!/bin/bash
#SBATCH --job-name=g5_v4
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:30:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/g5_c21_v4.out

# GEN5 v4: deflector passive-evolution brightening (Q=1.2 mag/z, Faber+2007
# red sequence — PHYSICS PENDING NURKYZ/BRIAN CONFIRM) applied via mig_sb.
# Same manifest seed 950 -> identical theta/z draws (verified in-job), so the
# v2 paltas renders are REUSED: rebuild manifest -> re-join -> re-combine ->
# euclidise (sky 2.2) -> selection -> gates + romanise (FLUX 0.17) -> gates.
set -e
set -o pipefail
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
TILES=/home/user/nurkyz/cosmos_acs/tiles
EC=/home/user/nurkyz/einstein_cnn
P=/home/user/nurkyz/paltas_g5_c21_pilot
cd "$TILES"

$PY g5_make_manifest.py --kine g1b_kinematics_v1.csv --n 1400 --seed 950 \
    --tmin 0.15 --tmax 3.70 --couple_shear --evo_q 1.2 \
    --out "$P/manifest_v4.csv"
$PY c10_check.py "$P/manifest_v4.csv" --require multipoles z_migration \
    fj_channel c15a_sigma_norm c15b_intrinsic_scatter gamma_coupling

# determinism guard: theta/z draws must be IDENTICAL to the rendered v2
# manifest (only mig_sb changed) or the render reuse is invalid
$PY - "$P/manifest_pilot.csv" "$P/manifest_v4.csv" <<'PYEOF'
import csv, sys
a = list(csv.DictReader(open(sys.argv[1])))
b = list(csv.DictReader(open(sys.argv[2])))
assert len(a) == len(b), "row count changed"
for ra, rb in zip(a, b):
    for col in ("stamp_id", "theta_E", "z_source", "z_l_new", "mig_scale",
                "mass_e1", "mult4_a"):
        assert ra[col] == rb[col], "draw mismatch in %s: %s vs %s" % (
            col, ra[col], rb[col])
print("DETERMINISM GUARD PASS: %d rows identical except mig_sb" % len(a))
PYEOF

$PY g2_join_assign.py "$P/sub_pilot" "$P/manifest_v4.csv" "$P/assign_v4.csv"
$PY hybrid_combine.py --run "$P/sub_pilot" --empty empty_cutouts_expanded_screened.h5 \
    --real "$EC/real_dapool_images.h5" \
    --out "$P/native_v4.h5" --seed 952 \
    --deflector_stamps deflector_stamps_lrg2b_raw.h5 \
    --deflector_manifest "$P/assign_v4.csv" --deflector_jitter 1.0 \
    --companion_stamps source_stamps_clean.h5 \
    --companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 \
    --arc_poisson
$PY g2_gate_fj.py "$P/assign_v4.csv"

cd "$EC"
export LF_EUC_SKY_SCALE=2.2
$PY euclidise.py --inp "$P/native_v4.h5" --out "$P/euclid_v4.h5" --seed 957
$PY arc_visibility_select.py --arcs "$P/sub_pilot_euclid_arcs" \
    --sim "$P/euclid_v4.h5" --out "$P/euclid_v4_selected.h5" \
    --thresh 0.8 --min_extent 150

cd "$TILES"
$PY gate_stage0.py --sim "$P/euclid_v4_selected.h5" \
    --real /home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5 \
    --csv failure_features_slacs.csv \
    --meta "$P/sub_pilot/metadata.csv" \
    --out "$P/gate_q1_stats_v4.png" || echo "GATE_Q1_NONZERO (read the numbers)"
$PY ar0_arc_gate.py --sim "$P/euclid_v4_selected.h5" \
    --real /home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5 \
    --n 200 --tag g5_c21_q1_v4 || echo "AR0_Q1_NONZERO (read the numbers)"
$PY side_by_side_real_sim.py \
    --real /home/user/nurkyz/cosmos_acs/q1_slde/q1_slde_eval_f2p85_zoom.h5 \
    --sim "$P/euclid_v4_selected.h5" --n 8 --seed 5 \
    --out "$P/real_vs_sim_q1_v4.png"

export LF_ROM_FLUX=0.17
$PY romanise.py --inp "$P/native_v4.h5" --out "$P/roman_pilot.h5" --seed 958
export LF_G5ROM_DIR="$P"
$PY g5rom_pilot_gate.py || echo "ROM_GATE_NONZERO (read the numbers)"

echo "GEN5_C21_V4_DONE"
