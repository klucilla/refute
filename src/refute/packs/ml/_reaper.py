"""Supervisor of one subprocess run on Linux (refute.packs.ml.sandbox), run as its own
process: ``python -I _reaper.py <status.json> <workdir> <log> -- argv...``.

It declares itself a **child subreaper** (prctl PR_SET_CHILD_SUBREAPER), so every
descendant of the run that loses its parent is re-parented to it, and it waits for
every process that ends as its child. The CPU total is the sum of their wait4 rusage
(each includes the children that process waited for), and never less than the largest
live reading from /proc (the time of live descendants plus what was already waited).
**Known limit:** a descendant reaped automatically by a parent that ignores SIGCHLD
leaves no rusage anywhere; its time is lost, and several such children in sequence add
up, so the total can be below the real usage. The live reading is not a guaranteed
bound either (the /proc scan is not atomic). Exact accounting needs a cgroup, which is
the docker backend's job on the VM (W3.10). This backend runs synthetic repositories
only and is never used for the budget of a real paper.

When the first process ends, on SIGTERM (the runner's stop), or on any error of its
own, it kills every remaining descendant and waits for all of them before writing the
final status. A descendant is signalled through a pidfd opened on it and checked to
still descend from this supervisor, so a reused PID is never signalled.
"""

from __future__ import annotations

import ctypes
import json
import os
import signal
import subprocess
import sys
import time

PR_SET_CHILD_SUBREAPER = 36
POLL_S = 0.05
_stop = False


def _on_term(signum, frame) -> None:  # noqa: ARG001
    global _stop
    _stop = True


def _write(path: str, status: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(status, handle)
    os.replace(tmp, path)


def _stat(pid: int) -> tuple[int, int] | None:
    """(ppid, ticks of utime + stime + cutime + cstime) of ``pid``, or None. Read as
    bytes: a process name may hold any byte."""
    try:
        with open(f"/proc/{pid}/stat", "rb") as handle:
            stat = handle.read()
        fields = stat[stat.rindex(b")") + 2 :].split()
        return int(fields[1]), sum(int(fields[i]) for i in (11, 12, 13, 14))
    except (OSError, ValueError, IndexError):
        return None


def _proc_table() -> dict[int, tuple[int, int]]:
    table = {}
    for entry in os.listdir("/proc"):
        if entry.isdigit():
            row = _stat(int(entry))
            if row is not None:
                table[int(entry)] = row
    return table


def _descendants(table: dict[int, tuple[int, int]], root: int) -> list[int]:
    children: dict[int, list[int]] = {}
    for pid, (ppid, _) in table.items():
        children.setdefault(ppid, []).append(pid)
    out, todo = [], list(children.get(root, []))
    while todo:
        pid = todo.pop()
        out.append(pid)
        todo.extend(children.get(pid, []))
    return out


def _descends_from(pid: int, root: int) -> bool:
    """Whether ``pid`` is now a descendant of ``root``, by its parent links."""
    seen = set()
    while pid not in (0, 1) and pid not in seen:
        seen.add(pid)
        row = _stat(pid)
        if row is None:
            return False
        pid = row[0]
        if pid == root:
            return True
    return False


def _kill(pid: int, root: int) -> None:
    """SIGKILL ``pid`` through a pidfd, only if, once the pidfd is open, the process it
    refers to still descends from ``root`` (a reused PID is never signalled)."""
    try:
        fd = os.pidfd_open(pid)
    except OSError:
        return  # gone
    try:
        if _descends_from(pid, root):
            signal.pidfd_send_signal(fd, signal.SIGKILL)
    except OSError:
        pass
    finally:
        os.close(fd)


def _reap(reaped: list[int], first_pid: int, result: dict) -> int:
    """Waits for every child that ended; returns -1 when there is no child left."""
    while True:
        try:
            pid, wstatus, rusage = os.wait4(-1, os.WNOHANG)
        except ChildProcessError:
            return -1
        if pid == 0:
            return 0
        reaped[0] += int(round((rusage.ru_utime + rusage.ru_stime) * 1_000_000))
        if pid == first_pid:
            result["exit_code"] = os.waitstatus_to_exitcode(wstatus)


def main(argv: list[str]) -> int:
    status_path, workdir, log_path = argv[0], argv[1], argv[2]
    command = argv[4:] if argv[3] == "--" else []
    if not command:
        raise SystemExit("usage: _reaper.py status workdir log -- argv...")
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "prctl(PR_SET_CHILD_SUBREAPER) failed")
    signal.signal(signal.SIGTERM, _on_term)
    me = os.getpid()
    ticks = os.sysconf("SC_CLK_TCK")
    with open(log_path, "ab") as log:
        first = subprocess.Popen(
            command, cwd=workdir, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT
        )
    reaped = [0]
    result: dict = {"exit_code": None}
    floor = 0  # the largest live reading
    error = None
    killing = False
    try:
        while True:
            left = _reap(reaped, first.pid, result)
            table = _proc_table()
            alive = _descendants(table, me)
            live = reaped[0] + sum(table[p][1] for p in alive) * 1_000_000 // ticks
            floor = max(floor, live)
            if left == -1 and not alive:
                break
            if result["exit_code"] is not None or _stop:
                killing = True
            if killing:
                for pid in alive:
                    _kill(pid, me)
            _write(status_path, {"final": False, "usage_usec": floor})
            time.sleep(POLL_S)
    except BaseException as exc:  # noqa: BLE001 - every error still ends the run
        error = f"{type(exc).__name__}: {exc}"
    finally:
        # whatever happened, nothing of the run outlives the supervisor
        deadline = time.monotonic() + 30
        while True:
            alive = _descendants(_proc_table(), me)
            for pid in alive:
                _kill(pid, me)
            if _reap(reaped, first.pid, result) == -1 and not alive:
                break
            if time.monotonic() > deadline:
                error = (error or "") + f"; descendants still alive after 30 s: {alive}"
                break
            time.sleep(POLL_S)
    _write(
        status_path,
        {
            "final": True,
            "usage_usec": max(reaped[0], floor),
            "exit_code": result["exit_code"],
            "stopped": bool(_stop),
            "error": error,
        },
    )
    return 0 if error is None else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
