# v0.2.1 H9(a) (eb_catalog on the target's own TIC): acceptance criteria

Status: **criteria fixed before any validation runs.** This file is committed on its
own, before the tests and the code it describes. Written 2026-10-10 on branch
`claude/v0-2-1-gauntlet-fixes-13f5e7`.

## Problem

`eb_catalog` cross-matches the target with eclipsing-binary catalogs attached to the
claim. A catalog entry that matches the target (by TIC ID, or within
`match_radius_arcsec`) with a period equal to the found period times one of
`period_factors` is a **fatal** failure. The v0.2 calibration uses two catalogs:

- **TESS-EB** (Prsa et al. 2022): built **from the same TESS photometry** that the
  gauntlet analyzes, and keyed by TIC.
- **Gaia DR3 eclipsing binaries**: another instrument, keyed by position (no TIC).

A TESS-EB entry under the target's own TIC at the signal's period is not evidence
independent of the light curve: it is a classification of the same photometry. The
v0.2 post-mortem reports Kepler-14 b refuted by `eb_catalog` alone (a TESS-EB entry
under its own TIC at 1 x the period) while every data test against an eclipsing
binary passed. That case is cited **only as motivation**; no known target is used to
validate H9(a).

## Definition

New parameter `test_plan.gauntlet.eb_catalog.same_photometry_catalogs: list[str]`,
default `["TESS-EB"]`: the catalogs built from the same photometry as the light
curve. The names are compared with the `catalog` column of the
`refute-eb-catalog-1` attachment. Every name must be non-empty. An **empty list
restores the v0.2 behavior** (it is the switch for before/after studies).

A matching entry is an **own-TIC same-photometry match** when its `tic_id` equals the
target's TIC ID **and** its catalog is in `same_photometry_catalogs`. Decision:

1. If any **other** matching entry has a compatible period (a neighbor's TIC, a
   position-only match such as a Gaia row, or the target's TIC in a catalog outside
   the list): **fatal FAIL**, as in v0.2.
2. Otherwise, if an own-TIC same-photometry match has a compatible period:
   **FAIL with severity WARNING** (never PASS). The verdict can then be at most
   WEAKENED (or INCONCLUSIVE when another test is), never SURVIVED.
3. Otherwise, a match by position or ID with another or unknown period: warning, as in
   v0.2. No match: PASS, as in v0.2. The coverage rules (INCONCLUSIVE without a scan
   record, and so on) are unchanged.

**Reporting (the change of definition is stated, R11):**

- The test message of case 2 says that the match is the target's own TIC in a
  catalog built from the same TESS photometry, and that from v0.2.1 it is a warning,
  not a fatal failure. The test metrics record `downgraded: true` and the downgraded
  matches.
- The per-target report adds a sentence when `eb_catalog` was downgraded.
- The calibration summary lists, under diagnostics, the targets whose `eb_catalog`
  was downgraded.

Not changed: the verdict aggregation, every other test, the period factors and
tolerance, the match radius.

## Acceptance criteria

