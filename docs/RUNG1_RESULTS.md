# Rung 1 — Results & Retrospective (as of 2026-09-18)

Companion to [`RUNG1_PLAN.md`](RUNG1_PLAN.md) (the plan) and
[`RUNG1_RESIDUAL_APPROACH.md`](RUNG1_RESIDUAL_APPROACH.md) (the Tier-2 scope).
This records what we actually ran, the numbers, and an honest post-mortem.

## The task
Roman Data Challenge **Rung 1**: a **binary classifier** that decides, per lens
image, whether a **Cold-Dark-Matter subhalo population is present** (label 1) or
absent (0). The organizers provide a **labeled training set** (107,507 systems)
and an **unlabeled test set** (95,603 systems); we train on the former and submit
per-system predictions on the latter. Data is native-Roman, real COSMOS-Web
sources, 3 bands (F106/F129/F158), 91×91 px @ 0.11″, romanisim noise. There is
**no data generation on our side** — this is a supervised ML task on provided
data. (Contrast Rung 0, which was θ_E *regression*.)

## What we built (all committed, branch `claude/roman-data-challenge-rung1-41103f`)
- `training/inspect_rung1_h5.py` — confirms the per-lens group layout
  (`images/strong_lens_<uid>/exposure_<uid>_<band>`; label = `substructure`
  attr; id = `uid`).
- `training/train_cnn_rung1.py` — lazy group-reading dataset, BCE-with-logits
  (`pos_weight`), stratified split, ROC-AUC model selection; reuses the
  resnet50/convnextv2 timm backbones + TTA from `train_cnn_paltas.py`.
  `--input_mode {raw,residual,stack}` adds the Tier-1 residual channels.
- `training/predict_rung1.py` — 8-view TTA + multi-seed ensemble → `ID,prob` CSV.
- `pipeline/rung1_{inspect,train,predict}.sbatch` + `rung1_ensemble.sh` — SLURM
  wrappers; runs on the `gpus` cluster (partition `normal`, `Stronglensing` env).

## Experiments and results (val AUC on our held-out 15% split)
| Run | Config | Val AUC |
|---|---|---|
| baseline seeds 0/1/2 | resnet50, 30 ep, lr 1e-3 | 0.549 / 0.550 / 0.551 |
| higher LR | resnet50, 50 ep, lr 3e-3 | 0.526 (worse) |
| stronger backbone | convnextv2, 40 ep | 0.500 (chance) |
| **longer + reg** | **resnet50, 100 ep, wd 1e-3** | **0.5704 (best)** |
| Tier-1 residual | stack (raw+high-pass), 30 ep | 0.5562 |
| Tier-1 residual | stack, 100 ep | 0.5566 |
| logistic reg. on global features | (sanity) | 0.513 |
| **overfit test** | 512 imgs, no aug, 100 ep | **train BCE→0.0004, val≈chance** |

**Scale reminder:** AUC 0.5 = random, 1.0 = perfect. Our best (~0.57) is only
slightly better than a coin flip.

Current submission: `~/cosmos_acs/roman_dc/submission_rung1_ensemble.csv`
(95,603 rows, `ID,prob`, ensemble of the raw seeds + the 0.5704 model, 8-view
TTA; mean prob 0.503, well-calibrated to the 50/50 prior). Valid and complete,
but weak.

## What worked
- **The engineering.** End-to-end pipeline, correct handling of the (initially
  mis-assumed) group HDF5 layout, cluster orchestration, ensembling, TTA, and a
  clean valid submission — all solid and reproducible.
- **Diagnostics.** The overfit test + logistic-regression sanity cleanly proved
  the low score is *not* a bug.
- **Longer training** — the only lever that moved the needle (0.549 → 0.570).

## What did NOT work
- **Hyperparameters.** Higher LR made it worse; nothing tuned past ~0.57.
- **A stronger backbone.** convnextv2 sat exactly at 0.500 (learned nothing).
- **Tier-1 residual imaging.** High-pass residual channels (0.556) came in
  *below* plain raw + longer training (0.570) — fit-free residuals do not expose
  the signal. **Tier-1 is a dead end.**

## Why we (probably) fell short — honest post-mortem
The evidence (three arch/LR configs ≈0.50–0.55, logistic 0.51, and an overfit
test that memorizes training to BCE≈0 yet generalizes at chance) points to one
conclusion: **the subhalo-presence signal is genuinely, physically subtle**, not
that we have a bug. Leading reasons:
1. **Tiny perturbation.** CDM subhalos down to 10⁶ M☉ perturb the lensed arc
   only slightly; against romanisim noise, single-image presence is near the
   detection floor.
2. **The signal is swamped.** Each image is dominated by the bright deflector
   galaxy + smooth arc; the subhalo effect is a small-scale fraction of the
   dynamic range, and global-average-pooled CNN features wash it out.
3. **Real-source variance.** Real COSMOS-Web sources vary far more, image to
   image, than the subhalo perturbation does — the network fits source/noise
   idiosyncrasies (hence perfect train memorization, zero generalization).
4. **Residual channels amplified noise too.** Fit-free high-pass raised the
   noise floor along with any signal, so it didn't help.
5. **We have not yet tried the method the field actually uses** — forward-model
   residuals or simulation-based inference (Tier 2). That, not more CNN tuning,
   is the real lever.

## Where this leaves us / next
- **Valid ~0.57 submission in hand.** Confirm the official submission column +
  scored metric with the organizers before uploading (`prob` is a placeholder).
- **To do meaningfully better → Tier 2** ([`RUNG1_RESIDUAL_APPROACH.md`](RUNG1_RESIDUAL_APPROACH.md)):
  reconstruct & subtract the smooth lens+source per system so the CNN sees clean
  subhalo residuals (weeks of work), or a generative anomaly-detection variant.
  Decide with the professor, and ask what AUC Rung 1 realistically expects.
