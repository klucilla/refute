"""The metered launcher of v0.5.13, version 1 (charter approved at 04402e7a: section 8, "The meter
and the caps criterion"; step 0).

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.13/tools/launch_v1.py <unit spec>
        [--label L] [--approval URL] [--retry-of ATTEMPT --retry-reason TEXT] [--bootstrap]
        [-- extra arguments]

**The meter is a Windows job object only** (no AppContainer):
- the launcher puts itself in an outer job at start, so its own CPU and every child's are
  counted; the unit runs in its own inner job (``docs/validation/v0.5.12/tools/jobrun.py``,
  imported unchanged, with no container), which also counts the bytes the unit's tree writes;
- processors 8 to 31 and BelowNormal for every process of the tree.

**Offline units** get ``UV_OFFLINE=1``; their pytest runs use ``--disable-socket`` (the project's
pytest configuration). These settings do not establish process-wide socket isolation (charter,
section 8). **Network units** must declare ``"network": {"kind": "github" | "review" | "mast",
"endpoints": [...], "operations": [...], "inbound_estimate_bytes": N}``; the inbound bytes charged
are the unit's measured count (``out/transfer.json``, ``{"inbound_bytes": N, "basis": ...}``)
when it writes one, otherwise the declared conservative estimate.

**The journal** (``docs/validation/v0.5.13/log.jsonl``): a ``before`` entry opens before the unit
starts (logical unit ID, attempt and parent IDs, approval or trigger, command, hashes, the
reservation, what is charged so far) and an ``after`` entry closes it (exit status, case-output
count, CPU, downloaded bytes, disk contribution). A ``before`` found with no ``after`` at the next
launch is recorded ``abandoned`` and its reservation stays charged.

**Executions outside the meter** are opened by the agent, before a planned launch or at once on
detecting an unexpected one, in ``docs/validation/v0.5.13/exceptions.jsonl``; the ledger charges
their conservative estimates.

**Repetitions** (charter, section 8, the retry classes). A logical unit that already started is
refused, unless:
- ``--approval URL``: a #218 approval of the reason and exact procedure; or
- ``--retry-of ATTEMPT --retry-reason TEXT`` for a spec whose ``retry_class`` is ``checker``,
  ``formatter`` or ``infra``, never for a spec marked ``"scientific": true`` or
  ``"emits_case_values": true``; ``infra`` once only, after the original attempt's ``after``
  entry shows a failure with zero case outputs.
Paths, output names and tree changes do not create a new logical identity: the key is the spec's
name and its extra arguments (plus the code state for a ``tree`` unit).

**The order proof.** A spec with ``"order_proof": "<manifest path>"`` starts only if a receipt of
``order_proof.py`` (a network unit) for that manifest's committed blob exists and says that it
passed: the evidence commit is on ``origin/main``, carries the trailer ``CI: order-proof``, and its
push run of ``ci.yml`` was created before now with ``record-only``.

**The bootstrap.** ``--bootstrap`` is allowed only while this launcher is not committed at HEAD:
the identity files are hashed from the working tree (they are not committed yet) and marked so. A
refused bootstrap commit can therefore be retried (as a ``checker`` retry); once the launcher is at
HEAD, every unit requires the committed blobs.

**The self-test.** With ``REFUTE_LAUNCH_SELFTEST=1`` the journal, ledger and work folder go under
``.cache/v0513prep/selftest/``, only the ``demo`` specs run, and identity is hashed from the
working tree; nothing is written into the phase's records.

**The caps** (charter, section 9): 8 CPU-h, 3 GB downloads, 5 GB peak disk. A unit whose
reservation would pass a cap does not start; a unit is stopped before it passes its own CPU or
written-bytes allowance.
"""

# ruff: noqa: N801
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
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

ROOT = diskbound.ROOT
_JOBRUN = ROOT / "docs" / "validation" / "v0.5.12" / "tools" / "jobrun.py"
_spec = importlib.util.spec_from_file_location("jobrun", _JOBRUN)
jobrun = importlib.util.module_from_spec(_spec)
sys.modules["jobrun"] = jobrun
_spec.loader.exec_module(jobrun)

# The self-test (REFUTE_LAUNCH_SELFTEST=1): journal, ledger and work folder under .cache, only
# the demo specs, identity hashed from the working tree. It exercises the launcher before the
# phase uses it and writes nothing into the phase's records.
SELFTEST = os.environ.get("REFUTE_LAUNCH_SELFTEST") == "1"
if SELFTEST:
    PHASE = ROOT / ".cache" / "v0513prep" / "selftest" / "phase"
    WORK = ROOT / ".cache" / "v0513prep" / "selftest" / "work"
