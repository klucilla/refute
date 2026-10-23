# Viability check (2026-10-23, read only)

> **Follow-up (the maintainer's option 2, 2026-10-23):** the two-year barriers, declared before
> the reading ([two-year-declaration.md](two-year-declaration.md)) and read
> ([two-year-results.md](two-year-results.md)): on these records only capacity, timing (T4's
> scope) and the undetermined hidden noise resolved together bring the white noise above the 195
> under specification B; the undetermined hidden noise is, in every round, an undetermined noise
> model with no valid replica depth counted, its sub-cause not recorded, and no committed plan
> specifies its repair.

Asked by the maintainer on 2026-10-23 after the delivery `cb671a7` (item 1). **Read only:** no lot,
no change of a criterion, of the engine or of the environment; X2f is not authorized. Every number
comes from committed code and records, or from the R_min study's archived records read in place
(the zip on the maintainer's Drive, checked by SHA-256 in [../../rmin-study/study/README.md](../../rmin-study/study/README.md)),
by the scripts in [scripts/](scripts/). Nothing here is a result of the engine on new data; the
optimistic bound is a hypothesis, never an execution.

## 1. Facts confirmed (the final aggregation, from the code)

- **The order of the rules**, `src/refute/core/verdict.py`, `aggregate`: a PASS without coverage
  becomes INCONCLUSIVE (line 148, `enforce_coverage`, lines 109 to 130); **a gate that did not PASS
  gives INCONCLUSIVE** (lines 149 to 157); **any fatal FAIL gives REFUTED** (lines 158 to 162); an
  expected test missing gives INCONCLUSIVE (lines 163 to 165); **any INCONCLUSIVE test gives
  INCONCLUSIVE** (lines 166 to 168); a warning FAIL gives WEAKENED (lines 169 to 173); otherwise
  SURVIVED (line 174).
- **The gate** is `snr` (`src/refute/packs/tess/gauntlet.py`, `check_snr`, `Severity.GATE` at lines
  43 and 58; on the corrected path `pipeline.py`, `_bls_gate`, line 333).
- **The holdout is a fatal test**: `holdout_by_year` with `Severity.FATAL` (`holdout.py`, lines
  1915, 1954 and 1991), and it is an expected test (`pipeline.py`, `expected_tests`, lines 360 to
  366; `conclude_analysis`, lines 394 to 395). It receives the raw data and the metadata only, never
  the global candidate (`pipeline.py`, lines 380 to 381; `holdout.py`, lines 1900 to 1906).
- **The holdout's own aggregation:** legacy (the engine's default), FAIL if any round FAILS, else
  PASS if any round PASSES, else INCONCLUSIVE (`holdout.py`, lines 1933 to 1945); specification B
  (X1b, experimental), FAIL if any FAIL, PASS only if **every** observing year's round PASSES, else
  INCONCLUSIVE (`spec_b_outcome`, lines 1862 to 1869).
- **So:** with the gate passed, a holdout FAIL gives REFUTED; with no fatal FAIL anywhere, a holdout
  INCONCLUSIVE makes the target INCONCLUSIVE; and **a holdout PASS alone does not give SURVIVED or
  WEAKENED** (any other fatal FAIL refutes, any other INCONCLUSIVE or missing test leaves it
  INCONCLUSIVE, and the gate comes first, even before a holdout FAIL). A planet is SURVIVED or
  WEAKENED **only if** its holdout PASSES (with positive coverage and every expected test present);
  G1 also needs signal identity. Two details (Codex's review), which do not change this for the
  population read here: `aggregate` raises an error when no gate is present (`verdict.py`, lines
  150 to 151), and specification B checks its rounds' completeness and refuses fewer than two
  observing years before it gives FAIL precedence (`holdout.py`, lines 1841 to 1864).

## 2. A necessary condition (item 1b)

In the measurable band, every planet whose holdout does not PASS ends REFUTED or INCONCLUSIVE.
C1 (REFUTED, upper bound ≤ 0.10) and C3 (INCONCLUSIVE, upper bound ≤ 0.20) therefore imply that the
holdout cannot fail to PASS on more than 30% of the planets at the point level; with the one-sided
95% Clopper-Pearson bounds of the population study's design (250 planets per noise model in the
band; C1 passes with at most 16 REFUTED, C3 with at most 39 INCONCLUSIVE), **at least 195 of the 250
need a holdout PASS (78%)** ([bounds.json](bounds.json)): necessary, never sufficient, and a
combination of the two acceptance counts, not a claim of simultaneous 95% coverage. Lowering the INCONCLUSIVE count by refuting
planets runs into C1's 16. G1's lower bound of 0.60 needs, per regime, at least 101 PASS of 150
(two-year) and 37 of 50 (three-year; variability).

## 3. The holdout of the true planets, measurable band, per noise and regime (item 1c)

**Source:** the R_min study's `constant` scenario (a planet present at constant depth), configuration
`M4-rmin-study`, records of code `2e4ff99`, each target derived at R = 8 with bs-choice's committed
pair (b 0.585, s 2.883) by the evaluator's own functions ([scripts/holdout_reading.py](scripts/holdout_reading.py),
[holdout-reading.json](holdout-reading.json)). **The reading reproduces the study's committed
INCONCLUSIVE counts in every group** (5599, 6319, 5056 and 5924 of 6400). The regimes come from the
case index (`population_v2._planet_mechanism`).

