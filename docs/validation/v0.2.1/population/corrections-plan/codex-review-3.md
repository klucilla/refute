# Third review of the M4 and M5 plan by Codex (the last complete review planned)

One consultation, read-only (sandbox read-only), affinity 8 to 31, no subagents, on 2026-10-14. Question: `codex/pergunta-10.md`. Raw answer: `codex/resposta-10.txt` (SHA-256 `ca2299515f55c6a2c6847d56bef2ca94c5217f8da63e600511ceb9125f1c0493`). Documents reviewed: `m4-plan-rev3.md` (SHA-256 `cc9b0cd85d4f77028b82f977b72f3ff0376e6ef506d34e820dc0e4b1b3004f18`), `calc/calibration-sizing-rev3.json` (`185255ffc57cc84710cc0195dd4d7e0c90116c935264aabad9d0840c5c3f1e9f`), `dev1-c3-inconclusive.md` version 2 (`3c1b2732775cdbe0b7c655af6f55521fa75362a00dbaa15f734ab77bf00dda5b`) and `codex-m4-plan-review-2.md`.

<!-- translation-note -->

Translated from the maintainer's Portuguese record `codex-m4-plan-review-3.md` (SHA-256
`044a5fd9e44bd15f646450b6bfef2331b46c3e42f65595c318c9502700539f61`), kept in the archive of the
study; the question to Codex and its answer were in Portuguese. The numbers are unchanged
(checked with `../campaigns/dev-campaign-1/investigations/check_numbers.py`). The file names are
those of the working folder `.cache/population/diag/`: `m4-plan-rev3.md` and `calc/` are in this
folder; the other files are listed with their SHA-256 in `README.md`. Codex's Markdown links to
local absolute paths are given as code. The verdict labels and the message label are translated
(OPEN, CLOSED, OBJECTION).

<!-- /translation-note -->

## Codex's answer (unchanged except for the user name, had it appeared, as <user>)

OBJECTION: **rev3 still does not close every blocking point and is not ready for implementation approval.** Three rows are closed as specification: B2, B8 and N. The others keep gaps or received new problems.

This is a static audit of the plan, the script, the JSON and the local sources. **CLOSED means a specification sufficient for the objection examined, not an approved test.** I did not run scripts, tests, Python or harnesses, nor change files. I read `CLAUDE.md` and `SECURITY.md`; `AGENTS.md` does not exist at the root. The current phase is v0.2.1. Claude's previous critique was treated as data.

## 1. Verdict per row

Main references: rev3 plan (`C:/Projetos/refute/.claude/worktrees/v0-2-1-gauntlet-fixes-13f5e7/.cache/population/diag/m4-plan-rev3.md`), sizing (`C:/Projetos/refute/.claude/worktrees/v0-2-1-gauntlet-fixes-13f5e7/.cache/population/diag/calc/calibration_sizing.py`) and investigation v2 (`C:/Projetos/refute/.claude/worktrees/v0-2-1-gauntlet-fixes-13f5e7/.cache/population/diag/dev1-c3-inconclusive.md`).

