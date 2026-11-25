"""The metered launcher of v0.5.12, version 1 (charter, step 0 and section 5, rule (e)).

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.12/tools/launch_v1.py <unit spec>
        [--label L] [--approval URL] [-- extra arguments]

A single-file port of v0.5.11's ``launch_v9.py`` and the chain it loads (v2 to v8), with this
phase's paths and ceilings, and with what the charter's step 0 adds.

**Carried from v0.5.11:**
- one unit at a time, under ``.cache/v0512/launcher.lock``;
- the spec, this launcher, ``jobrun.py``, ``diskbound.py`` and every identity file must equal their
  committed blobs, and none may be empty;
- a ``before`` journal entry (question, choices, argv, HEAD, tree, code state, identities,
  reservation, what is charged so far) and an ``after`` entry (status, use, outputs);
- the logical key (the spec's name and the extra arguments, plus the code state for a ``tree``
  unit); a key that already started is a repetition, refused without ``--approval`` (rule (d));
- a ``before`` with no ``after`` found at the next launch is recorded ``abandoned`` and its
  reservation stays charged;
- a unit does not start if its reservation would pass a ceiling, and it is stopped before it can
  pass its own allowance.

**What step 0 adds:**
- **The whole tree is metered.** The launcher puts itself in an outer job object at start, so its
  own CPU and that of every child (git calls included) are counted; the unit runs in its own inner
  job (``jobrun.py``), which also counts the bytes its tree writes.
- **Offline across the process tree.** A unit with ``"network": false`` runs in the AppContainer
  ``refute.v0512.offline`` (no capability), with a private home, temp and caches under its run
  folder, ``{python}`` being the container's copy of the interpreter (``.cache/v0512/cpy``) and
  ``git`` the container's copy (``.cache/v0512/git``). It writes only under ``.cache/v0512`` and
  ``.git`` (and ``.ruff_cache``); its outputs are copied by the launcher, outside the container, to
  their committed destinations.
- **Permitted traffic only.** A unit with network must say ``"network": {"kind": "github" |
  "review", "endpoints": [...], "operations": [...]}``; it runs in a job without the container, and
  its argv, endpoints and operations are journaled as evidence. No other unit has network.
- **One phase-wide disk bound** (``diskbound.py``): the roots are scanned before and after each
  unit; the unit's written bytes are its allowance's measure while it runs; the bound
  ``max(O_start + W, O_end)`` is journaled and the phase peak is the largest over every unit,
  bootstrap included (``bootstrap-disk.jsonl``).
- **The bootstrap is charged once,** by cross-reference: every attempt listed in
  ``bootstrap-attempts.json`` is read from v0.5.11's journal and charged here.
"""

# ruff: noqa: N801
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import msvcrt
import os
import shutil
import subprocess
import sys
import time
import uuid
from ctypes import wintypes
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diskbound  # noqa: E402
import jobrun  # noqa: E402

ROOT = diskbound.ROOT
PHASE = ROOT / "docs" / "validation" / "v0.5.12"
LOG = PHASE / "log.jsonl"
LEDGER = PHASE / "caps-ledger.json"
GAPS = PHASE / "meter-gaps.json"
BOOT_DISK = PHASE / "bootstrap-disk.jsonl"
BOOT_ATTEMPTS = PHASE / "bootstrap-attempts.json"
V0511_LOG = ROOT / "docs" / "validation" / "v0.5.11" / "log.jsonl"
WORK = ROOT / ".cache" / "v0512"
LOCK = WORK / "launcher.lock"
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"
CPY = WORK / "cpy" / "python.exe"
GIT_BIN = WORK / "git" / "mingw64" / "bin"
CONTAINER = "refute.v0512.offline"
CAPS = {"cpu_s": 3 * 3600.0, "download_bytes": 0, "disk_bytes": 2_000_000_000}
JOURNAL_FILES = (
    "docs/validation/v0.5.12/log.jsonl",
    "docs/validation/v0.5.12/caps-ledger.json",
    "docs/validation/v0.5.11/log.jsonl",
    "docs/validation/v0.5.11/caps-ledger.json",
)
OUTSIDE_METER = [
    "the agent's own file tools (reading and editing files; their writes are carried by the next "
    "disk scan)",
    "the agent's shell host process that starts this launcher",
    "remote CI provisioning and reviewer inference (reported apart)",
]
kernel32 = jobrun.kernel32
BELOW_NORMAL = jobrun.BELOW_NORMAL_PRIORITY_CLASS


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def committed_sha256(rel: str) -> str:
    rel = Path(rel).as_posix()
    try:
        blob = git("show", f"HEAD:{rel}")
    except subprocess.CalledProcessError:
        raise SystemExit(f"refused: {rel} is not committed") from None
    if (ROOT / rel).read_bytes().replace(b"\r\n", b"\n") != blob.replace(b"\r\n", b"\n"):
        raise SystemExit(f"refused: {rel} differs from its committed blob")
    if not blob:
        raise SystemExit(f"refused: {rel} is empty")
    return hashlib.sha256(blob).hexdigest()


