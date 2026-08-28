## **5\. Results**

### **5.1. Headline benchmark performance**

\[TABLE 2: Two-domain performance of GEN4 self-consistent population\]

| Domain | Sample | Bias | RMSE | NMAD | R² | Fail\>15% |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| Native HST | SLACS 62 | \+0.005″ | 0.152″ | 0.048″ | \+0.64 | 15% |
| Native HST | S4TM 40 (r50\_3) | \+0.013″ | 0.088″ | 0.047″ | \+0.90 | 8% |
| Euclid like(real-PSF) | SLACS 62 | \-0.010″ | 0.137″ | 0.056″ | \+0.71 | 15% |
| Euclid like | S4TM 40 (G3 r50\_3) | \+0.027″ | 0.117″ | 0.082″ | \+0.81 | 22% |

vs Cao et al. 2025 (conventional modeling, same lenses/GT: ≲5% dev., \~10% fail)—we match the accuracy class at \~10⁶× the speed. vs LEMON Q1 (synthetic-trained CNN, own-model GT: RMSE 0.14 / NMAD 0.11 / R² 0.53)—we lead on NMAD/R²/bias with independent GT.

### **5.2. Causal ablations**

\[TABLE 3: Each variant removes exactly ONE ingredient\]

| Variant | SLACS R² / fail | S4TM R² / fail | SLACS median | S4TM median |
| :---- | :---- | :---- | :---- | :---- |
| v2 (full recipe) | \+0.27 / 23% | \+0.47 / 38% | \-2.6% | \-1.8% |
| Skewed θ\_E prior | \-0.52 / 29% | \-0.03 / 50% | \-6.3% | \-7.8% |
| Gaussian PSF | \-0.46 / 31% | \+0.06 / 50% | \-5.4% | \-9.8% |
| Gaussian noise | \-5.10 / 58% | \-14.67 / 90% | \+24.1% | \+99.5% |
| Broad ePSF pool | \+0.22 / 21% | \+0.42 / 38% | \-1.6% | \-2.2% |

Finding: Real empty-sky backdrops are the dominant ingredient by an order of magnitude (A2: trained on Gaussian noise, the model over-predicts catastrophically). Flat θ\_E prior and real empirical ePSF are each individually necessary. The benchmark-matched ePSF pool adds nothing over a fully disjoint archival pool (A4)—clearing the circularity concern.

### **5.3. Uncertainty and confidence gating**

The NLL uncertainty head provides a domain-aware confidence score. Spearman(σ/μ, |frac error|) \= \+0.71 (SLACS). σ/μ is itself domain-aware: median ≈ 9–10% on real lenses vs. ≈1% on sim-val.

\[TABLE 4: Confidence-gated performance\]

| Sample | Subset | N | Median frac err | Fail\>15% |
| :---- | :---- | :---- | :---- | :---- |
| SLACS | Full | 62 | \-2.6% | 23% |
| SLACS | σ/μ ≤ median | 31 | \-1.6% | 6% |
| SLACS | σ/μ ≤ q75 | 46 | \-1.5% | 7% |
| S4TM | Full | 40 | \-1.8% | 38% |
| S4TM | σ/μ ≤ median | 20 | \-0.9% | 15% |

The confident-half SLACS subset meets the full success bar (±5% median, ≲10% failure) and is competitive with Cao et al.'s \~10% failure rate at \~10⁵× the inference speed.

### **5.4. Comparison to Cao (conventional modeling)**

Using the per-lens predictions kindly provided by Cao et al. (2025), we compare our CNN to TinyLensGPU on the identical 63 SLACS lenses, both evaluated against the Bolton b\_SIE ground truth. \[Table to be added.\] Our CNN matches the accuracy class of conventional modeling at \~10⁶× the speed.

We got their per lens predictions. 

### **5.5. Comparison to LEMON (CNN benchmark)**

We evaluate both methods on the identical lenses LEMON reports predictions for, in their Euclidised-HST domain. Their released predictions cover 59 systems (29 SLACS \+ 12 EELs \+ 5 COSMOS \+ 13 ACS; the paper lists 60, but EEL J0913 is absent). We split the comparison by whether a published θ\_E ground truth exists:

θ\_E subsample (46 lenses with a real published θ\_E)—we lead decisively:

* SLACS-29 (Bolton b\_SIE): ours R² \+0.57, NMAD 0.045″, catastrophic 7% vs. LEMON R² \-4.26, NMAD 0.307″, 55% (LEMON over-predicts by \~+0.29″ mean bias).  
* EELs-12 (Oldham 2017 PL+shear): ours (native arm) R² \+0.83, NMAD 0.023″, 8% vs. \+0.21, 0.110″, 42%.  
* COSMOS-5 (Faure Lenstool): a small-N wash where both struggle—LEMON over-predicts, we under-predict because 2/5 lie above our training θ\_E ceiling (2.3″, out-of-support; disclosed).

ACS subsample (13 lenses) has NO published θ\_E—only an arc radius (Pawase et al. 2014). We exclude it from the θ\_E aggregate (unlike LEMON's Table 3, which folds 13/60 \= 22% arc-radius into one "θ\_E" number). For transparency, we score both methods against the arc radius: our scatter is tighter (NMAD 0.310″ vs. 0.358″), but we carry the expected θ\_E \< arc-radius negative bias.

Caveat: We cannot recover LEMON's published Table 3 (RMSE 0.14″, NMAD 0.11″, R² 0.53) by scoring their released predictions against the literature θ\_E. An inquiry to the authors is in progress.

### **5.6. Transfer to Euclid Q1 and Roman**

Euclid Q1 (native, N=322, vs PyAutoLens GT): Our zero-shot transfer achieves in-support R²+0.61 / fail 32% / bias \-8%—below LEMON's own Q1 (R²=0.71). This is an honest limitation and frontier for future work.

Roman: Zero-shot transfer from HST/Euclid-trained models fails (R²=0.11). Retraining on Roman-domain simulations (G5a, 6-network ensemble) achieves R²=0.93–0.94 / fail 6–9% on the challenge validation set.

Do we have to mention that we participate in the Roman challenge? 

