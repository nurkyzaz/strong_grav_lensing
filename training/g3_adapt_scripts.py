#!/usr/bin/env python
"""Generate g3_arbitrate.py / g3_arbitrate.sbatch / l18_eval.sbatch /
l18_tables.py as adaptations of their audited g4/l17 counterparts (textual
substitution + explicit edits; aborts if any expected pattern is missing)."""
import os

EC = os.path.expanduser("~/einstein_cnn")


def adapt(src_fn, dst_fn, subs, must=()):
    src = open(os.path.join(EC, src_fn)).read()
    for pat in must:
        assert pat in src, "missing pattern in %s: %s" % (src_fn, pat[:80])
    for a, b in subs:
        assert a in src, "sub source missing in %s: %s" % (src_fn, a[:80])
        src = src.replace(a, b)
    open(os.path.join(EC, dst_fn), "w").write(src)
    print("wrote", dst_fn)


# --- arbitration ---
adapt("g4_arbitrate.py", "g3_arbitrate.py", [
    ('VAL = os.path.join(HOME, "val_g4_5k.h5")',
     'VAL = os.path.join(HOME, "val_g3_5k.h5")'),
    ('MEMBERS = (["g4_resnet_s%d" % i for i in (1, 2, 3, 4, 5)] +\n'
     '           ["g4_incnext_s%d" % i for i in (1, 2, 3, 4, 5)] +\n'
     '           ["g4_cnv2_s%d" % i for i in (1, 2, 3)] +\n'
     '           ["g4_r50_s%d" % i for i in (1, 2, 3)] +\n'
     '           ["g4_logpolar_s1"])',
     'MEMBERS = (["g3_resnet_s%d" % i for i in (1, 2, 3, 4, 5)] +\n'
     '           ["g3_incnext_s%d" % i for i in (1, 2, 3, 4, 5)] +\n'
     '           ["g3_cnv2_s%d" % i for i in (1, 2, 3)] +\n'
     '           ["g3_r50_s%d" % i for i in (1, 2, 3)])'),
    ('if "g4_logpolar_s1" in mu:\n    V["all17+lp"] = V["all16"] + ["g4_logpolar_s1"]',
     ''),
    ('fitted_on="val_g4_5k.h5 (sim-val, TTA)"',
     'fitted_on="val_g3_5k.h5 (sim-val, TTA)"'),
    ('note="frozen before eval #17"', 'note="frozen before eval #18"'),
    ('"g4_recal.json"', '"g3_recal.json"'),
    ('print("frozen -> g4_recal.json")', 'print("frozen -> g3_recal.json")'),
])

open(os.path.join(EC, "g3_arbitrate.sbatch"), "w").write("""#!/bin/bash
#SBATCH --job-name=g3_arbitrate
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=01:30:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_g3_arbitrate_%j.out
~/miniconda3/envs/Stronglensing/bin/python ~/einstein_cnn/g3_arbitrate.py
echo G3_ARBITRATE_DONE
""")
print("wrote g3_arbitrate.sbatch")

# --- eval #18 ---
open(os.path.join(EC, "l18_eval.sbatch"), "w").write("""#!/bin/bash
#SBATCH --job-name=l18_eval
#SBATCH --partition=normal
#SBATCH --gres=gpu:1
#SBATCH --time=03:00:00
#SBATCH --output=/home/user/nurkyz/einstein_cnn/slurm_l18_eval_%j.out

# EVAL #18 (authorized by Nurkyz's "continue with b" ruling, 2026-07-11;
# running count 18; results reported immediately). Benchmarks are the _g3
# RE-DERIVED Euclidised sets (same real-PSF operator as training).
set -e
PY=/home/user/nurkyz/miniconda3/envs/Stronglensing/bin/python
cd /home/user/nurkyz/einstein_cnn
MEMBERS="g3_resnet_s1 g3_resnet_s2 g3_resnet_s3 g3_resnet_s4 g3_resnet_s5 g3_incnext_s1 g3_incnext_s2 g3_incnext_s3 g3_incnext_s4 g3_incnext_s5 g3_cnv2_s1 g3_cnv2_s2 g3_cnv2_s3 g3_r50_s1 g3_r50_s2 g3_r50_s3"
for M in $MEMBERS ; do
  for SAMPLE in euclid_slacs_images_g3 euclid_s4tm_images_g3 ; do
    $PY predict_real_lenses_paltas.py --ckpt ${M}.pt --real ${SAMPLE}.h5 \\
        --tta --outdir brian_run --out preds_l18_${M}_${SAMPLE}.csv
  done
done
$PY l18_tables.py
echo EVAL18_DONE
""")
print("wrote l18_eval.sbatch")

