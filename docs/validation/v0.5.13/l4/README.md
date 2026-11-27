# L4: #226 under amendment 2, revision 6, prepared without any check (in progress)

The maintainer's decision L4 (#218, comment 7223634913). Labels: `exploratory`,
`method_status: not_validated`. **Nothing is frozen.** No golden file was opened, no check of
amendment 2 ran and NR-A2 did not run. The manifest is approved by the maintainer by its hash
before any check.

## What exists

**(b) The comparator of section 3.1** ([`../tools/comparator.py`](../tools/comparator.py)):
- the inventory and SHA-256 of each file against each setting's recorded payload;
- `plan-` and `error-` files, and `ERROR` outputs, byte for byte;
- JSON cut into tokens with their paths. Whitespace and every token other than a number compare
  exactly. A number may differ only when all of these hold:
  - it is in float form;
  - its path is on a measurement pattern of the schema and on no exact pattern;
  - its last key is not an exact key;
  - the two values are within `1e-6` relative, in exact rational arithmetic. Zero equals only
    zero. A nonfinite value is `null` in both settings.
- the report line by line, through exactly one shared template;
- the claim inventory and resolved SHA-256 values exactly. The baseline exception is preserved
  because every value compares exactly.

Its tests ([`tests/test_v0513_comparator.py`](../../../../tests/test_v0513_comparator.py)) use
synthetic tokens only: 16 passed, 0 failed (JUnit XML, with `tests/test_ci_plan.py`: 44 in all,
0 failed).

**J3's docs-only pattern.** That test reads `l4/comparator-schema-parts.json` and imports a tool
from this folder. J3 made `docs/validation/v0.5.13/*.json` documentation only, on the basis that
no test read the folder, and that basis no longer holds for this file.
- A commit that touches only that JSON runs no test in CI.
- A commit that touches the tool or the test still runs them.
- The freeze must therefore run this test itself, locally, on the frozen files.

**A property of the design.** The schema's classification is consulted only when two tokens
differ. So an incomplete measurement list can only make the comparator fail; it can never let it
pass. Lists that are too wide are what the review must catch.

**The schema's exact keys** ([schema-keys.json](schema-keys.json), the committed unit
`schema-keys`, from source only):
- **The modules:** the 73 files of I2's inventory (its `module_files`), not a typed list; a
  missing file fails (decision M3).
- **Rule 1:** the fields of the plan models in `params.py`, except the names of measurement
  outputs. These are the fields and `to_dict` keys of `Candidate` and `Ephemeris`, and the
  literal keys of `key_values` in `build_result`.
- **Rule 2:** the keys of `thresholds` mappings: dict literals, `dict(...)` keywords,
  `thresholds["key"] = ...`, `thresholds.update({...})`, and a name resolved to its dict literal
  in the same or an enclosing function. Of 42 arguments it lists apart:
  - 36 are a plan model's dump, whose keys are plan fields (rule 1);
  - 5 are a function's parameter, whose values are its callers' arguments, which the rule reads at
    the call sites;
  - 1 is not resolved: `src/refute/core/verdict.py:111`, `TestResult.from_dict`, which reads
    thresholds back from a serialized record. It writes no new key.
- **Rule 3:** a key of a `metrics`, `inputs` or `sensitivity` mapping whose value echoes
  configuration: a plan-field attribute that is not a measurement name, an all-caps name, or a
  numeric literal. It finds 4 keys: `aggregation`, `attempt`, `inconclusive_class` and
  `inconclusive_detail`.
- **Rule 4, the exact subtrees:** `thresholds` itself, and the key of a dict entry whose value is
  a name the same function also puts in a `thresholds` mapping. Everything under such a key
  compares exactly, wherever it sits. There are 9, among them `thresholds_m4`
  (`battery.py:659`).
- **The result:** 216 exact keys and 9 exact subtree keys. Five plan-field names are left out as
  measurement outputs: `depth_ppm`, `duration_hours`, `period_days`, `snr` and `t0_bjd`.
- **D1a's differing fields:** none of them is an exact key. Their names were known when the
  schema was written.
