# Blind review: v0.5.13 charter, amendment 2, revision 3

**Manifest check:** all 21 files listed in `MANIFEST.md` match their recorded SHA-256 and byte counts. No mismatch. (`MANIFEST.md` itself is not self-listed; its SHA-256 is `59a5377d…35e58e8`.)

Line numbers below refer to `amendment-2-revision-3.md` unless another file is named.

## 1. Verdict

`NOT_APPROVABLE`

The direction (decision identity, no pin, no v5 run in Step 1) is not what blocks it. Six points in the text do: one loophole, one ambiguity, one vacuous-pass path, one uncheckable condition, one inaccurate statement about a record, and one missing label.

## 2. Blocking items

**1. Lines 163-168 (§4): a near-threshold predicate can be reclassified as a "declared limit" instead of failing.**

Problem: "If serialization uncertainty … could change the predicate or margin result, record the specific unavailable operand" turns exactly the cases the margin check exists to catch into unassessed ones. The golden values are already exposed (D1a), so the present/absent classification can also be made with the values in view. This weakens "results are never tuned to pass a gate" (Process diet 2, item 7).

Replacement for lines 163-168:

> Evaluate both sides of a case-derived threshold using that setting's golden values. Classify each operand as present or absent from the frozen source, the resolved plan and the golden file's schema alone, without regard to any operand value. The frozen manifest fixes that classification. An operand is absent only when no serialized field, and no reconstruction formula that is independent of the values, yields it. Where an operand is present, bound the effect of its serialization by one unit in the last serialized digit of each token, and evaluate the predicate and the margin at both ends of that bound. If the outcome or the margin result differs between the ends, the check **fails**; it is never reclassified as unavailable. A genuine absence in the existing golden is a **declared limit of #226**, never a predicate PASS. A missing required file, hash mismatch, malformed or nonfinite token, or invalid mapping remains a failure under §3.1.

**2. Lines 156-161 (§4): `x` and `t` are not defined for compound predicates, so the result depends on how the manifest author arranges the algebra.**

Problem: for `box_after + 3 * sigma_r < 0.5 * depth` (`excerpts/src-refute-packs-tess-battery_v52.py-L337-340.txt`), writing it as `x = box_after + 3*sigma_r - 0.5*depth`, `t = 0` makes the margin test pass for any nonzero `x`. A margin relative to `max(|x|, |t|)` also does not bound the effect of the §3.2 budget when a side is a sum with cancellation. The arithmetic of reconstruction is not stated either.

Replacement for lines 156-161:

> Evaluate each predicate separately in ID-BEFORE and in each required comparison setting. `x` and `t` are the values of the left and right operand expressions of the comparison exactly as written at the predicate's source location, with no algebraic rearrangement; the manifest quotes that source expression. A conjunction or disjunction is split into its comparisons, each a row, and a non-comparison conjunct such as a finiteness test is its own row. Where both operands are present or can be reconstructed using only that setting's existing golden, compute them in exact rational arithmetic from the serialized decimal tokens, and require finite `x` and `t` and `abs(x - t) > 0.000001 * max(abs(x), abs(t))`. Equality fails, including `x = t = 0`. In addition, recompute `x` and `t` with every mapped measurement `v` replaced by `v * (1 - 0.000001)` and by `v * (1 + 0.000001)`, over all combinations, and require the same predicate outcome and `x != t` at every combination. Thresholds, configuration and integer counts are not varied. The manifest states why each formula is monotone in each measurement over those intervals; a row without that statement fails. Where the predicate is assessable in both the reference and comparison setting, also require identical predicate outcomes. A failed check in either setting leaves #226 unmet even if another setting lacks an operand.

**3. Lines 170-174 (§4) and 229-231 (§6, item c): the margin condition can be satisfied with zero assessed predicates, and nobody approves the list of limits.**

