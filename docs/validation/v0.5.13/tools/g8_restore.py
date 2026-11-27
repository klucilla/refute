"""Write the exact index blobs of five literal files back to the working tree (the maintainer's
decision G8, #218 comment 7219469262).

    unit g8-restore:  {python} -I -B docs/validation/v0.5.13/tools/g8_restore.py

For each file it records before and after:
- ``git ls-files --eol``;
- the file's SHA-256 and CRLF count.

It writes the bytes of ``git cat-file blob :<file>``, in binary mode, to the file. Then it requires:
- the file's SHA-256 equals the blob's;
- ``git hash-object --no-filters <file>`` equals the index blob's id;
- ``git diff --quiet -- <file>`` succeeds;
- ``git ls-files --eol`` shows ``w/lf``.

Nothing is staged or committed. No other file is touched. It writes ``out/g8-restore.json``.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FILES = (
    "src/refute/packs/tess/a0.py",
    "scripts/ci_shard.py",
    "tests/test_junit_counts.py",
    "tests/test_v051_a0.py",
    "tests/test_v051_wp2.py",
)


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True)


def eol(rel: str) -> str:
    return git("ls-files", "--eol", "--", rel).stdout.decode().strip()


def state(rel: str) -> dict:
    data = (ROOT / rel).read_bytes()
    return {"eol": eol(rel), "sha256": hashlib.sha256(data).hexdigest(),
            "crlf_count": data.count(b"\r\n")}  # fmt: skip


def main() -> int:
    rows = []
    for rel in FILES:
        blob_id = git("ls-files", "-s", "--", rel).stdout.decode().split()[1]
        blob = git("cat-file", "blob", blob_id).stdout
        row = {"path": rel, "index_blob": blob_id,
               "blob_sha256": hashlib.sha256(blob).hexdigest(), "before": state(rel)}  # fmt: skip
        with open(ROOT / rel, "wb") as f:
            f.write(blob)
        after = state(rel)
        after["hash_object_no_filters"] = (
            git("hash-object", "--no-filters", "--", rel).stdout.decode().strip()
        )
        after["diff_empty"] = git("diff", "--quiet", "--", rel).returncode == 0
        after["checks"] = {
            "sha256_equals_blob": after["sha256"] == row["blob_sha256"],
            "hash_object_equals_index_blob": after["hash_object_no_filters"] == blob_id,
            "diff_empty": after["diff_empty"],
            "w_lf": "w/lf" in after["eol"].split(),
        }
        row["after"] = after
        rows.append(row)
    ok = all(all(r["after"]["checks"].values()) for r in rows)
    out = Path(os.environ.get("REFUTE_RUN_OUT", "."))
    text = json.dumps({"files": rows, "all_ok": ok}, indent=1) + "\n"
    (out / "g8-restore.json").write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({r["path"]: r["after"]["checks"] for r in rows} | {"all_ok": ok}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
