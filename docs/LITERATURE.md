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
  GT. Direct head-to-head route: HST2EUCLID is public → Euclidise our 29 shared SLACS and
  compare in THEIR domain.**
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

- **Schuldt et al. 2023b, HOLISMOKES IX (arXiv:2206.11279)**: ResNet θ_E+σ on 31 real SuGOHI
  lenses, but ground-based and GT = their own MCMC models (not uniform spectroscopic-survey b_SIE).
- **Gawade et al. 2025 (MNRAS 540 3384; arXiv:2404.18897)**: HSC CNN, ~10–20% θ_E scatter on
  real ground-based lenses vs modeling-based GT. Our prior "benchmark to beat" — now superseded
  by LEMON as the sharpest comparison.
- **Wagner-Carena et al. 2023 / paltas (ApJ; arXiv:2203.00690)**: closest simulator recipe
  (real COSMOS sources, HST PSF/drizzle) but target = substructure, and uses *modeled* PSF +
  *simulated* correlated noise. Our recipe adds: empirical focus-diverse ePSF (per-exposure
  focus states), REAL empty-field backdrops, per-image sky-RMS draws from the real distribution,
  and the joint empirical lens-light prior — each of which we ablate (they don't ablate realism).
- **STRIDES NPE 2025 (AJ)**: documents sim→real breakage on native HST (quasar lenses, γ) —
  perfect motivation citation for why native-HST θ_E was still open.
- **Zhang et al. 2023 (MNRAS 527 4183)**: real SLACS + matched sims, but substructure target.

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
