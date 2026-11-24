**Amendment of 2026-11-23: process diet 2 (the maintainer's decision, #218).** It applies to phases
opened from its adoption on; earlier phases, records, locks and verdicts are unchanged. It adds to
the process diet of 2026-11-21 and to "Working mode (v0.3)"; where they differ, this text applies.

1. **One charter per phase.** A phase opens with one maintainer decision, recorded on its issue
   before any work, that fixes: the question; the target sets; the caps (CPU-h, downloads, disk,
   calendar); every rerun the phase may make, each with its reason and exact procedure (this
   satisfies the rule that every rerun is approved in an issue before it runs); the Codex rounds;
   and the stops. Inside the charter, the session proceeds without further approval.
2. **Four stops per phase.** Besides the opening (the charter), the session stops only before:
   (a) the first commit of a change in `src/`, with the change reviewed; (b) a lock or a drand
   round; (c) public text (site, root README, release, the approval of a report, a Zenodo record);
   (d) anything outside the charter or its caps. The list "Ask the maintainer only before" of
   "Working mode (v0.3)" still applies in full (third-party code run for the first time,
   dependencies, deletions outside `.cache/`, force push, history rewrite, branch deletion,
   Administrator or Hyper-V steps).
3. **A time box.** A phase has 7 calendar days from its opening. At the limit it closes with
   declared limits (case (c) of the advance rule), unless the maintainer extends it once, by a
   recorded decision with a new date. No extra correction round is opened to rescue a phase.
4. **Exploration without stops.** Exploratory work on synthetic data or on targets already
   exposed in earlier phases needs no stop, up to 5 CPU-h and 20 GB of downloads per phase, when:
   its outputs are labelled exploratory and are never verdicts; it changes no committed record,
   lock or verdict; and its choice, reason, inputs and outputs are logged in the repository.
   Such a run is exploration, not a rerun of a recorded result. Anything that bears on a claim,
   a lock or a verdict stays under the confirmatory rules.
5. **Less paperwork.** One plan and one report per phase. An error found in an exploratory
   report of a phase goes into one dated errata file of that phase (a new file, never an edit);
   a separate dated correction is kept for locks, verdicts and published records (site, Zenodo,
   releases).
6. **Reviews in proportion.** The gate review of a phase with no lock and no verdict is one
   Codex round. An independent Claude session reviews a gate only when the phase has a lock or a
   verdict, with the maintainer's approval (purpose, number and cost). A rule change still has
   its blind review.
7. **Unchanged.** Pre-registration, locks, hidden data, the verdict vocabulary, "no PASS without
   evidence" and zero coverage as INCONCLUSIVE; the rules on safety, privacy, the machine,
   deletion and dependencies; and every earlier verdict, target and record.
