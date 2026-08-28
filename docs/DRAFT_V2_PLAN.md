# Draft v2 plan — finish the paper answering the prof's comments (week of 2026-08-21)

**Goal this week:** finish v2 of the manuscript, addressing all 9 professor comments.
**Status:** experiments are DONE — this is now a WRITING task, nothing blocks it.
Source material: GEN5_PIPELINE.md, DOMAIN_SPECIALIZATION.md, PROF_COMMENTS_RESPONSE.md,
MODELS_AND_RESULTS.md; figures in _local/reviews/gen5_q1defl/.

## Headline to lead with (honest, ensemble-based)
GEN5 (real Euclid Q1 deflector light) — a CNN trained only on hybrid-real sims —
recovers θ_E on 322 real Euclid Q1 lenses at **R² ≈ 0.71 (deep ensemble; single-seed
0.68–0.73), on par with LEMON (0.71)**, unbiased, with calibrated deep-ensemble
uncertainty — while offering real-image realism + multi-instrument (HST/Euclid/Roman)
capability LEMON lacks. Do NOT headline the seed-lucky 0.729.

## Section-by-section checklist (revise the GEN4-era PAPER_DRAFT.md)

| § | Content | Prof comment | Material ready | Status |
|---|---|---|---|---|
| 1 Intro | reframe around real-Euclid result + hybrid-real realism | — | headline above | WRITE |
| 2.x GEN5 simulator | real-Q1-deflector-light pipeline (A–G) | #3 | GEN5_PIPELINE.md | WRITE |
| 2.x Mock validation | population realism (σ_v/z/mass) | #1 | mock_realism.png | WRITE (fig ready) |
| 2.x σ_v→θ_E label | validation + error budget | #2 | sigma_theta_validation.png (bias +2%, scatter 16%) | WRITE (fig ready) |
| 2.x GT quality | Bolton (SLACS) vs PyAutoLens (Q1) reliability; Cao decision | #6 | label-reliability analysis | WRITE |
| 3 Model & training | resnet + NLL + deep ensemble; arch grid | #7 | arch grid table | WRITE (data ready) |
| 4.headline | GEN5 v2 on real Q1 + matched-difficulty vs LEMON | — | v2 table, cross_matrix_v2.png | WRITE |
| 4.x Domain specialization | GEN4 vs GEN5 crossover | (context) | DOMAIN_SPECIALIZATION.md, cross_matrix.png | WRITE |
| 4.x Uncertainty | deep-ensemble calibration (ρ=0.59, recalibrate) | #5 | UQ numbers | WRITE (+opt recalib) |
| 4.x DA findings | why DA isn't the lever; specialize renderings | #4 | zero-shot Roman +0.11 | WRITE |
| 4.x Positioning | vs LEMON, Gawade 2025 (HSC simct, 10–20% scatter), Jaelani 2024, More 2016 | #3 | comparison table | WRITE |
| 5 Discussion | limitations (high-θ tail, PyAutoLens GT, deflector overlap) | #6 | caveats | WRITE |

## Comment → where it's answered (so nothing is missed)
1 mock data → §2 Mock validation (fig). 2 σ_v→θ_E → §2 label (fig). 3 simct/why-better
→ §2 simulator + §4 Positioning (table). 4 DA → §4 DA findings. 5 UQ → §4 Uncertainty.
6 GT quality → §2 GT + §5. 7 best arch → §3 (arch grid). 8 Sam/Brian → user (meeting).

## Most-effective sequence (to finish v2 this week)
1. **§4 headline + Positioning table + Domain-specialization** (the new science; highest
   reviewer impact) — figures ready.