else:
    PHASE = ROOT / "docs" / "validation" / "v0.5.13"
    WORK = ROOT / ".cache" / "v0513"
LOG = PHASE / "log.jsonl"
LEDGER = PHASE / "caps-ledger.json"
EXCEPTIONS = PHASE / "exceptions.jsonl"
RECEIPTS = ROOT / "docs" / "validation" / "v0.5.13" / "order-proofs"
LOCK = WORK / "launcher.lock"
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"
CAPS = {"cpu_s": 8 * 3600.0, "download_bytes": 3_000_000_000, "disk_bytes": 5_000_000_000}
NETWORK_KINDS = ("github", "review", "mast")
RETRY_CLASSES = ("checker", "formatter", "infra")
ENV_ALLOWED = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
JOURNAL_FILES = (
    "docs/validation/v0.5.13/log.jsonl",
    "docs/validation/v0.5.13/caps-ledger.json",
    "docs/validation/v0.5.13/exceptions.jsonl",
)
kernel32 = jobrun.kernel32


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


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


def charge(entries: list[dict]) -> dict:
    """Measured use for settled attempts; the larger of reservation and use otherwise; plus the
    conservative estimates of every execution outside the meter."""
    afters = {e["attempt_id"]: e for e in entries if e["event"] == "after"}
    cpu, down, peak = 0.0, 0, 0
    for b in (e for e in entries if e["event"] == "before"):
        a = afters.get(b["attempt_id"])
        res = b["reserve"]
        if a is not None and a.get("telemetry_complete"):
            cpu += a["cpu_s"]
            down += a.get("download_bytes", 0)
            peak = max(peak, a["disk_bound_bytes"])
        else:
            cpu += max(res["cpu_s"], (a or {}).get("cpu_s", 0.0))
            down += max(res.get("download_bytes", 0), (a or {}).get("download_bytes", 0))
            peak = max(peak, b["o_start"] + res["disk_bytes"])
    for x in read_jsonl(EXCEPTIONS):
        if x.get("event") == "exception-open":
            est = x.get("estimate", {})
            cpu += float(est.get("cpu_s", 0.0))
            down += int(est.get("download_bytes", 0))
            peak = max(peak, int(est.get("disk_peak_bytes", 0)))
    return {"cpu_s": round(cpu, 3), "download_bytes": int(down), "disk_peak_bytes": int(peak)}


def write_ledger(entries: list[dict]) -> None:
    afters = {e["attempt_id"]: e for e in entries if e["event"] == "after"}
    abandoned = {e["attempt_id"] for e in entries if e["event"] == "abandoned"}
    rows, complete = [], True
    for b in (e for e in entries if e["event"] == "before"):
        a = afters.get(b["attempt_id"])
        row = {"unit": b["unit"], "label": b.get("label"), "attempt": b["attempt_id"]}
        row.update({"start": b["utc"], "reserve": b["reserve"], "retry": b.get("retry")})
        if a is None:
            gone = b["attempt_id"] in abandoned
            row["status"] = "abandoned (reservation charged)" if gone else "unsettled"
            complete = False
        else:
            for k in ("status", "cpu_s", "download_bytes", "write_bytes", "disk_bound_bytes",
                      "case_outputs", "telemetry_complete"):  # fmt: skip
                row[k] = a.get(k)
            complete = complete and bool(a.get("telemetry_complete"))
        rows.append(row)
    exc = [x for x in read_jsonl(EXCEPTIONS) if x.get("event") == "exception-open"]
    used = charge(entries)
    within = (
        used["cpu_s"] <= CAPS["cpu_s"]
        and used["download_bytes"] <= CAPS["download_bytes"]
        and used["disk_peak_bytes"] <= CAPS["disk_bytes"]
    )
    doc = {
        "phase": "v0.5.13",
        "labels": ["exploratory", "method_status: not_validated"],
        "caps": CAPS,
        "charged": used,
        "within_caps_so_far": within,
        "telemetry_complete": complete,
        "exceptions_outside_meter": len(exc),
        "charging_rule": "measured use for settled attempts with complete telemetry; otherwise "
        "the larger of the reservation and the measured use; plus the conservative estimates of "
        "every execution recorded outside the meter (exceptions.jsonl)",
        "downloads_rule": "offline units run with UV_OFFLINE=1 and pytest --disable-socket (no "
        "process-wide socket isolation); network units are named (github, review, mast) and "
        "charge their measured inbound bytes, or their declared conservative estimate",
        "reconciliation": "at the seal, through the sealed journal cursor, with headroom reserved "
        "for the final review, gate and closure; the post-seal tail is appended and reconciled "
        "before report approval (charter, section 8, Codex r2, item 5)",
        "rows": rows,
    }
    LEDGER.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")


