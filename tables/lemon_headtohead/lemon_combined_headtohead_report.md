# LEMON combined head-to-head: SLACS-29 + EEL-12 + COSMOS-5 + ACS-12 (N=58)

GT sourced directly from the papers LEMON's own methods cite: Bolton+08 T5, Oldham&Auger17 T2, Faure+08 T4, Pawase+14 T3 (arc radius). 1 ACS lens excluded (confirmed chip-gap cutout).

| domain | N | bias | RMSE | NMAD | R2 | fail>15%% |
|---|---|---|---|---|---|---|
| LEMON (all 4 subsamples) | 58 | +0.181 | 0.535 | 0.303 | +0.26 | 59% |
| OURS native HST | 58 | -0.158 | 0.539 | 0.062 | +0.25 | 28% |
| OURS Euclid-domain | 58 | -0.250 | 0.669 | 0.086 | -0.15 | 29% |

## Per-subsample


### SLACS (N=29)

| config | bias | RMSE | NMAD | R2 | fail>15%% |
|---|---|---|---|---|---|
| LEMON | +0.288 | 0.473 | 0.307 | -4.26 | 55% |
| OURS native | -0.017 | 0.174 | 0.038 | +0.29 | 10% |
| OURS Euclid | -0.044 | 0.136 | 0.045 | +0.57 | 7% |

### EEL (N=12)

| config | bias | RMSE | NMAD | R2 | fail>15%% |
|---|---|---|---|---|---|
| LEMON | +0.081 | 0.126 | 0.110 | +0.21 | 42% |
| OURS native | +0.022 | 0.056 | 0.023 | +0.84 | 8% |
| OURS Euclid | +0.077 | 0.209 | 0.025 | -1.15 | 8% |

### COSMOS (N=5)

| config | bias | RMSE | NMAD | R2 | fail>15%% |
|---|---|---|---|---|---|
| LEMON | +0.359 | 0.886 | 0.483 | +0.12 | 60% |
| OURS native | -0.399 | 0.826 | 0.200 | +0.24 | 40% |
| OURS Euclid | -0.778 | 1.254 | 0.418 | -0.76 | 80% |

### ACS (N=12)

| config | bias | RMSE | NMAD | R2 | fail>15%% |
|---|---|---|---|---|---|
| LEMON | -0.048 | 0.708 | 0.664 | +0.36 | 83% |
| OURS native | -0.577 | 1.022 | 0.400 | -0.34 | 83% |
| OURS Euclid | -0.853 | 1.191 | 0.697 | -0.82 | 83% |
