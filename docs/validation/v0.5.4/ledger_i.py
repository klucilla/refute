"""v0.5.4 Information checks: the budget ledger and the other caps (#217; the maintainer's decision
of 2026-11-12, 14:00, item 4). ``method_status: not_validated``.

Like stage B's ``ledger_b.py``, it imports v0.5.2's ``budgeted.py`` and ``driver.py`` unchanged and
points their module constants at a ledger of its own: one line, ``v054``, of 50 CPU-h, with nothing
spent before. The first half is a sub-line of 25 CPU-h: its parts are the ones named ``h1_*``.
``budgeted``'s stop rules apply unchanged. Import this module before any use of ``budgeted`` in a
v0.5.4 script.

**The other caps** (``caps.json``): review tokens and agent-days, counted as in stage B.

- **Review tokens:** each Codex conversation's last turn ``input_tokens - cached_input_tokens +
  output_tokens``, plus every independent review session. Caps: the first half 2.0 M, the phase
  3.5 M (an independent review of up to 0.35 M at the end apart). A STOP at 80 % of either.
- **Agent-days:** Claude's session transcripts since the phase opened, as wall clock over 8-hour
  days (an upper bound), with the active time also recorded. Caps: the first half 4, the phase 10.
- **Disk:** 5 GB for the phase, under ``.cache/v054/``."""

from __future__ import annotations

import hashlib
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

SECTION = "v054"
CAP_HOURS = 50.0
H1_CAP_HOURS = 25.0
CHARGES_ROOM = 0.1  # kept outside the line for the charges (smokes, summaries)
ALLOCATIONS = {  # declared before any dispatch; the second half stays unallocated until approved
    "h1_i1": 8.0,
    "h1_i4": 8.0,
    "h1_reserve": 8.9,  # 0.1 CPU-h of the first half left for its charges
    "h2_unallocated": 25.0,
}  # 49.9 allocated, the whole line: the charges must fit in CHARGES_ROOM
V052_LEDGER = V052 / "ledger.json"
CAPS = HERE / "caps.json"
CODEX_EVENTS = ROOT / ".cache/v054/codex"
AGENT_TIME = ROOT / ".cache/v052/tools/agent_time.py"
TRANSCRIPTS = Path.home() / ".claude/projects/C--Projetos-refute"
PHASE_START = "2026-11-12T17:00:00"  # 14:00 local time (UTC-3), the maintainer's decision
OVERSHOOT = 1.10  # the driver may pass a part's cap by up to 10 %
TOKEN_CAPS = {"h1": 2_000_000, "phase": 3_500_000}
FINAL_REVIEW_CAP = 350_000  # the phase's final independent review, an allowance of its own
DAY_CAPS = {"h1": 4.0, "phase": 10.0}
TOKEN_STOP = 0.80  # the maintainer: stop at 80 % of a cap
DISK_QUOTA = 5 * 10**9
DISK_ROOT = ROOT / ".cache/v054"

budgeted.LEDGER = HERE / "ledger.json"
budgeted.LINES = {SECTION: CAP_HOURS - CHARGES_ROOM}
budgeted.HARD_MAXIMUM = CAP_HOURS
budgeted.SPENT_BEFORE = 0.0


def _atomic_save(ledger: dict) -> None:
    """``budgeted.save``'s bytes, written atomically (a temporary file replaced); only while
    ``budgeted`` is bound to v0.5.4's ledger."""
    assert_bound()
    tmp = budgeted.LEDGER.with_name(budgeted.LEDGER.name + ".tmp")
    tmp.write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    tmp.replace(budgeted.LEDGER)


budgeted.save = _atomic_save


def assert_bound() -> None:
    """Stage B's modules bind the shared ``budgeted`` to stage B's ledger when imported; a v0.5.4
    script imports them first and this module last. Checked before every mutation (Codex's round
    1 of the first half's design)."""
    if (
        budgeted.LEDGER != HERE / "ledger.json"
        or budgeted.LINES != {SECTION: CAP_HOURS - CHARGES_ROOM}
        or budgeted.HARD_MAXIMUM != CAP_HOURS
        or budgeted.SPENT_BEFORE != 0.0
        or budgeted.save is not _atomic_save
    ):
        raise SystemExit("budgeted is not bound to v0.5.4's ledger: refused")


LOCK = ROOT / ".cache/v054/ledger.lock"
CAPS_LOCK = ROOT / ".cache/v054/caps.lock"
_held: dict[Path, int] = {}


class Exclusive:
    """The ledger's writers are serialized for their whole run (stage B's rule): a second process
    refuses (a STOP), it never waits or removes a lock it does not hold. Re-entrant in one
    process."""

    def __init__(self, step: str, path: Path = LOCK) -> None:
        self.step, self.path = step, path

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


