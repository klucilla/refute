"""PreToolUse hook: refuse shell commands that break the project rules below.

1. Excerpts are read with the Read tool, never with ``sed``, ``awk`` (or ``gsed``,
   ``gawk``, ``mawk``, ``nawk``) or PowerShell's ``Select-String`` (alias ``sls``); in
   Bash, never with ``head`` or ``tail``, nor with ``cat`` given a file (a ``cat`` fed
   only by a here-document or here-string writes text and passes).
2. pytest runs only through ``scripts/run_tests_affinity.ps1``, which sets the CPU
   affinity to threads 8 to 31 and writes a JUnit XML file (CLAUDE.md). Any command
   that itself starts pytest is refused; calling that script does not start pytest in
   the command, so it passes.
3. A backslash never appears in an inline PowerShell command (the PowerShell tool, or
   code given to ``powershell``/``pwsh -Command``), not even inside a quoted string:
   paths are written with ``/``, and code that needs a backslash or a regular
   expression goes into a saved script, which this hook never reads.
4. A commit runs only after ruff passes on the staged Python files: a direct
   ``git commit`` is refused, and so is any git command that would commit on its own
   (``git merge`` unless ``--no-commit`` or ``--squash`` is in effect, or it is
   ``--abort``/``--quit``; ``git cherry-pick`` and ``git revert`` unless
   ``-n``/``--no-commit`` is in effect, or it is ``--abort``/``--quit``; ``git pull``
   unless ``--ff-only`` is in effect, without ``--rebase``). The last of ``--commit`` and
   ``--no-commit`` (and of ``--squash``/``--no-squash``, ``--ff-only``/``--ff``/``--no-ff``)
   wins, as in git; option values (``-m MESSAGE``, ``-X OPTION``, ...) are skipped, and an
   abbreviated long option counts as the option it uniquely abbreviates. An alias given
   with ``git -c alias.NAME=...`` is expanded (a ``!`` alias is checked as a shell
   command); one given with ``--config-env`` cannot be read and is refused. The way to
   commit is ``scripts/commit_checked.py``, which runs ``ruff check`` and
   ``ruff format --check`` on the staged Python files, as staged, and commits only when
   both exit with code 0 (the maintainer's rule of 2026-10-16).

Claude Code sends the tool call as JSON on stdin (``tool_name``,
``tool_input.command``). A refused command exits with code 2 and the reason on stderr;
anything else exits 0 with no output. ``.claude/settings.json`` wraps the hook so that
a failure of the hook itself also blocks.

**Limits.** This is a guard against slips, not a sandbox. It reads the command text; it
does not follow scripts, variables, shell aliases or functions, nor git aliases defined in
a git configuration file. Git commands that replay or build commits from existing content
(``git am``, ``git rebase``, ``git stash``, ``git commit-tree``) are not covered. Input
that is not JSON, or a call of another tool, is let through: the hook trusts the Claude
Code protocol. If the wrapper shell cannot start, or the hook times out, the command is
blocked too: ``.claude/settings.json`` sets ``"onFailure": "block"`` (Claude Code
v2.1.295 or later), and the wrapper turns any exit code other than 0 and 2 into 2.

How a command is read. The tool decides the shell rules: ``Bash`` (and code given to
``bash -c``) uses Bash quoting, ``PowerShell`` (and ``powershell -Command``) uses
PowerShell quoting, and code given to ``cmd /c`` uses the caret as its escape, with no
substitutions.

- Line continuations are joined first (``\\`` + new line in Bash, a backtick + new line
  in PowerShell, a caret + new line in cmd).
- A ``#`` that starts a word, outside quotes, starts a comment (Bash and PowerShell).
- ``&`` inside a word belongs to it only in a redirection (``2>&1``, ``>&2``, ``&>``);
  otherwise it separates commands (``a&b`` runs ``b``).
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
  redirections (``2>/dev/null git ...``, ``0<file cat``), shell keywords and prefixes
  (``env``, ``sudo``, ``xargs``, ``uv run``, ``timeout``, the call operator ``&``, ...,
  quoted or not), skipping their options and option values, and after ``find -exec``.
  A program given by path counts by its file name. The string of ``env -S`` is checked
  as a command.
- Code given to a shell is checked as a command: ``bash``/``sh -c`` (also ``-lc``) and
  a ``<<<`` here-string fed to a shell, ``powershell``/``pwsh`` with ``-Command`` or any
  prefix of it (``-c``, ``-co``, ...) or with code as its first argument, ``cmd /c``,
  ``eval``, ``Invoke-Expression``/``iex``, and ``Start-Process`` with the program and its
  arguments named or by position (a string, a list or ``@(...)``). Code a shell reads
  from a pipe (``... | bash``, ``... | powershell -Command -``) and a PowerShell
  ``-EncodedCommand`` cannot be read, so they are refused. ``python -m pytest`` starts
  pytest; Python code given with ``-c``, in a here-document or in a here-string starts
  it when its syntax tree imports pytest or calls ``pytest.main`` (a string that only
  mentions pytest does not count).
- ``cat`` reads a file when it has a file operand (after ``--`` every word is one, and a
  quoted ``<<x`` is a file name, not a here-document) or an input redirection from a file,
  before or after the command word.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass, field

READ_TOOLS = {"sed", "gsed", "awk", "gawk", "mawk", "nawk", "select-string", "sls"}
BASH_READ_TOOLS = {"head", "tail"}  # cat is refused only when it is given a file
GIT_VALUE_OPTIONS = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--super-prefix",
    "--config-env",
}
# Per committing git subcommand: the options whose value is the next word, and the long
# options whose state decides whether it commits (abbreviations resolve against both).
GIT_SUB_VALUE_OPTIONS: dict[str, set[str]] = {
    "merge": {
        "-m",
        "-F",
        "-s",
        "-X",
        "--file",
        "--strategy",
        "--strategy-option",
        "--into-name",
        "--cleanup",
    },
    "cherry-pick": {"-m", "-X", "--mainline", "--strategy", "--strategy-option", "--cleanup"},
    "revert": {"-m", "-X", "--mainline", "--strategy", "--strategy-option", "--cleanup"},
    "pull": {
        "-s",
        "-X",
        "-j",
        "-o",
        "--strategy",
        "--strategy-option",
        "--depth",
        "--deepen",
        "--shallow-since",
        "--shallow-exclude",
        "--upload-pack",
        "--jobs",
        "--server-option",
        "--negotiation-tip",
    },
}
GIT_SUB_FLAGS: dict[str, list[str]] = {
    "merge": [
        "--commit",
        "--no-commit",
        "--squash",
        "--no-squash",
        "--abort",
        "--quit",
        "--continue",
    ],
    "cherry-pick": ["--commit", "--no-commit", "--abort", "--quit", "--skip", "--continue"],
    "revert": ["--commit", "--no-commit", "--abort", "--quit", "--skip", "--continue"],
    "pull": ["--ff-only", "--ff", "--no-ff", "--rebase", "--no-rebase"],
}
# powershell.exe / pwsh parameters that take a value, and their documented short names
PS_EXE_VALUE_PARAMETERS = (
    "-executionpolicy",
    "-windowstyle",
    "-version",
    "-psconsolefile",
    "-inputformat",
    "-outputformat",
    "-configurationname",
    "-workingdirectory",
    "-settingsfile",
    "-custompipename",
)
PS_EXE_VALUE_SHORT = {"-ex", "-ep", "-w", "-wd", "-wo", "-if", "-in", "-of", "-o", "-v"}
# Start-Process parameters (and documented aliases): the program, its arguments, other
# parameters with a value, and switches
START_PROCESS_PARAMETERS = {
    "-filepath": "file",
    "-path": "file",
    "-pspath": "file",
    "-argumentlist": "args",
    "-args": "args",
    "-workingdirectory": "value",
    "-credential": "value",
    "-redirectstandarderror": "value",
    "-redirectstandardinput": "value",
    "-redirectstandardoutput": "value",
    "-rse": "value",
    "-rsi": "value",
    "-rso": "value",
    "-verb": "value",
    "-windowstyle": "value",
    "-environment": "value",
    "-wait": "flag",
    "-nonewwindow": "flag",
    "-nnw": "flag",
    "-passthru": "flag",
    "-loaduserprofile": "flag",
    "-lup": "flag",
    "-usenewenvironment": "flag",
}
STDIN_REASON = (
    "code a shell reads from standard input cannot be checked: give it with -c/-Command, "
    "or put it in a saved script"
)
BACKSLASH_REASON = (
    "a backslash is not allowed in an inline PowerShell command: write paths with '/', "
    "and put code that needs a backslash or a regular expression in a saved script "
    "(CLAUDE.md, the maintainer's rules)"
)
COMMIT_REASON = (
    "commit through scripts/commit_checked.py, which runs ruff on the staged Python files "
    "and commits only if ruff exits 0 (for a merge: git merge --no-commit, then "
    "scripts/commit_checked.py --no-edit)"
)
PYTEST_WORDS = {"pytest", "py.test"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
POWERSHELLS = {"powershell", "pwsh"}
BASH, POWERSHELL, CMD = "bash", "powershell", "cmd"
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
_REDIRECTION = re.compile(r"^(\d*)(&>>|&>|<<<|<<-|<<|<>|<&|>&|>>|>\||<|>)(.*)$", re.S)
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
    herestrings: list[str] = field(default_factory=list)  # PowerShell bodies
    separators: list[str] = field(default_factory=list)  # what ended each segment


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
        elif line.startswith("<<<", i):
            i += 3
            continue
        elif line.startswith("<<", i):
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
    elif shell == POWERSHELL:
        text = re.sub(r"`\r?\n", " ", command)
    else:  # cmd: a caret ends a continued line
        text = re.sub(r"\^\r?\n", " ", command)

    def herestring(match: re.Match[str]) -> str:
        body = match.group(2)
        out.herestrings.append(body)
        if match.group(1) == '"':  # expandable: its $(...) subexpressions run
            k = 0
            while (start := body.find("$(", k)) >= 0:
                if start > 0 and body[start - 1] == "`":  # `$( is literal
                    k = start + 2
                    continue
                inner, k = _read_until(body, start + 2, ")")
                out.nested.append(inner)
        return f" __HERESTRING_{len(out.herestrings) - 1}__ "

    if shell == POWERSHELL:  # here-strings are PowerShell syntax only
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

    escape = {BASH: "\\", POWERSHELL: "`", CMD: "^"}[shell]
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

    def end_segment(separator: str = "") -> None:
        nonlocal segment
        end_word()
        if segment:
            out.segments.append(segment)
            out.separators.append(separator)
        segment = []

    while i < len(text):
        ch = text[i]
        if ch == "'" and shell != CMD:
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
                if shell != CMD and text.startswith("$(", j):
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
        if ch == "#" and not in_word and shell != CMD:
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
            continue
        if ch == escape and i + 1 < len(text):
            word += text[i + 1]
            in_word = True
            all_quoted = False
            i += 2
            continue
        if shell == POWERSHELL and text.startswith("@(", i):
            # an array subexpression: its commands run, and it is one argument value
            body, i = _read_until(text, i + 2, ")")
            out.nested.append(body)
            word += f"@({body})"
            in_word = True
            all_quoted = False
            continue
        if shell != CMD and text.startswith("$(", i):
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
        if ch == "&" and in_word and (word.endswith((">", "<")) or text.startswith("&>", i)):
            # a redirection such as 2>&1 or >&2: part of the word
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
            end_segment(ch)
            i += 1
            continue
        if ch in " \t\r":
            end_word()
            i += 1
            continue
        if ch in "<>" and in_word and not word.isdigit() and word[-1:] not in ("<", ">", "&"):
            end_word()  # cat<file: the redirection starts its own word (2>&1 stays whole)
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
                or (isinstance(func, ast.Name) and func.id == "import_module")
            ):
                return True
    return False


def _reads_python_stdin(words: list[Word]) -> bool:
    """A segment that runs Python on its standard input: ``python -``, or Python with
    no script, no ``-c`` and no ``-m`` (it then reads the program from stdin)."""
    start = _command_index(words)
    if start is None or not _is_python(_name(words[start].text)):
        return False
    rest = words[start + 1 :]
    args = [w.text for w in rest]
    k = 0
    while k < len(args):
        arg = args[k]
        redirection = _redirection(rest[k])
        if redirection:  # <<< code, < file: not a script operand
            k += 1 if redirection[1] else 2
            continue
        if arg == "-":
            return True
        if not arg.startswith("-"):
            return False  # a script
        if arg == "--check-hash-based-pycs":  # a long option that takes a value
            k += 2
            continue
        if arg.startswith("--"):
            k += 1
            continue
        for pos in range(1, len(arg)):
            if arg[pos] in "mc":
                return False  # -c CODE or -m MODULE: not the program from stdin
            if arg[pos] in "WX":
                if pos == len(arg) - 1:
                    k += 1  # the value is the next word
                break
        k += 1
    return True


def _redirection(word: Word) -> tuple[str, str] | None:
    """The operator and the attached target of a redirection word (``2>/dev/null``,
    ``0<file``, ``<``), or None. A quoted word is never a redirection."""
    if word.quoted:
        return None
    m = _REDIRECTION.match(word.text)
    return (m.group(2), m.group(3)) if m else None


def _command_index(words: list[Word]) -> int | None:
    """Index of the command word of a segment, after assignments, redirections and
    prefixes."""
    i = 0
    n = len(words)
    while i < n:
        text = words[i].text
        name = _name(text)
        if not words[i].quoted and _ENV_ASSIGNMENT.match(text):
            i += 1
            continue
        redirection = _redirection(words[i])
        if redirection:
            i += 1 if redirection[1] else 2  # the target is attached or the next word
            continue
        if name in PREFIX_VALUE_OPTIONS and not (words[i].quoted and name == "&"):
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


def _drop_redirections(words: list[Word]) -> list[Word]:
    """The words without redirections and their detached targets."""
    kept: list[Word] = []
    k = 0
    while k < len(words):
        redirection = _redirection(words[k])
        if redirection:
            k += 1 if redirection[1] else 2
            continue
        kept.append(words[k])
        k += 1
    return kept


def _leading_redirections(words: list[Word], start: int) -> list[Word]:
    """The redirections before the command word, each with its detached target."""
    found: list[Word] = []
    k = 0
    while k < start:
        redirection = _redirection(words[k])
        if redirection:
            found.append(words[k])
            if not redirection[1] and k + 1 < start:
                found.append(words[k + 1])
                k += 1
        k += 1
    return found


def _env_split_strings(words: list[Word], end: int) -> list[str]:
    """The strings given to ``env -S``/``--split-string`` before the command word: env
    splits each into words and runs them as the command."""
    found: list[str] = []
    seen_env = False
    for k in range(end):
        text = words[k].text
        if _name(text) == "env":
            seen_env = True
            continue
        if not seen_env:
            continue
        if text in ("-S", "--split-string") and k + 1 < len(words):
            found.append(words[k + 1].text)
        elif text.startswith("--split-string="):
            found.append(text.split("=", 1)[1])
        elif text.startswith("-S") and len(text) > 2:
            found.append(text[2:])
    return found


def _cat_reads_a_file(words: list[Word]) -> bool:
    """True when ``cat`` reads a file: a file operand, or an input redirection from a file
    (before or after ``cat``). Here-documents and here-strings (``<<EOF``, ``<<<``), output
    redirections, descriptor copies (``<&3``), options and ``-`` (standard input) do not
    read a file. After ``--`` every word is an operand; a quoted word is never a
    redirection (``cat '<<notes'`` reads the file ``<<notes``)."""
    k = 0
    operands = False
    while k < len(words):
        word = words[k]
        redirection = _redirection(word)
        if redirection:
            operator, target = redirection
            if operator in ("<", "<>"):
                return True
            k += 1 if target else 2
            continue
        text = word.text
        if not operands and text == "--":
            operands = True
        elif text == "-" or (not operands and text.startswith("-")):
            pass  # standard input, or an option
        else:
            return True
        k += 1
    return False


def _git_long(arg: str, names: list[str]) -> str | None:
    """The long option a word names: itself, or the one known name it abbreviates (git
    accepts an unambiguous prefix); None when it is unknown or ambiguous."""
    name = arg.split("=", 1)[0].lower()
    if name in names:
        return name
    matches = [n for n in names if n.startswith(name)]
    return matches[0] if len(matches) == 1 else None


def _git_flags(sub: str, rest: list[str]) -> list[str]:
    """The options of a git subcommand that decide whether it commits, in order, with
    option values skipped (``-m --no-commit`` is a message, not an option)."""
    values = GIT_SUB_VALUE_OPTIONS.get(sub, set())
    names = GIT_SUB_FLAGS.get(sub, []) + sorted(v for v in values if v.startswith("--"))
    flags: list[str] = []
    k = 0
    while k < len(rest):
        arg = rest[k]
        if arg == "--":
            break
        if arg.startswith("--"):
            name = _git_long(arg, names)
            if name in values and "=" not in arg:
                k += 2
                continue
            if name:
                flags.append(name)
            k += 1
            continue
        if arg.startswith("-") and len(arg) > 1:  # a cluster of short options: -nx, -m1
            for pos in range(1, len(arg)):
                option = "-" + arg[pos]
                if option in values:
                    if pos == len(arg) - 1:
                        k += 1  # the value is the next word
                    break
                if option == "-S":  # -S[keyid]: the rest is its value
                    break
                flags.append(option)
        k += 1
    return flags


def _git_commit_reason(args: list[str], depth: int = 0) -> str | None:
    """COMMIT_REASON (or another reason) when the git command would create a commit by
    itself."""
    if depth > 8:
        return "the git aliases nest too deeply to be checked"
    aliases: dict[str, str] = {}
    k = 0
    while k < len(args) and args[k].startswith("-"):
        option = args[k]
        if option.startswith("--config-env"):
            value = option.split("=", 1)[1] if "=" in option else ""
            if not value and k + 1 < len(args):
                value = args[k + 1]
            if value.lower().startswith("alias."):
                return "a git alias given with --config-env cannot be checked"
        if option == "-c" and k + 1 < len(args):
            key, _, value = args[k + 1].partition("=")
            if key.lower().startswith("alias."):
                aliases[key[len("alias.") :].lower()] = value
        k += 2 if option in GIT_VALUE_OPTIONS else 1
    if k >= len(args):
        return None
    sub, rest = args[k].lower(), args[k + 1 :]
    if sub in aliases:
        expansion = aliases[sub]
        if expansion.startswith("!"):  # a shell command, given the rest as arguments
            return check(" ".join([expansion[1:], *rest]), depth + 1, BASH)
        words = [w.text for segment in lex(expansion).segments for w in segment]
        return _git_commit_reason([*args[:k], *words, *rest], depth + 1)
    if sub == "commit":
        return COMMIT_REASON
    flags = _git_flags(sub, rest)
    if sub == "merge":
        if {"--abort", "--quit"} & set(flags):
            return None
        no_commit = squash = False
        for flag in flags:
            if flag in ("--commit", "--no-commit"):
                no_commit = flag == "--no-commit"
            elif flag in ("--squash", "--no-squash"):
                squash = flag == "--squash"
        return None if (no_commit or squash) and "--continue" not in flags else COMMIT_REASON
    if sub in ("cherry-pick", "revert"):
        if {"--abort", "--quit"} & set(flags):
            return None
        no_commit = False
        for flag in flags:
            if flag in ("--commit", "--no-commit", "-n"):
                no_commit = flag != "--commit"
        commits = "--continue" in flags or "--skip" in flags  # both go on with the sequence
        return None if no_commit and not commits else COMMIT_REASON
    if sub == "pull":
        mode, rebase = "", False
        for flag in flags:
            if flag in ("--ff-only", "--ff", "--no-ff"):
                mode = flag
            elif flag in ("--rebase", "-r", "--no-rebase"):
                rebase = flag != "--no-rebase"
        return None if mode == "--ff-only" and not rebase else COMMIT_REASON
    return None


def _ps_parameter(arg: str, names: dict[str, str] | tuple[str, ...]) -> list[str]:
    """The parameter names a PowerShell argument can mean: itself, or the names it is a
    prefix of (PowerShell accepts an unambiguous prefix)."""
    name = arg.lower().split(":", 1)[0]
    if name.startswith("/"):
        name = "-" + name[1:]
    if name in names:
        return [name]
    return [n for n in names if n.startswith(name)] if len(name) > 1 else []


def _powershell_code(args: list[str]) -> tuple[str, str]:
    """What a ``powershell``/``pwsh`` command line runs: ("code", text), ("file", ""),
    ("stdin", ""), ("encoded", "") or ("none", "") when it would start an interactive
    shell or read standard input."""
    k = 0
    while k < len(args):
        arg = args[k]
        name = arg.lower().split(":", 1)[0]
        if name.startswith("/"):
            name = "-" + name[1:]
        if name == "-":
            return "stdin", ""
        if not name.startswith("-") or len(name) == 1:
            return "code", " ".join(args[k:])  # Windows PowerShell's default is -Command
        if name in ("-e", "-ec") or (
            len(name) > 2
            and ("-encodedcommand".startswith(name) or "-encodedarguments".startswith(name))
        ):
            return "encoded", ""
        if "-command".startswith(name):  # -c, -co, -com, ... (checked before -ConfigurationName)
            if k + 1 >= len(args):
                return "none", ""
            code = " ".join(args[k + 1 :])
            return ("stdin", "") if code == "-" else ("code", code)
        if "-file".startswith(name):
            return ("stdin", "") if k + 1 < len(args) and args[k + 1] == "-" else ("file", "")
        if name in PS_EXE_VALUE_SHORT or _ps_parameter(name, PS_EXE_VALUE_PARAMETERS):
            k += 1 if ":" in arg else 2
            continue
        k += 1  # a switch: -NoProfile, -NonInteractive, ...
    return "none", ""


def _reads_code_from_stdin(words: list[Word]) -> bool:
    """A shell that reads its commands from standard input: ``bash``/``sh`` with no ``-c``
    and no script (or with ``-s``), ``powershell``/``pwsh`` with ``-Command -``, ``-File -``
    or no command, ``cmd`` with no ``/c`` or ``/k``."""
    start = _command_index(words)
    if start is None:
        return False
    name = _name(words[start].text)
    rest = words[start + 1 :]
    args = [w.text for w in rest]
    if name in SHELLS:
        k = 0
        while k < len(rest):
            arg = args[k]
            if _redirection(rest[k]):
                k += 1 if _redirection(rest[k])[1] else 2
                continue
            if arg.startswith("--"):
                k += 1
                continue
            if arg[:1] in "-+" and len(arg) > 1:
                if "c" in arg[1:]:
                    return False
                if "s" in arg[1:]:
                    return True
                k += 2 if arg[-1] in "oO" else 1  # -o OPTION, -O SHOPT
                continue
            return False  # a script file
        return True
    if name in POWERSHELLS:
        return _powershell_code(args)[0] in ("stdin", "none")
    if name == "cmd":
        return not any(a.lower() in ("/c", "/k") for a in args)
    return False


PYTEST_REASON = (
    "pytest runs only through scripts/run_tests_affinity.ps1 (affinity 8-31, JUnit XML): "
    "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_tests_affinity.ps1 "
    "-Junit .cache/<task>/junit.xml [-Tests a.py,b.py]"
)


def _check_segment(words: list[Word], depth: int, shell: str) -> str | None:
    start = _command_index(words)
    for split in _env_split_strings(words, len(words) if start is None else start):
        tail = [w.text for w in words[start:]] if start is not None else []
        reason = check(" ".join([split, *tail]), depth + 1, BASH)
        if reason:
            return reason
    if start is None:
        return None
    if shell == POWERSHELL and start == 0 and words[0].quoted:
        # a string that opens a PowerShell statement is a value, not a call; after '&',
        # '.' or a prefix program (env.exe 'git' ...) it is the program, and is checked
        return None
    rest = words[start:]
    name = _name(rest[0].text)
    args = [w.text for w in rest[1:]]
    lowered = [a.lower() for a in args]
    if name in READ_TOOLS:
        return _refuse_read(name)
    if shell == BASH and name in BASH_READ_TOOLS:
        return _refuse_read(name)
    if (
        shell == BASH
        and name == "cat"
        and _cat_reads_a_file(_leading_redirections(words, start) + rest[1:])
    ):
        return _refuse_read(name)
    if name == "git":  # redirections anywhere (git 2>/dev/null commit) are not arguments
        reason = _git_commit_reason([w.text for w in _drop_redirections(rest[1:])], depth)
        if reason:
            return reason
    shell_program = name in SHELLS and _reads_code_from_stdin(words)
    if shell_program or _reads_python_stdin(words):  # a <<< here-string is the program
        around = _leading_redirections(words, start) + rest[1:]  # before or after the name
        for k, word in enumerate(around):
            redirection = _redirection(word)
            if not redirection or redirection[0] != "<<<":
                continue
            body = redirection[1] or (around[k + 1].text if k + 1 < len(around) else "")
            if shell_program:
                reason = check(body, depth + 1, BASH)
                if reason:
                    return reason
            elif _python_uses_pytest(body):
                return PYTEST_REASON
    if name in PYTEST_WORDS:
        return PYTEST_REASON
    if _is_python(name):
        k = 0
        while k < len(args):  # what follows -c CODE, -m MODULE or a script is argv
            arg = args[k]
            if arg == "--check-hash-based-pycs":
                k += 2
                continue
            if not arg.startswith("-") or arg in ("-", "--"):
                break
            if arg.startswith("--"):
                k += 1
                continue
            stop = False
            for pos in range(1, len(arg)):  # a cluster of short options: -Bm, -mpytest
                option = arg[pos]
                if option in "mcWX":
                    value = arg[pos + 1 :]
                    if not value:
                        k += 1
                        value = args[k] if k < len(args) else ""
                    if option == "m" and value.lower() in PYTEST_WORDS:
                        return PYTEST_REASON
                    if option == "c" and _python_uses_pytest(value):
                        return PYTEST_REASON
                    stop = option in "mc"
                    break
            if stop:
                break
            k += 1
    if name in SHELLS:
        for k, arg in enumerate(args):
            if re.fullmatch(r"-[a-z]*c[a-z]*", arg) and k + 1 < len(args):
                return check(args[k + 1], depth + 1, BASH)
    if name in POWERSHELLS:
        kind, code = _powershell_code(args)
        if kind == "encoded":
            return "an encoded PowerShell command cannot be checked; write it in clear"
        if kind == "stdin":
            return STDIN_REASON
        if kind == "code":
            return check(code, depth + 1, POWERSHELL)
    if name == "cmd":
        for k, arg in enumerate(lowered):
            if arg in ("/c", "/k") and k + 1 < len(args):
                return check(" ".join(args[k + 1 :]), depth + 1, CMD)
    if name == "eval" and args:
        return check(" ".join(args), depth + 1, BASH)
    if name in ("invoke-expression", "iex") and args:
        return check(" ".join(args), depth + 1, POWERSHELL)
    if name in ("start-process", "saps", "start"):
        target, arglist = "", ""
        positional = []
        k = 0
        while k < len(args):
            arg = args[k]
            if not (arg.startswith("-") and len(arg) > 1):
                positional.append(arg)  # position 0 is the program, 1 its arguments
                k += 1
                continue
            kinds = {
                START_PROCESS_PARAMETERS[n] for n in _ps_parameter(arg, START_PROCESS_PARAMETERS)
            }
            kind = kinds.pop() if len(kinds) == 1 else "flag"
            if kind == "flag":
                k += 1
                continue
            if ":" in arg:  # -ArgumentList:'...'
                parts = [arg.split(":", 1)[1]]
                k += 1
            else:
                parts = [args[k + 1]] if k + 1 < len(args) else []
                k += 2
            while kind == "args" and parts and parts[-1].endswith(",") and k < len(args):
                parts.append(args[k])  # 'a', 'b', ...
                k += 1
            if kind == "file" and parts:
                target = parts[0]
            elif kind == "args":
                arglist = " ".join(parts)
        if not target and positional:
            target = positional.pop(0)
        if not arglist and positional:
            arglist = positional[0]
        if arglist.startswith("@(") and arglist.endswith(")"):
            arglist = arglist[2:-1]
        arglist = arglist.replace(",", " ")
        if target:
            # the target is one word even with blanks; the argument list is lexed
            # again, so a quoted argument (for example the code of -c) stays whole
            words = [w for seg in lex(arglist, POWERSHELL).segments for w in seg]
            return _check_segment([Word("&"), Word(target, quoted=True), *words], depth + 1, shell)
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
    if shell == POWERSHELL and "\\" in command:
        return BACKSLASH_REASON
    lexed = lex(command, shell)
    for n, words in enumerate(lexed.segments):
        reason = _check_segment(words, depth, shell)
        if reason:
            return reason
        if n and lexed.separators[n - 1] == "|" and _reads_code_from_stdin(words):
            return STDIN_REASON
    for n, words in enumerate(lexed.segments):  # @'...'@ | python -
        piped = n + 1 < len(lexed.segments) and lexed.separators[n] == "|"
        if not piped or not _reads_python_stdin(lexed.segments[n + 1]):
            continue
        for w in words:
            m = re.fullmatch(r"__HERESTRING_(\d+)__", w.text)
            if m and _python_uses_pytest(lexed.herestrings[int(m.group(1))]):
                return PYTEST_REASON
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
