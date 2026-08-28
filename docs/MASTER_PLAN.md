# MASTER PLAN — the single live plan (consolidated 2026-07-13)

This file replaces ALL previous plan documents. Everything undone from them is
carried here; their full text lives in `docs/archive/` (MASTER_PLAN_20260702,
IMPROVEMENT_PIVOT_PLAN_20260710, PATHB_IMPROVEMENT_PLAN, DATA_OVERHAUL_GEN4_PLAN,
PAPER_PLAN, LEMON_HEADTOHEAD_PLAN). Authority order is unchanged:
**DECISIONS_LOG.md > this plan**; COMMITMENTS.md is the deferred-work ledger
(reconciled at every ⛔ and before any full generation); MODELS_AND_RESULTS.md
holds current numbers; PAPER_DRAFT.md is the manuscript; CLAUDE.md holds the
operating rules. If a stage here conflicts with a newer DECISIONS_LOG entry,
the log wins — update this file when that happens.

## 0c. GEN5 v2 delivered + paper-revision phase (2026-08-21)

GEN5 (real Q1 deflector light) is DONE and validated: **v2 = R² +0.73 on real
Euclid Q1, ahead of LEMON's 0.71 on R²** (ties NMAD/bias at matched difficulty;
trails only on RMSE = a high-θ tail). Final model `einstein_cnn_gen5_v2.pt`. Full
recipe: docs/GEN5_PIPELINE.md; GEN4-vs-GEN5 crossover: docs/DOMAIN_SPECIALIZATION.md.
Negative results banked: T0 ensemble (variance, not the lever) and v3 high-θ
oversampling (overfits the tail) — the residual RMSE needs better high-θ DATA, not
resampling/ensembling.

**We are now in the paper-revision phase; WEEK GOAL = finish draft v2 answering the
9 comments.** Mapping in **docs/PROF_COMMENTS_RESPONSE.md**; section-by-section
writing plan in **docs/DRAFT_V2_PLAN.md**.

EXPERIMENTS ARE DONE — the draft is no longer blocked on compute:
- #1 mock realism → mock_realism.png ✓ (σ_v 268, z_l 0.76, z_s 2.09, θ_E 0.91, logM_E 11.5)
- #2 σ_v→θ_E → sigma_theta_validation.png ✓ (bias +2%, scatter 16% after C15a)
- #5 UQ → deep ensemble ✓ (σ↔error ρ=0.59; recalibrate ×1.6 for coverage)
- #7 arch → resnet best ✓ (R²0.70; incnext/cnv2 tighter core, worse tail)
- HONEST headline: GEN5 Q1 R² ≈ **0.71 (ensemble; seed 0.68–0.73) = on par with LEMON**,
  not the seed-lucky 0.729.

Remaining = WRITING (see DRAFT_V2_PLAN.md sequence): §4 headline+positioning+domain-
spec → §2 simulator+mock+σ_v+GT → §4 UQ+§3 arch → §4 DA+intro+discussion. Optional
5-min recalibrate_sigma for the coverage number. User-parallel: LEMON same-354
email; Sam/Brian meeting.

## 0. Where we are (2026-07-13, eval count 22; details in MODELS_AND_RESULTS.md)

GEN4 (self-consistent population: real HST galaxy = light AND mass, SDSS σ_v →
θ_E, FJ channel) delivered the central result on the frozen benchmark:

