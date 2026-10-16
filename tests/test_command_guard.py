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
    ".venv/Scripts/python.exe scripts/commit_checked.py -m 'stop using sed and pytest directly'",
    "cat <<'EOF' > .cache/x/msg.txt\nfix: no sed, no awk, no pytest here\n"
    "Select-String is mentioned too\nEOF\n"
    ".venv/Scripts/python.exe scripts/commit_checked.py -q -F .cache/x/msg.txt\ngit push -q",
    ".venv/Scripts/python.exe - <<'EOF'\nimport re\nprint('sed awk pytest')\nEOF",
    'gh pr comment 1 --body "ran pytest through the script; no sed"',
    "grep -n pytest pyproject.toml",
    "grep -rn 'sed -n' docs",
    "ls tests | grep test_seal",
    "echo used based awkward pytestish",
    "git log --oneline -1 && git status --short",
    "Get-Content x.txt -TotalCount 5",
    "$x = @'\nsed -n 1p\npytest\n'@\nWrite-Output $x",
    ".venv/Scripts/python.exe -m ruff check src tests",
    "set -e; git fetch -q origin",
    "grep -e sed -e awk file",
    "powershell -NoProfile -File .cache/codex/run-codex.ps1 -Question q.md -Answer a.txt "
    "-Events e.jsonl",
    # Codex round 1: false positives
    ".venv/Scripts/python.exe scripts/commit_checked.py -m 'pytest'",
    ".venv/Scripts/python.exe scripts/commit_checked.py -m pytest",
    "grep -c 'sed' README.md",
    "gh pr comment 1 --body 'Example: bash -c \"sed -n 1p README.md\"'",
    "gh pr comment 1 --body 'Document pwsh -EncodedCommand AAA='",
    "echo 'python -m pytest is not allowed here'",
    "git log 2>&1 > .cache/x/log.txt",
]


B, P = guard.BASH, guard.POWERSHELL

# Codex round 2: cases that depend on the shell's own quoting and escapes.
BLOCK_BY_SHELL = [
    ('& "C:\\Program Files\\Git\\usr\\bin\\sed.exe" -n 1p README.md', P),
    ('& "C:\\Program Files\\Git\\usr\\bin\\sed.exe" -n 1p README.md', B),
    ('& "C:\\Projetos\\refute\\.venv\\Scripts\\python.exe" -m pytest -q', P),
    ('& "C:\\Projetos\\refute\\.venv\\Scripts\\python.exe" -m pytest -q', B),
    (".venv/Scripts/python.exe \\\n  -m pytest -q", B),
    ("& .venv/Scripts/python.exe `\n  -m pytest -q", P),
    ("Start-Process -FilePath .venv/Scripts/python.exe -ArgumentList '-m','pytest','-q' -Wait", P),
    ('Write-Output @"\n$(Select-String -Path README.md -Pattern Refute)\n"@', P),
    ("echo '<<EOF'\n.venv/Scripts/python.exe -m pytest -q", B),
    ('echo "<<EOF"\nsed -n 1p x', B),
    ("Get-Content x | sls y", P),
    ("iex 'sed -n 1p x'", P),
]

PASS_BY_SHELL = [
    (".venv/Scripts/python.exe -c \"print('import pytest')\"", B),
    (".venv/Scripts/python.exe -c \"print('import pytest')\"", P),
    (".venv/Scripts/python.exe - <<'EOF'\nprint('pytest.main is only text here')\nEOF", B),
    ("Write-Output @'\n$(Select-String is literal in a single here-string)\n'@", P),
    ("git log --format='%h `x`' -1", P),
    ("echo 'a # <<EOF'\ngit status", B),
    ("git status # <<EOF\ngit log -1", B),
]


@pytest.mark.parametrize("command", BLOCK)
@pytest.mark.parametrize("shell", [B, P])
def test_refused(command, shell):
    if shell == P and ("<<" in command or "\\\n" in command or "`" in command):
        pytest.skip("Bash here-documents, continuations and backticks are not PowerShell syntax")
    assert guard.check(command, shell=shell) is not None


@pytest.mark.parametrize("command", PASS)
def test_allowed(command):
    assert guard.check(command, shell=B) is None


@pytest.mark.parametrize(("command", "shell"), BLOCK_BY_SHELL)
def test_refused_by_shell(command, shell):
    assert guard.check(command, shell=shell) is not None


@pytest.mark.parametrize(("command", "shell"), PASS_BY_SHELL)
def test_allowed_by_shell(command, shell):
    assert guard.check(command, shell=shell) is None


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


