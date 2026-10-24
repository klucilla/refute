"""The command guard's hook in .claude/settings.json runs on every platform: it takes the project's
virtual environment at .venv/Scripts/python.exe (Windows) or .venv/bin/python (elsewhere),
whichever exists, and blocks the command (exit 2) when neither exists (maintainer's decision of
2026-10-24). The hook's command is run as Claude Code runs it, with bash; no network."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _bash() -> str | None:
    """Git's bash on Windows (the one Claude Code runs hooks with; ``bash`` on the PATH can be
    WSL's), ``bash`` elsewhere."""
    if os.name != "nt":
        return shutil.which("bash")
    git = shutil.which("git")
    if git is None:
        return None
    for parent in Path(git).resolve().parents:
        candidate = parent / "bin" / "bash.exe"
        if candidate.is_file():
            return str(candidate)
    return None


BASH = _bash()
pytestmark = pytest.mark.skipif(BASH is None, reason="no bash (Git's bash on Windows)")


def _hook() -> dict:
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    (entry,) = settings["hooks"]["PreToolUse"]
    (hook,) = entry["hooks"]
    return hook


def _run(project: Path, command: str = "git status") -> subprocess.CompletedProcess:
    hook = _hook()
    assert hook["shell"] == "bash" and hook["onFailure"] == "block"
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    env = {**os.environ, "CLAUDE_PROJECT_DIR": project.as_posix()}
    return subprocess.run(
        [BASH, "-c", hook["command"]], input=payload, capture_output=True, text=True, env=env,
        timeout=60,
    )  # fmt: skip


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / ".claude" / "hooks").mkdir(parents=True)
    (project / ".claude" / "hooks" / "command_guard.py").write_text("", encoding="utf-8")
    return project


def test_no_virtual_environment_blocks(tmp_path):
    done = _run(_project(tmp_path))
    assert done.returncode == 2
    assert "blocked" in done.stderr


def test_a_posix_virtual_environment_is_used(tmp_path):
    project = _project(tmp_path)
    python = project / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8", newline="\n")
    python.chmod(0o755)
    done = _run(project)
    assert done.returncode == 0, done.stderr


def test_the_guard_allows_in_this_project():
    done = _run(ROOT)
    assert done.returncode == 0, done.stderr


def test_the_guard_still_blocks_through_the_wrapper():
    done = _run(ROOT, "sed -n 1p README.md")  # a command the guard refuses
    assert done.returncode == 2


def test_a_guard_that_cannot_run_blocks(tmp_path):
    project = _project(tmp_path)
    python = project / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8", newline="\n")  # a crash
    python.chmod(0o755)
    done = _run(project)
    assert done.returncode == 2 and "could not run" in done.stderr
