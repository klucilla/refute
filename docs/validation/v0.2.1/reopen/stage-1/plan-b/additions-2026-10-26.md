# Plan B: requirements added on 2026-10-26 (validity and execution; the design is not reopened)

Decided by the maintainer on 2026-10-26, after Codex's audit of `ab4c233`. They add conditions to
gates already in plan B (section 7); none changes the domain, the populations, the criteria or
their counts.

## A1. Gate 2 (the profile O2): a year that disappears after the flux filters

The acceptance record of gate 2 includes, among its tests:

- **A test with a year whose flux becomes entirely invalid after the filters** (every cadence of
  that year dropped by a flux-based filter, while its time stamps and quality flags are inside the
  domain).
- **Specification B's required years come from the domain** (the sectors' labels on the input of
  Amendment B, before any flux-based filter), **not from the data that reach the holdout**. A year
  that disappears never allows a `PASS` with fewer years: the case is not judged on the years that
  remain.
- **Outside the domain, a fatal FAIL kept as a diagnostic never becomes `REFUTED`**: the target
  verdict stays `INCONCLUSIVE` with the reason "outside the validated scope" (plan B section 2).
- With erratum E1 ([errata.md](errata.md)): the sector's label for the domain and for the engine
  comes from the same cadence, or the case is refused when the two labels differ.

## A2. Before X5: an evaluator of its own

Before X5 (gate 8), **a new evaluator, with its own path and its own tests**, computes **G1, G2, B5
and W1e** besides **C1 to C6** on the records of the B2 populations. `population_v2.py` (frozen,
SHA-256 pinned) is not changed; the new evaluator does not import its metrics code to change it.

## A3. The holdout's necessary count for B2

In B2's 360 measurable planets per noise model, C1 (at most 26) and C3 (at most 59) together leave
**at least 360 − 26 − 59 = 275** results that are neither counted by C1 nor by C3 (plan B section 4
already gives 275 of 360). The count **195 of 250** of the earlier stage-1 documents
([../README.md](../README.md), [../viability/README.md](../viability/README.md)) belongs to the
original design of 250 measurable planets (250 − 16 − 39) and **does not apply to B2**. Like the
others, this count is a necessary condition, never a success criterion.
