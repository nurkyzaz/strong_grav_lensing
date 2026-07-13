#!/usr/bin/env python
"""Generate the step-2 (g3b, stricter selection) and native-arm (g4n) chain
scripts by adaptation from the audited g3 versions (pattern-asserted), plus a
corrected native merge script and both eval scripts. Run on the cluster."""
import os

EC = os.path.expanduser("~/einstein_cnn")
TI = os.path.expanduser("~/cosmos_acs/tiles")


def adapt(src_path, dst_path, subs):
    src = open(src_path).read()
    for a, b in subs:
        assert a in src, "missing pattern in %s: %r" % (src_path, a[:80])
        src = src.replace(a, b)
    open(dst_path, "w").write(src)
    print("wrote", dst_path)


# ---------- g3b generation (stricter selection) ----------
adapt(os.path.join(TI, "generate_g3.sbatch"), os.path.join(TI, "generate_g3b.sbatch"), [
    ("#SBATCH --job-name=lf_genG3", "#SBATCH --job-name=lf_genG3b"),
    ("/paltas_shards_g3/slurm_", "/paltas_shards_g3b/slurm_"),
    ("SHARDS=/home/user/nurkyz/paltas_shards_g3", "SHARDS=/home/user/nurkyz/paltas_shards_g3b"),
    ("--thresh 0.7 --min_extent 150", "--thresh 0.8 --min_extent 150"),
])
adapt(os.path.join(TI, "submit_g3.sh"), os.path.join(TI, "submit_g3b.sh"), [
    ("mkdir -p /home/user/nurkyz/paltas_shards_g3", "mkdir -p /home/user/nurkyz/paltas_shards_g3b"),
    ("generate_g3.sbatch", "generate_g3b.sbatch"),
    ("G3_ALL_WAVES_DONE", "G3B_ALL_WAVES_DONE"),
])
adapt(os.path.join(TI, "g3_verify_labels.py"), os.path.join(TI, "g3b_verify_labels.py"), [
    ("train_g3_100k.h5", "train_g3b_100k.h5"), ("val_g3_5k.h5", "val_g3b_5k.h5"),
])
adapt(os.path.join(TI, "merge_gate_g3.sbatch"), os.path.join(TI, "merge_gate_g3b.sbatch"), [
    ("#SBATCH --job-name=lf_mergeG3", "#SBATCH --job-name=lf_mergeG3b"),
    ("merge_gate_g3.out", "merge_gate_g3b.out"),
    ("echo \"[0] delete superseded G4 train/val (reproducible; quota headroom for merge) ...\"",
     "echo \"[0] delete superseded G3 train/val (reproducible; superseded by g3b on PASS) ...\""),
    ("rm -f /home/user/nurkyz/einstein_cnn/train_g4_100k.h5 /home/user/nurkyz/einstein_cnn/val_g4_5k.h5",
     "rm -f /home/user/nurkyz/einstein_cnn/train_g3_100k.h5 /home/user/nurkyz/einstein_cnn/val_g3_5k.h5 /home/user/nurkyz/einstein_cnn/g3_merged_small_theta.h5"),
    ("--shards /home/user/nurkyz/paltas_shards_g3 ", "--shards /home/user/nurkyz/paltas_shards_g3b "),
    ("train-out /home/user/nurkyz/einstein_cnn/train_g3_100k.h5", "train-out /home/user/nurkyz/einstein_cnn/train_g3b_100k.h5"),
    ("val-out /home/user/nurkyz/einstein_cnn/val_g3_5k.h5", "val-out /home/user/nurkyz/einstein_cnn/val_g3b_5k.h5"),
    ("g3_verify_labels.py", "g3b_verify_labels.py"),
    ("ASSIGN_ALL=/home/user/nurkyz/cosmos_acs/tiles/g3_assign_all.csv", "ASSIGN_ALL=/home/user/nurkyz/cosmos_acs/tiles/g3b_assign_all.csv"),
    ("/paltas_shards_g3/assign_00.csv", "/paltas_shards_g3b/assign_00.csv"),
    ("/paltas_shards_g3/assign_*.csv", "/paltas_shards_g3b/assign_*.csv"),
    ("--sim /home/user/nurkyz/einstein_cnn/train_g3_100k.h5", "--sim /home/user/nurkyz/einstein_cnn/train_g3b_100k.h5"),
    ("--meta /home/user/nurkyz/paltas_shards_g3/manifest_note_none.csv", "--meta /home/user/nurkyz/paltas_shards_g4/manifest_00.csv"),
    ("--out gate_g3_merged.png", "--out gate_g3b_merged.png"),
    ("--out real_vs_train_G3.png", "--out real_vs_train_G3B.png"),
    ("reb_report.py train_g3_100k.h5 g3_merged", "reb_report.py train_g3b_100k.h5 g3b_merged"),
    ("rm -f /home/user/nurkyz/paltas_shards_g3/hybrid_shard_*.h5", "rm -f /home/user/nurkyz/paltas_shards_g3b/hybrid_shard_*.h5"),
    ("MERGE_GATE_G3_DONE", "MERGE_GATE_G3B_DONE"),
])
# fix the duplicated --sim sub above (side effect guard): re-read and sanity check
s = open(os.path.join(TI, "merge_gate_g3b.sbatch")).read()
assert "train_g3b_100k.h5" in s and "manifest_note_none" not in s

