# Roman Data Challenge — Rung 1 Plan (CDM subhalo classifier)

**Task.** Rung 1 is a *binary classification* problem: for each simulated Roman
strong-lens system, decide whether a Cold-Dark-Matter **subhalo population is
present** (label 1) or **absent** (label 0). This is a different task from our
Rung 0 work, which regressed the Einstein radius θ_E (see
[`results/roman_dc/`](../results/roman_dc/)). Same instrument and image style;
new prediction head, loss, and metric.

**Data (provided — we do NOT generate it).** The organizers ship the training
and test sets on Zenodo; the giant `mejiro` YAML in the challenge page only
*documents* how they made the data (via `mejiro` + `pyhalo` CDM + `romanisim`
noise). We are a participant, so **no paltas / mejiro / romanisim runs here.**

| | DOI (→ versioned record) | Contents |
|---|---|---|
| Labeled (train) | [10.5281/zenodo.20249305](https://doi.org/10.5281/zenodo.20249305) → rec 21877582 | `roman_data_challenge_rung_1_v_3_0.h5` (11.75 GB) + `view_rung_1_dataset.ipynb` |
| Unlabeled (test) | [10.5281/zenodo.20249307](https://doi.org/10.5281/zenodo.20249307) → rec 21877583 | `roman_data_challenge_rung_1_unlabeled_v_3_0.h5` (10.29 GB) + notebook |

**Confirmed HDF5 layout** (from `view_rung_1_dataset.ipynb`, not the config) — a
per-lens GROUP hierarchy, *not* a flat cube:
```
images/
  strong_lens_<uid>/           attrs: substructure ('True'/'False'), uid, theta_e, z_lens, …
    exposure_<uid>_F106         (91, 91) float, units MJy/sr
    exposure_<uid>_F129
    exposure_<uid>_F158
```
- **label** = `group.attrs['substructure'][0]` → `'True'`/`'False'` (a *string attr*, not a 0/1 dataset)
- **id** = `group.attrs['uid'][0]` (e.g. `'00095948'`, already 8-digit)
- **bands** F106/F129/F158, **91×91** px (10.01″ FOV ÷ 0.11″/px), real COSMOS-Web sources
- labeled set has **107,507** lenses; positive class = full CDM population (`log_mlow 6→12`, `sigma_sub 0.055`), ~50/50 balanced.

**Reality check.** Subhalo *presence* is a much subtler signal than θ_E (small,
low-amplitude perturbations to arc surface brightness, not gross lens scale).
Expect ROC-AUC in roughly the **0.6–0.8** band, not Rung-0-level accuracy. The
real work is a clean, leakage-free pipeline with good augmentation.

---

## What we reuse vs. what is new

**Reused unchanged** from [`training/train_cnn_paltas.py`](../training/train_cnn_paltas.py):
the `resnet50` / `convnextv2` timm backbones (the only archs that accept
`in_chans>1`), the scale-conditioned head interface, and `augment_batch`
(dihedral flips/rotations — all label-preserving for this task).

**New files (added this branch):**

| File | Role |
|---|---|
| [`training/inspect_rung1_h5.py`](../training/inspect_rung1_h5.py) | **Step 0.** Walks `images/strong_lens_*`, prints root attrs, exposure shapes/dtypes, per-band pixel ranges, and the `substructure` class balance — a sanity check on the real file. |
| [`training/train_cnn_rung1.py`](../training/train_cnn_rung1.py) | Classifier: lazy per-lens group reader (labels/uids up front, the 3 exposures stacked on demand — no 10 GB preload), per-channel asinh normalization, BCE-with-logits (`pos_weight`), stratified split, **ROC-AUC** model selection. |
| [`training/predict_rung1.py`](../training/predict_rung1.py) | Scores the unlabeled set with 8-view TTA, ensembles across seed checkpoints, writes `ID,<prob>` keyed by `uid`. |

SLURM wrappers (in `pipeline/`, mirroring `train_ablation.sbatch`):
`rung1_inspect.sbatch` (Step 0), `rung1_train.sbatch` (Steps 1–2, env
`TRAIN_H5`/`ARCH`/`SEED`), `rung1_predict.sbatch` (Step 3, env
`TEST_H5`/`CKPTS`/`PROB_COL`).

**Deliberately NOT added:** no data generation, no domain-adaptation/"romanise"
step (Rung 0 needed it to bridge our HST/Euclid sims to Roman; Rung 1 data is
*already* native Roman), no θ_E regression/uncertainty head.

---

## Step-by-step

Everything below runs on the CUHK SLURM cluster via the wrappers in
`pipeline/rung1_*.sbatch`. Those `cd ~/einstein_cnn`, so the four scripts
(`inspect/train/predict_rung1.py` + the reused `train_cnn_paltas.py`) must be
present there, and the data downloaded to `~/cosmos_acs/roman_dc/`.

### 0. Download + inspect
Data is downloaded via the Zenodo file API (the concept DOI won't resolve in
`zenodo_get`; the versioned records 21877582 / 21877583 do). Then sanity-check
the real file:
```bash
H5=~/cosmos_acs/roman_dc/roman_data_challenge_rung_1_v_3_0.h5 \
    sbatch pipeline/rung1_inspect.sbatch
```
The layout (label = `substructure` attr, id = `uid`, bands F106/F129/F158) is
already wired into the scripts as defaults; inspect just confirms the class
balance and per-band pixel ranges (→ whether `--asinh_a 1.0` is sensible for the
MJy/sr values). **Still to confirm with the organizers:** the required
**submission column name** and the scored **metric** — the `view_*` notebooks
are dataset viewers and don't specify a submission format.

### 1. Baseline train (single seed)
```bash
TRAIN_H5=~/cosmos_acs/roman_dc/roman_data_challenge_rung_1_v_3_0.h5 \
    ARCH=resnet50 SEED=0 sbatch pipeline/rung1_train.sbatch
```
Watch `val_AUC` climb and plateau in the slurm log. If it sits at ~0.5, the
signal isn't being learned — revisit normalization (`--asinh_a`, or
`--norm minmax`). `convnextv2` is the stronger backbone to try second.

### 2. Ensemble (seeds 0/1/2)
Resubmit step 1 with `SEED=1` and `SEED=2` (and optionally `ARCH=convnextv2`).
Each writes `rung1_<arch>_s<seed>.pt` to `~/cosmos_acs/roman_dc/`. Ensembling +
TTA gave measurable gains in Rung 0 and is essentially free here.

**One-command path (Steps 1–3 together).** Once Step 0 has confirmed the keys,
`pipeline/rung1_ensemble.sh` submits the seed training jobs and a predict job
gated on `afterok` of all of them, so the submission is written only if every
run succeeds:
```bash
TRAIN_H5=~/cosmos_acs/roman_dc/roman_data_challenge_rung_1_v_3_0.h5 \
TEST_H5=~/cosmos_acs/roman_dc/roman_data_challenge_rung_1_unlabeled_v_3_0.h5 \
PROB_COL=<CONFIRM_WITH_ORGANIZERS> \
    bash pipeline/rung1_ensemble.sh
```

### 3. Predict + submit
```bash
TEST_H5=~/cosmos_acs/roman_dc/roman_data_challenge_rung_1_unlabeled_v_3_0.h5 \
CKPTS="rung1_resnet50_s0.pt rung1_resnet50_s1.pt rung1_resnet50_s2.pt" \
PROB_COL=<CONFIRM_WITH_ORGANIZERS> \
    sbatch pipeline/rung1_predict.sbatch
```
Verify the printed `frac>=0.5 ≈ 0.5` (matches the balanced prior) and that the
row count equals the test-set size, then submit
(`roman_data_challenge_submissions@stonybrook.edu` / the challenge portal).

### 4. Iterate if AUC is low
In rough priority order: (a) stronger augmentation and light regularization;
(b) `convnextv2` backbone; (c) longer schedule / LR tuning; (d) feed all three
bands vs. best single band as an ablation; (e) K-fold instead of a single 15%
val split for a lower-variance model-selection signal.

---

## Open items
- [x] layout confirmed: label = `substructure` attr, id = `uid`, images `exposure_<uid>_<band>`
- [x] image dimensions 91×91, 3 bands F106/F129/F158, units MJy/sr
- [ ] **submission column name = `?` · scored metric = `?` · probability or hard 0/1?** (ask organizers — not in the notebooks)
- [ ] confirm `--asinh_a 1.0` is sensible once `rung1_inspect` prints MJy/sr pixel ranges on the real file

## Runbook / environment
Runs on the CUHK SLURM cluster; see
[`docs/LensFusion_cluster_runbook.md`](LensFusion_cluster_runbook.md). Needs
`torch`, `h5py`, `timm`, `scikit-learn` (all in
[`requirements.txt`](../requirements.txt)). GPU strongly recommended for the
full labeled set; the scripts fall back to CPU for smoke tests
(`--limit`, `--epochs 1`).
