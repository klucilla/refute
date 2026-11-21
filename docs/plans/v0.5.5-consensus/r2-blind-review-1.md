# Blind review of the R2 bundle (v0.5.5), round 1

**Provenance (written by the maintainer's adviser, not by the reviewer).**
- Reviewer: one fresh session of Claude Fable 5.2, launched by the maintainer's adviser on 2026-11-21 under the maintainer's approval of that day (one session, read only).
- Input: only the 12 files of the blind bundle, rebuilt from git at `55e32fd0` and checked against `docs/validation/v0.5.5/r2-bundle-manifest.json` (built 2026-11-21T17:05:45Z): all 12 SHA-256 equal. Three source files (`battery_v51.py`, `params.py`, `power.py`) carry CRLF line endings in the manifest; the rebuilt copies were given the same bytes.
- Rules given to the reviewer: no other path, no git, no network, no writing; report any contamination.
- The reviewer's use: 230,327 tokens, 16 tool calls, about 4.8 minutes; it counts apart from Codex's lines, as the decisions say.
- The text below the line is the reviewer's report, unchanged.

---

# Blind review of the R2 bundle (v0.5.5)

Reviewer scope: only `/home/claude/r2blind/bundle/` was read (12 files plus `MANIFEST.json`). No git, no network, no other path, nothing written. Nothing from user memory was used.

## 0) Manifest check and contamination findings

**Manifest.** All 12 files match `MANIFEST.json` by SHA-256 (`arguments.md`, `code-semantics.md`, and the ten files under `frozen-rules/src/refute/`). No extra or missing file.

**Contamination.** I found no target number, forecast, earlier-round count or R1 result in any file. I did find directional text that says which targets each option moves; none of it states magnitude or that a target would pass. The maintainer decides whether this voids blindness; my judgment is that it does not, but it should be reworded before a second reviewer sees it.

| File:line | Quote (under 15 words) | What it reveals |
|---|---|---|
| `arguments.md:21` | "test-rule changes relevant to D2 (planets kept) and T2a" | Which targets drive the scope (by inference, the ones not met) |
| `arguments.md:109` | "INCONCLUSIVE planets with only warning-class gaps become WEAKENED" | Direction of B1 (e) on D2, D4, T2a |
| `arguments.md:143` | "raising the alternative eases the power certificate" | The B2 (b) derivation's direction is known before the derivation exists |
| `arguments.md:215` | "which is the purpose and also the risk" | B3.3 is aimed at planets on variable stars |
| `arguments.md:249` | "it serves D2 and T2a" | The `odd_even` estimator change is target-directed |
| `arguments.md:254-261` | "Helps" column: "D2, D4, T2a" / "D2, T2a" | Per-option direction for every change |

Other mentions are existence only, not content: `arguments.md:246` ("at the expected counts", "R1's development checks") and the `excluded` field of `MANIFEST.json`. `power.py:40` ("at least 45 of 50 simulated sinusoids") is a rule definition, not a result.

**Bundle gaps that limit this review.**
- `battery.py`, `centroid_v5.py`, `a0*.py` and `calib05/` are absent. I cannot verify the outcome-dependent severities of `period_alias` and `eb_catalog`, nor the severities of `plausibility`, `centroid_shift` and `nearby_contamination`.
- The targets D1 to D4, T2a to T2c and T3a are never defined. Claims such as "D1 counts SURVIVED only" (`arguments.md:103`) and "T2b counts ... SURVIVED or WEAKENED (`calib05/c2.py`)" (`arguments.md:106-107`) cannot be checked.

## 1) Per-question review

### Summary table

| Question | Document's primary | Classification of the options | My primary | Agree? | Verdict on the primary |
|---|---|---|---|---|---|
| B1 | (a) keep blocking; (e) as registered variant | (a) no change; (b), (c), (d), (e) are rule changes; (e) is a relaxation of WEAKENED | (a), plus a reporting-only sub-class of INCONCLUSIVE | Yes | **SURVIVED** |
| B2 | (a) keep 0.5 + 0.3; (b) only with a derivation | (a) no change; (b) rule change (narrows what a PASS certifies); (c) new test | (a) | Yes | **SURVIVED** |
| B3.1 | (a) keep the small-residual requirement | (a) no change; (c) rule change | (a) | Yes | **SURVIVED** |
| B3.2 | Simulated joint only with a derived, accepted model; otherwise Fréchet | Method change if the model is validated; a disguised relaxation if not | Fréchet now; joint later via a closed-form covariance | Yes, with a condition | **WEAKENED** |
| B3.3 | Evidence split, declared as a rule change | Rule change (INCONCLUSIVE to PASS) | Evidence split, with four added conditions | Yes, conditionally | **WEAKENED** |
| B4 | New draws, none in R2 | Procedure | Same, plus a frozen decision rule | Yes | **WEAKENED** |

### B1: warning-severity INCONCLUSIVE blocking

- **Code check.** The description of `aggregate` is correct (`core/verdict.py:251-276`): gate, then fatal FAIL, then missing or any INCONCLUSIVE, then warning FAIL.
- **Are the arguments principled?** Yes. The rejections of (b), (c) and (d) follow from "no statement stronger than its evidence" and need no number. The document itself says (e) "lowers the evidential requirement for a retained ... verdict" and that the principles do not justify it (`arguments.md:91-93`). That is an honest classification, not a disguised relaxation.
- **Hole in (e): deferred tests.** `defer_tests` returns a deferred test as INCONCLUSIVE with zero coverage and its severity kept (`core/verdict.py:157-177`). It is present, not "missing". Under (e) as written, a warning test that never ran at this stage would yield WEAKENED. The definition must treat deferred and zero-coverage results as blocking.
- **Hole in (e): emitted severity.** `code-semantics.md:55` scopes B1 by the severity a result emits. For tests whose severity depends on the outcome (`period_alias`, `eb_catalog`), an INCONCLUSIVE could carry WARNING and escape the block. I could not check this (file absent). (e) must be defined by whether the test can ever emit FATAL, not by the emitted severity.
- **(e) has no frozen limit on its cost.** The document says D1 does not limit it (`arguments.md:103-105`), and the proposed check (paired transitions) is a measurement with no pass/fail rule. Before (e) could ever be adopted it needs a pre-frozen bound on spurious SURVIVED + WEAKENED.
- **(e) mixes three different things** under WEAKENED: a test that examined nothing, a test without power, and the ambiguous sinusoid (a doubt partly shown). Only the third resembles "a doubt shown by evidence".
- **Tension in the "For" of (a).** "WEAKENED keeps its narrow meaning ... which every historical record uses" (`arguments.md:72-73`). In battery versions 2 and 3, a flagged sinusoid alone was a warning FAIL, so WEAKENED meant "a sinusoid exists" (`battery_v5.py:446`, `battery_v51.py:211`). The meaning was already broader than stated.
- **My primary.** (a). Add a reporting-only split of INCONCLUSIVE into "warning-only gaps" and "fatal or gate gaps". That delivers principle 3 without changing what any verdict asserts.

### B2: the background sub-check's alternative

- **Code check.** Correct: FAIL at rise ≥ 3 errors and fraction ≥ 0.5 (`battery_v51_diff.py:548`, `params.py:152-153`); alternative 0.5 + 0.3 (`battery_v51_diff.py:651`, `params.py:317`); depth and rise drawn independently (`battery_v51_diff.py:654-657`).
- **Selective scrutiny in the "Against (a)".** The argument that an increment "with no derivation" is "an accident" applies equally to the aperture and SAP increments, which are the same undeived convention (`params.py:311-317`, comment "conventions"). Singling out the background's increment is principled only if the same test is applied to all three, or a reason is given for the difference.
- **Direction known before the derivation.** `arguments.md:143` already says the alternative would be raised. That is consistent with simple arithmetic (a 1:1 coupling gives a fraction of 1.0), but it means (b) is known to be a relaxation of the certificate before its model exists.
- **Model inconsistency (b) would have to fix.** If the background rise causes the dip, depth and rise are strongly correlated under the alternative. The block draws them independently, unlike the aperture and SAP blocks, which use a measured correlation (`battery_v51_diff.py:316-320`, `625-629`). Adopting a contamination model without changing the draw would be incoherent.
- **(b) cannot be validated in this version.** Its required controls are "a future obligation; nothing is run now" (`arguments.md:164-166`). It should be explicitly ineligible for adoption until those controls exist.
- **My primary.** (a). The document's statement that a PASS certifies sensitivity under the stated model, not the absence of contamination, is correct and should be carried into the records.

### B3.1: keep the small-residual requirement

- Agree with (a). The requirement is what makes the test attack "the variability explains the dip".
- Note for the record: (c), "rejected on principle", was the frozen rule of versions 2 and 3 (`battery_v5.py:446`, `battery_v51.py:211`). The document should say so, since it bears on B1.

### B3.2: Fréchet versus a simulated joint probability

- **Code check.** Correct: block probability is `max(0, p + q − 1)` only when coverage is valid and FAIL is allowed (`battery_v52.py:371`); `p` is the minimum over eight phases (`battery_v5.py:465-495`); `q` is Gaussian with zero residual mean (`battery_v52.py:341-345`).
- **The gain is bounded, without any target number.** A joint probability cannot exceed min(p, q). So the simulated joint can only change cases where both marginals already reach 0.95 and their sum is under 1.95. It cannot rescue a case where either marginal is below 0.95.
- **A common model is closer than the document suggests.** The fitted coefficients and `r` are both linear in the same flux vector (`battery_v52.py:248-255`). Under the noise model both marginals already assume (white errors scaled by beta), their covariance is determined in closed form. The open assumption is beta: a scalar inflation does not represent how red noise correlates the coefficients with the box.
- **Why WEAKENED.** The primary is conditional and the bundle contains no model, so this review cannot accept one. By the document's own rule, Fréchet is the primary today. The freeze must state that, and a model added later needs its own blind review before any number.
- Using the lower limit of a declared band is stricter than the current blocks, which use a point estimate from 2000 draws (`core/sensitivity.py:58`, `279-297`). That is sound.

### B3.3: the evidence split of the ambiguous branch

- **Code check.** Correct: flagged without a small residual returns INCONCLUSIVE with no sensitivity blocks (`battery_v52.py:420-430`).
- **Principled.** "Shown large" (`r − 3·sigma_r > 0.5·D`) is the mirror of the FAIL rule and uses the same 3-sigma standard. Under the Gaussian model, a dip half explained by the sinusoid is shown large with probability about 0.13 %. The framework's general logic (no rejection plus certified power gives PASS) would allow more; the split asks for positive evidence on top.
- **It is a relaxation of SURVIVED**, correctly declared as a rule change. D1's frozen rule does limit it, because the new PASSes can reach SURVIVED.
- **Issues to fix before the freeze.**
  1. `D` is treated as a constant with no error. `r` is measured on the raw, median-normalized flux minus the test's own model with a global out-of-transit baseline (`battery_v52.py:248`, `pipeline_v52.py:187`); `D` comes from the detrended (and possibly pre-whitened) series (`pipeline.py`, `attack_candidate`). An unmodelled trend can inflate `r` relative to `D` and produce a false "shown large".
  2. The main risk, which the document names, is variability outside the fitted model. No adversarial family is designed for it. V1 and V2 may not contain non-sinusoidal periodic variability that leaves a large residual.
  3. Non-finite or zero `sigma_r` must stay INCONCLUSIVE in the new branch; the FAIL branch guards this (`battery_v52.py:338`), the split's text does not.
  4. The record must distinguish "PASS, not flagged" from "PASS, flagged and shown large", so the transitions can be counted and audited.
- **Implementation trap.** The `q` marginal hard-codes `3.0` instead of `ATTENUATION_SIGMAS` (`battery_v52.py:342`).

### B4: data outside development

- New draws with every earlier seed and target excluded is the right design; nothing is drawn in R2.
- **Missing.** No decision rule: which variant combination decides, what counts as a failed confirmation, and that there is one confirmation only with no redraw.
- New seeds of the same generator test seed overfitting, not overfitting to the generator's families. Only the newly drawn real targets (C2', C3') test that.
- Excluding all earlier real targets may leave a systematically different (harder or fainter) population. This should be stated in advance.
- "v0.5.1 plan's section 5" is not in the bundle and could not be checked.

## 2) Safeguards C1-C7

| Item | Operational? | Gap |
|---|---|---|
| C1 historical locks | Yes; STOP on non-reproduction | None material |
| C2 freeze before any number | Yes, strong ("not even a cost pilot") | Protects only against new-version numbers. The scope was chosen knowing the old results. It is sufficient only together with C3 and C5. The freeze content is not enumerated |
| C3 blind review | Yes | Directional text (section 0); bundle lacks target definitions and several source files |
| C4 both variants published | Partly | Does not say which variant decides acceptance. Up to 16 combinations exist (B1 × B2 × B3.2 × B3.3) with no declared decisive one. Lists D2, D4, T2a only; costs (D1, T2b, spurious families) must be reported under both too |
| C5 confirmation on new draws | Partly | No decision rule, no single-shot statement, no sizing for the adversarial side |
| C6 disclosure | Yes | Not reviewable here, by design |
| C7 spurious families | Partly | See below |

**C7 in detail.**
- "Necessary, not sufficient" is stated, and a failure is a STOP, not a trade. Both are right.
- D1's frozen rule is a threshold. Spurious survival can rise inside its slack and still pass. Every change, not only B1 (e), needs paired old-versus-new transitions on the same curves with a non-inferiority margin frozen in advance.
- The safeguard has no power statement. By the project's own rule (no PASS without the power to fail), an adversarial check that "passes" on too few curves has shown nothing. Sizes must be set so an increase of the frozen margin is detectable.
- The families are the known ones. B3.3 and B2 (b) each have a specific failure mode with no family designed for it.

**Sufficiency against relaxation by redesign.** Not yet sufficient. The three missing pieces are: a single decisive primary combination frozen with the arguments, a paired non-inferiority rule for every change, and a confirmation decision rule.

## 3) Build order and dependencies

- **The `odd_even` estimator change has no argument at all.** It is first in the build order and labelled "method" (`arguments.md:249`, `260`), but nothing in the bundle says what the estimator, its error model or its alternative would be. `odd_even` is FATAL (`battery_v52.py:93-98`, `176-178`), so it moves both REFUTED and SURVIVED. Version 3 used a matched-trapezoid estimator (`pipeline.py`, `v05_tests`, comment "WP3 (d)"), version 4 uses box depths (`battery_v52.py:104-187`); a third estimator for the same test is a forking path. I cannot classify it as method or rule change. This is the most severe item.
- **Order.** Sinusoid, then background, then B1 is reasonable; B1 is a recount, so its position does not matter. The document must state that no parameter is changed between steps after a step's numbers are seen; steps serve attribution only.
- **Interactions not measured.** B3.2 and B3.3 act on the same test; only their joint effect is planned. Report each main effect and the full combination.
- **B1 (e) × ambiguous sinusoid.** Under (e) every ambiguous-sinusoid case becomes WEAKENED, which restores the version-3 outcome for flagged stars. That interaction with B3.3 is not in the table.
- **Costs that are named but not bounded:** spurious SURVIVED + WEAKENED under (e); partial contamination under B2 (b) (controls deferred).
- The dependency table is otherwise candid about what each change can worsen, including EB1/EB2 and PV transitions that D3 cannot see.

## 4) Factual errors against the code

1. **`code-semantics.md:52`** says the two-sided `secondary_eclipse` is WARNING "also when INCONCLUSIVE". In the no-candidate path it is emitted as FATAL (`pipeline.py:217`). Harmless today because the gate fails first, but the statement is not exact.
2. **`arguments.md:72-73`** ("narrow meaning ... every historical record uses") is contradicted in spirit by versions 2 and 3, where a flag alone was a warning FAIL (`battery_v5.py:446`, `battery_v51.py:211`).
3. **`code-semantics.md:15-17`** lists the modules `v052_tests` assembles from; it omits `power`, `centroid_v5` and `battery.check_period_alias` (`pipeline_v52.py:37`, `116-126`, `158-169`). Incomplete, not wrong.
4. **`code-semantics.md:90`** cites `ATTENUATION_SIGMAS` for the outcomes; the sensitivity marginal uses a literal `3.0` (`battery_v52.py:342`). Same value, latent divergence.

Verified as correct: the aggregation order; coverage and sensitivity enforcement (`core/sensitivity.py:184-197`); the registry and the 0.95 / 0.9 probabilities (`power.py:41`, `57-68`); background and sinusoid constants (`params.py:152-153`, `317`, `330-332`, `364-366`); the flag rule (`battery_v52.py:373-376`); the deferral semantics.

Not verifiable from the bundle: outcome-dependent severities of `period_alias` and `eb_catalog`; severities of `plausibility`, `centroid_shift`, `nearby_contamination`; every statement about how D1, T2b and the other targets count.

## 5) Overall verdict

**WEAKENED.** The bundle is a usable basis for the design decision. Its primaries are conservative (three of them keep the current rule), relaxations are labelled as such, and no argument I checked holds only by an unstated number. It is not SURVIVED because one change is unargued, the acceptance rule across variants is undefined, and two definitions have holes.

**Must change before the arguments are frozen, most severe first:**

1. **Argue the `odd_even` estimator change or remove it from the build order.** State the estimator, error model, alternative and whether it is a method or rule change, under the same writing rule.
2. **Freeze one decisive combination of primaries** for acceptance and confirmation. State that variants are reported only and can never replace the primary after the freeze.
3. **Add a paired, pre-frozen non-inferiority rule** on the spurious families and T2b for every change, with sizes that give it power.
4. **Fix the definition of B1 (e):** deferred and zero-coverage results block; scope by whether a test can emit FATAL, not by emitted severity; add a frozen limit on spurious SURVIVED + WEAKENED.
5. **B3.3:** handle the uncertainty and provenance of `D`; add an adversarial family of non-sinusoidal periodic variability; keep non-finite `sigma_r` INCONCLUSIVE; record the new PASS distinctly.
6. **B3.2:** state that Fréchet is the primary at the freeze; any joint model needs its own blind review before any number.
7. **B2:** state that (b) is ineligible until its coupling controls exist; apply the "no derivation" test to the aperture and SAP increments too, or explain the difference; if (b) is ever adopted, make the block's draw follow the contamination model.
8. **B4 / C5:** add the confirmation decision rule, single-shot, and the population caveat.
9. **C3:** remove the directional text listed in section 0, add count-free definitions of the targets, and add `battery.py` to the bundle for the next reviewer.
10. **Correct the four factual items** in section 4.

**Uncertainty.** I could not see how the targets are defined or the absent source files, so item 4's severity concern and the "D1 limits B3.3" statement rest on the document's own descriptions. I ran no code; all statistical statements are from reading the formulae.