- **The earlier runs:** four runs, each after a committed change to the rule, were replaced by
  the next one. None of their outputs was committed:
  - the first, without the exception for measurement names;
  - the second, whose rule 3 took `candidate.snr` as configuration;
  - the third, with unclassified parameters;
  - the fourth, without rule 4.

**The schema's other parts, a draft** ([comparator-schema-parts.json](comparator-schema-parts.json)),
written from `dumps_json`, `build_result`, `chain` and `render_report`:
- the measurement and exact JSON patterns of `verdict` and `chain`;
- eleven report templates, each with its source lines. A test checks that each template compiles,
  that its groups are the declared ones, and that each synthetic example line matches exactly one
  template.

## Found in review and fixed

- **The three open items of the interim report** (the module list, the unresolved `thresholds`
  arguments and the renamed configuration echoes) are closed by decision M3. See the rules above.
- **Also fixed:**
  - `comparator.last_key` returned a list index for a list item, so it now returns the nearest
    key (with a test);
  - `comparator.main` did not compare the claim inventory, and now does.

## (a) The candidate list of the decision layer (a working record, not the manifest)

[decision-layer.json](decision-layer.json), the committed unit `decision-layer`
([`../tools/decision_layer.py`](../tools/decision_layer.py), from source only; 9 tests on
synthetic snippets, 0 failed). Its rule is stated in full in the tool's docstring. It applies
section 4's first paragraph mechanically and includes when in doubt.

| Count | Value |
| --- | --- |
| Functions in the 73 modules | 924 |
| Reachable by name from the golden path's five calls | 524 |
| Decision functions (holding a sink) / returning decision functions | 77 / 31 |
| **Candidate rows** | **410**: 152 numeric, 20 finiteness, 238 non-numeric |
| Rows with an enclosing `if` / behind a preceding data-dependent exit | 68 / 246 |
| J1's 173 atoms not found | 7, all in `duration.estimate_duration`, which only `TessAnalyzer.analyze` calls (`pipeline.py:1177`), off the golden path |
| `attenuated` (`battery_v52.py:338-340`) | a row |
| Rows in `power` / `a0` / `a0_v4` / `core/inconclusive` | 1 / 0 / 0 / 8 |
| I2 sites in reachable functions that are not rows | 1,443 (not in a decision context: internal selections or values) |
| Rows reached from `chain` (stage 1) / from the verdict's entries / from both | 404 / 409 / 403 |

**What the list does not settle yet** (before any operand is mapped):
1. **Reachability is too wide.** Calls are resolved by name only, so modules off the golden
   path appear reachable, among them `calib05`, `screen_d5` and `discover/pilot`. A cited table of
   configuration dispatch, evaluated on each fixture's plan taken from source, must prune it and
   attribute each row to its fixtures.
2. **`a0` and `a0_v4` give no row.** Their comparisons choose data: the stratum and its error, the
   pooled variance (`shortcut`), the events kept (`event_meta`). Under section 4's first paragraph
   these are internal selections, which fall under the declared limit. This needs Codex's check.
3. **Rows behind a data-dependent exit (246).** Revision 6 has no rule for a predicate that a
   fixture may not reach. Whether its operands are "present" cannot be classified from source when
   a metric is written on one path only. This is a question for the maintainer.
4. **Two evaluations per fixture.** `chain` (stage 1) evaluates almost the same predicates again
   and serializes statuses with no operands. Whether that is a second case for the margin check
   changes N. Count it both ways; the decision is the maintainer's.
5. **The earlier runs:** four runs, each after a committed change to the rule, were replaced; none
   of their outputs was committed:
   - the first lacked bare flags and references;
   - the second lacked mutated lists;
   - the third lacked the location of J1's misses;
   - the fourth lacked the counts of the last two rows of the table.

## Under block N (#218, comment 7224847166): fixtures and configuration pruning

**What changed.** The extractor now resolves calls through each module's imports instead of by
name alone. It runs once per fixture:
- each version's verdict, error and report, labelled `v1`, `v2`, `v2-eb`, `v3`, `v4`;
- each version's `chain` at stage 1, labelled `chain-v1` to `chain-v4` (N2).

