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

## What does not exist yet

- **(a) The manifest of the decision layer.** It follows section 4's first paragraph, and the plan
  is:
  1. A committed tool finds the predicates mechanically from source. A predicate qualifies when it
     reaches a serialized status, class, eligibility flag, reason code or verdict only through
     branch tests, assignments, returns, arguments and boolean operators. This covers:
     - J1's direct sites;
     - a comparison that sets a named boolean a later branch tests (`attenuated`);
     - functions whose returned value carries the decision (`power`, `a0`, `a0_v4`,
       `core/inconclusive`).
  2. Every J1 atom is either a row or listed with a reason class.
  3. Each row is attributed to its fixtures by version dispatch, never by an outcome.
  4. Each numeric row gets its operands' locations in the serialized outputs, or a reconstruction
     formula, from source, the plan and the schema only. The plan comes from source too:
     `synthetic.discovery_*_plan_dict` and the `params` defaults. The `plan-` goldens stay
     unopened.
  5. Each row states why its formula is monotone in each measurement.
- **(c) The freeze commit.** The tools and their tests go in earlier ordinary commits. The freeze
  commit holds data only: the fixture list, the code digest, the comparator's SHA-256, the frozen
  schema, the manifest and the raw goldens' hashes. It is pushed alone, with the trailer
  `CI: order-proof`.
- **(d) Codex's round.** One round, in a new conversation, read only. It checks the manifest and
  the span mapping for completeness against the frozen source. The declared inputs are the view of
  `verdict-v4.txt` and the search for `refute_version`. Codex is forbidden to open the golden
  folders.
