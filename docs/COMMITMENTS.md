# COMMITMENTS LEDGER — design decisions that defer implementation

Rule (added to CLAUDE.md 2026-07-12): every time a decision says "later", "at
stage X", "flagged for verification", or couples a fix to a future stage, it
gets a row HERE at decision time. **Before any full generation and at every ⛔,
this ledger is reconciled**: each OPEN row is either implemented, re-deferred
with a reason, or retired with a reason — silently dropping a row is the
failure mode this file exists to prevent (discovered when the G0-anchored
ΔPA↔γ_ext coupling was found unimplemented at eval #19, 2026-07-12).

Status: OPEN / IN-PROGRESS / DONE / RETIRED (reason).

| id | commitment | origin | status | enforced/verified where |
|---|---|---|---|---|
| C1 | ΔPA ↔ γ_ext coupling in the generator | G0 2026-07-11 | IN-PROGRESS (patched 07-12, AR2 pilot overnight) | manifest spec block (C10) |
| C2 | q_mass–q_light exact relation fitted from Shajib+2021 / Etherington+2022 tables (currently ad-hoc q ⊕ 0.08) | GEN4 plan P1.3 "at G2 — flagged for verification" | OPEN | fit script + manifest spec block |
| C3 | WFC3/UVIS 0.04″→0.05″ resample step in the stamp builder | G1b 2026-07-12 | OPEN (blocks 541 of 1,982 G1b targets) | g1b fetch/builder |
| C4 | Known-lens catalog crossmatch (BELLS/SL2S/…) added to G1b exclusions before fetch | G1b 2026-07-12 | DONE (g1b_fetch_precheck.py, VizieR w/ fallback) | g1b fetch precondition |
| C5 | AR3 isophote (a3/a4) fits added to the G1b measurement pass | AR plan 2026-07-12 | OPEN | g1b builder |
| C6 | AR7 LOS structure needs a θ_E-label-convention ruling BEFORE implementation | AR plan 2026-07-12 | OPEN (ruling needed, then implement or retire) | this ledger |
| C7 | HUDF deeper source-morphology tier as ablation | GEN4 plan P4 | OPEN (→ AR4 tier 2) | AR4 |
| C8 | Emails: Busillo — **their per-lens predictions RECEIVED 2026-07-22 (tables/lemon_predictions/); SLACS-29 now resolved.** Still worth a reply to confirm their SLACS-only internal metric + how ACS-13 GT (arc radius) was assigned. Bergamini (HST2EUCLID), TinyLensGPU authors, Brian — still to send | 2026-07-10, upd. 07-13/07-22 | IN-PROGRESS | EMAIL_DRAFTS_20260710.md |
| C9 | Old-generation training-set deletion (~25 GB) | 2026-07-12 Nurkyz ruling | DONE (approved + executed by night driver) | quota check before G1b fetch |
| C10 | Generator prints a PHYSICS SPEC block (FJ ✓/✗, misalignment ✓/✗, γ-coupling ✓/✗, multipoles ✓/✗, arc-Poisson ✓/✗ …) so pilots surface unimplemented physics mechanically | AR0/AR1 session 2026-07-12 | OPEN (implement with AR2) | pilot gate output |
| C11 | Conformal σ on a real-disjoint pool (σ coverage still under: RAW 53/89 at #17, 50/74 at #18) | eval #16 finding 4 | OPEN (needs real-GT-disjoint pool design) | eval protocol |
| C12 | g3_cnv2_s3 diverged member: retrain or exclude from any reused G3 ensemble | eval #18 incident | OPEN (moot if g3b supersedes G3) | arbitration MEMBERS list |
| C13 | AR1 native-arm arc shot noise: patch APPLIED 2026-07-12 (default OFF, smoke-verified flux 0.9985 / scatter √(f/t)); pilot + gates before enabling in any full generation | AR plan | IN-PROGRESS (pilot after chain) | hybrid_combine --arc_poisson + pilot |
| C14 | AR0 arc-realism gate: BASELINE RECORDED 2026-07-12 — all 4 metrics PASS in BOTH domains (sim inside real 16–84% throughout; sim contrast trends high ~7.8–9.1 vs real ~6, consistent with visibility selection) → the first-order arc-morphology gap is SMALL; wire ar0_arc_gate.py into every pilot chain alongside gate_stage0 | AR plan | baseline DONE; pilot-wiring OPEN | ar0_arc_gate.py in pilot sbatches |
| C15 | σ_v→θ_E mapping corrections: (a) f_SIS normalization σ_SIS = σ_fiber/0.948 (SLACS-measured; our θ_E ~11% low at fixed light); (b) +7% intrinsic stellar-vs-lensing dispersion scatter in quadrature; (c) validation figure θ_SIS(σ_fiber) vs b_SIE on the benchmark (literature-normalized, never fitted on test data) | P1-AUDIT 2026-07-13 | OPEN (pilot with next data build; figure immediate) | g2_make_manifest + paper fig |
| C16 | LEMON head-to-head program (Q1a–Q3): reconstruct their exact 60-lens Euclidised sample + native Q1-354 eval vs PyAutoLens GT — full staging in MASTER_PLAN.md §2. **UPDATE 2026-07-22: their per-lens predictions received → SLACS-29 RESOLVED; head-to-head recomputed vs Bolton (results/lemon_vs_ours_slacs29.csv; we win every metric). UPDATE 2026-08-01: domain-A COMPLETE — EEL/COSMOS tabled (results/lemon_vs_ours_eel_cosmos_acs.csv); lead SLACS+EEL, COSMOS a small-N wash (out-of-support >2.3"), ACS no θ_E GT. Remaining: domain-B (native Euclid Q1, evals #24/#25 R²~0.6 < LEMON 0.71) + paper table.** | Nurkyz directive 2026-07-13 | IN-PROGRESS (Q0 done; domain-A DONE; domain-B open) | MASTER_PLAN.md §2 + §6 checklist, reconciled at every ⛔ |
| C17 | Q2c flux/ZP gate on real VIS cutouts BEFORE any Q1 eval (LEMON needed −0.22 mag; measure ours, don't assume) | Q program 2026-07-13 | OPEN | Q2c gate script + DECISIONS_LOG |
| C18 | New real-lens files (real_lemon31, Q1 cutouts) frozen at creation; every eval on them logged with the running count | Q program 2026-07-13 | OPEN (standing rule extension) | DECISIONS_LOG eval entries |
