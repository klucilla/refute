"""Place the TESS-EB static edition where the C3 run reads it, under the deviation approved on
2026-11-04 (#199; calibration/v0.5/deviation/README.md).

Why: ``run_calibration.py c3-run`` resolves the claim's TESS-EB reference rows from
``<the c3-fetch cache>/v04/tess-eb/tess_ebs_prsa2022.tsv`` (the ``cache_path`` of
``eb_catalog_scan.json``; ``refute.packs.tess.ebcatalog.resolve_references``), but the frozen
``c3-fetch`` never places the edition there, so every control would be an error record. This
script copies the static edition there; it changes no analysis code, threshold, test role,
selection or frozen input.

- The expected hashes are read from the claim's scan (``eb_catalog_scan.json``: ``cache_path``,
  raw ``sha256`` and ``content_sha256``) and must equal those ``inputs.json`` froze for
  ``tess_eb.tsv``; the source (by default the static edition's path recorded in ``inputs.json``)
  must have both: the raw SHA-256 (the exact file of 2026-10-18) and the content SHA-256 (the
  rule the resolver checks).
- Nothing is written over: when the destination exists, it must hold the same raw bytes
  (nothing is done) or the script stops. The copy goes to an exclusively created temporary file
  in the destination's folder, is checked, and is published by a hard link, which fails when the
  destination appeared meanwhile; the temporary file is then removed (this call's own file only).
- The cache folder and the source must be inside the repository; no link or junction is
  accepted on the source or on the way to the destination (each folder is created one level at a
  time, ``refute.core.reproduce.make_parents``).
- Last, the claim's catalog is loaded from that cache exactly as ``c3-run`` loads it
  (``refute.packs.tess.discover.measure.load_catalogs``), so the reference rows resolve.

Run from the repository root, with the cache given to ``c3-fetch``:
``.venv/Scripts/python.exe calibration/v0.5/deviation/prepare_tess_eb.py --cache <dir>``
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

STEP = Path("calibration/v0.5")
SCAN = STEP / "eb_catalog_scan.json"
CATALOG = STEP / "eb_catalog.csv"
INPUTS = STEP / "inputs.json"


class PlacementError(Exception):
    """The edition cannot be placed: nothing (more) is written."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def is_link(path: Path) -> bool:
    return path.is_symlink() or (path.exists() and path.is_junction())


def no_link_up_to(path: Path, stop: Path) -> None:
    """Refuse a link or a junction on ``path`` and every parent up to ``stop`` (inclusive)."""
    for part in [path, *path.parents]:
        if is_link(part):
            raise PlacementError(f"{part} is a link or a junction")
        if part == stop:
            return
    raise PlacementError(f"{path} is not inside {stop}")


def expected(root: Path) -> dict:
    """The TESS-EB snapshot of the claim's scan, checked against the frozen inputs record."""
    scan = json.loads((root / SCAN).read_text(encoding="utf-8"))
    snaps = [s for s in scan["snapshots"] if s.get("catalog_name") == "TESS-EB"]
    if len(snaps) != 1 or snaps[0].get("redistributed") is not False:
        raise PlacementError("the scan does not hold exactly one external TESS-EB snapshot")
    snap = snaps[0]
    inputs = json.loads((root / INPUTS).read_text(encoding="utf-8"))
    frozen = [f for f in inputs["files"] if f["name"] == snap["file"]]
    if len(frozen) != 1:
        raise PlacementError(f"inputs.json does not hold exactly one {snap['file']}")
    edition = frozen[0]["static_edition"]
    if frozen[0]["sha256"] != snap["sha256"] or edition["content_sha256"] != snap["content_sha256"]:
        raise PlacementError("the scan's hashes are not those frozen in inputs.json")
    cache_path = snap["cache_path"]
    parts = cache_path.split("/")
    if cache_path.startswith("/") or "\\" in cache_path or any(p in ("", ".", "..") for p in parts):
        raise PlacementError(f"unexpected cache_path {cache_path!r}")
    return {
        "cache_path": cache_path,
        "sha256": snap["sha256"],
        "content_sha256": snap["content_sha256"],
        "default_source": edition["path"],
    }


