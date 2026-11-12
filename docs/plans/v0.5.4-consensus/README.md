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