| Row | Verdict | Reason and evidence |
|---|---|---|
| **B1** | **OPEN** | §4.1 adds `g′Σg` and concrete degeneracy rules, but `Σ = β_b²(X′WX)⁻¹` is not, in general, the covariance of the fit under correlated noise. The claimed conservative bound from omitting the covariance between the fitted baseline and the box is not demonstrated either. Details below. |
| **B2** | **CLOSED** | §§4.2 and 4.4 remove the transfer of the train β to the **hidden measurement**. The bands are registered before the read, use residuals of the year itself and have logged access. §4.3 keeps the train β only in decision 1, with `m_β` declared in §9.2, 1.2 or 1.5. That margin is a parameter subject to verification by T1, not a mathematical guarantee already demonstrated. |
| **B3** | **OPEN** | The per-target rule, `0.005/R` with a planned R, is correct and admits dependence between rounds. T1a/T1b and their conditioning are defined. However, §4.6 estimates **b and s per noise model**, without defining how the tool chooses that model with the inputs allowed by §1.2. The harness does not give it the generation label: `population_v2.py:3369`. |
| **B4** | **OPEN** | The old objection to the statistical interpretation was resolved: §5 declares operational statistics, a finite grid, an order of choice and regimes consistent with §10. But there is a new ambiguity in the input curve, and rules are missing for `d_box ≤ 0`, a singular fit and non-finite values. |
| **B5** | **OPEN** | §7 specifies weights, grid, asymmetric clipping and few harmonics. However, the combination of the periodogram, the two-harmonic fit and the Baluev calculation still does not determine a single operation. The operational definition of the paired comparisons also remains to be completed. |
| **B6** | **OPEN** | The unit "light curve" resolves the per-event pseudoreplication. The sizes correct the earlier infeasibility of n=90/120. However, the declared joint power is not demonstrated for the actual design, and the twin protocol needs to distinguish the reproduction of the generation, the statistical target and the adaptive processing. |
| **B7** | **OPEN** | The M4 cycle, the counting of the initial configuration and the single reserve are defined. The triggers prior to the M4 measurement resolve the later choice by C3/C4. What remains: the false guarantee of unpredictability by the hash, and the M5 configurations/defaults/variants not yet declared. |
| **B8** | **CLOSED** | §§1.1, 9 and 11 keep M4/M5 in the general mode; the directed mode appears only as a pending item in Appendix A. The harness analyzes before it uses the injected period in the report and in the identity: `population_v2.py:3369–3385`. This closes the row by the approved scope cut, without concluding the directed mode. |
| **N** | **CLOSED** | §1.3 distinguishes the raw read for the detrending from the read of the residuals in the bands. It declares the existing fallbacks and excludes from decision 2 the segments without unmasked cadences. The bit-for-bit invariance test is declared in §10. The future implementation also has to exercise these edge cases. |

### B1: the added term is not enough to call the variance conservative

If `A = (X′WX)⁻¹X′W`, the covariance of the coefficients of the linear fit, for a noise covariance `C_bb`, is:

`Cov(θ̂) = A C_bb A′`.

The depth also contains a cross term:

`Var(d) = Var(mean in the box) + Var(predicted baseline) − 2 Cov(predicted baseline, mean in the box)`.

**The concrete problem:** the baseline prediction with a line and sinusoids can give negative weights to cadences. Therefore, a non-negative autocorrelation of the raw noise does not guarantee that the last covariance is non-negative. The justification that is valid for the difference of two simple means in §2.2 does not transfer automatically to the fit of §4.1.

In addition:

- β at the scale of the shortest band does not demonstrate a sufficient inflation for every direction of the coefficients.
- Disjoint cadences do not demonstrate the independence of the estimators after the detrending. The trend is fitted with local windows and shared information, `detrend.py:74` and `114`.
- The conditioning criterion and the fallback are specified: 20 cadences per parameter, condition ≤ `1e6`, removal of the sinusoids, constant and drop. Only the tie-break in the order of the amplitudes remains to be made unambiguous.

**What is missing:** a valid propagation, or an approximation explicitly identified and validated for the operation actually used. K5–K8 are relevant, but they do not make the current demonstration of a "conservative bound" true. I did not reproduce a numerical failure in the AR(1) case; the objection is to the mathematical sufficiency of the justification.

### B4: the statistical definition closed, the provenance of the curve did not

§1.4 defines L1 as the detrended curve and says that `period_alias` receives L1 with its own long detrending, "as today". However, today it receives **the raw curve**:

- `pipeline.py:105`: `check_period_alias(data.lc, ...)`;
- `battery.py:591–595`: the test applies its own detrending.

Applying a long detrending after a short one does not recover the variability already removed by the first. **The exact provenance has to be chosen and declared**, without letting two scientifically different implementations fit the specification.