| Noise | Regime | Planets | Holdout, legacy: PASS / FAIL / INC | Spec B: PASS / FAIL / INC | INC targets: capacity only / capacity and other / no capacity reason | Main INCONCLUSIVE round reasons |
|---|---|---|---|---|---|---|
| AR(1) | 2 years | 2400 | 963 / 0 / 1437 (PASS 0.401) | 626 / 0 / 1774 (0.261) | 413 / 475 / 549 | capacity train 1118, hidden noise undetermined 1110, timing 644, capacity hidden 312, replicas below R 25 |
| AR(1) | 3+ years | 800 | 381 / 0 / 419 (0.476) | 248 / 0 / 552 (0.310) | 417 / 2 / 0 | capacity train 1371, capacity hidden 74, replicas 3 |
| AR(1) | variability | 3200 | 474 / 2 / 2724 (0.148) | 34 / 2 / 3164 (0.011) | 2515 / 208 / 1 | capacity train 8187, capacity hidden 490, train noise undetermined 161, timing 49, hidden noise undetermined 38, replicas 34 |
| white | 2 years | 2400 | 510 / 6 / 1884 (0.212) | 205 / 6 / 2189 (0.085) | 54 / 421 / **1409** | **timing 2371, hidden noise undetermined 1131**, capacity train 483, capacity hidden 69, replicas 12 |
| white | 3+ years | 800 | 285 / 0 / 515 (0.356) | 196 / 0 / 604 (0.245) | 514 / 1 / 0 | capacity train 1602, capacity hidden 75, replicas 1 |
| white | variability | 3200 | 81 / 0 / 3119 (0.025) | 3 / 0 / 3197 (0.001) | 2934 / 173 / 12 | capacity train 9066, capacity hidden 176, train noise undetermined 160, train SNR below the gate 52 |

("timing" is the rule "train-only timing uncertainty in the hidden year"; "capacity train" and
"capacity hidden" are decisions 1 and 2.)

- **Final verdicts and the global candidate's identity: not identifiable with the current records**
  in this configuration: the R_min records hold the holdout rounds only (no search, no gauntlet, no
  global candidate). The table bounds G1 from above (a planet is delivered only if its holdout
  PASSES); what the gauntlet and the gate would add is unknown here.
- **The limits this imposes** (the per-regime rates standardized to the population study's quotas
  per noise model, 150 two-year, 50 three-year, 50 variability: a descriptive standardization that
  corrects the R_min study's oversampling of variability; reading it as an expectation for another
  sample assumes the rates transport): holdout PASS of 250 under the legacy aggregation **51
  (white) and 91 (AR(1))**, under specification B **25 and 55**, against the **195** that C1 and C3
  need; no regime reaches G1's count as read.
- **An older configuration, for the final verdicts only** ([scripts/dev_campaign_reading.py](scripts/dev_campaign_reading.py),
  [dev-campaign-reading.json](dev-campaign-reading.json)): development campaign 1 (2026-10-13,
  before the M4 corrections, the whole analysis, point M3, catalog condition (i)), measurable
  planets, SURVIVED or WEAKENED / REFUTED / INCONCLUSIVE: AR(1) 2 years 142 / 4 / 4 of 150, 3+
  years 48 / 2 / 0 of 50, variability 12 / 38 / 0; white 2 years 84 / 9 / 57, 3+ years 46 / 4 / 0,
  variability 1 / 45 / 4. **Not the same configuration** (no capacity decisions, the old holdout);
  it shows that, there, the analysis outside the holdout did not stop most measurable planets
  without variability; the signal identity of the delivered ones is not in the committed metrics
  (the full result records are a release asset, not read).

## 4. What spec C can change, and what it cannot (item 1d)

- **Spec C can change** only the capacity decisions: decision 1 (`insufficient_capacity_train`) and
  decision 2 (`insufficient_capacity_hidden_noise`), through `e_pred` (X3's `b` and `s` change the
  same threshold).
- **It cannot change:** the timing rule (the train-only timing uncertainty in the hidden year), the
  hidden and train noise undetermined, the train SNR gate, the replicas below `R` (the choice of
  `R`), the duration-to-period ratio and the hidden window fraction, the rounds without windows;
  and, outside the holdout, the SNR gate, the gauntlet's fatal tests, a missing test, the
  attenuation of the measured depth (X2-A: FAIL with variability), the candidate's identity (X2-A:
  the wrong candidates without variability) and the aggregation rule (legacy or B).

## 5. The optimistic, descriptive bound (item 1e)

**Hypothesis:** every round INCONCLUSIVE by a capacity decision counted as PASS (the most favourable
case for delivering candidates: none of them FAILS); every other round as recorded; the gauntlet
and the gate not considered (they could only lower it). Not an engine run.

