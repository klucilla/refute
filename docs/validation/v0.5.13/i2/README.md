# I2: the preparation of #226 under amendment 2 (stopped before the freeze)

The maintainer's decision I2 (#218, comment 7222329150), under amendment 2, revision 4 (adopted,
item I1). Labels: `exploratory`, `method_status: not_validated`.

**No check of amendment 2 ran, and NR-A2 did not run.**

| Part | State |
| --- | --- |
| (a) The raw goldens in git | **Done.** Commit `a9044264`: 80 files in `docs/validation/v0.5.13/goldens/<setting>/`, about 1.5 MB, so the Drive rule does not apply. Before the copy, the unit `golden-commit` checked each file's SHA-256 against the payload recorded for the same setting, read from the committed records, and checked that no file holds a CR byte. After the commit, its `verify` mode found all 80 committed blobs equal to their records. |
| (b) The sidecar | **Done.** [`../numerical-environment.md`](../numerical-environment.md). Each value is copied from a committed record named by its blob's SHA-256; what no record holds is "not recorded by ID-BEFORE". |
| (c) The comparator, schema, span map, fixture list, source commits and complete margin manifest | **Not complete.** Only the countable inventory exists (below). |
| (d) The freeze commit | **Not made.** |
| (e) Codex's completeness review | **Not run.** |

## (c): the inventory, and why the work stopped there

The committed unit `predicate-inventory` (`tools/predicate_inventory.py`) wrote
[predicate-inventory.json](predicate-inventory.json). It reads source only.
- **The modules.** It follows, statically and to closure, the `refute` imports of the modules
  that `tests/baseline_code_v0511.py` uses to compute the goldens. It finds **73 modules**.
- **The source is the same where the goldens were made.** Every module's file is identical at
  `HEAD`, at ID-BEFORE's head (`a150096de04e4caae9ef0042e6ae4c458823ac9e`) and at NR-A1's head
  (`ce154119c7f05ee4d317e13eecc9b0fd0edb9476`), except `src/refute/__init__.py`, which differs by
  the version string only (0.5.12).
- **The sites:** **2,746**. There are 2,103 comparisons and 643 calls of a selection or a guard:
  `isfinite` 154, `max` 130, `sorted` 89, `min` 82, `any` 77, `all` 46, `where` 33, `clip` 12,
  `argmin` 11, `minimum` 4, `isnan` 3, `argmax` 1, `maximum` 1.

Section 4 requires each operative numeric predicate to have its own row, with:
- its verbatim source expression;
- the split of conjunctions;
- the integer or configuration flag;
- a monotonicity statement;
- the exact operand locations in the serialized schema, with branch conditions.

Every other site needs a written reason. **0 of the 2,746 sites are resolved.** The comparator, the
schema and the numeric span map of the 20 golden files per setting do not exist either.

**The work stopped here on purpose.** A freeze or a Codex round on a manifest known to be
incomplete would spend both one-shot steps on a result that has to fail.

**A disclosure.** Earlier in this session, before I2, the agent read part of
`.cache/v0513/golden/before/verdict-v4.txt`: lines 65 to 124, the list of tests, their roles and
the start of `global_ephemeris` (on 2026-11-27, during H2). That is a view of golden values. Since
I2 started, no `chain-`, `verdict-` or `error-` golden has been opened; the tools hash their bytes
only. Revision 4 requires the classification of operands without regard to values; this view is to
be weighed in the manifest's review.

## What finishing (c) takes (an estimate, for the maintainer)

1. **Pre-classify** the 2,746 sites mechanically, in a committed tool: non-numeric comparisons
   (`is None`, `isinstance`, strings, membership) get a written reason class. The rest are candidate
   rows.
2. **Write a row per operative numeric predicate** from the source, test by test, for the
   batteries of versions 1 to 4. Each row ties to the serializing code: `build_result`,
   `render_report`, the chain writer and `dumps_json`. Rows are conditional on the branches that
   write their fields.
3. **Build and test the comparator, the schema and the span map** on synthetic tokens only.
4. Then the freeze commit, alone, with its order proof, and Codex's one round (I2(d), (e)).

This is several working sessions, not one. Each step is a commit of tools and records; nothing
runs a check.
