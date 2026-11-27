"""Prepare the clean copy for G1's one approved rerun of check-f2, resumed by the maintainer's
decision G7 (#218 comment 7219469262).

    unit g7-prepare:  {python} -I -B docs/validation/v0.5.13/tools/g7_prepare.py

0. **The discarded copy.** It deletes the old export ``.cache/v0513/g1`` by that literal path,
   after a guard that the path resolves inside ``<project>/.cache/``.
1. **The tip.** It reads ``main`` and ``origin/main`` and refuses if they differ.
2. **The export.** ``git archive`` of that exact commit is extracted into the NEW folder
   ``.cache/v0513/g7/tree`` (refused if it exists).
3. **The F2 files.** These are copied in byte for byte, with each SHA-256 recorded for source and
   destination:
   - ``pyproject.toml`` from ``.cache/v0513/f2/pyproject.f2.toml``;
   - ``scripts/make_pypi_readme.py``, ``README-pypi.md`` and ``tests/test_pypi_readme.py`` from
     the working tree.
4. **The CRLF check.** No file of the copy may contain CRLF unless one of these holds:
   - its path is one that ``.gitattributes`` marks ``-text`` or ``binary``;
   - git treats it as binary, that is, ``git ls-files --eol`` shows ``i/-text`` for it (the only
     exemption G7 adds).
   Each exempted file is listed with its reason.

It writes ``out/g7-prepare.json`` and exits 0 only if every step holds.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OLD = ROOT / ".cache" / "v0513" / "g1"
DEST = ROOT / ".cache" / "v0513" / "g7" / "tree"
COPIES = [
    ("pyproject.toml", ".cache/v0513/f2/pyproject.f2.toml"),
    ("scripts/make_pypi_readme.py", "scripts/make_pypi_readme.py"),
    ("README-pypi.md", "README-pypi.md"),
    ("tests/test_pypi_readme.py", "tests/test_pypi_readme.py"),
]

_G1 = Path(__file__).with_name("g1_prepare.py")
_spec = importlib.util.spec_from_file_location("g1_prepare", _G1)
g1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g1)


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def index_binary() -> set[str]:
    out = set()
    for line in git("ls-files", "--eol").decode("utf-8").splitlines():
        fields, _, path = line.partition("\t")
        if "i/-text" in fields.split():
            out.add(path)
    return out


def main() -> int:
    report: dict = {"steps": {}}
    cache = (ROOT / ".cache").resolve()
    old = OLD.resolve()
    deleted = False
    if old.exists():
        if not old.is_relative_to(cache) or old == cache:
            raise SystemExit(f"refused: {old} is not inside {cache}")
        shutil.rmtree(old)
        deleted = not old.exists()
    report["old_copy"] = {"path": ".cache/v0513/g1", "deleted": deleted}
    tip = git("rev-parse", "main").decode().strip()
    origin = git("rev-parse", "origin/main").decode().strip()
    report.update(main=tip, origin_main=origin)
    report["steps"]["tip_matches_origin"] = tip == origin
    if tip == origin:
        if DEST.exists():
            raise SystemExit(f"refused: {DEST} exists; G7 needs a new folder")
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
        patterns = g1.not_text_patterns((DEST / ".gitattributes").read_text(encoding="utf-8"))
        binary = index_binary()
        files = sorted(p for p in DEST.rglob("*") if p.is_file())
        crlf = [p.relative_to(DEST).as_posix() for p in files if b"\r\n" in p.read_bytes()]
        exempt, outside = [], []
        for rel in crlf:
            if g1.exempt(rel, patterns):
                exempt.append({"path": rel, "reason": ".gitattributes -text or binary"})
            elif rel in binary:
                exempt.append({"path": rel, "reason": "git ls-files --eol: i/-text"})
            else:
                outside.append(rel)
        report.update(files=len(files), crlf_files=len(crlf),
                      exempt_by_index_binary=[e for e in exempt if e["reason"].startswith("git")],
                      crlf_outside=outside)  # fmt: skip
        report["steps"]["no_crlf_outside_exemptions"] = not outside
    report["all_ok"] = len(report["steps"]) == 3 and all(report["steps"].values())
    out = Path(os.environ.get("REFUTE_RUN_OUT", "."))
    text = json.dumps(report, indent=1) + "\n"
    (out / "g7-prepare.json").write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({"main": tip, **report["steps"], "all_ok": report["all_ok"]}))
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
