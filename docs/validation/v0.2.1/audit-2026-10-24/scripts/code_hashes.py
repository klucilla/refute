"""The code hash (refute-code-1) and X2's lot code digest of the checkout, after checking that
every file they cover is the committed one (no difference from HEAD)."""

import subprocess
import sys
from pathlib import Path

root = Path("C:/Projetos/refute/.cache/wt-merge-check")
dirty = subprocess.run(
    [
        "git",
        "status",
        "--porcelain",
        "--",
        "src",
        "pyproject.toml",
        "uv.lock",
        "docs/validation/v0.2.1/population",
    ],
    cwd=root,
    capture_output=True,
    text=True,
    check=True,
).stdout.strip()
if dirty:
    raise SystemExit(f"covered files differ from HEAD:\n{dirty}")
sys.path.insert(0, str(root / "src"))
sys.path.insert(0, str(root / "docs/validation/v0.2.1/population"))
import x2_study  # noqa: E402

from refute.core.codehash import compute_code_hash  # noqa: E402

head = subprocess.run(
    ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
).stdout.strip()
print("commit", head)
print("refute-code-1", compute_code_hash(root).sha256)
print("x2_code_digest", x2_study.code_digest())
