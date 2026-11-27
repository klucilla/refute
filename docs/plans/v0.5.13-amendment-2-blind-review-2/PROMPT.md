# Review prompt: v0.5.13 charter, amendment 2, revision 5

You are an independent reviewer. Use only the files in this folder; `MANIFEST.md` lists each one
with its source and SHA-256. Work read-only. Do not open the raw golden outputs; none is in this
folder.

## What to review

`amendment-2-revision-5.md` is a proposed revision of an amendment to the approved phase charter
`charter.md`, which was already amended by `amendment-1.md`.
- Its previous revision, `amendment-2-revision-4.md`, was adopted.
- `diff-revision-4-to-5.patch` shows every change between the two.
- `blind-review-1-answer.md` is the blind review of an earlier revision.

Review revision 5 against:
- the charter, amendment 1 and revision 4;
- the project's rules in `excerpts/CLAUDE.md-*`;
- the records in `records/`;
- the source excerpts in `excerpts/`.

Assess whether revision 5 is fit to be adopted as written:
- whether its rules are complete, unambiguous and checkable by deterministic code;
- whether it is consistent with the charter, amendment 1 and the project's rules;
- whether its statements about the records and the source are accurate;
- whether anything in it, or in what changed from revision 4, weakens a safeguard of those rules.

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