def outer_job():
    job = kernel32.CreateJobObjectW(None, None)
    lim = jobrun.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    b = lim.BasicLimitInformation
    b.LimitFlags = jobrun.JOB_OBJECT_LIMIT_AFFINITY | jobrun.JOB_OBJECT_LIMIT_PRIORITY_CLASS
    b.Affinity = jobrun.AFFINITY_MASK
    b.PriorityClass = jobrun.BELOW_NORMAL_PRIORITY_CLASS
    kernel32.SetInformationJobObject(
        job, jobrun.JobObjectExtendedLimitInformation, ctypes.addressof(lim), ctypes.sizeof(lim)
    )
    me = ctypes.windll.kernel32.GetCurrentProcess()
    if not kernel32.AssignProcessToJobObject(job, wintypes.HANDLE(me)):
        raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject (launcher)")
    return job


def check_retry(spec: dict, a, entries: list[dict], logical: str) -> dict | None:
    """None for a first run; a retry record, or SystemExit, for a repetition."""
    started = [e for e in entries if e["event"] == "before" and e.get("logical_key") == logical]
    if not started:
        if a.retry_of:
            raise SystemExit("refused: --retry-of given, but the logical unit never started")
        return None
    if a.approval:
        return {"kind": "approved", "approval": a.approval, "previous": started[-1]["attempt_id"]}
    cls = spec.get("retry_class")
    if not a.retry_of or not a.retry_reason:
        raise SystemExit(
            f"refused: the logical unit {spec['name']} already started; a repetition needs an "
            "approval in #218 (--approval), or a named retry class with --retry-of and "
            "--retry-reason"
        )
    if spec.get("scientific") or spec.get("emits_case_values") or cls not in RETRY_CLASSES:
        raise SystemExit("refused: this unit is not eligible for a retry class")
    orig = next((e for e in started if e["attempt_id"] == a.retry_of), None)
    if orig is None:
        raise SystemExit("refused: --retry-of does not name an attempt of this logical unit")
    after = next(
        (e for e in entries if e["event"] == "after" and e["attempt_id"] == a.retry_of), None
    )
    if after is None:
        raise SystemExit("refused: the original attempt has no after entry (unknown output state)")
    if after.get("case_outputs", 0) != 0:
        raise SystemExit("refused: the original attempt emitted case values")
    if cls == "infra":
        earlier = [e for e in started if (e.get("retry") or {}).get("class") == "infra"]
        if earlier:
            raise SystemExit("refused: an infra retry is allowed once")
        if after.get("status") == "ok":
            raise SystemExit("refused: an infra retry follows a recorded failure only")
    return {"kind": "class", "class": cls, "original": a.retry_of, "reason": a.retry_reason}


