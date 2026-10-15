# Independent reviewer protocol (v0.2)

**Agents propose. Deterministic tests decide.** An independent reviewer is a fresh,
read-only agent session that receives one dossier and tries to refute it. Its report
is stored in the dossier. A reviewer raises objections; it never sets or changes a
verdict. Verdicts come only from the deterministic tests in `verdict.json`.

## Which dossiers are reviewed

The calibration protocol of each claim fixes, before the lock, which dossiers are
reviewed and how any random choice is made. For the v0.2 calibration the
maintainer decided:

- every known false positive;
- every unexpected verdict: a known planet `REFUTED`, or a known false positive
  `SURVIVED`;
- 3 known planets drawn with a seed of their own, derived from a future drand
  round fixed in the protocol, with the rule written in the protocol.

## Who reviews

- **Primary reviewer**: Claude Opus 5.5, one fresh session per dossier. The session
  has never seen the claim being built or the analysis code being written, and it
  receives nothing but the dossier path and the prompt below.
- **Second reviewer** (unexpected verdicts only): a model from a different family
  (Codex), if its connection works. If it does not, the run log records that the
  second review was left out and why.

## Rules for the reviewer session

- **Read-only.** No file is created, edited, moved or deleted; nothing is committed,
  pushed, downloaded or installed; nothing is posted anywhere.
- **Allowed**: reading and searching the dossier; `uv run --frozen refute
  check-dossier <dossier>`; `uv run --frozen refute verify <claim>` in a checkout of
  the commit named in `REPRODUCE.md`; read-only `git log`/`git show` on that commit.
- **Not given**: the conversation that built the claim, the expected answer, the
  other dossiers' reviews, or the builder's opinion. The reviewer may read the
  public catalogs cited in the dossier, but must say so and cite them.
- Every objection points to evidence: a file and a field or line in the dossier, a
  plot, or a command output.

## Prompt

The session is started with this prompt, with `<dossier>` replaced by the path:

```text
You are an independent reviewer for Refute. Your job is to try to REFUTE the
verdict in one dossier, using only the evidence in it. You did not build it.

Dossier: <dossier>

Rules: read-only. Do not create, edit, move or delete files; do not commit, push,
download, install or post anything. You may read every file in the dossier, run
`uv run --frozen refute check-dossier <dossier>`, and read the code at the commit
named in REPRODUCE.md.

Check, with evidence (file and field, plot, or command output):
1. Integrity: does check-dossier pass? Do the claim, lock and data hashes agree?
2. Data: right target, product, sectors, stellar parameters, neighbors? Anything
   that makes a test meaningless (wrong star, missing sectors, bad aperture)?
3. Each test: is the input sensible, and does the result follow from it? Look for
   a test that passed for the wrong reason or failed for an artifact.
4. Blind holdout: did any hidden-year read fall outside a predicted window? Was
   any round decided with windows wider than the transit?
5. Alternatives the gauntlet does not test that the evidence supports (for example
   a blend closer than one pixel, a stellar companion, a systematic).
6. Text: does the report overstate anything or call this a discovery?

Write your report in Markdown with these sections:
## Summary (two sentences)
## Objections (table: severity critical/important/minor, evidence, why it matters)
## Checks with no objection (with evidence)
## Assessment: one of NO OBJECTION, OBJECTIONS, SERIOUS OBJECTIONS

You do not decide the verdict. Never write that a planet or signal is confirmed.
```

## Storing the report

The maintainer's session saves the reviewer's answer as a Markdown file and
attaches it:

```bash
uv run refute review attach <dossier> <report.md> --reviewer opus-1 --model claude-opus-5-5
```

`refute review attach` refuses a dossier that is not intact, copies the report to
`review/<reviewer>.md`, records its SHA-256 in `review/index.json` with two
fingerprints of the dossier before review (the manifest of every analysis file, and
`verdict.json`), writes `review/index.md` and updates `MANIFEST.sha256`. From then
on `refute check-dossier` fails if the analysis, the verdict or any report changes.
Every dossier's `report.md` links `review/index.md`.

## What happens with objections

Objections never change a verdict. The maintainer reads every report; an important
or critical objection becomes a GitHub issue, and a fix can only be tested by a new,
separately locked claim on new targets.

## Paper dossiers (v0.3)

The procedure above (TESS dossiers, v0.2) is unchanged. For paper dossiers, v0.3
adapts it as follows ([docs/plans/v0.3-plan.md](plans/v0.3-plan.md), section 10.3).
The tooling for paper dossiers is built in the v0.3 work packages; until then this
section is the planned procedure.

### Which dossiers are reviewed

The protocol of the v0.3 claim fixes the list before the lock. A **second reviewer**
from another model family reviews every dossier with a negative claim verdict
(`FRAGILE`, `NOT_REPRODUCED` or `NOT_REPRODUCIBLE`), plus 1 drawn dossier with no
negative claim, if access is available at no additional cost.

### What the reviewer also checks

Besides the checks of the TESS prompt that apply (integrity, data, each check, text),
the reviewer of a paper dossier checks:

- the claim inventory and the transcription of each drawn claim against the paper
  (value, location, metric, split, command, type and comparison reference);
- the triage rejections recorded in the selection log.

A reviewer raises objections and never sets a verdict. The report is an **annex** of
the dossier, with its own manifest citing the hash of the sealed experimental core
([right-of-reply.md](right-of-reply.md)).

### Prompt for paper dossiers

```text
You are an independent reviewer for Refute. Your job is to try to REFUTE the
verdicts in one paper dossier, using only the evidence in it and the paper it
cites. You did not build it.

Dossier: <dossier>

Rules: read-only. Do not create, edit, move or delete files; do not commit, push,
download, install or post anything. You may read every file in the dossier, run
`uv run --frozen refute check-dossier <dossier>`, read the code at the commit named
in REPRODUCE.md, and read the paper at the version named in the claims.

Check, with evidence (file and field, page and table of the paper, or command
output):
1. Integrity: does check-dossier pass? Do the claim, lock, core seal and data
   hashes agree?
2. Inventory and transcription: does each drawn claim match the paper (value,
   location, metric, split, command, type, comparison reference)? Was the inventory
   built by the rules of the protocol?
3. Triage: does each rejection in the selection log follow its stated reason?
4. Each check: is the input sensible, and does the result follow from it? Look for
   a check that passed for the wrong reason or failed because of a limitation of
   Refute rather than of the artifact.
5. Verdict rules: does each claim verdict follow the order and the attribution
   rules of docs/verdicts.md?
6. Text: does the report overstate anything, describe an inconclusive paper as
   positive, or say anything about the authors rather than the claims?

Write your report in Markdown with these sections:
## Summary (two sentences)
## Objections (table: severity critical/important/minor, evidence, why it matters)
## Checks with no objection (with evidence)
## Assessment: one of NO OBJECTION, OBJECTIONS, SERIOUS OBJECTIONS

You do not decide the verdicts. Objections concern the claims and the procedure,
never the authors.
```
