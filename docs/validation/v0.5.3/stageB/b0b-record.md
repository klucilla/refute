# v0.5.3 stage B, B0b: D1's infeasibility test, as it came out

**The result: (N), the criterion is not met.** Under the maintainer's decision of 2026-11-11 (#217,
comment 6804003610, item 2 (d)), B0b is recorded and the work goes on. D1 for EB1 and EB2 stays
pending, with no new route in this round. No draft infeasibility record is written, and nothing is
declared infeasible. `method_status: not_validated`.

The design, the criterion and the script were fixed and committed in `98fa3c7` before the
measurement ([`v0.5.3-stageB0b-design.md`](../../../plans/v0.5.3-stageB0b-design.md), reviewed by
Codex: `WEAKENED`, then `SURVIVED`). The output is [`d1-infeasibility.json`](d1-infeasibility.json),
with fingerprint `584a56d8f50283fe` and 0 errors.

## The measurement

B0's bound (v0.5.1's oracle, B0's assumptions) on 800 new development binaries, seeds
`refute-v053-b0b:<family>:<i>`, checked disjoint from B0's.

| | EB1 | EB2 |
|---|---|---|
| attempted (generation failures) | 400 (1) | 400 (1) |
| eligible (folded) | 391 (288) | 357 (333) |
| C1' projection `n'`, D1's allowance | 196, 11 | 178, 9 |

The expected non-rejected binaries at `n'` and the median cohort's probability of meeting the
allowance (2,000 bootstrap cohorts, seed 20261112):

| Star, level | EB1 expected | EB1 median probability | EB2 expected | EB2 median probability |
|---|---|---|---|---|
| catalog, 0.0027 | 26.4 | 0.000 | 36.1 | 0.000 |
| **catalog, 0.05** | **12.0** | **0.452** | **13.1** | **0.102** |
| star known, 0.0027 (information) | 9.3 | 0.915 | 12.9 | 0.077 |
| star known, 0.05 (information) | 4.2 | 1.000 | 4.0 | 0.999 |

## The criterion, read as fixed

For each family, with the catalog star, both levels must give an expected count above the
allowance and a median probability below 0.05.

| | 0.0027 | 0.05 |
|---|---|---|
| EB1 | met (26.4 > 11; 0.000) | **not met**: 12.0 > 11, but the probability is 0.452 |
| EB2 | met (36.1 > 9; 0.000) | **not met**: 13.1 > 9, but the probability is 0.102 |

At the project's level, 0.0027, the oracle's optimistic bound leaves about two and a half (EB1)
and four (EB2) times D1's allowance, with extremely small median probabilities of meeting it
(3.3 x 10^-8 and 1.9 x 10^-14; the tables' 0.000 is rounding). At the permissive level 0.05, 12.0
and 13.1 are the oracle's optimistic bounds on the expected counts, still above the allowance,
and 0.452 and 0.102 are the median probabilities of meeting the allowance under that bound. Both
are conditional on B0's assumptions and do not show what a route can attain. The criterion
required both levels, against a false infeasibility conclusion, so it is not met. Whether such a
test exists, or whether a 5 % false failure of planets would be acceptable, is not decided here.

**Compared with B0:** B0, on other seeds, gave 0.077 (EB1) and 0.247 (EB2) at the catalog star and
0.05. Neither B0 nor B0b has a probability below 0.05 at that level, for either family. The
families' order is reversed between the two seed sets, which illustrates the sensitivity to the
development seed set, without quantifying it.

## Consumption

- CPU: the run took 2.451 CPU-h (`b0_infeasibility`, of a strict cap of 5.45, so at most 6
  with the overshoot). The smoke took 0.002 and the summary 0.006. B0 in all has used 4.92 of its
  30 CPU-h.
- Review tokens (Codex, uncached input plus output): the design review 109,572 and this record's
  end review 105,745. B0 in all has used 489,509 of its 1.5 M.
