# The advance rule after the pause: options for the maintainer

**The decision asked.** The maintainer's decision of 2026-11-16 (#217), item 2: "escreva
docs/plans/advance-rule-options.md, só com opções, sem recomendação e sem mudar nada."

**What this page is.** Options only.
- It recommends nothing and changes nothing: the ROADMAP and the advance rule are as they were.
- Any change to the rule is the maintainer's decision, and a non-delegated stop.
- The options are an agent's proposal of wording and consequences. They decide nothing.

## The rule as it stands

`ROADMAP.md`, "How phases work" (the maintainer's decision of 2026-11-05, taken on the day v0.5
closed as `WEAKENED`):

> **Advance rule (the maintainer's decision of 2026-11-05).** A new capability phase starts only
> after the current line of work succeeds: every declared target either PASSes or is shown to be
> infeasible with the available data (one infeasibility record per such target, with evidence,
> reviewed by Codex and by an independent review, approved by the maintainer). Until then, the
> next phase is a correction phase on the same line (v0.5.1, v0.5.2, ...). [...] After three
> correction rounds without success, the maintainer decides between a change of approach, an
> infeasibility record, or a pause.

## Where the line stands (from the records)

- **v0.5** closed as `WEAKENED`. Its failed targets are D1 (EB1 and EB2), D2, D4 and T2a
  ([closing record](../../calibration/v0.5/results/closing-record.md)).
- **The three correction rounds** closed as not approved
  ([v0.5.1](../validation/v0.5.1/closing-record.md),
  [v0.5.2](../validation/v0.5.2/closing-record.md),
  [v0.5.3](../validation/v0.5.3/closing-record.md)).
- **The change of approach** (v0.5.4 Information checks) closed without passing or failing a
  target.
- **The pause.** On 2026-11-13 the maintainer chose it. It is one of the rule's own three exits.
- **No infeasibility record exists**, and the records say no target has a basis for one now
  ([pause record](../validation/v0.5.4/pause-record.md)).
- **The pause record** gives, per target, the evidence that would warrant reconsidering it. It
  states that those items authorize nothing.

**What the rule conditions, and what it does not:**
- It conditions the **advance** to a new capability phase: every target passing, or an
  infeasibility record per target.
- It does not condition the **end of the pause**. Resuming work on the targets is the
  maintainer's decision (`ROADMAP.md`, "Current phase": resuming "is the maintainer's decision
  only, after the publication of 2026-11-19").
- It does not say what work is allowed during a pause. It speaks of "a new capability phase".
  Maintenance, publication and the open items of #59 are not capability phases.

## A fact that bears on every amendment

The rule was fixed on 2026-11-05, before the correction rounds ran. Options B and C change it
after three rounds failed and the results are known.

Two kinds of rule are involved, and the records treat them differently:
- **The scientific rules** (targets, thresholds, tests, data) are protected by the roadmap:
  "Results are never tuned to pass a gate. If a pre-registered claim fails, the failure is
  reported and analyzed, never hidden by changing thresholds, targets or data." The rule itself
  adds: "a round's targets are never relaxed after its results." No option here touches these.
- **The advance rule** is a rule of governance: it says when the next phase may start. The
  records do not forbid the maintainer from amending it. An amendment made with the results known
  can only be prospective, would be disclosed as such, and could not relabel anything that already
  happened.

How a reader weighs a governance rule amended after it bound is a credibility question for B and
C. Option A does not raise it.

## Option A: keep the rule

**What changes.** Nothing. No new capability phase starts until every failed target passes or
has an approved infeasibility record. Whether and when work on the targets resumes stays the
maintainer's decision.

**What it says publicly.** What the drafts of the release of 2026-11-19 say, as the decision of
2026-11-16 requires: v0.5 closed as `WEAKENED`; three correction rounds not approved; the line
paused; no target relaxed and none declared infeasible; no new capability phase until the rule is
met.

**Credibility.**
- *For:* the rule decided before the results stands unchanged, so the question of a rule amended
  after it bound does not arise.
- *Against:* the pause has no end date. If no reconsideration evidence appears and no work
  resumes, the project shows no new capability for an open-ended time. An open-ended pause may be
  read as an abandoned project, whatever the records say.

**The outstanding targets.** They stay as they are. D1, D2, D4 and T2a failed in v0.5. T3b passed
in v0.5; what is outstanding for it is the new confirmation sample a further round would need,
which is short by 9 eligible stars.

**The pause record's items.** They stay what they are: evidence that would motivate
reconsidering a target, authorizing nothing by themselves. They are not the only way to resume;
the maintainer may resume work for other reasons. Examples of the items:
- D1: a new test with its planet side, or information beyond the star's density;
- T2a: a new noise model, a new forecast, or new data for its hosts;
- T3b: 11 new domain-eligible stars available to the frame, with new TOIs. Today 2 are available
  beyond the 11 that v0.5 used.

**Open under A:**
- whether the pause has a review date;
- who checks the pause record's items, and when (for example, T3b's count against a later TOI
  table).

## Option B: a prospective amendment; v0.6 may start with v0.5's targets as public limitations

**What changes.** The rule gains a third way for a line to stop blocking the next capability
phase: the maintainer declares the failed targets **public limitations**. v0.6 may then start.
v0.5 stays `WEAKENED`. No target is relaxed, none is declared passed or infeasible, and
`method_status` stays `not_validated`.

**What it says publicly.**
- The rule was amended on a stated date, with v0.5's results and the three failed rounds known.
- A limitations statement, in the README and the release notes, lists each failed target with its
  numbers.
