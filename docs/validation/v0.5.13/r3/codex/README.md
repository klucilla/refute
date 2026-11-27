# Codex's round on the frozen schema and span mapping (R3(b))

The maintainer's decision R3(b) (#218, comment 7226818333): one round, a new conversation, read
only, through `.cache/v04/tools/codex_affinity.ps1` (processors 8 to 31). Labels: `exploratory`,
`method_status: not_validated`.

| Item | Value |
| --- | --- |
| The freeze under review | commit `8b15cede2a64ee37eff08869eae81b3bf5aff19b`, `docs/validation/v0.5.13/manifests/freeze-226/` |
| [prompt.md](prompt.md) | committed with this record; written before the round |
| [answer.md](answer.md) | 13,193 bytes, SHA-256 `931e20fa9fe6e20a5dd44ae6f4d000c086bf8785dd8bc52dc4ac0328093b59cd`, unchanged (in Portuguese) |
| Thread | `01a21e91-52fc-76d0-a749-6c5cda7ce113` (new) |
| Usage | 2,541,097 input tokens (2,383,488 cached), 12,958 output tokens (4,774 reasoning) |
| Events | `.cache/v0513/codex-r3/events.jsonl`, SHA-256 `ec4f611291fa53dd50806ceb0d8a65c28d426732fa447bc6141a87bc844401bf` (not committed) |
| **Verdict** | **`NOT_APPROVABLE`**, 6 blocking items |

**The first attempt** failed before Codex reviewed anything. The folder `.cache/v0513/codex-r3/` for
`-Events` did not exist, so `Out-File` stopped the pipe. The journal records it, and the round ran
again once as an infra retry with the same prompt and arguments.

**The blocking items** (rendered in English; the answer is the source):
1. The exact key regex makes three computed measurements exact: `max_duration_hours`,
   `max_event_snr` and `max_timing_sigma_days`. The `keys_not_exact_under` exception for
   `v05.parameters.**` is wider than the one colliding field.
2. Broad patterns tolerate configuration:
   - `search_diagnostics.refined[*].factor`;
   - `near_systematic_periods_days`;
   - plan-derived `alternative` values in sensitivity;
   - effective detrending parameters recorded as metrics.
3. The gauntlet table's `test['message']` lines carry measurements with no report template. The
   JSON copy of each message stays exact under §3.1.
4. Malformed values still pass:
   - a non-numeric measurement group passes on equal lines;
   - `strict_loads` accepts `NaN`.

   A valid change of notation fails: `_fmt` can print `99999.9` or `1.0e+05` for the same field.
5. The claim exception is compared after JSON decoding, not as the bound reference bytes.
6. The unbound-alternate path:
   - it can give `PASS` for any label absent from the freeze, with any frozen reference;
   - the files are read again after their hashes are checked.

**What follows.** Under R3, this is a stop. The comparator and its schema are not approved, and
nothing is corrected before the maintainer decides.
