# v0.5.1 scope consensus: Codex's answers

The maintainer delegated, on 2026-11-06, the scope of v0.5.1 Battery corrections to a consensus
between Claude and Codex, within one direction: correct the targets that failed in v0.5 without
losing the ones that passed. Codex ran read-only (sandbox `read-only`, logical processors 8 to 31,
through `.cache/v04/tools/codex_affinity.ps1`) on the drafts of
[../v0.5.1-plan.md](../v0.5.1-plan.md) in three rounds of one conversation on 2026-11-06. Its
answers are kept here unchanged; the prompts stay local because they name a private folder the
session was told not to open.

| Round | Time (UTC) | What Codex reviewed | Verdict | File | SHA-256 |
|---|---|---|---|---|---|
| 1 | 13:15 to 13:24 | the first draft | `WEAKENED` (8 objections) | [round-1-answer.md](round-1-answer.md) | `e2a5d6a02a501a6c85e716c1a000b1d01521bcbb2577aef1462afc27eea501b4` |
| 2 | 13:27 to 13:33 | the plan with the round-1 changes | `WEAKENED` (6 objections) | [round-2-answer.md](round-2-answer.md) | `0eaea60624c2653e36bee63d109442e24162dfc225ca5c994cd690584cad8c7e` |
| 3 | 13:35 to 13:39 | the plan with the round-2 changes | `SURVIVED`; scope adopted | [round-3-answer.md](round-3-answer.md) | `c1de4c984fa16b915fc47663a134ad6333a7786063b2198e9e4a619954f96a39` |

How each objection was handled: the consensus record at the end of the plan. No disagreement
remained, so nothing went to the maintainer.

The numbers of the plan's section 2 come from
[../v0.5.1-wp0/diagnose_v05_records.py](../v0.5.1-wp0/diagnose_v05_records.py) (its output:
[../v0.5.1-wp0/diagnosis.json](../v0.5.1-wp0/diagnosis.json)), run on the v0.5 records, which this
phase uses for development only.

## The acceptance documents

Codex's one review of [../v0.5.1-acceptance.md](../v0.5.1-acceptance.md) and of the plan's
amendment 1 (2026-11-06, 14:14 to 14:20 UTC, a new conversation): `WEAKENED`, 7 objections (2
critical), all applied as the acceptance documents' revision 1 (the one revision before code the
plan's stop rule allows): [acceptance-review-1.md](acceptance-review-1.md) (SHA-256
`67fc49966e5410cdb5c8667afea4629b97f92443f753f552dbf85bd8d1aefe4d`).

Codex's review of the proposed revision 2 of A0 (2026-11-06, a recorded deviation from the plan's
stop rule 1): `WEAKENED`, 3 critical and 1 important objection; it requires the maintainer's
disposition before any A0 code: [acceptance-review-2.md](acceptance-review-2.md) (SHA-256
`0c49b83772b77f8a728277c6d8fe77557347d84f93be5e0a466f8ea43b8597eb`).

## A0, the corrected revision 2 (the maintainer's conditions, amendment 2)

Three rounds in one conversation on 2026-11-06; not adopted (no `SURVIVED`); the remaining
objection goes to the maintainer.

| Round | File | Verdict | SHA-256 |
|---|---|---|---|
| 1 | [a0-round-1-answer.md](a0-round-1-answer.md) | `WEAKENED` | `6b5374b37f34e226d1f1de5c5e9a50f6859a605be3fc3fd8daf99256b5dd4e70` |
| 2 | [a0-round-2-answer.md](a0-round-2-answer.md) | `WEAKENED` | `b480733cd0a3737735a757cdf5ee172b3a7c471caeae1dcf735d4b9e61204a46` |
| 3 | [a0-round-3-answer.md](a0-round-3-answer.md) | `WEAKENED` | `8337c14f2fa07fad9adcdb761cd233b2c544a029ecf6f74a7979ee86c82e76d8` |

## A0 under amendment 3 (the maintainer's decision on the cross-coverage correlation)

Three rounds in one conversation on 2026-11-06; **adopted** with `SURVIVED` in the third.

| Round | File | Verdict | SHA-256 |
|---|---|---|---|
| 1 | [a0-amendment3-round-1-answer.md](a0-amendment3-round-1-answer.md) | `WEAKENED` | `d994e244655e04dcdb45701707ed8cfcb53a8f658dffdc19a301903118964205` |
| 2 | [a0-amendment3-round-2-answer.md](a0-amendment3-round-2-answer.md) | `WEAKENED` | `a8bff73fb2423d99c05717ed223722ae39d213db35021c0d565263d2997ae4a3` |
| 3 | [a0-amendment3-round-3-answer.md](a0-amendment3-round-3-answer.md) | `SURVIVED` | `e4008c6466bbff4761b27b078ea2ee806fe7976049b932316e33c1bbd62efcdd` |

## The duration warning (amendment 3, item 2)

Codex's check of the development measurement and its recommendation (item (d), the same as
Claude's): [duration-recommendation.md](duration-recommendation.md) (SHA-256 `f782e82edf17875f05dbab095512f0056112fa3df7ccc171b60345010b17f9f1`).

## A0 window availability (amendment 5)

Codex's two answers on the finding that A0 kept no window for short periods, both unchanged:
[a0-availability-answer-1.md](a0-availability-answer-1.md) (SHA-256 `ee88efa1c53bb46106e5ceb9ea933a1ddd027ae62c028a0f6cb2ae9c5f6dca4d`) recommended keeping A0's
rule and accepting the loss (it read Claude's option (d) as amendment 4, which is about
`duration_excess`); after the measurement of option (a),
[a0-availability-answer-2.md](a0-availability-answer-2.md) (SHA-256 `64e0b25b51bb9acc2be3bba72487b2b12436a3a4b71e64d46943170b30af6507`) recommended option (a),
with the caveat that a phase-0.5 signal can bias the variance and the correlations in either
direction. The maintainer approved option (a) with a conditional exclusion (amendment 5).

Codex's three rounds on amendment 5's text (the conditional exclusion, A0.8, A0.9, the sabotage):
**adopted** with `SURVIVED` in the third.

| Round | File | Verdict | SHA-256 |
|---|---|---|---|
| 1 | [amendment5-round-1-answer.md](amendment5-round-1-answer.md) | `WEAKENED` | `5920c65bb4de507e372f9b211f9e80960a0d4e4e3edf18749c33ea871abdb526` |
| 2 | [amendment5-round-2-answer.md](amendment5-round-2-answer.md) | `WEAKENED` | `e1b40169fac9e7d2cb913df630bce6eeca708fb2a37eac093939c6a890aae4fa` |
| 3 | [amendment5-round-3-answer.md](amendment5-round-3-answer.md) | `SURVIVED` | `e5e85665791969c877b74806ea31075183d29c92f33566e49e7864e4ecc2ac5a` |
