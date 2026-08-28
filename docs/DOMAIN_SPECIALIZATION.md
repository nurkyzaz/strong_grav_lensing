# Domain specialization: one population, instrument-specialized renderings

**Paper-ready section draft (2026-08-21).** Figure: `_local/reviews/gen5_q1defl/
cross_matrix.png`.

## Result

We train the same θ_E-regression network on two instrument-specialized renderings
of one physical lens population — **GEN4** (HST-native / Euclidised-HST, the
SLACS/S4TM domain) and **GEN5** (native Euclid, real Q1 deflector light) — and
cross-evaluate each on three real test sets through an identical prediction
pipeline (8-view TTA). θ_E ground truth is Bolton et al. spectroscopic-lensing
b_SIE for SLACS/S4TM and the Euclid pipeline PyAutoLens SIE for Q1.

| model | real Euclid Q1 (n=322) | Euclid-SLACS (n=63) | Euclid-S4TM (n=40) |
|---|---|---|---|
| **GEN4** | R² +0.51 · RMSE 0.30″ | **R² +0.56 · RMSE 0.17″** | **R² +0.60 · RMSE 0.17″** |
| **GEN5** | **R² +0.65 · RMSE 0.25″** | R² +0.26 · RMSE 0.22″ | R² +0.42 · RMSE 0.21″ |

**A clean crossover: each model is best on its own instrument domain.** On native
Euclid Q1, GEN5 beats GEN4 by **ΔR² +0.14** (0.65 vs 0.51) and RMSE 0.25″ vs 0.30″.
On the Euclidised-HST SLACS/S4TM sets the ordering reverses — GEN4 leads by
**ΔR² +0.30 / +0.18**. Neither model dominates everywhere; specialization pays.

## Interpretation

1. **The axis is instrument, not redshift.** The split tracks pixel scale, PSF,
   noise, and — decisively — *deflector appearance* (real Euclid galaxies vs
   HST galaxies degraded to Euclid). Redshift (Q1 median θ_E 0.88″ vs SLACS 1.17″)
   is a correlated consequence of what each survey selects, not the driver: a
   low-z lens observed *by Euclid* still belongs to the GEN5 (Euclid) model.

2. **Domain shift between instruments is large.** Independently corroborated by
   the failed zero-shot Roman transfer (R²+0.11 untrained vs +0.93 trained on the
   Roman rendering). One model cannot serve HST + Euclid + Roman; instrument-
   specialized renderings of a shared population are the right design — the
   professor's "one population, three renderings" made concrete.

3. **Caveats (stated for honesty).** (a) GEN4-on-Q1 (0.51) carries a flux-unit
   mismatch (GEN4 trained in Euclidised-HST units; Q1 is native-Euclid), so its
   true Euclid-domain deficit is if anything understated. (b) These are single
   models through a common pipeline for a fair crossover; the published GEN4
   SLACS-Euclid headline (ensemble + frozen recal, R²+0.71) is higher than the
   0.56 shown here — which only *widens* GEN4's home-domain lead over GEN5.

## Companion finding — the GEN5 gap is systematic, not variance

A 5-member GEN5 ensemble on Q1 gives R²+0.65 — identical to the single model
(one member, convnextv2, failed to converge and was dropped; the 4 good members
are error-correlated). Ensembling reduces variance, but the GEN5 Q1 gap is
**systematic bias**: high-θ under-prediction (match_theta prior-pull) and absent
multiply-imaged doubles/quads (extended-only sources). Hence the improvement path
is the **data** (GEN5_IMPROVEMENT_PLAN T1/T3), not the model — validated by the v2
pilot (compact sources → blob configs; flat prior → high-θ coverage).

## Update (v2): specialization holds, but GEN5 became more general

The v2 data fixes lifted GEN5 to **R² +0.73 on Q1** (best Q1 model, ahead of LEMON
0.71) AND lifted **Euclid-SLACS 0.26 → 0.60** — the high-θ coverage made GEN5 far
less brittle off-domain. So the crossover conclusion stands (GEN5 owns native
Euclid; GEN4 still owns low-θ HST S4TM at 0.60 vs v2's 0.30), but the practical
takeaway sharpens: **the biggest lever was giving GEN5 the θ_E coverage it lacked,
not the instrument split per se.** Full 3-model matrix: `cross_matrix_v2.png`.
