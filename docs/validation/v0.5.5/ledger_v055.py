"""v0.5.5 Core resolution: the budget ledger and the other caps, up to the gate G1 (#218; the
maintainer's decision of 2026-11-20, 15:40, part 2). ``method_status: not_validated``.

Like v0.5.4's ``ledger_i.py``, it imports v0.5.2's ``budgeted.py`` unchanged and points its module
constants at a ledger of its own: one line, ``v055``, with nothing spent before. Import this module
LAST, after any earlier stage's module (they bind ``budgeted`` to their own ledgers on import).

**The caps up to G1** (the decision): 80 CPU-h; 3.0 M review tokens (this session's Codex; the
independent review counts apart); 9 agent-days; 5 GB of disk under ``.cache/v055/``. **At 80 % of
any cap, STOP.** So the CPU line given to ``budgeted`` is 80 % of 80 = 64 CPU-h, and every
allocation and charge fits inside it.

**Review tokens:** each Codex conversation's last turn ``input_tokens - cached_input_tokens +
output_tokens`` (the events under ``.cache/v055/codex/``), as in every earlier phase.
**Agent-days:** Claude's session transcripts since the phase opened, wall clock over 8-hour days
(an upper bound), with the active time also recorded (``.cache/v052/tools/agent_time.py``)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
V052 = ROOT / "docs/validation/v0.5.2/stage2"
for p in (str(ROOT / "src"), str(V052)):
    if p not in sys.path:
        sys.path.insert(0, p)

import budgeted  # noqa: E402

SECTION = "v055"
CAP_HOURS = 80.0
STOP_FRACTION = 0.80  # the maintainer: at 80 % of a cap, STOP
LINE_HOURS = STOP_FRACTION * CAP_HOURS  # 64 CPU-h: the line budgeted may spend
CHARGES_ROOM = 0.5  # kept inside the line for the charges (summaries)
# Declared before any dispatch (docs/plans/v0.5.5-r1-designs.md, "The prices"). They sum, with
# the charges' room, to the 64 CPU-h line.
ALLOCATIONS = {
    "r1_d1p_a": 16.0,
    "r1_d1p_b": 16.0,
    "r1_d2f_a": 11.0,
    "r1_d2f_b": 11.0,
    "r1_t2ae_1": 2.5,
    "r1_t2ae_2": 2.5,
    "r1_reserve": 4.5,  # never dispatched; a transfer from it needs the maintainer
}  # T3b's recount has no part: the decision-value test defers it to G1 (the designs, T3b)
CAPS = HERE / "caps.json"
CODEX_EVENTS = ROOT / ".cache/v055/codex"
AGENT_TIME = ROOT / ".cache/v052/tools/agent_time.py"
TRANSCRIPTS = Path.home() / ".claude/projects/C--Projetos-refute"
PHASE_START = "2026-11-20T18:40:00"  # 15:40 local time (UTC-3), the maintainer's decision
OVERSHOOT = 1.10  # the driver may pass a part's cap by up to 10 %
TOKEN_CAP = 3_000_000
DAY_CAP = 9.0
DISK_QUOTA = 5 * 10**9
DISK_ROOT = ROOT / ".cache/v055"

budgeted.LEDGER = HERE / "ledger.json"
budgeted.LINES = {SECTION: LINE_HOURS - CHARGES_ROOM}
budgeted.HARD_MAXIMUM = LINE_HOURS
budgeted.SPENT_BEFORE = 0.0


def _atomic_save(ledger: dict) -> None:
    """``budgeted.save``'s bytes, written atomically; only while bound to v0.5.5's ledger."""
    assert_bound()
    tmp = budgeted.LEDGER.with_name(budgeted.LEDGER.name + ".tmp")
    tmp.write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    tmp.replace(budgeted.LEDGER)


budgeted.save = _atomic_save


def assert_bound() -> None:
    """Checked before every mutation: an earlier stage's module imported after this one would
    rebind ``budgeted`` to its own ledger."""
    if (
        budgeted.LEDGER != HERE / "ledger.json"
        or budgeted.LINES != {SECTION: LINE_HOURS - CHARGES_ROOM}
        or budgeted.HARD_MAXIMUM != LINE_HOURS
        or budgeted.SPENT_BEFORE != 0.0
        or budgeted.save is not _atomic_save
    ):
        raise SystemExit("budgeted is not bound to v0.5.5's ledger: refused")


LOCK = ROOT / ".cache/v055/ledger.lock"
CAPS_LOCK = ROOT / ".cache/v055/caps.lock"
_held: dict[Path, int] = {}


class Exclusive:
    """The ledger's writers are serialized for their whole run: a second process refuses (a
    STOP); it never waits or removes a lock it does not hold. Re-entrant in one process."""

    def __init__(self, step: str, path: Path | None = None) -> None:
        # the module's LOCK read at call time, so that a test's temporary lock is honoured
        self.step, self.path = step, (LOCK if path is None else path)

    def __enter__(self) -> Exclusive:
        if _held.get(self.path, 0) == 0:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                held = self.path.read_text("utf-8", errors="replace").strip()
                raise SystemExit(f"{self.path.name} is held ({held}): refused") from None
            stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            os.write(fd, f"pid {os.getpid()}; {self.step}; {stamp}\n".encode())
            os.close(fd)
        _held[self.path] = _held.get(self.path, 0) + 1
        return self

    def __exit__(self, *exc) -> None:
        _held[self.path] -= 1
        if _held[self.path] == 0:
            self.path.unlink()


def _rows() -> dict:
    return budgeted.load().get("sections", {}).get(SECTION, {}).get("parts", {})


def part_consumption(part: str) -> float:
    """A part's consumption over every attempt."""
    r = _rows().get(part, {})
    return r.get("spent_hours", 0.0) + sum(a["spent_hours"] for a in r.get("attempts", []))


