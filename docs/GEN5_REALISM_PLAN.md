# GEN5 Realism Plan — match simulated Euclid lenses to real Q1, property by property

**Purpose (Nurkyz 2026-08-03):** make the GEN5 generator produce images that match
real Euclid Q1 in every measurable property, by MEASURING each real distribution,
SETTING the corresponding physics/config parameter, and VALIDATING against real +
the AR0 gate + eyeball. This is the checklist so no property is forgotten.

**The loop (do NOT deviate):** for each property below —
1. MEASURE it on real Q1 (PyAutoLens modeling CSVs, or source_light.fits, or the
   real eval cutouts). 2. MEASURE the same on our sim. 3. If they differ, identify
   the PHYSICS/config parameter that controls it. 4. Adjust that parameter (not a
   magic number — the physical prior). 5. Re-validate. Never tune brightness to
   paper over a physics error; never add an arbitrary cut.

**Real Q1 sources of truth:** `q1_slde/modeling_lens_mass.csv` (θ_E, ellipticity,
shear, centre), `modeling_mge_magnitude.csv` (deflector/arc/source VIS+NIR mags,
magnification, arc S/N), `modeling_lens_sersic.csv` (deflector Re, n, q),
`lens/lens/<id>/result/source_light.fits` (image-plane lensed-source model =
noise/deflector-free arc → morphology). Analysis scripts in `analysis/`:
real_q1_measure, real_arc_morph, sim_arc_morph, measure_phot, arc_vis_diag,
meas_p2_p3, defl_tail, coupling.

**Key calibration fact:** euclidise PRESERVES AB mag → sim VIS mag == native
ZP-25.94 mag (no offset). Real θ_E 0.70/0.88/1.13; deflector VIS 20.35/21.39/22.13;
arc VIS 21.81/22.28/22.75; contrast +0.35/+1.00/+1.65; magnification 2.03/2.63/3.21;
arc S/N 7.6/10.5/15.4; deflector Re 0.47/0.68/0.94, n 4.4, q 0.80; completeness
0.26/0.43/0.68 (61% partial, 17% full-ring); sky RMS median 0.0059 (95th 0.0095).

