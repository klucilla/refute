# WP3 addendum: a population counted before the lock, and an errata of an inventory

Addendum to [wp3-acceptance.md](wp3-acceptance.md) (1.5a, the coverage of
`metric_extracted`; W3.12) and to the inventory format (WP5), committed before its tests
and code (plan section 11). Both are generic rules of the engine, decided by the maintainer
on 2026-10-18 (decisions D1 option (c), and D2), with the first case in the main sample.
The design was reviewed by Codex before the code; its objections are in the text below.

## 0. Why

**The population.** 2302.12465's metric (Table 4, "ROC-AUC on learned masks") is the mean of
one `roc_auc_score` per test link, over only the links the GNN predicts as positive
(`eval_explanations.py` lines 87-145: the 144 test links are iterated, those with
`pred > 0.5` are kept in `comp_graphs`, keyed by the pair, and the mean is printed). The
number of links in the mean is not printed, and no coverage route the engine offers shows
it (Codex, 2026-10-18). Its size is not a property of the data alone: it depends on the
repository's model (the checkpoint `saved_models/synthetic_model.pth`, a file of the pinned
commit). The test split itself is fixed: `process_data` splits with `eids_split`, whose
`idx_split` reseeds the generators with seed 0 before `torch.randperm`
(`data_processing.py` line 46, `utils.py` lines 41 and 66).

**The errata.** The transcribed commands of two candidates of 2302.12465's frozen
inventory are wrong (the agent's transcription; approved errata, issue #158 comment
6256771262). The frozen inventory is never edited, and the claim schema requires the
claim's command to be the inventory's.

## 1. A population counted before the lock (W3.12f)

- **What it is.** A derived split (`derived_splits`, wp3-data-sources-acceptance.md
  section 2) whose membership the repository's own computation decides, upstream of the
  measured value, may declare `counted_before_lock: {script, record}`: the paths of an
  attachment with role `population-count` (a script written by Refute, versioned in the
  repository) and of an attachment with role `population-count-record` (its output). An
  absent `counted_before_lock` is not written by the resolution, so an existing claim keeps
  its canonical bytes. Two counted populations in one claim each name their own pair of
  attachments; an attachment serves one population only.
- **The script reproduces the evaluator's selection, and stops there.** It loads the
  repository's data and saved model with the evaluator's effective arguments (for
  2302.12465: the evaluator's split ratios and sample limit, the checkpoint, the
  dimensions 64, the prediction operation, the node and edge types, `num_hops`, the
  subgraph built by `hetero_src_tgt_khop_in_subgraph` with its remapped feature ids, the
  `train_eval` section of the configuration only when the command passes `--config_path`
  (2302.12465's corrected commands do not), and the strict comparison `> 0.5`), applies
  the same selection, and counts the selected keys as the evaluator does (distinct pairs,
  as `comp_graphs`). It does not import the evaluator's executable module (which goes on to
  read masks and compute the metric). It prints exactly one line
  `refute-population-count <K>` and exits 0. It computes no explanation, no mask and no
  value of the claim's metric, and reads no output of a run. Codex checks, before it runs,
  that it stops before anything the claim measures.
- **Where it runs.** In the production container of the claim's environment: the clone at
  the claim's commit, anchored on the commit's tree, the claim's allowed patches applied in
  their order (the same `prepare_inputs` and `patch_tree` sequence as a run), the image the
  claim's ladder builds, no network, the production limits and the run profile, as a setup
  step of the paper before the lock. Its log is filtered to the count line only (no other
  output kept).
- **The record** (canonical JSON, committed before the lock): the dataset and the derived
  split it counts; the count; the script's SHA-256; the repository commit; the SHA-256 of
  each allowed patch, in order; the SHA-256 of the configuration files the selection reads;
  the environment: the base image's digest, the rung that built the image (one of the
  rungs that write a resolved lock), the SHA-256 of the resolved lock it wrote
  (`.refute/requirements.lock`) and the SHA-256 of its venv's `pyvenv.cfg` (the
  interpreter's implementation and full version, and the uv version; the build copies it
  to `.refute/pyvenv.cfg`), since two rungs with different interpreters can resolve the
  same lock (Codex, 2026-10-18); the exit code, the CPU usage and the UTC times; the
  Refute commit. (An image ID is not used: an image committed from a build container gets
  a new ID at every build, even with the same content.)
- **At validation** the claim is refused unless: the record names this dataset and split;
  its count is an integer of at least 1 (a count of 0 has no valid coverage and is
  refused; never a fraction or a boolean) and equals the split's `expected_examples`; the
  script attachment's SHA-256 equals the record's; the record's commit and patches (in
  order) equal the claim's, and its base image the claim's; its rung is one with a
  resolved lock, and the lock and `pyvenv.cfg` hashes are present; its configuration is a
  list of `{path, sha256}`, each path relative and listed once; the exit code is 0.
