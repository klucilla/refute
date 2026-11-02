"""The inputs a clean clone lacks to reproduce the v0.4 pilot's five stage-2 dossiers, fetched and
checked automatically (the maintainer's approval of 2026-11-01, Option 1; #189). Nothing is
placed by hand: every input comes from a declared source and is checked against a SHA-256 that a
commit recorded before the reproduction runs. Any difference stops the step; nothing is adjusted
to make a hash match, and nothing falls back to another file.

Outside the code hash on purpose: the locked code (src/, pyproject.toml, uv.lock) is unchanged.

Subcommands:

- ``build-archives --out <dir>`` (the maintainer's side, before the reproduction commit): the two
  deterministic zips that a clone cannot rebuild, and their record
  ``calibration/v0.4/runs/reproduce_archives.json`` (hashes only):
  ``v0.4-stage1-verdicts.zip`` (the 100 funnel stage-1 ``verdict.json`` files, which
  ``verify_promotion`` reads) and ``v0.4-stage2-originals.zip`` (the five sealed stage-2 dossiers,
  for ``check-dossier --against``). Private until P7, then deposited by the maintainer.
- ``prepare --archive <folder or https URL>`` (the reproducer's side, in the clone's root, with a
  fresh ``.cache``):
  - the TESS-EB static edition: downloaded from VizieR (the URL in ``inputs.json`` on the CDS,
    then on the mirrors of ``MIRRORS``, in order), its content checked, its header's server and
    date lines restored to the frozen values of ``inputs.json``, its raw SHA-256 checked, and
    written where the claim's scan and the promotion check read it; a server that does not give
    the frozen edition is refused and recorded, and ``prepare.json`` names the server used;
  - ``toi.csv``, ``ctoi.csv``, ``pscomppars.csv`` from git; ``gaia_dr3_eb.csv`` from its public
    release asset; each checked against ``inputs.json``;
  - the two zips from the archive, checked against ``reproduce_archives.json``; each stage-1
    verdict against ``entries.json``; each original dossier's core recomputed against its public
    anchor, and its annexes against their manifests.
- ``instructions --commit <C> --archive <location> --out <file> [--version 3|4 --doi <DOI>
  [--reproduced <commit>]]``: the corrected instructions, with every command written out:
  ``REPRODUCE-2.md`` (version 2, the default), ``REPRODUCE-3.md`` (version 3: the same commands,
  with ``ARCHIVE`` the public deposit of P7) or ``REPRODUCE-4.md`` (version 4: the commit with the
  VizieR mirrors, checked by ``git diff`` against the commit of the full reproduction).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import time
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]
V04 = ROOT / "calibration" / "v0.4"
RUNS = V04 / "runs"
ARCHIVES_RECORD = RUNS / "reproduce_archives.json"
STAGE1_ZIP = "v0.4-stage1-verdicts.zip"
ORIGINALS_ZIP = "v0.4-stage2-originals.zip"
ORIGINALS_DIR = "originals"
PILOT = ROOT / ".cache" / "v04" / "pilot"
PREPARE_RECORD = Path(".cache") / "v04" / "reproduce" / "prepare.json"
CDS_HOST = "vizier.cds.unistra.fr"
# The VizieR servers asked for the TESS-EB table, in order: the CDS, then the mirrors chosen by the
# maintainer (2026-11-02), from VizieR's mirrors page (calibration/v0.4/sources/
# vizier-mirrors-2026-11-02.md). NAOJ and China-VO answer over HTTP only; integrity comes from the
# frozen edition's hashes, never from the transport.
MIRRORS = (
    "https://vizier.cds.unistra.fr",
    "https://vizier.cfa.harvard.edu",
    "https://vizier.idia.ac.za",
    "http://vizier.nao.ac.jp",
    "http://vizier.china-vo.org",
)
HOSTS = tuple(urlsplit(base).hostname for base in MIRRORS)
TESS_EB_TIMEOUT = 120.0
TESS_EB_MAX_BYTES = 2 * 1024 * 1024
GIT_INPUTS = ("toi.csv", "ctoi.csv", "pscomppars.csv")
STAGE2 = (
    ("controls-s2", "TIC-86396382"),
    ("controls-s2", "TIC-393911494"),
    ("promoted-s2", "TIC-88096786"),
    ("promoted-s2", "TIC-286480954"),
    ("promoted-s2", "TIC-406413408"),
)
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
ATTEMPTS = 3
LF = "\n"


class InputError(Exception):
    """An input could not be obtained or does not match its recorded hash."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------- TESS-EB header


