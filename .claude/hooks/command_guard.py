"""PreToolUse hook: refuse shell commands that break two project rules.

1. Excerpts are read with the Read tool, never with ``sed``, ``awk`` (or ``gsed``,
   ``gawk``, ``mawk``, ``nawk``) or PowerShell's ``Select-String`` (alias ``sls``).
2. pytest runs only through ``scripts/run_tests_affinity.ps1``, which sets the CPU
   affinity to threads 8 to 31 and writes a JUnit XML file (CLAUDE.md). Any command
   that itself starts pytest is refused; calling that script does not start pytest in
   the command, so it passes.

Claude Code sends the tool call as JSON on stdin (``tool_name``,
``tool_input.command``). A refused command exits with code 2 and the reason on stderr;
anything else exits 0 with no output. ``.claude/settings.json`` wraps the hook so that
a failure of the hook itself also blocks.

**Limits.** This is a guard against slips, not a sandbox. It reads the command text; it
does not follow scripts, variables or aliases. Input that is not JSON, or a call of
another tool, is let through: the hook trusts the Claude Code protocol. If the wrapper
shell cannot start, or the hook times out, Claude Code continues (``onFailure: block``
needs a newer Claude Code than the one in use).

How a command is read. The tool decides the shell rules: ``Bash`` (and code given to
``bash -c``) uses Bash quoting, ``PowerShell`` (and ``powershell -Command``, ``cmd
/c``) uses PowerShell quoting.

- Line continuations are joined first (``\\`` + new line in Bash, a backtick + new line
  in PowerShell).
- A lexer splits the command into segments at ``;``, ``|``, ``&&``, ``||``, ``&``,
  ``(``, ``)``, ``{``, ``}``, new lines and command substitutions, outside quotes.
  Quotes join with the surrounding word as in a shell (``s""ed`` is ``sed``); a quoted
  string is one word, so text in a commit message or a ``--body`` is data.
- Escapes: in Bash, ``\\`` escapes outside quotes, and inside double quotes only before
  ``$``, a backtick, ``"``, ``\\`` or a new line (so ``"C:\\Program Files\\x"`` keeps its
  backslashes). In PowerShell the backtick escapes and ``\\`` is literal.
- Command substitutions are commands and are checked: ``$(...)`` anywhere except in
  single quotes; backticks in Bash outside single quotes; ``$(...)`` in a PowerShell
  double-quoted here-string. Bash here-documents are found only outside quotes and
  comments. A quoted here-document (``<<'EOF'``) is data, an unquoted one has its
  substitutions checked, one fed to a shell is checked as code, and one fed to Python
  is checked for pytest.
- Only the **command word** of a segment counts, found after environment assignments,
  shell keywords and prefixes (``env``, ``sudo``, ``xargs``, ``uv run``, ``timeout``,
  the call operator ``&``, ...), skipping their options and option values, and after
  ``find -exec``. A program given by path counts by its file name.
- Code given to a shell is checked as a command: ``bash``/``sh -c`` (also ``-lc``),
  ``powershell``/``pwsh -Command`` (quoted or not), ``cmd /c``, ``eval``,
  ``Invoke-Expression``/``iex``, and ``Start-Process -FilePath ... -ArgumentList ...``
  (a string or an array). ``python -m pytest`` starts pytest; Python code given with
  ``-c`` or in a here-document starts it when its syntax tree imports pytest or calls
  ``pytest.main`` (a string that only mentions pytest does not count). A PowerShell
  ``-EncodedCommand`` cannot be read, so it is refused.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass, field

READ_TOOLS = {"sed", "gsed", "awk", "gawk", "mawk", "nawk", "select-string", "sls"}
PYTEST_WORDS = {"pytest", "py.test"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
POWERSHELLS = {"powershell", "pwsh"}
BASH, POWERSHELL = "bash", "powershell"
_PY_FALLBACK = re.compile(r"\bimport\s+pytest\b|\bfrom\s+pytest\b|\bpytest\s*\.\s*main\b")

# Prefixes before the command word, with the options of each that take a value.
PREFIX_VALUE_OPTIONS: dict[str, set[str]] = {
    "env": {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"},
    "sudo": {"-u", "-g", "-C", "-D", "-h", "-p", "-U", "-r", "-t"},
    "xargs": {"-n", "-P", "-L", "-I", "-d", "-s", "-E", "-a", "-l", "-i", "-e"},
    "nohup": set(),
    "time": set(),
    "nice": {"-n"},
    "exec": {"-a"},
    "command": set(),
    "builtin": set(),
    "&": set(),
    ".": set(),
    "call": set(),
    "stdbuf": {"-i", "-o", "-e"},
    "if": set(),
    "then": set(),
    "else": set(),
    "elif": set(),
    "do": set(),
    "while": set(),
    "until": set(),
    "!": set(),
}
UV_RUN_VALUE_OPTIONS = {
    "--project",
    "--directory",
    "--python",
    "-p",
    "--with",
    "--with-requirements",
    "--env-file",
    "--package",
    "--group",
    "--extra",
    "--index",
    "--index-url",
    "--extra-index-url",
    "--find-links",
    "-f",
    "--isolated-from",
    "--script",
    "--cache-dir",
    "--config-file",
    "--only-group",
    "--no-group",
    "--with-editable",
}
_ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_HEREDOC_START = re.compile(r"<<(-?)[ \t]*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
_HERESTRING = re.compile(r"@(['\"])[ \t]*\r?\n(.*?)\r?\n\1@", re.S)


@dataclass
class Word:
    text: str
    quoted: bool = False  # the whole word came from one quoted string


@dataclass
class Lexed:
    segments: list[list[Word]] = field(default_factory=list)
    nested: list[str] = field(default_factory=list)  # command substitution bodies
    heredocs: list[tuple[list[Word], str, bool]] = field(default_factory=list)


def _read_until(text: str, i: int, close: str) -> tuple[str, int]:
    """Text up to the matching ``)`` (for ``$(``) or backtick, from position i."""
    if close == "`":
        j = text.find("`", i)
        return (text[i:], len(text)) if j < 0 else (text[i:j], j + 1)
    depth = 1
    j = i
    quote = ""
    while j < len(text):
        ch = text[j]
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "'\"":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[i:j], j + 1
        j += 1
    return text[i:], len(text)


def _unquoted_heredoc_starts(line: str) -> list[re.Match[str]]:
    """``<<`` markers of a Bash line that are outside quotes and before a comment."""
    found = []
    quote = ""
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            if ch == "\\" and quote == '"':
                i += 2
                continue
            if ch == quote:
                quote = ""
        elif ch == "\\":
            i += 2
            continue
        elif ch in "'\"":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t;|&("):
            break
        elif line.startswith("<<", i) and not line.startswith("<<<", i):
            m = _HEREDOC_START.match(line, i)
            if m:
                found.append(m)
                i = m.end()
                continue
        i += 1
    return found


def lex(command: str, shell: str = BASH) -> Lexed:
    out = Lexed()
    if shell == BASH:
        text = re.sub(r"\\\r?\n", " ", command)
    else:
        text = re.sub(r"`\r?\n", " ", command)

    def herestring(match: re.Match[str]) -> str:
        if match.group(1) == '"':  # expandable: its $(...) subexpressions run
            body = match.group(2)
            k = 0
            while (start := body.find("$(", k)) >= 0:
                inner, k = _read_until(body, start + 2, ")")
                out.nested.append(inner)
        return " HERESTRING "

    text = _HERESTRING.sub(herestring, text)

    pending: list[tuple[str, bool]] = []
    if shell == BASH:  # here-documents: keep the header line, take the body out
        lines = text.split("\n")
        kept: list[str] = []
        k = 0
        while k < len(lines):
            line = lines[k]
            kept.append(line)
            k += 1
            for m in _unquoted_heredoc_starts(line):
                delimiter, quoted = m.group(3), bool(m.group(2))
                body = []
                while k < len(lines) and lines[k].strip() != delimiter:
                    body.append(lines[k])
                    k += 1
                k += 1  # the terminator
                pending.append(("\n".join(body), quoted))
        text = "\n".join(kept)

    escape = "\\" if shell == BASH else "`"
    segment: list[Word] = []
    word = ""
    in_word = False
    all_quoted = True
    i = 0

    def end_word() -> None:
        nonlocal word, in_word, all_quoted
        if in_word:
            segment.append(Word(word, quoted=all_quoted))
        word, in_word, all_quoted = "", False, True

    def end_segment() -> None:
        nonlocal segment
        end_word()
        if segment:
            out.segments.append(segment)
        segment = []

    while i < len(text):
        ch = text[i]
        if ch == "'":
            j = text.find("'", i + 1)
            j = len(text) if j < 0 else j
            word += text[i + 1 : j]
            in_word = True
            i = j + 1
            continue
        if ch == '"':
            j = i + 1
            content = []
            while j < len(text) and text[j] != '"':
                c = text[j]
                if shell == BASH and c == "\\" and j + 1 < len(text):
                    if text[j + 1] in '$`"\\\n':
                        content.append(text[j + 1])
                        j += 2
                        continue
                if shell == POWERSHELL and c == "`" and j + 1 < len(text):
                    content.append(text[j + 1])
                    j += 2
                    continue
                if text.startswith("$(", j):
                    body, j = _read_until(text, j + 2, ")")
                    out.nested.append(body)
                    continue
                if shell == BASH and c == "`":
                    body, j = _read_until(text, j + 1, "`")
                    out.nested.append(body)
                    continue
                content.append(c)
                j += 1
            word += "".join(content)
            in_word = True
            i = j + 1
            continue
        if ch == escape and i + 1 < len(text):
            word += text[i + 1]
            in_word = True
            all_quoted = False
            i += 2
            continue
        if text.startswith("$(", i):
            end_segment()
            body, i = _read_until(text, i + 2, ")")
            out.nested.append(body)
            continue
        if shell == BASH and ch == "`":
            end_segment()
            body, i = _read_until(text, i + 1, "`")
            out.nested.append(body)
            continue
        if text.startswith("&&", i) or text.startswith("||", i):
            end_segment()
            i += 2
            continue
        if ch == "&" and in_word:  # 2>&1 and similar: part of a word
            word += ch
            i += 1
            continue
        if ch == "&":
            # PowerShell call operator "& path" or shell background "cmd &"
            end_segment()
            segment.append(Word("&"))
            i += 1
            continue
        if ch in ";|(){}\n":
            end_segment()
            i += 1
            continue
        if ch in " \t\r":
            end_word()
            i += 1
            continue
        word += ch
        in_word = True
        all_quoted = False
        i += 1
    end_segment()

    headers = [s for s in out.segments if any(w.text.startswith("<<") for w in s)]
    for n, (body, quoted) in enumerate(pending):
        out.heredocs.append((headers[n] if n < len(headers) else [], body, quoted))
    return out


def _name(token: str) -> str:
    """The command name of a word: its last path part, lowercase, without .exe."""
    base = re.split(r"[\\/]", token)[-1].lower()
    return base[:-4] if base.endswith(".exe") else base


def _is_python(name: str) -> bool:
    return name.startswith("python") or name == "py"


def _python_uses_pytest(code: str) -> bool:
    """True when Python code imports pytest or calls pytest.main (by its syntax tree;
    a string that only mentions pytest does not count)."""
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return bool(_PY_FALLBACK.search(code))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            a.name.split(".")[0] in PYTEST_WORDS for a in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "pytest":
            return True
        if isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "pytest"
            ):
                return True
            args = [a.value for a in node.args if isinstance(a, ast.Constant)]
            if "pytest" in args and (
                (isinstance(func, ast.Name) and func.id == "__import__")
                or (isinstance(func, ast.Attribute) and func.attr == "import_module")
            ):
                return True
    return False


def _command_index(words: list[Word]) -> int | None:
    """Index of the command word of a segment, after assignments and prefixes."""
    i = 0
    n = len(words)
    while i < n:
        text = words[i].text
        name = _name(text)
        if not words[i].quoted and _ENV_ASSIGNMENT.match(text):
            i += 1
            continue
        if name in PREFIX_VALUE_OPTIONS and not words[i].quoted:
            options = PREFIX_VALUE_OPTIONS[name]
            i += 1
            while i < n and words[i].text.startswith("-"):
                i += 2 if words[i].text in options else 1
            continue
        if name == "uv" and i + 1 < n and words[i + 1].text == "run":
            i += 2
            while i < n and words[i].text.startswith("-"):
                i += 2 if words[i].text in UV_RUN_VALUE_OPTIONS else 1
            continue
        if name == "timeout":
            i += 1
            while i < n and words[i].text.startswith("-"):
                i += 2 if words[i].text in ("-s", "--signal", "-k", "--kill-after") else 1
            i += 1  # the duration
            continue
        return i
    return None


def _refuse_read(word: str) -> str:
    return (
        f"'{word}' is not allowed: read excerpts with the Read tool and search with the "
        "Grep tool (CLAUDE.md, project rules)"
    )


PYTEST_REASON = (
    "pytest runs only through scripts/run_tests_affinity.ps1 (affinity 8-31, JUnit XML): "
    "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_tests_affinity.ps1 "
    "-Junit .cache/<task>/junit.xml [-Tests a.py,b.py]"
)


def _check_segment(words: list[Word], depth: int, shell: str) -> str | None:
    start = _command_index(words)
    if start is None:
        return None
    rest = words[start:]
    name = _name(rest[0].text)
    args = [w.text for w in rest[1:]]
    lowered = [a.lower() for a in args]
    if name in READ_TOOLS:
        return _refuse_read(name)
    if name in PYTEST_WORDS:
        return PYTEST_REASON
    if _is_python(name):
        for k, arg in enumerate(args):
            if arg == "-m" and k + 1 < len(args) and args[k + 1].lower() in PYTEST_WORDS:
                return PYTEST_REASON
            if arg == "-c" and k + 1 < len(args) and _python_uses_pytest(args[k + 1]):
                return PYTEST_REASON
    if name in SHELLS:
        for k, arg in enumerate(args):
            if re.fullmatch(r"-[a-z]*c[a-z]*", arg) and k + 1 < len(args):
                return check(args[k + 1], depth + 1, BASH)
    if name in POWERSHELLS:
        for k, arg in enumerate(lowered):
            if arg in ("-e", "-ec", "-en", "-enc", "-encodedcommand", "/e", "/enc"):
                return "an encoded PowerShell command cannot be checked; write it in clear"
            if arg in ("-c", "-command", "/c", "/command") and k + 1 < len(args):
                return check(" ".join(args[k + 1 :]), depth + 1, POWERSHELL)
    if name == "cmd":
        for k, arg in enumerate(lowered):
            if arg in ("/c", "/k") and k + 1 < len(args):
                return check(" ".join(args[k + 1 :]), depth + 1, POWERSHELL)
    if name == "eval" and args:
        return check(" ".join(args), depth + 1, BASH)
    if name in ("invoke-expression", "iex") and args:
        return check(" ".join(args), depth + 1, POWERSHELL)
    if name in ("start-process", "saps", "start"):
        target, arglist = "", ""
        positional = []
        k = 0
        while k < len(args):
            a = lowered[k]
            if a in ("-filepath", "-file", "-path") and k + 1 < len(args):
                target = args[k + 1]
                k += 2
                continue
            if a in ("-argumentlist", "-args", "-arguments") and k + 1 < len(args):
                arglist = args[k + 1].replace(",", " ")  # an array joins with commas
                k += 2
                continue
            if not args[k].startswith("-"):
                positional.append(args[k])
            k += 1
        target = target or (positional[0] if positional else "")
        if target:
            # the target is one word even with blanks; the arguments are re-read
            return _check_segment(
                [Word(target, quoted=True), *(Word(t) for t in arglist.split())],
                depth + 1,
                shell,
            )
    for k, arg in enumerate(args):  # find -exec <command> ...
        if arg in ("-exec", "-execdir", "-ok") and k + 1 < len(args):
            found = _check_segment(rest[k + 2 :], depth, shell)
            if found:
                return found
    return None


def check(command: str, depth: int = 0, shell: str = BASH) -> str | None:
    """The reason to refuse ``command``, or None when it may run."""
    if depth > 8:
        return "the command nests shells too deeply to be checked"
    lexed = lex(command, shell)
    for words in lexed.segments:
        reason = _check_segment(words, depth, shell)
        if reason:
            return reason
    for body in lexed.nested:
        reason = check(body, depth + 1, shell)
        if reason:
            return reason
    for header, body, quoted in lexed.heredocs:
        start = _command_index(header) if header else None
        runner = _name(header[start].text) if start is not None else ""
        if _is_python(runner) and _python_uses_pytest(body):
            return PYTEST_REASON
        if runner in SHELLS:
            reason = check(body, depth + 1, BASH)  # a here-document fed to a shell is code
            if reason:
                return reason
        elif not quoted:  # an unquoted here-document expands $(...) and backticks
            for inner in re.findall(r"\$\(([^()]*)\)|`([^`]*)`", body):
                reason = check(inner[0] or inner[1], depth + 1, BASH)
                if reason:
                    return reason
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0  # not a tool call this hook understands
    tool = payload.get("tool_name")
    if tool not in ("Bash", "PowerShell"):
        return 0
    command = (payload.get("tool_input") or {}).get("command")
    if not isinstance(command, str):
        return 0
    reason = check(command, shell=BASH if tool == "Bash" else POWERSHELL)
    if reason:
        print(f"command_guard: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
