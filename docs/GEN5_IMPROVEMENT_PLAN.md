# GEN5 Improvement Plan — closing the real-Euclid-Q1 gap

**Created 2026-08-20.** After the first GEN5 model (real Q1 deflector light, thin
partial arcs) hit **R² +0.65 / RMSE 0.253″ / NMAD 0.097″** on the 322 real Euclid
Q1 lenses (LEMON: 0.71 / 0.17 / 0.07). This plan is driven by (a) the metric
decomposition and (b) Nurkyz's manual review of all 322 lenses (`_local/reviews/
gen5_q1defl/q1_review.html` → `q1_review.csv`, 2026-08-20).

## Diagnosis — where the gap actually is

The gap is **not** a worse core; it's an **outlier tail**: RMSE 0.253 ≫ MAE 0.143 ≫
NMAD 0.097. Three concrete, physically-grounded failure modes, all confirmed by
Nurkyz's review:

1. **Systematic under-prediction at high θ_E.** Every large "pal is right"
   disagreement has ours < pal on a clear ring (2.29→0.92, 3.50→2.24, 2.46→1.42,
   1.60→0.86, 2.19→1.31…). The model regresses large θ_E toward the training
   median (~0.9″). **Root cause:** `g5_make_manifest --match_theta` matched the
   training θ_E distribution to the *observed* Q1 (median 0.87″, thin high tail),
   so the network rarely saw θ_E>1.5″. This is the exact prior-pull GEN4's
   tempered/flat prior (REB) was designed to avoid — match_theta re-introduced it.

2. **Faint arcs → the model struggles** (Nurkyz: "arc is not very visible",
   1.47→1.02). **Root cause:** the arc-visibility selection floor (arc/sky ≥ 7.6)
   *removed* faint-arc systems from training, so the model never learned to read
   low-contrast arcs — but real Q1 (discovery-selected, but PyAutoLens still
   models faint ones) contains them.

3. **Multiply-imaged "2–3–4 separate blobs" → we miss, PAL right.** **Root
   cause:** GEN5 sources are extended COSMOS galaxies → smooth arcs/rings. A
   *compact* source is lensed into **distinct point images** (doubles/quads), a
   very common real configuration entirely absent from our training.

Also: only ~3 of 322 PyAutoLens labels are catastrophically wrong (pub=0.00/0.01/
3.50); removing them lifts R² 0.65→0.69. Real, but small — the tail above is the
main lever.

## The plan (ordered by impact/cost; iteration law: pilot → eyeball → scale)

### T0 — Ensemble (LAUNCHED 2026-08-20; reuses existing gen5_train.h5)
5 members (resnet×3 seeds + inceptionnext + convnextv2), TTA, prediction-averaged
→ ensemble eval on Q1. Variance reduction trims the outlier tail and improves
calibration; this is how GEN4 got its headline. Jobs 50953–50958. Expected:
+0.02–0.05 R², lower RMSE. **No regeneration needed.**

### T1 — θ_E reweight: drop match_theta, use a flat/high-θ-tempered prior
The single biggest data fix. Regenerate the manifest WITHOUT `--match_theta`
(tempered-flat prior, GEN4 REB style) so the training θ_E distribution is wide/
flat to ~2.5″ — the network sees plenty of high-θ. The *evaluation* distribution
is unchanged; only training coverage widens. Gate: post-selection training θ_E
should be ~flat, and the high-θ under-prediction should shrink.

### T2 — Faint-arc tier (mixed selection floor)
Keep the visible-arc set BUT add a tier with a *lower* arc/sky floor (~3–4 instead
of 7.6) for ~25–30% of the training set, so the model learns low-contrast arcs.
Label stays exact (θ_E from the manifest). Gate: eyeball that the faint tier is
still a real lens (arc present), not noise.

### T3 — Compact-source multiply-imaged tier (doubles/quads)
For ~20–30% of images, use a VERY compact source (LF_SRC_MAX_RE_ARCSEC ≈ 0.08–0.12,
approaching point-like) so it lenses into distinct 2/4-image "blob" configs rather
than a smooth arc. Vary source position across the caustics to span double↔quad.
Nurkyz offered to help pick real Q1 blob-lenses as exemplars to match the config/
θ_E distribution. Gate: eyeball a pilot montage vs the real blob-lenses.

### T4 — Retrain + re-eval
Regenerate a v2 100k set combining T1+T2+T3 (deflector-disjoint splits kept),
retrain the ensemble, re-eval on Q1 + the reliable-label SLACS/S4TM benchmarks.
Report clean-label Q1 (drop the ~3 impossible pub) transparently.

## Execution status
- T0 ensemble: **running** (50953–50958).
- T1–T3: piloting on a few hundred images first (this session), eyeball gallery
  for Nurkyz before any full v2 regen.
- Reliable-label context (no independent Q1 θ_E exists; PyAutoLens is the
  reference; spec-z paper withdrawn) is in the eval memory + MASTER_PLAN.

## Guardrails
- Change ONE lever per pilot; always serve a real-vs-sim gallery.
- Freeze the deflector (real Q1 light) — it's approved; do not touch it.
- Keep train/val deflector-disjoint; track q1_deflector_evalidx for a clean
  held-out-eval variant.