MAX_RESUMES = 1  # the charter, process change 4: one pre-approved resume, same code and rows


def _starts(book: dict, part: str) -> list:
    return book.get("starts", {}).get(part, [])


def check_run(part: str, fingerprint: str, shards) -> int:
    """Read only, under the caller's lock: refuses a part that ran under another identity or has
    an archived attempt (a rerun needs the maintainer's recorded approval and a new part), and a
    run beyond the one pre-approved resume. **Every earlier start of the part counts**, recorded
    persistently in the ledger (``starts``) whether or not it spent anything, so an interruption
    before any consumption is still a start (Codex, r0r1 round 2). Returns the number of earlier
    starts (0 for a first run, 1 for the resume)."""
    assert_bound()
    book = budgeted.load()
    r = book.get("sections", {}).get(SECTION, {}).get("parts", {}).get(part)
    if r is None:
        raise SystemExit(f"{part}: not declared")
    now = budgeted._identity(fingerprint, shards, r["allocation_hours"])
    if r.get("identity") not in (None, now) or r.get("attempts"):
        raise SystemExit(f"{part}: a new identity or an archived attempt: a rerun is refused")
    earlier = _starts(book, part)
    if any(s["identity"] != now for s in earlier):
        raise SystemExit(f"{part}: an earlier start under another identity: a rerun is refused")
    if len(earlier) > MAX_RESUMES:
        raise SystemExit(f"{part}: the one pre-approved resume was used: the maintainer's")
    return len(earlier)


def guarded_run(
    part: str,
    fingerprint: str,
    shards,
    step: str,
    reserve_days: float,
    reserve_bytes: int,
    workers: int,
    max_shard_seconds: float,
    launch,
) -> str:
    """One lock (the ledger's) around the whole run (Codex, r0r1 round 2): the declaration, the
    identity and resume checks, the caps, the part's cap, the start's record (only after every
    precondition passed) and the driver's run, ``launch(cap)``. Returns the driver's state."""
    assert_bound()
    with Exclusive(step):
        declare()
        check_run(part, fingerprint, shards)
        check_caps(step, reserve_days, 300_000, reserve_bytes)
        cap = hard_cap(part, workers, max_shard_seconds)
        earlier = record_start(part, fingerprint, shards)
        kind = "the pre-approved resume" if earlier else "a first run"
        print(f"{part}: {len(shards)} shards; {workers} workers; cap {cap:.2f} CPU-h; {kind}",
              flush=True)  # fmt: skip
        return launch(cap)


def record_start(part: str, fingerprint: str, shards) -> int:
    """Under the caller's lock, after every precondition passed (the caps, the cap): the checks
    of ``check_run`` again, then this start recorded before the driver runs. Returns the number
    of earlier starts."""
    earlier = check_run(part, fingerprint, shards)
    book = budgeted.load()
    r = book["sections"][SECTION]["parts"][part]
    book.setdefault("starts", {}).setdefault(part, []).append(
        {
            "identity": budgeted._identity(fingerprint, shards, r["allocation_hours"]),
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "resume": earlier > 0,
        }
    )
    budgeted.save(book)
    return earlier


def _charges() -> float:
    return sum(c["hours"] for c in budgeted.load().get("charges", []))


def declare() -> None:
    assert_bound()
    with Exclusive("declare"):
        merged = dict(ALLOCATIONS)
        for p, r in _rows().items():
            if r.get("spent_hours", 0.0) > 0 or r.get("attempts"):
                merged[p] = r["allocation_hours"]
        if sum(merged.values()) + max(_charges(), CHARGES_ROOM) > LINE_HOURS + 1e-9:
            raise SystemExit("the allocations and the charges' room pass the 64 CPU-h line")
        budgeted.declare(SECTION, merged)


def spent() -> float:
    return budgeted.spent(budgeted.load())


def charge(name: str, hours: float, basis: str) -> None:
    """Consumption outside a part (a summary), charged once by name; a STOP follows if the
    charges pass their room."""
    assert_bound()
    with Exclusive("charge"):
        budgeted.charge(name, hours, basis)
    if _charges() > CHARGES_ROOM + 1e-12:
        raise SystemExit("the charges passed their room: a STOP")


