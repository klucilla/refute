You are Codex, the project's second agent for verdict and validation, in a read-only sandbox. Repository: C:\Projetos\refute at main (411173ba or later; the draft was written at 411173ba). Do not write, edit, commit or contact the network. Never open K:\Meu Drive\Pessoal\Segurança. You may read files and recount committed JSON records with the project's .venv Python in isolated mode, without writing files.

## Task
One review round (design, before the maintainer approves) of a DRAFT charter for the next phase, "v0.5.11 Battery version 5", written by a fresh read-only Claude Fable 5.2 session under Process diet 2 (CLAUDE.md "Exploratory and confirmatory work" items 1-7; ROADMAP.md "How phases work" items 3 and 6):
- C:\Projetos\refute\.cache\v0511\charter-review\charter-draft.md (English; SHA-256 4b6a8f72145735169461434c08827bb4cace6987788d2f08105174f05ff4dfe2)
- C:\Projetos\refute\.cache\v0511\charter-review\charter-cover.md (Portuguese cover with 3 open decisions and the author's disagreements with docs/plans/battery-v5-spec.md)

## Check, with path:line evidence
1. Process diet 2 compliance: charter contents (question, scope, caps, exit criteria, reviews, stops, named reruns), stops kept, time box (it proposes 14 days, an extension), gate (it says an independent Claude review, not Codex, because of a rule change in src/ and acceptance), blind review for the rule change, the rules (a)-(e) carried from v0.5.10 (docs/reports/v0.5.10-report.md section 9; docs/plans/next-phases-2026-11-24.md).
2. Design soundness: two-level output (screen retained/rejected/unassessed; level 2 verdict byte-identical); versions 2-4 unchanged and old locks verifiable by tag (src/refute/core/lock_compat.py, docs/lock-format.md, scripts/verify_locked_tags.py); the centroid guards limited to version 5 (does the draft's claim that putting them in centroid_v5 would change v2-v4 hold?); module naming (_d5).
3. Statistics: completeness Wilson lower >= 0.85 (224/250), effectiveness >= 0.90 (235/250), planet REFUTED guard <= 12/250; the "assessability budget" in stage 0; is the target reachable given part B decidability (24/100) and the definition of unassessed; are values frozen at stage 0 and not tunable later; is the power analysis right (it says power 0.9 needs true rates near 0.92 and 0.96)?
4. The LEO-Vetter false-positive tests reimplemented from papers (Kunimoto et al. 2025 Eqs. 9-13; Thompson et al. 2018 Eqs. A4, A5, A13-A15; Seager and Mallen-Ornelas 2003 Eq. 7) and model-shift uniqueness MS1-MS3: is the plan clean-room (no GPL code copied), deterministic, coverage-declared? Flag any equation or threshold you cannot verify offline.
5. TLS/wotan: the draft recommends a conditional, isolated comparator arm first and a project dependency only later (uv.lock is part of every future lock's code hash). Sound? Check the pins recorded in the repository by v0.5.10 (docs/validation/v0.5.10/engines/) against the draft (the author suspects its PyPI reading was stale).
6. Data and exposure: 72 exposed TOIs, up to 300 exposed hosts, a new named pool DEV-N up to 250 behind a stop; selection rule and seed committed before selection; nothing unexposed or reserved read; the d1 pool untouched (rule (a)).
7. Caps (50 CPU-h, 75 with TLS; 30 GB; 20 GB disk) against measured costs (v0.5.9 about 0.17 CPU-h and 0.25 GB per TOI; v0.5.10 TLS about 250 CPU-s per TOI).
8. Proportion: is the phase too big for one charter? Would a split (spec freeze + synthetic acceptance + src/ change first; calibration and acceptance second) be safer and faster? Recommend.

## Answer (English, concise, at most ~120 lines)
- OVERALL: SURVIVED / WEAKENED / REFUTED for approving this charter as drafted.
- BLOCKING items with the exact replacement wording.
- NON-BLOCKING items.
- The 3 open decisions: your recommendation for each, one line of reason.
- Split or not, with a concrete proposal if split.
