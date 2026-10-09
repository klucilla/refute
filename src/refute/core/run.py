"""Run orchestration shared by ``refute replicate`` and ``refute calibrate``.

1. Verify the lock (claim, attachments, code). TAMPERED aborts with exit code 2.
2. Fetch data for every target (network, one target at a time), unless ``--offline``.
3. Analyze every target in parallel worker processes (offline, CPU-bound).
   Each worker writes one complete dossier.
4. Write the run summary (and, for calibration claims, evaluate the claim).
"""

from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import refute
from refute.core.claim import ClaimError, LoadedClaim, load_claim
from refute.core.codehash import CodeHashError, git_state, project_root
from refute.core.dossier import DossierWriter
from refute.core.environment import snapshot
from refute.core.io import dumps_json, write_json, write_text
from refute.core.lock import VerifyStatus, lock_path_for, verify_claim
from refute.core.pack import load_pack
from refute.core.runner import default_workers, run_processes


def default_cache_dir() -> Path:
    try:
        return project_root() / ".cache"
    except CodeHashError:
        return Path.cwd() / ".cache"


@dataclass(frozen=True)
class TargetTask:
    """Everything one worker process needs to produce one dossier (picklable)."""

    pack_name: str
    target: dict[str, Any]
    target_key: str
    test_plan: dict[str, Any]
    context: dict[str, Any]
    cache_dir: str
    dossier_dir: str
    claim_filename: str
    claim_bytes: bytes
    lock_bytes: bytes
    integrity: dict[str, Any]
    attachments: tuple[tuple[str, bytes], ...]
    environment: dict[str, Any]
    fetch_error: str | None = None


def reproduce_markdown(task: TargetTask) -> str:
    ctx = task.context
    mode = ctx["mode"]
    claim_ref = ctx.get("claim_path_in_repo") or task.claim_filename
    claim_arg = f"--claim {claim_ref}" if mode == "calibrate" else claim_ref
    run_commit = ctx.get("run_git_commit")
    checkout = (
        f"git checkout {run_commit}"
        if run_commit
        else "# (the run was not made from a git checkout; use a source tree whose code hash "
        f"is {ctx['code_sha256']})"
    )
    key = task.target_key
    return f"""# Reproduce this dossier

These commands re-run the analysis of `{key}` from scratch in a fresh clone of the
Refute repository and compare the new result with this dossier.

- Claim: `{ctx["claim_id"]}` (`{claim_ref}`), claim SHA-256 `{ctx["claim_sha256"]}`
- Code SHA-256 (refute-code-1): `{ctx["code_sha256"]}`
- Commit recorded in the lock (code, claim and attachments as locked):
  `{ctx.get("lock_git_commit") or "none"}`
- Commit checked out when this dossier was produced: `{run_commit or "none"}`
  (it contains the lock file; `refute verify` proves its code hash equals the
  locked code hash)

```bash
git clone {refute.__repository__}.git refute
cd refute
{checkout}
uv sync --frozen
uv run refute verify {claim_ref}
uv run refute {mode} {claim_arg} --target {key} --out repro --run-id repro --workers 1
uv run refute check-dossier repro/repro/{key} --against <this dossier>
```

Replace `<this dossier>` with the path of the folder that contains this
`REPRODUCE.md` (wherever the dossier archive was unpacked).

`refute {mode}` downloads the input data from the public archive when it is not
already cached. `check-dossier` verifies both manifests, requires identical input
data hashes, identical verdict and test statuses, and key numeric results equal
within a relative tolerance of 1e-6.
"""


def run_target_task(task: TargetTask) -> dict[str, Any]:
    """Analyze one target and write its complete dossier. Never raises for analysis errors."""
    pack = load_pack(task.pack_name)
    writer = DossierWriter(task.dossier_dir)
    writer.write_bytes("claim.yaml", task.claim_bytes)
    writer.write_bytes("claim.lock.json", task.lock_bytes)
    writer.write_json("integrity.json", task.integrity)
    writer.write_json("target.json", task.target)
    for name, content in task.attachments:
        writer.write_bytes(f"attachments/{name}", content)

    if task.fetch_error is not None:
        result = pack.analyzer.error_result(
            task.target, f"data fetch failed: {task.fetch_error}", task.context
        )
    else:
        try:
            data = pack.adapter.load(task.target, task.test_plan, Path(task.cache_dir))
            result = pack.analyzer.analyze(task.target, data, task.test_plan, task.context, writer)
        except Exception:  # noqa: BLE001 - any failure is recorded in the dossier
            result = pack.analyzer.error_result(task.target, traceback.format_exc(), task.context)

    try:
        pack.exporter.export(result, writer.root / "export")
    except Exception:  # noqa: BLE001
        writer.write_text("export/EXPORT_ERROR.txt", traceback.format_exc())

    writer.write_json("verdict.json", result)
    writer.write_text("report.md", pack.analyzer.report(result, task.context))
    writer.write_json("environment/environment.json", task.environment["info"])
    writer.write_text("environment/requirements.txt", task.environment["requirements_txt"])
    if task.environment.get("uv_lock") is not None:
        writer.write_text("environment/uv.lock", task.environment["uv_lock"])
    writer.write_text("REPRODUCE.md", reproduce_markdown(task))
    writer.finalize()
    return result


