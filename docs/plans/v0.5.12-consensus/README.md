# v0.5.12 consensus record: Codex on the charter draft (2026-11-25)

Written on the maintainer's decision recorded at 16:43 local on 2026-11-25 (#218, comment
7172688755), item 3: Codex reviews the charter draft in one round, up to three because the charter
fixes acceptance limits, resuming the same thread. Answers that change nothing are recorded here; a
divergence is settled by the more conservative option.

## The rounds

- **Codex** ran read-only through `.cache/v04/tools/codex_affinity.ps1`, on processors 8 to 31.
  - **Codex CLI** 0.167.0-alpha.3.2 (`codex_affinity.ps1 -VersionOnly`).
  - **Model and effort:** gpt-6.2-sol, effort high, read from the Codex configuration in force when
    this record was written; the event files do not name them.
  - **Thread:** `01a21442-fe21-7871-bb52-594741873b3f`, new for this charter; rounds 2 and 3 resumed
    it.
  - These rounds ran before the phase opens, outside any launcher: they are not v0.5.12 work
    (charter, section 6).
- **The files,** stored unchanged; each answer's SHA-256 was checked on the copy against the
  original under `.cache/v0512/`:

| File | Bytes | SHA-256 |
|---|---|---|
| [r1-codex-prompt.md](r1-codex-prompt.md) | 4,694 | `1371695c026862d41caced27db716c6d5aaeb103dd57ed0feac37c102b39cee5` |
| [r1-codex-answer.md](r1-codex-answer.md) | 11,743 | `ecac79f5f67cb7f12e411c4d73ffba5f85effb47989c1934fe41f973111268c2` |
| [r2-codex-prompt.md](r2-codex-prompt.md) | 1,570 | `bbb8a052906d61db34d7ff19d80c9e8a1e0e1deb77e6bee1d879f58cf975a927` |
| [r2-codex-answer.md](r2-codex-answer.md) | 4,295 | `a82bd5f0bb74513131fbfeb1d0331c5ff39a695c0825f7eead8d803a5ec0bae7` |
| [r3-codex-prompt.md](r3-codex-prompt.md) | 2,173 | `4946f23f09f9ca3c3250bb22759c4231757a81e3d3fe0d3a52db7c50be669b76` |
| [r3-codex-answer.md](r3-codex-answer.md) | 2,671 | `53bf9972b03eddd00cb3e1a0ce38c808344af064cec1d559dd21b49f5e929493` |
| [wilson_design.py](wilson_design.py) | 1,325 | `9aea36b7b99fcace28ae1b9b8e5243d7970c896c1351014bfd306d8c6d0aab59` |

- **The prompts** do not name the private folder that Codex must not open. They forbid every path
  on the K: drive instead, which is stricter (the v0.5.11 gate's finding 17).

| Round | Charter SHA-256 reviewed | Verdict | What it found |
|---|---|---|---|
| 1 | `1267bbf4…e855` | `REFUTED` | 6 blocking items: the null at F1's level (a box model), a sensitivity control for M2, #223's oracles and baseline procedure, case identity and F-1's causal evidence, enforceable metering, an executable gate and seal |
| 2 | `dcfec0c0…6979` | `REFUTED` | items 1 and 2 applied; exact fixes for items 3 to 6 |
| 3 | `c1088dc7…c8ed` | `REFUTED` | items 3, 4 and 6 applied (6 by the recorded alternative); item 5 not applied in full: the disk bound must be phase-wide |

## Codex's choices

- **#222's limit:** keep the maintainer's proposal: the 95 % Wilson upper bound at most 1 %, with
  3,000 cases per family, so at most 19 `fail` and 0 `not_assessed`; with the corrected null (a
  noiseless box on F1's mask) and, if M2 runs, the sensitivity control (seeds 200001 to 200300, at
  least 281 `fail` of 300 per family). Codex checked the arithmetic: the upper bounds for 19 and 20
  failures are 0.98710 % and 1.02753 %; the pass probability per family is 99.9711 % at the
  benchmark 0.0026997961.
- **The caps:** keep 3 CPU-h, 0 GB of downloads and 2 GB of peak disk, conditional on
  demonstrating the amended meter before M1. Codex recounted v0.5.11's ledger: 3.015 measured
  CPU-h, of which tests 2.638, and estimated 0.265 CPU-h per 21,000 F1 calls.

## Divergences, settled by the more conservative option

- **Round 2, item 6: a change to the gate protocol.** Codex proposed adding a rule to
  `.claude/commands/gate-review.md`. That is a rule change, so it was not made: it is the
  maintainer's decision. The charter instead has six exit criteria judged at the seal, and the gate
  is the closure condition of ROADMAP.md. Codex found this alternative applied in round 3.
- **Round 3, item 5: the phase-wide disk bound.** The three rounds the maintainer allows were used.
  Codex's exact fix is quoted in the charter's step 0 and applied **without a fourth round**, so
  Codex has not checked its application. The last verdict on record is round 3's `REFUTED`.

## Tokens, the real sum of the events

Each round's `turn.completed` usage, summed over the three rounds (every resumed round sends the
thread again):

| Round | Input | of which cached | Output | Review tokens (input not cached + output) |
|---|---|---|---|---|
| 1 | 1,339,589 | 1,212,416 | 11,598 | 138,771 |
| 2 | 2,145,185 | 1,992,704 | 15,195 | 167,676 |
| 3 | 2,906,726 | 2,739,072 | 17,658 | 185,312 |
| **Sum** | **6,391,500** | **5,944,192** | **44,451** | **491,759** |
