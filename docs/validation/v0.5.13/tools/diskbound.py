"""The phase-wide disk bound of v0.5.13 (charter, section 8, Codex r1's caps wording; section 9).

**The roots** are where the phase's writes can stay:
- the project folder, except ``.venv`` and ``.cache`` (``.git`` included);
- ``.cache/v0513`` (the phase's working folder: runs, light-curve cache, outputs);
- ``.cache/lock-compat`` (the warm tag environments), scanned only when a unit asks, because it is
  large.

**The bound.** Phase occupancy O is the roots' total size minus the baseline total recorded by the
first unit. During a unit the occupancy is at most ``O_start + W`` (W: every byte the unit's
process tree wrote, files deleted afterwards included); after it, ``O_end`` is measured and carried
forward. The phase peak is the largest of these over every unit. Writes made between units by the
agent's editing tools are carried by the next ``O_start``.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXCLUDE_TOP = {".venv", ".cache"}
# the launcher's self-test (REFUTE_LAUNCH_SELFTEST=1) scans its own folder instead
CACHE_ROOTS = (
    ("v0513prep/selftest",) if os.environ.get("REFUTE_LAUNCH_SELFTEST") == "1" else ("v0513",)
)
LOCK_COMPAT = "lock-compat"


def tree_size(p: Path) -> int:
    if p.is_file():
        return p.stat().st_size
    total = 0
    for dirpath, _dirnames, filenames in os.walk(p):
        for name in filenames:
            try:
                total += os.lstat(os.path.join(dirpath, name)).st_size
            except OSError:
                pass
    return total


def scan(lock_compat: bool = False) -> dict:
    """Sizes of the roots, in bytes; ``fast_total`` is their sum without lock-compat."""
    roots: dict[str, int] = {}
    for child in sorted(ROOT.iterdir()):
        if child.name not in EXCLUDE_TOP:
            roots[child.name] = tree_size(child)
    for name in CACHE_ROOTS:
        p = ROOT / ".cache" / name
        roots[".cache/" + name] = tree_size(p) if p.exists() else 0
    doc = {"fast_total": sum(roots.values()), "roots": roots}
    if lock_compat:
        doc["lock_compat"] = tree_size(ROOT / ".cache" / LOCK_COMPAT)
    return doc