def refuse_new_identity(part: str, fingerprint: str, shards) -> None:
    """A part that has run under another identity does not run again: a rerun needs the
    maintainer's recorded approval and a new part. A resume under the same identity is allowed."""
    r = _rows().get(part)
    if r is None:
        return
    now = budgeted._identity(fingerprint, shards, r["allocation_hours"])
    if r.get("identity") not in (None, now) or r.get("attempts"):
        raise SystemExit(f"{part}: a new identity or an archived attempt: a rerun is refused")


def _charges(prefix: str = "") -> float:
    charges = budgeted.load().get("charges", [])
    return sum(c["hours"] for c in charges if c["name"].startswith(prefix))


def declare() -> None:
    assert_bound()
    with Exclusive("declare"):
        _declare()


def _declare() -> None:
    """Declare the allocations. A part that has spent nothing takes the design's value; after a
    transfer, or once a part has spent, the persisted allocation rules. The allocations plus the
    charges stay within 50 CPU-h, and the first half's within 25."""
    merged = dict(ALLOCATIONS)
    transferred = bool(budgeted.load().get("transfers"))
    for p, r in _rows().items():
        if transferred or r.get("spent_hours", 0.0) > 0 or r.get("attempts"):
            merged[p] = r["allocation_hours"]
    if sum(merged.values()) + _charges() > CAP_HOURS + 1e-9:
        raise SystemExit("the allocations and charges pass the 50 CPU-h cap")
    if _charges() > CHARGES_ROOM + 1e-9:
        raise SystemExit("the charges pass their 0.1 CPU-h room: a STOP")
    h1 = sum(v for k, v in merged.items() if k.startswith("h1_")) + _charges("h1_")
    if h1 > H1_CAP_HOURS + 1e-9:
        raise SystemExit("the first half's allocations and charges pass its 25 CPU-h sub-cap")
    budgeted.declare(SECTION, merged)


def transfer(source: str, target: str, hours: float, reason: str) -> None:
    assert_bound()
    with Exclusive("transfer"):
        _transfer(source, target, hours, reason)


def _transfer(source: str, target: str, hours: float, reason: str) -> None:
    """A prospective transfer between parts, recorded before the target runs; the first half's
    parts trade only among themselves (its sub-cap)."""
    if source.startswith("h1_") != target.startswith("h1_"):
        raise SystemExit("a transfer across the first half's sub-cap is refused")
    rows = _rows()
    alloc = {p: r["allocation_hours"] for p, r in rows.items()}
    if alloc[source] - hours < rows.get(source, {}).get("spent_hours", 0.0):
        raise SystemExit(f"{source}: cannot give back hours it has spent")
    alloc[source] -= hours
    alloc[target] = alloc.get(target, 0.0) + hours
    budgeted.declare(SECTION, alloc)
    book = budgeted.load()
    book.setdefault("transfers", []).append(
        {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "from": source,
         "to": target, "hours": hours, "reason": reason}
    )  # fmt: skip
    budgeted.save(book)


def spent() -> float:
    return budgeted.spent(budgeted.load())


def h1_spent() -> float:
    """The first half's parts (their attempts included) and its charges."""
    book = budgeted.load()
    total = sum(c["hours"] for c in book.get("charges", []) if c["name"].startswith("h1_"))
    for p, r in _rows().items():
        if p.startswith("h1_"):
            total += r.get("spent_hours", 0.0)
            total += sum(a["spent_hours"] for a in r.get("attempts", []))
    return total


def charge(name: str, hours: float, basis: str) -> None:
    """``budgeted.charge``: consumption outside a part (a smoke, a summary), charged once by name;
    a STOP follows if the charges pass their room."""
    assert_bound()
    with Exclusive("charge"):
        budgeted.charge(name, hours, basis)
    if _charges() > CHARGES_ROOM + 1e-12:
        raise SystemExit("the charges passed their 0.1 CPU-h room: a STOP")


def hard_cap(part: str, workers: int, max_shard_seconds: float) -> float:
    """The part's strict cap: what is left of the 50 CPU-h (and, for a first-half part, of its
    25) minus one batch's in-flight reserve, over the driver's 10 % overshoot, and at most 1.5
    times the part's allocation less what the part consumed in every earlier attempt."""
    assert_bound()
    rows = _rows()
    if part not in rows:
        raise SystemExit(f"{part}: not declared")
    reserve = workers * max_shard_seconds / 3600.0
    left = CAP_HOURS - spent() - reserve
    if part.startswith("h1_"):
        left = min(left, H1_CAP_HOURS - h1_spent() - reserve)
    own = 1.5 * rows[part]["allocation_hours"] - part_consumption(part)
    cap = min(left, own) / OVERSHOOT
    if cap <= 0:
        raise SystemExit(f"{part}: no room under the caps: a STOP")
    return cap