def tree_state() -> str:
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


def read_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def append_log(entry: dict) -> None:
    PHASE.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def bootstrap_rows() -> list[dict]:
    """The bootstrap's attempts in v0.5.11's journal, charged here once."""
    opened = json.loads(BOOT_ATTEMPTS.read_text(encoding="utf-8"))["phase_opened_utc"]
    entries = read_jsonl(V0511_LOG)
    wanted = [
        e["attempt_id"]
        for e in entries
        if e["event"] == "before" and e.get("attempt_id") and e["utc"] >= opened
    ]
    rows = []
    for att in wanted:
        b = next((e for e in entries if e.get("attempt_id") == att and e["event"] == "before"), {})
        a = next((e for e in entries if e.get("attempt_id") == att and e["event"] == "after"), None)
        rows.append(
            {
                "attempt": att,
                "unit": b.get("unit"),
                "start": b.get("utc"),
                "status": (a or {}).get("status", "missing"),
                "cpu_s": (a or {}).get("cpu_s", b.get("reserve", {}).get("cpu_s", 0.0)),
                "telemetry_complete": bool(a and a.get("telemetry_complete")),
            }
        )
    return rows


def charge(entries: list[dict]) -> dict:
    """Measured use for settled attempts, the larger of reservation and use otherwise; the disk
    peak is the largest bound over every unit and the bootstrap."""
    befores = [e for e in entries if e["event"] == "before"]
    afters = {e["attempt_id"]: e for e in entries if e["event"] == "after"}
    cpu = sum(r["cpu_s"] for r in bootstrap_rows())
    base = json.loads(BOOT_ATTEMPTS.read_text(encoding="utf-8"))["baseline_fast_total"]
    peak = 0
    for x in read_jsonl(BOOT_DISK):  # each bootstrap bound, moved to the phase's baseline
        shift = x["baseline_fast_total"] - base
        peak = max(peak, x["o_start"] + shift + x["job"]["write_bytes"], x["o_end"] + shift)
    for b in befores:
        a = afters.get(b["attempt_id"])
        if a is not None and a.get("telemetry_complete"):
            cpu += a["cpu_s"]
            peak = max(peak, a["disk_bound_bytes"])
        else:
            cpu += max(b["reserve"]["cpu_s"], (a or {}).get("cpu_s", 0.0))
            peak = max(peak, b["o_start"] + b["reserve"]["disk_bytes"])
    return {"cpu_s": round(cpu, 3), "download_bytes": 0, "disk_peak_bytes": int(peak)}