def test_hook_reads_powershell_with_powershell_rules():
    command = "& .venv/Scripts/python.exe `\n  -m pytest -q"
    out = run_hook({"tool_name": "PowerShell", "tool_input": {"command": command}})
    assert out.returncode == 2 and "run_tests_affinity" in out.stderr


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
    # A wrapper that cannot start, a timeout or invalid output blocks the command too.
    assert hook["onFailure"] == "block"


# Codex round 3 ------------------------------------------------------------------------------

BLOCK_ROUND3 = [
    (
        "Start-Process -FilePath .venv/Scripts/python.exe -ArgumentList '-m', 'pytest', '-q' -Wait",
        P,
    ),
    ("git status&sed -n 1p README.md", B),
    (r'cmd /c ".venv\Scripts\py^thon.exe -m pytest -q"', P),
    (
        '.venv/Scripts/python.exe -c "from importlib import import_module; '
        "import_module('pytest').main()\"",
        B,
    ),
    ("git status; sed -n 1p x # a comment after the command", B),
]

PASS_ROUND3 = [
    ("git status # example; sed -n 1p README.md", B),
    ("Get-ChildItem # example | Select-String x", P),
    ("cat <<'EOF'\n@\"\n$(Select-String -Path README.md -Pattern Refute)\n\"@\nEOF", B),
    ('.venv/Scripts/python.exe -c "print(1)" -m pytest', B),
    (".venv/Scripts/python.exe scripts/x.py -m pytest", B),
    ("echo hi >&2", B),
]


@pytest.mark.parametrize(("command", "shell"), BLOCK_ROUND3)
def test_refused_round3(command, shell):
    assert guard.check(command, shell=shell) is not None


@pytest.mark.parametrize(("command", "shell"), PASS_ROUND3)
def test_allowed_round3(command, shell):
    assert guard.check(command, shell=shell) is None


# Codex round 4 ------------------------------------------------------------------------------

BLOCK_ROUND4 = [
    (
        "Start-Process -FilePath .venv/Scripts/python.exe "
        "-ArgumentList '-c \"import pytest; pytest.main()\"' -Wait",
        P,
    ),
    ("@'\nimport pytest\npytest.main()\n'@ | & .venv/Scripts/python.exe -", P),
    ("cat <<< hello\n.venv/Scripts/python.exe -m pytest -q", B),
]

PASS_ROUND4 = [
    ('Write-Output @"\n`$(Select-String -Path README.md -Pattern Refute)\n"@', P),
    ("@'\nprint('pytest is only text')\n'@ | & .venv/Scripts/python.exe -", P),
    ("cat <<< hello", B),
]


@pytest.mark.parametrize(("command", "shell"), BLOCK_ROUND4)
def test_refused_round4(command, shell):
    assert guard.check(command, shell=shell) is not None


@pytest.mark.parametrize(("command", "shell"), PASS_ROUND4)
def test_allowed_round4(command, shell):
    assert guard.check(command, shell=shell) is None


# Codex round 5 ------------------------------------------------------------------------------

BLOCK_ROUND5 = [
    (".venv/Scripts/python.exe -mpytest -q", B),
    (".venv/Scripts/python.exe -Bmpytest -q", P),
    (".venv/Scripts/python.exe -B -m pytest", B),
    ('cmd /c "echo I\'m ready & .venv\\Scripts\\python.exe -m pytest -q"', P),
    ("@'\nimport pytest\n'@ | & .venv/Scripts/python.exe -", P),
]

PASS_ROUND5 = [
    ("Write-Output @'\nimport pytest\n'@\n@'\nprint(\"ok\")\n'@ | & .venv/Scripts/python.exe -", P),
    ('.venv/Scripts/python.exe -W ignore -c "print(1)" -m pytest', B),
    (".venv/Scripts/python.exe -X utf8 scripts/x.py -mpytest", B),
]


@pytest.mark.parametrize(("command", "shell"), BLOCK_ROUND5)
def test_refused_round5(command, shell):
    assert guard.check(command, shell=shell) is not None


@pytest.mark.parametrize(("command", "shell"), PASS_ROUND5)
def test_allowed_round5(command, shell):
    assert guard.check(command, shell=shell) is None


# WP2 package review --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "@'\nimport pytest\npytest.main()\n'@ | & .venv/Scripts/python.exe",
        "@'\nimport pytest\n'@ | .venv/Scripts/python.exe -u",
    ],
)
def test_here_string_piped_to_python_reading_stdin_implicitly(command):
    assert guard.check(command, shell=P) is not None


def test_python_with_a_script_does_not_read_the_here_string():
    command = "@'\nimport pytest\n'@ | .venv/Scripts/python.exe scripts/x.py"
    assert guard.check(command, shell=P) is None


# Rules of the maintainer's message of 2026-10-16: head, tail and cat reading a file in Bash;
# a backslash in an inline PowerShell command; a commit without the ruff gate --------------

