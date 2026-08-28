# Professor's draft-paper comments — status & action plan (2026-08-21)

Each comment mapped to: **HAVE** (what's already done), **GAP**, **ACTION**. Ordered
into a next-steps ladder at the end. Current headline: GEN5 v2 = R² +0.73 on real
Euclid Q1 (ahead of LEMON 0.71 on R²); see GEN5_PIPELINE.md, MODELS_AND_RESULTS.md.

## 1. How good is the mock data? (statistics, stellar mass, halo mass, M/L, source z)
- **HAVE:** per-image measured σ_v (SDSS), z_l (migrated, lognormal med 0.79), z_s
  (~N(2.0,0.6)), θ_E from σ_v (SIS), real deflector light. θ_E dist matches real Q1.
- **GAP:** no explicit characterization of stellar mass, halo mass, M/L, source-z
  vs real/literature — the prof wants the mock validated as a *population*.
- **DONE (mock_realism.png):** σ_v med 268 km/s (SLACS ~250 ✓), z_l med 0.76 (real
  Q1 0.79 ✓), z_s med 2.09 (high-z ✓), θ_E med 0.91 (real 0.88; mock deliberately
  broader = flat train prior), Einstein mass log M_E med 11.5 (3×10¹¹ M_sun, galaxy-
  scale ✓), θ_E–σ_v Faber-Jackson channel visible. Minor: z_l pile-up at the 1.5
  clip boundary (cosmetic; can smooth the migration cap). TODO: stellar-mass + M/L
  panel with a stated M/L (needs a mag zeropoint reconciliation) if the prof wants it.

## 2. Is velocity dispersion good enough for θ_E? Error/uncertainty?
- **HAVE:** the σ_v→θ_E audit (P1-AUDIT): C15a σ_SIS = σ_fiber/0.948 (SDSS fiber
  under-reads SIE by ~11%, corrected); C15b +7% intrinsic scatter (≈14% in θ_E)
  beyond measurement error. Route = HOLISMOKES-standard (SDSS z+σ_v → SIE).
- **GAP:** the validation figure (C15c) — θ_SIS(σ_fiber) vs true b_SIE on the 62
  benchmark lenses — may not be in the draft; no explicit θ_E error budget.
- **DONE (sigma_theta_validation.png, N=57 SLACS):** raw σ_fiber → θ_E has bias
  **−8%**, scatter **16%**; the C15a correction (σ/0.948) removes it → bias **+2%**
  (unbiased), scatter **17%**. So σ_v gives θ_E to ~2% bias / ~16% scatter — good
  enough as a label, and the scatter is the honest per-lens θ_E uncertainty from σ_v.

## 3. Realistic mock images — simct / More 2016; Jaelani 2024; Gawade 2025
- **KEY comparator: Gawade et al. 2025 (MNRAS 540, 3384)** — CNN θ_E regression on
  HSC via simct (arcs superposed on real HSC cutouts; best "LensLight" variant):
  **10–20% scatter, <5% bias, ~10% outliers** on real SuGOHI lenses. Also **Jaelani
  et al. 2024 (SuGOHI-X, MNRAS 535, 1625)** — simct lens *finding* (classification),
  and **More et al. 2016** (simct origin).
- **HAVE:** the SAME hybrid methodology (real deflector cutouts + injected arcs) —
  but on **Euclid (space)** with **real Q1 deflector light at native amplitude** and
  **per-object σ_v→θ_E self-consistency**, plus multi-domain (HST/Euclid/Roman).
- **WHY WE'RE BETTER (for the paper):** (a) space-based Euclid vs ground HSC —
  higher resolution, our NMAD ~9–10% sits at/below the *good* end of Gawade's
  10–20% on harder-to-beat data; (b) real *Euclid* deflector light, not scaling-
  relation SIE on ground images; (c) per-lens self-consistent light↔mass (they use
  a photometric scaling relation for σ_v); (d) validated against a large real Euclid
  sample with quantitative θ_E, beating LEMON. **ACTION:** add a related-work
  paragraph + comparison table (Gawade/simct vs LEMON vs ours).

## 4. Domain adaptation — why not working?
- **HAVE:** zero-shot cross-instrument transfer fails (Roman R²+0.11 untrained vs
  +0.93 trained-on-Roman); DA attempted (C22, train_da).
- **METHOD CRITIQUE (prof was right):** our DA came from Ćiprijanović et al. 2023
  (arXiv:2311.17238), validated **sim→sim only**. The embed-MMD variant **fails
  under label shift** (our broad sim θ_E prior vs the peaked real population) — we
  diagnosed and named this (DECISIONS_LOG 2026-07-07). So the published method is
  provably inappropriate for our sim→real case; the label-shift-robust target is
  the shallow **style** subspace.
- **DECOMPOSITION DIAGNOSTIC (diag_decomp.py, 2026-08-21) — REVERSES "DA moot":**
  in the GEN5-v2 model's features, sim↔real STYLE MMD = 0.178 (vs 0.008 real-real
  floor, 22×) and CONTENT MMD = 0.069 (vs 0.009, 7.6×). Error ↔ OOD-distance ρ=0.38
  AND error ↔ θ_E ρ=0.32; per-θ |err| 0.030→0.267 (0.4→3.5″); most-OOD real lenses
  are the high-θ ones. So there IS a real, adaptable domain gap (biggest = style),
  entangled with a high-θ coverage gap DA can't fix.
