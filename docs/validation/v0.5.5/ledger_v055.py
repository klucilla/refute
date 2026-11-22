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
output_tokens`` (the events under ``.cache/v055/codex/``), as in every earlier phase; since
2026-11-21 (21:00, #218), summed over the conversation's threads when its rounds did not resume one
thread (``codex_tokens``).
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
# The projections (CPU-h) from the timed pilot of 2026-11-20 (pilot_costs.py; 4 binaries): the
# paired chain took 14 to 70 CPU-s per curve (mean 41.5) and the three oracle fits 1 to 20 CPU-s
# (mean 5.9). The projection uses the pilot's MAXIMA as unit costs (70 s and 20 s), the
# conservative side. T2a-E's uses step 6's measured 3.78 CPU-h for the 102 replays, plus 24
# placebo calls of E4 per injection.
PROJECTIONS = {
    "r1_d1p_a": (400 * 70 + 380 * 20) / 3600,  # 9.9: 400 curves; distances for ~380 eligible
    "r1_d1p_b": (400 * 70 + 380 * 20) / 3600,
    "r1_d1p_bridge": (200 * 70 + 190 * 20) / 3600,  # 4.9: set A's first 100 per family, C1 v1
    "r1_t2ae_1": 2.1,
    "r1_t2ae_2": 2.1,
}
CAP_MARGIN = 1.3  # the maintainer: each part's cap at least 1.3 times its projection
OVERSHOOT_FACTOR = 1.10  # the driver's tolerance; the part's cap is its allocation over it
ALLOCATIONS = {
    **{k: round(CAP_MARGIN * v * OVERSHOOT_FACTOR + 0.05, 1) for k, v in PROJECTIONS.items()},
    "r1_d2f_a": 0.0,  # D2-F does not run before its redesign is checked (a stop not delegated)
    "r1_d2f_b": 0.0,
}
# what the line leaves, kept for D2-F's redesign and the reserve; a transfer needs the maintainer
ALLOCATIONS["r1_reserve"] = round(LINE_HOURS - CHARGES_ROOM - sum(ALLOCATIONS.values()), 2)
# T3b's recount has no part: the decision-value test defers it to G1 (the designs, T3b)
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


def bind() -> None:
    """Point ``budgeted`` at v0.5.5's ledger (done on import; call it again after importing an
    earlier stage's module, which rebinds ``budgeted`` to its own ledger on import)."""
    budgeted.LEDGER = HERE / "ledger.json"
    budgeted.LINES = {SECTION: LINE_HOURS - CHARGES_ROOM}
    budgeted.HARD_MAXIMUM = LINE_HOURS
    budgeted.SPENT_BEFORE = 0.0
    budgeted.save = _atomic_save


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
_lines: dict[Path, bytes] = {}
_BINARY = getattr(os, "O_BINARY", 0)  # no newline translation on Windows
GUARD_TRIES = 20  # about 10 s of retries for the short guard; then a STOP


class _Guard:
    """Mutual exclusion of every acquisition, release and recovery of one lock (Codex, night
    round 1): an operating-system lock on ``<lock>.guard`` (a byte-range lock on Windows, flock
    elsewhere), held only for the few file operations, and released by the system if the process
    dies. The guard file is never removed."""

    def __init__(self, path: Path) -> None:
        self.path = path.with_name(path.name + ".guard")
        self.fd: int | None = None

    def __enter__(self) -> _Guard:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR | _BINARY)
        for _ in range(GUARD_TRIES):
            if _try_lock(fd):
                self.fd = fd
                return self
            time.sleep(0.5)
        os.close(fd)
        raise SystemExit(f"{self.path.name} could not be taken: refused")

    def __exit__(self, *exc) -> None:
        assert self.fd is not None
        _unlock(self.fd)
        os.close(self.fd)
        self.fd = None


def _try_lock(fd: int) -> bool:
    if sys.platform == "win32":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True
    import fcntl

    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _unlock(fd: int) -> None:
    if sys.platform == "win32":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_UN)


def _identity(path: Path) -> tuple[int, int, int, bytes]:
    """The lock file's instance: its file id, size, modification time and bytes."""
    st = os.stat(path)
    return st.st_ino, st.st_size, st.st_mtime_ns, path.read_bytes()


class Exclusive:
    """The ledger's writers are serialized for their whole run: a second process refuses (a
    STOP); it never waits for the run's lock. Re-entrant in one process. Creating, releasing and
    recovering the lock all happen under its guard (``_Guard``), so no two of them interleave; a
    lock left by a dead process is recovered only by ``release_stale``."""

    def __init__(self, step: str, path: Path | None = None) -> None:
        # the module's LOCK read at call time, so that a test's temporary lock is honoured
        self.step, self.path = step, (LOCK if path is None else path)

    def __enter__(self) -> Exclusive:
        if _held.get(self.path, 0) == 0:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with _Guard(self.path):
                if self.path.exists() and not release_stale(self.path, guarded=True):
                    held = self.path.read_text("utf-8", errors="replace").strip()
                    raise SystemExit(f"{self.path.name} is held ({held}): refused")
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | _BINARY)
                stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                line = f"pid {os.getpid()}; {self.step}; {stamp}\n".encode()
                os.write(fd, line)
                os.close(fd)
            _lines[self.path] = line
        _held[self.path] = _held.get(self.path, 0) + 1
        return self

    def __exit__(self, *exc) -> None:
        _held[self.path] -= 1
        if _held[self.path] == 0:
            with _Guard(self.path):
                # only this process's own instance is removed
                if self.path.read_bytes() != _lines.pop(self.path):
                    raise SystemExit(f"{self.path.name} is not this process's lock: kept; STOP")
                self.path.unlink()