adapt("l17_tables.py", "l18_tables.py", [
    ('"""EVAL #17 tables — PRE-REGISTERED before any benchmark numbers exist.',
     '"""EVAL #18 tables — PRE-REGISTERED before any benchmark numbers exist.\n'
     'G3 hypothesis on the line: the REAL VIS PSF (0.20" + wings, replacing the\n'
     '0.16" Gaussian) should attack the residual small-theta_E SCATTER\n'
     '(eval #17: SLACS <0.9" fail 50%, pull already collapsed to +9.6%).'),
    ('R = json.load(open(os.path.expanduser("~/einstein_cnn/g4_recal.json")))',
     'R = json.load(open(os.path.expanduser("~/einstein_cnn/g3_recal.json")))'),
    ('REF = {"euclid_slacs_images": [\n'
     '        ("eval #14 pair", +0.062, 0.208, 0.084, +0.33, 31.0),\n'
     '        ("eval #16 resnet5", +0.063, 0.220, 0.131, +0.25, 31.0)],\n'
     '       "euclid_s4tm_images": [\n'
     '        ("eval #14 pair", +0.129, 0.250, 0.092, +0.16, 30.0),\n'
     '        ("eval #16 resnet5", +0.116, 0.245, 0.095, +0.19, 32.0)]}',
     'REF = {"euclid_slacs_images_g3": [\n'
     '        ("eval #16 resnet5", +0.063, 0.220, 0.131, +0.25, 31.0),\n'
     '        ("eval #17 cnv2_3", -0.005, 0.145, 0.047, +0.67, 11.0)],\n'
     '       "euclid_s4tm_images_g3": [\n'
     '        ("eval #16 resnet5", +0.116, 0.245, 0.095, +0.19, 32.0),\n'
     '        ("eval #17 cnv2_3", +0.050, 0.163, 0.081, +0.64, 30.0)]}'),
    ('ALL = (["g4_resnet_s%d" % i for i in (1, 2, 3, 4, 5)] +\n'
     '       ["g4_incnext_s%d" % i for i in (1, 2, 3, 4, 5)] +\n'
     '       ["g4_cnv2_s%d" % i for i in (1, 2, 3)] +\n'
     '       ["g4_r50_s%d" % i for i in (1, 2, 3)] + ["g4_logpolar_s1"])',
     'ALL = (["g3_resnet_s%d" % i for i in (1, 2, 3, 4, 5)] +\n'
     '       ["g3_incnext_s%d" % i for i in (1, 2, 3, 4, 5)] +\n'
     '       ["g3_cnv2_s%d" % i for i in (1, 2, 3)] +\n'
     '       ["g3_r50_s%d" % i for i in (1, 2, 3)])'),
    ('DERIVED = {"custom10": ALL[:10], "cnv2_3": ALL[10:13], "r50_3": ALL[13:16],\n'
     '           "all16": ALL[:16], "logpolar1": ALL[16:]}',
     'DERIVED = {"custom10": ALL[:10], "cnv2_3": ALL[10:13], "r50_3": ALL[13:16],\n'
     '           "all16": ALL[:16]}'),
    ('RNG = np.random.default_rng(20260712)', 'RNG = np.random.default_rng(20260713)'),
    ('print("EVAL #17 — %s', 'print("EVAL #18 — %s'),
    ('for sample in ("euclid_slacs_images", "euclid_s4tm_images"):',
     'for sample in ("euclid_slacs_images_g3", "euclid_s4tm_images_g3"):'),
    ('"preds_l17_%s_%s.csv"', '"preds_l18_%s_%s.csv"'),
    ('"preds_l17_ens_%s.csv"', '"preds_l18_ens_%s.csv"'),
    ('"eval #17 ens"', '"eval #18 ens"'),
])
print("ALL ADAPTED OK")
