"""The deterministic checks of the maintainer's decision D4 (#218, comment 7207651312), metered.

    unit check-m45:  {python} -I -B docs/validation/v0.5.13/tools/check_m45.py files|uvlock

- ``files`` (before the version change):
  - the prepared diff ``.cache/v0513prep/m45/pyproject.diff`` and workflow
    ``.cache/v0513prep/m45/release.yml`` have the SHA-256 the maintainer approved;
  - the working ``pyproject.toml`` is byte for byte the prepared result
    (``.cache/v0513prep/m45/pyproject.patched.toml``), and that result is HEAD's ``pyproject.toml``
    with the approved diff applied (checked by re-applying the diff's hunks to HEAD's text);
  - the working ``.github/workflows/release.yml`` is byte for byte the approved workflow.
- ``uvlock`` (after ``uv lock``): ``git diff -U0 -- uv.lock`` changes exactly one line pair, the
  ``version`` of the ``refute`` package itself, from ``0.5.0`` to ``0.5.12``; no other line of
  ``uv.lock`` changes (no dependency changes).
The result goes to ``out/check-m45-<mode>.json``; exit 0 only when every check passes.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
M45 = ROOT / ".cache" / "v0513prep" / "m45"
APPROVED_DIFF = "70b4aeaba5019b399cfe282e68366409fc951a316abfa193eb393e47f4d2ff6e"
APPROVED_WORKFLOW = "b48adbef34360ec58cd0b3ecf9424b3c64ddaded320657602b2bb5c072d0f448"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def apply_unified(old: str, diff: str) -> str:
    """Apply a unified diff of one file (as written by difflib) to ``old``; strict context."""
    lines = old.splitlines(True)
    out: list[str] = []
    pos = 0
    body = diff.splitlines(True)
    i = 0
    while i < len(body):
        m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", body[i])
        if not m:
            i += 1
            continue
        start = int(m.group(1)) - 1
        out.extend(lines[pos:start])
        pos = start
        i += 1
        while i < len(body) and not body[i].startswith("@@"):
            tag, text = body[i][0], body[i][1:]
            if tag == " ":
                if lines[pos] != text:
                    raise ValueError(f"context mismatch at line {pos + 1}")
                out.append(text)
                pos += 1
            elif tag == "-":
                if lines[pos] != text:
                    raise ValueError(f"removed line mismatch at line {pos + 1}")
                pos += 1
            elif tag == "+":
                out.append(text)
            i += 1
    out.extend(lines[pos:])
    return "".join(out)


def check_files() -> dict:
    diff = (M45 / "pyproject.diff").read_bytes()
    workflow = (M45 / "release.yml").read_bytes()
    patched = (M45 / "pyproject.patched.toml").read_bytes()
    head = git("show", "HEAD:pyproject.toml").decode("utf-8")
    reapplied = apply_unified(head, diff.decode("utf-8")).encode("utf-8")
    work_py = (ROOT / "pyproject.toml").read_bytes()
    work_wf = (ROOT / ".github" / "workflows" / "release.yml").read_bytes()
    return {
        "diff_sha256": sha(diff),
        "diff_is_approved": sha(diff) == APPROVED_DIFF,
        "workflow_sha256": sha(workflow),
        "workflow_is_approved": sha(workflow) == APPROVED_WORKFLOW,
        "head_plus_diff_equals_patched": reapplied == patched,
        "working_pyproject_equals_patched": work_py == patched,
        "working_release_yml_equals_approved": sha(work_wf) == APPROVED_WORKFLOW,
    }


def check_uvlock() -> dict:
    d = git("diff", "-U0", "--", "uv.lock").decode("utf-8")
    minus = [x for x in d.splitlines() if x.startswith("-") and not x.startswith("---")]
    plus = [x for x in d.splitlines() if x.startswith("+") and not x.startswith("+++")]
    hunks = [x for x in d.splitlines() if x.startswith("@@")]
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8").splitlines()
    idx = next((i for i, x in enumerate(lock) if x == 'name = "refute"'), None)
    in_refute = idx is not None and lock[idx + 1] == 'version = "0.5.12"'
    return {
        "hunks": len(hunks),
        "removed": minus,
        "added": plus,
        "only_refute_version": minus == ['-version = "0.5.0"']
        and plus == ['+version = "0.5.12"']
        and len(hunks) == 1
        and in_refute,
    }


def main() -> int:
    mode = sys.argv[1]
    res = check_files() if mode == "files" else check_uvlock() if mode == "uvlock" else None
    if res is None:
        raise SystemExit("mode must be files or uvlock")
    flags = [v for k, v in res.items() if isinstance(v, bool)]
    res["passed"] = bool(flags) and all(flags)
    out = Path(os.environ["REFUTE_RUN_OUT"])
    (out / f"check-m45-{mode}.json").write_text(json.dumps(res, indent=1) + "\n", "utf-8")
    print(json.dumps(res))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
