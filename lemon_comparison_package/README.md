# LEMON head-to-head comparison package

Everything needed to compare LEMON's θ_E predictions with ours on the **exact
lenses LEMON reports**, for the paper and the email to the LEMON team.
All tables share one lens list (LEMON's four prediction files):
**29 SLACS + 12 EEL + 5 COSMOS + 13 ACS = 59 lenses.**

## Files
| file | what it is | rows |
|---|---|---|
| `ground_truth.csv` | literature θ_E ground truth + its source + verification status | 59 |
| `lemon_predictions.csv` | LEMON's predicted θ_E (+ uncertainty) | 59 |
| `our_predictions.csv` | our predicted θ_E (Euclid-domain, G4 cnv2 seed-ensemble) | 59 |
| `combined_comparison.csv` | the join for the 46 lenses that HAVE a θ_E GT (SLACS+EEL+COSMOS): GT, both predictions, and each method's % error | 46 |
| `raw_sources/` | the original source CSVs (LEMON's 4 files, Bolton table, lemon60 targets) for provenance | 6 |

`combined_comparison.csv` is the one to send / put in the paper.

## Ground-truth verification (checked 2026-08-01)
| subsample | GT source | status |
|---|---|---|
| **SLACS (29)** | Bolton et al. 2008 b_SIE | ✅ **verified** — all 29 match `bolton08_table5.csv` exactly |
| **COSMOS (5)** | Faure et al. 2008 Table 4 (Lenstool Einstein radius) | ✅ **verified** — all 5 match VizieR `J/ApJS/176/19/table4` exactly (incl. 0012+2015 = 0.67) |
| **EEL (12)** | Oldham et al. 2017 Table 2 (arXiv:1611.00008) | ✅ **verified** — all 12 checked vs the paper's Table 2; **J1446 was corrected 0.41″ → 0.43″** to match the paper |
| **ACS (13)** | Pawase et al. 2014 | ❌ **NO θ_E ground truth** — arc radius only; excluded from the θ_E aggregate, reported separately as an arc-radius proxy (see below) |

### ACS: arc-radius proxy comparison (NOT θ_E accuracy)
Because ACS has only an arc radius (Pawase 2014 T3), not θ_E, it is kept out of
the θ_E aggregate. For transparency we still score **both** methods against the
arc radius on the **12 usable** lenses (chip-gap `221501.12` excluded), mirroring
LEMON's own §6.1 substitution. Table: `../results/lemon_vs_ours_acs_arcradius.csv`;
regenerate with `python analysis/lemon_acs_arcradius.py`.

| ACS vs arc radius (N=12) | bias | NMAD | R² | med\|frac\| |
|---|---|---|---|---|
| **LEMON** | −0.05 | 0.358 | +0.36 | 0.24 |
| **Ours (native)** | −0.57 | **0.310** | −0.34 | 0.29 |

Read: our **scatter is tighter** (NMAD 0.31 < 0.36); the R² gap is entirely a
systematic negative bias — the expected θ_E < arc-radius offset, since we predict
θ_E and arc radius is systematically larger. LEMON's arc-radius fit co-occurs with
the +θ_E over-prediction that gives it R²=−4.26 on SLACS. So arc radius is the
wrong scoreboard for θ_E accuracy, which is why ACS stays out of the aggregate.

## Headline numbers (from `combined_comparison.csv`, predictions vs the GT column)
| | RMSE | NMAD | R² |
|---|---|---|---|
| LEMON's **published Table 3** | 0.14″ | 0.11″ | 0.53 |
| **LEMON** preds vs literature GT (this package) | 0.48″ | 0.23″ | ≈ 0.00 |
| **Ours** vs the same GT | 0.44″ | **0.06″** | +0.14 |

Two facts the verification establishes:
1. We **cannot reproduce LEMON's Table 3** from their own predictions + literature GT — the email asks them to confirm the GT values / metric convention (log vs linear R²; whether ACS and σ-filtering are in the aggregate).
2. The large SLACS over-prediction (~+14% mean) and the COSMOS `0012+2015` miss (+273%) are **real** — the ground truth is verified correct, so these are not our errors.
   - Our own inflated RMSE (0.44″) is caused by a few COSMOS lenses with θ_E > 2.3″ (above our training range → we under-predict); our typical-lens accuracy is the NMAD 0.06″.

Regenerate with: `python analysis/lemon_perlens_comparison.py` and the package build step (see DECISIONS_LOG 2026-08-01).
