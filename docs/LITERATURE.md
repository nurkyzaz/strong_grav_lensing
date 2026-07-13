# LITERATURE (rewritten 2026-07-06 from Nurkyz's systematic review table; source: Downloads/table.csv)

## The competitive map in one paragraph

Nineteen relevant works. Only ONE other sim-trained θ_E network has ever been scored on real
lenses against published numeric ground truth: **LEMON/Busillo 2026** — and it operates on
*Euclidised* (resolution-degraded) imagery, not native HST, and gets **negative full-sample R²**.
The three domain-adaptation works (Ćiprijanović 2023; Agarwal 2025; DA-NPE 2024) are all
**sim-to-sim** and explicitly defer real data. Nobody isolates *which* realism ingredient closes
the sim-to-real gap (no ablations of PSF/backdrop/prior realism anywhere). The conventional
comparator (Cao 2025) has public per-lens data. These four facts define our differentiators.

## Tier 1 — must engage in detail

- **Busillo et al. 2026, LEMON (A&A 711 A31; arXiv:2503.15329) — NEAREST COMPETITOR.**
  **[RETRACTION 2026-07-09: the numbers previously recorded here (bias +0.17″, RMSE 0.63″,
  NMAD 0.23″, "R²≈−0.03 full sample", "R² 0.91 after σ-filtering") are WRONG — verified
  against the paper's full text (Table 3). The −0.03 appears to be their BIAS in arcsec,
  transposed into the R² cell of the review table. Corrected values below. The old
  "every metric 2–3× better" claim is DEAD — do not repeat it.]**
  Verified (their Table 3, θ_E on 60 EUCLIDISED real HST lenses = 29 SLACS + 13 EELs +
  5 COSMOS + 13 ACS, heterogeneous literature GT, HST2EUCLID degradation, NO σ-filtering):
  **bias −0.03″, RMSE 0.14″, NMAD 0.11″, R² = 0.53.** Plus 5 real Euclid ERO lenses (within
  1σ, one outlier) and Euclid Q1 discussion. BNN (dropout epistemic + aleatoric head),
  Platt-scaled σ (s=0.78–0.92). Training: 80k Euclid VIS sims, SIE+shear, sources = 1–4
  Sérsic profiles (HUDF-anchored), lens light = single Sérsic. NO realism ablations, NO
  domain adaptation, per-lens predictions NOT released (aggregate table only).
  **Honest comparison vs our v2 (eval #2): 102 native-HST lenses, uniform-survey b_SIE GT:
  bias −0.059″, RMSE 0.210″, NMAD 0.096″, R² +0.45 no filtering. Aggregates are COMPARABLE
  (they win RMSE, we win NMAD; R² not cross-comparable — different samples, GT variance and
  domains). Our defensible edges are QUALITATIVE: native HST (higher resolution, harder
  sim-to-real), uniform spectroscopic-survey GT vs their 4-catalogue mix (their own paper
  flags "differing modelling assumptions"), 1.7× real-GT sample, REAL sources + REAL
  deflector light + realism ablations (they are fully parametric, no ablations), DA on real
  GT. Direct head-to-head route: Euclidise our benchmark and compare in THEIR domain.
  [CORRECTED 2026-07-13: "HST2EUCLID is public" was WRONG — DECISIONS_LOG (authoritative,
  2026-07-09 R1.2) verified NO public-code statement (Bergamini et al., arXiv:2508.20860);
  our euclidise.py is a disclosed reimplementation. Status: already EXECUTED at
  distribution level — eval #14 ensemble on all 62 Euclidised SLACS: bias +0.062, RMSE
  0.208, NMAD 0.084 (beats their 0.11), R² +0.33 (behind their 0.53; gap isolated to the
  31% catastrophic tail, confident-half fail 10–13%). The exact shared-29 table stays
  blocked on the Busillo email: re-verified 2026-07-13 on the PUBLISHED A&A version
  (aa54538-25, July 2026) — still no lens names, no per-subsample (SLACS-only) metrics,
  and no data-availability release.]**
- **Cao et al. 2025 (MNRAS 540 3121; arXiv:2503.08586)** — conventional GPU pixel modeling
  (TinyLensGPU + nautilus), 63 SLACS, ≲5% deviation, ~10% catastrophic failures, ~3 min/lens.
  **[CORRECTED 2026-07-09: only the CODE is public (github.com/caoxiaoyue/TinyLensGpu); the
  per-lens θ_E results are NOT in the repo, the paper's data-availability line, or the
  author's other repos — verified. Per-lens comparison needs the email ask, or re-running
  their public code on the same 63 lenses ourselves.]** Our speed contrast: ~ms/lens
  amortized vs ~3 min/lens.
- **Ćiprijanović et al. 2023 (arXiv:2311.17238)**: DANN/MMD for θ_E regression, sim→sim
  (DES-noise-emulated target). **Agarwal, Ćiprijanović & Nord 2025 (arXiv:2411.03334)**:
  MVE+UDA, sim→sim, ~2× target-domain gain, calibrated aleatoric σ — closest to our
  uncertainty+DA combination but never touches real data (flagged as future work).
  **Domain-Adaptive NPE (arXiv:2410.16347)**: UDA improves posterior coverage 1–2 dex, sim→sim.
  ⇒ **Sim-to-REAL DA validated on real GT is still unclaimed. That is our peak.**

## Tier 2 — cite and position against

- **Schuldt et al. 2023, HOLISMOKES IX (arXiv:2206.11279) + X (arXiv:2207.10124)**:
  **[CORRECTED 2026-07-13: the 31 real SuGOHI lenses are in paper X, not IX — IX is
  sims-only (sim test-set θ_E median diff 0.003″ +0.21/−0.24). Verified against both
  A&A full texts.]** X applies the ResNet to 31 real HSC lenses vs their own GLEE
  traditional models and reports **NO aggregate accuracy statistics** — only
  qualitative: "good match" for θ_E ≲ 2″, systematic underprediction above (worst:
  3.1″ modeled → 1.8″ network), ellipticity compressed toward zero, shear ~0 with
  large σ. Per-lens values in their Tables B.1–B.2. Ground-based; GT = their own
  MCMC models, not spectroscopic-survey b_SIE.
- **Gawade et al. 2025 (MNRAS 540 3384; arXiv:2404.18897)**: HSC CNN (sims = lensed
  sources injected into real empty HSC cutouts — closest recipe-cousin to our hybrid).
  Real test (verified 2026-07-13, full text): **182 Grade A+B SuGOHI lenses, GT =
  their own YattaLens automated pipeline** (not spectroscopic b_SIE): θ_E accuracy
  "10–20%", bias "<5%", outlier fraction "~10%" — headline numbers only, no
  aggregate table; ellipticities show "systematic uncertainties beyond quoted errors"
  even between conventional methods. Plus 10 lenses vs literature models: θ_E
  consistent, ellipticity scatter large. Ground-based seeing-limited.
- **Wagner-Carena et al. 2023 / paltas (ApJ; arXiv:2203.00690)**: closest simulator recipe
  (real COSMOS sources, HST PSF/drizzle) but target = substructure, and uses *modeled* PSF +
  *simulated* correlated noise. Our recipe adds: empirical focus-diverse ePSF (per-exposure
  focus states), REAL empty-field backdrops, per-image sky-RMS draws from the real distribution,
  and the joint empirical lens-light prior — each of which we ablate (they don't ablate realism).
- **STRIDES NPE 2025 (Erickson et al., AJ 170; arXiv:2410.10123)**: documents sim→real breakage
  on native HST (quasar lenses, γ) — perfect motivation citation for why native-HST θ_E was
  still open. **Exact numbers (verified 2026-07-13, full text): 14 real HST lensed quasars;
  population mean γ_lens = 2.13 ± 0.06 (SNPE) vs 2.03 ± 0.04 (Schmidt et al. 2023 forward
  modeling) — consistent but offset; per-lens γ error 4.2% on "shifted" sims vs 5.0% on
  realistic "doppelganger" sims, with doppelganger posteriors MORE overconfident (their
  sim-to-real miscalibration finding); no per-lens ground truth on real data (galaxy-quasar,
  no b_SIE equivalent). Population-level only — no real-lens θ_E accuracy claim.**
- **Zhang et al. 2023 (MNRAS 527 4183)**: real SLACS + matched sims, but substructure target.

## 2026-07-13 systematic sweep (Nurkyz's 5 links + arXiv keyword sweep + Roman check)

**Bottom line: the competitive map HOLDS.** After a multi-keyword arXiv sweep (API queries:
strong lensing×NN×θ_E; SBI×strong lens; NPE×lens; Roman×strong lens; Euclid×lens modelling×
network; SLACS×NN — all sorted newest-first), the complete set of NN-parameter papers tested
on REAL lenses is still: LEMON/Busillo (Euclidised, aggregate stats), Gawade (ground-based,
GT = own pipeline), HOLISMOKES X (ground-based, NO aggregate stats), STRIDES NPE (14 quasars,
population-level γ only). **Native-HST galaxy-galaxy θ_E regression scored per-lens against
uniform spectroscopic-survey b_SIE with full-sample statistics remains UNCLAIMED except by us.**

New adjacent competitors found (both are AUTOMATION of conventional modeling, not sim-trained
regressors — they compete with Cao, not with our network):
- **LensAgent (arXiv:2604.03691, Apr 2026)**: LLM-driven agent (ReAct loop) proposing
  parameters to lenstronomy; training-free. Real data: **20 SLACS Grade A** systems,
  reduced χ² 0.994–1.150, predicted σ_v within 1σ of SDSS for all 20; 5 subhalo candidates
  (e.g. ~5.6×10⁹ M☉ near J1029−0420's θ_E). **No θ_E-vs-b_SIE accuracy numbers, no speed
  claim comparable to amortized ms/lens.** Cite in the automation paragraph next to Cao;
  monitor for a v2 with per-lens tables.
- **dolphin (arXiv:2503.22657, Shajib group)**: NN = semantic segmentation only (F1 > 86%,
  sims) to auto-configure lenstronomy forward modeling. Real data: 6 SLACS + 6 STRIDES,
  **qualitative demos only — zero quantitative real-lens validation** (verified full text).

**Roman status — the gap is OPEN (checked directly, multiple queries):**
- **Wedig et al. 2025, "The Roman View of Strong Gravitational Lenses" (arXiv:2506.03390,
  ApJ)**: yield forecast (~160k detectable lenses, ~500 substructure-quality); explicitly
  releases sim products "to support … training neural networks" — i.e. the training data
  is being laid out, but **no Roman parameter-estimation network exists yet**.
- Kirmani et al. (arXiv:2512.19886): lensed-SN DETECTION CNN aimed at Roman, sims-only.
- Everything else Roman×lensing is forecasting/substructure-survey design (2010.15173,
  2306.12864) or weak lensing. ⇒ Positioning: our recipe (real ePSF + real backdrops +
  self-consistent population) is exactly what a Roman network will need; we can claim the
  method transfers and cite Wedig as the waiting application. Risk: this gap will not stay
  open long — Wedig's sims are public.

**Nurkyz's 5 links, resolved (do not re-check):**
- arXiv:2603.06339 (dropout CNN): **CSST sims ONLY**, confirmed — 76,396 synthetic images,
  R² up to ~0.96 for SIE params, errors ≲9% at 90% CL, all on their own sims. No real test.
- arXiv:2502.09802 (Euclid ERO): lens FINDING CNN (detection), not parameter regression;
  ends at 97 visually-vetted candidates + 1 spectroscopic confirmation. Not a competitor.
- arXiv:2404.18897 (Gawade): updated in Tier 2 above with exact real-lens numbers.
- arXiv:2606.23781: Roman/Rubin **weak-lensing 3×2pt** model-approximation study — irrelevant.
- arXiv:2605.18959 (Hyrax): general ML infrastructure framework; lens-related content is
  cluster-lens candidate clustering demo — irrelevant to parameter estimation.

Also checked, sims-only (Tier 3 material): Huang et al. ViT (arXiv:2210.04143, 31,200 sim
quasar lenses, γ'/e/center, no real test); Poh et al. NPE-vs-BNN (arXiv:2501.08524, DES-like
sims, NPE calibration <10% of optimal vs BNN rarely <20%); Poh et al. 2022 SBI
(arXiv:2211.05836, sims); HOLISMOKES XVI (arXiv:2503.07733) = lens search, not modeling;
Euclid Q1 AgileLens (arXiv:2604.06648) = detection. CNN substructure on real SLACS exists
(arXiv:2403.13881, 23 lenses, GRF power spectrum) but takes main-deflector params from prior
traditional fits — not a θ_E competitor.

## Tier 3 — background/history

- Hezaveh et al. 2017 (Nature 548; arXiv:1708.08842): first CNN SIE regression (sim only).
- Perreault Levasseur et al. 2017 (ApJL 850 L7): first BNN lens uncertainties (sim-calibrated).
- Pearson et al. 2019 (MNRAS stz1750); Pearson et al. 2021 (arXiv:2103.03257): CNN-vs-conventional
  on sims; multiband gains.
- Schuldt et al. 2021, HOLISMOKES IV (A&A 646 A126): ground-based SIE baseline.
- Bom et al. 2020 (arXiv:1911.06341): DES-like gri CNN (~10–15%). [resolves the old
  "gri wide-field CNN" placeholder — this IS the 1911.06341 entry; distinct from Gawade.]
- Gentile et al. 2023, LEMON I: mostly mock; check before citing beyond lineage of Busillo 2026.
- Morningstar et al. 2018 (arXiv:1808.00011): RIM on ALMA interferometry (different modality).
- "Dropout CNN" 2026 (arXiv:2603.06339): CSST sims only.
- IllustrisTNG central-image artifact: Bolton 2012; Shu et al. 2016 [verify exact refs] — hydro
  cores ⇒ central images absent in real lenses; gating requirement for any TNG-κ variant.

## What this means for OUR paper (the four differentiators, ranked by impact)

1. **Sim-to-real domain adaptation validated on real b_SIE ground truth** — literally unclaimed
   (all three DA works are sim-to-sim). Requires a benchmark-DISJOINT unlabeled real pool.
2. **Causal realism ablations** (flat-vs-skewed θ_E prior; empirical ePSF vs Gaussian; real
   backdrops vs Gaussian noise; benchmark-matched vs broad ePSF pool) — nobody in the table
   isolates ingredients; this converts our recipe from "engineering" to "science".
3. **Native-HST positive full-sample R² on the largest real-GT benchmark (102)** — direct
   LEMON supersession, already in hand (eval #2); present in THEIR metric conventions.
4. **Per-lens matched comparison vs Cao 2025** (public data) — CNN-vs-conventional on identical
   real lenses; only sim-based versions of this exist (Pearson 2021).

## Standing cautions (from earlier notes, still valid)

- Ellipticity is the fragile parameter (lens-light leakage; HSC warnings) — keep θ_E the headline.
- Our σ under-covers on real data (52%/83% for 1σ/2σ) — recalibrate on SIM-VAL ONLY (never the
  benchmark), report raw + recalibrated; LEMON's Platt scaling is the precedent to cite.
- LensFusion failure bar |Δθ_E/θ_E| > 15%; Perreault Levasseur 2017 for uncertainty lineage.
