# MASTER PLAN — From m3 Failure to a Publishable Real-Lens Model

---

## ⚡ 2026-07-06 ADDENDUM — Differentiator campaign (supersedes the Stage-4 ablation list below; informed by the systematic literature review, see LITERATURE.md)

**Context:** hybrid v2 already achieves full-sample R² +0.45 on 102 native-HST real lenses
(bias −0.059″, RMSE 0.210″, NMAD 0.096″ — every metric 2–3× better than LEMON/Busillo 2026,
the nearest competitor, who report R² ≈ −0.03 full-sample in the Euclidised domain). The review
identifies exactly four unclaimed differentiators. Execute in this order:

**D1 — Causal realism ablations (converts the recipe into science; nobody in the literature
isolates ingredients).** Each = one dataset variant (100k, same pipeline, ONE change) + one
training run + one benchmark evaluation (logged, batched as the ablation bundle):
  - A3 θ_E prior: flat U[0.45,2.3] → m3-like skewed (truncated normal at ~1.0″) — the paper's
    causal spine (prior-pull diagnosis → fix → proof). RUN FIRST.
  - A1 PSF: empirical focus-diverse ePSF bank → single Gaussian FWHM 0.10″.
  - A2 backdrop: real empty COSMOS cutouts → pure Gaussian noise at the same per-image RMS draws.
  - A4 ePSF pool: benchmark-matched → broad non-benchmark pool (the circularity answer).
  Quota discipline: delete each ablation's dataset after its training+eval; keep ckpt+CSVs.

**D2 — Per-lens matched comparison vs Cao et al. 2025** (conventional pipeline, same 63 SLACS,
public per-lens data: github.com/caoxiaoyue/TinyLensGpu). Deliverable: per-lens scatter
(us-vs-Cao), agreement statistics, speed contrast (~ms vs ~3 min/lens).

**D3 — σ recalibration + honest coverage.** Our σ under-covers on real data (52%/83% vs 68%/95%).
Fit a single temperature/scale factor on SIM-VAL ONLY (never the benchmark), report raw AND
recalibrated real-lens coverage; cite LEMON's Platt scaling and Busillo's σ-filtering as prior
art for gating; our additions = ρ(σ, |err|) on real GT + failure-rate CIs + domain-aware σ.

**D4 — Sim-to-real domain adaptation (THE unclaimed peak; all prior DA work is sim-to-sim).**
  - Assemble a benchmark-DISJOINT unlabeled real pool (HST ACS F814W): non-benchmark SLACS
    grades, S4TM candidates beyond our 40, SLACS-extension programs; target ≥100 cutouts through
    the existing fetch pipeline. HARD RULE: zero overlap with the frozen 62+40 (name-level check
    logged).
  - Method v1: MMD feature alignment added to the v2 training recipe (MVE+UDA pairing mirrors
    Agarwal 2025, who stopped at sim-to-sim); DANN as v2 if MMD underwhelms.
  - Metrics that DA must move: compression slope (0.72/0.71 → 1), full-sample failure rate
    (23%/38% → ≲15%), σ coverage. Evaluate ONCE per DA variant, logged.
  - This is the paper's second novelty pillar; if it works, consider titling around it.

Sequencing note: D1–D3 are independent of D4 and feed the "before-DA gap fully characterized"
requirement; run D1 generation/training on the cluster while D2/D3 (analysis-only) complete
locally, then D4.

**D5 — multi-domain generalization (added 2026-07-06 after colleague input; runs AFTER D4).**
Colleague-proposed real-lens sources that are the WRONG instrument domain for the HST-targeted
DA pool (ruling logged in DECISIONS_LOG) but ideal for a cross-instrument generalization
experiment: ~250 Euclid Q1 grade-A lenses (A&A aa55141-25 — also the future LEMON home-turf
arena), BELLS GALLERY (WFC3/UVIS F606W), COWLS JWST (M25/S12-09). Design sketch: multi-target
MMD or per-domain adapters; evaluate zero-shot vs adapted per domain. Separate paper section or
follow-up paper. ALSO: report the Etherington et al. 2022 (arXiv:2202.09201) literature-defined
SLACS subset alongside the full frozen benchmark (never shrink the benchmark itself post-hoc).

---
 
