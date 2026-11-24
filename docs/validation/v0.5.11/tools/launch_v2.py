"""The metered launcher of v0.5.11, version 2. It replaces launch.py (kept unchanged) after
Codex's blocking item 5 of step 0's first round (docs/plans/v0.5.11-consensus/).

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.11/tools/launch_v2.py <unit spec>
        [--label L] [--approval URL] [-- extra arguments]

What changed from version 1:

- **Admission is serialized.** One unit runs at a time. The launcher holds an exclusive lock on
  ``.cache/v0511/launcher.lock`` from admission to the end of the run, and refuses to start if
  another launch holds it.
- **Attempts and logical units.**
  - Every execution has a unique ``attempt_id``.
  - The ``logical_key`` is stable across worker revisions: the spec's name and the extra
    arguments, plus the code's state for a ``tree`` unit.
  - A logical key with any earlier start is a repetition. It is refused unless ``--approval``
    names the issue comment that approved it (rule (d)).
  - A version-1 row has no logical key, so it matches by the unit's name for a ``data`` unit.
- **Unsettled attempts are charged.** A ``before`` with no ``after`` is marked ``abandoned``. Its
  reservation is charged in the ledger until a reconciliation row settles it.
- **Polls:**
  - the job's CPU every 0.5 s;
  - the machine's transfer bytes (``netstat -e``) every 1 s;
  - the disk every 5 s.

  A unit is stopped at 30 s of CPU, 50 MB of transfer or 100 MB of disk below its reservation, or
  at 90 % of a smaller reservation. The overshoot between polls is bounded by the poll interval,
  and it is recorded when it happens.
- **Ambiguous telemetry is incomplete:**
  - a decrease of the netstat counter;
  - a failed counter read;
  - any disk-scan error.
- **The launcher's own CPU** (its scans and polls) is added to the unit's CPU and recorded apart.
- **Gaps.** ``docs/validation/v0.5.11/meter-gaps.json`` lists the work done outside the meter.
  The ledger's ``within_caps`` is "not demonstrated" while any gap or incomplete row remains.

Everything else is as in version 1:
- the committed-blob identity check;
- the Job object on processors 8 to 31 at BelowNormal;
- the user-time limit;
- the journal;
- the ledger.

Standard library only; Windows only.
"""