def charges_left() -> float:
    return CHARGES_ROOM - _charges()


def hard_cap(part: str, workers: int, max_shard_seconds: float) -> float:
    """The part's strict cap, **cumulative** over its current identity (the driver compares it
    with the identity's whole consumption, earlier runs and the resume included; Codex, r0r1
    round 1): at most the part's allocation less what archived attempts consumed (a fixed cap:
    the charter, process change 4), and at most what the 64 CPU-h line leaves once every other
    consumption and one batch's in-flight reserve are counted; over the driver's 10 %
    overshoot."""
    assert_bound()
    rows = _rows()
    if part not in rows:
        raise SystemExit(f"{part}: not declared")
    row = rows[part]
    current = row.get("spent_hours", 0.0)
    archived = sum(a["spent_hours"] for a in row.get("attempts", []))
    reserve = workers * max_shard_seconds / 3600.0
    left = LINE_HOURS - CHARGES_ROOM - (spent() - current) - reserve
    own = row["allocation_hours"] - archived
    cap = min(left, own) / OVERSHOOT
    if cap <= 0:
        raise SystemExit(f"{part}: no room under the caps: a STOP")
    return cap


def codex_tokens() -> dict:
    """Per Codex conversation (``<name>-r<round>-events.jsonl``), the last round's cumulative
    uncached input plus output, and the phase's total."""
    last: dict[str, tuple[int, int]] = {}
    for path in sorted(CODEX_EVENTS.glob("*-events.jsonl")):
        m = re.fullmatch(r"(.+)-r(\d+)-events\.jsonl", path.name)
        if not m:
            continue
        usage = None
        for line in path.read_text("utf-8-sig", errors="replace").splitlines():
            line = line.strip().lstrip("﻿")
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") == "turn.completed" and "usage" in event:
                usage = event["usage"]
        if usage is None:
            continue
        count = usage["input_tokens"] - usage["cached_input_tokens"] + usage["output_tokens"]
        conv, rnd = m.group(1), int(m.group(2))
        if conv not in last or rnd > last[conv][0]:
            last[conv] = (rnd, count)
    per = {conv: c for conv, (_, c) in last.items()}
    return {"conversations": per, "phase": sum(per.values())}


def agent_days() -> tuple[float, float]:
    """Claude's agent-days since the phase opened: (wall clock, active), by the transcripts."""
    out = subprocess.run(
        [sys.executable, str(AGENT_TIME), str(TRANSCRIPTS), PHASE_START],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    wall = float(out.split("wall ")[1].split(" h")[0]) / 8.0
    active = float(out.split("= ")[1].split(" agent-days")[0])
    return wall, active


def disk_used() -> int:
    if not DISK_ROOT.exists():
        return 0
    return sum(f.stat().st_size for f in DISK_ROOT.rglob("*") if f.is_file())


def check_caps(step: str, reserve_days: float, reserve_tokens: int, reserve_bytes: int = 0) -> dict:
    """Before a step: tokens, agent-days, CPU and disk (each with the step's reservation) under
    80 % of their caps; recorded in ``caps.json``."""
    with Exclusive("check_caps", CAPS_LOCK):
        doc = json.loads(CAPS.read_text("utf-8"))
        codex = codex_tokens()
        wall, active = agent_days()
        disk = disk_used()
        cpu = spent()
        entry = {
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "step": step,
            "codex_tokens": codex,
            "agent_days_wall": round(wall, 2),
            "agent_days_active": round(active, 2),
            "cpu_hours": round(cpu, 3),
            "disk_bytes": disk,
            "reserved": {
                "agent_days": reserve_days,
                "review_tokens": reserve_tokens,
                "disk_bytes": reserve_bytes,
            },
        }
        doc["entries"].append(entry)
        CAPS.write_text(json.dumps(doc, indent=1) + "\n", "utf-8", newline="\n")
    if codex["phase"] + reserve_tokens >= STOP_FRACTION * TOKEN_CAP:
        raise SystemExit("review tokens would reach 80 % of the cap: a STOP")
    if wall + reserve_days >= STOP_FRACTION * DAY_CAP:
        raise SystemExit("agent-days (wall-clock bound) would reach 80 % of the cap: a STOP")
    if cpu >= LINE_HOURS - 1e-9:
        raise SystemExit("CPU reached 80 % of the cap: a STOP")
    if disk + reserve_bytes >= STOP_FRACTION * DISK_QUOTA:
        raise SystemExit("the disk would reach 80 % of 5 GB: a STOP")
    return entry


if __name__ == "__main__":
    if sys.argv[1:] == ["declare"]:
        declare()
        print("declared; spent", round(spent(), 3), "CPU-h of the", LINE_HOURS, "line")
    elif sys.argv[1:2] == ["check"]:
        print(json.dumps(check_caps(sys.argv[2], float(sys.argv[3]), int(sys.argv[4])), indent=1))
    else:
        print(json.dumps(codex_tokens(), indent=1))
