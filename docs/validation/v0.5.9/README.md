# v0.5.9 Ephemeris entry: exploratory prototype (records)

Plan: [docs/plans/v0.5.9-plan.md](../../plans/v0.5.9-plan.md). Tracking: #218.

**Everything here is exploratory:**
- an output is never a verdict on a TOI, a candidate or a disposition;
- every record carries the limits label **"WEAKENED; does not meet D1, D2, D4, T2a"** and
  `method_status: not_validated`;
- nothing here changes `src/`, the v0.5 battery's tests, thresholds or rules, or any verdict.

| File | What it is |
|---|---|
| `prototype_run.py` | The prototype: the set's draw, the two entry modes, the fixed evaluation, the six probes, the consensus rule and the centroid guard, with the run's caps. It imports v0.5.7's `seeded_run.py`, v0.5.8's `stability_report.py` and the battery without editing them. Steps: `draw`, `run`, `bundle`, `clean`. |
| `prototype_report.py` | The five questions and their counting rules, fixed before any result. |
| `prototype-set.json` | The 24 TOIs, written once by `draw` after the seed was committed. *(Added by the draw.)* |
| `prototype-ledger.json`, `prototype-records.json`, `prototype-units.json`, `prototype-report.json`, `prototype-report.md` | The run's ledger, the 48 mode records, the 252 unit records and the script's report. Written by the run of 2026-11-24 (complete), approved at `331ca03` (#218, comment 7125778250). |
| `pilot_run.py`, `pilot_observe.py`, `pilot-comparison.json`, `pilot-observed.json` | The pilot of the approval: the first three batches, on three TOIs only, and the supervisor's account compared with an independent measure (Windows process CPU, file sizes). It passed (#218, comment 7126035677). `pilot-observed.json` holds the observer's per-process and per-file readings (a byte copy of the run's `.cache/v059/pilot/observed.json`, SHA-256 `676c29c2…ffaad5d`, committed after the gate review, finding 6). *Note:* the docstring of `pilot_run.py` says "the first batch"; the pilot took three batches, because the runner admits a TOI's bases and probes only in the batch after their inputs are recorded. The script that ran is kept as it was (gate review, finding 4). |
| `wilson_check.py`, `yield_model.py`, `check_codex4.py` | The checks cited by the version-5 specification draft and the consensus record: Wilson numbers, the pair-yield and cost model, and Codex's round-4 numbers. They ran from `.cache/v059/tools/` and are committed after the gate review (finding 5). Changes from the files that ran: ruff formatting, two names (`dE`, `dS` became `d_e`, `d_s`; the printed labels are unchanged), an unused loop variable, and `check_codex4.py` imports `yield_model` from this folder. Each gives byte-identical output to the file that ran (checked on 2026-11-24). SHA-256 of the files that ran: `wilson_check.py` `1b4bd71e…bf5893`, `yield_model.py` `0bd8cec6…7c8a11`, `check_codex4.py` `c5b1fc1b…ed9e80`. Run: `.venv/Scripts/python.exe docs/validation/v0.5.9/<name>.py`. |
| `pinrun.py` | A byte copy of `.cache/v055/tools/pinrun.py`, which runs a command pinned to processors 8 to 31 at BelowNormal priority; the v0.5.9 procedure ran through it. SHA-256 `9a01edc1a08d87c13adc985db99be849ce512bd05215c179c5b3802dab5c19aa`. |

The phase report is [docs/reports/v0.5.9-report.md](../../reports/v0.5.9-report.md).

The tests are in `tests/v059/`.

**The Codex rounds** are in the consensus record
[docs/plans/v0.5.9-consensus/](../../plans/v0.5.9-consensus/README.md).

## Data and acknowledgments

- **TOIs and their ephemerides:** v0.5.6's frozen frame, from the NASA Exoplanet Archive's TOI
  table.
- **Light curves and pixel files:** SPOC products at MAST. None is kept here.
- **The acknowledgments** (ExoFOP, the NASA Exoplanet Archive and MAST) are given in full in
  [the v0.5.8 report](../../reports/v0.5.8-report.md#data-and-acknowledgments).