STALE_LOG = ROOT / ".cache/v055/stale-locks.jsonl"


def _process_started_before(pid: int, stamp: str) -> bool | None:
    """Whether a process with ``pid`` exists and started no later than ``stamp`` (the lock's
    time): True, False (no such process, or one started after the lock, so a reused PID), or
    None if it cannot be told (then the lock is kept)."""
    import ctypes
    import datetime as _dt
    from ctypes import wintypes

    if sys.platform != "win32":
        return None
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    pft = ctypes.POINTER(wintypes.FILETIME)
    k32.GetProcessTimes.restype = wintypes.BOOL
    k32.GetProcessTimes.argtypes = [wintypes.HANDLE, pft, pft, pft, pft]
    k32.GetExitCodeProcess.restype = wintypes.BOOL
    k32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    k32.CloseHandle.restype = wintypes.BOOL
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return False if ctypes.get_last_error() == 87 else None  # 87: no such process
    try:
        times = [wintypes.FILETIME() for _ in range(4)]
        if not k32.GetProcessTimes(handle, *[ctypes.byref(t) for t in times]):
            return None
        code = wintypes.DWORD()
        if not k32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return None
        if code.value != 259:
            return False  # it has exited (259 is STILL_ACTIVE)
        ticks = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        created = _dt.datetime(1601, 1, 1, tzinfo=_dt.UTC) + _dt.timedelta(microseconds=ticks / 10)
        locked = _dt.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dt.UTC)
        return created <= locked + _dt.timedelta(seconds=1)
    finally:
        k32.CloseHandle(handle)


def release_stale(path: Path, guarded: bool = False) -> bool:
    """A lock left by a crash (the maintainer's decision of 2026-11-20, night, 4c). **The
    recovery removes only the instance of the lock whose identity was checked, under the mutual
    exclusion that creation and release also respect; any doubt keeps the lock** (Codex, night
    round 1). Under the guard, the lock's identity (file id, size, time, bytes) is read; the lock
    is removed only if the process recorded in it does not exist (or the PID now belongs to a
    process started after the lock) and its identity is unchanged just before the removal; the
    removal is recorded in ``STALE_LOG`` after it happened. Returns whether it was removed."""
    if not guarded:
        with _Guard(path):
            return release_stale(path, guarded=True)
    try:
        before = _identity(path)
    except FileNotFoundError:
        return False
    text = before[3].decode("utf-8", errors="replace").strip()
    m = re.fullmatch(r"pid (\d+); (.*); (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)", text)
    if not m or _process_started_before(int(m.group(1)), m.group(3)) is not False:
        return False
    try:
        if _identity(path) != before:
            return False
    except FileNotFoundError:
        return False
    path.unlink()
    STALE_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "lock": path.name,
             "held": text, "by": os.getpid(), "removed": True}  # fmt: skip
    with STALE_LOG.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")
    return True


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
    """Per Codex conversation (``<name>-r<round>-events.jsonl``), its uncached input plus output,
    and the phase's total.

    Rounds that resume one Codex thread (the same ``thread.started`` id, ``codex_affinity.ps1
    -Thread``) report cumulative usage, so a thread counts by its last round. Rounds run as new
    sessions each start a thread of their own, so a conversation counts by the **sum over its
    threads** (the maintainer's decision of 2026-11-21, 21:00, item 3, #218: the conversation
    "pause" ran its rounds as new sessions and its last round alone undercounted it; the figures
    already recorded keep their bytes, and the correction is
    ``docs/validation/v0.5.5/pause-tokens-correction.md``). In short: sum the last completed
    round's net usage for each distinct thread.

    The contract: a conversation of one counted round counts even without a thread id; in a
    conversation of several counted rounds, every counted round must name its thread; a file that
    names two different thread ids is refused. Rounds are ordered by their number (``r10`` after
    ``r2``)."""
    rounds: dict[str, list[tuple[int, str | None, int]]] = {}
    for path in sorted(CODEX_EVENTS.glob("*-events.jsonl")):
        m = re.fullmatch(r"(.+)-r(\d+)-events\.jsonl", path.name)
        if not m:
            continue
        usage, ids = None, set()
        for line in path.read_text("utf-8-sig", errors="replace").splitlines():
            line = line.strip().lstrip("﻿")
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") == "thread.started" and event.get("thread_id"):
                ids.add(event["thread_id"])
            if event.get("type") == "turn.completed" and "usage" in event:
                usage = event["usage"]
        if len(ids) > 1:
            raise SystemExit(f"{path.name}: conflicting thread ids; refused")
        if usage is None:
            continue
        count = usage["input_tokens"] - usage["cached_input_tokens"] + usage["output_tokens"]
        conv, rnd = m.group(1), int(m.group(2))
        rounds.setdefault(conv, []).append((rnd, next(iter(ids), None), count))
    per = {}
    for conv, items in rounds.items():
        if len(items) > 1 and any(thread is None for _, thread, _ in items):
            raise SystemExit(f"{conv}: a round of several has no thread id; refused")
        last: dict[str | None, tuple[int, int]] = {}
        for rnd, thread, count in items:
            if thread not in last or rnd > last[thread][0]:
                last[thread] = (rnd, count)
        per[conv] = sum(c for _, c in last.values())
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
