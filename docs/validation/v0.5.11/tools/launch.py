"""The metered launcher of v0.5.11 (charter sections 5 and 6; rules (b) to (e); Codex's blocking
item 3 of the round on the charter). Every local unit of the phase runs through it.

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.11/tools/launch.py <unit spec> [--label L]
        [--approval URL] [-- extra arguments]

A **unit spec** is a committed JSON file under ``docs/validation/v0.5.11/units/``:

    {"name": ..., "question": ..., "choices": ...,
     "argv": [...],                 # "{python}" is the project's .venv Python
     "identity": [paths],           # scripts and rule files: committed, unchanged, hashed
     "reserve": {"cpu_s": ..., "transfer_bytes": ..., "disk_bytes": ...},
     "network": false | true,
     "disk_extra": [".cache/lock-compat", "uv-cache"],   # optional, growth counted
     "outputs": [paths]}            # optional, hashed after the run

**Before dispatch** the launcher:
- checks that the spec and every ``identity`` file are tracked and that the working bytes equal
  the ``HEAD`` blob (LF), and records the SHA-256 of each blob;
- computes the instance key, the SHA-256 of the spec blob, the extra arguments and the ``HEAD``
  tree. A key already started is a repetition, refused unless ``--approval`` names the issue
  comment that approved it (rule (d));
- marks an earlier ``before`` entry with no ``after`` as ``abandoned``;
- reserves the unit's allowance against the phase's ceilings, from the journal's totals, and
  refuses if the rest would not cover it;
- appends a ``before`` entry to ``docs/validation/v0.5.11/log.jsonl``: the question, the
  choices, the command, the hashes, the reservation and a machine timestamp.

**During the run** the unit runs in a Job object:
- on processors 8 to 31, at BelowNormal priority, killed with the job;
- with a user-time limit equal to its CPU reservation.

Every second the launcher reads the job's CPU (user and kernel). Every 10 seconds it reads:
- the machine's received and sent bytes (``netstat -e``), an upper bound of the unit's transfer
  that counts every program;
- the disk footprint: ``.cache/v0511`` plus the growth of each ``disk_extra`` path. ``uv-cache``
  stands for uv's cache folder, outside the project, whose path is never written.

It stops the unit before it can exceed any reservation, and records the interruption.

**After the run** it appends an ``after`` entry (the exit code, the CPU, the wall time, the
transfer bound, the peak disk, the interruption and the output hashes) and rewrites
``docs/validation/v0.5.11/caps-ledger.json`` from the journal.

**What is outside the meter:** GitHub CI, the Codex and Claude review processes, and the agent's
own reads and inspection commands (git status, log and diff; reading files; GitHub comments). The
ledger names them.

Standard library only; Windows only.
"""

# ruff: noqa: N801  (the structures keep their Win32 names)
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PHASE = ROOT / "docs" / "validation" / "v0.5.11"
LOG = PHASE / "log.jsonl"
LEDGER = PHASE / "caps-ledger.json"
WORK = ROOT / ".cache" / "v0511"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
CAPS = {"cpu_s": 36000.0, "transfer_bytes": 5_000_000_000, "disk_bytes": 10_000_000_000}
AFFINITY_MASK = 0xFFFFFF00  # processors 8 to 31
CPU_MARGIN_S = 30.0  # stop this much before the CPU reservation (one poll at 24 processors)
OUTSIDE_METER = [
    "GitHub CI (remote)",
    "the Codex review processes (reported apart, with their tokens)",
    "the Claude gate (reported apart)",
    "the agent's reads and inspection commands: git status, log, diff and show; file reads; "
    "GitHub comments",
]

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
ntdll = ctypes.WinDLL("ntdll")
_H, _D, _V = wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p
kernel32.CreateJobObjectW.restype = _H
kernel32.CreateJobObjectW.argtypes = [_V, ctypes.c_wchar_p]
kernel32.SetInformationJobObject.argtypes = [_H, ctypes.c_int, _V, _D]
kernel32.AssignProcessToJobObject.argtypes = [_H, _H]
kernel32.QueryInformationJobObject.argtypes = [_H, ctypes.c_int, _V, _D, _V]
kernel32.TerminateJobObject.argtypes = [_H, wintypes.UINT]
kernel32.CloseHandle.argtypes = [_H]
ntdll.NtResumeProcess.argtypes = [_H]

