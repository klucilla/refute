# Proposal: `refute demo`, then `refute check`

**Status: a proposal, not adopted.** It was written on 2026-11-26 by the maintainer's decision
(#218, comment 7203695669, item A5b).

- It contains no code. Any code in `src/` is a stop for the maintainer.
- It is engineering-lane work if [the two-lanes proposal](two-lanes-proposal.md) is adopted, and
  phase work otherwise.

## 1. Why

**The gap.** A newcomer cannot see Refute work in under a minute today.

- `refute calibrate`, `discover` and `replicate` need public data, a cache and a long run.
- `refute verify` and `refute check-dossier` check records, but they show no attack being made.

**What the demo does.** It shows the core idea ("find signals, try to kill them, keep what
survives") on synthetic data, offline, in seconds, with a report a person can read.

## 2. `refute demo` (first)

### 2.1 Behaviour

```
refute demo [--out DIR] [--seed N] [--open]
```

- **Data:** synthetic only. It uses the existing generator,
  `refute.packs.tess.synthetic.scenario_data`, with the fast plan (`fast_plan_dict`), so no new
  science code is written.
- **Scenarios,** proposed (5, each with its seed fixed):
  - `planet`, a transit that should survive;
  - `eb_secondary`, an eclipsing binary with a secondary eclipse;
  - `eb_odd_even`, an eclipsing binary with unequal odd and even depths;
  - `blend`, a neighbour's signal;
  - `noise`, no signal, where the search should find nothing to attack.
- **No network and no cache.** It writes only under `--out`, by default `./refute-demo/` in the
  current directory, never inside the package.
- **The report.** It writes `report.md` and `report.html`:
  - for each scenario, the injected truth, what the search found, each test with its status and
    **coverage**, and the scenario's class;
  - one plot per scenario: the phase-folded light curve, with the odd and even transits marked;
  - a header that states, in plain words:
    - that these are synthetic scenarios;
    - that the output is a demonstration, not a verdict on any real star;
    - `method_status: not_validated`.
- **Self-check.** The classes it prints are compared with a committed expectation file (the
  scenario names and the expected classes at the fixed seeds).
  - A mismatch prints `DEMO MISMATCH`, names the scenario, and exits 1.
  - So the demo is also a smoke test of the battery's behaviour. It decides nothing about real
    data.
- **Time.** At most 30 s on the reference machine, measured before acceptance on a clean clone
  with a cold start (`uv run refute demo`). If it does not fit, the plot or a scenario is dropped,
  never a test.
- **Workers.** At most 2, so it runs on a laptop. The CPU rules of `CLAUDE.md` apply to the
  project's own runs, not to a user's.

### 2.2 Acceptance (written before any code)

1. The demo runs offline. A test runs it with the socket disabled (`--disable-socket`, as the
   existing suite does).
2. It finishes in under 30 s on CI's ubuntu job. This is measured, not assumed, and the
   threshold is fixed before the code.
3. The report contains, for every scenario: every test of the plan, its status and its
   coverage. A test with zero coverage is shown as `INCONCLUSIVE`, never as a pass.
4. The expectation file matches at the fixed seeds. Changing it is a reviewed change, never an
   update to make the demo pass.
5. No output says "confirmed", "discovery" or "planet found". The words checked are listed in a
   test.
6. The README's quick start can then add `refute demo` as its first command. That is public text,
   and needs the maintainer's approval.

### 2.3 What it does not do

- No real data.
- No verdict on any target.
- No dossier that `refute check-dossier` would accept as a published record.
- No lock.

## 3. `refute check` (later, separate)

```
refute check --tic <TIC ID> --period <days> --t0 <BTJD> --duration <hours> [--out DIR]
```

It runs the battery on **real** TESS light curves of one star, entering through a given
ephemeris. That is the ephemeris entry that v0.5.9 prototyped; it is exploratory, and nothing in
it is adopted. It is a larger step than the demo, and it comes only after the demo. Before it
could be built:

- **Which battery.** Version 4 carries the limits label 'WEAKENED; does not meet D1, D2, D4, T2a',
  and every output must carry it. Version 5 is not adopted for confirmatory use. The output is
  `exploratory`, `method_status: not_validated`, and never a verdict.
- **Exposure.** A star that a user checks becomes exposed for Refute's own confirmatory work
  only if Refute's maintainers run it. The command must never write to the project's records. A
  run by the project itself is logged under the rules of exploration (Process diet 2, item 4).
- **Data and licences.** Light curves come from MAST through `lightkurve`, which is already a
  dependency. The data licence statement needs a `sources/` record (the operating rule of issue
  #34). No restricted catalogue (TESS-EB, Gaia) is bundled.
- **The ephemeris is the user's input.** The output says so, and gives the archive values next to
  it only when they are retrieved with their source and date (the non-negotiable rule on
  scientific facts).
- **Wording.** Same as section 2.2, item 5. It never submits anything anywhere.
- **Cost.** Downloads are bounded and cached in the user's chosen directory. A `--dry-run` lists
  what would be fetched.

## 4. Order and stops

1. The maintainer decides on this proposal. It then goes either to the engineering lane, if
   adopted, or to a phase charter.
2. The acceptance of section 2.2 is written before any code. The first commit in `src/` is a
   stop, with Codex's review of the diff.
3. `refute check` gets its own proposal and acceptance after the demo is merged.