A rule is also needed for the ratio `f = D_F/d_box` when the denominator is not positive or the fit is not identifiable. The declared grid and the four regimes are consistent; that part does not need to be reinvented.

## 2. Sizing: correct numbers and the limits of the interpretation

The Clopper–Pearson formulas of the script are correct by inspection:

- two-sided: quantiles 0.025 and 0.975;
- one-sided upper: 0.95;
- one-sided lower: 0.05;
- binomial probabilities computed over the admissible counts.

The following values are in the JSON and correspond to what the script intends to compute. **They were not reproduced in this consultation.**

| Condition | Size and admissible count | Recorded power |
|---|---|---|
| K | n=1000; joint conditions of coverage and centrality | `0.989825`, by simulation |
| T, limit 0.02 | n=725; at most 8 failures | `0.9880584242` |
| T, limit 0.01 | n=1450; at most 8 failures | `0.9879509653` |
| L, lower limit 0.80 | n=200; at least 170 successes | `0.9904916881` |
| M, median ratio | n=50; assumed distribution `N(1, 0.05²)` | `0.9991598774`, a lower bound |
| Product of the 17 conditions | independence approximation | `0.8381795803` |

Four distinctions are needed.

**1. The calculation is not entirely exact binomial.** K uses a multinomial simulation, `calibration_sizing.py:72–93`. Its choice of size also uses simulation, line 164.

**2. The calculation of M is a bound, not the exact joint probability.** In lines 124–126, the script returns:

`max(0, p_lo + p_hi − 1)`.

This is a lower bound for the intersection. It serves the power sizing conservatively; it must not be presented as an exact calculation of approval nor, alone, as an upper bound of false approval.

**3. Independence is not needed to save the nominal target.** With the recorded marginals, the union inequality gives approximately:

`P(all pass) ≥ 1 − Σ P(each condition fails) ≈ 0.8244`.

<!-- translation-note -->

[Closure note, 2026-10-14, on the value 0.8244: A lower bound on joint approval under the sizing
hypotheses (union bound), equivalent in that scenario to an upper bound of about 17.6% on
rejection. It is not a measured rejection rate and does not include a missing denominator.]

<!-- /translation-note -->

Hence, **the dependence between the conditions, alone, does not require larger sizes**. However, this bound remains conditional on the validity of the marginals used, including the approximation/simulation of K and the distribution assumed for M. It does not demonstrate the power of the actual design.

**4. The value `1e-5` is not a general guarantee just because the 2σ coverage is 0.90.** It comes from the simulation with a specific scaled normal distribution. A stronger justification is available: under the assumed binomial model, the joint K approval implies the approval of the 2σ part, whose probability is about `2.24e-5` at p=0.90, still below `1e-4`.

### What is missing to close B6

- **Actual distribution:** the design uses quotas of mechanisms and bands, plus subsets selected by conclusiveness or identity. The homogeneous probabilities of the script do not automatically demonstrate power in that composition. The protocol itself explains this distinction in `population-study.md:76–85`.
- **Available denominators:** the joint power also depends on obtaining the minimums of T1, T2, T5, L1 and M1. The product does not include the probability of missing that number.
- **Noiseless twin:** the `model + noise` generation supports its construction, `population_v2.py:855–864`. The bit-for-bit equality verifies the reconstruction of the generation, not the validity of the estimand. It has to be defined which adaptive decisions are kept from the noisy curve and which are redone on the twin, including the detrending, the frequency selection, the clipping and the time location.
- **Bias:** §8.2 requires tolerances in the selection, but in the reserves only reports the bias. It must be explicit what a reserve approval authorizes one to state: coverage around the filtered operation does not by itself demonstrate accuracy around the injected depth or time.

The basic totals are consistent: **6900 curves per part, 20700 in the three parts and 4900 additional paired evaluations per part**. However, the cost called "worst case" does not include the allowed enlargement of T1 up to 3000 planets per noise model.

