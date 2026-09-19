# Rung 1 — Improvement Plan (post-diagnosis)

**Where we start.** Pipeline is *proven correct* (identical code classifies
Einstein radius at **0.996 AUC**; see [`RUNG1_RESULTS.md`](RUNG1_RESULTS.md)).
Subhalo-presence tops out ~**0.57** because the signal is a subtle, arc-localized
perturbation swamped by (a) the bright central deflector galaxy and (b) heavy
noise + large source variety. So every idea below targets **the signal**, not the
machinery. Baseline to beat = **raw resnet50, 100 ep = 0.5704** on the frozen
val split.

## Guiding hypotheses (what limits us)
1. **The deflector galaxy dominates** normalization + global pooling, so the arc
   (where subhalos act) is low-contrast to the network. → *remove the deflector*.
2. **Global average pooling dilutes** a few perturbed arc pixels. → *focus on the
   arc region*.
3. **The label is intrinsically noisy** — many "yes" systems have no *massive*
   subhalo near the arc, so they look like "no". This caps achievable AUC; we
   should find *where* signal concentrates (high-SNR / large-arc systems).
4. Gaussian high-pass (Tier-1) failed because it removes *all* smooth flux and
   *amplifies noise*; it does not specifically remove the centered galaxy.

## Phase 0 — analysis (cheap, informs everything)
- **Stratify** the best model's val AUC by `snr`, `theta_e`, arc brightness. If
  AUC is materially higher in high-SNR / large-θ_E systems, that (a) confirms the
  signal is real but concentrated, and (b) motivates arc-focused inputs and
  possibly SNR-gated training. Script: extend `rung1_gallery.py` / a small
  `rung1_stratify.py`.

## Phase 1 — cheap, executable now (reuse the CNN)
- **1a. Deflector removal by radial-profile subtraction** (`--residual_type
  radial`). Subtract the azimuthally-averaged radial profile (the centered,
  ~symmetric galaxy) while preserving the azimuthally-localized arc — a fit-free,
  *targeted* deflector removal, unlike Gaussian high-pass. Test as `--input_mode
  stack --residual_type radial` (raw + radial-residual, 6ch).
- **1b. Bankable ensemble.** raw resnet50 **100 ep × 3 seeds** + TTA. Longer
  training is the only lever that has helped so far (0.549→0.570); a 100-ep
  ensemble should reach ~0.58. Low-risk, do in parallel.
- **1c. Arc-annulus crop/mask** (optional). Zero the central disk (r < ~0.5·θ_E
  in px) and/or crop to an annulus, so the network only sees arc pixels.

Success = val AUC on the frozen split, vs 0.5704. Keep only what beats it; fold
winners into the submission ensemble.

## Phase 2 — medium effort
- **Texture / power-spectrum of the deflector-subtracted arc.** The *integrated*
  effect of a subhalo population is added small-scale "roughness" in the arc.
  Compute radial/azimuthal power spectra or Haralick/texture features on the
  radial-residual arc and classify (gradient-boosting or a small MLP). This
  targets the collective signal a whole-image CNN pools away.
- **Multi-crop / arc-aligned sampling**: rotate each arc to a canonical frame
  (using the arc centroid) so the CNN sees aligned inputs.

## Phase 3 — the real lever (professor-gated, weeks)
- **Forward-model residuals** ([`RUNG1_RESIDUAL_APPROACH.md`](RUNG1_RESIDUAL_APPROACH.md)
  Tier 2a): per-system reconstruct + subtract the smooth lens+source (lenstronomy),
  classify the clean residual. Field-standard; large compute.
- **Generative anomaly residuals** (Tier 2b): train on smooth-only systems,
  residual = reconstruction error.
- Decide with the professor, informed by Phases 0–2 and by what AUC Rung 1 is
  expected to reach.

## Execution order (this session)
1. Launch Phase-1b (raw 100ep seeds 1 & 2) — bankable, runs while we iterate.
2. Implement + launch Phase-1a (radial-residual stack, 100 ep).
3. Run Phase-0 stratification.
4. Compare; if 1a/1b beat 0.5704, regenerate the submission from the best set.
5. Write the professor update; scope Phase 3 if warranted.
