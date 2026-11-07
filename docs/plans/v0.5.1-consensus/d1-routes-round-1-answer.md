## Verdict: **WEAKENED**

The three main facts are substantially right. The transit geometry route is worth measuring as a **development diagnostic**, but the script and data described so far do not establish an acceptance route. I found a partial `decompose.jsonl`, but no completed route summary, so I cannot assess its measured power.

## A. Generator and candidate routes

1. **The EB model is trapezoid-only.** EB1 adds primary and secondary trapezoids with the same duration and ingress shape, the secondary at phase 0.5 and scaled depth. EB2 does the same at twice the found period. Their primary geometry comes from the same `_transit_truth` and `solve_depth` path used for planet-like transits. The frozen C1 generator adds no ellipsoidal variation, Doppler beaming, or reflection to these EB families. Those effects therefore cannot improve D1 on this C1 generator, though they could help on real data. The astrophysical effects are real binary signals, but their absence here is visible in the generator code; the general mechanisms are described in the [BEER paper](https://arxiv.org/abs/1106.2713).

2. **The synthetic catalog star is fixed at solar radius and mass, with 5% reported errors.** C1 calls `synthetic.make_star()` with its defaults. Gaia measurements cannot supply new target-specific information for these synthetic stars. A tighter prior centered on the known synthetic values could change a score, but that would be using generator truth, not demonstrating that Gaia improves C1 classification. The external data route belongs on real targets and brings the stated source, licence, provenance, and dependency costs.

3. **The forecast supports the stated duration limitation.** The WP1 oracle leaves about 4.6 EB1 and 7.9 EB2 survivors at C1′ scale. The adopted `duration_excess` measurement marks 69.5% of family P as not detectable, consistent with “about 70%.” The oracle’s advantage matters: it knows the shape and noise, while a measured duration has estimator error. See the [feasibility report](</C:/Projetos/refute/docs/validation/v0.5.1/feasibility/README.md>) and [plan amendment 10](</C:/Projetos/refute/docs/plans/v0.5.1-plan.md>).

**Catalog-free signatures:** the eclipse shape and ingress/egress ratio are not promising for these folded binaries as generated: the two EB eclipses have identical trapezoid shape and ingress fraction. Odd/even depth is already the useful shape-independent signal when the depths differ, consistent with the [Kepler Robovetter treatment](https://iopscience.iop.org/article/10.3847/1538-4365/aab4f9/pdf). For near-equal depths, joint consistency among depth, duration, ingress, and impact parameter is the credible remaining photometric route. It is the same underlying geometry as the duration test, but can use more of the shape information.

## B. Risks and calibration for transit-geometry consistency

The score compares a physical-geometry planet fit with a free trapezoid. That is a sensible development experiment, but several details prevent interpreting its current thresholds as calibrated flags:

- **C1 planet controls are unusually favorable.** Their transit is generated as a trapezoid from the same geometry the physical model assumes. Real planets have limb darkening, and eccentric orbits can produce durations inconsistent with circular-orbit density expectations. The assumptions behind deriving stellar properties from transit shape are explicit in [Seager and Mallén-Ornelas](https://arxiv.org/abs/astro-ph/0206228); the duration effect of eccentricity is discussed in [Dawson and Johnson](https://arxiv.org/abs/1203.5537). A low flag rate on C1 planets would not establish a low false-flag rate for T3a real planets.

- **The proposed white-weight score is not valid for correlated cases.** The script uses a median per-cadence error for both white and correlated noise, so its correlated-noise `dchi2` does not use the generator’s covariance. Detrending and candidate selection also affect the residuals. The statistic and its threshold need calibration with the full covariance and the full candidate-generation chain, including search and selection.

- **Neither threshold is currently justified.** `dchi2 >= 9` has no established false-flag meaning here. The proposed 99.73% quantile from about 300 C1 planets is too imprecise for a 0.27% tail claim: it rests on roughly one expected tail observation. A nominal tail rate needs a predeclared calibration method and enough independent controls, or a validated parametric tail model.

- **The mass-uncertainty decomposition is missing.** Amendment 10(a) asks how much the separation depends on radius and mass uncertainty. The `decompose` path varies radius only; `forecast.planet_model` holds mass fixed. The separate geometry route does fit mass under a prior, but that does not answer the decomposition question.

To earn a route’s acceptance, predeclare its statistic, decision threshold, covariance treatment, eligible population, and D1/D2 accounting. Calibrate the entire search-and-fit chain on independent development controls, report false flags and binary power with uncertainty, and preserve a separate held-out acceptance run. Include realistic transit-shape and stellar-prior stress cases for the real-data counterpart. The supplied development sample can screen a design; it cannot validate the rare false-flag tail.

**Recommendation:** keep this route diagnostic for now. If later accepted, make it a warning that can classify a candidate as **WEAKENED**, not a fatal refutation. A D1 route must materially reduce EB survivors while preserving the plan’s D2 requirement and all applicable non-regression gates. This measurement alone cannot establish that.

## C. Other work within the remaining budget

I would spend the remaining roughly seven processor-hours on the following, in order:

1. **Complete the radius/mass decomposition.** Add mass uncertainty alongside radius, including their joint variation, and report how often fits hit bounds. This directly answers amendment 10(a); it does not need a new classifier.

2. **Use the geometry score as a comparative screen.** Compare white-weight and covariance-aware fits on the same eligible EB1, EB2, P, and PG development curves. Report per-family and per-noise results, with uncertainty, without treating a development quantile as an acceptance threshold.

3. **Do not spend this budget on extra shape-only classifiers.** The generator gives both eclipses the same ingress and duration, and has no out-of-eclipse orbital modulation. More tests of eclipse-shape asymmetry, ingress ratios, or BEER-like harmonics should have no designed signal on these C1 binaries. Their possible value is for real data, after a route is specified and separately calibrated.

**Objections**

1. **Critical, rare-tail calibration.** Evidence: the script uses white weights for correlated curves and an empirical 99.73% planet quantile from about 300 controls, alongside an uncalibrated threshold of 9. **Required change:** treat both thresholds as exploratory; before route acceptance, predeclare the full-chain statistic and calibrate its false-flag rate with covariance-aware independent controls and sufficient tail evidence.

2. **Critical, D2 and real-planet transfer risk.** Evidence: C1 planets share the assumed trapezoid geometry; limb darkening, eccentricity, and non-Gaussian TIC errors are not represented by that control. **Required change:** do not use the C1 false-flag rate to claim real-data safety. Preserve D2 in the combined acceptance and separately assess the T3a real-data counterpart; keep the route diagnostic or warning-only until that evidence supports a stronger role.

3. **Important, incomplete uncertainty decomposition.** Evidence: `nearest_with_bounds` varies radius, while `forecast.planet_model` fixes mass; amendment 10(a) asks about both. **Required change:** include mass and joint radius/mass uncertainty in the decomposition and report the resulting survivor estimates before concluding how much catalog precision matters.

4. **Important, shape-only alternatives are structurally unavailable.** Evidence: C1 EB1 and EB2 use identical eclipse durations and ingress fractions, and omit ellipsoidal, beaming, and reflection signals. **Required change:** record these as unavailable signatures for C1 and avoid spending the remaining development budget measuring their power on this generator.

