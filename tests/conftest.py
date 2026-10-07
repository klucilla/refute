"""Shared fixtures. Nothing here (or in any test) uses the network: pytest runs with
``--disable-socket`` (pytest-socket), so any network access fails the suite."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from refute.core.runner import default_workers, run_processes
from refute.packs.tess.synthetic import SCENARIOS, analyze_scenario, fast_plan_dict

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
