# WP1: section 10 checklist for what PR #60 delivered

Prepared by the agent on 2026-10-16 for issue #44. **This is not the maintainer's
review.** Section 10 of [wp1-acceptance.md](wp1-acceptance.md) requires that "the
maintainer has reviewed each criterion against the document"; this checklist only lays
out, criterion by criterion, where each one is met in the documents and what evidence
exists, so that review can be done against it. Nothing here accepts WP1.

## Scope and method

- **What #60 delivered:** merge commit `2b9c637` (head `0ad337b`, base `020f15d`),
  merged on 2026-10-15. The head and the merge have the same tree (`691f445`), so the
  checks recorded on the head apply to what was merged. Files: `docs/verdicts.md`, `docs/claim-spec.md`,
  `docs/sandbox.md` (new), `docs/right-of-reply.md` (new), `docs/reviewer-protocol.md`,
  `CLAUDE.md`, `docs/validation/v0.3/checks/check_wp1.py` (new). Sections 2 to 7 of
  the acceptance document.
- **Not in #60:** section 8 (the AI use statement in `README.md`, #14 part 1) was
  delivered by #61; it is outside this checklist.
- **Line numbers** below refer to the files at `2b9c637`. Plan lines refer to
  `docs/plans/v0.3-plan.md` at `8456780`, as the acceptance document says; the plan is
  identical at `2b9c637` (`git diff 8456780 2b9c637 -- docs/plans/v0.3-plan.md` is
  empty).
- **How each criterion was checked:** each document was read against the plan section
  it cites. #60 only added lines: `git diff --numstat 020f15d 2b9c637` gives 0 deleted
  lines in each of the 7 files, so no line that existed before #60 was changed.
