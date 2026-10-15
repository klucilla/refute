"""The PreToolUse command guard (.claude/hooks/command_guard.py): commands that must be
refused and commands that must pass. Offline; the hook is a pure function of the
command text."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "command_guard.py"
spec = importlib.util.spec_from_file_location("command_guard", HOOK)
guard = importlib.util.module_from_spec(spec)
sys.modules["command_guard"] = guard  # dataclasses look the module up by name
spec.loader.exec_module(guard)

SCRIPT = (
    "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_tests_affinity.ps1 "
    "-Junit .cache/x/junit.xml -Tests tests/test_seal.py"
)

BLOCK = [
    # reading excerpts with sed, awk or Select-String
    "sed -n '1,20p' README.md",
    "cd /c/Projetos/refute && sed -n '/paths-ignore/,/^[a-z]/p' ci.yml | head -20",
    "cat file | awk '{print $1}'",
    "gawk -F, '{print $2}' data.csv",
    "/usr/bin/sed -e 's/a/b/' x",
    "find . -name '*.py' -exec sed -i 's/a/b/' {} +",
    "ls | xargs -n1 sed -n 1p",
    "echo $(sed -n 1p file)",
    "VAR=1 sed -n 1p file",
    "Get-Content x.txt | Select-String 'foo'",
    "Get-Content x.txt | sls foo",
    "select-string -Path *.md -Pattern foo",
    "& 'C:\\Program Files\\Git\\usr\\bin\\sed.exe' -n 1p file",
    "bash -c 'sed -n 1p file'",
    'powershell -NoProfile -Command "Get-Content x | Select-String y"',
    'cmd /c "awk 1 file"',
    'eval "sed -n 1p file"',
    "if true; then sed -n 1p x; fi",
    "uv run sed -n 1p x",
    "timeout 10 awk 1 x",
    # pytest outside the affinity script
    "uv run pytest -q",
    ".venv/Scripts/python.exe -m pytest tests/test_seal.py",
    "cd /c/Projetos/refute && .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider",
    "pytest tests",
    "& 'C:\\Projetos\\refute\\.venv\\Scripts\\python.exe' -m pytest -q",
    "py.test -q",
    "python -m py.test",
    'bash -c ".venv/Scripts/python.exe -m pytest"',
    f"{SCRIPT}; .venv/Scripts/python.exe -m pytest -q",
    # unreadable
    "powershell -EncodedCommand ZQBjAGgAbwA=",
    "pwsh -enc ZQBjAGgAbwA=",
    # Codex round 1: false negatives
    ".venv/Scripts/python.exe -m pytest --junitxml=.cache/run_tests_affinity.ps1.xml",
    "bash -lc 'sed -n 1p README.md'",
    "pwsh -Command Select-String -Path README.md -Pattern Refute",
    'echo "$(sed -n 1p README.md)"',
    'echo "`awk 1 x`"',
    "xargs -n 1 sed -n 1p",
    "uv run --project C:/Projetos/refute pytest -q",
    "Start-Process -FilePath .venv/Scripts/python.exe -ArgumentList '-m pytest -q' -Wait",
    ".venv/Scripts/python.exe -c \"import pytest; pytest.main(['-q'])\"",
    "cat <<'EOF' | awk '1'\nline\nEOF",
    "cat <<EOF\n$(sed -n 1p README.md)\nEOF",
    's""ed -n 1p README.md',
    ".venv/Scripts/python.exe - <<'EOF'\nimport pytest\npytest.main(['-q'])\nEOF",
    "bash <<'EOF'\nsed -n 1p x\nEOF",
]

PASS = [
    SCRIPT,
    "powershell -NoProfile -ExecutionPolicy Bypass -File 'C:\\Projetos\\refute\\scripts\\"
    "run_tests_affinity.ps1' -Junit 'C:\\x\\j.xml'",
    "git commit -m 'stop using sed and pytest directly'",
    "git -c user.name=x commit -q -F - <<'EOF'\nfix: no sed, no awk, no pytest here\n"
    "Select-String is mentioned too\nEOF\ngit push -q",
    ".venv/Scripts/python.exe - <<'EOF'\nimport re\nprint('sed awk pytest')\nEOF",
    'gh pr comment 1 --body "ran pytest through the script; no sed"',
    "grep -n pytest pyproject.toml",
    "grep -rn 'sed -n' docs",
    "ls tests | grep test_seal",
    "echo used based awkward pytestish",
    "git log --oneline -1 && git status --short",
    "cat .cache/x/junit.xml",
    "Get-Content x.txt -TotalCount 5",
    "$x = @'\nsed -n 1p\npytest\n'@\nWrite-Output $x",
    ".venv/Scripts/python.exe -m ruff check src tests",
    "set -e; git fetch -q origin",
    "grep -e sed -e awk file",
    "powershell -NoProfile -File .cache/codex/run-codex.ps1 -Question q.md -Answer a.txt "
    "-Events e.jsonl",
    # Codex round 1: false positives
    "git commit -m 'pytest'",
    "git commit -m pytest",
    "grep -c 'sed' README.md",
    "gh pr comment 1 --body 'Example: bash -c \"sed -n 1p README.md\"'",
    "gh pr comment 1 --body 'Document pwsh -EncodedCommand AAA='",
    "echo 'python -m pytest is not allowed here'",
    "git log 2>&1 | head -5",
]


@pytest.mark.parametrize("command", BLOCK)
def test_refused(command):
    assert guard.check(command) is not None


@pytest.mark.parametrize("command", PASS)
def test_allowed(command):
    assert guard.check(command) is None


def run_hook(payload):
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )


def test_hook_exit_code_2_with_the_reason_on_stderr():
    out = run_hook({"tool_name": "Bash", "tool_input": {"command": "sed -n 1p x"}})
    assert out.returncode == 2
    assert "command_guard" in out.stderr and "Read tool" in out.stderr


def test_hook_passes_allowed_commands_and_other_tools_silently():
    for payload in (
        {"tool_name": "Bash", "tool_input": {"command": "git status"}},
        {"tool_name": "PowerShell", "tool_input": {"command": SCRIPT}},
        {"tool_name": "Read", "tool_input": {"file_path": "x"}},
        {"tool_name": "Bash", "tool_input": {}},
    ):
        out = run_hook(payload)
        assert out.returncode == 0 and out.stdout == "" and out.stderr == ""


def test_hook_ignores_input_that_is_not_json():
    out = subprocess.run(
        [sys.executable, str(HOOK)], input="not json", capture_output=True, text=True
    )
    assert out.returncode == 0


def test_settings_register_the_hook_for_bash_and_powershell():
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    (entry,) = settings["hooks"]["PreToolUse"]
    assert entry["matcher"] == "Bash|PowerShell"
    (hook,) = entry["hooks"]
    assert hook["type"] == "command"
    assert any("command_guard.py" in part for part in [hook["command"], *hook.get("args", [])])
