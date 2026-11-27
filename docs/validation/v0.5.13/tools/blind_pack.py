"""Build the blind-review package of amendment 2, revision 3 (the maintainer's decision F1, #218
comment 7218843893): byte-for-byte copies only, then a MANIFEST.md with each file's SHA-256.

    unit blind-pack:  {python} -I -B docs/validation/v0.5.13/tools/blind_pack.py <issue-231 export>

- Whole files are read from git objects at named commits (``git show <commit>:<path>``), never
  from the working tree, and the three named texts are checked against their known SHA-256.
- Excerpts are the exact bytes of the named line ranges of a file at the named commit.
- The export of #231 (the ``gh issue view`` output of a metered unit) is copied byte for byte.
- ``PROMPT.md`` must already be in the package folder; it is listed like every other file.
- The folder must hold nothing else. The script writes no file outside the folder.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "docs" / "plans" / "v0.5.13-amendment-2-blind-review"
REV = "c92ff977"  # the commit of revision 3, named by the maintainer (F1)

# (package name, commit, repository path, expected SHA-256: full, or (prefix, suffix), or None)
WHOLE = [
    ("amendment-2-revision-3.md", REV, "docs/plans/v0.5.13-charter-amendment-2-rev3.md",
     "f5598f0050ada236e3944b623ee42b46888e0f1bc8c9b564ab67b529fffcdc38"),
    ("charter.md", "04402e7a", "docs/plans/v0.5.13-charter.md", ("2832dc48", "c230c813")),
    ("amendment-1.md", "69de5f9f", "docs/plans/v0.5.13-charter-amendment-1.md",
     ("cd2a6892", "cdbaefc")),
    ("records/step0-golden-before.json", REV, "docs/validation/v0.5.13/step0/golden-before.json",
     None),
    ("records/step1-comparison-nr-a1.json", REV,
     "docs/validation/v0.5.13/step1/comparison-nr-a1.json", None),
    ("records/step1-diag-golden-diff.json", REV,
     "docs/validation/v0.5.13/step1/diag-golden-diff.json", None),
]  # fmt: skip

# (package name, commit, repository path, first line, last line), 1-based and inclusive
EXCERPTS = [
    ("excerpts/CLAUDE.md-core-principle-L33-43.md", REV, "CLAUDE.md", 33, 43),
    ("excerpts/CLAUDE.md-process-diet-2-item-4-L89-112.md", REV, "CLAUDE.md", 89, 112),
    ("excerpts/CLAUDE.md-process-diet-2-item-5-L113-117.md", REV, "CLAUDE.md", 113, 117),
    ("excerpts/CLAUDE.md-process-diet-2-item-7-L119-123.md", REV, "CLAUDE.md", 119, 123),
    ("excerpts/CLAUDE.md-verdicts-L150-156.md", REV, "CLAUDE.md", 150, 156),
    ("excerpts/src-refute-core-dossier.py-L29.txt", REV, "src/refute/core/dossier.py", 29, 29),
    ("excerpts/src-refute-packs-tess-battery_v51.py-L41.txt", REV,
     "src/refute/packs/tess/battery_v51.py", 41, 41),
    ("excerpts/src-refute-packs-tess-battery_v51.py-L134-147.txt", REV,
     "src/refute/packs/tess/battery_v51.py", 134, 147),
    ("excerpts/src-refute-packs-tess-battery_v52.py-L309-320.txt", REV,
     "src/refute/packs/tess/battery_v52.py", 309, 320),
    ("excerpts/src-refute-packs-tess-battery_v52.py-L337-340.txt", REV,
     "src/refute/packs/tess/battery_v52.py", 337, 340),
    ("excerpts/src-refute-core-environment.py-L54-104.txt", REV,
     "src/refute/core/environment.py", 54, 104),
    ("excerpts/src-refute-core-run.py-L137.txt", REV, "src/refute/core/run.py", 137, 137),
    ("excerpts/src-refute-core-run.py-L365.txt", REV, "src/refute/core/run.py", 365, 365),
]  # fmt: skip


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expect(name: str, digest: str, want) -> None:
    ok = (
        want is None
        or (isinstance(want, str) and digest == want)
        or (isinstance(want, tuple) and digest.startswith(want[0]) and digest.endswith(want[1]))
    )
    if not ok:
        raise SystemExit(f"refused: {name} has SHA-256 {digest}, expected {want}")


def put(name: str, data: bytes, rows: list, source: str) -> None:
    path = OUT / name
    if path.exists():
        raise SystemExit(f"refused: {name} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if path.read_bytes() != data:
        raise SystemExit(f"refused: {name} did not write back byte for byte")
    rows.append((name, len(data), sha(data), source))


def main() -> int:
    export = Path(sys.argv[1])
    prompt = OUT / "PROMPT.md"
    if not prompt.is_file():
        raise SystemExit("refused: PROMPT.md must be written first")
    present = sorted(p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file())
    if present != ["PROMPT.md"]:
        raise SystemExit(f"refused: the folder holds more than PROMPT.md: {present}")
    rows: list = []
    data = prompt.read_bytes()
    rows.append(("PROMPT.md", len(data), sha(data), "the review prompt (written for this package)"))
    for name, commit, rel, want in WHOLE:
        full = git("rev-parse", f"{commit}^{{commit}}").decode().strip()
        data = git("show", f"{full}:{rel}")
        expect(name, sha(data), want)
        put(name, data, rows, f"`{rel}` at `{full}`, whole file")
    for name, commit, rel, first, last in EXCERPTS:
        full = git("rev-parse", f"{commit}^{{commit}}").decode().strip()
        lines = git("show", f"{full}:{rel}").splitlines(keepends=True)
        if last > len(lines):
            raise SystemExit(f"refused: {rel} has {len(lines)} lines")
        data = b"".join(lines[first - 1 : last])
        put(name, data, rows, f"`{rel}` at `{full}`, lines {first} to {last}, exact bytes")
    data = export.read_bytes()
    put("issue-231.json", data, rows,
        "#231's title, body and correction comment, as exported by `gh issue view 231 --json` "
        "(the metered unit gh2), byte for byte")  # fmt: skip
    head = [
        "# MANIFEST: blind-review package of amendment 2, revision 3",
        "",
        "Built by `docs/validation/v0.5.13/tools/blind_pack.py` (the maintainer's decision F1, "
        "#218 comment 7218843893). Every file is a byte-for-byte copy of its source, except "
        "`PROMPT.md`, written for this package.",
        "",
        "| File | Bytes | SHA-256 | Source |",
        "| --- | --- | --- | --- |",
    ]
    body = [f"| `{n}` | {b} | `{d}` | {s} |" for n, b, d, s in sorted(rows)]
    (OUT / "MANIFEST.md").write_bytes(("\n".join(head + body) + "\n").encode("utf-8"))
    print(f"MANIFEST.md sha256 {sha((OUT / 'MANIFEST.md').read_bytes())}, {len(rows)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
