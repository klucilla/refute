# WP3 addendum: an extraction file in a folder named by the run

Addendum to [wp3-acceptance.md](wp3-acceptance.md) (W3.11, metric extraction), committed
before its tests and code (plan section 11).

## 0. Why

Some repositories write their results into a folder whose name the run makes up, such as
the date and time it started. 2304.14390 (a development paper) writes its test results to
`<path>/results/static_target/<experiment>/<date and time>/models/test_loss_stats.txt`
(`src/utils/experiment.py`, `init_experiment`, and `src/trainer/trainer.py`,
`log_epoch_loss_stats`, at commit 72f9ebe of jzenn/DSMCS). Today `metric_extraction.file`
is a fixed path, with `{seed}` at most, so such a value cannot be read, whatever the run
does. The maintainer asked on 2026-10-18 for a deterministic rule that finds the single
output that run created, never choosing a file by the value it holds; without such a rule,
the extraction is `INCONCLUSIVE` and that is recorded. This is a generic contract of the
extraction, not a change made to obtain a conclusion on a paper.

The design was reviewed by Codex on 2026-10-18 before any code (thread
`01a14f58-0c57-73f3-8894-2c897e3d705b`); its objections are in the text below.

## 1. The rule (W3.11a)

- **Where a pattern may appear.** The `file` of `metric_extraction` (method and reference)
  and the `file` of the count selectors of the coverage routes (`printed_count` and
  `sufficient_statistics`, which share the selector model) may hold **one** path
  component that is exactly `*`. Nothing else is a pattern: no `?`, `[`, `]`, no `**`, no
  `*` mixed with other characters in a component, never two `*` components. `{seed}` keeps
  its meaning. The `predictions` file of `metric_recompute` does not accept `*` (refused at
  validation).
- **Before the run**, no path matches any pattern of the run in its fresh folder: the rule
  that every output of a run is absent before it starts (`integration.py`) is extended to
  patterns. A match present before the run is a Refute error of the paper's preparation,
  as today for a fixed path.
- **After the run**, the run's processes have all ended (the container is gone) when the
  outputs are read, so no process of the run writes during the reading. The matches are
  the names `n` in the folder named by the components before `*` for which the whole path,
  with `n` in place of `*`, exists. They are **counted before any content is read**:
  exactly one match is read; zero or more than one is an `ExtractionError`
  (`metric_extracted` does not pass), whatever the files hold, including when one of two
  candidates is unreadable or holds no metric. The choice never depends on a file's
  content, time, value or the order in which the folder lists its names, and a failure on
  one candidate never moves the reading to another.
- **The file read.** Every component of the resolved path is a real folder or file (no
  symbolic link, checked component by component), inside the run's folder; the file is a
  regular file with a single link (`st_nlink == 1`), opened without following links where
  the system allows it, and checked again on the open handle (regular, one link) before
  its bytes are read. An error while inspecting a component is an `ExtractionError`, never
  read as "no match".
- **One resolution for every reader.** The value, the path recorded with it
  (`Extracted.source`, `file:<the resolved path>`) and the evidence of the coverage routes
  that read the same file come from one resolution of the pattern; the coverage code does
  not rebuild the path from the pattern. The comparison of the evidence of two methods
  (W3.12a) uses the resolved paths.
- **What the rule shows, and what it does not.** It shows that the path read did not exist
  before the run and exists after it, and that it was the only one. It does not show where
  its bytes came from (a copy of older bytes written by the run would pass): the link
  between the bytes and the evaluation is the coverage evidence of W3.12, which still
  decides `metric_extracted`.

## 2. Synthetic cases

**Must pass:** one folder created by the run, the value read from the file inside it, and
the resolved path recorded; `{seed}` and `*` in one path; two folders of which only one
holds the whole path (one match); a count selector with `*` read from the same resolved
file as the metric, with the coverage evidence citing that file.

**Must fail** (`ExtractionError`, a Refute error before the run, or refused at
validation):
- two folders created by the run that both hold the path, with equal values, with
  different values, and with one of the two unreadable or holding no metric: always no
  value, whatever the order the folder lists them in;
- no folder; the output present before the run (a Refute error, the run does not start);
- a match that is a symbolic link, a folder, or a file with a second hard link; a link
  among the components before or after `*`; a component that cannot be inspected;
- at validation: two `*` components, `**`, `a*`, `?`, `[`, and any `*` in a `predictions`
  file.

## 3. Regression

Every existing extraction test passes unchanged. A path with no `*` is read as today, with
the checks of "The file read" above now applied to it too (no symbolic link on its path, a
regular file with a single link, checked again on the open handle): those are new
refusals, not a loosening.