BLOCK_2026_10_16 = [
    # cat, head and tail read in Bash, in every compound form
    ("cat README.md", B),
    ("cat < README.md", B),
    ("head -5 README.md", B),
    ("tail -n 3 x.log", B),
    ("git log --oneline | head -5", B),
    ("git log 2>&1 | head -5", B),
    ("ls; cat x", B),
    ("git status && tail -1 x", B),
    ("(cat x)", B),
    ("echo $(head -1 x)", B),
    ("git status\ncat x", B),
    ("bash -c 'tail -f x.log'", P),
    # a backslash in an inline PowerShell command, even inside quotes
    ("Get-Content -LiteralPath 'C:\\Projetos\\refute\\README.md' -TotalCount 5", P),
    ("& 'C:\\Projetos\\refute\\.venv\\Scripts\\python.exe' -m ruff check src", P),
    ('Write-Output "a\\b"', P),
    ("$p = 'x'; Test-Path $p\\y", P),
    ("bash -c 'powershell -Command \"Get-ChildItem C:\\\\x\"'", B),
    # a commit without the ruff gate, in every compound form
    ("git commit -m x", B),
    ("git commit -m x", P),
    ("git add a.py && git commit -m x", B),
    ("ruff check a.py; git commit -q -F msg.txt", P),
    (".venv/Scripts/python.exe -m ruff check a.py || git commit -m x", B),
    ("echo msg | git commit -F -", B),
    ("(git commit -m x)", B),
    ("x=$(git commit -m y)", B),
    ("git status\ngit commit -m x", B),
    ("git -C C:/Projetos/refute -c user.name=x commit -m x", B),
    ("git merge --no-edit origin/main", B),
    ("git merge origin/main", P),
    ("git cherry-pick abc123", B),
    ("git revert HEAD", B),
    ("git pull origin main", B),
    ("bash -c 'git commit -m x'", P),
]

PASS_2026_10_16 = [
    # cat fed only by a here-document or here-string writes text, it reads no file
    ("cat <<'EOF' > .cache/x/msg.txt\nline\nEOF", B),
    ("cat <<< hello", B),
    ("git log --oneline -3", B),
    # the gate script, and the git commands that do not commit
    (".venv/Scripts/python.exe scripts/commit_checked.py -q -F .cache/x/msg.txt", B),
    (".venv/Scripts/python.exe scripts/commit_checked.py -q -F .cache/x/msg.txt", P),
    ("git merge --no-commit origin/main", B),
    ("git merge --abort", P),
    ("git cherry-pick -n abc123", B),
    ("git pull --ff-only origin main", B),
    ("git log --grep 'commit' -1", B),
    ("gh pr create --title 'git commit without ruff is refused' --body-file x.md", B),
    # a backslash is fine in Bash (the rule is about inline PowerShell), and a saved
    # script is called by a path written with '/'; the hook never reads its content
    ("grep -c 'a\\\\b' README.md", B),
    (
        "powershell -NoProfile -ExecutionPolicy Bypass -File C:/Projetos/refute/.cache/tools/x.ps1",
        P,
    ),
    ("& 'C:/Projetos/refute/.venv/Scripts/python.exe' 'C:/Projetos/refute/.cache/tools/x.py'", P),
    ("Get-Content -LiteralPath 'C:/Projetos/refute/README.md' -TotalCount 5", P),
]


@pytest.mark.parametrize(("command", "shell"), BLOCK_2026_10_16)
def test_refused_2026_10_16(command, shell):
    assert guard.check(command, shell=shell) is not None


@pytest.mark.parametrize(("command", "shell"), PASS_2026_10_16)
def test_allowed_2026_10_16(command, shell):
    assert guard.check(command, shell=shell) is None


def test_a_saved_script_with_backslashes_is_not_read(tmp_path):
    """The rule is about inline commands: a saved script whose code holds backslashes and a
    regular expression passes, because the hook checks only the command text."""
    script = tmp_path / "saved.ps1"
    script.write_text("Get-ChildItem 'C:\\Windows' | Where-Object { $_.Name -match '^\\w+$' }\n")
    command = f"powershell -NoProfile -File {script.as_posix()}"
    assert "\\" in script.read_text() and "\\" not in command
    assert guard.check(command, shell=P) is None


def test_the_reasons_name_the_rule():
    assert "commit_checked.py" in guard.check("git commit -m x", shell=B)
    assert "backslash" in guard.check("Write-Output 'a\\b'", shell=P)
    assert "Read tool" in guard.check("head -1 x", shell=B)


def test_long_python_option_with_a_value_before_reading_stdin():
    command = (
        "@'\nimport pytest\npytest.main()\n'@ | "
        ".venv/Scripts/python.exe --check-hash-based-pycs always"
    )
    assert guard.check(command, shell=P) is not None