A call that a configuration guard keeps from running in a fixture is pruned. `GUARD_TABLE` holds
13 guards, each with its source; a guard it does not hold keeps the call. 11 tests, 0 failed.

| Fixture | Rows | Numeric | Finiteness | Fixture | Rows | Numeric | Finiteness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v1 | 159 | 62 | 5 | chain-v1 | 115 | 52 | 4 |
| v2 | 210 | 85 | 5 | chain-v2 | 166 | 75 | 4 |
| v2-eb | 210 | 85 | 5 | chain-v2-eb | 166 | 75 | 4 |
| v3 | 271 | 109 | 7 | chain-v3 | 218 | 99 | 6 |
| v4 | 273 | 115 | 11 | chain-v4 | 220 | 105 | 10 |

- **The unpruned union:** 398 rows (151 numeric, 19 finiteness, 228 non-numeric). 89 of them are
  on no fixture after pruning, for example the `corrections.active` paths.
- **J1's atoms:** every one is found except the 7 in `duration.estimate_duration`, which is off the
  golden path. `attenuated` is a row.
- **Pruning acts on calls, not rows.** No row is itself pruned by a guard. The version-3 and
  version-4 checks become unreachable in the earlier fixtures through the guarded calls of
  `v05_tests`, `attack_candidate` and `conclude_analysis`.

**N2, the reading it rests on.** `tests/baseline_code_v0511.py:47-50` records that CI run
45514526728 gave version 3's floats different last digits on the same machine and code, between
two executions. `chain` runs detrending, search and the gauntlet again, in its own call (stage
1), apart from `analyze_data` (stage 2).
- So no `chain` row has a source proof that it is "the same call with the same inputs" as a
  verdict row.
- Under N2, a `chain` row whose operands are not in the `chain` file itself has absent operands,
  and is a declared limit.
- The `chain` file serializes `candidate.period_days`, `t0_btjd` and `snr`
  (`discover/measure.py:72-75`). Rows whose operands are those three fields can be present in
  `chain` itself.

**Still open before the freeze:**
1. **The reach rule (N1(b) to N1(d)).**
   - For each decision function, its exits with their static status and literal code.
   - The rewrites that change a serialized status after the check returns: `enforce_coverage`,
     `enforce_sensitivity`, `defer_tests`, `classify_v051`, `_with_a0_note`, `power.attach`
     and `stable_consistency_label`.
   - For each row, the output evidence of reach. It is "reach unknown" (a declared limit) unless
     the serialized name, status and literal codes prove the branch was taken. Rows in helpers,
     in loop bodies or with a non-literal status are "reach unknown".
2. **The operands and monotonicity of each numeric and finiteness row, per fixture.**
   - A verified location in the serialized output, or a formula independent of the values.
   - Otherwise a stated reason why it is absent: no field, no formula, unit scaling, `round`, or
     a reassignment between the comparison and the write.
   - An instance rule for rows inside loops.
3. **The freeze commit and Codex's round,** which also asks whether N1 or N2 changes a rule of
   revision 6 (N3).

## Under block O (#218, the decisions of 2026-11-27 (11)): the reach rule, the operands, the manifest

**The reach rule of N1** ([`../tools/reach.py`](../tools/reach.py), unit `reach`, from source
only; [reach-table.json](reach-table.json)). It classes each row of each fixture as reached-if or
reach unknown; the docstring states it in full.
- **Reached-if.** A row is reached-if when:
  - its function is proven executed from the fixture's entries, through calls with a single
    target at unconditional positions, with configuration guards evaluated by the table;
  - the row sits at an unconditional position.

  Its evidence conditions are read after the freeze, only from the fixture's serialized
  non-numeric output: `output-ok` (the file is not an `ERROR` text), and `candidate-present` or
  `candidate-null` (the serialized `candidate` field is an object or `null`).
- **Not reached** only when the output proves every alternative false. Anything else is reach
  unknown, with its reason.
- **The loop rule (O1).** A row inside a loop body, a comprehension or a generator is reach
  unknown in every fixture, and counts once per fixture among the declared limits. Its instances
  cannot be told apart by a serialized status or code.