_Date: 2026-07-02. Supersedes nothing; consolidates PAPER_PLAN + DATA_PIPELINE next steps into one
ordered campaign with hard gates. Rule #1 of this plan: **no run larger than 200 images until the
previous gate passes numerically.** This is the anti-blob discipline._
 
---
 
## 0. Two new findings from direct paltas source inspection (2026-07-02)
 
These were verified by reading the actual paltas code (pip wheel 0.1.1 vs GitHub main), not guessed.
 
### Finding 1 — the `magnitude` convention DEPENDS ON WHICH PALTAS YOU INSTALLED. This is the #1 suspect for the invisible lens light.
 
- **pip `paltas==0.1.1`** (`pip install paltas`): `SingleSersicSource.draw_source()` passes
  `magnitude` straight to `mag_to_amplitude()`. → `magnitude` is **APPARENT** magnitude.
  Apparent 16.5–18.5 with zeropoint 25.94 = very bright lens. Good.
- **GitHub `main`**: `draw_source()` calls `absolute_to_apparent(magnitude, z_source, cosmo)`
  (plus a k-correction). → `magnitude` is **ABSOLUTE** magnitude. If you feed it 16.5–18.5,
  at z=0.5 the distance modulus is ~+42 mag → apparent ~58 → **the lens light renders at
  literally zero flux. Arcs visible, lens invisible — exactly your symptom.**
Check which one you have (run on the cluster, env `Stronglensing`):
 
```
python -c "import inspect; from paltas.Sources import sersic; import paltas; print(paltas.__file__); src = inspect.getsource(sersic.SingleSersicSource.draw_source); print('ABSOLUTE convention' if 'absolute_to_apparent' in src else 'APPARENT convention')"
```
 
- If it prints `ABSOLUTE convention` → mystery solved. Fix = either (a) `pip install paltas==0.1.1
  --force-reinstall --no-deps` to get the apparent-magnitude version, or (b) keep main and set
  lens-light `magnitude` to absolute values (elliptical galaxies: roughly −21 to −23) **and** make
  sure `z_source` for lens light equals z_lens (main uses it for the distance modulus). Option (a)
  is simpler and matches the config you already wrote.
- If it prints `APPARENT convention` → the two "fallback" hypotheses in DECISIONS_LOG are red
  herrings: in pip 0.1.1 the lens-light `z_source` is **discarded** (config_handler does
  `..., _ = draw_source()`, the redshift is never used for lens light), and the combined `'e1,e2'`
  key is the **standard** paltas pattern (the Horton config itself uses `'e1,e2'` with
  `dist.EllipticitiesTranslation` for lens light). So neither can suppress the light. The
  color-scale-artifact hypothesis then becomes near-certain → run `diagnose_paltas_lens_light.py`
  and expect core/edge ≫ 1.
### Finding 2 — acceptance rate 1.000 means the magnification cut is probably NOT active.
 
paltas only rejects draws when a config defines `mag_cut` (module-level variable; e.g. the Horton
config sets `mag_cut = 2.0`). With `mag_cut` set, some draws must fail (source outside caustic,
low magnification) and acceptance < 1. **Acceptance exactly 1.0 strongly suggests no `mag_cut` in
`config_lensfusion_acs.py`** — which means the training set will contain barely-lensed blobs
(source far from caustic → one faint smudge, no arc). This is precisely the "blobs, not lenses"
failure class you're worried about. Fix: add at module level
 
```python
mag_cut = 3.0   # require total magnification >= 3; expect acceptance ~0.5-0.9 afterwards
```
 
and confirm the acceptance rate drops below 1.0 on the next test run. (Note: this is a total-
magnification cut, which the standing decision said is weak *as a detectability criterion* —
here it serves a different purpose: guaranteeing a genuinely lensed geometry in every training
image. Keep it moderate; do not use it as the detectability filter.)
 
### Finding 3 (paper framing correction) — Cao et al. 2025 is NOT a CNN.
 
Cao et al. 2025 (arXiv:2503.08586) is an **automated conventional lens-modeling pipeline**
(pixel-based modeling + nautilus nested sampler, ~3 minutes per lens), applied to 63 SLACS lenses,
≲5% deviation, ~10% catastrophic failures on SLACS. Two consequences:
 
