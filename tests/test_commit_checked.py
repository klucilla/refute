"""scripts/commit_checked.py: a commit runs only when ruff passes on the staged Python files
(the maintainer's rule of 2026-10-16). Each test works in a new git repository in a
temporary folder; nothing touches this repository and nothing uses the network."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "commit_checked.py"


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    path = tmp_path / "repo"
    path.mkdir()
    for args in (
        ("init", "-q"),
        ("config", "user.name", "test"),
        ("config", "user.email", "test@example.invalid"),
        ("config", "commit.gpgsign", "false"),
    ):
        assert git(path, *args).returncode == 0
    (path / "pyproject.toml").write_text("[tool.ruff]\nline-length = 100\n", encoding="utf-8")
    return path


def commit(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=repo, capture_output=True, text=True, check=False
    )


def commits(repo: Path) -> int:
    out = git(repo, "rev-list", "--count", "HEAD")
    return int(out.stdout.strip()) if out.returncode == 0 else 0


def stage(repo: Path, name: str, text: str) -> None:
    (repo / name).write_text(text, encoding="utf-8")
    assert git(repo, "add", name).returncode == 0


def test_ruff_check_failing_blocks_the_commit(repo):
    stage(repo, "bad.py", "import os\n")  # F401: unused import
    out = commit(repo, "-m", "x")
    assert out.returncode != 0 and "nothing was committed" in out.stderr
    assert commits(repo) == 0


def test_ruff_format_failing_blocks_the_commit(repo):
    stage(repo, "ugly.py", "x=1\n")  # passes ruff check, fails ruff format --check
    out = commit(repo, "-m", "x")
    assert out.returncode != 0 and "format" in out.stderr
    assert commits(repo) == 0


def test_ruff_passing_commits(repo):
    stage(repo, "good.py", "x = 1\n")
    out = commit(repo, "-q", "-m", "good")
    assert out.returncode == 0, out.stdout + out.stderr
    assert "ruff passed on 1 staged Python file" in out.stdout
    assert commits(repo) == 1


def test_only_staged_files_are_checked_and_unstaged_ones_are_not_committed(repo):
    stage(repo, "good.py", "x = 1\n")
    (repo / "bad.py").write_text("import os\n", encoding="utf-8")  # not staged
    out = commit(repo, "-q", "-m", "good")
    assert out.returncode == 0 and commits(repo) == 1
    assert git(repo, "ls-files", "bad.py").stdout == ""


def test_no_python_file_commits_without_ruff(repo):
    stage(repo, "notes.md", "text\n")
    out = commit(repo, "-q", "-F", str(repo / "notes.md"))
    assert out.returncode == 0 and commits(repo) == 1


def test_a_message_from_a_file_and_quiet(repo):
    stage(repo, "good.py", "x = 1\n")
    message = repo.parent / "msg.txt"
    message.write_text('subject with "quotes" and a \\ backslash\n', encoding="utf-8")
    out = commit(repo, "-q", "-F", str(message))
    assert out.returncode == 0 and commits(repo) == 1
    assert git(repo, "log", "-1", "--format=%s").stdout.strip() == message.read_text().strip()


@pytest.mark.parametrize(
    "args",
    [
        ["-a", "-m", "x"],
        ["--all", "-m", "x"],
        ["-m", "x", "bad.py"],
        ["--only", "-m", "x"],
        ["-i", "-m", "x"],
        ["--amend", "-m", "x"],
        ["--no-verify", "-m", "x"],
        ["-q"],
        ["-m"],
    ],
)
def test_options_that_could_commit_unchecked_content_are_refused(repo, args):
    stage(repo, "good.py", "x = 1\n")
    (repo / "bad.py").write_text("import os\n", encoding="utf-8")
    out = commit(repo, *args)
    assert out.returncode == 2 and "nothing was committed" in out.stderr
    assert commits(repo) == 0


def test_a_merge_prepared_with_no_commit_is_committed_with_no_edit(repo):
    stage(repo, "base.py", "x = 1\n")
    assert commit(repo, "-q", "-m", "base").returncode == 0
    assert git(repo, "checkout", "-q", "-b", "side").returncode == 0
    stage(repo, "side.py", "y = 2\n")
    assert commit(repo, "-q", "-m", "side").returncode == 0
    assert git(repo, "checkout", "-q", "-").returncode == 0
    stage(repo, "main.py", "z = 3\n")
    assert commit(repo, "-q", "-m", "main").returncode == 0
    assert git(repo, "merge", "--no-commit", "--no-ff", "side").returncode == 0
    out = commit(repo, "-q", "--no-edit")
    assert out.returncode == 0, out.stdout + out.stderr
    parents = git(repo, "log", "-1", "--format=%P").stdout.split()
    assert len(parents) == 2