def codex_tokens() -> dict:
    """Per Codex conversation (``<h1|h2>-<name>-r<round>-events.jsonl``), the last round's
    cumulative uncached input plus output; totals for the first half and the phase."""
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
    return {
        "conversations": per,
        "h1": sum(c for k, c in per.items() if k.startswith("h1")),
        "phase": sum(per.values()),
    }


def independent_review_tokens() -> int:
    """Ordinary independent review sessions, counted in their scope (the first half's while it
    runs, and the phase's)."""
    doc = json.loads(CAPS.read_text("utf-8"))
    return int(doc.get("independent_review_tokens", 0))


def final_review_tokens() -> int:
    """The phase's final independent review, against its own 0.35 M allowance."""
    doc = json.loads(CAPS.read_text("utf-8"))
    return int(doc.get("final_review_tokens", 0))


def agent_days() -> tuple[float, float]:
    """Claude's agent-days since the phase opened: (wall clock, active), by the transcripts."""
    out = subprocess.run(
        [sys.executable, str(AGENT_TIME), str(TRANSCRIPTS), PHASE_START],
        capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    wall = float(out.split("wall ")[1].split(" h")[0]) / 8.0
    active = float(out.split("= ")[1].split(" agent-days")[0])
    return wall, active


def disk_used() -> int:
    if not DISK_ROOT.exists():
        return 0
    return sum(f.stat().st_size for f in DISK_ROOT.rglob("*") if f.is_file())


def check_caps(
    step: str, reserve_days: float, reserve_tokens: int, in_h1: bool = True, reserve_bytes: int = 0
) -> dict:
    """Before a step: tokens (with the step's reservation) under 80 % of their caps, agent-days
    (with the reservation) under theirs, and the disk with the step's reserved output under 5 GB;
    recorded in ``caps.json``. With every argument 0 after a run, it checks the disk used."""
    with Exclusive("check_caps", CAPS_LOCK):
        return _check_caps(step, reserve_days, reserve_tokens, in_h1, reserve_bytes)


def _check_caps(
    step: str, reserve_days: float, reserve_tokens: int, in_h1: bool, reserve_bytes: int
) -> dict:
    doc = json.loads(CAPS.read_text("utf-8"))
    codex = codex_tokens()
    review = independent_review_tokens()
    final = final_review_tokens()
    wall, active = agent_days()
    disk = disk_used()
    tokens = {"h1": codex["h1"] + review, "phase": codex["phase"] + review}
    entry = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "step": step,
             "codex_tokens": codex, "independent_review_tokens": review,
             "final_review_tokens": final,
             "agent_days_wall": round(wall, 2), "agent_days_active": round(active, 2),
             "cpu_hours": {"phase": round(spent(), 3), "h1": round(h1_spent(), 3)},
             "disk_bytes": disk,
             "reserved": {"agent_days": reserve_days, "review_tokens": reserve_tokens,
                          "disk_bytes": reserve_bytes}}  # fmt: skip
    doc["entries"].append(entry)
    CAPS.write_text(json.dumps(doc, indent=1) + "\n", "utf-8", newline="\n")
    scopes = ("h1", "phase") if in_h1 else ("phase",)
    for scope in scopes:
        if tokens[scope] + reserve_tokens >= TOKEN_STOP * TOKEN_CAPS[scope]:
            raise SystemExit(f"{scope}: review tokens would reach 80 % of the cap: a STOP")
        if wall + reserve_days >= DAY_CAPS[scope]:
            raise SystemExit(f"{scope}: the agent-day cap (wall-clock bound) is reached: a STOP")
    if final >= TOKEN_STOP * FINAL_REVIEW_CAP:
        raise SystemExit("the final review's tokens reach 80 % of its allowance: a STOP")
    if disk + reserve_bytes >= DISK_QUOTA:
        raise SystemExit("the disk quota of 5 GB would be reached: a STOP")
    return entry


def v052_ledger_sha256() -> str:
    return hashlib.sha256(V052_LEDGER.read_bytes()).hexdigest()


if __name__ == "__main__":
    if sys.argv[1:] == ["declare"]:
        declare()
        print("declared; spent", round(spent(), 3), "CPU-h of", CAP_HOURS)
    elif sys.argv[1:2] == ["check"]:
        print(json.dumps(check_caps(sys.argv[2], float(sys.argv[3]), int(sys.argv[4])), indent=1))
    else:
        print(json.dumps(codex_tokens(), indent=1))
