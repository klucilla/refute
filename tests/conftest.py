"""Shared fixtures. Nothing here (or in any test) uses the network: pytest runs with
``--disable-socket`` (pytest-socket), so any network access fails the suite."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import pytest
import yaml

from refute.core.runner import default_workers, run_processes
from refute.packs.tess.synthetic import SCENARIOS, analyze_scenario, fast_plan_dict

# The test trace: with REFUTE_TEST_TRACE set to a file, the full id of every test is
# appended to it before the test starts ("start <id>") and after it ends ("end <id>"),
# each line flushed at once. When a run ends without its JUnit file (pytest-timeout's
# "thread" method on Windows ends the whole process), scripts/junit_counts.py reads the
# trace and names the test that was running (issue #59; Codex review of 2026-10-17).
TRACE = os.environ.get("REFUTE_TEST_TRACE", "")
# The trace belongs to the pytest process that started it: its PID goes into the
# environment, so a pytest that a test starts as a child (it inherits REFUTE_TEST_TRACE)
# leaves the trace alone (Codex review of #148).
TRACE_OWNER = "REFUTE_TEST_TRACE_OWNER"
_active = False


def pytest_sessionstart(session: pytest.Session) -> None:
    # a new run starts a new trace (its folder is created), so the lines of an earlier
    # run that ended early are never read as this one's
    global _active
    if not TRACE or os.environ.get(TRACE_OWNER, str(os.getpid())) != str(os.getpid()):
        return
    os.environ[TRACE_OWNER] = str(os.getpid())
    _active = True
    try:
        Path(TRACE).parent.mkdir(parents=True, exist_ok=True)
        Path(TRACE).write_text("", encoding="utf-8")
    except OSError as error:
        _stop_trace(error)


def _stop_trace(error: OSError) -> None:
    # the trace is a diagnostic aid, not a check: an error writing it turns it off with a
    # warning instead of ending the run
    global _active
    _active = False
    sys.stderr.write(f"test trace turned off: {type(error).__name__}\n")


def _trace(line: str) -> None:
    if not (_active and TRACE):
        return
    try:
        with open(TRACE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            fh.flush()
    except OSError as error:
        _stop_trace(error)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logstart(nodeid: str, location: tuple) -> None:
    _trace(f"start {nodeid}")


@pytest.hookimpl(trylast=True)
def pytest_runtest_logfinish(nodeid: str, location: tuple) -> None:
    _trace(f"end {nodeid}")


# Work folders under .cache/ (#197). Some tests need a folder inside the project (a harness
# that writes only there, a script that resolves paths from the project root); each gets
# .cache/test-<name>/<uuid> from cache_test_dir(), and the folder is removed after the test
# (or, for one created by a wider-scoped fixture, at the end of the session), with a guard
# that the path is exactly of that form. The test-<name> folder is removed when it is empty.
CACHE = Path(__file__).resolve().parents[1] / ".cache"
_cache_dirs: list[Path] = []


def cache_test_dir(name: str) -> Path:
    """A fresh path ``.cache/test-<name>/<uuid>`` (not created), removed after the test."""
    if not name or not all(c.isalnum() or c in "-_" for c in name):
        raise ValueError(f"invalid cache test folder name: {name!r}")
    path = CACHE / f"test-{name}" / uuid.uuid4().hex
    _cache_dirs.append(path)
    return path


def _writable(function, path, _exc) -> None:
    # a read-only file (git objects, for example) cannot be removed on Windows
    os.chmod(path, stat.S_IWRITE)
    function(path)


def remove_cache_test_dir(path: Path) -> None:
    """Remove one folder made by :func:`cache_test_dir`; refuse any other path."""
    base = CACHE.resolve()
    target = path.resolve()
    group = target.parent
    if (
        group.parent != base
        or not group.name.startswith("test-")
        or len(target.name) != 32
        or not all(c in "0123456789abcdef" for c in target.name)
    ):
        raise RuntimeError(f"refusing to remove {target}: not .cache/test-<name>/<uuid>")
    for attempt in range(5):
        if not target.exists():
            break
        try:
            shutil.rmtree(target, onexc=_writable)
        except OSError:
            # a child process may still hold a file for a moment on Windows
            time.sleep(0.2 * (attempt + 1))
    try:
        group.rmdir()
    except OSError:
        pass  # not empty: another test's folder is still there


@pytest.fixture(autouse=True)
def _remove_cache_test_dirs():
    start = len(_cache_dirs)
    yield
    while len(_cache_dirs) > start:
        remove_cache_test_dir(_cache_dirs.pop())


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    while _cache_dirs:
        remove_cache_test_dir(_cache_dirs.pop())


SOURCE = {
    "name": "synthetic test data",
    "url": "synthetic://refute-tests",
    "retrieved_utc": "2026-10-07T00:00:00Z",
}


@pytest.fixture(scope="session")
def scenario_results() -> dict[str, Any]:
    """Full analyses of every synthetic scenario, computed once in parallel processes."""
    workers = max(1, min(len(SCENARIOS), default_workers()))
    results = run_processes(analyze_scenario, list(SCENARIOS), workers)
    return dict(zip(SCENARIOS, results, strict=True))


def git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        [
            "git",
            "-c",
            "user.name=Refute Test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.autocrlf=false",
            *args,
        ],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    return repo


def target_entry(tic: int, kind: str, period: float | None, name: str | None = None) -> dict:
    return {
        "key": f"TIC-{tic}",
        "tic_id": tic,
        "kind": kind,
        "name": name or f"synthetic {kind} {tic}",
        "published": {"period_days": period},
        "source": dict(SOURCE),
    }


def write_yaml(path: Path, data: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(yaml.safe_dump(data, sort_keys=False).encode("utf-8"))
    return path


def replicate_claim(targets: list[dict], **extra: Any) -> dict:
    claim = {
        "schema_version": 1,
        "id": "synthetic-replicate",
        "kind": "replicate",
        "pack": "tess",
        "title": "Synthetic replication",
        "hypothesis": "The injected transit is recovered and survives the gauntlet.",
        "created": "2026-10-07",
        "authors": ["Refute test suite"],
        "targets": targets,
        "test_plan": fast_plan_dict(),
    }
    claim.update(extra)
    return claim


def calibration_claim(planets: int, fps: int, **criteria: Any) -> dict:
    pass_criteria = {
        "period_tolerance": 0.001,
        "expected_planets": planets,
        "min_recovered_planets": planets,
        "expected_false_positives": fps,
        "min_flagged_false_positives": fps,
        "max_refuted_planets": 0,
    }
    pass_criteria.update(criteria)
    return {
        "schema_version": 1,
        "id": "synthetic-calibration",
        "kind": "calibration",
        "pack": "tess",
        "title": "Synthetic calibration",
        "hypothesis": "Refute recovers the synthetic planets and flags the synthetic binaries.",
        "created": "2026-10-07",
        "authors": ["Refute test suite"],
        "attachments": [{"path": "targets.yaml", "role": "targets"}],
        "test_plan": fast_plan_dict(),
        "pass_criteria": pass_criteria,
    }


def targets_file(targets: list[dict]) -> dict:
    return {
        "schema": "refute-tess-targets-1",
        "generated_utc": "2026-10-07T00:00:00Z",
        "generator": "refute test suite",
        "selection": {"note": "synthetic"},
        "targets": targets,
    }
