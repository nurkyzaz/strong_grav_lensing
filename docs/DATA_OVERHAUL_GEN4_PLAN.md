# GEN4 — PHYSICALLY SELF-CONSISTENT GENERATION PROGRAM (the data overhaul)

Date: 2026-07-10 (night). Trigger: Nurkyz — "big substantial changes of the whole image
generation, no quick fixes"; eval #16 proved the residual failures are data-side.
Status: PROPOSAL for Nurkyz's ruling. DECISIONS_LOG.md stays authoritative.

---

## 0. The organizing insight (from eval #16 + literature research, 2026-07-10)

Eval #16: with a FLAT training prior and zero in-distribution bias, real small-θ_E
lenses still fail 62% with a +29% pull. When the arc carries no usable signal, a
physical model — or a human — falls back on the deflector's LIGHT: luminosity and
size predict σ_v (Faber–Jackson / fundamental plane), and σ_v sets θ_E. **Our
generator actively destroys that channel**: θ_E is drawn independently of the
deflector stamp, so a bright fat LRG carries θ_E=0.5″ as often as 2.2″ and the
network provably learns to ignore the light. The two most successful literature
recipes both KEEP the channel:

- **HOLISMOKES / Cañameras (the most successful lens-search sims):** cutouts centred
  on real SDSS galaxies with MEASURED σ_v and z; the SIE mass is computed from that
  same galaxy's σ_v; lensed COSMOS sources painted on top. Light and mass belong to
  the same physical object by construction.
- **LEMON (Q1):** lens light (mag, Re, PA, q, z) drawn from a Flagship-simulation
  galaxy; θ_E normalised from the stellar mass + DM fraction of the SAME galaxy →
  the amplitude channel (brighter/bigger ↔ larger θ_E) is present in training.
  (Their mass–light ELLIPTICITIES are deliberately unaligned — verified from the
  paper — so the orientation channel is absent; the amplitude channel is what
  matters for θ_E.)
- **Ours:** best-in-class realism per ingredient (real sources, real deflector light,
  real backdrops, real focus-diverse PSFs, measured populations) but the ingredients
  are statistically INDEPENDENT — physically impossible combinations dominate.

**GEN4 = keep the hybrid realism, restore the physics that ties the ingredients
together.** This subsumes the S4TM fix, the mass–light alignment axis, and the
small-θ_E problem under one design.

## 0b. "If we copy LEMON exactly, do we get their numbers?"

Mostly yes — ON THEIR VALIDATION. Their validation images share the degradation
operator, the selection function, and the population priors with their training set;
replicating all of that reproduces their Table 3 more or less by construction. But it
buys nothing we want: fully synthetic (no real-image realism), single instrument, no
native-HST capability, and their own real-Euclid check (R²=0.71 vs traditional models
on 354 Q1 lenses) shows the ceiling of that approach. Our goal is ONE physical
population model with THREE renderings (native HST / Euclid / Roman) that matches or
beats them in their domain while doing what they cannot elsewhere. Copy their good
idea (population self-consistency), keep our realism advantages.

---

## 1. GEN4 pillars (each = "best available" for one ingredient)

