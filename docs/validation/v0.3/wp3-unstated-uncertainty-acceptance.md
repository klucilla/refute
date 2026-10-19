# WP3 addendum: a published deviation whose kind the paper does not state

Addendum to [wp3-acceptance.md](wp3-acceptance.md), section 1.0.9 (the published
uncertainty), committed before its test and code (plan section 11). Found while writing the
claims package: Table 1 of 2305.19518 prints `61.39 ± 0.15` and the paper does not say what
the `±` is (a standard deviation, a standard error, an interval) nor over how many runs
(the inventory's decisions of 2026-10-18).

## 1. The rule

Section 1.0.9 already classifies a CI of method `other_or_unknown` ("bootstrap, transformed,
model-based, not stated") as **reported but not convertible**: never "no uncertainty", and
its tolerance only known to be at least the lower tolerance. Such a record still had to give
a level, which a paper that states nothing does not give, and inventing one would be a fact
the paper does not hold. So:

- a CI of method `other_or_unknown` may omit its `level` (its construction, level included,
  is not stated); with a level, the level is checked as today;
- a CI of method `t` or `normal` still needs its level;
- the record is written with `lower = value − half-width` and `upper = value + half-width`,
  its location and quote, and resolves to `not_convertible`, as any CI of that method. Here
  `ci` with `other_or_unknown` is the operational representation of a printed `±` of unknown
  kind: `lower` and `upper` are the ends derived from the printed expression, with no claim
  of a probabilistic coverage, of a mean of runs or of a number of runs (Codex review).

A `±` whose kind is not stated is recorded this way, never as `sd` or `se` (which would
state a kind the paper does not state).

## 2. Cases

**Must pass:** a CI of method `other_or_unknown` with no level validates and resolves to
`not_convertible`. **Must fail:** a CI of method `t` or `normal` with no level.

## 3. Regression

Every other uncertainty record validates and resolves as today.