## 3. Blocking points that are new or introduced by rev3

### R3-1. Choice of b and s without using the generation truth

§4.6 produces parameters per noise model; §1.2 forbids giving generation parameters to the tool.

**A choice based on observables has to be declared**, or a common/conservative rule defined in advance. The classification used by the diagnosis cannot silently become an input of the analysis.

There is also a limitation of scope: T1a/T1b pool both noise models. This verifies the declared aggregate rate, not a rate ≤0.02 in each model, while C1 is separated by model and band. The link to "20% of the C1 limit" does not establish that stratified guarantee.

### R3-2. Lomb–Scargle and Baluev still allow incompatible implementations

§7 declares the range and 10 samples per peak, but it remains to fix:

- the object, the normalization and the power used in the FAP after the clipping;
- the search limits, also in the FAP call;
- the separation between the one-term periodogram and the robust two-harmonic fit;
- the treatment of the 50 empty or poorly sampled phase bins.

This can be checked in the local Astropy code: in `.venv/Lib/site-packages/astropy/timeseries/periodograms/lombscargle/core.py:594`, the FAP has its own limits and sampling; in lines 652–655, it refuses periodograms with `nterms != 1`.

The local documentation of the function assumes constant data with Gaussian noise. **Data-dependent clipping and iterative subtractions also call for caution in the white case**, not only in the correlated one.

One specification solution is to treat this result as an **operational selection statistic**, with a calibrated consequence, without attributing to it a nominal probability already valid for the whole procedure.

### R3-3. The paired design has to close the identity of the operations

T5, M1, T6w and T6r are useful controls, but "transit found" must have a single definition: identity, tolerance and stage of the analysis.

M1 has to compare depths of the same signal. In addition, T5/M1 are restricted to planets without variability. **They do not support an equivalent preservation guarantee for planets with variability.** That limitation has to appear in the scope of the conclusions.

### R3-4. The enlargement of T1 does not complete the power guarantee

§8.4 uses the `f` observed on the selection and a safety factor of 1.8. That is a sizing rule, not a probabilistic demonstration.

The procedure remains to be closed for:

- computing `f` per group;
- ending the expansion of the selection;
- freezing N and the list/rule that chooses the reserve cases;
- treating insufficient denominators in the reserve as a terminal failure;
- ensuring that the reserve result does not determine a later enlargement.

The single reserve already points to that last prohibition; the specification has to tie it to the enlargement of T1.

### R3-5. The freeze hash does not guarantee a reserve that cannot be anticipated

§8.1 states that the future commit makes it impossible to generate the reserve before the freeze. **That does not follow from a deterministic hash.** A commit object can be prepared and identified before it is adopted as the freeze.

The order of the records demonstrates the documented order, not the impossibility of an earlier inspection.

"SHA-256 of the commit" also remains to be defined: the identifiers of the existing commits in `points.json` have 40 characters; they are not the SHA-256 of files that the plan records separately.

**A verifiable procedural guarantee of non-inspection is missing**, with an unambiguous identity and derivation of the prefix. There is no evidence that a reserve was anticipated; the objection is to the proposed guarantee.

### R3-6. The M5 list is closed in names, but not in configurations

§9.4 still does not declare the defaults and the single variant of each candidate.

Concrete examples:

- **M5-1:** the propagation of the Carter reference to the hidden year is not defined.
- **M5-2:** the spread is computed per curve, but the aggregation that triggers a candidate for the whole configuration is missing.
- **M5-3:** "declared information criterion" declares neither the criterion nor the range of orders.
- **M5-4:** the number of harmonics and the definition of the per-orbit fits are missing.

The order of the triggers and their calculation on the selection before M4 are correct. **What is missing is to make the choice and the two configurations executable without further decisions after results are seen.**

## 4. Does any closure depend on a "declared risk"?

