"""Archive the per-trial detail of the v0.5 acceptance run to the maintainer's Drive (CLAUDE.md: a
raw output above 5 MB never enters git; it is archived with a SHA-256 manifest of source and
destination, checked). The manifest is written next to this script and committed.

usage: archive_detail.py <detail.json> <drive folder> <manifest.json>"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str]) -> int:
    source, folder, manifest = Path(argv[0]), Path(argv[1]), Path(argv[2])
    destination = folder / source.name
    if destination.exists():
        print(f"refusing to overwrite {destination.name}")
        return 2
    folder.mkdir(parents=True, exist_ok=True)
    before = sha256(source)
    shutil.copy2(source, destination)
    after = sha256(destination)
    if before != after or sha256(source) != before:
        print("SHA-256 mismatch after the copy")
        return 1
    record = {
        "file": source.name,
        "bytes": source.stat().st_size,
        "source_sha256": before,
        "destination_sha256": after,
        "destination": "Drive: Pessoal/Projetos/refute/" + folder.name + "/" + source.name,
        "checked_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    manifest.write_bytes((json.dumps(record, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    print(f"archived {source.name}: {before}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
