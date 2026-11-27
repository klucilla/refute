# Read-only review: the frozen schema and span mapping of the comparator (Refute v0.5.13, #226)

You are a read-only reviewer. This is a new conversation, one round. Do not modify any file. Do
not run project code that writes files. You may read files and run read-only git commands in the
repository at `C:\Projetos\refute`.

**Forbidden to open (any of these voids the review):**
- `docs/validation/v0.5.13/goldens/` and `.cache/v0513/golden/` (the golden outputs: no golden may
  be read before the maintainer approves the comparator and its span mapping);
- `K:\Meu Drive\Pessoal\Segurança`.

## What is frozen

Commit `8b15cede2a64ee37eff08869eae81b3bf5aff19b` (the freeze commit of amendment 2, revision 8,
section 4, pushed alone with the trailer `CI: order-proof`) adds
`docs/validation/v0.5.13/manifests/freeze-226/`:
- **`comparator-schema.json`: the schema under review.** It holds the JSON measurement and exact
  patterns, the exact keys, exact subtree keys, exact key regex, keys not exact under, the report
  templates and the claim exception. Two older schemas exist, `docs/validation/v0.5.13/l4/comparator-schema.json`
  and `docs/validation/v0.5.13/manifests/margin-226/comparator-schema.json`. They are records of
  earlier states and are **not** under review.
- **`freeze.json`:** the fixture list; for ID-BEFORE and NR-A1's three settings, the golden and
  claim-hash records, the source commit each golden record names, the `src` tree and the SHA-256 of
  `tests/baseline_code_v0511.py` at that commit, every golden SHA-256 taken from the records, the
  resolved plans and the error outputs; the comparator, the schema and revision 8, each by
  SHA-256.

**How they were built.** The committed unit `tools/freeze_226.py` built them from records and
source only. The schema comes from `docs/validation/v0.5.13/l4/comparator-schema-parts.json` (the
patterns, templates and decision P2's fields) and `l4/schema-keys.json` (the exact keys, from
`tools/schema_keys.py`). The comparator is `docs/validation/v0.5.13/tools/comparator.py`, at the
SHA-256 `freeze.json` records. Its tests, on synthetic tokens only, are
`tests/test_v0513_comparator.py`.

**Not reviewed by anyone yet:**
- the comparator's corrections under decision P2. They answer items 6 and 7 of your earlier round
  on the revision-6 freeze; the record is `docs/validation/v0.5.13/l4/codex/answer.md`;
- its coverage report under decision R2;
- two additions made with R2:
  - a setting with no file compared is `INCONCLUSIVE`;
  - an alternate setting absent from the freeze list (NR-A2, which runs after the freeze) binds
    only the schema and the reference, and is reported as not bound.

## The rules

- **The governing text:** `docs/plans/v0.5.13-charter-amendment-2-rev8.md`, adopted by the
  maintainer.
  - Section 3.1 is the comparator's rule, with the paragraph on its coverage. Section 3.2 is the
    budget.
  - In section 4, "What still holds for versions 1 to 4" covers the freeze, this review, the
    maintainer's approval by hash, and the void rule. Under the void rule, a numeric span found
    missing afterwards, or a span that covers a byte §3.1 compares exactly, voids the result.
  - There is no margin check for versions 1 to 4.
- **The golden fixtures:** produced by `tests/baseline_code_v0511.py` (`_compute`) for versions v1,
  v2, v2-eb, v3 and v4. Each fixture writes `verdict-<v>.txt` (JSON, the separator
  `---report---`, then the rendered report), `chain-<v>.json`, `error-<v>.json` and
  `plan-<v>.json`.
- **The frozen source:** read it at the source commits `freeze.json` records, for example
  `git show <commit>:src/refute/packs/tess/report.py`. The writers of the serialized outputs are
  the source of truth for which numbers are measurements and which are thresholds, configuration,
  integer counts or IDs.

## Declared inputs (decision K2(c), and what else the agent knew)

1. During an earlier decision (H2), the agent read lines 65 to 124 of ID-BEFORE's
   `verdict-v4.txt`: the list of tests, their roles and the start of `global_ephemeris`.
2. While the package version of decision D4 was weighed, one search of the ID-BEFORE golden folder
   for `0.5.0` or `refute_version` scanned all twenty files. It showed the line
   `"refute_version": null` from each `error-` and `verdict-` file, and nothing from `plan-` or
   `chain-` files.
3. The diagnostic D1a (revision 8, section 1) listed the fields that differ between ID-BEFORE and
   NR-A1 at 1 and 4 threads:
   - `beta`, `amplitude_snr`, `significance`;
   - `semi_amplitude_ppm`, `semi_amplitude_err_ppm`;
   - `box_depth_after_model_ppm`, `box_depth_after_model_err_ppm`.

   Its largest relative difference was 2.12e-9. The agent knew this while the span mapping was
   written.

Weigh whether any of these could have shaped the span mapping. For example, a mapping fitted to
the fields known to differ, with other measurements left exact.

## Questions

1. **Completeness of the span mapping.** Against the frozen source, is any number that the
   writers serialize as a measurement (in `verdict-*.txt` JSON, its report, or `chain-*.json`)
   not mapped as one?
   - Such a number would be compared exactly, and a numerical difference within the budget would
     fail.
   - Check every writer of the fixtures' outputs: test metrics, parameters, holdout rows,
     sensitivity, the report's tables and lines, and numbers inside test messages.
2. **Correctness.** Can a threshold, configuration value, integer count, ID or error record fall
   under the tolerance through a measurement pattern or a report group? Is the exact key regex,
   or the `keys_not_exact_under` exception, too wide or too narrow?
3. **The report templates.** Do they cover every report line that can carry a measurement? Can
   two templates match one line? Does any `exact` or `measurement` group have the wrong role?
4. **The comparator.** Does `comparator.py` at the frozen SHA-256 apply this schema as section
   3.1 says?
   - Review the P2 corrections, the R2 coverage report and the two additions.
   - Does the `INCONCLUSIVE` result or the unbound-alternate path weaken section 3.1?
   - Is the coverage report correct: files compared, numeric pairs compared and differing, the
     largest relative difference?
5. **The freeze list.** Does `freeze.json` hold what revision 8, section 4 requires?
   - the fixture list;
   - the source commits and code digests;
   - the resolved plans;
   - the golden SHA-256 of ID-BEFORE and NR-A1's three settings;
   - the comparator with its schema and span mapping.

   Is anything taken from a source other than the records?
6. **The declared inputs:** could any of them have shaped the span mapping?

## Answer format

- First line: `VERDICT: APPROVABLE` or `VERDICT: NOT_APPROVABLE`.
- Then the blocking items, each with:
  - the file and line;
  - the problem;
  - a concrete fix;
- then the non-blocking items;
- then what you checked and did not check.
