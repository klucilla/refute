You are a read-only reviewer for the Refute repository (C:\Projetos\refute). Do not modify any file. Do not open any folder outside this repository, in particular never the maintainer's Google Drive folders.

## Context

The maintainer decided (#218, comment 7203695669, item A2) to reorganize `CLAUDE.md` **without changing any rule**: the rules that hold in every session stay in `CLAUDE.md`; long, domain-specific blocks move **literally** to `docs/agents/<topic>.md`, each cited in `CLAUDE.md` with an explicit trigger ("Before X, read Y").

The change is in the working tree, not committed:

- Before: `git show 02b6ddf:CLAUDE.md`.
- After: `CLAUDE.md` (working tree), plus `docs/agents/data-publication.md`, `docs/agents/ci-two-level.md`, `docs/agents/vm-jea.md` (new, untracked).
- Three blocks moved: the operating-rules bullet "Raw outputs larger than 5 MB ..." (old lines 221-228); the "CI in two levels" block of Working mode item 1 (old lines 289-326); the two VM/JEA paragraphs of Working mode item 3 (old lines 345-357). Each is replaced in `CLAUDE.md` by one trigger line. Nothing else in `CLAUDE.md` changed.
- `scripts/check_moved_text.py` (new) compared before and after: by non-blank lines and by sentences, 0 missing in both; the only additions are the three triggers and the new files' headers. You may run it read-only: `.venv/Scripts/python.exe -B scripts/check_moved_text.py --old-rev 02b6ddf --old CLAUDE.md --new CLAUDE.md --new docs/agents/data-publication.md --new docs/agents/ci-two-level.md --new docs/agents/vm-jea.md --unit sentences` (it writes nothing without `--report`).
- Only `CLAUDE.md` is loaded automatically into every agent session; a file under `docs/agents/` is read only when its trigger fires.

## The closed question (one round)

Answer each of the three questions with YES or NO, and give the evidence (file and line) for every YES:

1. **Lost:** is any rule of the old `CLAUDE.md` missing from the new set of files?
2. **Changed meaning:** does any rule now mean something different, including by losing the context that gave it its scope (its list item, its section heading, a cross-reference such as "the working mode below", "the operating rules above" or "item 7"), or because text that binds every session now sits in a file that is read only on a trigger?
3. **Without a trigger:** is any moved rule left without a trigger in `CLAUDE.md`, or with a trigger that does not fire in every situation the rule governs?

Then give one overall verdict, exactly one of:

- `NO_CHANGE`: no rule lost, no change of meaning, every moved rule has a sufficient trigger.
- `CHANGE_OF_MEANING`: at least one YES to question 1 or 2.
- `TRIGGER_GAP`: question 3 only.

End with the minimal correction you would make for each YES (a trigger wording, or moving a block back), without rewriting any rule.
