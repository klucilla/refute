"""The frozen inputs of v0.5 claims (docs/plans/v0.5-acceptance.md, case 8.4; issue #196).

A frozen input lives in its own folder, named after its SHA-256, under ``.cache/frozen/``, a
folder the project's hygiene rule never deletes (CLAUDE.md). The TESS-EB edition of the v0.4
pilot (``discover.pilot.TESS_EB_STATIC``) keeps its recorded path for v0.4; a v0.5 claim reads the
same edition from ``.cache/frozen/tess-eb/<sha256>/tess_ebs_prsa2022.tsv``. Placing a file there
copies it (never moves it), checks the SHA-256 of the source before and of the copy after, refuses
a link or a junction on the way, and never overwrites a file with other bytes.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path

FROZEN = Path(".cache") / "frozen"
TESS_EB_NAME = "tess_ebs_prsa2022.tsv"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _check_hex(sha256: str) -> None:
    if len(sha256) != 64 or any(c not in "0123456789abcdef" for c in sha256):
        raise ValueError(f"not a lowercase SHA-256: {sha256!r}")


def frozen_tess_eb_path(root: Path, sha256: str) -> Path:
    """Where a v0.5 claim reads the TESS-EB edition with this raw SHA-256."""
    _check_hex(sha256)
    return Path(root) / FROZEN / "tess-eb" / sha256 / TESS_EB_NAME


def tess_eb_input(sha256: str, url: str) -> dict[str, str]:
    """The declaration of the TESS-EB edition as an input of a v0.5 claim (its ``reproduction``
    section, read by ``refute prepare-inputs`` and checked before every run), at its frozen
    destination. The edition is not redistributed (#33): ``url`` is the public source (VizieR),
    never a copy made by Refute."""
    dest = frozen_tess_eb_path(Path("."), sha256).as_posix()
    return {"name": "TESS-EB edition", "sha256": sha256, "url": url, "dest": dest}


def _no_link(path: Path, stop: Path) -> None:
    """Refuse a link or a junction on ``path`` or any parent up to ``stop`` (inclusive)."""
    for part in [path, *path.parents]:
        if part.exists() or part.is_symlink():
            if part.is_symlink() or part.is_junction():
                raise ValueError(f"{part} is a link or a junction")
        if part == stop:
            break


def place_frozen_tess_eb(source: Path, root: Path, sha256: str) -> Path:
    """Copy the verified edition to its frozen folder and return the path. Idempotent when the
    folder already holds the same bytes; refuses other bytes, a link, or a source whose SHA-256
    is not ``sha256``."""
    source, root = Path(source), Path(root)
    dest = frozen_tess_eb_path(root, sha256)
    _no_link(source, source.parent)
    if _sha256(source) != sha256:
        raise ValueError(f"{source}: its SHA-256 is not {sha256}")
    _no_link(dest, root)
    if dest.exists():
        if _sha256(dest) != sha256:
            raise ValueError(f"{dest} holds other bytes; it is never overwritten")
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    _no_link(dest.parent, root)
    temporary = dest.with_name(dest.name + ".part")
    shutil.copyfile(source, temporary)
    if _sha256(temporary) != sha256:
        os.remove(temporary)
        raise ValueError("the copy's SHA-256 differs from the source's")
    os.replace(temporary, dest)
    return dest
