"""Store a file unchanged inside the project (a Codex answer, a prompt actually sent, a review),
byte for byte, with its SHA-256 checked before and after the copy.

    launch_v3 unit store-file:
        {python} -I -B docs/validation/v0.5.12/tools/store_file.py <source> <destination>

Both paths are inside the project; the destination must not exist. When the source is a Codex
events file, it also prints the thread id and the real sum of every ``turn.completed`` usage.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def inside(p: Path) -> Path:
    p = (ROOT / p).resolve()
    if ROOT not in p.parents:
        raise SystemExit(f"refused: {p} is outside the project")
    return p


def main() -> int:
    src, dst = inside(Path(sys.argv[1])), inside(Path(sys.argv[2]))
    if dst.exists():
        raise SystemExit(f"refused: {dst} exists already")
    before = hashlib.sha256(src.read_bytes()).hexdigest()
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    a = hashlib.sha256(src.read_bytes()).hexdigest()
    b = hashlib.sha256(dst.read_bytes()).hexdigest()
    out = {"bytes": dst.stat().st_size, "sha256": b, "match": before == a == b}
    if src.suffix == ".jsonl":
        thread, usage = None, {}
        for line in src.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get("type") == "thread.started":
                thread = ev.get("thread_id")
            if ev.get("type") == "turn.completed":
                for k, v in (ev.get("usage") or {}).items():
                    if isinstance(v, int):
                        usage[k] = usage.get(k, 0) + v
        out.update({"thread": thread, "usage": usage})
    print(json.dumps(out))
    return 0 if out["match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
