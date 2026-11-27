"""Prepare the clean copy for the one approved rerun of check-f2 (the maintainer's decision G1,
#218 comment 7219180143).

    unit g1-prepare:  {python} -I -B docs/validation/v0.5.13/tools/g1_prepare.py

1. **The tip.** It reads the commit of ``main`` and of ``origin/main``, and refuses if they differ.
2. **The export.** ``git archive`` of that exact commit is extracted into the NEW folder
   ``.cache/v0513/g1/tree`` (refused if the folder exists). Nothing is read from the working tree
   for the export.
3. **The F2 files.** They are copied in byte for byte, with each SHA-256 recorded for source and
   destination:
   - ``pyproject.toml`` from ``.cache/v0513/f2/pyproject.f2.toml``;
   - ``scripts/make_pypi_readme.py``, ``README-pypi.md`` and ``tests/test_pypi_readme.py`` from
     the working tree.
4. **The CRLF check.** No file of the copy may contain CRLF outside the paths that
   ``.gitattributes`` marks ``-text`` or ``binary``.

It writes ``out/g1-prepare.json`` and exits 0 only if every step holds.
"""

from __future__ import annotations

import fnmatch
import hashlib
import io
import json
import os
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DEST = ROOT / ".cache" / "v0513" / "g1" / "tree"
COPIES = [
    ("pyproject.toml", ".cache/v0513/f2/pyproject.f2.toml"),
    ("scripts/make_pypi_readme.py", "scripts/make_pypi_readme.py"),
    ("README-pypi.md", "README-pypi.md"),
    ("tests/test_pypi_readme.py", "tests/test_pypi_readme.py"),
]


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def not_text_patterns(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and not line.lstrip().startswith("#"):
            if "-text" in parts[1:] or "binary" in parts[1:]:
                out.append(parts[0])
    return out


def exempt(rel: str, patterns: list[str]) -> bool:
    for pat in patterns:
        if pat.endswith("/**"):
            prefix = pat[:-3]
            if "*" in prefix:
                if fnmatch.fnmatchcase(rel, pat.replace("/**", "/*")) or any(
                    fnmatch.fnmatchcase("/".join(rel.split("/")[:k]), prefix)
                    for k in range(1, rel.count("/") + 1)
                ):
                    return True
            elif rel.startswith(prefix + "/"):
                return True
        elif "/" not in pat and fnmatch.fnmatchcase(rel.rsplit("/", 1)[-1], pat):
            return True
        elif fnmatch.fnmatchcase(rel, pat):
            return True
    return False


def main() -> int:
    tip = git("rev-parse", "main").decode().strip()
    origin = git("rev-parse", "origin/main").decode().strip()
    report: dict = {"main": tip, "origin_main": origin, "steps": {}}
    ok = tip == origin
    report["steps"]["tip_matches_origin"] = ok
    if ok:
        if DEST.exists():
            raise SystemExit(f"refused: {DEST} exists; G1 needs a new folder")
        DEST.mkdir(parents=True)
        archive = git("archive", "--format=tar", tip)
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(DEST, filter="data")
        report["archive_sha256"] = sha(archive)
        copies = []
        for dest_rel, src_rel in COPIES:
            data = (ROOT / src_rel).read_bytes()
            target = DEST / dest_rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            back = target.read_bytes()
            copies.append({"destination": dest_rel, "source": src_rel, "bytes": len(data),
                           "source_sha256": sha(data), "destination_sha256": sha(back),
                           "equal": back == data})  # fmt: skip
        report["copies"] = copies
        report["steps"]["copies_byte_for_byte"] = all(c["equal"] for c in copies)
        patterns = not_text_patterns((DEST / ".gitattributes").read_text(encoding="utf-8"))
        report["not_text_patterns"] = patterns
        files = sorted(p for p in DEST.rglob("*") if p.is_file())
        crlf = [p.relative_to(DEST).as_posix() for p in files if b"\r\n" in p.read_bytes()]
        outside = [r for r in crlf if not exempt(r, patterns)]
        report["files"] = len(files)
        report["crlf_files"] = len(crlf)
        report["crlf_outside_not_text"] = outside
        report["steps"]["no_crlf_outside_not_text"] = not outside
    report["all_ok"] = all(report["steps"].values()) and len(report["steps"]) == 3
    out = Path(os.environ.get("REFUTE_RUN_OUT", "."))
    (out / "g1-prepare.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"main": tip, **report["steps"], "all_ok": report["all_ok"]}))
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
