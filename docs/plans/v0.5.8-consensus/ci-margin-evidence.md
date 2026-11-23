# Evidence: the v0.5.4 timing test on CI (collected 2026-11-23)

**The failures.** `tests/test_v054_budgeted_v3.py` failed in the `windows-2025 / rest` jobs of four CI runs on `main`. The stop reported was `stopped: shard s00N ran beyond its declared limit`, and once a follow-on `KeyError: 'checkpoint_shards'`.

| Commit | Run | Job | Result |
|---|---|---|---|
| a94223a | 45189388799 | py3.12 rest | failed |
| fdafa8a | 45191145096 | py3.12 rest | failed (attempt 1) |
| fdafa8a | 45191145096 | py3.12 rest | **passed** (attempt 2, the same code, rerun) |
| 4201b40 | 45194905379 | py3.12 and py3.13 rest | both failed |
| 4b57f7c | 45204249580 | py3.13 rest | failed |
| 4b57f7c | 45204249580 | py3.12 rest | passed |

The ubuntu `heavy-a` job of 4b57f7c failed at 219 s with "The runner has received a shutdown signal": an infrastructure event, not a test.

**The job durations** (seconds, from the Actions API): passing Windows `rest` jobs take about the same before and after the v0.5.7 tests entered.
- Before: 532ba44 2910/2930; 57c4160 2935/2169; 185fd91 2953/2888.
- After: fdafa8a attempt 2 2878/2710; 4b57f7c py3.12 2931.
- Failing jobs end earlier (1595 to 2220 s).

**The test order** in the `rest` shard (`scripts/ci_shard.py rest`, collected locally without running):
- `tests/test_v054_budgeted_v3.py` is at positions 3212 to 3225 of 3909 (82.2 %);
- `tests/v057/test_seeded_run.py` is at 3895 to 3908 (99.6 %), after it.
- The CI failure appears at the 82 % mark.
- No pytest-xdist, so the v0.5.7 tests never run beside the timing test.
- At collection they only import two scripts with no module-level side effect.

**Locally**, the file passes alone (14 of 14, JUnit), both before and after the change below.

**The limit.**
- The real-pool tests run `budgeted_v3.execute` with `max_shard_seconds=1.0`: a spawned shard (about 0.3 s of CPU) must finish within one second of wall time, measured from dispatch.
- The driver (`docs/validation/v0.5.2/stage2/driver.py`) stops a run when a shard passes that limit, and charges a crash as `workers * (max_shard_seconds + CHARGE_SECONDS)`.
- It is a harness limit of a test, not a scientific threshold.

**The change (uncommitted, in the working tree):**
- `MAX_SHARD = 10.0` replaces the real-pool tests' `max_shard_seconds=1.0` (`KW`).
- The three assertions that encode the crash charge (`1.0 + CRASH`) now use `MAX_SHARD + CRASH`.
- The deterministic batch (`EKW`, `Exact`) keeps its own 1.0, since it does not depend on time.
- `MAX_SHARD` stays below `batch_seconds=30.0`, which the driver requires.
