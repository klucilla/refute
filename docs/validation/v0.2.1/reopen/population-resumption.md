# Resumption of the v0.2.1 population study (2026-10-17)

Status: **resumption record**, by the maintainer's decision of 2026-10-17 (Phase I, the reopening of
v0.2.1 in parallel with v0.3). It amends nothing of the closed study: `../population-study.md`, the
closure record `../population/closure-record.md` and every file under `../population/` stay as they
are. It records the decision, its conditions and how the resumption meets the four conditions of
the closure record.

The FAIL of the v0.2 calibration stays a valid result: the resumption measures corrections and
neither erases nor reinterprets that history (`calibration/v0.2/POSTMORTEM.md`). The v0.2 claim is
never re-locked or re-run.

## The decision

- **The corrections are resumed** on revision 4 of the plan, with its Amendment 1
  (`corrections-plan-rev4.md`; the SHA-256 of the approved version in
  `corrections-plan-rev4.sha256`). Its design is approved. The updated sizing of its section 5 and a
  ceiling of execution go to the maintainer before the calibration population of the estimators is
  generated.
- **The development population is reused** (the frozen manifest `../population/manifest-dev.json`),
  with these conditions, all from the maintainer:
  1. C1 to C6 and their limits stay (`../population-study.md`, section 1).
  2. M0 to M3, their results and the manifest stay.
  3. The limit of two candidate versions, M4 and M5, stays.
  4. The inherited counters, journals and limits of attempts are **not** reset by the reopening.
  5. The confirmation stays unseen: frozen code, seeds from a future drand round (each round declared
     with the maintainer's approval), run once. It must be able to fail the package; a failure does not
     authorize another attempt automatically: it goes to the maintainer.

## The four conditions of the closure record

| Condition (closure record) | How it is met |
|---|---|
| 1. Close the method and the six open rows before any code and before any reserve is sized | revision 4 closes B1, B3, B4, B5, B6 and B7 as a specification (Codex review 4, four rounds); no code of the corrections exists before its commit |
| 2. Decide beforehand whether to reuse the development population or a new one | reuse, decided by the maintainer on 2026-10-17 (above), before any code |
| 3. No constant is tuned on the M0 to M3 development numbers | revision 4's settings come from revision 3's declared configurations (9.2) and from rules fixed before any measurement; the sizing uses declared reference rates, never M0 to M3 |
| 4. Known exposure, stated in every record | stated here and in revision 4: the corrections were chosen after the development failures were seen |

## What the agreement of Codex does not show

It closes the specification, not the method: approval depends on the implementation, its tests, the
calibration of the estimators (21 conditions and the reserves), M4 (and M5) on the development
population, and the confirmation.