### P1 — Self-consistent deflectors (THE pillar; subsumes S4TM + mass–light + small-θ_E)
1. **Rebuild the deflector library around galaxies with known kinematics.** Our LRG
   stamps come from SLACS-parent (SDSS spectroscopic) targets → σ_v and z_l are
   QUERYABLE for the existing 49; expand to **~200–500 stamps spanning σ_v ≈ 120–350
   km/s** (covers S4TM's lower-mass population natively) from HST-archival
   early-types with SDSS spectroscopy; where σ_v is missing, fundamental-plane
   photometric σ_v with its scatter carried as label noise.
2. **Per image:** pick a library galaxy (its stamp = the lens light, its σ_v/z_l =
   the mass); draw z_s from the source population; **θ_E follows from σ_v and
   (z_l, z_s)** — no independent θ_E prior at all.
3. **Mass shape = light shape ⊕ measured scatter:** q_mass and PA from the stamp's
   measured light shape, perturbed by the empirical SLACS misalignment distribution
   (|ΔPA| ~ 10°, q_mass–q_light relation) — alignment realism with honest scatter,
   not the fake perfect alignment and not our current full decorrelation.
4. **The effective θ_E distribution vs prior-pull doctrine:** physical draws give a
   peaked θ_E distribution; flat was our anti-prior-pull rule. Resolution:
   **importance-sample WHICH galaxy/z_s pair is drawn** so the effective θ_E
   distribution stays wide/flat-ish, while every individual image remains physically
   self-consistent. (Weight the sampling, never break the physics inside an image.)
   New gate: the light–θ_E correlation in the training set must match the
   SLACS-measured relation.

### P1-AUDIT (2026-07-13, Nurkyz directive: "is our self-consistency good; how to improve") — the σ_v→θ_E mapping vs the literature

What we implement: θ_E = 4π(σ_fiber/c)² D_ls/D_s (pure SIS), σ = SDSS fiber
velDisp jittered within min(σ_err, 0.2σ), z_s ~ truncN(0.65, 0.15) on
[max(0.55, z_l+0.05), 1.10], flat ΛCDM (70, 0.3). HOLISMOKES uses exactly this
route (SDSS z + σ_v → SIE painted on real LRG images; HUDF sources) — our
approach is the state-of-the-art recipe, plus things they don't do (native
amplitude, misalignment ⊕ scatter, tempered wide prior, FJ gate). LEMON's
stellar-mass+DM-fraction route is the fully synthetic alternative.

**Finding 1 (correctable NORMALIZATION bias):** SLACS measured
σ_fiber = 0.948 ± 0.008 σ_SIE — SDSS fiber dispersions under-read the lensing
(SIE) dispersion. Since θ_E ∝ σ², our computed θ_E is **systematically ~11%
LOW at fixed light** ((1/0.948)² = 1.11). This does NOT bias the arc-reading
channel (labels are self-consistent within each image) but mis-calibrates the
LIGHT-prior channel — the network's luminosity→θ_E fallback is taught ~11%
low relative to nature. Fix (C15a): σ_SIS = σ_fiber/0.948 in the manifest
generator (one line). Side benefit: every galaxy's θ_E range shifts up ~11%,
deepening the thin θ_E>1.5″ tail.

**Finding 2 (UNDER-SCATTER):** the stellar-vs-lensing dispersion relation has
~7% intrinsic scatter (≈14% in θ_E) BEYOND measurement error; we currently
jitter by measurement error only. Fix (C15b): add 7% intrinsic scatter in
quadrature — honest label noise that also softens the FJ-vs-flatness tension.

**Finding 3 (free validation figure, C15c):** for the 62 benchmark lenses we
hold both SDSS σ_fiber and true b_SIE → plot θ_SIS(σ_fiber) vs b_SIE and
measure the mapping's bias+scatter directly. VALIDATION ONLY: the
normalization comes from the literature (0.948), never fitted on the
benchmark (no leakage). Expected: ~−11% offset confirming Finding 1 — a
paper figure that grounds the whole GEN4 design.

**Ranked improvement queue:** C15a+b (one-line physics corrections; pilot →
regen with next data build) → C15c figure (analysis-only, immediate) →
G1b library scale-up (structural: less tempering → training FJ ρ moves from
−0.15 toward the real −0.32) → AR6 γ'(σ,Σ) slope coupling (medium; SIS→EPL)
→ z-dependent fiber-aperture correction (small; Jorgensen-style) →
two-component stellar+DM mass (defer; σ inside R_e already captures most).

### P2 — Best PSF per instrument
- Native HST: focus-diverse ePSF bank (already best-in-class — done).
- Euclid arm: **real VIS PSF** (public Euclid PSF model and/or Q1 star stacks)
  replacing the Gaussian in BOTH Euclidiser sides; ideally the original **HST2EUCLID**
  (Bergamini — email, no public-code statement in the paper).
- Roman arm: STPSF/WebbPSF-Roman models (public) — paper-2 rendering.

### P3 — Best backdrops: REAL Euclid sky for the Euclid arm
Q1 data are public: harvest **real Euclid VIS empty-sky cutouts** (+ real noise,
real PSF stars, real companions) and inject Euclidised arcs + deflectors onto REAL
Euclid backgrounds. The Euclid arm stops being "Euclidised COSMOS approximation" and
becomes near-native. Nobody has this (LEMON is fully synthetic). Native arm keeps
the screened COSMOS pool.

