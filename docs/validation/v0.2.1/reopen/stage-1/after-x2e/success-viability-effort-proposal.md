# Scientific success, viability and the effort ceiling (proposal, not adopted)

The maintainer's decision after X2e, item 9, brought with the package of item 5, before any big lot
and before the pilot X5. **Nothing here replaces or loosens the ROADMAP's v0.2.1 exit criteria**
(the acceptance records; the synthetic population study with its rates and limits committed before
it runs; the dev/confirmation split with drand seeds; no regression; no threshold set on known or
real targets; the new pre-registered calibration; the explicit decision on failure; the reviewer
reports). The objectives below are **in addition**, for the maintainer's decision **before the data
that judge them**; every number is a proposal.

## 1. Joint objectives (proposed; distinct from the approved criteria)

Each objective is a rate over targets (spec B's unit), per group (white and AR(1), without and with
variability) and per regime in scope, with its 95% bound by the method the study's declaration fixes;
all must hold together for the configuration to count as useful.

| # | Objective | Proposed number | Why this number |
|---|---|---|---|
| O1 | **True planets preserved**: injected-planet targets that end refuted (a false FAIL of the target) | ≤ 5%, upper bound ≤ 8% | a falsification tool that kills real planets is not usable; 5% matches a conventional error level |
| O2 | **False positives recognized**: injected eclipsing-binary and blend targets that end refuted or flagged | ≥ 80%, lower bound ≥ 70% | the gauntlet's purpose: below that, more than one false positive in five passes |
| O3 | **Spurious signals approved on curves without a planet** (white and correlated noise, apart): targets whose signal survives | ≤ 1%, upper bound ≤ 2% | the safety objective; the strictest |
| O4 | **Useful fraction of conclusive results**: targets in scope with a conclusive verdict that is correct | ≥ 10% of the targets in scope | below this, fewer than one target in ten gets a correct conclusive answer (whether from INCONCLUSIVE or from wrong conclusive verdicts) |
| O5 | **Processing cost**: logical-processor seconds per curve at the default workers, and the main study within the ceiling of section 2 | ≤ 60 LP-s per curve | X2's variability cells cost 61.6, X2e's cells 18.2 |

**The risk, stated before any data:** O4 is far from the development evidence. In the R_min study
the smallest decided yield was 0.64% (41 decided of 6400 disappearing targets in
`white, variability`; [../experiments-plan.md](../experiments-plan.md)), with the old gates and
without spec B. The corrected gates and spec B change that yield, in a direction not known; the
pilot measures it.

## 2. The cumulative effort ceiling up to X6

Logical-processor hours (LP-h: one worker on one logical processor for one hour) are kept apart from
wall time.

**Consumed so far (compiled from the run reports):**

| Lot | LP-h | Wall |
|---|---|---|
| R_min study (76 800 curves, 6 workers) | about 271 | 45.24 h |
| X2 (8000 curves, 22 workers) | about 89 | 4.03 h |
| X2e (4000 curves, 22 workers) | about 20 | 0.92 h |
| **Compiled** | **about 380** | **about 50.2 h** |

Not yet compiled (to be added from their run reports before the ceiling is approved): the bs-choice
lot, the timing lot, the development campaigns, X0c, X1b's controls and the CI's jobs.

**Remaining, estimated** (ranges because the cost per curve of the corrected engine is not
measured: 12.7 LP-s per curve in the R_min study, 18.2 and 61.6 in X2e and X2):

| Step | Size | LP-h |
|---|---|---|
| Spec C's choice lot (item 5) | option B, C or A | 195, 292 or 430 |
| Spec C's confirmation lot | as the choice lot | 195 to 430 |
| X3 (b/s calibration) | about 2600 curves | 9 to 45 |
| X4 | arithmetic | 0 |
| X5 (pilot) | 56 400 to 114 000 curves | 199 to 1950 |
| X6 (main study) | from the pilot; at the scale of 200 000 curves | 706 to 3420 |

**Proposed ceiling up to X6 (X7 and T4 apart):** **4000 LP-h and 200 h of wall time**, cumulative,
including what was consumed; whichever is reached first stops the attempt at the next check. The
high ends above add to more than the ceiling; that is the point of the viability check, not an
accident.

## 3. The viability check (before the package, before X5 and before X6)

Run as arithmetic on declared numbers, committed before the step it gates:

1. **Mathematical compatibility of the criteria:** every filter of every criterion has a non-empty
   window at each number of years (X4); and every objective can be shown at the planned size. For
   example, a one-sided, pointwise 95% binomial upper bound of 2% on O3 with no event needs at least
   149 independent targets per group (`ln 0.05 / ln 0.98`), and of 1% at least 299; with events, or
   with a correction for several groups, more.
2. **Coverage by regime:** each regime in scope reaches its minimum with probability at least 0.9
   at the planned size, from the rates measured; a regime that cannot is declared out of scope
   before the data, or the size grows by a new decision.
3. **The errors of the final aggregation:** a target's verdict aggregates its rounds (spec B), so a
   round-level rate is not a target-level rate; the check bounds the target-level false PASS and
   false FAIL from the round-level bounds and the rounds per target, and the objectives are judged
   at the target level.
4. **Budget:** the consumed LP-h plus the remaining estimate at its high end within the ceiling; if
   not, the outcome below.

## 4. The possible outcomes of a check

- **Continue:** every item holds.
- **Propose an explicit scope reduction:** the regimes or groups that fail are named, the validated
  population and where results stay INCONCLUSIVE are published exactly (the scope rule of
  [../experiments-plan.md](../experiments-plan.md)); this is not the validation of the original
  four-group claim, and it needs the maintainer's decision.
- **End the attempt without approval:** v0.2.1 stays not passed, the result is recorded as such.

**No outcome authorizes a new attempt automatically.** Opening Discover (v0.4) without meeting the
v0.2.1 gate depends on a future explicit decision and an exception recorded in the ROADMAP; nothing
here authorizes it.

## 5. The ideas issue

The draft of an ideas issue on eclipsing binaries and variability as results of their own is in
[ideas-issue-eb-variability-draft.md](ideas-issue-eb-variability-draft.md); it opens no
implementation front.