2. **§2 simulator + Mock validation + σ_v→θ_E + GT** (answers #1,#2,#3,#6) — figures ready.
3. **§4 Uncertainty + §3 arch** (#5,#7) — data ready; optional 5-min recalibrate_sigma
   run to state nominal coverage.
4. **§4 DA findings + §1 Intro + §5 Discussion + Abstract/Conclusion** — prose.
5. **User in parallel:** LEMON same-354 email; schedule Sam/Brian (bring the brief).

## Small optional compute (not blocking writing)
- recalibrate_sigma.py on sim-val → the ×1.6 scale + nominal-coverage number for §4 UQ.
- (Later, if a reviewer asks) stellar-mass/M-L panel; same-354 eval if LEMON shares the list.

## OPEN ITEMS / don't-forget (reviewed 2026-08-21)

**RESOLVED (2026-08-28) — deflector-appearance leakage / held-out eval. NO meaningful leakage.**
GEN5 injects the REAL Q1 deflector light, flux-CALIBRATED per-lens to each lens's own
eval cutout (inject_q1_deflector.py). Since we then evaluate on those same cutouts, the
eval-set deflectors' appearance is present in training → potential leakage. Mitigating
facts: (a) θ_E labels come from the manifest (σ_v-derived), NOT the Q1 deflector's true
θ_E; (b) each deflector is reused across ~300 images with a RANGE of θ_E (θ_E-nearest
K=6 + manifest spread), so no single-value memorization; (c) our R²≈0.71 ≈ LEMON, not
wildly higher, suggesting inflation is limited.
**CHECK RUN (held-out-deflector eval):** trained on 258 deflectors (kept 113058/139252
train images), evaluated on the 64 held-out deflectors the model NEVER saw:
**held-out N=64 R² +0.541, RMSE 0.267″, NMAD 0.095″** vs **in-training control N=258
R² +0.659, RMSE 0.253″, NMAD 0.090″** (v2 on all 322: R² 0.729). **NMAD is essentially
identical (0.095 vs 0.090) → per-lens accuracy on unseen deflectors matches the control;
the model generalizes to unseen deflector appearance, headline is NOT a memorization
artifact.** The modest R² gap (0.54 vs 0.66) is largely the 64-lens subset being smaller
+ narrower-range (R² is composition-sensitive), not leakage. **For the paper:** report as
the reviewer answer — "held-out-deflector R² 0.54, NMAD 0.095″ ≈ in-training NMAD 0.090″;
deflector-light reuse does not inflate the θ_E headline." (job on cluster; NMAD is the
robust signal, quote it alongside R².)

**SLACS / LEMON off-domain framing — LOCKED (2026-08-28). Use this exact framing in
§4 Positioning + §5 Discussion; do NOT report R²=−4.26 as a claim about LEMON.**
On the 29 shared SLACS lenses, LEMON's per-lens predictions vs Bolton b_SIE give bias
**+0.29″**, R² −4.26. De-biased test: removing the +0.29″ offset explains only **37%** of
the squared error; R² stays **−2.32** with **0.376″** residual scatter (on a 0.8″ range).
→ so it is **NOT** a clean convention/units artifact (de-biasing doesn't collapse it) AND
**NOT** evidence of a scoring error — it is **off-domain degradation**: 63% is genuine
per-lens scatter, exactly what a model applied outside its training domain produces.
Their paper corroborates: predictions are SIE θ_E on Euclidised-HST (same definition +
domain as ours, so those are ruled out as causes), and their Sect. 7 states real-image
predictions are worse than on sims. Their reported Table 3 bias is −0.03″ on 60 lenses;
our +0.29″ is on the 29-SLACS subset — NO contradiction: it's subsample cancellation.
ALL three subsets with a real θ_E GT are positive (SLACS +0.29, EEL +0.08, COSMOS +0.36);
the aggregate is pulled to ≈0 only by the ACS subset scored vs ARC RADII (>θ_E → negative
apparent bias). So do NOT frame Table 3 as wrong — frame the θ_E-GT subsets as showing a
consistent small positive offset that the arc-radius subset masks in the aggregate. **PAPER RULE:** present this ONLY as domain-specialization evidence (each
method strongest in its own domain: ours degrades on native-Euclid, LEMON degrades on the
HST-anchored SLACS). NEVER a headline "we beat LEMON on SLACS," and NEVER quote R²=−4.26
as LEMON's number — R² is violently unstable on 29 lenses over a 0.8″ range. Our value on
the same 29: R² +0.57, NMAD 0.045″, bias −0.04″. Reconciliation is out to LEMON
(EMAIL_DRAFTS FOLLOW-UP #3): ask which SLACS GT + share Euclid per-lens predictions.

**Model to report:** the deep ENSEMBLE (R²≈0.71, robust + calibrated UQ) as primary —
NOT the seed-lucky single 0.729. DA (0.737) = a small documented top-up.

**Offered, awaiting Nurkyz's call (both optional, both ~1 day, bounded gain):**
- Targeted **high-θ generation** (NEW diverse θ_E>1.4 lenses, not oversampling) to
  tighten the RMSE tail. Caveat: deflector diversity + small noisy eval limit the gain.
- **354 reconstruction** (option B): identify LEMON's 354 from public grades/success-
  filter → re-score our model on exactly those (public GT) → self-sufficient same-354
  aggregate without waiting on LEMON.

**No code bugs found** (2026-08-21 review): train_cnn_paltas.py --theta_oversample edit
parses + preserves default path; gen5_per_lens_predictions.csv clean (322, no NaN).
Cosmetic only: manifest z_l pile-up at the 1.5 migration clip (histogram artifact).