1. **Better positioning for us, not worse.** The claim becomes: a millisecond-inference CNN
   matches (or beats) a full likelihood-based automated modeling pipeline on the identical lens
   sample — a ~10⁵× speedup at comparable accuracy. And Cao et al. explicitly say their failures
   "can be mitigated by incorporating prior knowledge from machine learning techniques" — our
   paper is literally the thing they call for. Quote-mine that for the intro.
2. **The CNN-vs-CNN comparisons are separate:** Hezaveh et al. 2017 (Nature; CNN SIE parameters
   from HST) and Gawade et al. 2025 (ground-based HSC). Cite all three but keep the head-to-head
   table honest about method class.
3. **Their code and per-lens data are public** (linked from the arXiv abstract). Download their
   per-lens θ_E results → per-lens scatter plot of us-vs-Cao on the same lenses. That figure is
   far stronger than comparing two summary statistics.
---
 
## Stage 0 — Diagnose & fix the generator (NO compute beyond 200 images)
 
**Goal:** a config that provably produces SLACS-lookalikes. Everything here runs in minutes.
 
0.1 Run the version check (Finding 1). Apply the fix if needed.
 
0.2 Run `diagnose_paltas_lens_light.py` on the existing 64-image test run.
    Interpretation:
    - core/edge ≫ 1 (say > 10): lens light present; problem was the display stretch. Proceed.
    - core/edge ≈ 1: light truly absent → almost certainly Finding 1 (absolute-magnitude
      version). Fix and re-run.
 
0.3 Add `mag_cut = 3.0` (Finding 2). Re-run 64 images; confirm acceptance < 1.0.
 
0.4 Preview discipline forever after: every preview panel gets **three stretches** —
    linear, 1–99 percentile clip, and asinh — side by side. Most historical "blobs" and
    "missing light" scares were stretch artifacts. Bake this into `paltas_to_train.py --preview`.
 
0.5 **200-image pilot** with the fixed config, then run the numeric realism gate
    (adapt `diagnose_simct.py`; targets from the real-SLACS diagnostics you already measured):
 
    | Gate metric                     | Target (from real SLACS)     |
    |---------------------------------|------------------------------|
    | Lens peak / sky                 | median inside 93–197         |
    | Arc thickness FWHM              | 0.1–0.4″                     |
    | PSF FWHM (from unresolved src)  | ≈ 0.10″                      |
    | Grid                            | exactly 128 px @ 0.05″/px    |
    | Sky RMS                         | within ~20% of `sky_rms` col |
    | Acceptance rate                 | < 1.0 (mag_cut active)       |
    | Visible arc by eye (16-panel)   | most images                  |
 
    Plus one cheap, decisive domain check: **overlay the pixel-value histogram and the
    azimuthally-averaged radial profile of the 200 pilot images vs. the 62 real SLACS cutouts,
    both passed through the exact CNN input normalization (asinh + scale conditioning).**
    If those two distributions don't overlap, the CNN sees the domain gap on day one and no
    amount of training fixes it. This one plot is the honest gatekeeper.
 
**Gate to Stage 1: all table rows pass + histogram/profile overlap looks sane.**
 
---
 
## Stage 1 — Noise & photometric calibration (still small runs)
 
The last mile between "looks right" and "is right".
 
1.1 **Sky/noise:** tune `exposure_time`, `sky_brightness`, `read_noise`, `num_exposures` until
    empty-corner RMS of generated images matches the `sky_rms` distribution from
    `failure_features_slacs.csv`. Don't assume the SLACS exposure times from memory — calibrate
    empirically against your own measured column. Then **randomize** noise within the observed
    real range (±~30%) rather than fixing one value: domain randomization makes the CNN
    insensitive to residual miscalibration.
 
1.2 **Lens-light magnitude prior from data, not guesswork:** Bolton 2008 (your VizieR table)
    includes deflector I-band photometry. Build the apparent-magnitude histogram of the actual
    62 deflectors and set the lens-light `magnitude` prior to cover it (slightly wider). Same for
    `R_sersic`: use the effective radii from Bolton 2008 if present, else keep ~1.2″ ± spread.
 
