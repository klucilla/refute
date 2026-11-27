# Blind review 2: v0.5.13 charter, amendment 2, revision 5

**Manifest check:** all 39 files listed in `MANIFEST.md` match their recorded byte counts and SHA-256. No mismatch, no missing file, no unlisted file. `MANIFEST.md` is not self-listed; its SHA-256 is `3435df693d7427e3532e44b218bb2d6be30a30f8197033df33745e00525cc260`.

Line numbers refer to `amendment-2-revision-5.md` unless another file is named.

## 1. Verdict

`NOT_APPROVABLE`

The narrowing of the margin manifest to a "decision layer" is not what blocks it; it is declared as a limit and no margin result was known. Four points in the text block it: the boundary of the decision layer is not deterministic, the retained examples now contradict the new scope, the new declared limit has no place in the label or the count N, and section 7 misstates two records.

## 2. Blocking items

**1. Line 202 (§4, first paragraph): the boundary of the "decision layer" is not checkable, and its supporting argument is inaccurate.**

Problem:
- **"Directly" is undefined.** `records/j1-decision-count.json` lists the bare atoms `attenuated` and `can_fail` at `battery_v52.py:411`. The comparison that sets `attenuated` (`battery_v52.py:338-340`) is not among J1's 173 rows; it appears only in `records/i2-predicate-inventory.json`. The paragraph does not say whether a comparison one assignment away from the branch is in the decision layer. The retained example at lines 246-252 assumes it is.
- **"Numeric" was dropped.** Revision 4 said "every operative numeric predicate"; revision 5 says "every predicate". By my parse, only about 59 of J1's 173 atoms contain an ordering operator; the rest are identity, string, membership or bare-flag tests (`candidate is None`, `test.name == "odd_even"`, `plan.is_v051`). The rest of §4 defines `x` and `t` only for comparisons, so these rows would be neither assessable nor clearly absent operands. That makes the three counts and N indeterminate.
- **"Operative predicate" and "complete" are orphaned.** The unchanged text still says "An operative predicate … found missing afterwards voids the result" (line 211) and "the manifest is complete" (line 228). Revision 5 no longer defines "operative", so it is unclear whether a missing internal selection voids the result.
- **The argument omits a case.** "A flip that changes neither leaves the goldens unchanged" is false for a flip that changes a serialized number within the 1e-6 budget: the golden changes and §3.1 passes. The argument also covers only flips observed at the compared settings, not clearance from a cutoff, which is the margin check's stated purpose (§3.2, lines 186-187).

Replacement for line 202 (the whole first paragraph of §4, inside the quoted block):

> The margin manifest covers the **decision layer** of each golden fixture. A predicate belongs to the decision layer when its boolean outcome reaches an output that the goldens serialize as a test status, a test class, an eligibility flag, a reason code or the aggregate verdict, and reaches it only through branch tests, assignments, returns, arguments and boolean operators, with no arithmetic and no selection of data in between. This includes the compound predicates, the numeric coverage and count cutoffs, and a comparison that sets a named boolean which a later branch tests (for example `attenuated`, `src/refute/packs/tess/battery_v52.py:338-340`, tested at line 411). Each is traced to its source location. A numeric predicate of the decision layer gets a row under the rules below. A non-numeric predicate of the decision layer (an identity, type, string or membership test, or a bare configuration flag) is listed with its source location and a reason class; it gets no margin row, is not a declared limit and is not counted as assessed. In the rest of this amendment, "predicate", "operative predicate" and "the manifest is complete" refer to the decision layer as defined here.
>
> Internal comparisons whose outcome reaches the goldens only through a number or through a selection of data, cadences, peaks or models are not enumerated. At a compared setting, a flip in one of them that changes a serialized non-numeric byte, or a serialized number beyond the budget of §3.2, already fails §3.1. A flip that changes a serialized number within that budget passes §3.1, as any other difference within the budget does. A flip that changes no serialized byte is not observed. None of this shows that an internal selection is clear of its cutoff. That internal selections were not assessed for margin is a declared limit of #226: the margin record lists it first among the declared limits, N counts it, and the label of section 6 names it.

