# Blind review 3: v0.5.13 charter, amendment 2, revision 7

**Manifest check:** all 42 files listed in `MANIFEST.md` match their recorded byte counts and SHA-256. No mismatch, no missing file, no unlisted file. `MANIFEST.md` is not self-listed; its SHA-256 is `d2b442e9fbe2e3a038e5294beb21e8e88a509aa2b5a10e2879b50f0f713a51c7`.

Line numbers refer to `amendment-2-revision-7.md` unless another file is named.

## 1. Verdict

`NOT_APPROVABLE`

The direction P1 (the margin check leaves versions 1 to 4, declared as a limit and named in the label) is not what blocks it. Four points in the text do:
- the comparator's safeguards were dropped along with the margin manifest;
- "the freeze commit of section 4" now has two candidates;
- text kept from revision 6 still makes the margin check a condition of #226;
- the stated reason for P1 is not what the cited manifest records.

## 2. Blocking items

**1. Lines 241-246 (§4): the review, approval and void rule of the span mapping no longer apply to versions 1 to 4.**

Problem:
- The bullet keeps only the freeze. "The rest of this section" is assigned to version 5 onward.
- That rest includes the paragraph at line 262: Codex's review of the span mapping against the frozen source, the maintainer's approval by hash, and the rule that a missing numeric span voids the result.
- It also includes decision K2(c) (lines 287-290) and the status paragraph of blind review 1, item 6 (line 318).
- The span mapping decides which bytes get the `1e-6` tolerance and which are compared exactly. Under revision 7 it is written by the agent with D1a known, and nobody reviews or approves it before it decides #226.
- This undoes the part of blind review 1, item 4, that concerned the span mapping ("agents propose, deterministic tests decide").
- Without line 318, the comparator's run on NR-A1's exposed records has no statement that it is logged beforehand, exploratory and post hoc (Process diet 2, item 4).

Replacement for lines 241-246:

> - **What still holds for versions 1 to 4.** These parts of the quoted text below still apply, with "the comparator's schema and span mapping" read where the text says "the manifest":
>   - **The freeze.** The fixture list, the source commits and code digests, the resolved plans, the SHA-256 of each golden file of ID-BEFORE and of NR-A1's three settings, and the comparator with its schema and span mapping are frozen, hashed, committed and pushed in one order-proof commit under the charter's section 8, before the comparator of §3.1 reads a golden file and before NR-A2 runs.
>   - **The review and the approval.** The comparator does not establish the completeness or the correctness of its own schema and span mapping. Before it reads a golden file, Codex reviews both against the frozen source (read-only, one round), with the disclosure of decision K2(c) as an input, and the maintainer approves them in #218 by hash.
>   - **The void rule.** A numeric span found missing afterwards, or a span found to cover a byte that §3.1 compares exactly (an ID, path, version, integer count, configuration value, threshold or error record), voids the result: #226 returns to unmet until a corrected comparator passes the same steps, and the first result is preserved.
>   - **The status of the result.** The paragraph "Blind review, item 6, as written" at the end of this section applies to the comparator's run on NR-A1's records, with "the check" read as that run.
> - **What applies from version 5 onward.** Everything else in this section, including the margin manifest, the decision layer and its declared limit on internal selections, applies from version 5 onward (section 5).

**2. Lines 426-430 (§7), with lines 162 and 394-396: "the freeze commit of section 4" is ambiguous.**

Problem:
- Two freeze commits now exist or are planned: `ba94f3a…` (made under revision 6) and the new one.
- Lines 162 and 394-396 let NR-A2 run "after the freeze commit of section 4". Read literally, `ba94f3a…` already satisfies that.
- The comparator was "corrected under decision P2" after that commit, so NR-A2 could run before the corrected comparator is frozen.
- NR-A2 is the only prospective evidence. Its record shows which files differ, so the comparator must be frozen before it runs (pre-registration order, Process diet 2, item 7).

Replacement for lines 426-430:

> - **A freeze commit made under revision 6** exists (section 1): `ba94f3a6ccca09c6868ee00d80429bb09ac01be2`. It is a record. It is not "the freeze commit of section 4" of this revision. For versions 1 to 4 there is no margin manifest and no margin check.
> - **A new freeze commit** is made after the adoption of this revision, before the comparator reads a golden file and before NR-A2 runs. It is "the freeze commit of section 4" wherever sections 3, 4 and 6 name it. It holds the fixture list, the source commits and code digests, the resolved plans, the golden files' SHA-256, and the corrected comparator with its schema and span mapping.

**3. Lines 163-164, 214-215, 385-388 and 410-419: text kept from revision 6 still makes the margin check a condition of #226.**

Problem:
- Line 214-215 (§3.2) says "The independent margin check separately requires clearance from the decision cutoffs". For versions 1 to 4 nothing does any more. This sentence is part of the reasoning the `1e-6` budget is submitted on "for explicit judgment".
- Lines 385-387 (§6) say a failed "assessable margin check" leaves #226 unmet, and that the absent-operand allowance applies.
- Line 164 sends NR-A2 to "sections 3, 4 and 6".
- Lines 413-419 list "the margin manifest and check of section 4" as an open item of #226.
- Each contradicts lines 156-158 and 230. The acceptance rule of #226 must read one way only.

Replacement: insert after line 246 (after the bullets of item 1 above):

> **Text kept from revision 6 that names the margin check.** For #226 and versions 1 to 4 it is read as follows. Nothing in it makes a margin check, a margin record, a list of absent operands or a count N a condition of #226.
> - **Section 3, NR-A2:** in "(sections 3, 4 and 6)", section 4 means only the freeze, the review and the void rule above.
> - **Section 3.2:** "The independent margin check separately requires clearance from the decision cutoffs" holds from version 5 onward only. For versions 1 to 4 no check requires clearance from the decision cutoffs, and the `1e-6` budget is judged without it.
> - **Section 6:** "or assessable margin check" and "The absent-operand allowance in §4 applies only to the margin check" have no effect on #226. "Its declared limits" are the limits that the label of section 6 names.
> - **Section 7:** its first four bullets describe the state under revision 6. The paragraph "The open items under revision 7" governs.

**4. Lines 116-118 (§1) and 233-235 (§4): the stated reason is not what the manifest records.**

Problem:
- Both passages say the goldens "do not record the operands of most decisions".
- `records/margin-226-manifest.json` has 923 numeric and finiteness rows over the ten fixtures: 50 assessable, 87 `absent`, 786 `reach-unknown`.
- The 874 declared limits are 1 (internal selections) + 786 + 87.
- So 786 of the 873 specific limits are "reach unknown": 327 "its function is not proven executed", 114 under the loop rule, the rest after an exit or under a data guard. Only 87 are operands the goldens do not hold.
- Example: the v4 residual-box comparison (`battery_v52.py:338-340`) is `reach-unknown`, although lines 312-314 say its operands may map to serialized fields.
- This is the reason given for removing an acceptance condition, so it must match the record.

Replacement for lines 116-118:

>   - Its counts: 923 numeric and finiteness rows over the ten fixtures. Of these, 50 are assessable, 87 have an operand the goldens do not record, and 786 are "reach unknown" (the reach rule could not show from source that the predicate runs in that fixture). Per fixture, 2 to 9 rows are assessable (8, 9, 9, 7 and 5 in the verdict fixtures of v1, v2, v2-eb, v3 and v4; 2, 3, 3, 2 and 2 in their `chain` fixtures). The 874 declared limits are the limit on internal selections, those 786 rows and those 87 rows. Most numeric predicates of versions 1 to 4 could not be assessed; for most of them the recorded cause is reach, not an operand missing from the goldens.

Replacement for lines 233-235:

> - **The reason.** Most numeric predicates of the decision layer of versions 1 to 4 cannot be assessed from the existing goldens. The manifest frozen under revision 6 (section 1) found 2 to 9 assessable rows per fixture (50 of 923 numeric and finiteness rows) and 874 declared limits: 786 rows whose reach it could not establish from source, 87 rows with an operand the goldens do not record, and the limit on internal selections. Codex's round found that manifest incomplete.

## 3. Non-blocking items

