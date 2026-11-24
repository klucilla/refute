"""The metered launcher of v0.5.11, version 4: version 3 with a disk scan that follows no link
and no junction.

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.11/tools/launch_v4.py <unit spec>
        [--label L] [--approval URL] [-- extra arguments]

**Why.** Version 3 refused the first `tests` unit before dispatch (2026-11-24, errata entry 5).
Its baseline scan of pytest's temporary folder had errors: an old test had left a directory
junction pointing at its own parent. `os.DirEntry.is_symlink()` is false for a Windows junction,
so the scan followed it in a loop, until the path was too long.

**What changed.** This version neither follows nor counts a symbolic link or a junction
(`DirEntry.is_junction()`). It counts the bytes of regular files, as before. Every other rule is
version 3's, unchanged:
- baselines are required before dispatch;
- lost telemetry stops the job;
- reservations and charging are as before;
- the helpers come from launch_v2.py.

The SHA-256 of launch_v2.py and of this file are in every attempt's identity.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import msvcrt
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("launch_v2", _HERE / "launch_v2.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

ROOT, WORK, CAPS, MARGIN = base.ROOT, base.WORK, base.CAPS, base.MARGIN


def tree_bytes(p: Path) -> tuple[int, int]:
    """(bytes, scan errors) of a folder tree; links and junctions are neither followed nor
    counted."""
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
                        if e.is_symlink() or e.is_junction():
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


def job_cpu(job) -> tuple[float, int, int, bool]:
    a = base.JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
    ok = base.kernel32.QueryInformationJobObject(
        job,
        base.JobObjectBasicAccountingInformation,
        ctypes.addressof(a),
        ctypes.sizeof(a),
        None,
    )
    cpu = (a.TotalUserTime + a.TotalKernelTime) / 1e7
    return cpu, a.TotalProcesses, a.ActiveProcesses, bool(ok)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--label", default=None)
    ap.add_argument("--approval", default=None)
    ap.add_argument("extra", nargs="*")
    a = ap.parse_args()
    t_launcher = time.process_time()

    me = ctypes.windll.kernel32.GetCurrentProcess()
    ctypes.windll.kernel32.SetProcessAffinityMask(me, base.AFFINITY_MASK)
    ctypes.windll.kernel32.SetPriorityClass(me, base.BELOW_NORMAL_PRIORITY_CLASS)

    WORK.mkdir(parents=True, exist_ok=True)
    lock = open(base.LOCK, "a+b")
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        raise SystemExit("refused: another unit holds the launcher lock") from None

    spec_rel = Path(a.spec).as_posix()
    spec_sha = base.committed_sha256(spec_rel)
    spec = json.loads((ROOT / spec_rel).read_text(encoding="utf-8"))
    me_rel = Path(__file__).resolve().relative_to(ROOT).as_posix()
    v2_rel = (_HERE / "launch_v2.py").relative_to(ROOT).as_posix()
    identity = {
        me_rel: base.committed_sha256(me_rel),
        v2_rel: base.committed_sha256(v2_rel),
        spec_rel: spec_sha,
    }
    for rel in spec.get("identity", []):
        identity[Path(rel).as_posix()] = base.committed_sha256(rel)
    head = base.git("rev-parse", "HEAD").decode().strip()
    tree = base.git("rev-parse", "HEAD^{tree}").decode().strip()
    state = base.tree_state()
    kind = spec.get("key", "data")
    parts = [spec["name"], a.extra] + ([state] if kind == "tree" else [])
    logical = hashlib.sha256(json.dumps(parts, separators=(",", ":")).encode()).hexdigest()
    attempt = uuid.uuid4().hex

    entries = base.read_log()
    settled = {
        e.get("attempt_id") or e["instance_key"]
        for e in entries
        if e["event"] in ("after", "abandoned")
    }
    for e in entries:
        key = e.get("attempt_id") or e.get("instance_key")
        if e["event"] == "before" and key not in settled:
            base.append_log(
                {
                    "event": "abandoned",
                    "utc": base.utc(),
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

    entries = base.read_log()
    used = base.charge(entries)
    res = spec["reserve"]
    extras = {n: base.resolve_extra(n) for n in spec.get("disk_extra", [])}
    base_extra, scan_err = {}, 0
    for n, p in extras.items():
        base_extra[n], err = tree_bytes(p)
        scan_err += err
    disk_now, err = tree_bytes(WORK)
    scan_err += err
    net0 = base.net_bytes()
    if net0 is None:
        raise SystemExit("refused: the transfer baseline is not available")
    if scan_err:
        raise SystemExit("refused: the disk baseline has scan errors")
    if used["cpu_s"] + res["cpu_s"] > CAPS["cpu_s"]:
        raise SystemExit("refused: the CPU reservation would pass the phase's ceiling")
    if used["transfer_bytes"] + res["transfer_bytes"] > CAPS["transfer_bytes"]:
        raise SystemExit("refused: the transfer reservation would pass the phase's ceiling")
    if max(used["disk_peak_bytes"], disk_now) + res["disk_bytes"] > CAPS["disk_bytes"]:
        raise SystemExit("refused: the disk reservation would pass the phase's ceiling")
    job = base.make_job(res["cpu_s"])
    if not job_cpu(job)[3]:
        base.kernel32.CloseHandle(job)
        raise SystemExit("refused: the job's CPU query is not available")

    argv = [str(base.PYTHON) if x == "{python}" else x for x in spec["argv"]] + list(a.extra)
    shown = ["{python}" if x == str(base.PYTHON) else x for x in argv]
    extra_files = {}
    for x in a.extra:
        p = (ROOT / x).resolve()
        if ROOT in p.parents and p.is_file():
            extra_files[Path(x).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    base.append_log(
        {
            "event": "before",
            "utc": base.utc(),
            "launcher": "launch_v4.py",
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
    t0 = time.time()
    proc = subprocess.Popen(
        argv,
        cwd=ROOT,
        stdout=out,
        stderr=err_f,
        stdin=subprocess.DEVNULL,
        creationflags=base.CREATE_SUSPENDED | base.BELOW_NORMAL_PRIORITY_CLASS,
    )
    if not base.kernel32.AssignProcessToJobObject(job, int(proc._handle)):
        proc.kill()
        raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject")
    base.ntdll.NtResumeProcess(int(proc._handle))

    stops = {k: base.stop_level(res[k], MARGIN[k]) for k in MARGIN}
    interrupted, overrun, telemetry_ok = None, [], True
    peak, transfer, last_net, last_disk, t_net = disk_now, 0, net0, 0.0, 0.0

    def stop(reason: str) -> None:
        nonlocal interrupted
        if interrupted is None:
            interrupted = reason
            base.kernel32.TerminateJobObject(job, 1)

    cpu = 0.0
    nproc = 0
    while True:
        code = proc.poll()
        c, n_p, active, ok = job_cpu(job)
        if ok:
            cpu, nproc = c, n_p
        else:
            telemetry_ok = False
            stop("telemetry")
            active = 0 if code is not None else active
        if cpu > stops["cpu_s"]:
            stop("cpu")
        now = time.time()
        finished = code is not None and active == 0
        if now - t_net >= base.POLL_NET or finished:
            t_net = now
            nb = base.net_bytes()
            if nb is None or nb < last_net:
                telemetry_ok = False
                stop("telemetry")
            else:
                transfer = nb - net0
                last_net = nb
            if transfer > stops["transfer_bytes"]:
                stop("transfer")
        if now - last_disk >= base.POLL_DISK or finished:
            last_disk = now
            d, e1 = tree_bytes(WORK)
            grow = 0
            for n, p in extras.items():
                b, e2 = tree_bytes(p)
                e1 += e2
                grow += max(0, b - base_extra[n])
            if e1:
                telemetry_ok = False
                stop("telemetry")
            disk = d + grow
            peak = max(peak, disk)
            if disk - disk_now > stops["disk_bytes"]:
                stop("disk")
        if finished:
            break
        time.sleep(base.POLL_CPU)
    c, n_p, _, ok = job_cpu(job)
    if ok:
        cpu, nproc = c, n_p
    else:
        telemetry_ok = False
    base.kernel32.CloseHandle(job)
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
    base.append_log(
        {
            "event": "after",
            "utc": base.utc(),
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
    base.write_ledger(base.read_log())
    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
    lock.close()
    print(json.dumps({"unit": spec["name"], "status": status, "exit_code": proc.returncode}))
    print(f"stdout: {(run_dir / 'stdout.txt').relative_to(ROOT).as_posix()}")
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
