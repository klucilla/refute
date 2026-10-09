"""Command-line interface: ``refute``.

Exit codes are documented in ``docs/cli.md``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer

import refute
from refute.core.claim import ClaimError, load_claim
from refute.core.dossier import check_dossier, write_archive
from refute.core.lock import LockError, create_lock, verify_claim
from refute.core.pack import PackError, available_packs, load_pack
from refute.core.review import ReviewError, attach_review

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Refute: find signals, try to kill them, keep what survives.",
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"refute {refute.__version__}")
        raise typer.Exit(0)


@app.callback()
def _root(
    version: Annotated[
        bool,
        typer.Option("--version", callback=_version_callback, is_eager=True, help="Show version."),
    ] = False,
) -> None:
    """Refute command-line interface."""


@app.command("packs")
def packs_command() -> None:
    """List installed domain packs."""
    packs = available_packs()
    if not packs:
        typer.echo("no domain packs installed")
        raise typer.Exit(1)
    for name, target in sorted(packs.items()):
        try:
            pack = load_pack(name)
            typer.echo(f"{name} {pack.version}: {pack.description}")
        except PackError as exc:
            typer.echo(f"{name} ({target}): ERROR {exc}")


@app.command("lock")
def lock_command(
    claim: Annotated[Path, typer.Argument(help="Path to claim.yaml")],
    force: Annotated[
        bool, typer.Option("--force", help="Re-lock an already locked claim.")
    ] = False,
    reason: Annotated[
        str | None, typer.Option("--reason", help="Why the claim is re-locked (with --force).")
    ] = None,
) -> None:
    """Lock a claim: hash the claim, its attachments and the code; record it in LOCK_HISTORY.md."""
    try:
        lock = create_lock(claim, force=force, reason=reason)
    except LockError as exc:
        typer.echo(f"lock refused: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"locked {lock['claim_path']} ({lock['claim_id']})")
    typer.echo(f"  claim_sha256: {lock['claim_sha256']}")
    for attachment in lock["attachments"]:
        typer.echo(f"  attachment {attachment['path']}: {attachment['sha256']}")
    typer.echo(f"  code_sha256:  {lock['code']['sha256']} ({len(lock['code']['files'])} files)")
    typer.echo(f"  git_commit:   {lock['git_commit']} (dirty: {lock['git_dirty']})")
    typer.echo(f"  locked_at:    {lock['locked_at_utc']}")


@app.command("verify")
def verify_command(
    claim: Annotated[Path, typer.Argument(help="Path to claim.yaml")],
    as_json: Annotated[bool, typer.Option("--json", help="Print the result as JSON.")] = False,
) -> None:
    """Verify a locked claim. Exit code 0 PASS, 1 FAIL, 2 TAMPERED."""
    result = verify_claim(claim)
    if as_json:
        typer.echo(json.dumps(result.to_dict(), indent=2))
    else:
        typer.echo(result.status.value)
        for message in result.messages:
            typer.echo(f"  {message}")
    raise typer.Exit(result.exit_code)


@app.command("fetch")
def fetch_command(
    claim: Annotated[Path, typer.Argument(help="Path to claim.yaml")],
    target: Annotated[
        list[str] | None, typer.Option("--target", help="Only this target (repeatable).")
    ] = None,
    cache_dir: Annotated[Path | None, typer.Option("--cache-dir")] = None,
) -> None:
    """Download and cache the public data of a claim's targets (network)."""
    from refute.core.run import _fetch_one, _select_targets, default_cache_dir

    try:
        loaded = load_claim(claim)
    except ClaimError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    selected, missing = _select_targets(loaded, target)
    if missing:
        typer.echo(f"unknown target(s): {', '.join(missing)}", err=True)
        raise typer.Exit(1)
    from refute.core.run import RunOutcome, prepare_claim_data

    cache = cache_dir or default_cache_dir()
    prepared = prepare_claim_data(loaded.pack, loaded, cache, offline=False)
    if isinstance(prepared, RunOutcome):
        typer.echo(prepared.messages[0], err=True)
        raise typer.Exit(1)
    for message in prepared:
        typer.echo(message)
    failures = 0
    for item in selected:
        key = loaded.pack.schema.target_key(item)
        error = _fetch_one((loaded.pack, item, loaded.claim.test_plan, cache))
        typer.echo(f"{key}: {'ok' if error is None else 'FAILED ' + error}")
        failures += error is not None
    raise typer.Exit(1 if failures else 0)


def _run(
    mode: str,
    claim: Path,
    target: list[str] | None,
    out: Path,
    workers: int | None,
    offline: bool,
    run_id: str | None,
    cache_dir: Path | None,
) -> None:
    from refute.core.run import execute_run

    if workers is not None and workers < 1:
        typer.echo("--workers must be >= 1", err=True)
        raise typer.Exit(1)
    outcome = execute_run(
        claim,
        mode=mode,
        targets=target,
        out_dir=out,
        workers=workers,
        offline=offline,
        run_id=run_id,
        cache_dir=cache_dir,
    )
    for message in outcome.messages:
        _echo_safely(message, err=outcome.exit_code != 0)
    if outcome.run_dir is not None:
        _echo_safely((outcome.run_dir / "summary.md").read_text(encoding="utf-8"))
        _echo_safely(f"dossiers written to {outcome.run_dir}")
    raise typer.Exit(outcome.exit_code)


