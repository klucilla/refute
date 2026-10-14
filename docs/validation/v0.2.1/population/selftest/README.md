# Self-test of the population harness (not a measurement)

These files are the self-test of `../population.py` (SHA-256
`7713c531a97eba039286878319df66bd034945a87c9ddeb5012d695a953f8ad5`), run on
2026-10-11 under Amendment 1 of `../../population-study.md`. They show that the chain
works; **they are not a measurement**, their numbers mean nothing about Refute, and no
case of the development population was generated or analyzed.

- Population `selftest`: seeds with the prefix `refute-v0.2.1-population-selftest`, at
  most 2 cases per class and mechanism in each noise model, 44 cases.
- `manifest.json`, `manifest-repeat.json`, `manifest-workers3-reverse.json`,
  `manifest-workers1-shuffle7.json`, `manifest-hash-only.json`: five generations in
  separate processes (24 workers in index order, twice; 3 workers in reverse order;
  1 worker in a shuffled order; 24 workers without writing the cases), all byte-identical
  (SHA-256 `e6d1808a6eb6a3e382ca7a7ac34f5d009ba8306077961838baf2a78a934d0eda`); and a
  sixth generation with 5 workers in another shuffled order, checked against
  `manifest.json` (44 identical, 0 diverged).
- `M0-f479823-*/` and `HEAD-cbd98cb-*/`: `analyze` in the environment of tag `v0.2.0`
  and in this branch's environment (the harness was not yet committed; `src/` was that
  of `cbd98cb`).
- `corrupt-byte-check-*/`: one byte of one cached case was changed (XOR 0x01 at its
  middle byte); `analyze` refused the case without analyzing it. The byte was then
  restored and the case checked against the manifest again (identical).
- `metrics-*.json` and `.md`: `metrics` over the two runs.
- `selftest-log.txt`: the commands and their output, in order (including a resumed
  `analyze` that found every case done and analyzed nothing).

The cached case files are in the git-ignored `.cache/population/selftest/` and are not
published. The BLAS paths inside the recorded NumPy configuration are those of NumPy's
own build machine, as NumPy reports them.
