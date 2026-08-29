# LensCNN v3 — Scientific Review, Reviewer-Concern Audit, and Rewrite Plan

**Prepared autonomously, 2026-08-29.** This document (1) identifies everything to improve/fix/add for stronger scientific representation, (2) anticipates what an MNRAS referee will flag, (3) lists experiments/code that may be needed, and (4) gives the section-by-section plan for writing **LensCNN v3** from scratch. It is the roadmap for `paper/main.tex` (v3) and the new "LensCNN v3" Google Doc.

Companion files:
- `paper/main.tex` — the v3 paper (authoritative, MNRAS, compiles to PDF).
- `docs/CHANGELOG_v1_v2_v3.md` — what changed v1→v2 and v2→v3, and where each prof comment is addressed.
- `docs/COMMENTS_TRACKER.md` — per-comment status.

---

## 1. Executive summary of the paper's scientific claims

- **Thesis:** physical realism in training simulations (not architecture, not domain adaptation) is what closes the sim-to-real gap for CNN Einstein-radius (θ_E) regression.
- **Method:** a real-ingredient generator (real HST lens-light, real COSMOS sources, real empty-sky backdrops, empirical PSF) in physical e⁻/s units, with **observational self-consistency** — each deflector's mass (SIS via its measured σ_v) is tied to its own light.
- **Headline evidence:** on a frozen spectroscopic benchmark (62 SLACS + 40 S4TM, Bolton b_SIE GT), native-HST R²=+0.64 (SLACS) / +0.90 (S4TM); Euclid-degraded R²=+0.71; beats the m3 baseline (R²=−1.02) and matches conventional modelling (Cao 2025) at ~10⁶× inference speed.
- **Ablations:** real backdrops dominate (>10×); flat θ_E prior and empirical PSF each necessary; GEN4 self-consistency is the decisive step.
- **Uncertainty:** Gaussian-NLL head; σ correlates with true error (ρ≈0.57–0.71); confidence-gated failure 3–6%.

This is a genuinely interesting, publishable thesis. The weaknesses below are about **rigor of evidence and honest framing**, which is exactly what a referee will probe.

---

## 2. Top reviewer concerns (ranked) — these MUST be pre-empted in v3