| Noise | Regime | Holdout PASS as read, legacy / spec B | Optimistic, legacy / spec B | G1 needs |
|---|---|---|---|---|
| AR(1) | 2 years | 0.401 / 0.261 | **0.771** / 0.487 | 0.673 |
| AR(1) | 3+ years | 0.476 / 0.310 | 1.000 / 0.996 | 0.740 |
| AR(1) | variability | 0.148 / 0.011 | 0.999 / 0.927 | 0.740 |
| white | 2 years | 0.212 / 0.085 | **0.410** / 0.117 | 0.673 |
| white | 3+ years | 0.356 / 0.245 | 1.000 / 0.999 | 0.740 |
| white | variability | 0.025 / 0.001 | 0.996 / 0.942 | 0.740 |

- **Holdout PASS of 250 at the study's quotas, optimistic:** legacy **161.4 (white)** and 215.6
  (AR(1)); specification B **114.6 (white)** and **169.2 (AR(1))**; the necessary condition needs
  195. **Under the recorded M4 configuration and the stated optimistic substitution, the
  quota-standardized reading stays below the necessary threshold in white noise under either
  aggregation, and in AR(1) noise under specification B**; G1's count is not reached in `white, 2
  years` under both, nor in `AR(1), 2 years` under specification B. This is a reading of these
  records, not a deterministic bound on a future sample of 250 planets nor on the final
  configuration, **whose viability is not identifiable from these records**.
- **The binding barrier is the two-year layouts**, and there the rounds left INCONCLUSIVE after the
  hypothesis are the timing rule and the undetermined hidden noise (white: 815 targets by timing
  alone, 238 by the hidden noise alone, 345 by both; AR(1): 56, 259 and 217), which spec C does not
  touch. Under specification B the variability cells also keep 186 (white) and 230 (AR(1)) targets
  INCONCLUSIVE, years undecided for other reasons.
- What the bound leaves out: some capacity-INCONCLUSIVE rounds, once measured, would FAIL or stay
  INCONCLUSIVE (how many is not identifiable with these records); the gate and the gauntlet; the
  final configuration's `b`, `s` and error model. On these records the substitution can only raise
  the holdout PASS; it is not an estimate of what the final configuration would give.

## 6. The other barriers, and one quantification only (item 1f)

**Barriers beyond spec C** (each its own front, none started): the timing rule in the two-year
layouts; the undetermined hidden noise; under specification B, every year decided; the train noise
and train SNR in the variability cells; the attenuation of the measured depth; the identity of the
train candidate; and, unknown under M4, the gate and the gauntlet on true planets.

**A quantification, not a proposal:** if the final aggregation counted a holdout INCONCLUSIVE as
WEAKENED (when every other test passes), the holdout would stop being a barrier to G1 and C3: the
upper bound of G1 from the holdout becomes its non-FAIL fraction, **249.6 of 250 (white) and
249.97 of 250 (AR(1))** at the quotas ([bounds.json](bounds.json); not zero FAIL: 6 white two-year
and 2 AR(1) variability targets FAIL as read). This would change what the verdict
asserts: a claim never tested on a hidden year would be reported as WEAKENED, a survival verdict.
It would need its own specification and validation, and is not proposed.

> **Recorded on the maintainer's decision of 2026-10-23 (item 3):** this quantification stands as
> a **warning**: the lever empties what the verdict asserts. It is not a path proposed.

## 7. Short report

- **Confirmed:** the aggregation's order (section 1); a delivered planet needs a holdout PASS; C1 and
  C3 together need at least 195 holdout PASS of 250 measurable planets per noise model.
- **The optimistic bound and its hypothesis:** with every capacity decision resolved in favour, on
  these records and standardized to the study's quotas, 161.4 (white) and 215.6 (AR(1)) of 250
  under the legacy aggregation, 114.6 and 169.2 under specification B; in white noise the reading
  stays below 195 either way. The final configuration's viability is not identifiable from these
  records.
- **Missing information:** the final verdicts and the global candidate's identity under M4; how the
  capacity-INCONCLUSIVE rounds would split once measured; the gate and the gauntlet on true planets
  under M4; the final configuration's rates (only X5 measures them).
- **What spec C can change:** the capacity decisions only. In the three-year and variability
  regimes, **resolving the capacity blocks favourably leaves room to meet the targets in the
  optimistic bound** (the maintainer's wording of 2026-10-23; not "spec C suffices"); in the
  two-year regimes it does not.
- **The next decision (the maintainer's) and its cost:**
  1. continue to X2f knowing that, on these records, spec C's best case leaves the white-noise
     reading below the necessary condition (X2f: 427 LP-h estimated, 641 at its ceilings);
  2. first, a read-only diagnosis of the two-year barriers (the timing rule and the undetermined
     hidden noise) on the same archived records: minutes of local reading, no lot;
  3. a scope reduction declared before any data (for example the claim without the two-year
     layouts), by the scope rule;
  4. end the attempt without approval.
  No option is chosen here, and none authorizes a run.
