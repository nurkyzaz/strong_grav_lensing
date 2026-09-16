# Rung 1 — Residual-Imaging Approach (scope)

**Why.** Our plain whole-image CNN tops out at **~0.55–0.57 AUC** (see
[`RUNG1_PLAN.md`](RUNG1_PLAN.md) and the diagnostics: it can overfit 512 images
to train-BCE≈0 but doesn't generalize). The reason is physical: each 91×91 image
is dominated by (a) the bright deflector-galaxy light and (b) the *smooth*
lensed arc. A CDM subhalo population perturbs the arc only **subtly and at small
scales**, so that signal is a tiny fraction of the image's dynamic range and the
CNN can't isolate it. **Residual imaging** removes the smooth/known component so
the network sees mostly the perturbations where the subhalo signature lives.

Key fact that shapes everything: the subhalo signal is a perturbation to the
**lensed source (the arc)**, *not* to the deflector's own light. So the ideal
residual is `observed − model(smooth lens + source)`. Removing only the galaxy
light helps normalization but does **not** by itself isolate substructure.

---

## Tiered plan (cheap → rigorous)

### Tier 1 — preprocessing "poor-man's residual" (days; low risk; reuses our CNN)
No lens modeling. Add a preprocessing step to the existing `Rung1H5Dataset` that
produces extra input channels emphasizing small-scale structure, then retrain the
same resnet50/convnextv2 classifier. Options to try as channels (stack with, or
replace, the raw bands):
- **Deflector-light subtraction**: fit a smooth elliptical model to the central
  galaxy (photutils isophote `Ellipse`, or a 2-component Sérsic via a quick
  least-squares on the central region masked away from the arc) and subtract it.
- **Unsharp mask / high-pass**: `img − GaussianBlur(img, σ)` at 1–2 scales —
  suppresses the smooth arc+galaxy, keeps fine structure. Trivial, no fitting.
- **Multi-band contrast**: F158−F106 etc. (subhalo lensing is achromatic, so
  color mostly won't help — include only as an ablation).

*Expected*: modest lift (~0.55 → ~0.58–0.62 if lucky). It's a rule-in/rule-out
experiment: cheap, and if a simple high-pass already helps, that validates the
residual hypothesis before investing in Tier 2. **Do this first.**

### Tier 2a — forward-model residuals (weeks; rigorous; the field-standard)
For each system, reconstruct the **smooth** model and subtract:
1. Fit a smooth lens mass (SIE + external shear; init from the training attrs
   `theta_e`, `sigma_v`, `z_lens/z_source` which the labeled set provides).
2. Reconstruct the **source** *without* substructure — real COSMOS-Web sources
   are complex, so a parametric Sérsic won't do; use lenstronomy's pixelated /
   shapelet source reconstruction (regularized), or a linear source inversion on
   a smooth lens.
3. `residual = observed − best_fit_smooth_model`; train the CNN on residuals.

This is the Vegetti/Hezaveh-style approach and gives the cleanest signal, but:
- **Cost**: a per-system optimization × ~200k systems → SLURM array job, many
  GPU/CPU-hours; fitting stability with real sources is the main risk.
- We already sit on the right stack: the repo is built on **paltas → lenstronomy**
  (see `README.md`), so the modeling primitives exist.

### Tier 2b — anomaly-detection residual (weeks; tractable ML alternative)
Avoid explicit per-system lens fitting. Train a generative model to reconstruct
**only smooth (label=0) systems**; at test time, subhalo systems reconstruct
worse, so the **reconstruction residual is the signal**:
1. Train an autoencoder / smooth-image predictor (or reuse the project's
   diffusion machinery in `~/lensfusion`) on the ~53k no-substructure images.
2. `residual = observed − reconstruction`; classify on residual (CNN) or on a
   scalar residual-energy/anomaly score.

Cheaper and more novel than 2a; risk is the model also failing to reconstruct
benign source variety (false anomalies). A good middle path.

### Tier 3 — beyond CNN (research)
Substructure **power spectrum** of the residuals, or simulation-based inference
(Brehmer/Cranmer-style) on the residual maps. Flag as a stretch goal, likely
past the scope of this challenge entry.

---

## How it plugs into what we have
- **Classifier unchanged**: `train_cnn_rung1.py` / `predict_rung1.py` keep the
  resnet50/convnextv2 + BCE + AUC + TTA + ensemble machinery. Tier 1 is a new
  branch inside `Rung1H5Dataset.read_image()` (compute residual channels there);
  add `--input_mode {raw,residual,stack}` and `--n_channels` so `in_chans` and
  the timm stem adapt automatically.
- **Fair comparison**: reuse the *same* stratified val split and seeds; the
  current **0.57 ensemble is the frozen baseline** to beat. Report AUC deltas.
- **Data volume**: preprocessing that needs fitting is best precomputed once into
  a residual HDF5 cache (mirrors the training set layout) so training I/O stays
  fast — a one-time SLURM array job, then training reads residuals directly.

## Compute / effort estimate
| Tier | Coding | Compute | Expected AUC |
|---|---|---|---|
| 1 (high-pass / light-sub) | 1–3 days | ~free (36 min/train run) | 0.58–0.62 (uncertain) |
| 2a (forward-model resid.) | 1–3 weeks | large (200k fits, array job) | best, unknown |
| 2b (anomaly / generative) | 1–2 weeks | GPU-days train + inference | medium–high |

## Risks / open questions
- Residuals **amplify noise** as well as signal → the CNN may latch onto
  romanisim noise artifacts rather than physics; watch for train/val gap and
  test on a noise-only control.
- Tier 2a source reconstruction may be **unstable** on real COSMOS sources;
  budget for failures and a fallback (Sérsic-only smooth model).
- We still lack the **official scored metric + submission column** (organizers) —
  orthogonal to this work but needed before any upload.

## Recommended first step
Implement **Tier 1** (deflector-light subtraction + a 2-scale high-pass, as extra
channels via `--input_mode stack`), retrain seed-0, and compare val AUC to 0.57
on the identical split. One ~40-min run tells us whether residuals help at all
before committing to Tier 2. Decide 2a vs 2b with the professor based on that
result and how much modeling effort is warranted.
