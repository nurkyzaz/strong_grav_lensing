# PAPER PLAN — Accurate Strong-Lensing Parameter Prediction from Single-Band HST Imaging
 
_Last updated: 2026-07-02. Status: pre-results (training set being finalized)._
 
## One-sentence thesis
 
A CNN trained on physically realistic simulations (paltas: real COSMOS sources, HST-calibrated
photometry, real ACS PSF) predicts the Einstein radius (and mass ellipticity and centroid) of
real SLACS/S4TM lenses **more accurately and with fewer catastrophic failures than published
CNN methods on the same band and lens sample**, and we explain *why* prior simulators fail via a
sim-to-real (in-distribution vs. out-of-distribution) failure analysis.
 
## Why this is publishable / novel
 
1. **A clean sim-to-real failure diagnosis.** We show the dominant real-lens failure of a
   simulator-trained θ_E CNN is **prior-pull** (regression to a training-mean attractor), that it
   is **systemic rather than image-specific** (all per-feature correlations weak), and that it is
   driven by **arc *realism*, not arc *visibility*** (lenses with obvious arcs still fail). This is
   a transferable lesson, not just a result for our model.
2. **A realism fix that is physically calibrated, not hand-tuned.** We move from a bespoke
   composite generator (hand-balanced flux ratios in arbitrary units) to `paltas`/`lenstronomy`
   with real COSMOS sources and physical magnitudes, and we quantify the closing of the gap on
   the *same* real lenses.
3. **Head-to-head accuracy vs. literature** on an identical benchmark (see below).
4. **Multi-parameter extension:** simultaneous θ_E, mass ellipticity (e1, e2), and centroid,
   with an honest account of what transfers to real data and what does not.
5. **A downstream application:** the compact-source θ_E regime as a soft constraint for the
   LensFusion diffusion sampler (Phase 2).
## Benchmark (frozen)
 
- **Sample:** 62 SLACS + 40 S4TM real lenses (J0955+0101 dropped — bad cutout). HST ACS/WFC F814W.
- **Ground truth:** Bolton 2008 SIE b_SIE (VizieR J/ApJ/682/964 for SLACS; J/ApJ/851/48 for S4TM).
- **Evaluation:** `metrics_real.py` — median fractional error, 16–84% interval, R², MAE, failure
  rate (|Δθ_E/θ_E| > 15%). Report against b_SIE directly; with paltas SIE labels there is no
  convention conversion.
## Head-to-head references
 
- **Cao et al. 2025 (arXiv:2503.08586)** — the primary comparison. Same HST F814W, ~63 grade-A
  SLACS, same b_SIE ground truth. Reports ≲5% deviation with ~10% catastrophic-failure rate.
  **Our bar: match or beat 5% / 10% on the same lenses.**
- **Gawade et al. 2025 (arXiv:2404.18897)** — HSC (ground-based) CNN; source of the θ_E²
  sample-weighting idea and the geometric detectability cut (separation > 0.5″ + second-image
  brightness). HST should beat its ~10–20% ground-based error.
## Target metrics (success criteria)
 
| Metric (on 62 SLACS + 40 S4TM) | Baseline m3 (before) | Target (after) |
|---|---|---|
| Median fractional error | SLACS −7.9%, S4TM −5.3% | within ±5% |
| 16–84% interval | wide, biased | within ≈ [−5%, +10%] |
| R² (per-lens tracking) | −1.02 / −0.53 (**negative**) | **> 0**, ideally > 0.5 |
| Failure rate (>15%) | 55% / 68% | ≲ 10% |
 
Crossing R² from negative to clearly positive is the single most important headline: it means the
model tracks individual real lenses, which m3 did not.
 
## Planned figures
 
1. Sim-to-real failure: signed fractional error vs. true θ_E (the prior-pull sweep), both samples.
2. Failure is systemic: |frac error| vs. image features with weak Spearman ρ (arc contrast, core
   SNR, compactness, neighbors) + a worst-case gallery.
3. Generation realism: side-by-side of paltas composites vs. real SLACS cutouts.
4. Before/after on the frozen benchmark: predicted vs. true θ_E, m3 vs. paltas-trained model,
   with Cao 2025's band overlaid.
5. Multi-parameter: e1/e2 recovery (with the honest caveat on lens-light information leakage).
6. (Optional) Compact-source regime advantage for LensFusion Phase 2.
## PSF-source design and ablation (added 2026-07-05)

Training PSFs are real STScI focus-diverse ACS/WFC F814W ePSFs (ACS ISR 2018-08 /
ISR 2023-06, acspsf.stsci.edu; retrieved via `acstools.focus_diverse_epsfs`, see
`epsf_retrieve.py`). Two pools are maintained deliberately:

1. **Benchmark-matched pool** (`epsf_library/benchmark/`): ePSFs for the actual
   exposures of the 62 SLACS + 40 S4TM benchmark images (focus-matched, same filter,
   same instrument state). Maximum realism for the deployment domain.
2. **Broad pool** (`epsf_library/broad/`): public archival ACS/WFC F814W exposures
   with every benchmark field excluded (2′ exclusion radius around each lens).

**Circularity concern, stated up front:** training with the benchmark exposures'
own PSFs could be criticized as information leakage from the test set. Our position:
the ePSF encodes *instrument state* (focus/optics at the observation epoch), not any
property of the lenses or their θ_E labels — no label information can leak through a
PSF model built from field stars. But the concern is answerable empirically, which
is stronger than answering it rhetorically: we train matched models on pool 1 vs
pool 2 and report both. If accuracy on the benchmark is preserved with the broad
pool, the result does not depend on having seen the benchmark's instrument state;
if it degrades, that gap measures how much PSF fidelity matters (itself a useful
result). Either outcome strengthens the paper; the ablation joins §4.4's list.

## Honest risks / open questions to resolve before claims
 
- **Parametric vs. real lens light.** paltas renders the deflector as a Sérsic, not a real
  elliptical image — the one realism gap Path A does not close. *Testable:* if residual real-lens
  failure still tracks lens-light realism, escalate to data-driven injection onto real deflectors
  (Path B; Cañameras/Rojas/Savary/DES style).
- **Noise/zeropoint calibration.** paltas detector noise and the ACS F814W zeropoint (~25.94) must
  be matched to the real SLACS cutouts' sky RMS before quantitative claims.
- **Ellipticity transfer.** Clean-model e1/e2 R²≈0.79 is the conservative publishable number;
  the higher realistic-model R² may include a lens-light↔mass correlation cue and needs a
  controlled test.
- **Author order / manuscript placement** to confirm with Brian (Nura not currently listed on the
  LensFusion manuscript author list: Wan, Chan, Lange, Hannuksela).