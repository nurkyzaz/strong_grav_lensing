# CLAUDE.md — Strong-lensing θ_E CNN (paltas pipeline; operated over SSH)

You (Claude Code) run LOCALLY on Nurkyz's Mac. Code, data, and compute live on a
remote cluster reachable via `ssh nurkyz@gpus`. Read this file fully before acting.
It is project memory. **`DECISIONS_LOG.md` in this folder is the single most
authoritative file — if anything here conflicts with it, DECISIONS_LOG.md wins,
and say so out loud rather than silently picking one.**

## Superseded document warning

A document titled "Project Instructions for Claude" describing CNN training data
generated via LensFusion's own `forward_operator` + IllustrisTNG κ maps (κ̄=1 labels,
Gaussian PSF/noise) may exist in this folder or be pasted again later. **Its
data-generation approach is SUPERSEDED** (see DECISIONS_LOG.md, 2026-07-02 pivot and
2026-07-05 ruling) — the actual project uses **paltas**, real ACS PSF, HST-calibrated
noise, and **SIE θ_E labels** (not κ̄=1). That document's terminology section (source
vs. lens vs. lens light vs. convergence) and its Phase-2 non-differentiability
caution are still valid background. If you see it, treat data-generation claims in
it as historical, not current.

## Code repository

GitHub (private): **https://github.com/nurkyzaz/strong_grav_lensing** — this Mac folder is
the working tree (`main`). Layout convention (set by the initial curation, keep it):
the FLAT root files are the live working copies and stay UNTRACKED; the repo tracks
curated mirrors — `docs/` (the .md/.tex docs), `pipeline/` (~/cosmos_acs/tiles scripts),
`training/` (~/einstein_cnn scripts), `analysis/` (Mac-side scripts), `results/`
(per-lens prediction CSVs + forensics), `tables/`, `paper_figures/`. To publish: copy
root docs into `docs/`, pull current cluster scripts into `pipeline/`+`training/`,
add new eval CSVs to `results/`, commit, push. **Push policy (Nurkyz ruling
2026-07-10): push whenever meaningful changes accumulate** — a logged eval, a new
plan/stage, a new script generation, or a DECISIONS_LOG milestone; don't wait to be
asked, and don't push mid-experiment noise. Data/binaries never enter git
(*.h5, *.pt, *.npy, PDFs, epsf_library/ — cluster or Zenodo).

## Cluster operational facts (validated by a prior orientation pass — do not re-derive)

- Login shell is **csh**. Every remote command needs `bash -lc '...'` wrapping:
  `ssh nurkyz@gpus "bash -lc 'cd ~/cosmos_acs/tiles && python foo.py 2>&1'"`
  Bare `cmd 2>&1` over plain ssh fails with "Ambiguous output redirect".
- **No tmux/screen on the login node.** It's a SLURM head node (`sbatch`/`squeue`
  present; `nvidia-smi` fails on the head node itself — GPUs are on compute nodes,
  presumably a1–a6). Long jobs (pilot generation past a few minutes, training, full
  dataset generation) go through **SLURM batch scripts**, not tmux. Write an
  `.sbatch` file, `sbatch` it, poll with `squeue -u nurkyz`, read logs from the
  SLURM output file — do not block a foreground ssh session on a long job.
- **Quota 75/100 GB** (as of last check — re-verify with `quota -s` or the cluster's
  equivalent before any large generation run). A ~3 GB pilot fits; delete superseded
  datasets/checkpoints before generating a new full (50–100k image) set.
- conda env `Stronglensing`, Python 3.8 → no backslashes inside f-strings.
- Working dirs: `~/einstein_cnn/` (models, benchmark, metrics, diagnostics),
  `~/cosmos_acs/tiles/` (paltas config, PSF file, generation/fix toolchain).
- **Monitors report, the session submits** (rule adopted after the 2026-07-10 merge
  collision): completion-monitors and watcher loops must never carry submission
  side-effects that can race a manual action. Only an explicit submit script (the
  `sbatch --wait` wave pattern, e.g. `submit_pathb.sh`/`submit_l1.sh`) or the live
  session may submit jobs.
