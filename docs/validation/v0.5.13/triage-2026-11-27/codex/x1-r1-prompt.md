# Codex check, one round: the adopted rule is the reviewed patch plus three changes (block X, item X1)

You are a read-only reviewer. You must not edit any file and must not run anything that writes. Do
not open `K:\Meu Drive\Pessoal\Segurança`.

**The maintainer's decision X1:** the rule proposed for #207 is adopted, with item 2's exception.
The agent applied the reviewed patch
`C:\Projetos\refute\docs\validation\v0.5.13\triage-2026-11-27\proposals\207-rule.patch` to
`C:\Projetos\refute\docs\data-publication.md`. The edit is in the working tree, not committed yet.
It made exactly these three changes:
1. **The heading:** "(PROPOSED, #207; not adopted)" became "(adopted 2026-11-27, #207, the
   maintainer's decision X1)".
2. **The section "Open questions for the maintainer"** was removed.
3. **Item 2 no longer depends on adoption:**
   - "Exception: item 2 below, and only if the maintainer adopts that exception with this rule."
     became "Exception: item 2 below.";
   - in item 2, "If the maintainer adopts the exception, the check also passes when" became "The
     check also passes when".

**Your only task** (the maintainer decided that this round checks only this): compare the working
tree file with the patch, and say whether the applied text equals the patch's added lines with
exactly these three changes and nothing else. Lines 1 to 88 must be unchanged against git `HEAD`.
Do not re-review the rule's substance.

**Answer:** `SURVIVED` if it matches exactly, otherwise `REFUTED`, with each difference (line and
text). Short.
