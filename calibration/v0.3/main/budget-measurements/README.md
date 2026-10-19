# Budget measurements of the main sample (timing only)

Short timing runs of the papers' code on the VM, for the budget estimates of their claims,
made before any claim is written (the maintainer's decision 2 of 2026-10-18). The records
are the VM's output of `scripts/vm/measure_paper.py`, with their content unchanged; some
were fetched to the host with CRLF line endings, which git stores as LF. Their SHA-256 in
`SHA256SUMS` are of the bytes stored in the repository.

## Conditions (decision 2 of 2026-10-18)

- a. Production isolation: the docker backend, 22 CPUs, 12 GiB, no network in the run.
- b. Short runs with a fixed number of epochs declared in the spec before the run; only
  time is read (`usage_usec`, `wall_s`, and progress-bar lines).
- c. Metric outputs are never read or recorded: the run's log is filtered on the VM to the
  lines the spec's timing patterns match (a failed run keeps its error lines only, a
  traceback and its exception), and the raw log and the run's folder are deleted on the VM.
  No measurement informed a tolerance, an attack or the choice of a claim.
- d. An estimate is extrapolated from these times with a margin; if it does not fit the
  budget, the claim is `INCONCLUSIVE` by budget. Epochs, grid and data are never reduced.
- e. Data downloaded on the host from the official sources, with SHA-256.

Before this commit every run record was checked by a script that prints counts only: each
kept line matches one of its spec's timing patterns or the error patterns, and no kept
line names a metric (auc, acc, loss, rmse, nll, f1, top-1, top-5): 0 records to check.

## Files

- `lra2-build.json` and `pglb2-build.json`: the records of one build of a paper's
  environment (the ladder's rung `requirements_compiled`, the resolved lock, the exit code
  and the CPU usage), with the spec they were built from.
- `lra-build.json`, `lrab-build.json`, `mwe-build.json`, `pgl-build.json` and
  `pglb-build.json`: build **specs only** (the repository, commit, Python, base image, cut-off
  date and patches given to the build), not records of a build: the output of those builds
  (exit code, time, resolved lock) was not kept on the host. They are what each named build
  was asked to do; the run records below are what was measured (end-of-round review of
  2026-10-18).
- `run-<name>-<run>.json`: one timing run (its command with the declared epochs, the exit
  code, the CPU usage, the kept timing lines and, for a failed run, its error lines).

| prefix | paper | notes |
| --- | --- | --- |
| `mwe` | 2309.15704 | UCI datasets (energy, protein); 10 and 40 epochs per method |
| `pgl` | 2302.12465 | the first base image (glibc 2.41): the runs failed at import |
| `pglb`, `pglb2` | 2302.12465 | the bookworm base image (glibc 2.36), with the dependency patch |
| `lra`, `lra2`, `lrab` | 2305.19518 | SimCLR on CIFAR-10 and CIFAR-100, 6 epochs declared; both runs ended with exit 137 (killed) |
