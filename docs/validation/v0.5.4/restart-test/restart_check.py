"""Check the restart probe (#217) against the criteria fixed before its launch (``criteria.json``).
Reads only, except ``--save <label>``, which writes ``<label>.json`` (the report) in the probe's
folder. Labels: ``pre`` (before the restart), ``post`` (after it), ``final`` (after the probe's end;
the decision). The final decision passes only if every item holds; any 'unknown' fails it.

Process states come from ``restart_probe.status``: alive only when the PID opens with the recorded
creation time and a zero-timeout wait on its handle times out (not merely queryable).

Usage: .venv/Scripts/python.exe .cache/v054/tools/restart_check.py <dir> [--save pre|post|final]
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import restart_probe  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
EPOCH = dt.datetime(1601, 1, 1, tzinfo=dt.UTC)


def filetime(value: int) -> dt.datetime:
    return EPOCH + dt.timedelta(microseconds=value / 10)


def load(path: Path):
    return json.loads(path.read_text("utf-8")) if path.exists() else None


def main() -> None:
    folder = (ROOT / sys.argv[1]).resolve()
    label = sys.argv[sys.argv.index("--save") + 1] if "--save" in sys.argv else None
    k32 = restart_probe._k32()
    crit = load(folder / "criteria.json")
    launch = load(folder / "launch.pid.json")
    ident = load(folder / "identity.json")
    beats = [json.loads(x) for x in (folder / "heartbeat.jsonl").read_text("utf-8").splitlines()]
    final_line = beats[-1] if beats and beats[-1].get("final") else None
    live = [b for b in beats if "final" not in b]
    utcs = [dt.datetime.fromisoformat(b["utc"]) for b in beats]
    gaps = [(b - a).total_seconds() for a, b in zip(utcs, utcs[1:], strict=False)]
    monos = [b["mono"] for b in live]
    mono_gaps = [b - a for a, b in zip(monos, monos[1:], strict=False)]
    states = [s for b in live for s in b["watch"].values()]
    gone = {}
    for b in live:
        for pid, s in b["watch"].items():
            if s == "ended" and pid not in gone:
                gone[pid] = b["utc"]
    started = dt.datetime.fromisoformat(ident["started_utc"])
    report = {
        "label": label,
        "checked_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "launcher": restart_probe.status(k32, launch["pid"], launch["created"]),
        "interpreter": restart_probe.status(k32, ident["pid"], ident["created"]),
        "interpreter_parent_is_launcher": ident["ppid"] == launch["pid"]
        and ident["parent_created"] == launch["created"],
        "criteria_before_launch": crit is not None
        and dt.datetime.fromisoformat(crit["written_utc"]) < started,
        "affinity_ok": int(ident["affinity_mask"], 16) == int(crit["affinity_mask"], 16),
        "priority_ok": int(ident["priority_class"], 16) == int(crit["priority_class"], 16),
        "beats": len(beats),
        "sequence_without_gap": [b["seq"] for b in beats] == list(range(len(beats))),
        "first_utc": beats[0]["utc"],
        "last_utc": beats[-1]["utc"],
        "largest_interval_utc_s": round(max(gaps), 3) if gaps else None,
        "largest_interval_mono_s": round(max(mono_gaps), 3) if mono_gaps else None,
        "intervals_ok": bool(gaps)
        and all(0 < g <= crit["max_interval_s"] for g in gaps)
        and all(0 < g <= crit["max_interval_s"] for g in mono_gaps),
        "watched_alive_at_first_beat": bool(live)
        and all(s == "alive" for s in live[0]["watch"].values()),
        "watched_states_seen": sorted(set(states)),
        "watched_gone_first_seen_utc": gone,
        "final_line": final_line is not None,
        "stderr_bytes": (folder / "launch.err.txt").stat().st_size,
    }
    if label == "final":
        pre, post = load(folder / "pre.json"), load(folder / "post.json")
        after = load(folder / "after_restart.json") or {"pids": {}}
        exit_utc = min((dt.datetime.fromisoformat(t) for t in gone.values()), default=None)
        new = [filetime(c) for c in after["pids"].values()]
        duration = (utcs[-1] - utcs[0]).total_seconds()
        expected = crit["minutes"] * 60.0
        report["new_app_created_utc"] = [t.isoformat(timespec="seconds") for t in new]
        report["duration_s"] = round(duration, 1)
        checks = {
            "pre_both_alive": bool(pre)
            and pre["launcher"] == "alive"
            and pre["interpreter"] == "alive",
            "post_both_alive": bool(post)
            and post["launcher"] == "alive"
            and post["interpreter"] == "alive",
            "app_exit_seen_in_window": exit_utc is not None,
            "new_app_created_in_window": exit_utc is not None
            and any(exit_utc <= t <= utcs[-1] for t in new),
            "pre_before_exit_and_post_after_reopen": bool(pre and post and exit_utc and new)
            and dt.datetime.fromisoformat(pre["checked_utc"]) < exit_utc
            and dt.datetime.fromisoformat(post["checked_utc"]) > max(new),
            "duration_ok": expected - 2 * crit["every_seconds"] <= duration <= expected + 60.0,
            "no_unknown_state": not any(s.startswith("unknown") for s in states),
            "both_ended_now": report["launcher"] == "ended" and report["interpreter"] == "ended",
        }
        for key in (
            "interpreter_parent_is_launcher",
            "criteria_before_launch",
            "affinity_ok",
            "priority_ok",
            "sequence_without_gap",
            "intervals_ok",
            "watched_alive_at_first_beat",
            "final_line",
        ):
            checks[key] = bool(report[key])
        report["checks"] = checks
        report["survived_the_restart"] = all(checks.values())
    text = json.dumps(report, indent=1, sort_keys=True)
    if label:
        path = folder / f"{label}.json"
        if path.exists():
            raise SystemExit(f"{path.name} exists: never overwritten")
        path.write_text(text + "\n", "utf-8")
    print(text)


if __name__ == "__main__":
    main()