- ssh prints a quota banner on STDOUT — never pipe binary data (tar) through a plain
  ssh channel; write to a cluster file and `scp` it instead.

## Environment pins (violating these breaks things — see DECISIONS_LOG.md for why)

- paltas **0.2.0**, installed with `--no-deps` (its numpy pin must never be
  resolved). Do **not** downgrade to 0.1.1 (calls `ProfileListBase._import_class`,
  removed from our lenstronomy → crash). Do **not** upgrade lenstronomy past the
  current ~1.12–1.13 band (≥1.14 renames `DataAPI` numpix→num_pix and breaks paltas
  0.2.0; ≤1.11 breaks on modern numba).
- Config `config_lensfusion_acs.py` defines an `ApparentSersic` subclass for lens
  light (paltas 0.2.0 treats `magnitude` as absolute; this restores the apparent
  convention) and `mag_cut` (anti-blob gate). Do not remove either.

## Established diagnoses — paid for, do not re-litigate without new evidence

1. **Prior-pull**: `einstein_cnn_m3.pt` fails on real lenses because its training
   θ_E prior was narrow/skewed → predictions collapse to ~0.95–1.0″. Fix = paltas's
   flat θ_E prior. Failure was distributional, not architectural — keep the m3
   architecture unless a gate proves otherwise.
2. **paltas 0.2.0 magnitude convention**: `SingleSersicSource.magnitude` is
   ABSOLUTE. `ApparentSersic` fixes lens light. If a Sersic SOURCE is ever added,
   its convention must be decided explicitly (COSMOSCatalog, the current source,
   is unaffected — it uses its own photometry).
3. **Central square artifact = truncated PSF kernel support, CONFIRMED** (27×27 px
   kernel → 26 px square; discontinuity ratio 107.6; absent under Gaussian PSF).
   The COSMOS-stamp-footprint hypothesis was tested and RETRACTED (stamp noise
   subdominant, ratio 0.38) — don't re-propose it.
4. **The PSF kernel itself is a known weak link**: edge_median/peak = 0 with
   edge_max/peak = 1.6e-2 → empirical stamp, noise floor ~0.5% of peak, negatives
   clipped to zero. `fix_psf_kernel.py`'s wing-extension has hardening for exactly
   this (adaptive r0, alpha cap, >10% flux abort guard) — always run
   `inspect_psf_kernel.py` first and choose `--r0`/`--alpha` from its output, don't
   trust naive extension on a noise-dominated stamp. Standing parallel ask: request
   a larger/cleaner ACS PSF from Sam (TinyTim or star stack, ≥51 px).
5. **mag_cut = 3.0** rejects unlensed-blob geometries on purpose. Log acceptance
   rate every run; exactly 1.0 with no mag_cut = bug.
6. **κ̄=1 vs SIE offset**: paltas SIE labels match the SLACS b_SIE benchmark
   directly — no conversion needed for evaluation. (Only matters again if Phase 2
   ever compares against a sampler-side κ̄=1 θ_E — flag, don't solve, until then.)
7. **The original empirical `acs_psf.npy` is RETIRED** (2026-07-05): only ~15% of
   its flux was in the core, ~70% in a noise plateau — it, not just its truncation,
   was why old previews looked strange. Real STScI focus-diverse ePSFs replaced it.
8. **Independent-marginal priors are an anti-pattern for lens light**: data-driven
   mag and Re priors sampled independently produced faint+huge deflectors nature
   doesn't make (peak/sky collapsed). Sample JOINT empirical (mag, Re) pairs.
9. **Aperture vs total magnitude**: paltas `magnitude` is the Sérsic TOTAL; an
   r=2″ aperture on an Re≈2″ n=4 galaxy holds only ~50% of the light. Any
   photometric prior derived from cutouts needs the incomplete-gamma
   aperture-to-total correction (`build_lens_light_prior.py` does this).
10. **Docs may promise scripts that don't exist** (`inspect_psf_kernel.py` and the
    hardened `fix_psf_kernel.py` flags were specified but never shipped). Verify a
    tool exists and read its actual `--help` before building a plan around it.
