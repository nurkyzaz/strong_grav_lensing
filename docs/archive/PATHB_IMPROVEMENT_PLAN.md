> **ARCHIVED 2026-07-13.** Superseded by docs/MASTER_PLAN.md (the single live plan).
> All undone items were carried into MASTER_PLAN.md at archive time. Historical record only.

# PATH B IMPROVEMENT PLAN — real deflector light, done right

Date: 2026-07-09. Author: Claude session with Nurkyz (pilot-v3 diagnosis session).
Status of each phase is tracked in the checklist below — UPDATE IT as you go.

**Read first, in this order: `CLAUDE.md` (operating rules), `DECISIONS_LOG.md` top entries
(2026-07-08 → 2026-07-09), this file. DECISIONS_LOG.md remains the single most authoritative
file; log every step there (dated entry) as you execute.**

---

## 0. Checklist (update in place)

| # | Phase | Status |
|---|-------|--------|
| P0 | Housekeeping: deletions (user-run), quota check | ✅ DONE 2026-07-09 (quota 49.5 GB, shards+v1/v2 gone) |
| P1 | Deflector brightness: peak/sky draw → empirical-magnitude scaling | ✅ P1b DONE & pilot-verified (v4 TOTAL-mag was 1.85× over-bright in-frame → scale to r=2″ APERTURE mag; pilot v4b: emergent peak/sky 950 vs real 994, absolute profile ON real) |
| P2 | 256 px LRG refetch + library rebuild (edge fix) | ✅ DONE 2026-07-09: `deflector_stamps_lrg_v6.h5` (49 stamps, 256px, prune list 7→26 — 256px revealed junk the old over-subtraction hid); pilot v5 PASSES, profile tracks real in shape+brightness. **⛔ awaiting Nurkyz visual sign-off** |
| P3 | Deflector dihedral augmentation + val-reserved stamps | ✅ DONE 2026-07-09: 41 train + 8 val stamps (`split_deflector_lib.py`), augment ON; pilot v6 PASS (peak/sky 959) |
| P4 | Calibration source: benchmark SLACS file → disjoint DA pool | ✅ DONE 2026-07-09: pool covers S4TM + SLACS bulk (`dapool_skyrms_check.png`); pilot v7 PASS (sky-RMS 1.23 — at the edge, expected & disclosed) |
| P5 | Arc-visibility metric + acceptance decision (⛔ Nurkyz) | ◐ metric v2 built & eye-calibrated (v1 retracted); v7: 58% eye-visible, 34% clear vs real ~75% — selection-bias-consistent. **⛔ decision pending** |
| P6 | Full 100k+5k generation + merged gate (⛔ Nurkyz sign-off before launch) | ◐ scripts staged on cluster (`*_v2`), NOT launched — awaiting ⛔ sign-off |
| P7 | Quick-train sanity → full training → benchmark evals #10/#11 (⛔ Nurkyz present) | ✅ DONE 2026-07-09, count→11. **Null result: real deflector light does not improve the benchmark** (v2-ResNet ≈ v3; causal decomposition complete). NEW positive: sim-val-frozen σ-recal transfers to real GT (ResNet 95/95% coverage). v3 IncNeXt stays primary; v2 ResNet = calibration exhibit |
| P8 | Parallel/optional: backdrop tiles retry, companion realism v2, paper chores | ☐ not started |

Rule that overrides everything: **ANY config/pipeline change → 200-image pilot →
`gate_stage0.py` numeric gates + side-by-side visual check BEFORE anything larger. One change
at a time.** Benchmark files (`real_slacs_images.h5`, `real_s4tm_images.h5`) are never trained
on; benchmark evaluations only at ⛔ checkpoints with Nurkyz, logged with the running count
(currently **9**).

---

## 1. Context — what Path B is and where it stands

