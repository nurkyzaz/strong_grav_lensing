# PAPER PROVENANCE & GENERATOR REFERENCE (internal)

Purpose: a single, code-grounded ledger that maps **every number and claim in the
LensCNN manuscript** (`paper/LensCNN*.md`) to the file, line, CSV, or DECISIONS_LOG
entry it came from — plus a detailed walkthrough of the generator for writing §3.
Written 2026-08-03 by reading the actual code (`pipeline/`, `training/`,
`analysis/`) and records (`DECISIONS_LOG.md`, `COMMITMENTS.md`,
`docs/MODELS_AND_RESULTS.md`, `GENERATOR_AND_CODEBASE_REFERENCE.md`). Every row
marked ✓ was verified against the cited source in this pass. Rows marked ⚠ are
discrepancies to fix in the manuscript. Rows marked ❓ need one more check before
submission.

Companion doc: `../GENERATOR_AND_CODEBASE_REFERENCE.md` (generator walkthrough,
photometry/units chain). This file adds the **paper-claim → source** mapping and
the **GEN4-vs-GEN5** bookkeeping the manuscript keeps conflating.

---

## 0. The one distinction the paper must keep straight: GEN4 vs GEN5

The paper's own P.S. (LensCNN (2).md) says "Gen4 = HST-like (low-z), Gen5 =
Euclid/Roman (high-z)". Keep this rigid, because the numbers differ:

| | GEN4 (paper's CORE result) | GEN5 (Euclid/Roman extension) |
|---|---|---|
| Domain | native HST + Euclidised-HST bench | migrated high-z, Euclid Q1 + Roman |
| Deflector library | **139 stamps** (119 train / 20 val) | **488 stamps** (`tables/g1b_kinematics_v1.csv`) |
| Manifest builder | `g2_make_manifest.py` | `g5_make_manifest.py` |
| paltas config | `config_lensfusion_acs_g2.py` | `config_lensfusion_acs_g5.py` |
| Multipoles | none (PEMD+shear) | AR3 isophote-anchored m=3,4 |
| Source | Newton-renormalized COSMOS | `Gen5HighZSource` (+ z-dimming) |
| Train scale | **104,314 train / 6,907 val** | Roman G5a ≈ 10,660 train |
| Headline eval | native SLACS **+0.64**, Euclid **+0.71** | Roman challenge-val +0.93–0.94; real Q1 miss |

**The headline table (§5.1) is GEN4. The ablation table (§5.2) is the PRE-GEN4
hybrid "v2" recipe (+0.27).** These are two different models — see §5 note below.

---

## 1. Verified numbers ledger (paper claim → source)

### Benchmark & data
| Claim (paper) | Value | Source | ✓ |
|---|---|---|---|
| Frozen benchmark size | 62 SLACS + 40 S4TM | `docs/MODELS_AND_RESULTS.md`; 1 dropped = J0955+0101 | ✓ |
| Ground truth | Bolton 2008 SIE b_SIE | `bolton08_table5.csv`, 63 grade-A rows | ✓ |
| Cutout geometry | 128 px @ 0.05″/px = 6.4″ | `GENERATOR_AND_CODEBASE_REFERENCE.md §2.1` | ✓ |
| AB zeropoint (F814W) | 25.94 | `pipeline/config_lensfusion_acs.py:22` | ✓ |
| Euclid VIS zeropoint | 23.9 | `GENERATOR_AND_CODEBASE_REFERENCE.md §2.6` (euclidise.py, cluster) | ✓ |
| Exposure / sky | 675 s, sky_brightness 22.1 | `pipeline/config_lensfusion_acs.py:114` | ✓ |
| θ_E training range | [0.45, 2.30]″ | `pipeline/g2_make_manifest.py:28-29` | ✓ |

### Source catalog (§3.2)
| Claim | Value | Source | ✓ |
|---|---|---|---|
| Catalog | COSMOS_23.5, 56,062 gals | `DECISIONS_LOG.md:200,3173` | ✓ |
| SB cut ≤21 (SLACS) | 7,808 / 56,062 | `DECISIONS_LOG.md:3173`; `config_lensfusion_acs_pathb_euclid.py:72` | ✓ |
| SB cut ≤22.5 (Euclid) | 28,388 / 56,062 | `DECISIONS_LOG.md:200` | ✓ |
| SB formula | SB_eff = mag_auto + 2.5·log₁₀(2π·(flux_radius·pix)²) | `config_lensfusion_acs_pathb_euclid.py:26,43` | ✓ (see ⚠ below — paper drops the ·pix) |
| Source renorm | Newton et al. 2011, mean≈24.3 at z≈0.65 | `GENERATOR_AND_CODEBASE_REFERENCE.md §2.3` | ✓ |

### Deflector library (§3.3) & GEN4 physics (§3.4)
| Claim | Value | Source | ✓ |
|---|---|---|---|
| GEN5 library | 488 measured stamps | `tables/g1b_kinematics_v1.csv`; `COMMITMENTS.md C5`; `DECISIONS_LOG.md:740,1034` | ✓ |
| GEN4 library | 139 stamps (119/20 split) | `pipeline/g4_split_kine.py`; `DECISIONS_LOG.md:2349` | ✓ |
| Per-stamp measured | σ_v, z_l, mag, Re, q, PA, a3/b3/a4/b4 | `g1b_measure_stamps.py:41`; `g1b_kinematics_v1.csv` | ✓ |
| θ_E from σ_v | SIS: 4π(σ_v/c)²·D_ls/D_s | `g2_make_manifest.py:8` | ✓ |
| Mass shape | q_mass=q_light⊕0.08; ΔPA~N(0,10°) | `g2_make_manifest.py`; ref doc §3 | ✓ |
| Tempered α | 0.6 (flat θ_E, keeps ρ(mag,θ_E)≤−0.15) | ref doc §3; old PAPER_DRAFT.md §2.4 | ✓ |
| σ_v→θ_E normalization | f_SIS correction /0.948 (~11% low) + 7% scatter | `COMMITMENTS.md C15` | ✓ (disclose as limitation) |

### Headline results (§5.1) — all GEN4
| Domain / sample | bias / RMSE / NMAD / R² / fail | Source | ✓ |
|---|---|---|---|
| Native HST SLACS 62 | +0.005 / 0.152 / 0.048 / **+0.64** / 15% | `docs/MODELS_AND_RESULTS.md` (eval #21, g4n cnv2_3) | ✓ |
| Native HST S4TM 40 | +0.013 / 0.088 / 0.047 / **+0.90** / 8% | same (eval #21, r50_3 derived) | ✓ |
| Euclid SLACS 62 | −0.010 / 0.137 / 0.056 / **+0.71** / 15% | same (eval #19, G4 cnv2_3) | ⚠ local CSVs give **R²+0.68** (bias −0.005, RMSE 0.145, NMAD 0.047, fail 11%) from `preds_l17_g4_cnv2_s[123]`; +0.71 needs the cluster recal (`g4_recal.json`) — reconcile |
| Euclid S4TM 40 | +0.027 / 0.117 / 0.082 / +0.81 / 22% | same (eval #18, **G3** r50_3) | ✓ recomputed +0.815 from `preds_l18_g3_r50_s[123]` (note: G3 model, not G4) |

**VERIFICATION PASS 2026-08-03 (recomputed from `results/preds_*` CSVs):**
- Native SLACS cnv2_3: R²**+0.640**, bias +0.008, RMSE 0.153, NMAD 0.048, fail 16% → matches +0.64 ✓
- Native S4TM r50_3: R²**+0.894**, bias +0.018, RMSE 0.089, NMAD 0.049, fail 8% → matches +0.90 ✓
- Euclid SLACS cnv2_3 (63 / 62-no-J0955): R²**+0.677 / +0.674** → draft says +0.71 ⚠ (recal gap)
- Euclid S4TM G3 r50_3: R²**+0.815** → matches +0.81 ✓
- **Headline mixes architectures per sample:** native SLACS = cnv2_3, native S4TM = r50_3, Euclid S4TM = G3 r50_3. Disclose this ("best per-architecture ensemble per sample") or unify.
- **Latest real Euclid Q1** (l25 ens2, GEN4/g4ar zero-shot, eval #25): full R²**+0.573**, in-support R²**+0.609**, bias −0.098, med −7.7%, fail 32% → matches records ✓. **No GEN5-trained model has been evaluated on real Q1 (GEN5 full-gen HELD 2026-08-02).**

### Causal chain (§1.4, §5, §6.1)
| Step | R² | Source | ✓ |
|---|---|---|---|
| m3 baseline (native) | −1.02 / fail 55% | `docs/MODELS_AND_RESULTS.md`; old PAPER_DRAFT.md §4.1 | ✓ |
| + flat wide θ_E prior | → ~0 | MODELS_AND_RESULTS causal chain #1 | ✓ |
| + real-unit hybrid (v2) | → +0.27 / fail 23% (native) | causal chain #2; old PAPER_DRAFT.md §4.3 | ✓ |
| + GEN4 self-consistency | → **+0.64** (native) / +0.67 (Euclid, eval #17) | causal chain #3 | ✓ |

### Ablations (§5.2) — on the v2 (PRE-GEN4) recipe, evals #3–#6, 2026-07-06
| Variant | SLACS R²/fail | S4TM R²/fail | Source | ✓ |
|---|---|---|---|---|
| v2 full recipe | +0.27 / 23% | +0.47 / 38% | old PAPER_DRAFT.md §4.5 (Table 6) | ❓ re-cross-check vs saved CSVs |
| Skewed θ_E prior | −0.52 / 29% | −0.03 / 50% | same | ❓ |
| Gaussian PSF | −0.46 / 31% | +0.06 / 50% | same | ❓ |
| Gaussian noise | −5.10 / 58% | −14.67 / 90% (S4TM med +99.5%) | same | ❓ |
| Broad ePSF pool | +0.22 / 21% | +0.42 / 38% | same | ❓ |

Note: these are internally consistent with the "backdrops dominate" narrative and
match the old draft exactly, but were logged pre-consolidation. Before submission,
regenerate from the saved ablation prediction CSVs and re-tabulate.

### Uncertainty (§5.3) — ⚠ STALE: draft quotes hybrid-v2 numbers; GEN4 differs
| Claim | Draft (v2-era) | **GEN4 recomputed 2026-08-03** | Source |
|---|---|---|---|
| Spearman(σ/μ, |frac err|) SLACS | +0.71 | **+0.57** | `preds_l21_ens_real_slacs_images.csv` |
| Spearman(σ/μ, |frac err|) S4TM | +0.39 | **+0.70** | `preds_l21_ens_real_s4tm_images.csv` |
| median σ/μ on real | ~9–10% | **3.0% (SLACS), 3.4% (S4TM)** | recompute |
| Confident-half SLACS (σ/μ≤median) fail | 6% | **3%** (N=32) | recompute |
| Confident-half S4TM fail | 15% | **0%** (N=20) | recompute |
| σ/μ≤q75 SLACS fail | 7% | **9%** (N=47) | recompute |
| σ coverage 1σ/2σ | sim-val 76/96; real 52/83 | ❓ (needs sim-val CSV, cluster) | old draft §4.6 |

**Action:** update §5.3 to the GEN4 numbers. They remain a strong result — the
gating still works (confident-half fail 3%/0%), and S4TM Spearman actually improves
to +0.70. But the specific numbers (+0.71/+0.39, "9–10%", "fail 6%") are from the
superseded hybrid-v2 model and must be replaced.

### LEMON head-to-head (§5.5) — VERIFIED against CSVs this pass
| Subsample | Ours | LEMON | Source CSV | ✓ |
|---|---|---|---|---|
| SLACS-29 (Euclid arm) | R²+0.571, NMAD 0.045, fail 7% | R²−4.263, NMAD 0.307, fail 55%, bias +0.288 | `results/lemon_vs_ours_slacs29.csv` | ✓ |
| SLACS-29 (native arm) | R²+0.295, NMAD 0.038, fail 10% | — | same | ✓ |
| EEL-12 (native arm) | R²+0.834, NMAD 0.022, fail 8% | R²+0.208, NMAD 0.110, fail 42% | `results/lemon_vs_ours_eel_cosmos_acs.csv` | ✓ |
| EEL-12 (Euclid arm) | **R²−1.209**, NMAD 0.019, fail 8% | same | same | ⚠ paper uses native arm here but Euclid arm for SLACS — arm-mixing, disclose |
| COSMOS-5 (native) | R²+0.242, bias −0.39 (under) | R²+0.123, bias +0.36 (over) | same | ✓ |
| ACS-12 arc-radius (native) | R²−0.34, NMAD 0.310, bias −0.57 | R²+0.36, NMAD 0.358, bias −0.05 | `lemon_comparison_package/README.md` | ✓ |
| Combined-46 vs GT | RMSE 0.44, NMAD 0.06, R²+0.14 | RMSE 0.48, NMAD 0.23, R²≈0.00 | `lemon_comparison_package/README.md` | ✓ |
| LEMON published Table 3 (unreproducible) | — | RMSE 0.14, NMAD 0.11, R²0.53 | LEMON paper; author inquiry in progress | ✓ |

### Euclid Q1 real (§5.6) — a KNOWN MISS
| Claim | Value | Source | ✓ |
|---|---|---|---|
| Our sample | N=322 (of LEMON's 354; 13 GT empty +14 no-GT) | `DECISIONS_LOG.md:724,1809` | ✓ |
| Grade split | 185 A + 129 B + 8 C | `DECISIONS_LOG.md:1733` | ✓ |
| Best zero-shot (#25 ens2) | in-support R²+0.61 / fail 32% / bias −8% | `DECISIONS_LOG.md:729`; MODELS_AND_RESULTS | ✓ |
| Verdict | BELOW LEMON's own Q1 (R²+0.71); P(beat)=0.01 | `DECISIONS_LOG.md:730-735` | ✓ |
| Physical reading | failure is a SLOPE (compression): faint Q1 deflector → small σ_v → small θ_E via our FJ channel; worst on big lenses | `DECISIONS_LOG.md:1805,1818-1830` | ✓ |
| One-line finding | "Euclidising the benchmark ≠ Euclid-ready: the operator transfers, the population prior does not." | `DECISIONS_LOG.md:1827` | ✓ |

### Roman (§5.6)
| Claim | Value | Source | ✓ |
|---|---|---|---|
| LEMON Q1 (their turf) | R²0.71, NMAD 0.07 | LEMON Fig 12a | ✓ |
| G5a retrain (challenge-VAL) | R²+0.93–0.94 / fail 6–9% | `DECISIONS_LOG.md:765-769,1562` | ✓ (⚠ self-graded, sim val; hidden-test PENDING) |
| G5b zero-shot HST/Euclid→Roman | R²+0.11 / fail 59% | `DECISIONS_LOG.md:771-774` | ✓ |
| Roman challenge format | 3-band, Rung 0, submitted; grade pending | `COMMITMENTS.md C20` | ✓ |

### Cao et al. 2025 (§2.1, §5.4)
| Claim | Value | Source | ✓ |
|---|---|---|---|
| TinyLensGPU, 63 grade-A SLACS | ≲5% dev, ~10% fail, ~3 min/lens | `docs/LITERATURE.md:64` | ✓ |
| Per-lens preds provided | yes | `docs/LITERATURE.md`; §5.4 | ✓ |

---

## 2. DISCREPANCIES TO FIX (⚠ — ordered by severity)

1. **Abstract (LensCNN (1).md) real-Euclid-Q1 line is wrong & unfinished.**
   Says "…we achieve _(in the process)__ , also surpassing LEMON (hopefully)."
   Records: real Q1 is a **MISS** (R²+0.61 in-support < LEMON 0.71). Do NOT claim
   surpassing LEMON on real Q1. Either drop the real-Q1 claim from the abstract or
   state it as the honest current frontier. Contradicts §5.6 (which is correct).

2. **Abstract "surpassing LEMON on every aggregate θ_E metric"** is true only for
   the **shared-lens Euclidised-HST** comparison (SLACS-29, EEL-12), NOT for real
   Euclid Q1. Scope the sentence to the shared-benchmark comparison.

3. **§5.5 arm-mixing.** SLACS-29 leads with the **Euclid** arm (R²+0.57), EEL-12
   with the **native** arm (R²+0.83). Our Euclid arm on EEL-12 is **R²−1.21**
   (worse than LEMON's +0.21). LEMON's predictions are Euclidised-HST domain, so
   the domain-matched comparison is our Euclid arm throughout. Either (a) report
   both arms for both subsamples (honest, recommended), or (b) justify the native
   arm explicitly. As written it reads as cherry-picking.

4. **§3.1 "300 real Euclid lenses"** → should be **322** (matches abstract, §2.4,
   §5.6). Fix the 300.

5. **§5.4 "identical 63 SLACS lenses"** vs our benchmark of **62** (J0955+0101
   dropped). Reconcile: compare on the 62 (or the overlap) and say so.

6. **Deflector-library number conflation.** §3.3 says "expanded to 488"; the CORE
   GEN4 results use **139**. §6.3 limitation says "139 stamps; 488 expansion
   underway." State plainly: GEN4 (core) = 139; GEN5 (extension) = 488.

7. **§3.2 SB formula** drops the pixel scale: code is
   `mag_auto + 2.5·log₁₀(2π·(flux_radius·pix)²)`. Add the ·pix (or define
   r_flux in arcsec).

8. **§3.2 size cuts** "min_flux_radius=1.0, minimum_size=8 px": base config
   `config_lensfusion_acs.py:77,80` has `minimum_size_in_pixels=20`,
   `min_flux_radius=5.0`. The 1.0/8 numbers are from a different (Euclid-sel)
   config. Verify which config the paper's stated dataset used and cite that one.

9. **Roman R²0.93–0.94 framing.** It is **challenge-VAL, self-graded, sim-to-sim**
   (no real Roman data exists; hidden-test grade pending). Frame as "on the
   challenge's own validation set" and add "hidden-test grade pending" — do not
   let it read as a real-lens result.

10. **"LEMON R²=−4 on SLACS"** (§1.3 note) is OUR recomputation from LEMON's
    released predictions vs verified Bolton GT — defensible, but frame as such
    ("scoring LEMON's public predictions against Bolton b_SIE") and keep the
    reproducibility caveat (§5.5) attached.

---

## 3. Generator, end-to-end (for writing §3) — see also ../GENERATOR_AND_CODEBASE_REFERENCE.md

Chain (one population draw → three instrument renderings):

```
(A) MEASURE   g1b_measure_stamps.py      real HST early-types → (σ_v,z_l,mag,Re,q,PA,a3/a4)
              measure_real_deflector_mags.py  SLACS cutouts → lens_light_empirical.csv
(B) MANIFEST  g2_make_manifest.py (GEN4)  one row/image: pick galaxy→draw z_s→θ_E from σ_v (SIS)
              g5_make_manifest.py (GEN5)   + z-migration + AR3 m=3,4 multipoles
(C) RENDER    config_lensfusion_acs_g2.py  paltas/lenstronomy PEMD(+shear)(+multipole) → noiseless e⁻/s
(D) ASSEMBLE  hybrid_combine.py            render + real deflector stamp + real empty-sky cutout
                                           + real companions + Gaussian top-up (sky-RMS matched)
(E) OPERATOR  euclidise.py / Roman (G5a)   native-HST → Euclid VIS / Roman WFI (ZP, PSF, resample, noise)
(F) TRAIN     train_cnn_paltas.py          per-image asinh + z-score → scale-conditioned ResNet/InceptionNeXt, (μ,logσ²)
(G) EVAL      metrics_real.py              frozen 62 SLACS + 40 S4TM, Bolton b_SIE, running eval count
```

Units chain (the research-meeting question): everything is **e⁻/s, ZP 25.94**;
each light component is flux-calibrated in that system, all summed into one image;
the CNN input normalizes **once, on the combined image** (`arcsinh` a=1.0 then
per-image z-score, `train_cnn_paltas.py::normalize_images`), which removes absolute
flux — correct because θ_E is geometric. Pixel scale is passed as a separate
conditioning scalar. Full detail: `../GENERATOR_AND_CODEBASE_REFERENCE.md §2`.

Assembly (`hybrid_combine.py`, verified):
```
image = paltas_noiseless_source_render (e⁻/s)
      + real_deflector_stamp           (e⁻/s, NATIVE amplitude — GEN4 self-consistency)
      + real_empty_HST_cutout          (e⁻/s, median-subtracted: correlated noise + field galaxies)
      + real_field_companions          (e⁻/s)
      + Gaussian top-up                (sky-RMS matched to real SLACS distribution)
      (+ AR1 optional arc Poisson,   --arc_poisson)
```
GEN5 FJ deflector-mag clip: `--fj_mag_min/max` = [19.2, 23.4] (`COMMITMENTS.md C47`).

Euclid operator (`euclidise.py`, cluster; `patch_euclidise_realpsf.py` mirrored):
flux→VIS ZP 23.9, ACS→VIS PSF-match with real Q1 GRID-PSF kernel
(`acs2vis_matching_kernel.npy`; Gaussian = ablation only), 2×2 sum → 100 mas/px,
Poisson at 2280 s EWS depth (sky var ×~2.2, real Q1 noisier than nominal),
bilinear upsample back to 128 px.

Gates (`gate_stage0.py`, `ar0_arc_gate.py`): sky-RMS ratio 0.8–1.25; peak/sky in
real 16–84% band; θ_E range/flatness; radial-profile overlay; (Euclid) AR0 arc
contrast/width/knots/asymmetry. GEN4 full-scale gates: sky-RMS 0.956, peak/sky 919
vs real [574,1310], FJ gate PASS.

---

## 4. Key files (repo mirror; generator lives on cluster ~/cosmos_acs/tiles/)
- Manifests: `pipeline/g2_make_manifest.py` (GEN4), `pipeline/g5_make_manifest.py` (GEN5), `pipeline/g4_split_kine.py` (119/20 split)
- Measurement: `pipeline/g1b_measure_stamps.py`, `pipeline/measure_real_deflector_mags.py`
- Configs: `pipeline/config_lensfusion_acs.py`, `..._g2.py`, `..._g5.py`, `..._pathb_euclid.py` (HighSBCOSMOSCatalog)
- Assembly: `pipeline/hybrid_combine.py`; Euclid: `pipeline/patch_euclidise_realpsf.py`
- Train/eval: `training/train_cnn_paltas.py`, `pipeline/metrics_real.py`, `pipeline/gate_stage0.py`
- Comparison: `analysis/lemon_headtohead_recompute.py`; CSVs `results/lemon_vs_ours_*.csv`, `lemon_comparison_package/`
- Benchmark data: `real_slacs_images.h5` (62), `real_s4tm_images.h5` (40); library `tables/g1b_kinematics_v1.csv`

---

## 5. Provenance for the referee response
- All headline numbers: `docs/MODELS_AND_RESULTS.md` (summary) → `DECISIONS_LOG.md` (per-eval, dated, with slurm out-file names).
- Running eval count = 25 (through the 2026-08-01 consolidation).
- LEMON comparison fully reproducible: `analysis/lemon_perlens_comparison.py`, `analysis/lemon_acs_arcradius.py`.
- Open commitments (σ recalibration C11, σ_v→θ_E correction C15, GEN5 photometry match C44/C47): `COMMITMENTS.md`.
