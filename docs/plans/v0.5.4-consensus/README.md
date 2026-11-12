# v0.5.4 consensus record

Codex's answers in v0.5.4 Information checks (#217), stored unchanged, with the model, the effort and
the Codex CLI's version. Codex is consulted read only (sandbox read-only, processors 8 to 31). The
token count is the maintainer's rule: each conversation's last turn, `input_tokens -
cached_input_tokens + output_tokens`. Divergence after three rounds goes to the more conservative
option, recorded.

## The first half's design, ledger and code (`docs/plans/v0.5.4-h1-design.md`, `ledger_i.py`, `i1_diagnose.py`, `i4_bound.py`)

Codex's review of I1's and I4's design with their frozen rules, the phase's ledger, and then the code, before any run (the maintainer's decision of 2026-11-12, 14:00, item 3). Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [h1-design-round-1-answer.md](h1-design-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (I1's enforcement order and identity checks, I4's derivatives and validity, the ledger's binding, review tokens and disk, the Fisher cost) | `fe940998cb2b8b3c2c0f9516fe14f1bf9928eec7d0c600228304b5b4d8f5fbed` |
| 2 | [h1-design-round-2-answer.md](h1-design-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (binding stops, block validation, retained diagnostics, disk bounds, I4's isolation) | `daddc29642ae39ea1b4dd303757e42e9961cf8c8c618554a9e62ec04d0f2eb06` |
| 3 | [h1-design-round-3-answer.md](h1-design-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (I4's stops, I1's provenance, a report when assembly is refused: the conservative options) | `4655f5cb0f490d62854ba2e329f6268ca7dfdb8fa3d3eadc2f678226c408099d` |

The tokens are cumulative over the conversation `h1-design`:

- round 1: 1,147,893 input (1,044,608 cached) and 7,165 output;
- round 2: 2,550,830 input (2,386,560 cached) and 13,650 output;
- round 3: 3,815,627 input (3,611,008 cached) and 17,451 output;

The conversation now counts **222,070** against v0.5.4's caps.

Applied as Codex wrote them. Round 1: the full pipeline replayed (coverage, sensitivity, deferral); every supplied block validated; `dumps` categorical; T2a's identity (v0.4's C2 compatibility, the candidate, decisive and deferred lists, inputs in the fingerprint); L over all 178; I4's mean model frozen, analytic derivatives with a baseline-aware convergence check, E extended, the condition number after column scaling, k² Fisher calls and a 4-8 CPU-h price; the ledger's `assert_bound`, independent-review tokens counted (a separate final allowance), and a disk reservation. Round 2: binding stops by a stop file with later shards skipped and a failing summary; absent versus malformed sensitivity and undeclared blocks; the decisive tests' raw and enforced messages and the report's distributions, estimators and unresolved cases; bounded records; I4's sinusoid isolated and non-finite convergence rejected; `_atomic_save` bound. Round 3 (the last) left three stop defects; by the tie-break, its conservative options were applied and recorded: in I4 an unexpected error or an oversized record is a binding stop, not part of E; I4 verifies I1's provenance (its current fingerprint, the completed and verified part, 206 cases, none skipped, no stop anywhere) before scheduling; and a summary writes its report from the verified shards when the assembly is refused, exiting with a failure.

## I2's and I3's paper designs (`docs/plans/v0.5.4-I2-I3-designs.md`)

Codex's review of the paper designs of I2 (T2a's per-host background bound) and I3 (D1's joint test with the planet side), written in the first half and frozen only after I1's result, with neither run (the maintainer's decision of 2026-11-12, 14:00, item 3). Round 2 was interrupted by the desktop app's restart and rerun from the same prompt; only the completed answer is stored. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [h1-i2i3-round-1-answer.md](h1-i2i3-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (I2's measurement correspondence and unknowns, I3's joint definition, Monte Carlo uncertainty, the price) | `4a5731c12bddadcb3e2317a95666783b60979355acfbe167a1f1a3ef380031aa` |
| 2 | [h1-i2i3-round-2-answer.md](h1-i2i3-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (I3's quantile and fatal precedence, I2's nuisances, numerical freeze and price) | `295e30f765fe001a8daa234a7d22152244f29468e236c4d586ea8f74b398dea9` |
| 3 | [h1-i2i3-round-3-answer.md](h1-i2i3-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (I2's internal detrending, open numerical starts, I3's joint envelope and quantile claim: the conservative options) | `039b36fe7e8dbb755e7016664bb99461710f952b887d57fdb63763dc2b9a67e7` |

The tokens are cumulative over the conversation `h1-i2i3`:

- round 1: 1,491,314 input (1,364,352 cached) and 10,263 output;
- round 2: 2,143,294 input (1,993,984 cached) and 14,373 output;
- round 3: 2,502,745 input (2,344,192 cached) and 19,231 output;

The conversation now counts **177,784** against v0.5.4's caps.

Applied as Codex wrote them. Round 1: I2 rebuilds each injection to read the sub-check's own measurement and the SAP depth's error, keeps σ_op (the sub-check's contrast) apart from σ_GLS (the information bound), counts unknowns so they cannot make a route, and the 56 above 20 a conditional scenario; I3's statistic defined with aliases and penalized priors as a new test, its calibration frozen, its uncertainty propagated, the joint distribution as a conditional scenario, the warning and INCONCLUSIVE paths to the maintainer, its price about 860 CPU-h. Round 2: I3's threshold is the lower α quantile with strict rejection, and a new fatal FAIL makes any gate-passed verdict REFUTED; I2's nuisances are E4's quadratic terms, its numerics filled in, its price 95-380 CPU-h, a smoke only with authorization. Round 3 (the last): by the tie-break, the conservative options were applied and the designs frozen as paper designs only: E4's internal detrending must enter I2's contrast with unit response shown, or the injection is unknown; the remaining starts are impediments; I3 needs a joint-coverage envelope (route only with its lower bound at least 0.95, a finding only with its upper bound below 0.05, unresolved otherwise) and no population guarantee for the quantile. Neither runs before the maintainer's decision.
