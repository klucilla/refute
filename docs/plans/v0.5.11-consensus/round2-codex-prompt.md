Same rules as before: read-only sandbox, repository C:\Projetos\refute, no writing, editing, committing or network. Never open K:\Meu Drive\Pessoal\Segurança. You may recount committed JSON records with the project's .venv Python in isolated mode, without writing files.

## Context
After your REFUTED of the draft, the maintainer chose the split you recommended (decision of 2026-11-24, 19:33 local, #218 comment 7146372481):
- v0.5.11 "Battery version 5: specification and software" (exploratory): step 0, freeze the specification derived from the papers; step 1, synthetic tests written BEFORE the code; step 2, the `src/` change (the maintainer's stop before the first `src/` commit, with your review of the diff). Exit by identity of the old verdict, lock compatibility by tag, full CI, and a gate by an independent Claude review (approved by the maintainer with purpose, number and cost). Time box 7 days. No third-party code, no new dependency, no new target.
- v0.5.12 (a proposal only, nothing opened): calibration with measurement, frozen acceptance targets, sizing, the blind review of the rule change, the lock decision; TLS and wotan as isolated comparators with a benefit bar written first. The (d1) claim waits until after v0.5.12.

The maintainer asked that your blocking items be applied **in the exact wording you proposed**, where they fit v0.5.11: item 1 (whole); item 2 (only the step-0 part: freeze the core, required coverage and eligibility; recount assessability in the records, unknown kept unknown); item 4 (whole); item 5 (process, exposure, reruns; the (d1) exclusion failing closed); item 6 (end-to-end metering, caps as limits). Item 3 (sizing) and the DEV-H/DEV-N pools go to v0.5.12. The v0.5.10 rules (a) to (e) enter as obligations. Caps realistic for this phase (no calibration on TOIs).

## Files (uncommitted, in the working tree)
- docs/plans/v0.5.11-charter.md (SHA-256 9ca4f5048ea9b7f8ed785fc64fe99fa939d5d36c1111c0988a43998544cb5c99)
- docs/plans/v0.5.12-proposal.md (SHA-256 d0612d17792ee6532fa136b7b24d907a126b7cb0b16e71e1aed52b3301b35341)
- the draft and your answer, stored unchanged: docs/plans/v0.5.11-consensus/charter-draft.md, docs/plans/v0.5.11-consensus/codex-answer.md

## Check, with path:line evidence
1. Each of your blocking items 1, 2 (step-0 part), 4, 5, 6: is it applied as you wrote it, where it fits this phase? Are the sentences left out for v0.5.12 the right ones, and is anything that should bind v0.5.11 missing?
2. The split: does v0.5.11 stay inside steps 0 to 2 and the gate, with nothing of calibration, pools, reruns, sizing, acceptance targets A1 to A3, blind review or lock? Are A4 and A5 as software invariants sound for this phase?
3. Process diet 2 contents (question, scope, caps, exit criteria, reviews, stops, time box, gate) and rules (a) to (e) as obligations: complete and checkable?
4. Caps: 10 CPU-h, 5 GB transferred, 10 GB peak disk for this phase. Realistic? Flag if verify_locked_tags.py in each tag's environment or the full local suite could plausibly exceed them.
5. The v0.5.12 proposal: does it carry everything moved out, without committing anything?

## Answer (English, concise, at most ~80 lines)
- OVERALL: SURVIVED / WEAKENED / REFUTED for approving this charter.
- BLOCKING items, each with the exact replacement wording.
- NON-BLOCKING items.