CREATE_SUSPENDED = 0x00000004
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
JOB_OBJECT_LIMIT_JOB_TIME = 0x00000004
JOB_OBJECT_LIMIT_AFFINITY = 0x00000010
JOB_OBJECT_LIMIT_PRIORITY_CLASS = 0x00000020
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JobObjectBasicAccountingInformation = 1
JobObjectExtendedLimitInformation = 9


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [(n, ctypes.c_ulonglong) for n in ("r", "w", "o", "rb", "wb", "ob")]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("TotalUserTime", ctypes.c_longlong),
        ("TotalKernelTime", ctypes.c_longlong),
        ("ThisPeriodTotalUserTime", ctypes.c_longlong),
        ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
        ("TotalPageFaultCount", wintypes.DWORD),
        ("TotalProcesses", wintypes.DWORD),
        ("ActiveProcesses", wintypes.DWORD),
        ("TotalTerminatedProcesses", wintypes.DWORD),
    ]


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def committed_sha256(rel: str) -> str:
    """SHA-256 of the HEAD blob of a tracked file whose working bytes equal that blob."""
    rel = Path(rel).as_posix()
    try:
        blob = git("show", f"HEAD:{rel}")
    except subprocess.CalledProcessError:
        raise SystemExit(f"refused: {rel} is not committed") from None
    if (ROOT / rel).read_bytes() != blob:
        raise SystemExit(f"refused: {rel} differs from its committed blob")
    digest = hashlib.sha256(blob).hexdigest()
    if digest == hashlib.sha256(b"").hexdigest():
        raise SystemExit(f"refused: {rel} is empty")
    return digest


JOURNAL_FILES = ("docs/validation/v0.5.11/log.jsonl", "docs/validation/v0.5.11/caps-ledger.json")


def tree_state() -> str:
    """SHA-256 of the code's state: the HEAD tree, the staged and unstaged differences, and the
    untracked files with their contents, leaving out the journal and the ledger."""
    excl = [f":(exclude){p}" for p in JOURNAL_FILES]
    h = hashlib.sha256()
    h.update(git("diff", "--binary", "HEAD", "--", ".", *excl))
    for line in git("ls-tree", "-r", "HEAD").splitlines():
        if line.split(b"\t", 1)[-1].decode() not in JOURNAL_FILES:
            h.update(line + b"\n")
    names = git("ls-files", "--others", "--exclude-standard", "-z", "--", ".", *excl)
    for name in sorted(x for x in names.split(b"\0") if x):
        h.update(name + b"\0" + hashlib.sha256((ROOT / name.decode()).read_bytes()).digest())
    return h.hexdigest()


def read_log() -> list[dict]:
    if not LOG.exists():
        return []
    return [json.loads(x) for x in LOG.read_text(encoding="utf-8").splitlines() if x.strip()]


def append_log(entry: dict) -> None:
    PHASE.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def net_bytes() -> int:
    out = subprocess.run(["netstat", "-e"], capture_output=True, text=True, errors="replace")
    for line in out.stdout.splitlines():
        parts = line.split()
        if parts and parts[0] == "Bytes" and len(parts) >= 3:
            return int(parts[1]) + int(parts[2])
    raise RuntimeError("netstat -e gave no Bytes line")


def uv_cache_dir() -> Path:
    out = subprocess.run(["uv", "cache", "dir"], capture_output=True, text=True, check=True)
    return Path(out.stdout.strip())


