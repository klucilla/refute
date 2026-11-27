# Codex review, one round: the ideas backlog against its source issues (block W, item W2.4)

You are a read-only reviewer. You must not edit any file and must not run anything that writes. Do
not open `K:\Meu Drive\Pessoal\Segurança`.

## Context

The maintainer decided (decision W2, recorded on #218, comment 7229841832) to move 17 GitHub
issues labelled "future-phase" into one file, `docs/backlog/ideas.md`, and then close them. Each
section must hold the number, the title, the essential text of the body and the comments (a
faithful summary that invents nothing), the external references with their URLs, and the link to
the issue.

The agent kept one of the 17, #30, out of the file and open. It holds that #30 describes a known
defect of the engine, so it is an unresolved finding and not an idea: the lock's hash changes when
the claim schema gains an optional field, and `refute verify` then reports TAMPERED.

## Files

- **The file to check:** `C:\Projetos\refute\docs\backlog\ideas.md`.
- **The issues, exactly as GitHub returned them** (`gh issue view --json number,title,body,comments,state,labels`), one JSON per file:
  - #9 `C:\Projetos\refute\.cache\v0513\runs\gh4__dfb5f6452198\stdout.txt`
  - #10 `C:\Projetos\refute\.cache\v0513\runs\gh4__f75475952f5b\stdout.txt`
  - #11 `C:\Projetos\refute\.cache\v0513\runs\gh4__21b7e5666790\stdout.txt`
  - #12 `C:\Projetos\refute\.cache\v0513\runs\gh4__53a1a4907d4d\stdout.txt`
  - #13 `C:\Projetos\refute\.cache\v0513\runs\gh4__4007b5c8c580\stdout.txt`
  - #16 `C:\Projetos\refute\.cache\v0513\runs\gh4__676fb01508ae\stdout.txt`
  - #17 `C:\Projetos\refute\.cache\v0513\runs\gh4__205501a32088\stdout.txt`
  - #18 `C:\Projetos\refute\.cache\v0513\runs\gh4__f9875a1abc2e\stdout.txt`
  - #21 `C:\Projetos\refute\.cache\v0513\runs\gh4__1b1079c245a4\stdout.txt`
  - #24 `C:\Projetos\refute\.cache\v0513\runs\gh4__7edc6cb578a7\stdout.txt`
  - #25 `C:\Projetos\refute\.cache\v0513\runs\gh4__78332af6271f\stdout.txt`
  - #26 `C:\Projetos\refute\.cache\v0513\runs\gh4__0c1a926e08ae\stdout.txt`
  - #27 `C:\Projetos\refute\.cache\v0513\runs\gh4__bdcbdc1291ef\stdout.txt`
  - #28 `C:\Projetos\refute\.cache\v0513\runs\gh4__77a05f1ab726\stdout.txt`
  - #29 `C:\Projetos\refute\.cache\v0513\runs\gh4__6c8535640939\stdout.txt`
  - #30 `C:\Projetos\refute\.cache\v0513\runs\gh4__93a1f1905880\stdout.txt`
  - #167 `C:\Projetos\refute\.cache\v0513\runs\gh4__f620a55c5934\stdout.txt`

## Questions

1. **Nothing lost.** For each of the 16 issues in the file: does its section keep every essential
   point of the body and of every comment, and every external reference (URL, arXiv identifier,
   DOI or paper) with its read date where the issue gives one? List each omission by issue and
   point.
2. **Nothing invented.** Does any sentence of the file state something its issue does not say, or
   say it more strongly or differently (a number, a date, a name, a status, a decision)? List each
   one, with the file's line and the issue's text.
3. **The links and titles:** does each section give the right number, title and link?
4. **Scope:**
   - Is any of the 16 in fact an unresolved finding, a gate item, or about a paper in its authors'
     reply period, so that it should stay open (W2.3)?
   - Is the agent's reading of #30 right?

## Answer format

- One verdict for the file: `SURVIVED`, `WEAKENED` or `REFUTED`.
- Then the findings, numbered, each with its issue, the file's line, the evidence, and the exact
  correction.
- Keep it short; no preamble.