### R1. σ_v→θ_E label accuracy — the label-noise floor (HIGH)
**Refined (per CLAUDE.md diagnosis #6):** the training pipeline builds a paltas
**SIE** mass, whose Einstein radius is directly comparable to Bolton b_SIE (no
SIS→SIE profile conversion is needed — that is a settled project point). The real
concern is therefore narrower and cleaner: each training deflector's θ_E *value*
is set from its measured **σ_v** via the SIS relation, so **how accurately does
σ_v predict the true b_SIE?** Any scatter in that relation is label noise the
scheme injects, and it caps the attainable R².
- **Fix (writing):** state this precisely (§3.4 already does); quote the empirical
  σ_v→b_SIE bias and scatter from E1.
- **Experiment (E1):** on the benchmark, compute θ_E^SIS(σ_v, z_l, z_s) and
  compare to b_SIE (no CNN). Reports the label-noise floor directly. Needs σ_v +
  (z_l, z_s) per benchmark J-name (not in repo → fetch from the SLACS catalog).

### R2. Train/benchmark leakage via the lens-light library (HIGH)
The lens-light library is drawn from "SLACS/S4TM parent samples," and the benchmark is 62 SLACS + 40 S4TM. A referee will ask: *are any benchmark galaxies' light stamps used in training?* Even light-only reuse is a leakage concern (the network could memorize deflector morphologies).
- **Fix (writing):** state explicitly that the library is **non-lens** early-types (or benchmark-disjoint), and that the split is deflector-disjoint. If the parent sample overlaps the benchmark, quantify and justify.
- **Experiment (recommended):** audit name-level overlap between the library (`tables/g1b_kinematics_v1.csv`) and the benchmark (`tables/bolton08_table5.csv` + S4TM list). Report "N benchmark galaxies in library = 0" or handle it. **CODE NEEDED:** `analysis/leakage_audit.py`.

### R3. θ_E support / ceiling (MEDIUM-HIGH)
Training θ_E ∈ [0.45, 2.30]″. Real lenses above 2.3″ are under-predicted (already disclosed for COSMOS-5). Referee: *the method cannot generalize beyond its training support; report what fraction of each real sample is out-of-support and its effect.*
- **Fix (writing):** a short "domain of validity" paragraph; report out-of-support fractions for SLACS-62, S4TM-40, Euclid Q1.

### R4. LEMON comparison is not reproducible (HIGH — credibility)
The draft admits it *cannot* reproduce LEMON's published Table 3 (R²=0.53) from LEMON's released predictions, and "an inquiry to the authors is in progress." A referee will not accept a headline comparison built on numbers you can't reconcile.
- **Fix (writing):** either (a) resolve the discrepancy before submission, or (b) frame the comparison strictly on the subsample with independent published θ_E and clearly separate "our re-scoring of LEMON's public predictions" from "LEMON's own reported numbers," with the discrepancy stated as a caveat, not buried.
- **Action:** follow up with LEMON authors; meanwhile compute both scorings transparently.

### R5. Ablation baseline mismatch (MEDIUM)
Ablations are run on the **v2 hybrid recipe (R²+0.27)**, while the headline is **GEN4 (+0.64)**. Referee: *your ablations don't decompose the headline model.* 
- **Fix:** clarify the logic (ablations isolate ingredients on the pre-self-consistency recipe; self-consistency is then an additional, larger step), OR re-run key ablations on the GEN4 recipe. Present a single coherent ladder: baseline → +real ingredients (ablated) → +self-consistency → GEN4. **CODE (optional):** re-run the two dominant ablations (Gaussian noise, flat-prior) on GEN4.

### R6. Small-sample statistics — no confidence intervals (MEDIUM-HIGH)
All headline metrics (R², NMAD, bias, fail rate) are point estimates on N=62/40. A referee will demand **bootstrap CIs**, especially before claiming "we beat LEMON on every metric."
- **Fix:** add bootstrap 68% CIs to every metric in every results table. **CODE NEEDED:** `analysis/bootstrap_metrics.py` (resample lenses, recompute R²/NMAD/bias/fail).

### R7. Uncertainty calibration, not just correlation (MEDIUM)
σ correlates with |error| (good), but calibration coverage is poor on real data (52%/83% vs nominal 68%/95%). Confidence-gating helps but discards 50% of lenses. Referee: *is the uncertainty calibrated, and is a 50%-throwaway gate practical for a 10⁵-lens survey?*
- **Fix:** add a reliability diagram / calibration curve; report a recalibration (temperature/σ-scaling) and the retained fraction vs failure-rate trade-off curve (not a single 50% point). **CODE NEEDED:** `analysis/calibration_curve.py`.

### R8. Incomplete results (BLOCKER for submission)
"to be added": Euclid Q1 GEN5 (N=322), post-DA results, Cao comparison table (§5.4), GEN5 Euclid benchmark row. These must be filled before submission.
- **Action:** run the GEN5 Euclid Q1 evaluation and the DA experiment; produce the tables.

### R9. Roman "retrain succeeds" is circular (MEDIUM)
Zero-shot Roman fails (R²=0.11); retraining on Roman sims succeeds (0.93–0.94) but GT is *simulated* (Wedig sims). Referee: *this only shows sim→sim on Roman; no real-Roman validation exists (pre-launch). Do not over-claim.*
- **Fix (writing):** frame Roman as a forward-looking demonstration of instrument-agnostic retraining, explicitly sim→sim, with real validation deferred to post-launch.

### R10. Cao comparison fairness (MEDIUM) — Prof. Chan's C6
Chan notes Cao "is not too expensive" and *provides uncertainty quantification.* The "10⁶× speed" framing over-sells. Referee: *compare like-for-like — wall-clock incl. CPU, and note Cao also yields UQ and full posteriors.*
- **Fix (writing):** soften the speed framing to "amortized inference cost"; add a fair note that conventional modelling yields uncertainties and more parameters; if possible, a CPU-time comparison. **CODE (optional):** time TinyLensGPU on CPU for a few lenses.

### R11. Single-band, θ_E-only scope (LOW-MEDIUM)
Only F814W / VIS single band; only θ_E (no ellipticity, shear, source). Referee will note the narrow scope. 
- **Fix (writing):** frame scope explicitly; position θ_E as the first, most robust step; future multi-band/multi-parameter work.

### R12. Reproducibility (LOW but easy points)
Configs, seeds, library CSVs are in-repo — make the Data Availability Statement concrete (repo, DOI, exact config files, seed lists).

---

## 3. Structural / MNRAS-compliance improvements

- **Abstract → MNRAS single unstructured paragraph** (drop A&A Context/Aims/Methods/Results/Conclusions headers). [Prof. Chan C2] Keep ≤250 words.
- **Add a Discussion section (§6)** consolidating limitations (R1, R3, R7, R9, R11) and future work — pre-empts referee. [Prof. Chan C8 lives here.]
- **Real LaTeX tables** (caption above) for all data tables + the §3.1 benchmark-properties table; Table 1 (method comparison) needs an **Uncertainty-quantification row** [C17].
- **Figures** with captions below, referenced "Fig. N": (i) predicted-vs-true θ_E (have: `paper_figures/figure2_pred_vs_true.png`); (ii) real-vs-sim example stamps (have: `figure1_real_vs_sim.png`); (iii) ablation bar chart; (iv) calibration/reliability diagram; (v) SIS-vs-SIE label-noise (from R1); (vi) confidence-gating trade-off curve.
- **Consistent notation:** θ_E, σ_v, b_SIE; British spelling; units as `km s⁻¹`, `e⁻ s⁻¹`.
- **BibTeX:** replace all `% VERIFY` entries with canonical NASA ADS exports.

---

## 4. Section-by-section plan for v3

**§1 Introduction** — keep the v2 formalism paragraph (lens equation; lens light Sérsic, lens mass SIS, source light; cite Meneghetti 2021, Saha 2024, Treu 2010). Sharpen the five contributions. State scope (single-band, θ_E). Add domain-of-validity forward-pointer. Define GEN4/GEN5.

**§2 Related work** — keep Swierc 2024 citation; keep the Bolton-vs-YattaLens justification. Add the method-comparison table WITH a UQ row (Ours ✓, Cao ✓, LEMON/Gawade/HOLISMOKES ✗/limited). Sharpen LEMON positioning + the reproducibility caveat (R4).

**§3 Data and simulator** — keep "lens-light library" rename + the mass-construction paragraph. ADD: (i) benchmark-properties table (θ_E from Bolton; z_l, z_s, mag from literature — Bolton 2008 / Auger 2009 / Shu 2017; cite); (ii) explicit leakage statement (R2); (iii) SIS-vs-SIE label-noise note (R1); (iv) source/lens redshift priors table; (v) domain-of-validity / θ_E support (R3).

**§4 CNN architecture and training** — keep technical text + the training/inference-cost paragraph. ADD a hyperparameter table; state the calibration/recalibration method (R7).

**§5 Results** — fill all "to be added" (Euclid Q1 GEN5, DA, Cao table). ADD bootstrap CIs everywhere (R6); a calibration/reliability figure and a confidence-gating trade-off curve (R7); fair Cao comparison (R10); coherent ablation ladder (R5); the predicted-vs-true figure.

**§6 Discussion (NEW)** — limitations: SIS assumption & label noise (R1), θ_E support (R3), calibration (R7), single-band scope (R11); honest statement that hard cases remain hard (Prof. Chan C8); Roman is sim→sim (R9). Future work: multi-band, multi-parameter, post-launch Roman, DA on top of realism.

**§7 Conclusions** — crisp restatement; realism > architecture > DA.

**Data Availability** — concrete repo/DOI/config/seed statement (R12).

---

## 5. Experiments / code to run (priority order)

| # | Item | Why (concern) | Data / script | Blocking? |
|---|------|---------------|---------------|-----------|
| E1 | SIS(σ_v) vs b_SIE label-noise on benchmark | R1 | bolton08 + σ_v; `sis_vs_sie_labelnoise.py` | strongly recommended |
| E2 | Library↔benchmark leakage audit | R2 | g1b_kinematics + bolton08 + S4TM | recommended |
| E3 | Bootstrap CIs on all metrics | R6 | preds_*.csv in results/; `bootstrap_metrics.py` | strongly recommended |
| E4 | Calibration curve + gating trade-off | R7 | preds_* with σ; `calibration_curve.py` | recommended |
| E5 | Complete Euclid Q1 GEN5 eval (N=322) | R8 | GEN5 pipeline | BLOCKER |
| E6 | Complete DA experiment results | R8/§5.4 | DA scripts | BLOCKER |
| E7 | Cao CPU-time comparison | R10 | TinyLensGPU | optional |
| E8 | Re-run 2 key ablations on GEN4 recipe | R5 | ablation pipeline | optional |
| E9 | Benchmark-properties table values | §3.1 | Bolton08/Auger09/Shu17 literature | recommended |
| E10 | LEMON discrepancy resolution | R4 | correspondence + rescoring | important |

The v3 text is written so that E1–E4, E9 can be slotted in as tables/figures with placeholders clearly marked `\todo{}` where a number is pending, so the paper is submission-ready the moment the runs finish.

---

## 6. Decisions made autonomously (since questions were disallowed)
- v2 (Google Doc): the substantive prof comments already addressed in-doc (C7, C9, C10, C11, C13, C15, C18, C19, C23); the remainder (C1, C2, C6, C8, C17, C22, C30) are **fully addressed in v3** and mapped in the changelog. Rationale: v3 is a from-scratch rewrite that supersedes v2, and hours of unattended browser editing is unreliable — files are not.
- v3 "new document" delivered as **both** the authoritative LaTeX (`paper/main.tex`) and a new Google Doc created via the Drive API.
- Where a number requires an unrun experiment, v3 marks it `\todo{}` rather than inventing it (no fabricated data).
- Benchmark table redshifts sourced from the literature with citations (not repo), clearly attributed.

---

## 7. Experiments actually run during the v3 build (real results)

### E3 — Bootstrap 68% CIs on the headline metrics (addresses R6) — DONE
Script: `analysis/bootstrap_metrics.py` (10 000 resamples of the lenses).

| Sample / model | R² (68% CI) | NMAD″ (CI) | RMSE″ | bias″ | fail (CI) |
|---|---|---|---|---|---|
| SLACS 62, GEN4 ensemble (`preds_l21_ens`) | **0.64** [0.45, 0.82] | 0.047 [0.041, 0.064] | 0.153 | +0.002 | 15.9% [11.1, 20.6] |
| S4TM 40, r50\_3 (`preds_l21_g4n_r50_s3`) | **0.90** [0.86, 0.93] | 0.042 | 0.119 | +0.023 | 7.5% [2.5, 12.5] |

- The SLACS ensemble reproduces the headline **exactly** (0.641 vs reported 0.64), so those numbers are solid; the CI is wide ($\pm$0.18 in R²) because N=62 — **this is why CIs are essential and must appear in every table.**
- **New finding / referee flag (important):** the S4TM headline **+0.90 is a single pre-registered member (r50\_3)**; the *full ensemble* gives only **+0.81** (`preds_l21_ens_real_s4tm`). The three r50 seeds give 0.878/0.866/0.897 — i.e. r50\_3 is the best of them. A referee will ask whether r50\_3 was genuinely pre-registered or selected post-hoc. **Action for v3:** either report the ensemble number for S4TM too (0.81), or document the pre-registration of r50\_3 airtight (seed fixed before touching the benchmark). Do **not** headline a cherry-picked member.

### Number validation (recomputed from `results/preds_*` — all consistent)
- SLACS GEN4 ensemble R²=**0.641** (paper 0.64 ✓), NMAD 0.047 (0.048 ✓), bias +0.002 (+0.005 ✓).
- S4TM r50\_3 R²=**0.897** (paper 0.90 ✓), fail 7.5% (8% ✓).
- m3 baseline: S4TM R²=**−0.526** (paper −0.53 ✓); SLACS R²=**−1.018 with N=62** (excluding the corrupted J0955+0101 cutout, as §3.1 states) = paper −1.02 ✓ (N=63 gives −1.22). **RESOLVED** — the paper is correct; all SLACS evals use N=62. Catastrophic fraction 56% ≈ paper's 55%; pred median 1.01 ≈ the training-mean attractor. GEN4 SLACS R²=0.641 is unchanged by the exclusion.
- **Flag:** the draft's S4TM *native* bias/RMSE/NMAD (+0.013/0.088/0.047) differ from the r50\_3 recompute (+0.023/0.119/0.042) though R²/fail match — likely a different canonical eval; reconcile before submission.

### E2 — Leakage audit (R2) — DONE (position cross-match)
Script: `analysis/leakage_audit.py`. Cross-matched library sky positions
(`g0_stamp_kinematics.csv` + `g1b_lens_candidates.csv`, 109 galaxies with
coords) against benchmark positions (`manifest_benchmark.csv`, 103 systems).
**Result: 0 J-name overlap; 0 library galaxies within 5″ of any benchmark lens;
nearest library-to-benchmark separation = 2798″ (~0.78°). No leakage detected.**
Caveat: covers the ~109 library galaxies that carry coordinates; the remaining
`g1b_kinematics_v1.csv` stamps use internal IDs without coords — add coordinates
to that CSV to make the audit exhaustive (expected to remain clean, since the
library is drawn from non-lens parents).

### E4 — Calibration + confidence-gating trade-off (R7) — DONE
Script: `analysis/calibration_gating.py`.
- **Calibration (raw uncertainties are overconfident):** SLACS 1σ-coverage
  **39.7%** vs nominal 68.3% (2σ: 68.3%), suggested global σ-scale **k=2.0**;
  S4TM 1σ-coverage **60.0%** (2σ: 80.0%), k=1.37. Confirms §5.4's statement and
  gives concrete recalibration factors. (Draft quoted 52%/83%; likely a
  different eval or aleatoric-only σ — reconcile, but the direction is the same.)
- **Gating trade-off (the curve to replace the single 50% point):**

  | retain most-confident | SLACS fail | S4TM fail |
  |---|---|---|
  | 25% | 0.0% | 0.0% |
  | 50% | 3.1% | 0.0% |
  | 60% | 5.3% | 0.0% |
  | 75% | 8.5% | 3.3% |
  | 90% | 10.5% | 5.6% |
  | 100% | 15.9% | 7.5% |

  SLACS 50%→3.1% reproduces the paper's "confident-half 3%". **Action:** plot
  this as the reliability/trade-off figure; apply the k-scaling before reporting
  calibrated coverage.

### E1 — SIS(σ_v)-vs-b_SIE label noise (R1) — blocked in-repo (needs external join)
No in-repo object has *both* a measured σ_v and a measured SIE θ_E: the benchmark
(`bolton08_table5.csv`) has b_SIE but no σ_v/z_s; the library
(`g0_stamp_kinematics.csv`, 84 non-lens galaxies) has σ_v/z but no measured θ_E,
and shares 0 J-names with the benchmark. **Action:** join SDSS σ_v + source
redshifts (Bolton 2008 / Auger 2009) to the 62 SLACS benchmark J-names, then
θ_E^SIS(σ_v,z_l,z_s) vs b_SIE gives the label-noise floor directly. This remains
the single highest-value experiment for R1.
