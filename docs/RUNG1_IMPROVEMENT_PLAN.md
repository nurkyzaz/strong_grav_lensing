# Rung 1 — Improvement Plan (v2, evidence-based rewrite)

Rewritten after diagnosis. Every line below is backed by an experiment or the
literature, not a guess. Baseline to beat = **raw resnet50, 100 ep = 0.5704 AUC**
on the frozen val split. Full evidence in [`RUNG1_RESULTS.md`](RUNG1_RESULTS.md).

## Hard constraints we have PROVEN this session
1. **The data is given by the organizers; we generated nothing.** We download the
   labeled train (107,507) + unlabeled test (95,603) from Zenodo and cannot change
   either distribution. The submission is scored on *their* test set.
2. **The pipeline is correct.** Identical code/model classifies Einstein radius at
   **0.996 AUC** (`--label_attr theta_e`). Not a bug.
3. **The image is the ONLY signal.** Metadata-only (theta_e, sigma_v, mu, snr,
   z's, magnitudes) → substructure logistic regression = **0.497 AUC** (chance).
   Substructure was assigned independently of every parameter, and the population
   params (sigma_sub, log_mlow/high) are constants → **feeding parameters to the
   model cannot help classify.** (`rung1_meta_test.py`.)
4. **No richer label exists.** The only substructure info in the file is the
   *binary* flag; there is no per-system subhalo mass / count / position / arc
   convergence. So we **cannot build a continuous or cleaner target** — the label
   noise (undetectable "yes" systems) is irreducible.
5. **Physics floor.** The CDM mass function (slope −1.9, 10⁶–10¹² M☉) is dominated
   by sub-detectable halos; a direct CNN needs individual subhalos ≳5×10⁹ M☉
   (Diaz Rivero & Dvorkin 2020) and "does not improve with a low-mass population."
   With real COSMOS sources + deflector light + romanisim noise, **~0.55–0.57 is
   the expected result for realistic direct-CNN detection.**

## Dead ends — ruled out, do NOT revisit
- Metadata as model inputs (0.497). Continuous/relabeled targets (not in data).
- Hyperparameter tuning; convnextv2 (0.50). Gaussian high-pass residual channels
  (0.556 < 0.570). Exact deflector subtraction — the smooth counterfactual, source
  model, and full lens params are **not provided**, so it would require a hard
  per-system fit (Tier 2), not a lookup.

## The one cheap lever left: GUIDE the model to the arc (ring geometry)
The subhalo signal is a few perturbed **arc** pixels; global pooling averages them
away and the bright central galaxy dominates. `theta_e` *is* available and tells
us the ring radius — useless as a classifier feature, but perfect as a **guide**.
- **Phase 1a — arc-annulus mask (cheapest). TRIED → 0.5377, WORSE than 0.5704.**
  Zeroing everything outside `[0.4, 1.6]·θ_E` threw away useful context (exact
  centre, arc beyond the annulus) and added hard-edge artifacts. Dead end.
- **Phase 1b — polar transform.** Resample each image to (r, φ) about the centre so
  the ring becomes a horizontal band and arc perturbations become local features;
  the repo already has `LogPolarScale` (needs adapting 128px→91px, 1→3 band).
Success = beat 0.5704 on the identical val split + seeds. One ~40-min run each.

## Medium — TRIED, both underperformed 0.5704
- **Masked-autoencoder SSL pretraining + fine-tune → 0.5641.** Best of all the
  tweaks, still < raw+longer. Encoder learns source/galaxy morphology, not the
  noise-level subhalo cue.
- **Arc-aligned canonicalization → 0.5490.** Worse (overfit without augmentation).

## Literature cross-check (what the field does vs. what we did)
| Method | Reference | Us |
|---|---|---|
| Direct CNN on images (no subtraction) | Diaz Rivero & Dvorkin 2020 | ✅ baseline 0.57 |
| Longer training + ensemble | standard | ✅ |
| Self-supervised MAE | Masked-AE lensing 2025 | ✅ 0.564 |
| **Polar / rotation-equivariant net** | arXiv:2607.02663 (2026) | ❌ **not done (Phase 1b)** |
| Substructure **power-spectrum** regression | Wagner-Carena 2024 (arXiv:2403.13881) | ❌ needs a PS target we lack; reframes task |
| **SBI / neural posterior** on the population | arXiv:2511.17732 (2025) | ❌ Tier 2b, heavy |
| Forward-model residuals (grav. imaging) | Vegetti/Hezaveh | ❌ Tier 2a, heavy |

**Key insight:** on *realistic* data the field does **not** rely on per-image
binary CNN — it does **population-level inference** (power spectrum, SBI). Rung 1's
per-image binary framing is the hardest possible, which is exactly why direct CNNs
(ours *and* Diaz Rivero & Dvorkin's) plateau. Two levers remain:

## Remaining, in order of cost
- **Phase 1b — polar / equivariant architecture (cheap, ~1 run).** The one
  literature-backed method we have NOT tried (`LogPolarScale` in repo needs
  91px/3-band adapting). Given every preprocessing tweak failed, odds are modest,
  but it is architecturally different and worth it for completeness.
- **Tier 2 (weeks, professor-gated):** forward-model residuals (needs source
  reconstruction the challenge withholds) or SBI/power-spectrum on the population
  — the field-standard for realistic data, but reframes the task.

## Honest expectation & recommendation
Everything cheap-to-medium is done and all landed 0.54–0.57. The only untried
cheap item is **Phase 1b (polar)**; the only path with real upside is Tier 2, which
reframes to population inference and is a multi-week project. Recommendation: run
Phase 1b for completeness *or* stop here, then take the write-up + these two
literature-grounded options to the professor — the Tier-2 decision is theirs.