def tree_bytes(p: Path) -> int:
    if not p.exists():
        return 0
    total = 0
    stack = [p]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for e in it:
                    try:
                        if e.is_symlink():
                            continue
                        if e.is_dir(follow_symlinks=False):
                            stack.append(Path(e.path))
                        elif e.is_file(follow_symlinks=False):
                            total += e.stat(follow_symlinks=False).st_size
                    except OSError:
                        continue
        except OSError:
            continue
    return total


def resolve_extra(name: str) -> Path:
    """A path whose growth during the unit counts as the phase's disk. Two names stand for
    folders outside the project, whose paths are never written: "uv-cache" (uv's cache) and
    "pytest-temp" (pytest's base temporary folder for this user)."""
    if name == "uv-cache":
        return uv_cache_dir()
    if name == "pytest-temp":
        import getpass
        import tempfile

        return Path(tempfile.gettempdir()) / f"pytest-of-{getpass.getuser()}"
    p = (ROOT / name).resolve()
    if ROOT not in p.parents:
        raise SystemExit(f"refused: disk_extra {name} is outside the project")
    return p


def totals(entries: list[dict]) -> dict:
    cpu = sum(e.get("cpu_s", 0.0) for e in entries if e["event"] == "after")
    tr = sum(e.get("transfer_bytes_upper", 0) for e in entries if e["event"] == "after")
    peak = max([e.get("disk_peak_bytes", 0) for e in entries if e["event"] == "after"] or [0])
    return {"cpu_s": round(cpu, 3), "transfer_bytes": tr, "disk_peak_bytes": peak}


def write_ledger(entries: list[dict]) -> None:
    befores = {e["instance_key"]: e for e in entries if e["event"] == "before"}
    afters = {e["instance_key"]: e for e in entries if e["event"] == "after"}
    abandoned = {e["instance_key"] for e in entries if e["event"] == "abandoned"}
    rows = []
    complete = True
    for key, b in befores.items():
        a = afters.get(key)
        row = {"unit": b["unit"], "label": b.get("label"), "instance_key": key, "start": b["utc"]}
        if a is None:
            row["status"] = "abandoned" if key in abandoned else "running or no after entry"
            complete = False
        else:
            row.update(
                {
                    "status": a["status"],
                    "cpu_s": a["cpu_s"],
                    "transfer_bytes_upper": a["transfer_bytes_upper"],
                    "disk_peak_bytes": a["disk_peak_bytes"],
                    "telemetry_complete": a["telemetry_complete"],
                }
            )
            complete = complete and a["telemetry_complete"]
        rows.append(row)
    t = totals(entries)
    within = (
        t["cpu_s"] <= CAPS["cpu_s"]
        and t["transfer_bytes"] <= CAPS["transfer_bytes"]
        and t["disk_peak_bytes"] <= CAPS["disk_bytes"]
    )
    doc = {
        "phase": "v0.5.11",
        "labels": ["exploratory", "method_status: not_validated"],
        "caps": CAPS,
        "used": t,
        "within_caps": (within if complete else "not demonstrated"),
        "telemetry_complete": complete,
        "transfer_note": "an upper bound: the machine's netstat -e bytes during each unit",
        "outside_meter": OUTSIDE_METER,
        "rows": rows,
    }
    LEDGER.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")


def make_job(cpu_limit_s: float):
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise OSError(ctypes.get_last_error(), "CreateJobObjectW")
    lim = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    b = lim.BasicLimitInformation
    b.LimitFlags = (
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        | JOB_OBJECT_LIMIT_AFFINITY
        | JOB_OBJECT_LIMIT_PRIORITY_CLASS
        | JOB_OBJECT_LIMIT_JOB_TIME
    )
    b.Affinity = AFFINITY_MASK
    b.PriorityClass = BELOW_NORMAL_PRIORITY_CLASS
    b.PerJobUserTimeLimit = int(cpu_limit_s * 1e7)
    ok = kernel32.SetInformationJobObject(
        job, JobObjectExtendedLimitInformation, ctypes.addressof(lim), ctypes.sizeof(lim)
    )
    if not ok:
        raise OSError(ctypes.get_last_error(), "SetInformationJobObject")
    return job


