# v0.5.4, first half: the stop report (#217)

**State: the first half ended**, under the maintainer's decisions of 2026-11-12, 14:00, 15:46 and
18:05. The maintainer's decisions of the same night, recorded on #217, answer this report and
open the second half. `method_status: not_validated`. Development data only. Nothing
here is a verdict on a claim; no target, test rule, battery, lock or `src/` file changed.

## I1. T2a's `systematics` losses, by class

From [`i1-diagnosis.json`](i1-diagnosis.json) (`i1_diagnose.py`; the replay order coverage, then
sensitivity, then deferral). Classes: (iii) a code defect, (ii) a refusal or a procedure, (i)
insufficient sensitivity.

| T2a group | (i) | (ii) | (iii) |
|---|---:|---:|---:|
| 2 to 4 sectors | 63 | 41 | 0 |
| 5 to 20 sectors | 40 | 25 | 0 |
| **all (169 losses)** | **103** | **66** | **0** |

- Class (i), the non-detectable block: `background` 102, SAP 1. The background block's power has a
  median of 0.371 over the 103 class-(i) cases.
- Class (ii), the reasons (the sub-checks that could not run): 42 grid refusals (`sap_vs_pdcsap`
  outside A0's grid), 14 with no transit measured in the background or SAP flux, 8 with an error
  that cannot be measured, 2 with no transit measured in the PDCSAP flux or in both series.
- No class (iii): no code defect was found, so no stop on that ground.
- D2, for reference: `odd_even` (i) 25, (ii) 1, unresolved 1 (planet 3129); `sinusoid` (i) 18,
  (ii) 8.
- CPU: 6.40 CPU-h.

## I4. `odd_even`'s bound with the transit shape as a nuisance

From [`i4-bound.json`](i4-bound.json) (`i4_bound.py`, fingerprint `161851db746b905b`; completed
through `i4_rest.py` and `i4_rest2.py` after the interruption of 15:40).

- **L = 2 against the threshold of 23: the outcome is `route`.** L counts the eligible fresh
  planets whose bound is below the required power with the transit shape as a nuisance; E = 15
  planets failed the convergence check and are counted apart, so L + E = 17 is also below 23. The
  frozen rule: L ≥ 23 a draft, L < 23 ≤ L + E unresolved, otherwise route.
- Fresh set: 177 eligible planets (planet 3129 excluded, the maintainer's decision of 15:46: power
  1.0, its battery `REFUTED`), 162 valid; the two below are 3041 and 3182. The nuisance widens the
  bound very little: σ with the nuisance over σ with the known template has a median of 1.00004
  and a maximum of 1.002. Six planets fall below at the oracle for `sinusoid`; they are kept
  apart and never enter L.
- The v0.5.2 set, for comparison: L = 2 (1046, 1075), E = 15.
- No row was rerun outside the plan; every finished shard was read exactly once.

## I2 and I3: frozen on paper, not run

[`docs/plans/v0.5.4-I2-I3-designs.md`](../../plans/v0.5.4-I2-I3-designs.md), frozen after I1 with
round 3's conservative options (Codex, `h1-i2i3`). Neither ran. The impediments to running, each
needing a new reviewed design step and the maintainer's authorization:
- **I2** (T2a's per-host bound on the background-rise error): the internal detrending in the
  contrast, with a demonstration of unit response and of nuisance removal; the remaining
  numerical starts; a measured, smaller cost (the estimate is 95 to 380 CPU-h, against a second
  half of 25).
- **I3** (D1's joint test with the planet side): the starts, bounds and convergence criteria; the
  joint-coverage envelope; a justified reduction of its cost (about 860 CPU-h by extrapolation).

## The driver correction for future parts and the detached launcher

Committed in `65680a3`, reviewed by Codex in three rounds (`h1-driverv3`, the consensus record).
- [`budgeted_v3.py`](budgeted_v3.py): the projection on measured CPU, the crash charge still
  consumed in the line, the total and every caller's cap; never applied to a part that ran under
  v0.5.2's rule; a larger measured projection can raise the part's own cap after the checkpoint
  (documented and tested). Not used by any run of this half.
- [`launch_detached.py`](launch_detached.py): a candidate launcher that starts its child suspended
  and broken away from the app's job, records its PID and creation time, then resumes it. A
  proposal: `scripts/launch_affinity.ps1` stays the launcher of record.
- Tests: 28 passed, 0 failed, 0 errors, 0 skipped (JUnit), offline.
- Codex: `WEAKENED` in each round; every correction applied; round 3 found the driver's and the
  launcher's points resolved and gave conservative options for the restart check, which were
  applied.

### The restart test

**The probe survived the restart of the desktop app: every one of the 16 criteria held.** The
criteria were written before the launch. The probe read no data and wrote only under `.cache`;
its records and scripts are copied to [`restart-test/`](restart-test/README.md).

- **The probe.** A harmless probe ran 60 minutes from 2026-11-12 23:18:25 UTC, started through
  `launch_detached.py`. Every 10 s it wrote a numbered heartbeat. In each beat it also recorded
  whether each of the two app processes above the agent's shell was still the same process: same
  PID, same creation time, and its handle not signaled.
- **The restart.** The maintainer restarted the app once.
  - The probe saw both app processes end at 00:13:06 UTC.
  - The new app processes were created at 00:13:08 and 00:13:28 UTC.
  - The heartbeats never stopped: 361 beats, no gap in the sequence. The largest interval was
    10.009 s by both the UTC and the monotonic clock, against a tolerance of 30 s fixed before.
- **The probe's own processes.** These are the venv launcher and its interpreter child.
  - They were alive with the same PIDs and creation times before the restart (23:18:27 UTC) and
    after it (00:15:32 UTC).
  - The interpreter's parent was the launcher.
  - The affinity mask was 0xFFFFFF00 and the priority class 0x4000 (BelowNormal).
  - The probe wrote its final line after 3,600.3 s, and both processes then ended, with nothing
    on standard error.
- **Not shown by this test.**
  - It does not show survival of a reboot, a sign-out, or an exit of the app's process tree by
    other means.
  - The probe ran no worker pool, so the driver's workers were not exercised. They are the
    interpreter's children, in the venv launcher's job.
- **The decision.** By the maintainer's decision of 2026-11-12 (night), item 7b,
  `launch_detached.py` becomes the launcher of record for long runs from now on, since the probe
  survived.

## Consumption of the first half

| Resource | Used | Cap (first half) | Share |
|---|---:|---:|---:|
| CPU, charged | 17.17 CPU-h | 25 | 69 % |
| of which the crash charge of `h1_i4` | 4.90 CPU-h | | |
| CPU, measured (charged less the crash charge) | 12.27 CPU-h | | |
| Tokens, Codex conversations | 767,841 | | |
| Tokens, independent review (Fable 5.2's audit, apart) | 266,456 | | |
| Tokens, in all | 1,034,297 | 2.0 M | 52 % |
| Agent-days (wall clock, an upper bound) | 0.91 (0.50 active) | 4 | 23 % |
| Disk under `.cache/v054` | 4.3 MB | (phase) 5 GB | 0.1 % |

The Codex conversations: `h1-design` 222,070; `h1-i2i3` 177,784; `h1-i4rest` 104,498;
`h1-i4rest2` 114,356; `h1-driverv3` 149,133. The audit's tokens are the harness's count, as the
maintainer reported it; they are recorded in `caps.json` as an independent review. In the phase's
scope the same 1,034,297 are 30 % of 3.5 M.

CPU by part: `h1_i1` 6.398; `h1_i4` 5.083 (its crash charge; its 10 finished shards measured
0.186); `h1_i4_rest` 0.363; `h1_i4_rest2` 5.326. No cap was reached and no cap reached 80 %.

## The second half

**Decided.** The maintainer decided on 2026-11-12 (night), after Fable 5.2's strategic audit
([`docs/plans/v0.5.4-fable-audit.md`](../../plans/v0.5.4-fable-audit.md), an agent's proposal that
decides nothing), with the decisions recorded on #217 before any action:
- The second half becomes the audit's section-5 plan, steps 1 to 7, adjusted by Codex's check of
  the audit's 18 points and of that plan.
- The frozen I2 and I3 stay as a record, superseded, and do not run.

**What the first half leaves for it:**
- **I4 routes:** `odd_even`'s loss is not explained by the transit shape as a nuisance.
- **I1:** 103 of T2a's 169 `systematics` losses are in class (i), almost all in the `background`
  block.
- **I2 and I3, as frozen,** cost far more than the second half's 25 CPU-h.
