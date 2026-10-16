"""scripts/commit_checked.py: a commit runs only when ruff passes on the staged Python files
(the maintainer's rule of 2026-10-16). Each test works in a new git repository in a
temporary folder; nothing touches this repository and nothing uses the network."""

import importlib.util
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
    assert git(path, "add", "pyproject.toml").returncode == 0
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
    assert "ruff passed on 1 of 1 staged Python file(s) (0 in folders CI excludes)" in out.stdout
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


LONG_LINE = "x = " + "1 + " * 21 + "1\n"  # 90 columns: fine at 100, too long at 80


def test_ruff_reads_the_staged_bytes_not_the_work_tree(repo):
    """Codex review: a failing staged file with a passing work tree is refused."""
    stage(repo, "mod.py", "import os\n")
    (repo / "mod.py").write_text("x = 1\n", encoding="utf-8")
    out = commit(repo, "-m", "x")
    assert out.returncode != 0 and "staged mod.py" in out.stderr
    assert commits(repo) == 0


def test_a_partial_commit_of_a_passing_staged_file_commits_the_staged_bytes(repo):
    stage(repo, "mod.py", "x = 1\n")
    (repo / "mod.py").write_text("import os\n", encoding="utf-8")  # not staged
    out = commit(repo, "-q", "-m", "x")
    assert out.returncode == 0, out.stdout + out.stderr
    assert git(repo, "show", "HEAD:mod.py").stdout == "x = 1\n"


def test_a_clean_filter_cannot_hide_the_committed_bytes(repo, tmp_path):
    """Codex review: with a clean filter the work tree and the blob differ although
    ``git hash-object`` of the work tree equals the blob; ruff reads the blob."""
    filt = tmp_path / "clean.py"
    filt.write_text(
        "import sys\nsys.stdin.buffer.read()\nsys.stdout.buffer.write(b'import os\\n')\n",
        encoding="utf-8",
    )
    command = f'"{Path(sys.executable).as_posix()}" "{filt.as_posix()}"'
    assert git(repo, "config", "filter.bad.clean", command).returncode == 0
    stage(repo, ".gitattributes", "mod.py filter=bad\n")
    stage(repo, "mod.py", "x = 1\n")
    assert git(repo, "show", ":mod.py").stdout == "import os\n"
    out = commit(repo, "-m", "x")
    assert out.returncode != 0 and "staged mod.py" in out.stderr
    assert commits(repo) == 0


def test_an_extended_configuration_must_be_staged_too(repo):
    stage(repo, "ruff.toml", 'extend = "base.toml"\n')
    stage(repo, "base.toml", "line-length = 100\n")
    stage(repo, "long.py", LONG_LINE)
    (repo / "base.toml").write_text("line-length = 80\n", encoding="utf-8")
    out = commit(repo, "-m", "x")
    assert out.returncode == 2 and "base.toml" in out.stderr
    assert commits(repo) == 0


def test_an_extend_chain_through_a_file_named_like_pyproject_is_followed(repo):
    """Codex review: base-pyproject.toml holds top-level options, so its extend counts."""
    stage(repo, "ruff.toml", 'extend = "base-pyproject.toml"\n')
    stage(repo, "base-pyproject.toml", 'extend = "rules.toml"\n')
    stage(repo, "rules.toml", "line-length = 100\n")
    stage(repo, "good.py", "x = 1\n")
    (repo / "rules.toml").write_text("line-length = 80\n", encoding="utf-8")
    out = commit(repo, "-m", "x")
    assert out.returncode == 2 and "rules.toml" in out.stderr
    assert commits(repo) == 0


def test_an_extended_configuration_outside_the_repository_is_refused(repo):
    stage(repo, "ruff.toml", 'extend = "../base.toml"\n')
    stage(repo, "good.py", "x = 1\n")
    out = commit(repo, "-m", "x")
    assert out.returncode == 2 and "outside the repository" in out.stderr
    assert commits(repo) == 0


def test_a_ruff_other_than_the_locked_one_is_refused(repo):
    stage(repo, "uv.lock", 'version = 1\n\n[[package]]\nname = "ruff"\nversion = "0.0.1"\n')
    stage(repo, "good.py", "x = 1\n")
    out = commit(repo, "-m", "x")
    assert out.returncode == 2 and "uv.lock" in out.stderr
    assert commits(repo) == 0