11. **Every SLURM partition here (normal/a/b/c) requires `--gres=gpu:N`**, even for
    pure-CPU jobs (paltas generation uses no GPU) — omit it and `sbatch` rejects
    the job outright. Request the minimum (`gpu:1`).
12. **QOS "normal" caps `MaxJobs`/`MaxSubmit` at 8.** Any array/job set bigger than
    8 must be split into sequential waves (`sbatch --wait` per wave), not submitted
    at once — `--array=0-21` or even three concurrent 8-task arrays both fail.

## Hard rules

- **FROZEN BENCHMARK, disclosed integrity gap**: `real_slacs_images.h5` (62) and
  `real_s4tm_images.h5` (40) are test data. DECISIONS_LOG.md 2026-07-05 records that
  they were already evaluated an unrecorded number of times in prior sessions
  (pre-dating logging discipline) — that's done and can't be undone, but from now
  on: never train or tune on them, evaluate only at explicit human checkpoints, and
  log every single evaluation here with a running count. Model selection uses ONLY
  a held-out simulation validation split.
- **Anti-blob discipline**: never generate more than 200 images until the previous
  pilot passes `gate_stage0.py`; never launch the full dataset until a 200-image
  pilot passes every gate. Every preview uses `preview_three_stretch.py` (linear /
  percentile / asinh) — a "blob" under one stretch is often a lens under another.
- **Diagnose before fixing**: reproduce/measure an artifact before changing config
  or code (pattern: `diagnose_components.py`, `diagnose_psf_square.py`,
  `inspect_psf_kernel.py`). One change at a time; re-smoke-test after each.
- **Log like a scientist**: dated entries in `DECISIONS_LOG.md` for every decision,
  fix, retraction, and benchmark evaluation. RETRACTED, not silently edited, when a
  hypothesis is disproven.
- Evolve `config_lensfusion_acs.py` with backups (the `.bak`/`.bak2` pattern already
  in use), don't rewrite it from scratch. Don't touch anything under `~/einstein_cnn/`
  starting with `real_`.

## Toolchain already present in ~/cosmos_acs/tiles/ (use, don't reinvent)

`run_paltas_pilot.py`, `preview_three_stretch.py`, `paltas_npy_to_train.py`,
`gate_stage0.py`, `diagnose_components.py`, `diagnose_psf_square.py`,
`inspect_psf_kernel.py`, `fix_psf_kernel.py`, `patch_config_apparent_sersic.py`,
`patch_config_clean_cosmos.py`, `measure_real_deflector_mags.py`,
`hybrid_combine.py` (the default image assembler), `side_by_side_real_sim.py`
(real-vs-sim gallery, run on every dataset version),
`config_lensfusion_acs_nonoise.py` (no_noise wrapper for hybrid generation),
`lens_light_empirical.csv` (joint mag–Re prior table). Read each script's own
docstring/`--help` before use; confirm it exists before planning around it.

On the Mac (this folder): `epsf_retrieve.py` + `.venv_epsf/` retrieve STScI
focus-diverse ePSFs into `epsf_library/{benchmark,broad}/` (169 + 52 cubes
retrieved 2026-07-05, manifests alongside).

## Staged plan with human checkpoints (STOP and report at each ⛔)

**STATUS (2026-07-06): Stages 0–2 DONE — see DECISIONS_LOG for the full record.**
`~/einstein_cnn/train_hybrid_100k.h5` (100k) + `val_hybrid_5k.h5` (5k, kernel- and
seed-disjoint) exist, merged from 22 SLURM shards, gated on the FULL merged set
(not just a 200-pilot) — all PASS. Next: Stage 3 training, gated on Nurkyz's
go-ahead (>30 min run, standing rule).
Config `config_lensfusion_acs.py` now runs: real STScI focus-diverse ePSF
(`acs_psf_epsf23_extended.npy`, wings extended, square-diagnostic 2.3), noise
calibrated (exposure_time 675 s), JOINT empirical lens-light prior
(`lens_light_empirical.csv`, per-lens Bolton-Re × aperture-corrected total mag,
sampled via `cross_object`). The **hybrid is the default training image**:
noiseless paltas render + real empty COSMOS cutout + Gaussian topup to a
per-image draw from the real SLACS sky-RMS distribution (`hybrid_combine.py`).
Hybrid pilot F passed ALL gates (sky-RMS 1.16, peak/sky 607, θ_E flat U[0.6,2.2])
with radial-profile overlay lying on the real one.

