# SLACS-29 verification against FRESH-fetched Bolton 2008 + Auger 2009

Source: VizieR J/ApJ/682/964/table5 (Bolton+08) + CDS raw table3.dat (J/ApJ/705/1099, Auger+09), fetched 2026-07-15 independently of the cached tables/bolton08_table5.csv (which matched exactly, 0 discrepancies).

| config | N | bias | RMSE | NMAD | R2 | fail>15%% |
|---|---|---|---|---|---|---|
| LEMON (their Euclid preds) | 29 | +0.288 | 0.473 | 0.307 | -4.26 | 55% |
| OURS native HST | 29 | -0.017 | 0.174 | 0.038 | +0.29 | 10% |
| OURS Euclid-domain | 29 | -0.044 | 0.136 | 0.045 | +0.57 | 7% |