### P4 — Sources: keep what's validated
COSMOS morphologies + Newton-measured mags + SLACS source-z (the levers that halved
NMAD stay). Optional later: deeper morphology libraries (HUDF) as an ablation.

### P5 — One generative population, three renderings (merges Track R)
`PopulationConfig` (the physics: library, σ_v→θ_E, shapes, sources, environment) ×
`InstrumentConfig` (pixel scale, PSF source, backdrop pool, noise, band, depth) →
native-HST / Euclid / Roman datasets from the SAME population draw. This is the
professor's "flexible for any observations" made concrete, and the multi-domain
paper claim ("one physical model, validated on real GT in two domains, ready for
Roman") nobody else can make. (Community context: LSST-DESC's SLSim is moving this
direction for fully synthetic sims — our hybrid real-image version goes further.)

### P6 — Task-specific architecture (Nurkyz's ask; a genuine methods novelty)
The custom 2.8M net wins because θ_E is a GEOMETRIC low-level feature; design for it:
- **Log-polar branch:** resample the image to (r, φ) around the deflector centre —
  a ring becomes a horizontal line whose ROW IS θ_E; radius estimation becomes 1-D
  localization, rotation-invariance is free (φ-pooling), and stride never destroys
  radial precision.
- **Photometric branch:** small head on deflector photometric features (peak, Re,
  total flux — the FJ channel) so the physical prior has an explicit path.
- **Gated fusion + (μ, σ) head:** arc evidence when visible, light prior when not —
  mirroring how GEN4 training data now carries both channels.
Prototype cost: one resampling layer + small CNN; joins the training grid as a 5th
arch. Nobody in this literature uses log-polar for θ_E regression.

## 2. Staging (est. 2–3 weeks to eval; parallel with paper writing)

### ✅ G0 RESULTS (2026-07-10/11 — feasibility PROVEN)

1. **σ_v crossmatch: 82/84 of the existing LRGDEFL targets have clean SDSS σ_v**
   (median 204 km/s, range 73–408; z_l median 0.131). Implied SIS θ_E at SLACS-like
   z_s: median ~0.9″, 16–84% [0.65, 1.30], full range 0.13–3.9″ → the benchmark range
   [0.45, 2.3] is coverable by weighted draws; **G1 directive: expansion targets
   preferentially HIGH σ_v (>250 km/s)** — the θ_E>1.5″ tail is stamp-thin.
   Bonus: the stamp population is already S4TM-like in σ_v — the S4TM mismatch came
   from the imposed SLACS-tuned brightness prior, which GEN4 deletes outright.
   (g0_stamp_kinematics.csv, tables/ in the repo.)
2. **Expansion source identified: the SLACS-lineage HST snapshot archives** —
   PI Bolton ~349 + Treu ~124 + Koopmans ~49 ≈ **520 distinct ACS/WFC3 pointings of
   SDSS-spectroscopic targets** (σ_v by construction; mostly non-lenses). After
   removing the frozen-102 benchmark and known lenses: realistic net library
   ~300–450 stamps — inside the plan's 200–500 target. Random-archive harvesting is
   NOT viable (0.8% HST coverage of the 1.0M-galaxy SDSS σ_v pool) — the snapshot
   programs are the route.
3. **Misalignment relations anchored (literature):** mass–light PA aligned within
   ~±10–12°; large ΔPA correlates with large external shear → implement
   ΔPA ~ N(0, 10°) with the misalignment tail COUPLED to γ_ext; q_mass from q_light
   with ~0.1 scatter (exact relation to be fitted from Shajib+2021/Etherington+2022
   tables at G2 — flagged for verification).
4. **Importance-sampling design (the anti-prior-pull reconciliation):** per training
   image draw (stamp i, z_s) with probability ∝ w(θ_E(i, z_s)) where θ_E(i, z_s) is
   precomputed on a (stamp × z_s-grid) table and w = 1/density so the EFFECTIVE θ_E
   distribution is ~flat on [0.45, 2.3]; σ_v jittered within its measurement error
   per draw (honest label noise); weights capped (max reuse factor per stamp logged;
   effective-sample-size per θ_E bin reported by the generator as a new gate metric);
   physics inside each image never broken — only WHICH system is drawn is weighted.