def rebuild_tess_eb(fresh: bytes, obtained: str, url: str) -> bytes:
    """The frozen raw bytes from a fresh VizieR download: only the metadata of the ``#`` lines
    that name the server, the query date and the request URL are restored (server -> the CDS
    host, dates -> ``obtained``, request -> ``url``); every other byte is the download's. The
    content (non-comment lines) is never touched, so a changed table can never pass."""
    out = []
    for line in fresh.split(b"\n"):
        text = line.decode("utf-8")
        if text.startswith("#   VizieR Astronomical Server "):
            for host in HOSTS:
                if text == f"#   VizieR Astronomical Server {host}":
                    text = f"#   VizieR Astronomical Server {CDS_HOST}"
        elif text.startswith("#    Date: "):
            text = re.sub(r"Date: \S+", lambda _m: f"Date: {obtained}", text)
        elif text.startswith("#INFO\trequest_date="):
            text = re.sub(r"request_date=\S+", lambda _m: f"request_date={obtained}", text)
        elif text.startswith("#INFO\trequest="):
            text = re.sub(r"request=\S+", lambda _m: f"request={url}", text)
        out.append(text.encode("utf-8"))
    return b"\n".join(out)


def on_server(url: str, base: str) -> str:
    """The recorded URL with only its scheme and host replaced by a server's; path and query
    are kept."""
    parts, server = urlsplit(url), urlsplit(base)
    return urlunsplit((server.scheme, server.netloc, parts.path, parts.query, parts.fragment))


def fetch_tess_eb(url: str) -> tuple[bytes, str]:
    """One server's answer for the TESS-EB table, with up to ATTEMPTS tries: HTTP status 200 and
    at most TESS_EB_MAX_BYTES, read with a timeout of TESS_EB_TIMEOUT per blocking operation.
    Returns the bytes and the final URL (after any redirect)."""
    error: Exception | None = None
    for attempt in range(ATTEMPTS):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "refute-reproduce/0.4"})
            with urllib.request.urlopen(request, timeout=TESS_EB_TIMEOUT) as response:  # noqa: S310
                final = response.geturl()
                if response.status != 200:
                    raise InputError(f"HTTP status {response.status} from {final}")
                data = response.read(TESS_EB_MAX_BYTES + 1)
                if len(data) > TESS_EB_MAX_BYTES:
                    raise InputError(f"larger than {TESS_EB_MAX_BYTES} bytes from {final}")
                return data, final
        except Exception as exc:  # noqa: BLE001
            error = exc
            if attempt + 1 < ATTEMPTS:
                time.sleep(5 * (attempt + 1))
    raise InputError(f"download failed after {ATTEMPTS} attempts: {type(error).__name__}: {error}")