1. **Lines 24-29.** "What it amends" names the charter and amendment 1 only. Amendment 4 names "amendment 2, revision 6" by hash (`amendment-4.md`, lines 9-10); amendment 3 says "the adopted revision of amendment 2". Add a sentence that amendments 3 and 4 are unchanged and that amendment 4's reference is read as the adopted revision.
2. **Lines 424-425 and 46.** "Decision P2" is not among the marks and is not described in §1. The text does not say what was corrected in the comparator, why, whether the comparator was in `ba94f3a…`, or whether Codex's round covered it. State this, and that the comparator read no golden before or after the correction.
3. **Lines 124-126.** "N3" and "the maintainer's interpretation N1(c)" are not defined. Say in one clause what N1(c) was and that it is moot under P1.
4. **Lines 127-128 and 371-372.** With the margin check gone, criterion (b) rests on records where D1a already shows no non-numeric difference and a maximum of 2.12e-9 against `1e-6`. Its outcome is foreseeable. NR-A2 is the only condition whose outcome is unknown. The label covers this ("post hoc, on exposed records"), but §1 could say it plainly for the maintainer's approval.
5. **Lines 356-358 (P1(d)).** "Records" does not say where: suggest "serializes in its outputs". It binds v0.5.14 only once that charter adopts it. Its relation to decision H2(f) (line 348-350) could be stated: the requirement is the default, H2(f) the fallback.
6. **§3.1 (lines 170-185).** The comparator's record is not required to report coverage: files compared, numeric tokens compared and differing, maximum relative difference, per setting. The inventory check makes zero coverage impossible, but "evidence for every PASS" is clearer with the counts in the record.
7. **`records/numerical-environment.md`, last line.** The sidecar says the criterion elsewhere is "decision identity (amendment 2, sections 3 and 4)". Under revision 7, section 4 no longer applies to versions 1 to 4. The sidecar is a hashed record, so this needs a dated correction file, not an edit (Process diet 2, item 5).
8. **Lines 422-423 and 410.** "The two bullets above" are four. Line 410 still says "They stay valid under revision 5". Line 418 says the list of absent operands "exists only once the margin manifest is built", yet a manifest with 87 absent rows exists as a record.
9. **Lines 119-120.** The reach rule was changed after a run showed zero coverage in every `chain` fixture. This is disclosed and moot for versions 1 to 4. If the method is reused from version 5, the rule should be fixed before the manifest is built.
10. **Line 12-13.** "Each hunk of the committed diff is tied to P1" cannot be checked here; that README is not in the dossier.

## 4. What I checked and did not check

Checked:
- Byte count and SHA-256 of all 42 manifest rows.
- The hashes revision 7 quotes for revision 6, the charter, amendment 1, `step0-golden-before.json`, `step0-claim-hashes-before.json` and the margin manifest.
- That applying `diff-revision-6-to-7.patch` to revision 6 gives revision 7 exactly (same SHA-256). A fresh `diff -u` differs from the patch only in how it aligns the title and the blank line 2.
- The manifest counts, recounted from its rows: assessable 8, 9, 9, 7, 5 and 2, 3, 3, 2, 2; 874 declared limits; the classes and reasons behind them.
- §1's NR-A1 and D1a statements against `step1-comparison-nr-a1.json` and `step1-diag-golden-diff.json`.
- Line 18 of the claim-hash record; charter lines 539-540 and 563; the sidecar against the records it cites.
- Every source citation against the excerpts.
- Consistency with the charter (§2, §3 steps 0, 1 and 5, exit criteria, §8, §9 stops, §12), amendments 1, 3 and 4, revision 6, both earlier blind reviews, and the six `CLAUDE.md` excerpts.

Not checked (not in the dossier, or forbidden):
- The raw goldens, the comparator, its schema and span mapping.
- `l4/README.md` and Codex's answer on the manifest (only its quoted SHA-256 and summary are here).
- The maintainer's decisions in #218 (E1, H2, J1, K2, L1, N1, P1, P2), so whether the text renders them faithfully and whether revision 6 was adopted.
- Whether any cited commit exists, including `ba94f3a…` and `c6236e9…`.
- Source beyond the excerpted lines.

I ran no git, no network and no project code, and created or modified no file. Nothing in this report comes from memory or from outside the dossier folder.