def place(root: Path, cache: Path, source: Path, want: dict) -> dict:
    from refute.core.reproduce import InputError, make_parents
    from refute.packs.tess.ebcatalog import content_sha256

    root = root.resolve()
    if is_link(root):
        raise PlacementError(f"{root} is a link or a junction")
    cache = Path(os.path.normpath(root / cache))  # an absolute cache stays itself
    try:
        cache.relative_to(root)
    except ValueError as error:
        raise PlacementError(f"the cache {cache} is not inside the repository") from error
    if cache == root:
        raise PlacementError("the cache cannot be the repository root")
    source = Path(os.path.normpath(root / source))
    if not source.is_relative_to(root):
        raise PlacementError(f"the source {source} is not inside the repository")
    if not source.is_file():
        raise PlacementError(f"no source file at {source}")
    no_link_up_to(source, root)
    if sha256_file(source) != want["sha256"]:
        raise PlacementError(f"{source}: its SHA-256 is not {want['sha256']}")
    if content_sha256(source.read_bytes()) != want["content_sha256"]:
        raise PlacementError(f"{source}: its content SHA-256 is not {want['content_sha256']}")
    dest = cache.joinpath(*want["cache_path"].split("/"))
    if dest.exists() or dest.is_symlink():
        no_link_up_to(dest, root)
        if not dest.is_file() or sha256_file(dest) != want["sha256"]:
            raise PlacementError(f"{dest} exists with other bytes; it is never written over")
        return {"dest": dest.relative_to(root).as_posix(), "action": "already in place"}
    try:
        make_parents(dest.parent, root)
    except InputError as error:
        raise PlacementError(str(error)) from error
    no_link_up_to(dest.parent, root)
    temporary = dest.with_name(f"{dest.name}.{os.getpid()}.part")
    with open(temporary, "xb") as out, open(source, "rb") as src:  # exclusive: never a link
        shutil.copyfileobj(src, out)
    try:  # from here on the temporary file is this call's own
        if sha256_file(temporary) != want["sha256"]:
            raise PlacementError("the copy's SHA-256 differs from the source's")
        try:
            os.link(temporary, dest)  # fails when the destination exists: never written over
        except FileExistsError as error:
            raise PlacementError(f"{dest} appeared meanwhile; it is never written over") from error
    finally:
        os.remove(temporary)
    if sha256_file(dest) != want["sha256"]:
        raise PlacementError(f"{dest}: its SHA-256 after the copy is not {want['sha256']}")
    return {"dest": dest.relative_to(root).as_posix(), "action": "copied"}


def resolves(root: Path, cache: Path) -> int:
    """The claim's catalog loaded from ``cache`` as ``c3-run`` loads it; the reference rows."""
    from refute.packs.tess.discover.measure import load_catalogs

    cache = Path(os.path.normpath(root.resolve() / cache))
    catalogs, _ = load_catalogs(((root / CATALOG).as_posix(),), (root / SCAN).as_posix(), cache)
    return sum(1 for entry in catalogs if entry.catalog == "TESS-EB")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cache", required=True, help="the cache given to c3-fetch")
    parser.add_argument("--source", help="the static edition (default: its inputs.json path)")
    args = parser.parse_args(argv)
    root = Path.cwd()
    want = expected(root)
    source = Path(args.source or want["default_source"])
    result = place(root, Path(args.cache), source, want)
    result.update(
        {
            "sha256": want["sha256"],
            "content_sha256": want["content_sha256"],
            "tess_eb_reference_rows_resolved": resolves(root, Path(args.cache)),
        }
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except PlacementError as error:
        print(f"STOP: {error}", file=sys.stderr)
        sys.exit(1)