**2. Lines 230-231 and 241-245 (§4, the examples): the retained examples contradict the new scope.**

Problem: the header says only the first paragraph of §4 changed, but the examples were written for revision 4's scope ("intermediate cutoffs that select the model used by a decision"). The extra-frequency loop cutoff (`peak[1] <= cp.sinusoid_extra_min_snr`, `battery_v51.py:140` and `battery_v52.py:313` in `records/i2-predicate-inventory.json`) selects peaks and the model, so the new paragraph excludes it. Lines 230-231 still say the manifest "lists every one", and lines 241-242 still say "The frozen manifest establishes it per case". A reader cannot tell whether the loop is in the manifest. Its operand `amplitude_snr` is one of the seven fields D1a found to differ, so the reader should be told plainly that it is out of scope.

Replacement for lines 230-231:

> **Examples known from the source when this was written.** They do not replace the manifest. Under revision 5 they show both sides of the scope set by this section's first paragraph: the extra-frequency loops are internal selections, which the manifest does not enumerate, and the v4 residual-box comparison belongs to the decision layer. (Decision H2(e) corrects these against the source, cited by file and line.)

Replacement for lines 241-245 (the last two sub-bullets of "The extra-frequency loops"):

>   - Each loop's cutoff (`src/refute/packs/tess/battery_v51.py:140`; `src/refute/packs/tess/battery_v52.py:313`) selects peaks and the model. Under this section's first paragraph it is an internal selection: the manifest does not enumerate it, whether each saved verdict records three peaks is not established, and it falls under the declared limit stated there. Its operand `amplitude_snr` is one of the fields D1a found to differ.
>   - **The weighted-fit condition-number guard** (`src/refute/packs/tess/battery_v51.py:46-47`: `np.linalg.cond(normal) > 1e12` raises `LinAlgError`, in `_wls`, defined at line 41) is not serialized by the goldens. Where it only stops this loop, it is an internal selection under the same limit.

**3. Line 304 (§6, the label) and line 300 (§6, item c): the new declared limit is not in the label or in N.**

Problem: line 202 says the limit is "carried with its label", but the label is a fixed quoted string, and N comes from the margin record, which lists absent operands only (lines 228 and 300). The new limit is not an absent operand. As written, a later result can cite #226 without it, which weakens "carry applicable limits" (Process diet 2, item 4).

Replacement for the label sentence in line 304 (from "it carries the label" to "with N from the margin record."):

> it carries the label **'#226 met under amendment 2 (decision identity, post hoc, on exposed records); the charter's byte-identity rule was not met at 1 and 4 threads (NR-A1: STOP); N declared limits, the first being that internal selections were not assessed for margin'**, with N from the margin record.

Replacement for the last sentence of line 300:

> Its list of absent operands, together with the limit on internal selections of section 4, is recorded one by one as declared limits of #226 and approved by the maintainer in #218 by the hash of the margin record.

**4. Lines 334-340 (§7): two items listed as "None of these exists yet" exist.**

