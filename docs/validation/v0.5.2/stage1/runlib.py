"""Shared pieces of the v0.5.2 stage-1 experiments E2 and E3: a run bounded by its cap, resuming
from its records, and a paired interval for binary endpoints."""

from __future__ import annotations

import json
import math
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from scipy import stats

# a share of the cap kept unspent, for the units of a batch already running when it is reached
CAP_RESERVE = 0.05


def clopper_pearson(k: int, n: int, confidence: float) -> tuple[float, float]:
    """The exact two-sided binomial interval."""
    alpha = 1.0 - confidence
    lo = 0.0 if k == 0 else float(stats.beta.ppf(alpha / 2.0, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))
    return lo, hi


def paired_binary(baseline, arm, confidence: float = 0.95) -> dict | None:
    """The change ``arm - baseline`` of a binary endpoint on the same curves, with conservative
    simultaneous bounds: exact intervals for the probabilities of a gain (0 to 1) and of a loss (1
    to 0), each at level ``1 - (1 - confidence) / 2``, combined. Identical pairs do not give zero
    uncertainty, so the interval is valid at the boundary. None when empty."""
    pairs = [(bool(a), bool(b)) for a, b in zip(baseline, arm, strict=True)]
    n = len(pairs)
    if n == 0:
        return None
    gains = sum(1 for a, b in pairs if not a and b)
    losses = sum(1 for a, b in pairs if a and not b)
    level = 1.0 - (1.0 - confidence) / 2.0
    g_lo, g_hi = clopper_pearson(gains, n, level)
    l_lo, l_hi = clopper_pearson(losses, n, level)
    return {
        "n": n,
        "gains": gains,
        "losses": losses,
        "difference": (gains - losses) / n,
        "lo": g_lo - l_hi,
        "hi": g_hi - l_lo,
    }


class Guarded:
    """A picklable wrapper: a unit's failure becomes a record, with the CPU it used."""

    def __init__(self, fn, uid, fingerprint):
        self.fn, self.uid, self.fingerprint = fn, uid, fingerprint

    def __call__(self, arg):
        started = time.process_time()
        try:
            return self.fn(arg)
        except Exception as exc:  # noqa: BLE001 - recorded, never dropped
            return {
                "unit": self.uid(arg),
                "fingerprint": self.fingerprint,
                "status": "ERROR",
                "reason": repr(exc),
                "cpu_seconds": time.process_time() - started,
            }


def read_records(records: Path, fingerprint: str) -> list[dict]:
    rows = []
    if records.exists():
        rows = [json.loads(x) for x in records.read_text("utf-8").splitlines() if x.strip()]
    if any(r.get("fingerprint") != fingerprint for r in rows):
        raise SystemExit("a record of another fingerprint: refused")
    return rows


def bounded_run(
    fn, uid, schedule, fingerprint, out, cap_hours, probe_units, batch, workers, limit=None
):
    """Runs the unfinished units in batches. Before any dispatch it checks the cumulative cost; it
    projects against the **whole** unfinished schedule; it refuses to continue when that projection
    passes the cap; a batch is never larger than the remaining budget allows. ``limit`` only bounds
    this invocation, and never changes the projection. Returns the state."""
    records = out / "records.jsonl"
    rows = read_records(records, fingerprint)
    done = {r["unit"] for r in rows}
    spent = sum(float(r.get("cpu_seconds", 0.0)) for r in rows) / 3600.0
    unfinished = [a for a in schedule if uid(a) not in done]
    args = [(*a, fingerprint) for a in unfinished]
    guarded = Guarded(fn, uid, fingerprint)
    costs = [float(r.get("cpu_seconds", 0.0)) for r in rows]
    dispatched = 0
    state = "complete"
    usable = cap_hours * (1.0 - CAP_RESERVE)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        while args:
            if spent >= usable:
                state = "stopped: the cap is reached"
                break
            if costs:
                mean = sum(costs) / len(costs)
                projected = spent + mean * len(args) / 3600.0
                if projected > usable:
                    state = f"stopped: the projection {projected:.2f} h passes the cap"
                    _log(out, spent, projected, len(args), state)
                    break
                room = max(1, int(math.floor((usable - spent) * 3600.0 / max(mean, 1e-6))))
                size = min(batch, room)
            else:
                size = probe_units
            if limit is not None:
                size = min(size, limit - dispatched)
                if size <= 0:
                    state = "stopped: the invocation limit"
                    break
            chunk, args = args[:size], args[size:]
            dispatched += len(chunk)
            results = list(pool.map(guarded, chunk))
            with records.open("a", encoding="utf-8") as fh:
                for rec in results:
                    fh.write(json.dumps(rec, sort_keys=True) + "\n")
            new = [float(r.get("cpu_seconds", 0.0)) for r in results]
            costs += new
            spent += sum(new) / 3600.0
            _log(
                out,
                spent,
                spent + (sum(costs) / len(costs)) * len(args) / 3600.0,
                len(args),
                "running",
            )
    if spent > cap_hours:
        state = "over the cap: the spent cost passed it"
    doc = {"state": state, "spent_hours": spent, "remaining": len(args), "cap_hours": cap_hours}
    (out / "state.json").write_text(json.dumps(doc, sort_keys=True) + "\n", "utf-8")
    print(json.dumps(doc), flush=True)
    return state


def read_state(out: Path) -> dict | None:
    path = out / "state.json"
    return json.loads(path.read_text("utf-8")) if path.exists() else None


def _log(out, spent, projected, remaining, state):
    line = {
        "spent_hours": spent,
        "projected_hours": projected,
        "remaining": remaining,
        "state": state,
    }
    with (out / "probe.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line) + "\n")
    print(json.dumps(line), flush=True)