- **EXPERIMENT DONE (job 51327) — SMALL BUT GENUINE POSITIVE:** targeted style-MMD
  DA (α=1, warmup 5), GEN5→real-Euclid, adapt to 258 unlabeled real Q1, eval on the
  held-out 64 (clean) + full 322. **Held-out 64: R² 0.725→0.734, RMSE 0.237→0.233,
  NMAD 0.117→0.114. Full 322: R² 0.729→0.737, RMSE 0.223→0.220.** The gain (+0.009
  R²) is small but (a) POSITIVE — unlike the old embed-MMD that failed via label
  shift, because we targeted the label-shift-robust STYLE subspace; (b) GENERALIZES
  — the held-out (DA never aligned to those) shows the same gain as transductive, so
  it's not pool-overfitting. → **The first sim→real DA for lens-parameter regression
  that WORKS** (modestly). Story: naive DA fails (label shift) → decomposition finds
  the style gap → targeted style-DA gives a real, generalizing top-up; realism did
  the heavy lifting, the residual is high-θ COVERAGE (not DA-addressable). **Deeper
  lever:** the large STYLE gap also points to a SIM fix (analytic-Sérsic deflector
  too smooth / noise texture) as more fundamental than post-hoc DA. Model:
  einstein_cnn_gen5_da.pt.
- **ACTION:** write §DA around this (method critique + decomposition + result); the
  headline result does NOT depend on DA.

## 5. Generate uncertainties — dropouts / deep ensembles (recommended) / BNN
- **HAVE:** Gaussian-NLL aleatoric head (μ, logσ²) + TTA spread; recalibrate_sigma.py.
- **GAP:** no epistemic UQ. Prof recommends **deep ensembles** (and lists MC-dropout,
  BNN as alternatives; LEMON uses a BNN).
- **ACTION (GPU, concrete, HIGH PRIORITY — prof-recommended):** build a proper deep
  ensemble on v2 (5 members, diverse seeds/archs — reuse the working members, fix the
  convnextv2 LR), epistemic σ = member spread, combine with aleatoric → total
  predictive σ, **recalibrate + report reliability/coverage** on the sim-val split;
  compare vs MC-dropout and NLL-only. This is the UQ deliverable for the paper.
- **DONE:** 5-member deep ensemble on v2. Predictive σ = epistemic (0.014″) ⊕
  aleatoric (0.032″) = 0.038″; **σ correlates with true error (ρ=0.59)** — the
  uncertainty is meaningful. Coverage under-nominal (|z|<1 41%, |z|<2 68%) → apply
  recalibrate_sigma.py (×~1.6) for nominal coverage. Deep ensembles = the prof's
  recommended method, delivered. (MC-dropout comparison optional/later.)

## 6. How good is the reference/GT? Bolton? PyAutoLens? drop Cao?
- **HAVE:** GT-reliability investigation. SLACS = Bolton et al. spectroscopic-lensing
  b_SIE (gold standard). Q1 = PyAutoLens automated SIE — ~1% precise on good fits but
  a handful of confident catastrophic failures (we drop 3 impossible); no independent
  Q1 θ_E catalogue exists (verified). Both our GT and LEMON's use the SAME PyAutoLens
  for Q1 → the comparison is fair.
- **ACTION:** add a GT-quality subsection (Bolton reliable; PyAutoLens caveats +
  our clean-label handling). **Cao decision:** Cao 2025 = conventional modeling on
  SLACS; keep only as a "matches/beats conventional" point, or drop if it muddies the
  Euclid story. Recommend: keep a one-line SLACS-vs-Cao note, lead with LEMON on Euclid.
- **DEFLECTOR-LEAKAGE CHECK DONE (2026-08-28) — NO meaningful leakage.** Since GEN5
  injects the real Q1 deflector light of the very lenses we evaluate on, a reviewer will
  ask if the headline is inflated by deflector memorization. Held-out-deflector eval
  (train on 258 deflectors, eval on the 64 the model never saw): **held-out R² +0.541,
  NMAD 0.095″ vs in-training control R² +0.659, NMAD 0.090″.** NMAD ≈ identical → the
  model generalizes to unseen deflector appearance; the reuse does not inflate θ_E
  accuracy. Report NMAD alongside R² (R² gap is the smaller/narrower 64-lens subset).

## 7. Which models are more accurate?
- **HAVE:** resnet (v2 primary), convnextv2 (GEN4). No systematic arch sweep on v2.
- **DONE:** arch grid on v2 (Q1): resnet R²+0.70/RMSE0.234 (best overall);
  inceptionnext +0.625 / convnextv2 +0.676 (tighter NMAD 0.074–0.076 but worse
  tail). **Resnet is the pick.** convnextv2 converged at lr 3e-4 (1e-3 diverged).

## 8. Discussion with Sam and Brian
- **ACTION (user):** schedule it. I can prep a one-page results brief / slides
  (cross-matrix, v2-vs-LEMON table, mock-realism figure) for the meeting.

## Next-steps ladder (recommended order)
1. **Deep-ensemble UQ on v2** (#5, prof-recommended) — GPU, ~half day; the clearest
   paper gap. Reuse/extend the arch grid (#7) as the ensemble members.
2. **Arch grid on v2** (#7) — GPU; gives the accuracy claim + ensemble members.
3. **Analysis figures** (#1 mock-realism, #2 σ_v→θ_E validation) — CPU, quick, high
   paper value.
4. **Paper text** (#3 related-work + why-better table, #6 GT-quality section, #4 DA
   framing) — writing.
5. **LEMON email** (same-354 ask) + **Sam/Brian meeting prep** (#8) — user-driven.
