# v0.2.1 issue #23 (how blind the holdout is): acceptance criteria

Status: **criteria fixed before the tests and the code.** This file is committed on its own,
before the tests and the code it describes. Written 2026-10-17 on branch
`claude/v0-2-1-reopen` (Phase I, the reopening of v0.2.1 decided by the maintainer on
2026-10-17).

## Problem

Every TESS dossier's `report.md` says, in the section "Blind holdout by year": "the hidden
year is read only inside the predicted windows" (`src/refute/packs/tess/report.py`). Five
reviews of the v0.2 calibration found that this overstates how blind the test is
(`calibration/v0.2/POSTMORTEM.md`, "Reviewers' other notes on the holdout"): the constructor
of `HiddenYear` (`src/refute/packs/tess/holdout.py`) detrends the **whole** raw hidden year,
with the predicted windows masked, before any logged read, and that step is not logged.
After it, only the registered windows (transit and phase-0.5 control) and their baseline
bands are read, and each read is logged. Issue #23 asks for the wording to be corrected
wherever the documentation says otherwise; the roadmap requires the report sentence to
change under the new lock (ROADMAP.md, v0.2.1, Scope: "how blind the holdout is, in the
documentation and in the report sentence of every dossier, changed under the new lock
(issue #23)").

The behavior of the holdout does not change. Only the sentence, and the documentation.

## Definition

The sentence of the report becomes a constant, `HOLDOUT_BLINDNESS_NOTE` in
`src/refute/packs/tess/report.py`, with this text:

> Each year is hidden in turn, and the ephemeris is fitted on the other years only. Before
> any logged read, the whole hidden year is detrended once, with the predicted windows
> masked; that step is not logged. After it, the test reads only the predicted transit
> windows, the phase-0.5 control windows and their baseline bands, and every such read is
> logged.

`docs/gauntlet-tess-v0.2.1.md` gets a section "How blind the holdout is" with the same
facts and a pointer to this file.

## Acceptance criteria

### A. Report (`tests/test_holdout_report_wording.py`)

- A1. A result with holdout rounds: `render_report` contains `HOLDOUT_BLINDNESS_NOTE`
  exactly, and does not contain the phrase "read only inside the predicted windows".
- A2. A result without holdout rounds: no "Blind holdout by year" section and no note
  (unchanged).

### B. The sentence is true of the code (same file)

- B1. Constructing `HiddenYear` on a synthetic hidden year passes **every** hidden cadence
  to the detrending (checked by wrapping `refute.packs.tess.holdout.detrend` and recording
  the length of the light curve it receives), and the mask it receives covers only the
  registered windows; after construction `access_log` is empty.
- B2. A read of a registered transit window and of its baseline band adds one logged entry
  each; a read of an unregistered window raises `HoldoutAccessError` and logs nothing.

### C. No regression

- C1. The tests that render reports and the holdout tests pass unchanged
  (`tests/test_ebcatalog_own_tic_e2e.py`, `tests/test_holdout.py`,
  `tests/test_holdout_isolation.py`, `tests/test_holdout_blindness.py`).
- C2. `ruff check` and `ruff format --check` pass.

## Planned sabotages (run after the code passes, never committed)

| Sabotage | Must be caught by |
|---|---|
| S1. The old sentence restored in `render_report` | A1 |
| S2. `HiddenYear` detrends only the cadences outside the windows' baseline bands (a smaller input) | B1 |
| S3. `HiddenYear` logs the detrending as an access | B1 |

## Amendment 1 (2026-10-17): sabotage results

After the code passed every case (commit `fd87ce1`; tests committed before it in
`227b7b3`, which failed at collection without the code: 1 error in the JUnit file), the
planned sabotages were run against `tests/test_holdout_report_wording.py` only. The
implementation was staged first; each sabotage was applied to the file named, the tests ran
through `scripts/run_tests_affinity.ps1` (threads 0-7, 6 workers), and the file was restored
from the index; `git diff` was empty after every restore. Nothing was committed.

| Sabotage | Failing cases | Planned and caught |
|---|---|---|
| S1. The old sentence restored in `render_report` | A1 (`test_a1_the_report_states_how_blind_the_holdout_is`) | yes |
| S2. `HiddenYear` detrends only the cadences outside the masked windows | B1 | yes |
| S3. `HiddenYear` logs the detrending as an access | B1, B2 | yes (B2 also, because the log has one more entry) |

No criterion changes.

## Effect on locks

`report.py` is under `src/`, so the code hash changes, as for every v0.2.1 change. The v0.2
dossiers and their lock are not touched: their reports keep the old sentence, and the v0.2
calibration is verified at its locked tag `v0.2.0-calibration-lock`.

## Out of scope (texts the maintainer decides)

- The root `README.md` says the same thing twice: the paragraph that starts "The sharpest
  attack is the **blind holdout**", and item 4 of "The steps in detail" under "How a TESS
  signal claim moves through Refute". It is public text; the wording is proposed to the
  maintainer, not changed here.
- `CLAUDE.md` ("checked only at predicted windows"): the maintainer's file; the wording is
  proposed to the maintainer.
- `PROMPT-v0.1.md` is the historical v0.1 prompt and is left as it was.
