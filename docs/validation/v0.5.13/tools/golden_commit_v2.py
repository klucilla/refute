"""The raw goldens of NR-A2 into git, as those of NR-A1 (the maintainer's decision V2, #218 comment
7228712102). A new file: golden_commit.py stays unchanged as the record of I2(a).

    unit golden-commit-v2:  {python} -I -B docs/validation/v0.5.13/tools/golden_commit_v2.py \
        copy|verify

The payload recorded for NR-A2 is its own record, read from its committed blob at HEAD (never the
working tree): ``step1/golden-nr-a2-t2.json``.

**``copy``.** The files of ``.cache/v0513/golden/nr-a2-t2/`` must be exactly the payload's
inventory. Each must hold no CR byte (so that git stores it byte for byte under ``eol=lf``) and
have the recorded SHA-256. Their total must not exceed 5 MB (CLAUDE.md, raw outputs; above it,
the Drive with a SHA-256 manifest, not this tool). Only then is each file copied, byte for byte, to
``docs/validation/v0.5.13/goldens/nr-a2-t2/``, which must not exist.

**``verify``** (after the commit). For each of the 20 files, the SHA-256 of ``git show
HEAD:<path>`` must equal the recorded one.

The tool reads bytes and hashes; it does not parse or print any golden value. It writes
``out/golden-commit-v2-<mode>.json``.
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
SETTING = "nr-a2-t2"
RECORD = f"{V}/step1/golden-nr-a2-t2.json"
LIMIT = 5_000_000


def git_show(rel: str) -> bytes:
    return subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True,
                          check=True).stdout  # fmt: skip


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    mode = sys.argv[1]
    rows, problems = [], []
    recorded = json.loads(git_show(RECORD))["payload"]["files_sha256"]
    src_dir = ROOT / ".cache" / "v0513" / "golden" / SETTING
    dst_rel = f"{V}/goldens/{SETTING}"
    if mode == "copy":
        present = sorted(p.name for p in src_dir.iterdir() if p.is_file())
        if present != sorted(recorded):
            problems.append(f"inventory {present} != recorded {sorted(recorded)}")
        elif (ROOT / dst_rel).exists():
            problems.append(f"{dst_rel} exists")
        else:
            staged = {}
            for name, want in sorted(recorded.items()):
                data = (src_dir / name).read_bytes()
                if b"\r" in data:
                    problems.append(f"{name}: holds a CR byte")
                if sha(data) != want:
                    problems.append(f"{name}: SHA-256 differs from the record")
                staged[name] = data
            total = sum(len(d) for d in staged.values())
            if total > LIMIT:
                problems.append(f"total {total} bytes is above 5 MB: the Drive, not git")
            if not problems:
                (ROOT / dst_rel).mkdir(parents=True)
                for name, data in staged.items():
                    (ROOT / dst_rel / name).write_bytes(data)
                    rows.append({"file": name, "sha256": recorded[name], "bytes": len(data)})
    elif mode == "verify":
        for name, want in sorted(recorded.items()):
            got = sha(git_show(f"{dst_rel}/{name}"))
            if got != want:
                problems.append(f"{name}: committed SHA-256 {got} != recorded {want}")
            rows.append({"file": name, "sha256": got, "equal": got == want})
    else:
        raise SystemExit("mode must be copy or verify")
    report = {"mode": mode, "record": RECORD, "files": len(rows), "problems": problems,
              "rows": rows, "all_ok": not problems and len(rows) == len(recorded)}  # fmt: skip
    out = Path(os.environ.get("REFUTE_RUN_OUT", "."))
    text = json.dumps(report, indent=1) + "\n"
    (out / f"golden-commit-v2-{mode}.json").write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({"mode": mode, "files": len(rows), "problems": problems[:10],
                      "all_ok": report["all_ok"],
                      "bytes": sum(r.get("bytes", 0) for r in rows)}))  # fmt: skip
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
