## OVERALL: WEAKENED

Adopt the revised amendment after one blind review. The draft makes rerun approval too easy to bypass, treats a deadline as authority to advance, and lets a gate lose independence. I reviewed the rules at `4a704f0f`. Local `main` is at `e581d078`, where v0.5.9 is already open and its run still requires recorded approval. The amendment should start with the next phase. [ROADMAP.md, current checkout, lines 49–66](/C:/Projetos/refute/ROADMAP.md:49)

### Blocking items

The numbered provisions below give the exact replacement wording.

- **2. Stops.** “Four stops” reads as an exhaustive list even though individual approvals and pre-registration checkpoints still apply. The new `src/` stop would also add friction to phases where the existing working mode permits direct commits. Keep it where the phase requires it. [CLAUDE.md, lines 194–234](/C:/Projetos/refute/CLAUDE.md:194)
- **3. Deadline.** Seven days can end execution. Case (c) still requires a closure record, listed failures and a limits label carried into downstream results. The no-rescue rule can prevent an automatic extra round while preserving the advance rule’s correction, change-of-approach and pause options. [CLAUDE.md, lines 9–27](/C:/Projetos/refute/CLAUDE.md:9) · [ROADMAP.md, baseline, lines 10–34](/C:/Projetos/refute/ROADMAP.md:10)
- **4. Exploration.** v0.5.8 explicitly calls its changed-seed run exploratory **and** a rerun. Without an operational boundary, someone could vary seeds, thresholds or subsets after a failure, then report the favorable branch. Require approval for repeat evaluations, retain all attempts, and keep data that informed a choice out of its confirmation. [CLAUDE.md, lines 41–48, 119–125](/C:/Projetos/refute/CLAUDE.md:41) · [ROADMAP.md, baseline, lines 15–24, 59–63](/C:/Projetos/refute/ROADMAP.md:15)
- **6. Gate.** A Codex-only gate can preserve the audit trail if Codex is fresh, read-only and uninvolved in the work. The absence of a lock or claim verdict is insufficient on its own. An infeasibility decision, for example, requires both Codex and an independent review. [CLAUDE.md, lines 75–78](/C:/Projetos/refute/CLAUDE.md:75) · [ROADMAP.md, baseline, lines 10–24](/C:/Projetos/refute/ROADMAP.md:10)

### Non-blocking items

- **1 and 7.** An issue-approved charter can authorize exact reruns in advance. Preserve the pre-registration sequence, lock integrity, verdict and coverage rules, and all operational safeguards. [CLAUDE.md, lines 64–88, 102–145, 194–258](/C:/Projetos/refute/CLAUDE.md:102)
- **5.** One errata log is enough for working exploratory reports. Approved and published records need separate dated corrections. Batch approvals in the existing phase issue and reuse the charter as the standing authorization. A second plan, approval ledger or routine gate review would add paperwork. [CLAUDE.md, lines 173–177, 211–222](/C:/Projetos/refute/CLAUDE.md:173) · [ROADMAP.md, baseline, lines 64–69](/C:/Projetos/refute/ROADMAP.md:64)

### Final text to adopt

Put **1, 2, 4, 5 and 7** under **Exploratory and confirmatory work** in `CLAUDE.md`. Put **3 and 6** under **How phases work** in `ROADMAP.md`, with a cross-reference from `CLAUDE.md`’s **Phases** section. Use one fresh, read-only blind review of the proposed text and governing rules, without this verdict or the drafting discussion. [CLAUDE.md, lines 41–55, 75–76](/C:/Projetos/refute/CLAUDE.md:41)

**Process diet 2 (#218).** Applies to phases opened after recorded adoption. Existing phase authorizations and historical records remain in force.

**1. Charter.** Before work starts, the maintainer records one charter in the phase issue. It fixes the question, target and data scope, resource caps, exit criteria, reviews and stops. It may approve named reruns, each with its reason, exact procedure and permitted conditions. Authorized work proceeds within that scope.

**2. Stops.** Keep all mandatory individual approvals, pre-registration checkpoints and phase-specific stops. Stop before a lock or drand checkpoint, public or report approval, publication, a dependency change, or work beyond the charter. Require a reviewed first `src/` commit stop where the phase calls for one. Batch decisions ready at the same time in one issue comment, with explicit approval for each and checkpoint order preserved. Obtain any Claude review authorization with purpose, number and cost.

**3. Time box.** Stop execution seven calendar days after opening unless the maintainer records one extension with a new deadline before expiry. Record completed and unmet criteria. Advance only under case (a), (b) or (c) of the 2026-11-21 rule. For case (c), list failed targets, label the battery and carry that label into every later result using it. Pause if no case applies. Expiry opens no automatic rescue round. Any later correction phase follows the advance rule.

**4. Exploration and reruns.** Within the charter and all applicable stops, explore on synthetic development data or previously examined public data, up to 5 CPU-h and 20 GB of downloads cumulatively per phase, subject to lower charter caps. A rerun includes retrying, reproducing or re-evaluating a recorded run or evaluation on all or part of its original cases, including failed or incomplete cases, even with different code, seeds, thresholds, inputs or entry modes. Obtain issue approval for the exact procedure before execution. Genuinely new diagnostics may reuse exposed data. Log the question and choices before each run, then record provenance, coverage and every outcome, including failures and abandoned attempts. Label outputs `exploratory` and carry applicable limits. Use findings to generate hypotheses. Claims, acceptance and verdicts require locked, pre-registered confirmation on unused targets or data that did not inform the choices, or on prospective data. Keep active holdouts sealed and preserve the original results and stop decisions.

**5. Records.** Use the charter as the plan and keep one phase report. Add dated entries to one versioned, append-only errata log for working exploratory reports. Identify the source version, correction and impact. Use separate dated correction files for approved, published, locked or hashed records and verdict-related corrections. Preserve the originals and track findings that affect a gate.

**6. Gate.** For solely exploratory phases with no lock, scientific verdict, scientific acceptance or separately mandated review, one fresh, read-only Codex session uninvolved in the work may serve as the independent gate. Give it only the dossier. Store its review and track every issue behind a `WEAKENED` gate. Combine it with the final review when independence permits. Retain the required independent reviews for confirmatory work and infeasibility decisions. Rule changes receive a fresh blind review before adoption.

**7. Safeguards.** Preserve pre-registration order, locks, hidden data, rerun approval, deterministic verdicts and their vocabulary, evidence for every PASS, zero coverage as `INCONCLUSIVE`, and all safety, privacy, machine, deletion and dependency rules.