def tess_eb(record: dict[str, Any], download=None) -> tuple[bytes, dict[str, Any]]:
    """The TESS-EB static edition, from the first VizieR server of MIRRORS (in order) whose answer
    gives the frozen edition: its content hash first, then its raw hash after
    ``rebuild_tess_eb``. ``download(url)`` returns the bytes and the final URL; a server whose
    answer fails (no answer, a redirect outside MIRRORS, a status, a size, invalid bytes or a
    hash) is refused and recorded with the reason and the hashes observed, and the next is
    asked. No server after the accepted one is asked. If none matches, the step stops."""
    from refute.packs.tess.ebcatalog import content_sha256

    static = record["static_edition"]
    tried: list[dict[str, Any]] = []
    for base in MIRRORS:
        url = on_server(record["url"], base)
        entry: dict[str, Any] = {"url": url}
        try:
            fresh, final = (download or fetch_tess_eb)(url)
            server = urlsplit(final).hostname
            entry.update({"final_url": final, "bytes": len(fresh), "received_utc": utc_now()})
            if server not in HOSTS:
                raise InputError(f"redirected to {server}, which is not in the server list")
            entry["content_sha256"] = content_sha256(fresh)
            if entry["content_sha256"] != static["content_sha256"]:
                raise InputError("content SHA-256 differs from the frozen edition")
            rebuilt = rebuild_tess_eb(fresh, static["obtained"], record["url"])
            entry["rebuilt_sha256"] = sha256(rebuilt)
            if entry["rebuilt_sha256"] != record["sha256"]:
                raise InputError("raw SHA-256 differs after the header rebuild")
        except Exception as exc:  # noqa: BLE001 - recorded, then the next server
            entry["error"] = f"{type(exc).__name__}: {exc}"[:300]
            entry["refused_utc"] = utc_now()
            tried.append(entry)
            continue
        return rebuilt, {
            "source": final,
            "requested": url,
            "server": server,
            "obtained_utc": entry["received_utc"],
            "failed_sources": tried,
        }
    raise InputError(
        f"TESS-EB: none of the {len(MIRRORS)} VizieR servers gave the frozen edition (raw SHA-256 "
        f"{record['sha256']}, content SHA-256 {static['content_sha256']}); refused in order: "
        f"{tried}"
    )


# ---------------------------------------------------------------- zips


_RESERVED = {"con", "prn", "aux", "nul"} | {f"{p}{i}" for p in ("com", "lpt") for i in range(10)}
_FORBIDDEN = set('<>:"\\|?*')


def _safe_name(name: str) -> bool:
    """A relative POSIX path that is portable to Windows: no empty, ``.`` or ``..`` component,
    no forbidden or control character, no component ending in a dot or a space, no reserved
    device name."""
    if not name or name.startswith("/") or name.endswith("/"):
        return False
    for part in name.split("/"):
        if part in ("", ".", "..") or part[-1] in ". ":
            return False
        if any(c in _FORBIDDEN or ord(c) < 32 for c in part):
            return False
        if part.split(".")[0].lower() in _RESERVED:
            return False
    return True


def read_zip(data: bytes, expected_sha256: str, expected_names: set[str]) -> dict[str, bytes]:
    """The members of a recorded zip, after its SHA-256, its member names (exactly the expected
    set, each safe, once, and distinct ignoring case) and nothing else are checked. A directory
    entry is refused: the archives hold files only."""
    if sha256(data) != expected_sha256:
        raise InputError("the zip's SHA-256 differs from its record")
    members: dict[str, bytes] = {}
    folded: set[str] = set()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                raise InputError(f"directory entry {info.filename!r}")
            if not _safe_name(info.filename):
                raise InputError(f"unsafe member name {info.filename!r}")
            if info.filename in members or info.filename.lower() in folded:
                raise InputError(f"duplicate member {info.filename!r}")
            folded.add(info.filename.lower())
            members[info.filename] = archive.read(info)
    if set(members) != expected_names:
        missing = sorted(expected_names - set(members))[:5]
        extra = sorted(set(members) - expected_names)[:5]
        raise InputError(f"zip members differ from the record: missing {missing}, extra {extra}")
    return members


def write_zip(path: Path, files: dict[str, bytes]) -> str:
    """A deterministic zip: sorted names, fixed times and modes. Refuses an existing file."""
    with zipfile.ZipFile(path, "x") as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name)
            info.date_time = ZIP_TIME
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            info.create_system = 3
            archive.writestr(info, files[name], compresslevel=9)
    return sha256(path.read_bytes())


