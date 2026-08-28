# MODELS AND RESULTS — consolidated 2026-07-13

Authoritative per-eval record: DECISIONS_LOG.md (running count; every entry
dated). This file is the SUMMARY VIEW of where the numbers stand. Pre-GEN4
content (m3/simct/hybrid-v1..v3/Path-B eras) lives in git history of this file
and in DECISIONS_LOG.

## Update 2026-08-01 (retroactive: evals #22–#25 consolidated from cluster)

Eval count is now **25** (was stale at 21 here; #22–#25 ran on the cluster
2026-07-13/14 and were logged retroactively — DECISIONS_LOG 2026-08-01).
- **#22 (g4ar, AR1+AR2, Euclid SLACS):** R²+0.62/fail 15% — flat vs #19 (+0.71);
  AR1+AR2 are refinements, not headline movers. Euclid primary stays G4 (#19).
- **#24/#25 (native REAL Euclid Q1, N=322, vs PyAutoLens GT):** best = #25 ens
  in-support **R²+0.61/fail 32%, bias −8%** — BELOW LEMON's own Q1 (R²+0.71).
  Current frontier/limitation; most of the #24→#25 gain was preprocessing.
- **Roman Data Challenge (G5a, 6-net ensemble):** challenge-VAL R²+0.93–0.94/
  fail 6–9% (optimistic; hidden-test pending). Zero-shot transfer (G5b) fails
  (R²+0.11) — training on the Roman rendering is what works.
- **LEMON head-to-head, exact 29 SLACS vs Bolton:** ours R²+0.57 (Euclid)/+0.30
  (native) vs LEMON R²−4.26 (results/lemon_vs_ours_slacs29.csv). EEL/COSMOS/ACS
  aggregate table still to compute from results/preds_lemonq1b_*.
- Full generator/photometry reference: docs/GENERATOR_AND_CODEBASE_REFERENCE.md.

## Update 2026-08-20 (GEN5 with REAL Q1 deflector light — dataset + first eval)

The GEN5 "dots" blocker was a deflector-rendering regression (synthetic FJ/
cosmetic knobs can't make a real de Vaucouleurs galaxy). Fix: render the
deflector from the **real Euclid Q1 deflector light** (each lens's own VIS Sérsic
fit, eval-unit calibrated, centered), thin partial arcs (source Re≤0.3″, offset
0.4″), strict arc-visibility floor (arc/sky≥7.6). Nurkyz signed off the look
(review artifacts under `_local/reviews/gen5_q1defl/`). Generated a **100k**
deflector-disjoint set (`/home/user/nurkyz/gen5_100k/gen5_train.h5` 103,359 /
`gen5_val.h5` 6,693) via a resumable SLURM worker pool.

**First GEN5 model** (resnet + Gaussian-NLL, sim-val R² 0.996) on the **322 real
Euclid Q1 lenses vs PyAutoLens theta_E_pub:**

| cut | N | R² | RMSE | MAE | NMAD | bias |
|---|---|---|---|---|---|---|
| as-is | 322 | +0.651 | 0.253″ | 0.143″ | 0.097″ | −1.4% |
| drop ~3 impossible PyAutoLens labels (0.00/0.01/3.50) | 319 | **+0.687** | 0.223″ | 0.132″ | 0.096″ | — |

- **Beats our own prior real-Q1 attempt** (#24/#25: R²+0.61) and closes on LEMON
  (their Fig 12a on 354 Q1 vs PyAutoLens: R²0.71 / RMSE0.17 / NMAD0.07). LEMON
  still ahead on all comparable metrics — do NOT claim we beat them.
- Gap is an **outlier tail** (RMSE≫MAE≫NMAD), not a worse core: systematic
  high-θ under-prediction (match_theta re-introduced prior-pull), faint-arc
  struggle (selection floor removed them), and missing multiply-imaged
  doubles/quads (extended sources → arcs only). See docs/GEN5_IMPROVEMENT_PLAN.md.
- **Label reliability:** no independent Q1 θ_E catalogue exists (PyAutoLens IS the
  reference; ~1% on good fits + a handful of confident failures; NISP spec-z paper
  arXiv2604.02726 is redshifts-only + withdrawn). Nurkyz reviewed all 322
  (`q1_review.csv`); eyeball confirms the ~3 catastrophic failures.
- **In flight (2026-08-20):** 5-member ensemble (jobs 50953–58) + a v2 data pilot
  (high-θ prior + compact-source multiply-image tier, job 50959).

## Update 2026-08-21 (GEN4 vs GEN5 cross-matrix; ensemble null; v2 pilot)

**Domain-specialization crossover CONFIRMED** (same predict pipeline, single
models; fig `_local/reviews/gen5_q1defl/cross_matrix.png`; write-up
docs/DOMAIN_SPECIALIZATION.md):

| model | real Euclid Q1 | Euclid-SLACS | Euclid-S4TM |
|---|---|---|---|
| GEN4 | R²+0.51 RMSE0.30 | **+0.56 0.17** | **+0.60 0.17** |
| GEN5 | **+0.65 0.25** | +0.26 0.22 | +0.42 0.21 |

Each model wins its own instrument domain: GEN5 beats GEN4 on real Euclid Q1 by
ΔR²+0.14; GEN4 beats GEN5 on SLACS/S4TM by ΔR²+0.30/+0.18. The split is by
INSTRUMENT (HST/Euclid/Roman), not redshift. Caveat: GEN4-on-Q1 has a flux-unit
mismatch (understates its deficit); GEN4-SLACS single here (0.56) < published
ensemble+recal (0.71), which widens GEN4's home lead.

- **T0 ensemble is a NULL:** 5-member GEN5 ensemble on Q1 = R²+0.65 = single
  (convnextv2 member failed to converge, dropped; 4 good members error-correlated).
  The Q1 gap is SYSTEMATIC (high-θ prior-pull + missing blob configs), not
  variance → the lever is DATA (T1/T3), not the model.
- **v2 pilot works:** compact sources (Re≤0.12″) → multiply-imaged doubles/quads +
  thin rings; dropping match_theta → high-θ coverage restored. Validates T1+T3.

## Update 2026-08-21b (GEN5 v2 full result — BEATS LEMON on R²; vs LEMON detail)

Full v2 100k regen (T1 flat/high-θ prior + T2 faint-arc tier + T3 compact-source
blob tier) → retrain (`einstein_cnn_gen5_v2.pt`, resnet+NLL). On 322 real Euclid
Q1 vs PyAutoLens theta_E_pub:

| metric | GEN5 v2 (all 322) | v2 (clean 319) | LEMON (354) | winner |
|---|---|---|---|---|
| R² | +0.729 | +0.764 | +0.71 | **us** |
| RMSE | 0.223″ | 0.194″ | 0.17″ | LEMON |
| NMAD | 0.083″ | 0.082″ | 0.07″ | LEMON |
| bias | −0.012″ | −0.015″ | +0.01″ | ~tie |

**Matched-difficulty** (filter our 322 to LEMON's ~61% retention: Grade-A / good-
fit / top-61% expert-score, N≈185–196): **R² +0.78, RMSE 0.196″, NMAD 0.076–0.079″,
bias −0.013″.** So at their difficulty we **win R², TIE NMAD, TIE bias, trail only
RMSE** — and the matched test proves the RMSE gap is a high-θ tail (Grade-A lenses
we under-predict), not a sample-quality artifact. Difficulty-matching pulled NMAD
to LEMON's level (0.076 vs 0.07) but barely moved RMSE (0.194→0.196).

- v2 also lifted Euclid-SLACS 0.26→0.60 (more general); S4TM 0.42→0.30 (flat prior
  trades low-θ). Refreshed matrix: `cross_matrix_v2.png`.
- **v3 NEGATIVE (ablation):** high-θ WeightedRandomSampler (--theta_oversample 1.5)
  REGRESSED everything — Q1 R² 0.729→0.684, high-θ bias −10.4%→−14%, overall bias
  drifted −1.5%→−2/−3.6%. Oversampling a small hard tail (with replacement)
  overfits it and shifts calibration. Lesson: v2's flat prior is the right balance;
  the residual high-θ RMSE needs BETTER high-θ DATA or a loss-based method, not a
  sampler. **v2 (`einstein_cnn_gen5_v2.pt`) stands as the final model.**

## Update 2026-08-21c (deep-ensemble UQ + arch grid; SEED-VARIANCE honesty)

Arch grid on v2 (Q1): resnet R²+0.70/RMSE0.234, inceptionnext +0.625 (NMAD 0.076),
convnextv2 +0.676 (NMAD 0.074), 3 resnet seeds 0.68–0.70. **Deep ensemble (5): R²
+0.706, RMSE 0.232, NMAD 0.085.** IMPORTANT: fresh seeds span 0.68–0.73, so v2's
single 0.729 was seed-lucky; **the robust GEN5 Q1 number is ~0.71 = ON PAR with
LEMON**, not clearly ahead. **Report the ensemble (0.706) + seed spread as the
headline** — do not lean on 0.729. Resnet = best arch (best R²/RMSE; incnext/cnv2
tighter core, worse tail). **UQ:** epistemic 0.014″ + aleatoric 0.032″ → total
0.038″; predictive σ CORRELATES with error (ρ=0.59, meaningful) but under-covers
(|z|<1 41%, |z|<2 68%) → recalibrate σ ×~1.6 (recalibrate_sigma.py) for nominal
coverage. This is the paper's UQ result (deep ensembles, prof-recommended).
- Full pipeline documented in docs/GEN5_PIPELINE.md.
- LEMON same-354 comparison: their per-lens data NOT public (Busillo emailed ~July,
  aggregate only); a same-lens test needs the 354 list (email ask, or reconstruct
  from public Walmsley/Rojas catalogues).

## Update 2026-08-21d (first WORKING sim->real DA; small but genuine)

Decomposition diagnostic (diag_decomp.py) found a real feature-level domain gap
(style MMD 22x the real-real floor, content 7.6x), reversing "DA moot." Targeted
style-MMD DA (label-shift-robust subspace; naive embed-MMD from Ciprijanovic 2023
fails via label shift), GEN5->real-Euclid, adapt to 258 unlabeled real Q1: held-out
64 R2 0.725->0.734 RMSE 0.237->0.233; full 322 R2 0.729->0.737 RMSE 0.223->0.220.
Small (+0.009 R2) but POSITIVE + GENERALIZING (held-out matches transductive) = the
first sim->real DA for lens-param regression that works. Realism did the heavy
lifting; DA a marginal top-up; residual = high-theta COVERAGE (not DA-addressable).
Model einstein_cnn_gen5_da.pt. Deeper lever: the style gap points to a SIM texture
fix as more fundamental than post-hoc DA.

## The frozen benchmark (never trained on; core result = evals #19/#21)

62 SLACS + 40 S4TM real HST/ACS F814W cutouts; ground truth = Bolton et al.
2008 spectroscopic-lensing b_SIE. Euclid-domain testing = the SAME cutouts
through the euclidise operator (real Q1 VIS PSF since G3). All model selection
on sim-val only; recal frozen before benchmark contact; TTA ×8; bootstrap CIs.

## Headline results (as of eval #21)

| domain | config | bias | RMSE | NMAD | R² | fail>15% |
|---|---|---|---|---|---|---|
| **Native HST, SLACS** | eval #21, g4n cnv2_3 | +0.005″ | 0.152″ | 0.048″ | **+0.64** | **15%** |
| **Native HST, S4TM** | eval #21, g4n r50_3 (derived) | +0.013″ | **0.088″** | 0.047″ | **+0.90** | **8%** |
| **Euclid (real-PSF bench), SLACS** | eval #19, G4 cnv2_3 | −0.010″ | **0.137″** | 0.056″ | **+0.71** | 15% |
| **Euclid, S4TM** | eval #18, G3 r50_3 | +0.027″ | 0.117″ | 0.082″ | +0.81 | 22% |

References: Cao et al. 2025 (conventional modeling, same lenses/GT): ≲5%
median dev., ~10% fail. LEMON Q1 (CNN, synthetic training, own-model GT):
bias −0.03, RMSE 0.14, NMAD 0.11, R² 0.53. m3 baseline (native): R² −1.02,
fail 55%. July-6 v2 (native): −2.6%, R² +0.27, fail 23%.

## The causal chain (each step measured on the same benchmark)

1. Flat wide θ_E prior (kills prior-pull): R² −1.02 → ~0 (native).
2. Real-unit hybrid realism (real ePSF, real backdrops, calibrated noise,
   joint empirical lens-light prior): → R² +0.27 / fail 23% (native v2).
3. **GEN4 physical self-consistency** (real galaxy = light AND mass; measured
   σ_v → θ_E; FJ channel): Euclid R² +0.25→+0.67 (eval #17), native
   +0.27→+0.64 (eval #21); small-θ_E pull +29% → ~0. THE decisive step.
4. Real Q1 VIS PSF (G3): faithful benchmark; teaches the faint-arc regime
   (S4TM best numbers); exposed the arc-selection dial.
5. Arc-selection strictness (g3b): fixes high-θ bias (44%→22% fail in-bin)
   but trades against faint-arc performance — an ablation-grade finding
   (eval #20). One selection cannot sit at both ends; motivates AR4/mixed
   curricula.

## Model generations (checkpoints on cluster ~/einstein_cnn/)

| generation | training set | status |
|---|---|---|
| g4n_* (16) | train_g4native_100k (GEN4 native arm) | CURRENT native primary (cnv2_3 + g4n_recal.json) |
| g4_* (17) | train_g4_100k (GEN4 Euclid, gauss-PSF era; set deleted, reproducible) | CURRENT Euclid primary ON the real-PSF bench (cnv2_3 + g4_recal.json) |
| g3b_* (16) | train_g3b_100k (real PSF + SNR>0.8 selection) | kept; high-θ-bias-free alternative |
| g3_* (16) | train_g3 (real PSF, old selection; set deleted, reproducible) | kept; S4TM-Euclid best (r50_3); cnv2_s3 diverged (C12) |
| g4ar_* | train_g4ar (g3b + arc-Poisson + coupled shear) | GRID RUNNING → eval #22 |
| logpolar | — | retired after two nulls |

## Known open items

σ coverage under (RAW ~50–57/70–89) — domain miscalibration, conformal-on-real
open (C11). σ_v→θ_E normalization ~11% low at fixed light (f_SIS=0.948) +
missing 7% intrinsic scatter — fixes queued (C15). Full ledger: COMMITMENTS.md.