def test_an_unstaged_ruff_configuration_is_refused(repo):
    stage(repo, "long.py", LONG_LINE)
    (repo / "pyproject.toml").write_text("[tool.ruff]\nline-length = 80\n", encoding="utf-8")
    out = commit(repo, "-m", "x")
    assert out.returncode == 2 and "pyproject.toml" in out.stderr
    assert commits(repo) == 0


def test_an_untracked_ruff_configuration_in_a_parent_folder_is_refused(repo):
    (repo / "pkg").mkdir()
    stage(repo, "pkg/long.py", LONG_LINE)
    (repo / "pkg" / "ruff.toml").write_text("line-length = 80\n", encoding="utf-8")
    out = commit(repo, "-m", "x")
    assert out.returncode == 2 and "pkg/ruff.toml" in out.stderr
    assert commits(repo) == 0


def test_a_staged_ruff_configuration_is_the_one_ruff_reads(repo):
    stage(repo, "long.py", LONG_LINE)
    stage(repo, "pyproject.toml", "[tool.ruff]\nline-length = 80\n")
    out = commit(repo, "-m", "x")
    assert out.returncode != 0 and "ruff" in out.stderr
    assert commits(repo) == 0


def test_a_renamed_file_is_checked_under_its_new_name(repo):
    stage(repo, "notes.txt", "import os\n")
    assert commit(repo, "-q", "-m", "notes").returncode == 0
    assert git(repo, "mv", "notes.txt", "bad.py").returncode == 0
    out = commit(repo, "-m", "rename")
    assert out.returncode != 0 and "nothing was committed" in out.stderr
    assert commits(repo) == 1


def test_a_stub_file_is_checked(repo):
    stage(repo, "bad.pyi", "import os\n")
    out = commit(repo, "-m", "x")
    assert out.returncode != 0 and commits(repo) == 0


def test_files_in_folders_ci_excludes_are_counted_apart(repo):
    (repo / "calibration" / "v0" / "audit").mkdir(parents=True)
    stage(repo, "calibration/v0/audit/record.py", "import os\n")  # a published record
    stage(repo, "good.py", "x = 1\n")
    out = commit(repo, "-q", "-m", "x")
    assert out.returncode == 0, out.stdout + out.stderr
    assert "ruff passed on 1 of 2 staged Python file(s) (1 in folders CI excludes)" in out.stdout


def test_the_script_refuses_to_run_outside_a_virtual_environment(repo, monkeypatch):
    spec = importlib.util.spec_from_file_location("commit_checked", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.sys, "prefix", module.sys.base_prefix)
    monkeypatch.chdir(repo)
    stage(repo, "good.py", "x = 1\n")
    assert module.main(["-m", "x"]) == 2
    assert commits(repo) == 0


@pytest.mark.parametrize("setting", ["fix = true", "fix-only = true"])
def test_a_configuration_that_turns_fixes_on_cannot_pass_a_failing_blob(repo, setting):
    """Codex review: with fixes on, ruff check would judge its fixed output."""
    stage(repo, "pyproject.toml", f"[tool.ruff]\nline-length = 100\n{setting}\n")
    stage(repo, "bad.py", "import os\n")
    out = commit(repo, "-m", "x")
    assert out.returncode != 0 and "staged bad.py" in out.stderr
    assert commits(repo) == 0
    assert git(repo, "show", ":bad.py").stdout == "import os\n"


@pytest.mark.parametrize("step", ["check", "format"])
@pytest.mark.parametrize("code", [-11, 1, 2])
def test_any_failing_ruff_code_stops_before_the_commit(repo, monkeypatch, step, code):
    """Codex review: a negative code (a run ended by a signal) must stop too."""
    spec = importlib.util.spec_from_file_location("commit_checked", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    real_run = module.subprocess.run
    calls = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(cmd)
        if "--stdin-filename" in cmd and step in cmd:
            return subprocess.CompletedProcess(cmd, code)
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.chdir(repo)
    stage(repo, "good.py", "x = 1\n")
    result = module.main(["-m", "x"])
    assert result != 0 and result == (code if code > 0 else 1)
    assert not any(c[:1] == ["git"] and "commit" in c for c in calls)
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