H9(a) is accepted when every case below holds, the full existing test suite passes
unchanged (in particular the existing `tests/test_ebcatalog.py` cases, which all stay
fatal under this definition: a TESS-EB row matched by position without TIC, a
Gaia-EB row under the target's TIC, a catalog "X" matched by position), and
`ruff check` / `ruff format --check` pass.

### A. Unit cases (`tests/test_ebcatalog_own_tic.py`, synthetic catalogs)

Become a **warning** (FAIL, severity WARNING, `downgraded: true`):

- A1. A TESS-EB row under the target's TIC at P, at 2P and at P/2, at the target's
  position and far from it (the TIC decides, as for any TIC match).

Stay **fatal**:

- A2. A TESS-EB row under a **neighbor's** TIC within the match radius at P.
- A3. A Gaia row without TIC at the target's position (0 arcsec) at P.
- A4. A Gaia row **under the target's TIC** at P (catalog outside the list).
- A5. An own-TIC TESS-EB row at P together with a neighbor's TESS-EB row at P: fatal,
  and the message names the neighbor's entry.

Unchanged:

- A6. A position match with another period: warning, `downgraded` false. No match:
  PASS. Coverage cases: INCONCLUSIVE as before.
- A7. Switch: with `same_photometry_catalogs: []`, the A1 rows are fatal again.
- A8. Schema: an empty catalog name is rejected; a claim without the field loads with
  `["TESS-EB"]`.

### B. End to end (`tests/test_ebcatalog_own_tic_e2e.py`, `analyze_data` with a catalog)

Seeds 0-4 of the development set for each scenario. Each case checks its premise
with the switch off (`same_photometry_catalogs: []`) in the test itself.

- B1. `planet` with a TESS-EB row under the target's TIC at the injected period.
  Premise (switch off): REFUTED, with `eb_catalog` the only fatal failure. Expected
  (default): WEAKENED, `eb_catalog` FAIL WARNING, and the per-target report contains
  the downgrade sentence.
- B2. `eb_secondary` and `eb_odd_even` with the same kind of row at their injected
  period: REFUTED with the default (their data tests fail), with the switch on and
  off.
- B3. `blend` with a TESS-EB row under a **neighbor's** TIC at the neighbor's period
  (premise: the found period matches it): REFUTED, `eb_catalog` fatal, with the
  default.

### C. Calibration (`tests/test_ebcatalog_own_tic_e2e.py`)

From the results of B1 and B2 (`build_result`, then `TessCalibrator.evaluate`), with
`flag_excluded_tests: [eb_catalog]` as in the v0.2 claim, switch on and off:

- C1. The flagged false-positive count is identical with the switch on and off (the
  signal verdict already ignores `eb_catalog`).
- C2. The refuted-planet count (degeneracy guard) drops by exactly the planets of B1.
- C3. The summary diagnostics list the B1 planets as downgraded, with the default
  only.

### D. Property (in `tests/test_ebcatalog_own_tic_e2e.py`)

Every existing scenario plus `fp_variability_dominates` and
`variability_train_only`, seeds 0-9, with a TESS-EB row under the target's TIC at
the scenario's injected period (for scenarios without a periodic signal, an arbitrary
fixed period), switch on and off:

- D1. REFUTED with the default implies REFUTED with the switch off.
- D2. The two test lists are identical except, possibly, the severity of
  `eb_catalog` (FATAL to WARNING); the verdict changes only when `eb_catalog` was
  the only fatal failure, and it is then never SURVIVED.

## Seeds

Development seeds 0-4 (B, C) and 0-9 (D), from the development set used by H7 and H4.
The confirmation set is not generated and not used.

## Planned sabotages (run after the code passes, never committed)

Each run against the H9(a) tests only, reverted with an empty `git diff` before the
next.

| Sabotage | Must be caught by |
|---|---|
| S1. The rule is ignored (own-TIC same-photometry matches stay fatal) | A1, B1, C2, C3 |
| S2. Any TESS-EB row counts as the target's own (neighbors downgraded) | A2, A5, B3 |
| S3. Position-only matches (Gaia rows) downgraded | A3 |
| S4. The catalog list is ignored (any catalog with the target's TIC downgraded) | A4 |
| S5. The downgrade gives PASS instead of a warning | A1, B1 |
| S6. The switch is inverted (empty list downgrades, default does not) | A1, A7 |

## Declared price

A real eclipsing binary that looks like a planet in the TESS data and is caught only
by a TESS-EB entry under its own TIC goes from REFUTED to WEAKENED, with the warning
visible in its report. In `discover` mode that is a loss of power against such
binaries. It is the declared price of option (a); it is not compensated by any other
hypothesis (H11 is judged on what it measures).

## Risks to other criteria

- **Refuted planets (degeneracy guard):** can only fall, by exactly the planets that
  only an own-TIC TESS-EB entry refuted (C2, D1).
- **Flagged false positives:** unchanged while the claim lists `eb_catalog` in
  `flag_excluded_tests`, as the v0.2 claim does (C1). The information line "flagged
  with every test" can fall. A future claim that does not exclude `eb_catalog` can
  see the flagged count fall.
- **Gaia stays fatal.** Gaia DR3 contains planet hosts misclassified as eclipsing
  binaries, so a real planet can still be refuted by a Gaia row at its position and
  period.
- **Lock:** the new parameter changes the resolved `test_plan` of older claims, as
  for the other v0.2.1 changes (issue #30).

## Open items

- **Identifying the target's own Gaia source.** A Gaia row at the target's position
  could be recognized as the target itself (rather than an unresolved neighbor)
  through the Gaia source identifier recorded in the TIC. That would allow a
  separate decision for own-source Gaia matches. Not part of H9(a): Gaia matches by
  position stay fatal.
- H9(b) (fatal only with an independent source) and H9(c) remain unchosen; R9 prefers
  (a) and asks to avoid (c).
