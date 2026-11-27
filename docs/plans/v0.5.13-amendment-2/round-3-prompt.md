Round 3 of 3, the last, same conversation. You remain a read-only reviewer: modify no file, run no network command, open no folder outside C:\Projetos\refute (never the maintainer's Google Drive folders, and never K:\Meu Drive\Pessoal\Segurança).

**The maintainer decided the direction after round 2** (#218, comment 7216128796, item E1). These decisions are not reopened; check only their implementation.
- No synthetic v5 verification in Step 1, and no thread pin. The object of reproducibility is the decision, not the last digits.
- Amendment 2 is rewritten as a simplified revision 3, in a new file:
  - (a) versions 1 to 4: no change; byte identity in ID-BEFORE's recorded numerical environment;
  - (b) other thread settings: decision identity by your round-1 typed comparator (every non-numeric byte equal, claim hashes equal, 10 tags PASS, each numeric field within the 1e-6 engineering budget declared post hoc, with the text you accepted);
  - (c) the margin check uses only operands present in the existing goldens; an absent operand is a DECLARED LIMIT of #226, listed one by one, with no supplemental execution;
  - (d) v5 onward: the same decision identity is the reproducibility criterion; byte equality only in the same numerical environment, recorded in each execution's provenance; what exists and what is missing becomes a Part B item, with no src/ change now;
  - (e) a read-only survey of where `refute verify` and `check-dossier` compare bytes of numeric outputs, in an exploratory issue, with no fix proposed;
  - (f) Part A's exit criterion 1 and Step 1 become (a) to (c); the historical CI mechanism stays a declared limit of F-1.
- Removed from the amendment: the pinned worker, the src/ patches, the blas-pin extra and the §12 exception request. The maintainer denied that exception (E2).

**Please review** `docs/plans/v0.5.13-charter-amendment-2-rev3.md` (uncommitted). Revisions 1 and 2, `docs/plans/v0.5.13-charter-amendment-2.md`, stay as the record. The survey's text is `.cache/v0513/issue-e1e.md`, opened as #231.

Check in particular:
1. Does revision 3 implement (a) to (f) faithfully, without relaxing anything the direction does not relax and without adding back what it removed?
2. Is the round-1 text quoted as written in sections 3.1 and 3.2? Is the adaptation of your round-1 item 3 in section 4 a correct and conservative implementation of (c)? Covered: operands only from the existing goldens, absent operands as listed declared limits never a pass, no supplemental execution.
3. Section 3.1 says the per-setting evidence of the ten locked-claim checks is a verification run under that setting's thread variables (verification, not a rerun, under Process diet 2 item 4). Is that consistent with (b) and with the charter's stops?
4. Section 5's inventory of what the dossier provenance records now (`src/refute/core/environment.py`, `numeric_runtime` and `snapshot`) and what is missing: is it accurate?
5. Section 6's replacement of exit criterion 1 and the Step 1 clause of stop 2: is it consistent with the approved charter (`docs/plans/v0.5.13-charter.md` at `04402e7a`) and amendment 1, and does it keep ID-AFTER and criteria 2 to 6?
6. Are the source line references in section 4's examples and in the survey correct?

Answer in English:
1. **Verdict:** `APPROVABLE` or `NOT_APPROVABLE`. This is for submission to the blind review, which the maintainer's adviser proposes; adoption is the maintainer's.
2. **Blocking items,** numbered, each with file and line, the problem, and the **exact replacement wording**.
3. **Non-blocking items.**
