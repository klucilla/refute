# Closure of the v0.2.1 population study by scope decision (2026-10-14)

On 2026-10-14 the maintainer closed the synthetic population study of v0.2.1
(`../population-study.md`) by a scope decision. The closure does not show that approval was
impossible; it records where the study stopped and what is kept.

## State at closure

- **M0 to M3:** FAILS on the development population, with full integrity. Campaign 1 measured
  the four points in two slots: 52 lots, 208 slot comparisons, all identical, no lock, no
  divergence (`campaigns/dev-campaign-1/README.md`,
  `campaigns/dev-campaign-1/metrics/metrics-dev-campaign-1.md`).
- **Confirmation:** not run; no drand round was declared.
- **M4 and M5:** not implemented, not measured.
- **Proposed corrections:** hypotheses and plans, with blocking points still open: 6 of the 9
  rows of revision 3 (B1, B3, B4, B5, B6, B7; `corrections-plan/README.md`).
- **Calibration population of the corrections plan:** never generated nor analyzed.
- **Closure:** a scope decision, without a demonstration that approval was impossible.

## What does not change

The criteria C1 to C6 and their limits (`../population-study.md`, section 1), the frozen
development manifest (`manifest-dev.json`), `points.json` and the results of M0 to M3 are
unchanged. The v0.2 claim is not affected: it is verified at its locked commit `cc9d104`, the
tag `v0.2.0-calibration-lock`. Nothing was deleted at the closure.

## Records added at the closure

- `campaigns/dev-campaign-1/diagnosis.md`: the diagnosis of M0 and M3.
- `campaigns/dev-campaign-1/holdout-investigation.md`: the holdout failures with the right
  signal.
- `campaigns/dev-campaign-1/c3-inconclusive-investigation.md`: the 57 C3 white INCONCLUSIVE
  planets, version 2, with a dated errata.
- `campaigns/dev-campaign-1/investigations/`: the read-only scripts and the small JSON outputs
  behind these three documents; a rerun reproduces each document byte for byte, and the
  numbers of each translation equal those of the maintainer's Portuguese record (its
  `README.md`).
- `corrections-plan/`: revision 3 of the corrections plan, Codex review 3 with Claude's
  critique, the sizing script and its output (its `README.md`).
- `closure/`: the summary of the archive manifest and the archive verification script.
- This record, and the "Study status" section at the end of `../population-study.md`.

## Errata (2026-10-14)

The C3 investigation (Portuguese version 2, SHA-256
`3c1b2732775cdbe0b7c655af6f55521fa75362a00dbaa15f734ab77bf00dda5b`, kept unchanged) said that
leaving out the cross term C01 gave its counts an uncertainty of a few cases. The omission
affects the reported lever arm, not directly the counts 21 and 38. The errata is at the top of
`campaigns/dev-campaign-1/c3-inconclusive-investigation.md`, in four separate items, each with
its source (this one and three smaller corrections from the same review). The Portuguese errata
is a separate file in the archive with the same four items (`dev1-c3-inconclusive-errata-v2.md`);
the numbers of each item are identical in the two languages.

## The calibration declarations (the planned noise-calibration population)

Every declaration below concerns the same thing: the **planned noise-calibration population of
the corrections plan, never generated nor analyzed**. It was meant to check the error models of
the corrections (pulls, tails) on synthetic light curves before M4. It is distinct from
`calibration/v0.2/` (the v0.2 calibration on real targets, locked at the tag
`v0.2.0-calibration-lock`), and distinct from the new pre-registered calibration on real
targets required by the v0.2.1 exit criteria, which was never started.

| Where | What it declares | In git |
|---|---|---|
| `corrections-plan/m4-plan-rev3.md`, section 8, and the status note and sections 0, 4.2, 6, 9, 11 and 13 that refer to it (its section 12 is about `calibration/v0.2/`, a different thing) | prefixes `refute-v0.2.1-calibration-selection`, `refute-v0.2.1-calibration-r4-<C4>`, `refute-v0.2.1-calibration-r5-<C5>`; 17 conditions; 6900 light curves per part | added at the closure |
| `corrections-plan/calc/calibration_sizing.py` and `calibration-sizing-rev3.json` | the sizes and power of the 17 conditions | added at the closure |
| `corrections-plan/codex-review-3.md` | the review of those sizes and of the reserves | added at the closure |
| `campaigns/dev-campaign-1/c3-inconclusive-investigation.md`, observation 2 | the effect of the ingress model "has to be measured on the calibration population" (annotated there) | added at the closure |
| `m4-plan.md` (revision 1), "Demonstrating the coverage" and line 61 | prefix `refute-v0.2.1-population-noise-calibration`, 2 x 1000 light curves | archive only |
| `m4-plan-rev2.md` (revision 2), line 238 and section 8 | the same prefix, declared for an amendment | archive only |
| `calc/calibration-sizing.json` | the first sizing run (16 conditions) | archive only |
| Codex reviews 1 to 3 with Claude's critiques; Codex questions and event logs 8 to 10; the Portuguese `dev1-c3-inconclusive.md` | discussion of that population | archive only |

**Check (2026-10-14; read-only script `confirm_no_calibration.py` and its output
`calibration-check.json`, both in the archive under `.cache/population/closure/`):**
50689 non-binary files (3.86 GB) under `.cache/population/`, `docs/` and the repository root
were searched for the five strings `noise-calibration`, `calibration-selection`,
`calibration-r4`, `calibration-r5` and `v0.2.1-calibration`. Every hit is in a plan, a review, a
Codex question or event log, a script or this closure's own files; none is in a declaration,
journal, manifest or record. The only seed prefix found in any campaign or diagnostic
declaration, or in any manifest that records one, is `refute-v0.2.1-population-dev`.
`git log --all -S` finds no commit with any of the five strings.

Other uses of the word "calibration" in this folder are not declarations of that population:
"the calibration plan" in the metrics reports means the search plan of the v0.2 calibration
claim (`../population-study.md`, section 7), and "the coverage requirement of the calibration"
in `../population-study.md` means the new calibration on real targets.

## Conditions for a future resumption

1. Close the method and the six open rows (B1, B3, B4, B5, B6, B7) before any code and before
   any reserve is sized.
2. Decide beforehand whether to reuse the same development population (its limit of two
   candidate versions stays intact) or a new one.
3. No constant is tuned on the M0 to M3 development numbers.
4. Known exposure, stated in every record of the resumption: the corrections were chosen after
   the development failures were seen.

## Archive

The working files of the study (`.cache/population/`, git-ignored) were fixed as one snapshot,
`snap-v0.2.1-population-20261014T115407Z` (48717 files, 28.248 GB), and are kept in full, with
their folder structure, in a private archive kept by the maintainer.
`closure/archive-summary.md` records the snapshot, the SHA-256 of its manifest and where the
manifest sits inside the archive; `closure/verify_archive.py` checks a copy against it. The
working folder is deleted only by that manifest, after the maintainer has verified the copy; a
file that differs from the manifest, or that the manifest does not name, is kept. Publication
(for example on Zenodo or as a GitHub release asset) is a later decision, after a privacy
review.
