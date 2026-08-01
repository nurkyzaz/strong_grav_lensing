# COMMITMENTS LEDGER — design decisions that defer implementation

Rule (added to CLAUDE.md 2026-07-12): every time a decision says "later", "at
stage X", "flagged for verification", or couples a fix to a future stage, it
gets a row HERE at decision time. **Before any full generation and at every ⛔,
this ledger is reconciled**: each OPEN row is either implemented, re-deferred
with a reason, or retired with a reason — silently dropping a row is the
failure mode this file exists to prevent (discovered when the G0-anchored
ΔPA↔γ_ext coupling was found unimplemented at eval #19, 2026-07-12).

**FULL REWRITE 2026-07-14 (Nurkyz directive: "write out commitments so we
execute everything and forget nothing").** Every stream swept: C-rows, the
AR ladder, the inherited I-items (MASTER_PLAN §4), the professor comments
(P-rows, evaluated — we act where warranted, and record why elsewhere).

Status: OPEN / IN-PROGRESS / DONE / RETIRED (reason).

## Closed rows (kept for the audit trail)

| id | commitment | status |
|---|---|---|
| C1 | ΔPA↔γ_ext coupling | DONE (g4ar, ⛔ #22: SLACS null, helps faint-arc; in recipe) |
| C4 | Known-lens crossmatch before G1b fetch | DONE (g1b_fetch_precheck.py) |
| C9 | Old-generation training-set deletion (~25 GB) | DONE (night driver) |
| C13 | AR1 arc shot noise pilot + gates | DONE (in g4ar, ⛔ #22) |
| C15 | σ_v→θ_E corrections (a) /0.948 (b) +7% scatter (c) validation figure | (a)+(b) IMPLEMENTED in g2_make_manifest (takes effect at the NEXT build — verify in the z-migration pilot gates, see C21); (c) DONE (raw −8.5% → corrected +1.8%, N=57) |
| C17 | Q2c flux/ZP gate before any Q1 eval | DONE (measured, swept, frozen ×11.4; ⛔ #24 ran; texture-convention translation ×2.85 in ⛔ #25) |

## Live rows

| id | commitment | origin | status | next action / enforced where |
|---|---|---|---|---|
| C2 | q_mass–q_light exact relation fitted from Shajib+2021/Etherington+2022 (currently ad-hoc q ⊕ 0.08) | GEN4 P1.3 | OPEN — **data source RESOLVED (Zenodo 6104823, Etherington+2022 per-lens `model.results`); a TOP blocker for GEN5 full generation**: fit BEFORE the full-gen manifest | fit script + C10 sidecar shows it |
| C3 | WFC3/UVIS 0.04″→0.05″ resample in the stamp builder | G1b | OPEN (blocks 541 of 1,982 G1b targets; ACS-only fetch running meanwhile) | g1b builder, before phase-2 fetch |
| C5 | G1b measurement pass INCLUDING isophote a3/a4 (feeds AR3) | AR plan | **DONE 2026-07-21** (jobs 48446/48447): 488 stamps measured, iso OK 487, AR3-usable 394; g1b_kinematics_v1.csv (cluster + tables/) | consumed by the C21 merge (carry iso_* columns) |
| C6 | AR7 LOS structure needs a θ_E-label-convention ruling BEFORE implementation | AR plan | OPEN (ruling needed, then implement or retire) | this ledger |
| C7 | AR4 HUDF deep source-morphology tier | GEN4 P4 | OPEN (only if the arc gate shows a gap after AR3) | AR4 |
| C8 | Emails: Busillo — **REWRITTEN 2026-08-01 (Nurkyz): drop "cannot reproduce" framing; two concrete asks (1) ACS θ_E ground truth — is it the Pawase arc radius or another θ_E; (2) SLACS — share our preds + ask them to confirm their scoring (our recompute of their SLACS preds vs Bolton gives R²≈−4.3) + permission for a same-lens SLACS comparison in our paper; plus a post-GEN5 native-Euclid cross-check (C34).** Ready to send (Nurkyz sets provenance line + sends). Bergamini (HST2EUCLID), Cao/TinyLensGPU (I1), Brian (authorship, I15) still to send | 2026-07-10+, upd 08-01 | IN-PROGRESS | EMAIL_DRAFTS_20260710.md; Nurkyz sends |
| C10 | Physics spec block | AR0/AR1 | generator half DONE (sidecar + print); **REMAINING: AR3/z-migration pilot scripts FAIL HARD if sidecar missing — blocks those pilots** | pilot scripts |
| C11 | Conformal σ on a real-disjoint pool (coverage 20–23/43–50 at #24 — WORSE out-of-domain) | eval #16 | OPEN, urgency HIGH — merges with P3 (UQ paper section, C23); pool design = the real question | eval protocol + paper |
| C12 | g3_cnv2_s3 diverged member | eval #18 | RETIRE-CANDIDATE (G3 superseded by g3b/g4ar in every recipe; retire formally at next ⛔) | arbitration lists |
| C14 | Wire ar0_arc_gate.py into every pilot chain | AR plan | OPEN — add to the z-migration + AR3 pilot sbatches | pilot sbatches |
| C16 | LEMON head-to-head (Q1a–Q3) | Nurkyz 2026-07-13 | IN-PROGRESS: Q2 arm complete; **LEMON REPLIED 2026-07-14 with 4 CSVs (59 lenses). Q1a (SLACS-29) DONE — zero-cost row-filter, we win both domains (native R² +0.29 vs their −4.26; Euclid +0.57 vs −4.26), flagged as a puzzle not yet explained. Q1b (30 non-SLACS): DONE. **UPDATE 2026-08-01: domain-A COMPLETE — EEL/COSMOS tabled (results/lemon_vs_ours_eel_cosmos_acs.csv): lead SLACS+EEL, COSMOS small-N wash (out-of-support >2.3″). ACS scored vs Pawase arc radius for BOTH methods (C35) — reported SEPARATELY, kept OUT of the θ_E aggregate. GT verified vs primary sources (EEL J1446 0.41→0.43 corrected). Paper §4.6 paragraph written; email rewritten (C8). Remaining: domain-B = native Euclid Q1 (C34, post-GEN5).** | lemon_headtohead/ + lemon_comparison_package/ |
| C18 | New real-lens files frozen at creation; every eval logged with count | Q program | STANDING (honored through #25) | DECISIONS_LOG |
| C19 | ⛔ eval #25 texture-fixed Q1 re-run + pre-registered interpretation rule | #24 forensics | DONE (count → 25): R² +0.57/fail 29% — **#24 headline RETRACTED as preprocessing artifact; #25 = official Q2e number**; residual population effect modest, = the C21/C22 target | DECISIONS_LOG |
| C20 | Path A Rung 0 submission: exactly-once unlabeled run → CSVs → **NURKYZ emails Stony Brook**; log the submission + their returned grade when it arrives | Nurkyz go 2026-07-14 | RUN DONE, CSVs DELIVERED to Mac roman_dc/ (3band all6 ×0.98 primary; f106 all6 ×1.11; N=11,067). **WAITING: Nurkyz's email, then their grade** | roman_dc/ + DECISIONS_LOG |
| C21 | **GEN5 = z-migration + AR3 module** (renamed from Path B v2; Nurkyz GEN4/GEN5 naming ruling 2026-07-22) | strategy session 2026-07-14 | **v4 PILOT PASSES ALL GATE STATS 2026-07-22 (peak/sky 141, sky-RMS 0.955, FJ -0.48, AR0 4/4, Roman 1.03/1.02/1.05); recipe FROZEN (evo_q 1.2, EUC_SKY 2.2, selection 0.8/150, ROM_FLUX 0.11).** Full gen BLOCKED on: C30 (Phase-1 visual fixes), C31 (evo_q confirm), C2 fit, Nurkyz >1k confirm | pipeline/g5_* + g5_c21_pilot_review gallery |
| C22 | DA experiment (I9 execution): target = native real Q1 (only domain with measured gap + real unlabeled pool, 322 cutouts); --da_pool machinery exists; baseline = ⛔ #25; scored on PyAutoLens GT (their referee, disclosed) — professor P2 alignment | strategy session | OPEN — after #25 harvest | training run + one logged eval |
| C23 | UQ first-class paper section (professor P3): per-domain coverage tables, ρ(σ,|err|), ensemble-vs-single-member ablation (FROM SAVED CSVs — no new evals), conformal story incl. the #24 OOD collapse as the honest exhibit; cite Lakshminarayanan+17, Fort+19 (1912.02757) | professor P3 | OPEN — analysis-only, cheap, high paper value | PAPER_DRAFT §reliability |
| C24 | Original LEMON paper (MNRAS 522, 5442, 2023) into LITERATURE.md + cite/compare alongside the 2026 A&A paper (professor P4) | professor P4 | OPEN — reading + one table row | LITERATURE.md |
| C25 | Architecture-insensitivity finding (professor P1): on REAL lenses all archs score within noise while sim-val separates them → the binding constraint is the training distribution, not capacity. Write as a paper finding WITH the arch/seed spread table (saved CSVs); "better model" bar DEFINED as: same arch ± DA scored on real-GT (C22) + σ quality under TDLMC-style grading (C23) | professor P1 | OPEN — analysis-only; no new experiment beyond C22/C23 | PAPER_DRAFT §discussion |
| C26 | Rung 1/2 decision: Rung 1 (substructure) is LIVE — decide enter/skip after the Rung 0 grade returns; 8-band ruled out for Rung 0 (3 bands shipped) but recheck band count on later rungs | Roman program | OPEN — decision with Nurkyz | MASTER_PLAN §2R |
| C27 | Housekeeping: truncated Rung 0 h5 on the Mac (775 of 1225 MB — unusable); resume via rsync --partial or delete | 2026-07-14 | OPEN (Nurkyz preference) | roman_dc/ on Mac |
| C28 | Full-SIMBAD all-otype crossmatch (10″; lens types gLS/gLe/LeI/LeG/LS?/Le?) is a STANDING precheck for every future deflector/library fetch — C4's 3-catalog version missed 44 lens fields incl. 3 EELs, 3 CSWAs, 6 Faure COSMOS lenses | G1b prune 2026-07-21 | DONE for g1b (44 removals); STANDING for future fetches | fetch prechecks + g1b_prune_final.csv |
| C29 | G1b measurement pass must consume keep_final from tables/g1b_prune_final.csv (NOT the raw review CSV) and resolve the close_pair/bcg/low_snr flags via isophote-fit quality gates; the 6 new lens candidates (tables/g1b_lens_candidates.csv: 00266/00777 HIGH) get a follow-up decision with Nurkyz | G1b prune 2026-07-21 | keep_final consumption DONE (builder --keep_csv); flags resolved via iso diagnostics (94 pair-flagged); candidate follow-up with Nurkyz still OPEN | C5 measurement pass |

## Inherited I-items (MASTER_PLAN §4) — next-action sweep 2026-07-14

- I1 (Cao per-lens): email unsent (C8); fallback = re-run TinyLensGpu ourselves — decide at paper time.
- I2 (two-stage hybrid row): OPEN, paper-value high — schedule after C21/C22.
- I3 (aux heads): OPEN — natural add-on to the z-migration training grid if slots free.
- I4 = C11. I5 (confirmation set): assemble with Nurkyz BEFORE submission — calendar item.
- I6 (GT-error ceiling): analysis-only, cheap — fold into paper sprint with C23/C25.
- I7 (inference cost): trivial — fold into paper sprint.
- I8 (ablation-table decision): decide with Nurkyz at paper time.
- I9 = C22. I10/AR8 (TNG-κ): paper-2. I11 (BELLS/COWLS): follow-up paper.
- I12 (universal loader): Q2b built the Q1 side; generalize opportunistically.
- I13 (companion v2): dormant. I14 (release package): at submission.
- I15 (Brian authorship): NURKYZ, overdue. I16 = C8. I17 (Etherington subset): verify in eval protocol during the paper sprint. I18: retired.

## AR ladder sweep 2026-07-14

AR0 gate: wire-in = C14. AR1+AR2: DONE (#22). **AR3: next physics build after
G1b measure (C5) + C10 check; expect to ride the z-migration regen so ONE
regen carries AR3 + C2 + C15-verify.** AR4: C7-gated. AR5: after AR3.
AR6 (slope–σ_v): bundle with the z-migration regen if cheap. AR7: C6-gated.
AR8: paper-2.

⛔ #22 reconcile (2026-07-13): C1, C13 → DONE. C15 a/b implemented, c done.
C17 measured. Others re-deferred with reasons (see git history for the full
note).

| C30 | GEN5 Phase-1 visual fixes (Nurkyz eye-check 2026-07-22). **2026-08-02 PROGRESS:** (1) companion cut DONE — rate 8-26→**2-9** (flux_pct 35), field comp tail 33%→4%, side-by-side clean vs real Q1; (2) arc-SMOOTHNESS metric BUILT (analysis/arc_smoothness.py) → "too-elliptical" NOT confirmed, CLOSED (no tuning); (3) deflector Re fixed as a bonus (0.63→0.547"≈real). **REMAINING: deflector peak/sky reads ~80 (real 103-727) — core too faint/diffuse → deflector-brightness pass (ties to C31 evo_q); then re-pilot + Nurkyz eye-check.** | GEN5 Phase 0 2026-07-22 | IN-PROGRESS (companion+smoothness DONE; deflector-brightness open) | analysis/{arc_smoothness,measure_pilot}.py + pipeline/g5_phase1_companion.sbatch + re-pilot |
| C31 | evo_q deflector passive-evolution brightening (Q=1.2 mag/z, Faber+2007) is my literature-anchored addition, NOT measured here — CONFIRM with Nurkyz/Brian before full generation | GEN5 v4 2026-07-22 | OPEN (physics confirm) | g5_make_manifest --evo_q; sidecar flags PENDING CONFIRM |
| C32 | Real Q1 eval-set (322) data-quality: auto-audit RULED unreliable (over-reads arcs); Nurkyz adjudicates via the upgraded q1_real_review gallery. Only DEFENSIBLE machine flag = tiny-theta (2 failed PyAutoLens models, incl. #161). Frozen test data -> nothing dropped without Nurkyz | GEN5 Phase 0 2026-07-22 | OPEN (Nurkyz visual pass; then decide flag-vs-subset for the head-to-head) | q1_real_review/index.html + real_q1_characterization.csv |
| C33 | Q1 SLDE full set is 336 dirs / 335 GT; frozen eval h5 has 322 — reconcile the 322-vs-335-vs-354(LEMON) counts and disclose at the Q1 eval | Q program | OPEN | eval writeup |
| C34 | **Native-Euclid LEMON head-to-head with the GEN5 model** (Nurkyz 2026-08-01): once GEN5 is finalized, compare our model to LEMON on native Euclid Q1 in *their* home domain (= the domain-B half of C16). Blocked on GEN5 completion (C21/C30). | Nurkyz 2026-08-01 | OPEN (blocked on GEN5) | MASTER_PLAN §2 domain-B + email C8 point 3 |
| C35 | **ACS scored vs Pawase arc radius for BOTH methods — DONE 2026-08-01** (analysis/lemon_acs_arcradius.py, results/lemon_vs_ours_acs_arcradius.csv, tables/pawase_arc_radius.csv). Our scatter tighter (NMAD 0.31 vs 0.36) but expected θ_E<arc-radius neg bias; reported SEPARATELY from the θ_E aggregate (unlike LEMON Table 3). | Nurkyz 2026-08-01 | DONE | PAPER_DRAFT §4.6, lemon_comparison_package/README.md |

⛔ #24 reconcile (2026-07-13 night): C17 → DONE; C16 Q2-arm complete; C18
honored; C11 urgency raised; C10 generator half done.

Rewrite reconcile (2026-07-14): all rows above re-verified against
MASTER_PLAN §1R/§2R/§3/§4, DECISIONS_LOG through the strategy session, and
the professor comments. Nothing from the archived plans remains untracked.
