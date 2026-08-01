# Email drafts — updated 2026-07-13 (Nurkyz ruling: keep only what the paper
# needs → the LEMON email. Bergamini email RETIRED: we now use the official
# Q1 GRID-PSF-VIS product directly, which supersedes the HST2EUCLID code ask
# (and keeps our operator fully independent). TinyLensGPU and Brian emails
# RETIRED per the same ruling. Prior drafts live in git history.)

**VERIFIED ADDRESS (from the paper's footnote):**
- LEMON corresponding author: **valerio.busillo@inaf.it** (V. Busillo, INAF-Capodimonte)

---

## To the LEMON team (Euclid Collaboration: Busillo et al. 2026, A&A)

Subject: Shared SLACS sample and per-lens predictions — LEMON (Q1) comparison from a two-domain θ_E CNN with spectroscopic-lensing ground truth

Dear Dr. Busillo and the LEMON team,

I am a researcher working on CNN-based Einstein-radius estimation for real
galaxy-galaxy lenses. Our training simulations follow the same structural
principle as LEMON — the deflector's light and mass belong to one physical
object — but implemented with real observed ingredients: real HST images of
SDSS-spectroscopic early-type galaxies as deflectors (each galaxy's measured
σ_v sets its θ_E), real COSMOS sources, and the measured Euclid Q1 VIS PSF
(from the released MER GRID-PSF product) in the degradation operator. We
evaluate against the independent, uniform spectroscopic-lensing b_SIE values
of Bolton et al. (2008) for 62 SLACS and 40 S4TM lenses, in two domains from
one population model:

- Euclid-like domain (Q1-PSF-degraded real HST cutouts):
  bias −0.010″, RMSE 0.137″, NMAD 0.056″, R² = 0.71, catastrophic rate 15%;
- native HST domain: bias +0.005″, RMSE 0.152″, NMAD 0.048″, R² = 0.64
  (and RMSE 0.088″ / R² = 0.90 on the lower-mass S4TM sample).

Your Q1 LEMON paper is the closest published work to ours, and we would like
to compare with it as carefully and fairly as possible — in your conventions
and your evaluation domain. Two things would make the comparison exact rather
than distribution-level, and we would of course credit them explicitly:

1. The list of the 29 SLACS systems in your 60-lens Euclidised-HST validation
   set, so we can report a same-lens head-to-head table.
2. If possible, your per-lens θ_E predictions (and uncertainties) for those
   systems — aggregate metrics hide sample-composition effects, and a
   per-lens scatter plot of the two methods would be more informative for
   both papers.

We would gladly share our per-lens predictions on the same systems in return
(they are ready). We believe a careful cross-validation between a fully
synthetic Euclid-native pipeline and a real-ingredient HST-anchored one would
strengthen confidence in both ahead of DR1.

Thank you for the impressive work — the Q1 modeling papers are a real service
to the community.

Best regards,
Nurkyz Ydyrysova
[affiliation]

---

Notes for Nurkyz before sending:
- The per-lens numbers quoted are eval #19 (Euclid domain, G4-trained cnv2_3
  on the real-PSF benchmark) and eval #21 (native) — update if a later eval
  supersedes them before you send.
- Euclid Collaboration papers sometimes route through a collaboration
  contact — if the footnote address bounces, CC the first author's
  institutional address from the A&A page.

---

## FOLLOW-UP (CURRENT — rewritten 2026-08-01 per Nurkyz: lead with concrete,
## per-subsample questions, NOT a "we can't reproduce your table" framing.
## Two focused asks — ACS ground truth, and SLACS same-lens comparison — plus a
## forward-looking Euclid note.)

Attachments (2): `lemon_comparison_package/our_predictions.csv` (our per-lens θ_E
on their exact systems) and `results/lemon_vs_ours_acs_arcradius.csv` (the ACS
arc-radius table). ⚠️ Nurkyz: set the provenance line to how you actually received
their predictions (public release vs. shared). Numbers regenerate via
analysis/build_lemon_package.py and analysis/lemon_acs_arcradius.py.

Subject: LEMON θ_E predictions — two questions (ACS ground truth; SLACS same-lens
comparison) and our per-lens predictions to share

Dear Dr. Busillo and the LEMON team,

Thank you again for the LEMON Q1 work. As we prepare a careful, same-lens
comparison with our own θ_E method for our paper, two specific points came up that
we would rather resolve with you directly than assume. We would of course cite
Busillo et al. (2026) throughout.

**1. ACS subsample — which θ_E ground truth?**
You report predictions for the 13 ACS systems. We tried to pin down a published
Einstein-radius ground truth for these and the only values we could find are the
*arc radii* in Pawase et al. (2014, MNRAS 439, 3392), Table 3
(https://doi.org/10.1093/mnras/stu235 ; arc radius, not θ_E). Your Section 6.1
notes the Einstein radius is not reported for these lenses and that you "compared
with the radius of the arc … as a substitute", which matches what we found. Could
you confirm whether you scored these against the Pawase arc radii, or whether you
have a different θ_E ground truth for them? We ask because the arc radius is
generally larger than θ_E, so it matters for how (and whether) this subsample
enters an aggregate θ_E metric.

**2. SLACS subsample — a sanity check on scoring, and permission for a same-lens
comparison.**
We have per-lens predictions ready for the same 29 SLACS systems and are glad to
share them (attached). When we score *your* SLACS predictions against the
Bolton et al. (2008) b_SIE values, we get a low coefficient of determination
(R² ≈ −4.3 in linear θ_E) driven by a systematic offset — your predictions sit on
average ~0.29″ above b_SIE (e.g. J1153+4612 2.00″ vs 1.05″; J2300+0022 2.29″ vs
1.24″; J0822+2652 2.12″ vs 1.17″). Before we say anything about this in print, we
want to check with you: (a) is the Bolton b_SIE the ground truth you used for
SLACS, or did you score against something else / in log-space / with σ-filtering,
and (b) would you be comfortable with us including a same-lens SLACS comparison —
your predictions vs. ours on the identical 29 lenses, in your Euclidised-HST
domain — in our paper? We would send you the exact table and text for your review
before submission.

**3. Looking ahead — a native-Euclid cross-check.**
We are finalizing a next-generation model trained on Euclid-matched simulations,
and once it is ready we would like to extend this comparison onto native Euclid
data in your home domain — a fully-synthetic Euclid pipeline against our
real-ingredient one. We would welcome your thoughts on the fairest way to set that
up when the time comes.

We see the two approaches as complementary and want the comparison to be accurate
and collegial. Thank you for considering these.

With thanks and best regards,
Nurkyz Ydyrysova (CUHK), on behalf of the authors

Notes for Nurkyz before sending:
- Tone check: this asks "which GT did you use / may we compare", NOT "your numbers
  are wrong". Keep it that way.
- SLACS numbers: R² −4.26 / bias +0.29″ / NMAD 0.307 / 55% catastrophic on the 29
  (analysis output; DECISIONS_LOG 2026-08-01). Ours on the same 29: R² +0.57 /
  NMAD 0.045 / 7% — we can offer these if they ask, but the email only *shares our
  predictions* and asks them to confirm their scoring, it does not lead with a
  "we beat you" table.
- ACS: 13 predicted; 12 usable after we drop ACS 221501.12−135822.9 (detector
  chip-gap over the cutout). The arc-radius proxy table (both methods) is the
  second attachment if useful.
- We do NOT need consent to cite published results; Q2(b) is courtesy + a route to
  their exact GT.
- Retired framing (git history): the earlier "we cannot reproduce your Table 3"
  version. Nurkyz preferred concrete per-subsample questions instead.