1.3 **Optional but high-value realism upgrade — real backdrops:** you already own
    `empty_cutouts.h5` (1317 real empty COSMOS cutouts, 0.05″/px, 6.4″). Generate paltas images
    with `no_noise = True`, then add each to a randomly drawn real empty cutout (after matching
    units — flag: paltas outputs counts/s; confirm the empty cutouts' units before adding).
    This injects **correlated drizzled noise, faint field neighbors, and background structure**
    that no Gaussian noise model captures — the same trick the HOLISMOKES/Cañameras lens-finding
    pipelines use, and the one realism axis pure paltas lacks. Keep Poisson noise on the lensed
    flux itself (source shot noise) if feasible; if not, the sky-dominated regime makes the
    approximation acceptable — state it in the paper.
    Do a 200-image pilot of this variant too, re-run the Stage-0 gate on it.
 
**Gate to Stage 2: sky RMS within ~10–20% of real, lens-light magnitudes data-driven, and (if
using 1.3) the hybrid pilot passes the same gates.**
 
---
 
## Stage 2 — Training-set design & generation (first big compute)
 
2.1 **Priors (the anti-prior-pull core):**
    - θ_E ~ U[0.55, 2.3] — flat, and slightly WIDER than the benchmark's 0.7–1.7″ so the real
      range sits in the interior (regressors bias toward the prior interior at the edges;
      padding the range keeps the benchmark away from the edge effect).
    - γ (power-law slope) ~ N(2.0, 0.15); q, PA, shear as in the Horton pattern.
    - Source: full COSMOS_23.5 catalog, position offsets ~ U(−0.25, 0.25)″ per axis (with
      mag_cut doing the lensing-geometry enforcement), source magnitudes spanning the faint end
      (real SLACS arcs are faint — do NOT bias sources bright, that's the old v0 mistake in
      photometric clothing).
    - **Decouple lens light from mass:** sample lens-light (e1,e2, PA) independently from mass
      (e1,e2), or with only partial correlation, and jitter light center vs. mass center by a few
      hundredths of an arcsec. This (a) prevents the CNN from learning the θ_E-irrelevant
      light↔mass shortcut, and (b) is the honest-training prerequisite for the e1/e2 leakage
      test later.
    - PSF: real ACS kernel, but randomly rotate it (90° multiples + small interpolated angles)
      per image so the CNN doesn't memorize one diffraction-spike orientation.
 
2.2 **Size:** 100k images (50k floor). paltas generation is CPU-parallel — shard it:
    run 4–8 `generate` processes with different `--seed`/output dirs in tmux, merge in
    `paltas_to_train.py`. Preview-check EACH shard's first 16 images (cheap paranoia).
 
2.3 **Held-out sim validation split:** 5k images from the same config, generated with a
    disjoint seed, never trained on. This is the in-distribution yardstick (expect ~1–3%
    median error, like m3 achieved in-distribution).
 
**Gate to Stage 3: 16-panel visual per shard passes; metadata θ_E histogram is flat over the
intended range; no shard has anomalous acceptance rate.**
 
---
 
## Stage 3 — Training
 
3.1 **Keep the m3 architecture.** The diagnosis was explicit: the failure was distributional,
    not architectural. Scale-conditioned ResNet + asinh input norm, Huber loss, Adam. The only
    required change: read per-image `theta_E` directly from the new h5 (no `kappa_index` join —
    that whole hazard class is gone).
 
3.2 **Same normalization for sim and real, verified once:** recompute scale_mean/scale_std on
    the new training set; apply the identical transform in `metrics_real.py`'s loader; re-plot
    the Stage-0 normalized-histogram overlay with the final constants.
 
3.3 **Uncertainty head (cheap, high paper value):** train the output as (μ, log σ²) with a
    Gaussian NLL loss instead of a point estimate. Costs one extra output unit; gives per-lens
    error bars, a calibration plot for the paper, and — crucially — the natural per-sample weight
    for Brian's Phase-2 regularizer (penalize by CNN confidence). If it destabilizes training,
    fall back to Huber and note it; don't fight it.
 
3.4 **Model selection ONLY on the sim validation split.** The frozen 62+40 is evaluated once
    per major experiment version, logged in DECISIONS_LOG with a running count. Every extra
    peek at the benchmark is a small act of fitting it; keeping the peek-count low and
    documented is what makes the final number credible.
 
3.5 Augmentation: flips/rotations fine for θ_E; if training multi-output, apply the
    already-established e1/e2 label transformation (the corrected augmentation code).
 
**Gate to Stage 4: sim-val median |frac error| ≲ 3% and no train/val divergence.**
 
---
 
## Stage 4 — Evaluation, ablations, and the "beats the literature" case
 
4.1 **Primary result:** `metrics_real.py` on the frozen 62 SLACS + 40 S4TM. Success bars are
    already fixed in PAPER_PLAN (median within ±5%, R² > 0, failure ≲ 10%).
 
4.2 **Uncertainty on every headline number (reviewers WILL ask at N=62):**
    percentile bootstrap (10k resamples) for median fractional error, 16–84 interval, and
    failure rate; report as e.g. "failure rate 8% (95% CI 3–16%)". For failure-rate comparison
    with Cao's ~10%: at N=63 the binomial CI is wide — a claim of "fewer failures" needs the CI,
    a claim of "comparable" is safe earlier.
 
4.3 **Matched per-lens comparison with Cao:** pull their released per-lens θ_E (code/data
    public), restrict to the intersection lens list, and make the per-lens us-vs-them scatter.
    Also state clearly: same lenses, same b_SIE ground truth, different method class
    (amortized CNN vs. per-lens sampling).
 
4.4 **Ablations (each = one dataset variant + one training run; ranked by narrative value):**
    1. **θ_E prior: flat vs. m3-like skew** — this closes the paper's causal loop: the diagnosis
       said prior-pull, the fix flattened the prior, the ablation proves that specific change
       drives the recovery. Highest priority; it's the paper's spine.
    2. **Lens light on/off** in training (off ≈ old v0 regime) — shows arc-realism matters.
    3. **Real backdrop (Stage 1.3) vs. Gaussian noise** — quantifies the correlated-noise gap.
    4. Real ACS PSF vs. Gaussian PSF (cheapest, fold into 2 or 3 if compute-tight).
    5. (Optional) COSMOS sources vs. Sérsic sources.
 
4.5 **Kill-criterion / escalation:** if the full-realism model still has R² < 0 on real lenses
    after passing every Stage-0/1 gate → the residual gap is the parametric-Sérsic lens light →
    escalate to **Path B** (paltas noiseless arcs injected onto REAL deflector cutouts —
    which needs real SLACS-sized ellipticals; the intersection trick: use the 40 S4TM... no —
    those are benchmark. Realistic Path B sourcing: non-lens LRG cutouts from HST archives, ask
    Sam). Decision point is here and no earlier — do not pre-build Path B.
 
---
 
## Stage 5 — Multi-parameter extension (after θ_E lands)
 
- Because Stage 2 decoupled light from mass, the leakage question becomes measurable: evaluate
  e1/e2 on sim subsets where light and mass ellipticity agree vs. disagree. The gap between
  those two numbers IS the leakage, quantified — that's the honest caveat turned into a result.
- Real-lens e1/e2 check against Bolton 2008 SIE q/PA (convert q,PA → e1,e2 consistently;
  watch the PA convention — verify against 2–3 lenses by eye before batch evaluation).
- Centroid: report in pixels as before.
## Stage 6 — Paper assembly + LensFusion tie-ins
 
- Figures 1–6 as already planned in PAPER_PLAN, with Figure 4 upgraded to the per-lens Cao
  comparison (4.3) and a new small calibration figure if the uncertainty head (3.3) works.
- Intro framing: Cao et al.'s own "mitigated by ML priors" line → our contribution.
- Compact-source result and Phase-2 regularizer stay as the downstream-application section.
- Separately (not in this paper's critical path): Brian's source-amplitude CNN — still blocked
  on confirming which amplitude definition he wants.
- Authorship conversation with Brian — do this early, not after results exist.
---
 
## The anti-blob checklist (pin above the terminal)
 
1. **Never** launch > 1k images before the 200-image pilot passes the numeric gate table.
2. Every preview = three stretches (linear / percentile / asinh). A blob under one stretch is
   often a lens under another.
3. Acceptance rate 1.000 = your magnification cut is not active = blobs incoming.
4. Verify the magnitude convention of the *installed* paltas (Finding 1) after ANY reinstall.
5. FOV sanity: θ_E max 2.3″ → ring diameter 4.6″ < 6.4″ FOV ✓; source offsets ≤ 0.25″ ✓.
   Never widen θ_E or source-offset priors without redoing this arithmetic.
6. One normalized-histogram + radial-profile overlay (sim vs. real) per dataset version.
   If they don't overlap, stop — the CNN will fail before you train it.
7. Units check before ANY image addition (paltas counts/s vs. empty-cutout electrons/s).