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
| C1 | ΔPA ↔ γ_ext coupling in the generator | G0 2026-07-11 | DONE (in g4ar; ⛔ eval #22 2026-07-13: SLACS-aggregate null, helps faint-arc/S4TM + conf gating; stays in the recipe going forward) | manifest spec block (C10) |
| C2 | q_mass–q_light exact relation fitted from Shajib+2021 / Etherington+2022 tables (currently ad-hoc q ⊕ 0.08) | GEN4 plan P1.3 "at G2 — flagged for verification" | OPEN | fit script + manifest spec block |
| C3 | WFC3/UVIS 0.04″→0.05″ resample step in the stamp builder | G1b 2026-07-12 | OPEN (blocks 541 of 1,982 G1b targets) | g1b fetch/builder |
| C4 | Known-lens catalog crossmatch (BELLS/SL2S/…) added to G1b exclusions before fetch | G1b 2026-07-12 | DONE (g1b_fetch_precheck.py, VizieR w/ fallback) | g1b fetch precondition |
| C5 | AR3 isophote (a3/a4) fits added to the G1b measurement pass | AR plan 2026-07-12 | OPEN | g1b builder |
| C6 | AR7 LOS structure needs a θ_E-label-convention ruling BEFORE implementation | AR plan 2026-07-12 | OPEN (ruling needed, then implement or retire) | this ledger |
| C7 | HUDF deeper source-morphology tier as ablation | GEN4 plan P4 | OPEN (→ AR4 tier 2) | AR4 |
| C8 | Emails: Busillo/LEMON **REPLIED (2026-07-14): will provide the requested lists/numbers — await, no nudge needed**; Bergamini (HST2EUCLID), TinyLensGPU authors, Brian — still to send | 2026-07-10, upd. 07-14 | IN-PROGRESS | EMAIL_DRAFTS_20260710.md |
| C9 | Old-generation training-set deletion (~25 GB) | 2026-07-12 Nurkyz ruling | DONE (approved + executed by night driver) | quota check before G1b fetch |
| C10 | Generator prints a PHYSICS SPEC block (FJ ✓/✗, misalignment ✓/✗, γ-coupling ✓/✗, multipoles ✓/✗, arc-Poisson ✓/✗ …) so pilots surface unimplemented physics mechanically | AR0/AR1 session 2026-07-12 | IN-PROGRESS — **BLOCKING AR3 PILOT** (Nurkyz ruling 2026-07-13). Generator half DONE 07-13: g2_make_manifest.py prints the full block AND writes `<manifest>.physics_spec.json` sidecar (.bak_c10; compiles). REMAINING: the AR3 pilot script MUST fail hard if the sidecar is missing/incomplete — AR3 cannot launch without this check | manifest sidecar + AR3 pilot script check |
| C11 | Conformal σ on a real-disjoint pool (σ coverage still under: RAW 53/89 at #17, 50/74 at #18) | eval #16 finding 4 | OPEN (needs real-GT-disjoint pool design) | eval protocol |
| C12 | g3_cnv2_s3 diverged member: retrain or exclude from any reused G3 ensemble | eval #18 incident | OPEN (moot if g3b supersedes G3) | arbitration MEMBERS list |
| C13 | AR1 native-arm arc shot noise: patch APPLIED 2026-07-12 (default OFF, smoke-verified flux 0.9985 / scatter √(f/t)); pilot + gates before enabling in any full generation | AR plan | DONE (pilot passed 07-12; in g4ar; ⛔ eval #22 2026-07-13 — same reading as C1) | hybrid_combine --arc_poisson + pilot |
| C14 | AR0 arc-realism gate: BASELINE RECORDED 2026-07-12 — all 4 metrics PASS in BOTH domains (sim inside real 16–84% throughout; sim contrast trends high ~7.8–9.1 vs real ~6, consistent with visibility selection) → the first-order arc-morphology gap is SMALL; wire ar0_arc_gate.py into every pilot chain alongside gate_stage0 | AR plan | baseline DONE; pilot-wiring OPEN | ar0_arc_gate.py in pilot sbatches |
| C15 | σ_v→θ_E mapping corrections: (a) f_SIS normalization σ_SIS = σ_fiber/0.948 (SLACS-measured; our θ_E ~11% low at fixed light); (b) +7% intrinsic stellar-vs-lensing dispersion scatter in quadrature; (c) validation figure θ_SIS(σ_fiber) vs b_SIE on the benchmark (literature-normalized, never fitted on test data) | P1-AUDIT 2026-07-13 | (a)+(b) IMPLEMENTED 2026-07-13 in g2_make_manifest.py (.bak_c15; takes effect next manifest build, pilot-gated); (c) DONE (raw −8.5% → corrected +1.8%, N=57; paper_figures/c15c_validation.png + tables/c15c_theta_sis_vs_bsie.csv; first attempt used the photometry table by mistake — retracted and refetched Bolton08 table4 kinematics) | g2_make_manifest + paper fig |
| C16 | LEMON head-to-head program (Q1a–Q3): reconstruct their exact 60-lens Euclidised sample (31 non-SLACS from cited tables; 29 SLACS via email/H-flags/H-fig9) + native Q1-354 eval vs PyAutoLens GT — full staging in MASTER_PLAN.md §2 (LEMON plan archived) | Nurkyz directive 2026-07-13 | PARKED 2026-07-14 (Nurkyz ruling): Q2 arm COMPLETE (⛔ #24 + forensics); Q1a/Q1b resume when LEMON's promised lists arrive (reply received); do NOT reconstruct in the meantime | MASTER_PLAN.md §2 + §6 checklist, reconciled at every ⛔ |
| C17 | Q2c flux/ZP gate on real VIS cutouts BEFORE any Q1 eval (LEMON needed −0.22 mag; measure ours, don't assume) | Q program 2026-07-13 | DONE (measured, swept Q2c2, FROZEN ×11.4 no-pedestal by ruling, gate re-verified on the full frozen set — skyRMS matched; ⛔ #24 ran on it. Residual note: full-set peak/sky 218 vs bench 480 = population contrast gap, logged as the #24 finding, not a normalization issue) | q2_c17_gate.py + DECISIONS_LOG #24 |
| C18 | New real-lens files (real_lemon31, Q1 cutouts) frozen at creation; every eval on them logged with the running count | Q program 2026-07-13 | OPEN (standing rule extension) | DECISIONS_LOG eval entries |

⛔ #22 reconcile (2026-07-13): C1, C13 → DONE (evaluated #22). C15 → a/b
implemented (pilot-gated), c done. C17 → measured, rescale ruling pending.
Re-deferred with reasons: C2+C5 (G1b measurement pass, next build); C3 (g1b
builder, UVIS targets); C6 (needs ruling); C7 (AR4 tier); C10 (NOT in the
g4ar chain — verify, else implement at the AR3 pilot); C11 (pool design);
C12 (moot if the #22 recipe proposal is confirmed); C14 (wire ar0_arc_gate
into the AR3 pilot chain); C16, C18 active.

⛔ #24 reconcile (2026-07-13 night): C17 → DONE (frozen ×11.4, evaluated).
C16 → Q2 arm COMPLETE (native-Q1 miss logged as the headline negative
finding); Q1 60-lens Euclidised arm still open (Q1a/Q1b). C18 → honored
(frozen file, single logged eval). C11 → URGENCY RAISED: coverage 20/43%
out-of-domain at #24 — conformal-on-real pool design should precede any
real-survey deployment claim. C10 → generator half done, AR3-pilot check
still the blocker. Others: unchanged from the #22 reconcile.