def write_ledger(entries: list[dict]) -> None:
    afters = {e["attempt_id"]: e for e in entries if e["event"] == "after"}
    abandoned = {e["attempt_id"] for e in entries if e["event"] == "abandoned"}
    rows, complete = [], True
    boot = bootstrap_rows()
    complete = all(r["telemetry_complete"] for r in boot)
    for b in (e for e in entries if e["event"] == "before"):
        a = afters.get(b["attempt_id"])
        row = {"unit": b["unit"], "label": b.get("label"), "attempt": b["attempt_id"]}
        row.update({"start": b["utc"], "reserve": b["reserve"]})
        if a is None:
            gone = b["attempt_id"] in abandoned
            row["status"] = "abandoned (reservation charged)" if gone else "unsettled"
            complete = False
        else:
            for k in ("status", "cpu_s", "write_bytes", "disk_bound_bytes", "telemetry_complete"):
                row[k] = a.get(k)
            complete = complete and bool(a.get("telemetry_complete"))
        rows.append(row)
    gaps = json.loads(GAPS.read_text(encoding="utf-8"))["gaps"] if GAPS.exists() else []
    used = charge(entries)
    within = used["cpu_s"] <= CAPS["cpu_s"] and used["disk_peak_bytes"] <= CAPS["disk_bytes"]
    doc = {
        "phase": "v0.5.12",
        "labels": ["exploratory", "method_status: not_validated"],
        "caps": CAPS,
        "charged": used,
        "within_caps": within if (complete and not gaps) else "not demonstrated",
        "telemetry_complete": complete,
        "gaps": len(gaps),
        "gaps_file": "docs/validation/v0.5.12/meter-gaps.json",
        "charging_rule": "measured use for settled attempts with complete telemetry; otherwise the "
        "larger of the reservation and the measured use; the bootstrap charged once by "
        "cross-reference to v0.5.11's journal",
        "downloads_rule": "every offline unit runs in the AppContainer with no capability; only "
        "units declaring GitHub or review traffic have network, with their operations journaled",
        "outside_meter": OUTSIDE_METER,
        "bootstrap": boot,
        "rows": rows,
    }
    LEDGER.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")


def outer_job():
    """Put this launcher in a job: its CPU and every child's are counted from here on."""
    job = kernel32.CreateJobObjectW(None, None)
    lim = jobrun.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    b = lim.BasicLimitInformation
    b.LimitFlags = jobrun.JOB_OBJECT_LIMIT_AFFINITY | jobrun.JOB_OBJECT_LIMIT_PRIORITY_CLASS
    b.Affinity = jobrun.AFFINITY_MASK
    b.PriorityClass = BELOW_NORMAL
    kernel32.SetInformationJobObject(
        job, jobrun.JobObjectExtendedLimitInformation, ctypes.addressof(lim), ctypes.sizeof(lim)
    )
    me = ctypes.windll.kernel32.GetCurrentProcess()
    if not kernel32.AssignProcessToJobObject(job, wintypes.HANDLE(me)):
        raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject (launcher)")
    return job


