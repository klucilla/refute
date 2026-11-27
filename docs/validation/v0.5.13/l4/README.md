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
synthetic tokens only: 14 passed, 0 failed (JUnit XML).

**A property of the design.** The schema's classification is consulted only when two tokens
differ. So an incomplete measurement list can only make the comparator fail; it can never let it
pass. Lists that are too wide are what the review must catch.

**The schema's exact keys** ([schema-keys.json](schema-keys.json), the committed unit
`schema-keys`, from source only):
- **Rule 1:** the fields of the plan models in `params.py`, except the names of measurement
  outputs. These are the fields and `to_dict` keys of `Candidate` and `Ephemeris`, and the
  literal keys of `key_values` in `build_result`.
- **Rule 2:** the keys of `thresholds` dicts on the golden path.
- **The result:** 212 exact keys. Five plan-field names are left out as measurement outputs:
  `depth_ppm`, `duration_hours`, `period_days`, `snr` and `t0_bjd`.
- **D1a's differing fields:** none of them is an exact key. Their names were known when the
  schema was written.
- **The first run:** it used rule 1 without the exception for measurement names. Its output was
  never committed and is replaced by this one. The change was committed before the second run.

**The schema's other parts, a draft** ([comparator-schema-parts.json](comparator-schema-parts.json)),
written from `dumps_json`, `build_result`, `chain` and `render_report`:
- the measurement and exact JSON patterns of `verdict` and `chain`;
- eleven report templates, each with its source lines. A test checks that each template compiles,
  that its groups are the declared ones, and that each synthetic example line matches exactly one
  template.

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
