# DECISIONS LOG

Chronological record of decisions, dead ends (with reasons), and pivots. Newest at top.
Corrections/retractions are logged explicitly rather than silently edited.

---

## 2026-07-08 (cont.) — PATH B pilot PASSES both gates (LRG deflectors + radial taper); full generation LAUNCHED

**LRG deflector library:** `build_deflector_from_lrg.py` on the 84 fetched non-lens LRG cutouts
→ 72 clean centred ellipticals (dropped 12 edge-on/faint via moment axis-ratio q<0.55). Preview
(`da_pool_inspection/lrgdefl_lib.png`): smooth SLACS-like ellipticals, real HST PSF.

**Pilot 1 (Tukey/square taper):** all numeric gates PASS (sky-RMS 1.03, peak/sky 1650 in real
band 492-1798, θ_E range; acceptance 0.98) but side-by-side showed a faint rounded-SQUARE halo
from the separable Tukey window's square envelope → OOD cue. FIX: radial (circular) taper
(1 inside 0.33·n, cosine roll-off to 0 by 0.48·n).

**Pilot 2 (radial taper): PASSES BOTH GATES.** Numeric: sky-RMS 1.01, peak/sky 1760, θ_E range
all PASS. Visual (`da_pool_inspection/real_vs_pathb_pilot_v2.png`): square halo gone; deflector
light fades circularly and naturally; SIM deflectors are REAL ellipticals (real morphology, colour
gradients, PSF) visually matching the real SLACS deflectors — the whole point of Path B. Minor:
our LRGs skew slightly round (q>0.55 selection) vs the real spread; acceptable (real light).

**Full Path B generation LAUNCHED** (`generate_pathb.sbatch` + `submit_pathb.sh`, 3 resilient
waves): arc-only paltas (`config_lensfusion_acs_pathb_nonoise.py`) + real LRG deflector light
(brightness-matched) + companions + real backdrop + calibrated noise. → `paltas_shards_pathb/`
100k train + 5k val, seeds 701+/1101+ (disjoint from v1/v2/v3). Then merge + gate + train
InceptionNeXt (NLL, primary) + ResNet (comparison) → eval #10/#11. NLL head + scale conditioning
retained; benchmark untouched.

## 2026-07-08 (cont.) — PATH B started: COSMOS-morphology deflector source ABANDONED → non-lens LRG cutouts (Nurkyz ruling)

**Goal:** replace the parametric Sérsic lens light with REAL elliptical-galaxy cutouts as the
foreground deflector, keeping paltas for the lensing (arc-only render + valid SIE θ_E label).
Pipeline built: `config_lensfusion_acs_pathb_nonoise.py` (removes lens_light + cross_object →
arc-only), `hybrid_combine.py --deflector_stamps` (pastes a real elliptical centred, brightness-
matched to a draw from the real-SLACS deflector mag distribution `lens_light_empirical.csv`,
ZP 25.94, small centre jitter; provenance in `deflector_index`/`deflector_mag`). NLL head + scale
conditioning unchanged.

**Deflector SOURCE — first attempt ABANDONED:** `build_deflector_stamps.py` tried to carve smooth
ellipticals out of the COSMOS ACS F814W tiles by pixel morphology (size + concentration + moment
axis-ratio + asymmetry + clumpiness + peak-S/N cuts). Two rounds of previews
(`da_pool_inspection/defl_test*_preview.png`): loose cuts let through edge-on disks / clumpy
irregulars; strict cuts yielded almost nothing AND still leaked 3/4 junk. ROOT CAUSE (not fixable
by tuning): single-band F814W has no COLOUR, so the red-sequence — the strongest early-type
discriminator — is unavailable, and COSMOS at z~0.5–1 is late-type-dominated. Nurkyz's call:
switch to a dedicated real-elliptical source (Option B). RETAINED for possible reuse but not the
Path-B source.

**Deflector SOURCE — adopted (Nurkyz choice = self-service):** NON-LENS LRGs from the SLACS/S4TM
parent samples. `build_lrg_deflector_list.py`: SLACS Lens=='X' (42) + S4TM Class 'E-*-X'
(early-type non-lens, 42) = **84 real massive early-type galaxies**, HST ACS F814W (same
instrument/band as benchmark → real HST PSF), CONFIRMED non-lenses (no arcs to contaminate the
deflector light), and grade-X ⟂ the grade-A benchmark by construction (re-checked: 0 name / 0
coord overlap with the frozen 62+40). This is the exact "non-lens LRG cutouts" MASTER_PLAN
foresaw — obtained self-service (no Sam dependency). Small library (~84) → rely on flip/rotate
augmentation; acceptable since the deflector is a nuisance the CNN sees through. Cutouts fetching
now via the DA-pool MAST pipeline (`fetch_real_lens_images.py --survey LRGDEFL`, login-node nohup;
cache to be purged after — quota discipline). Sam's set can swap in later with zero code change.

## 2026-07-08 (cont.) — ⛔ BENCHMARK EVALS #8 (InceptionNeXt/v3) & #9 (ResNet/v3): companion fix + new architecture, nuanced result

**Running count: 9.** Both v3 models (companion-injected data, NLL head, TTA). Sim-val: ResNet
MAE 0.0544/R²0.929, InceptionNeXt 0.0641/R²0.913 (both slightly higher-MAE than v2's 0.042 —
companion clutter makes the in-distribution task marginally harder, expected).

| model | SLACS med / R² / fail / conf-half fail | S4TM med / R² / fail / conf-half fail |
|---|---|---|
| v2 ResNet (NO companions) | −2.6% / **+0.27** / 23% / 6% | −1.8% / **+0.47** / 38% / 15% |
| v3 ResNet (companions) | **−0.9%** / +0.22 / 32% / 10% | **−0.0%** / +0.03 / 35% / 10% |
| v3 InceptionNeXt (companions) | **−0.4%** / +0.22 / **24%** / 10% | +3.1% / +0.02 / **32%** / 10% |

**Honest reading (no overclaiming):**
1. **Companions IMPROVED median bias** (both samples move toward 0%: SLACS −2.6→−0.9/−0.4,
   S4TM −1.8→0.0) — the clean-field OOD was inducing a small systematic bias; removing it
   re-centres predictions. Real, modest, good.
2. **Companions did NOT improve R²/failure** — SLACS R² flat within noise (+0.27→+0.22, N=62);
   S4TM R² dropped (+0.47→+0.02) BUT N=40 R² is high-variance and v2's +0.47 was likely partly
   lucky (its 16-84 was already wide). Net: field-companion realism was NOT the dominant driver
   of catastrophic failures — consistent with ablations + DA post-mortem all pointing at
   lens-light CONTENT, not field/style, as the residual gap.
3. **InceptionNeXt modestly beats ResNet on identical data**: SLACS failure 24% vs 32%, MAE
   0.137 vs 0.151, tighter 16-84 [−11,+7] vs [−17,+15]; R² tied (+0.22). A real but modest
   architecture win → adopt InceptionNeXt as the primary backbone (best-rounded: low bias,
   tight scatter, lowest failure, modern).
4. **Confidence-gating remains the robust headline**: confident-half failure = **10% on BOTH
   samples for BOTH architectures**; σ still predicts error (ρ +0.48…+0.76). The confident
   subset meets the ≲10% bar regardless of arch.

**Conclusion:** the two requested changes (companion realism + InceptionNeXt) delivered a
re-centred, tighter, modern model, but did NOT close the full-sample failure gap — which now
points, for the 4th independent time (ablations, DA, J0841 shared failure, companions), at real
deflector LIGHT (parametric-Sérsic limitation) as the one unaddressed axis → Path B is the
evidence-indicated next step. v2's higher S4TM R² flagged as likely N=40 noise, not a reason to
revert. Primary model → `einstein_cnn_v3_inceptionnext.pt`.

## 2026-07-08 (cont.) — v3 companion dataset generation LAUNCHED; InceptionNeXt backbone implemented (Nurkyz-requested)

**Nurkyz approved the v3 companion smoke → full regen launched.** `generate_stage3_companions.sbatch`
+ `submit_gen3.sh` (3 waves, resilient nohup+SLURM): v2 recipe (θ_E U[0.45,2.3], 88 real ePSFs,
joint lens light) + real companion injection (`source_stamps_clean.h5`, rate U[8,26], flux_pct 35).
→ `paltas_shards3/` (100k train + 5k val, seeds 501+/901+ disjoint from v1/v2). Job 47135 etc.

**InceptionNeXt implemented (arXiv:2303.16900), replacing ResNet per Nurkyz.** Self-contained (no
timm), faithful to sail-sg/inceptionnext: `InceptionDWConv2d` (identity + 3×3 square + 1×11 and
11×1 orthogonal band depthwise convs, split along channels at branch_ratio 0.125), `ConvMlp`
(1×1), `MetaNeXtBlock` (token-mixer → BN → MLP → LayerScale → residual), `MetaNeXtStage` (stride-2
downsample except first). Adapted for OUR task: 1-channel 128px input, stem 4×4/4 → 32², 4 stages
at 32/16/8/4, scale-scalar concatenated pre-head, out_dim 1 (point) or 2 (NLL). Config
depths=(2,2,6,2) dims=(48,96,192,384) → **4.19M params** (ResNet was 2.83M). Selectable via
`--arch {resnet,inceptionnext}`; checkpoint records `arch`; `predict_real_lenses_paltas.py` +
`build_model()` auto-load the right backbone. ResNet KEPT for a clean architecture ablation.
Smoke-tested (CPU, 400 imgs, 3 ep): learns cleanly (loss 0.98→0.51, val MAE 1.36→0.70), stable.

**Plan when v3 data lands:** merge + gate (companion-count vs real), then train InceptionNeXt AND
ResNet on v3 (isolates arch effect AND companion-fix effect), evaluate both on the frozen benchmark.

## 2026-07-08 (cont.) — Companion-injection smoke CONVERGED over 3 iterations; awaiting Nurkyz approval for full regen

Three smoke iterations (all SLURM, previews in da_pool_inspection/):
- v1 (uniform stamps, rate U[3,22]): injection works but too sparse — detected median 2 vs real 10.
- v2 (flux-weighted, brightest 55%, rate U[8,30]): right density (median 7) BUT the bright-tail
  filter grabbed cosmic rays / satellite trails → elongated streak artifacts + visible stamp-box
  edges. Rejected on visual inspection (metric alone would have passed it — project rule: eye > metric).
- v3 (ADOPTED): stamp builder rebuilt with artifact rejection (bbox aspect ≤ 2.2, fill-fraction
  ≥ 0.35 → removes CRs/trails) + Tukey edge apodization (no box seam); inject rate U[8,26],
  flux_pct 35. Visual: round companion sources scattered realistically, no boxes; a realistic
  MINORITY of streaks remain (real HST images have satellite trails / diffraction spikes too).
  Detector median 3 (strict 5σ/4px) undercounts the fainter apodized real-galaxy stamps, but the
  field busyness now visually matches real; density knob (rate) available if Nurkyz wants busier.

Pipeline pieces final: `build_source_stamps.py` (clean library `source_stamps_clean.h5`, 6000
apodized artifact-filtered real COSMOS stamps) + `hybrid_combine.py --companion_stamps` (flux-
weighted, count-controlled, lens/arc-protected, corner-safe). ⛔ Awaiting Nurkyz's approval of the
v3 smoke before the full 100k regen (which will be SLURM, sharded, same as the v2 dataset build).

## 2026-07-08 — Stamp-builder HANG diagnosed & fixed; smoke pipeline moved to resilient SLURM

**Incident:** `build_source_stamps.py` ran 2h19min at 99.8% CPU with no output. Root cause: it
called `scipy.ndimage.center_of_mass(mask, lab, i)` PER label, each an O(N) scan of the full
~400-Mpx tile → effectively O(N × n_sources), hours-to-days. Killed (process-group kill).
**Fixed:** block-wise processing (2048-px blocks in randomized order) + `find_objects` for all
bounding boxes in ONE pass; stop at --n. Verified: 300 stamps in <180 s (was: never).

**Resilience (Nurkyz may lose internet):** the whole SSH chain originates from Nurkyz's Mac, so a
Mac-side internet drop kills my ssh AND any foreground remote process. Fix = everything now runs
as SLURM jobs on compute nodes, which are independent of the login session entirely. The
companion smoke is `smoke_companions.sbatch` (job 47131 on node b7): build full 6000-stamp
library → 200 v2-config images → inject real companions → preview + companion-count verification
vs real → stop for inspection. Survives disconnection; I pull previews to da_pool_inspection/
when it lands. Full regen will likewise be SLURM (already the pattern).

---

