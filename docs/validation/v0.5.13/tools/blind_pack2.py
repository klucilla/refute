"""Build the package of the second blind review of amendment 2, revision 5 (the maintainer's
decision J1, #218 comment 7222879969): byte-for-byte copies only, then a MANIFEST.md with each
file's SHA-256.

    unit blind-pack2:  {python} -I -B docs/validation/v0.5.13/tools/blind_pack2.py

The same procedure as ``blind_pack.py`` (F1):
- whole files are read from git objects at named commits, never from the working tree, and the
  named texts are checked against their known SHA-256;
- excerpts are the exact bytes of the named line ranges at the named commit;
- ``PROMPT.md`` must already be in the folder, and it is listed like every other file.

Nothing of the sessions and nothing of Codex is included. The export of #231 that the first
package held is left out, because its correction comment quotes a Codex review.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "docs" / "plans" / "v0.5.13-amendment-2-blind-review-2"
REV = "86f1f289"  # the commit of revision 5
V = "docs/validation/v0.5.13"

WHOLE = [
    ("amendment-2-revision-5.md", REV, "docs/plans/v0.5.13-charter-amendment-2-rev5.md",
     "c69b23e9074477bb481638f39577ac98eaed549e9e00271478900d944235518b"),
    ("amendment-2-revision-4.md", "288d5785", "docs/plans/v0.5.13-charter-amendment-2-rev4.md",
     "7d96726de18157ccd4d20f494a9efcef076107efda9337179b1f5f67870d8d4e"),
    ("diff-revision-4-to-5.patch", REV, "docs/plans/v0.5.13-amendment-2-rev5/rev4-to-rev5.patch",
     "efec9517065b08b5ad44ad79a6f2713a64998f7b71dcae57e9f7402702b27fce"),
    ("charter.md", "04402e7a", "docs/plans/v0.5.13-charter.md",
     "2832dc4870b0fb094e724a3ff6d6fb6c5710f2da5827791b8fa102c06230c813"),
    ("amendment-1.md", "69de5f9f", "docs/plans/v0.5.13-charter-amendment-1.md",
     "cd2a689231688b5e22c3e6c9602a706fbbca37b7de16ea087417227d5cdbaefc"),
    ("blind-review-1-answer.md", REV,
     "docs/plans/v0.5.13-amendment-2-blind-review-result/answer.md",
     "bfa79fb48d7125e971a7c9fe3c77789003c9b91ff48ba5be7f0dd13585d3ddad"),
    ("records/step0-golden-before.json", REV, f"{V}/step0/golden-before.json", None),
    ("records/step0-claim-hashes-before.json", REV, f"{V}/step0/claim-hashes-before.json", None),
    ("records/step1-comparison-nr-a1.json", REV, f"{V}/step1/comparison-nr-a1.json", None),
    ("records/step1-diag-golden-diff.json", REV, f"{V}/step1/diag-golden-diff.json", None),
    ("records/step1-golden-nr-a1-default.json", REV, f"{V}/step1/golden-nr-a1-default.json", None),
    ("records/step1-golden-nr-a1-t1.json", REV, f"{V}/step1/golden-nr-a1-t1.json", None),
    ("records/step1-golden-nr-a1-t4.json", REV, f"{V}/step1/golden-nr-a1-t4.json", None),
    ("records/numerical-environment.md", REV, f"{V}/numerical-environment.md", None),
    ("records/i2-README.md", REV, f"{V}/i2/README.md", None),
    ("records/i2-predicate-inventory.json", REV, f"{V}/i2/predicate-inventory.json", None),
    ("records/j1-README.md", REV, f"{V}/j1/README.md", None),
    ("records/j1-decision-count.json", REV, f"{V}/j1/decision-count.json", None),
]  # fmt: skip

T = "src/refute/packs/tess"
EXCERPTS = [
    ("CLAUDE.md", 33, 43, "core-principle"),
    ("CLAUDE.md", 89, 112, "process-diet-2-item-4"),
    ("CLAUDE.md", 113, 117, "process-diet-2-item-5"),
    ("CLAUDE.md", 119, 123, "process-diet-2-item-7"),
    ("CLAUDE.md", 150, 156, "verdicts"),
    ("CLAUDE.md", 221, 228, "raw-outputs"),
    ("src/refute/core/dossier.py", 29, 29, None),
    (f"{T}/battery_v51.py", 41, 47, None),
    (f"{T}/battery_v51.py", 134, 147, None),
    (f"{T}/battery_v52.py", 36, 37, None),
    (f"{T}/battery_v52.py", 309, 320, None),
    (f"{T}/battery_v52.py", 338, 340, None),
    (f"{T}/pipeline.py", 454, 457, None),
    (f"{T}/pipeline_v52.py", 186, 186, None),
    (f"{T}/params.py", 370, 371, None),
    ("src/refute/core/environment.py", 46, 51, None),
    ("src/refute/core/environment.py", 54, 104, None),
    ("src/refute/core/run.py", 137, 137, None),
    ("src/refute/core/run.py", 365, 365, None),
    (f"{V}/tools/identity.py", 37, 55, None),
]


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def excerpt_name(rel: str, first: int, last: int, tag: str | None) -> str:
    stem = rel.replace("/", "-")
    span = f"L{first}" if first == last else f"L{first}-{last}"
    suffix = ".md" if rel.endswith(".md") else ".txt"
    return f"excerpts/{stem}-{tag + '-' if tag else ''}{span}{suffix}"


def main() -> int:
    prompt = OUT / "PROMPT.md"
    if not prompt.is_file():
        raise SystemExit("refused: PROMPT.md must be written first")
    present = {p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file()}
    if present != {"PROMPT.md"}:
        raise SystemExit(f"refused: the folder holds more than PROMPT.md: {sorted(present)}")
    rows = []
    data = prompt.read_bytes()
    rows.append(("PROMPT.md", len(data), sha(data), "the review prompt (written for this package)"))
    for name, commit, rel, want in WHOLE:
        full = git("rev-parse", f"{commit}^{{commit}}").decode().strip()
        data = git("show", f"{full}:{rel}")
        if want is not None and sha(data) != want:
            raise SystemExit(f"refused: {name} has SHA-256 {sha(data)}, expected {want}")
        path = OUT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        rows.append((name, len(data), sha(data), f"`{rel}` at `{full}`, whole file"))
    full = git("rev-parse", f"{REV}^{{commit}}").decode().strip()
    for rel, first, last, tag in EXCERPTS:
        lines = git("show", f"{full}:{rel}").splitlines(keepends=True)
        data = b"".join(lines[first - 1 : last])
        name = excerpt_name(rel, first, last, tag)
        path = OUT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        rows.append((name, len(data), sha(data), f"`{rel}` at `{full}`, lines {first} to {last}"))
    head = [
        "# MANIFEST: package of the second blind review of amendment 2, revision 5",
        "",
        "Built by `docs/validation/v0.5.13/tools/blind_pack2.py` (the maintainer's decision J1, "
        "#218 comment 7222879969). Every file is a byte-for-byte copy of its source, except "
        "`PROMPT.md`, written for this package. Nothing of the review sessions and nothing of "
        "Codex is included; the export of #231 is left out because its correction comment quotes "
        "a Codex review.",
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
