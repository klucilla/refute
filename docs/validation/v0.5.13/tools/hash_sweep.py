"""A read-only sweep of the SHA-256 recorded in this phase's files (the maintainer's decision G9,
#218 comment 7219469262).

    unit hash-sweep:  {python} -I -B docs/validation/v0.5.13/tools/hash_sweep.py

**Scope.** The tracked files under ``docs/validation/v0.5.13/`` and ``docs/plans/v0.5.13-*``,
including the review packages. A recorded SHA-256 (64 hex digits) is paired with a tracked file
as follows.
- **JSON and JSONL.** It pairs:
  - an object key that is a tracked path, with its 64-hex value;
  - an object holding exactly one tracked path among its string values, with every 64-hex value
    in it.
- **Text** (Markdown and others). On one line, the candidate paths are the backticked tokens and
  link targets. Each is resolved first against the recording file's own folder, then against the
  repository root. If exactly one candidate is tracked, it is paired with every 64-hex on that
  line.
- Anything else (several paths, or none) is counted as "not paired" and not compared.

**Comparison.** Each pair is compared with the SHA-256 of the bytes of the path's blob at
``HEAD``. A divergence is classified as:
- ``crlf-of-head``: the SHA-256 of the HEAD blob with LF turned into CRLF;
- ``earlier-version``: the SHA-256 of an earlier committed version of that path (the commit is
  named);
- ``no-match``: neither of the above.
Divergences are listed, with the recording file, the line or JSON location and both values.
Nothing is corrected. It writes ``out/hash-sweep.json``.
"""

from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HEX = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{64}(?![0-9a-fA-F])")
TOKEN = re.compile(r"`([^`\s]+)`|\]\(([^)\s#]+)")


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


TRACKED = set(git("ls-files", "-z").decode("utf-8").split("\0")) - {""}
_head: dict[str, bytes] = {}
_versions: dict[str, dict[str, str]] = {}


def head_bytes(path: str) -> bytes:
    if path not in _head:
        _head[path] = git("show", f"HEAD:{path}")
    return _head[path]


def versions(path: str) -> dict[str, str]:
    """SHA-256 of each earlier committed version of ``path`` -> the commit (at most 200)."""
    if path not in _versions:
        out: dict[str, str] = {}
        commits = git("log", "--format=%H", "-n", "200", "--", path).decode().split()
        for c in commits:
            try:
                out.setdefault(sha(git("show", f"{c}:{path}")), c)
            except subprocess.CalledProcessError:
                continue
        _versions[path] = out
    return _versions[path]


def resolve(token: str, folder: str) -> str | None:
    token = token.split("#")[0].split("?")[0]
    for cand in (posixpath.normpath(posixpath.join(folder, token)), posixpath.normpath(token)):
        if cand in TRACKED:
            return cand
    return None


def walk(node, where: str, pairs: list, unpaired: list) -> None:
    if isinstance(node, dict):
        strings = {k: v for k, v in node.items() if isinstance(v, str)}
        paths = sorted({v for v in strings.values() if v in TRACKED})
        hexes = [(k, v) for k, v in strings.items() if HEX.fullmatch(v)]
        for k, v in node.items():
            if k in TRACKED and isinstance(v, str) and HEX.fullmatch(v):
                pairs.append((k, v, f"{where}.{k}"))
        keyed = {k for k, v in node.items() if k in TRACKED}
        loose = [(k, v) for k, v in hexes if k not in keyed]
        if loose and len(paths) == 1:
            pairs += [(paths[0], v, f"{where}.{k}") for k, v in loose]
        elif loose:
            unpaired += [f"{where}.{k}" for k, _ in loose]
        for k, v in node.items():
            walk(v, f"{where}.{k}", pairs, unpaired)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, f"{where}[{i}]", pairs, unpaired)


def scan(rel: str) -> tuple[list, list]:
    text = (ROOT / rel).read_bytes().decode("utf-8", errors="replace")
    pairs: list = []
    unpaired: list = []
    if rel.endswith(".json"):
        try:
            walk(json.loads(text), "$", pairs, unpaired)
            return pairs, unpaired
        except ValueError:
            pass
    if rel.endswith(".jsonl"):
        for n, line in enumerate(text.splitlines(), 1):
            try:
                walk(json.loads(line), f"line {n}", pairs, unpaired)
            except ValueError:
                continue
        return pairs, unpaired
    folder = posixpath.dirname(rel)
    for n, line in enumerate(text.splitlines(), 1):
        hexes = HEX.findall(line)
        if not hexes:
            continue
        cands = {resolve(a or b, folder) for a, b in TOKEN.findall(line)} - {None}
        if len(cands) == 1:
            path = cands.pop()
            pairs += [(path, h, f"line {n}") for h in hexes]
        else:
            unpaired += [f"line {n}"] * len(hexes)
    return pairs, unpaired


def main() -> int:
    scope = sorted(p for p in TRACKED if p.startswith("docs/validation/v0.5.13/")
                   or p.startswith("docs/plans/v0.5.13-"))  # fmt: skip
    seen: dict[tuple, list] = defaultdict(list)
    unpaired_total = 0
    for rel in scope:
        pairs, unpaired = scan(rel)
        unpaired_total += len(unpaired)
        for path, value, where in pairs:
            seen[(rel, path, value)].append(where)
    divergences = []
    matched = 0
    for (rel, path, value), wheres in sorted(seen.items()):
        head = head_bytes(path)
        now = sha(head)
        if value == now:
            matched += 1
            continue
        if value == sha(head.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")):
            kind, commit = "crlf-of-head", None
        else:
            commit = versions(path).get(value)
            kind = "earlier-version" if commit else "no-match"
        divergences.append({"recorded_in": rel, "where": wheres[:5], "occurrences": len(wheres),
                            "file": path, "recorded_sha256": value, "head_sha256": now,
                            "kind": kind, "earlier_commit": commit})  # fmt: skip
    counts: dict[str, int] = defaultdict(int)
    for d in divergences:
        counts[d["kind"]] += 1
    report = {"head": git("rev-parse", "HEAD").decode().strip(), "files_scanned": len(scope),
              "pairs": len(seen), "matched_head": matched, "divergences": len(divergences),
              "by_kind": dict(counts), "not_paired": unpaired_total,
              "list": divergences}  # fmt: skip
    out = Path(os.environ.get("REFUTE_RUN_OUT", "."))
    text = json.dumps(report, indent=1) + "\n"
    (out / "hash-sweep.json").write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in report.items() if k != "list"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
