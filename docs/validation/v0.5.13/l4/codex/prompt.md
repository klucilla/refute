# Read-only review: completeness of the frozen margin manifest and span mapping (Refute v0.5.13, #226)

You are a read-only reviewer. Do not modify any file. Do not run project code that writes files.
You may read files and run read-only git commands in the repository at `C:\Projetos\refute`.

**Forbidden to open (any of these voids the review):**
- `docs/validation/v0.5.13/goldens/` and `.cache/v0513/golden/` (the golden outputs: no golden may
  be read before the maintainer approves the manifest);
- `K:\Meu Drive\Pessoal\Segurança`.

## What is frozen

Commit `ba94f3a6ccca09c6868ee00d80429bb09ac01be2` (the freeze commit, pushed alone with the
trailer `CI: order-proof`) adds `docs/validation/v0.5.13/manifests/margin-226/`:
- `manifest.json`: the margin manifest;
- `comparator-schema.json`: the comparator's schema and mapping of numeric spans;
- `freeze.json`: the fixture list, the recorded source commits and golden hashes, and the SHA-256
  of the comparator, schema and manifest;
- `reach-table.json`, `operand-map.json`, `decision-layer.json` and `schema-keys.json`: the
  inputs.

They were built from source and records only, by these committed tools:
- `docs/validation/v0.5.13/tools/decision_layer.py` (the candidate rows; reachability; configuration
  guards);
- `tools/reach.py` (the reach rule);
- `tools/manifest.py`;
- `tools/schema_keys.py`;
- `tools/comparator.py` (the comparator of section 3.1).

The human-written part is `operand-map.json`. The record is `docs/validation/v0.5.13/l4/README.md`.

## The rules

- **The governing text:** `docs/plans/v0.5.13-charter-amendment-2-rev6.md`, adopted. Sections 3.1,
  3.2 and 4 are what matters here.
- **The golden fixtures:** produced by `tests/baseline_code_v0511.py` (`_compute`), for versions
  v1, v2, v3, v4 and v2-eb. Each fixture writes `verdict-<v>.txt`, `chain-<v>.json`,
  `error-<v>.json` and `plan-<v>.json`.
- **The maintainer's decisions of 2026-11-27 (10)** (#218), given in Portuguese and rendered here:
  - **N1, rows behind early exits** (an interpretation of revision 6, always on the stricter side):
    - (a) the condition of an early exit that leads to a serialized status, class, reason or
      verdict is itself a row of the decision layer;
    - (b) a row is assessed in a fixture and setting only if it is REACHED there. Reach is decided
      by a frozen rule that reads ONLY the serialized non-numeric output (statuses and reason
      codes) of that fixture, after the freeze. A row not reached has no margin check and does
      not count as assessed;
    - (c) if the serialized output does not show whether the branch was taken, the row is "reach
      unknown": not assessed, and counted among the declared limits (it enters N);
    - (d) the reach rule, and the table tying each row to the output that proves its reach, enter
      the frozen manifest.
  - **N2:** `chain` (stage 1) is its own fixture. Its statuses are already compared byte for byte
    by section 3.1. In the margin check, a `chain` row may use operands of the verdict of the same
    version only if source proves, in the manifest, that it is the same call with the same
    inputs. Without that proof the operands are absent, and the row is a declared limit (it enters
    N).
  - **N3:** N1 and N2 are a recorded interpretation, not a rule change. You are asked explicitly
    whether they change any rule of revision 6.
  - **O1:** an explicit rule for rows inside loops.
- **Rows inside loops:** the manifest's rule is that a row in a loop body, comprehension or
  generator is reach unknown in every fixture.

## Declared inputs (earlier reads of golden content by the agent, before any of this was built)

1. During an earlier decision (H2), the agent read lines 65 to 124 of ID-BEFORE's
   `verdict-v4.txt`: the list of tests, their roles and the start of `global_ephemeris`.
2. While the package version of decision D4 was weighed, one search of the ID-BEFORE golden folder
   for `0.5.0` or `refute_version` scanned all twenty files. It showed the line
   `"refute_version": null` from each `error-` and `verdict-` file, and nothing from `plan-` or
   `chain-` files.

Weigh whether either read could have shaped the manifest or the span mapping.

## Questions

1. **Completeness of the decision layer.** Against the source at the freeze commit, is any
   predicate of the decision layer (amendment 2, revision 6, section 4, first paragraph) missing
   from `decision-layer.json` for a fixture where it runs? Check especially:
   - the reachability and configuration-guard pruning (`GUARD_TABLE`, `LOCAL_GUARDS`);
   - the call resolution through imports;
   - the version dispatch of `v05_tests`, `v052_tests` and `conclude_analysis`.
2. **The reach rule.** Is `reach.py`'s classification sound and strict? Can it call a row
   reached-if when the serialized output could not prove its reach, or miss an early exit? Is the
   loop rule applied consistently?
3. **The operand map.** For each of the 17 rows in `operand-map.json`, are these correct against
   source?
   - the producer (which call's result is serialized in each fixture);
   - the locations and formulas, read exactly as the comparison is written;
   - the conditional (`if_key`) locations;
   - the monotonicity statements;
   - the reasons for absence, and the `reach_unknown` overrides.

   Is any assessable row wrong, or any absent row actually present?
4. **The span mapping.** Are the comparator's measurement and exact JSON patterns, exact keys,
   exact subtree keys and report templates in `comparator-schema.json` complete and correct? Can a
   threshold or configuration number fall under the tolerance? Can a measurement that must be
   tolerated be compared exactly by mistake? Does `comparator.py` implement section 3.1?
5. **N3, explicitly:** do N1 or N2, as the maintainer wrote them, change any rule of amendment 2,
   revision 6? Answer **yes** or **no**, with the reason. If yes, name the rule and the change.
6. **The declared inputs:** could either earlier read have shaped the manifest or the span
   mapping?

## Answer format

- First line: `VERDICT: APPROVABLE` or `VERDICT: NOT_APPROVABLE`.
- Second line: `N3: yes` or `N3: no`.
- Then the blocking items, each with:
  - the file and line;
  - the problem;
  - a replacement text or concrete fix;
- then the non-blocking items;
- then what you checked and did not check.
