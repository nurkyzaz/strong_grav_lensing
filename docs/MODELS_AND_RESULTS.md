# MODELS AND RESULTS — consolidated 2026-07-13

Authoritative per-eval record: DECISIONS_LOG.md (running count; every entry
dated). This file is the SUMMARY VIEW of where the numbers stand. Pre-GEN4
content (m3/simct/hybrid-v1..v3/Path-B eras) lives in git history of this file
and in DECISIONS_LOG.

## The frozen benchmark (never trained on; eval count at 25)

62 SLACS + 40 S4TM real HST/ACS F814W cutouts; ground truth = Bolton et al.
2008 spectroscopic-lensing b_SIE. Euclid-domain testing = the SAME cutouts
through the euclidise operator (real Q1 VIS PSF since G3). All model selection
on sim-val only; recal frozen before benchmark contact; TTA ×8; bootstrap CIs.

## Headline results (as of eval #23)

Nurkyz ruling 2026-07-13: NO single "main benchmark" frozen — the model is
multi-domain by design; paper tables report all domains and the headline is
chosen at final drafting. Provisional recipe: per-domain picks below + the
eval-#23 two-model ensemble as the combined cross-domain row.

| domain | config | bias | RMSE | NMAD | R² | fail>15% |
|---|---|---|---|---|---|---|
| **Native HST, SLACS** | eval #21, g4n cnv2_3 | +0.005″ | 0.152″ | 0.048″ | **+0.64** | **15%** |
| **Native HST, S4TM** | eval #21, g4n r50_3 (derived) | +0.013″ | **0.088″** | 0.047″ | **+0.90** | **8%** |
| **Euclid (real-PSF bench), SLACS** | eval #19, G4 cnv2_3 | −0.010″ | **0.137″** | 0.056″ | **+0.71** | 15% |
| **Euclid, S4TM** | eval #22, g4ar r50_3 (derived) | +0.020″ | **0.103″** | 0.071″ | **+0.86** | 22% |
| Euclid, SLACS — combined ens2 | eval #23 (derived): mean(G4 cnv2_3, g4ar r50_3) | −0.032″ | 0.156″ | 0.077″ | +0.62 | 16% |
| Euclid, S4TM — combined ens2 | eval #23 (derived), same config | +0.041″ | 0.136″ | 0.093″ | +0.75 | 22% |

Eval-#23 honest reading: the two-model ensemble is a COMPROMISE row — it does
not beat #19 on SLACS nor r50_3 on S4TM, and as a single cross-domain config
it ties the all-g4ar cnv2_3 ensemble (#22: +0.62/+0.76). Per-domain picks
dominate; ens2 exists for single-config cross-domain reporting.

**Native real Q1 (⛔ eval #25, N=322, zoom convention — the OFFICIAL Q2e
number; #24's "decisive miss" headline RETRACTED as a preprocessing
artifact per the pre-registered rule):** primary cnv2_3 −0.075/0.282/
0.088/R² +0.57/fail 29% (in-support +0.61). LEMON Fig 12a bar
(0.01/0.17/0.07/+0.71) still unmet — honest frame: ZERO-SHOT
cross-population transfer at R² +0.57 vs their in-domain-trained 0.71 on
their-referee, success-filtered board. Residual population effect real but
modest (slope −5%→−11% with θ_E; deflector-contrast gap). DA (C22) and
z-migration (C21) target exactly this residual. σ overconfident on real
Q1 (cov 32/56) — C11/C23.

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
| g4ar_* | train_g4ar (g3b + arc-Poisson + coupled shear) | evaluated #22: NULL on the SLACS-Euclid aggregate (−0.028/0.157/+0.62/15%) but conf-half fail 0% (first ever) and **new S4TM-Euclid best (r50_3 0.103/+0.86/22%)** |
| logpolar | — | retired after two nulls |

## Known open items

σ coverage under (RAW ~50–57/70–89) — domain miscalibration, conformal-on-real
open (C11). σ_v→θ_E corrections (C15a/b) now IMPLEMENTED in g2_make_manifest
(pilot-gated, next data build); C15c validated them on the benchmark
(raw σ_fiber −8.5% → corrected +1.8%, N=57 — paper_figures/c15c_validation.png).
Q2/Q2e complete: normalization frozen ×11.4, texture convention fixed at
⛔ #25 (the official Q1 number above; #24 headline retracted). Remaining
levers on real Q1: DA (C22) and z-migration (C21). Full ledger: COMMITMENTS.md.
