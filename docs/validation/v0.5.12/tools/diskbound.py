"""The phase-wide disk bound of v0.5.12 (charter, step 0; Codex's round 3, item 5).

**The roots** are where the phase's writes can stay:
- the project folder, except ``.venv`` and ``.cache`` (``.git`` included);
- ``.cache/v0512`` and ``.cache/v0511/runs`` (the outer launcher's run folders during the
  bootstrap);
- ``.cache/lock-compat`` (the warm tag environments), scanned only when asked, because it holds
  117,496 files: at the phase's baseline, around each tag verification, and at the seal.

**The bound.** Phase occupancy O is the roots' total size minus the baseline total. A unit cannot
grow the disk by more than the bytes its process tree writes, so during a unit the phase's
occupancy is at most ``O_start + W``, where W is the job's write-transfer count (every byte
written, files deleted afterwards included). After the unit, ``O_end`` is measured and carried
forward to the next unit. The phase peak is the largest ``O_start + W`` and ``O_end`` over every
unit, bootstrap included. Writes made between units by the agent's editing tools are carried by
the next ``O_start``. The warm environments' growth is charged from its last scan and, at the
seal, any growth beyond it is added to every unit since that scan (the worst case).
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXCLUDE_TOP = {".venv", ".cache"}
CACHE_ROOTS = ("v0512", "v0511/runs")
LOCK_COMPAT = "lock-compat"


def tree_size(p: Path) -> int:
    total = 0
    if p.is_file():
        return p.stat().st_size
    for dirpath, _dirnames, filenames in os.walk(p):
        for name in filenames:
            try:
                total += os.lstat(os.path.join(dirpath, name)).st_size
            except OSError:
                pass
    return total


def scan(lock_compat: bool = False) -> dict:
    """Sizes of the roots, in bytes; 'total' is their sum (lock-compat only when asked)."""
    roots: dict[str, int] = {}
    for child in sorted(ROOT.iterdir()):
        if child.name not in EXCLUDE_TOP:
            roots[child.name] = tree_size(child)
    for name in CACHE_ROOTS:
        p = ROOT / ".cache" / name
        roots[".cache/" + name] = tree_size(p) if p.exists() else 0
    fast = sum(roots.values())
    doc = {"fast_total": fast, "roots": roots}
    if lock_compat:
        doc["lock_compat"] = tree_size(ROOT / ".cache" / LOCK_COMPAT)
    return doc