Problem: "satisfied only when the manifest is complete and every assessable check passes" is vacuously true if nothing is assessable. That conflicts with "evidence for every PASS" and "zero coverage as `INCONCLUSIVE`" (Process diet 2, item 7). The unassessed count is unbounded and reaches "#226 passed" with no stop.

Replacement for lines 170-174:

> List each absent operand by case, setting, test, predicate, source location and reason. Record the counts of assessed, failed and unassessed predicates, in total and per golden fixture, test and setting. The margin condition of #226 is satisfied only when the manifest is complete, every assessable check passes, and no coverage is zero: for each golden fixture and setting for which the manifest lists a predicate, at least one predicate is assessed. Zero assessed predicates for a fixture and setting leaves the margin condition unmet, never satisfied. Before #226 is recorded as met, the maintainer approves the list of declared limits and the three counts in #218, citing the hash of the margin record. Carry the full list of declared limits into #226 and every later result that relies on it. Make no supplemental execution to recover an operand.

Replacement for lines 229-231:

> - **(c)** The margin check of section 4 passes on every predicate with present operands, at each of those settings, with no zero coverage as section 4 defines it. Its list of absent operands is recorded one by one as declared limits of #226 and approved by the maintainer in #218 by the hash of the margin record.

**4. Lines 141-146 (§4): "the manifest is complete" is not checkable by deterministic code, and the freeze has no provable order.**

Problem: tracing "every operative numeric predicate" from source is a human or LLM judgment, yet the acceptance rule depends on it (core principle: agents propose, deterministic tests decide). The same holds for the span mapping of §3.1 (line 93-94). "Frozen and hashed" is not "committed and pushed", so git cannot prove the order (charter §8). The "frozen source" is not named, and the records show two different heads (`a150096…` for ID-BEFORE, `ce15411…` for NR-A1).

Replacement for lines 141-146:

> Before the comparator of §3.1 or the margin check reads a golden file, the following are frozen, hashed, committed and pushed in one order-proof commit under the charter's section 8:
> - the fixture list;
> - the source commit and code digest that produced each set of goldens, and the resolved plans;
> - the existing golden files of ID-BEFORE and of NR-A1's three settings, each by SHA-256;
> - the comparator, with its schema and its mapping of numeric spans;
> - the complete manifest, including its classification of each operand as present or absent.
>
> The check does not establish the completeness of the manifest or of the span mapping. Before it runs, Codex reviews both against the frozen source (read-only, one round), and the maintainer approves them in #218 by hash. An operative predicate or numeric span found missing afterwards voids the result: #226 returns to unmet until a corrected manifest passes the same steps, and the first result is preserved.

**5. Lines 71-82 (§2) and 245-247 (§6): the sidecar is to record values that ID-BEFORE's `provenance` does not hold, and ID-AFTER's "recorded numerical environment" has no check.**

Problem: `records/step0-golden-before.json` `provenance` holds `head`, `python`, `numpy`, `scipy`, `system: "Windows"`, `script_sha256`, three thread variables and the two thread-pool entries. It holds no OS version, no processor affinity, no processor model and no OpenBLAS kernel. Line 72 says identity "holds in the numerical environment recorded by ID-BEFORE"; the evidence is two executions on one machine. "In ID-BEFORE's recorded numerical environment" (line 246) is not tied to any field comparison.

Replacement for lines 71-82:

> Versions 1 to 4 get no change of code, pin or configuration. Their **byte-for-byte identity** was observed in two executions on one machine: ID-BEFORE (`step0/golden-before.json`) and NR-A1's inherited default (`step1/comparison-nr-a1.json`, `nr-a1-default`). It is asserted for those executions' recorded numerical environment and for no other. That environment enters the reproduction recipe of each locked claim as a separate dated sidecar (`docs/validation/v0.5.13/numerical-environment.md`). The sidecar maps each locked claim and tag to the ID-BEFORE record and manifest by hash. It records, each with the record and SHA-256 it is copied from:
> - the inherited thread variables and the effective thread counts;
> - both BLAS libraries' identities, versions and threading layers;
> - the versions of Python, NumPy and SciPy;
> - the OS and the processor affinity.
>
> A value that ID-BEFORE's `provenance` does not hold is copied from another existing hashed record of the same execution, named with its hash, or is written as "not recorded by ID-BEFORE". ID-BEFORE's `provenance` holds `system` and no OS version, no processor affinity, no processor model and no OpenBLAS kernel; the sidecar says so. Nothing is measured again or inferred to fill it.
>
> No lock, dossier, tag or recorded byte is edited.

Replacement for the two sentences at lines 245-248 ("The once-only named ID-AFTER … leaves criterion 5 unmet."):

> The once-only named ID-AFTER verifies legacy golden and error-output byte identity, claim-hash identity, and all ten locked-claim checks. Its recorded provenance must equal ID-BEFORE's in every field of `provenance.blas` and in `python`, `numpy`, `scipy` and `system`. A difference in any of those fields, a byte mismatch or a missing proof leaves criterion 5 unmet.

**6. Lines 190-191 (§4) and 223-233 (§6): a post-hoc pass on exposed records is called "#226 passed" with no label, and the text is inconsistent with Process diet 2, item 4.**

Problem: lines 190-191 invoke item 4's diagnostic clause ("replaces or re-scores no recorded result"), while §6 uses that diagnostic's result as acceptance evidence that turns a recorded `STOP` into "passed". Item 4 says findings on exposed data only generate hypotheses, and acceptance needs unexposed or prospective data. The numeric part of criterion (b) was also known to hold when the rule was written (D1a: 2.12e-9 against 1e-6). The charter's §2 says "A close with declared limits does not satisfy a failed precondition"; the amendment puts declared limits inside a "passed" precondition without saying how Part B may rely on it. The byte non-identity at 1 and 4 threads is not among the "declared limits" that line 239 carries forward.

Replacement for lines 190-191:

> The check is a new computation over existing, exposed records, and its rule was written with NR-A1 and D1a known. Its question, quantity and cases are logged before it runs. It changes no recorded result: NR-A1's `STOP` stands as recorded. Its result is exploratory and post hoc. It is used here as evidence for an engineering precondition of an exploratory phase, under the maintainer's decision E1, and for nothing else. It is not a confirmation under Process diet 2, item 4, and it supports no claim, verdict or acceptance of a scientific result.

Insert after line 233, inside the quoted block:

> Wherever #226 is cited as met under this rule (in #226, the phase report, Part B's charter and every later result that relies on it), it carries the label **'#226 met under amendment 2 (decision identity, post hoc, on exposed records); the charter's byte-identity rule was not met at 1 and 4 threads (NR-A1: STOP); N declared limits'**, with N from the margin record. Under the charter's section 2, Part B may rely on #226 only with that label, and only if the maintainer's approval of this amendment says so explicitly.

## 3. Non-blocking items

