# Review prompt: v0.5.13 charter, amendment 2, revision 7

You are an independent reviewer. Use only the files in this folder; `MANIFEST.md` lists each one
with its source and SHA-256. Work read-only. Do not open the raw golden outputs; none is in this
folder.

## What to review

`amendment-2-revision-7.md` is a proposed revision of an amendment to the approved phase charter
`charter.md`. The charter was already amended by `amendment-1.md`, `amendment-3.md` and
`amendment-4.md`.
- Its previous revision, `amendment-2-revision-6.md`, was adopted.
- `diff-revision-6-to-7.patch` shows every change between the two.
- `blind-review-1-answer.md` and `blind-review-2-answer.md` are the blind reviews of earlier
  revisions.
- `records/margin-226-manifest.json` is the margin manifest that revision 7 cites as a record.

Review revision 7 against:
- the charter, its amendments and revision 6;
- the project's rules in `excerpts/CLAUDE.md-*`;
- the records in `records/`;
- the source excerpts in `excerpts/`.

Assess whether revision 7 is fit to be adopted as written:
- whether its rules are complete, unambiguous and checkable by deterministic code;
- whether it is consistent with the charter, its amendments and the project's rules;
- whether its statements about the records and the source are accurate;
- whether anything in it, or in what changed from revision 6, weakens a safeguard of those rules.

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
