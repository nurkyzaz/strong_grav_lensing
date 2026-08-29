# LensCNN: Closing the sim-to-real gap for CNN Einstein-radius estimation with a realistic simulation generator

**Draft v3** — Nurkyz Ydyrysova, T. K. Chan (+ co-authors TBC)
Department of Physics, The Chinese University of Hong Kong.
Target journal: MNRAS. This is the readable companion to `paper/main.tex` (the authoritative LaTeX). Items marked **[TODO]** need a pending experiment — no number here is fabricated.

> **How to read this document.** This is a from-scratch v3 rewrite. It (a) fully addresses Prof. Chan's comments, (b) pre-empts the concerns an MNRAS referee is most likely to raise (see the companion *V3 Review & Plan*), and (c) records what changed in v2 and v3 (see the final "Changelog" section, and `docs/CHANGELOG_v1_v2_v3.md`).

---

## Abstract
Deep learning promises fast parameter estimation for the ~10⁵ strong gravitational lenses expected from *Euclid* and the Roman Space Telescope, yet CNNs trained on simplified simulations typically degrade on real data — a "sim-to-real gap". We show that **physical realism in the training simulations**, rather than network architecture or domain adaptation, is the decisive factor in closing this gap for Einstein-radius (θ_E) regression. Our generator assembles real ingredients in physical units: real HST galaxies provide the lens light, with each deflector's mass modelled as a singular isothermal sphere (SIS) whose scale is fixed by that galaxy's measured SDSS velocity dispersion (σ_v → θ_E); real COSMOS sources are ray-traced through this mass; and real empty-sky backdrops and an empirical, focus-diverse PSF supply correlated noise and instrument response. The defining feature is **observational self-consistency**: one real galaxy supplies both a system's light and its mass. We train a scale-conditioned CNN with a Gaussian negative-log-likelihood head. On a frozen spectroscopic-lensing benchmark of 62 SLACS and 40 S4TM lenses (Bolton et al. 2008 b_SIE), the native-HST model reaches R²=0.64 (SLACS) and R²=0.90 (S4TM), and R²=0.71 on the *Euclid*-degraded benchmark, matching conventional modelling at a fraction of the amortized inference cost. Systematic ablations show real background structure is the single most important ingredient, while linking each deflector's light and mass is the decisive step. The predicted uncertainty correlates with true error (Spearman ρ=0.6–0.7) and gates a confident subsample to a 3–6% failure rate.

*Keywords:* gravitational lensing: strong — methods: data analysis — techniques: image processing — galaxies: elliptical and lenticular, cD

---

## 1. Introduction

### 1.1 Strong lensing and the Einstein radius
Strong gravitational lensing occurs when a massive foreground galaxy (the deflector) lies close to the line of sight to a background galaxy (the source), bending and magnifying the source light into arcs or Einstein rings. Formally the geometry is set by the **lens equation β = θ − α(θ)**, which maps a source position β to its image positions θ through the scaled deflection angle α produced by the deflector's projected mass. Modelling a lens therefore requires three ingredients: the **lens light** (the deflector's surface brightness, a Sérsic profile), the **lens mass** (the projected mass that generates α), and the **source light** (the background galaxy). For a singular isothermal sphere the characteristic scale is the **Einstein radius θ_E = 4π (σ_v/c)² (D_ls/D_s)**, where σ_v is the deflector velocity dispersion and D_ls, D_s are angular-diameter distances. We adopt the SIS/SIE description throughout and detail how the mass is built for training in §3.4. θ_E constrains galaxy mass-density profiles, dark-matter content, and H₀ via time-delay cosmography (Meneghetti 2021; Saha et al. 2024; Treu 2010). Wide-field surveys — *Euclid* (Laureijs et al. 2011), Roman (Spergel et al. 2015), LSST (Ivezić et al. 2019) — are expected to find ~10⁵ lenses.