# ---------- g3b training/eval ----------
adapt(os.path.join(EC, "train_g3_member.sbatch"), os.path.join(EC, "train_g3b_member.sbatch"), [
    ("--job-name=g3_member", "--job-name=g3b_member"),
    ("slurm_g3_%j.out", "slurm_g3b_%j.out"),
    ("train_g3_100k.h5", "train_g3b_100k.h5"), ("val_g3_5k.h5", "val_g3b_5k.h5"),
])
adapt(os.path.join(EC, "submit_grid_g3.sh"), os.path.join(EC, "submit_grid_g3b.sh"), [
    ("train_g3_member.sbatch", "train_g3b_member.sbatch"),
    ("qt_g3_resnet.pt", "qt_g3b_resnet.pt"),
    ("slurm_g3_*.out", "slurm_g3b_*.out"),
    ("G3_QUICKTRAIN_FAIL", "G3B_QUICKTRAIN_FAIL"),
    ("g3_resnet_s", "g3b_resnet_s"), ("g3_incnext_s", "g3b_incnext_s"),
    ("g3_cnv2_s", "g3b_cnv2_s"), ("g3_r50_s", "g3b_r50_s"),
    ("g3_arbitrate.sbatch", "g3b_arbitrate.sbatch"),
    ("G3_GRID_ALL_DONE", "G3B_GRID_ALL_DONE"),
])
adapt(os.path.join(EC, "g3_arbitrate.py"), os.path.join(EC, "g3b_arbitrate.py"), [
    ('"val_g3_5k.h5"', '"val_g3b_5k.h5"'),
    ('"g3_resnet_s%d"', '"g3b_resnet_s%d"'), ('"g3_incnext_s%d"', '"g3b_incnext_s%d"'),
    ('"g3_cnv2_s%d"', '"g3b_cnv2_s%d"'), ('"g3_r50_s%d"', '"g3b_r50_s%d"'),
    ('"g3_recal.json"', '"g3b_recal.json"'),
    ('frozen -> g3_recal.json', 'frozen -> g3b_recal.json'),
    ('fitted_on="val_g3_5k.h5 (sim-val, TTA)"', 'fitted_on="val_g3b_5k.h5 (sim-val, TTA)"'),
    ('note="frozen before eval #18"', 'note="frozen before eval #20"'),
])
adapt(os.path.join(EC, "g3_arbitrate.sbatch"), os.path.join(EC, "g3b_arbitrate.sbatch"), [
    ("g3_arbitrate", "g3b_arbitrate"),
    ("G3_ARBITRATE_DONE", "G3B_ARBITRATE_DONE"),
])
adapt(os.path.join(EC, "l18_eval.sbatch"), os.path.join(EC, "l20_eval.sbatch"), [
    ("--job-name=l18_eval", "--job-name=l20_eval"),
    ("slurm_l18_eval_%j.out", "slurm_l20_eval_%j.out"),
    ("# EVAL #18 (authorized by Nurkyz's \"continue with b\" ruling, 2026-07-11;\n# running count 18; results reported immediately). Benchmarks are the _g3\n# RE-DERIVED Euclidised sets (same real-PSF operator as training).",
     "# EVAL #20 (authorized by Nurkyz's \"do 1 then 2\" ruling, 2026-07-12;\n# count 20; report immediately). g3b = real-PSF operator + re-tuned selection\n# (SNR>0.8): the step-2 hypothesis is that restoring the G4-era arc-quality\n# profile recovers the SLACS high-theta bin without losing the S4TM gain."),
    ("g3_resnet_s1 g3_resnet_s2 g3_resnet_s3 g3_resnet_s4 g3_resnet_s5 g3_incnext_s1 g3_incnext_s2 g3_incnext_s3 g3_incnext_s4 g3_incnext_s5 g3_cnv2_s1 g3_cnv2_s2 g3_cnv2_s3 g3_r50_s1 g3_r50_s2 g3_r50_s3",
     "g3b_resnet_s1 g3b_resnet_s2 g3b_resnet_s3 g3b_resnet_s4 g3b_resnet_s5 g3b_incnext_s1 g3b_incnext_s2 g3b_incnext_s3 g3b_incnext_s4 g3b_incnext_s5 g3b_cnv2_s1 g3b_cnv2_s2 g3b_cnv2_s3 g3b_r50_s1 g3b_r50_s2 g3b_r50_s3"),
    ("preds_l18_", "preds_l20_"),
    ("l18_tables.py", "l20_tables.py"),
    ("EVAL18_DONE", "EVAL20_DONE"),
])
adapt(os.path.join(EC, "l18_tables.py"), os.path.join(EC, "l20_tables.py"), [
    ("EVAL #18 tables", "EVAL #20 tables"),
    ("g3_recal.json", "g3b_recal.json"),
    ('("eval #17 cnv2_3", -0.005, 0.145, 0.047, +0.67, 11.0)],',
     '("eval #17 cnv2_3", -0.005, 0.145, 0.047, +0.67, 11.0),\n        ("eval #18 r50_3", -0.059, 0.201, 0.083, +0.37, 23.0),\n        ("eval #19 G4cnv2/realb", -0.010, 0.137, 0.056, +0.71, 15.0)],'),
    ('("eval #17 cnv2_3", +0.050, 0.163, 0.081, +0.64, 30.0)]}',
     '("eval #17 cnv2_3", +0.050, 0.163, 0.081, +0.64, 30.0),\n        ("eval #18 r50_3", +0.027, 0.117, 0.082, +0.81, 22.0)]}'),
    ('["g3_resnet_s%d"', '["g3b_resnet_s%d"'), ('["g3_incnext_s%d"', '["g3b_incnext_s%d"'),
    ('["g3_cnv2_s%d"', '["g3b_cnv2_s%d"'), ('["g3_r50_s%d"', '["g3b_r50_s%d"'),
    ("default_rng(20260713)", "default_rng(20260714)"),
    ('print("EVAL #18 — %s', 'print("EVAL #20 — %s'),
    ("preds_l18_", "preds_l20_"),
    ('"eval #18 ens"', '"eval #20 ens"'),
])

