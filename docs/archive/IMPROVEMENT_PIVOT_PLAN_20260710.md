> **ARCHIVED 2026-07-13.** Superseded by docs/MASTER_PLAN.md (the single live plan).
> All undone items were carried into MASTER_PLAN.md at archive time. Historical record only.

# IMPROVEMENT / PIVOT PLAN — 2026-07-10 (rev 2, after Nurkyz's rulings)

Status: ADOPTED DIRECTION (Nurkyz 2026-07-10): beat-LEMON-on-every-axis is an explicit
goal; work staged for minimum time/effort; website idea REMOVED; Roman endorsed by
professor. DECISIONS_LOG.md remains authoritative; log each stage's outcome there.

## STATUS AUDIT (2026-07-10 evening — update in place)

| Item | Status |
|---|---|
| §0 LEMON Table 3 verification | ✅ RESOLVED (Nurkyz, from the paper; logged) |
| L0.1 tail forensics | ✅ DONE — B3 REJECTED; tail = small-θ_E prior-pull (selection-skewed prior, median 1.609″); NOT benchmark-intrinsic (0 lenses fail all native+euclid) |
| L0.2 bias forensics | ✅ DONE — benchmark + sim-val (job 47433): +7–8% bias at θ_E<0.9″ in-distribution; B4 survivor-gradient real but secondary |
| L0.3 R² sample math | ✅ DONE — NMAD win P=0.75 (not decisive); cross-sample R² near-meaningless (report same-sample only); fail≤12% ⇒ RMSE≤0.14 |
| L0.4 emails (HUMAN) | ◐ drafted (EMAIL_DRAFTS_20260710.md) — ⏳ Nurkyz to send |
| L1 members (5×2 scratch + 2 tinit) | ✅ DONE (jobs 47434–47443, 50 min; all clean, seeds distinct) |
| L1 arbitration + frozen recal | ✅ DONE — all12 recommended (sim-val MAE 0.0839 vs pair 0.0851); b=+0.0028″, s=0.862 frozen in l1_recal.json; E5 tinit = in-dist NULL (kept as diversity) |
| ⛔ eval #15 | ✅ DONE (count 15) — L1 NULL on aggregates (fail 31→27%, conf-half 13→10%, rest flat/worse); bias proven structural; NEW seed-variance finding (R² +0.01…+0.33 across seeds) → paper paragraph |
| L2+L3 (RESTRUCTURED post-#15, see §2b below) | ☐ ONE combined regeneration: θ_E rebalance + aux-head labels + provenance fix; then heads-vs-no-heads control on sim-val; ⛔ eval #16 for the winner. Awaiting Nurkyz go |
| E3 VIS PSF | ☐ after the combined regen (kept separate — one image-affecting change at a time) |
| L4 closers | ☐ blocked on email replies / eval #15 outcome |
| Track N native back-port | ☐ NOT STARTED (next parallel item; pilot ≤200 img can start anytime) |
| Track R InstrumentConfig refactor | ☐ NOT STARTED (training-downtime task) |
| Track P housekeeping | ◐ CLAUDE.md monitor rule ✅ (added 2026-07-10); repo synced+pushed ✅ (6883ea3); merge-provenance patch ☐; stale-doc consolidation ☐; PAPER_DRAFT refresh ☐; shard-backup deletion ⏳ Nurkyz |
| GitHub | ✅ https://github.com/nurkyzaz/strong_grav_lensing (layout convention in CLAUDE.md) |

Deviations from plan: none of substance. Two additions beyond plan: sim-val bias probe
(l0_simval_bias.py) executed as part of L0.2; ssh-banner/tar pitfall documented in
CLAUDE.md. Known deferred bug-fixes: merge script provenance-column drop (fix BEFORE
the next generation run — L3 depends on it).

---

## 0. LEMON Table 3 — RESOLVED (Nurkyz verified from the paper, 2026-07-10)

The 2026-07-09 LITERATURE.md values were CORRECT; this session's A&A auto-fetch had misread
rows. Verbatim record (Euclidised real HST lenses, cumulative, no filtering):

| Metric | θ_E (″) | ϵx | ϵy | Re,lens (″) | n_lens | m_lens |
|---|---|---|---|---|---|---|
| Bias (μ) | −0.03 | 0.00 | 0.00 | 0.03 | −0.35 | 0.01 |
| RMSE | 0.14 | 0.07 | 0.04 | 0.18 | 1.05 | 0.30 |
| NMAD | 0.11 | 0.04 | 0.03 | 0.06 | 1.10 | 0.21 |
| R² | 0.53 | 0.87 | 0.88 | 0.64 | −0.47 | 0.69 |

Implications: (a) our ensemble NMAD 0.084 beats their 0.11 — stands; (b) the remaining θ_E
axes to close: |bias| 0.062→≤0.03, RMSE 0.208→≤0.14, R² +0.33→≥0.53; (c) their n_lens R² is
NEGATIVE (−0.47) and Re is biased above 1″ (their own admission) — with aux heads (E4) we can
compete on ALL six columns, and some are soft targets. Facts already verified for the paper:
their training mocks are detectability-selected (S/N>10) → our visibility selection is
methodologically parallel; they publish NO σ-gated real-lens metrics and NO per-lens
predictions; their stated limitation ("Platt scaling could be not robust when switching to
real data") is exactly what our σ-transfer result answers.

---

## 1. Professor's feedback, interpreted (2026-07-10)

"Keep the code flexible for any observations" = NOT an architecture change request. It is a
software/pipeline directive: the training generator and the inference stack should be
instrument-agnostic — instrument specifics (pixel scale, PSF source, zeropoint, noise model,
band, cutout size) live in a config object, so targeting Euclid / Roman / LSST / any new
observation is a config swap, not a rewrite. He also endorsed the Roman direction.

Concrete implementation (Track R below):
- `InstrumentConfig` abstraction in the generation pipeline (we are already ~80% there:
  PSF bank, noise draws, backdrops, Euclidiser are swappable pieces — formalize it).
- Inference-side loader that accepts ANY cutout (FITS + WCS) and resamples/normalizes to
  the model grid; the m3 lineage is already scale-conditioned, so feeding pixel scale as
  conditioning input is a natural, minimal extension (one input, not a new architecture).
- Optional (only if multi-domain training happens): instrument-metadata conditioning
  (pixel scale + PSF FWHM) so ONE checkpoint serves several observation domains.
This directly serves the "first CNN evaluated on real lenses across domains" claim
(native HST 102 + Euclidised + real Euclid Q1 + later Roman).

---

## 2. Campaign L — BEAT LEMON ON EVERY AXIS (Euclid arm)

Per-axis gap → lever mapping (current = eval #14 ensemble):

| Axis | Ours | LEMON | Gap driver | Levers (stage) |
|---|---|---|---|---|
| NMAD | **0.084** | 0.11 | — (won) | protect it (regression-check each stage) |
| |bias| | 0.062 | 0.03 | selection-survivor bias (B4) | L0 diagnosis → L1 sim-val recentering |
| RMSE | 0.208 | 0.14 | catastrophic tail (31%) | L1 ensembles, L2 aux heads, L3 VIS PSF/floor, L4 hybrid |
| R² | +0.33 | 0.53 | tail + sample composition | same as RMSE + L0 sample math + shared-29 |
| ϵ, Re, n, m | not predicted | see §0 | no aux heads yet | L2 (n_lens is their weak spot: R² −0.47) |

Integrity guardrail (standing, Nurkyz's own earlier ruling): we do NOT shrink or cherry-pick
our benchmark post-hoc. The legitimate "select better lenses" forms are: (i) the shared-29
SLACS table (their sample, their choice — email pending); (ii) sample-composition analysis
(their 60 mixes curated EELs/COSMOS — quantify what R²/RMSE our current per-lens errors
would give ON a sample with their θ_E variance); (iii) a validity scope DECLARED from
training-selection statistics BEFORE an eval; (iv) confident-subset columns clearly labeled
as our added gating (they have none). All four are honest; only silent post-hoc trimming is
banned.

### Stage L0 — analysis only, no training, no new benchmark passes (~1–2 days) [START HERE]
Runs entirely on EXISTING eval-#14 predictions + sim-val. Everything else is sequenced by
what this finds.
1. Tail forensics: failure-overlap matrix across v3 / pathb / euclid models (+ Cao's J0841);
   stratify real errors by post-degradation arc SNR and θ_E; test the B3 hypothesis that
   failures concentrate below the training selection floor (SNR 0.7 / extent 150).
2. Bias forensics: bias vs arc SNR / θ_E on sim-val and benchmark — confirm
   selection-survivor bias before correcting it.
3. R² sample math: recompute our metrics under their sample's θ_E variance; bootstrap CIs.
4. HUMAN (send today, longest lead time): LEMON email (29 SLACS names + HST2EUCLID code +
   Q1 per-lens predictions), Cao email (per-lens θ_E), Brian authorship.
Output: a one-page verdict — how much of the 31% tail is OOD-by-selection vs
benchmark-intrinsic — which decides L3's design.

### Stage L1 — model-side bundle, zero new data (~2–3 days, one ⛔ eval)
Batched deliberately (all training-side, no dataset change → attribution stays clean at the
dataset level; disclosed as a bundle):
1. Deep ensembles: 5 seeds × 2 archs on the existing Euclid-sel dataset (tails shrink,
   known effect; current ensemble is only 2 members).
2. E5 transfer-init: initialize from the best NATIVE checkpoint (cheap, likely helps).
3. Bias recentering + σ/conformal recalibration frozen on SIM-VAL ONLY (fixes the bias
   axis legitimately; disclose raw + recentered).
⛔ Eval #15: full LEMON-convention table. Expected: bias axis closed, RMSE/R² partially
closed, NMAD held.

### Stage L2 — aux heads on the SAME dataset (~3–4 days, one ⛔ eval)
E4: multi-parameter heads (θ_E + e1/e2 + lens-light Re, n, m) using the existing
ellipticity-label machinery + paltas/light metadata; orientation-aware augmentation
(the corrected e1/e2 transform — bug class already fixed once, reuse it).
Two payoffs: (a) auxiliary tasks regularize θ_E (LEMON's 7-param head plausibly explains
part of their stability); (b) we can then publish the FULL six-column table vs §0 — their
n_lens R² −0.47 and Re bias >1″ are beatable columns. Real-GT for ϵ exists via Bolton q/PA.
⛔ Eval #16.

### Stage L3 — dataset-side fixes, informed by L0 (~1 week, one ⛔ eval)
**L0 VERDICT (2026-07-10, see DECISIONS_LOG): B3 rejected — the tail is small-θ_E
prior-pull from the selection's θ_E-graded pass rate (selected training median 1.609″;
SLACS θ_E<0.9″ fails 62% with +29% overestimate). L3 priorities reordered accordingly:**
1. **θ_E REBALANCING of the selected training set (NEW #1):** oversample small-θ_E
   renders so the POST-selection θ_E distribution is flat (generation waves sized by the
   measured per-bin pass fractions 26/53/64/84%). This revisits the deferred
   "reweighting-vs-accept" decision WITH evidence; cost ≈ extra renders concentrated in
   the two small bins, not a full-size regeneration.
2. E3: real Euclid VIS PSF in the Euclidiser, BOTH sides (training degradation + benchmark
   degradation) — removes the biggest disclosed reimplementation gap.
3. Selection-floor change: NOT justified by L0 (faintest-prominence real lenses fail
   LESS than average) — dropped unless later evidence reopens it.
One regeneration (Euclidise-only reprocessing of existing renders where possible — the
native renders are unchanged, so this may be combine/euclidise/select reruns, NOT new
paltas generation → much cheaper than a full 100k regen; verify npy availability first).
⛔ Eval #17.

### §2b — POST-EVAL-#15 RESTRUCTURE (2026-07-10 evening; replaces the L2-then-L3 ordering)

Eval #15 closed the model-side avenue: ensembles, transfer-init, and recentering are
all measured NULLs against a bias that is structural (three independent confirmations:
benchmark θ_E-bin table, sim-val bias probe, common-mode ensemble bias). Consequence:
stop spending on model-side levers; go straight at the dataset. To avoid paying two
regenerations and two training cycles:

**ONE combined regeneration** (needs Nurkyz go + merge-provenance patch FIRST):
1. θ_E rebalancing: size generation waves by the measured per-bin pass fractions
   (26/53/64/84%) so the POST-selection θ_E distribution is flat. This is the L0-
   diagnosed fix for the +0.09″ bias and the 62%-fail small-θ_E bin.
2. Carry the aux-head LABELS (mass e1/e2 + lens-light Re/n/m from paltas metadata)
   through combine→euclidise→select→merge. Labels don't change images — no new
   realism variable; the merged gate stays a one-change comparison (rebalance).
3. Fix the merge provenance-column drop in the same pass (bug queued since eval #14).
Then: train BOTH θ_E-only and θ_E+aux-heads models on the new dataset (5 seeds each,
seed-honest); arbitrate heads-vs-no-heads on SIM-VAL; ⛔ eval #16 evaluates the winner
(+ the loser as a derived column only if its predictions are made in the same pass).
E3 (real VIS PSF) stays AFTER this — it changes images, so it must be its own gated step.

Reporting rule adopted from the seed-variance finding: all future eval tables report
seed-ensembles or seed-averages with spread, never single seeds.

### FRESH-EYES REVIEW (2026-07-10 night, requested by Nurkyz; full reasoning in session)

New findings, ranked:
1. **S4TM deflector-prior mismatch (new hypothesis for the persistent S4TM +8–13%
   bias):** the deflector stamp library AND lens_light_empirical.csv are built from
   SLACS-parent LRGs; S4TM deflectors are lower-σ_v (smaller, fainter, smaller θ_E).
   Our sims may systematically over-glare S4TM-like systems. Diagnostic before fixing:
   compare S4TM benchmark deflector photometry vs the training prior. Candidate fix:
   population-conditioned deflector prior. (Would also sharpen the "S4TM =
   generalization test" framing.)
2. **Benchmark-adaptivity defense for the paper:** 16 logged evals steer development
   (physics-motivated, sim-val-selected — but a reviewer can still ask). Strongest
   answer: assemble a small CONFIRMATION SET of never-evaluated real lenses (e.g.
   Bolton grade-B SLACS beyond the frozen 102, or BELLS) and evaluate the final model
   on it EXACTLY ONCE at paper time. Cheap insurance; decide with Nurkyz.
3. **GT-error ceiling analysis:** b_SIE has its own uncertainty; at NMAD 0.084″ (~7%)
   we may approach the floor for some lenses. Compute the best-achievable RMSE/R²
   given published b_SIE errors → converts "R² gap to LEMON" into "distance from the
   ceiling". Add to the L0 sample-math script (analysis-only).
4. **Mass–light alignment realism (unlisted ablation axis):** with real deflector
   stamps, mass e1/e2 is drawn INDEPENDENTLY of the stamp's light orientation —
   deliberate (anti-shortcut) but physically wrong (real lenses align). May matter for
   aux-head e1/e2 and marginally for θ_E. Log as a candidate ablation, not a fix.
5. **Native arm drift:** all recent effort is Euclid-arm; the paper's HEADLINE is
   native-HST. Track N (population back-port; no selection needed natively → no
   selection-skew issue) is still the largest untapped lever. Schedule right after
   eval #16.
6. Chores surfaced: PAPER_DRAFT stale since eval #9 (update through #16);
   measure and report the REAL inference cost (ensemble × TTA = 40 forwards/lens);
   confirm the three emails went out (shared-29 table blocks on it).

### Stage L4 — closers (only for axes still short after L3)
1. Shared-29 per-lens head-to-head (when names arrive) — likely flips RMSE/R² by itself if
   the tail is sample-composition-driven.
2. Two-stage hybrid: σ-gated fallback to TinyLensGpu initialized at CNN prediction —
   reported as a separate "system" row (different method class), doubles as the Cao D2
   reproduction. Headline: full-sample failure 31% → X% at ~ms average cost.
3. Mass-model realism arm (professor R2.2, TNG-κ mixed-mass) if the residual tail looks
   like model mismatch — also becomes the 6th ablation axis.

---

## 3. Track N — native-HST spine (parallel; the paper's primary result)

Runs in parallel with Campaign L because it shares no compute bottleneck except quota
(schedule the 100k regen while L1/L2 train, delete superseded sets first).
N1. Back-port the population program to the native arm: HighSB selection, Newton mags,
    SLACS z_source, 1px jitter, screened backdrops — the levers that halved Euclid-arm NMAD
    were never applied to the native primary (v3 still trains on the old population).
    Pilot (200) → gates + side-by-side → ⛔ → 100k regen → both archs + 5-seed ensembles →
    ⛔ native eval. Biggest untapped native lever; native numbers are the paper's headline.
N2. Native tail forensics come free from L0 (same scripts, native predictions).

## 4. Track R — flexibility + cross-domain (professor's directive; feeds paper 1 AND 2)

R1. InstrumentConfig refactor + universal inference loader (§1). Small, do during L1/L2
    training downtime.
R2. Real Euclid Q1 zero-shot (~250 grade-A lenses): run the existing Euclid-arm model on
    ACTUAL Euclid cutouts through the R1 loader. No numeric GT → report per-lens concordance
    with LEMON's Q1 predictions (if released/obtained) + the few conventionally modeled
    systems. Cheap, big reviewer appeal, completes the "real lenses across domains" claim:
    native HST (102, real GT) + Euclidised (102) + real Euclid (~250). → paper-1 section.
R3. Roman arm (professor-endorsed): Roman config via R1 (public Roman PSF models, HLWAS
    specs), validate by Roman-ising the real-GT benchmark exactly like HST2EUCLID. Launch
    is ~Oct 2026 — timed right for paper 2 (or a short letter). Do NOT let it block paper 1.

## 5. Track P — paper assembly (starts now, continuous)

P1. Housekeeping batch (from rev-1 §1 B6): shard-backup sign-off + deletion; merge
    provenance patch; PAPER_DRAFT updated through eval #14+; stale-doc consolidation;
    CLAUDE.md gains the "monitors report, the session submits" rule.
P2. D1 ablation bundle (prior spine, PSF, backdrop, ePSF pool) + population-realism as a
    new ablation axis — batched evals, quota-disciplined.
P3. Reliability assets: conformal layer, coverage figure, ρ(σ,|err|), failure-rate CIs.
P4. Framing locked (rev-1 §5 stands): two-domain structure, negatives-as-findings
    (Euclidisation ≠ sim-to-real fix; deflector light null; DA null), reliability-as-product,
    speed/system vs Cao, HST-as-stress-test-for-Roman. Release package = benchmark
    ("SLACS-102"), weights, per-lens predictions, protocol (Zenodo DOI). [Website: REMOVED
    by Nurkyz's ruling 2026-07-10 — release artifacts only.]

---

## 6. What runs when (minimum-time schedule)

Week 1:  L0 (days 1–2, local/analysis) ‖ emails out day 1 ‖ P1 housekeeping ‖
         N1 pilot on cluster (small) ‖ R1 refactor design.
         Then L1 training (cluster GPU) ‖ N1 100k regen (cluster CPU — different queue
         pressure, quota-checked) → ⛔ eval #15 (L1) at week's end.
Week 2:  L2 aux-head training ‖ N1 native training → ⛔ evals #16 (L2) + native.
         R1 refactor lands during training downtime.
Week 3:  L3 (Euclidiser VIS-PSF reprocess + floor decision) → ⛔ eval #17 ‖ R2 Q1 zero-shot
         through the new loader ‖ P2 ablation generation starts.
Week 4:  L4 closers as needed (shared-29 if names arrived; hybrid system row) ‖ P2 ablation
         evals batched ‖ P3/P4 writing sprint.
Paper 2 seed (post-submission): R3 Roman + cross-instrument + population-level demo.

Rules unchanged: one dataset change at a time; gates before scale; ⛔ evals with Nurkyz,
counted; sim-val-only selection/calibration; quota checked before every regen.
