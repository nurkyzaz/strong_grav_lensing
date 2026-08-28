## **1\. Introduction**

### **1.1. Strong gravitational lensing as a cosmological probe**

Strong gravitational lensing occurs when a massive foreground galaxy (the deflector) lies along the line of sight to a background galaxy (the source). The deflector's gravitational field bends and magnifies the source light, producing Einstein rings or arcs. The characteristic angular scale of this phenomenon is the Einstein radius (θ\_E), which directly measures the enclosed mass of the deflector within that radius. For a singular isothermal sphere (SIS), θ\_E is given by:

θ\_E \= 4π (σ\_v/c)² × (D\_ls / D\_s)

where σ\_v is the velocity dispersion of the deflector, and D\_ls and D\_s are angular diameter distances.

θ\_E is a fundamental observable in galaxy evolution and cosmology: it constrains the mass–density profile of galaxies, the dark matter content of early-type galaxies, and the Hubble constant through time-delay cosmography. Upcoming wide-field surveys—Euclid (Laureijs et al. 2011), Roman (Spergel et al. 2015), and LSST (Ivezić et al. 2019)—are expected to discover \~10⁵ strong lenses, presenting both an opportunity and a challenge.

### **1.2. The need for automated lens modeling**

Traditional lens modeling relies on iterative, likelihood-based inference (e.g., MCMC, nested sampling) to fit parametric mass models (Sérsic light profiles, SIE mass profiles, external shear). While accurate, this approach is computationally expensive (\~3 minutes per lens; Cao et al. 2025\) and requires human expert input for initialization and quality control. With \~10⁵ lenses expected from Euclid alone, traditional modeling cannot scale.

Convolutional neural networks (CNNs) offer a solution. Once trained, a CNN can estimate θ\_E from a single image in milliseconds—amortizing the inference cost across the training set. Pioneering work by Hezaveh et al. (2017) and Perreault Levasseur et al. (2017) demonstrated that CNNs can recover SIE parameters from simulated HST-like images. More recently, the LEMON framework (Busillo et al. 2026\) showed that a CNN can be trained on fully parametric Euclid VIS simulations and applied to real Euclid Q1 lenses, achieving R²=0.71 on θ\_E.

### **1.3. The sim-to-real gap**

Despite these successes, a persistent problem remains: CNNs trained on simulations degrade substantially when applied to real telescope data. This "sim-to-real gap" manifests in several ways:

Lemon’s R^2 \= \-4 when applied to SLACS (I don’t know can we mention this) 

* Prior-pull: CNNs trained on a narrow or skewed θ\_E prior collapse to the training mean on real lenses (the m3 baseline in this work: R²=-1.02).  
* Compression: Predicted θ\_E vs. true θ\_E slopes are \<1, indicating the network hedges toward the mean under domain shift.  
* Calibration failure: Uncertainty estimates that are well-calibrated on simulations become overconfident on real data (e.g., 76%/96% coverage on sim-val vs. 52%/83% on real lenses).

The physical origins of this gap remain poorly understood. While several works have attempted domain adaptation (Ćiprijanović et al. 2023; Agarwal et al. 2025), all have been sim-to-sim, explicitly deferring real-data validation to future work. LEMON (Busillo et al. 2026\) does evaluate on real Euclid Q1 lenses, but their training remains fully parametric and they report degraded performance on real vs. simulated data (their Sect. 7: "on real images the predictions from LEMON are worse than on simulated lenses").

### **1.4. This work: closing the gap through physical self-consistency**

In this paper, we present a CNN-based θ\_E estimator trained on a physically self-consistent, real-ingredient simulation pipeline. Our key innovations are:

1. Observational self-consistency (GEN4): Each training system uses one real HST galaxy for both its light (the deflector stamp) and its mass (θ\_E computed from that galaxy's measured SDSS velocity dispersion σ\_v). This forces the network to learn the luminosity–mass (Faber–Jackson) relationship that human modelers use when arcs are faint.  
2. Real ingredients throughout: Real COSMOS sources (GREAT3-vetted), real HST empty-sky backdrops (for correlated noise and field neighbors), real focus-diverse empirical PSFs (STScI ACS ISR 2018-08, ISR 2023-06), and real field companions—all in physical e⁻/s units at AB zeropoint 25.94.  
3. Causal ablations: We systematically remove each realism ingredient to measure its impact. We find that real backdrops dominate (\>10× effect), followed by the empirical PSF and flat θ\_E prior. The GEN4 self-consistency step is the decisive breakthrough: without it, even a flat prior fails to improve real-lens performance (R²≈0).  
4. Uncertainty quantification: A Gaussian-NLL head provides a domain-aware uncertainty that correlates with real-world error (Spearman ρ=+0.71). On the confident half of SLACS, the failure rate drops to 6%—meeting the publishable bar for automated modeling.  
5. Comprehensive evaluation: We evaluate on the frozen spectroscopic-lensing benchmark of 62 SLACS and 40 S4TM lenses (Bolton et al. 2008 b\_SIE), as well as on Euclid-degraded versions (real Q1 VIS PSF), real Euclid Q1 lenses (vs. PyAutoLens GT), and a public Roman simulation challenge. We compare to LEMON, Cao et al. (2025), Gawade et al. (2025), and HOLISMOKES X (Schuldt et al. 2023).

This paper is organized as follows. Section 2 reviews the literature and positions our work. Section 3 describes the generator pipeline in detail. Section 4 presents the CNN architecture and training. Section 5 presents results, including benchmark performance, comparisons to LEMON and Cao, ablations, uncertainty calibration, and transfer to Euclid/Roman. Section 6 discusses limitations and future work. Section 7 concludes.

P.S. we gonna mention Gen4 and Gen5 a lot, Gen4 simply means a generation of HST like lenses (low redshift), Gen5 is for euclid and roman like domain (high redshift) 