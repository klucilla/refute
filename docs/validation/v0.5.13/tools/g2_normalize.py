"""Normalize to LF, in the working tree only, the five literal files of the maintainer's decision
G2 (#218 comment 7219180143), and list every other working-tree file with CRLF, by folder.

    unit g2-normalize:  {python} -I -B docs/validation/v0.5.13/tools/g2_normalize.py

**Before**, for each of the five files, it records:
- ``git ls-files --eol``;
- that ``git diff`` on the file is empty;
- that the working-tree content with CRLF replaced by LF has the index blob's id
  (``git hash-object --stdin`` against ``git ls-files -s``).
If any of these fails for any file, nothing is touched.

**Then**, for each file, ``git checkout -- <file>``.

**After**, it records ``git ls-files --eol`` and requires ``w/lf``. Nothing is staged or
committed, and ``core.autocrlf`` is not changed.

**Then** it lists every other tracked file whose working-tree copy has CRLF
(``git ls-files --eol``, ``w/crlf``), grouped by folder. Those files are not touched.

It writes ``out/g2-normalize.json``.
"""

from __future__ import annotations

import json
import os
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FILES = (
    "src/refute/packs/tess/a0.py",
    "scripts/ci_shard.py",
    "tests/test_junit_counts.py",
    "tests/test_v051_a0.py",
    "tests/test_v051_wp2.py",
)


def git(*args: str, data: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, input=data)


def eol(rel: str) -> str:
    return git("ls-files", "--eol", "--", rel).stdout.decode().strip()


def main() -> int:
    before = []
    for rel in FILES:
        raw = (ROOT / rel).read_bytes()
        index_blob = git("ls-files", "-s", "--", rel).stdout.decode().split()[1]
        normalized = git("hash-object", "--no-filters", "--stdin",
                         data=raw.replace(b"\r\n", b"\n")).stdout.decode().strip()  # fmt: skip
        diff_empty = git("diff", "--quiet", "--", rel).returncode == 0
        before.append({"path": rel, "eol": eol(rel), "diff_empty": diff_empty,
                       "crlf_count": raw.count(b"\r\n"), "index_blob": index_blob,
                       "lf_content_blob": normalized,
                       "lf_content_equals_index": normalized == index_blob})  # fmt: skip
    ready = all(b["diff_empty"] and b["lf_content_equals_index"] for b in before)
    report: dict = {"before": before, "ready": ready, "after": []}
    if ready:
        for rel in FILES:
            p = git("checkout", "--", rel)
            after_eol = eol(rel)
            crlf = (ROOT / rel).read_bytes().count(b"\r\n")
            report["after"].append({"path": rel, "checkout_exit": p.returncode, "eol": after_eol,
                                    "w_lf": "w/lf" in after_eol.split(),
                                    "crlf_count": crlf})  # fmt: skip
    listing = git("ls-files", "--eol").stdout.decode().splitlines()
    others: dict[str, list[str]] = defaultdict(list)
    for line in listing:
        fields, _, path = line.partition("\t")
        if "w/crlf" in fields.split() and path not in FILES:
            folder = path.rsplit("/", 1)[0] if "/" in path else "."
            others[folder].append(path)
    report["other_crlf_files"] = sum(len(v) for v in others.values())
    report["other_crlf_by_folder"] = {k: sorted(v) for k, v in sorted(others.items())}
    report["all_ok"] = ready and all(a["w_lf"] and a["crlf_count"] == 0 for a in report["after"])
    out = Path(os.environ.get("REFUTE_RUN_OUT", "."))
    text = json.dumps(report, indent=1) + "\n"
    (out / "g2-normalize.json").write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({"ready": ready, "after_w_lf": [a["w_lf"] for a in report["after"]],
                      "other_crlf_files": report["other_crlf_files"],
                      "all_ok": report["all_ok"]}))  # fmt: skip
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
