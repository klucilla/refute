# Corrections plan for M4 and M5 (TESS pack): not implemented; open blocking points

**Status: not implemented; open blocking points.** This folder keeps the last revision of the
plan of corrections that M4 and M5 would have measured, its third review by Codex, and the
sizing script of its calibration population. The plan is a set of hypotheses and
specifications. No code, test, calibration case or measurement was made from it. The
population study was closed by a scope decision on 2026-10-14 (`../closure-record.md`) while
6 of the 9 rows below were open.

| File | What it is | SHA-256 |
|---|---|---|
| `m4-plan-rev3.md` | revision 3 of the plan (2026-10-14), byte-identical to the reviewed file | `cc9b0cd85d4f77028b82f977b72f3ff0376e6ef506d34e820dc0e4b1b3004f18` |
| `codex-review-3.md` | Codex review 3 of revision 3, with Claude's critique, translated from Portuguese (234 numeric tokens, identical; `../campaigns/dev-campaign-1/investigations/check_numbers.py`) | `deaa6d0d88b71b86f4f05ae5080f87c39412af688ccd9022548dcbfcc310a96f` |
| `calc/calibration_sizing.py` | the sizing script cited by revision 3 (section 8) | `aa45d4ed512fb45bb0c29d60a784c2360e457a55d8179c237fba431369ddac79` |
| `calc/calibration-sizing-rev3.json` | its output, byte-identical (CRLF line endings, as written on Windows) | `185255ffc57cc84710cc0195dd4d7e0c90116c935264aabad9d0840c5c3f1e9f` |

The `calc/` folder keeps the relative paths that revision 3 cites. The sizing script is seeded;
run again on a copy on 2026-10-14, it wrote a byte-identical JSON. It refuses to replace its
output, so a rerun needs a copy of the script in an empty folder.

## The nine rows after review 3

Revision 3 marked every row "closed" (its section 0). Codex review 3 found six of them open,
and Claude's critique agreed with each (`codex-review-3.md`). These are the final states; no
revision 4 was made.

| Row | Blocking point | Final state | What is missing (review 3) |
|---|---|---|---|
| B1 | covariance of the hidden-window depth (baseline fit) | **open** | the covariance under correlated noise is A·C·A′, not β²(X′WX)⁻¹; the conservative bound is not shown |
| B2 | the train β transferred to the hidden year | closed | — |
| B3 | the tail of the capacity rule | **open** | b and s are set per noise model, which the tool does not receive; T1 pools the noise models |
| B4 | the `period_alias` statistic | **open** | the input curve (raw today) is not fixed; rules for d_box ≤ 0, a singular fit and non-finite values |
| B5 | prewhitening that protects the transit | **open** | the Lomb-Scargle and FAP operation is not unique; the paired comparisons are not fully defined; T5 and M1 only without variability |
| B6 | estimand, unit and size of the calibration | **open** | the joint power is not shown for the actual design; the twin protocol; the probability of a missing denominator; the M1 false pass used a lower bound |
| B7 | the revision cycle and the M5 rule | **open** | the reserve guarantee by a commit hash is false (git commit ids are 40-character SHA-1 and can be prepared in advance); M5 defaults, variants and trigger aggregation |
| B8 | directed mode in M5 | closed (removed from M4 and M5; a separate pending item) | — |
| N | blindness note (hidden-year detrending) | closed | — |

New blocking points of review 3 (R3-1 to R3-6) fall under these rows: R3-1 under B3, R3-2 and
R3-3 under B5, R3-4 under B3 and B6, R3-5 and R3-6 under B7.

On the joint power of the 17 conditions: revision 3 gives 0.838 by an independence
approximation; review 3 replaces it by the union bound, about 0.8244. That value is a lower bound
on joint approval under the sizing hypotheses (union bound), equivalent in that scenario to an
upper bound of about 17.6% on rejection. It is not a measured rejection rate and does not include
a missing denominator.

## The calibration population of this plan

