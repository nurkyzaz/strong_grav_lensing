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

| | DOI | Contents |
|---|---|---|
| Labeled (train) | [10.5281/zenodo.20249305](https://doi.org/10.5281/zenodo.20249305) | `roman_data_challenge_rung_1_v_3_0.h5` (11.8 GB) + `view_rung_1_dataset.ipynb` |
| Unlabeled (test) | [10.5281/zenodo.20249307](https://doi.org/10.5281/zenodo.20249307) | unlabeled `.h5` + example notebook |

Key facts from the config: images are **3-band** (Roman **F106 / F129 / F158**),
FOV **10.01″**, real COSMOS-Web JWST sources remapped to Roman filters, and the
positive class is a full CDM subhalo population (`log_mlow 6 → log_mhigh 12`,
`sigma_sub 0.055`). `subhalos.fraction: 0.5` ⇒ labels are **~50/50 balanced**.

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
| [`training/inspect_rung1_h5.py`](../training/inspect_rung1_h5.py) | **Step 0.** Prints the challenge HDF5 structure — image key/layout/bands, the 0/1 label column, the ID column — so we fill in the exact key names instead of guessing from the notebook. |
| [`training/train_cnn_rung1.py`](../training/train_cnn_rung1.py) | Classifier: multi-band per-channel normalization, BCE-with-logits (`pos_weight` for balance), stratified train/val split, **ROC-AUC** model selection. |
| [`training/predict_rung1.py`](../training/predict_rung1.py) | Scores the unlabeled set with 8-view TTA, ensembles across seed checkpoints, writes `ID,<prob>` submission CSV. |

**Deliberately NOT added:** no data generation, no domain-adaptation/"romanise"
step (Rung 0 needed it to bridge our HST/Euclid sims to Roman; Rung 1 data is
*already* native Roman), no θ_E regression/uncertainty head.

---

## Step-by-step

### 0. Download + inspect (resolves the two unknowns)
Download both Zenodo records to the cluster (`~/cosmos_acs/roman_dc/` alongside
the Rung 0 files). Then:
```bash
python training/inspect_rung1_h5.py <labeled>.h5
```
Note the **image key**, **label key**, and **ID key** it reports. Open
`view_rung_1_dataset.ipynb` once to confirm the required **submission column
name** and the official **metric** (AUC vs. accuracy vs. TPR@FPR). These are the
only two facts the code can't infer on its own.

### 1. Baseline train (single seed)
```bash
python training/train_cnn_rung1.py \
  --train_file <labeled>.h5 --image_key <IMG> --label_key <LAB> \
  --arch resnet50 --in_chans 3 --epochs 40 --seed 0 --out_ckpt rung1_r50_s0.pt
```
Watch `val_AUC` climb and plateau. If it sits at ~0.5, the signal isn't being
learned — revisit normalization (`--asinh_a`, or `--norm minmax`) and check the
label key is right. `convnextv2` is the stronger backbone to try second.

### 2. Ensemble (seeds 0/1/2)
Repeat step 1 with `--seed 1` / `--seed 2` (and optionally `--arch convnextv2`).
Ensembling + TTA gave measurable gains in Rung 0 and is essentially free here.

### 3. Predict + submit
```bash
python training/predict_rung1.py --test_file <unlabeled>.h5 \
  --ckpt rung1_r50_s0.pt rung1_r50_s1.pt rung1_r50_s2.pt \
  --out submission_rung1.csv --prob_col <NAME_FROM_NOTEBOOK>
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

## Open items (fill after Step 0)
- [ ] image key = `?`  · label key = `?`  · ID key = `?` (or row index)
- [ ] submission column name = `?`  · metric = `?`  · probability or hard 0/1?
- [ ] exact image dimensions H×W (config FOV 10.01″; Rung 0 was 128 px @ 6.4″)
- [ ] pixel-value units / dynamic range → confirm `--asinh_a` is sensible

## Runbook / environment
Runs on the CUHK SLURM cluster; see
[`docs/LensFusion_cluster_runbook.md`](LensFusion_cluster_runbook.md). Needs
`torch`, `h5py`, `timm`, `scikit-learn` (all in
[`requirements.txt`](../requirements.txt)). GPU strongly recommended for the
full labeled set; the scripts fall back to CPU for smoke tests
(`--limit`, `--epochs 1`).
