# WP1 acceptance: v0.3 documentation

Line numbers refer to docs/plans/v0.3-plan.md at commit 8456780.

Work package WP1 of [docs/plans/v0.3-plan.md](../../plans/v0.3-plan.md) (section 11,
line 880: "Docs: paper section of `docs/verdicts.md`, ML section of
`docs/claim-spec.md`, `docs/sandbox.md`, `docs/right-of-reply.md`, reviewer prompt for
papers"). Issue #44. Also covers part 1 of #14 (AI use statement in the README) and
the rule of #34 (sourcing of legal and license statements).

This document is committed **before** the documents it accepts (plan lines 871-875).
The plan has not changed between its last commit (`bc288b1`) and `8456780`.

## 1. General criteria (every WP1 document)

- **G1.** Every rule in a WP1 document repeats or points to the plan section it
  comes from. It adds no rule the plan does not contain, and it changes none. A
  difference found later is corrected in the document or brought to the maintainer
  as a plan change; it is never settled silently.
- **G2.** Every term keeps the meaning it has in the plan: verdict names, check names,
  `comparison_mode` values, "base reproduction", "experimental core", "annex",
  "dossier verification", "experimental reproduction", CPU-hours.
- **G3.** Every relative link resolves at the commit of the PR.
- **G4.** Every external fact (a URL, a license, a date) has its source and retrieval
  date (plan line 81, "Never invent facts"). Every legal or license statement also
  follows the rule of section 7 once that rule is adopted.
- **G5.** English only, as for everything written to the repository.
- **G6.** The documents describe what is planned or decided; they do not describe as
  done anything that is not implemented. Behavior that depends on code not yet
  written (WP2 to WP6) is stated as a requirement.

WP1 adds no code, so no synthetic test case applies. Its regression check is the
existing CI suite, which must stay green on any PR of WP1 that runs CI.

## 2. `docs/verdicts.md`: paper section (plan section 8, lines 612-716)

- **V1.** The list of paper verdicts, with `INCONCLUSIVE` and its meaning (lines
  643-647; the list is already present from PR #40).
- **V2.** The gates of the base reproduction, kept separate from the prerequisites of
  each attack (lines 616-621).
- **V3.** The deterministic order for each claim, steps 0 to 6, with the note that it
  differs from the order used for discovery verdicts on purpose (lines 623-641).
- **V4.** The attribution rule: `NOT_REPRODUCIBLE` only for a failure of the
  artifact's own documented procedure, shown by complete attempts; every other cause
  is `INCONCLUSIVE`, at every stage (lines 653-664).
- **V5.** Partial results: a valid negative conclusion is kept when the budget ends;
  the status "Basic reproduction obtained; robustness inconclusive"; partial values
  are information only (lines 666-679).
- **V6.** The paper result is the claim profile: the full profile in the drawn order,
  `INCONCLUSIVE` in the denominators, a headline only when all claims agree, "Mixed
  results: see the claims" otherwise, no single claim defining the paper; a paper
  with no negative claim and some `INCONCLUSIVE` claims is never described as
  positive (lines 681-692).
- **V7.** Coverage units and minimum coverage for every check, for a positive and for
  a negative conclusion; zero or insufficient coverage never yields a pass (lines
  694-716).
- **V8.** The existing discovery section is unchanged.

## 3. `docs/claim-spec.md`: ML section (plan sections 5 and 6.2)

- **C1.** The fields of an ML claim, from the example in lines 247-263: `type`,
  `statement`, `source` (with location and quote), `metric`, `comparison_mode`,
  `scope`, `run` (with deterministic metric extraction), `tolerance`,
  `coverage_minimum`, `attacks`. The exact schema is fixed in WP3; the document says
  so (lines 265-267).
- **C2.** The inventory and the claim draw: granularity, canonical ID, order, approval
  before the draw, publication before the claim round, the draw itself, and the
  rules after the draw (lines 269-314).
- **C3.** The conditional comparison of D-6: required only when the frozen inventory
  has an eligible comparison; otherwise up to 3 value claims, and the dossier states
  that no comparison was evaluated (lines 289-291 and 296-305).
- **C4.** The definitions required before the lock (lines 321-334) and the recording
  of approvals (lines 336-341).
- **C5.** The tolerance formula, its defaults, and the value and comparison modes with
  their predicates, including the orientation of `d`, the operational convention for
  `tol_d`, and equality at the limit (lines 410-462).
- **C6.** Outside tolerance, the dossier records the value, the difference and the
  quantitative reason, and infers neither an error in the paper nor a change of
  configuration (lines 460-462).
- **C7.** The existing TESS sections are unchanged.

## 4. `docs/sandbox.md` (plan sections 6.1 and 7)

- **S1.** Every isolation requirement of section 6.1 (lines 345-408): VM only;
  network blocks enforced outside the guest; build egress only through an allowlist;
  declared inputs fetched by Refute; run phase without network; container limits; no
  mounts or credentials; builder configuration; pinned repository version; datasets
  and weights; the build ladder; allowed patches; who executes; what CI can test.
- **S2.** The document states that these are **requirements, not yet validated**, and
  that only the acceptance tests of WP6 validate them, before any third-party code
  runs (lines 25-27 and 347-349).
- **S3.** The machine and the budget as they apply to the sandbox: the VM, CPU only,
  the CPU-hour accounting over all containers, the operational guards, capacity
  control and the pre-run memory check (lines 496-603). Budget rules point to plan
  section 7.3 instead of copying it.
- **S4.** No host, address, credential or path of the maintainer's machine beyond what
  the plan already states.

## 5. `docs/right-of-reply.md` (plan section 9)

- **R1.** The seal of the experimental core, the annexes with their own manifests, and
  the embargo with only hashes or neutral metadata in public (lines 722-731).
- **R2.** The draft (content, address taken only from the paper, neutral wording), the
  send by the maintainer, the records in `reply/`, the period of 30 days extendable by
  up to 14, and the handling of replies, including the neutral public issue for
  reruns (lines 732-749).
- **R3.** The three recorded states: "notice sent", "period ended", "reply received"
  (lines 751-752).
- **R4.** Papers with no negative claim: the courtesy notice, the optional reply
  period, and the absence of a wait never waiving the gate (lines 754-763).
- **R5.** The order notification → gate → publication, and the conditions for
  publishing a paper with a negative claim (lines 765-781).
- **R6.** An agent never sends email; nothing is submitted to any venue (plan line 82).

## 6. Reviewer prompt for papers (plan section 10.3)

- **P1.** Added to `docs/reviewer-protocol.md` as a paper section. The v0.2 procedure
  for TESS dossiers stays unchanged.
- **P2.** The reviewer also checks the claim inventory and the transcription against
  the paper, and the triage rejections (lines 833-835).
- **P3.** A reviewer raises objections and never sets a verdict; the report is an
  annex of the dossier (lines 835-836).
- **P4.** The second reviewer from another model family: every dossier with a
  negative claim verdict, plus 1 drawn dossier with no negative claim, if access is
  available at no additional cost (lines 838-840).
- **P5.** The prompt asks for the verdict-neutral, claim-level wording of the plan
  (line 83): objections concern the claim and the procedure, never the authors.

## 7. Rule of #34 in `CLAUDE.md`

- **L1.** A rule added to "Operating rules for agents working in this repo": every
  legal or license statement in the repository gives the source URL, the retrieval
  date and a short literal excerpt stored in the repository, so it can be checked
  later. Covered: README, protocols, data-license files, release notes. A statement
  that cannot be sourced is marked as unconfirmed, or is not made.
- **L2.** Where the excerpts are stored: a `sources/` record next to the statement, or
  another location the rule names explicitly.
- **L3.** The rule applies to new statements from its adoption on. Existing
  statements are not rewritten in this package; their review, if wanted, is a
  separate item.
- **L4.** The part of #34 about the release checklist is **not** in WP1. It is
  tracked in #53, where the next release is prepared. WP1 covers only the rule in the
  operating rules of `CLAUDE.md`.
- **L5.** The PR that adds the rule refers to #34 and does not close it before the
  maintainer decides.

## 8. AI use statement in `README.md` (#14, part 1)

- **A1.** The statement describes **what the agents do**, only as far as the
  repository records it: for example writing code and documentation, proposing plans,
  claims and run commands, running analyses in the maintainer's sessions, reviewing
  dossiers as independent reviewers, and reviewing plans as a second agent. Each
  activity named has a source in the repository (`CLAUDE.md`, the plan, the reviewer
  protocol, commit trailers).
- **A2.** The statement describes **what the maintainer decides**: approving every
  pre-registration step, lock, run, commit, push, merge, release, issue change and
  publication; sending every message to authors; building the VM. It names no
  decision that the repository's rules do not reserve to the maintainer.
- **A3.** It keeps "Agents propose. Deterministic tests decide.": no LLM output is a
  verdict (plan line 78).
- **A4.** **No claim the project cannot support.** It does not say or imply:
  - that agents verified results;
  - that verdicts are correct, or that agents are accurate;
  - that a reproduction was repeated (plan lines 69-72);
  - that any capability, model or tool beyond those recorded in the repository was
    used;
  - any quantity (for example a share of code written by agents) unless it is measured
    and sourced.
- **A5.** It names model families or tools only as recorded in the repository (for
  example the co-author trailers of commits, and the second reviewer of the v0.2 gate),
  without versions the repository does not record.
- **A6.** Part 2 of #14 (what the blind holdout proves) is not in this package; it is
  tracked in #23.
- **A7.** `README.md` is not in the CI `paths-ignore` list, so the PR that changes it
  runs CI, which must be green.

## 9. Verification method

How each group of criteria is checked. The scripts named here are declared, not yet
written; each is added, with its own review, in the PR whose documents it checks.

| Group | Script | Maintainer review | Independent review |
|---|---|---|---|
| G (general) | **Link checker:** every relative link of the WP1 documents resolves at the PR commit (G3). **Plan reference checker:** every cited plan line range exists in `docs/plans/v0.3-plan.md` at the stated commit (G1, by reference). | G1, G2, G4, G5, G6: the text against the plan | — |
| V (`docs/verdicts.md`) | Link and plan reference checkers. A fixed-string check that the discovery section is byte-identical to main (V8). | Each criterion against plan section 8 | **Yes:** a read-only second agent compares the paper section with plan 8.1-8.4 and reports any rule added, changed or missing |
| C (`docs/claim-spec.md`) | Link and plan reference checkers. A fixed-string check that the TESS sections are byte-identical to main (C7). | Each criterion against plan sections 5 and 6.2 | **Yes:** the same read-only comparison, for the claim fields, the draw and the comparison predicates |
| S (`docs/sandbox.md`) | Link and plan reference checkers. A fixed-string check that the document states "not yet validated" (S2). | Each requirement against plan 6.1 and 7; S4 (no host, address, credential or path beyond the plan) | **Yes:** the read-only comparison with plan 6.1. The requirements themselves are validated only by the WP6 acceptance tests, not by this check |
| R (`docs/right-of-reply.md`) | Link and plan reference checkers | Each criterion against plan section 9 | **Yes:** the read-only comparison with plan section 9, including the order notification, gate, publication |
| P (reviewer prompt) | Link checker. A fixed-string check that the v0.2 TESS procedure of `docs/reviewer-protocol.md` is byte-identical to main (P1). | Each criterion against plan 10.3 | — |
| L (rule of #34 in `CLAUDE.md`) | A fixed-string check that the rule is in the section "Operating rules for agents working in this repo" (L1) | L1-L5: the wording of the rule | — |
| A (AI use statement) | — | A1-A7: every sentence traced to a source in the repository, listed in the PR | **Yes:** a read-only second agent looks for claims the repository does not support (A4, A5) |

The independent reviews are read-only. Their answers are saved outside the repository
and summarized in the PR, as for the plan of v0.3. They raise objections; the
maintainer decides.

## 10. Acceptance of the package

WP1 is accepted when:
- every document of sections 2 to 8 exists on main and meets its criteria;
- the checks of section 9 were run, and their results are recorded in the PRs;
- the maintainer has reviewed each criterion against the document;
- CI is green on every WP1 PR that runs CI.

The planned order of PRs, each after this document is on main:
- the WP1 documents under `docs/` (`docs/**/*.md` is in the CI `paths-ignore` list, so
  that PR runs no CI);
- the `README.md` and `CLAUDE.md` changes of sections 7 and 8, which run CI because
  of `README.md`.