Revision 3 (section 8) declares a synthetic calibration population for the corrections:
prefixes `refute-v0.2.1-calibration-selection`, `refute-v0.2.1-calibration-r4-<C4>` and
`refute-v0.2.1-calibration-r5-<C5>`; revisions 1 and 2 named it
`refute-v0.2.1-population-noise-calibration`. It is the **planned noise-calibration population,
never generated nor analyzed**: no declaration, journal, manifest, record or commit carries any
of these prefixes (checked by script on 2026-10-14; `../closure-record.md`). It is distinct from
`calibration/v0.2/` (the v0.2 calibration on real targets, verified at the tag
`v0.2.0-calibration-lock`, commit `cc9d104`) and from the new pre-registered calibration on real
targets that the v0.2.1 exit criteria require, which was never started.

## Earlier revisions and reviews (kept in the archive of the study, not committed)

All in Portuguese except the plans, which are in English. Listed with the archive manifest
(`../closure/archive-summary.md`).

| File | What it is | SHA-256 |
|---|---|---|
| `m4-plan.md` | revision 1 of the plan | `aeef07cf384c6ad465f43630a36b5e88ae2b477ab02d0671b2603fd84efd2efd` |
| `m4-plan-rev2.md` | revision 2 | `515fe33f352fe204213b0763d2e4d6094d21cd370e93ff5cdd104bc6c48cc468` |
| `codex-m4-plan-review.md` | Codex review 1, with Claude's critique | `c2f845e34822fc9ef591b07ec9cf24d6fb266fd4a5edb2d68067a738c4b62b7f` |
| `codex-m4-plan-review-2.md` | Codex review 2, with Claude's critique | `9e65a2511660414bd51f8f7638c031bf8b00dd71e706a4a929f8f84bff531400` |
| `codex-m4-plan-review-3.md` | Codex review 3, with Claude's critique (the source of `codex-review-3.md`) | `044a5fd9e44bd15f646450b6bfef2331b46c3e42f65595c318c9502700539f61` |
| `codex-m4-plan-review-critica.md` | Claude's critique of review 1, alone | `32ebb6abc38ee952862fff0c82a2654e37ec0434cf126905262cd1d4e99ff1f0` |
| `codex-m4-plan-review-2-critica.md` | Claude's critique of review 2, alone | `f32f74a09294324bb19b4d53ad5eca1df1fca15292b6d357be85915410b5c8ec` |
| `codex-m4-plan-review-3-critica.md` | Claude's critique of review 3, alone | `14d0c06b1f8386ab28f763605cd80cc3aabb75ff55f5039c8298c995eb592865` |
| `codex/pergunta-8.md`, `codex/resposta-8.txt` | question and raw answer of review 1 | `483e5befb9ab567512679464a920c1fe67dd078e3e8c81121499c78af31067f6`, `784faa83f26a5c8685aa66176be12d8955b065a26d29db7c864f9b929c9aa066` |
| `codex/pergunta-9.md`, `codex/resposta-9.txt` | question and raw answer of review 2 | `d2561de311e49ddaeda0f666a7450d830adf6e0d84bce637cd423ae9871fe361`, `274c0ac33a6d47f35c8691ac9aaecef43f1e9a66baa856a48f43e4806a724b46` |
| `codex/pergunta-10.md`, `codex/resposta-10.txt` | question and raw answer of review 3 | `feeedd6e12a56f6323930845194292ecf4c6fc02148d68074666d5542463f84c`, `ca2299515f55c6a2c6847d56bef2ca94c5217f8da63e600511ceb9125f1c0493` |
| `calc/calibration-sizing.json` | first sizing run (16 conditions), superseded by the rev3 run | `3a989764ce7e92db8e0b1d37dd7b927ce0c3fd164cf8155a8697361ed00a69d4` |

## Before any resumption

The conditions are in `../closure-record.md`: the method and the six open rows are closed before
any code and before any reserve is sized; the reuse of the development population (within its
limit of two versions) or a new one is decided first; no constant is tuned on the M0 to M3
development numbers; and the known exposure is stated: these corrections were chosen after the
development failures were seen.
