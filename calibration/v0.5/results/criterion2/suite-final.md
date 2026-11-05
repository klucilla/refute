# The full suite after the last commit of the phase (finding M4, 2026-11-05)

- Commit: `88cc5300bc847443e56471a0c2f8d12a2e2c33c8` (main, pushed; its CI run 42092997835:
  success). The commits after it add records only (this file and the second gate's records); none
  touches `src/` or `tests/`.
- Run: `scripts/run_tests_affinity.ps1 -Junit .cache/v05/gate2/junit-final.xml` (CPUs 8-31),
  2026-11-05; `pytest exit=0`.
- Counts from the JUnit XML (`scripts/junit_counts.py`; the file is kept locally, SHA-256
  `b67cc3fd6de9ceb59e6d84b3bc357258a46113e5ffd02a30f836f8f0fe02ab31`): **4,538 tests, 0
  failures, 0 errors, 91 skipped.**
- Against the v0.4.0 baseline (`scripts/check_test_baseline.py --baseline
  v0.4.0-passing-tests.txt`): 4,174 passed by exact node ID; the same 2 "missing" IDs as in
  [README.md](README.md): the two zip-parameter cases of `test_host_readers_count`, whose ID
  embeds the archive's bytes, including the local time that `zipfile.ZipFile.writestr` records at
  collection (`tests/test_ml_data_sources.py`, `_zip`); both pass in this run.
- No `.cache/test-*` folder after the run (counted: 0), as exit criterion 7 asks.
