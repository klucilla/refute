# Step 0's recount: the rules, fixed before the first run

This is the charter of v0.5.11, step 0, item 2, Codex's wording: "Recount joint assessability and
retention for recorded tests by host and population. Mark missing coverage and new-test
assessability unknown."

These rules are committed before
[../tools/recount.py](../tools/recount.py) runs (rule (b)). The run is a read-only recount of
committed records: verification, not a rerun. No record is changed, and no recorded value is
replaced or re-scored.

**Labels.**
- Every output is `exploratory`, with `method_status: not_validated`.
- The part B records carry 'WEAKENED; does not meet D1, D2, D4, T2a'.
- The outputs are never verdicts on any TOI, never candidates, and never acceptance.

## R1. Inputs (the only files read)

- **P1, v0.5.6 part B:** `docs/validation/v0.5.6/part-b-records.json`, every one of the 300
  records.
- **P2, v0.5 C2 (T2a):** `calibration/v0.5/runs/c2/records.jsonl` and
  `calibration/v0.5/runs/c2-prefix/records.jsonl`. The set is the one of
  `docs/validation/v0.5.10/recount_section2.py`: injections with status `OK` that were
  recovered, on hosts whose original curve did not pass the version-1 gate. The tests read are
  `chain.v05.tests`.

## R2. The recorded tests examined

These are the legacy counterparts of the screen's candidate tests:
- `odd_even`, for F1;
- `secondary_eclipse`, for F2;
- `plausibility`, for F3.

No other test is examined.

## R3. One class per record and test

| Class | When |
|---|---|
| `assessed_pass` | status PASS, and `coverage` is an integer above zero |
| `assessed_fail` | status FAIL, and `coverage` is an integer above zero |
| `not_assessed` | status INCONCLUSIVE; or status PASS or FAIL with `coverage` equal to zero; or the test is absent from the record |
| `unknown` | status PASS or FAIL, and the record has no `coverage` field |

## R4. The joint class of a record

This is the legacy replay under the draft screen's precedence, with the three tests of R2 as the
core. The first rule that applies decides:
1. any `assessed_fail`: `rejected`;
2. any `not_assessed`: `unassessed`;
3. any `unknown`: `unknown`;
4. otherwise: `retained`.

A P1 record whose status is not `OK` has no battery output. It is counted apart as
`no_output`, never as any class.

## R5. The screen's own tests

F1, F2, F3, F4 and U1 were never run on any record. Their assessability is `unknown` for every
record, and it is written so. Nothing is imputed.

## R6. Groups

- **P1:** all records; by arm (`planet`, `fp`); and by `identity.matched` (true or false).
- **P2:** all records.
- **Per population:**
  - the counts of each class per test (R3) and of the joint class (R4);
  - the number of distinct hosts (P1: `tic_id`; P2: `target_key`), and records per host (minimum,
    median, maximum);
  - the hosts whose every record is `retained`.

## R7. Outputs

- `docs/validation/v0.5.11/recount/recount.json`: every count, with the inputs' SHA-256 and these
  rules' SHA-256.
- `docs/validation/v0.5.11/recount/recount.md`: the same tables, with the labels.