# ruff: noqa: N801  (the structures keep their Win32 names)
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import msvcrt
import os
import subprocess
import sys
import time
import uuid
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PHASE = ROOT / "docs" / "validation" / "v0.5.11"
LOG = PHASE / "log.jsonl"
LEDGER = PHASE / "caps-ledger.json"
GAPS = PHASE / "meter-gaps.json"
WORK = ROOT / ".cache" / "v0511"
LOCK = WORK / "launcher.lock"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
CAPS = {"cpu_s": 36000.0, "transfer_bytes": 5_000_000_000, "disk_bytes": 10_000_000_000}
AFFINITY_MASK = 0xFFFFFF00  # processors 8 to 31
MARGIN = {"cpu_s": 30.0, "transfer_bytes": 50_000_000, "disk_bytes": 100_000_000}
POLL_CPU, POLL_NET, POLL_DISK = 0.5, 1.0, 5.0
JOURNAL_FILES = (
    "docs/validation/v0.5.11/log.jsonl",
    "docs/validation/v0.5.11/caps-ledger.json",
)
OUTSIDE_METER = [
    "GitHub CI (remote)",
    "the Codex review processes (reported apart, with their tokens)",
    "the Claude gate (reported apart)",
    "remote page retrieval by the agent's web tool (its local conversion is a gap if done "
    "outside a unit)",
    "the agent's reads: git status, log, diff and show; file reads by the agent's tools; GitHub "
    "comments",
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
    if not blob:
        raise SystemExit(f"refused: {rel} is empty")
    return hashlib.sha256(blob).hexdigest()


def tree_state() -> str:
    """SHA-256 of the code's state (HEAD tree, staged and unstaged differences, untracked files
    with their contents), leaving out the journal and the ledger."""
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


def net_bytes() -> int | None:
    try:
        out = subprocess.run(["netstat", "-e"], capture_output=True, text=True, errors="replace")
    except OSError:
        return None
    for line in out.stdout.splitlines():
        parts = line.split()
        if parts and parts[0] == "Bytes" and len(parts) >= 3:
            try:
                return int(parts[1]) + int(parts[2])
            except ValueError:
                return None
    return None


def resolve_extra(name: str) -> Path:
    """A path whose growth counts as the phase's disk. "uv-cache" and "pytest-temp" stand for
    folders outside the project, whose paths are never written."""
    if name == "uv-cache":
        out = subprocess.run(["uv", "cache", "dir"], capture_output=True, text=True, check=True)
        return Path(out.stdout.strip())
    if name == "pytest-temp":
        import getpass
        import tempfile

        return Path(tempfile.gettempdir()) / f"pytest-of-{getpass.getuser()}"
    p = (ROOT / name).resolve()
    if ROOT not in p.parents:
        raise SystemExit(f"refused: disk_extra {name} is outside the project")
    return p


def tree_bytes(p: Path) -> tuple[int, int]:
    """(bytes, scan errors) of a folder tree; links are not followed."""
    if not p.exists():
        return 0, 0
    total, errors = 0, 0
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
                        errors += 1
        except OSError:
            errors += 1
    return total, errors


def charge(entries: list[dict]) -> dict:
    """What the ledger charges: measured use for settled attempts with complete telemetry, the
    reservation (or the measured use, whichever is larger) for every other attempt."""
    befores = [e for e in entries if e["event"] == "before"]
    afters = {e.get("attempt_id") or e["instance_key"]: e for e in entries if e["event"] == "after"}
    cpu = tr = 0.0
    peak = 0
    for b in befores:
        key = b.get("attempt_id") or b["instance_key"]
        a = afters.get(key)
        res = b["reserve"]
        # a row of launch.py version 1 (no "launcher" field) is never counted as complete:
        # its transfer was taken modulo 2^32 and its disk scan skipped errors (Codex, step 0)
        if a is not None and a.get("telemetry_complete") and "launcher" in b:
            cpu += a["cpu_s"]
            tr += a["transfer_bytes_upper"]
            peak = max(peak, a["disk_peak_bytes"])
        else:
            cpu += max(res["cpu_s"], (a or {}).get("cpu_s", 0.0))
            tr += max(res["transfer_bytes"], (a or {}).get("transfer_bytes_upper", 0))
            peak = max(peak, res["disk_bytes"], (a or {}).get("disk_peak_bytes", 0))
    return {"cpu_s": round(cpu, 3), "transfer_bytes": int(tr), "disk_peak_bytes": int(peak)}


def write_ledger(entries: list[dict]) -> None:
    afters = {e.get("attempt_id") or e["instance_key"]: e for e in entries if e["event"] == "after"}
    abandoned = {
        e.get("attempt_id") or e["instance_key"] for e in entries if e["event"] == "abandoned"
    }
    rows, complete = [], True
    for b in (e for e in entries if e["event"] == "before"):
        key = b.get("attempt_id") or b["instance_key"]
        a = afters.get(key)
        row = {
            "unit": b["unit"],
            "label": b.get("label"),
            "attempt": key,
            "launcher": b.get("launcher", "launch.py (version 1)"),
            "start": b["utc"],
            "reserve": b["reserve"],
        }
        if a is None:
            row["status"] = "abandoned (reservation charged)" if key in abandoned else "unsettled"
            complete = False
        else:
            row.update(
                {
                    k: a.get(k)
                    for k in (
                        "status",
                        "cpu_s",
                        "transfer_bytes_upper",
                        "disk_peak_bytes",
                        "telemetry_complete",
                        "overrun",
                    )
                }
            )
            v1 = "launcher" not in b
            if v1:
                row["telemetry_complete"] = False
                row["note"] = "launch.py version 1: transfer modulo 2^32, scan errors skipped"
            complete = complete and bool(a.get("telemetry_complete")) and not v1
        rows.append(row)
    gaps = json.loads(GAPS.read_text(encoding="utf-8"))["gaps"] if GAPS.exists() else []
    used = charge(entries)
    within = (
        used["cpu_s"] <= CAPS["cpu_s"]
        and used["transfer_bytes"] <= CAPS["transfer_bytes"]
        and used["disk_peak_bytes"] <= CAPS["disk_bytes"]
    )
    doc = {
        "phase": "v0.5.11",
        "labels": ["exploratory", "method_status: not_validated"],
        "caps": CAPS,
        "charged": used,
        "within_caps": within if (complete and not gaps) else "not demonstrated",
        "telemetry_complete": complete,
        "gaps": len(gaps),
        "gaps_file": "docs/validation/v0.5.11/meter-gaps.json",
        "charging_rule": "measured use for settled attempts with complete telemetry; otherwise "
        "the larger of the reservation and the measured use",
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


def stop_level(reserve: float, margin: float) -> float:
    return reserve - margin if reserve > 2 * margin else 0.9 * reserve


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--label", default=None)
    ap.add_argument("--approval", default=None)
    ap.add_argument("extra", nargs="*")
    a = ap.parse_args()
    t_launcher = time.process_time()

    me = ctypes.windll.kernel32.GetCurrentProcess()
    ctypes.windll.kernel32.SetProcessAffinityMask(me, AFFINITY_MASK)
    ctypes.windll.kernel32.SetPriorityClass(me, BELOW_NORMAL_PRIORITY_CLASS)

    WORK.mkdir(parents=True, exist_ok=True)
    lock = open(LOCK, "a+b")
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        raise SystemExit("refused: another unit holds the launcher lock") from None

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
    kind = spec.get("key", "data")
    parts = [spec["name"], a.extra] + ([state] if kind == "tree" else [])
    logical = hashlib.sha256(json.dumps(parts, separators=(",", ":")).encode()).hexdigest()
    attempt = uuid.uuid4().hex

    entries = read_log()
    settled = {
        e.get("attempt_id") or e["instance_key"]
        for e in entries
        if e["event"] in ("after", "abandoned")
    }
    for e in entries:
        key = e.get("attempt_id") or e.get("instance_key")
        if e["event"] == "before" and key not in settled:
            append_log(
                {
                    "event": "abandoned",
                    "utc": utc(),
                    "unit": e["unit"],
                    "attempt_id": e.get("attempt_id"),
                    "instance_key": e.get("instance_key"),
                    "note": "a before entry with no after entry, found at the next launch; its "
                    "reservation stays charged until a reconciliation row settles it",
                }
            )
    prior = [
        e
        for e in entries
        if e["event"] == "before"
        and (
            e.get("logical_key") == logical
            or ("logical_key" not in e and kind == "data" and e["unit"] == spec["name"])
        )
    ]
    if prior and not a.approval:
        raise SystemExit(
            f"refused: the logical unit {spec['name']} ({logical[:12]}) already started; a "
            "repetition needs an approval in the issue first (rule (d))"
        )

    entries = read_log()
    used = charge(entries)
    res = spec["reserve"]
    extras = {n: resolve_extra(n) for n in spec.get("disk_extra", [])}
    base_extra, scan_err = {}, 0
    for n, p in extras.items():
        base_extra[n], err = tree_bytes(p)
        scan_err += err
    disk_now, err = tree_bytes(WORK)
    scan_err += err
    if used["cpu_s"] + res["cpu_s"] > CAPS["cpu_s"]:
        raise SystemExit("refused: the CPU reservation would pass the phase's ceiling")
    if used["transfer_bytes"] + res["transfer_bytes"] > CAPS["transfer_bytes"]:
        raise SystemExit("refused: the transfer reservation would pass the phase's ceiling")
    if max(used["disk_peak_bytes"], disk_now) + res["disk_bytes"] > CAPS["disk_bytes"]:
        raise SystemExit("refused: the disk reservation would pass the phase's ceiling")

    argv = [str(PYTHON) if x == "{python}" else x for x in spec["argv"]] + list(a.extra)
    shown = ["{python}" if x == str(PYTHON) else x for x in argv]
    # the identity of an extra argument that names a file in the project (an inspection script,
    # a message file): its SHA-256 at dispatch
    extra_files = {}
    for x in a.extra:
        p = (ROOT / x).resolve()
        if ROOT in p.parents and p.is_file():
            extra_files[Path(x).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    append_log(
        {
            "event": "before",
            "utc": utc(),
            "launcher": "launch_v2.py",
            "unit": spec["name"],
            "label": a.label,
            "attempt_id": attempt,
            "logical_key": logical,
            "key_kind": kind,
            "question": spec["question"],
            "choices": spec.get("choices"),
            "argv": shown,
            "head": head,
            "tree": tree,
            "tree_state_sha256": state,
            "identity_sha256": identity,
            "extra_files_sha256": extra_files,
            "reserve": res,
            "charged_before": used,
            "repetition_approval": a.approval,
        }
    )

    run_dir = WORK / "runs" / f"{spec['name']}__{attempt[:12]}"
    run_dir.mkdir(parents=True, exist_ok=True)
    out = open(run_dir / "stdout.txt", "wb")
    err_f = open(run_dir / "stderr.txt", "wb")
    job = make_job(res["cpu_s"])
    net0 = net_bytes()
    telemetry_ok = net0 is not None and scan_err == 0
    t0 = time.time()
    proc = subprocess.Popen(
        argv,
        cwd=ROOT,
        stdout=out,
        stderr=err_f,
        stdin=subprocess.DEVNULL,
        creationflags=CREATE_SUSPENDED | BELOW_NORMAL_PRIORITY_CLASS,
    )
    if not kernel32.AssignProcessToJobObject(job, int(proc._handle)):
        proc.kill()
        raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject")
    ntdll.NtResumeProcess(int(proc._handle))

    stops = {k: stop_level(res[k], MARGIN[k]) for k in MARGIN}
    interrupted, overrun = None, []
    peak, transfer, last_net, last_disk = disk_now, 0, net0, 0.0
    t_net = 0.0
    while True:
        code = proc.poll()
        cpu, nproc, active = job_cpu(job)
        if interrupted is None and cpu > stops["cpu_s"]:
            interrupted = "cpu"
            kernel32.TerminateJobObject(job, 1)
        now = time.time()
        finished = code is not None and active == 0
        if now - t_net >= POLL_NET or finished:
            t_net = now
            nb = net_bytes()
            if nb is None or last_net is None or nb < last_net:
                telemetry_ok = False
            else:
                transfer = nb - net0
                last_net = nb
            if interrupted is None and transfer > stops["transfer_bytes"]:
                interrupted = "transfer"
                kernel32.TerminateJobObject(job, 1)
        if now - last_disk >= POLL_DISK or finished:
            last_disk = now
            d, e1 = tree_bytes(WORK)
            grow = 0
            for n, p in extras.items():
                b, e2 = tree_bytes(p)
                e1 += e2
                grow += max(0, b - base_extra[n])
            if e1:
                telemetry_ok = False
            disk = d + grow
            peak = max(peak, disk)
            if interrupted is None and disk - disk_now > stops["disk_bytes"]:
                interrupted = "disk"
                kernel32.TerminateJobObject(job, 1)
        if finished:
            break
        time.sleep(POLL_CPU)
    cpu, nproc, _ = job_cpu(job)
    kernel32.CloseHandle(job)
    out.close()
    err_f.close()
    wall = round(time.time() - t0, 3)
    launcher_cpu = time.process_time() - t_launcher
    total_cpu = cpu + launcher_cpu
    if total_cpu > res["cpu_s"]:
        overrun.append("cpu")
    if transfer > res["transfer_bytes"]:
        overrun.append("transfer")
    if peak - disk_now > res["disk_bytes"]:
        overrun.append("disk")

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
            "attempt_id": attempt,
            "logical_key": logical,
            "status": status,
            "exit_code": proc.returncode,
            "interrupted": interrupted,
            "overrun": overrun,
            "unit_cpu_s": round(cpu, 3),
            "launcher_cpu_s": round(launcher_cpu, 3),
            "cpu_s": round(total_cpu, 3),
            "wall_s": wall,
            "processes": nproc,
            "transfer_bytes_upper": int(transfer),
            "disk_peak_bytes": int(peak),
            "telemetry_complete": telemetry_ok,
            "outputs_sha256": outputs,
            "stdout_sha256": hashlib.sha256((run_dir / "stdout.txt").read_bytes()).hexdigest(),
            "stderr_sha256": hashlib.sha256((run_dir / "stderr.txt").read_bytes()).hexdigest(),
        }
    )
    write_ledger(read_log())
    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
    lock.close()
    print(json.dumps({"unit": spec["name"], "status": status, "exit_code": proc.returncode}))
    print(f"stdout: {(run_dir / 'stdout.txt').relative_to(ROOT).as_posix()}")
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
