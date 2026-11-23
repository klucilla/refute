# v0.5.7 The TOI's own signal: records

Plan: [docs/plans/v0.5.7-plan.md](../../plans/v0.5.7-plan.md). Consensus record:
[docs/plans/v0.5.7-consensus/](../../plans/v0.5.7-consensus/README.md). Tracking: #218.

**Everything here is exploratory.** Outputs are never verdicts, candidates or dispositions of any
TOI. Every result that uses the v0.5 battery carries its limits label, **"WEAKENED; does not meet
D1, D2, D4, T2a"**. `method_status: not_validated`.

The phase closed at its pilot gate, with declared limits, on 2026-11-23. The pilot reproduced 8 of
10 TOIs, against the 9 required, so the 540 TOIs were not run.

| File | What it is |
|---|---|
| `seeded_run.py` | The TOI-seeded runner: the TOI's ephemeris seeds the unchanged battery. Committed before any result (fdafa8a). |
| `seeded_report.py` | The report script, with the four doors counted in total and over the records that stayed on the TOI ephemeris. Committed before any result; never run on the 540, which were not run. |
| `seeded-pilot.json` | The pilot's comparison with the v0.5.6 records: 8 of 10 reproduced. |
| `seeded-pilot-records.json` | The pilot's 10 records and their TPF deletion records, unchanged, each with its SHA-256. |
| `seeded-ledger.json` | The pilot's ledger: CPU, disk, downloads, and the stop. |
| `diagnostic_rerun.py`, `diagnostic-rerun.json`, `diagnostic-rerun.md` | The approved diagnostic rerun of the two TOIs that differed: four runs each. The answer is the seeding. |

**The phase's report:** [docs/reports/v0.5.7-report.md](../../reports/v0.5.7-report.md), approved
by the maintainer on 2026-11-23 (#218).
