# Scientific success, viability and the effort ceiling (proposal, revision 2; not adopted)

Revision 2, after the maintainer's decisions of 2026-10-22 on the delivery `0abc6de` (items 3 and
4): the objectives are not accepted as a block and are restated by class and regime; the ceiling of
4000 LP-h and 200 h is an **investment limit to discuss, not a sufficient budget**. Revision 1 is in
git history (`0abc6de`); its O3 (an upper bound of 2% on false alarms) was looser than the approved
C4 for white noise (1%) and is withdrawn.

**The approved criteria stay as they are.** The v0.2.1 population study's criteria
([../../../population-study.md](../../../population-study.md), section 1, approved on 2026-10-11)
are unchanged: C1 refuted planets, upper bound ≤ 0.10 per band and noise model; C2 flagged false
positives (REFUTED without `eb_catalog`, with signal identity), lower bound ≥ 0.60 in the measurable
band per noise model; C3 INCONCLUSIVE, upper bound ≤ 0.20 per class in the measurable band per noise
model; C4 false alarms (SURVIVED or WEAKENED) on the curves without a transit, upper bound ≤ 0.01
(white) and ≤ 0.05 (correlated), on the defined mixture; C5 H9(a) zero; C6 analysis errors kept in
the denominators, published apart, and blocking the confirmation's approval while any is
unresolved. C1 to C4 use a one-sided 95% exact Clopper-Pearson bound; C5 is a zero-event requirement
and C6 a blocker, neither probabilistic. Each is judged **individually** (per criterion and set; the
study states that 80% per criterion is not 80% for the study). **Nothing below
replaces or loosens any of them**: each objective either is one of them, unchanged, or adds a set or
a quantity; a number below never applies where an approved number is stricter.

## 1. The objectives by class and regime (proposed for the maintainer's decision, before the data)

**The sets.** Classes: planets, false positives, curves without a transit. Per noise model (white,
correlated) and SNR band (below, near, measurable; `population-study.md`, section 3), and for
planets by **layout regime**: two observing years (`two_years`, `few_train`), three
(`three_years`), with variability (`variability_some_years`); for false positives by mechanism
(`eb_secondary`, `eb_odd_even`, `blend`, `variability_masked`); for curves without a transit by
mechanism (`pure_noise`, `trend`, `trend_variability`). **No case leaves a denominator** (an
INCONCLUSIVE, an unfound period or an error stays in it), as in the approved criteria.

