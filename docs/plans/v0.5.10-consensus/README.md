# v0.5.10 consensus record

## The round on part (f) before its first run (2026-11-24)

By the maintainer's decision of 2026-11-24 received at 12:51 local (#218, comment 7136727624),
item 3. The round covered **only part (f) and its isolation**: supply chain, licences and
exposure. It came before the first run. A blocking item is applied without a new round; a
blocking item that changes the phase's scope is a stop.

| File | SHA-256 |
|---|---|
| [engines-round-prompt.md](engines-round-prompt.md) | `ae8319883a641cf63243c32b580b503adc4d10f7cae93164c2cde2e85e608797` |
| [engines-round-answer.md](engines-round-answer.md) | `1b5c49dd7defae53b5065d04c85ad40ec28e6088042cfadc9cf31a5923288ba0` |

- **Codex:** Codex CLI 0.167.0-alpha.3.2, model gpt-6.2-sol, effort high, a new thread
  (`01a20e46-71fd-73d0-97cb-1a6782b07b73`). It ran read-only through
  `.cache/v04/tools/codex_affinity.ps1` (processors 8 to 31). The answer is stored unchanged, with
  its SHA-256 checked against the original.
- **Its tokens, the real sum of its events:** 4,970,254 input (4,817,152 cached) and 17,543
  output, so **170,645** review tokens.
- **Verdict: `WEAKENED`.** Blocking items 1 to 5 and 8 change no scope. Item 9 changes the scope.

**What follows from it:**
- **Items 1 to 5 and 8** are applied to the plan in
  [docs/validation/v0.5.10/engines/README.md](../../validation/v0.5.10/engines/README.md),
  section "After Codex's round". They take effect when the engines run.
- **Item 9 is a stop for the maintainer.**
  - v0.5.9's mode S already recorded the best period, epoch and SDE of these TOIs. A TLS search
    of the same light curves, with a recovery result, would produce those same quantities.
  - A different algorithm alone does not make a new diagnostic under Process diet 2, item 4. The
    same crosswalk applies to exoVetter's odd/even and centroid outputs against the recorded
    tests.
  - So part (f) stops before any engine is installed or run: nothing of part (f) has run. Parts
    (a) to (d) do not depend on it and go on within the charter.
- **Nothing installed:** no package of `requirements.txt` was installed, and no wheel was
  downloaded for installation. Only PyPI metadata was read.

## The round on the scripts and the report, before the gate (2026-11-24)

This is the charter's section 6: one Codex round on the scripts and the report, before the gate. A
blocking finding is fixed or recorded, and a divergence ends with the most conservative option.

| File | SHA-256 |
|---|---|
| [report-round-prompt.md](report-round-prompt.md) | `c40ba5c85bb52c53467cd74a3db9ef6b7439f14c5e28d3c71564f29b56e24f94` |
| [report-round-answer.md](report-round-answer.md) | `4644d6f454433accee284d461ea696bbb2e74ae6eeb2f0f2274a2e76aa96b910` |

- **Codex:** Codex CLI 0.167.0-alpha.3.2, model gpt-6.2-sol, effort high, read-only, a new
  thread (`01a20f31-a64d-72d3-ac8b-42082d51ce8d`), reviewing `0a96209`. The answer is stored
  unchanged, its SHA-256 checked against the original.
- **Tokens (the real sum of its events):** 2,478,117 input (2,314,624 cached) and 19,306 output,
  so **182,799** review tokens.
- **Verdict: `WEAKENED`.**

**What was done with each finding.** Every one was fixed or recorded; none was dismissed.

| # | Finding | Disposition |
|---|---|---|
| B1 | Five runs logged the empty file's SHA-256 for their worker | **Recorded, conservative.** `build_table.py` treats the five outputs as `unavailable_provenance` in G1 to G5. The runs, their logs and their result files are kept. Errata entry 2. |
| B2 | No per-target route (e) table in git | **Fixed in part.** `route-e-targets.csv` gives, per list and target, the on-silicon state per sector, the transits on silicon and the 2-minute history, with the expected product "not determined". The per-event timing and the non-overlapping windows are recorded as limits, not recomputed. Exit criterion 2 is marked not met as written. |
| B3 | The exposure filter misses records outside its scan | **Fixed.** `recheck_after_codex.py` scans every tracked run record and draw outside v0.5.10. The usable counts do not change: KELT-FP 307, ground 181. |
| I8 | Recount coverage and the wording of two differences | **Recorded.** The report calls them last-digit differences. The quantities not recounted are listed, and criterion 1 is marked not met as written. |
| I9 to I11 | Units, ambiguous facilities, TGLC zeros, bin edges | **Fixed in the report** with `recheck-after-codex.json`: rows against distinct TICs; ground 171 without the ambiguous labels; TGLC "not determined". |
| I12 | The ranking is provisional | **Applied:** the report says provisional, with the units named. |
| I13 | The install record | **Fixed:** `engines/install-record.json`, with the sequence, the commands and the hashes. |
| I14 | The isolation count, and the export schema not enforced | **Recorded:** errata entry 3 (24 checks, not 25). The export schema not being enforced by the launcher is recorded as a limit. |
| I15 | Post-hoc aggregation, the crosswalk timing, G1 per test | **Fixed in part:** G1 per test is added. The aggregations are labelled post hoc in `table.json`. Errata entry 4 covers the crosswalk's timing. |
| I16 | 95 attempts, wall-time limits, the TLS factor | **Fixed in the report.** |
| I17 | Missing `after` entries; what the caps measure | **Fixed:** late `after` entries for `census-d1b` and `tfopwg`. The report separates metered, estimated and unknown. |
| I18 | The cleanup's guards | **Fixed:** `cleanup_v0510.py` checks `.cache` itself for a link or junction, and hashes the Drive copies again before deleting. |
| M19 | Wording and labels | **Fixed:** labels on every result record and on the recount's Markdown, and "discovery facility" changed to the catalog field. |