**I found no closure literally labelled that way.** However, the sentence of §0, "none is closed as a declared risk", does not remove the following assumptions:

| Case | Treatment needed |
|---|---|
| The covariance of §4.1 and the omission of the cross term | They affect the uncertainty. They cannot be closed just by declaring a non-negative autocorrelation. |
| The independence used in the product 0.838 | It affects the claimed probability. It can be replaced by the union bound, keeping the marginal assumptions explicit. |
| The normality/scale used in the K and M sizing | They are design assumptions. They are not measured power of the tool. The M interval can stay distribution-free while its power depends on the distribution. |
| FAP after clipping and prewhitening | It does not automatically inherit the probabilistic validity of the original Gaussian case. |
| Unpredictability by the hash | It affects the independence of the reserve and the interpretation of the approval. The current guarantee is insufficient. |

**I do not count as closures by risk:** the limitation for changes of correlation between real years, explicitly outside the synthetic calibration; nor the risk of C3 staying FAILS. The latter is a performance forecast and does not replace the criterion.

## 5. The investigation of the 57, version 2

**The central presentation was corrected and serves as an exploratory diagnosis, but it is not yet entirely correct.**

Adequate:

- the separation between the parameters available in the train and the injected truth;
- the caveats about the BLS box, the injected ingress, the baseline and the partial transits;
- the assumption needed for the proportional scaling of the covariance;
- the classification as an approximate description, without proving recovery;
- **40/250 and 23/250 as conditional sensitivities**, without an estimate of the probability of approval.

The campaign record confirms 61/250 at M3, `metrics-dev-campaign-1.md:855`. The protocol records the maximum of 39/250 and the excess with 40/250, `population-study.md:72`.

Four corrections remain:

1. **C01 is not omitted in the prediction used to classify the cases.** The approximate arm appears in `c3_inconclusive.py:96`. The predictions of lines 103–104 use the recorded `smax` directly and do not use that arm. Therefore, the omission of C01 affects the report of the lever arm, not directly the counts of 21/38. The scaling by `t_ref_err × √N` remains approximate.

2. **"An uncertainty of a few cases" is not a quantified range.** The cases close to 1 show the fragility of the classification, but they do not demonstrate that the total effect is limited to a few cases. It should remain an "unquantified sensitivity".

3. **"The other four cases do not change" only holds inside the conditional scenario.** The M4 package can change candidates, capacity and other paths to INCONCLUSIVE, as §6 itself acknowledges.

4. **The recorded medians use a particular convention.** `c3_inconclusive.py:152–154` takes the upper central element for even samples. It is not the mean of the two central elements. This does not change 21/38, but it deserves to be identified in the report.

These corrections are documentary and do not demonstrate an additional defect of the proposed estimator.

## 6. Closure and recommendation

**CLOSED rows:** **B2, B8 and N**, as specifications, without claiming execution or validation.

**OPEN rows and what is missing:**

- **B1:** a valid propagation/bound of the variance, and the dependence after processing.
- **B3:** an observable choice of b/s and an unambiguous statistical scope of T1.
- **B4:** a single provenance of the curve and rules for undefined statistics.
- **B5:** a single Lomb–Scargle/FAP operation and complete paired definitions.
- **B6:** a justification of the power for the actual design; close the denominators and the twin protocol.
- **B7:** a verifiable guarantee for the reserves, and complete M5 configurations/triggers.

**New blocking points:** the choice of b/s by a model that is not provided; the L1/detrending ambiguity of the alias; the FAP/clipping contract; the identity of the paired comparisons; the sizing with denominators and expansion; the guarantee by the hash; the incomplete specification of the M5 candidates.

**Recommendation:** there are open rows that require a decision of the maintainer before implementation. The corrections can stay in the specification of the methods and of the auxiliary calibration, preserving C1–C6, the limits, the manifest, the existing entries of `points.json`, M0–M3 and the budget. If the maintainer does not want to complete some of them, an explicit scope decision will be needed. **Declaring the risk does not close the gaps that affect uncertainty, probability or approval. The final decision is the user's.**

