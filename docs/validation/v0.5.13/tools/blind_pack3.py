"""Build the package of the third blind review of amendment 2, revision 7 (the maintainer's
decision P1, #218 comment 7225754254): byte-for-byte copies only, then a MANIFEST.md with each
file's SHA-256.

    unit blind-pack3:  {python} -I -B docs/validation/v0.5.13/tools/blind_pack3.py

The same procedure as ``blind_pack2.py``:
- whole files are read from git objects at named commits, never from the working tree, and the
  named texts are checked against their known SHA-256 (a mismatch refuses the build);
- excerpts are the exact bytes of the named line ranges at revision 7's commit;
- ``PROMPT.md`` must already be in the folder, and it is listed like every other file.

Nothing of the sessions and nothing of Codex is included (P1). The frozen margin manifest is
included as a record; Codex's answer on it is not.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "docs" / "plans" / "v0.5.13-amendment-2-blind-review-3"
REV = "09fe317ad8f3acaee63517b5603501dcc90df333"  # the commit of revision 7
V = "docs/validation/v0.5.13"

WHOLE = [
    ("amendment-2-revision-7.md", REV, "docs/plans/v0.5.13-charter-amendment-2-rev7.md",
     "eb320426b194da7195b9e5131ead295940d11ea06dcc5265ff8645d74393a5b5"),
    ("amendment-2-revision-6.md", REV, "docs/plans/v0.5.13-charter-amendment-2-rev6.md",
     "86a3853e3d052e5f65c2b3049e58f913abb105997109d362f07056801e235b7c"),
    ("diff-revision-6-to-7.patch", REV, "docs/plans/v0.5.13-amendment-2-rev7/rev6-to-rev7.patch",
     "0f91ab0c68ea576b18b57bf4fc8b30b7653e77d5522aecdb5978e88c8f3a0667"),
    ("charter.md", "04402e7a", "docs/plans/v0.5.13-charter.md",
     "2832dc4870b0fb094e724a3ff6d6fb6c5710f2da5827791b8fa102c06230c813"),
    ("amendment-1.md", "69de5f9f", "docs/plans/v0.5.13-charter-amendment-1.md",
     "cd2a689231688b5e22c3e6c9602a706fbbca37b7de16ea087417227d5cdbaefc"),
    ("amendment-3.md", REV, "docs/plans/v0.5.13-charter-amendment-3-extension.md",
     "e6981c1645c2531729b166b6f334d1750ace0f3999c619a3640200a56428aac4"),
    ("amendment-4.md", REV, "docs/plans/v0.5.13-charter-amendment-4-checkpoints.md",
     "28fc69d532f4e51455d720b7a8f1ff802adb0df9454e7a2f2b51dc16c5d75078"),
    ("blind-review-1-answer.md", REV,
     "docs/plans/v0.5.13-amendment-2-blind-review-result/answer.md",
     "bfa79fb48d7125e971a7c9fe3c77789003c9b91ff48ba5be7f0dd13585d3ddad"),
    ("blind-review-2-answer.md", REV,
     "docs/plans/v0.5.13-amendment-2-blind-review-2-result/answer.md",
     "7f71b206d7efbc1afef2ce62d14cb8483365b2ac04ed12752007c1f63f70114a"),
    ("records/margin-226-manifest.json", REV, f"{V}/manifests/margin-226/manifest.json",
     "df2d3eebadae071bc2cf99c5f1d810d956bb4d2a57e11a04338aab4a7fb2d6cf"),
    ("records/step0-golden-before.json", REV, f"{V}/step0/golden-before.json", None),
    ("records/step0-claim-hashes-before.json", REV, f"{V}/step0/claim-hashes-before.json", None),
    ("records/step1-comparison-nr-a1.json", REV, f"{V}/step1/comparison-nr-a1.json", None),
    ("records/step1-diag-golden-diff.json", REV, f"{V}/step1/diag-golden-diff.json", None),
    ("records/step1-golden-nr-a1-default.json", REV, f"{V}/step1/golden-nr-a1-default.json", None),
    ("records/step1-golden-nr-a1-t1.json", REV, f"{V}/step1/golden-nr-a1-t1.json", None),
    ("records/step1-golden-nr-a1-t4.json", REV, f"{V}/step1/golden-nr-a1-t4.json", None),
    ("records/numerical-environment.md", REV, f"{V}/numerical-environment.md", None),
    ("records/i2-README.md", REV, f"{V}/i2/README.md", None),
    ("records/j1-README.md", REV, f"{V}/j1/README.md", None),
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
    (f"{T}/battery_v52.py", 411, 411, None),
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
    for rel, first, last, tag in EXCERPTS:
        lines = git("show", f"{REV}:{rel}").splitlines(keepends=True)
        data = b"".join(lines[first - 1 : last])
        name = excerpt_name(rel, first, last, tag)
        path = OUT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        rows.append((name, len(data), sha(data), f"`{rel}` at `{REV}`, lines {first} to {last}"))
    head = [
        "# MANIFEST: package of the third blind review of amendment 2, revision 7",
        "",
        "Built by `docs/validation/v0.5.13/tools/blind_pack3.py` (the maintainer's decision P1, "
        "#218 comment 7225754254). Every file is a byte-for-byte copy of its source, except "
        "`PROMPT.md`, written for this package. Nothing of the review sessions and nothing of "
        "Codex is included.",
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
