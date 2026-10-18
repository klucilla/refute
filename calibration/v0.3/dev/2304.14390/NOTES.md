# Development run of 2304.14390 (DSMCS): the rules fixed before the run

Position 335 of the main walk, a development paper (plan 4.5; `selection_log.md`). Its
verdict is computed and recorded but does not count; nothing of this run sets or tunes a
threshold, a tolerance or a budget (the maintainer's terms of 2026-10-18). The claim is
`claim.json`, written by `make_claim.py` with the ML schema's own models; its single
candidate (`inventory.json`) was chosen as the cell the README's DAIS command produces
(Table 3, DAIS, delta-hat 0.25, K 32, N 32), not drawn: a development paper has no claim
round, and its inventory is not approved by the maintainer.

## (a) Where the value is read: one deterministic rule

The run writes its test results to
`runs/results/static_target/local-mbp/<date and time>/models/test_loss_stats.txt`
(`--path runs`; `src/utils/experiment.py`, `init_experiment`; `src/trainer/trainer.py`,
`log_epoch_loss_stats`, at commit 72f9ebe). The extraction uses the rule of
`docs/validation/v0.3/wp3-extraction-pattern-acceptance.md` (W3.11a): the file
`runs/results/static_target/local-mbp/*/models/test_loss_stats.txt` must be absent before
the run (the run's folder is a fresh copy of the repository), and exactly one path must
match after it, counted before any content is read. A file is never chosen by the value it
holds; zero or several matches leave the extraction INCONCLUSIVE, and the path read is
recorded with the value. The value is `$.elbo`, the mean over the 10 test iterations of the
bound the code computes (the paper's "log-likelihood bound" of Tables 2 and 3).

## (b) The seed: what the code does and what Refute can fix or record

- **What the code does.** `--seed` is parsed (`src/arguments.py`, default 2023) and
  `set_seed` exists (`src/utils/experiment.py`), but `train_static_target.py` never calls it.
  The run's randomness therefore comes from the libraries' own state at start: torch's
  default CPU generator is seeded non-deterministically when it is created
  (`getNonDeterministicRandom()` in torch 1.13.1,
  https://github.com/pytorch/pytorch/blob/v1.13.1/aten/src/ATen/CPUGeneratorImpl.cpp#L52,
  cited by the end-of-round review of 2026-10-18; this note first said, wrongly, that it
  starts from a fixed default seed), and numpy's global generator is seeded from the
  operating system.
- **What Refute fixes and records without editing the authors' code.** The command, the
  image (by digest), the locked requirements, the thread variables (22) and the environment
  of every run, all written into the dossier. It records the claim's base seed (2023) only
  as a label: the argument is not passed, because it has no effect.
- **What Refute cannot fix or record.** The effective seed of the run's generators: setting
  or reading it would need a change to the authors' code (an allowed patch), which this run
  does not make. So the `seeds` attack does not apply, and a second run of the same command
  is not guaranteed to give the same value.

## Coverage: what is not proven

The code writes means only: no count of the examples that contributed to the bound, and no
per-example values (`src/trainer/static_target_trainer.py`, `update_epoch_loss_stats`;
`src/trainer/trainer.py`, `log_epoch_loss_stats`). The maintainer's rule of 2026-10-18
(generated data: data_present does not apply, but the evaluated population, the count of
the examples behind the metric and the link of the result to the run and its configuration
must still be shown) is therefore not met: the declared `printed_count` route finds no
count, `metric_extracted` is INCONCLUSIVE, and so is the claim, whatever the value.

**What this development run can show:** the build (requirements.txt with torch 1.13.1 on
Python 3.10), the run under the docker backend, the accounting of the development budget,
and the extraction path of W3.11a. It is recorded as a partial development run (build, run,
accounting, extraction), not a complete one: coverage cannot be shown for this repository
without editing its code.
