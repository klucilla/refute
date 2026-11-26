"""Read-only: list the files in the Drive archive folder that are not in the cleanup's manifest.

    launch_v4.py docs/validation/v0.5.12/units/inspect.json -- \
        docs/maintenance/cleanup-2026-11-26-v0512-close/drive_extras.py

The maintainer's decision recorded in #218, comment 7202817195, item 1: if the destination holds
files that are not in the manifest, they are listed, never deleted. It reads ``record.json`` beside
this file (the cleanup's manifest), walks the Drive folder, and prints a JSON summary. The
manifest itself and the script copy, which the cleanup writes there, are not extras. It writes
nothing.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-26-v0512-close")
OWN = {"MANIFEST-sha256.json", "cleanup.py"}


def main() -> int:
    record = json.loads((HERE / "record.json").read_text(encoding="utf-8"))
    expected = {r["path"].removeprefix(".cache/") for r in record["archived"]}
    found = sorted(p.relative_to(DRIVE).as_posix() for p in DRIVE.rglob("*") if p.is_file())
    extras = [f for f in found if f not in expected and f not in OWN]
    missing = sorted(expected - set(found))
    print(json.dumps({"drive_files": len(found), "manifest_files": len(expected),
                      "extras": extras, "missing": missing}, indent=1))  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
