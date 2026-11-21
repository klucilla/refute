"""v0.5.5 R2: the blind review's bundle (#218; the maintainer's decisions of 2026-11-21, 13:30,
item 4; charter (d)3; amendment 1 (f)). ``method_status: not_validated``.

Builds the bundle **from an allowlist only** into ``.cache/v055/r2/bundle/`` and writes its SHA-256
manifest **before any review** (``docs/validation/v0.5.5/r2-bundle-manifest.json``). It launches no
reviewer: the blind review is launched by the maintainer's adviser, read only.

**What goes in** (the decisions' item 4): the design questions, the code's semantics, the
proposed rules and the arguments, all carried by ``docs/plans/v0.5.5-r2-arguments.md`` **cut at
its disclosure section** (that section and everything after it are left out); and the frozen
rules, as the source files that define them (the verdict aggregation, the battery's test table and
severities, the background block, the sinusoid test and the power policy). **What stays out:**
the disclosure section, every forecast, every record of R1 and of v0.5 to v0.5.5, the questions
draft (it cites results), the plan, the reports, the ledger and the consensus answers.

**The leak check** (a guard, not a proof): the bundle is refused if its argument file still holds
the disclosure heading, or if any bundled file names a record of results (a list of patterns:
record file names, R1's checks, the plan's forecast terms). The source files are bundled byte for
byte; they are the frozen rules themselves.

Usage: ``.venv/Scripts/python.exe -B docs/validation/v0.5.5/r2_bundle.py build`` (refuses an
existing bundle), ``... check`` (re-hashes the bundle against the manifest).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / ".cache/v055/r2/bundle"
MANIFEST = ROOT / "docs/validation/v0.5.5/r2-bundle-manifest.json"
ARGUMENTS = "docs/plans/v0.5.5-r2-arguments.md"
DISCLOSURE = "## Disclosure: results known when this was written"
FROZEN_RULES = (
    "src/refute/core/verdict.py",
    "src/refute/packs/tess/pipeline.py",
    "src/refute/packs/tess/battery_v51_diff.py",
    "src/refute/packs/tess/battery_v52.py",
    "src/refute/packs/tess/power.py",
)
LEAKS = (
    r"d2f-A",
    r"t2ae-[12]",
    r"d1p-A",
    r"\bD2-F\b",
    r"\bT2a-E\b",
    r"\bD1-P\b",
    r"closing-record",
    r"g1-report",
    r"pause-record",
    r"\bforecast(s|ed)?\b",
    r"98 (kept )?against 97",
    r"14 against 13",
    r"empirically limited",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def arguments_cut() -> bytes:
    """The arguments document up to (not including) its disclosure section."""
    text = (ROOT / ARGUMENTS).read_text("utf-8")
    if text.count(DISCLOSURE) != 1:
        raise SystemExit("the arguments document must hold exactly one disclosure heading")
    cut = text.split(DISCLOSURE)[0].rstrip() + "\n"
    return cut.encode("utf-8")


def leaks(name: str, data: bytes) -> list[str]:
    text = data.decode("utf-8", errors="replace")
    found = [p for p in LEAKS if re.search(p, text, flags=re.IGNORECASE)]
    if DISCLOSURE in text:
        found.append("the disclosure heading")
    return [f"{name}: {p}" for p in found]


def contents() -> dict[str, bytes]:
    files = {"arguments.md": arguments_cut()}
    for rel in FROZEN_RULES:
        files["frozen-rules/" + rel] = (ROOT / rel).read_bytes()
    return files


def build() -> dict:
    """The bundle and its manifest, written once; refused on any leak."""
    if OUT.exists() or MANIFEST.exists():
        raise SystemExit("the bundle or its manifest exists: a bundle is built once")
    files = contents()
    found = [x for name, data in files.items() for x in leaks(name, data)]
    if found:
        raise SystemExit("the bundle would leak: " + "; ".join(found))
    manifest = {
        "label": "v0.5.5 R2: the blind review's bundle (charter (d)3; amendment 1 (f))",
        "method_status": "not_validated",
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "builder": "docs/validation/v0.5.5/r2_bundle.py",
        "builder_sha256": _sha(Path(__file__).read_bytes()),
        "sources": {
            "arguments.md": {
                "from": ARGUMENTS,
                "source_sha256": _sha((ROOT / ARGUMENTS).read_bytes()),
                "cut_at": DISCLOSURE,
            },
            **{
                "frozen-rules/" + rel: {
                    "from": rel,
                    "source_sha256": _sha((ROOT / rel).read_bytes()),
                }
                for rel in FROZEN_RULES
            },
        },
        "files": {name: _sha(data) for name, data in sorted(files.items())},
        "excluded": "the disclosure section; every forecast, count and record of v0.5 to v0.5.5 "
        "(R1 included); the questions draft; the plan; the reports; the ledger; the consensus",
        "reviewer": "not launched by this script; the maintainer's adviser launches the blind "
        "review, read only, with no clone, no history and no network",
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n"
    )
    for name, data in files.items():
        path = OUT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (OUT / "MANIFEST.json").write_bytes(MANIFEST.read_bytes())
    return manifest


def check() -> dict:
    """Every bundled file against the manifest, and no file outside it."""
    manifest = json.loads(MANIFEST.read_text("utf-8"))
    on_disk = {
        p.relative_to(OUT).as_posix(): _sha(p.read_bytes())
        for p in OUT.rglob("*")
        if p.is_file() and p.name != "MANIFEST.json"
    }
    if on_disk != manifest["files"]:
        raise SystemExit("the bundle differs from its manifest: a STOP")
    return {"files": len(on_disk), "ok": True}


if __name__ == "__main__":
    print(json.dumps({"build": build, "check": check}[sys.argv[1]](), indent=1))