## 2026-07-07 (cont.) — "Busy field" gap QUANTIFIED (Nurkyz's observation confirmed); companion-injection built; LEMON same-lens & TNG assessed

**Nurkyz's observation — real lenses have field companions, sims don't — CONFIRMED and it is
large.** `characterize_field.py` counts bright sources outside the central 15 px:
- current backdrops (empty_cutouts_4k): median **0** companions/img (mean 0.6)
- finished hybrid train v2: median **1** (mean 1.3; only 4% have ≥3)
- real SLACS benchmark: median **10** (mean 9.9; **70%** have ≥3)
- real DA pool: median **16** (mean 15.9; 97% have ≥3)
The empty-cutout harvest (`harvest_empty_cutouts.py`) only required the central arc region to be
source-free but in practice stripped ~all field neighbours (COSMOS regions it kept were sparse,
and median-subtraction faded the rest). So sims are ~2 orders of magnitude too clean in the
field — a real OOD axis the CNN can key on. Visual (`da_pool_inspection/field_busyness_compare.png`)
is unambiguous. This is the SAME content-gap direction the DA post-mortem pointed to, but a
CHEAPER, more targeted fix than full real-deflector-light Path B.

**Companion injection built (real stamps, not synthetic):** `build_source_stamps.py` extracts a
library of REAL compact-source postage stamps from the COSMOS ACS F814W tiles (real HST
morphology/PSF/noise, tile e-/s units = same as sim/backdrop, no rescale). `hybrid_combine.py`
gains `--companion_stamps` + rate controls: per image, N ~ Poisson(U[3,22]) real stamps pasted
at r∈[18,62] px (protecting the lens+arc, clear of the corner sky-estimation boxes). Count
recorded per image (`n_companions`). Smoke test → preview to da_pool_inspection/ for Nurkyz to
inspect BEFORE any full regen (iteration law).