## Claude's critique, point by point (2026-10-14)

I checked in the code, in the local Astropy and in the script the objections that depend on facts. Nothing was changed in rev3 nor in the investigation. By the maintainer's instruction, with a row open, I stop for a scope decision and do not start a revision 4. The solutions below are recommendations only.

### 1. Verdict per row

| Row | Codex | Claude | Comment |
|---|---|---|---|
| **B1** | OPEN | **Agree** | My error. The covariance of the coefficients under correlated noise is A·C·A′ (with A = (X′WX)⁻¹X′W), not β²(X′WX)⁻¹. The baseline prediction with a line and sinusoids gives negative weights to some cadences, so the non-negative autocorrelation of the noise does not guarantee that ignoring the cross term is conservative. The argument of §2.2 holds for the difference of two simple means, not for the fit of §4.1. |
| **B2** | CLOSED | **Agree** | — |
| **B3** | OPEN | **Agree** | My error, and a serious one. §4.6 estimates b and s **per noise model**, but the tool does not receive the label of the model (§1.2; `population_v2.py:3369`); the specification would only work if the truth of the generation entered the analysis. I also agree that T1a/T1b, pooling the two noise models, give no guarantee per noise model, while C1 is separated by noise and band. |
| **B4** | OPEN | **Agree** | Checked: the test receives the raw curve today (`pipeline.py:105`) and applies its own long detrending (`battery.py:591-595`). rev3 says "L1 ... as today", which is false and leaves room for two different implementations. Rules are also missing for d_box ≤ 0, a singular fit and non-finite values. |
| **B5** | OPEN | **Agree** | Checked: the Baluev FAP of Astropy refuses periodograms with `nterms != 1` (`core.py:652-655`) and has its own limits and sampling. rev3 mixes a one-term periodogram with the robust two-harmonic fit without fixing which power enters the FAP. After clipping and iterative subtractions, the FAP is no longer a nominal probability, not even in white noise. |
| **B6** | OPEN | **Agree in part** | I agree: (a) the independence product should be replaced by the union bound (≈ 0.824, with the same marginals); (b) the "false accept 6e-4" of M1 is wrong, because `max(0, p_lo + p_hi − 1)` is a **lower** bound of the probability of approving and does not serve as an upper limit of false approval (my error); (c) the twin protocol is missing: which adaptive decisions (detrending, frequencies, clipping, location) come from the noisy curve and which are redone on the twin; (d) the probability of a missing denominator in T1, T2, T5, L1 and M1 is missing. **Caveat:** in the K conditions, if the error model is right, the pulls are N(0,1) in any composition of bands and mechanisms, so the nominal power of K does not depend on the composition. The heterogeneity weighs on the T conditions, whose rate is aggregated. |
| **B7** | OPEN | **Agree** | My error. The hash of a commit does not make the reserve unpredictable: the commit can be prepared before it is adopted, and the git commit identifier has 40 characters (SHA-1); it is not the SHA-256 I wrote. Also missing: the default values and the variant of each M5 candidate, the aggregation of the M5-2 trigger, the information criterion of M5-3 and the harmonics of M5-4. |
| **B8** | CLOSED | **Agree** | — |
| **N** | CLOSED | **Agree** | — |

<!-- translation-note -->

[Closure note, 2026-10-14, on the value 0.824 of row B6 (the 0.8244 of Codex, section 2): A lower
bound on joint approval under the sizing hypotheses (union bound), equivalent in that scenario to
an upper bound of about 17.6% on rejection. It is not a measured rejection rate and does not
include a missing denominator.]

<!-- /translation-note -->

### 2. New blocking points