- **The rule's own changes,** each committed before the run that used it:
  - `discovery is None` added to the guard table, because `chain` binds `discovery = plan.discovery`;
  - the condition on `and`/`or` removed;
  - `check_snr` added to `CANDIDATE_FUNCS`;
  - a guard on `noise` scoped to `attack_candidate`.
- **What was known when those changes were made.** The second run had left the SNR gate's rows
  reach unknown, and with them every chain fixture without a row whose operands are present, so
  zero coverage there. The reasons for the changes stand on their own:
  - the `and`/`or` condition was the rule's own addition, against section 4, which splits a
    conjunction into rows; its example `attenuated` is a second conjunct;
  - the other changes are configuration facts taken from source.

**The operand map** ([operand-map.json](operand-map.json), written from source). It covers the 17
numeric and finiteness rows that are reached-if in some fixture. For each fixture it names:
- the call whose result is serialized, since `v05_tests` and `v052_tests` replace `odd_even`,
  `secondary_eclipse`, `centroid_shift` and `period_alias`;
- each operand's location, or a formula, with its monotonicity statement; or the reason the
  operand is absent.

The instance whose result is serialized may be a call inside the loop of `v05_tests` or
`v052_tests`. Then the row is reach unknown in that fixture, under the loop rule, although the
reach table proves another instance ran:
- `odd_even` in v2 and v2-eb;
- `period_alias` in v3 and v4.

Some locations are conditional (`if_key`). They are present only when the branch that writes the
key ran, and otherwise absent, for the reason given.

**The manifest** ([manifest.json](manifest.json), unit `manifest`, from source and records only)
and the freeze list ([freeze.json](freeze.json)):

| Fixture | Rows | Non-numeric | Reach unknown | Absent | Assessable (integer or configuration; conditional) |
| --- | --- | --- | --- | --- | --- |
| v1 | 159 | 92 | 58 | 1 | 8 (5; 2) |
| v2 | 210 | 120 | 76 | 5 | 9 (4; 3) |
| v2-eb | 210 | 120 | 76 | 5 | 9 (4; 3) |
| v3 | 271 | 155 | 102 | 7 | 7 (4; 3) |
| v4 | 273 | 147 | 114 | 7 | 5 (2; 2) |
| chain-v1 | 115 | 59 | 46 | 8 | 2 (0; 0) |
| chain-v2 | 166 | 87 | 62 | 14 | 3 (0; 0) |
| chain-v2-eb | 166 | 87 | 62 | 14 | 3 (0; 0) |
| chain-v3 | 218 | 113 | 89 | 14 | 2 (0; 0) |
| chain-v4 | 220 | 105 | 101 | 12 | 2 (0; 0) |

- **What the columns mean:**
  - non-numeric rows are listed with a reason class; they are not assessed and are not limits;
  - reach-unknown and absent rows are declared limits;
  - an assessable row is assessed after the freeze when its reach conditions hold on the output.
    It is not reached when they fail, and it becomes absent when a conditional location's key is
    missing.
- **Declared limits:** N = 874, counted per fixture and row. The first is that internal
  selections were not assessed for margin.
- **Not reached and assessed** are known only after the freeze, from the frozen rule and the
  output. No count of them can be given now.
- **Every fixture has at least two assessable rows.** In each chain fixture they are the SNR
  gate's: `math.isfinite(candidate.snr)` and `candidate.snr >= params.min_snr`, with
  `chain:candidate.snr` and the plan's `min_snr`.

## Still to do

- **(c) The freeze commit:** data only and alone, with the trailer `CI: order-proof`. It holds the
  manifest, the comparator's schema, the freeze list, the reach table, the operand map, the
  candidate list and the exact keys. The comparator and the tools are in earlier commits.
- **(d) Codex's round:** one round, a new conversation, read only, with N3's question.
  - It checks the manifest and the span mapping for completeness against the frozen source.
  - Its declared inputs are the view of `verdict-v4.txt` and the search for `refute_version`.
  - Codex is forbidden to open the golden folders.
