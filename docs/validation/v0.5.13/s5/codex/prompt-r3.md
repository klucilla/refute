# Round 3 (same conversation, the last one under S5): the corrections of your round 2

You are the same read-only reviewer. The rules of rounds 1 and 2 still hold:
- do not modify any file, and do not run project code that writes files;
- forbidden to open: `docs/validation/v0.5.13/goldens/`, `.cache/v0513/golden/` and
  `K:\Meu Drive\Pessoal\Segurança`.

Under the maintainer's decision S5, this is the last round. After it the agent stops, and the
maintainer approves the comparator by hash, or not.

## What changed after your round 2

- **The code:** commit `b1950d06c12d58adf012bf1f51b5063ecf34f2cf`.
  - `docs/validation/v0.5.13/tools/comparator.py`. Its docstring has a paragraph "Corrections
    after Codex's round 2"; see `receipt_ok`, `journal_entries`, `head_digests`,
    `journal_bound`, `bind_prospective`, `claim_values`, `_markers` and the integer-form rule in
    `compare_json`.
  - `docs/validation/v0.5.13/l4/comparator-schema-parts.json`:
    - the new exact patterns;
    - `message_lines` (with `chain`);
    - the `cadence-row` regex;
    - `group_markers` of `parameters-line`.
  - `docs/validation/v0.5.13/tools/freeze_226.py`: the prospective entry gains `journal`,
    `units`, `fixture_code`, `src_tree` and `fixture_code_sha256`.
  - `docs/validation/v0.5.13/units/nr-a2-t2-golden.json` and `nr-a2-t2-claims.json`: new, not
    run.
  - `tests/test_v0513_comparator.py`: 39 tests.
- **The freeze:** commit `2e86f48442f2a8c009075e5f346e48776c783696`, pushed alone with
  `CI: order-proof`. It adds `docs/validation/v0.5.13/manifests/freeze-226-s5r3/`, which holds
  the schema under review.
  - Its order-proof receipt is written after this round starts, so it is not in the checkout yet.
  - The freeze `780d4912` of round 2 now has a committed receipt,
    `docs/validation/v0.5.13/order-proofs/e406e728dc97231ee7807493b66b0620083930a5013f04a5d02b1dc36b043a4e.v2.json`.
- **NR-A2's manifest (not committed):** `.cache/v0513/nr-a2/manifest.json`. Its SHA-256 is in the
  new `freeze.json`, `prospective.nr-a2-t2.manifest.sha256`.

**The agent's answers to your round-2 items:**
1. These are now exact:
   - `tests[*].inputs.**`;
   - `target_tmag`, `median_crowdsap` and `stellar_mass_msun`;
   - the neighbours' `tmag` and `separation_arcsec`;
   - `**.detrend_window_days` and `**.hidden_detrend_window_days`.

   The effective windows are therefore compared exactly, even when the measured period sets
   them. That is the conservative side.
2. `message_lines` now lists:
   - `temporal_diagnostic.message`;
   - the temporal diagnostic's per-year reasons and inability reasons;
   - `chain`'s `verdict_reason` and `stage_verdict_reason`.
3. The changes:
   - `cadence-row` matches a row by its structure, so a malformed fraction is validated and fails;
   - `parameters-line` accepts `None` only in `period_err` and `epoch_err`;
   - a pair of integer-form tokens is an integer count, compared exactly;
   - a mixed pair (`1` and `1e0`) on a measurement path is compared by value.

   Python's JSON writer never turns an `int` into a float token, so a count cannot meet the
   mixed rule.
4. A claim entry is compared by the raw bytes of its key and its value.
5. The receipt is checked for its schema, its path, the commit it attests (the commit that last
   changed the manifest) and its files (the manifest alone; for the freeze, the folder's two
   files). The receipt itself must be committed.

   Each NR-A2 record is bound to exactly one run of its authorized unit in the committed journal
   (`git show @:docs/validation/v0.5.13/log.jsonl`). That run must have:
   - the frozen unit spec and `identity_v2.py` in `identity_sha256`;
   - `env` at 2;
   - this manifest as `order_proof`;
   - a single `after` with status `ok` and exit 0;
   - `outputs_sha256` equal to the committed record.

   The records' head must have the frozen `src` tree and fixture code.
6. The manifest has changed:
   - it names the freeze folder `freeze-226-s5r3`;
   - it states the authorized tree. The `src` tree differs from ID-BEFORE's only in
     `src/refute/__init__.py`, the package version, at commit `124bdd92`; the goldens do not
     serialize it;
   - the two unit specs exist, with their `outputs` mapping;
   - their SHA-256 are in the freeze.

## Questions

1. Are your round-2 blocking items 1 to 6 resolved? For each one, say resolved or not, with file
   and line.
2. Does anything in these corrections open a new path to a `PASS` without the evidence that
   section 3.1 and decision S3 require, or make a configuration value tolerated, or make a
   computed measurement exact?
3. Is NR-A2's manifest ready for its commit alone, consistent with the freeze and the unit specs?

## Answer format

- First line: `VERDICT: APPROVABLE` or `VERDICT: NOT_APPROVABLE`.
- Then the blocking items, each with:
  - the file and line;
  - the problem;
  - a concrete fix;
- then the non-blocking items;
- then what you checked and did not check.