def stage1_verdict_hashes() -> dict[str, str]:
    entries = load(RUNS / "stage1" / "entries.json")["entries"]
    return {e["target_key"]: e["verdict_sha256"] for e in entries}


def core_anchors() -> dict[str, str]:
    controls = load(RUNS / "controls_seals.json")["runs"]["stage2"]["core_sha256"]
    anchor = load(RUNS / "p5_anchor.json")["stage2_dossiers"]
    out = {}
    for run, key in STAGE2:
        out[f"{run}/{key}"] = controls[key] if run == "controls-s2" else anchor[key]["core_sha256"]
    return out


# ---------------------------------------------------------------- build-archives


def cmd_build_archives(out: Path) -> int:
    from refute.core.seal import check_sealed, read_seal

    if ARCHIVES_RECORD.exists() or out.exists():
        print(f"{ARCHIVES_RECORD} or {out} exists: the archives are built once")
        return 1
    hashes = stage1_verdict_hashes()
    seals = load(RUNS / "stage1" / "seals.json")["core_sha256"]
    stage1: dict[str, bytes] = {}
    for key in sorted(hashes):
        dossier = PILOT / "stage1" / "funnel-s1" / key
        if not check_sealed(dossier).ok or read_seal(dossier)["core_sha256"] != seals[key]:
            print(f"{key}: the stage-1 core is not intact against its committed seal")
            return 1
        data = (dossier / "verdict.json").read_bytes()
        if sha256(data) != hashes[key]:
            print(f"{key}: verdict.json differs from entries.json")
            return 1
        stage1[f"funnel-s1/{key}/verdict.json"] = data
    anchors = core_anchors()
    originals: dict[str, bytes] = {}
    for run, key in STAGE2:
        dossier = PILOT / "stage2" / run / key
        if (
            not check_sealed(dossier).ok
            or read_seal(dossier)["core_sha256"] != anchors[f"{run}/{key}"]
        ):
            print(f"{run}/{key}: not intact against its public anchor")
            return 1
        files = sorted(p for p in dossier.rglob("*") if p.is_file())
        for path in files:
            originals[f"{run}/{key}/{path.relative_to(dossier).as_posix()}"] = path.read_bytes()
    out.mkdir(parents=True)
    record = {
        "schema": "refute-v04-reproduce-archives-1",
        "built_utc": utc_now(),
        "location_before_p7": "the maintainer's private archive (not public)",
        "location_after_p7": "a deposit by the maintainer at P7, with the same hashes",
        "stage1": {
            "file": STAGE1_ZIP,
            "sha256": write_zip(out / STAGE1_ZIP, stage1),
            "members": {name: sha256(data) for name, data in sorted(stage1.items())},
        },
        # only the zip's hash is published: it pins every member name and byte, and the
        # dossiers' structure (files, annexes) stays in the private zip until P7
        "originals": {
            "file": ORIGINALS_ZIP,
            "sha256": write_zip(out / ORIGINALS_ZIP, originals),
            "dossiers": [f"{run}/{key}" for run, key in STAGE2],
        },
    }
    with open(ARCHIVES_RECORD, "x", encoding="utf-8", newline=LF) as handle:
        handle.write(json.dumps(record, indent=2, sort_keys=True) + LF)
    print(json.dumps({k: record[k]["sha256"] for k in ("stage1", "originals")}, indent=2))
    return 0


# ---------------------------------------------------------------- prepare


def fetch(url: str, timeout: float = 600.0) -> bytes:
    """One download with up to ATTEMPTS tries (a transient error is retried, never skipped)."""
    error: Exception | None = None
    for attempt in range(ATTEMPTS):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "refute-reproduce/0.4"})
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
                return response.read()
        except Exception as exc:  # noqa: BLE001
            error = exc
            time.sleep(5 * (attempt + 1))
    raise InputError(f"download failed after {ATTEMPTS} attempts: {url}: {error}")


