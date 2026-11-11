# v0.5.3 consensus record

Codex's answers in round 3 of the correction line (v0.5.3, #217), each stored unchanged with its
model, effort, Codex CLI version and SHA-256. Codex is consulted read only (sandbox read-only,
processors 8 to 31, through `.cache/v04/tools/codex_affinity.ps1`). Its tokens do not count against
the review limit (the maintainer, 2026-11-09). After three rounds of divergence, the option more
conservative against a false conclusion wins, with both arguments recorded.

## The design questions

The maintainer's decision of 2026-11-11 (#217, item 2): the principled argument on both sides of
three design questions, written before stage A's numbers and validated by Codex, deciding nothing
([v0.5.3-design-questions.md](../v0.5.3-design-questions.md)). Codex CLI 0.167.0-alpha.3.2, a new
conversation.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [design-questions-round-1-answer.md](design-questions-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (7 findings) | `e3adb9b4d012ae4c8074b55604e05971fb87062ec91346f5ce34dce094efb6e4` |
| 2 | [design-questions-round-2-answer.md](design-questions-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (7 confirmed applied, 2 new) | `e60e2178a19f1a74f2c45218feac718c7c3226ca41bc308117664d9a793f2f02` |
| 3 | [design-questions-round-3-answer.md](design-questions-round-3-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `1045e6d4a9ac2dcd3aa3ae45218b191c2f3eda750d14a9b90db24a06f1cebc77` |

Tokens: round 1, 445,574 input (372,224 cached) and 4,561 output; round 2, 706,321 (620,288) and
6,458; round 3, 893,027 (802,944) and 7,481. Every finding was applied as Codex wrote it: the
chronology stated as pending until this commit; the monotonicity argument conditioned on an
operational decision, with its counterargument; the background's alternative distinguished from
its FAIL thresholds, its simulation described, the power policy's exceptions (`period_alias` at
0.90, categorical checks), the self-fulfilling risk of a noise-scaled alternative, and the "scale"
argument replaced by an argument that constrains change; the sinusoid's FAIL guards, weights and
Fréchet assumptions; the confirmation sets: none drawn or used, pool metadata examined for T3b.
Round 3: each question keeps a genuine argument for changing, which justifies reconsidering or
deriving a convention, not a particular relaxation.

## The stage A design

The design of stage A ([v0.5.3-stageA-design.md](../v0.5.3-stageA-design.md)), its ledger shim
and item (a)'s script (`docs/validation/v0.5.3/stageA/`), reviewed before any run. Codex CLI
0.167.0-alpha.3.2, a new conversation.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [stageA-design-round-1-answer.md](stageA-design-round-1-answer.md) | gpt-6.1-sol, high | `REFUTED` (10 findings) | `b0eb17f2f041265f00556a1aeaf14989bdde7cc1934f2d258238d406a4d2db0d` |
| 2 | [stageA-design-round-2-answer.md](stageA-design-round-2-answer.md) | gpt-6.1-sol, high | `REFUTED` (10 points) | `a1a0157ede13e9f2ff1d3ab434ac9d927c3646b8be7a78ebd0c5d98b72049475` |
| 3 | [stageA-design-round-3-answer.md](stageA-design-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` for item (a) and for the design | `456c554062408673f6e216a1ad045cf03e5e5bf93dad7054fdfb6d4149863f8a` |

Tokens: round 1, 1,432,503 input (1,292,160 cached) and 9,466 output; round 2, 2,603,762
(2,435,456) and 17,116; round 3, 3,604,326 (3,414,272) and 27,278. Every finding was applied as Codex
wrote it: kept retention kept apart from the evidence-qualified PASS, so a warning blocker counts as
recoverable (a warning FAIL gives WEAKENED) and only fatal blockers can be bounded as lost; the
sinusoid's oracle GLS standard error with the flag's power at 1; the background's scatter as an
audit, not a bound; the joint Fisher information for `odd_even` with per-sector level columns and
the contrast `(1, -1, 0, ...)`; unbounded blockers recoverable; sampling uncertainty apart from the
bounds' validity, and T2a's plug-in as a conditional scenario; item (a)'s traces of the group
variance, the empirical events (each dropped event and its reason) and D2's A0 depths, with replays
excluded and any trace failure quarantined; the strict cap, prospective transfers, the token and
day checks before each step, the earlier ledger checked in a `finally`; no child process, and (c3)
on hold until a batch deadline enforced during the run is designed and reviewed. **One finding was
answered rather than applied:** round 3 read `caps.json`'s zero review tokens as an omission of
Codex's tokens; by the maintainer's decision of 2026-11-09 Codex's tokens do not count against the
review limit, so `caps.json` now states that rule and counts independent review sessions only (none
yet).

## Item (b)'s implementation

`docs/validation/v0.5.3/stageA/d2_bounds.py`, reviewed before its run. Codex CLI 0.167.0-alpha.3.2,
a new conversation.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [d2-bounds-round-1-answer.md](d2-bounds-round-1-answer.md) | gpt-6.1-sol, high | `REFUTED` (3 findings) | `1cef8f94ac65dceb47c4f176b278011560826f2cf414d0d187c64b8b9b2825a6` |
| 2 | [d2-bounds-round-2-answer.md](d2-bounds-round-2-answer.md) | gpt-6.1-sol, high | `REFUTED` (3 corrections) | `9f73ba3b0c6eaf0b373226125c5078c0a27ecd4c51f652d499386fd6c03d2707` |
| 3 | [d2-bounds-round-3-answer.md](d2-bounds-round-3-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `bdd5a39094e9f1ee3c372f97ed7e9420fb389c242351140665a2000defd4c5a3` |

Tokens: round 1, 773,957 input (698,240 cached) and 8,439 output; round 2, 1,465,182 (1,364,864)
and 13,663; round 3, 1,998,102 (1,885,184) and 16,387. Applied as Codex wrote them: item (a)'s
refusals read and bound into the fingerprint, an absent or failed (a) diagnosis counted
optimistically; the generator's known multiplicative trend on the odd and even template columns
only; the sinusoid's residual box in normalized coordinates (a fixed-normalizer oracle assumption),
the odd/even columns raw. Codex checked the polarization against a dense covariance (relative error
1.3e-16) and seven counting scenarios.