def _echo_safely(text: str, err: bool = False) -> None:
    """Print without letting a broken or closed output stream fail a completed run.

    In v0.1 the CLI crashed with "I/O operation on closed file" while printing the
    summary of a run that had already written every dossier (issue #1). The exit
    code reports whether the run completed, so printing must never change it.
    """
    try:
        typer.echo(text, err=err)
    except (ValueError, OSError):
        try:
            stream = sys.__stderr__ if err else sys.__stdout__
            if stream is not None and not stream.closed:
                stream.write(text + chr(10))
                stream.flush()
        except (ValueError, OSError):
            pass


TargetOpt = Annotated[
    list[str] | None, typer.Option("--target", help="Only this target, e.g. TIC-123 (repeatable).")
]
OutOpt = Annotated[Path, typer.Option("--out", help="Output directory for dossiers.")]
WorkersOpt = Annotated[
    int | None, typer.Option("--workers", help="Analysis processes (default: CPU count - 2).")
]
OfflineOpt = Annotated[bool, typer.Option("--offline", help="Use cached data only; no network.")]
RunIdOpt = Annotated[str | None, typer.Option("--run-id", help="Name of the run directory.")]
CacheOpt = Annotated[Path | None, typer.Option("--cache-dir", help="Data cache directory.")]


@app.command("replicate")
def replicate_command(
    claim: Annotated[Path, typer.Argument(help="Path to a locked replicate claim.")],
    target: TargetOpt = None,
    out: OutOpt = Path("dossiers"),
    workers: WorkersOpt = None,
    offline: OfflineOpt = False,
    run_id: RunIdOpt = None,
    cache_dir: CacheOpt = None,
) -> None:
    """Re-derive a published claim from public data, then attack it."""
    _run("replicate", claim, target, out, workers, offline, run_id, cache_dir)


@app.command("calibrate")
def calibrate_command(
    claim: Annotated[Path, typer.Option("--claim", help="Locked calibration claim.")] = Path(
        "calibration/self_claim.yaml"
    ),
    target: TargetOpt = None,
    out: OutOpt = Path("dossiers"),
    workers: WorkersOpt = None,
    offline: OfflineOpt = False,
    run_id: RunIdOpt = None,
    cache_dir: CacheOpt = None,
) -> None:
    """Run the locked calibration claim on every calibration target."""
    _run("calibrate", claim, target, out, workers, offline, run_id, cache_dir)


@app.command("check-dossier")
def check_dossier_command(
    dossier: Annotated[Path, typer.Argument(help="Dossier directory to check.")],
    against: Annotated[
        Path | None, typer.Option("--against", help="Original dossier to compare with.")
    ] = None,
) -> None:
    """Verify a dossier's MANIFEST and optionally compare it with an original dossier."""
    result = check_dossier(dossier, against)
    for problem in result.integrity_problems:
        typer.echo(f"integrity: {problem}")
    for difference in result.differences:
        typer.echo(f"difference: {difference}")
    if result.ok:
        message = "OK: manifest intact"
        if against is not None:
            message += "; key results reproduced"
        typer.echo(message)
    raise typer.Exit(0 if result.ok else 1)


@app.command("archive")
def archive_command(
    run_dir: Annotated[Path, typer.Argument(help="Run directory containing dossiers.")],
    out: Annotated[Path | None, typer.Option("--out", help="Zip file to write.")] = None,
) -> None:
    """Write a deterministic zip of a run directory and its SHA-256."""
    target = out or run_dir.with_name(run_dir.name + ".zip")
    try:
        path, digest = write_archive(run_dir, target)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"{digest}  {path}")


review_app = typer.Typer(no_args_is_help=True, help="Independent reviewer reports.")
app.add_typer(review_app, name="review")


@review_app.command("attach")
def review_attach_command(
    dossier: Annotated[Path, typer.Argument(help="Dossier directory.")],
    report: Annotated[Path, typer.Argument(help="Reviewer report (Markdown).")],
    reviewer: Annotated[str, typer.Option("--reviewer", help="Reviewer id, e.g. opus-1.")],
    model: Annotated[str, typer.Option("--model", help="Model that wrote the report.")],
) -> None:
    """Attach a reviewer report to a dossier. The verdict and analysis files never change."""
    try:
        entry = attach_review(dossier, report, reviewer=reviewer, model=model)
    except ReviewError as exc:
        typer.echo(f"review refused: {exc}", err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"attached {entry['file']} (sha256 {entry['sha256']})")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
