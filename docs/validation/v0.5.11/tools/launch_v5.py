"""The metered launcher of v0.5.11, version 5: version 4 with two telemetry fixes, after the
step-2 tests unit was interrupted for lost telemetry (errata entry 6).

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.11/tools/launch_v5.py <unit spec>
        [--label L] [--approval URL] [-- extra arguments]

**1. A file that vanishes during a scan is not an error.** pytest creates and deletes temporary
files while it runs, so a directory entry can disappear between the listing and the ``stat``.
- A ``FileNotFoundError`` on an entry, or on a directory that no longer exists, is skipped:
  the file is gone, so it occupies no disk.
- Any other ``OSError``, a ``PermissionError`` for example, is still a scan error, and the
  telemetry is lost.

**2. The transfer counters are read apart and unwrapped.** ``netstat -e`` gives the received
and the sent bytes, which may be 32-bit counters.
- Each is read separately.
- A decrease of one counter, read when its previous value was above 2^31, is one wrap of
  2^32. One second cannot carry 2^31 bytes, so a second wrap in one poll is impossible.
- Any other decrease, and any failed read, is lost telemetry, as in version 4.

Every other rule is version 4's:
- the junction-free scan;
- baselines before dispatch;
- lost telemetry stops the job;
- the charging rule;
- the helpers of launch_v2.py.

The SHA-256 of launch_v2.py, launch_v4.py and of this file are in every attempt's identity.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v4 = _load("launch_v4")
base = v4.base
WRAP = 1 << 32
HALF = 1 << 31


def tree_bytes(p: Path) -> tuple[int, int]:
    """(bytes, scan errors); links and junctions are neither followed nor counted; a file or a
    directory that vanished during the scan is skipped, not an error."""
    if not p.exists():
        return 0, 0
    total, errors = 0, 0
    stack = [p]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for e in it:
                    try:
                        if e.is_symlink() or e.is_junction():
                            continue
                        if e.is_dir(follow_symlinks=False):
                            stack.append(Path(e.path))
                        elif e.is_file(follow_symlinks=False):
                            total += e.stat(follow_symlinks=False).st_size
                    except FileNotFoundError:
                        continue
                    except OSError:
                        errors += 1
        except FileNotFoundError:
            continue
        except OSError:
            errors += 1
    return total, errors


class _Counter:
    """The machine's received plus sent bytes, unwrapped per counter."""

    def __init__(self) -> None:
        self.last: tuple[int, int] | None = None
        self.offset = [0, 0]

    @staticmethod
    def _read() -> tuple[int, int] | None:
        try:
            out = subprocess.run(
                ["netstat", "-e"], capture_output=True, text=True, errors="replace"
            )
        except OSError:
            return None
        for line in out.stdout.splitlines():
            parts = line.split()
            if parts and parts[0] == "Bytes" and len(parts) >= 3:
                try:
                    return int(parts[1]), int(parts[2])
                except ValueError:
                    return None
        return None

    def read(self) -> int | None:
        now = self._read()
        if now is None:
            return None
        if self.last is not None:
            for i in (0, 1):
                if now[i] < self.last[i]:
                    if self.last[i] < HALF:
                        return None  # a decrease that is not a wrap: lost telemetry
                    self.offset[i] += WRAP
        self.last = now
        return now[0] + self.offset[0] + now[1] + self.offset[1]


def main() -> int:
    counter = _Counter()
    # version 4's main, with this version's scan and counter, and this file in the identity
    v4.tree_bytes = tree_bytes
    base.net_bytes = counter.read
    v5_rel = Path(__file__).resolve().relative_to(base.ROOT).as_posix()
    v5_sha = base.committed_sha256(v5_rel)  # refuses an uncommitted or changed launcher
    original_append = base.append_log

    def append_log(entry: dict) -> None:
        if entry.get("event") == "before":
            entry = dict(entry, launcher="launch_v5.py")
            entry["identity_sha256"] = {v5_rel: v5_sha, **entry.get("identity_sha256", {})}
        original_append(entry)

    base.append_log = append_log
    return v4.main()


if __name__ == "__main__":
    sys.exit(main())