FETCH_ATTEMPTS = 3
FETCH_RETRY_SECONDS = 10.0


def _fetch_one(args: tuple[Any, dict[str, Any], dict[str, Any], Path]) -> str | None:
    """Fetch one target's data, retrying transient network failures. Returns an error or None."""
    pack, target, test_plan, cache_dir = args
    error = None
    for attempt in range(1, FETCH_ATTEMPTS + 1):
        try:
            pack.adapter.fetch(target, test_plan, cache_dir)
        except Exception as exc:  # noqa: BLE001 - recorded per target
            error = f"{type(exc).__name__}: {exc} (attempt {attempt} of {FETCH_ATTEMPTS})"
            if attempt < FETCH_ATTEMPTS:
                time.sleep(FETCH_RETRY_SECONDS * attempt)
        else:
            return None
    return error


@dataclass
class RunOutcome:
    exit_code: int
    messages: list[str] = field(default_factory=list)
    run_dir: Path | None = None
    summary: dict[str, Any] | None = None
    results: list[dict[str, Any]] = field(default_factory=list)


def _utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _select_targets(
    loaded: LoadedClaim, wanted: list[str] | None
) -> tuple[list[dict[str, Any]], list[str]]:
    schema = loaded.pack.schema
    targets = schema.targets_for_run(loaded)
    if not wanted:
        return targets, []
    normalized = {w.strip().upper().replace(" ", "-") for w in wanted}
    chosen = [t for t in targets if schema.target_key(t).upper() in normalized]
    found = {schema.target_key(t).upper() for t in chosen}
    missing = sorted(normalized - found)
    return chosen, missing


def execute_run(
    claim_path: Path | str,
    *,
    mode: str,
    targets: list[str] | None = None,
    out_dir: Path | str = "dossiers",
    workers: int | None = None,
    offline: bool = False,
    run_id: str | None = None,
    cache_dir: Path | str | None = None,
    code_root: Path | None = None,
) -> RunOutcome:
    """Verify, fetch, analyze and summarize. ``mode`` is ``replicate`` or ``calibrate``."""
    started = datetime.now(UTC).isoformat(timespec="seconds")
    claim_file = Path(claim_path).resolve()

    integrity = verify_claim(claim_file, code_root=code_root)
    if integrity.status is not VerifyStatus.PASS:
        return RunOutcome(
            exit_code=integrity.exit_code,
            messages=[f"refute verify: {integrity.status.value}", *integrity.messages],
        )
    try:
        loaded = load_claim(claim_file)
    except ClaimError as exc:
        return RunOutcome(exit_code=1, messages=[str(exc)])

    expected_kind = {"calibrate": "calibration", "replicate": "replicate"}[mode]
    if loaded.claim.kind != expected_kind:
        return RunOutcome(
            exit_code=1,
            messages=[
                f"`refute {mode}` needs a claim of kind '{expected_kind}', "
                f"got '{loaded.claim.kind}'"
            ],
        )

    selected, missing = _select_targets(loaded, targets)
    if missing:
        return RunOutcome(exit_code=1, messages=[f"unknown target(s): {', '.join(missing)}"])
    if not selected:
        return RunOutcome(exit_code=1, messages=["the claim has no targets to run"])

    pack = loaded.pack
    test_plan = loaded.claim.test_plan
    cache = Path(cache_dir) if cache_dir is not None else default_cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    claim_data_messages = prepare_claim_data(pack, loaded, cache, offline)
    if isinstance(claim_data_messages, RunOutcome):
        return claim_data_messages
    lock = integrity.lock or {}
    run_state = git_state(claim_file.parent)
    claim_sha = lock["claim_sha256"]
    run_name = run_id or f"{_utc_stamp()}-{claim_sha[:8]}"
    run_dir = Path(out_dir).resolve() / run_name
    run_dir.mkdir(parents=True, exist_ok=True)

    fetch_errors: list[str | None]
    if offline:
        fetch_errors = [None] * len(selected)
    else:
        # One target at a time: concurrent downloads truncated files in v0.1 (issue #1).
        fetch_errors = [_fetch_one((pack, t, test_plan, cache)) for t in selected]

    env = snapshot(code_root or _safe_project_root())
    context = {
        "mode": mode,
        "run_id": run_name,
        "claim_id": loaded.claim.id,
        "claim_kind": loaded.claim.kind,
        "claim_title": loaded.claim.title,
        "hypothesis": loaded.claim.hypothesis,
        "definitions": loaded.claim.definitions,
        "pass_criteria": loaded.claim.pass_criteria,
        "claim_sha256": claim_sha,
        "code_sha256": lock["code"]["sha256"],
        "lock_git_commit": lock.get("git_commit"),
        "locked_at_utc": lock.get("locked_at_utc"),
        "claim_path_in_repo": lock.get("claim_path_in_repo"),
        "run_git_commit": run_state.commit,
        "run_git_dirty": run_state.dirty,
        "refute_version": refute.__version__,
        "pack": f"{pack.name} {pack.version}",
        "attachments": [{"path": a.path, "role": a.role} for a in loaded.claim.attachments],
        "cache_dir": str(cache),
    }
    attachments = tuple(
        (a.path, loaded.attachment_path(a).read_bytes()) for a in loaded.claim.attachments
    )
    tasks = [
        TargetTask(
            pack_name=pack.name,
            target=target,
            target_key=pack.schema.target_key(target),
            test_plan=test_plan,
            context=context,
            cache_dir=str(cache),
            dossier_dir=str(run_dir / pack.schema.target_key(target)),
            claim_filename=claim_file.name,
            claim_bytes=claim_file.read_bytes(),
            lock_bytes=lock_path_for(claim_file).read_bytes(),
            integrity=integrity.to_dict(),
            attachments=attachments,
            environment=env,
            fetch_error=error,
        )
        for target, error in zip(selected, fetch_errors, strict=True)
    ]
    n_workers = workers if workers is not None else default_workers()
    results = run_processes(run_target_task, tasks, n_workers)

    complete = not targets
    if loaded.claim.kind == "calibration":
        summary = pack.calibrator.evaluate(loaded, results, complete)
        summary_md = pack.calibrator.summary_markdown(summary)
    else:
        summary = _replicate_summary(loaded, results)
        summary_md = _replicate_summary_markdown(summary)
    summary["run"] = {
        "run_id": run_name,
        "started_utc": started,
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "workers": n_workers,
        "offline": offline,
        "targets_requested": targets or "all",
        "claim_sha256": claim_sha,
        "code_sha256": lock["code"]["sha256"],
        "lock_git_commit": lock.get("git_commit"),
        "run_git_commit": run_state.commit,
        "run_git_dirty": run_state.dirty,
        "environment": env["info"],
    }
    write_json(run_dir / "summary.json", summary)
    write_text(run_dir / "summary.md", summary_md + _run_footer(summary["run"]))
    return RunOutcome(exit_code=0, run_dir=run_dir, summary=summary, results=results)