def from_archive(location: str, name: str) -> bytes:
    if location.startswith("https://"):
        return fetch(location.rstrip("/") + "/" + name)
    return (Path(location) / name).read_bytes()


def inside(rel: str) -> Path:
    """A destination given relative to the clone's root: relative, without ``..``, and resolving
    inside the root."""
    if not _safe_name(rel):
        raise InputError(f"unsafe destination {rel!r}")
    path = ROOT / rel
    if not path.resolve().is_relative_to(ROOT):
        raise InputError(f"destination outside the clone: {rel!r}")
    return path


def _no_links(path: Path) -> None:
    current = ROOT
    for part in path.relative_to(ROOT).parts:
        current = current / part
        if current.is_symlink() or current.is_junction():
            raise InputError(f"a link on the way to {path}")


def write_new(path: Path, data: bytes) -> None:
    """Write a prepared input to a new file inside the clone (exclusive creation; no link on the
    way). A fresh clone has none of these files, so an existing one stops the step."""
    _no_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _no_links(path)
    try:
        with open(path, "xb") as handle:
            handle.write(data)
    except FileExistsError as exc:
        raise InputError(f"{path} exists: not a fresh clone") from exc


def cmd_prepare(location: str) -> int:
    from refute.core.seal import check_sealed, read_seal

    work = Path.cwd()
    if work.resolve() != ROOT:
        print(f"run this from the clone's root ({ROOT}), not {work}")
        return 1
    if (ROOT / PREPARE_RECORD).exists():
        print(f"{PREPARE_RECORD} exists: the inputs were already prepared here")
        return 1
    inputs = load(V04 / "inputs.json")
    files = {f["name"]: f for f in inputs["files"]}
    provenance = load(RUNS / "promotion.json")["provenance"]
    scan = load(V04 / "eb_catalog_scan.json")
    tess_snapshot = next(s for s in scan["snapshots"] if s["catalog_name"] == "TESS-EB")
    record: dict[str, Any] = {"started_utc": utc_now(), "archive": location, "inputs": {}}
    try:
        # every destination is checked before anything is downloaded or written: inside the
        # clone, and new (a fresh clone has none of them)
        inputs_dir = inside(provenance["inputs_dir"])
        stage1_dir = inside(provenance["stage1_run_dir"])
        tess_cache = inside(".cache/" + tess_snapshot["cache_path"])
        originals_dir = inside(ORIGINALS_DIR)
        record_path = inside(PREPARE_RECORD.as_posix())
        for path in (inputs_dir, stage1_dir, tess_cache, originals_dir, record_path):
            _no_links(path)
            if path.exists() or path.is_symlink():
                raise InputError(f"{path} exists: not a fresh clone")
        data, how = tess_eb(files["tess_eb.tsv"])
        write_new(inputs_dir / "tess_eb.tsv", data)
        write_new(tess_cache, data)
        record["inputs"]["tess_eb.tsv"] = {"sha256": sha256(data), **how}
        for name in GIT_INPUTS:
            data = (V04 / "inputs" / name).read_bytes()
            if sha256(data) != files[name]["sha256"]:
                raise InputError(f"{name} in git differs from inputs.json")
            write_new(inputs_dir / name, data)
            record["inputs"][name] = {"sha256": sha256(data), "source": "git"}
        gaia = files["gaia_dr3_eb.csv"]
        data = fetch(gaia["url"])
        if sha256(data) != gaia["sha256"]:
            raise InputError("gaia_dr3_eb.csv differs from inputs.json")
        write_new(inputs_dir / "gaia_dr3_eb.csv", data)
        record["inputs"]["gaia_dr3_eb.csv"] = {
            "sha256": sha256(data),
            "source": gaia["url"],
            "obtained_utc": utc_now(),
        }
        archives = load(ARCHIVES_RECORD)
        stage1 = archives["stage1"]
        members = read_zip(
            from_archive(location, stage1["file"]), stage1["sha256"], set(stage1["members"])
        )
        expected = stage1_verdict_hashes()
        for name, data in members.items():
            key = PurePosixPath(name).parts[1]
            if sha256(data) != stage1["members"][name] or sha256(data) != expected.get(key):
                raise InputError(f"{name}: differs from entries.json")
            write_new(stage1_dir / key / "verdict.json", data)
        record["inputs"][stage1["file"]] = {"sha256": stage1["sha256"], "members": len(members)}
        originals = archives["originals"]
        data = from_archive(location, originals["file"])
        if sha256(data) != originals["sha256"]:
            raise InputError("the originals zip differs from its record")
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = {i.filename for i in archive.infolist()}
        # the zip's hash pins every name and byte; read_zip still refuses unsafe names
        members = read_zip(data, originals["sha256"], names)
        wanted = {f"{run}/{key}" for run, key in STAGE2}
        if {"/".join(n.split("/")[:2]) for n in members} != wanted:
            raise InputError("the originals zip does not hold exactly the five stage-2 dossiers")
        for name, content in members.items():
            write_new(originals_dir / name, content)
        anchors = core_anchors()
        for ident in sorted(wanted):
            dossier = originals_dir / ident
            if not check_sealed(dossier).ok:
                raise InputError(f"{ident}: the original is not intact (core or an annex)")
            if read_seal(dossier)["core_sha256"] != anchors[ident]:
                raise InputError(f"{ident}: the original's core differs from its public anchor")
        record["inputs"][originals["file"]] = {"sha256": originals["sha256"], "dossiers": 5}
        record["finished_utc"] = utc_now()
        text = json.dumps(record, indent=2, sort_keys=True) + LF
        write_new(record_path, text.encode("utf-8"))
    except InputError as exc:
        print(f"STOP: {exc}")
        return 1
    print(text, end="")
    return 0


