# v0.5.4: the restart test of `launch_detached.py` (#217)

These are the records of the harmless probe that showed whether a run started through
[`../launch_detached.py`](../launch_detached.py) survives a restart of the desktop app. The
maintainer's decisions of 2026-11-12, 15:46, item 4, and 18:05, item 3, asked for it. The result
is in [`../h1-stop-report.md`](../h1-stop-report.md) ("The restart test"): **all 16 criteria held**.

The probe read no data and wrote only under `.cache/v054/restart-test/run-1/`. These files are
copies of what it wrote.
- In git, the JSON files written with Windows line endings are stored with LF.
- The three scripts are copies of what ran from `.cache/v054/tools/`. There, `ROOT` (three
  folders up) is the project root; from this folder it is not, so they are kept as a record of
  what ran.

| File | What it is |
|---|---|
| `criteria.json` | The criteria, written before the launch: a beat every 10 s for 60 minutes, at most 30 s between beats, mask 0xFFFFFF00, priority 0x4000 |
| `watch.json` | The app's two processes above the agent's shell (PID and creation time), written before the launch |
| `launch.pid.json` | The launcher's record: the venv launcher's PID and creation time, written while it was suspended |
| `identity.json` | The interpreter's own record: PID, creation time, parent and the parent's creation time, mask, priority |
| `heartbeat.jsonl` | 361 beats, each with its sequence, UTC and monotonic times and each watched process's state; the final line |
| `pre.json`, `post.json` | The checks before (23:18:27 UTC) and after (00:15:32 UTC) the restart |
| `after_restart.json` | The new app processes above the agent's shell after the restart |
| `final.json` | The final check: each criterion and `survived_the_restart: true` |
| `restart_probe.py`, `restart_check.py`, `app_ancestors.py` | The probe, the check and the process-chain reader |

A process counts as alive only when its PID opens with the recorded creation time and a
zero-timeout wait on its handle times out. A query that fails is "unknown", and any "unknown"
fails the decision. This is round 3's conservative option from Codex (`h1-driverv3`).
