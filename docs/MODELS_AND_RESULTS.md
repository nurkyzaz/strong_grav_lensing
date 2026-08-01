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
