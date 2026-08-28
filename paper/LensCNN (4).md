## **3\. Data and Simulator** 

or maybe call it Generator Pipeline section? 

### **3.1. Real benchmark (frozen, never trained on)**

We evaluate on the frozen spectroscopic-lensing benchmark of 62 SLACS and 40 S4TM lenses (Bolton et al. 2008 b\_SIE). The ground truth is the SIE b\_SIE Einstein radius, which is independent of our CNN training. One SLACS lens (J0955+0101) is dropped due to a bad cutout. All cutouts are 128×128 px at 0.05″/px \= 6.4″ FOV, from HST ACS/WFC F814W drizzled products. \[Table of sample properties to be added.\]

Also, we evaluate on 300 real Euclid lenses with the Ground Truth being PyAutoLens. 

### **3.2. Source catalog (real COSMOS galaxies)**

The source galaxies are drawn from the COSMOS\_23.5 catalog (GREAT3-vetted, 56,062 galaxies). We apply a surface-brightness cut: 

mag\_auto \+ 2.5·log10(2π r\_flux²) ≤ 21 for SLACS (7,808 galaxies) 

and ≤ 22.5 for Euclid (28,388 galaxies). 

Additional size cuts (min\_flux\_radius \= 1.0 px, minimum\_size \= 8 px) remove unresolved sources. The source brightness is renormalized to match the measured SLACS source population (Newton et al. 2011, mean ≈ 24.3 mag at z≈0.65). 

For GEN5 (Euclid/Roman), we use absolute magnitude with z-dependent cosmological dimming.

### **3.3. Deflector library (real HST galaxies)**

The deflector light comes from real HST stamps of non-lens LRGs from the SLACS/S4TM parent samples, later expanded to 488 stamps via a footprint crossmatch of all HST F814W frames against the SDSS σ\_v pool. Each stamp has measured σ\_v, z\_l, magnitude, effective radius, axis ratio, position angle, and isophote coefficients (a3/a4). The deflector is pasted at native amplitude—no brightness scaling.

### **3.4. GEN4: Physically self-consistent population**

The key innovation is observational self-consistency. Each training image is generated from one real galaxy:

1. Pick a library galaxy (with measured σ\_v, z\_l, light shape).  
2. Draw z\_s from a survey-specific prior.  
3. Compute θ\_E from σ\_v using the SIS formula (no independent θ\_E prior).  
4. Mass shape \= light shape ⊕ empirical misalignment (ΔPA\~N(0,10°), q\_mass \= q\_light ⊕ 0.08).  
5. Use tempered importance sampling (α=0.6) to keep θ\_E distribution flat while preserving the Faber–Jackson correlation (ρ(mag, θ\_E) ≤ \-0.15).

The split is deflector-disjoint (119 train / 20 val stamps), PSF-disjoint, and seed-disjoint.

### **3.5. Hybrid image assembly**

The final training image is assembled in physical e⁻/s units (AB zeropoint 25.94):

* Noiseless paltas source render (lensed source)  
* Real deflector stamp (native amplitude)  
* Real empty HST cutout (correlated noise \+ field neighbors)  
* Real field companions  
* Gaussian top-up to match real SLACS sky-RMS distribution

For Euclid/Roman, we apply the instrument operator (euclidise.py / romanise.py) with real Q1 VIS PSF (FWHM ≈ 0.20″ with wings), ZP conversion, and survey-depth noise.

### **3.6. Dataset validation gates**

Every dataset version must pass gate\_stage0.py: sky-RMS ratio (0.8–1.25), peak/sky (within real 16–84% band), θ\_E range and flatness, and radial profile overlay. For Euclid, AR0 arc-realism gates (contrast, width, knots, asymmetry) are also applied.