- **At the run** the environment must be the record's: after the build, the record's rung
  must be the one that built the image (its resolved lock and `pyvenv.cfg` have the
  record's SHA-256, and no later rung ran), and the configuration files in the patched
  tree must have the record's SHA-256 (the base image is the claim's, checked at
  validation); otherwise the count does not apply, and the paper stops as a Refute error
  before its runs (its claims `INCONCLUSIVE`), never an adjusted K. The record is given to
  the run (`--count-record attachment=file`) and must equal its attachment's SHA-256.
- **At the run, the evidence.** An allowed patch of instrumentation, minimal, prints the
  size of the population the measured value was computed on, after the value, on one line
  named by the method (for 2302.12465, `refute-population-size <explainer> <n>` with
  `len(mask_auc_list)`, right after the mean). The claim's coverage route is `printed_count`
  with a regular expression that matches that line exactly once (a second match is refused
  by the parser), and its `link` cites the list, the mean and the instrumented print. It is
  checked against `expected_examples` as today: equal passes; any other number, or none, is
  `INCONCLUSIVE` with the reason. Each method of a comparison prints and selects its own
  line (shared evidence between the two sides is refused, as today).
- **What is exposed before the lock.** Only K, a fact about the model's predictions on the
  test links, never the value the claims measure. This is recorded in the claim with the
  reason, as an amendment of the protocol declared before the lock.
- **Patches of instrumentation.** A third purpose of an allowed patch, besides the origin of
  the bytes and the dependencies a README declares: printing a count the coverage needs, at
  a point after the value is computed, with no change to the computation. Codex checks each
  one line by line.
- **Determinism.** The selection has no random operation in its forward pass (Codex read
  `model.py`), but numerical determinism of Torch and DGL on the CPU is not guaranteed in
  general; a K at the run that differs from the record's is `INCONCLUSIVE`, never adjusted.
  An acceptance case runs the script twice, in independent processes with the same image
  and profile, and requires the same K.

## 2. An errata of an inventory (WP5)

- **What it is.** A file next to the frozen inventories, `<arxiv_id>-errata-<n>.json`
  (format `refute-ml-inventory-errata-1`), naming the inventory by its SHA-256, with
  entries `{candidate_id, field, old, new}`, the evidence, the uses by comparisons
  (`also_used_by`), and an approval block (by the maintainer, the URL of a GitHub issue
  comment). The only field an errata may change is `command` (a closed list); value,
  location, metric and split never change, and the draw is untouched (it depends on the
  candidate ids and the inventory's hash).
- **In a claim.** The errata is an attachment with role `inventory-errata`, covered by the
  lock. At validation: its inventory hash equals the claim's inventory; each entry names a
  candidate of the inventory, and its `old` equals the inventory's field; a candidate
  appears in one entry of one errata only (two erratas for one candidate are refused); the
  approval block is complete.
- **The transcription.** `approvals.transcription.inventory_sha256` and the draw stay bound
  to the original inventory (its hash is never recomputed on a corrected copy). The claim's
  transcription must equal the original inventory's with only `command` replaced by the
  errata's `new` for its candidate, and the claim's command must equal that corrected one.
- **The reference of a comparison.** When a comparison's reference method is a candidate an
  errata corrects (by `also_used_by` or by the method's name), the claim's
  `reference_run.argv` (with its seed argument) must equal that candidate's corrected
  command; with the old command, the claim is refused.

## 3. Cases

**Must pass:** a derived split with a count record bound to the claim (dataset and split,
count equal to `expected_examples`, script hash, commit, patches in order, configuration
hashes, exit 0); the script run twice in independent processes gives the same K; a run
whose printed count, on its own line, equals K (coverage passes); a comparison whose two
sides each print and select their own line; a claim whose transcription equals the
inventory's corrected by an approved errata, with the reference run's command corrected
too; a claim without `counted_before_lock` and without errata keeps its canonical bytes.

**Must fail:** a count record whose count differs from `expected_examples`; a count of 0, a
fraction or a boolean; a script whose SHA-256 differs from the record's; a record of
another commit, other patches or another order, another configuration, another dataset or
split; a rung without a resolved lock, a missing `pyvenv.cfg` hash, a configuration entry
with a path outside the tree or listed twice; an exit code other than 0; two lines or none
in the script's output; at the run, another resolved lock, another interpreter with the
same lock, another rung, a later rung that ran, or another configuration than the
record's (a Refute error before the runs), a printed count other than K, two matching
lines, or none (`INCONCLUSIVE`); an errata for another inventory; an entry for a candidate
that does not
exist, or whose `old` is not the inventory's; a field other than `command`; a candidate in
two entries or two erratas; an errata without approval; a claim whose command is the old
one while an errata for its candidate is attached; a comparison whose method is right and
whose reference run keeps the old command.

## 4. Regression

A claim with no `counted_before_lock` and no errata validates, runs and hashes as today.