def check_order_proof(spec: dict) -> dict | None:
    manifest = spec.get("order_proof")
    if not manifest:
        return None
    blob = committed_sha256(manifest)
    receipt = RECEIPTS / f"{blob}.json"
    if not receipt.exists():
        raise SystemExit(f"refused: no order-proof receipt for {manifest} ({blob[:12]})")
    r = json.loads(receipt.read_text(encoding="utf-8"))
    if not r.get("passed") or r.get("manifest_sha256") != blob:
        raise SystemExit(f"refused: the order-proof receipt for {manifest} did not pass")
    return {
        "manifest": manifest,
        "manifest_sha256": blob,
        "receipt": receipt.name,
        "evidence_commit": r.get("evidence_commit"),
        "ci_run_id": r.get("ci_run_id"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--label", default=None)
    ap.add_argument("--approval", default=None)
    ap.add_argument("--retry-of", default=None)
    ap.add_argument("--retry-reason", default=None)
    ap.add_argument("--bootstrap", action="store_true")
    ap.add_argument("extra", nargs="*")
    a = ap.parse_args()
    job0 = outer_job()
    WORK.mkdir(parents=True, exist_ok=True)
    lock = open(LOCK, "a+b")
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        raise SystemExit("refused: another unit holds the launcher lock") from None

    entries = read_jsonl(LOG)
    me = Path(__file__).resolve().relative_to(ROOT).as_posix()
    launcher_at_head = (
        subprocess.run(["git", "cat-file", "-e", f"HEAD:{me}"], cwd=ROOT, capture_output=True)
    ).returncode == 0
    if a.bootstrap and launcher_at_head:
        raise SystemExit("refused: --bootstrap only while the launcher is not committed at HEAD")
    if not a.bootstrap and not launcher_at_head and not SELFTEST:
        raise SystemExit("refused: the launcher is not committed; use --bootstrap")
    spec_rel = Path(a.spec).as_posix()
    spec = json.loads((ROOT / spec_rel).read_text(encoding="utf-8"))
    if SELFTEST and not spec["name"].startswith("demo"):
        raise SystemExit("refused: the self-test runs the demo specs only")
    files = [spec_rel, me, "docs/validation/v0.5.13/tools/diskbound.py",
             "docs/validation/v0.5.12/tools/jobrun.py", *spec.get("identity", [])]  # fmt: skip
    if a.bootstrap or SELFTEST:
        identity = {Path(f).as_posix(): sha256_file(ROOT / f) for f in files}
    else:
        identity = {Path(f).as_posix(): committed_sha256(f) for f in files}
    net = spec.get("network", False)
    if net is not False and (not isinstance(net, dict) or net.get("kind") not in NETWORK_KINDS):
        raise SystemExit("refused: a unit's network must be false, or github, review or mast")
    env_extra = spec.get("env", {})
    if any(k not in ENV_ALLOWED for k in env_extra):
        raise SystemExit(f"refused: env may set only {ENV_ALLOWED}")
    head = git("rev-parse", "HEAD").decode().strip()
    state = tree_state()
    kind = spec.get("key", "data")
    parts = [spec["name"], a.extra] + ([state] if kind == "tree" else [])
    logical = hashlib.sha256(json.dumps(parts, separators=(",", ":")).encode()).hexdigest()
    attempt = uuid.uuid4().hex

    settled = {e["attempt_id"] for e in entries if e["event"] in ("after", "abandoned")}
    for e in entries:
        if e["event"] == "before" and e["attempt_id"] not in settled:
            append_log({"event": "abandoned", "utc": utc(), "unit": e["unit"],
                        "attempt_id": e["attempt_id"],
                        "note": "a before entry with no after entry, found at the next launch; "
                        "its reservation stays charged"})  # fmt: skip
    entries = read_jsonl(LOG)
    retry = check_retry(spec, a, entries, logical)
    proof = check_order_proof(spec)

    used = charge(entries)
    res = {"cpu_s": 0.0, "disk_bytes": 0, "download_bytes": 0, **spec["reserve"]}
    if net:
        res["download_bytes"] = max(
            res["download_bytes"], int(net.get("inbound_estimate_bytes", 0))
        )
    lc_scan = bool(spec.get("lock_compat_scan"))
    before = diskbound.scan(lock_compat=lc_scan)
    base = next((e for e in entries if e["event"] == "baseline"), None)
    if base is None:
        base = {"event": "baseline", "utc": utc(), "fast_total": before["fast_total"],
                "lock_compat": diskbound.scan(lock_compat=True)["lock_compat"],
                "note": "the phase's disk baseline, taken by its first unit"}  # fmt: skip
        append_log(base)
    grown = [e.get("lock_compat_growth", 0) for e in entries if e["event"] == "after"]
    lc_carried = max([0, *grown])
    o_start = before["fast_total"] - base["fast_total"] + lc_carried
    if used["cpu_s"] + res["cpu_s"] > CAPS["cpu_s"]:
        raise SystemExit("refused: the CPU reservation would pass the phase's cap")
    if used["download_bytes"] + res["download_bytes"] > CAPS["download_bytes"]:
        raise SystemExit("refused: the download reservation would pass the phase's cap")
    if o_start + res["disk_bytes"] > CAPS["disk_bytes"]:
        raise SystemExit("refused: the disk reservation would pass the phase's cap")

    argv = [str(VENV_PY) if x == "{python}" else x for x in spec["argv"]] + list(a.extra)
    shown = ["{python}" if x == str(VENV_PY) else x for x in argv]
    extra_files = {}
    for x in a.extra:
        p = (ROOT / x).resolve()
        if ROOT in p.parents and p.is_file():
            extra_files[Path(x).as_posix()] = sha256_file(p)
    append_log({
        "event": "before", "utc": utc(), "launcher": "launch_v1.py", "unit": spec["name"],
        "label": a.label, "attempt_id": attempt, "logical_key": logical, "key_kind": kind,
        "question": spec["question"], "choices": spec.get("choices"), "argv": shown,
        "network": net, "env": env_extra, "scientific": bool(spec.get("scientific")),
        "emits_case_values": bool(spec.get("emits_case_values")),
        "retry_class": spec.get("retry_class"), "retry": retry, "order_proof": proof,
        "approval_or_trigger": a.approval or spec.get("trigger"), "bootstrap": a.bootstrap,
        "head": head, "tree_state_sha256": state, "identity_sha256": identity,
        "extra_files_sha256": extra_files, "reserve": res, "charged_before": used,
        "o_start": o_start,
    })  # fmt: skip
    run_dir = WORK / "runs" / f"{spec['name']}__{attempt[:12]}"
    (run_dir / "out").mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["REFUTE_RUN_OUT"] = str(run_dir / "out")
    if not net:
        env["UV_OFFLINE"] = "1"
    if SELFTEST:
        env["REFUTE_DEMO_DIR"] = str(WORK / "demo")
    env.update({k: str(v) for k, v in env_extra.items()})
    rec = jobrun.run(
        argv,
        ROOT,
        run_dir / "stdout.txt",
        run_dir / "stderr.txt",
        env=env,
        container=None,
        cpu_limit_s=res["cpu_s"],
        write_limit_bytes=max(0, min(res["disk_bytes"], CAPS["disk_bytes"] - o_start)),
        timeout_s=spec.get("timeout_s", 1800),
    )
    after = diskbound.scan(lock_compat=lc_scan)
    o_end = after["fast_total"] - base["fast_total"] + lc_carried
    lc_growth = lc_carried
    if lc_scan:
        lc_growth = max(lc_carried, after["lock_compat"] - base["lock_compat"])
        o_end += lc_growth - lc_carried
    bound = max(o_start + rec["write_bytes"], o_end)
    ok = rec["exit_code"] == 0 and rec["stopped"] is None
    outputs = {}
    if ok:
        for src_rel, dst_rel in spec.get("outputs", {}).items():
            src = run_dir / "out" / src_rel
            dst = ROOT / dst_rel
            if src.is_file():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
                outputs[dst_rel] = sha256_file(dst)
            else:
                outputs[dst_rel] = None
    transfer = run_dir / "out" / "transfer.json"
    if net and transfer.is_file():
        t = json.loads(transfer.read_text(encoding="utf-8"))
        download = int(t["inbound_bytes"])
        download_basis = t.get("basis", "measured by the unit")
    elif net:
        download = int(net.get("inbound_estimate_bytes", 0))
        download_basis = "the spec's declared conservative estimate"
    else:
        download, download_basis = 0, "offline unit"
    cases_file = run_dir / "out" / "case-outputs.json"
    if cases_file.is_file():
        case_outputs = int(json.loads(cases_file.read_text(encoding="utf-8"))["case_outputs"])
    else:
        case_outputs = int(spec.get("case_outputs", 0))
    total_cpu = max(jobrun._account(job0)["cpu_s"], rec["cpu_s"])
    overrun = [k for k, v in (("cpu", total_cpu > res["cpu_s"]),
                              ("disk", bound - o_start > res["disk_bytes"])) if v]  # fmt: skip
    status = "interrupted" if rec["stopped"] else ("ok" if rec["exit_code"] == 0 else "failed")
    append_log({
        "event": "after", "utc": utc(), "unit": spec["name"], "attempt_id": attempt,
        "logical_key": logical, "status": status, "exit_code": rec["exit_code"],
        "interrupted": rec["stopped"], "overrun": overrun, "unit_cpu_s": round(rec["cpu_s"], 3),
        "cpu_s": round(total_cpu, 3), "wall_s": rec["wall_s"], "processes": rec["processes"],
        "write_bytes": rec["write_bytes"], "read_bytes": rec["read_bytes"],
        "download_bytes": download, "download_basis": download_basis,
        "case_outputs": case_outputs, "o_end": o_end, "lock_compat_growth": lc_growth,
        "disk_bound_bytes": bound, "telemetry_complete": True, "outputs_sha256": outputs,
        "stdout_sha256": sha256_file(run_dir / "stdout.txt"),
        "stderr_sha256": sha256_file(run_dir / "stderr.txt"),
    })  # fmt: skip
    write_ledger(read_jsonl(LOG))
    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
    lock.close()
    summary = {"unit": spec["name"], "status": status, "exit_code": rec["exit_code"],
               "cpu_s": round(total_cpu, 3), "download_bytes": download,
               "write_bytes": rec["write_bytes"], "disk_bound_bytes": bound,
               "run": run_dir.relative_to(ROOT).as_posix()}  # fmt: skip
    print(json.dumps(summary))
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
