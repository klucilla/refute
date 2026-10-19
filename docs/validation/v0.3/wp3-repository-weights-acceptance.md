# WP3 addendum: weights that are a file of the pinned commit

Addendum to [wp3-acceptance.md](wp3-acceptance.md) (1.0.2 and 1.0.3, `weights` and
`scope`), to [wp3-declared-weights-acceptance.md](wp3-declared-weights-acceptance.md) and to
[wp3-population-count-acceptance.md](wp3-population-count-acceptance.md), committed before
its tests and code (plan section 11).

## 0. Why, and what kind of change this is

**An explicit change of a rule, decided after the sample was known.** Decided by the
maintainer on 2026-10-19, after the claims package of the main sample was written, and
recorded as such. Until now no claim that names declared weights runs in version 1, whatever
its scope (wp3-declared-weights-acceptance.md, section 1). This addendum narrows that rule:
weights that are a file of the pinned commit, verified, run; weights from outside the
repository (as the CLIP weights of 2305.19518 and the BOLT weights of 2502.16782) stay
unsupported in this version, unchanged.

**The case that showed it.** In 2302.12465 every drawn claim runs an explainer (PaGE-Link,
GNNExplainer or PGExplainer), which optimizes its explanation masks from scratch, and then
`eval_explanations.py`, which scores those masks. Both load the repository's trained link
predictor, `saved_models/synthetic_model.pth`, a file of the pinned commit, and keep it
frozen; the predictor is never trained by the run. Its predictions also decide which test
links are evaluated (the population counted before the lock).

**The justification recorded.** To support, in a generic and checkable way, a legitimate
dependency of the published procedure. It allows the claims to run; it does not guarantee a
conclusive result, and the scientific criteria are unchanged.

**What does not change.** The inventories, the claim draw, the tolerances and the budgets.
The code freeze moves to the commit that closes this change, and the five locks are made on
it.

## 1. The rule (generic)