Path B replaces the parametric Sérsic lens light with REAL elliptical-galaxy cutouts
(non-lens LRGs from the SLACS/S4TM parent samples, 84 fetched, benchmark-disjoint), pasted
onto arc-only paltas renders. Motivation: four independent diagnostics (ablations, DA
negative result, shared J0841+3824 failure with Cao's pipeline, companion experiment) all
point at real deflector-light CONTENT as the last unaddressed sim-to-real axis.

State as of 2026-07-09:
- Deflector library **v3** (`~/cosmos_acs/tiles/deflector_stamps_lrg_v3.h5`, 64 stamps,
  builder = `build_deflector_from_lrg.py` v5) fixed the "circular frame": the old builder
  multiplied stamps by a linear opacity ramp → visible circular boundary + profile
  distortion. v5 uses NO opacity ramp (corner-bg subtraction makes stamps ≈0 at corners
  naturally), neighbour replacement, trail/chip-edge rejection, 7-stamp visual prune.
- Pilot v3 passed all numeric gates (sky-RMS 1.04, peak/sky 795 in real band, θ_E range).
- **BUT Nurkyz's visual inspection of `real_vs_pathb_pilot_v3run.png` found 3 residual
  problems, all now root-caused quantitatively** (see §2). Fixing them is P1/P2.
- A Path B v1 model trained 2026-07-08 had sim-val MAE 0.194″ (v3-parametric: 0.064″) —
  the brightness bug in §2 is the prime suspect; P7's quick-train checks this.

---

## 2. The measured evidence driving P1 and P2 (from `inspect_pathb_pilot.py`, 2026-07-09)

`hybrid_combine.py --deflector_stamps` currently scales each stamp so its PEAK/sky equals a
draw from the real SLACS peak/sky array. Three measured consequences:

1. **Stamp concentration (peak/total flux) spans 31× across the 64-stamp library** → at
   fixed peak/sky draw, TOTAL deflector flux varies 31×. Peak-matching does not control
   how much light is in the image.
2. **Implied deflector TOTAL magnitudes span 13.5–22.1** (median 17.3) vs the real
   empirical prior 14.8–18.7 (median 16.8, `lens_light_empirical.csv`). Both tails are
   unphysical:
   - "tiny blob" panels (e.g. pilot SIM #129): peak/sky draw of **25** (the tail of the
     real array — almost certainly J0955+0101, the known-bad cutout that is excluded from
     metrics but still present in `real_slacs_images.h5`) → implied mag 21.97, invisible
     deflector.
   - "too bright, abrupt edge" panels (e.g. SIM #8): the most diffuse stamp × a high draw
     → implied mag 14.23 (2.6 mag brighter than ANY real deflector) with an edge step of
     7.8σ; sim edge-step tail reaches 27σ vs real max 9σ (sim median 2.77σ vs real 2.48σ
     — the MEDIAN is fine, the TAIL is the artifact).
3. **Arc burial / arcs visible in only ~2/8 panels**: deflector brightness is drawn
   independently of arc flux, so a 14th-mag deflector can sit on a 24th-mag arc. Also the
   overall wide nuisance range plausibly explains the Path-B-v1 sim-val collapse.

Additional confirmed bugs/facts:
- `deflector_mag` dataset in the output h5 actually stores the peak/sky draw (mislabel).
- `lens_light_empirical.csv` columns: `name, mag, re, mag_aper, aper_frac` — per-lens
  JOINT (mag, Re); paltas ZP = 25.94; images are e-/s. Everything needed for physical scaling.
- `fetch_real_lens_images.py` (in `~/einstein_cnn/`) supports `--box` and `--npix` →
  256 px refetch is one flag. The MAST cache was purged, so it re-downloads (~1.5 h, login
  node nohup is the established pattern for this script).
- COSMOS tiles 071/072 downloads FAILED silently (see `tile_dl.log`: gzip "No such file");
  only tile 073 is on disk → the backdrop pool is still 1,317 unique cutouts (P8).

---

## P0 — Housekeeping (Nurkyz runs these; agent is permission-blocked from rm on cluster)

Frees ~19.5 GB (quota was 69.3/100 GB). All items are superseded/flawed; models & CSVs kept:

```
ssh gpus
bash -lc "rm -rf ~/paltas_shards_pathb"                          # 6.5 GB, generated with the FLAWED v4-era library — must not be trained on
bash -lc "rm -f ~/einstein_cnn/train_hybrid_100k.h5 ~/einstein_cnn/val_hybrid_5k.h5"        # v1 dataset, superseded by v2/v3 (seeds+configs logged, reproducible)
bash -lc "rm -f ~/einstein_cnn/train_hybrid_100k_v2.h5 ~/einstein_cnn/val_hybrid_5k_v2.h5"  # v2 dataset, superseded by v3 (v2 model kept)
bash -lc "quota -s | tail -2"
```

Keep: `train_hybrid_100k_v3.h5` + `val_hybrid_5k_v3.h5` (current best model's data), all
`.pt` checkpoints (incl. the flawed-data `einstein_cnn_pathb_*.pt`, kept as record), old
deflector libraries (small), `pathb_pilot*.h5`. Log the deletion in DECISIONS_LOG.

---

## P1 — Deflector brightness: physical magnitude scaling (THE critical fix)

**Change** (in `hybrid_combine.py`, function `inject_deflector`; keep a `.bak`):
1. Load `lens_light_empirical.csv` (already passed as `--deflector_mag_csv`, currently
   unused for scaling). Precompute each library stamp's effective radius Re_stamp
   (half-light radius from the stamp itself, in arcsec at 0.05″/px).
2. Per image: draw a CSV row **Re-matched** to the chosen stamp — e.g. among the 63 rows,
   sample with probability ∝ exp(−(Re_row − Re_stamp)²/(2·0.4²)) (Gaussian kernel in
   arcsec; keeps the JOINT mag–Re structure; DECISIONS_LOG diagnosis #8 forbids
   independent marginals). Add mag jitter ±0.2 (same spirit as the parametric
   `cross_object` jitter).
3. Scale: `flux_target = 10**(-0.4*(mag_draw - 25.94))` e-/s (TOTAL);
   `st *= flux_target / st.sum()`. NO peak-based scaling anywhere.
4. Store the actual `mag_draw` in `deflector_mag` (fixes the provenance mislabel), keep
   `deflector_index`.
5. Remove the `real_peaksky` draw machinery from the deflector path (peak/sky stays in
   `gate_stage0.py` as a check — see below).

**Why this also strengthens the science:** with brightness set by physical magnitudes, the
gate's peak/sky comparison becomes an EMERGENT check (nothing matches it by construction
anymore) — if it still lands in the real band, that is genuine validation, not tautology.

**Pilot** (copy `pathb_pilot_v3.sbatch` → `pathb_pilot_v4.sbatch`, change combine flags,
output names `*_v4`): expect
- implied-mag distribution ≡ the CSV prior (verify with `inspect_pathb_pilot.py`, adapt it);
- peak/sky median still inside [492, 1798] (EMERGENT — report it prominently);
- no "tiny blob" and no >10σ edge-step outliers;
- side-by-side: deflector brightness visually matches real panels.
⛔ Show Nurkyz the side-by-side before P2's pilot (or bundle the viewing with P2 if P2's
fetch finished — but generate the P1-only pilot regardless, it isolates the change).

---

## P2 — 256 px LRG cutouts: kill the residual abrupt-edge for the brightest wings

The current 128 px cutouts force background estimation from corners that still contain
galaxy wing → over-subtraction → bright wings step down at the frame edge (the "abrupt
contrast with darker background" Nurkyz saw; measured tail to 27σ, real max 9σ). P1
removes the worst cases (no more 14th-mag monsters); P2 removes the mechanism.

1. **Refetch at 256 px / 12.8″** (start this early — it's independent and slow):
   ```
   cd ~/einstein_cnn
   nohup bash -lc "~/miniconda3/envs/Stronglensing/bin/python fetch_real_lens_images.py \
     --survey LRGDEFL --box 12.8 --npix 256 --out real_lrgdefl_images_256.h5" \
     > fetch_lrgdefl_256.log 2>&1 &
   ```
   (login-node nohup is the established pattern for MAST fetches; ~1.5 h for 84 targets.)
   **Purge `mast_cache/` immediately after** (quota! it grew to ~32 GB last time).
2. **Builder v6** (`build_deflector_from_lrg.py`, keep `.bak_v5`): accept 256 px input;
   bg from the 256-frame corners (r≈180 px — negligible wing there); clean/detect exactly
   as v5 but on 256; **output 256 px stamps**. Keep the same rejections + `--drop` list
   (re-inspect the grid — src indices refer to the same 84 targets, but re-verify visually;
   the drop list may shift).
3. **`hybrid_combine.py`**: when the stamp is larger than the frame, apply the ±2 px jitter
   as a shift of the crop window and paste the CENTRE 128×128 crop. The visible frame then
   sits entirely inside real galaxy light — no boundary can exist by construction.
4. **Pilot v5**: edge-step distribution must match real (median ~2.5σ, max ≤ ~9σ);
   side-by-side inspection. ⛔ Nurkyz eyeballs it — this is the checkpoint where the
   original complaint ("abrupt contrast toward the edges") must be visibly gone.

---

## P3 — Deflector diversity: augmentation + val disjointness

1. In `inject_deflector`: random dihedral transform per paste (`np.rot90` k∈{0..3} +
   optional flip — 8 variants). 64 stamps × 8 = 512 effective morphologies; matches the
   flip/rotation invariance already used in training. (θ_E label unaffected — the arcs are
   rendered separately.)
2. Val stamp disjointness (mirrors the PSF-kernel pattern: val kernels 80–87 are
   train-disjoint): reserve 8 stamps for val only. Implementation: builder writes
   `deflector_stamps_lrg_v4_train.h5` (56) and `..._val.h5` (8, chosen to span
   morphology/Re); the generation sbatch passes the val library to sub-shards 80–87.
3. Pilot: augmentation is visually neutral — a quick 200-image pilot + gate re-run
   suffices; can be bundled with P2's pilot IF P2 is ready (log the bundling explicitly);
   otherwise run separately.

---

## P4 — Calibration statistics: benchmark file → disjoint DA pool

Today every generation draws its sky-RMS targets (and until P1, peak/sky) from
`real_slacs_images.h5` = the frozen TEST images. Logged as accepted "calibration usage",
but unnecessary now: `~/einstein_cnn/real_dapool_images.h5` (104 cutouts, triple-verified
benchmark-disjoint, same instrument/band/pixel scale, same messy population) can supply
them.

1. `hybrid_combine.py --real` → point at the DA pool file for the sky-RMS draw.
   First VERIFY the pool's robust-sky distribution vs benchmark SLACS and S4TM (one
   script, three histograms, saved to `da_pool_inspection/`): the pool is S4TM-candidate-
   dominated (78/104), so its sky-RMS should naturally cover S4TM-like exposures —
   **this subsumes the still-pending "S4TM noise union" fix from 2026-07-06** (log that).
2. `gate_stage0.py` keeps comparing against benchmark SLACS — that's a diagnostic
   readout, not a training input. Gate targets unchanged (0.8–1.25 sky-RMS ratio vs
   benchmark). If the pool-driven noise widens the sim distribution slightly, that is
   expected and fine as long as the gate still passes.
3. If J0955+0101 statistics are needed anywhere else, exclude it explicitly.
4. Pilot + gate + side-by-side (one change, as always).
5. Paper note (add to PAPER_DRAFT §2.2 when done): "all noise/brightness calibration
   statistics are drawn from a benchmark-disjoint pool" — closes the last calibration-
   leakage objection.

---

## P5 — Arc-visibility metric + acceptance decision (⛔ Nurkyz)

Build the metric BEFORE deciding whether to act on it (diagnose-before-fix):
1. Regenerate the 200 arc-only renders (seed 111 — 2 min) and KEEP the noiseless npys
   this time. For each pilot image compute arc SNR: max over the arc's own footprint of
   arc_flux / local (deflector+backdrop+noise) fluctuation. Report the fraction of images
   with arc SNR > 3.
2. Compute the same for a matched parametric reference (the v3 recipe) if cheap, and count
   by eye on the real side-by-side panels (the benchmark systems are grade-A lenses —
   their arcs ARE visible in these very cutouts).
3. ⛔ Decision with Nurkyz: if the visible-arc fraction is clearly below real, adjust —
   but carefully: DO NOT simply brighten sources (the old v0 mistake, and the flat-vs-
   peaked source-mag tension is documented). Preferred knobs, in order: (a) confirm P1
   removed the burial cases; (b) revisit `mag_cut` (currently 3.0); (c) only as a last
   resort, source-magnitude prior changes with a full re-gate.

---

## P6 — Full generation (⛔ only after P1–P4 pilots pass and Nurkyz signs off)

1. Edit `generate_pathb.sbatch`: new library names (train/val split from P3), DA-pool
   `--real`, P1 combine flags. Show Nurkyz the diff before submitting (standing rule).
2. `nohup bash submit_pathb.sh > submit_pathb.log 2>&1 &` (3 waves, QOS cap 8 — the
   script already handles this; ~40 min total; sub-shard npys are deleted en route).
3. Merge + gate on the FULL merged 100k (not just a pilot) via `merge_gate_pathb.sbatch`
   (update names) + `side_by_side_real_sim.py` + per-shard previews.
4. Quota check before AND after (target: stay under ~85 GB).

## P7 — Training + benchmark evaluation

1. **Quick-train sanity first** (~20 min GPU): train InceptionNeXt on a 20k subset,
   10 epochs. Compare the val-MAE trajectory against Path-B-v1's (0.194″ final) and
   v3-parametric's. Expectation if P1 fixed the collapse: dramatically better than 0.19.
   If val MAE still plateaus ≥0.15″: **STOP, do not spend a benchmark eval** — the task
   may be genuinely harder with real light; diagnose (e.g. deflector-subtraction probe,
   arc-SNR stratified error) and discuss with Nurkyz.
2. Full training, both architectures for the clean comparison (`train_pathb.sbatch`
   pattern): InceptionNeXt (primary) + ResNet, NLL head, selection on the new sim-val
   ONLY. Note: sim-val MAE is NOT comparable across dataset generations (different task
   difficulty) — qualification is "trains cleanly, converges, no pathological bias", not
   an absolute threshold.
3. ⛔ Benchmark evals **#10 (InceptionNeXt) / #11 (ResNet)**, Nurkyz present, TTA,
   standard protocol, logged with running count. Success bar vs v3 (eval #8/#9):
   SLACS fail < 24%, R² ≥ +0.22, |median| ≤ 5%, confident-half fail ≤ 10%; S4TM
   correspondingly. Pre-written negative-result framing (use it honestly if needed):
   "real deflector light is not the residual failure driver either; remaining failures
   are system-specific complexity" — that would complete the causal decomposition
   (backdrops ≫ prior ≈ PSF > pool ≈ DA ≈ companions ≈ lens light) and is publishable.

## P9 — POST-PATH-B EXECUTION QUEUE (added 2026-07-09, Nurkyz: "execute each point")

Ordered by expected value per effort. Each row follows the house rules: one change at a
time, gates before scale, benchmark evals only at ⛔ checkpoints with running count.

| # | Item | What/how | Status |
|---|------|----------|--------|
| Q1 | **σ recalibration (MASTER_PLAN D3)** | Fit one temperature/scale factor for the NLL σ on SIM-VAL ONLY (never benchmark); report raw AND recalibrated coverage (52%/83% → target ~68%/95%) at the next ⛔ eval; add ρ(σ,│err│) + failure-rate CIs | ☐ script to write; run right after P7 full training |
| Q2 | **Eval-time ensembling (new 2026-07-09)** | Average TTA predictions of InceptionNeXt + ResNet (trained on identical data for the arch comparison anyway); zero training cost; report as an extra eval column at ⛔ #10/#11 | ☐ fold into eval protocol |
| Q3 | **Arc-SNR-stratified error analysis (new 2026-07-09)** | Bin sim-val error by the P5 arc-SNR (machinery exists: `arc_snr_metric.py`, needs val arc npys kept for one 5k regen); if error concentrates in invisible-arc bin → THEN consider curriculum/weighting (evidence-gated, do not pre-apply) | ☐ after P7 training |
| Q4 | **DA retry on Path-B model (MASTER_PLAN D4)** | The DA negative result was measured against PARAMETRIC lens light — DA was fighting the lens-light gap. With real deflector light the residual gap is smaller; one style-MMD training run (`--da_mode style`, existing code path) on the pathb_v2 dataset | ☐ after ⛔ #10/#11 establish the non-DA baseline |
| Q5 | **Backdrop pool 1,317 → ~4k** | `dl_more_tiles.sh` FIXED (071/072 don't exist at IRSA; now 066+074, loud failures); run when quota allows (post-merge); re-harvest empty cutouts; RE-GATE before use in any dataset | ☐ script ready, quota-gated |
| Q6 | **D1 causal ablations** (A3 prior spine first, then A1 PSF, A2 backdrop, A4 ePSF pool) | One dataset variant + one retrain + one logged eval each, batched; delete each ablation dataset after its eval (quota) | ☐ after the main Path-B result lands |
| Q7 | **D2 Cao per-lens comparison** | Data NOT public (verified 2026-07-09). (a) Nurkyz/Brian email Cao for per-lens θ_E; (b) fallback: re-run their public TinyLensGpu on the same 63 lenses ourselves (~3 min/lens GPU), labeled as our reproduction | ☐ (a) HUMAN; (b) ready to build if (a) stalls |
| Q8 | **Etherington gold-subset reporting** | Report the literature-defined SLACS subset alongside the full benchmark at every future ⛔ eval (never shrink the benchmark itself) | ☐ fold into `metrics_real.py` protocol |
| Q9 | **Paper chores** | PAPER_DRAFT §2.3 limitation → Path B method section; P4 calibration-disjointness sentence (§2.2); consolidate stale PAPER_PLAN/MODELS_AND_RESULTS (banners added 2026-07-09) | ☐ writing task |
| Q10 | **Companion realism v2** | Only if post-P2 previews still show speckle-cluster texture (v7 side-by-side: much improved — re-judge on the merged side-by-side) | ☐ conditional |
| Q11 | **HUMAN tasks** | (a) Cao email; (b) Brian authorship conversation (PAPER_PLAN: "do early" — results are close now); (c) Sam PSF ask: recommend DOWNGRADE to optional cross-check (superseded by the STScI focus-diverse ePSF library) — Nurkyz decides | ☐ Nurkyz/Brian |
| Q12 | **D5 multi-domain generalization** (Euclid Q1, BELLS, COWLS) | After D4; separate section/follow-up paper | ☐ far queue |
| Q13 | **Pretrained backbones** (professor, 2026-07-09) | ConvNeXt V2 controlled run + DINOv2 frozen-feature probe on pathb-v2 data — see MASTER_PLAN R2.1 | ☐ after R0 evals |
| Q14 | **TNG-κ mass-realism arm** (professor, reframed) | κ maps via lenstronomy INTERPOL in the current hybrid pipeline; κ̄=1→SIE label calibration — see MASTER_PLAN R2.2 | ☐ after R0 evals |
| Q15 | **Euclidised-SLACS head-to-head vs LEMON** | HST2EUCLID (public) on our 29 shared SLACS; compare to their Table 3 in THEIR domain — see MASTER_PLAN R1.2 | ☐ paper core |

## P8 — Parallel / optional (do not block P1–P7)

- **Backdrop tiles**: fix `dl_more_tiles.sh` (071/072 downloads failed silently — check
  the IRSA URLs; resumable wget), then re-harvest empty cutouts toward a true 4k-unique
  pool and (optionally) more companion stamps from the new tiles. Re-gate before use.
- **Companion realism v2** (only if previews still show speckle-cluster texture after
  P1/P2): larger stamps (~35–49 px), stricter fill-fraction, brightness distribution
  matched to the real companion flux function (measure from the DA pool, not the
  benchmark). Own smoke + visual check (the v2→v3 companion iteration history shows the
  metric alone is not enough — eye > metric).
- **Paper chores**: fix the stale "m3 zero-shot" title in `metrics_real.py`; chase the
  Cao per-lens data email (Nurkyz/Brian); PAPER_DRAFT updates — §2.3 limitation → Path B
  method section; add the P4 calibration-disjointness sentence; Etherington gold-subset
  reporting alongside the full benchmark.
- **Standing ask**: larger/cleaner ACS PSF from Sam (≥51 px) — unchanged.

---

## Operating notes for the executing agent (hard-won, do not rediscover)

- Login shell is csh: every remote command = `ssh nurkyz@gpus "bash -lc '...'"`. No
  heredocs through ssh (quoting breaks); scp script files instead.
- All SLURM partitions need `--gres=gpu:1` even for CPU jobs; QOS caps 8 jobs/submit —
  arrays >8 must go in `sbatch --wait` waves (`submit_pathb.sh` is the template).
- SLURM `--output` directory must exist before submission.
- Python 3.8 (no backslashes in f-strings); paltas 0.2.0 pinned with `--no-deps`;
  don't touch lenstronomy/numpy versions.
- Long jobs: SLURM only (no tmux on the head node); MAST fetches: login-node nohup.
- Quota 100 GB hard: delete intermediate npys per shard (the sbatch does), purge
  mast_cache after fetches, re-check `quota -s` before big runs.
- Every preview: three stretches; every dataset version: `side_by_side_real_sim.py`.
- The permission system blocks the agent from `rm -rf` and `scancel` on things it didn't
  create — put such commands in the report for Nurkyz instead of retrying.
- Log EVERYTHING in DECISIONS_LOG.md as you go (the 2026-07-08 afternoon went unlogged
  and cost a session of reconstruction).
