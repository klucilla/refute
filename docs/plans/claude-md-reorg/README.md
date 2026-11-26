# CLAUDE.md reorganization (item A2): stopped on Codex's verdict

The maintainer's decision of 2026-11-26, item A2 (#218, comment 7203695669): reorganize
`CLAUDE.md` without changing any rule, moving long domain sections literally to
`docs/agents/<topic>.md` with a trigger each; one Codex round with a closed question; "if there
is a change of meaning: stop".

**Result: stopped. Nothing was applied: `CLAUDE.md` is unchanged (423 lines, the same bytes as
`02b6ddf`), and no `docs/agents/` file was committed.** The decision is the maintainer's.

## What was tried (in the working tree only)

- `make_claude.py` (this folder) moved three blocks literally to three files under `docs/agents/`:
  - the operating-rules bullet on raw outputs above 5 MB and Zenodo;
  - the "CI in two levels" block of Working mode item 1;
  - the two VM and JEA paragraphs of Working mode item 3.

  It put one trigger in `CLAUDE.md` in place of each block.
- `CLAUDE.md` would have gone from 423 to 367 lines.
- **Kept in `CLAUDE.md` on purpose:**
  - the Process diet texts: its items 1, 2, 4, 5 and 7 bind every session, and `ROADMAP.md` says
    they are in `CLAUDE.md`;
  - "the site": `CLAUDE.md` has no section on it, only its mention in the ask-first list.
- `scripts/check_moved_text.py` compared before and after:
  - by non-blank lines: 372 before, 0 missing ([check-lines.json](check-lines.json));
  - by sentences: 339 before, 0 missing ([check-sentences.json](check-sentences.json)).

  The only additions were the triggers and the new files' headers.

## Codex's round (one round, a fresh conversation)

- **Model and thread:** Codex CLI 0.167.0-alpha.3.2 (the model of its local configuration), read
  only, sandbox read-only, threads 8 to 31, thread `01a219c2-91c7-7e53-8ea6-90d532aa52d4`.
- **Tokens:** 203,156 input (169,600 cached) and 3,651 output.
- **The prompt and the answer, unchanged:**
  - the prompt: [codex-round-1-prompt.md](codex-round-1-prompt.md);
  - the answer: [codex-round-1-answer.pt.md](codex-round-1-answer.pt.md). Codex answered in
    Portuguese, and the file is stored as it came (SHA-256 `44031688…bc99cd`).

**The verdict was `CHANGE_OF_MEANING`.** Codex's three answers:

1. **Lost:** NO.
2. **Changed meaning:** YES.
   - The data-publication trigger fires at a commit, so an output above 5 MB could be staged
     before it fires.
   - Publishing a prepared Zenodo record would not fire it.
   - The moved relative links render under `docs/agents/`, where they point to the wrong place.
3. **Without a trigger:** YES.
   - The CI trigger does not cover reading a finished run as test evidence, or a manual CI
     dispatch.
   - The VM trigger does not cover the network checks on the maintainer's machine.

Its minimal corrections:

- put the data-publication block and the CI block back in `CLAUDE.md`;
- widen the VM trigger.

They were not applied: the decision allowed one round, and a change of meaning is a stop.

## Records here

| File | What it is |
|---|---|
| `make_claude.py` | the generator that was run in the working tree |
| `check-lines.json`, `check-sentences.json` | the two checks of the tried split |
| `codex-round-1-prompt.md` | Codex's prompt, unchanged |
| `codex-round-1-answer.pt.md` | Codex's answer, unchanged |