- **No script was run for this checklist.** The results of the section 9 checks are
  the ones recorded in the description of #60 (run on `0ad337b`); they were not run
  again here. Later changes to these documents on main (after #60) are not covered.

## Section 10 conditions

| Condition | Status for #60 | Evidence |
|---|---|---|
| Every document of sections 2 to 8 exists on main and meets its criteria | Sections 2 to 7: **met, with the observations below**. Section 8: not in #60 (#61). The condition for the whole of WP1 also needs section 8, which this checklist does not cover | The criteria table below |
| The checks of section 9 were run and their results are recorded in the PRs | **Met for sections 2 to 7, as recorded.** Scripts: `links`, `plan-lines`, `plan-sections`, `verdicts-discovery`, `claim-spec-tess`, `reviewer-v02`, `sandbox-status`, `claude-rule`, all `PASS` on `0ad337b`, with negative probes. Independent review: one read-only Codex conversation covering V, C, S and R (section 9 asks for V, C, S, R and A; A belongs to #61), 3 rounds, ending in agreement after two corrections of `check_wp1.py`. These are historical results of the session that wrote #60: Codex could not run the script then (an `encodings` import error) and reviewed by inspection and in-memory probes; nothing was run again for this checklist | Description of #60, sections "Checks (section 9)" and "Independent review" |
| The maintainer has reviewed each criterion against the document | **Not shown.** #60 records no review or comment; this shows that no review is recorded in the PR, not that none happened elsewhere. This checklist is not that review | #60 on GitHub: 0 comments, 0 reviews |
| CI is green on every WP1 PR that runs CI | **Met for #60.** #60 ran CI (it changes a `.py` file, which is not in `paths-ignore`): 4 of 4 jobs passed | Run 38656692295: `ubuntu-24.04` and `windows-2025`, Python 3.12 and 3.13 |

## Criteria of sections 1 to 7

| Criterion | Status | Evidence (file:lines at `2b9c637`) |
|---|---|---|
| **G1** no rule added, changed or missing | Met, with observations O1 to O9 | Each document read against its plan section (rows below): this textual comparison is the evidence. `plan-lines` and `plan-sections` PASS only show that the cited line ranges and sections exist (`check_wp1.py:123-151`), not that the rules are equivalent |
| **G2** terms keep the plan's meaning | Met | Verdict names, check names, `comparison_mode` values, "base reproduction", "experimental core", "annex" used as in the plan; no term found with another meaning |
| **G3** relative links resolve | Met (recorded) | `links` PASS on `0ad337b` (checked in the commit's tree) |
| **G4** external facts sourced | Met | No new external fact. RFC 1918 and the IANA registry (`sandbox.md:28-30`) come from plan 355-357, whose sources section gives the retrieval date (plan 960, "Retrieved on 2026-10-14 unless stated otherwise") and the IANA registry URL (plan 988-989) |
| **G5** English only | Met | All 7 files |
| **G6** nothing unimplemented described as done | Met | Status notes: `verdicts.md:25-27`, `claim-spec.md:160-163`, `sandbox.md:6-9`, `right-of-reply.md:7-9`, `reviewer-protocol.md:104-105` |
| **V1** paper verdicts with `INCONCLUSIVE` | Met | `verdicts.md:15-31`; plan 643-647 |
| **V2** gates separate from attack prerequisites | Met | `verdicts.md:33-41`; plan 616-621 |
| **V3** order 0 to 6, deliberately different from discovery | Met | `verdicts.md:43-63`; plan 623-641 |
| **V4** attribution rule | Met | `verdicts.md:65-80`; plan 653-664 (same text) |
| **V5** partial results | Met | `verdicts.md:82-95`; plan 668-679 |
| **V6** paper result is the claim profile | Met | `verdicts.md:97-113`; plan 681-692 |
| **V7** coverage units and minimums | Met, observation O7 | `verdicts.md:115-135`; plan 694-716 |
| **V8** discovery section unchanged | Met | 0 deleted lines in `verdicts.md`; `verdicts-discovery` PASS (bytes) |
| **C1** fields of an ML claim; schema fixed in WP3 | Met | `claim-spec.md:160-189`; plan 247-267 |
| **C2** inventory and draw | Met | `claim-spec.md:191-233`; plan 271-314 |
| **C3** conditional comparison (D-6) | Met | `claim-spec.md:218-224`; plan 299-305 |
| **C4** definitions before the lock; approvals | Met | `claim-spec.md:238-255`; plan 321-341 |
| **C5** tolerance, modes, orientation of `d`, `tol_d`, equality at the limit | Met, observation O3 | `claim-spec.md:257-302`; plan 410-458 |
| **C6** outside tolerance | Met | `claim-spec.md:304-306`; plan 460-462 |
| **C7** TESS sections unchanged | Met | 0 deleted lines in `claim-spec.md`; `claim-spec-tess` PASS (bytes) |
| **S1** every isolation requirement of plan 6.1 | Met, observation O5 | `sandbox.md:11-91` and `128-131`; plan 351-408 |
| **S2** "requirements, not yet validated" | Met | `sandbox.md:6-9`; `sandbox-status` PASS |
| **S3** machine and budget, budget rules by reference | Met, observations O4, O8, O9 | The VM: `sandbox.md:16-23`; CPU, budget, guards, capacity control and the memory check: `sandbox.md:93-126`; budget rules point to plan 7.3 and 7.4 (`sandbox.md:97-100`) |
| **S4** no host, address, credential or path beyond the plan | Met | `sandbox.md` names only what plan 7.1 states (VM shape, 24 of 32 threads); no address, credential or path |
| **R1** seal, annexes, embargo | Met | `right-of-reply.md:15-26`; plan 722-731 |
| **R2** draft, send, `reply/`, 30 + 14 days, replies | Met | `right-of-reply.md:28-54`; plan 732-749 |
| **R3** three recorded states | Met | `right-of-reply.md:56-57`; plan 751-752 |
| **R4** papers with no negative claim | Met, observation O1 | `right-of-reply.md:59-70`; plan 756-763 |
| **R5** notification, gate, publication | Met | `right-of-reply.md:72-88`; plan 767-781 |
| **R6** no agent email; nothing submitted | Met | `right-of-reply.md:11-13`; plan 740 and line 82 |
| **P1** paper section added; v0.2 procedure unchanged | Met | `reviewer-protocol.md:100-105`; 0 deleted lines; `reviewer-v02` PASS (bytes) |
| **P2** inventory, transcription, triage rejections | Met | `reviewer-protocol.md:114-121` and prompt items 2-3 (`145-148`); plan 833-835 |
| **P3** objections only; report is an annex | Met | `reviewer-protocol.md:123-125`; plan 835-836 |
| **P4** second reviewer from another family | Met, observation O6 | `reviewer-protocol.md:107-112`; plan 838-840 |
| **P5** claim-level wording, never the authors | Met | `reviewer-protocol.md:154-155` and `163-164`; plan line 83 |
| **L1** rule in the operating rules | Met | `CLAUDE.md:139-144`, inside "Operating rules for agents working in this repo" (`CLAUDE.md:106`); `claude-rule` PASS |
| **L2** where the excerpts are stored | Met | `CLAUDE.md:141-142`: "in a `sources/` record next to the statement" |
| **L3** new statements from adoption | Met | `CLAUDE.md:143-144` |
| **L4** release checklist part tracked in #53 | Met | A comment on #53 of 2026-10-14T23:28:13Z, before the merge of #60: "Also tracked here: the release-checklist part of #34 (the sourcing rule for legal and license statements), prepared with the next release." |
| **L5** refers to #34 without closing it | Met | #60 description: "Refs #34"; #34 is open |

## Observations for the maintainer

None of these changes a rule as far as this reading shows, and the plan stays
referenced in each document; each is a place where a document is not a literal copy of
the plan, listed so the maintainer can decide whether it matters (G1: "a difference found later is corrected in the document or
brought to the maintainer as a plan change").

- **O1.** `right-of-reply.md:70` states "Negative claim verdicts are `FRAGILE`,
  `NOT_REPRODUCED` and `NOT_REPRODUCIBLE`." Plan section 9 does not state this list
  literally. The same list appears in `reviewer-protocol.md:110-111`. To confirm that
  it is the plan's meaning of "negative claim verdict".
- **O2.** `claim-spec.md:235-236` keeps plan 5.3 (D-7) except its last clause, "never a
  judgment on the paper's quality" (plan 318-319).
- **O3.** `claim-spec.md:288` leaves out the parenthesis of plan 442 ("the tolerance
  never admits a tie or an inversion"). The rule itself is kept (`d_rep > 0` in the
  row, and `claim-spec.md:301-302`). It also leaves out the sentence of plan 446-447
  ("Each mode keeps the meaning of the original statement; it is chosen before the
  lock"); `claim-spec.md:270-271` says the mode is written before the lock.
- **O4.** `sandbox.md:101-103` keeps the guards of plan 559-565 except three sentences:
  "Active time and wall-clock time are recorded and are never the budget limit" (plan
  559-560); "User-requested pauses are excluded from the guard clock"; and "An
  interruption by a guard is `INCONCLUSIVE` with an operational reason; it does not, by
  itself, show a defect in the authors' code" (the attribution part is in
  `verdicts.md:76-78`). The reference to plan 7.3 stays (`sandbox.md:97-100`).
- **O5.** `sandbox.md:15` writes "Third-party code never runs on any other server of
  the maintainer" for plan 353, "Never the maintainer's existing VPS". The wording
  differs and names no server (S4); the rule itself does not widen, since plan 351-353
  already allows only the dedicated VM.
- **O6.** `reviewer-protocol.md:109` says "The protocol of the v0.3 claim fixes the list
  before the lock"; plan 10.3 does not say when the list is fixed. Plan 833 says the v0.2
  protocol "is adapted to papers", and the v0.2 text fixes the list before the lock
  (`reviewer-protocol.md:10-12`), so this reads as that adaptation rather than a new
  rule.
- **O7.** The coverage table of `verdicts.md` leaves out plan 715-716, "Every row gets a
  synthetic case that must not pass and one that must": a testing requirement, which
  belongs to the acceptance documents of the code (WP2, WP4) rather than to the
  verdict rules.
- **O8.** `sandbox.md` does not repeat plan 516-518: no paid fallback (the financial
  budget of v0.3 is zero), and if the VM cannot be built or hardened the phase pauses
  for a decision of the maintainer. The plan is referenced (`sandbox.md:3-4`).
- **O9.** `sandbox.md:97-100` does not repeat how CPU-hours are measured (from the
  cgroup of each container, `cpu.stat` `usage_usec`) nor that the CPU model is recorded
  with every run (plan 537-540); it points to plan 7.3 for the budget rules.

O8 and O9 were found by the Codex review of this checklist, which also corrected a first
version of it: that version said #53 held no item for the release-checklist part of #34,
having read only the body of #53, not the comment that records it (L4 above).
