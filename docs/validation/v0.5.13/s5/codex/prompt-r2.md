# Round 2 (same conversation): the corrected comparator, schema and span mapping, and NR-A2's manifest

You are the same read-only reviewer as in round 1 of this conversation. The rules of round 1
still hold: do not modify any file, and do not run project code that writes files.

**Forbidden to open:**
- `docs/validation/v0.5.13/goldens/`;
- `.cache/v0513/golden/`;
- `K:\Meu Drive\Pessoal\Segurança`.

## What the maintainer decided after your round 1 (#218, decisions S1 to S5, given in Portuguese and rendered here)

- **S1.** Correct your six blocking items, with tests on synthetic tokens only and without reading
  a golden:
  1. `max_duration_hours`, `max_event_snr`, `max_timing_sigma_days`, and any other computed
     measurement that the name rule catches, become measurements, with tolerance;
  2. configuration is always exact: tighten the broad patterns;
  3. see S2;
  4. malformed values fail, and a valid change of notation of a measurement number is accepted by
     the numeric comparison;
  5. the claim exception is compared by the bytes of the record;
  6. see S3.
- **S2.** Item 3 is a decision, not a rule change. The message lines, in the JSON and in the
  rendered report, stay compared byte for byte, with no tolerance. This is declared in the schema,
  per message line, explicitly. A message that changes is a failure.
- **S3.** NR-A2 uses option A: a new file, with `identity.py` intact. The unbound path leaves the
  comparator. NR-A2 is bound as follows:
  - (a) NR-A2's manifest is committed and pushed alone, with the order proof, before it runs;
  - (b) the executor writes, at the end, a record with the SHA-256 of each output, committed before
    any read by the comparator;
  - (c) the comparator binds to that record and refuses any file that does not match.
- **S4.** Zero files compared gives `INCONCLUSIVE`, never `PASS`. The unbound path is replaced by
  S3.
- **S5.** A new freeze, alone, with its order proof; `8b15cede` stays as a record. Then this
  round, on the schema, the span mapping, the comparator and NR-A2's manifest (not yet pushed).

## What changed

**The code:** commit `735b075c369895170bc6718263b6dca54f39b159`.
- `docs/validation/v0.5.13/tools/comparator.py`: its docstring maps each change to S1 to S4.
- `docs/validation/v0.5.13/l4/comparator-schema-parts.json`. Its fields:
  - `s1`, `computed_keys_despite_name`, `exact_key_exempt_paths`, `exact_by_sibling`;
  - `message_lines`;
  - the template `gauntlet-row`, with `exact_line`;
  - two new exact patterns.
- `docs/validation/v0.5.13/tools/identity_v2.py`: new, not run.
- `docs/validation/v0.5.13/tools/freeze_226.py`: the `prospective` entry.
- `tests/test_v0513_comparator.py`: 36 tests.

**The freeze:** commit `780d49121cbc837ad870a5265dcae76365696dbd`, pushed alone with `CI: order-proof`.
- It adds `docs/validation/v0.5.13/manifests/freeze-226-s5/`, holding `freeze.json` and
  `comparator-schema.json`. That schema is the one under review.
- The folder `manifests/freeze-226/` (commit `8b15cede`) is the record you reviewed in round 1.

**NR-A2's manifest (draft, not committed):** `.cache/v0513/nr-a2/manifest.json`. Its SHA-256 is in
`freeze.json`, `prospective.nr-a2-t2.manifest.sha256`. Under S3(a), the commit of the manifest must
carry those bytes.

**Two choices of the agent, for your judgment:**
- The effective detrending windows stay measurements:
  - `detrend_window_days` (`battery.py:645` and `816`) is the larger of a plan value and a
    multiple of the measured period;
  - `hidden_detrend_window_days` (`holdout.py:1184`).

  Which branch of the max is taken is treated as an internal selection, a declared limit of #226.
- In `centroid_v5.py:347`, the sensitivity `alternative` "source offset" stays tolerated. It
  scales the arcsec threshold, which comes from the measured pixel scale.

## Questions

1. Are your six blocking items of round 1 resolved, each as S1 to S4 decide? For each one, say
   resolved or not, with file and line.
2. Is any computed measurement still exact by the name rule, or any configuration value still
   tolerated, under the new schema, against the frozen source?
3. Do S2's exact message lines and the `gauntlet-row` template introduce an ambiguity or a gap?
4. Does the NR-A2 binding in `comparator.py` (`bind`, `bind_prospective`) meet S3 (a) to (c)? Can
   any comparison emit `PASS` without NR-A2's own evidence, or with bytes other than those whose
   SHA-256 was checked?
5. Is NR-A2's manifest complete and consistent with revision 8, sections 3 and 6(c), and with
   `identity_v2.py`?
6. Does the new `freeze.json` hold what revision 8, section 4 requires, plus the prospective entry?

## Answer format

- First line: `VERDICT: APPROVABLE` or `VERDICT: NOT_APPROVABLE`.
- Then the blocking items, each with:
  - the file and line;
  - the problem;
  - a concrete fix;
- then the non-blocking items;
- then what you checked and did not check.