| # | Objective | Numerator (what counts as a success, or as the error) | Denominator | Rule | Limit | Status |
|---|---|---|---|---|---|---|
| G1 | **Planets with a signal preserved as candidates** (the capacity to deliver planets) | planets whose final verdict is SURVIVED or WEAKENED **and** that satisfy signal identity (C2's rule: `f` in {1, 2, 1/2}, relative period difference ≤ 0.001) | every planet of the set | one-sided 95% Clopper-Pearson lower bound | ≥ **0.60** in the measurable band, per noise model and per layout regime; the near and below bands published without a limit | **new** (no approved criterion measures it) |
| G2 | **Planets refuted unduly** | planets whose final verdict is REFUTED | every planet of the set | upper bound | C1 unchanged (≤ 0.10 per band and noise model); **added:** the same ≤ 0.10 per layout regime in the measurable band | C1 approved; the per-regime sets new and stricter |
| G3 | **False positives correctly recognized** | C2's numerator unchanged (REFUTED recomputed without `eb_catalog`, with signal identity) | every measurable false positive of the noise model | lower bound | C2 unchanged (≥ 0.60); **added:** published per mechanism, no limit | C2 approved |
| G4 | **False-alarm control on curves without a transit** (absent signals not approved) | the error: curves whose final verdict is SURVIVED or WEAKENED (C4's numerator); **published apart, no limit:** REFUTED (the absent signal correctly rejected) and INCONCLUSIVE | every curve of the "no injected transit" group of the noise model | upper bound on the false-alarm rate | C4 unchanged (≤ 0.01 white, ≤ 0.05 correlated, on the mixture); **added:** published per mechanism, no limit | C4 approved |
| G5 | **INCONCLUSIVE** | cases whose final verdict is INCONCLUSIVE, analysis errors included | every case of the class in the measurable band of the noise model | upper bound | C3 unchanged (≤ 0.20 per class); **added:** published per layout regime (planets) and per mechanism (false positives), no limit | C3 approved |
| G6 | **Processing cost** | logical-processor seconds per light curve | the curves of the run | measured | see section 2 | **new**, a budget objective |

- **C5 and C6 apply unchanged** beside G1 to G5 (C6: an unresolved analysis error blocks the
  confirmation's approval).
- **Individual, not simultaneous.** Each limit is judged on its own set with its own 95% bound, as
  the approved criteria are; no family-wise guarantee is claimed. The alternative, for the new sets
  only, is a simultaneous rule (for example Bonferroni over the `k` new sets: each bound at
  `1 − 0.05/k`); it is stricter and needs larger sets; it is the maintainer's choice.
- **G1's number** is a proposal: in the measurable band, C1 (≤ 0.10 refuted) and C3 (≤ 0.20
  INCONCLUSIVE) together leave room for about 0.70 delivered at the point level, over the band; G1
  adds signal identity and the per-regime split, and its lower bound 0.60 asks less than that point
  value on purpose, since the bound is conservative. It does not loosen C1 or C3, which still apply.
- **What the per-regime sets need:** the population puts, per band and noise model, 150 two-year
  planets, 50 three-year and 50 with variability. With 50, an upper bound ≤ 0.10 passes only with at
  most 1 REFUTED (Clopper-Pearson: 1 of 50 gives 0.091, 2 give 0.121), and a lower bound ≥ 0.60
  needs at least 37 of 50. The viability check (section 4) decides, before X5, whether the per-regime
  limits are kept, the sets enlarged in X6, or the limits replaced by publication only.

## 2. Which run measures the cost (G6)

- **The 61.6 and 18.2 LP-s per curve are diagnostic runs**: X2's and X2e's calibration measurement
  with the noiseless twin and every capacity decision recorded and not enforced. The 12.7 is the R_min
  study (the configuration of 2026-10-19, 6 workers). **None measures the final configuration.**
- **G6 is measured on X5**, the pilot, with the final frozen configuration (the corrected gates,
  spec B's aggregation, the full gauntlet), on processors 8 to 31 with 22 workers: its run report's
  elapsed time × workers / curves. Until then, every projection uses the range 12.7 to 61.6.
- **G6's limit:** the cost per curve measured on X5, times X6's size, fits the remaining ceiling
  (section 3); there is no separate number per curve.

## 3. The effort: what counts, what was consumed, what remains

**What counts toward the ceiling.** (a) Every lot and study of this attempt, from the R_min study's
bs-choice lot (2026-10-19) on, in logical-processor hours (LP-h: one worker on one logical processor
for one hour) and in wall time, from their run reports. (b) From now on, the local full suites and
sabotage runs, recorded per round from their JUnit time × the 24 logical processors they may use (an
upper bound). (c) **The CI apart**, in job-hours on GitHub's runners (not the maintainer's machine),
with its own cap. **Outside:** the v0.2.1 work before 2026-10-19 (the population study's development,
self-tests and D6, partly recorded; listed below), the agents' sessions (Claude, Codex), the
maintainer's time, **X7** (the reserve) and **T4** (map Amendment 28).

**Consumed (2026-10-19 to 2026-10-22):**

| Item | LP-h | Wall | Source |
|---|---|---|---|
| R_min study (76 800 curves, 6 workers) | 271.5 | 45.24 h | its run report (`elapsed_hours` 45.243) |
| bs-choice lot (100 targets) | ≤ 6.0 | ≤ 0.99 h | no elapsed recorded; bounded by its start (13:30 UTC) and the study's start (14:29 UTC) on the same 6 processors (0.985 h, 5.91 LP-h, rounded up) |
| X2 (8000 curves, 22 workers) | 88.6 | 4.03 h | its run report (4.026) |
| X2e (4000 curves, 22 workers) | 20.2 | 0.92 h | its run report (0.917) |
| **Lots, total** | **≤ 386.2** | **≤ 51.2 h** | |
| Local full suites and sabotages | partly recorded | | the JUnit files still kept in `.cache` add to 2860 s, at most 19.1 LP-h at 24 processors (Codex's count); the earlier ones were not kept; one full suite now takes about 41 min (2453 s), at most 16.4 LP-h; from now on, (b) above |
| **CI** (56 runs since 2026-10-19) | **167.1 job-hours** | | [ci-minutes.json](ci-minutes.json) ([scripts/ci_minutes.py](scripts/ci_minutes.py)), from the run metadata |
| Before 2026-10-19 (outside) | not counted | | D6 1456 s (`population/d6/`), the self-tests' per-process times, the dev population's generation (`population/manifest-dev.README.md`); the rest not recorded |

**Remaining, estimated** (LP-h; ranges where the final configuration's cost is not measured):

| Step | Size | LP-h | Wall on 22 workers |
|---|---|---|---|
| X2f, spec C's choice ([x2f-declaration.md](x2f-declaration.md)) | 63 000 curves | 427 | 19.4 h |
| Spec C's confirmation | as X2f | 427 | 19.4 h |
| X3 | about 2600 curves | 9 to 45 | 0.4 to 2.0 h |
| X5 (pilot) | 56 400 to 114 000 curves | 199 to 1950 | 9 to 89 h |
| X6 (main study) | from the pilot; 200 000 curves for scale | 706 to 3420 | 32 to 155 h |
| **Total remaining** | | **1768 to 6269** | **80 to 285 h** |

With the consumed lots (≤ 386 LP-h), the whole path is **2154 to 6655 LP-h** and **131 to 336 h** of
wall time (the maintainer's sum, 6655, with the revised X2f size); these figures **leave out** the
local suites and sabotages (recorded only in part: at most 19.1 LP-h by the 24-processor proxy for
the JUnit files kept, an accounting proxy rather than a measured consumption) and the work before
2026-10-19, so they are incomplete projections, not complete totals. At their ceilings rather than their estimates,
X2f and its confirmation would take 641 LP-h each (29.15 h × 22). **The high end exceeds 4000 LP-h and
200 h**: under the viability rule as written (the high end within the ceiling), the plan is **not
viable today**. The ceiling never rises automatically after an unfavourable result.

## 4. Reconciling the ceiling with the viability rule (the maintainer's choice)

| | Reconciliation | What it means |
|---|---|---|
| R1 | **Keep 4000 LP-h and 200 h, and amend the viability rule** (an explicit amendment, not a way of meeting the rule as written): instead of the whole path's high end, each gate checks the consumed plus the steps up to the **next** gate at their ceilings, plus the later steps at the best cost known then. Before X2f: 386 + 641 (X2f at its ceilings) + 641 (the confirmation) + 45 (X3's high end) + the suites' proxy, about 1730 LP-h, within; plus the later steps at the best cost known now (X5 1950 and X6 3420 at 61.6 LP-s per curve, the only measurement), about 7100 LP-h, **not within**: so under R1 the gate before X2f funds X2f, its confirmation and X3 and states that X5 and X6 are not affordable at today's best known cost, which only X5's own measurement or a scope decision can change. Before X5: X5's own declaration fixes its size so that X5 at its ceiling, plus X6 projected at the highest cost per curve measured by then on the final configuration's nearest run (61.6 LP-s per curve if none is closer), fit what is left; before X6, X6's size is bounded by X5's measured cost. If a gate cannot fit, the outcome is a scope reduction or the end (section 5), decided there | the plan is funded only conditionally: the path to X6 is not funded at its high end today; this is an amendment of the rule, stated now, before any result |
| R2 | **Set a higher ceiling now**, before any result: at least 6700 LP-h and 340 h | it covers the high end of the scale estimate used here (200 000 curves for X6), not an established maximum size of X6, and not the local suites' cost; a larger investment |
| R3 | **Reduce the scope now**, before any result: for example X5 at 4700 targets per group (the low size) and X6 limited to the groups that the pilot can size within 4000 | the four-group claim may not be validated; the scope rule of [../experiments-plan.md](../experiments-plan.md) applies |

Proposed: **R1**, as an explicit amendment of the viability rule, with its condition stated in every
gate's record. Any choice is fixed before the
next lot; none is revisited after a result.

**The CI's cap (proposed):** 600 job-hours from 2026-10-19 to X6, the 15-minute job target of the
ROADMAP unchanged; a cap reached stops pushes that run the full matrix, for the maintainer's
decision.

## 5. The viability check and its outcomes

Before X2f, before X5 and before X6, as arithmetic on declared numbers, committed before the step:

1. **The criteria's compatibility:** every filter of every criterion non-empty at each number of
   years (X4); every limit of section 1 attainable at the planned size (for example, an upper bound
   ≤ 0.01 with no event needs at least 299 independent curves, ≤ 0.10 at least 29).
2. **Coverage by regime:** each regime in scope reaches its minimum with probability at least 0.9
   at the planned size, the rates' uncertainty included (as X2f's sizing does).
3. **The final aggregation's errors:** the target-level false PASS and false FAIL bounded from the
   round-level rates and the rounds per target (spec B), the objectives judged at the target level.
4. **Budget:** section 4's rule, as chosen.

**Outcomes:** continue; propose an explicit scope reduction (the validated population and where
results stay INCONCLUSIVE published exactly; not the four-group claim; the maintainer's decision);
or end the attempt without approval (v0.2.1 stays not passed). **No outcome authorizes a new attempt
automatically.** Opening Discover (v0.4) without meeting the v0.2.1 gate depends on a future
explicit decision and an exception recorded in the ROADMAP; nothing here authorizes it.

## 6. The stage's milestone (the maintainer's decision of 2026-10-22, item 7)

Show, on independent data, that the final configuration preserves a useful fraction of true planets
as candidates, recognizes false positives and keeps its errors controlled (G1 to G5 with the approved
criteria). Spec C can correct a capacity barrier; it does not by itself resolve the attenuation in
the processing, the identity of the candidates or the aggregation, each with its own front.