- Every later output of a phase that uses the TESS battery carries those limitations.

**Credibility.**
- *For:* new capability phases can start, and each failed target is stated as a limitation in
  the texts that readers see first.
- *Against:*
  - It is a governance rule amended after it bound, with the results known (the section above).
  - A reader may take it as the advance rule giving way the first time it bound.
  - The limitations are not side issues for the next phase. v0.6 is the variable stars pack
    (eclipsing binaries and pulsating stars) on the same TESS data, and D1 is about synthetic
    eclipsing binaries that survive the battery.

**The outstanding targets.** D1, D2, D4 and T2a stay failed and visible, as limitations. T3b
stays as it is: passed in v0.5, with its further confirmation sample short by 9 stars. Nothing
obliges further work on them, unless the amendment says so.

**The pause record's items.** They stay evidence for reconsidering a target. B replaces the
rule's requirement (a PASS or an infeasibility record per target) with the declaration, so the
advance does not depend on that evidence. Whether the items stay as standing
obligations, to be re-checked for example at each later gate, is a choice inside the amendment.

**Open under B:**
- the exact text of a limitations statement, and who reviews it;
- whether later phases may reuse the v0.5 battery at all, or only with a label;
- whether the amendment applies only to this line, or to every future line.

## Option C: a middle path; advance only on an independently reviewed limitations record

**What changes.** As in B, a line may stop blocking without every target passing. C adds three
conditions to B:
1. **A limitations record per failed target,** on the model of the infeasibility record. It has
   the evidence, what was not shown, and the reconsideration items. It is reviewed by Codex and
   by an independent review, and approved by the maintainer. The pause record is a first draft of
   its content, not that record.
2. **A dependency clause for the next phase.** Its plan states, before any code, which of its
   claims rest on a capability that a failed target measures. Those claims are either left out or
   labelled in every output.
3. **A standing check.** At each later gate, the reconsideration items are re-read against the
   new evidence, and the result is recorded.

**What it says publicly.**
- The rule was amended prospectively, with the results known.
- Advancing required a reviewed record per target, and the reviews are published as they came
  out.
- v0.5 stays `WEAKENED`.
- The limitations follow every dependent output.

**Credibility.**
- *For:* the advance needs a record per target that two reviews have read, besides the
  maintainer's decision. The next phase has to state its dependencies on the failed targets
  before any code.
- *Against:*
  - It is still a governance rule amended after it bound, with the results known.
  - Reviews and labels correct nothing. They do not fix D1, and they do not show that a later
    use of the battery is scientifically adequate. The concern about v0.6 under B holds under C
    too.
  - Its records have the same form as the infeasibility record (a record per target, two reviews,
    the maintainer's approval) but ask for less: not that a target cannot be met, only what is
    known and not shown. A "limitations record" may then work in practice as a softer
    infeasibility record. The line between "not shown feasible" and "infeasible" is held only by
    the wording and the reviewers.
  - It adds cost: an independent review per target, and a check at every later gate. The
    reviews may also return objections that block it.

**The outstanding targets.** D1, D2, D4 and T2a each get a reviewed record, and their state
stays failed, never passed or infeasible. T3b stays as it is (passed in v0.5; its further
confirmation sample short by 9 stars), with a record of that.

**The pause record's items.** They become the standing check's content.

**Open under C:**
- who the independent reviewer is, and under what cap;
- what happens if a review does not accept a record;
- whether the dependency clause can be checked mechanically, or only by review.

## Variants seen while writing (not developed)

- **A with a dated review.** The rule stays; the pause gets a date on which the maintainer
  re-reads the reconsideration items.
- **A scope-limited advance.** Only a phase with no dependency on the TESS battery may start (in
  the current roadmap, v0.7 Mathematics), out of the roadmap's order. It changes the rule and
  the roadmap's order, so it carries the costs of B.
- **A single case outside the phases.** For example, a prospective prediction for one target.
  That is not an option of this page. Any exception to the phase rule would be a question for
  the maintainer and a non-delegated stop; the one exception on record was specific to the
  passage from v0.2.1 to v0.3.

## Side by side

| | A: keep the rule | B: public limitations | C: reviewed limitations record |
|---|---|---|---|
| The rule's text | unchanged | amended, prospective | amended, prospective, with conditions |
| A rule changed after results | no | yes | yes |
| v0.5's verdict | `WEAKENED` | `WEAKENED` | `WEAKENED` |
| Failed targets (D1, D2, D4, T2a) | failed; block the next capability phase | failed; public limitations | failed; each with a reviewed record |
| T3b | passed in v0.5; a further sample short by 9 | the same | the same, with a record |
| What unblocks v0.6 | every target passing or an infeasibility record | the maintainer's declaration | reviewed records, the dependency clause, the standing check |
| The pause record's items | evidence for reconsidering; they authorize nothing | still evidence for reconsidering; the advance does not depend on it | the standing check |
| Review the option adds | none added (advancing still needs what the rule asks: a PASS or a reviewed infeasibility record) | the limitations statement's review, if any | an independent review per target, and a check per gate |
| Main risks | an open-ended pause | the rule giving way when it first bound; v0.6 leans on D1's limitation | the same two as B; a softer infeasibility in practice; cost |

## What no option does

- **Targets.** None is relaxed. No failed target becomes a PASS, and none is declared infeasible
  without the record the rule already asks for.
- **Method status.** No method becomes validated: `method_status: not_validated` stays in every
  output.
- **Locks and records.** No lock, verdict or published record of an earlier phase changes.
- **Authority.** Nothing happens without the maintainer's decision, recorded before any action.
