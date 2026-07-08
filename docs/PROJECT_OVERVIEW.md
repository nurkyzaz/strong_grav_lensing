# PROJECT_OVERVIEW
 
## One paragraph
LensFusion (Wan, Chan, Lange, Hannuksela) reconstructs the unlensed background
source light (s) and the foreground lens mass map (convergence, kappa) from a
single noisy lensed image, by combining learned diffusion priors with a
differentiable ray-tracing forward model (two-stage sampler: DAPS -> PnP-DM).
**My contribution is a SEPARATE supervised CNN** that takes a lensed image and
predicts the Einstein radius theta_E (one number, arcsec). It is not part of the
diffusion pipeline; it is a helper that will later be plugged into the sampler as
a soft constraint to reduce mis-magnified reconstructions.
 
## Why
LensFusion recovers theta_E accurately on most systems (success fraction > 90%,
4,441 of 4,820 test systems), but a tail of reconstructions fit the image yet settle
on the WRONG magnification — the inferred theta_E (and enclosed mass) is too large or
too small. These cluster at COMPACT sources: small sources make short, weakly
structured arcs that poorly constrain the mass scale (paper: success fraction drops
toward smaller source half-light radii). A CNN that reads theta_E straight from the
image gives an independent anchor the sampler can be pulled toward (Phase 2).
theta_E is the primary constraint; ellipticity + center are possible later additions.
 
**Scope of what this fixes (important).** This targets the magnification-driven
failure mode (under-/over-magnified solutions under a weak likelihood), NOT the
mass-sheet degeneracy. theta_E defined by kappa_bar(<theta_E)=1 is INVARIANT under the
mass-sheet transformation (kappa -> lambda*kappa + (1-lambda) leaves kappa_bar=1 at
the same radius), so a theta_E anchor cannot resolve that degeneracy. The LensFusion
paper notes the framework inherits mass-sheet-like transformations as a separate,
imaging-only limitation. [verified against the paper]
 
**Where this sits.** theta_E prediction is the agreed FIRST of three possible "helper"
CNNs discussed with Brian: (1) separate the foreground lens light (hardest),
(2) segment the arc / source-light region into a mask for the inference (medium),
(3) predict theta_E from the image (easiest, best literature support) <- this project.
Team split: Edgar on the denoising side, Nurkyz on the CNN.
 
## Scope
- **Phase 1 (current): standalone CNN.**
  - Model 1: fixed pixel scale, predict theta_E (DONE; ~1.2% median fractional
    error on the unseen-halo test set).
  - Model 2: varied image/kappa FOV + angular scale fed as a scalar input, predict
    theta_E in arcsec (DONE 2026-06-09; test 1.14% frac, R2 0.996 — matches model 1,
    so scale-robustness achieved with no accuracy loss).
  - Model 3: realistic training = lens light (varied amp) + messy noise + asinh norm
    (DONE 2026-06-09; realistic test 2.00% frac, R2 0.977; fixes lens-light 56.9%->2.2%
    and noise 10.7%->2.7%; robust generalist, raw-image path viable).
  - Lens-light experiments M1/M2/M3 (Ishida) — superseded by Model 3 for the sim case;
    not pursued further on clean sims (degenerate without imperfect subtraction).
  - Ground-based generalization (HSCempty-style arc injection into real cutouts) —
    planned/future, pending Brian; see MODELS.md. Extends the CNN beyond clean HST-like
    sims toward real HSC/CFHT images.
- **Phase 1b (in progress): expand the model.** (1) Real-lens validation on SLACS HST/F814W +
  published theta_E (decisive; data-gated on Brian/Sam) — PRIORITY, still pending data.
  (2) Ellipticity + center multi-output head — labels DONE & validated (EPL fit + moment
  cross-check, fit-vs-moment corr ~0.98); multi-output CNN run. On CLEAN images (corrected
  orientation-aware augmentation): theta_E 1.44%, **e1/e2 R2 ~0.80, centre ~0.9px** — all
  three recoverable. (An earlier R2~0 was an augmentation bug, now fixed/overturned.) On
  REALISTIC (m3) images ellipticity SURVIVES: theta 2.58%, e1/e2 R2 ~0.87-0.88, centre
  ~0.9px -> working multi-parameter estimator on realistic sims. (Note: lens light adds an
  ellipticity cue; arc-only R2 is 0.80, the conservative number for real data.)
  (3) Multiband (snapshot-90, 7-band) — color separates lens from arc; the lever to try for
  ellipticity/lens-light if the clean test shows recoverable signal.
  Ablation (2026-06-09) confirmed Model 3 reads the ARC not the lens light (raw-image path
  trustworthy for theta_E).
- **Phase 2 (later, with Brian): sampler integration.** Needs a differentiable
  soft-theta_E estimator or a fixed scalar target; kappa lives in asinh space.
## Team
- Brian C.K. Wan — supervisor (technical direction).
- Prof. T.K. Chan — PI.
- Edgar — diffusion / denoising side (separate from the CNN).
- Sam Lange — co-author.
## Success criteria
- Fractional error on theta_E ~< 10%; beat LensFusion's own failure bar
  |dtheta_E/theta_E| > 15%. (Even ~10% may be plenty to help, since the targeted
  failures are already > 15% off.)
- Target literature-level accuracy on OUR data and OUR theta_E definition (not a
  raw comparison to other papers' numbers).
- The honest measure is the unseen-halo test set (and later real SLACS lenses),
  not the validation split.
## Known limitations (keep in mind)
- Capped lens diversity: 22,768 fixed IllustrisTNG kappa maps. We can't generate new
  lenses — only new source pairings, observational variety, and augmentation
  (rotation/flip). Effective diversity is bounded by the halo count.
- theta_E distribution is halo-determined (~0.5-2.5", ~50% in the typical 0.7-1.7"
  range), NOT uniform; under-represented ranges may be less accurate.
- Sim-to-real gaps: IllustrisTNG central-flux artifact; idealized/fixed PSF and noise;
  no lens light (model 1); fixed-FOV kappa. Real SLACS lenses are the honest test.
## Where details live
- Conventions + data gotchas -> DATA_PIPELINE.md
- Repo / code locations + functions -> CODEBASE_MAP.md
- Papers -> LITERATURE.md
- Architectures + experiments (incl. Experiment 2) -> MODELS.md
- Dated decisions and Brian/Chan input -> DECISIONS_LOG.md (most recent wins)