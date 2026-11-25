# v0.5.11, proof (iv): full CI evidence on the last commit that changed `src/`

Required before the gate by the charter (section 7, "Its SHA") and the maintainer's decision of
2026-11-25 (#218, comment 7162573384, item 2).

- **The commit:** `f18d6f84d9ed122b9d13daf4cbf14971686e4801`, correction 1 in `src/`. It was the
  tip of `main` when pushed; its push run of `ci.yml` was the full matrix (it touches `src/**`).
- **The command,** run once through the metered unit `ci-evidence` (launch_v9, network), on
  2026-11-25:

  ```
  scripts/ci_evidence.py f18d6f84d9ed122b9d13daf4cbf14971686e4801 --level full
  ```
- **Its whole output:**

  ```
  run 45621658147 (push): 28 jobs, all success
  evidence holds
  ```
- **Exploratory, `method_status: not_validated`.** This is software evidence, not a verdict.
