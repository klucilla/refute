"""v0.5.5 R2: the blind review's bundle (#218; the maintainer's decisions of 2026-11-21, 13:30,
item 4; charter (d)3; amendment 1 (f)). ``method_status: not_validated``.

Builds the **second** bundle (the maintainer's decisions of 2026-11-21, 15:20) **from an allowlist
only** into ``.cache/v055/r2/bundle-2/`` and writes its SHA-256 manifest **before any review**
(``docs/validation/v0.5.5/r2-bundle-2-manifest.json``); the first bundle keeps its folder and its
manifest. It launches no reviewer: the blind review is launched by the maintainer's adviser, read
only, with a new session.

**What goes in** (the decisions' item 4): the design questions, the proposed rules and the
arguments, carried by ``docs/plans/v0.5.5-r2-arguments.md`` **cut at its disclosure section**
(that section and everything after it are left out); the code's semantics,
``docs/plans/v0.5.5-r2-code-semantics.md``; the targets defined without counts,
``docs/plans/v0.5.5-r2-targets.md``; and the frozen rules, as the source files that define them
(the aggregation, the coverage and sensitivity rules, the registry, the parameters, the test lists,
the tests that the questions touch, and how C1's and C2's targets are counted). **A review copy**
replaces one comment of ``calib05/values.py`` that states a historical acceptance outcome
(``REVIEW_COPIES``); the manifest declares the transformation, the source's hash and the delivered
hash; the frozen source is not changed. **What stays out:**
the disclosure section, every forecast, every record of R1 and of v0.5 to v0.5.5, the questions
draft (it cites results), the plan, the reports, the ledger and the consensus answers.

**The leak check** (a guard, not a proof of blinding; the final bytes are also read in context
before the bundle is released): the bundle is refused if its argument file still holds the
disclosure heading, or if any bundled file matches a pattern of results or retrospective
reference (record file names, R1's checks, forecast terms, known phrases); **the manifest
itself is checked before its first write**. The source files are bundled byte for byte, except
the review copy declared in the manifest; they are the frozen rules themselves. ``check``
compares the delivered manifest with the recorded one, and every file in the bundle (only the
manifest's exact path left out) with the manifest.

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
# the second bundle (the decisions of 2026-11-21, 15:20); the first one keeps its folder and its
# manifest (``.cache/v055/r2/bundle``, ``r2-bundle-manifest.json``)
OUT = ROOT / ".cache/v055/r2/bundle-2"
MANIFEST = ROOT / "docs/validation/v0.5.5/r2-bundle-2-manifest.json"
ARGUMENTS = "docs/plans/v0.5.5-r2-arguments.md"
DISCLOSURE = "## Disclosure: results known when this was written"
SEMANTICS = "docs/plans/v0.5.5-r2-code-semantics.md"
TARGETS = "docs/plans/v0.5.5-r2-targets.md"
FROZEN_RULES = (
    "src/refute/core/verdict.py",
    "src/refute/core/sensitivity.py",
    "src/refute/packs/tess/params.py",
    "src/refute/packs/tess/pipeline.py",
    "src/refute/packs/tess/pipeline_v52.py",
    "src/refute/packs/tess/power.py",
    "src/refute/packs/tess/battery_v5.py",
    "src/refute/packs/tess/battery_v51.py",
    "src/refute/packs/tess/battery_v51_diff.py",
    "src/refute/packs/tess/battery_v52.py",
    # added after the first blind review (its item 9)
    "src/refute/packs/tess/battery.py",
    "src/refute/packs/tess/centroid_v5.py",
    "src/refute/packs/tess/ebcatalog.py",
    "src/refute/packs/tess/calib05/c1.py",
    "src/refute/packs/tess/calib05/c2.py",
    "src/refute/packs/tess/calib05/values.py",
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
    # retrospective references (Codex, r2args round 1)
    r"was the limit",
    r"lacked power",
    r"objections in the record",
    r"route, if any",
    r"\bround 3\b",
    r"\bI1\b|\bI4\b",
    # directional text (the first blind review, section 0)
    r"\|\s*Helps\s*\|",
    r"relevant to D2",
    r"serves D2",
    r"purpose and also the risk",
    r"eases the power certificate",
    r"planets with only warning-class gaps",
    r"motivated R2",
    r"moves to SURVIVED",
    r"every ambiguous-sinusoid case",
    r"acceptance failed",
    r"whose acceptance",
)


# review copies: the frozen source is kept; the delivered copy replaces an exact text (Codex,
# r2rev round 1: values.py's comment states which tests' acceptance failed)
REVIEW_COPIES = {
    "src/refute/packs/tess/calib05/values.py": (
        "# The roles of the v0.5 battery (the acceptance README and the S2 decisions): every v0.4 "
        "decisive\n# test except centroid_shift (in a v0.5 plan it is the per-sector centroid, not "
        "accepted), plus the\n# accepted v0.5 tests; diagnostic: the tests whose acceptance "
        "failed, and the holdout.\n",
        "# The roles of the tests in the v0.5 battery.\n",
    ),
}


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
    files = {
        "arguments.md": arguments_cut(),
        "code-semantics.md": (ROOT / SEMANTICS).read_bytes(),
        "targets.md": (ROOT / TARGETS).read_bytes(),
    }
    for rel in FROZEN_RULES:
        data = (ROOT / rel).read_bytes()
        if rel in REVIEW_COPIES:
            old, new = REVIEW_COPIES[rel]
            text = data.decode("utf-8")
            if text.count(old) != 1:
                raise SystemExit(f"{rel}: the review copy's text is not found once: refused")
            data = text.replace(old, new).encode("utf-8")
        files["frozen-rules/" + rel] = data
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
                "cut_at": "the heading of the arguments' last section (charter (d)6); that "
                "section and everything after it are left out",
            },
            "code-semantics.md": {
                "from": SEMANTICS,
                "source_sha256": _sha((ROOT / SEMANTICS).read_bytes()),
            },
            "targets.md": {
                "from": TARGETS,
                "source_sha256": _sha((ROOT / TARGETS).read_bytes()),
            },
            **{
                "frozen-rules/" + rel: {
                    "from": rel,
                    "source_sha256": _sha((ROOT / rel).read_bytes()),
                    **(
                        {
                            # Codex, r2rev round 2: the removed text is not republished here
                            "review_copy": "the comment immediately before V05_DECISIVE is "
                            "replaced in the review copy; the frozen source is unchanged",
                            "delivered_sha256": _sha(files["frozen-rules/" + rel]),
                        }
                        if rel in REVIEW_COPIES
                        else {}
                    ),
                }
                for rel in FROZEN_RULES
            },
        },
        "files": {name: _sha(data) for name, data in sorted(files.items())},
        "excluded": "the disclosure section; every prediction, count and record of the earlier "
        "versions; the questions draft; the plan; the reports; the ledger; the consensus",
        "reviewer": "not launched by this script; the maintainer's adviser launches the blind "
        "review, read only, with no clone, no history and no network",
    }
    text = json.dumps(manifest, indent=1, sort_keys=True) + "\n"
    found = leaks("MANIFEST.json", text.encode("utf-8"))  # before the first write
    if found:
        raise SystemExit("the manifest would leak: " + "; ".join(found))
    MANIFEST.write_text(text, "utf-8", newline="\n")
    for name, data in files.items():
        path = OUT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (OUT / "MANIFEST.json").write_bytes(MANIFEST.read_bytes())
    return manifest


def check() -> dict:
    """Every bundled file against the manifest, and no file outside it."""
    manifest = json.loads(MANIFEST.read_text("utf-8"))
    if (OUT / "MANIFEST.json").read_bytes() != MANIFEST.read_bytes():
        raise SystemExit("the delivered manifest differs: a STOP")
    on_disk = {
        p.relative_to(OUT).as_posix(): _sha(p.read_bytes())
        for p in OUT.rglob("*")
        if p.is_file() and p != OUT / "MANIFEST.json"  # only the exact path is left out
    }
    if on_disk != manifest["files"]:
        raise SystemExit("the bundle differs from its manifest: a STOP")
    return {"files": len(on_disk), "ok": True}


if __name__ == "__main__":
    print(json.dumps({"build": build, "check": check}[sys.argv[1]](), indent=1))
