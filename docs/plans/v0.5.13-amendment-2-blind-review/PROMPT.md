# Review prompt: v0.5.13 charter, amendment 2, revision 3

You are an independent reviewer. Use only the files in this folder; `MANIFEST.md` lists each one
with its source and SHA-256. Work read-only.

## What to review

`amendment-2-revision-3.md` is a proposed amendment to the approved phase charter `charter.md`,
which was already amended by `amendment-1.md`. Review the proposed amendment against:
- the charter and amendment 1;
- the project's rules in `excerpts/CLAUDE.md-*`;
- the records in `records/`;
- the source excerpts in `excerpts/src-*`;
- the issue export `issue-231.json`.

Assess whether the amendment is fit to be adopted as written:
- whether its rules are complete, unambiguous and checkable by deterministic code;
- whether it is consistent with the charter, amendment 1 and the project's rules;
- whether its statements about the records and the source are accurate;
- whether anything in it weakens a safeguard of those rules.

## Answer format

Answer in English, in this order.

1. **Verdict:** exactly one of `APPROVABLE` or `NOT_APPROVABLE`.
2. **Blocking items:** numbered. For each item give:
   - its location (file and line);
   - the problem;
   - the **exact replacement text** that would resolve it.

   Write "none" if there are none.
3. **Non-blocking items:** numbered, each with its location.
4. **What you checked and did not check:** one short list.
