"""The raw goldens of ID-BEFORE and of NR-A1's three settings, into git (amendment 2, revision 4,
section 3.1, decision H2(b); the maintainer's decision I2(a), #218 comment 7222329150).

    unit golden-commit:  {python} -I -B docs/validation/v0.5.13/tools/golden_commit.py copy|verify

The payload recorded for each setting is that setting's own record, read from its committed blob
at HEAD (never the working tree):
- ``before``: ``step0/golden-before.json``;
- ``nr-a1-default``, ``nr-a1-t1``, ``nr-a1-t4``: ``step1/golden-nr-a1-<setting>.json``.

**``copy``.** For each setting, the files of ``.cache/v0513/golden/<setting>/`` must be exactly
the payload's inventory. Each file must hold no CR byte, so that git stores it byte for byte under
``eol=lf``, and its SHA-256 must equal the recorded one. Only then is each file copied, byte for
byte, to ``docs/validation/v0.5.13/goldens/<setting>/``, which must not exist.

**``verify``** (after the commit). For each of the 80 files, it requires that the SHA-256 of
``git show HEAD:<path>`` equals the recorded one.

The tool reads bytes and hashes; it does not parse or print any golden value. It writes
``out/golden-commit-<mode>.json``.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
V = "docs/validation/v0.5.13"
RECORDS = {
    "before": f"{V}/step0/golden-before.json",
    "nr-a1-default": f"{V}/step1/golden-nr-a1-default.json",
    "nr-a1-t1": f"{V}/step1/golden-nr-a1-t1.json",
    "nr-a1-t4": f"{V}/step1/golden-nr-a1-t4.json",
}


def git_show(rel: str) -> bytes:
    return subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True,
                          check=True).stdout  # fmt: skip


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    mode = sys.argv[1]
    rows, problems = [], []
    for setting, record in RECORDS.items():
        blob = git_show(record)
        recorded = json.loads(blob)["payload"]["files_sha256"]
        src_dir = ROOT / ".cache" / "v0513" / "golden" / setting
        dst_rel = f"{V}/goldens/{setting}"
        if mode == "copy":
            present = sorted(p.name for p in src_dir.iterdir() if p.is_file())
            if present != sorted(recorded):
                problems.append(f"{setting}: inventory {present} != recorded {sorted(recorded)}")
                continue
            if (ROOT / dst_rel).exists():
                problems.append(f"{setting}: {dst_rel} exists")
                continue
            staged = {}
            for name, want in sorted(recorded.items()):
                data = (src_dir / name).read_bytes()
                if b"\r" in data:
                    problems.append(f"{setting}/{name}: holds a CR byte")
                if sha(data) != want:
                    problems.append(f"{setting}/{name}: SHA-256 differs from the record")
                staged[name] = data
            if problems:
                continue
            (ROOT / dst_rel).mkdir(parents=True)
            for name, data in staged.items():
                (ROOT / dst_rel / name).write_bytes(data)
                rows.append({"setting": setting, "file": name, "sha256": recorded[name],
                             "bytes": len(data)})  # fmt: skip
        elif mode == "verify":
            for name, want in sorted(recorded.items()):
                got = sha(git_show(f"{dst_rel}/{name}"))
                if got != want:
                    problems.append(f"{setting}/{name}: committed SHA-256 {got} != recorded {want}")
                rows.append({"setting": setting, "file": name, "sha256": got, "equal": got == want})
        else:
            raise SystemExit("mode must be copy or verify")
    report = {"mode": mode, "records": RECORDS, "files": len(rows), "problems": problems,
              "rows": rows, "all_ok": not problems and len(rows) == 80}  # fmt: skip
    out = Path(os.environ.get("REFUTE_RUN_OUT", "."))
    text = json.dumps(report, indent=1) + "\n"
    (out / f"golden-commit-{mode}.json").write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({"mode": mode, "files": len(rows), "problems": problems[:10],
                      "all_ok": report["all_ok"]}))  # fmt: skip
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