**Iteration law (learned the hard way, C→F):** ANY config change → 200-image
pilot → `gate_stage0.py` + `side_by_side_real_sim.py` must pass BEFORE any
larger run. One change at a time. Never trust a preview folder without checking
its embedded config copy and date (the `paltas_smoke8` lesson).

Stage 2 — full training set (IN PROGRESS):
  a. Config completion (each re-gated): decouple mass center from light center
     (light ≈ cutout center, mass jittered ~0.05″); widen source offsets to
     U(±0.25″); open source selection to full COSMOS depth (mag 23.5, smaller
     min sizes — the compact-source regime is a paper deliverable, don't
     exclude it); γ ~ N(2.0, 0.15).
  b. PSF diversity: per-SLURM-shard kernels drawn from the benchmark-matched
     ePSF bank (random exposure/chip/position/rotation, wings extended). The
     broad (non-benchmark) ePSF pool is reserved for the PSF-source ablation
     dataset (PAPER_PLAN "PSF-source design and ablation").
  c. Scale: 100k train = 20 SLURM shards × 5k (disjoint seeds, one kernel per
     shard) + 5k sim-val (disjoint seeds AND disjoint kernels). Per shard:
     generate noiseless → hybrid combine → h5 → preview first 16 → DELETE the
     intermediate npy (quota!). Merge to `train_hybrid_100k.h5` + `val_hybrid_5k.h5`.
  ⛔ merged-set gate table + per-shard previews + side-by-side before training.

Stage 3 — training: keep the m3 architecture (scale-conditioned ResNet, asinh
  input norm), Huber loss, Adam; optional (μ, log σ²) Gaussian-NLL head (per-lens
  error bars for the paper + Phase-2 weighting; drop it if it destabilizes).
  Flips/rotations OK for θ_E. Selection on sim-val ONLY. Target: sim-val median
  |frac err| ≲ 3%. ⛔ curves + sim-val metrics BEFORE any real-lens evaluation.

Stage 4 — the real evaluation (WITH Nurkyz, logged with running count):
  `metrics_real.py` on the frozen 62 SLACS + 40 S4TM; bootstrap CIs; per-lens
  scatter vs Cao et al. 2025 (their per-lens θ_E is public). SUCCESS = median
  within ±5%, R² > 0 (ideally > 0.5), failure (>15%) ≲ 10% — i.e. match/beat
  Cao on the same lenses; that is the paper's headline.
  Ablations (each = one dataset variant + one retrain, in this order):
  (1) flat vs m3-skewed θ_E prior (the causal spine); (2) benchmark-matched vs
  broad ePSF pool (the circularity answer); (3) real backdrop vs pure Gaussian
  noise; (4) real ePSF vs Gaussian PSF.

Stage 5 — multi-parameter (θ_E + e1/e2 + center) only after Stage 4 passes.
  Path B escalation criterion unchanged: only if the full-realism model still
  has R² < 0 on real lenses (then: real LRG cutouts as deflectors).

## Benchmark / literature context

Primary comparison: **Cao et al. 2025** (arXiv:2503.08586) — automated conventional
modeling pipeline (not a CNN), same 63 grade-A SLACS, same b_SIE ground truth, ≲5%
deviation / ~10% failure. Bar: match or beat on the same lenses. Secondary
CNN-to-CNN reference: **Gawade et al. 2025** (arXiv:2404.18897, ground-based HSC,
~10–20% error) and **Hezaveh et al. 2017** (Nature, foundational SIE-CNN). See
`LITERATURE.md` for what's confirmed vs. unverified from each.

## Style

Exact copy-paste commands in reports; plain-language explanation next to technical
results; flag uncertain physics explicitly ("confirm with Brian") rather than
asserting; before/after comparisons for every change. Ask before: any generation run
>1k images, any training run >30 min, any SLURM job you haven't shown the script
for first, deleting/rewriting (rather than patching) existing scripts/configs,
installing/upgrading packages, and any use of the real-lens files.
