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

---

## FOLLOW-UP #2 (2026-08-21) — post-GEN5: we now compete on EUCLID, so lead with the
## per-lens Euclid Q1 ask; SLACS = domain-specialization fairness check (that R² is
## OFF-DOMAIN — never a "we beat LEMON on SLACS" headline).

**To:** valerio.busillo@inaf.it (cc first author's institutional address if it bounces)
**Subject:** Follow-up — per-lens Euclid Q1 predictions for a same-sample θ_E comparison (and a fairness check on the SLACS-domain numbers)

Dear Dr. Busillo and the LEMON team,

Following up on my earlier note about a θ_E CNN benchmarked against real ground
truth — with an update that makes a direct comparison to LEMON newly relevant. We
have now built a Euclid-native training simulator that uses the **real Euclid Q1
deflector light** (each lens's own VIS Sérsic model) rather than degraded HST
galaxies, and evaluated it on the 322 SLDE Q1 lenses against the PyAutoLens SIE
θ_E. Our model reaches **R² ≈ 0.71** there (deep-ensemble; single-seed 0.68–0.73)
— on par with LEMON's Q1 result — so a careful head-to-head on *your* home domain
is now worthwhile for both papers.

Two requests would let us make the comparison exact and fair, credited explicitly:

1. **Your per-lens θ_E predictions (and uncertainties) on the Euclid Q1 sample** —
   ideally the 354 lenses of your Fig. 12a evaluation, with identifiers. Aggregate
   metrics hide sample-composition effects; a per-lens same-sample scatter would be
   far more informative than our current overlapping-subset comparison. We'll gladly
   send ours on the identical lenses in return (ready).

2. **A fairness check on the cross-domain numbers.** In our paper we frame the two
   approaches as instrument-specialized: each is strongest in its own domain. Applied
   off-domain, both degrade — our HST-anchored models underperform on native Euclid,
   and, symmetrically, our reconstruction of LEMON on the HST-based SLACS sample gives
   a low/negative R² (consistent with a ≈+0.29″ θ_E offset there). We want to
   represent your method accurately, so: does that off-domain behavior match your
   expectation, and — if possible — could you share your per-lens predictions on the
   SLACS/Euclidised-HST systems so the comparison rests on your outputs, not our
   reconstruction?

A cross-check between a fully-synthetic Euclid-native pipeline and a real-ingredient
one strengthens confidence in both ahead of DR1. Thank you again for the LEMON work.

With thanks and best regards,
Nurkyz Ydyrysova (CUHK), on behalf of the authors

**Before sending:** (a) provenance line for how we got the SLACS numbers (public
release vs. prior share) → "our reconstruction" vs. "your data"; (b) SLACS paragraph
is deliberately collegial (verify, not accuse) — the −4.26 is OFF-DOMAIN, use it only
as domain-specialization evidence, never as a "we beat LEMON on SLACS" headline;
(c) new since FOLLOW-UP#1: we can now compete on Euclid (GEN5), which is the reason
to re-open the thread.

### SHORT VERSION (minimal ask; attach our per-lens file)
Attachment: `gen5_per_lens_predictions.csv` (322 lenses: lens_id, our θ_E [5-member
deep ensemble], our σ [epistemic+aleatoric], PyAutoLens θ_E ref).
Built by /tmp/mk_predfile.py from the UQ-member preds; copy in _local/reviews/gen5_q1defl/.

**Subject:** Per-lens Euclid Q1 θ_E predictions — a same-sample comparison (ours attached)

Dear Dr. Busillo,

We've trained a CNN that estimates Einstein radii on real Euclid Q1 lenses (R² ≈ 0.71
against the SLDE PyAutoLens values), and we'd like to compare it with LEMON on the
*same* lenses for our paper. Could you share LEMON's **per-lens θ_E predictions** on
your Q1 sample — ideally the ~354 of your Fig. 12a, with lens identifiers?

I've attached our per-lens predictions (and uncertainties) on the 322 SLDE-modelled
lenses so you can compare from your side too. We'll credit LEMON explicitly.

Thank you — the Q1 modelling papers are a great resource for the community.

Best regards,
Nurkyz Ydyrysova (CUHK)

---

## FOLLOW-UP #3 (2026-08-28) — SEND-READY. Merges the two asks Nurkyz wants in ONE
## email: (1) request LEMON's per-lens EUCLID Q1 predictions; (2) reconcile the SLACS
## per-lens offset. Grounded in what their PAPER states (checked LITERATURE.md), which
## RULES OUT the two innocent explanations and makes the ask concrete, not accusatory.

**Paper facts that shape this draft (verified — LITERATURE.md, Busillo et al. 2026):**
- Their model is trained on **SIE+shear** sims → it predicts the **SIE θ_E**, the SAME
  family as Bolton b_SIE. → a "b_SIE vs effective/circularized" convention mismatch is
  UNLIKELY to explain the offset. (Answers our Q1 to ourselves.)
- Their 60-lens validation set (incl. the 29 SLACS) is **Euclidised HST**, matching our
  degradation domain — NOT native HST. (Answers our Q2 to ourselves.)
- Their **Table 3 reports bias −0.03″** on the 60 — NOT a contradiction with the SLACS
  offset, and we do NOT frame it as one. It's a **subsample-cancellation (masking)**
  effect: the three subsets with a real θ_E ground truth ALL show a POSITIVE offset
  (SLACS **+0.29″**, EEL **+0.08″**, COSMOS **+0.36″**); the aggregate is pulled to ≈0
  only by the **ACS subset scored against ARC RADII** (arc radius > θ_E → strong negative
  apparent bias). Arithmetic requires it: our 46 θ_E-GT lenses sum to +11.1″, so the 13
  ACS must sum ≈ −13″ (mean ≈ −1″) to land the 60 at −0.03. → so the two real questions
  are (a) are they AWARE the θ_E-GT subsets carry a consistent positive offset, and (b)
  is it OK for us to REPORT the SLACS/θ_E-subset comparison — NOT "your Table 3 is wrong."
- SLACS example offsets: J1153+4612 2.00 vs 1.05; J2300+0022 2.29 vs 1.24; J0822+2652
  2.12 vs 1.17.
- Their **Sect. 7** already states "on real images the predictions from LEMON are worse
  than on simulated lenses" → the collegial anchor: we echo their disclosure, not accuse.
- The SLACS GT source is NOT pinned in their paper (EELs=Oldham, COSMOS=Faure, ACS=Pawase
  arc radius are pinned; SLACS is not) → legitimately worth asking which GT they used.

Attachment: `gen5_per_lens_predictions.csv` (322 lenses; copy in _local/reviews/gen5_q1defl/).

**Subject:** LEMON per-lens Euclid Q1 predictions for a same-sample comparison — and a
quick reconciliation on the shared SLACS numbers

Dear Dr. Busillo,

Thank you again for sharing LEMON's per-lens SLACS predictions — and for the Q1 work,
which is the closest published method to ours. We've since built a Euclid-native training
simulator (using the real Euclid Q1 deflector light of each lens) and evaluated it on the
322 SLDE-modelled Q1 lenses against the PyAutoLens SIE θ_E, reaching **R² ≈ 0.71**
(deep-ensemble; single-seed 0.68–0.73) — on par with LEMON's Q1 result. That makes a
careful head-to-head on your home domain newly worthwhile, so I have one request and one
small reconciliation.

**1. Per-lens Euclid Q1 predictions.** Could you share LEMON's per-lens θ_E predictions
(and uncertainties) on your Euclid Q1 sample — ideally the ~354 lenses of your Fig. 12a,
with identifiers? Aggregate metrics hide sample-composition effects; a same-sample
per-lens scatter would be far more informative for both papers than our current
overlapping-subset comparison. I've attached our per-lens predictions on the 322 SLDE
lenses so you can compare from your side too, and we'll credit LEMON explicitly.

**2. A per-subsample offset we'd like to check with you before reporting.** As we set up
the same-lens SLACS comparison, we noticed something we'd rather confirm with you than
interpret on our own. Scoring the per-lens predictions you shared against their θ_E ground
truths, the three subsamples that have an actual Einstein-radius reference all sit
slightly *above* it — SLACS ~+0.29″ vs Bolton b_SIE (e.g. J1153+4612 2.00″ vs 1.05″;
J2300+0022 2.29″ vs 1.24″), EEL ~+0.08″, COSMOS ~+0.36″. This is fully consistent with
your Table 3's near-zero aggregate bias: the 60-lens mean is pulled back toward zero by
the ACS subset, which (per your Sect. 6.1) is compared against the arc radius rather than
θ_E, and arc radius runs larger than θ_E. So we read the aggregate as sound — we're just
trying to represent the per-subsample behavior correctly. Two questions: (a) on the SLACS
subsample specifically, is Bolton b_SIE the reference you scored against, and does a
positive θ_E offset of this size on real Euclidised images match your expectation — your
Sect. 7 notes real-image predictions are worse than on simulations, and we want to
attribute this to the sim-to-real gap rather than anything else; and (b) would you be
comfortable with us including a same-lens SLACS comparison (your predictions vs. ours on
the identical 29 systems, in the Euclidised-HST domain) in our paper? We'd of course send
you the exact table and text for your review before anything appears in print.

We see the two approaches — a fully-synthetic Euclid-native pipeline and our
real-ingredient one — as complementary, and want the comparison to be accurate and
collegial ahead of DR1. Thank you for considering these.

With thanks and best regards,
Nurkyz Ydyrysova (CUHK), on behalf of the authors

**Before sending:**
- Provenance line is set to "you shared" (they did send the per-lens SLACS file) — keep it.
- Tone: Q2 asks "which GT / does this match your expectation", explicitly anchored on
  THEIR Sect. 7 disclosure. It never says "your R²/numbers are wrong." Keep it that way.
- If the footnote address bounces, cc the first author's institutional address (A&A page).
- Do NOT attach our R²-computation code or the −4.26 number in this email; offer them only
  if they ask to reconcile further (leading with them reads as building a case).
