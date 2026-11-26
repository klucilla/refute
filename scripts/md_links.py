"""Relative link targets in Markdown files: find them, normalize them, re-prefix them.

The maintainer's decision of 2026-11-26, item M2 (#218, comment 7204660147): the links moved
literally into ``docs/history/roadmap-archive.md`` and ``docs/STATUS.md`` were written for the
repository root, and are re-prefixed so that they work from the new folder. This module is the one
place that says what a link target is, so that the rewriting script and the moved-text checker
agree.

**A target** is the destination of a Markdown inline link or image (``](target)``, with an optional
quoted title after it), or the value of an HTML ``src``, ``href`` or ``srcset`` attribute.

**A relative target** is one that does not start with ``#``, ``/`` or ``\\``, and has no scheme
(``https:``, ``mailto:``...). Its path part (before ``#`` or ``?``) is what is re-prefixed; the
fragment and the query are kept as they are.

Lines inside fenced code blocks (between lines starting with three backticks or tildes) are left
alone. A ``srcset`` value with a comma or a space (several candidates) is left alone, and reported
by :func:`targets`.

Standard library only; no network.
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Callable

_MD = re.compile(r"(\]\()([^)\s]+)((?:\s+\"[^\"]*\")?\))")
_HTML = re.compile(r"""(\b(?:src|href|srcset)=)(["'])([^"']*)(\2)""", re.IGNORECASE)
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_FENCE = re.compile(r"^\s*(```|~~~)")


def is_relative(target: str) -> bool:
    return bool(target) and not (
        target.startswith(("#", "/", "\\")) or _SCHEME.match(target) or "," in target
    )


def split_target(target: str) -> tuple[str, str]:
    """The path part and the rest (``#fragment`` or ``?query``, kept as it is)."""
    cut = min((i for i in (target.find("#"), target.find("?")) if i >= 0), default=len(target))
    return target[:cut], target[cut:]


def map_targets(text: str, fn: Callable[[str], str], start_line: int = 0) -> str:
    """``text`` with every relative target ``t`` on lines from ``start_line`` on (0-based)
    replaced by ``fn(t)``; fenced code is left alone."""
    out = []
    fenced = False
    for n, line in enumerate(text.split("\n")):
        if _FENCE.match(line):
            fenced = not fenced
            out.append(line)
            continue
        if fenced or n < start_line:
            out.append(line)
            continue

        def md(m: re.Match[str]) -> str:
            t = m.group(2)
            return m.group(1) + (fn(t) if is_relative(t) else t) + m.group(3)

        def html(m: re.Match[str]) -> str:
            t = m.group(3)
            return m.group(1) + m.group(2) + (fn(t) if is_relative(t) else t) + m.group(4)

        out.append(_HTML.sub(html, _MD.sub(md, line)))
    return "\n".join(out)


def targets(text: str, start_line: int = 0) -> list[tuple[int, str]]:
    """Every relative target, with its 1-based line number."""
    found: list[tuple[int, str]] = []
    fenced = False
    for n, line in enumerate(text.split("\n")):
        if _FENCE.match(line):
            fenced = not fenced
            continue
        if fenced or n < start_line:
            continue
        found += [(n + 1, m.group(2)) for m in _MD.finditer(line) if is_relative(m.group(2))]
        found += [(n + 1, m.group(3)) for m in _HTML.finditer(line) if is_relative(m.group(3))]
    return found


def to_root(target: str, file_dir: str) -> str:
    """The repository-root form of a relative target written in a file under ``file_dir``
    (``""`` for the root)."""
    path, rest = split_target(target)
    if not path:
        return target
    norm = posixpath.normpath(posixpath.join(file_dir, path))
    if path.endswith("/") and not norm.endswith("/"):
        norm += "/"
    return norm + rest


def from_root(target: str, file_dir: str) -> str:
    """A repository-root target written so that it works from a file under ``file_dir``."""
    path, rest = split_target(target)
    if not path:
        return target
    rel = posixpath.relpath(posixpath.normpath(path), file_dir or ".")
    if path.endswith("/") and not rel.endswith("/"):
        rel += "/"
    return rel + rest


def normalize(text: str, file_dir: str) -> str:
    """``text`` with every relative target in its repository-root form."""
    return map_targets(text, lambda t: to_root(t, file_dir))
