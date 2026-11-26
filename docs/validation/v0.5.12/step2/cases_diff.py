"""v0.5.12 step 2: check that the rebuilt case record differs from the probed one ONLY by the
removal of case C05's two F1 assertions (#218 comment 7198110621, item 1).

    launch_v3 unit step2-cases-diff:
        {python} -I -B docs/validation/v0.5.12/step2/cases_diff.py

The probed record is ``cases.json`` at commit 6f9925e (SHA-256 0bb30fac...); the new one is the
working file. It prints the differences and exits 1 unless the only one is the removal of
``expect.F1`` (``state`` and ``reason_prefix``) from C05.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REL = "docs/validation/v0.5.12/step2/cases.json"
PROBED = "6f9925e"
PROBED_SHA256 = "0bb30fac75e45a64628cb3b3f831020d500daa87de7326e74ea7617943a3b5b5"


def walk(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in b:
                out.append(("removed", path + [k], a[k]))
            elif k not in a:
                out.append(("added", path + [k], b[k]))
            else:
                walk(a[k], b[k], path + [k], out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b, strict=True)):
            key = x.get("id", i) if isinstance(x, dict) else i
            walk(x, y, path + [key], out)
    elif a != b:
        out.append(("changed", path, [a, b]))


def main() -> int:
    blob = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{PROBED}:{REL}"], check=True, capture_output=True
    ).stdout
    if hashlib.sha256(blob).hexdigest() != PROBED_SHA256:
        raise SystemExit("refused: the probed record is not the one of the probe")
    old = json.loads(blob)
    new = json.loads((ROOT / REL).read_text(encoding="utf-8"))
    diffs = []
    walk(old, new, [], diffs)
    expected = [("removed", ["cases", "C05", "expect", "F1"])]
    got = [(kind, path) for kind, path, _ in diffs]
    ok = got == expected and diffs[0][2] == {"state": "fail", "reason_prefix": "OE_box "}
    print(json.dumps({"differences": [[k, p, v] for k, p, v in diffs], "only_c05_f1": ok}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
