You are a read-only reviewer for the Refute repository (C:\Projetos\refute). Do not modify any file, run no network command, and open no folder outside this repository (never the maintainer's Google Drive folders). This is a new conversation, for this charter only.

## Context

Read `CLAUDE.md` (rules), `ROADMAP.md` ("How phases work", Process diet 2 items 3 and 6) and the maintainer's decision recorded in #218, comment 7203695669, item B1 (its text is reproduced in the requirements below). No phase is open.

The draft to review is `docs/plans/v0.5.13-charter.md` at commit `65e83be` (HEAD). Its preparation records are in `docs/plans/v0.5.13-charter-prep/` (exposure_check.py and its JSON, power.py and its JSON/MD, log.jsonl). Background: `docs/plans/v0.5.13-proposal.md`, `docs/plans/v0.5.12-charter.md`, issues #224, #226, #227, #228 as summarized in the proposal and in `docs/gates/v0.5.12-review.md`.

The maintainer's requirements for this charter (item B1), in brief:
- a) Preconditions, in this order, before any calibration: #226 (BLAS: decide on pinning threads without changing any byte of versions 1 to 4; if any byte changes: stop); #227 (assertions against the generating model on the #223 cases, before calibrating U1); #224 (inject synthetic transits, equal and different depths, into REAL TESS light curves of quiet and active stars, only from already-exposed or development targets, plus synthetic correlated-noise families, B6 included, and the control rule with the red depth; if the estimator must change, a dated specification correction with a blind review).
- b) New targets fixed before data: "not assessed" reasons from the CODE in two buckets (unassessed_data, unassessed_power); three axes with the AND rule (safety: Wilson upper bound of surviving FPs; sensitivity: Wilson lower bound of retained planets among assessed; coverage: minimum assessed without falling into unassessed_power); floors per stratum (2 or 3 SNR or depth bands); a symmetry lock between abstention on planets and on FPs. X, Y, Z sized by the v0.6 sample (KELT-FP: 171 planets and 307 FPs), with the power calculation in the charter.
- c) Data: only already-exposed sets; check and record whether any KELT-FP target or any target of the "Kepler stars in TESS" set of Dallas et al. 2026 (arXiv:2610.32949) was already examined with tests.
- d) Product: a frozen candidate battery and proposed v0.6 targets, exploratory, never a verdict; an annex proposing (for v0.6 only) the comparison with exoVetter (BSD-3) and LEO-vetter (GPL, comparator only, no code copied) on the same targets, official configurations, risk-versus-coverage curves, the invocation script shown to the authors before publishing.
- e) Lighter process (#228): meter only through the job object, with UV_OFFLINE=1 and --disable-socket, without AppContainer; caps criterion "caps measured and met; every execution outside the meter recorded at once with its estimated cost"; pre-approved repetition classes with checkable conditions (checkers, formatting, infrastructure failures that give no case a new value), never for scientific measurements; order proof by push (CI: order-proof) before each probe; decisions in #218 cite the pasted block with no declared hour; Codex's final review in a NEW conversation; the gate with Fable (only the protocol and the phase name) and Codex as second opinion.
- f) Caps (CPU-h, downloads, disk peak), the 7-day deadline and the stops; if it does not fit in 7 days, split into two phases and say where.

## Your task (round 1 of at most 3)

Review the draft for approval-readiness. Answer, in English, with these sections:

1. **Verdict:** `APPROVABLE` or `NOT_APPROVABLE`.
2. **Blocking items:** numbered; for each, the defect (file and line), why it blocks (which rule of CLAUDE.md / ROADMAP.md / item B1 it breaks, or which loophole it opens: leakage, post-hoc choice, rerun, exposure, degeneracy, relaxed target), and the **exact replacement wording** to put in the charter.
3. **Your choices** (give a value or a wording, not only a critique):
   - X, Y, Z, D, the strata floors and the power calculation: are they correctly computed by `power.py` (check the Wilson and Newcombe formulas and the bisection), correctly sized for 171/307, and is the AND/joint-power treatment honest? Give the values you would freeze.
   - The design of the injection into real light curves (step 3 ii): star selection, activity index and its thresholds, injection counts, depth ratio, SNR bands, the rules applied to real curves. Give the design you would freeze.
   - The new caps rule of section 8 ("measured and met; every execution outside the meter recorded at once with its estimated cost") and the pre-approved repetition classes: is each condition checkable from the records? Give the wording you would freeze.
   - The split into Part A (v0.5.13) and Part B (v0.5.14), and Part A's caps (8 CPU-h, 3 GB, 5 GB).
4. **The exposure check:** does `exposure_check.py` answer item c) honestly, and are its limits (the Dallas no-KOI control not determinable; "examined" = v0.5.10's run-record rule) stated correctly?
5. **Non-blocking items:** short list.

Keep to this scope. Do not propose changes to rules outside this charter; if you find one needed, list it as a non-blocking note for the maintainer.