def private_env(run_dir: Path) -> dict[str, str]:
    dirs = {}
    for name in ("home", "ad", "lad", "tmp", "xdg_config", "xdg_cache", "mpl", "out"):
        d = run_dir / "private" / name if name != "out" else run_dir / "out"
        d.mkdir(parents=True, exist_ok=True)
        dirs[name] = str(d)
    sysroot = os.environ.get("SystemRoot", "C:/Windows")
    path = [str(CPY.parent), str(CPY.parent / "Scripts"), str(GIT_BIN), f"{sysroot}/System32"]
    return {
        "SystemRoot": sysroot,
        "windir": sysroot,
        "PATH": ";".join([*path, sysroot]),
        "HOME": dirs["home"],
        "USERPROFILE": dirs["home"],
        "APP" + "DATA": dirs["ad"],
        "LOCAL" + "APP" + "DATA": dirs["lad"],
        "TEMP": dirs["tmp"],
        "TMP": dirs["tmp"],
        "XDG_CONFIG_HOME": dirs["xdg_config"],
        "XDG_CACHE_HOME": dirs["xdg_cache"],
        "MPLCONFIGDIR": dirs["mpl"],
        "MPLBACKEND": "Agg",
        "UV_OFFLINE": "1",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": str(WORK / "gitconfig"),
        "REFUTE_RUN_OUT": dirs["out"],
        "NUMBER_OF_PROCESSORS": os.environ.get("NUMBER_OF_PROCESSORS", "32"),
        "PROCESSOR_ARCHITECTURE": os.environ.get("PROCESSOR_ARCHITECTURE", "AMD64"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--label", default=None)
    ap.add_argument("--approval", default=None)
    ap.add_argument("extra", nargs="*")
    a = ap.parse_args()
    job0 = outer_job()
    WORK.mkdir(parents=True, exist_ok=True)
    lock = open(LOCK, "a+b")
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        raise SystemExit("refused: another unit holds the launcher lock") from None

    spec_rel = Path(a.spec).as_posix()
    spec = json.loads((ROOT / spec_rel).read_text(encoding="utf-8"))
    identity = {spec_rel: committed_sha256(spec_rel)}
    for rel in [
        Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "docs/validation/v0.5.12/tools/jobrun.py",
        "docs/validation/v0.5.12/tools/diskbound.py",
        *spec.get("identity", []),
    ]:
        identity[Path(rel).as_posix()] = committed_sha256(rel)
    net = spec.get("network", False)
    if net is not False and (
        not isinstance(net, dict) or net.get("kind") not in ("github", "review")
    ):
        raise SystemExit("refused: a unit's network must be false, or github or review traffic")
    head = git("rev-parse", "HEAD").decode().strip()
    tree = git("rev-parse", "HEAD^{tree}").decode().strip()
    state = tree_state()
    kind = spec.get("key", "data")
    parts = [spec["name"], a.extra] + ([state] if kind == "tree" else [])
    logical = hashlib.sha256(json.dumps(parts, separators=(",", ":")).encode()).hexdigest()
    attempt = uuid.uuid4().hex

    entries = read_jsonl(LOG)
    settled = {e["attempt_id"] for e in entries if e["event"] in ("after", "abandoned")}
    for e in entries:
        if e["event"] == "before" and e["attempt_id"] not in settled:
            append_log({"event": "abandoned", "utc": utc(), "unit": e["unit"],
                        "attempt_id": e["attempt_id"],
                        "note": "a before entry with no after entry, found at the next launch; "
                        "its reservation stays charged"})  # fmt: skip
    if any(e["event"] == "before" and e.get("logical_key") == logical for e in entries):
        if not a.approval:
            raise SystemExit(
                f"refused: the logical unit {spec['name']} ({logical[:12]}) already started; a "
                "repetition needs an approval in the issue first (rule (d))"
            )

    entries = read_jsonl(LOG)
    used = charge(entries)
    res = spec["reserve"]
    lc_scan = bool(spec.get("lock_compat_scan"))
    before = diskbound.scan(lock_compat=lc_scan)
    boot = json.loads(BOOT_ATTEMPTS.read_text(encoding="utf-8"))
    baseline, lc_baseline = boot["baseline_fast_total"], boot["lock_compat_baseline"]
    grown = [e.get("lock_compat_growth", 0) for e in entries if e["event"] == "after"]
    lc_carried = max([0, *grown])
    o_start = before["fast_total"] - baseline + lc_carried
    if used["cpu_s"] + res["cpu_s"] > CAPS["cpu_s"]:
        raise SystemExit("refused: the CPU reservation would pass the phase's ceiling")
    if o_start + res["disk_bytes"] > CAPS["disk_bytes"]:
        raise SystemExit("refused: the disk reservation would pass the phase's ceiling")

    offline = net is False
    py = str(CPY) if offline else str(VENV_PY)
    argv = [py if x == "{python}" else x for x in spec["argv"]] + list(a.extra)
    shown = ["{python}" if x == py else x for x in argv]
    extra_files = {}
    for x in a.extra:
        p = (ROOT / x).resolve()
        if ROOT in p.parents and p.is_file():
            extra_files[Path(x).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    append_log(
        {
            "event": "before",
            "utc": utc(),
            "launcher": "launch_v1.py",
            "unit": spec["name"],
            "label": a.label,
            "attempt_id": attempt,
            "logical_key": logical,
            "key_kind": kind,
            "question": spec["question"],
            "choices": spec.get("choices"),
            "argv": shown,
            "network": net,
            "sandbox": f"appcontainer {CONTAINER}" if offline else f"job, network {net['kind']}",
            "head": head,
            "tree": tree,
            "tree_state_sha256": state,
            "identity_sha256": identity,
            "extra_files_sha256": extra_files,
            "reserve": res,
            "charged_before": used,
            "o_start": o_start,
            "repetition_approval": a.approval,
        }
    )
    run_dir = WORK / "runs" / f"{spec['name']}__{attempt[:12]}"
    run_dir.mkdir(parents=True, exist_ok=True)
    env = private_env(run_dir) if offline else None
    if not offline:
        env = dict(os.environ)
        env["REFUTE_RUN_OUT"] = str(run_dir / "out")
        (run_dir / "out").mkdir(exist_ok=True)
    rec = jobrun.run(
        argv,
        ROOT,
        run_dir / "stdout.txt",
        run_dir / "stderr.txt",
        env=env,
        container=CONTAINER if offline else None,
        cpu_limit_s=res["cpu_s"],
        write_limit_bytes=max(0, min(res["disk_bytes"], CAPS["disk_bytes"] - o_start)),
        timeout_s=spec.get("timeout_s", 1800),
    )
    after = diskbound.scan(lock_compat=lc_scan)
    o_end = after["fast_total"] - baseline + lc_carried
    lc_growth = lc_carried
    if lc_scan:
        lc_growth = max(lc_carried, after["lock_compat"] - lc_baseline)
        o_end += lc_growth - lc_carried
    bound = max(o_start + rec["write_bytes"], o_end)
    outputs = {}
    if rec["exit_code"] == 0 and rec["stopped"] is None:
        for src_rel, dst_rel in spec.get("outputs", {}).items():
            src = run_dir / "out" / src_rel
            dst = ROOT / dst_rel
            if src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
                outputs[dst_rel] = hashlib.sha256(dst.read_bytes()).hexdigest()
            else:
                outputs[dst_rel] = None
    # the outer job holds the launcher and, nested, the unit's job: its total is the whole tree's
    total_cpu = max(jobrun._account(job0)["cpu_s"], rec["cpu_s"])
    overrun = []
    if total_cpu > res["cpu_s"]:
        overrun.append("cpu")
    if bound - o_start > res["disk_bytes"]:
        overrun.append("disk")
    status = "interrupted" if rec["stopped"] else ("ok" if rec["exit_code"] == 0 else "failed")
    append_log(
        {
            "event": "after",
            "utc": utc(),
            "unit": spec["name"],
            "attempt_id": attempt,
            "logical_key": logical,
            "status": status,
            "exit_code": rec["exit_code"],
            "interrupted": rec["stopped"],
            "overrun": overrun,
            "unit_cpu_s": round(rec["cpu_s"], 3),
            "cpu_s": round(total_cpu, 3),
            "wall_s": rec["wall_s"],
            "processes": rec["processes"],
            "write_bytes": rec["write_bytes"],
            "read_bytes": rec["read_bytes"],
            "o_end": o_end,
            "lock_compat_growth": lc_growth,
            "disk_bound_bytes": bound,
            "telemetry_complete": True,
            "outputs_sha256": outputs,
            "stdout_sha256": hashlib.sha256((run_dir / "stdout.txt").read_bytes()).hexdigest(),
            "stderr_sha256": hashlib.sha256((run_dir / "stderr.txt").read_bytes()).hexdigest(),
        }
    )
    write_ledger(read_jsonl(LOG))
    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
    lock.close()
    summary = {"unit": spec["name"], "status": status, "exit_code": rec["exit_code"]}
    summary.update({"cpu_s": round(total_cpu, 3), "write_bytes": rec["write_bytes"]})
    summary.update({"disk_bound_bytes": bound, "run": run_dir.relative_to(ROOT).as_posix()})
    print(json.dumps(summary))
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
