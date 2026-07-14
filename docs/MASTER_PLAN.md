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
3. **G1b library build**: Nurkyz visual prune of the 800-target fetch →
   measurement pass INCLUDING isophote a3/a4 (C5, feeds AR3) → C15a/b σ_v
   corrections (f_SIS = σ_fiber/0.948, +7% intrinsic scatter) in the next
   manifests; C15c validation figure (analysis-only) can be made immediately.
4. **AR3 isophote-anchored multipoles** (one pilot, gates incl. AR0 arc gate)
   → regen with the BIG G1b library + C15 corrections → ⛔ eval pair
   (native + Euclid). Expect less tempering (stronger training FJ ρ).
   **HARD GATE (C10, Nurkyz ruling 2026-07-13): the AR3 pilot script must
   verify `<manifest>.physics_spec.json` exists and contains every physics
   axis (incl. multipoles=ON) and FAIL IMMEDIATELY otherwise — AR3 does not
   launch without it.** Generator side shipped 07-13 (g2_make_manifest.py
   prints the block + writes the sidecar).
5. **G5 ROMAN** — full focus after 4; FULL PROGRAM NOW IN §2R (researched
   2026-07-13): Wedig et al.'s 16,214 public Roman sims WITH θ_E GT become
   our external Roman benchmark (zero-shot baseline first, then the
   G5-trained arm); own InstrumentConfig rendering stays the training side;
   multiband as a staged non-gating extension.
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
  J1619 0.50″, J2228 0.60″; GT = power-law+shear, disclose). COSMOS 5 = the
  spectroscopically-confirmed subset of Faure 2008 (VizieR table pulled; pick
  the spec-z 5). ACS 13 = spec-confirmed subset of Pawase 2014 Table 3 (not
  on VizieR — extract from paper; NO true θ_E, dual-report vs arc radius or
  exclude, flagged). SLACS 29: NOT uniquely derivable — Ring=32,
  Ring∩σ_good=31 (tables/bolton08_table5.csv), Auger-photometry cut RULED OUT
  (all 31 have I-band). Routes: (i) Busillo reply (email SENT ~07-12/13;
  nudge ~07-20), (ii) digitize their Fig. 9 (z_lens, log θ_E) 29 points and
  match against the 63 Bolton pairs. Until resolved: 62-superset row
  (defensible; already beats their aggregate). Gate: any claimed 29-list must
  reproduce their Fig. 9 scatter. Deliverable: tables/lemon60_targets.csv
  (skeleton exists).
- **Q1b imaging (31 non-SLACS)**: MAST F814W fetch (g1/g1b driver pattern;
  COSMOS 5 may be in local COSMOS tiles — check first) → benchmark-grid
  cutouts → files FROZEN at creation (`real_lemon31_*`, C18) → euclidise
  (real Q1 VIS PSF) → three-stretch previews on ALL before any eval. Pilot 3
  lenses (1/subsample) first.
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

**UPDATE 2026-07-14 — G5 is the ACTIVE phase (Nurkyz ruling) and the slot
got better: the mejiro team now runs a formal "Roman Strong Lens Data
Challenge" (roman-data-challenge.readthedocs.io). Rung 0 v2.1 (Zenodo
21200584, 1.22 GB h5 + viewer notebook) is downloading to
~/cosmos_acs/roman_dc/. G5a now = inspect Rung 0 format + challenge rules
(deadlines, metrics, submission format) FIRST — entering the challenge
beats privately scoring their 2024 release. Rest of the ladder unchanged.**

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
