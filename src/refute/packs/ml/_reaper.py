"""Supervisor of one subprocess run on Linux (refute.packs.ml.sandbox), run as its own
process: ``python -I _reaper.py <status.json> <workdir> <log> -- argv...``.

It declares itself a **child subreaper** (prctl PR_SET_CHILD_SUBREAPER), so every
descendant of the run that loses its parent is re-parented to it, and it waits for
**every** process of the run. The total CPU time is then exact: each waited process
reports its own time and the time of the children it waited for (wait4 rusage), and
nothing escapes, wherever in the tree a process ends. While the run is alive the status
holds an estimate from /proc (live descendants plus what was already waited), used only
by the guards; the final status holds the exact total.

When the first process ends, or when the supervisor receives SIGTERM (the runner's
stop), it kills every remaining descendant, found by walking the parent links in /proc
from itself, waits for all of them and writes the final status. It only ever signals
its own descendants.
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


def _proc_table() -> dict[int, tuple[int, int]]:
    """pid -> (ppid, ticks of utime + stime + cutime + cstime), for every process."""
    table = {}
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/stat", encoding="ascii") as handle:
                stat = handle.read()
        except OSError:
            continue
        fields = stat[stat.rindex(")") + 2 :].split()
        table[int(entry)] = (int(fields[1]), sum(int(fields[i]) for i in (11, 12, 13, 14)))
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
    reaped_usec = 0
    exit_code = None
    killing = False
    while True:
        # wait for every process that ended: the run's own processes only (all of them
        # are this supervisor's descendants)
        while True:
            try:
                pid, wstatus, rusage = os.wait4(-1, os.WNOHANG)
            except ChildProcessError:
                pid = -1
                break
            if pid == 0:
                break
            reaped_usec += int(round((rusage.ru_utime + rusage.ru_stime) * 1_000_000))
            if pid == first.pid:
                exit_code = os.waitstatus_to_exitcode(wstatus)
                first.returncode = exit_code
        table = _proc_table()
        alive = _descendants(table, me)
        if pid == -1 and not alive:
            break  # nothing left of the run
        if not killing and (exit_code is not None or _stop):
            killing = True
        if killing:
            for victim in alive:
                try:
                    os.kill(victim, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        live_usec = sum(table[p][1] for p in alive if p in table) * 1_000_000 // ticks
        _write(status_path, {"final": False, "usage_usec": reaped_usec + live_usec})
        time.sleep(POLL_S)
    _write(
        status_path,
        {
            "final": True,
            "usage_usec": reaped_usec,
            "exit_code": exit_code,
            "stopped": bool(_stop),
        },
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
