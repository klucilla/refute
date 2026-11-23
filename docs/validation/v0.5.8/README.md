# v0.5.8 Output stability: records

Plan: [docs/plans/v0.5.8-plan.md](../../plans/v0.5.8-plan.md). Tracking: #218.

**Everything here is exploratory:**
- an output is never a verdict on a TOI, a candidate or a disposition;
- every record carries the limits label **"WEAKENED; does not meet D1, D2, D4, T2a"** and
  `method_status: not_validated`;
- nothing here changes the v0.5 battery or any verdict.

| File | What it is |
|---|---|
| `stage0_records.py`, `stage0-records.json`, `stage0-records.md` | Stage 0: the recommendation's section 1 recounted from the committed records, with the two recorded differences. |
| `stability_run.py` | Stage 1's runner. It imports v0.5.7's `seeded_run.py` without editing it, and has three steps: `draw`, `run` and `clean`. |
| `stage1-set.json` | The set, written once and committed before the run: the 107 decided records and the 60 of 257 INCONCLUSIVE drawn with a committed seed. |
| `stability_report.py` | The doors and the flips, with their counting rules. It was committed before any result (`1f3e5f9`). |
| `stability-records.json` | The 167 TOI-seeded records and the 167 TPF deletion records, unchanged, each with the SHA-256 of its file. |
| `stability-ledger.json` | The run's ledger: five batches, CPU, downloads, disk and the terminal state. |
| `stability-report.json`, `stability-report.md` | The doors in total and over provenance `same`, with the flips per output and per test and Wilson 95 % intervals. |

The tests of the runner and the report are in `tests/v058/`.

**The phase's report and note** (both approved by the maintainer on 2026-11-23, #218):
- [docs/reports/v0.5.8-report.md](../../reports/v0.5.8-report.md);
- [docs/reports/v0.5.8-stability-note.md](../../reports/v0.5.8-stability-note.md), "How stable is a
  Refute output?".

**Its addendum to v0.5.6:** [docs/reports/v0.5.6-report-addendum-2026-11-23.md](../../reports/v0.5.6-report-addendum-2026-11-23.md).

**The Codex rounds** are in the consensus record
[docs/plans/v0.5.8-consensus/](../../plans/v0.5.8-consensus/README.md).

## Data and acknowledgments

- **TOIs and their ephemerides:** v0.5.6's frozen frame, from the NASA Exoplanet Archive's TOI
  table.
- **Light curves and pixel files:** SPOC products at MAST. None is kept here.
- **The acknowledgments** (ExoFOP, the NASA Exoplanet Archive and MAST) are given in full in
  [the report](../../reports/v0.5.8-report.md#data-and-acknowledgments).