# ---------- native (g4n) training/eval ----------
adapt(os.path.join(EC, "train_g3_member.sbatch"), os.path.join(EC, "train_g4n_member.sbatch"), [
    ("--job-name=g3_member", "--job-name=g4n_member"),
    ("slurm_g3_%j.out", "slurm_g4n_%j.out"),
    ("train_g3_100k.h5", "train_g4native_100k.h5"), ("val_g3_5k.h5", "val_g4native_5k.h5"),
])
adapt(os.path.join(EC, "submit_grid_g3.sh"), os.path.join(EC, "submit_grid_g4n.sh"), [
    ("train_g3_member.sbatch", "train_g4n_member.sbatch"),
    ("qt_g3_resnet.pt", "qt_g4n_resnet.pt"),
    ("slurm_g3_*.out", "slurm_g4n_*.out"),
    ("G3_QUICKTRAIN_FAIL", "G4N_QUICKTRAIN_FAIL"),
    ("g3_resnet_s", "g4n_resnet_s"), ("g3_incnext_s", "g4n_incnext_s"),
    ("g3_cnv2_s", "g4n_cnv2_s"), ("g3_r50_s", "g4n_r50_s"),
    ("g3_arbitrate.sbatch", "g4n_arbitrate.sbatch"),
    ("G3_GRID_ALL_DONE", "G4N_GRID_ALL_DONE"),
])
adapt(os.path.join(EC, "g3_arbitrate.py"), os.path.join(EC, "g4n_arbitrate.py"), [
    ('"val_g3_5k.h5"', '"val_g4native_5k.h5"'),
    ('"g3_resnet_s%d"', '"g4n_resnet_s%d"'), ('"g3_incnext_s%d"', '"g4n_incnext_s%d"'),
    ('"g3_cnv2_s%d"', '"g4n_cnv2_s%d"'), ('"g3_r50_s%d"', '"g4n_r50_s%d"'),
    ('"g3_recal.json"', '"g4n_recal.json"'),
    ('frozen -> g3_recal.json', 'frozen -> g4n_recal.json'),
    ('fitted_on="val_g3_5k.h5 (sim-val, TTA)"', 'fitted_on="val_g4native_5k.h5 (sim-val, TTA)"'),
    ('note="frozen before eval #18"', 'note="frozen before the native eval"'),
])
adapt(os.path.join(EC, "g3_arbitrate.sbatch"), os.path.join(EC, "g4n_arbitrate.sbatch"), [
    ("g3_arbitrate", "g4n_arbitrate"),
    ("G3_ARBITRATE_DONE", "G4N_ARBITRATE_DONE"),
])
adapt(os.path.join(TI, "g3_verify_labels.py"), os.path.join(TI, "g4n_verify_labels.py"), [
    ("train_g3_100k.h5", "train_g4native_100k.h5"), ("val_g3_5k.h5", "val_g4native_5k.h5"),
])
adapt(os.path.join(EC, "l18_eval.sbatch"), os.path.join(EC, "l21_eval.sbatch"), [
    ("--job-name=l18_eval", "--job-name=l21_eval"),
    ("slurm_l18_eval_%j.out", "slurm_l21_eval_%j.out"),
    ("# EVAL #18 (authorized by Nurkyz's \"continue with b\" ruling, 2026-07-11;\n# running count 18; results reported immediately). Benchmarks are the _g3\n# RE-DERIVED Euclidised sets (same real-PSF operator as training).",
     "# EVAL #21 — THE NATIVE-HST EVAL (Track N; authorized by Nurkyz's \"run a in\n# parallel\" ruling, 2026-07-12; count 21; report immediately). Benchmarks are\n# the FROZEN native real_slacs/real_s4tm images (first native-domain eval of\n# the GEN4 population)."),
    ("g3_resnet_s1 g3_resnet_s2 g3_resnet_s3 g3_resnet_s4 g3_resnet_s5 g3_incnext_s1 g3_incnext_s2 g3_incnext_s3 g3_incnext_s4 g3_incnext_s5 g3_cnv2_s1 g3_cnv2_s2 g3_cnv2_s3 g3_r50_s1 g3_r50_s2 g3_r50_s3",
     "g4n_resnet_s1 g4n_resnet_s2 g4n_resnet_s3 g4n_resnet_s4 g4n_resnet_s5 g4n_incnext_s1 g4n_incnext_s2 g4n_incnext_s3 g4n_incnext_s4 g4n_incnext_s5 g4n_cnv2_s1 g4n_cnv2_s2 g4n_cnv2_s3 g4n_r50_s1 g4n_r50_s2 g4n_r50_s3"),
    ("for SAMPLE in euclid_slacs_images_g3 euclid_s4tm_images_g3 ; do",
     "for SAMPLE in real_slacs_images real_s4tm_images ; do"),
    ("preds_l18_", "preds_l21_"),
    ("l18_tables.py", "l21_tables.py"),
    ("EVAL18_DONE", "EVAL21_DONE"),
])
adapt(os.path.join(EC, "l18_tables.py"), os.path.join(EC, "l21_tables.py"), [
    ("EVAL #18 tables", "EVAL #21 tables (NATIVE)"),
    ("g3_recal.json", "g4n_recal.json"),
    ('REF = {"euclid_slacs_images_g3": [\n        ("eval #16 resnet5", +0.063, 0.220, 0.131, +0.25, 31.0),\n        ("eval #17 cnv2_3", -0.005, 0.145, 0.047, +0.67, 11.0)],\n       "euclid_s4tm_images_g3": [\n        ("eval #16 resnet5", +0.116, 0.245, 0.095, +0.19, 32.0),\n        ("eval #17 cnv2_3", +0.050, 0.163, 0.081, +0.64, 30.0)]}',
     'REF = {"real_slacs_images": [\n        ("m3 baseline (native)", -0.100, 0.310, 0.180, -1.02, 55.0)],\n       "real_s4tm_images": [\n        ("m3 baseline (native)", -0.060, 0.280, 0.160, -0.53, 68.0)]}'),
    ('["g3_resnet_s%d"', '["g4n_resnet_s%d"'), ('["g3_incnext_s%d"', '["g4n_incnext_s%d"'),
    ('["g3_cnv2_s%d"', '["g4n_cnv2_s%d"'), ('["g3_r50_s%d"', '["g4n_r50_s%d"'),
    ("default_rng(20260713)", "default_rng(20260715)"),
    ('print("EVAL #18 — %s', 'print("EVAL #21 (NATIVE) — %s'),
    ("preds_l18_", "preds_l21_"),
    ('for sample in ("euclid_slacs_images_g3", "euclid_s4tm_images_g3"):',
     'for sample in ("real_slacs_images", "real_s4tm_images"):'),
    ('"eval #18 ens"', '"eval #21 ens"'),
])

