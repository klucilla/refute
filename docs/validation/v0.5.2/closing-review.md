# The independent review of the v0.5.2 closing record

The maintainer's decision of 2026-11-10, third set (#216, item 2 (c)): one independent review session (a new Claude Opus session, read only, the record and its annexes only, at most 350,000 tokens) with the question "are the targets D2 and T2a reachable by a battery that only passes with evidence, and what should round 3 try?". The report enters as it came out.

- Session: a Claude Code subagent of type Explore (no write or edit tools), model Opus, launched on 2026-11-10 after commit `2f9e410` (the record as reviewed). Its brief is in the session; it listed the files below the record it could read, forbade writing, the network, git and Python, and set the 350,000-token limit.
- Tokens: 203,057, as counted by the session tool (the reviewer's own estimate, at the end of its report, is about 130,000); 47 tool calls; 10 minutes 39 seconds.
- The reviewer disclosed one read-only `ls`/`wc` call and one file read outside its list (`a0_v4.py`, lines 140 to 190), on which it says nothing relies.
- **A scope deviation:** the brief expanded the permitted corpus beyond the maintainer's "the record and its annexes only" to six source files (`core/verdict.py`, `core/sensitivity.py`, `packs/tess/battery_v51_diff.py`, `a0.py`, `battery_v52.py`, `params.py`), so that the reviewer could check claims about the rules.
- The report below was transcribed from the session's hand-back message (the harness indents each line; the indentation was removed), not copied from a file.

The report, unchanged:

---

# Review of the v0.5.2 closing record (D2 and T2a)

**Scope disclosure.** I made one read-only Bash `ls`/`wc` call on `stage2\`. One grep across the directory also returned `a0_v4.py` lines 140–190, which are not on the list; nothing below relies on them. I wrote no files.

**Not checked:** the adequacy figures, the budget and CPU-h ledger, the commits, and stage 1's E1 and E2.

## 1. Verdict on the record: **WEAKENED**

The record reports its results faithfully and never overstates success. The numbers I reconciled match the annexes:
- **D2:** 0.964, 0.839 and 0.723; the minimum 0.8643.
- **T2a:** 0.3126 (= 302/615·11/40 + 257/615·17/40); the minimum 0.89675.
- **What-ifs:** 0.50/0.59, 0.69–0.78, 0.62–0.71, 0.91–1.00, upper bound 0.9008, and the +0.31/+0.19/+0.60 recoveries.
- **Background figures:** 0.41 median, the 0.17 requirement, the 2.4× and 29× factors.
- **Blocker sets:** they sum to 51.

The verdict is WEAKENED, not SURVIVED, for four reasons:
- **The sinusoid's power is misdescribed** (`closing-record.md` lines 104, 142, 158–159). The record calls it "undetermined". The decision-relevant fact is in fact settled for all 15 T2a losses:
  - `battery_v52.py:371` reports max(0, p + small − 1), and the true joint power is at most min(p, small).
  - In 9 losses the three harmonic blocks are identical (0.492 to 0.945; `forecast-t2a-diagnosis.json`, for example lines 887–901 and 1169–1183). That means p ≈ 1, so the reported value equals the `small` marginal, an upper bound, and it is below 0.95.
  - In the other 6, a zero at some harmonic means p + small ≤ 1, so the power is at most 0.5.
  - So none of the 15 is a looseness of the Fréchet bound. The binding term is mostly `small`: the residual box error σ_r must be at most about 0.108 of the depth (ATTENUATION 0.5 and 3σ, lines 36–37, 341–345).
- **A directly relevant stage 1 result is left out** (line 142). `stage1/README.md:79` says that in E3's SNR 12, correlated-trend cell, 0 of 150 planets had every harmonic detectable.
- **The annex asserts a cause the record says is undiagnosed.** Record line 101 says the `group_variance` branch was not diagnosed. `forecast_t2a_diagnosis_reading.py` (lines 11–13 and 45) nonetheless writes "MIN_PAIRS" as the cause. Its line 93 then counts the 6 `odd_even` label defects by matching that same inserted string.
- **"Data present" for class (d) is not established** (line 101). Four of the 9 grid refusals have "0 sector(s) contribute measured events" (diagnosis lines 81, 562, 953 and 1276).

## 2. D2: reachable by an evidence-only battery? **Undetermined; if reachable, only on a thin margin.**

The target needs 97 of 112 planets kept.
- v4 keeps 81: 80 of v0.4's 108 plus 1 planet v0.4 did not keep.
- Removing every non-sinusoid blocker gives at most 108 − 13 + 1 = **96**, short of 97 (it could go higher only if some planets v0.4 lost were gained).
- **So D2 is unreachable unless the sinusoid's INCONCLUSIVEs are resolved.**

Per blocking test:
- **`odd_even` (23 losses):**
  - On the 17 sensitivity conversions, A0's error is 1.49× the Cramér-Rao (CR) bound.
  - The conditional linear box (`sigma_box_true`) would recover 7 of them; the CR bound would recover 16.
  - Scenario c (`odd_even` where the bound supports it, plus the sinusoid) gives 99, which leaves 2 planets of slack. The estimator therefore has to recover about 14 of those 16, i.e. come close to the CR bound. That is clearly better than the linear box, which is 1.33× CR, and E2 found no candidate that qualifies.
  - The other 6 `odd_even` losses (5 `insufficient_sensitivity`, 1 outside the grid) are probably A0 refusals, as they turned out to be on T2a. The CR diagnosis does not cover them.
- **Sinusoid (13 losses):** not diagnosed on D2; 12 of the 13 have no class in `forecast-v4-losses.json`. Undetermined.
- **`aperture_depth` (9) and `systematics` (6):** not diagnosed. If they are A0 refusals, fixing them is the other route to more slack: scenario d reaches 111.

## 3. T2a: reachable by an evidence-only battery? **Undetermined; unlikely with the present tests and their declared minimum effects (the alternatives each power check must detect).**

**The arithmetic is harsh.** Version 4 refuses hosts above 20 sectors, 56 of 615 (0.091) of the population. With that refusal, the battery must keep at least **552 of the remaining 559 injections (0.987)**. That is v0.4's own in-sample rate (79 of 80). Otherwise the stratum above 20 has to be measured and kept at about 0.90. Removing every (d) refusal and every background blocker still leaves 0.69–0.78. The 19 sample losses that remain carry the sinusoid (15), `odd_even` (b) (4) and `period_alias` (2). **T2a needs essentially every blocker class resolved at once.**

Per blocking test:
- **`systematics` background sub-check (23 losses):**
  - The background error must shrink by more than 2× in 17 of the 23, by more than 3× in 7, and by up to 29×.
  - The weighted incidence of these losses (0.26) exceeds the available slack. If their errors are near an information floor, T2a fails under this declared minimum effect.
  - **An anomaly the record notes but does not pursue:** the background-rise error is far larger than the SAP depth's own error. It is about 8× at the median and about 46× for the SNR-36 case (1.28 of the depth). This assumes SNR ≈ depth/σ.
  - Measurement noise in SAP_BKG should also appear in SAP. So the excess is either scattered-light variability that cancels in SAP, or a normalization or units issue. From the listed files I could not check that SAP_BKG and SAP_FLUX share units.
  - Either way, this points to the statistic rather than to missing information. Undetermined.
- **Sinusoid (15 losses):** every one is genuinely below 0.95 (section 1).
  - For any box estimator, σ_r is at least roughly depth/SNR (a white-noise approximation). Requiring σ_r ≤ 0.108·D therefore sets an implicit floor of about SNR 9.3.
  - Some recovered injections lie near that floor (for example SNR 9.4 in the reading file).
  - The present σ_r uses uniform in/out weights times β (lines 248–255), so it is not efficient.
  - Information-limited for low-SNR injections, estimator-limited above that. Undetermined.
- **(d) refusals (25 `systematics`, 12 `odd_even`) and the stratum above 20:** procedural refusals. Fixing them means extending and recalibrating A0's domain, which is unpriced.
- **`odd_even` (b) (4 losses, 0.79–0.93) and `period_alias` (b) (2 losses, 0.898 and 0.207):** small, but not removable.

## 4. What round 3 should try, in priority order

1. **Compute bounds before building any estimator** (low CPU; the record prices the background bound at about 2–10 CPU-h). On T2a's 80 injections and D2's 112 planets, compute for each power-gated statistic a per-injection lower bound on its error:
   - for the background: its white-noise floor;
   - for the sinusoid: the σ_r of the linear model with β = 1, inverse-variance weights and a matched box;
   - for `odd_even`: the CR bound already in hand.

   Then compute the maximum retention those bounds imply, with its sampling interval.
   - **Shows it worked:** a bound that sits above or below 0.897 and 0.864 decides whether estimator work can succeed.
   - **Shows it failed:** bounds that cannot be mapped to the population.
   - If the bound falls below a minimum, that is the material for an infeasibility record, which is the maintainer's call.
2. **Audit the background statistic** (zero CPU). Check SAP_BKG against SAP_FLUX units and normalization, and compare the background-rise error with the SAP depth error and with the background's white-noise floor on the 23 losses.
   - **Worked:** the ratio is explained, either by a defect (class c) or by scattered light that a model can absorb.
   - **Failed:** the error sits at its floor.
3. **Diagnose the A0 refusals** (cheap). Find which `group_variance` branch returns none (MIN_PAIRS or a covariance that is not positive semi-definite) in the 21 such cases, and the 0-sector against 1-sector grid cases. Then decide whether a calibrated domain extension is worth pricing.
   - **Worked:** each of the 37 (d) blockers has a named, fixable cause.
4. **Measure the stratum above 20** on a sample, using smaller batches or a cheaper path. Without it, T2a's slack is about 7 injections.
   - **Worked:** a kept-fraction estimate with an interval for that stratum.
5. **Only if step 1 leaves room:**
   - a more efficient sinusoid box estimator, frozen and recalibrated in E3's cells. Measure σ_r against its bound and the false-failure rate.
   - a near-CR `odd_even` estimator. D2 needs about 14 of the 16 conversions recovered.

**Do not try:**
- tightening the sinusoid's Fréchet bound, which rescues none of the 15;
- estimator development before the bounds exist;
- pricing a full acceptance before a passing forecast.

**Where a requirement and the data seem to conflict** (for the maintainer; I am not proposing a change):
- v0.4, the baseline, had no sinusoid test, so every sinusoid INCONCLUSIVE is a loss that baseline never carried.
- A 3σ rule combined with power 0.95 against an effect comparable to the depth implies an SNR floor that near-threshold injections may not meet with any estimator.
- A warning test's INCONCLUSIVE blocks the verdict (lesson 3, confirmed in `verdict.py`, where rule 3 comes before rule 4).

## 5. Errors or gaps in the record

- **`closing-record.md` lines 104, 142, 158–159:** the sinusoid power is called "undetermined" although every one of the 15 is below 0.95, as shown in section 1.
- **Line 142:** omits `stage1/README.md:79` (0 of 150 planets with every harmonic detectable at SNR 12 in correlated trend).
- **Line 101 against `forecast_t2a_diagnosis_reading.py` lines 11–13, 45 and 93:** the annex asserts MIN_PAIRS and counts the label defects by matching its own inserted string.
- **Lines 100–101:** class (d) is called "data present", but 4 refusals have 0 contributing sectors.
- **Lines 154–157:** the `odd_even` evidence covers 17 of the 23 D2 losses. The 5 `insufficient_sensitivity` cases may be A0 refusals, and the record draws that analogy only for `aperture_depth` and `systematics`.
- **Lines 136 and 166–177:** the 552/559 (0.987) in-domain requirement is never stated outright.
- **Line 110:** the background error far exceeding the SAP depth error is noted, but its implication (a statistic or units issue, rather than missing information) is not drawn.
- **Line 150 and `forecast-v4-losses.json`:** 12 of D2's 13 sinusoid INCONCLUSIVEs carry no class.

Estimated tokens used: about 130,000 (input and output across all tool calls).
