# [Working title] Real-unit-calibrated simulations close the sim-to-real gap for CNN Einstein-radius regression, with self-diagnosed confidence

Status: SKELETON DRAFT — bullets + tables only, for Nurkyz to expand. Numbers are real
(evaluation #1/#2, logged in DECISIONS_LOG.md); prose is not written yet. Citations marked
`[confirm]` need an exact arXiv/DOI check before submission — do not cite as-is.

---

## Abstract (bullets → 150-200 words later)

- Task: CNN predicts Einstein radius θ_E from a single HST ACS/WFC F814W lensed image.
- Prior CNN sims → good in-distribution, fail on real lenses (R² < 0, prior-pull).
- Fix: paltas + real COSMOS sources + real STScI focus-diverse ePSF + real empty-cutout
  backdrops + noise calibrated to real SLACS sky-RMS → "hybrid" training images.
- Result: R² crosses negative → positive on 62 SLACS + 40 S4TM (frozen, never trained on).
- Novel add: (μ, log σ²) uncertainty head — σ correlates with real error (ρ=+0.71 SLACS);
  confidence-gated subset meets the ≲10% failure / ±5% median bar outright.
- Positions against Cao et al. 2025 [confirm arXiv:2503.08586] (same lenses, same b_SIE,
  conventional modeling ~3 min/lens): CNN matches on the confident subset at ~10⁵× speed.

---

## 1. Introduction

- Strong lensing θ_E is a standard mass-scale probe; upcoming surveys (LSST, Euclid, Roman)
  will find ~10⁵ lenses — amortized CNN inference is the only tractable option at that scale.
- Prior CNN work:
  - Hezaveh, Perreault Levasseur & Marshall 2017 (Nature) [confirm exact citation] — first
    CNN SIE-parameter regression from HST-like sims.
  - Perreault Levasseur, Hezaveh & Wechsler 2017 (ApJL) [confirm] — uncertainty estimation.
  - Gawade et al. 2025 (arXiv:2404.18897) — ground-based HSC CNN, ~10–20% fractional error.
  - [confirm] arXiv:1911.06341 — gri wide-field CNN, θ_E to ~10–15% (check if same as above
    or a separate ground-based reference; verify before citing both).
  - Cao et al. 2025 (arXiv:2503.08586) [confirm] — NOT a CNN; automated pixel-based modeling +
    nested sampling, 63 grade-A SLACS, ≲5% deviation, ~10% catastrophic failures, ~3 min/lens.
    Explicitly note in their discussion that ML priors could mitigate failures — direct hook.
- Known open problem: CNNs trained on simplified sims fail on real telescope data
  (sim-to-real gap) — this paper's central diagnosis + fix + quantification.
- Contributions (bullet list, 3–4 max):
  1. Diagnose m3-era failure as **prior-pull** (systemic regression to training mean),
     not architectural — established via signed-error sweep + weak per-feature correlations.
  2. Physically-calibrated "hybrid" simulator: paltas/lenstronomy + real COSMOS sources +
     real focus-diverse ePSF (STScI ISR 2018-08 / ISR 2023-06 [confirm both]) + real empty
     backdrops + noise matched to the real sky-RMS distribution — no hand-tuned flux.
  3. R² crosses negative → positive on the frozen real benchmark; quantify residual gap via
     the pred-vs-true regression slope (compression metric).
  4. Uncertainty head whose σ is domain-aware and predictive of real-world failure —
     confidence-gated subset meets the paper's own success bar.

---

## 2. Data

### 2.1 Real benchmark (frozen, never trained on)

- N = 62 SLACS + 40 S4TM [confirm S4TM full name/citation], HST ACS/WFC F814W.
- Ground truth: Bolton et al. 2008 SIE b_SIE [confirm exact citation: J/ApJ/682/964 VizieR].
- 1 SLACS lens (J0955+0101) dropped — bad cutout.
- Cutouts: 128×128 px @ 0.05″/px = 6.4″ FOV, MAST `_drc` drizzled products.
- **TODO**: table of sample properties (θ_E range, redshift range, mag range) — pull from
  `real_lens_labels.csv` + Bolton tables.

### 2.2 Training simulator ("hybrid")

- Base: paltas [confirm citation: Wagner-Carena et al.] on lenstronomy, PEMD+shear deflector,
  COSMOS_23.5 source catalog (real GREAT3-vetted galaxies).
- θ_E ~ U[0.45, 2.30]″ (flat; widened from an initial U[0.6, 2.2] after real S4TM lenses were
  found to reach 0.54″ — see §4.1).
- Lens light: joint empirical (magnitude, R_sersic) prior — 63 (mag, R_e) pairs measured
  directly from the real SLACS cutouts (aperture photometry, de Vaucouleurs
  aperture→total correction) + Bolton R_e, sampled with jitter via paltas `cross_object`.
- PSF: STScI focus-diverse empirical PSFs (real HST optics, not Gaussian/Moffat), 88 distinct
  kernels drawn from real archival exposures, wing-extended, random rotation per shard.
- Backdrop: noiseless paltas render + REAL empty COSMOS cutout (correlated real noise + field
  neighbors) + Gaussian top-up drawn per-image from the real SLACS sky-RMS distribution.
- **Table 1** — dataset gate summary (sim vs real, same estimator both sides):

| metric | sim | real | target |
|---|---|---|---|
| sky RMS ratio | — | — | 0.8–1.25 |
| lens peak/sky | — | — | real 16–84% band |
| θ_E range | [0.45, 2.30] | [0.54, 1.78] | benchmark inside interior |

  *(fill exact numbers from `gate_stage0_report_FINAL_v2.png` / DECISIONS_LOG 2026-07-06)*

- 100,000 train / 5,000 val images; val uses seed- AND PSF-kernel-disjoint generation.
- **Figure 1**: real vs. simulated cutouts, identical asinh stretch —
  `previews_stage2/real_vs_train100k_v2.png` (or v2 equivalent once regenerated for the paper).

### 2.3 What was explicitly NOT in the v1–v2 simulator (motivates GEN4, §2.4)

- Lens light was parametric Sérsic, not a real elliptical image (real ellipticals show disky/
  inclined morphology, dust, tidal features — e.g. real SLACS J1103+5322).
- Only one COSMOS tile harvested for empty-cutout backdrops (1,317 unique cutouts, reused
  ~76× across 100k images) — more tiles downloading, not yet incorporated.
- Mass model is SIE/PEMD only — no hydro-simulation (IllustrisTNG) mass structure yet
  (see §6, proposed extension).
- **The decisive one (eval #16 → GEN4):** θ_E was drawn INDEPENDENTLY of the deflector light,
  so the luminosity→σ_v→θ_E channel (Faber–Jackson) that a physical modeler falls back on
  when the arc is faint was absent — provably unlearnable — in training.

### 2.4 GEN4: physically self-consistent population (current training set, 2026-07-11)

Design principle (shared with HOLISMOKES sims and LEMON, unlike either in realism): light
and mass of every training deflector belong to ONE physical object.

- **Deflector library:** 139 real HST/ACS early-type stamps (49 original + 90 from the
  SLACS-lineage snapshot archives, visually pruned from 197 fetched), each with SDSS
  spectroscopic σ_v (median ≈ 210 km/s, span ≈ 120–410) and measured light shape
  (mag, R_e, q, PA per stamp).
- **Per image (manifest generator):** pick a library galaxy → its stamp IS the lens light
  at NATIVE amplitude (no magnitude draw); draw z_s → **θ_E computed** from σ_v(±σ_err
  jitter) and (z_l, z_s) via SIS — no independent θ_E prior exists anywhere;
  mass ellipticity = measured light shape ⊕ empirical misalignment (ΔPA ~ N(0, 10°),
  q_mass = q_light ⊕ 0.08); mass+light rotated together (dihedral augmentation).
- **Tempered effective prior:** draws accepted with weight (1/density)^α, α = 0.6 chosen by
  sweep as the flattest α keeping manifest ρ(mag, θ_E) ≤ −0.15. Finding worth a paragraph:
  perfect θ_E flatness and a preserved light–mass correlation are INCOMPATIBLE with a
  narrow-σ_v library (flatness exploits the z_s lever and decouples θ_E from σ_v); the
  tempered prior is the disclosed compromise. Sim FJ correlation ρ = −0.15 vs real SLACS
  −0.32 (sign preserved, amplitude diluted — stated honestly); the per-system conditional
  structure is exact by construction.
- **New gate (FJ gate):** training-set ρ(deflector mag, θ_E) must match the real SLACS
  relation in sign and within 0.25 — verified at full scale, not just pilot.
- **Scale:** 104,314 train / 6,907 val (Euclid arm); split is **deflector-disjoint**
  (119 train / 20 val stamps) AND PSF-kernel- and seed-disjoint. θ_E ∈ [0.45, 2.30],
  train occupancy 0.15/0.31/0.35/0.20 in the [0.45, 0.8, 1.2, 1.7, 2.3] bins.
- **Gates at full scale (same-estimator, sim vs real Euclidised SLACS):** sky-RMS ratio
  0.956 (target 0.8–1.25); lens peak/sky 919 vs real 16–84% band [574, 1310]; FJ gate PASS;
  radial profile overlays the real one. → Table 1 numbers now exist; Figure 1 candidate:
  `real_vs_train_G4.png`.
- Remaining limitations to state: Euclid arm still uses the Gaussian VIS PSF approximation
  (real VIS PSF = plan G3, pending); σ_v library thin above ≈ 300 km/s (high-θ_E tail
  leans on importance weights); tempered FJ amplitude diluted vs real (above); native-HST
  arm re-renderable from the SAME retained population manifests (Track N).

---

## 3. Model & training

- Architecture: scale-conditioned ResNet (4 residual stages, GAP, scale-scalar concat, MLP
  head) — kept identical to the pre-existing "m3" baseline architecture; only the data pipeline
  and label source changed (MASTER_PLAN principle: isolate the realism variable).
- Input: single-band asinh-normalized image (per-image mean/std after arcsinh compression).
- Loss: point-estimate (Huber) for v1; (μ, log σ²) Gaussian-NLL for v2 (uncertainty head).
- Optimizer: Adam, cosine LR schedule, 40 epochs, batch 64, flip/rotation augmentation
  (θ_E is invariant under all 8 dihedral transforms).
- Model selection: sim-val split ONLY (seed+kernel-disjoint from train); real benchmark
  touched only at two explicit checkpoints (§4), logged with a running count.
- Test-time augmentation (evaluation only): average μ over the 8 dihedral views; total σ =
  aleatoric variance (mean over views) + epistemic view-spread variance.

---

## 4. Results

### 4.0 CURRENT HEADLINE RESULTS (2026-07-13 — restructure §4 around these; evals #17–#21 in DECISIONS_LOG)

**Table: two-domain performance of the GEN4 self-consistent population
(frozen benchmark, Bolton 2008 b_SIE GT, pre-registered ensembles):**

| domain | sample | bias | RMSE | NMAD | R² | fail>15% |
|---|---|---|---|---|---|---|
| native HST | SLACS 62 | +0.005″ | 0.152″ | 0.048″ | +0.64 | 15% |
| native HST | S4TM 40 (r50_3) | +0.013″ | 0.088″ | 0.047″ | +0.90 | 8% |
| Euclid (real-Q1-PSF operator) | SLACS 62 | −0.010″ | 0.137″ | 0.056″ | +0.71 | 15% |
| Euclid | S4TM 40 (G3 r50_3) | +0.027″ | 0.117″ | 0.082″ | +0.81 | 22% |

vs Cao et al. 2025 (conventional modeling, same lenses/GT: ≲5% dev., ~10%
fail — we match the accuracy class at ~10⁶× the speed) and LEMON Q1
(synthetic-trained CNN, own-model GT: RMSE 0.14 / NMAD 0.11 / R² 0.53 —
we lead on NMAD/R²/bias with independent GT).

**The causal chain (the paper's spine; each step = one measured ablation):**
prior (−1.02→~0) → real-unit realism (→+0.27) → PHYSICAL SELF-CONSISTENCY
(→+0.64/+0.67, the decisive step; eval #16 proved prior alone does nothing)
→ real VIS PSF (faithful benchmark; faint-arc gains; #18/#19 2×2) → selection
dial (#20: high-θ bias vs faint-arc trade-off). Small-θ_E pull: +29% → ~0.

New methods novelties to write up: the FJ gate; the tempered prior (flatness↔
FJ incompatibility finding); the measured Q1 mosaic PSF (0.20″ + wings, not
0.16″ Gaussian); deflector-disjoint validation; the operator 2×2 diagnostic;
the selection-dial ablation; COMMITMENTS/pre-registration discipline.
Known-limitations section: σ coverage under (C11); f_SIS ~11% normalization +
7% intrinsic scatter queued (C15, with validation figure); tempered FJ ρ
diluted (−0.15 vs −0.32, improves with G1b library).

### 4.1 Sim-to-real failure diagnosis (baseline "m3", pre-paltas)

- **Table 2** — locked baseline, native-forward-operator-trained model, before this paper's fix:

| sample | N | median frac err | R² | MAE | fail>15% |
|---|---|---|---|---|---|
| SLACS | 62 | −7.9% | −1.02 | 0.274″ | 55% |
| S4TM | 40 | −5.3% | −0.53 | — | 68% |

- Diagnosis: signed error sweeps positive→negative across true θ_E, crossing zero near the
  training-mean attractor (~0.95–1.0″) — classic prior-pull, not architecture (per-feature
  Spearman |ρ| < 0.3 on both samples ⇒ systemic).

### 4.2 Evaluation #1 — hybrid v1 (θ_E U[0.6,2.2], 24 PSF kernels, point estimate)

| sample | N | median frac err | 95% CI | R² | MAE | fail>15% | 95% CI |
|---|---|---|---|---|---|---|---|
| SLACS | 62 | −1.1% | [−4.0,+2.2] | +0.23 | 0.139″ | 27% | [18,39] |
| S4TM | 40 | +5.8% | [+2.1,+16.9] | +0.33 | 0.159″ | 38% | [22,52] |

- R² crosses negative → positive on both samples (headline result vs. baseline).
- Audit found: S4TM bias driven by out-of-prior-support lenses (θ_E down to 0.54″, prior
  floor was 0.6″) — 4/5 lenses below 0.6″ failed, median error +68.5% in that bin.

### 4.3 Evaluation #2 — hybrid v2 (θ_E U[0.45,2.3], 88 PSF kernels, NLL head, 8× TTA)

| sample | N | median frac err | 95% CI | R² | MAE | fail>15% | 95% CI | slope |
|---|---|---|---|---|---|---|---|---|
| SLACS | 62 | −2.6% | [−4.5,−0.1] | +0.27 | 0.129″ | 23% | [13,34] | 0.72 |
| S4TM | 40 | −1.8% | [−7.9,+1.5] | +0.47 | 0.140″ | 38% | [22,52] | 0.71 |

- Both medians now inside the ±5% bar; slope (pred-vs-true regression, 1.0 = no compression)
  improves 0.62→0.72 (SLACS) and 0.58→0.71 (S4TM) — domain-gap compression, quantified.
- **Figure 2**: predicted vs. true θ_E scatter, m3 vs. v2 vs. Cao's band —
  `previews_stage2/real_benchmark_scatter_paltas_v2.png` (needs m3/Cao overlay added).

### 4.4 Confidence-gated performance (uncertainty head)

- Spearman(σ/μ, |frac error|): **+0.71 (SLACS)**, +0.39 (S4TM) — the NLL σ is predictive of
  real-world error, not just sim-val error.
- σ/μ is itself domain-aware: median ≈ 9–10% on real lenses vs. ≈1% regime on sim-val — the
  model's own uncertainty flags the domain shift without being told about it.
- **Table 3** — confidence-gated subsets:

| sample | subset | N | median frac err | fail>15% |
|---|---|---|---|---|
| SLACS | full | 62 | −2.6% | 23% |
| SLACS | σ/μ ≤ median | 31 | −1.6% | **6%** |
| SLACS | σ/μ ≤ q75 | 46 | −1.5% | 7% |
| S4TM | full | 40 | −1.8% | 38% |
| S4TM | σ/μ ≤ median | 20 | −0.9% | 15% |

- Confident-SLACS-half meets the full success bar (±5% median, ≲10% failure) outright and is
  competitive with Cao et al.'s ~10% failure rate at ~10⁵× the inference speed.

### 4.5 Ablations — the causal decomposition of the sim-to-real gap (DONE 2026-07-06)

**Table 6 — each variant is the full v2 recipe with exactly ONE ingredient removed; identical
training and evaluation protocol (benchmark evaluations logged as #3–#6).**

| variant | SLACS R² / fail | S4TM R² / fail | SLACS median | S4TM median |
|---|---|---|---|---|
| **v2 (full recipe)** | **+0.27 / 23%** | **+0.47 / 38%** | −2.6% | −1.8% |
| A3: skewed θ_E prior | −0.52 / 29% | −0.03 / 50% | −6.3% | −7.8% |
| A1: Gaussian PSF | −0.46 / 31% | +0.06 / 50% | −5.4% | −9.8% |
| A2: Gaussian noise (no real backdrops) | −5.10 / 58% | −14.67 / 90% | +24.1% | +99.5% |
| A4: broad (non-benchmark) ePSF pool | +0.22 / 21% | +0.42 / 38% | −1.6% | −2.2% |

- Real empty-sky backdrops are the **dominant** ingredient by an order of magnitude (A2):
  trained on uncorrelated Gaussian noise, the model reads real correlated background structure
  and field neighbors as lensed flux → catastrophic over-prediction (S4TM median +99.5%).
- Flat θ_E prior (A3) and real empirical ePSF (A1) are each individually necessary: removing
  either flips full-sample SLACS R² negative. A3 closes the prior-pull causal loop.
- A4 clears the circularity concern empirically: the benchmark-matched ePSF library adds
  nothing over a fully disjoint archival pool — no benchmark information leaks through the PSF,
  and the broad-pool recipe generalizes to lenses with no matched ePSF (future surveys).
- Removing any single core ingredient breaks the result → the recipe is a conjunction.

### 4.5b Still pending

- [ ] Per-lens comparison vs. Cao et al. (per-lens data lives only in their figures — author
      contact needed; their Appendix-A failure trio already cross-checked, see §4.6).
- [ ] S4TM-specific noise recalibration (hybrid noise targets drawn from SLACS sky-RMS only).
- [ ] Sim-to-real domain adaptation (§6.2) — unlabeled disjoint pool assembly next.
- [ ] Multi-parameter (e1/e2, centroid) re-validation on the v2/hybrid pipeline.

---

### 4.6 Positioning vs. the literature (added 2026-07-06 after the systematic review)

- **Nearest competitor — LEMON (Busillo et al. 2026, A&A 711 A31; arXiv:2503.15329)**: the only
  other sim-trained θ_E network evaluated on real lenses with numeric published GT. Their
  combined real sample (Euclidised domain, i.e. resolution-degraded): bias +0.17″, RMSE 0.63″,
  NMAD 0.23″, R² ≈ −0.03 full-sample; R² 0.91 after aggressive σ-filtering. **Ours (combined
  102 native-HST lenses, LEMON conventions): bias −0.059″, RMSE 0.210″, NMAD 0.096″, R² +0.45
  full-sample — every metric 2–3× better without filtering, on native HST, on a ~1.7× larger
  real-GT sample.** Cite Busillo for the σ-filtering idea (they did it first); our additions are
  ρ(σ/μ, |err|) = +0.71 on real GT, failure-rate CIs, and the domain-aware σ finding.
- **Uncertainty calibration-transfer gap (new result)**: σ coverage is 76%/96% (1σ/2σ) on
  sim-val but 52%/83% on real lenses — the miscalibration is a domain effect a sim-fitted
  recalibration cannot repair (it would overcorrect). This quantifies domain shift in the
  uncertainty channel and is the target metric for the DA extension (§6.2).
- **Cao et al. 2025 failure-mode cross-check**: their Appendix A names 3 catastrophic failures
  (complex lens light) and explicitly calls for ML θ_E priors as the remedy. Our model on those
  systems: J1153+4612 solved confidently (−3.6%); J1016+3859 wrong but correctly flagged
  uncertain (−28.9%, σ above gate); J0841+3824 confidently wrong (−65.3%) — a shared failure
  mode across method families, pointing at lens-light complexity as the common enemy (honest
  limitation; motivates the real-deflector-light escalation path).

## 5. Discussion (bullets only — expand into prose later)

- The R²-negative→positive crossing is the headline: m3 didn't track individual real lenses,
  hybrid does.
- Residual gap is compression (slope <1), not bias (median ≈0) — model hedges toward the prior
  mean under domain shift; consistent with, but milder than, m3's prior-pull.
- Uncertainty head does double duty: (a) calibration/error-bar deliverable for the paper,
  (b) practical deployment filter, (c) the exact ingredient (MVE) prior sim-to-sim domain
  adaptation work pairs with UDA [Ciprijanovic-style, arXiv:2411.03334] — sets up §6.
- Honest limitation: parametric Sérsic lens light is the standing residual realism gap
  (Path-B trigger criterion: if a full-realism model still shows R²<0 after all gates pass,
  escalate to real deflector-cutout injection — not yet triggered, R² is positive).

---

## 6. Proposed extensions (not yet started — sequencing matters, see DECISIONS_LOG 2026-07-06)

### 6.1 IllustrisTNG convergence maps inside paltas (Prof. Chan's proposal)

- Replace/augment SIE deflectors with deflection fields from the 22,768 TNG κ maps (same maps
  used by the LensFusion diffusion prior — narrative synergy with Phase 2).
- Adds real (non-elliptical) mass structure: twists, substructure, boxiness.
- Risks to gate first: (a) label-convention offset, SIE b_SIE vs. κ̄=1 θ_E — quantify on a TNG
  subsample before mixing label types; (b) TNG central-image artifact [Bolton 2012, Shu 2016 —
  confirm exact citations] — a NEW sim-to-real gap this would introduce, must be checked;
  (c) 22,768 fixed halos vs. unlimited parametric draws (diversity ceiling).
- Sequencing: ablation-tier, after real-data results in §4 are finalized.

### 6.2 Sim-to-real domain adaptation — EXECUTED 2026-07-07; two-round rigorous NEGATIVE result (move to Results as a "DA findings" section)

- Setup: first sim-to-REAL UDA test for lens-parameter regression validated on real GT (all
  prior work sim-to-sim: Ciprijanovic et al. [confirm arXiv:2311.17238]; Agarwal et al.
  [confirm arXiv:2411.03334]). Unlabeled target pool: 104 real ACS F814W lens-candidate
  cutouts (non-benchmark SLACS grades + S4TM candidates), TRIPLE-verified disjoint from the
  frozen benchmark (name, 5″ coordinate, pixel near-duplicate). Selection rules pre-registered
  before each round; exactly one benchmark evaluation spent (eval #7).
- **Round 1 — semantic-embedding MMD (the published recipe, α ∈ {0.5, 1.4}): fails via LABEL
  SHIFT.** MMD aligned (distance ↓~40%) yet sim-val acquired a systematic positive bias:
  flat source labels vs peaked real lens population → alignment distorts the label-carrying
  subspace. The sim-to-sim successes assume identical source/target label distributions;
  sim-to-real breaks that assumption. Detected on sim-val alone (benchmark untouched).
- **Round 2 — shallow style-statistics MMD (per-channel mean/std of early layers; label-shift-
  robust by construction): preserves sim accuracy (val MAE 0.0426″ vs 0.0420″ reference) but
  does NOT improve the benchmark**: SLACS R² +0.27→−0.02, slope 0.72→0.63, σ-coverage down;
  S4TM flat-to-slightly-worse. Interpretation: the realism-calibrated simulator ALREADY matches
  real style-level statistics (the dataset gates prove distributional overlap), so style
  alignment has nothing useful left to move; the residual gap is CONTENT-level (real deflector
  morphology — the parametric-Sérsic limitation, cf. the J0841+3824 failure shared with the
  conventional pipeline, §4.6).
- Combined claim for the paper: **realism engineering beats post-hoc adaptation in this
  regime**, with two named UDA failure modes (label shift; style saturation) as guidance for
  future DA work. Real deflector-light injection is the indicated next axis.
- Future work: multi-domain generalization (Euclid Q1 grade-A ~250, BELLS GALLERY WFC3/F606W,
  COWLS JWST) — different instrument domains, deliberately excluded from this HST-targeted
  experiment (see MASTER_PLAN D5); the Euclid arena doubles as a LEMON home-turf head-to-head.

---

## 7. Conclusion (bullets, 5 lines max — write last)

- ...

---

## References (working list — verify every entry before submission)

- Bolton et al. 2008, SLACS SIE b_SIE — VizieR J/ApJ/682/964 `[confirm exact citation]`
- Hezaveh, Perreault Levasseur & Marshall 2017, Nature 548, 555 `[confirm]`
- Perreault Levasseur, Hezaveh & Wechsler 2017, ApJL `[confirm]`
- Gawade et al. 2025, arXiv:2404.18897
- `[confirm]` arXiv:1911.06341 (gri wide-field CNN — verify not a duplicate of the above)
- Cao et al. 2025, arXiv:2503.08586 `[confirm]`
- Wagner-Carena et al., paltas `[confirm exact citation/arXiv]`
- Ciprijanovic et al., arXiv:2311.17238 (NeurIPS 2023 ML4PS)
- `[confirm]` arXiv:2411.03334 (UDA + mean-variance estimator)
- `[confirm]` arXiv:2410.16347 (domain-adaptive neural posterior estimation)
- Bolton 2012; Shu et al. 2016 — IllustrisTNG central-image artifact `[confirm exact citations]`
- Wan, Chan, Lange, Hannuksela — LensFusion `[confirm exact arXiv/journal citation]`
- Tessore & Metcalf 2015 (EPL) `[confirm]` — only needed if e1/e2 section is included
- arXiv:1910.10157 (blind-study ellipticity bias) `[confirm]` — same
