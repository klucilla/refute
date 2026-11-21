# Blind review of the R2 bundle (v0.5.5), round 2

**Provenance (written by the maintainer's adviser, not by the reviewer).**
- Reviewer: one NEW session of Claude Fable 5.2 (not the round-1 reviewer), launched by the maintainer's adviser on 2026-11-21 under the maintainer's approval of that day (15:21), read only.
- Input: only the 19 files of the second blind bundle, rebuilt by `docs/validation/v0.5.5/r2_bundle.py` from git at `621a14f5` and checked against `docs/validation/v0.5.5/r2-bundle-2-manifest.json` (built 2026-11-21T18:45:20Z): 19 of 19 SHA-256 equal; `calib05/values.py` delivered as the declared review copy.
- Rules given to the reviewer: no other path, no git, no network, no writing; report any contamination.
- The reviewer's use: 209,751 tokens, 14 tool calls, about 5.9 minutes; it counts apart from Codex's lines.
- The text below the line is the reviewer's report, unchanged.

---

# Blind review of the R2 bundle (v0.5.5), round 2

Scope: I read only `/home/claude/r2blind2/bundle/`. No git, no network, no writes. Code references are relative to `frozen-rules/src/refute/`. Numbers marked "my arithmetic" are design computations on no data.

## 0) Manifest check and contamination

**Manifest:** all 19 files match `MANIFEST.json` by SHA-256 (19 of 19). `calib05/values.py` matches its `delivered_sha256` (a review copy, as declared).

**Contamination:** I found no earlier count, forecast or result, and nothing that voids the review. Three soft leaks should be recorded:

| # | Where | Quote | Why it matters |
|---|---|---|---|
| 1 | `arguments.md:264` (with `:25`, `:27`) | "a new priced test for the eclipsing-binary families" | Lets a reader infer which target and families are open (D1 on EB; T3b "prepared apart"). No number, but it is direction-adjacent. |
| 2 | `targets.md:5` versus the sources | "the limits' values and every result are left out" | The delivered sources state the limits: `calib05/c1.py:649, 667-669, 682, 690, 700` and `calib05/values.py:27-28, 56, 69-70`. These are rules, not results; the sentence is simply inaccurate. |
| 3 | `arguments.md:195` | "the blind review found it unargued" | Reveals round-1 history (a dropped `odd_even` change). Not a result. |

The statement that B3.3 "turns some INCONCLUSIVEs into PASS" (`arguments.md:148-149`) is structural, not a leak.

## 1) Per-question review

| Question | Document's primary | Kind | Disguised relaxation? | My independent primary | Verdict on the document's primary |
|---|---|---|---|---|---|
| B1 | (a′): keep blocking, plus a report label | no rule change (label only) | No | (a′) | **SURVIVED** |
| B1 (e) | variant only | rule change, an open relaxation | Not disguised | variant only, or drop | n/a |
| B2 | (a) keep the alternative | no change | No | (a) | **SURVIVED** |
| B3.1 | keep the small-residual requirement | no change | No | keep | **SURVIVED** |
| B3.2 | Fréchet | no change | No | Fréchet | **SURVIVED** |
| B3.3 | evidence split, conditional on conditions 1-6 | rule change, monotone relaxation of one branch | Not disguised, but under-specified | keep the frozen branch decisive; split as a reported variant | **WEAKENED** (the conditions are not met, see section 3) |
| B4 / C5 | single-shot confirmation | procedure | No | same, with additions (section 5) | **WEAKENED** |

**B1.**
- The rule as described is the code: rules 1 to 5 at `core/verdict.py:251-276`.
- (a′) follows from principles 2 and 3 without reference to any outcome. (b) and (d) are rejected on semantics, which is correct. (c) is rightly dismissed: coverage is not power.
- (e) is honestly described as lowering the evidential requirement and as mixing three states under WEAKENED. It would change what WEAKENED asserts and directly feeds T2b's "retained" count (`calib05/c2.py:311-316`). Variant-only is the most it can be.
- One gap: "every test that can emit FATAL (by its definition)" is not a closed list. `secondary_eclipse` is WARNING for a candidate (`packs/tess/battery_v5.py:58`) but FATAL in the no-candidate path (`packs/tess/pipeline.py:217`). `period_alias` and `eb_catalog` are outcome-dependent (`packs/tess/battery.py:839-892`, `packs/tess/ebcatalog.py:236-353`). The freeze must enumerate the tests by name per battery version.
- The label "warning-only gaps" should also say whether a warning FAIL is present, and must never be summed into a headline count.

**B2.**
- Facts verified: FAIL rule at `packs/tess/battery_v51_diff.py:548`; independent draws at `:654-657`; measured correlation in the aperture and SAP blocks at `:304-320` and `:615-631`; "conventions" at `packs/tess/params.py:311`.
- (a) is the principled choice: no option singles out the background increment for a reason specific to it. Making (b) ineligible until coupling controls exist is correct.
- Not argued, and it should be said: whether independent draws are conservative or anti-conservative for the fraction criterion is unknown.

**B3.1 and B3.2.**
- Facts verified: versions 2 and 3 FAIL on the flag alone (`packs/tess/battery_v5.py:446`, `packs/tess/battery_v51.py:211`).
- The Fréchet bound is applied only when `can_fail` holds (`packs/tess/battery_v52.py:371`).
- The `min(p, q)` argument is correct, and the bound is a valid conservative choice.
- The hard-coded `3.0` is at `battery_v52.py:342`, against `ATTENUATION_SIGMAS` at `:338`.

**B3.3.** The reasoning is principled in form: a PASS that needs both the frozen power block and positive evidence is a stronger PASS than "not flagged". It is nevertheless a relaxation that can only add SURVIVED or WEAKENED verdicts. See section 3.

## 2) The decisive combination

- **Not yet single.** Section 6 states two combinations joined by "only if … else" (`arguments.md:194`). It becomes single only after this review. With my recommendation in section 3 it resolves to: B1 (a′), B2 (a), B3.1 keep, B3.2 Fréchet, B3.3 the frozen branch, `odd_even` unchanged.
- **That combination is behaviour-identical to the frozen battery** plus a report label. The confirmation would then be a re-test of the frozen rules on new draws. That is legitimate, and should be stated plainly in the freeze.
- **Protection against swapping is good in intent** (variants never replace it; single shot; a STOP is not a trade). Three gaps remain:
  1. **Code after the freeze is a second degree of freedom.** The order is "freeze commit, then code" (C2), and several definitions are open (the `D_r` components, VN details, the trinomial ordering). Implementation choices made after R3's numbers would act as a variant swap. A code-hash lock of the battery, the VN generator and the analysis script is needed before R3's first number, with any later change a new version.
  2. **Variants reported on the confirmation draws spend those draws.** State that a later promotion of any variant needs new draws.
  3. **The freeze list in C2 is incomplete.** It lacks: the trinomial ordering and algorithm, the FATAL-capable list, the exact `D_r` and `sigma_D` formulas, the full VN specification, the T2b rotation rule, and the seed derivations of the enlarged D1 paired sets (only VN's string is given; `refute-v05-c1` at `calib05/values.py:57` must be excluded).

## 3) B3.3 and VN

**Recommendation: B3.3 as a registered variant only. Not IN the decisive combination.** By the document's own clause (`arguments.md:175-177`), the frozen branch stays decisive. I do not accept conditions 2, 3 and 6 as written.

**Condition 2 (D's provenance): ambiguous.**
- `r` is the box contrast of the flux minus the whole joint model: per-sector offsets, tested harmonics and up to three extra frequencies (`battery_v52.py:235-255, 309-322`).
- "The flux before the sinusoid model is subtracted" has at least three readings: raw flux; flux minus offsets; flux minus offsets and extras. They differ materially when the extras absorb harmonics.
- `sigma_D` has no formula for any reading that involves a projection.
- The series is per-sector median-normalised raw flux (`:289-293`). The box baseline is every out-of-transit cadence of the whole curve, with uniform weights (`:248`), so `D_r` and `r` are both sensitive to anything the model does not fit.

**Condition 3 (the rule): a reference-depth loophole.**
- The FAIL side uses the candidate's depth D with no error (`battery_v52.py:330, 338-340`). The PASS side uses `D_r`. The two regions are not complements over one quantity.
- "A trend shared by both cannot inflate `r`" covers one direction only. A fitted sinusoid in anti-phase with the dip deflates `D_r` towards zero. The guard asks only that `D_r` be positive, so the threshold `f·(D_r + k·sigma_D)` becomes small and "shown large" becomes easy.
- Fix for the variant: require `r − k·sigma_r > f·max(D, D_r + k·sigma_D)`.
- In its favour: separate `k·sigma` margins are conservative under any correlation between `r` and `D_r`, since the standard deviation of `r − f·D_r` is at most `sigma_r + f·sigma_D`.

**Condition 4 (guards): adequate for the PASS.**
- Strictly positive, finite `sigma_r` and `sigma_D` close the degenerate cases. `beta` is at least 1 (`battery_v5.py:333-348`).
- When `can_fail` is false the block probability is zero (`battery_v52.py:371`), so "detectability" excludes those cases. The text should say so.
- The frozen ambiguous result carries no blocks (`:420-429`), so the new code must attach them or `enforce_sensitivity` refuses the PASS (`core/sensitivity.py:152-181`).
- Residual asymmetry, preserved by "FAIL unchanged": the frozen FAIL accepts `sigma_r = 0` (`:338` tests only finiteness).
- The error model is white noise times `beta`. A phase-locked, unmodelled structure is a mean shift, not noise, and no sigma covers it.

**Condition 5 (distinct record): sufficient**, if the status string and the four quantities are in the test's metrics and the transitions are tallied separately.

**Condition 6 (VN): not sufficient, on three counts.**
1. **VN sits almost inside the fitted model.**
   - The test fits P/2, P, 2P plus up to 3 extra frequencies up to 10 per day (`params.py:365-366`, `battery_v51.py:29`, `battery_v52.py:309-320`).
   - VN's highest frequency is 6/0.7 ≈ 8.6 per day. With the candidate at the variability period, harmonics 1 and 2 are tested and 3 to 5 can be taken as extras. Only harmonic 6 is left.
   - So `targets.md:52` ("content beyond the harmonics the `sinusoid` test fits") is only partly true.
   - VN will mostly produce a small `r` against `D_r`. It can pass the safeguard without probing the "shown large" region. The minimum of 100 ambiguous cases guarantees the branch is reached, not that the PASS boundary is.
2. **The riskiest populations are absent.**
   - A dip plus a phase-locked modulation: an eclipsing binary with ellipsoidal or synchronised-spot variation at P or P/2. There the flag itself is evidence of a binary, and the residual is large by construction, so "shown large" turns it into a PASS.
   - No synthetic family has this. VN has no transit. EB1 and EB2 are trapezoids (`calib05/c1.py:306-309`). PV deliberately avoids commensurate periods (`c1.py:251-254`).
   - Also missing: quasi-periodic (finite-coherence) variability, more components than the extras can take, and narrow periodic features with many harmonics.
3. **The specification is not reproducible as written.** Missing: the star model (sectors, red noise, trend: as `c1.py:167-192` or not), the total number of curves, the range and index set of `psi_k`, the sine or cosine and sign convention (it decides "steep rise" versus "steep decline"), the draw order, and the mapping from the seed string to a generator.

**Unmeasured harm:** see section 6 (T3b).

## 4) Non-inferiority and power

The intent is right: paired, one-sided, all families must pass (an intersection-union test, so no multiplicity inflation), STOP not trade. As written it is not yet well defined.

1. **The invalid-pair rule can make every reading NOT DECIDABLE.** "Not eligible" counts as invalid, and above 5 % invalid the reading is NOT DECIDABLE (`arguments.md:227-228`). Eligibility is passing the shared gate (`c1.py:600-609`). Any family whose gate pass rate is below 95 % is then never decidable, and for noise families that is expected by design. Fix: the paired population is the eligible curves; the 5 % rule covers only non-OK status; generation proceeds in index order to a frozen count of eligible pairs, with a frozen cap.
2. **T2b's paired reading is structurally NOT DECIDABLE.**
   - C2 has 100 stars (`values.py:64`), hence at most 100 pairs per group with one rotation per star, and fewer after the gate.
   - With zero discordant pairs, the one-sided 95 % upper bound on a rate exceeds 0.02 until n ≥ 149 (my arithmetic: `0.98^n ≤ 0.05`).
   - Under `arguments.md:244` a NOT DECIDABLE prevents adoption, so no change could ever be adopted, B3.3 included. The document defers this to a later computation; it is decidable now.
   - Options: enlarge the real set, or replace T2b's paired margin by an exact "no worsened pair" rule with its weaker meaning stated.
3. **For a monotone change the trinomial and the power statement are vacuous.**
   - B3.3 only turns a `sinusoid` INCONCLUSIVE into a PASS. A verdict retained under the old rule had no INCONCLUSIVE (`verdict.py:268-270`), so it is unchanged. Hence `p_better = 0` exactly and `d = p_worse`.
   - "Power at `d = 0`" then means zero discordance, which any n ≥ 149 satisfies.
   - The natural test is an exact binomial upper bound on `p_worse`. The power requirement should name the largest true `p_worse` at which adoption has 80 % probability.
   - The trinomial remains appropriate for two-directional variants.
4. **Ordering not specified.** "A pre-specified ordering" is promised, not given. It must be in the freeze, with the algorithm.
5. **The margin 0.02 is not justified on principle.** The text says only that it is frozen before any number.
   - It is absolute. Where a family's baseline SURVIVED rate is near zero, the allowed relative increase is unbounded.
   - It can pass while the data show a significant worsening. At about 1,550 pairs, roughly 20 net new spurious survivals could pass (my rough arithmetic).
   - It sits oddly beside D1's frozen "not above the earlier count" (`c1.py:649`), which allows zero net increase. The document does not say on which set that frozen rule applies in R3. If it applies to the paired set, the margin is moot; if only to the small set, the margin is the real rule.
   - Acceptable as a labelled convention if tied to something (for example a stated fraction of D1's limit) and paired with a point-estimate condition.
6. **Smaller points.**
   - T2b's "one rotation per star" needs a rule (which slot).
   - Per-reading power of 80 % across about 12 readings gives a low joint adoption probability in the worst case. It is conservative, but it should be stated so it is not "discovered" later.
   - It is not stated whether section 7 runs in R3, on the confirmation draws, or both.

## 5) Confirmation rule

Single shot, no redraw, no variant swap, "only PASS meets a target", and the population caveat stated in advance: sound, and the caveat is honest. Not yet sufficient:

- **Technical reruns are undefined.** Say what a crash or a data-fetch failure allows: byte-identical code and seeds, logged, approved before any count is read.
- **The draw is not pinned.** Freeze the drand round number before it is emitted, the selection scripts and sizes for C2' and C3', and the hash of the exclusion list.
- **Code-hash lock before the draw** (see section 2).
- **Where the mandatory safeguards are read** (R3 or confirmation) must be stated; `arguments.md:207-208` leaves it open.
- **C3' is small** (8 and 8 at `values.py:18-19`). A single shot there has little power either way; say so in advance.

## 6) Safeguards, order and dependencies

- **C1, C4, C7:** operational.
- **C2:** complete it with the list in section 2, item 3.
- **C3:** this bundle complied; see the soft leaks in section 0.
- **C5:** see section 5.
- **C6:** cannot be assessed (not in the bundle, correctly).
- **Build order:** with B3.3 as a variant it reduces to the report label. "No parameter is changed between steps" needs a companion rule for defect fixes after numbers (a new version, or an approved and logged rerun).
- **A target harmed and not measured: T3b.** B3.3 can only add SURVIVED verdicts. T3b counts known false positives SURVIVED with `sinusoid` decisive (`values.py:89-102`). T3b is absent from the B3.3 row (`arguments.md:255`), and also from the B3.2 and B2 (b) rows, which can likewise add PASSes. "Prepared apart" does not remove the dependency.
- **T2c** is audited but not in B3.3's adversarial column, although it counts SURVIVED (`c2.py:401-402`).
- **Relaxation by redesign:** the main residual route is post-freeze implementation freedom plus an under-specified VN. Both are closed by the code-hash lock and a complete VN specification.

## 7) Factual errors against the code

1. `targets.md:52`: the test also fits up to three extra frequencies (`params.py:365`, `battery_v52.py:309-320`). VN's content is not "beyond" the fit.
2. `arguments.md:153-154` and `targets.md:66-67`: "a flagged sinusoid without a small residual" does not describe the frozen branch. It also holds flagged cases with a small residual when coverage is invalid or FAIL is not allowed, and cases with non-finite `sigma_r` (`battery_v52.py:335, 338, 411, 420-429`). The guards exclude them; the description and VN's minimum count should be worded accordingly.
3. `targets.md:5`: limits are not left out of the bundle (section 0).
4. `arguments.md:241-243`: T2b's paired size is treated as an open computation. It is determinable now and negative at 100 stars (section 4, item 2).
5. Not an error, a precision: "the declared phase grid" is eight hard-coded phases (`battery_v5.py:476-477`).

Everything else I checked agrees with the sources:
- aggregation order, coverage and sensitivity rules, deferral;
- registry values: 0.95 default, 0.9 for `period_alias` (`power.py:41`);
- the background rule and block;
- the flag thresholds (`params.py:330, 332`);
- the V1 and V2 ranges (`c1.py:311-312`);
- the D1 to D5 and T2a to T2c rules.

## 8) Overall verdict

**WEAKENED** as a basis for freezing the arguments. The frame, B1, B2, B3.1, B3.2 and the single-shot principle hold. B3.3's conditions and section 7 do not yet.

**Blockers (must change before the freeze):**
1. Register B3.3 as a variant only; the frozen ambiguous branch stays decisive. State that the decisive combination is then behaviour-identical to the frozen battery.
2. Fix section 7's paired population and the invalid-pair rule.
3. Resolve T2b's paired reading: it is not decidable at 100 stars, which by the document's own rule blocks every adoption.
4. Freeze the test completely: the ordering and algorithm; the binomial form for monotone changes; a power statement at a named alternative.
5. Add a code-hash lock before R3's first number and before the confirmation draw, with a defect-fix rule.
6. Add T3b (and T2c) to the dependency rows of B3.3, B3.2 and B2 (b).
7. Enumerate the FATAL-capable tests by name for (a′) and (e).

**Needed before B3.3 could ever be promoted (not blocking the freeze if it is a variant):**
8. One exact definition of `D_r` and `sigma_D`, and the `max(D, D_r + k·sigma_D)` reference.
9. A VN that leaves the fitted span, plus an eclipse-with-phase-locked-modulation family, with a complete, reproducible specification.

**Nice to have:**
10. Justify or relabel the 0.02 margin; say on which set D1's "not above the earlier count" applies.
11. Pin the confirmation's draw, technical reruns and where safeguards are read.
12. Correct the wording in section 7, items 1 to 3; reword `arguments.md:264` to remove the soft leak.
13. State joint adoption power; state C3' low power in advance.

**Uncertainty:**
- I did not run any code. The claims about VN's residuals and the anti-phase `D_r` case are reasoned from the fit's structure, not measured.
- The search and detrending code is not in the bundle, so I cannot say how often VN reaches the gate or which alignment it finds.
- My sample-size figures are approximations, not the exact enumeration the document promises.

**Note for the main session:** nothing in this report came from memory; all facts are from the bundle.
