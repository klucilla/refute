# Proposal: two lanes, engineering and confirmatory

**Status: a proposal, not adopted.** Written on 2026-11-26 by the maintainer's decision (#218,
comment 7203695669, item A5a). It would change rules of `CLAUDE.md` and `ROADMAP.md`, so it
needs a **fresh blind review before it could hold** (Process diet 2, item 6: "Rule changes
receive a fresh blind review before adoption"). That review is not requested or run here. Until
the maintainer adopts a reviewed text, every rule stays as written.

## 1. The problem

Every change goes through the same machinery today:

- the phases;
- the charters (Process diet 2, item 1);
- the stops;
- the gates;
- direct commits to `main` (Working mode (v0.3), item 1).

Most of that machinery protects the **claims**: locks, hidden data, verdicts and acceptances. A
clearer CLI message, a plot, a loader for a new file format or a documentation fix carries none
of those risks, but it waits for the same machinery. The machinery was built for the claims, and
the time goes mostly to everything else.

## 2. The two lanes

| | Engineering lane | Confirmatory lane |
|---|---|---|
| **What** | CLI, plots, documentation, data loaders, tests, refactors with identical outputs, experimental features | calibration, battery promotion (a version frozen for confirmatory use), locks, pre-registrations, acceptances, verdicts, infeasibility records |
| **How** | a branch and a normal pull request; CI; one review (Codex); merge after review | everything that exists today: phase, charter, pre-registration, lock, stops, gate |
| **Charter, lock, blind review** | none | as today |
| **Outputs** | software; any number it prints on real data is `exploratory`, `method_status: not_validated` | verdicts, under the existing vocabulary |

### 2.1 Which lane a change belongs to

A deterministic rule decides it, in the style of `scripts/ci_plan.py`. It never relies on an
agent's judgement. **In doubt, the confirmatory lane.**

A change is **confirmatory** if it:

1. touches any **guarded path**:
   - `src/refute/core/verdict.py`, the lock and code-hash modules (`lock*`, `canonical*`,
     `codehash*`, `lock_compat*`), and `src/refute/selection/`;
   - every module that defines a battery version (1 to 5) or its parameters;
   - `calibration/**`, `docs/validation/**` and `.cache/frozen/**`;
   - the claim specs and the published dossiers;
   - `pyproject.toml` and `uv.lock`, the files of the gate protocol, and `CLAUDE.md` and
     `ROADMAP.md` themselves;
2. changes the output value of any recorded case: a golden test, a claim payload, a lock tag
   (`scripts/verify_locked_tags.py`) or the lock compatibility snapshot;
3. reads data that a lock, a holdout or a hidden window protects, or any target still
   unexposed;
4. or produces a number that a public text would cite as a result.

Everything else is **engineering**. The guarded-path list itself is a rule: changing it is a rule
change, with a blind review.

### 2.2 What the engineering lane must show before a merge

- **CI:** `scripts/ci_evidence.py <sha> --level full` on the pull request's head.
- **Records unchanged:** the golden tests, `verify_locked_tags.py` (10 of 10) and the lock
  compatibility check are unchanged and pass.
- **Review:** one Codex review of the diff, with its findings answered.
- **Experimental features:** labelled `experimental` in `--help` and in every output they write,
  with `method_status: not_validated` and the limits label of the battery they use.

## 3. The rules that would change (exactly)

Quoted from `CLAUDE.md` and `ROADMAP.md` as of `03247c8`. Each would get one sentence that
excludes the engineering lane, and nothing else in it would change.

| # | Where | Today's text (excerpt) | The change |
|---|---|---|---|
| 1 | `CLAUDE.md`, "Phases (read first)", item 2 | "Plan and build ONLY the current phase. Never pull in work from future phases." | Engineering-lane work is not phase work. It may run while no phase is open or beside the open phase, but it never builds the scope of a future phase's confirmatory work. |
| 2 | `ROADMAP.md`, "How phases work", first bullet | "One phase at a time. ... Never plan or build work from a future phase." | The same exception as row 1. |
| 3 | `CLAUDE.md`, "Working mode (v0.3)", item 1 | "direct commits to main ..., with no pull request and no wait for CI" | The engineering lane uses a pull request and requires the evidence of section 2.2. The confirmatory lane keeps item 1 as it is. |
| 4 | `CLAUDE.md`, Process diet 2, item 1 | "Before work starts, one charter file is committed ..." | It applies to phases, so to the confirmatory lane; engineering-lane work has no charter. |
| 5 | `CLAUDE.md`, Process diet 2, item 2 | "Where the charter calls for it, stop before the first commit in `src/` ..." | Unchanged for the confirmatory lane. An engineering-lane pull request that touches `src/` outside the guarded paths needs no stop; its review is section 2.2. |
| 6 | `CLAUDE.md`, "Working mode (v0.3)", item 2 | "At the end of each round, **one** Codex review of all the round's commits" | For the engineering lane, the review is per pull request. |
| 7 | `CLAUDE.md`, Process diet 2, item 4 (caps) | "exploration stays within 5 CPU-h and 20 GB of downloads per phase" | Engineering-lane runs on real data count toward a separate, smaller standing cap (proposed: 2 CPU-h and 5 GB a week), logged in the same way, and they expose the targets they read (row 9). |
| 8 | `ROADMAP.md`, the closed-phases table | — | The engineering lane gets a changelog, with no phase rows. |
| 9 | `CLAUDE.md`, Process diet 2, item 4 (exposure) | "A public target not yet exposed may be looked at only inside a pool the charter names" | An engineering-lane run may read only synthetic data, or targets already exposed. It never reads a new real target. |

## 4. What never changes

None of these may be relaxed by the engineering lane, by this proposal or by its review. These
are the safeguards of Process diet 2, item 7, with the rules it names:

- the pre-registration order; locks; hidden data; rerun approval;
- deterministic verdicts and their vocabulary;
- evidence for every PASS, and zero coverage as `INCONCLUSIVE`;
- "results are never tuned to pass a gate", and "no earlier verdict changes";
- the advance rule with its 2026-11-21 amendment;
- the non-negotiable rules of `CLAUDE.md`. Among them:
  - no invented scientific facts;
  - no automatic submission;
  - never "confirmed discovery";
  - verdicts about claims, never about authors, with a right of reply;
  - the scope exclusions;
  - tests without network;
- all the safety, privacy, machine, deletion and dependency rules. Among them:
  - the forbidden deletion roots;
  - processes ended only by their PID;
  - Python only from `.venv`;
  - the 7-day dependency cooldown;
  - dependency changes planned before a lock.
- the ask-first list of "Working mode (v0.3)", item 3. The engineering lane may never:
  - run third-party code for the first time;
  - publish or change public text (README, site, release);
  - delete anything outside `.cache/`;
  - force-push.

  Each of these stays an individual approval.

Also unchanged: the engineering lane never merges a change of its own lane rule, and never
changes a dependency. A dependency change stays a confirmatory-lane step, planned before a lock.

## 5. Risks, and what the rule does about them

- **Disguised changes.** A confirmatory change could be split into "engineering" pull requests.
  Guarded paths and recorded outputs are checked by code, never by the label of the pull
  request (section 2.1, items 1 and 2).
- **Code hash drift.** Merged engineering-lane changes enter the next lock's code hash. That is
  correct: a lock hashes what runs. Old locks are verified at their tags, so engineering-lane
  changes do not touch them; `verify_locked_tags.py` in section 2.2 shows it.
- **Exposure by convenience.** Engineering-lane runs on real targets would expose them. Hence row
  9: synthetic data, or targets already exposed, and nothing new.
- **Experimental numbers quoted as results.** Every output of an experimental feature carries the
  labels, and a public text may not cite one as a result (section 2.1, item 4).

## 6. Adoption steps (none taken)

1. The maintainer decides whether to send this text to a fresh blind review.
2. The blind review returns its findings. The text is revised, or dropped.
3. The maintainer adopts a final text in #218, citing its commit SHA. The rows of section 3 are
   then applied to `CLAUDE.md` and `ROADMAP.md` in one commit.
4. The guarded-path classifier and its tests are written in the engineering lane, so the
   confirmatory lane is never needed to build the lane rule. Its path list (section 2.1) is
   part of the adopted text.
