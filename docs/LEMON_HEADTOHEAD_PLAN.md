# LEMON HEAD-TO-HEAD PLAN — same lenses, both domains

Date: 2026-07-13. Authorized by Nurkyz ("start the Q1 plan, get the euclid images;
our goal is to get the exact set of lenses LEMON tests on"). DECISIONS_LOG.md stays
authoritative. COMMITMENTS.md carries the open-item pointers.

## Goal (one sentence)

Beat LEMON (Euclid Collaboration: Busillo et al. 2026, A&A aa54538-25;
arXiv:2503.15329) **on the exact lenses they evaluate, in both of their domains**:
(A) their 60 Euclidised real HST lenses, (B) their 354 real Euclid Q1 lenses —
adding to the native-HST domain they cannot enter at all.

## The two scoreboards (their published numbers, verified from the PDF 2026-07-13)

| domain | N | GT | bias | RMSE | NMAD | R² |
|---|---|---|---|---|---|---|
| A. Euclidised HST (their Table 3) | 60 | heterogeneous literature (13 = ARC RADIUS, not θ_E!) | −0.03″ | 0.14″ | 0.11″ | 0.53 |
| B. Real Euclid Q1 (their Fig. 12a) | 354 | PyAutoLens SIE, Euclid pipeline, same images | 0.01″ | 0.17″ | 0.07″ | 0.71 |

Our current standing on (A)-superset: ⛔ eval #19, all 62 SLACS, uniform b_SIE GT:
−0.010″ / 0.137″ / 0.056″ / +0.71 / fail 15% — already ahead on every aggregate.
(B) is unplayed by anyone but them. Their own Sect. 7 concedes real-image
performance is worse than sim; mass ellipticities on Q1 do NOT correlate
(R² −0.31/−0.44); magnitudes needed an ad-hoc −0.22 mag ZP shift.

---

## Stage Q0 — housekeeping (DONE 2026-07-13)

- [x] Branches merged to main (modeling consolidation + literature sweep;
      DECISIONS_LOG union).
- [x] This plan written; pointer added to COMMITMENTS.md.
- [x] Busillo email SENT by Nurkyz (29 SLACS names + per-lens predictions ask).
      Reply = the definitive route for Q1a-SLACS; everything below proceeds
      without blocking on it.

## Stage Q1a — reconstruct their 60-lens list

The 31 non-SLACS lenses are pinned by their Sect. 2.2 citations; the 29 SLACS are
not (Bolton 2008 Table 5 has 63 grade-A; their cut is unstated).

1. **EELs (13): ✅ IDENTIFIED (2026-07-13, Oldham Table 2 extracted):** J0837
   (0.56″), J0901 (0.67″), J0913 (0.42″), J1125 (0.86″), J1144 (0.68″), J1218
   (0.68″), J1323 (0.31″), J1347 (0.43″), J1446 (0.41″), J1605 (0.64″), J1606
   (0.52″), J1619 (0.50″), J2228 (0.60″) — range matches LEMON Fig. 9 red
   squares exactly. GT = elliptical power law + external shear (NOT SIE —
   disclose). Full coords from their Table 1 at fetch time. In
   `tables/lemon60_targets.csv`.
2. **COSMOS (5):** Faure et al. 2008 (ApJS 176 19) Table 2 systems, θ_E from the
   Faure erratum. GT = Lenstool SIE + shear.
3. **ACS/Pawase (13):** spectroscopically-confirmed subset of Pawase et al. 2014
   (MNRAS 439 3392) Table 3. **NO true θ_E exists — LEMON used the arc radius**
   (their Fig. 8 caption). We dual-report (pred vs arc radius, flagged) or
   exclude; either way state that 13/60 = 22% of their Table 3 "θ_E GT" is not θ_E.
4. **SLACS (29):** three routes, in parallel:
   - H-email (definitive): Busillo reply.
   - H-flags: Bolton Table 5 subsets — Ring=Yes gives 32; Ring+σ_good gives 31
     (list in `tables/bolton08_table5.csv`, parsed 2026-07-13); **H3 (∩ Auger
     photometry) RULED OUT 2026-07-13**: VizieR J/ApJ/705/1099/lenses shows all
     31 have Imag+Re(I) — the last cut to 29 is something unstated (candidates:
     image quality, or dropping special systems like the J0946+1006 double ring).
   - H-fig9: digitize their Fig. 9 left panel (29 SLACS points, z_lens vs
     log10 θ_E — caption says values are the forward-modeling GT = Bolton) and
     match pairs against the 63 known (z_l, b_SIE). Unambiguous if point
     extraction is good to ~0.02 dex.
   Until resolved: report the 62-superset row (defensible: superset ⊇ their 29).
   Gate: any claimed 29-list must reproduce their Fig. 9 scatter exactly.
5. Deliverable: `tables/lemon60_targets.csv` — name, RA/Dec, subsample, GT θ_E,
   GT convention/source, spectro-z (all systems are spec-confirmed).

## Stage Q1b — imaging + Euclidisation for the 31 non-SLACS

1. HST F814W cutouts: MAST fetch via the g1/g1b driver pattern (EELs + Pawase);
   COSMOS ACS F814W tiles for the Faure 5 (we already hold COSMOS tiles for
   backdrops — check local first).
2. Cutout to the benchmark grid (128 px @ 0.05″), same toolchain as
   `real_slacs_images.h5`. Files are FROZEN TEST DATA from birth:
   `real_lemon31_images.h5` (+ per-subsample keys), `real_` prefix discipline,
   never touched by training, every eval logged with the running count.
3. Euclidise with `euclidise.py` (real Q1 VIS PSF, G3 version). Preview
   `side_by_side` + three-stretch on ALL 31 before any eval (blob discipline).
4. Pilot-first: run the full chain on 3 lenses (1 per subsample), visual check,
   then the rest.

## Stage Q1c — ⛔ Domain-A eval (logged, human checkpoint)

- Current Euclid primary (g4 cnv2_3 + g4_recal) + TTA ×8; if eval #22 (g4ar)
  crowns a new primary first, use that — model choice on sim-val only, as always.
- Output: LEMON-convention table (bias/RMSE/NMAD/R², bootstrap CIs) per
  subsample and combined; SLACS row = 29-exact if list resolved, else
  62-superset; ACS row dual-reported (arc-radius caveat).
- Success bar: beat their Table 3 60-lens aggregate on NMAD and R² with the
  matched-composition sample; we already do on the SLACS superset.

## Stage Q2 — native real Euclid Q1 (the unplayed board)

1. **Q2a — GT availability check: ✅ RESOLVED OPEN (2026-07-13).** Zenodo
   record 15025832 ("Euclid Q1: The Strong Lensing Discovery Engine") publishes
   EVERYTHING: `modeling_lens_mass.csv` = **335 per-lens PyAutoLens SIE θ_E**
   (median_pdf + 1σ/3σ + max-LH) — the GT LEMON scored against;
   `q1_discovery_engine_lens_catalog.csv` = 2,584 candidates w/ RA/Dec +
   grades; **`lens.zip` (3.0 GB) = the VIS cutout images themselves**; plus
   MGE/Sérsic light models + magnitudes and `unsuccess.zip`. No ESA-archive
   harvest needed for the Walmsley sample. GT CSV mirrored to
   `tables/q1_slde_mass_models.csv`. LEMON's N=354 vs the 335 here: the
   remainder is presumably Rojas high-σ_v systems — find the Rojas release or
   reconcile at eval time (their Fig. 12 also plots Rojas points separately).
2. **Q2b — VIS cutouts:** Q1 data are public ("Q1 data are now public", their
   Sect. 8; ESA archive + IRSA mirror). Harvest 10″×10″ VIS cutouts at the 578
   candidate positions (LEMON's cutout convention). Route: IRSA/ESA cutout
   service if usable from the Mac, else bulk MER tiles on the cluster (quota
   check first — now 150 GB). Pilot: 10 cutouts + visual before the full 578.
3. **Q2c — preprocessing parity + flux gate:** real VIS 0.1″/px → the same
   2× upsample to the 128 px @ 0.05″ grid the Euclid arm trains on. NEW GATE
   before any eval: photometric sanity on real VIS cutouts (aperture mags of
   the deflectors vs catalog I_E) to catch a LEMON-style ZP mismatch — they
   needed −0.22 mag; our arm is calibrated to real Q1 PSF + sky (G3), so we
   predict a smaller offset; MEASURE, don't assume. Plus sky-RMS and peak/sky
   distribution comparison vs the training arm (gate_stage0-style).
4. **Q2d — population-shift audit (disclose, don't hide):** Q1 deflectors are
   not all LRGs; θ_E skews small; z_l extends higher than SLACS. Report the
   overlap of (θ_E, z_l, deflector mag) with our training support; flag
   out-of-support candidates in the per-lens table.
5. **Q2e — ⛔ Domain-B eval (logged):** our θ_E vs PyAutoLens θ_E on their 354
   (or our closest reconstruction, disclosed), LEMON conventions + bootstrap.
   Success bar: R² > 0.71 / NMAD < 0.07″. Secondary: σ calibration coverage on
   real Euclid (their Q1 σ is Platt-scaled from sims; ours conformal — C11).
6. Caveat to carry verbatim into the paper: PyAutoLens-as-GT is own-pipeline
   GT (the same weakness we flag in Gawade); frame as "their game, their
   referee, their field — and we still win" ONLY if we do.

## Stage Q3 — paper integration

- New results section: "one physical population model, three real-GT domains"
  (native HST b_SIE / Euclidised HST / real Euclid Q1) — the claim nobody else
  can currently make (LEMON: two domains, no native; Gawade/HOLISMOKES:
  ground-based, own-GT; Cao/LensAgent: conventional, single domain).
- Honesty box: their arc-radius GT (13/60); our Euclidiser as disclosed
  reimplementation; own-pipeline-GT caveats cut both ways; per-subsample GT
  conventions.
- Keep the Cao per-lens ask alive (second scoreboard on native HST).

## Don't-forget checklist (things that have bitten us before)

- [ ] Every new real-lens file: `real_` prefix, frozen at creation, eval count
      logged — NO exceptions for "quick looks".
- [ ] Previews with three stretches BEFORE any numeric eval (paltas_smoke8 lesson).
- [ ] One change at a time; pilot (3–10 objects) before full runs.
- [ ] Quota check before harvests (150 GB now; MAST cache purge pattern from g1).
- [ ] csh login shell → `bash -lc` wrapping; SLURM `--gres=gpu:1` even for CPU;
      QOS cap 8 → waves.
- [ ] Emails: Busillo reply → names + per-lens preds; if silent by ~2026-07-20,
      polite nudge + fall back to H-fig9/H-flags. Bergamini (HST2EUCLID) and
      Cao/Li (per-lens SLACS) still pending.
- [ ] When the 29 names arrive: shared-29 = row-filter on saved per-lens CSVs
      (results/preds_l19_*, l21_*) — do NOT re-run the benchmark for it.
- [ ] Log every eval on the NEW sets in DECISIONS_LOG with the running count,
      same as the frozen benchmark (they are benchmark extensions).
- [ ] G5 (Roman rendering) is untouched by this program; do not let Q2 eat its
      slot — the Roman gap is open but closing (Wedig sims are public).