- **The declaration.** A `test_plan.weights` entry may be a file of the repository:
  `{name, origin: repository_file, path, commit, sha256, size_bytes, license}`: `path`
  relative, with `/` separators, no `..`, not absolute and not under `.refute`; `commit` the
  full 40-hex commit, equal to `repository.commit`; `sha256` and `size_bytes` of the file's
  bytes at that commit; `license` the licence that applies to the file, stated as the
  repository states it (a statement written to the Refute repository also has its
  `sources/` record, issue #34). An entry without `origin` is a downloaded artifact, as
  today, and its bytes are unchanged. A weights file shares its path with no other weights
  entry and no dataset that is a file of the repository, compared normalized (`a/b`, `a//b`
  and `a/./b` are one path); two dataset entries may still name one file, as before; at the
  run no weights file is also a dataset's path in a run's folder. A path two dataset
  entries share is prepared and mounted once, from one source (the same verified bytes);
  two different sources for one path stop the paper before its runs (Codex review, round
  2, found that the preparation of the runs' folders did not yet handle a shared path).
- **The scope is fixed by the approved definition, never to avoid a restriction.** Plan
  section 5: "full training, or evaluation of a released checkpoint". `checkpoint_evaluation`
  is the metric of a released model itself; `full_training` is a run that produces what it
  measures, and it may load a pre-trained model as an input (wp3-declared-weights-acceptance.md,
  section 1: "for example a frozen encoder"). Either scope may name a repository file as its
  `weights`, and the claim file states which, with the reasoning, before the lock.
- **Verified before any code of the paper.** Right after the checkout, before the patches,
  the build or any code of the repository runs, Refute reads the file exactly as it reads a
  dataset that is a file of the repository (wp3-data-sources-acceptance.md, section 1): a
  regular file inside the clone, reached through no link in any component of its path, with
  the declared SHA-256 and size, and, for weights, a regular blob (mode 100644 or 100755) of
  the commit's tree (`git ls-tree`) with the same bytes (its Git blob id), so a file the
  commit does not hold (under `.git`, untracked) is refused (Codex review); its bytes are
  copied into Refute's cache, made read only, and hashed again. Refute's cache and the
  folder of the copies are private to the engine (no container mounts them); no link is
  followed there: the cache, its folder of copies and every folder above them are not
  links, and the copy is written through a new temporary file created exclusively without
  following a link (Codex review, round 2); between the check and the mount only the engine
  writes them. An allowed
  patch may not touch the path (as for a dataset's path). The orchestrator never
  deserializes the file.
- **Mounted read only where the run reads it.** In every container of a claim's runs (the
  method's and the reference's runs, base and attacks), the clone's copy at the path is
  removed and Refute's verified copy is mounted there read only, as a dataset's (the folders
  above it sticky). The container readers do not get it. A build does not get the verified
  mount: its folder is a copy of the whole tree, so the original file is there, and a
  change the build makes in its own folder never reaches a run. Deserializing the file
  happens only inside the VM and the run's container, as any code of the paper. The setup
  records the mount as planned for every run container; the containers created are in the
  run's records.
- **A file that does not verify.** Missing, reached through a link, outside the clone, not a
  regular blob of the commit, or other bytes: no copy is kept, and every claim naming the
  entry is not run (no container, nothing charged), with `run_completed` `INCONCLUSIVE`,
  cause `refute_error`, and the reason (the entry and what failed). The pinned commit fixes
  the bytes, so a mismatch is an error of the declaration, on Refute's side, never the
  artifact's failure. The other claims of the paper run, with two existing rules that stop
  the whole paper before its runs and are kept: a link of the repository that leaves it
  (the copy of the tree refuses it for every paper), and a count before the lock whose
  configuration no longer applies (W3.12f, below). The core's verdict order is unchanged
  (an artifact failure already established by an earlier gate holds, as in
  wp3-declared-weights-acceptance.md).
- **Weights from outside stay unsupported.** A claim that names an entry without
  `origin: repository_file`, or whose dataset is generated with such an entry among its
  `inputs`, is not run, with the reason of wp3-declared-weights-acceptance.md (now "declared
  weights from outside the repository"). A generated dataset whose `inputs` are all files of
  the repository runs, with them mounted.
- **The count before the lock is bound to the file** (W3.12f). When a claim names
  repository weights and its metric's split is a population `counted_before_lock`, the count
  record's `configuration` must list the weights' path with the declared SHA-256 (the
  selection reads them), and its `weights` must list them too, or the claim is refused at
  validation. The count reads the same bytes as the runs: its two containers get the
  weights the same way (verified in the clone as a regular blob of the commit, the tree's
  copy removed, Refute's copy mounted read only, the folders above sticky;
  `scripts/vm/count_population.py`, spec field `weights`, each listed in `configuration`),
  and the record's `weights` (a list of `{path, sha256}`) names the weights so verified and
  mounted, so a count that read the tree's file instead (a spec without `weights`) does
  not bind (Codex review, round 2). At the run the configuration is checked again in the patched
  tree (as today) and, for a weights file, in Refute's copy that the runs mount. Another
  file invalidates the record: before the lock the count is made again; after the lock the
  paper stops before its runs as a Refute error (its claims `INCONCLUSIVE`), never an
  adjusted K.
- **The dossier.** The setup records, for each weights entry, its origin, path and SHA-256,
  and whether it was verified and mounted, with the reason when not; for an entry from
  outside, the statement of wp3-declared-weights-acceptance.md.

## 2. Cases

**Must pass:** a repository weights entry with the commit's bytes is verified before the
build, its copy is mounted read only at its path in every run container (the method's and
the reference's, base and attacks) and in no reader container, the build keeps its copy of
the tree without the mount, and the claim runs and gets its verdict; a build that rewrites
the file in its folder leaves the runs reading the verified bytes; a claim naming external
weights next to it is still not run, with its reason; a weights file that does not verify
blocks only the claims that name it; a generated dataset whose inputs are repository
weights runs; a count record listing the weights' path and SHA-256 validates; the count's
containers mount the verified copy in place of the tree's; a claim with no weights keeps
its canonical bytes.

**Must fail (refused at validation):** a path that is absolute, has `..`, a backslash or is
under `.refute`; a commit that is not the repository's; two repository files with one path,
also through an alias (`a//b`); a counted population whose record does not list the
weights in its `configuration` or in its `weights`, or lists another SHA-256.

**Must fail (not run, `INCONCLUSIVE` on Refute's side):** a file with another SHA-256 or
size; a missing file; a path reached through a symbolic link; a path that is a folder; a
path the commit's tree does not hold (under `.git`, untracked); Refute's cache, a folder
above it or the temporary file of a copy reached through a link. **Must pass:** two
dataset entries naming one file are prepared and mounted once in a run's folder. **Must fail (the paper stops before its runs):** at the run, a weights copy
or a tree file other than the count record's configuration; at the count, weights not
listed in `configuration` or not verified.

## 3. Regression

A paper with no weights, and a paper whose weights are all from outside the repository
(2305.19518, 2502.16782), validate, run, charge and are judged as today.

## 4. Proof

Besides the offline tests: the real command on the VM (`scripts/vm/production_vm_test.py`)
with a synthetic repository holding a weights file that a run reads, and a build that
rewrites it; and the count of 2302.12465 itself, whose two containers read the verified
checkpoint.

## 5. Review

Codex reviewed this design before the code (2026-10-19, round 1): it agreed with the change
and with `full_training` for 2302.12465 (the run produces the explanations it measures; the
predictor is a pre-trained input), and asked for what this text now states: the count's
containers on the verified copy, the commit's tree as the source of truth for weights, the
cache's boundary, the container matrix, and the two rules that still stop a paper. It also
found that with the approved command of PGExp-Link (no `--train_pgexplainer`,
`baselines/pgexplainer_link.py` lines 55 and 117-125) the PGExplainer's mask generator is
not trained; that is a question about an approved command, for the maintainer, not a rule
of this addendum.