def job_cpu(job) -> tuple[float, int, int]:
    a = JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
    kernel32.QueryInformationJobObject(
        job, JobObjectBasicAccountingInformation, ctypes.addressof(a), ctypes.sizeof(a), None
    )
    return (a.TotalUserTime + a.TotalKernelTime) / 1e7, a.TotalProcesses, a.ActiveProcesses


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--label", default=None)
    ap.add_argument("--approval", default=None)
    ap.add_argument("extra", nargs="*")
    a = ap.parse_args()

    me = ctypes.windll.kernel32.GetCurrentProcess()
    ctypes.windll.kernel32.SetProcessAffinityMask(me, AFFINITY_MASK)
    ctypes.windll.kernel32.SetPriorityClass(me, BELOW_NORMAL_PRIORITY_CLASS)

    spec_rel = Path(a.spec).as_posix()
    spec_sha = committed_sha256(spec_rel)
    spec = json.loads((ROOT / spec_rel).read_text(encoding="utf-8"))
    me_rel = Path(__file__).resolve().relative_to(ROOT).as_posix()
    identity = {me_rel: committed_sha256(me_rel), spec_rel: spec_sha}
    for rel in spec.get("identity", []):
        identity[Path(rel).as_posix()] = committed_sha256(rel)
    head = git("rev-parse", "HEAD").decode().strip()
    tree = git("rev-parse", "HEAD^{tree}").decode().strip()
    state = tree_state()
    # The instance key (rule (d)): a "data" unit (the default) is the same unit whenever its
    # identity hashes and arguments are the same; a "tree" unit (tests, commit checks) also
    # depends on the state of the code, outside the journal and the ledger.
    parts = [sorted(identity.items()), a.extra]
    if spec.get("key", "data") == "tree":
        parts.append(state)
    key = hashlib.sha256(json.dumps(parts, separators=(",", ":")).encode()).hexdigest()

    entries = read_log()
    started = {e["instance_key"] for e in entries if e["event"] == "before"}
    ended = {e["instance_key"] for e in entries if e["event"] in ("after", "abandoned")}
    for e in entries:
        if e["event"] == "before" and e["instance_key"] not in ended:
            append_log(
                {
                    "event": "abandoned",
                    "utc": utc(),
                    "unit": e["unit"],
                    "instance_key": e["instance_key"],
                    "note": "a before entry with no after entry, found at the next launch",
                }
            )
    if key in started and not a.approval:
        raise SystemExit(f"refused: unit instance {key[:12]} already started (rule (d))")

    entries = read_log()
    used = totals(entries)
    res = spec["reserve"]
    WORK.mkdir(parents=True, exist_ok=True)
    extras = {n: resolve_extra(n) for n in spec.get("disk_extra", [])}
    base_extra = {n: tree_bytes(p) for n, p in extras.items()}
    disk_now = tree_bytes(WORK)
    if used["cpu_s"] + res["cpu_s"] > CAPS["cpu_s"]:
        raise SystemExit("refused: the CPU reservation would pass the phase's ceiling")
    if used["transfer_bytes"] + res["transfer_bytes"] > CAPS["transfer_bytes"]:
        raise SystemExit("refused: the transfer reservation would pass the phase's ceiling")
    if disk_now + res["disk_bytes"] > CAPS["disk_bytes"]:
        raise SystemExit("refused: the disk reservation would pass the phase's ceiling")

    argv = [str(PYTHON) if x == "{python}" else x for x in spec["argv"]] + list(a.extra)
    shown = ["{python}" if x == str(PYTHON) else x for x in argv]
    append_log(
        {
            "event": "before",
            "utc": utc(),
            "unit": spec["name"],
            "label": a.label,
            "instance_key": key,
            "question": spec["question"],
            "choices": spec.get("choices"),
            "argv": shown,
            "head": head,
            "tree": tree,
            "tree_state_sha256": state,
            "identity_sha256": identity,
            "reserve": res,
            "used_before": used,
            "repetition_approval": a.approval,
        }
    )

    run_dir = WORK / "runs" / f"{spec['name']}__{key[:12]}"
    run_dir.mkdir(parents=True, exist_ok=True)
    out = open(run_dir / "stdout.txt", "wb")
    err = open(run_dir / "stderr.txt", "wb")
    job = make_job(res["cpu_s"])
    net0 = net_bytes()
    t0 = time.time()
    proc = subprocess.Popen(
        argv,
        cwd=ROOT,
        stdout=out,
        stderr=err,
        stdin=subprocess.DEVNULL,
        creationflags=CREATE_SUSPENDED | BELOW_NORMAL_PRIORITY_CLASS,
    )
    if not kernel32.AssignProcessToJobObject(job, int(proc._handle)):
        proc.kill()
        raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject")
    ntdll.NtResumeProcess(int(proc._handle))

    interrupted = None
    peak = disk_now
    transfer = 0
    telemetry_ok = True
    last_slow = 0.0
    while True:
        code = proc.poll()
        cpu, nproc, active = job_cpu(job)
        if cpu > res["cpu_s"] - CPU_MARGIN_S and interrupted is None:
            interrupted = "cpu"
            kernel32.TerminateJobObject(job, 1)
        now = time.time()
        if now - last_slow >= 10.0 or (code is not None and active == 0):
            last_slow = now
            try:
                transfer = (net_bytes() - net0) % (1 << 32)
            except (RuntimeError, ValueError, OSError):
                telemetry_ok = False
            disk = tree_bytes(WORK) + sum(
                max(0, tree_bytes(p) - base_extra[n]) for n, p in extras.items()
            )
            peak = max(peak, disk)
            if interrupted is None and transfer > res["transfer_bytes"]:
                interrupted = "transfer"
                kernel32.TerminateJobObject(job, 1)
            if interrupted is None and disk - disk_now > res["disk_bytes"]:
                interrupted = "disk"
                kernel32.TerminateJobObject(job, 1)
        if code is not None and active == 0:
            break
        time.sleep(1.0)
    cpu, nproc, _ = job_cpu(job)
    kernel32.CloseHandle(job)
    out.close()
    err.close()
    wall = round(time.time() - t0, 3)

    outputs = {}
    for rel in spec.get("outputs", []):
        p = ROOT / rel
        outputs[rel] = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    status = "interrupted" if interrupted else ("ok" if proc.returncode == 0 else "failed")
    append_log(
        {
            "event": "after",
            "utc": utc(),
            "unit": spec["name"],
            "instance_key": key,
            "status": status,
            "exit_code": proc.returncode,
            "interrupted": interrupted,
            "cpu_s": round(cpu, 3),
            "wall_s": wall,
            "processes": nproc,
            "transfer_bytes_upper": transfer,
            "disk_peak_bytes": peak,
            "telemetry_complete": telemetry_ok,
            "outputs_sha256": outputs,
            "stdout_sha256": hashlib.sha256((run_dir / "stdout.txt").read_bytes()).hexdigest(),
            "stderr_sha256": hashlib.sha256((run_dir / "stderr.txt").read_bytes()).hexdigest(),
        }
    )
    write_ledger(read_log())
    print(
        json.dumps(
            {"unit": spec["name"], "status": status, "exit_code": proc.returncode, "cpu_s": cpu}
        )
    )
    print(f"stdout: {(run_dir / 'stdout.txt').relative_to(ROOT).as_posix()}")
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
