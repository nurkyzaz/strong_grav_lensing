# Structure  {#structure}

[**Structure	1**](#structure)

[1\. Introduction	1](#1.-introduction)

[1.1. Strong gravitational lensing as a cosmological probe	2](#1.1.-strong-gravitational-lensing-as-a-cosmological-probe)

[1.2. The need for automated lens modeling	2](#1.2.-the-need-for-automated-lens-modeling)

[1.3. The sim-to-real gap	2](#1.3.-the-sim-to-real-gap)

[1.4. This work: closing the gap through physical self-consistency	2](#1.4.-this-work:-closing-the-gap-through-physical-self-consistency)

[2\. Literature Review	2](#heading=h.6qljlat8x6p3)

[2.1. CNN-based strong lens parameter estimation	2](#2.1.-cnn-based-strong-lens-parameter-estimation)

[2.2. Domain adaptation for strong lensing	3](#2.2.-domain-adaptation-for-strong-lensing)

[2.3. Positioning our work	3](#2.3.-positioning-our-work)

[2.4. Roman status	3](#2.4.-roman-status)

[3\. Data and Simulator	3](#heading=h.etc2vsbpyp77)

[3.1. Real benchmark (frozen, never trained on)	3](#3.1.-real-benchmark-\(frozen,-never-trained-on\))

[3.2. Source catalog (real COSMOS galaxies)	3](#3.2.-source-catalog-\(real-cosmos-galaxies\))

[3.3. Deflector library (real HST galaxies)	3](#3.3.-deflector-library-\(real-hst-galaxies\))

[3.4. GEN4: Physically self-consistent population	4](#3.4.-gen4:-physically-self-consistent-population)

[3.5. Hybrid image assembly	4](#3.5.-hybrid-image-assembly)

[3.6. Dataset validation gates	4](#3.6.-dataset-validation-gates)

[4\. CNN Architecture and Training	4](#heading=h.2gqa2cc6vzgu)

[5\. Results	5](#heading=h.wdc2fbm9eh41)

[5.1. Headline benchmark performance	5](#5.1.-headline-benchmark-performance)

[5.2. Causal ablations	5](#5.2.-causal-ablations)

[5.3. Uncertainty and confidence gating	5](#5.3.-uncertainty-and-confidence-gating)

[5.4. Comparison to Cao (conventional modeling)	5](#5.4.-comparison-to-cao-\(conventional-modeling\))

[5.5. Comparison to LEMON (CNN benchmark)	5](#5.5.-comparison-to-lemon-\(cnn-benchmark\))

[5.6. Transfer to Euclid Q1 and Roman	5](#5.6.-transfer-to-euclid-q1-and-roman)

[6\. Discussion	6](#heading=h.rgiozrri7elh)

[6.1. Why GEN4 works	6](#6.1.-why-gen4-works)

[6.2. What ablations tell us	6](#6.2.-what-ablations-tell-us)

[6.3. Limitations	6](#6.3.-limitations)

[6.4. Future work	6](#6.4.-future-work)

[7\. Conclusions	6](#heading=h.e5yuz2h994ur)

[Acknowledgements	7](#heading=h.yqahf12pwv4v)

[References	7](#heading=h.p4iqbbi0rtrb)

[Appendices	7](#heading=h.dzpwdb1k6dm6)

[Appendix A: Per-lens comparison tables	7](#appendix-a:-per-lens-comparison-tables)

## **1\. Introduction** {#1.-introduction}

### **1.1. Strong gravitational lensing as a cosmological probe** {#1.1.-strong-gravitational-lensing-as-a-cosmological-probe}

* What is θ\_E and why does it matter?  
* The SIS formula: θ\_E \= 4π(σ\_v/c)² × (D\_ls/D\_s)  
* Cosmological applications (mass profiles, dark matter, H₀)  
* Future surveys: Euclid, Roman, LSST (\~10⁵ lenses)

### **1.2. The need for automated lens modeling** {#1.2.-the-need-for-automated-lens-modeling}

* Traditional modeling: MCMC, nested sampling, \~3 min/lens (Cao 2025\)  
* CNN solution: ms/lens, amortized inference  
* Pioneering work: Hezaveh 2017, Perreault Levasseur 2017, LEMON 2026

### **1.3. The sim-to-real gap** {#1.3.-the-sim-to-real-gap}

* Prior-pull, compression, calibration failure  
* Domain adaptation works are sim-to-sim (Ćiprijanović 2023, Agarwal 2025\)  
* LEMON admits real \< sim performance

### **1.4. This work: closing the gap through physical self-consistency** {#1.4.-this-work:-closing-the-gap-through-physical-self-consistency}

* Five innovations listed  
* Paper outline

**2\. Literature Review**

### **2.1. CNN-based strong lens parameter estimation** {#2.1.-cnn-based-strong-lens-parameter-estimation}

* Hezaveh 2017, Perreault Levasseur 2017  
* Gawade 2025: HSC, 10–20% accuracy, pipeline-derived GT  
* HOLISMOKES X 2023: HSC, qualitative match, shear fails  
* LEMON 2026: 60 Euclidised HST lenses (R²=0.53) \+ 354 real Euclid Q1 (R²=0.71)  
* Cao 2025: TinyLensGPU, ≲5% deviation, \~10% fail, \~3 min/lens

### **2.2. Domain adaptation for strong lensing** {#2.2.-domain-adaptation-for-strong-lensing}

* Ćiprijanović 2023, Agarwal 2025, DA-NPE 2024  
* All sim-to-sim; sim-to-real remains unclaimed

### **2.3. Positioning our work** {#2.3.-positioning-our-work}

* Table 1: Comparison of leading methods  
* Five differentiators listed

### **2.4. Roman status** {#2.4.-roman-status}

* Wedig 2025: \~160k lenses, public simulations  
* No Roman parameter-estimation network exists  
* Our generator is Roman-ready

**3\. Data and Simulator**

### **3.1. Real benchmark (frozen, never trained on)** {#3.1.-real-benchmark-(frozen,-never-trained-on)}

* 62 SLACS \+ 40 S4TM, Bolton b\_SIE ground truth  
* 128×128 px @ 0.05″/px \= 6.4″ FOV  
* \[Table of sample properties—to be added\]

### **3.2. Source catalog (real COSMOS galaxies)** {#3.2.-source-catalog-(real-cosmos-galaxies)}

* COSMOS\_23.5, 56,062 galaxies (GREAT3-vetted)  
* Surface-brightness cut: ≤21 (SLACS) or ≤22.5 (Euclid)  
* Size cuts: min\_flux\_radius=1.0, minimum\_size=8 px  
* Brightness renormalization: Newton 2011, mean 24.3 mag at z≈0.65  
* GEN5: absolute magnitude \+ z-dependent cosmological dimming

### **3.3. Deflector library (real HST galaxies)** {#3.3.-deflector-library-(real-hst-galaxies)}

* Non-lens LRGs from SLACS/S4TM parent samples  
* Expanded to 488 stamps via footprint crossmatch  
* Measured: σ\_v, z\_l, mag, Re, q, PA, isophotes (a3/a4)  
* Pasted at native amplitude (no brightness scaling)

### **3.4. GEN4: Physically self-consistent population** {#3.4.-gen4:-physically-self-consistent-population}

* One real galaxy \= light \+ mass  
* θ\_E computed from σ\_v (SIS formula)—no independent prior  
* Mass shape \= light shape ⊕ misalignment (ΔPA\~N(0,10°), q\_mass=q\_light⊕0.08)  
* Tempered importance sampling (α=0.6) for flat θ\_E \+ FJ correlation  
* Deflector-disjoint split: 119 train / 20 val

### **3.5. Hybrid image assembly** {#3.5.-hybrid-image-assembly}

* All in physical e⁻/s units (AB zeropoint 25.94)  
* Components: paltas render \+ deflector stamp \+ empty cutout \+ companions \+ Gaussian top-up  
* Euclid/Roman: euclidise.py / romanise.py with real Q1 VIS PSF

### **3.6. Dataset validation gates** {#3.6.-dataset-validation-gates}

* gate\_stage0.py: sky-RMS, peak/sky, θ\_E range, radial profile  
* AR0 arc-realism gates for Euclid: contrast, width, knots, asymmetry

**4\. CNN Architecture and Training**

* Architecture: scale-conditioned ResNet / InceptionNeXt (4 stages, GAP, scale-scalar concat)  
* Input: arcsinh (a=1.0) \+ per-image z-score standardization  
* Loss: Gaussian-NLL (μ, log σ²)  
* Training: 40 epochs, batch 64, Adam, cosine LR, flip/rotation augmentation  
* Model selection: sim-val only (deflector-disjoint, PSF-disjoint, seed-disjoint)  
* TTA: 8× dihedral, σ \= aleatoric \+ epistemic variance

**5\. Results**

### **5.1. Headline benchmark performance** {#5.1.-headline-benchmark-performance}

* Table 2: SLACS \+ S4TM, native \+ Euclid domains  
* vs Cao 2025: match accuracy at \~10⁶× speed  
* vs LEMON: lead on NMAD/R²/bias with independent GT

### **5.2. Causal ablations** {#5.2.-causal-ablations}

* Table 3: remove each ingredient  
* Finding: real backdrops dominate (\>10× effect)  
* Flat θ\_E prior \+ real ePSF are individually necessary

### **5.3. Uncertainty and confidence gating** {#5.3.-uncertainty-and-confidence-gating}

* Spearman ρ(σ/μ, |frac error|) \= \+0.71  
* Table 4: confident-half fail 6% (SLACS)  
* σ is domain-aware: 9–10% on real vs. \~1% on sim-val

### **5.4. Comparison to Cao (conventional modeling)** {#5.4.-comparison-to-cao-(conventional-modeling)}

* Per-lens predictions from Cao 2025  
* Same 63 SLACS lenses, same Bolton GT  
* \[Table to be added\]

### **5.5. Comparison to LEMON (CNN benchmark)** {#5.5.-comparison-to-lemon-(cnn-benchmark)}

* SLACS-29: ours R²+0.57 vs LEMON R²-4.26  
* EELs-12: ours R²+0.83 vs LEMON \+0.21  
* COSMOS-5: small-N wash  
* ACS-13: arc radius only, excluded from θ\_E aggregate

### **5.6. Transfer to Euclid Q1 and Roman** {#5.6.-transfer-to-euclid-q1-and-roman}

* Real Euclid Q1: R²=0.61 (zero-shot, PyAutoLens GT)  
* Roman: zero-shot fails (R²=0.11), retraining succeeds (R²=0.93–0.94)

**6\. Discussion**

### **6.1. Why GEN4 works** {#6.1.-why-gen4-works}

* R²-negative→positive crossing  
* Self-consistency forces learning of Faber–Jackson relation  
* Without it: flat prior fails (R²≈0)

### **6.2. What ablations tell us** {#6.2.-what-ablations-tell-us}

* Real backdrops dominate (\>10× effect)  
* Causal decomposition: backdrops ≫ prior ≈ PSF \> pool ≈ DA ≈ companions ≈ lens light

### **6.3. Limitations** {#6.3.-limitations}

1. Small deflector library (139 stamps; 488 expansion underway)  
2. σ under-coverage (52%/83% on real vs 76%/96% on sim-val)  
3. Euclid Q1 gap (R²=0.61 vs LEMON 0.71)  
4. No multi-band yet  
5. Roman zero-shot fails

### **6.4. Future work** {#6.4.-future-work}

* Multi-band training  
* Real Euclid Q1 retraining  
* Multi-parameter heads  
* Domain adaptation  
* Mixed-population training

**7\. Conclusions**

1. Physical realism—especially self-consistency between light and mass—closes the sim-to-real gap.  
2. Our CNN matches conventional modeling accuracy (Cao) at \~10⁶× speed.  
3. We beat LEMON on the shared SLACS benchmark with independent spectroscopic GT.  
4. Uncertainty head works on real data (confident-half fail 6%).  
5. Generator is instrument-agnostic, ready for Euclid, Roman, and future surveys.

**Acknowledgements**

* Cao 2025: per-lens predictions  
* LEMON team: per-lens θ\_E predictions  
* Euclid Q1 data release  
* Roman Data Challenge organizers  
* Funding

**References**

34 references (from BibTeX file)

**Appendices**

### **Appendix A: Per-lens comparison tables** {#appendix-a:-per-lens-comparison-tables}

* SLACS-62 predictions  
* S4TM-40 predictions  
* LEMON comparison tables  
* Cao comparison tables