| domain | bias | RMSE | NMAD | R² | fail |
|---|---|---|---|---|---|
| Native HST SLACS (eval #21) | +0.005″ | 0.152″ | 0.048″ | +0.64 | 15% |
| Native HST S4TM (eval #21) | +0.013″ | 0.088″ | 0.047″ | +0.90 | 8% |
| Euclid-domain SLACS (eval #19) | −0.010″ | 0.137″ | 0.056″ | +0.71 | 15% |
| Euclid-domain S4TM (eval #22, g4ar r50_3) | +0.020″ | 0.103″ | 0.071″ | +0.86 | 22% |

Beats/matches Cao 2025 (conventional, same lenses); beats LEMON Table 3 on every
θ_E aggregate in their Euclidised domain. **Eval #22 LANDED (2026-07-13 PM):**
g4ar (AR1+AR2) is a NULL on the SLACS-Euclid aggregate (−0.028/0.157/+0.62/15%;
#19 keeps that headline) but conf-half fail 0% (first ever) and a new
S4TM-Euclid best (r50_3 above). Recipe proposal PENDING NURKYZ CONFIRM:
G4 cnv2_3 stays Euclid primary, g4ar r50_3 takes the S4TM row. Also landed:
C15a/b implemented in g2_make_manifest.py (pilot-gated); C15c validation
figure done (raw −8.5% → corrected +1.8%, N=57); Q2 10-lens pilot passes
previews; C17 flux gate measured (~11× unit offset — ruling needed, §2 Q2c).
Still on the cluster: g1b 800-target stamp fetch (check g1b_fetch.log);
Q1 SLDE cutouts unzipped (~/cosmos_acs/q1_slde/, 336 lens dirs).

**Update 2026-07-21 (see log): G1b prune COMPLETE — 514 clean deflectors
(tables/g1b_prune_final.csv); 44 known-lens fields removed by full-SIMBAD
crossmatch (incl. EELs J1218/J0913/J1248 — Q1 contamination averted); 6 new
lens candidates (tables/g1b_lens_candidates.csv). LEMON-31 quality review
ruled: primary head-to-head = real-θ_E rows only (SLACS-29 + EEL + COSMOS-3
≈ 44, row-filter on banked CSVs); ACS-13 excluded/disclosed. C5 measurement pass DONE same day (488 measured, 394 AR3-clean) — AR3 + C21 z-migration UNBLOCKED.**

**Update 2026-08-20 (GEN5 real-Euclid milestone): the "dots" blocker is SOLVED —
deflector now rendered from REAL Q1 deflector light (not synthetic FJ). Nurkyz
signed off the look; a 100k deflector-disjoint set was generated and the first
CNN trained on it (sim-val R² 0.996). First eval on the 322 real Euclid Q1 lenses:
R²+0.65 (clean 0.69), RMSE 0.253″ — BEATS our prior real-Q1 attempt (#24/#25:
+0.61), closing on LEMON (0.71). Remaining gap = a high-θ / faint-arc / missing-
multiply-image outlier tail. Improvement program in docs/GEN5_IMPROVEMENT_PLAN.md
(ensemble + θ_E reweight + faint-arc tier + compact-source doubles/quads);
ensemble + v2 pilot running. Full details in MODELS_AND_RESULTS.md (2026-08-20).**

## 0b. GEN5 status (2026-07-22; the ACTIVE workstream) — see DECISIONS_LOG

**Naming ruling (Nurkyz 2026-07-22): GEN4 = low-z native (SLACS/S4TM);
GEN5 = high-z (Euclid-Q1 + Roman) via z-migration.** Roman is fully
simulated (no real GT); Euclid-Q1 has PyAutoLens GT for 322 real lenses.

GEN5 = C21 z-migration + AR3 isophote multipoles on the G1b library
(514 pruned / 488 measured / 394 AR3-clean; 488 STANDALONE per Nurkyz).
v4 pilot passes every gate STAT (peak/sky 141 in [103,727], sky-RMS 0.955,
FJ -0.48, AR0 4/4, Roman 1.03/1.02/1.05 @ FLUX 0.11). Frozen v4 recipe:
g5_make_manifest --evo_q 1.2 [PENDING CONFIRM] -> config_lensfusion_acs_g5
(Gen5HighZSource) -> hybrid_combine (migration + companion dim) -> euclidise
LF_EUC_SKY_SCALE=2.2 + arc_visibility_select 0.8/150 -> romanise FLUX 0.11.

**Nurkyz eye-check -> Phase 0 (DONE, tables/*_characterization.csv): (1)
companions ~4x too many [FIRM fix]; (2) "arcs not visible" = dynamic-range
from clutter, NOT faint arcs (GEN5 arcs measure BRIGHTER than real); (3)
"too-elliptical arcs" NOT confirmed by the coverage metric -> needs a
smoothness metric before tuning; (4) real-eval-set auto-audit ruled
unreliable -> Nurkyz adjudicates via the upgraded q1_real_review gallery
(only 2 tiny-theta failed-model flags are defensible).**

Phase 1 (NEXT, pending Nurkyz go): companion cut to the measured real rate
+ deflector-dominance check + arc-smoothness metric -> re-pilot -> re-show.
BLOCKING full generation: Phase-1 visual fixes; evo_q confirm (Nurkyz/Brian);
C2 q_mass-q_light fit (Zenodo 6104823, still ad-hoc); Nurkyz >1k scale ruling.

## 1R. ENDGAME LADDER (Nurkyz strategy session 2026-07-14 — supersedes the
   ladder below where they conflict; the four remaining workstreams)

1. **LEMON head-to-head (waiting on their email).** On arrival: exact-29
   SLACS row = row-filter on saved CSVs (no run); 31 non-SLACS fetch →
   euclidise → single ⛔ eval; head-to-head table into the paper.
   MEANWHILE (not blocked): ⛔ eval #25 = texture-FIXED re-run of the Q1
   board (staged, --conv zoom) so the comparison against their Fig 12a
   uses the corrected preprocessing, not the #24 bug.
2. **ROMAN.** (a) Path A SUBMISSION: one run on the unlabeled set →
   CSV (3band all6 primary; f106 all6 secondary) → Nurkyz emails Stony
   Brook. (b) **Path B v1 (FLUX-tuned 100k) CANCELLED by ruling** — the
   pilot proved the chain but exposed that z≈0.14 deflectors cannot mimic
   the z≈0.8 population by flux scaling alone. **Path B v2 = REDSHIFT
   MIGRATION**: render each real stamp as it would appear at the target
   z (shrink by D_A ratio, dim by D_L ratio; σ_v is intrinsic → the
   FJ/GEN4 self-consistency claim survives; the F814W→F106 rest-frame
   proxy IMPROVES at z~0.8). Same build serves the Euclid-Q1 population
   gap (the #24 remedy) — one migration module, two domains. Pilot-gated
   as always. (c) 8-band: IMPOSSIBLE on Rung 0 (only 3 image bands
   shipped); our 3-band arm is already the rung maximum; revisit at
   Rung 1/2.
3. **DOMAIN ADAPTATION (I9): target = native real Euclid Q1** — the only
   domain with BOTH a measured gap (#24) and real images for the
   unlabeled pool (322 cutouts). Machinery exists (train_cnn_paltas
   --da_pool). Run AFTER eval #25 sets the corrected baseline. Sim-to-real
   DA scored on real GT remains unclaimed in the literature.
4. **CONSOLIDATION**: AR3 (gated on G1b prune+measure — **prune DONE
   2026-07-21: 514 clean, g1b_prune_final.csv; the C5 measurement pass is
   now the AR3/C21 critical path** — and the C10 pilot check); C2 q_mass–q_light fit + C15 pilot
   verification fold into the z-migration regen; I6 GT-ceiling + I7
   inference-cost (cheap, paper-time); professor comments — NURKYZ TO
   PROVIDE THE LIST; paper §4 + Q3 sections continuous.

## 1. Priority ladder (Nurkyz-set direction + Q program; work top-down,
   parallel where independent)

1. **Harvest ⛔ eval #22** (g4ar) — DONE 2026-07-13; ⛔ eval #23 (derived
   two-model ensemble) DONE same day. **Nurkyz RULED: no headline freeze —
   multi-domain reporting; provisional recipe = G4 cnv2_3 (SLACS-Euclid),
   g4ar r50_3 (S4TM-Euclid), #23 ens2 as the combined row; headline chosen
   at final paper drafting.**
2. **Q program — PARKED 2026-07-14 (Nurkyz ruling): LEMON replied and will
   provide their exact lists/numbers — wait for that instead of
   reconstructing.** Q2 arm complete (⛔ #24 miss + forensics, logged);
   Q1a/Q1b (31 non-SLACS images) resume on their email; SLACS-29 row =
   row-filter when the list arrives. Two-scoreboard note: their Sect 2.2
   (60 Euclidised) vs Sect 6.3/Fig 12 (Q1-354, success-filtered) — both
   real, don't conflate.
3. **G1b library build**: ~~visual prune~~ DONE 07-21 (514 clean; 44
   known-lens fields caught, C28 standing crossmatch adopted) →
   ~~measurement pass~~ DONE 07-21 (488 measured incl. a3/a4, 394 AR3-clean; g1b_kinematics_v1.csv) → C15a/b σ_v corrections (f_SIS = σ_fiber/0.948, +7% intrinsic scatter) in the next
   manifests; C15c validation figure (analysis-only) can be made immediately.
4. **AR3 isophote-anchored multipoles** (one pilot, gates incl. AR0 arc gate)
   → regen with the BIG G1b library + C15 corrections → ⛔ eval pair
   (native + Euclid). Expect less tempering (stronger training FJ ρ).
   **HARD GATE (C10, Nurkyz ruling 2026-07-13): the AR3 pilot script must
   verify `<manifest>.physics_spec.json` exists and contains every physics
   axis (incl. multipoles=ON) and FAIL IMMEDIATELY otherwise — AR3 does not
   launch without it.** Generator side shipped 07-13 (g2_make_manifest.py
   prints the block + writes the sidecar).
5. **G5 ROMAN** — full focus after 4; FULL PROGRAM IN §2R (researched
   2026-07-13): Wedig et al.'s 16,214 public Roman sims WITH θ_E GT become our
   external Roman benchmark (zero-shot baseline first, then the G5-trained arm);
   own InstrumentConfig rendering (WFI 0.11″/px, STPSF PSF, HLWAS depths) stays
   the training side; multiband as a staged non-gating extension. Cite Wedig et
   al. 2025 (arXiv:2506.03390). **NB — a ROMAN COMPETITION entry was already
   SUBMITTED (our 6-network G5a ensemble; Nurkyz 2026-07-22); the G5 rendering
   here is the paper-2 sim work, NOT the competition submission.**
6. **Paper §4 rewrite + release assets** (§5) — continuous, parallel.

## 2. Q program — beat LEMON on their exact lenses, both domains (C16)

Scoreboards (verified from their PDF 2026-07-13):
(A) 60 Euclidised HST lenses, Table 3: θ_E bias −0.03″/RMSE 0.14″/NMAD 0.11″/
R² 0.53 — heterogeneous literature GT, and 13/60 (ACS/Pawase) have NO θ_E at
all (arc radius substituted; disclose this).
(B) 354 real Euclid Q1 lenses vs PyAutoLens SIE (Fig. 12a): bias 0.01″/
RMSE 0.17″/NMAD 0.07″/R² 0.71. Their mass ellipticities on Q1 do NOT correlate
(R² −0.31/−0.44); magnitudes needed an ad-hoc −0.22 ZP shift; their Sect. 7
admits real < sim performance.

### Q1 — their 60-lens Euclidised HST sample
- **Q1a sample identity**: EELs 13/13 IDENTIFIED (Oldham 2017 Table 2 —
  J0837 0.56″, J0901 0.67″, J0913 0.42″, J1125 0.86″, J1144 0.68″, J1218
  0.68″, J1323 0.31″, J1347 0.43″, J1446 0.41″, J1605 0.64″, J1606 0.52″,
  J1619 0.50″, J2228 0.60″; GT = power-law+shear, disclose). **UPDATE
  2026-07-22: LEMON's per-lens predictions received (tables/lemon_predictions/)
  — their EEL file has 12, NOT 13 (J0913 absent).** COSMOS 5 = the
  spectroscopically-confirmed subset of Faure 2008 — **PINNED from their file:
  {0012+2015, 0038+4133, 0047+5023, 0211+1139, 5921+0638}.** ACS 13 =
  spec-confirmed subset of Pawase 2014 Table 3 (NO true θ_E — arc radius only;
  scored SEPARATELY for both methods 2026-08-01 and kept OUT of the θ_E
  aggregate, C35). **SLACS 29: ✅ RESOLVED 2026-07-22 — their SLACS prediction
  file names all 29 (100% match to Bolton Table 5). Prior Ring=32 / Ring∩σ=31
  hypotheses FALSIFIED (actual: 22/29 ring, 28/29 good-σ, 21/29 both). List +
  head-to-head in DECISIONS_LOG 2026-07-22 and results/lemon_vs_ours_slacs29.csv.**
  Recomputed on the exact 29 vs Bolton: LEMON R²−4.26/NMAD 0.307/55% fail vs ours
  (Euclid) R²+0.57/NMAD 0.045/7% — the 62-superset row is superseded by the
  exact-29 row. Deliverable: tables/lemon60_targets.csv.
- **Q1b imaging (31 non-SLACS)**: DONE 07-15 (30/30 fetched, frozen, euclidised,
  ⛔ eval harvested — see log). **RULED 07-21 after Nurkyz's cutout quality review:
  primary table = real-θ_E rows only (SLACS-29 + EEL-12 + COSMOS-3..5 ≈ 44–46;
  ACS-13 excluded from the θ_E aggregate — Pawase GT is arc radius). UPDATE
  2026-08-01: domain-A tabled (results/lemon_vs_ours_eel_cosmos_acs.csv), GT
  verified vs primary sources (EEL J1446 0.41→0.43 corrected), ACS scored vs arc
  radius for both methods (C35), paper §4.6 written. Disclose ACS in the honesty
  box (13/60 of LEMON's own aggregate GT is arc radius).**
- **Q1c ⛔ eval (logged)**: current Euclid primary + TTA; LEMON-convention
  table per subsample + combined; SLACS row = 29-exact when resolved (then it
  is a ROW-FILTER on saved per-lens CSVs — no re-run). Bar: beat their 60-lens
  NMAD and R² on the matched composition.

### Q2 — native real Euclid Q1 (their 354; the unplayed board) — UNBLOCKED
- **Q2a GT: ✅ RESOLVED.** Zenodo 15025832 publishes everything: per-lens
  PyAutoLens SIE θ_E (`modeling_lens_mass.csv`, 335 rows, mirrored to
  tables/q1_slde_mass_models.csv), the 2,584-candidate catalog with grades,
  and lens.zip = per-lens dirs each holding the VIS cutout FITS, an
  extra-galaxies MASK, and the full PyAutoLens result JSONs. All on the
  cluster (~/cosmos_acs/q1_slde/lens/lens/, 336 dirs). LEMON's 354 vs 335:
  remainder presumably Rojas high-σ_v systems — find that release or
  reconcile/disclose at eval.
- **Q2b format inspection**: FITS pixel scale/size/units; info.json contents;
  mask conventions. THEN preprocessing to the 128px @ 0.05″ grid the g4
  Euclid arm expects (same 2× upsample as euclidise.py output side).
- **Q2c gates BEFORE eval (C17): MEASURED 2026-07-13.** 10-lens pilot passes
  three-stretch previews; aperture-vs-catalog flux uniform ±0.09 mag.
  vs euclid_slacs_images_g3.h5: peak/sky 0.73× (compatible) but absolute
  skyRMS 0.09× (≈2.6 mag; ZP 24.6-vs-23.9 explains only 1.9× — flux-unit
  convention) and Q1 cutouts are background-subtracted vs the bench pedestal.
  **NEXT: rescale ruling (skyRMS-matched ×~11 vs ZP-derived) + pedestal
  handling, then rerun the gate to confirm distributions align. No eval
  before that.**
- **Q2c2 NORMALIZATION SWEEP (Nurkyz ruling 2026-07-13; Option A — rescale
  the Q1 cutouts to the training domain; NO retraining/Option B):** the
  measured ~11× factor is NOT applied blindly.
  (i) Tuning subset: the 10-lens pilot set, extendable to a random 20%
  split (seeded, logged) if 10 is too noisy. These lenses are BURNED for
  tuning — Q2e reports full-sample AND excluding-tuning rows (disclose).
  (ii) Sweep ≥12 combos — **EXECUTED 2026-07-13 (job 47907, logged):
  factor response nearly flat (RMSE 0.414→0.385 over 1.9–14×), pedestal
  zero effect; nominal winner f14_none is grid-edge noise driven by one
  lens's FJ response; C17 re-check passes at f11.4 (skyRMS 1.05×, peak/sky
  0.92×) and fails at f14 (1.29×). RECOMMENDED FREEZE: f11.4 × no-pedestal
  — ruling pending. Per-lens: 5/9 within ±12%; one −67% outlier
  (102018666, suspect GT or faint-arc miss → Q2d case).**
  (iii) FREEZE the winning normalization; re-run the C17 gate to verify
  skyRMS/peak-sky distributions align with the benchmark.
  (iv) Only then ⛔ Q2e (eval #24), EXACTLY ONCE, full Q1 set.
- **Q2d population-shift audit (disclose)**: Q1 deflectors not all LRGs; θ_E
  skews small; z_l higher than SLACS. Report training-support overlap; flag
  out-of-support systems in the per-lens table.
- **Q2e ⛔ eval #24 — DONE 2026-07-13, MISS (the headline negative
  finding):** primary −0.244/0.428/R² 0.00/fail 64%; best row r50_3 +0.25;
  bar not approached (P=0.00). θ_E-dependent compression −15%→−34%,
  population-driven (Q1 deflectors half the benchmark contrast; FJ channel
  suspect); preprocessing exonerated (previews clean, C17 matched, support
  97%, tuning-exclusion null). Frozen file evaluated ONCE (C18). NEXT
  DECISIONS (Nurkyz): (a) paper framing "operator transfers, population
  prior does not" (Q3 honesty box has real content now); (b) I9 DA retry
  trigger FIRED; (c) G1b mixed-population training as the physical fix —
  both feed the AR3/G1b regen already planned. Their-GT caveat stands
  (their mass-ϵ R²<0 on Q1; Sect. 7 real<sim admission).
- Optional bonus: 5 Perseus ERO lenses (Acevedo Barroso classical models).

### Q3 — paper integration
"One physical population model, three real-GT domains" section (native-HST
b_SIE / Euclidised-HST / real-Euclid-Q1) — the claim nobody else can make.
Honesty box: their arc-radius GT 13/60; our Euclidiser = disclosed
reimplementation; own-pipeline-GT caveats cut both ways.

## 2R. G5 ROMAN program (researched 2026-07-13 from arXiv:2506.03390,
   Wedig et al. 2025; supersedes the one-line item 5 above)

**UPDATE 2026-07-14 (evening) — RULING: OPTION C, both paths, 3-band in
scope. G5a DONE (both Rung 0 sets banked + decoded: 11,160 lenses × 3
bands F106/F129/F158, 91×91 @ 0.11″ DN/s; submission = CSV ID/theta_E/
theta_E_sigma emailed to Stony Brook, hidden-label scoring; Rung 1 live
since May 2026 = substructure era).**

- **PATH A (their-train) — LAUNCHED 2026-07-14 (run_g5a_chain.sh, nohup,
  disconnected-safe):** convert (128px zoom grid, 1000-lens seeded
  challenge-val split) → quick-train gate (10-ep cnv2 f106, val_MAE<0.25)
  → wave 1 = 6 f106 members (cnv2_3 @3e-4 + r50_3 @1e-3) → wave 2 = same
  6 as 3-band (--in_chans 3; trainer patched, .bak_g5). θ filter opened
  to [0.10, 3.70] (24% of the set sits below the old 0.45 floor).
  Selection on the challenge-val split ONLY; the unlabeled test set gets
  model contact exactly once per approved submission.
- **PATH B (our-population G5c):** InstrumentConfig must match the
  CHALLENGE convention (0.11″/px, DN/s, 610 s romanisim L2 — not the
  paper's 146 s). PSF source decision first: mejiro Zenodo (20346761)
  PSF products if present (no install), else STPSF (pip install — needs
  Nurkyz approval). Manifests: GEN4 population + EXTENDED support
  (θ_E 0.15–3.7, σ_v to ~120, z_l to ~1.5; the #24 population lesson) +
  C15 corrections + C10 spec block (hard gate). Feeds off the G1b broad
  fetch (running).
- **G5d scoring:** both paths on challenge-val first → Nurkyz reviews →
  submission CSVs (theta_E_sigma from ensemble+TTA, conformal on the val
  split — C11 machinery) → NURKYZ sends the email (outward-facing).

**The opening:** Wedig et al. release **16,214 simulated Roman HLWAS lens
images on Zenodo (Wedig & Daylan 2024) WITH per-lens θ_E ground truth**, in
two versions each (synthetic + realistic WFI detector effects), 10.01″
cutouts @ 0.11″/px, WebbPSF PSFs, HLWAS bands F106/F129/F158/F184 @ ~146 s.
Their paper trains NO ML and explicitly offers the products "to support…
training neural networks" — the first-ML-on-the-public-Roman-benchmark slot
is open. Their population: θ_E mostly 0.3–1.5″, σ_v 229±51, z_l 0.57±0.27
(skews SMALLER than SLACS; partially below our 0.45″ training floor).

**Ruled strategy — do BOTH, in this order (answering "score on their images
or another way?"): their images become our EXTERNAL Roman benchmark; our own
G5 rendering stays the training side.** That yields the unique claim: "the
only θ_E estimator validated on real GT in two domains AND scored on the
independent public Roman sim benchmark — Roman-ready weights released."
Scoring on their images alone (without G5) would test domain adaptation to
their rendering choices (parametric Sérsic deflectors/sources — a different
philosophy from our real-stamp population) with no Roman-matched training;
G5 alone would leave the Roman claim sim-validated only by ourselves.
External-benchmark caveat to disclose (cuts both ways, same as Q2): their GT
is analytic sim truth (lenstronomy; subhalo perturbations included), not
real-lens GT — but it is INDEPENDENT of us, which is the point.

- **G5a — pull + freeze the Wedig benchmark**: Zenodo dataset (quota check
  first; 16k cutouts, modest), format inspection (q2b pattern), extract
  per-lens θ_E/SNR/band structure, mirror GT to tables/. Files frozen at
  creation (C18). Population-support audit vs our [0.45, 2.3]″ (Q2d
  pattern): report in-support subset + full, flagged.
- **G5b — zero-shot baseline (cheap, before any training)**: existing
  G4/g4ar models on their REALISTIC F106 and F129 images, preprocessed to
  our grid (0.11″→0.05″ resample; C17-style flux gate vs our training arm
  FIRST — their units/zodi background differ). ⛔ logged eval. This row
  quantifies how far pure cross-domain transfer gets — whatever it shows,
  it motivates G5c.
- **G5c — G5 Roman InstrumentConfig + training arm**: WFI 0.11″/px, STPSF
  (= WebbPSF renamed) PSF models, HLWAS 146 s depths, zodiacal+stray+thermal
  background per their §3 recipe — the THIRD rendering of OUR self-consistent
  population (same manifests, same physics; C15 corrections + C10 spec block
  mandatory). Pilot → gates (incl. AR0) → 100k → train → sim-val.
- **G5d — ⛔ Roman headline eval**: G5-trained ensemble on the frozen Wedig
  realistic set, both bands; LEMON-convention table + bootstrap; per-θ_E
  bins with the <0.45″ out-of-support rows flagged. Optional secondary:
  their synthetic (noise-free) version isolates detector-effect sensitivity.
- **G5e — multiband extension (staged, NOT gating the paper)**: HLWAS is
  natively 4-band and their release includes all bands — a 4-channel
  (F106/F129/F158/F184) input variant trained on the same manifests answers
  "does color help θ_E?" on the same external benchmark. But our REAL-GT
  domains (HST F814W, Euclid VIS) are single-band, so multiband can only be
  sim-validated for now → frame as a Roman-readiness ablation/paper-2 arm,
  single-band G5 first.

Refs to carry: Wedig et al. 2025 (arXiv:2506.03390), SLSim (LSST-strong-
lensing/slsim), mejiro v1.0.0 (AstroMusers/mejiro), Zenodo Wedig & Daylan
2024 (locate DOI at G5a).

## 3. AR ladder (arc realism; full table archived in
   DATA_OVERHAUL_GEN4_PLAN §AR)

| item | what | status |
|---|---|---|
| AR0 | quantitative arc-realism gate | baseline DONE (sim/real gap SMALL); wire into every pilot chain (C14) |
| AR1 | arc shot noise, native arm | DONE — in g4ar, evaluated #22 (C13): SLACS-aggregate null, helps faint-arc/S4TM + confidence gating |
| AR2 | ΔPA↔γ_ext coupling | DONE — in g4ar, evaluated #22 (C1): same reading as AR1 |
| AR3 | mass multipoles m=3,4 anchored to each stamp's MEASURED isophotes (novelty) | NEXT after G1b measurement (C5); pilot + AR0 gate |
| AR4 | source knots / HUDF deep-morphology tier | only if arc gate still shows a gap after AR3 (C7) |
| AR5 | companion MASS (FJ-scaled SIS) | conditional, after AR3 |
| AR6 | slope–σ_v coupling | cheap honesty, bundle with a regen |
| AR7 | LOS structure | DEFERRED until a θ_E-label-convention ruling (C6) |
| AR8 | TNG convergence maps (professor §6.1) | paper-2 / ablation (breaks per-observed-galaxy self-consistency) |

## 4. Inherited open items (deduped from ALL archived plans — nothing else
   from them remains undone; if you think something is missing, check the
   archive and ADD IT HERE)

| id | item | origin | status/next |
|---|---|---|---|
| I1 | Cao per-lens θ_E comparison: email sent chain (C8) OR re-run public TinyLensGpu on the 63 lenses ourselves (~3 min/lens GPU), labeled as our reproduction | MASTER D2 / PATHB Q7 | email pending; fallback ready to build |
| I2 | Two-stage hybrid "system" row: σ-gated fallback CNN → TinyLensGpu init at CNN prediction; headline = full-sample failure 15% → X% at ~ms average cost; doubles as the I1 fallback | PIVOT L4.2 | open, paper-value high |
| I3 | Aux heads (θ_E + e1/e2 + lens-light Re/n/m): labels flow through the pipeline; NEVER TRAINED (deferred at REB). LEMON's n_lens R²=−0.47 and Q1 mass-ϵ R²<0 are soft targets; real-GT for ϵ exists (Bolton q/PA) | PIVOT L2/E4, GEN4 keeps | open; train on GEN4/G1b data when grid slots free |
| I4 | σ calibration: conformal on a real-disjoint pool (RAW coverage still under) | C11 | open — needs pool design |
| I5 | Confirmation set: never-evaluated real lenses (Bolton grade-B / BELLS), evaluated EXACTLY ONCE at paper time (benchmark-adaptivity defense; 21+ logged evals make this cheap insurance) | PIVOT fresh-eyes #2 | open — assemble with Nurkyz before submission |
| I6 | GT-error ceiling analysis: best-achievable RMSE/R² given published b_SIE errors (converts "gap to X" into "distance from ceiling") | PIVOT fresh-eyes #3 | open, analysis-only, cheap |
| I7 | Inference-cost measurement (ensemble × TTA forwards/lens) for the speed claim | PIVOT chores | open, trivial |
| I8 | Ablation table for the paper: pre-GEN4 causal bundle exists (backdrops ≫ prior ≈ PSF > pool ≈ DA ≈ companions ≈ lens light, evals ≤ #11); DECIDE: report as-is (historical recipe) vs re-run key rows (prior, PSF, backdrop) on the GEN4 recipe | MASTER D1 / PATHB Q6 | decision with Nurkyz at paper time |
| I9 | DA retry on the GEN4-era model (pre-Path-B DA was NULL vs parametric light; sim-to-real DA on real GT is still unclaimed in the literature) | MASTER D4 / PATHB Q4 | optional second pillar; only if a real gap remains |
| I10 | TNG-κ mixed-mass arm (professor) = AR8 | MASTER R2.2 / PATHB Q14 | paper-2/ablation |
| I11 | BELLS GALLERY / COWLS JWST cross-instrument generalization | MASTER D5 / PATHB Q12 | follow-up paper |
| I12 | Universal inference loader (any FITS+WCS → model grid) — InstrumentConfig generation side is DONE via GEN4 P5; the inference-side loader is what Q2b partially builds | PIVOT R1 | fold into Q2b, then generalize |
| I13 | Companion realism v2 (speckle texture) | PATHB P8 | dormant — re-judge on current side-by-sides |
| I14 | Release package: benchmark ("SLACS-102"), weights, per-lens predictions, eval protocol → Zenodo DOI (website REMOVED by ruling) | PIVOT P4 | at submission |
| I15 | Brian: authorship + GEN4 direction paragraph | everywhere | Nurkyz, overdue |
| I16 | Emails: Bergamini (HST2EUCLID code), Cao/Li (per-lens) still unsent; Busillo SENT | C8 | Nurkyz; nudge Busillo ~07-20 if silent |
| I17 | Etherington gold-subset reporting alongside full benchmark | PATHB Q8 | verify it's in the eval protocol; add if not |
| I18 | Sam PSF ask | old standing item | RETIRED (superseded by STScI focus-diverse ePSFs + Q1 VIS PSF) unless Nurkyz revives |

## 5. Paper assembly (continuous; PAPER_DRAFT.md §4.0 has the tables)

- §4 rewrite around the GEN4 result + causal chain (prior → realism → physics
  self-consistency → real PSF → selection trade-off).
- Q3 three-domain section when Q evals land; LEMON six-column table if I3
  (aux heads) trains in time.
- Reliability: conformal σ (I4), coverage figure, ρ(σ,|err|), failure-rate CIs.
- Negatives-as-findings: Euclidisation ≠ fix; deflector-light null; DA null;
  ensembles/recentering null; flatness-vs-FJ incompatibility (tempering).
- Comparisons: Cao (same-lens, conventional), LEMON (both domains, same
  lenses where resolvable), Gawade/HOLISMOKES X/STRIDES (context, with their
  GT caveats — see LITERATURE.md 2026-07-13 sweep for exact numbers).
- Success bars (all already met at eval #21 — protect them): median ≤ ±5%,
  R² > 0.5 native, fail ≤ 15%, NMAD ≤ 0.06″.

## 6. Standing rules (full text in CLAUDE.md — this is the checklist)

- One config change → 200-image pilot → gate_stage0 + AR0 + FJ gate +
  side-by-side (three stretches) → only then scale.
- Benchmark evals ONLY at ⛔ human checkpoints, logged with the running count
  (now 21). New real-lens files (real_lemon31, Q1 cutouts) are frozen test
  data from birth (C18).
- Model/recal selection on sim-val ONLY. Seed-ensembles or seed-averages with
  spread in every table.
- COMMITMENTS.md reconciled at every ⛔ and before any full generation.
- Quota check before every fetch/generation (150 GB; mast_cache purges).
- csh login → bash -lc; SLURM needs --gres=gpu:1 always; QOS cap 8 → waves;
  monitors report, the session submits; push git at every milestone.
