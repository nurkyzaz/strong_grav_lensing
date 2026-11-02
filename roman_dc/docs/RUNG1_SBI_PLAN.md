# Rung 1 — SBI / Regeneration Plan (mejiro + gold-mining)

The evidence-based improvement plan ([`RUNG1_IMPROVEMENT_PLAN.md`](RUNG1_IMPROVEMENT_PLAN.md))
showed every cheap-to-medium method plateaus at ~0.57 because the *label is
binary and noisy* and the *signal is below noise for most systems*. This plan
attacks the label problem at its root: **regenerate matched training data with
the challenge's own simulator (`mejiro`) so we record the *rich, continuous*
truth the challenge withholds, and train a simulation-based-inference (SBI)
classifier on it.**

## Why this can beat 0.57 (and the honest caveat)
The optimal statistic for "subhalos present vs absent" is the **likelihood ratio**
`r(x) = p(x|present)/p(x|absent)`. A plain CNN approximates it from binary labels
only. **Gold-mining SBI** (Brehmer, Mishra-Sharma, Hermans, Louppe, Cranmer 2019,
[arXiv:1909.02005](https://arxiv.org/abs/1909.02005)) trains the *same* ratio using
**augmented data the simulator can emit** — the *joint* likelihood ratio and the
*score* `t(x,z) = ∇_θ log p(x,z|θ)` for each simulated image, where `z` is the
(known-at-generation) subhalo realization. Those targets carry far more gradient
than a 0/1 label, giving a provably better estimator for the same data budget.
Related: TMNRE/swyft (Anau Montel, Coogan, Weniger 2022,
[arXiv:2205.09126](https://arxiv.org/pdf/2205.09126)).

**Caveat, stated up front:** these papers infer *population/continuous* parameters
(substructure abundance, WDM mass, density slope) — **not per-image binary**. We
adapt the *machinery* to the binary hypothesis. And the **physics floor still
applies** — most subhalos are sub-detectable — so gains are bounded. This is a
multi-week research build, not a quick win.

## The rich labels we get FOR FREE by regenerating
When *we* generate, `pyHalo` hands us, per system, exactly what the challenge
omits — any of which is a far better training target than a 0/1 flag:
- the full subhalo catalog (masses, positions) → **mass of / distance to the most
  massive subhalo near the arc**;
- the **substructure convergence κ_sub sampled along the arc** (its perturbing
  power where it matters);
- the **joint log-likelihood + score** w.r.t. `sigma_sub` (the gold-mining targets).

## Two tiers of ambition (shared simulator gate)
- **Tier A — matched regeneration + continuous auxiliary labels (simpler).**
  Generate mejiro data recording the continuous quantities above; train a
  multi-task net (predict presence **and** κ_sub / nearest-subhalo-mass). The
  auxiliary regression heads inject the rich gradient; classify by thresholding.
  No score extraction needed. *Do this first.*
- **Tier B — full gold-mining neural ratio estimation (Brehmer).** Emit the
  joint-likelihood/score augmented data and train the ratio estimator with the
  ROLR/RASCAL/CASCAL loss family (their code is the reference). Strongest, hardest.

## Milestones (each a go/no-go gate)
0. **Feasibility / install.** Isolated conda env; install `mejiro`, `pyHalo`,
   `slsim`, `romanisim`, `lenstronomy`, `galsim`, `stpsf`. Confirm they import and
   a single lens generates. **Gate: does the stack run at all in our environment?**
1. **Matched generation + validation (CRITICAL).** Generate a few hundred lenses
   with the *exact* challenge config (the YAML we have: CDM, `log_mlow 6`,
   `log_mhigh 12`, `sigma_sub 0.055`, COSMOS-Web sources, STPSF PSF, romanisim
   noise, F106/F129/F158, 0.11″/px). Compare pixel/flux/arc statistics to the
   real challenge images (reuse `rung1_gallery.py` mean/diff + histograms).
   **Gate: is our distribution statistically indistinguishable from theirs?** If
   not, the whole approach fails — fix the config or stop.
2. **Rich-label extraction.** Record κ_sub-on-arc / nearest-subhalo-mass (Tier A)
   and/or joint-likelihood+score (Tier B) alongside each generated image.
3. **Train.** Tier A multi-task net (or Tier B ratio estimator) on ~100k generated
   lenses; select on a matched val split.
4. **Domain-gap check + evaluate.** Score the *challenge* labeled val set (real
   `substructure` flags) — the true test of transfer. **Gate: beat 0.5704.**
5. **Predict + submit** on the challenge unlabeled set.

## Risks (and mitigations)
- **Sim-to-sim gap** (biggest). Mitigate by matching the published config/catalog/
  PSF/noise *exactly* and validating at Milestone 1 before investing in training.
- **Install / dependency hell** for the mejiro stack → isolated env, pinned
  versions; fall back to `paltas` (we have it) with a larger gap if mejiro won't build.
- **Score extraction is advanced** → Tier A (continuous aux labels) needs no score;
  only Tier B does. Start with A.
- **Compute:** generating ~100k Roman lenses + PSF + romanisim is heavy (their run
  used 8064 runs across 60 cores). Budget cluster time; start with 10–20k.
- **Physics floor** caps the ceiling regardless — set expectations, and this is
  professor-scope.

## Immediate next action (Milestone 0, starting now)
Set up an isolated conda env and attempt the `mejiro`/`pyHalo`/`romanisim` install,
then generate one lens end-to-end. Everything downstream is gated on that working.
