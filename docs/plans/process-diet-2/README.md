# Record: the amendment "Process diet 2"

**Adopted** by the maintainer's decision of 2026-11-24 (#218, comment 7122240195), as the final
text of the blind review below ("Texto final que eu adotaria"), with the maintainer's two choices:
- **N1:** the 5 CPU-h cap is a default that a charter may raise, with the caps ledger above 5
  CPU-h;
- **N2:** a public target not yet exposed only inside a pool the charter names, with an exposure
  record.

Both are already in the final text. It applies to phases opened **after** this adoption; v0.5.9
keeps the rules it was opened with.

**Where the text is:** items 1, 2, 4, 5 and 7 in [CLAUDE.md](../../../CLAUDE.md), "Exploratory and
confirmatory work"; items 3 and 6 in [ROADMAP.md](../../../ROADMAP.md), "How phases work"; a
cross-reference in CLAUDE.md's "Phases". The numbers 1 to 7 are the same in both files.

## The origin

1. **The draft:** written by the maintainer's adviser ([amendment-draft.md](amendment-draft.md)).
2. **One Codex round** on the draft. It returned **WEAKENED**, with the text rewritten
   ([codex-answer.md](codex-answer.md); its final text, as a separate file:
   [codex-final-text.md](codex-final-text.md)).
   - Codex CLI 0.167.0-alpha.3.2, model gpt-6.2-sol, effort high.
   - Its tokens, the real sum of its events: 204,458 input (163,456 cached) and 5,021 output, so
     **46,023** review tokens.
3. **A blind review** by a new, read-only Claude Fable 5.2 session, which saw only the text and
   the rules ([blind-review.md](blind-review.md), in Portuguese, stored as it is).
   - It returned **WEAKENED**; its 7 blocking items are integrated in its final text, the text
     adopted.
   - It used 176,953 tokens.

## The files, stored unchanged

Each file was copied from `.cache/v059/diet2/` and its SHA-256 checked against the original before
the commit. Git stores them byte for byte (`.gitattributes`, `-text`).

| File | SHA-256 |
|---|---|
| [amendment-draft.md](amendment-draft.md) | `ac967d9fad00ea164664e2da7aebfb4e6647d98d60f9ba046acb287091f8b6ae` |
| [codex-prompt.md](codex-prompt.md) | `bf0de6c7821d6802861018f0a2f66f5fbdd5c8b8cbb45ed6bc82ecd980926196` |
| [codex-answer.md](codex-answer.md) | `63d3273417706ec117370e89e79d1a908c03faf45f4597931d2044f8843219ee` |
| [codex-final-text.md](codex-final-text.md) | `81c10591f9d906c21e611532ee7c12d34319d543c578494df5ab4ed49966d734` |
| [blind-review.md](blind-review.md) | `3922ffd684a24c3af3f90111b0ceb5f6a2157d543f27907fd3d2773ba12f0b88` |
