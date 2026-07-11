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
| G1 | Library expansion fetch + per-stamp light-shape/photometry measurement (q, PA, Re, mag) | 2–4 d |
| G2 | ◐ BUILT & PILOTING (2026-07-11): manifest generator + manifest config + combine manifest-mode + FJ gate + join. Pilot v1 caught draw-order desync (fixed: dispatcher); v2 gates PASS w/ FJ −0.19 but tail-ordering bug (fixed: shuffle + vectorized sampler); v3 revealed flatness↔FJ incompatibility → TEMPERED prior (α-sweep, ρ ≤ −0.15 required); v4 in flight | 2–3 d |
| G3 (∥) | Euclid-native ingredients: Q1 empty-sky harvest + VIS PSF (or HST2EUCLID) | 2–4 d |
| G4 | Full generation ×2 arms; training grid (custom nets + GEN4-NET + ConvNeXt V2 seat); sim-val arbitration; ⛔ eval #17 (Euclid) + ⛔ native eval | 3–5 d |
| G5 | Roman InstrumentConfig rendering (paper-2 seed; professor-endorsed) | after |

Risks, stated: library size is bounded by HST∩SDSS-spectroscopy overlap (mitigation:
FP-σ_v tier); importance-sampling design needs care (G0 note before any generation);
Q1 backdrop harvest is new tooling. Kill-criteria per stage: gates + visuals as always.

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