| Stage | Work | Est |
|---|---|---|
| G0 | ✅ DONE (above) | — |
| G1 | ✅ DONE (2026-07-11): 139 σ_v-clean stamps (90 new after visual prune + 49 old), all measured (q, PA, Re, mag + σ_v/z) | — |
| G2 | ✅ DONE (2026-07-11): manifest generator + FJ gate; pilots v1–v4 (draw-order dispatcher fix; shuffle + vectorized sampler; flatness↔FJ incompatibility → TEMPERED prior α=0.6, ρ ≤ −0.15). v4 ALL GATES PASS | — |
| G3 (∥) | ◻ OUTSTANDING — Euclid-native ingredients: Q1 empty-sky harvest + VIS PSF (or HST2EUCLID). G4 ran with the Gaussian-VIS approximation; G3 remains the E3 suspect fix from eval #16 | 2–4 d |
| G4 | ◐ IN PROGRESS (2026-07-11 PM): Euclid-arm generation ✅ (88/88 shards, 104,314 train / 6,907 val, deflector-disjoint split, all gates PASS at scale incl. FJ −0.15); quick-train sanity ✅ (0.106); 17-member grid RUNNING → arbitration → ⛔ eval #17 (pre-authorized). NOTE: native arm NOT rendered (intermediates deleted for quota) but all 88 manifests+assigns RETAINED → native arm re-renderable from the SAME population draws (Track N hop, ~2 h generation + quota check) | — |
| G5 | Roman InstrumentConfig rendering (paper-2 seed; professor-endorsed) | after |

Risks, stated: library size is bounded by HST∩SDSS-spectroscopy overlap (mitigation:
FP-σ_v tier); importance-sampling design needs care (G0 note before any generation);
Q1 backdrop harvest is new tooling. Kill-criteria per stage: gates + visuals as always.

## AR — ARC REALISM STAGE (added 2026-07-12, Nurkyz directive: "evaluate and
## research arc realism; update the plan")

