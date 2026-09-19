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

## Medium — only if Phase 1 shows a real lift
- Self-supervised **masked-autoencoder pretraining** on the ~95k unlabeled lenses,
  then fine-tune (MAE gave ~+1 AUC pt in the literature).
- Arc-aligned canonicalization (rotate each arc to a common frame).

## Hard / professor-gated (weeks; may exceed Rung-1 scope)
- **Tier 2 forward-model residuals** ([`RUNG1_RESIDUAL_APPROACH.md`](RUNG1_RESIDUAL_APPROACH.md)):
  per-system reconstruct + subtract smooth lens+source (lenstronomy). Now known to
  require full source reconstruction — the challenge withholds the source model.
- **Simulation-based inference** on the substructure *population* parameters
  (Brehmer et al.) — reframes the task away from per-image binary.

## Honest expectation & recommendation
Given constraints 1–5, even the arc-focused model likely lands ~0.55–0.62. So:
1. Run **Phase 1a** (arc-annulus mask) — the single best-justified cheap try.
2. Regardless of outcome, the highest-value deliverable is the **write-up**: we
   proved the pipeline is correct, that the parameters are uninformative, that the
   label can't be enriched, and that the physics caps detectability — then **ask
   the professor what AUC Rung 1 actually targets** before any Tier-2 investment.
