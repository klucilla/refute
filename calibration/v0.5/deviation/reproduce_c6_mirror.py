"""Exit criterion 6 with the recorded deviation of 2026-11-05 (#199): the same procedure as
``calibration/v0.5/reviews/reproduce_c6.py`` (the ``bash`` block of the dossier's
``REPRODUCE.md`` run literally, in a new folder, with no variable of the project's own checkout),
with one input placed from an official VizieR mirror and nothing else changed.

The single deviation: right before the first ``refute discover`` command, the TESS-EB table
fetched from the mirror by ``fetch_tess_eb_mirror.py`` is copied to
``<clean clone>/.cache/<cache_path>``, the path the frozen code reads (``core.run.
default_cache_dir`` and the scan's ``cache_path``). Before the copy, the file's content SHA-256
must equal the one the claim's scan records, read from the clean clone's own scan; the copy is
created exclusively (never over a file) and checked byte for byte. The frozen code then checks
the content hash again (``ebcatalog.prepare_external_snapshots``) and does not download.

After the instructions, ``uv run refute verify calibration/v0.5/claim.yaml`` runs again in the
clean clone (the claim must stay PASS: nothing in the claim, the code or the lock changed).
Every step is logged in ``reproduce.json`` with its exit code and UTC times; the placement is a
step of its own, with the source, the destination and both hashes.

Usage, from the repository root:
``.venv/Scripts/python.exe calibration/v0.5/deviation/reproduce_c6_mirror.py <dossier>
<work-folder> <fetch.json>`` (``<work-folder>`` new, inside ``.cache/``).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCAN = "calibration/v0.5/eb_catalog_scan.json"
PREP = Path(".cache/v05/c6-prep")
MIRRORS = ("vizier.cfa.harvard.edu", "vizier.idia.ac.za")
# the commands the generated instructions run (REPRODUCE.md), by their leading words; cd is
# handled apart
ALLOWED = (
    ("git", "clone"),
    ("git", "checkout"),
    ("uv", "sync", "--frozen"),
    ("uv", "run", "refute", "verify"),
    ("uv", "run", "refute", "discover"),
    ("uv", "run", "refute", "check-dossier"),
)


def no_link_on_the_way(path: Path, root: Path) -> bool:
    """True when no component of ``path`` from ``root`` down (both included) is a symbolic link
    or a junction."""
    path, root = Path(os.path.abspath(path)), Path(os.path.abspath(root))
    if not path.is_relative_to(root):
        return False
    current = root
    for part in (None, *path.relative_to(root).parts):
        if part is not None:
            current = current / part
        if current.is_symlink() or current.is_junction():
            return False
    return True


def allowed(argv: list[str]) -> bool:
    return any(tuple(argv[: len(prefix)]) == prefix for prefix in ALLOWED)


VERIFY_AFTER = "uv run refute verify calibration/v0.5/claim.yaml"


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _commands():
    spec = importlib.util.spec_from_file_location(
        "reproduce_c6", HERE.parent / "reviews" / "reproduce_c6.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.commands


def place(clone: Path, source: Path) -> dict:
    """Copy the mirror's TESS-EB file to the path the clean clone's frozen code reads."""
    from refute.packs.tess.ebcatalog import content_sha256, external_snapshots

    scan = json.loads((clone / SCAN).read_text(encoding="utf-8"))
    snaps = [s for s in external_snapshots(scan) if s["parser"] == "tess-eb-vizier-tsv"]
    if len(snaps) != 1:
        raise RuntimeError("expected one TESS-EB snapshot in the clean clone's scan")
    snap = snaps[0]
    data = source.read_bytes()
    if content_sha256(data) != snap["content_sha256"]:
        raise RuntimeError("the mirror file's content SHA-256 is not the claim's: STOP")
    dest = clone / ".cache" / snap["cache_path"]
    if dest.is_symlink() or not dest.resolve().is_relative_to(clone.resolve()):
        raise RuntimeError(f"{dest} is not inside the clean clone")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(source, "rb") as src, open(dest, "xb") as out:
        shutil.copyfileobj(src, out)
    if dest.read_bytes() != data:
        raise RuntimeError("the placed copy differs from the source")
    return {
        "source": source.as_posix(),
        "destination": dest.relative_to(clone).as_posix(),
        "raw_sha256": hashlib.sha256(data).hexdigest(),
        "content_sha256": content_sha256(data),
        "claim_content_sha256": snap["content_sha256"],
    }


def mirror_source(fetch_json: Path) -> tuple[dict, Path]:
    """The fetch record and its file, checked: both inside the preparation folder, no link on
    the way, a host of the approved list, and the file's raw SHA-256 the one the fetch
    recorded."""
    root = Path.cwd()
    prep = Path(os.path.abspath(root / PREP))
    fetch_json = Path(os.path.abspath(fetch_json))
    if not fetch_json.is_relative_to(prep) or not no_link_on_the_way(fetch_json, root):
        raise SystemExit(f"{fetch_json} is not inside {PREP.as_posix()} (or a link is on the way)")
    fetch = json.loads(fetch_json.read_text(encoding="utf-8"))
    if fetch.get("host") not in MIRRORS or not fetch.get("content_matches"):
        raise SystemExit("the fetch record is not a matching fetch from an approved mirror")
    source = Path(os.path.abspath(root / fetch["file"]))
    if not source.is_relative_to(prep / fetch["host"]) or not no_link_on_the_way(source, root):
        raise SystemExit(f"{source} is not inside {PREP.as_posix()}/{fetch['host']}")
    if hashlib.sha256(source.read_bytes()).hexdigest() != fetch["raw_sha256"]:
        raise SystemExit("the mirror file's raw SHA-256 is not the one its fetch recorded")
    return fetch, source.resolve()


def main(argv: list[str]) -> int:
    dossier = Path(argv[0]).resolve()
    work = Path(argv[1])
    fetch, source = mirror_source(Path(argv[2]))
    cache = (Path.cwd() / ".cache").resolve()
    if not work.resolve().is_relative_to(cache) or work.exists():
        raise SystemExit(f"{work} must be a new folder inside .cache/")
    if not no_link_on_the_way(work.parent, Path.cwd()):
        raise SystemExit(f"a link is on the way to {work}")
    work.mkdir(parents=True)
    work = work.resolve()
    steps = _commands()((dossier / "REPRODUCE.md").read_text(encoding="utf-8"))
    steps.append(VERIFY_AFTER)
    env = {
        k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")
    }
    cwd = work
    log: list[dict] = []
    code = 0
    placed = False
    for line in steps:
        line = line.replace("<this dossier>", dossier.as_posix())
        argv_ = shlex.split(line, posix=True)
        if not placed and argv_[:4] == ["uv", "run", "refute", "discover"]:
            entry = {"command": "(deviation) place the mirror's TESS-EB file", "start": now()}
            try:
                entry.update(place(cwd, source), exit=0)
            except Exception as exc:  # noqa: BLE001 - recorded; the run stops
                entry.update(error=repr(exc), exit=1)
            entry["end"] = now()
            log.append(entry)
            placed = True
            if entry["exit"]:
                code = 1
                break
        entry = {"command": line, "cwd": cwd.relative_to(work).as_posix() or ".", "start": now()}
        if line == VERIFY_AFTER:
            entry["note"] = "after the instructions: the claim must still verify"
        if argv_ and argv_[0] == "cd":
            target = (cwd / argv_[1]).resolve() if len(argv_) == 2 else None
            if target is None or not target.is_relative_to(work):
                entry.update(end=now(), exit=1, error="cd outside the work folder")
                log.append(entry)
                code = 1
                break
            cwd = target
            entry.update(end=now(), exit=0)
            log.append(entry)
            continue
        if not allowed(argv_):
            entry.update(end=now(), exit=1, error=f"command {line!r} is not expected")
            log.append(entry)
            code = 1
            break
        out = work / f"step-{len(log) + 1:02d}.log"
        with open(out, "w", encoding="utf-8") as handle:
            proc = subprocess.run(argv_, cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT)
        entry.update(end=now(), exit=proc.returncode, log=out.name)
        log.append(entry)
        if proc.returncode != 0:
            code = proc.returncode
            break
    if code == 0 and not placed:
        log.append({"command": "(deviation) placement", "exit": 1, "error": "never placed"})
        code = 1
    record = {
        "dossier": dossier.name,
        "deviation": "one input placed from an official CDS mirror, verified by the claim's "
        "content hash (the maintainer's decision of 2026-11-05, #199)",
        "note": "criterion 6 as written requires nothing placed by hand; this run placed one "
        "input, the single exception the maintainer approved",
        "mirror": {k: fetch[k] for k in ("host", "url", "utc", "raw_sha256", "content_sha256")},
        "steps": log,
        "result": "PASS" if code == 0 else "FAIL",
    }
    (work / "reproduce.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