Motivation: after GEN4 (light↔mass) and G3 (real PSF), the remaining small-θ_E
failure is SCATTER, not pull (eval #18/#19) — the network mis-reads faint arcs
rather than ignoring them. The arc itself is now the least-realistic ingredient:
a smooth COSMOS galaxy lensed by a PERFECT ellipsoid + independent mild shear.
Real arcs are lensed by lumpy, boxy/disky, environment-embedded galaxies and are
themselves knotty. Items ranked by (expected impact on the benchmark) / cost:

| # | Item | Physics | Implementation | Impact | Cost | Risk |
|---|---|---|---|---|---|---|
| AR0 | **Arc-realism gate first** | measure before fixing (project law) | azimuthal surface-brightness contrast + arc-annulus asymmetry stats, sim vs the ~29 obvious-arc SLACS (same estimator both sides); curated arc-panel side-by-side | — (diagnostic) | low | none |
| AR1 | **Arc shot noise, native arm** (Nurkyz c) | bright arc pixels are Poisson-noisier; Euclid arm already has Poisson(signal+sky) — the NATIVE arm composites a noiseless render | Poisson-sample the render at the calibrated 675 s before compositing | small (SLACS arcs are sky-dominated) but a correctness fix; zero downside | trivial | none |
| AR2 | **ΔPA ↔ γ_ext coupling** (Nurkyz b; anchored at G0, never implemented — verified: γ1,γ2 ~ N(0,0.04) independent) | big light–mass misalignment is environmental → comes WITH big external shear | manifest-level: draw ΔPA ~ N(0,10°), then γ_ext = γ0 + k·|ΔPA| ⊕ scatter (calibrate k to Shajib+21/Etherington+22); shear PA random | medium-low on arcs (curvature/length tails), medium on honesty of the misalignment tail | low | low |
| AR3 | **Mass multipoles m=3, m=4 anchored to MEASURED isophotes** (Nurkyz a) | real ellipticals are boxy/disky (a4/a ~ ±1–2%) + lopsided (m=3 ~0.5%); multipoles at observed amplitudes measurably change arc morphology (Van de Vyvere+22) and mimic substructure (O'Riordan & Vegetti) | lenstronomy MULTIPOLE profiles exist; GEN4 twist: FIT each stamp's own isophotes (photutils.isophote a4/b4) → mass multipole = light multipole ⊕ scatter, PA anchored to light. **Nobody in this literature does per-observed-galaxy multipole priors — a genuine novelty in the GEN4 spirit** | medium at small θ_E (arc-shape realism is the prime suspect post-PSF) | medium-low (isophote fits at G1-measure time + 2 profile terms) | low |
| AR4 | **Source micro-structure (knots)** | real z~1–2 sources are clumpy star-formers; arcs show beaded knots that drive detectability and centroiding at small θ_E | tier 1: parametric knots (2–5 point-ish clumps ⊕ Sérsic host); tier 2: HUDF deep morphology library (plan P4 ablation) | medium at small θ_E | medium | low (knot statistics need a source: HUDF/CANDELS clumpiness papers) |
| AR5 | **Companion MASS** | injected companions currently have LIGHT ONLY; real satellites perturb arcs (cf. SLACS J0946+1006) | give bright companions FJ-scaled SIS (σ_v from flux — the same channel we restored for the main deflector) | low-medium (affects the ~10–20% of systems with close bright satellites) | medium (per-companion profiles slow renders) | low |
| AR6 | **Slope–σ_v coupling** | γ' correlates with Σ_e (denser → steeper); currently γ ~ N(2.0,0.15) independent | manifest-level conditional γ(σ_v, Re) ⊕ scatter | low for θ_E (robust to slope), cheap honesty | low | low |
| AR7 | **LOS structure (κ_ext, LOS shear/halos)** | real beams carry κ_ext ~ ±2% | paltas has LOS classes | CAUTION: κ_ext changes the meaning of the θ_E label (SIE-fit vs true); benchmark GT is b_SIE which absorbs environment — adding LOS without redefining labels injects ~1–2% label noise | medium | **defer**: needs a label-convention decision first |
| AR8 | **IllustrisTNG convergence maps** (professor's §6.1) | the maximal version: real simulated galaxies' full complexity (answer to "is multipoles what TNG does?" — NO: multipoles are the cheap PARAMETRIC approximation of one part of what TNG maps contain; TNG = everything at once — twists, multipoles, substructure — but with resolution limits and no correspondence to OUR observed stamps) | ray-trace TNG maps inside paltas | high generality, but breaks the per-observed-galaxy self-consistency that GEN4 just won with | high | paper-2 / ablation |

**Sequencing (iteration law applies — one change, pilot, gates each):**
AR0 gate (build the metric while chains run) → AR1 + AR2 (cheap pair, separate
pilots) → AR3 (the substantive one; isophote fits added to the G1b measurement
pass so the expanded library lands multipole-ready) → ⛔ eval → AR4/AR5 only if
the arc gate still shows a sim/real arc-morphology gap. AR7 deferred pending a
label ruling; AR8 stays paper-2.

**Synergy with G1b:** the isophote fitting (AR3) should be added to the G1b
stamp-measurement pass so the 1,982-candidate expansion is measured ONCE with
everything we need (mag, Re, q, PA, a3/a4).

## 3. What this supersedes / keeps

- Supersedes: further tuning of the REB flat-θ_E arm (its negative result is banked
  as the ablation "flat prior ≠ fix"); the standalone S4TM diagnostic (P1 covers it);
  the standalone mass–light item (P1 covers it); Track R as a separate task (P5).
- Keeps: E3 (VIS PSF) — now part of P2/G3; L4 closers (shared-29, two-stage hybrid);
  aux heads (labels already flow; train on GEN4 data); native back-port = the native
  GEN4 rendering (Track N merges into G4); all frozen-benchmark discipline.

## 4. Emails (verified addresses; drafts in EMAIL_DRAFTS_20260710.md, updated)

1. **valerio.busillo@inaf.it** (LEMON corresponding author) — 29 SLACS names,
   per-lens predictions, offer ours in return.
2. **pietro.bergamini@inaf.it** (HST2EUCLID, Euclid prep. LXXIV) — code access
   (no public-code statement in the paper).
3. **liran@bnu.edu.cn + nan.li@nao.cas.cn** (TinyLensGPU corresponding authors;
   first author Xiaoyue Cao via GitHub) — per-lens θ_E for the 63 SLACS.
4. Brian — authorship + the GEN4 direction (one paragraph).
