"""Build the hashed package for correction 2's blind review (v0.5.12, step 4; the maintainer's
decision of #218 comment 7196269069, item 4).

    launch_v3 unit build-package:
        {python} -I -B docs/validation/v0.5.12/tools/build_package.py <commit>

The package holds ONLY:
- the correction, in its final version;
- the cited paper excerpts;
- the current specification, with correction 1.

Each file is the git blob at the given commit, written byte for byte to
``docs/plans/v0.5.12-correction-2-blind-review/``. ``MANIFEST.json`` lists each file's source path,
commit, bytes and SHA-256. The package's SHA-256 is the SHA-256 of ``MANIFEST.json``'s bytes. The
folder must not exist before.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "docs" / "plans" / "v0.5.12-correction-2-blind-review"
FILES = [
    ("correction-2.md", "docs/plans/v0.5.12-spec-correction-2.md"),
    ("paper-excerpts.md", "docs/plans/sources/v0.5.11-screen-papers-2026-11-24.md"),
    ("specification.md", "docs/plans/v0.5.11-spec.md"),
    ("correction-1.md", "docs/plans/v0.5.11-spec-correction-1.md"),
]


def main() -> int:
    commit = sys.argv[1]
    if OUT.exists():
        raise SystemExit(f"refused: {OUT} exists already")
    OUT.mkdir(parents=True)
    rows = []
    for name, rel in FILES:
        blob = subprocess.run(
            ["git", "show", f"{commit}:{rel}"], cwd=ROOT, capture_output=True, check=True
        ).stdout
        (OUT / name).write_bytes(blob)
        if (OUT / name).read_bytes() != blob:
            raise SystemExit(f"refused: the copy of {rel} does not match its blob")
        sha = hashlib.sha256(blob).hexdigest()
        row = {"file": name, "source": rel, "commit": commit}
        row.update({"bytes": len(blob), "sha256": sha})
        rows.append(row)
    manifest = {
        "schema": "refute-v0512-blind-review-package-1",
        "decision": "#218 comment 7196269069, item 4",
        "purpose": "correction 2's blind review; only the correction, the cited paper excerpts, "
        "and the current specification with correction 1",
        "files": rows,
    }
    data = (json.dumps(manifest, indent=1) + "\n").encode("utf-8")
    (OUT / "MANIFEST.json").write_bytes(data)
    print(json.dumps({"package_sha256": hashlib.sha256(data).hexdigest(), "files": len(rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