# ---------------------------------------------------------------- instructions


SAME_AT_BOTH_COMMITS = (
    "src/",
    "pyproject.toml",
    "uv.lock",
    "calibration/v0.4/claim.yaml",
    "calibration/v0.4/inputs.json",
    "calibration/v0.4/runs/promotion.json",
    "calibration/v0.4/runs/reproduce_archives.json",
)


def instructions(
    commit: str,
    archive: str,
    version: int = 2,
    doi: str | None = None,
    reproduced: str | None = None,
) -> str:
    """Version 2 (the private archive, before P7), version 3 (the same commands; ``ARCHIVE`` is
    the public deposit whose DOI is given) or version 4 (the commit with the VizieR mirrors; a
    ``git diff`` checks that it has the locked code and the records of ``reproduced``, the commit
    of the full reproduction). Versions 2 and 3 are kept byte for byte."""
    if version not in (2, 3, 4):
        raise ValueError("version must be 2, 3 or 4")
    if version >= 3 and (not archive.startswith("https://") or not doi):
        raise ValueError(f"version {version} needs an https archive and its DOI")
    if version == 4 and not (reproduced and re.fullmatch(r"[0-9a-f]{40}", reproduced)):
        raise ValueError("version 4 needs the full SHA-1 of the reproduced commit")
    promotion = "calibration/v0.4/runs/promotion.json"
    same = []
    if version == 4:
        same = [f"git diff --exit-code {reproduced} {commit} -- {' '.join(SAME_AT_BOTH_COMMITS)}"]
    discover, check = [], []
    for run, key in STAGE2:
        extra = f" --promotion {promotion}" if run == "promoted-s2" else ""
        discover.append(
            f"uv run refute discover calibration/v0.4/claim.yaml --stage 2{extra} "
            f"--target {key} --out repro2/{key} --run-id repro2-{key} --workers 1"
        )
        check.append(
            f"uv run refute check-dossier repro2/{key}/repro2-{key}/{key} "
            f"--against {ORIGINALS_DIR}/{run}/{key}"
        )
    if version == 2:
        intro = [
            "# Reproduce the v0.4 pilot's stage-2 dossiers (instructions version 2)",
            "",
            "These instructions supersede the core's `REPRODUCE.md` of the five stage-2 "
            "dossiers of",
            "the v0.4 pilot. They do not amend acceptance criterion 2 of",
            "`docs/plans/v0.4-acceptance.md`. They exist because the core's `REPRODUCE.md` is",
            "written by the locked `src/refute/core/run.py`: its commands are not self-sufficient",
            "in a fresh clone (#189), and neither the sealed core nor the locked code can change.",
            "The maintainer approved this replacement on 2026-11-01 (Option 1; recorded in #177).",
        ]
        archive_line = [f"- `ARCHIVE`: `{archive}`."]
        network = [
            "- Network: MAST (the TESS data), VizieR (the TESS-EB table), GitHub (a release asset",
            "  and the API, which the promotion check needs to verify R_prom).",
        ]
        limit = [
            "Limit: before P7 the two zips in `ARCHIVE` (the stage-1 verdicts and the original",
            "stage-2 dossiers) are in the maintainer's private archive, so a third party cannot",
            "run these commands until the maintainer deposits them at P7 with the same hashes.",
        ]
    elif version == 3:
        intro = [
            "# Reproduce the v0.4 pilot's stage-2 dossiers (instructions version 3)",
            "",
            "These instructions supersede `REPRODUCE-2.md` (annex `reproduce-2`) of the five",
            "stage-2 dossiers of the v0.4 pilot, whose `ARCHIVE` was the maintainer's private",
            "archive. The commands are those of version 2; only `ARCHIVE` changes, to the public",
            "deposit. Like version 2, they supersede the core's `REPRODUCE.md` (#189) and do not",
            "amend acceptance criterion 2 of `docs/plans/v0.4-acceptance.md`. The maintainer",
            "approved version 3 (P7, item 7; recorded in #177).",
        ]
        archive_line = [f"- `ARCHIVE`: `{archive}`, the files of the record https://doi.org/{doi}."]
        network = [
            "- Network: MAST (the TESS data), VizieR (the TESS-EB table), Zenodo (the two zips),",
            "  GitHub (a release asset and the API, which the promotion check needs to verify",
            "  R_prom).",
        ]
        limit = [
            f"`ARCHIVE` is public: the record https://doi.org/{doi} holds the two zips with the",
            "SHA-256 recorded in `calibration/v0.4/runs/reproduce_archives.json`, and `prepare`",
            "checks them. At the commit above, `prepare` tries the CDS and then the CfA mirror",
            "only for the TESS-EB table; if neither supplies data matching the frozen edition's",
            "checks, it stops.",
        ]
    else:
        servers = ", ".join(HOSTS)
        intro = [
            "# Reproduce the v0.4 pilot's stage-2 dossiers (instructions version 4)",
            "",
            "These instructions supersede `REPRODUCE-3.md` (annex `reproduce-3`) of the five",
            "stage-2 dossiers of the v0.4 pilot. At the commit of version 3, `prepare` asked only",
            "the CDS and the CfA mirror for the TESS-EB table, so it stopped when both were down.",
            "The commit below adds VizieR's mirrors to `prepare`; `ARCHIVE` and the analysis",
            "commands are those of version 3. Like the earlier versions, they supersede the",
            "core's `REPRODUCE.md` (#189) and do not amend acceptance criterion 2 of",
            "`docs/plans/v0.4-acceptance.md`. The maintainer approved version 4 (P7; recorded in",
            "#177).",
        ]
        archive_line = [
            f"- The full reproduction on record (annex `reproduction-2`) ran at `{reproduced}`.",
            "  The `git diff --exit-code` command below checks that the commit to check out has",
            f"  the same {', '.join(f'`{p}`' for p in SAME_AT_BOTH_COMMITS)}.",
            f"- `ARCHIVE`: `{archive}`, the files of the record https://doi.org/{doi}.",
        ]
        network = [
            "- Network: MAST (the TESS data), VizieR (the TESS-EB table), Zenodo (the two zips),",
            "  GitHub (a release asset and the API, which the promotion check needs to verify",
            "  R_prom).",
        ]
        limit = [
            f"`ARCHIVE` is public: the record https://doi.org/{doi} holds the two zips with the",
            "SHA-256 recorded in `calibration/v0.4/runs/reproduce_archives.json`, and `prepare`",
            "checks them. For the TESS-EB table, `prepare` asks these VizieR servers in order:",
            f"{servers}. It takes the table from the first whose answer, with the header's",
            "metadata restored, gives the frozen edition's SHA-256; each server that does not is",
            "refused. When `prepare` finishes, `.cache/v04/reproduce/prepare.json` names the",
            "server used and the servers refused before it. If none matches, it stops, and its",
            "error message lists the refusals in order.",
        ]
    lines = [
        *intro,
        "",
        f"- Commit to check out: `{commit}`. It holds the locked code and claim unchanged",
        "  (`refute verify` gives PASS), and the input tool",
        "  `calibration/v0.4/reproduce_inputs.py`.",
        *archive_line,
        "- `WORK`: the clone's root. Every command below runs there, and `WORK/.cache` must be",
        "  new.",
        *network,
        "- The numerical libraries run single-threaded, as in the pilot's runs.",
        "- Shell: Bash (on Windows, Git Bash). The block stops at the first command that fails",
        "  (`set -euo pipefail`); a failed step is never followed by the next.",
        "",
        "```bash",
        "set -euo pipefail",
        "git clone https://github.com/klucilla/refute.git WORK",
        "cd WORK",
        f"git checkout {commit}",
        *same,
        "export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1",
        "uv sync --frozen",
        "uv run refute verify calibration/v0.4/claim.yaml",
        f'uv run python calibration/v0.4/reproduce_inputs.py prepare --archive "{archive}"',
        *discover,
        *check,
        "```",
        "",
        "`reproduce_inputs.py prepare` fetches every input a clone lacks and checks each one",
        "against a SHA-256 recorded before the reproduction (see its docstring). Any difference",
        "stops it; nothing is adjusted to make a hash match. `check-dossier --against` verifies",
        "both dossiers and requires identical input data hashes, identical verdict and test",
        "statuses, and key numeric results equal within a relative tolerance of 1e-6.",
        "",
        *limit,
        "",
    ]
    return LF.join(lines)


def cmd_instructions(
    commit: str,
    archive: str,
    out: Path,
    version: int = 2,
    doi: str | None = None,
    reproduced: str | None = None,
) -> int:
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        print("the commit must be a full SHA-1")
        return 1
    if out.exists():
        print(f"{out} exists")
        return 1
    try:
        text = instructions(commit, archive, version, doi, reproduced)
    except ValueError as exc:
        print(exc)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "x", encoding="utf-8", newline=LF) as handle:
        handle.write(text)
    print(f"written: {out}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="step", required=True)
    build = sub.add_parser("build-archives")
    build.add_argument("--out", required=True, type=Path)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--archive", required=True)
    text = sub.add_parser("instructions")
    text.add_argument("--commit", required=True)
    text.add_argument("--archive", required=True)
    text.add_argument("--out", required=True, type=Path)
    text.add_argument("--version", type=int, choices=(2, 3, 4), default=2)
    text.add_argument("--doi")
    text.add_argument("--reproduced")
    args = parser.parse_args(argv)
    if args.step == "build-archives":
        return cmd_build_archives(args.out)
    if args.step == "prepare":
        return cmd_prepare(args.archive)
    return cmd_instructions(
        args.commit, args.archive, args.out, args.version, args.doi, args.reproduced
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
