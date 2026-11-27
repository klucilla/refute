# Codex review, one round: a proposed rule for release archives and papers in a reply period (#207; block W, item W1(e))

You are a read-only reviewer. You must not edit any file and must not run anything that writes. Do
not open `K:\Meu Drive\Pessoal\Segurança`.

## Context

The maintainer asked for a rule diff in `docs/data-publication.md` that answers issue #207. It is
proposed, not applied: the maintainer approves it before anything is adopted. This is a rule
change, so later rounds may follow in this conversation (up to three in all).

## Files

- **The issue:** `C:\Projetos\refute\.cache\v0513\runs\gh4__c7fa82bd41b7\stdout.txt` (GitHub's
  JSON for #207).
- **The patch:** `C:\Projetos\refute\.cache\v0513\w\207-rule.patch`. It applies to
  `C:\Projetos\refute\docs\data-publication.md`; the proposed full file is
  `C:\Projetos\refute\.cache\v0513\w\data-publication.proposed.md`.
- **The related rules:**
  - `C:\Projetos\refute\docs\right-of-reply.md` (the seal, the annexes, the embargo, the waiting
    period, and the order of notification, gate and publication);
  - `C:\Projetos\refute\CLAUDE.md` (sections "Non-negotiable rules", "Operating rules" and
    "GitHub operations");
  - the release workflow `C:\Projetos\refute\.github\workflows\release.yml`, if present.

## Questions

1. **The gap:** does the patch close #207's gap? That is, does rule 3's restriction reach the
   automatic release archive, with a check before each release, its record, and a decision path?
2. **Consistency:**
   - Is it consistent with `right-of-reply.md`: the embargo item 3, the waiting period items 6 and
     7 with extensions, and the order "notification, gate, publication"?
   - Is it consistent with CLAUDE.md: a human always publishes; the maintainer approves public
     text and releases; deletion and history rewrites need approval?
   - Does any sentence contradict an existing rule, or change the sense of one?
3. **Precision:**
   - Is "open on the planned release date" decidable from the `reply/` annexes?
   - Does a paper whose notice was never sent, or that has no `reply/` annex yet, escape the list?
   - Does the rule cover a release made from a tag later than the list?
   - Should the list be computed again at the release commit?
4. **Scope:**
   - Should the PyPI package and the GitHub release's own source archives be inside the rule,
     instead of in an open question?
   - Is the v0.4.0 question stated correctly against #207?
5. **Wording:** anything ambiguous, or stated as fact without a source.

## Answer format

- One verdict: `SURVIVED`, `WEAKENED` or `REFUTED`.
- Then the findings, numbered, each with the patch's line, the evidence, and the exact replacement
  text.
- Short; no preamble.