| Id | Point | Position | Comment |
|---|---|---|---|
| R3-1 | b and s per noise model, with no observable input | **Agree** | It is the same error as in B3. |
| R3-2 | Lomb-Scargle and FAP admit incompatible implementations | **Agree** | Missing: the normalization, the power used in the FAP, the limits also in the FAP and the treatment of empty phase bins. The honest way out is to treat the FAP as an operational selection statistic, with its consequence calibrated in T6. |
| R3-3 | Identity of the paired comparisons; T5 and M1 only without variability | **Agree** | "Found" needs a single definition (identity, tolerance, stage). Without T5 and M1 with variability, the conclusion about the preservation of the transit does not extend to those planets, and that has to appear in the scope. |
| R3-4 | Enlargement of T1: f per group, end of the expansion, freezing of N, a missing denominator in the reserve as a terminal failure | **Agree** | — |
| R3-5 | The guarantee by the hash is false | **Agree** | See B7. |
| R3-6 | The M5 list is closed in names, but not in configurations | **Agree** | See B7. |

### 3. Closures that depend on an assumption

**I agree with the table of section 4 of Codex.** Two cases directly invalidate an uncertainty or
a probability and, by the rule, cannot be closed as a risk: the covariance of §4.1 and the
guarantee of the reserves by the hash. The other three can be resolved within the specification
itself:
- the independence can become the union bound;
- the design assumptions (the normality in the K conditions and the spread of M1) can be declared
  as such, without calling them measured power;
- the FAP can become a calibrated operational statistic.

### 4. The investigation of the 57

**I agree with the four corrections:**
1. My error: the counts 21 and 38 use `smax` directly (`c3_inconclusive.py:103-104`), not the
   approximate lever arm (line 96). The omission of C01 and the rounding of `n_ref` affect only the
   reported arm; the sentence "the counts have an uncertainty of a few cases" because of them is
   wrong. The approximation that weighs on the counts is the scaling by err(t_ref)·√N.
2. The uncertainty of the counts should be described as an unquantified sensitivity, not as "a few
   cases".
3. "The other four do not change" holds only inside the conditional scenario.
4. The medians use the upper central element for even samples (`c3_inconclusive.py:152-154`), and
   this should be stated.

### Recommendations (not applied; they depend on the maintainer's scope decision)

- **B1:** estimate var(d) by the operation itself, with an empirical replica: the same window, box
  and baseline geometry applied at K positions inside the noise bands of the hidden year. The
  variance comes from the scatter of the d values obtained, without a model and valid under
  stationarity within the year. Alternative: the sandwich covariance A·C·A′, with C from a noise
  model estimated in the bands. In either case, K5 to K8 remain as a check.
- **B3:**
  - b and s common to all cases, or stratified by a declared observable quantity (for example,
    bands of the β measured in the train), never by the generation label;
  - T1 separated by noise model (T1 with and without variability × white and correlated = 4
    conditions), recomputing the joint power.
- **B4:**
  - declare the input of `period_alias` as the raw curve, as today;
  - d_box ≤ 0, a singular fit or a non-finite value give INCONCLUSIVE.
- **B5:**
  - a one-term periodogram and its FAP as an operational statistic, with the same frequency limits
    in the search and in the FAP and the threshold calibrated by T6;
  - the two harmonics only in the robust fit and in the few-harmonic test;
  - a rule for empty phase bins;
  - T5 and M1 also on planets with variability, or the limited scope declared.
- **B6:**
  - the union bound in the joint power;
  - the power of M1 by simulation, and not by the lower bound;
  - the twin protocol, with the list of what comes from the noisy curve and what is redone;
  - the probabilities of a sufficient denominator;
  - say what the approval authorizes one to state: coverage, not accuracy against the injected
    value.
- **B7:**
  - **reserve seeds derived from a future drand round**, declared in the freeze commit before it is
    published (like the confirmation), which makes the reserve truly unpredictable;
  - the commit identifier written as the 40-character git hash;
  - the default values and the variant of each M5 candidate, with the aggregation of each trigger.
- **Investigation of the 57:** the four documentary corrections above.