## ⚠️ META-PRINCIPLE (Nurkyz 2026-08-03): fixes are CUMULATIVE, applied ALL AT ONCE
Every fix below stays in the recipe permanently. A new pilot changes ONE open knob
and KEEPS every closed one. Two things made it *feel* like we were reverting:
(a) coupled knobs — tuning the source offset moved completeness, so it looked like
a regression when it was convergence; (b) ONE real replacement — the early
"more big/bright deflectors" hack (deflector_flux_scale ×2.5, C39) was replaced by
physical Faber-Jackson (C40, mag0 21.39). FJ matches the REAL deflector brightness
(not over-bright), which is why deflectors stopped looking artificially big — and
that revealed the genuine remaining gap, the visible ENVELOPE (#4b). We do NOT
revert to the over-bright hack; we keep FJ AND fix the envelope. **THE RECIPE BELOW
IS THE SINGLE SOURCE OF TRUTH — every pilot runs all of it.**

## THE COMPLETE GEN5-COSMOS RECIPE (current = fj13; every pilot carries ALL of this)
**Manifest** (g5_make_manifest + add_src_offset): `--match_theta` (θ_E→real Q1);
e1,e2 from real q+scatter; z_source ~N(2.0,0.6); multipoles m3,m4 (isophote-
anchored); z-migration mig_scale/mig_sb + evo_q 1.2; **source offset ABSOLUTE
r_max 0.4** (add_src_offset absolute 0.4) [C49].
**Render** (config_lensfusion_acs_g5cosmos): LF_SB_CUT 21.5; LF_MIN_FLUX_RADIUS 1.0;
LF_MIN_SIZE_PX 8; LF_SRC_ABSMAG −24.5 (→ arc VIS ~22.5); **LF_SRC_MAX_RE_ARCSEC 0.3**
[C51]; **LF_MAG_CUT 2.0** [C45]; PSF kernel_00_extended.
**Composite** (hybrid_combine): `--deflector_fj --fj_mag0 19.2 [C54: was 21.39; peak/sky match but Nurkyz STILL sees dots -> UNSETTLED, see GEN5_HANDOFF.md] --fj_slope 4.5
--fj_theta0 0.88 --fj_scatter 1.15` [C40]; `--fj_mag_min 19.2 --fj_mag_max 23.4`
(truncated-normal tail) [C50]; `--deflector_edgesmooth 1.5` [C43]; `--deflector_jitter
1.0`; companions `--companion_rate_lo 0 --companion_rate_hi 3 --companion_flux_pct 35
--companion_rmin 30 --companion_area_uniform`; `--arc_poisson`.
**Euclidise**: LF_EUC_SKY_SCALE 2.2; LF_EUC_NOISE_CORR 0.45.
**Selection** (arc_visibility_select): `--thresh 6 --min_extent 100 --min_sky_snr 7.6`
[C48].

## Nurkyz's 4 requirements → which fixes serve each (all live together)
**1. Right deflector distribution (big/diffuse/bright enough).** FJ brightness+slope
[C40] ✅ (selected mag 21.25 ≈ real 21.39; θ_E>1.1 frac 0.34 ≥ real 0.25 — NOT
selection-biased); faint-tail truncated [C50] ✅; half-light Re + 28% diffuse ✅.
**OPEN: visible ENVELOPE too small (#4b)** — wings fade at ~1.3″ vs real ~2-3″
(stamp wing-suppression + mig_scale + edge-smooth). Distribution is right;
envelope is the one gap.
**2. Noise background at real Euclid level.** LF_EUC_SKY_SCALE 2.2 + NOISE_CORR 0.45
✅ (sky RMS 0.0057 ≈ real 0.0059, no fat tail). Nurkyz: "seems fine" — confirmed.
**3. Physically-consistent arc↔deflector matching (Faber-Jackson + magnification).**
FJ ties deflector brightness to θ_E [C40]; **absolute source offset** ties ARC
brightness to θ_E via magnification [C49] → rho(arc,θ)−0.15≈real−0.11, small-θ
arc-brighter-than-deflector 51%→25-40% (real 30%) ✅; mag_cut 2.0 [C45] ✅.
**4. Arc morphology (partial/poles/thickness, source placed off-axis).** Absolute
offset (β at an ANGLE, not behind the deflector) [C49] → completeness 0.42, 15%
ring, arcs at poles/partial ✅; sky-SNR floor drops blobs [C48] ✅. **OPEN: arcs
still ~2× too THICK + clumpy (#12/#14)** — COSMOS sources too large/clumpy → switch
to Q1SourceCatalog (real delensed sources). Source max-Re cut [C51] partly helps.

## Full fix inventory (C-rows, what each did, all still in recipe)
- **C40/C44 Faber-Jackson deflector brightness** — deflector total flux from θ_E
  (mag0 21.39, slope 4.5, scatter 1.15); replaced the C39 ×2.5 over-bright hack;
  matches real mag + rho −0.47. LIVE.
- **C50 (was C47) FJ faint-tail truncated-normal** [19.2,23.4] — no invisible-
  deflector tail; matches real at all percentiles. LIVE.
- **C43 deflector edge-smooth 1.5** — peak-preserving; removes the square postage-
  stamp cut (NOT the v2 taper mistake). LIVE.
- **C45 mag_cut 2.0** — magnification distribution → real median 2.6. LIVE.
- **C49 absolute source offset r_max 0.4** — physical β (random background galaxy);
  restores magnification–θ_E coupling (#3) AND partial/off-axis arcs (#4). LIVE.
- **C46 completeness match** — emergent from C49+C45; 0.42 vs real 0.43. LIVE.
- **C48 selection sky-SNR floor 7.6** — real-comparable arc S/N; drops diffuse
  blobs. LIVE.
- **C51 source max-Re 0.3″** — thins arcs (partial fix for #12). LIVE.
- Companions (count/placement), backdrop noise correlation 0.45, multipoles,
  θ_E-match — all LIVE and matched from earlier work.

## OPEN items (the only things a new pilot should change)
- **#4b deflector visible ENVELOPE** — wings too faint/small vs real de Vauc.
  Candidates: reduce mig_scale wing-shrink; reduce edge-smooth; use stamps with
  intact wings or add a de Vauc envelope. NEEDS a clean matched-noise measurement
  first.
- **#12/#14 arc thickness + source clumpiness** — switch source library
  COSMOS→Q1SourceCatalog (q1_sources_smooth.h5, built C37). IN PROGRESS.

## Property checklist

| # | Property | Real Q1 target | Controlling parameter | Status |
|---|---|---|---|---|
| 1 | θ_E distribution | 0.70/0.88/1.13 | g5_make_manifest --match_theta | ✅ MATCHED |
| 2 | Deflector VIS mag (level + FJ slope) | 20.35/21.39/22.13, rho −0.47 | hybrid_combine --deflector_fj (mag0 21.39, slope 4.5, scatter 1.15) | ✅ MATCHED (C40/C44) |
| 3 | Deflector mag FAINT TAIL | max 23.4, q90 22.6, frac>23 = 3% | --fj_mag_min/max + TRUNCATED-NORMAL redraw | ✅ MATCHED (C50: q90 22.74, q99 23.25, frac>23 0.05 — all percentiles match, no pile-up) |
| 4 | Deflector half-light Re / diffuse frac | 0.47/0.68/0.94, 25% diffuse | z-migration mig_scale | ✅ MATCHED (0.72, 28%) |
| 4b | **Deflector VISIBLE / peak-over-noise** | isophotal radius (SB>sky+2σ) ~2-3″ | mig_scale shrink + FJ/edge-smooth envelope SB | ❌ RE-OPENED (Nurkyz 2026-08-03: "deflectors too small, real Euclid larger"). Half-light Re + R90/R50 concentration MATCH real, but deflector-only isophotal radius sim 1.2″ vs real ~3.4″ — the extended envelope falls below the noise. NOT intrinsic size; the deflector PEAK/sky is 8x too low (real 248, ours 33; noise MATCHES so it is the deflector being too faint, not noise). Envelope alone insufficient. FIX candidates: less mig_scale shrink of the wings, or the FJ/edge-smooth is suppressing outer-wing SB. Investigate. NOTE: partly a comparative artifact — thick bright arcs (#12) make deflectors look smaller; fixing #12/#14 helps the PERCEPTION but not the real envelope gap. |
| 5 | Arc (lensed-source) VIS mag | 21.81/22.28/22.75 | source apparent mag prior | ✅ MATCHED (22.5) (C44) |
| 6 | Arc−deflector contrast (median) | +0.35/+1.00/+1.65 | emergent from 2+5 | ✅ MATCHED (~1.0) |
| 7 | **Arc−deflector contrast vs θ_E (magnification COUPLING)** | rho(arc,θ_E) −0.11; small-θ contrast +0.48 (30% arc<defl) | source offset ABSOLUTE (add_src_offset absolute r_max 0.4) | ✅ MATCHED (C49, fj11/fj13: rho −0.15/−0.16, small-θ arc<defl 0.25-0.40; was +0.05/0.51) |
| 8 | Arc completeness (partial vs ring) | 0.26/0.43/0.68; 17% ring | absolute β r_max + mag_cut | ✅ MATCHED under absolute β (fj13: 0.42, full-ring 0.15) (C46/C49) |
| 9 | Magnification distribution | 2.03/2.63/3.21 | LF_MAG_CUT | ✅ 2.0 (C45) |
| 10 | Sky noise (RMS) | median 0.0059, 95th 0.0095 | euclidise LF_EUC_SKY_SCALE + real backdrop | ✅ MATCHED (ours narrower, no tail) — refuted "too wide" (C47 note) |
| 11 | Arc S/N (selection = real discovery) | 7.6/10.5/15.4 | arc_visibility_select --min_sky_snr | ✅ FLOOR 7.6 (C48) |
| 12 | Arc width / thickness [arcsec] | radial FWHM 0.47" (0.38" at small θ) | source angular size + compactness | ❌ OPEN — sim 1.2" (2.5x too thick). --deflector source max-Re cut (C51) helps (0.3"->1.1", 0.15"->0.9") but half-light cap saturates: it is COSMOS full-extent+clumpiness. FIX = compact sources (Q1SourceCatalog real delensed sources, already built) |
| 13 | Source POSITION prior | absolute β (random background galaxy) | manifest source_cx/cy | ✅ ABSOLUTE (C49, r_max 0.4) — mechanism for #7 |
| 14 | Source compactness / clumpiness | real high-z = compact star-forming knots | source LIBRARY (COSMOS max-Re cut, or switch to Q1SourceCatalog) | ❌ OPEN — the ROOT of #12 thick arcs + residual diffuse blobs. RECOMMEND: switch source library COSMOS→Q1SourceCatalog (real delensed Q1 sources, q1_sources_smooth.h5, already built C37) |
| 15 | Companions (count, placement) | sparse, ~1/img | hybrid_combine --companion_* | ✅ MATCHED |
| 16 | Backdrop noise correlation | drizzle-correlated | euclidise LF_EUC_NOISE_CORR 0.45 | ✅ MATCHED |
| 17 | Multipoles m=3,4 (AR3) | isophote-anchored | manifest mult3/4 | ✅ in manifest |
| 18 | Passive evolution evo_q | Faber+2007 ~1.2 | g5_make_manifest --evo_q | ⏳ PENDING physics confirm (C31) |
| 19 | q_mass–q_light relation | Etherington+2022 | g5_make_manifest | ⏳ OPEN pre-gen blocker (C2) |

## Generation gates (before ANY full GEN5 generation)
- [ ] #4b deflector VISIBLE envelope size (isophotal ~2-3") — re-opened 2026-08-03
- [ ] #7 arc–deflector magnification coupling matched (absolute β)
- [ ] #12/#14 arc thickness + source compactness (no thick-on-small-θ arcs)
- [ ] #3 deflector faint tail clean (no pile-up)
- [ ] C2 q_mass–q_light fit (#19)
- [ ] C31 evo_q physics confirm (#18)
- [ ] AR0 gate 4/4 + Nurkyz >1k-image eyeball sign-off

## Are we following the plan?
YES on the loop (measure→match→validate) — every fix above was data-driven, and we
refuted 2 wrong hypotheses (noise, deflector size) with measurement rather than
tuning. GAP: we were doing it REACTIVELY (per eyeball) instead of walking this full
list up front — which is why #7 (the θ_E-coupling) surfaced late. This doc is the
fix: work the list top-to-bottom, re-validate the whole table before generation.