**LEMON same-lens evaluation (Nurkyz point #2) — researched:** LEMON's real test = 29 SLACS
(Bolton08 Table 5 b_SIE — OUR EXACT GT) + 13 EEL + 5 COSMOS + 13 ACS, but **all EUCLIDISED**
(HST degraded to Euclid 0.1″/px). Two consequences: (a) same SLACS SYSTEMS are in our 62-lens
benchmark (both from Bolton08) → we can report native-HST numbers on the intersection = "same
lenses, same GT, we use the native (harder) HST observation, they use degraded"; their exact 29
names aren't in the paper (only Bolton08+Auger09 refs + filters r_e<2″) → reconstruct by filter
or email authors. (b) A TRUE "exact same observation" comparison would require Euclidising our
images too = the D5 cross-instrument experiment (their turf). Both are worth doing; (a) is the
stronger claim for us.

**TNG convergence maps vs Sérsic (Nurkyz question) — assessment: LOW priority for θ_E, do
companions first.** TNG κ changes the MASS model (arc geometry + θ_E label), NOT the lens light
where the measured gap is. Risks: (1) label offset — TNG θ_E is κ̄=1, benchmark GT is SIE b_SIE
(the 2026-07-02 pivot's core issue) → could HURT θ_E unless cross-calibrated; (2) TNG central-
image artifact = a NEW sim-to-real gap; (3) 22,768 fixed halos cap diversity. θ_E is a radial
enclosed-mass quantity, fairly robust to the mass substructure TNG adds. ⇒ TNG is valuable for
the MULTI-PARAMETER/substructure extension and as a "does mass realism matter" ablation, not for
θ_E accuracy now. Sequence: companions → (if residual gap) real deflector light → TNG for
multi-param.

---

## 2026-07-07 (cont.) — DA POST-MORTEM (Nurkyz-requested): pool audited, a real BN bug found & fixed; negative result SURVIVES the fix

**Pool audit (Nurkyz's hypothesis: "the DA lenses might be wrong / no arcs"):** downloaded all
104 pool cutouts locally (`da_pool_inspection/`, galleries + metrics). Verdict = NUANCED, not
"junk". Objective metrics: central peak/sky median 848 (benchmark SLACS 968, S4TM 902 — same
regime); every cutout has central deflector light. Morphological multiplicity (a crude
group/pair detector): pool 26% single / 23% pair / 51% multi-peak — which sits INSIDE the
benchmark's own range (SLACS 33/33/33; S4TM 12/18/70, i.e. the benchmark S4TM is MORE group-
dominated than the pool). So the pool is a plausible sample of the same messy SDSS-selected
population we evaluate on; it is NOT obviously worse than the benchmark. Real limitations
(honest): (a) only 104 images; (b) drawn from S4TM t0 = a CANDIDATE catalog → higher unconfirmed-
non-lens contamination than the graded benchmark; (c) arc-poor by eye (single-orbit F814W).
These would weaken DA but are NOT a fatal "wrong data" bug.

**REAL BUG FOUND — BatchNorm running-stat contamination.** During DA training the target-pool
(real) batches pass through BN in TRAIN mode, so running_mean/var drift toward the real-pool
distribution; at benchmark eval the model uses these contaminated buffers → the "DA effect" is
entangled with a BN-stats shift (classic DA gotcha; proper fix = source-only/frozen BN, AdaBN).
Confirmed: DA-v2-finetune vs v2 BN running_mean shifted 4.4% median / 32% p90 from only 12 DA
epochs.

**Decisive fix + re-analysis (same model #7, BN recomputed from SIM data only — a bug-fix
re-eval, not model-shopping; declared as such):**
| model | SLACS R² / med / fail | S4TM R² / med / fail |
|---|---|---|
| v2 reference (no DA) | +0.27 / −2.6% / 23% | +0.47 / −1.8% / 38% |
| DA-v2 (as run, buggy BN) | −0.02 / −4.7% / 24% | +0.41 / −5.5% / 35% |
| DA-v2 + BN-fix (sim-only BN) | +0.05 / −3.4% / 24% | +0.36 / −3.7% / 35% |

**Conclusion: the BN bug was real and recovered ~half the SLACS R² loss — but DA STILL does not
beat the v2 reference even bug-fixed (+0.05/+0.36 vs +0.27/+0.47).** The negative DA result is
therefore ROBUST, and now better-explained: with correct BN, DA is neutral-to-slightly-harmful,
consistent with "the simulator already matches the target distribution; the residual gap is
content (real deflector morphology), which feature alignment cannot inject." Prior log entry's
DA-v2 numbers stand as the as-run result; this entry adds the corrected-BN numbers and the bug.
(This diagnostic re-eval reused model #7; running benchmark-eval count unchanged at 7 by intent —
same model, corrected buffers.)

**Redirect (evidence-driven):** every diagnostic now converges on the SAME unhandled axis —
ablations (backdrops/PSF/prior handled), style-MMD null (style already matched), DA failure
(alignment can't help), shared J0841+3824 failure with Cao (complex lens light). ⇒ highest-value
next step is **Path B: inject paltas arcs onto REAL deflector cutouts (real lens light)** — which
is exactly what Sam's offered real LRG/deflector cutouts enable. Recommended over both "cleaner
DA pool" and "smarter DA technique" (DA's ceiling here is low: sim≈target already). Colleague's
Euclid/Gallery/COWLS remain D5 (cross-instrument generalization), not this gap.

---

## 2026-07-07 (cont.) — ⛔ D4 CONCLUDED: benchmark evaluation #7 (DA-v2); two-round rigorous NEGATIVE result; interpretation locked

**Running count: 7.** Both DA-v2 candidates QUALIFIED on sim-val (scratch 0.0426″, fine-tune
0.0437″ vs threshold 0.0483″ — style alignment fully preserved task accuracy, unlike DA-v1).
Pre-registered tiebreak (lowest final style-MMD) selected the from-scratch model (0.0232 vs
0.0385). ONE evaluation run, TTA, standard protocol.

**Eval #7 vs the pre-declared success metrics (v2 reference in parentheses):**
- SLACS: median −4.7% (−2.6), R² −0.02 (+0.27), fail 24% (23%), slope 0.63 (0.72), σ-coverage
  44/77% (52/83%).
- S4TM: median −5.5% (−1.8), R² +0.41 (+0.47), fail 35% (38%), slope 0.63 (0.71), σ-coverage
  40/72% (45/80%).
**Every pre-declared metric flat or worse ⇒ DA-v2 is a NEGATIVE result on the benchmark.**

**D4 final interpretation (two rounds, both informative):**
1. DA-v1 (semantic-embedding MMD, the published sim-to-sim recipe): fails via the label-shift
   mechanism — flat source labels vs peaked real population; alignment distorts the
   label-carrying subspace. Diagnosed from sim-val bias alone (no benchmark spent).
2. DA-v2 (shallow style-statistics MMD): preserves sim accuracy but does not improve — and
   slightly degrades — real-lens metrics. Consistent explanation: the hybrid simulator ALREADY
   matches the style-level statistics of real data (the Stage-1/2 gates proved distributional
   overlap), so style alignment has nothing useful left to move and only perturbs features;
   the RESIDUAL sim-to-real gap is CONTENT-level (real deflector morphology — the parametric-
   Sérsic limitation, cf. the shared J0841+3824 failure with Cao's pipeline), which UDA cannot
   inject from a small unlabeled pool.
**Paper framing:** "why UDA does not (yet) help realism-calibrated lens CNNs — two failure
modes identified (label shift; style saturation)" — novel, honest, and it sharpens the
conclusion that realism engineering beats post-hoc adaptation in this regime and that real
deflector light (Path B) is the correct next axis. All DA claims in PAPER_DRAFT updated from
"proposed" to results. D5 (multi-domain generalization) remains future work.

---

## 2026-07-07 — DA-v1 NEGATIVE RESULT (pre-registered rule enforced, no benchmark eval spent); label-shift diagnosis; DA-v2 PRE-REGISTERED

**DA-v1 outcome:** pool fetched complete (104/104 candidates had ACS F814W coverage — 2× the
expected pool size; triple disjointness verified on the fetched h5: 0 name overlaps, 0
coordinate matches, 0 pixel near-duplicates cos>0.995; mast_cache purged, quota 99.4→55.8 GB).
Both pre-registered runs trained cleanly but FAILED the sim-val threshold (≤0.0483″):
α=0.5 → best val MAE 0.0753″; α=1.4 → 0.0792″ (reference 0.0420″). Per the pre-registered rule:
**negative result declared; benchmark NOT evaluated (count stays 6).**

**Diagnosis (from the curves, paper-grade):** MMD alignment succeeded (distance 0.036→0.021 /
0.029→0.017) while sim-val acquired a systematic POSITIVE bias (16–84 ≈ [+0.2,+7.3]) — the
signature of the **label-shift failure mode of naive UDA for regression**: source labels are
flat U[0.45,2.3] but the real pool's implicit θ_E population is peaked (~0.7–1.7); MMD on the
semantic (post-GAP) embedding cannot separate domain style from label content, so it distorts
the label-carrying subspace. Agarwal et al. 2025's sim-to-sim success had IDENTICAL source/target
label distributions — the transfer of their recipe to sim-to-real breaks precisely here. This is
a novel, reportable finding regardless of DA-v2's outcome.

**DA-v2 PRE-REGISTERED (before any v2 result exists):** align SHALLOW STYLE STATISTICS only —
per-channel spatial mean+std of layer1/layer2 feature maps (where the measured domain gap lives:
noise texture, PSF, backgrounds), leaving deep label-carrying features free. Candidates:
C1 = from-scratch, style-MMD α=1.0 with 5-epoch linear warm-up, 40 epochs;
C2 = fine-tune from the v2 reference checkpoint, α=1.0, 2-epoch warm-up, 12 epochs at lr 2e-4.
Selection rule: among candidates with best sim-val MAE ≤ 0.0483″, take the one with the LOWEST
final style-MMD (most aligned while still accurate); exactly ONE benchmark evaluation (#7) for
the winner; if none qualify, DA is reported as a two-round negative result and the label-shift
analysis becomes the DA section's contribution. Success metrics unchanged (slope, fail rates,
σ coverage).

---

## 2026-07-06 (cont.) — DA pool design RULING after colleague input: HST-pure pool now, multi-domain generalization as a follow-on experiment (D5)

**Colleague proposal** (via Nurkyz): enlarge the DA pool with (a) ~250 Euclid Q1 grade-A lenses
(A&A aa55141-25), (b) BELLS GALLERY (Shu et al. 2016, HST WFC3/UVIS F606W), (c) COWLS JWST
(M25/S12-09 tiers), and (d) restrict SLACS to the "gold" sample (arXiv:2202.09201 = Etherington
et al. 2022, "no lens left behind", 59 uniformly-imaged HST lenses).

**Domain analysis:** an MMD pool must be drawn from the TARGET domain (native HST ACS/WFC F814W,
0.05″/px). Euclid VIS (0.1″/px), WFC3/UVIS F606W, and JWST NIRCam are different instrument
domains — including them would pull sim features toward non-HST statistics and convert the claim
from "sim-to-real adaptation" into "cross-instrument domain generalization" (a different, more
speculative experiment). The colleague's underlying stability concern (pool size) is valid but
is a property of the F814W archive itself (~50–60 lens-domain cutouts exist, period).

**RULING (Nurkyz, explicit choice):** HST-pure pool now → DA v1 targets the HST benchmark
cleanly; the colleague's sources become **D5, a follow-on multi-domain generalization
experiment** (Euclid arena doubles as the future LEMON home-turf head-to-head). Gold-sample
handling: the frozen 62+40 benchmark is NOT shrunk post-hoc (7 evaluations already logged
against it — test-set surgery would invalidate the record); instead the Etherington et al. 2022
subset will be reported ALONGSIDE the full sample (literature-defined, performance-independent).

**Ops:** first fetch stopped mid-run at 51/104 on Nurkyz's request (h5 written only at script
end, so cutouts not yet on disk — but all frames cached); fetch RESUMED after the ruling
(mast_cache 32 GB makes completed targets near-instant; cache purge scheduled right after the
pool h5 is written — quota at 88.5/100 GB).

---

## 2026-07-06 (cont.) — D4 sim-to-real domain adaptation: method chosen, pool assembling, selection rule PRE-REGISTERED

**Method (research-backed):** MMD feature alignment on the latent post-GAP embedding, added to
the NLL task loss — the exact recipe of Agarwal, Ćiprijanović & Nord 2025 (arXiv:2411.03334:
multi-kernel MMD at the flattened embedding, L = NLL + α·MMD², α=1.4, model selection on SOURCE
loss; they showed ~2× target-domain gain + repaired calibration, sim-to-sim). We upgrade their
setting to sim-to-REAL. DANN rejected for v1: adversarial training is unstable with a ~50-image
target pool; Ćiprijanović 2023 found MMD competitive. Implementation: `mmd2_multikernel`
(5 RBF kernels, median-heuristic bandwidth), `RealPoolSampler` (dihedral-augmented draws from
the pool, identical asinh normalization), `--da_pool/--da_weight` in train_cnn_paltas.py;
mechanics smoke-tested on CPU (MMD reported per epoch, task loss unaffected).

**Pool:** `da_pool_labels.csv` — 104 candidates (78 S4TM t0 + 26 SLACS t0 grade A/B/C),
disjoint from the frozen benchmark by BOTH normalized name AND 5″ coordinate match (207 → 104
after exclusions; checks logged in build_da_pool.py output). Pool is UNLABELED by construction
(theta_E_pub written as 0; never read). MAST fetch of ACS/WFC F814W cutouts running
(`real_dapool_images.h5`); targets without ACS coverage are skipped by the pipeline.

**PRE-REGISTERED selection rule (written BEFORE any DA training result exists):** train
α_UDA ∈ {0.5, 1.4}; both checkpoints selected on sim-val MAE as always. The single model taken
to the benchmark = the LARGEST α whose best sim-val MAE ≤ 1.15 × the v2 reference (0.0420″ →
threshold 0.0483″); if both fail the threshold, DA-v1 is declared unstable and reported as a
negative result. Exactly ONE benchmark evaluation (#7) for the chosen model (TTA, identical
protocol). Success criteria (also pre-registered): compression slope up from 0.72/0.71 toward 1,
full-sample failure rates down from 23%/38%, σ coverage up from 52%/83% — reported whichever
way they move. mast_cache to be purged after cutout extraction (quota).

---

## 2026-07-06 (cont.) — ⛔ D1 ABLATIONS COMPLETE (benchmark evaluations #3–#6): the sim-to-real gap is causally decomposed

**Running count: 6** (evals #3–#6 = the four pre-approved ablation evaluations, TTA, identical
recipe to v2 except ONE ingredient each; all datasets deleted post-eval, quota back to 78 GB).

| variant (ingredient removed) | SLACS R² / fail | S4TM R² / fail | SLACS med | S4TM med |
|---|---|---|---|---|
| **v2 reference (full recipe)** | **+0.27 / 23%** | **+0.47 / 38%** | −2.6% | −1.8% |
| A3 skewed θ_E prior (flat removed) | −0.52 / 29% | −0.03 / 50% | −6.3% | −7.8% |
| A1 Gaussian PSF (real ePSF removed) | −0.46 / 31% | +0.06 / 50% | −5.4% | −9.8% |
| A2 Gaussian noise (real backdrops removed) | **−5.10 / 58%** | **−14.67 / 90%** | **+24.1%** | **+99.5%** |
| A4 broad ePSF pool (benchmark-matched removed) | +0.22 / 21% | +0.42 / 38% | −1.6% | −2.2% |

**Findings (each is paper-grade):**
1. **Real empty-sky backdrops are the dominant ingredient by an order of magnitude** (A2):
   without real correlated background structure the model catastrophically OVER-predicts on
   real lenses (S4TM median +99.5%, R² −14.7) — real field structure/neighbors read as lensed
   flux when the training noise is uncorrelated Gaussian. Worse than the m3 baseline itself.
2. **Flat θ_E prior is individually necessary** (A3): reverting to the m3-like skew flips SLACS
   R² back negative (−0.52) — the prior-pull causal loop closes exactly as diagnosed.
3. **Real empirical ePSF is individually necessary** (A1): Gaussian PSF flips SLACS R² negative
   (−0.46), nearly as damaging as the skewed prior.
4. **CIRCULARITY CLEARED** (A4): swapping benchmark-matched ePSFs for the fully disjoint broad
   archival pool changes nothing (R² +0.22/+0.42 vs +0.27/+0.47; fail 21%/38% vs 23%/38%) —
   the benchmark-matched PSF library leaks no benchmark information. This kills the referee
   objection pre-emptively and licenses the simpler broad-pool recipe for future surveys.
Ordering: backdrops ≫ prior ≈ PSF > pool(nil). Removing ANY single core ingredient flips
full-sample SLACS R² negative — the recipe is a conjunction, not a sum of small effects.

Remaining from the differentiator campaign: D2 per-lens (await Cao author data — email drafted
by Nurkyz/Brian), D4 sim-to-real DA (unlabeled disjoint pool assembly next).

---

## 2026-07-06 (cont.) — D1 ablation campaign LAUNCHED; D3 calibration-transfer gap measured; D2 Cao-failure-trio checked

**D1 launched:** four-ablation chain running unattended on the cluster (`run_ablations.sh`,
job 46846 = A3 wave 1): A3 skewed-prior (truncnorm 1.00″±0.35″, same [0.45,2.3] support, verified
median 1.02″/64% in [0.7,1.3] with base config isolated via deepcopy) → A1 Gaussian-PSF (FWHM
0.10″, 47px, same support as extended ePSFs) → A2 Gaussian-noise (same per-image RMS draws,
`hybrid_combine.py --no-backdrop` added) → A4 broad-ePSF-pool (90-kernel bank built from the 52
non-benchmark cubes, extended). Each variant: 100k+5k, identical training recipe, TTA benchmark
eval (evals #3–#6, pre-approved bundle), dataset deleted after eval (quota). ~7 h total.

**D3 finding — the σ miscalibration is a DOMAIN effect, not a fixable bias:** sim-val coverage
(TTA σ, N=2000) is 76%/96% at 1σ/2σ — slightly conservative, c68 = 0.854. Real-lens coverage is
52%/83% — under-covering by ~1.3×. A sim-val-fitted recalibration would make real coverage WORSE.
⇒ Report both coverages and frame the gap as a quantified measurement of domain shift in the
uncertainty channel (the exact quantity sim-to-real DA should repair; Agarwal 2025 showed the
sim-to-sim analogue). No recalibration applied; benchmark never used for calibration.

**D2 status:** Cao 2025 arXiv source fetched — NO machine-readable per-lens table (results are in
summary figures); full per-lens comparison needs author contact or figure digitization (email
Cao — Nurkyz/Brian action). BUT their Appendix A names their 3 catastrophic failures and
explicitly calls for ML Einstein-radius priors as the fix. Our v2 on those exact systems
(re-analysis of eval-#2 CSVs, no new eval):
- J1153+4612: **−3.6%, confident** (σ/μ 4.2%) — we solve a system their pipeline fails.
- J1016+3859: −28.9%, **correctly flagged uncertain** (σ/μ 13.3% > gate).
- J0841+3824: **−65.3% while CONFIDENT** (σ/μ 3.9%) — a confidently-wrong failure, shared with
  Cao (their diagnosis: complex two-component lens light + faint central counter-image). Also
  regressed v1→v2 (−20%→−65%): the widened low-θ_E support opened a new failure mode on
  complex-lens-light systems. HONEST reporting required: confidence gating is strong
  statistically (ρ=+0.71) but not infallible per-lens; J0841 is the poster child for the
  parametric-lens-light limitation (Path-B axis) and a shared-failure-mode finding across
  method families.

---

## 2026-07-06 (cont.) — Literature review analyzed; differentiator campaign planned (MASTER_PLAN addendum); LEMON head-to-head computed

**Input:** Nurkyz's systematic 19-paper review table (Downloads/table.csv). Full synthesis now in
LITERATURE.md (rewritten). Four decisive facts: (1) LEMON/Busillo 2026 is the only other
sim-trained θ_E net scored on real numeric GT — Euclidised domain, full-sample R² ≈ −0.03, and
they ALREADY σ-filter on real lenses (so confidence-gating alone is not a novelty claim — cite
them); (2) all three DA works are sim-to-sim ⇒ sim-to-REAL DA on real GT remains unclaimed;
(3) nobody ablates realism ingredients; (4) Cao 2025 per-lens data is public (TinyLensGpu repo).

**LEMON-convention metrics computed from EXISTING eval-#2 predictions (re-analysis, benchmark
eval count unchanged at 2):** combined 102 native-HST lenses: bias −0.059″ (LEMON +0.17″),
RMSE 0.210″ (0.63″), NMAD 0.096″ (0.23″), **R² +0.45 full-sample (LEMON ≈ −0.03)**;
σ/μ≤median half: R² +0.71, NMAD 0.061″, fail 12% (S4TM confident half R² +0.87).
**Honest weakness found:** σ under-covers on real data (|err|<1σ: 52%; <2σ: 83%) — recalibration
must be fit on sim-val ONLY, report raw + recalibrated (D3).

**Plan (MASTER_PLAN 2026-07-06 addendum):** D1 causal ablations (A3 prior spine first, then A1
Gaussian-PSF, A2 Gaussian-noise, A4 broad-pool) → D2 Cao per-lens (public data) → D3 σ
recalibration → D4 sim-to-real DA (MMD v1) with a benchmark-disjoint unlabeled real pool.
Ablation benchmark evaluations pre-approved by Nurkyz as a batch ("proceed to executing the
plan"); each will be logged with the running count as it happens.

---

## 2026-07-06 (cont.) — ⛔ REAL-BENCHMARK EVALUATION #2 (v2 bundle: wider prior + 88 ePSFs + NLL head + TTA)

**Running count: 2.** Model `einstein_cnn_paltas_v2.pt` (sim-val: MAE 0.0420″, frac 0.96%,
R² 0.948 — better than v1 despite the wider θ_E range; NLL head stable). Dataset v2 gated on the
full merged 100k (sky-RMS 1.14, peak/sky 723, θ_E [0.450, 2.300] flat). Prediction with 8×
dihedral TTA, no flux rescale. Sub-shard duplicates cleaned post-merge (quota 84→78 GB).

| metric | v1 → v2 SLACS (N=62) | v1 → v2 S4TM (N=40) | bar |
|---|---|---|---|
| median frac err | −1.1% → −2.6% [95% CI −4.5,−0.1] | **+5.8% → −1.8%** [−7.9,+1.5] | ±5% ✓✓ |
| R² | +0.23 → +0.27 | +0.33 → **+0.47** | >0 ✓, <0.5 stretch |
| MAE | 0.139″ → 0.129″ | 0.159″ → 0.140″ | — |
| fail>15% | 27% → 23% [13,34] | 38% → 38% [22,52] | ≲10% ✗ |
| slope pred-vs-true | 0.62 → 0.72 | 0.58 → 0.71 | 1.0 |

**Headline finding — the NLL σ is a working failure detector:** Spearman(σ/μ, |frac err|) =
**+0.71 on SLACS** (+0.39 S4TM). The σ is domain-aware: median σ/μ ≈ 9–10% on real lenses vs
~1% regime on sim-val — the network itself reports the domain gap. **Confidence-gated subsets:
SLACS σ/μ ≤ median (31 lenses): failure 6%, median −1.6% — this subset MEETS the full
publishable bar (median ±5%, fail ≲10%) and matches/beats Cao's ~10% failure regime at
~10⁵× the speed, with a self-diagnosed confidence flag.** Even the 75% subset holds 7%.
S4TM confident half: 15% fail (weaker but useful).

**What the coverage fix did:** exactly what the audit predicted — S4TM's +5.8% bias eliminated;
predictions now reach 0.49″. Remaining S4TM failure structure is no longer low-end-specific
(mid-range [1.0,1.5) still 38–50% fail with −7…−16% under-prediction). NEW HYPOTHESIS for next
iteration (not yet tested): hybrid noise targets were drawn from the SLACS sky-RMS distribution
only; S4TM cutouts may sit at different S/N (different exposure structure) → S4TM-specific
residual domain gap. Check by comparing robust-sky distributions of the two real files
(calibration usage), then draw noise targets from the union.

**Verdict vs the paper bar:** full-sample medians now pass on BOTH samples; R² positive both
(S4TM near the 0.5 stretch); full-sample failure rates (23%/38%) still above ≲10% — the
confidence-gated result is the publishable-shaped story TODAY, and the remaining levers are
known (S4TM noise calibration; TNG-κ mass-realism variant; larger backdrop pool — tiles
downloading; then domain adaptation as the capstone per the Prof-Chan assessment).

---

## 2026-07-06 (cont.) — Audit-fix bundle EXECUTING (v2 dataset + NLL + TTA); Prof. Chan's two proposals assessed

**Bundle status (all four audit fixes in flight, Nurkyz-approved):**
1. θ_E prior → U[0.45, 2.30] (`.bak_theta`); re-gate pilot H PASSED (sky-RMS 1.14, peak/sky 786,
   θ_E [0.465, 2.298]) before any large run, per the iteration law.
2. PSF diversity 22 → 88 kernels: `psf_bank_v2` (90 kernels from benchmark ePSF cubes, random
   exposure/chip/position/rotation, all wing-extended). v2 generation runs 4 sub-shards per SLURM
   task, one kernel each: sub-shards 0–79 train (1250 imgs each = 100k), 80–87 val (625 each =
   5k; kernels 80–87 val-only). Bank-builder bug found&fixed: `interp_epsf` also rejects float
   coords here (rebuilt with ints).
3. Backdrops: harvest of 4000 came back with the SAME 1317 (only one COSMOS tile on disk — the
   grid scan is deterministic). Deviation logged honestly: v2 generation proceeds with 1317
   (ranked below prior/PSF fixes); tiles 071+072 downloading in background (resumable wget from
   IRSA, ~4 GB) for a bigger harvest in the NEXT iteration/ablation.
4. Training script upgraded: (μ, log σ²) Gaussian-NLL head (`--nll`, clamped logvar, backbone
   unchanged); stability smoke-tested on CPU before the GPU run (loss ↓ smoothly, MAE tracks the
   point-estimate smoke — MASTER_PLAN 3.3's escape clause not needed). Degenerate-scale fix:
   s_std floor → 1.0 when FOV fixed (s ≡ 0 train AND predict). Prediction script: 8× dihedral
   TTA (`--tta`) + per-lens σ column (mean aleatoric variance + view-spread variance).
Ops lessons re-learned: SLURM `--output` directory must exist BEFORE submission (instant
1-second FAILEDs otherwise); nested-quoting one-liners broke twice more — script files only.

**Prof. Chan proposal 1 — simulated (IllustrisTNG) convergence inside paltas: ADOPT as a planned
dataset variant/ablation, not a replacement.** Feasible: paltas deflectors are extendable (same
subclass pattern as ApparentSersic) wrapping lenstronomy's INTERPOL profile with deflection maps
derived from the 22,768 TNG κ maps (FFT solve exists in LensFusion's forward_operator; labels via
`einstein_radius_hard`). Scientific value: real azimuthal mass structure (twists, substructure,
boxiness) vs perfect-ellipse SIE arcs — a genuine realism axis AND a clean paper ablation
("parametric vs hydro mass"), plus narrative synergy with LensFusion Phase 2 (same TNG maps as
the diffusion prior). REQUIRED CARE, flag to Brian: (a) label-convention mixing — SIE maps carry
SIE θ_E, TNG maps carry κ̄=1 θ_E; quantify the offset on a TNG subsample (fit SIE to TNG
deflection or compare κ̄=1 radius vs b_SIE-style fit) before mixing labels in one training set;
(b) the known TNG central-image artifact (sub-kpc cores → bright central images not seen in real
lenses, Bolton 2012/Shu 2016, already in LITERATURE.md) — a NEW sim-to-real gap this would
introduce; lens light partly masks it, but it must be gated; (c) 22,768 fixed halos vs infinite
parametric draws (diversity cap). Sequencing: after eval #2, as ablation-tier work.

**Prof. Chan proposal 2 — domain adaptation: ADOPT, sequenced after the realism bundle +
ablations, with one important correction to the novelty claim.** Literature check (2026-07-06):
DA for strong-lens θ_E REGRESSION already exists — Ćiprijanović et al. (arXiv:2311.17238,
NeurIPS 2023 ML4PS): DANN+MMD for Einstein-radius regression, and arXiv:2411.03334: UDA +
mean-variance estimators (2× target-domain accuracy gain, better-calibrated σ). BUT both are
SIM-TO-SIM (target = simulations emulating DES noise); both explicitly defer real data to future
work. Also arXiv:2410.16347 (domain-adaptive neural posterior estimation) and DA for lens
FINDING. ⇒ The open, still-novel claim is **sim-to-REAL adaptation for lens-parameter regression
validated on a real spectroscopic benchmark** — which this project is uniquely positioned for
(frozen 62+40 with b_SIE truth). Hard constraint: UDA must NOT use the frozen benchmark images
as its unlabeled target pool (that would contaminate the test set — transductive adaptation is a
weaker, different claim); assemble a DISJOINT unlabeled real pool (BELLS, non-benchmark
SLACS/S4TM rejects, lens candidates from archives). Note our NLL head = the MVE component of
arXiv:2411.03334 — we are already building DA-ready infrastructure. Sequencing rationale: DA is
most defensible AFTER physical realism is maxed and ablations quantify the residual gap
(reviewers' "your sims were just bad" rebuttal), and the compression-slope metric (0.96 sim vs
0.62/0.58 real) is exactly the yardstick DA should move toward 1.

---

## 2026-07-06 (cont.) — FULL PIPELINE AUDIT (Nurkyz-requested, post-model-switch): one real deviation-from-plan bug found; failure structure diagnosed

Audited: Stage-2 generation, Stage-3 training, Stage-4 evaluation. No new benchmark evaluation
run (all diagnosis from existing eval-#1 CSVs + sim-val only; benchmark eval count stays 1).

**Verified correct:** dataset recipe/units/gates (incl. full-100k gate), val disjointness (seeds
AND PSF kernels), merge integrity, per-image paltas θ_E labels (no join hazard), training loss/
selection discipline (val-only, clean convergence), identical train/predict normalization,
pixscale read from file not assumed, no-flux-rescale decision consistent with the gate's
unit-calibration evidence, bootstrap CIs, m3-baseline comparability (same metrics script).

**BUG (the real one): θ_E prior range deviated from plan and truncates real coverage.** Config
used U[0.6, 2.2]; MASTER_PLAN 2.1 specified U[0.55, 2.3] "slightly WIDER than the benchmark so
the real range sits in the interior". Actual benchmark coverage: S4TM b_SIE reaches DOWN TO
0.54″ (5 lenses < 0.6) and SLACS up to 1.78″. Consequences, measured from eval-#1 residuals:
- S4TM θ_E<0.6 (outside training support): 4/5 fail, median error +68.5%.
- Low-edge effect is visible even in-distribution (sim-val [0.6,0.8): +1.3% bias, 12.9% fail
  vs 2.4% at high θ_E) and is amplified ~5× on real data ([0.6,0.8): 57% fail S4TM).
- Failure budget: ~8/15 S4TM and ~7/17 SLACS failures sit at θ_E<1.0 with systematic
  over-prediction; 6 SLACS failures are under-predictions at θ_E≥1.1; 1 wild outlier
  (J1134+6027, +79%).

**Checked and cleared:** degenerate scale conditioning (all training image_fov=6.4 → s_std=1e-8 →
s≡0 in training; inference fed s=+0.094 through never-trained weights). Measured effect on 256
val predictions: ≤0.001″ — NEGLIGIBLE. Cosmetic fix queued (pin s=0 while FOV is fixed).

**Central diagnosis — domain-gap compression, quantified:** pred-vs-true slope is 0.963 on
sim-val but 0.62 (SLACS) / 0.58 (S4TM) on real lenses. In-distribution the model barely hedges;
under domain shift it regresses toward ~1.1″. This is prior-pull's milder cousin and the paper's
central sim-to-real quantity. Candidate contributors (ranked, none yet ablated): parametric-Sérsic
lens light (the named Path-B trigger), PSF diversity (only 24 kernels), backdrop diversity (1317
cutouts reused ~76×), no TTA/uncertainty at inference.

**Minor findings:** per-shard previews imaged the NOISELESS stage (final hybrids only checked
merged — acceptable, noted); sim-val shares the empty-cutout pool with train (val slightly
optimistic); CLAUDE.md says R²=Pearson² but metrics_real.py computes coefficient of
determination (baseline used the same script → comparisons internally consistent; paper must
state which); stale "m3 zero-shot" title in metrics_real.py plot.

**Improvement plan (proposed, pending approval where >1k images / >30 min):**
1. Regenerate with θ_E ~ U[0.45, 2.3] (+ modest low-end oversampling) — directly removes the
   out-of-support failures and softens the low-edge bias. ~40 min cluster.
2. Before regen: enlarge PSF bank 24→~120 kernels; harvest ~4000 empty cutouts (both cheap).
3. Add 8× dihedral test-time augmentation to prediction (free; targets isolated outliers).
4. Retrain with (μ, log σ²) Gaussian-NLL head — per-lens error bars, "confident-subset" failure
   rate for the paper, Phase-2 weighting. Fall back to Huber if unstable.
5. Evaluation #2 only after all of the above, as one bundle. If failure rate remains ≫10% and
   residuals track lens-light features → Path-B discussion (real deflector cutouts).

---

## 2026-07-06 (cont.) — ⛔ STAGE 4, REAL-BENCHMARK EVALUATION #1 (with Nurkyz present)

**Running count: 1.** First-ever evaluation of any paltas-hybrid-trained model against the frozen
62 SLACS + 40 S4TM. Model: `einstein_cnn_paltas_v1.pt` (Stage-3 checkpoint, sim-val frac 1.38%,
R² 0.954 — see prior entry). Nurkyz explicitly asked to proceed and was present.

**New prediction script** `predict_real_lenses_paltas.py` (does not overwrite the old
m3-specific `predict_real_lenses.py`): imports `EinsteinCNNScale`/`normalize_images` from
`train_cnn_paltas.py`; reads `box_arcsec`/`pixscale` from each real h5 rather than assuming
6.4″/0.05″ (both confirmed 6.4/0.05 anyway). **Key design decision, stated explicitly**: no
`--peak` flux rescale (default off). m3 needed that hack because its training flux was an
arbitrary/synthetic convention divorced from real cutouts' raw e⁻/s — exactly the hand-tuning the
2026-07-02 paltas pivot exists to eliminate. Our hybrid training images are real-unit-calibrated
(paltas HST zeropoint 25.94 + real empty-cutout backdrops + noise matched to the real sky-RMS
distribution), already verified unit-consistent by `gate_stage0.py` on the full 100k set. If this
assumption is wrong, that itself would be a finding, not something to mask with a rescale flag.

**Results** (`metrics_real.py`, J0955+0101 excluded from SLACS per the standing convention;
bootstrap 95% CIs, 10k resamples, added per MASTER_PLAN 4.2):

| sample | N | median frac err | 95% CI (median) | 16–84% | R² | MAE | fail>15% | 95% CI (fail) |
|---|---|---|---|---|---|---|---|---|
| SLACS | 62 | **−1.1%** | [−4.0, +2.2] | [−10.6, +15.1] | **+0.23** | 0.139″ | 27% | [18, 39] |
| S4TM | 40 | **+5.8%** | [+2.1, +16.9] | [−6.6, +28.0] | **+0.33** | 0.159″ | 38% | [22, 52] |

**vs the locked m3 "before" baseline** (SLACS median −7.9%, R² −1.02, MAE 0.274″, fail 55%; S4TM
median −5.3%, R² −0.53, fail 68%): **R² crossed from negative to positive on both samples** — the
paper's own stated "single most important headline" (PAPER_PLAN). Median error and MAE both
improved substantially on both samples.

**vs the paper's success bar** (median within ±5%, R² > 0 ideally > 0.5, failure ≲ 10%, i.e.
match/beat Cao et al. 2025): SLACS median passes comfortably; S4TM median (+5.8%) sits just
outside ±5% but its CI includes values inside the bar. R² is positive on both but well short of
the ">0.5 ideally" stretch goal. **Failure rate is the dominant gap**: 27%/38%, both far above
the ≲10% target and above Cao's own ~10% — this is NOT yet a match/beat result.

**Assessment (no hype, no minimizing):** real, substantial progress — this is a working,
real-lens-generalizing model where m3 was not — but it does not yet clear the paper's bar,
principally on failure rate. Root cause not yet diagnosed (per "diagnose before fixing": next
step should be a failure-gallery/feature analysis in the style of `analyze_failures.py`, not
another blind retrain). Candidate factors already flagged as open in this project's own plan and
not yet tested: parametric-Sérsic vs real lens light (the standing Path-B trigger condition),
real-backdrop point-source density/richness, PSF-bank diversity (only 24 kernels), and the
untried Gaussian-NLL uncertainty head. None of these has been tested against this result yet —
listed as candidates, not conclusions.

Minor found issue, not fixed yet (flagging rather than silently patching a shared script): the
scatter-plot title in `metrics_real.py` is hardcoded to "m3 zero-shot... kappa_bar=1 vs SIE
caveat" — stale wording for a paltas-trained SIE-labeled model. Cosmetic only; numbers unaffected.

---

## 2026-07-06 (cont.) — Stage 3 training LAUNCHED (job 46755); 18.66 GB of superseded pre-paltas data deleted

**Training script** `~/einstein_cnn/train_cnn_paltas.py` (new file, not overwriting `train_cnn_m3.py`
— the data-loading assumptions are fundamentally different: no `kappa_index` join, `theta_E` read
per-image). Architecture, asinh input norm, Huber loss, Adam, flip/rotation augmentation all kept
IDENTICAL to m3 per MASTER_PLAN 3.1. Model selection uses the dedicated `val_hybrid_5k.h5`
(seed+kernel-disjoint), not a random split of train, per MASTER_PLAN 3.4. Point-estimate head only
for this first run — the optional Gaussian-NLL uncertainty head (MASTER_PLAN 3.3) is deferred to a
follow-up once the base pipeline is confirmed clean on this brand-new dataset, per that section's
own escape clause ("if it destabilizes... don't fight it").

**Smoke-tested before committing the GPU job**: 300 train / 100 val images, 2 epochs, CPU — no
crashes, loss dropped 0.35→0.09, val MAE 1.05→0.74″ (expected trajectory for 2 epochs on 300
images from random init). Confirmed the full pipeline (data loading, both h5 formats, augmentation,
checkpoint save) is correct before the multi-hour run.

**Launched**: `train_stage3.sbatch` (`--gres=gpu:1`, 32 GB mem, 6 h ceiling), dry-run tested first
(`sbatch --test-only`), then submitted for real — job 46755, running on node a1. 40 epochs, batch
64, lr 1e-3, Huber, asinh norm, augmentation on. Checkpoint: `einstein_cnn_paltas_v1.pt`. No
real-lens file touched (train/val only).

**Cleanup** (Nurkyz-authorized, with an explicit carve-out for anything m3-related): deleted
ONLY files this project's own docs label SUPERSEDED/"dead end"/RETIRED — the pre-paltas bespoke
SIMCT generator and its HSTempty/harvested-ellipticals variants (`lensed_hstempty.h5`,
`lensed_hstempty_arc.h5`, `lensed_train_combined.h5`, `lensed_train_src15/20.h5`, `lensed_raw.h5`,
`lensed_simct.h5`, `elliptical_cutouts.h5`, `ellip_train/test/test_quick.h5`) — plus the 22
per-shard `hybrid_shard_*.h5` files now fully duplicated inside the merged `train_hybrid_100k.h5`
/ `val_hybrid_5k.h5` (merge already passed its own row-count assertions). Dry-run listed and
totaled before any deletion. **18.66 GB freed** (quota 88.7 → 70.9 GB). Explicitly NOT touched:
anything `real_*`, anything m2/m3-named (datasets, checkpoints, or the m3 robustness test sweep
`test_noise_*`/`test_psf_*`/`test_lenslight_amp20`/`test_noarc_ll20`), `empty_cutouts.h5` (actively
read by `hybrid_combine.py`), the Stage-1 pilot/hybrid iteration artifacts (kept as small audit
evidence for the C→F narrative), and the raw COSMOS mosaic FITS tiles (reusable, ~4.1 GB, left
alone pending an explicit ask).

---

## 2026-07-06 (cont.) — ⛔ STAGE 2 COMPLETE: 100k train + 5k val hybrid dataset generated, merged, and gated

All 22 shards (3 SLURM waves) completed with zero errors. Merged: `train_hybrid_100k.h5`
(100,000 images, θ_E [0.600, 2.200] median 1.407, flat) and `val_hybrid_5k.h5` (5,000 images,
θ_E [0.601, 2.199] median 1.403) — val shards used kernels 20–21 and seed ranges disjoint from
every train shard, so validation is clean of both label and PSF leakage.

**Final gate on the full 100k merged set (not just a 200-pilot) — ALL PASS:** sky-RMS ratio 1.14,
peak/sky median 718 (band 492–1798), θ_E range/flatness both pass. Radial-profile overlay lies
on the real curve out to ~1.5″ with a small, expected deficit beyond it (extended real-galaxy
outskirts/neighbors — the known residual gap, unchanged from pilot F/G). Side-by-side galleries
(`real_vs_train100k.png`, `real_vs_val5k.png`) confirm realistic morphology in both splits,
including an inclined/disky real lens (J1032+5322) that the parametric Sérsic model cannot
mimic — logged as the standing parametric-lens-light caveat, not a new problem.

Disk: 88.7/100 GB used after generation (was 75 GB before this session). Flag for Nurkyz: the
old m2/m3-era datasets in `~/einstein_cnn/` (~15 GB) are cleanup candidates before Stage 3
checkpoints start accumulating — not deleted without approval.

**Frozen-benchmark model-evaluation count: still 0.** Every real-file touch this session was
image-statistics comparison (gate_stage0.py, side_by_side_real_sim.py), never a model prediction.

Stage 2 marked DONE in CLAUDE.md. Next: Stage 3 (CNN training) — a >30 min run, requires
Nurkyz's go per the standing rule.

---

## 2026-07-06 (cont.) — Stage-2 SLURM submission fixed (2 cluster constraints not in CLAUDE.md); generation LAUNCHED

Nurkyz attempted `sbatch generate_stage2.sbatch` directly and hit two undocumented cluster
policies, discovered and fixed here:
1. **Every partition (normal/a/b/c) requires `--gres=gpu:N`**, even for pure-CPU work (paltas
   generation uses no GPU) — added `--gres=gpu:1` (minimal request; flagged as cluster policy,
   not a design choice, since it occupies a shared GPU for CPU-only work).
2. **QOS "normal" caps `MaxJobs`/`MaxSubmit` at 8** — the planned single `--array=0-21` (22
   tasks) and even a naive 3×`--array=0-9` split both violate this ("Invalid job array
   specification" / `QOSMaxSubmitJobPerUserLimit`). Fixed: `submit_stage2.sh` now submits three
   SEQUENTIAL waves of ≤8 tasks each (`sbatch --wait`, which blocks until the whole array
   finishes) via an `OFFSET` env var that maps each wave's local array index back to the real
   shard id 0–21. Dry-run (`sbatch --test-only`) verified before the real launch.

**LAUNCHED** (nohup'd, survives SSH disconnect): wave 1 = shards 0–7 (job 46729), running on
nodes a1/a2/a4/a5/a6/a7 as of 23:27. Waves 2 (shards 8–15) and 3 (shards 16–21, incl. the 2
val shards) follow automatically once each prior wave's array fully completes. Monitor:
`squeue -u nurkyz`; `cat ~/cosmos_acs/tiles/submit_stage2.log`; per-shard SLURM output in
`~/paltas_shards/slurm_<jobid>_<idx>.out`.

Added to CLAUDE.md's paid-for-diagnoses list (#11, #12): this cluster's GPU-gres requirement
on every partition, and the QOS 8-job concurrency cap — both must be respected by any future
SLURM submission on this cluster.

---

## 2026-07-06 (cont.) — Plan rewritten in CLAUDE.md; Stage 2a complete (all re-gated); full generation STAGED, awaiting launch approval

**Plan reassessment (Nurkyz-requested):** CLAUDE.md staged plan rewritten to reflect reality —
Stages 0–1 marked DONE; the iteration law (any config change → 200-pilot → gate + side-by-side)
promoted to a named rule; ablation order fixed (θ_E prior, ePSF pools, backdrops, PSF form);
new paid-for diagnoses #7–10 added (retired kernel, independent-marginal anti-pattern,
aperture-vs-total, docs-promise-nonexistent-scripts).

**Stage 2a config changes (single patch, backup `.bak_stage2`), re-gated as pilot G:**
(1) PSF kernel selectable per-shard via LF_PSF_KERNEL env var; (2) mass center jittered
N(0, 0.05″), light center N(0, 0.02″) — exact-alignment cue removed; (3) source offsets widened
to U(±0.25″); (4) source selection opened to full COSMOS depth (mag 23.5, min sizes 20 px /
5 px flux radius — compact-source regime included); (5) γ ~ N(2.0, 0.15).
**Pilot G: ALL GATES PASS** — sky-RMS 1.08, peak/sky 726, θ_E flat [0.60, 2.20], acceptance
0.995; side-by-side shows realistic asymmetric arc segments (not only rings).

**PSF bank built:** 24 kernels from the benchmark-matched focus-diverse ePSF cubes (random
exposure/chip/position/rotation; `build_psf_bank.py` on the Mac; manifest in
`~/cosmos_acs/tiles/psf_bank/`), all wing-extended on the cluster. Kernels 00–19 = train shards,
20–21 = val (kernel-disjoint). Gotcha logged: `interp_epsf` silently returns None for FLOAT
detector coordinates — integers required.

**STAGED, NOT LAUNCHED** (auto-mode correctly blocked; per standing rule the sbatch script is
shown to Nurkyz first): `generate_stage2.sbatch` — array 0–21 on partition `normal` (20×5k train,
seeds 101–120; 2×2.5k val, seeds 901–902), per shard: noiseless render → hybrid combine →
preview 16 → delete npy; then `merge_hybrid_shards.py` → `train_hybrid_100k.h5` + `val_hybrid_5k.h5`.
Storage plan: ~13 GB peak, quota 75/100 GB — fits; old m2/m3-era datasets in `~/einstein_cnn/`
(~15 GB) flagged as cleanup candidates, pending Nurkyz approval.

---

## 2026-07-06 — ⛔ STAGE 1 COMPLETE: hybrid pilot F passes ALL gates, overlays agree

Pilot F (hybrid, joint empirical prior with aperture-to-total correction, seeds 9/10):
- **sky-RMS ratio 1.16 PASS** (up from E's 1.02 for a physical reason: brighter/bigger sim
  deflectors now leak envelope light into the corner "sky" boxes, exactly as the real ones do);
- **peak/sky median 607 PASS** (band 492–1798; was 353 in E, 307 in D);
- **θ_E U[0.60, 2.20] PASS**, 62% in benchmark band;
- **overlays agree**: median radial profile now lies on top of the real one (tiny deficit beyond
  ~2.5″); bright-tail of the pixel histogram matches; residual = modest excess of near-sky pixels
  in sim. Side-by-side (real_vs_hybrid_f.png): extended envelopes, arcs/rings, realistic texture.
  Remaining visible difference: real fields are somewhat busier with point sources.

Stage-1 iteration record: C (indep. mags, small Re) → D (data Re, peak/sky broke 307) →
E (joint pairs, aperture-mag bug, 353) → F (aperture-corrected totals, 607, ALL PASS).
Frozen-benchmark model-evaluation count: still 0 (all real-file usage was image statistics).

**Next (Stage 2, requires Nurkyz):** full-set design — size (100k/50k), sharding via SLURM
(script to be shown before launch, per standing rule), per-image PSF draws from the ePSF
library (benchmark-matched pool default + broad-pool ablation variant), decoupled light/mass
ellipticity + center jitter, source-selection cuts revisit (faintest_apparent_mag 22.5,
min sizes), disjoint-seed 5k sim-val split.

---

## 2026-07-06 (cont.) — Pilot E: aperture-vs-total magnitude bug found & fixed (analytic, not tuned)

Pilot E (joint empirical prior): sky-RMS **1.02** (best yet), θ_E PASS, but peak/sky only
353 (need ≥492). **Root cause found in our own measurement**: `measure_real_deflector_mags.py` /
`build_lens_light_prior.py` measured flux inside r=2″, but paltas `magnitude` is the Sérsic
TOTAL magnitude — for n=4 with Re≈2″ the 2″ aperture holds only ~50% of the light, so every sim
deflector rendered ~0.75 mag too faint (flux ×0.5 ≈ the missing peak/sky factor).

**Fix (analytic per-lens aperture-to-total correction, no hand-tuning):**
frac = gammainc(8, 7.669·(2″/Re)^0.25); mag_total = mag_aper + 2.5·log10(frac). Corrections
−0.57 (Re 1.43) to −1.00 mag (Re 2.92). Rebuilt table: total-mag median 16.80, ρ(mag, Re)
strengthened −0.29 → **−0.52** (correction couples size into brightness, as physics requires).
Residual known biases, accepted & stated: corner-sky over-subtraction (envelope light in the
"sky" boxes) biases mags slightly faint; arcs in the aperture bias slightly bright — opposing,
both small. Pilot F launched (seeds 9/10).

---

## 2026-07-06 — Hybrid pilot D: independent size fix regressed peak/sky; fix = JOINT empirical (mag, Re) prior via cross_object

Pilot D (data-driven R_sersic, independent of magnitude): sky-RMS 1.09 PASS, θ_E PASS, but
**peak/sky regressed to 307 (CHECK; real band lower edge 492)**. Cause: independent draws from
the two data-driven marginals produce faint+LARGE deflectors that real ellipticals don't have
(brightness–size correlation); spreading similar flux over ~2× the area halves the central peak.
Independent-marginal priors are hereby a known anti-pattern for lens light.

**Fix (applied):** joint empirical sampling. `build_lens_light_prior.py` writes
`lens_light_empirical.csv` — per-lens (aperture F814W mag from the real cutout, Bolton08 Re),
63 pairs, Spearman ρ(mag, Re) = −0.29. Config appends a `cross_object` sampler
('lens_light:magnitude,lens_light:R_sersic') drawing a random real pair with jitter (±0.3 mag,
×[0.85, 1.15] Re; backup `.bak_joint`). Verified: paltas 0.2.0 `cross_object` + comma-key
multivariate draws confirmed in installed source (sampler.py draw_from_dict); config imports and
draws sanely. paltas emits a one-time overwrite warning for magnitude/R_sersic — expected.
Hybrid pilot E launched (seeds 7/8) to re-gate.

---

## 2026-07-05 (late night, cont.) — Hybrid pilot C: all gates PASS; radial-profile gap root-caused to R_sersic; data-driven size prior applied

Hybrid pilot C (200 noiseless seed 3 + combine seed 4): **sky-RMS ratio 1.09 PASS** — and the
sim per-image RMS spread [0.0082, 0.0202] now brackets the real spread [0.0073, 0.0187] (the
per-image draw from the real distribution works, not just the median); peak/sky 497 PASS (band
lower edge — the wider mag prior adds faint deflectors, as it should); θ_E PASS; acceptance
0.995. Visual (real_vs_hybrid.png): field neighbors + correlated noise now present in sims;
qualitatively SLACS-like. Note: with no_noise generation, gate item 6's exposure-time suggestion
is IRRELEVANT (noise comes entirely from the combine step) — do not act on it for hybrids.

**Radial-profile gap SURVIVED the hybrid** (real above sim beyond ~0.3″; sim histogram excess of
near-sky pixels) → per the pre-registered trigger, checked R_sersic against data:
Bolton 2008 t0 `Re` cross-matched to all 63 benchmark SLACS: **median 1.98″, 16–84% [1.43, 2.92],
range [0.81, 5.85]**. The config prior (truncnorm loc 1.2″, scale 0.4) was ~40% too compact —
root cause found. Patched (backup `.bak_re`): truncnorm loc 1.98, scale 0.75, truncated
[0.4, ~7.0]. Hybrid pilot D launched (seeds 5/6) to re-gate with the corrected size prior.

---

## 2026-07-05 (late night) — Stale-preview scare resolved; visual real-vs-sim analysis; Stage 1.2 applied; Stage 1.3 hybrid built & launched

**Scare resolved (important for future sessions):** a report of "square + no arc" in
`~/paltas_smoke8/preview_*.png` turned out to be a STALE artifact — that folder is dated Jul 2
and its embedded config copy loads the retired `acs_psf.npy` at 420 s. It predates every fix in
this log. Current-session outputs live in `~/paltas_smoke_epsfext` / `~/paltas_pilot200b`.
Lesson: check the embedded config copy + folder date before judging any preview. Consider
deleting or archiving `~/paltas_smoke8` (not done — ask Nurkyz).

**Visual reference analysis** (`side_by_side_real_sim.py`, new tool in ~/cosmos_acs/tiles;
`real_vs_sim.png`, identical asinh stretch): matches — deflector size/concentration, arc surface
brightness (2/8 sims show obvious rings, like the real fraction), noise level. Gaps, each mapped:
(1) real frames full of faint field neighbors, sims sterile → Stage 1.3; (2) real envelopes more
extended → Stage 1.2 + 1.3; (3) real morphology diversity (e.g. J1103+5322 is disky/inclined) vs
always-spheroidal Sérsic → known parametric limitation, Path-B escalation criterion unchanged.
Decision reaffirmed: NO return to the native forward-operator generator (reasons of 2026-07-02
stand; current pipeline passes gates the old one never saw).

**Stage 1.2 APPLIED:** `measure_real_deflector_mags.py` on the 63 real SLACS cutouts (calibration
usage; model-eval count still 0): apparent F814W median 17.50, 16–84% [16.92, 18.16], range
[15.93, 19.32]. Config lens-light magnitude prior U[16.5, 18.5] → **U[15.6, 19.7]** (observed
range padded 0.3 mag; backup `.bak_mag`). R_sersic prior left unchanged for now — revisit against
Bolton 2008 R_e only if the radial-profile gap survives the hybrid.

**Stage 1.3 BUILT (now the default design):** `config_lensfusion_acs_nonoise.py` (module-level
`no_noise = True` wrapper) + `hybrid_combine.py`: hybrid = noiseless paltas + random real empty
COSMOS cutout + Gaussian topup, with per-image target sky RMS DRAWN from the empirical real-SLACS
robust-sky distribution (domain randomization over the real noise range, per MASTER_PLAN 1.1+1.3).
Units verified compatible before adding: both terms drizzled ACS F814W e-/s, 0.05″/px, ZP 25.94
(harvest_empty_cutouts.py median-subtracts and resamples; paltas output_ab_zeropoint=25.94).
Approximation stated: no Poisson on lensed flux (sky-dominated; goes in the paper). 200-image
hybrid pilot chain launched (seed 3 gen / seed 4 combine) → previews → gate → real-vs-hybrid
side-by-side.

---

## 2026-07-05 (night, cont.) — Stage-1 noise calibration: ALL numeric gates PASS at exposure_time 675 s

Pilot A (200 img, seed 1, exposure_time 420 s): sky-RMS ratio sim/real 1.27 → **marginal FAIL**
(target 0.8–1.25); peak/sky PASS (560 in real band 492–1798); θ_E PASS (U[0.61, 2.19], 63% in
benchmark band). Acceptance 1.000/200 with mag_cut confirmed ACTIVE — resolved as physically
real, not a bug: θ_E ≥ 0.6″ with ≤0.3″ source offsets keeps essentially every source inside the
caustic; 16-panel previews show genuine lenses throughout, no blobs (diagnosis #5 satisfied by
inspection, not assumption).

One change (gate's own suggestion): exposure_time 420 → 675 s (`.bak_exp420`).

Pilot B (200 img, seed 2): **sky-RMS ratio 0.941 PASS; peak/sky 628 PASS; θ_E PASS; acceptance
0.995** (a rejection occurred — cut demonstrably alive). Overlays: histogram modes now aligned;
peak/sky distributions overlap; radial profile — sim matches real at r ≲ 0.3″ but real rides
above sim at larger radii. **Interpretation (logged as the next Stage-1 target, not hidden):**
the remaining gap is missing extended deflector envelopes + real field neighbors, exactly what
Stage 1.2 (data-driven deflector magnitude/R_sersic prior via `measure_real_deflector_mags.py`)
and the now-default Stage 1.3 real-backdrop hybrid supply. Noise is calibrated; do NOT retune
exposure_time further until 1.2/1.3 are in (598 s re-suggestion is within the randomization
band planned for Stage 2 anyway).

Benchmark usage note: gate comparisons use image statistics of `real_slacs_images.h5` only
(planned Stage-1 calibration); model-evaluation count remains 0.

---

## 2026-07-05 (night) — Real STScI ePSF retrieved & adopted (extension validated); two-pool PSF design logged; Stage 1 pilot launched

**Rulings by Nurkyz:** (1) retrieval must support TWO pools — benchmark-matched ePSFs AND a broad
archival pool excluding the benchmark — for a later PSF-source ablation (circularity rationale
logged in PAPER_PLAN.md "PSF-source design and ablation"); (2) sequencing changed: ePSF swap
FIRST, then the 200-image pilot — no noise calibration on the Moffat interim (its lower core
concentration would shift peak/sky and force calibrating twice). Moffat was validated but never
used for calibration; retired same day.

**Retrieval built and run** (`epsf_retrieve.py` in the project folder; venv `.venv_epsf` on the
Mac — acstools 3.8.2, astroquery 0.4.11; NO cluster installs):
- Benchmark mode: rootnames resolved from MAST per real_lens_labels.csv coordinates (ACS/WFC
  F814W FLC exposures). Note: benchmark exposures are 1566–2200 s (prop 10886 etc.), not only
  420 s snapshots. Some exposures legitimately have no ePSF solution in the STScI service
  ("no_epsf_returned") — recorded in manifest_benchmark.csv, not an error.
- Broad mode: random 30-day windows across 2003–2022, one exposure per observation, 2′
  exclusion around every benchmark lens → manifest_broad.csv.
- ePSF cubes verified: (90, 101, 101) float32, 4× supersampled, filenames encode per-exposure
  focus (F01.6–F13.0 seen — real focus diversity confirmed).

**Kernel adopted into the config** (backup `.bak_epsf`): `interp_epsf(..., 2048, 1024, 'WFC1',
pixel_space=True)` on j9op01l7q → 23×23 detector-sampled kernel (centered; FWHM 1.59 px = 0.080″
— genuinely sharper than the 0.09–0.10″ rule of thumb at native sampling; 55 tiny negative
pixels = normal ePSF ringing, lenstronomy warns but accepts).
- First smoke: discontinuity 13.9 (>8–10 threshold) BUT no crisp square visually — the 23 px
  support step plus real speckle wings at the measurement radius. Resolved by wing extension,
  which is legitimate on this kernel (inspector: monotonic profile over all 11 rings, pos_frac
  ~1.0, data-driven r0=7, alpha=−2.54 — real wings, unlike the retired stamp).
- `fix_psf_kernel.py --factor 2.0` (deployed version lacks the logged `--r0/--alpha` hardening —
  second spec-vs-reality gap after the missing inspector; its internal defaults r0=8, fitted
  alpha=−2.47 were verified sound for THIS kernel; added wing flux ≈3.7%, under the 10% bar the
  hardened guard would enforce) → `acs_psf_epsf23_extended.npy` (47×47, FWHM preserved, edge=0).
- Re-validation with extended kernel: discontinuity **13.9 → 2.3** at the old edge radius;
  previews clean under all three stretches (same seed 42 as the Moffat smoke: sharper cores,
  crisp arcs, no square). **Config now runs the real, extended, focus-diverse ePSF.**

**Stage 1 pilot launched** (nohup chain on the cluster): 200 images seed 1 → three-stretch
previews → pilot200.h5 → `gate_stage0.py` vs real SLACS statistics. Note on benchmark usage:
the gate compares IMAGE STATISTICS (sky RMS, peak/sky, normalized histograms) of sim vs
`real_slacs_images.h5` — planned Stage-1 calibration usage, no model evaluation. Frozen-benchmark
model-evaluation count this session: still 0.

---

## 2026-07-05 (evening) — Moffat interim PSF adopted & validated: square GONE; STScI ePSF = required gate; Stage 1.3 promoted to default

**Rulings by Nurkyz:** (1) Moffat interim kernel now. (2) Do NOT wait on/contact Sam — the real-PSF
source is STScI's public focus-diverse ePSF library (ACS ISR 2018-08, ISR 2023-06;
acspsf.stsci.edu), and adopting it is a **required gate before generating the full (non-pilot)
training set**, not optional. (3) **Stage 1.3 (noiseless paltas render + real empty-cutout
backdrop) is promoted from optional to DEFAULT** for the main training set — explicitly a
paltas-physics + real-backdrop hybrid, NOT a SIMCT revival (SIMCT stays retired).

**Moffat interim, done and validated:**
- `make_acs_psf.py --mode moffat --size 51 --fwhm_arcsec 0.10` → `acs_psf_moffat51.npy`
  (verified: centered, FWHM 2.00 px = 0.100″, smooth wings, no zeros).
- Config patched to the new kernel (backup: `config_lensfusion_acs.py.bak_moffat`); comments
  updated to mark the kernel INTERIM pending the ePSF gate.
- 8-image smoke (seed 42): acceptance 1.000 over 8 tries (plausible at n=8 with mag_cut active;
  the 200-pilot will measure it properly). Three-stretch previews: bright SLACS-like lens light
  in 8/8, arcs/rings clearly visible in ≥4, faint in the rest (realistic regime), **no square
  under any stretch**.
- `diagnose_psf_square.py`: discontinuity ratio **107.6 → 1.7** (truncation threshold ~8–10);
  no square outline in the P−G difference panel. Old diagnostic preserved as
  `psf_square_diagnostic_BEFORE_moffat.png`. → **Stage 0 (kill the square) is closed.**
- Frozen-benchmark evaluation count this session: 0.

**STScI focus-diverse ePSF — process investigated (nothing pulled at scale yet):**
- Access: `acstools ≥3.7.0`, `from acstools.focus_diverse_epsfs import psf_retriever,
  multi_psf_retriever, interp_epsf`; or the webtool acspsf.stsci.edu. No auth/registration.
- Input: per-observation rootname (ipppssoot, FLC-based; association IDs not supported).
  Output: one FITS per rootname, 101×101×90 float32, **4× supersampled**, 90 ePSFs on a 9×10
  grid spanning both WFC chips (~3.7 MB each). `interp_epsf(..., x, y, chip,
  pixel_space=True)` returns the detector-sampled (0.05″/px) PSF at any location.
- Adoption plan (pending execution): retrieve ePSFs matched to the actual SLACS benchmark
  exposures' rootnames (focus-matched, F814W) and build the training PSF prior by randomly
  drawing + rotating from that per-observation ePSF set. Retrieval runs on the Mac + scp —
  no cluster installs needed.
- Caveats logged now: (a) ePSFs describe FLC (native, distorted) frames; the benchmark cutouts
  are drizzled `_drc` products — small, acceptable mismatch, to be stated in the paper;
  (b) detector-sampled ePSF has ~25 px support → re-run `diagnose_psf_square.py` on it (clean
  wings should make the edge step negligible; if not, `fix_psf_kernel.py` extension is now
  legitimate — the 2026-07-03 method was sound, it was the noise-dominated stamp that wasn't).

---

## 2026-07-05 (later) — Stage 0a run; VERDICT: acs_psf.npy unusable, wing extension is dead for this stamp

**Tooling gap closed:** `inspect_psf_kernel.py`, specified in the 2026-07-03 entry as the required
pre-step, did not actually exist anywhere (cluster or Mac). Built to spec and deployed to
`~/cosmos_acs/tiles/` (read-only inspector; also writes `psf_kernel_profile.png`).

**Findings on `acs_psf.npy`** (27×27, empirical, Jun 18):
- Peak pixel off-center by 1 px: (12,13) vs geometric center (13,13) — any use of this kernel
  shifts every image by ~1 px during convolution.
- FWHM 1.57 px = 0.078″ at 0.05″/px — slightly sharper than the ACS F814W truth (~0.09–0.10″).
- Pixel-scale-mismatch hypothesis (stamp extracted at the 030mas tile's native 0.03″/px) RAISED
  AND CLEARED same session: 0.03″ sampling would imply an impossible 0.047″ FWHM.
- **Decisive, σ-estimate-independent:** encircled energy is 0.146 at r≤1.5 px, 0.29 at r≤0.23″
  (real ACS/WFC F814W: ~0.8 at 0.25″), 0.58 at 0.48″. Ring medians sit FLAT at ~1.5–4.6% of peak
  from r=5–12 px with 30–60% zero fractions — a noise/contamination plateau, not PSF wings (real
  wings at 0.5″ are ~1e-4 of peak). ⇒ ~70% of the kernel's flux is plateau. Convolution with this
  kernel smears ~70% of ALL light into a 1.3″ box — this is not only the square artifact but a
  plausible main cause of "generated images look strange" overall.
- Data-driven r0 = 1 px ⇒ `fix_psf_kernel.py` wing extension has nothing real to extend from.
  The 2026-07-03 contingency ("wings are noise → get a better stamp") is now the confirmed branch.
- Noise-estimate caveat logged honestly: outer-shell clipped-Gaussian σ ≈ 7.8% of peak here vs
  0.5% quoted on 2026-07-03 (that earlier figure came from the border frame, which is 99% zeros
  and unusable as a σ estimator). The verdict does not depend on which σ is right.

**PENDING NURKYZ'S RULING (Stage 0 fork):** replace the kernel instead of fixing it —
(a) interim: Moffat ≥51 px via existing `make_acs_psf.py --mode moffat` (smooth wings, no
truncation square; loses diffraction spikes), (b) proper: TinyTim or star-stack ACS PSF ≥51 px
(the standing ask to Sam, now urgent), or (c) attempt a better empirical extraction. No generation
runs until ruled.

**Config state confirmed same pass:** `ApparentSersic` present; `mag_cut = 3.0` present; config
loads the original `acs_psf.npy`; no `*_extended.npy` exists; CleanCOSMOS patch not applied
(no `.bak2`) — consistent with the planned order (hygiene after PSF fix).

**Housekeeping:** the updated memory files had arrived locally as browser-download names
(`CLAUDE (1).md`, `DECISIONS_LOG (12).md`) → renamed to canonical `CLAUDE.md` / `DECISIONS_LOG.md`
so future sessions actually auto-load them.

---

## 2026-07-05 — Pipeline fork resolved (paltas confirmed); benchmark evaluation-count gap disclosed; cluster ops corrections

**Fork:** a stale "Project Instructions" document (pre-2026-07-02, describing CNN training data
generated via LensFusion's native `forward_operator` + IllustrisTNG κ + COSMOS, with κ̄=1 labels
and Gaussian PSF/noise) surfaced again alongside this log. **RULING: `DECISIONS_LOG.md` /
`PAPER_PLAN.md` / `MASTER_PLAN.md` govern.** That document's data-generation section (native
forward operator) is SUPERSEDED by the 2026-07-02 paltas pivot — reasons already logged there:
fixed Gaussian PSF and synthetic noise don't carry a real telescope's fingerprint, and κ̄=1 labels
carry a definitional offset from the SIE b_SIE benchmark ground truth that paltas's SIE labels
remove outright. That document's terminology definitions (source/lens/lens light/convergence)
and the Phase 2 non-differentiability caution (`einstein_radius_hard`) remain valid background
and are NOT superseded — only the data-generation method is.

**Disclosed gap (not yet closed):** an orientation pass over the cluster found existing
prediction CSVs and failure analyses against `real_slacs_images.h5` (62) and `real_s4tm_images.h5`
(40) dated "late June" — i.e. the frozen benchmark has already been evaluated an **unrecorded**
number of times in sessions that predate this log's evaluation-count discipline. Logged here as a
known integrity gap, not swept under anything: going forward, every evaluation against either
file must be logged here with a running count (see MASTER_PLAN 3.4). The pre-log count cannot be
reconstructed; treat any m3-era "before" numbers already in MODELS_AND_RESULTS.md as historical
record, not as a first evaluation.

**Cluster ops corrections (from a Claude Code orientation pass — supersede MASTER_PLAN's tmux
instructions):**
- Login shell is **csh**, not bash. Every remote one-liner needs `bash -lc '...'` wrapping;
  bare `cmd 2>&1` fails with "Ambiguous output redirect" under csh.
- **No tmux/screen on the login node.** It is a SLURM head node (`sbatch`/`squeue` present,
  `nvidia-smi` unavailable on the head node itself, compute nodes a1–a6). Long jobs (pilot
  generation beyond a few minutes, training, full dataset generation) must go through **SLURM
  batch jobs**, not tmux.
- **Quota: 75/100 GB used** at time of check. A ~3 GB pilot dataset fits; do not accumulate
  multiple full (50–100k image) datasets without deleting superseded ones first.

---

## 2026-07-03 (later) — PSF truncation CONFIRMED on cluster; kernel quality flagged; fix hardened

**CONFIRMED** by `diagnose_psf_square.py` on the real config: kernel is 27×27 px, predicted
square width 26 px = 1.30″ matches the previews, difference panel shows a crisp square present
under the pixel PSF and absent under a Gaussian PSF, discontinuity ratio 107.6. Bonus finding
from the same run: the Gaussian-PSF row shows clean arcs/rings — generation physics is healthy.

**Kernel-quality finding (new):** `edge_max/peak = 1.59e-2` with `edge_median/peak = 0`
indicates the kernel is an empirical star stamp with a noise floor of order 0.5% of peak,
background-subtracted with negatives clipped to zero (≈half the outskirt pixels exactly zero,
rest up to ~3σ). The visible square plateau is likely core flux scattered by this *noise floor*,
truncated at the stamp box. The kernel itself is now a known weak link — parallel action item:
ask Sam for a larger/cleaner ACS PSF stamp (TinyTim model or star stack).

**Fix hardened before use** (failure mode found in sandbox): naive wing extension of a
noise-dominated stamp fits its "wing slope" on noise (flat), propagates the noise floor outward,
and can inject tens of percent spurious flux (20% on a mock of the suspected regime), wrecking
kernel photometry on renormalization. `fix_psf_kernel.py` now has: adaptive r0 (largest ring
with ≥60% positive nearest-neighbour samples), max-blend filling of zero-clipped holes inside
r0, alpha capped at −2.0 with a warning when the fit is shallower (unphysical), `--r0`/`--alpha`
manual overrides, and a hard ABORT if the extension would add >10% flux (override `--force`).
**Required pre-step:** `inspect_psf_kernel.py` prints the per-ring profile, zero fractions,
noise estimate, and the last signal-dominated radius (the data-driven `--r0`). Rule: inspect,
then fix with data-chosen parameters, then validate visually (smoke + preview +
`diagnose_psf_square.py --half 13`).

---

## 2026-07-03 — Square artifact: stamp hypothesis RETRACTED; new diagnosis = truncated PSF kernel support

**RETRACTED:** the COSMOS-stamp-footprint explanation for the central square.
`diagnose_components.py` disconfirmed it: row B (arc + noise, **no lens light**) shows clean
Einstein rings and **no square** — the square travels with the lens light — and the measured
stamp-noise/detector-noise ratio is 0.38 (subdominant). `CleanCOSMOS` is therefore downgraded
from "the square fix" to **optional hygiene** (it still removes the large soft stamp-footprint
boundary visible in the noiseless C/D rows and ~7% in-quadrature noise inflation inside the
footprint; cheap and harmless, apply after the PSF fix).

**New diagnosis (sandbox-reproduced):** the square is the **truncated support of the pixel PSF
kernel**. Convolution with a finite kernel spreads light only within the kernel's box; the very
bright, quasi-point-like Sérsic core therefore produces a kernel-shaped plateau of scattered
wing light with a hard step exactly at the kernel half-width. Evidence: square appears only when
lens light is present; the `kernel_point_source` RuntimeWarning confirms a pixel kernel is in
use; the artifact was reproduced in a controlled sandbox with a synthetic truncated-wing kernel,
and the discontinuity localizes exactly at the kernel half-width in the pixel-vs-Gaussian
same-draw difference. **Confirmation on our config is pending** `diagnose_psf_square.py`, whose
decisive checks are (1) kernel width == square width in the previews and (2) the square present
under the pixel PSF, absent under a Gaussian PSF, in the same-draw difference panel.

**Fix path (validated in sandbox, in order tried):**
- Edge taper alone: **REJECTED by experiment** — the tapered ramp is still far steeper than a
  real PSF wing decline; the soft square survives. (`make_tapered_psf.py` never shipped.)
- **Adopted:** `fix_psf_kernel.py` — extend the kernel to ~2× size by per-angle power-law
  continuation of the wings from an inscribed circle (r0 = half−3), taper only the new far edge
  where wing values are tiny, renormalize to original total. The extended kernel's profile is
  smooth through the old edge (no localized curvature spike); the residual far boundary sits at
  2× the radius with ~4× fainter wings.
- Caveats (recorded, not hidden): wings beyond r0 are a power-law *model*, not data; diffraction
  spikes are continued in angle but approximate beyond r0. Gold-standard alternative if far-wing
  realism ever matters: a genuinely larger real ACS PSF stamp (ask Sam). Larger kernels slow
  generation somewhat.

**Methodology lesson (logged for reuse):** automated numeric verdicts on *noiseless* difference
images are brittle here — the smooth pixel-vs-Gaussian core mismatch sets a curvature floor, and
arcs landing near the measurement radii add variance. Decisive checks are the kernel-width match
and the visual same-draw P/G/difference panel; the discontinuity ratio is supporting evidence
only. The harm criterion for any residual artifact is amplitude vs. sky RMS, which Stage-1 noise
calibration will also raise.

---

## 2026-07-03 — Lens-light fix CONFIRMED on cluster; new issue: central square = suspected COSMOS stamp footprint

**Confirmed:** `ApparentSersic` patch works in production — smoke-test previews show bright
SLACS-like lens light in all 8 images. A faint arc is visible in at least one draw (#7), so
lensing is functioning.

**New issue:** a sharp-edged bright square/rectangle at image center in every draw.

**Code-inspection facts (verified in paltas 0.2.0 source, not hypothesis):**
- `COSMOSCatalog.image_and_metadata()` loads raw stamps with **no background subtraction**
  (optional Gaussian smoothing only). COSMOS stamps therefore carry their own HST sky noise.
- lenstronomy `INTERPOL` renders **zero outside the stamp footprint** → the stamp appears as a
  noise plateau with a hard boundary wherever it maps in the image plane.
- COSMOS imaging is deeper than SLACS snapshots, so with detector noise set too low (Stage-1
  calibration not yet done), stamp noise stands **above** the detector sky → visible rectangle.
  The square's visibility is itself evidence the current detector noise is too low.
- The source-flux pipeline (zeropoint correction, z-scaling, k-correction) is physically sound;
  0.2.0 also has an optional `source_absolute_magnitude` for explicit arc-brightness control.

**Hypothesis status:** stamp-footprint explanation is highly likely but UNCONFIRMED until
`diagnose_components.py` output is in (renders full / arc-only / arc-noiseless / unlensed-source
variants; the unlensed variant shows the undistorted stamp, and the script prints the
stamp-noise vs detector-noise ratio). Rule: run the diagnostic BEFORE applying the fix.

**Prepared fix (pending diagnostic):** `CleanCOSMOS` subclass in the config (same pattern as
`ApparentSersic`) — sigma-clipped border-median background subtraction + 6-px cosine edge
apodization per stamp. Applied by `patch_config_clean_cosmos.py` (backup `.bak2`, prints diff).
Unit-tested: background recovered exactly, stamp edges → 0, galaxy flux preserved. Caveat:
border subtraction can clip a small amount of real galaxy wing flux — negligible for a training
prior. Stage-1 noise calibration is the second half of the fix (buries residual stamp noise).

**Explicitly NOT a reason to rethink the generator:** faint arcs are the realistic regime (real
SLACS arcs are faint); arc visibility is arbitrated by the Stage-0 gate metrics and the
side-by-side with real cutouts, not by eye on previews.

---

## 2026-07-02 — RESOLVED: missing paltas lens light = version-dependent `magnitude` convention

**Root cause (verified by source inspection of both versions):** paltas **0.2.0** (what was
installed) treats `SingleSersicSource.magnitude` as an **ABSOLUTE** magnitude, converting via
`absolute_to_apparent(magnitude, z_source)` + a k-correction. Feeding it apparent-style values
(16.5–18.5) adds a distance modulus of ~+42 at z=0.5 → the lens light renders at effectively zero
flux. Arcs visible, lens invisible — the exact preview symptom. paltas **0.1.1** uses the
**APPARENT** convention (`magnitude` → `mag_to_amplitude` directly).

**Failed remedy (logged for the record):** downgrading to paltas 0.1.1. Correct diagnosis, wrong
remedy for this environment — 0.1.1 calls `ProfileListBase._import_class`, removed from the
installed lenstronomy → `AttributeError` on the first draw. Reverted same day.

**Adopted fix:** keep **paltas 0.2.0** (compatible with the env's lenstronomy) and define an
**`ApparentSersic`** subclass *inside `config_lensfusion_acs.py`* that overrides `draw_source()`
with the 0.1.1 apparent-magnitude logic; `lens_light` uses `ApparentSersic`. Applied by
`patch_config_apparent_sersic.py` (makes a `.bak`, prints a diff, aborts on any unexpected
pattern). **Verified in a controlled sandbox experiment** (paltas 0.2.0 + lenstronomy 1.13,
identical seeds): stock lens light core/edge ≈ 2–3 (absent) → ApparentSersic core/edge ≈ 165–320
(bright, SLACS-like).

**RETRACTED (earlier fallback hypotheses):** the lens-light `z_source: 0.5` and the combined
`'e1,e2'` key are **not** bugs. In both paltas versions the lens-light redshift list is discarded
by `config_handler` (`..., _ = draw_source()`), and `'e1,e2'` with `dist.EllipticitiesTranslation`
is the standard pattern used by paltas's own Horton example. `diagnose_paltas_lens_light.py` is
superseded by the three-stretch preview + `gate_stage0.py` peak/sky metric (same estimator applied
to sim and real).

**Environment pins (do not violate):**
- paltas must be installed with `--no-deps` (its `numpy<=1.24` pin would otherwise fight the env).
- Do **not** upgrade lenstronomy: ≥1.14 renames `DataAPI(numpix=…)` → `num_pix`, which breaks
  paltas 0.2.0; ≤1.11 uses `numba.generated_jit`, removed in newer numba. The working band around
  the current install is ~1.12–1.13.
- If `SingleSersicSource` is ever used as a *source* in this config, its `magnitude` is ABSOLUTE
  under stock 0.2.0 — decide the convention explicitly at that time. `COSMOSCatalog` (the current
  source) is unaffected: it uses the catalog's own photometry.

---

## 2026-07-02 — Objective sharpened to a standalone paper

**Decision:** Reframe the project from "θ_E CNN as a LensFusion Phase-2 helper" to a **standalone
paper on accurate strong-lensing parameter prediction that beats the literature** (Cao et al. 2025)
on the frozen real-lens benchmark. Phase-2 integration and the compact-source result become
downstream contributions, not the headline. See `PAPER_PLAN.md`.

---

## 2026-07-02 — PIVOT: bespoke SIMCT generator → paltas (Path A)

**Decision:** Retire the hand-built composite generator and adopt **`paltas`** (Wagner-Carena et al.,
on `lenstronomy`) for the training set.

**Why the bespoke generator was the wrong architecture (what didn't work):**
- It **hand-balanced flux ratios in arbitrary electron units** (lens peak/sky, arc snr) to *fake*
  realism, instead of working in physical magnitudes where brightnesses fall out correctly.
- Its **lens light was synthetic or mis-sized.** Every attempt to source real lens light from a
  single COSMOS tile failed for the same reason (below).

**Why paltas:**
- Real COSMOS F814W source galaxies (2262 GREAT3-vetted), physically lensed via lenstronomy.
- Physical magnitudes + HST-calibrated noise → no flux hand-tuning.
- **SIE θ_E labels** → match the SLACS b_SIE benchmark, resolving the κ̄=1-vs-SIE offset.
- **Direct control of the θ_E prior** (config samples θ_E ~ U[0.6, 2.2]) → attacks prior-pull at the
  source; **θ_E² reweighting no longer needed.**
- **Lens size is a parameter** (`R_sersic`) → the "lens too small" failure cannot recur.

**Known residual gap:** paltas lens light is a **parametric Sérsic**, not a real elliptical image.
Accepted for now; to be tested against the real-lens failure analysis, with data-driven injection
onto real deflectors (Path B) as the escalation if needed.

**Status:** paltas/galsim/lenstronomy installed (Py3.8). COSMOS_23.5 sample downloaded (4.2 GB,
Zenodo; required a resumable `wget -c` in tmux after repeated ~79% drops). 64-image test run
succeeds (acceptance 1.0). Config `config_lensfusion_acs.py` matched to the benchmark grid
(128 px @ 0.05″/px = 6.4″, real ACS PSF, ACS F814W noise). **Open:** lens light not visible in
the preview — under diagnosis (`diagnose_paltas_lens_light.py`); leading hypothesis is a preview
color-scale artifact (bright Sérsic saturating one pixel), fallback is a config bug
(`lens_light` `z_source: 0.5` deviates from the working Horton example's `None`; and the
combined `'e1,e2'` key).

---

## 2026-07-02 — Bespoke SIMCT attempts (all superseded by paltas)

Each iteration fixed the previous defect and revealed the next; all diagnosed with
`diagnose_simct.py` (arc geometry, PSF FWHM, lens peak/sky, arc thickness).

- **v0 (m3's original generator):** clean arc on empty sky, Gaussian PSF, white noise.
  *Verified good:* arc geometry (rendered radius / θ_E = 1.01), PSF (FWHM 0.10″).
  *Bad:* lens light absent/too faint; unrealistic noise/PSF → the OOD gap that fails on real data.
- **v1 (harvested COSMOS ellipticals as lens light):** *Failed* — field ellipticals are
  **peak/sky ≈ 39** vs. real SLACS **93–197**, i.e. far too faint; the arc (snr 5–40) rivaled the lens.
- **v2 (signal/noise-separated rescale to real peak/sky):** brightness fixed and verified
  (rescale lands peak/sky at target), but galaxies were still **too small** (compact, high-z field
  ellipticals render as bright dots, not SLACS-sized glows) and the **background was patchy**
  (crowded-field neighbors leaking through the `cutout − smooth` residual).
- **v3 (matched IllustrisTNG lens_light + empty backdrop):** built, but not adopted — the user
  correctly identified the whole hand-tuned-composite architecture as the deeper problem, prompting
  the paltas pivot before v3 was validated.

**Root cause across all bespoke attempts:** a single COSMOS tile does not contain enough massive,
nearby, SLACS-sized ellipticals, and compositing in arbitrary units forces unphysical hand-tuning.

---

## 2026-07-02 — Real-lens failure of m3 fully diagnosed (paper result)

**Finding:** m3's real-lens failure is **prior-pull** — predictions collapse toward a ~0.95–1.0″
attractor. Signed bias sweeps **positive→negative across θ_E** in both samples (SLACS tertiles
+1% → −11% → −24%; S4TM +27% → −8% → −22%), crossing zero at the predicted median. All per-feature
Spearman |ρ| < 0.3 ⇒ **systemic, not image-specific**. It is **arc-realism, not arc-visibility**
(J0044+0113 has obvious arcs yet lands at +74%). ⇒ Fix = training-distribution realism; **not**
architecture; **not** lens-light subtraction (m3 reads the arc).

**Locked baseline ("before"):** SLACS N=62 median −7.9%, R² −1.02, MAE 0.274, fail 55%;
S4TM N=40 median −5.3%, R² −0.53, fail 68%.

---

## Standing conventions and precedents (still in force)

- **Benchmark frozen:** 62 SLACS + 40 S4TM, F814W, Bolton 2008 b_SIE. Drop only broken cutouts,
  never faint-but-real lenses (that would bias the failure rate).
- **Label convention:** report against b_SIE directly; paltas SIE labels remove the offset.
- **Detectability:** magnification cut μ≥3 is ineffective — use Gawade geometric cut
  (separation > 0.5″ + second-image brightness). paltas's own selection handles this.
- **Label integrity:** join by `kappa_index`, never row position. (Moot with paltas: label is
  per-image `main_deflector_parameters_theta_E` in `metadata.csv`.)
- **Augmentation:** flips/rotations must transform (e1, e2) consistently; θ_E is invariant. A prior
  augmentation bug that scrambled orientation labels was caught and fixed.
- **Phase 2:** `einstein_radius_hard` is non-differentiable; a soft θ_E estimator is required for
  the sampler. Do not add the penalty inside the differentiable sampler without it.
- **Env:** Python 3.8 — no backslashes inside f-strings; `pip install --break-system-packages` when needed.
- **Practice:** preview/diagnose before committing compute; exact copy-paste commands; downloadable
  scripts over heredocs; flag uncertainties explicitly.