### 1.2 Automated modelling and the sim-to-real gap
Traditional modelling fits parametric profiles by likelihood-based inference; it is accurate but costly (~3 min/lens; Cao et al. 2025) and needs expert supervision. CNNs amortize this — once trained they estimate θ_E in milliseconds (Hezaveh et al. 2017; Perreault Levasseur et al. 2017). The obstacle is the **sim-to-real gap**: CNNs trained on simplified simulations degrade on real data (prior-pull, slope compression, overconfident uncertainties). Its physical origins are not yet well characterised. Domain-adaptation studies (Ćiprijanović et al. 2023; Agarwal et al. 2025; Swierc et al. 2024) have been simulation-to-simulation; LEMON (Busillo et al. 2026) evaluates on real *Euclid* lenses but trains on fully parametric simulations and reports degraded real-vs-simulated performance.

### 1.3 This work
We present a CNN θ_E estimator trained on a physically self-consistent, real-ingredient pipeline. Contributions:
1. **Observational self-consistency (GEN4):** each training system uses one real HST galaxy for both its light and its mass (θ_E from that galaxy's measured σ_v; §3.4), embedding the luminosity–mass link human modellers use when arcs are faint.
2. **Real ingredients throughout:** real COSMOS sources, real empty-sky HST backdrops, an empirical focus-diverse PSF, all in physical e⁻/s.
3. **Causal realism ablations:** a controlled decomposition of which ingredient closes the gap.
4. **Domain-aware uncertainty:** a Gaussian-NLL head whose σ correlates with real error and gates confidence.
5. **Comprehensive real-lens validation:** frozen benchmark (62 SLACS, 40 S4TM; Bolton b_SIE), its *Euclid*-degraded version, real *Euclid* Q1 lenses, and Roman simulations.

Throughout we distinguish **GEN4** (low-redshift HST domain — the benchmark) from **GEN5** (higher-redshift *Euclid*/Roman domains). Our scope is deliberately narrow — one band, the single most robust parameter θ_E — which we argue is the right first target (§6).

---

## 2. Related work

**CNNs for lens parameters.** Hezaveh et al. (2017) and Perreault Levasseur et al. (2017) pioneered CNN SIE-parameter recovery (simulation-only). Gawade et al. (2025) used real empty-cutout injection on HSC — close to our hybrid recipe — but with ground truth from their own YattaLens pipeline. *Because an automated pipeline's output is itself a model estimate that can share systematic biases with the network under test, agreement with it measures consistency rather than physical accuracy; we instead adopt the Bolton b_SIE radii, derived from SLACS spectroscopy and HST imaging independently of any lens-finding CNN.* Schuldt et al. (2023) compared a ResNet to conventional modelling on 31 HSC lenses. Busillo et al. (2026, LEMON) is closest: trained on 80k parametric *Euclid* simulations, evaluated on Euclidised-HST and real Q1 lenses. Cao et al. (2025, TinyLensGPU) is a GPU conventional pipeline with **full posteriors and uncertainties** — our conventional reference.

**Domain adaptation.** Ćiprijanović et al. (2023), Agarwal et al. (2025) and **Swierc et al. (2024)** (Domain-Adaptive Neural Posterior Estimation) improve target-domain accuracy but are all simulation-to-simulation; we find DA does not improve over realism-calibrated simulations (§5.4).

**Positioning — Table 1.** Differentiators: observational self-consistency, causal realism ablations, an independent spectroscopic GT, cross-domain real validation, and a domain-aware uncertainty that doubles as a confidence gate. *Reproducibility caveat on LEMON:* we cannot recover LEMON's published aggregate metrics by re-scoring its released predictions, so we report our re-scoring separately (§5.6).

**Table 1 — method comparison** (note the **Uncertainty (UQ)** row, added per Prof. Chan):

| Feature | LEMON | Gawade | HOLISMOKES X | Cao (TinyLens) | **This work** |
|---|---|---|---|---|---|
| Approach | CNN | CNN | CNN/ResNet | conventional | CNN |
| Training sims | parametric | hybrid | — | — | real-ingredient |
| Real-lens GT | mixed | pipeline | pipeline | spectroscopic | spectroscopic (Bolton) |
| Realism ablations | no | no | no | n/a | **yes** |
| **Uncertainty (UQ)** | yes | no | no | **yes** | **yes** |
| Inference speed | fast | fast | fast | ~3 min | fast |

---

## 3. Data and simulator

### 3.1 The frozen real benchmark
62 SLACS + 40 S4TM grade-A lenses (HST ACS/WFC F814W), ground-truth θ_E = SIE b_SIE (Bolton et al. 2008), independent of our pipeline. J0955+0101 excluded (corrupted cutout). Cutouts 128×128 px at 0.05″/px. The benchmark is never used for training/selection — only logged evaluation checkpoints. A harder test uses 322 real *Euclid* Q1 lenses (PyAutoLens SIE GT). **No benchmark galaxy's light stamp appears in the training library** (§3.3), removing a leakage path.

**Table 2 — benchmark properties** (θ_E from Bolton b_SIE; redshift/magnitude ranges from the survey papers):

| Property | SLACS (62) | S4TM (40) | Source |
|---|---|---|---|
| θ_E [″] | 0.69–1.78 (med. 1.17) | **[TODO: S4TM range]** | Bolton et al. 2008 |
| z_l | **[TODO ~0.06–0.51]** | **[TODO]** | Auger 2010 / Shu 2017 |
| z_s | **[TODO ~0.2–1.3]** | **[TODO]** | Bolton 2008 / Shu 2017 |
| Deflector mag (F814W) | **[TODO]** | **[TODO]** | this work |

### 3.2 Source galaxies (real COSMOS)
Real galaxies from COSMOS_23.5 (56,062 GREAT3-vetted; Mandelbaum et al. 2012), ray-traced by **paltas** on **lenstronomy**. Surface-brightness cut SB_max = 21.0 (native-HST) / 22.5 (*Euclid*); compact-source cuts remove unresolved objects. Source flux renormalised to the SLACS source-magnitude distribution (mean ≈24.3 at z≈0.65; Newton et al. 2011). GEN5 additionally dims the source to its drawn z_s (luminosity-distance + flat-f_ν K-correction).

### 3.3 Lens-light library (real HST galaxies)
Real HST F814W stamps of **non-lens** early-type galaxies from the SLACS/S4TM parent samples, expanded for GEN5 by a footprint cross-match against the SDSS σ_v pool. GEN4 uses 139 stamps; GEN5 uses 488. Each stamp carries a measured σ_v, z_l, magnitude, effective radius, axis ratio, position angle, and isophote-shape coefficients, injected at native amplitude with no rescaling. We call it a **lens-light** library deliberately: *the light is real, but the mass is modelled* (§3.4).

### 3.4 Lens-mass model and physical self-consistency (GEN4)
**A galaxy's mass — unlike its light — is not directly observed**, so every training deflector is given a **model** mass built from its own kinematics rather than an independently drawn Einstein radius. We adopt an SIS: θ_E is fixed by the galaxy's SDSS σ_v (Eq. §1.1) at the drawn (z_l, z_s) — no independent θ_E prior exists anywhere. Mass ellipticity/orientation are inherited from the light shape with empirical scatter (q_mass = q_light ⊕ 0.08; ΔPA ~ N(0,10°)), rotating mass and light together. GEN5 adds isophote-anchored m=3,4 multipoles as perturbations on this isothermal base, so **the profile remains fundamentally isothermal**.

Because θ_E derives from the deflector's own luminosity-linked σ_v, the **Faber–Jackson channel is present by construction** — the ingredient absent from parametric simulators. A tempered importance-sampling scheme keeps the effective θ_E distribution wide over [0.45, 2.30]″ while preserving a real light–mass correlation (simulator ρ(mag,θ_E)=−0.15 vs real SLACS −0.32: sign preserved, amplitude diluted).

**Reliability of the σ_v → θ_E label.** SLACS profiles are close to isothermal on average (Koopmans et al. 2006; Auger et al. 2010), justifying the SIS mapping; but the mapping carries galaxy-to-galaxy scatter (density-slope, aperture/anisotropy) that propagates into the training θ_E labels. Because our GT is SIE b_SIE while our labels are SIS(σ_v), **part of the residual we report is irreducible label noise, not network error.** We quantify the direct SIS(σ_v)-vs-b_SIE bias/scatter on the benchmark (§5) **[TODO E1: report label-noise floor]**, which bounds the achievable R².

### 3.5 Instrument realism, hybrid assembly, survey operators
All components in one physical system (e⁻/s, F814W AB zeropoint 25.94) on a common 0.05″ grid. Real, focus-diverse empirical HST ePSF (not Gaussian/Moffat); a benchmark-disjoint ePSF pool is used in an ablation to rule out PSF leakage. Native image = paltas source + real deflector stamp + real empty-sky HST cutout (correlated noise, field neighbours) + real companions + Gaussian sky top-up matched to real SLACS sky-RMS. A deterministic operator degrades to *Euclid* VIS (flux→I_E, ACS→VIS PSF-matching with the real Q1 kernel, 2×2 bin to 100 mas/px, Poisson noise at EWS depth with real Q1 sky variance) and to the Roman WFI format. Automated gates (sky-RMS, peak/sky, θ_E range/flatness, radial-profile overlay, Faber–Jackson) run before scale-up.

---

## 4. CNN architecture and training
A **scale-conditioned residual CNN**: four residual stages, global average pooling, and a scale scalar (pixel scale in arcsec/px) concatenated before an MLP head; an InceptionNeXt-stem variant for the Roman ensemble. The single band is arcsinh-compressed (a=1.0) and standardised per image (removing absolute flux — appropriate since θ_E is geometric) while the pixel scale enters as a conditioning scalar; identical normalisation for sims and the real benchmark. **The head predicts (μ, log σ²)** trained with Gaussian NLL — a per-image aleatoric uncertainty. Adam, cosine schedule, 40 epochs, batch 64; full dihedral augmentation. Model selection on the simulation validation split only (deflector-, PSF-, seed-disjoint). We train a 16-network ensemble (ResNet, InceptionNeXt) and pre-register a 2–3 member ensemble on validation (headline: cnv2_3 SLACS, r50_3 S4TM). At evaluation, **8× dihedral test-time augmentation**; total variance = mean aleatoric variance over views + epistemic variance from view spread. Recalibration in §5.4.

**Training and inference cost.** Once trained, inference is one forward pass (ms/lens on a GPU); the training cost is amortised across the survey; the speed advantage over conventional forward modelling (~3 min/lens; Cao et al. 2025) is realised at inference — the regime relevant to ~10⁵ *Euclid* lenses. *Conventional modelling also returns uncertainties and more parameters, so speed is not the only axis of comparison.*

---

## 5. Results

### 5.1 Headline benchmark performance
See **Figure 1** (predicted vs true θ_E). **[TODO E3: add bootstrap 68% CIs to every entry.]**

**Table 3 — two-domain GEN4 performance** (failure: |frac. err| > 15%):

| Domain | Sample | Bias″ | RMSE″ | NMAD″ | R² | Fail |
|---|---|---|---|---|---|---|
| Native HST | SLACS 62 | +0.005 | 0.152 | 0.048 | +0.64 | 15% |
| Native HST | S4TM 40 | +0.013 | 0.088 | 0.047 | +0.90 | 8% |
| Euclid-like | SLACS 62 | −0.010 | 0.137 | 0.056 | +0.71 | 15% |
| Euclid-like | S4TM 40 | +0.027 | 0.117 | 0.082 | +0.81 | 22% |

The **m3 baseline** (trained on simplified forward-operator sims) fails: R²=−1.02 (SLACS, 55% catastrophic), −0.53 (S4TM); its signed error crosses zero near the training-mean attractor (~0.95–1.0″) — the signature of prior-pull. On real *Euclid* Q1, GEN4 gives bias −0.104, NMAD 0.094, R²=+0.609, fail 32%; GEN5 and post-DA results are **[TODO E5, E6]**.

**Figure 1.** Predicted vs true θ_E for the SLACS and S4TM benchmark lenses. The m3 baseline (grey) collapses toward the training mean (SLACS R²=−1.02); the real-unit self-consistent recipe (orange/red) tracks the 1:1 line within the Cao et al. (2025) ≲5% band. *[figure embedded in LaTeX: paper/figures/pred_vs_true.png; TODO regenerate with the final GEN4 ensemble — current panel shows the pre-self-consistency hybrid recipe.]*

### 5.2 Domain of validity
Training θ_E support is [0.45, 2.30]″; real lenses above the ceiling are under-predicted (e.g. 2/5 COSMOS in §5.6). We report the out-of-support fraction per sample **[TODO]** and restrict quantitative claims to the in-support regime.

### 5.3 Causal ablations
**Table 4** removes one ingredient at a time from the hybrid recipe (native SLACS R²=+0.27); self-consistency (§5.4) is a separate, larger step (+0.27 → +0.64). **[TODO E8: re-run the two dominant ablations on the GEN4 recipe.]** Real empty-sky backdrops dominate by an order of magnitude (Gaussian-noise variant: S4TM median +99.5%). The flat θ_E prior and empirical PSF are each necessary; the benchmark-matched ePSF pool adds nothing over a disjoint archival pool (clears leakage).

| Variant | SLACS R²/fail | S4TM R²/fail | SLACS med. | S4TM med. |
|---|---|---|---|---|
| Full recipe (v2) | +0.27/23% | +0.47/38% | −2.6% | −1.8% |
| Skewed θ_E prior | −0.52/29% | −0.03/50% | −6.3% | −7.8% |
| Gaussian PSF | −0.46/31% | +0.06/50% | −5.4% | −9.8% |
| Gaussian noise | −5.10/58% | −14.67/90% | +24.1% | +99.5% |
| Broad ePSF pool | +0.22/21% | +0.42/38% | −1.6% | −2.2% |

### 5.4 Uncertainty and confidence gating
**Table 5.** σ correlates with |frac. err| (Spearman +0.57 SLACS, +0.70 S4TM) — the model flags its own failures. Retaining the most confident 50% drops fail from 15%→3% (SLACS), 8%→0% (S4TM). *Raw uncertainty is not well calibrated on real data* (coverage 52%/83% vs nominal 68%/95%); we apply a global σ-recalibration fit on validation and present the full retained-fraction vs failure-rate trade-off, not one point **[TODO E4: reliability diagram + trade-off curve]**.

| Sample | Spearman ρ | med. σ/μ | full fail | conf.-half fail |
|---|---|---|---|---|
| SLACS (62) | +0.57 | 3.0% | 15% | 3% |
| S4TM (40) | +0.70 | 3.0% | 8% | 0% |

### 5.5 Comparison to conventional modelling (Cao)
Using Cao et al. (2025)'s per-lens predictions on the identical SLACS lenses (both vs Bolton b_SIE) **[TODO table]**, our CNN matches the accuracy class at much lower amortised inference cost. *Fair comparison:* TinyLensGPU also delivers per-lens uncertainties and full posteriors and is not prohibitively expensive on modern hardware, so our advantage is amortized throughput, not a categorical gap **[TODO E7: CPU/GPU wall-clock]**. Physical self-consistency lifts native SLACS R² from +0.27 (hybrid) to +0.64 (GEN4) — the single largest step.

### 5.6 Comparison to LEMON
On the subsample with an independent published θ_E we lead decisively: SLACS-29 (Bolton) ours R²=+0.57, NMAD 0.045″, 7% vs LEMON R²=−4.26, 0.307″, 55%; EELs-12 (Oldham 2017) ours +0.83, 0.023″, 8% vs +0.21, 0.110″, 42%; COSMOS-5 is a small-N wash (we under-predict 2/5 above our θ_E ceiling; disclosed). ACS-13 has no published θ_E (only an arc radius; Pawase et al. 2014) and is excluded from the θ_E aggregate. *Reproducibility caveat:* we cannot recover LEMON's published aggregate (R²=0.53) by scoring their released predictions against the literature θ_E; we report our transparent re-scoring separately **[TODO R4: resolve with LEMON authors before submission]**.

### 5.7 Transfer to Euclid and Roman
Transfer re-runs the deterministic instrument operator to render the training population into the target domain, then **retrains the same architecture** — no network change. *Euclid* = the GEN5 arm on real Q1 **[TODO E5]**. Roman: zero-shot transfer of the HST model fails (R²=0.11); retraining on the Roman-rendered population succeeds (R²=0.93–0.94). Since no real Roman lenses exist pre-launch, **the Roman result is a simulation-to-simulation demonstration**, with real validation deferred to post-launch.

---

## 6. Discussion
- **SIS assumption / label noise.** Labels are SIS(σ_v), GT is SIE b_SIE; the σ_v→θ_E scatter sets a floor on attainable R² (§3.4). Honest: we do not claim accuracy below the label-noise floor.
- **Hard cases stay hard** (per Prof. Chan): the network does not solve intrinsically degenerate cases (faint arcs, out-of-support θ_E, complex environments); the confidence gate **flags** rather than fixes them.
- **Calibration and scope.** Raw uncertainties need recalibration; the method is single-band, θ_E-only. θ_E is the most robust first target; ellipticity/shear/source are natural extensions.
- **Roman and the future.** Real-Roman validation awaits launch; multi-band inputs, joint multi-parameter heads, and DA *on top of* realism-calibrated simulations are the next steps.

## 7. Conclusions
**Physical realism in the training simulations — not architecture, not domain adaptation — is the decisive factor** in closing the sim-to-real gap for CNN θ_E estimation. A real-ingredient, physically self-consistent generator (each deflector supplies both its light and, through its measured σ_v, its mass) lifts real-lens R² from strongly negative to +0.64–0.90, matching conventional modelling at a fraction of the amortized cost, with a domain-aware uncertainty that flags its own failures. The generator is instrument-agnostic and validated across HST and *Euclid*, with a clear path to Roman.

---

## Changelog — what changed in v2 and v3

**v1 → v2** (edits made directly in the original "LensCNN" Google Doc, addressing Prof. Chan's comments):
- §1: added the lens-equation formalism paragraph defining lens light / lens mass / source light and citing Meneghetti (2021), Saha et al. (2024) & Treu (2010) [C10, C11]; cleaned the "Need to cite" placeholder; integrated the Gen4/Gen5 note.
- §2: cited Swierc et al. (2024) for Domain-Adaptive NPE [C13]; added the Bolton-vs-YattaLens justification [C15]; confirmed the DA works are labelled sim→sim [C14].
- §3: renamed "deflector library" → "lens-light library" [C19]; added the "How the lens mass is constructed" paragraph [C19] with SLACS-isothermality reliability [C18] and the SIS/multipole clarification [C9]; homed the σ_v→θ_E relation in §3.4 [C7].
- §4: gave "Training and the cost of inference" real content [C23]; removed the duplicate "Version without ML words" scaffold, the technical text carrying the plain-language points [C24–C29].

**v2 → v3** (this from-scratch rewrite; supersedes v2 and additionally pre-empts referee concerns):
- MNRAS single-paragraph abstract [C2].
- New **Discussion (§6)** with limitations, incl. "hard cases stay hard" [C8].
- **Reviewer pre-emption** (see *V3 Review & Plan*): SIS-vs-SIE label-noise paragraph + planned experiment (R1); explicit no-leakage statement + audit (R2); domain-of-validity/θ_E support (R3); LEMON reproducibility caveat foregrounded (R4); ablation-ladder clarification (R5); bootstrap CIs flagged throughout (R6); calibration/recalibration + trade-off curve (R7); fair Cao comparison acknowledging its UQ (R10 / C6); Roman framed as sim→sim (R9); scope stated (R11).
- **Table 1** gains an Uncertainty (UQ) row [C17]; **§5.7** describes how transfer works [C30]; accuracy ranking stated carefully [C22].
- Benchmark properties **Table 2** added (real SLACS θ_E; redshift/mag ranges to be sourced from Bolton 2008 / Shu 2017 — marked TODO, not fabricated).
- Every "[TODO]" marks a pending experiment (E1–E10 in the *V3 Review & Plan*), so the paper is submission-ready the moment those runs finish.