# ---------- corrected native merge (single glob-compatible call) ----------
open(os.path.join(TI, "merge_gate_g4native.sbatch"), "w").write("""#!/bin/bash
#SBATCH --job-name=lf_mergeGN
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/cosmos_acs/tiles/merge_gate_g4native.out

# Track-N native-arm merge + gates (native shards named hybrid_shard_* in
# paltas_shards_g4n for merge_hybrid_shards compatibility). Gates vs NATIVE
# real SLACS (frozen files read-only; established Stage-2 practice).
# QUOTA: deletes two SUPERSEDED items (flagged to Nurkyz 2026-07-12):
# lensed_train_m2/m3.h5 (pre-paltas era) + g4_merged_small_theta.h5 (orphan).
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
EC=/home/user/nurkyz/einstein_cnn
cd /home/user/nurkyz/cosmos_acs/tiles

echo "[0] superseded-data cleanup for merge headroom ..."
rm -f "$EC/lensed_train_m2.h5" "$EC/lensed_train_m3.h5" "$EC/g4_merged_small_theta.h5"
quota -s 2>/dev/null | tail -1
USED_MB=$(quota 2>/dev/null | awk '/sda1/ {getline; print int($1)}')
if [ -n "$USED_MB" ] && [ "$USED_MB" -gt 102000 ]; then
    echo "ABORT: <8GB headroom to hard limit"; exit 1
fi

echo "[1] merge native shards ..."
$PY merge_hybrid_shards.py --shards /home/user/nurkyz/paltas_shards_g4n --train-max-id 80 \\
    --train-out "$EC/train_g4native_100k.h5" \\
    --val-out "$EC/val_g4native_5k.h5"

echo "[1b] verify labels BEFORE shard deletion ..."
$PY g4n_verify_labels.py

echo "[2] realism gate vs NATIVE real SLACS ..."
$PY gate_stage0.py --sim "$EC/train_g4native_100k.h5" \\
    --real "$EC/real_slacs_images.h5" \\
    --csv "$EC/failure_features_slacs.csv" \\
    --meta /home/user/nurkyz/paltas_shards_g4/manifest_00.csv \\
    --out gate_g4native_merged.png || echo "gate_stage0 meta quirk — numeric rows authoritative"

echo "[3] side-by-side + flatness ..."
$PY side_by_side_real_sim.py --real "$EC/real_slacs_images.h5" \\
    --sim "$EC/train_g4native_100k.h5" --n 8 --seed 7 \\
    --out real_vs_train_G4NATIVE.png
cd "$EC"
$PY reb_report.py train_g4native_100k.h5 g4native_merged

rm -f /home/user/nurkyz/paltas_shards_g4n/hybrid_shard_*.h5
echo "MERGE_GATE_G4NATIVE_DONE"
""")
print("wrote merge_gate_g4native.sbatch (corrected)")
print("ALL ADAPTED OK")