def prepare_claim_data(
    pack: Any, loaded: LoadedClaim, cache: Path, offline: bool
) -> list[str] | RunOutcome:
    """Run the pack's optional claim-level preparation; any failure stops the run."""
    prepare = getattr(pack.adapter, "prepare_claim_data", None)
    if prepare is None:
        return []
    try:
        return list(prepare(loaded, cache, offline))
    except Exception as exc:  # noqa: BLE001 - reported, the run stops before any analysis
        return RunOutcome(exit_code=1, messages=[f"claim data check failed: {exc}"])


def _safe_project_root() -> Path | None:
    try:
        return project_root()
    except CodeHashError:
        return None


def _run_footer(run: dict[str, Any]) -> str:
    return (
        "\n## Run\n\n"
        f"- Run id: `{run['run_id']}`\n"
        f"- Started / finished (UTC): {run['started_utc']} / {run['finished_utc']}\n"
        f"- Workers: {run['workers']}, offline: {str(run['offline']).lower()}\n"
        f"- Claim SHA-256: `{run['claim_sha256']}`\n"
        f"- Code SHA-256: `{run['code_sha256']}`\n"
        f"- Lock commit: `{run['lock_git_commit']}`; run commit: `{run['run_git_commit']}` "
        f"(dirty: {run['run_git_dirty']})\n"
        f"- Python {run['environment']['python_version']} on {run['environment']['platform']}\n"
    )


def _replicate_summary(loaded: LoadedClaim, results: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [
        {
            "target": r.get("target_key"),
            "verdict": r.get("verdict"),
            "status": r.get("status"),
            "tests": {t["name"]: t["status"] for t in r.get("tests", [])},
        }
        for r in results
    ]
    return {"schema": "refute-run-summary-1", "claim_id": loaded.claim.id, "targets": rows}


def _replicate_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [f"# Run summary: {summary['claim_id']}", "", "| Target | Verdict | Status |"]
    lines.append("|---|---|---|")
    for row in summary["targets"]:
        lines.append(f"| {row['target']} | {row['verdict']} | {row['status']} |")
    lines.append("")
    lines.append(dumps_json({"tests": {r["target"]: r["tests"] for r in summary["targets"]}}))
    return "\n".join(lines)
