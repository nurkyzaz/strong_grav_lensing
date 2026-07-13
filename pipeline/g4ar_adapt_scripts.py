#!/usr/bin/env python
"""Generate the g4ar chain (combined AR1 arc-Poisson + AR2 shear coupling on
the g3b recipe) by adaptation from the audited g3b scripts. g4ar generates
FRESH manifests per shard (--couple_shear changes the population version —
draw-identity with G4/G3/g3b is intentionally broken; FJ/flatness gates
re-verify). NOTHING here deletes g3b or native data."""
import os

EC = os.path.expanduser("~/einstein_cnn")
TI = os.path.expanduser("~/cosmos_acs/tiles")


def adapt(src_path, dst_path, subs):
    src = open(src_path).read()
    for a, b in subs:
        assert a in src, "missing pattern in %s: %r" % (src_path, a[:90])
        src = src.replace(a, b)
    open(dst_path, "w").write(src)
    print("wrote", dst_path)


adapt(os.path.join(TI, "generate_g3b.sbatch"), os.path.join(TI, "generate_g4ar.sbatch"), [
    ("#SBATCH --job-name=lf_genG3b", "#SBATCH --job-name=lf_genG4ar"),
    ("/paltas_shards_g3b/slurm_", "/paltas_shards_g4ar/slurm_"),
    ("SHARDS=/home/user/nurkyz/paltas_shards_g3b", "SHARDS=/home/user/nurkyz/paltas_shards_g4ar"),
    # fresh coupled manifests instead of reusing the retained G4 ones
    ('    MAN="$G4/manifest_$(printf \'%02d\' "$S").csv"\n    test -s "$MAN"   # retained manifests ARE the population; never regenerate',
     '    MAN="$SHARDS/manifest_$(printf \'%02d\' "$S").csv"\n'
     '    if [ "$S" -lt 80 ]; then KINE=g4_kine_train.csv; else KINE=g4_kine_val.csv; fi\n'
     '    if [ "$I" -lt 20 ]; then MROWS=3450; else MROWS=1725; fi\n'
     '    $PY g2_make_manifest.py --kine "$KINE" --n "$MROWS" --seed $((9700 + S)) \\\n'
     '        --couple_shear --out "$MAN"'),
    # the draw-identity cmp no longer applies (new population version)
    ('    cmp -s "$ASSIGN" "$G4/assign_$(printf \'%02d\' "$S").csv" \\\n'
     '        && echo "assign identical to G4 run (deterministic re-render confirmed)" \\\n'
     '        || echo "WARN: assign differs from G4 run — self-consistent but not draw-identical; disclose"',
     '    echo "g4ar: new population version (coupled shear) — no draw-identity check"'),
    ("--companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35",
     "--companion_rate_lo 8 --companion_rate_hi 26 --companion_flux_pct 35 --arc_poisson"),
])
adapt(os.path.join(TI, "submit_g3b.sh"), os.path.join(TI, "submit_g4ar.sh"), [
    ("mkdir -p /home/user/nurkyz/paltas_shards_g3b", "mkdir -p /home/user/nurkyz/paltas_shards_g4ar"),
    ("generate_g3b.sbatch", "generate_g4ar.sbatch"),
    ("G3B_ALL_WAVES_DONE", "G4AR_ALL_WAVES_DONE"),
])
adapt(os.path.join(TI, "g3b_verify_labels.py"), os.path.join(TI, "g4ar_verify_labels.py"), [
    ("train_g3b_100k.h5", "train_g4ar_100k.h5"), ("val_g3b_5k.h5", "val_g4ar_5k.h5"),
])
adapt(os.path.join(TI, "merge_gate_g3b.sbatch"), os.path.join(TI, "merge_gate_g4ar.sbatch"), [
    ("#SBATCH --job-name=lf_mergeG3b", "#SBATCH --job-name=lf_mergeG4ar"),
    ("merge_gate_g3b.out", "merge_gate_g4ar.out"),
    # keep g3b (current candidate best) — no deletion in the g4ar merge
    ('echo "[0] delete superseded G3 train/val (reproducible; superseded by g3b on PASS) ..."\n'
     'ls -la /home/user/nurkyz/paltas_shards_g4/manifest_00.csv   # reproducibility anchor must exist\n'
     'rm -f /home/user/nurkyz/einstein_cnn/train_g3_100k.h5 /home/user/nurkyz/einstein_cnn/val_g3_5k.h5 /home/user/nurkyz/einstein_cnn/g3_merged_small_theta.h5',
     'echo "[0] no deletions in the g4ar merge (g3b kept for comparison)"'),
    ("--shards /home/user/nurkyz/paltas_shards_g3b ", "--shards /home/user/nurkyz/paltas_shards_g4ar "),
    ("train-out /home/user/nurkyz/einstein_cnn/train_g3b_100k.h5", "train-out /home/user/nurkyz/einstein_cnn/train_g4ar_100k.h5"),
    ("val-out /home/user/nurkyz/einstein_cnn/val_g3b_5k.h5", "val-out /home/user/nurkyz/einstein_cnn/val_g4ar_5k.h5"),
    ("g3b_verify_labels.py", "g4ar_verify_labels.py"),
    ("ASSIGN_ALL=/home/user/nurkyz/cosmos_acs/tiles/g3b_assign_all.csv", "ASSIGN_ALL=/home/user/nurkyz/cosmos_acs/tiles/g4ar_assign_all.csv"),
    ("/paltas_shards_g3b/assign_00.csv", "/paltas_shards_g4ar/assign_00.csv"),
    ("/paltas_shards_g3b/assign_*.csv", "/paltas_shards_g4ar/assign_*.csv"),
    ("--sim /home/user/nurkyz/einstein_cnn/train_g3b_100k.h5", "--sim /home/user/nurkyz/einstein_cnn/train_g4ar_100k.h5"),
    ("--out gate_g3b_merged.png", "--out gate_g4ar_merged.png"),
    ("--out real_vs_train_G3B.png", "--out real_vs_train_G4AR.png"),
    ("reb_report.py train_g3b_100k.h5 g3b_merged", "reb_report.py train_g4ar_100k.h5 g4ar_merged"),
    ("rm -f /home/user/nurkyz/paltas_shards_g3b/hybrid_shard_*.h5", "rm -f /home/user/nurkyz/paltas_shards_g4ar/hybrid_shard_*.h5"),
    ("MERGE_GATE_G3B_DONE", "MERGE_GATE_G4AR_DONE"),
])
adapt(os.path.join(EC, "train_g3b_member.sbatch"), os.path.join(EC, "train_g4ar_member.sbatch"), [
    ("--job-name=g3b_member", "--job-name=g4ar_member"),
    ("slurm_g3b_%j.out", "slurm_g4ar_%j.out"),
    ("train_g3b_100k.h5", "train_g4ar_100k.h5"), ("val_g3b_5k.h5", "val_g4ar_5k.h5"),
])
adapt(os.path.join(EC, "submit_grid_g3b.sh"), os.path.join(EC, "submit_grid_g4ar.sh"), [
    ("train_g3b_member.sbatch", "train_g4ar_member.sbatch"),
    ("qt_g3b_resnet.pt", "qt_g4ar_resnet.pt"),
    ("slurm_g3b_*.out", "slurm_g4ar_*.out"),
    ("G3B_QUICKTRAIN_FAIL", "G4AR_QUICKTRAIN_FAIL"),
    ("g3b_resnet_s", "g4ar_resnet_s"), ("g3b_incnext_s", "g4ar_incnext_s"),
    ("g3b_cnv2_s", "g4ar_cnv2_s"), ("g3b_r50_s", "g4ar_r50_s"),
    ("g3b_arbitrate.sbatch", "g4ar_arbitrate.sbatch"),
    ("G3B_GRID_ALL_DONE", "G4AR_GRID_ALL_DONE"),
])
adapt(os.path.join(EC, "g3b_arbitrate.py"), os.path.join(EC, "g4ar_arbitrate.py"), [
    ('"val_g3b_5k.h5"', '"val_g4ar_5k.h5"'),
    ('"g3b_resnet_s%d"', '"g4ar_resnet_s%d"'), ('"g3b_incnext_s%d"', '"g4ar_incnext_s%d"'),
    ('"g3b_cnv2_s%d"', '"g4ar_cnv2_s%d"'), ('"g3b_r50_s%d"', '"g4ar_r50_s%d"'),
    ('"g3b_recal.json"', '"g4ar_recal.json"'),
    ('frozen -> g3b_recal.json', 'frozen -> g4ar_recal.json'),
    ('fitted_on="val_g3b_5k.h5 (sim-val, TTA)"', 'fitted_on="val_g4ar_5k.h5 (sim-val, TTA)"'),
    ('note="frozen before eval #20"', 'note="frozen before eval #22"'),
])
adapt(os.path.join(EC, "g3b_arbitrate.sbatch"), os.path.join(EC, "g4ar_arbitrate.sbatch"), [
    ("g3b_arbitrate", "g4ar_arbitrate"),
    ("G3B_ARBITRATE_DONE", "G4AR_ARBITRATE_DONE"),
])
adapt(os.path.join(EC, "l20_eval.sbatch"), os.path.join(EC, "l22_eval.sbatch"), [
    ("--job-name=l20_eval", "--job-name=l22_eval"),
    ("slurm_l20_eval_%j.out", "slurm_l22_eval_%j.out"),
    ("# EVAL #20 (authorized by Nurkyz's \"do 1 then 2\" ruling, 2026-07-12;\n# count 20; report immediately). g3b = real-PSF operator + re-tuned selection\n# (SNR>0.8): the step-2 hypothesis is that restoring the G4-era arc-quality\n# profile recovers the SLACS high-theta bin without losing the S4TM gain.",
     "# EVAL #22 (authorized by Nurkyz's 2026-07-12 overnight ruling: start AR1/AR2\n# automatically, 'it should be done'; count 22; report immediately).\n# g4ar = g3b recipe + AR1 arc shot noise + AR2 shear-misalignment coupling\n# (each change pilot-gated separately before this combined run)."),
    ("g3b_resnet_s1 g3b_resnet_s2 g3b_resnet_s3 g3b_resnet_s4 g3b_resnet_s5 g3b_incnext_s1 g3b_incnext_s2 g3b_incnext_s3 g3b_incnext_s4 g3b_incnext_s5 g3b_cnv2_s1 g3b_cnv2_s2 g3b_cnv2_s3 g3b_r50_s1 g3b_r50_s2 g3b_r50_s3",
     "g4ar_resnet_s1 g4ar_resnet_s2 g4ar_resnet_s3 g4ar_resnet_s4 g4ar_resnet_s5 g4ar_incnext_s1 g4ar_incnext_s2 g4ar_incnext_s3 g4ar_incnext_s4 g4ar_incnext_s5 g4ar_cnv2_s1 g4ar_cnv2_s2 g4ar_cnv2_s3 g4ar_r50_s1 g4ar_r50_s2 g4ar_r50_s3"),
    ("preds_l20_", "preds_l22_"),
    ("l20_tables.py", "l22_tables.py"),
    ("EVAL20_DONE", "EVAL22_DONE"),
])
adapt(os.path.join(EC, "l20_tables.py"), os.path.join(EC, "l22_tables.py"), [
    ("EVAL #20 tables", "EVAL #22 tables"),
    ("g3b_recal.json", "g4ar_recal.json"),
    ('["g3b_resnet_s%d"', '["g4ar_resnet_s%d"'), ('["g3b_incnext_s%d"', '["g4ar_incnext_s%d"'),
    ('["g3b_cnv2_s%d"', '["g4ar_cnv2_s%d"'), ('["g3b_r50_s%d"', '["g4ar_r50_s%d"'),
    ("default_rng(20260714)", "default_rng(20260716)"),
    ('print("EVAL #20 — %s', 'print("EVAL #22 — %s'),
    ("preds_l20_", "preds_l22_"),
    ('"eval #20 ens"', '"eval #22 ens"'),
])
print("G4AR_ADAPT_OK")