Problem: `records/i2-README.md` records, under revision 4, part (a) "Done" (commit `a9044264`, 80 raw golden files, each checked against its setting's payload) and part (b) "Done" (the sidecar). The sidecar itself is in this dossier (`records/numerical-environment.md`, dated 2026-11-27). Section 7 is an inaccurate statement about the records, and section 1's "Also known when revision 5 was written" does not mention either product.

Replacement for lines 334-340:

> - Two of the items exist, made under revision 4 (decision I2, `docs/validation/v0.5.13/i2/README.md`). They stay valid under revision 5, which changes neither rule they were made under:
>   - the commit of the raw goldens of section 3.1 (decision H2(b)): 80 files, each checked against the payload recorded for its setting;
>   - the sidecar of section 2 (`docs/validation/v0.5.13/numerical-environment.md`).
> - None of these exists yet:
>   - the comparator of 3.1, with its schema and span mapping;
>   - the margin manifest and check of section 4;
>   - the freeze commit of section 4;
>   - NR-A2 (section 3).

## 3. Non-blocking items

1. **Lines 10-11.** "The committed diff from revision 4 ties each hunk to decision J1": `diff-revision-4-to-5.patch` is a plain diff with no annotation, so this cannot be checked here. The patch is otherwise equal to a fresh `diff -u` of the two files, except that it shows blank line 2 as removed and re-added.
2. **Lines 103-104.** "So it is a floor" is not strict. J1 counts non-numeric atoms, counts each module whole in its first version, and is not attributed to fixtures (`records/j1-README.md`). It undercounts in one direction and overcounts in another. Suggest "not a bound on the number of manifest rows in either direction".
3. **Line 98.** The disclosure names `chain-`, `verdict-` and `error-` goldens; the payload also holds five `plan-` files. Say whether they were opened. `records/i2-README.md` says the earlier view of `verdict-v4.txt` "is to be weighed in the manifest's review"; revision 5 gives no rule for that. Suggest naming it as an input to Codex's completeness review (line 211).
4. **Lines 3-14.** Two "PROPOSED, not approved" banners follow each other, the second belonging to revision 4, which was adopted. Revision 5's own header does not say how it is adopted (after this blind review, by SHA-256).
5. **Lines 262-266 (§5).** Through "the same typed decision-identity and margin rules", the narrowed scope also applies to version 5 onward. The feasibility counts that motivate it cover versions 1 to 4 only. Say whether that is intended.
6. **Line 228.** Whether a predicate with only integer or configuration operands (lines 223-224, margin check "does not apply") counts as "assessed" for the zero-coverage rule is not stated. This was already so in revision 4, but the narrower scope makes such fixtures more likely.
7. **Lines 238-239.** The loop also stops when `peak is None` (excerpt lines 140 and 313); the text names only the SNR cutoff and `LinAlgError`.
8. **Lines 129-130.** "Under any other thread setting" is assessed at 1, 2 and 4 threads only. Line 314 covers it ("Report untested settings as unverified"); unchanged from revision 4.

## 4. What I checked and did not check

Checked:
- SHA-256 and size of all 39 manifest rows; the hashes revision 5 quotes for revision 4, the charter, amendment 1, `step0-golden-before.json` and `step0-claim-hashes-before.json`.
- That revision 5 differs from revision 4 only as the header says (fresh `diff -u` against the patch): title, new header block, the "Also known" block, and the first paragraph of §4.
- §1's new statements against the records: 73 modules; 2,746 sites (2,103 comparisons, 643 calls, recounted from the rows); 0 resolved; J1's 102, 130, 157 and 173 (recounted from the 173 rows); the disclosed view of `verdict-v4.txt`.
- §1's NR-A1 and D1a statements against `step1-comparison-nr-a1.json` and `step1-diag-golden-diff.json`.
- Every source citation against the excerpts: `dossier.py:29`, `environment.py:46-51` and `54-104`, `identity.py:37-55`, `run.py:137` and `365`, `battery_v51.py:41-47` and `134-147`, `battery_v52.py:36-37`, `309-320` and `338-340`, `params.py:370-371`, `pipeline.py:454-457`, `pipeline_v52.py:186`.
- Charter lines 539-540 and 563; line 18 of the claim-hash record; the sidecar against ID-BEFORE's `provenance`.
- Consistency with the charter (§2, §3 steps 0, 1 and 5, exit criteria, §8, stops, §12), amendment 1, blind review 1's six replacement texts, and the six `CLAUDE.md` excerpts.

Not checked (not in the dossier, or forbidden):
- The raw goldens and their schema, so whether `attenuated`, the test classes, flags and reason codes are serialized as revision 5 assumes.
- Source beyond the excerpted lines, including `battery_v52.py:411` itself (seen only as J1 rows).
- The maintainer's decisions in #218 (E1, H2, I1, I2, J1), so whether line 202 is "the maintainer's text" and whether revision 4 was adopted.
- #231, the Codex round records, revisions 1 to 3, and whether any cited commit exists.
- `tools/decision_count.py` and `tools/predicate_inventory.py`; only their outputs were read.

I ran no git, no network and no project code, and created or modified no file. Nothing in this report comes from memory or from outside the dossier folder.