1. **Lines 86-87 and 227.** §3 states a rule for "any other thread setting", but only 1 and 4 threads are assessed, both already exposed. One setting never run before, executed once after the freeze of item 4, would be the only prospective test. It is a rerun and would need its own approval; this is the maintainer's choice.
2. **Lines 91-92.** "Against its recorded payload" should read "against the payload recorded for that same setting". The raw goldens of the 1- and 4-thread settings and their hash payloads are not in this dossier; if they were not kept, §4's "no supplemental execution" leaves #226 unmet.
3. **Lines 96-97 and 158.** Nonfinite tokens are rejected, yet the source guards `math.isfinite(sigma_r)`, so a nonfinite value may be a legitimate serialized output. If any ID-BEFORE golden has one, (b) cannot be met. Say whether that is intended.
4. **Lines 137 and 158-159.** "Equality fails" also applies to integer count cutoffs. A count exactly at its minimum fails the margin check although counts are compared exactly and cannot drift. Decide this before the result is seen, not after.
5. **Lines 178-184.** `battery_v51.py:41` in the excerpt is only `def _wls(x, flux, err):`; no condition-number guard is shown. The loop excerpts show a `LinAlgError` break. The mapping of v3 and v4 to `battery_v51` and `battery_v52`, and "all three configured peaks", cannot be checked here.
6. **Lines 185-186.** The values `3` and `0.5` are not in the excerpt, which shows only `ATTENUATION_SIGMAS` and `ATTENUATION_FRACTION`. The amendment's rendering also omits the `math.isfinite(sigma_r)` conjunct.
7. **Lines 203-205.** "Four thread variables": `THREAD_VARIABLES` is not in the excerpt, and ID-BEFORE and NR-A1 record three. The rest of §5's description matches `environment.py` lines 54-104 (the five pool keys, no `threading_layer`, no SciPy version in `numeric_runtime`).
8. **Lines 197-201 (§5).** A Part A amendment sets a rule for version 5 onward. It is unclear whether the absent-operand allowance and "no supplemental execution" carry forward. Suggested addition: "For version 5 onward, an absent operand leaves the margin condition unmet unless that version's own approved charter declares it a limit before the evidence is produced."
9. **Lines 108-111 and 257-259.** The ten tag checks at 1 and 4 threads recompute nothing, as the text itself says, so they add no numerical evidence. They cost CPU and disk, and the amendment reserves nothing against the charter's caps or its day-2 checkpoint.
10. **Lines 101-103.** The "baseline exception" for `claim.generated.yaml` should cite the record and hash that hold the error record and the decision that accepted it.
11. **Line 43.** The effective thread counts come from a companion process, not the process that produced the goldens (`child_threadpool_info`). Worth stating in the sidecar.
12. **Line 11.** Amendment 1 is marked "proposed" in its own file; whether it is approved is not shown here.
13. **`charter.md` lines 539-540 and 563.** Stop 2's pin clause and risk 1 ("The pin moves a byte") become stale under this amendment; line 237 covers stop 2's acceptance clause only.

## 4. What I checked and did not check

Checked:
- SHA-256 and size of all 21 files against `MANIFEST.md`.
- The charter hash quoted at line 10 (`2832dc48…c230c813`) against `charter.md`.
- §1's NR-A1 statements against `records/step1-comparison-nr-a1.json`: default equal, 24 threads, both OpenBLAS versions, `verdict-v3.txt` and `verdict-v4.txt` differing at 1 and 4 threads, claims equal, outcome `STOP`.
- §1's D1a statements against `records/step1-diag-golden-diff.json`: 13 of 2,259 and 15 of 2,385 lines, zero non-numeric lines, the seven fields, maximum 2.1209e-9.
- §1's survey summary against `issue-231.json` including its correction comment; `DEFAULT_RELATIVE_TOLERANCE = 1e-6` at `dossier.py:29`.
- §4's and §5's source statements against the `excerpts/src-*` files.
- Consistency with the charter (Step 0, Step 1, Step 5, exit criteria, stops, §2, §8, §12), amendment 1, and the five `CLAUDE.md` excerpts.

Not checked (not in the dossier):
- ID-BEFORE's claim-hash payload and the ten tag checks ("joint PASS", line 56).
- The raw golden files, so "three configured peaks" and the operand mappings.
- The affinity of processors 8 to 31 (line 40).
- Revisions 1 and 2 and the Codex round records, so every "as written" quotation and the tolerance history (line 127).
- The maintainer's decisions E1, E2 and F1 in #218.
- Source beyond the excerpted lines, including `_wls`, `_ls_peak`, the constants and `THREAD_VARIABLES`.
- Whether the cited commits exist. I ran no git, no network and no project code, and modified nothing.

No fact in this report comes from memory; everything is from the dossier folder.
