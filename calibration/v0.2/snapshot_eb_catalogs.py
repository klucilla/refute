"""Snapshot the eclipsing-binary catalogs for the v0.2 eb_catalog test (needs network).

Run once, from the repository root, before the v0.2 protocol is committed:

    uv run python calibration/v0.2/snapshot_eb_catalogs.py

Sources (both authoritative, both independent of the ExoFOP TOI dispositions used
to select known false positives, although they may share underlying information;
see the protocol):

- TESS Eclipsing Binary catalog, Prsa et al. 2022, ApJS 258, 16, VizieR table
  J/ApJS/258/16/tess-ebs (TIC, coordinates J2000, orbital period in days). NOT
  redistributed (maintainer's decision; terms differ between the publisher and the
  CDS, see eb_snapshot/DATA_LICENSE.md): the file stays in .cache/eb_snapshot_v02/
  and only its URL, retrieval time and hashes are committed. VizieR writes the query
  date in comment lines, so the raw SHA-256 changes at every download; the content
  SHA-256 (comment lines removed, LF endings; refute.packs.tess.ebcatalog.vizier_content)
  is the one checked on reproduction.
- Gaia DR3 eclipsing-binary candidates, table gaiadr3.vari_eclipsing_binary joined
  with gaiadr3.gaia_source for coordinates (ICRS, epoch J2016.0), from the ESA Gaia
  archive TAP service. Only the four columns the eb_catalog test uses are requested:
  source_id, ra, dec, frequency (d**-1, checked in TAP_SCHEMA.columns; the period
  is 1/frequency).

  A single job for the whole table (about 2.2 million rows) failed on 2026-10-08 with
  a server-side error while recording the anonymous user's file quota. The table is
  therefore downloaded in PARTS: equal ranges of source_id, one asynchronous job at
  a time (never in parallel), each job deleted on the server after its result is
  downloaded so the anonymous quota is freed. The parts are joined in ascending
  source_id order (deterministic), and the total must equal the table's COUNT(*)
  exactly, or the script stops. The joined file is kept in .cache/eb_snapshot_v02/
  (git-ignored, published later as a release asset); its SHA-256 and the ADQL, job,
  times, rows and SHA-256 of every part are committed in eb_snapshot/.

Authentication: two anonymous attempts failed on 2026-10-08 with the archive's
anonymous file-quota error, so the Gaia parts are downloaded with the maintainer's
registered Gaia archive account (same source, same queries). The maintainer runs:

    uv run --frozen python -u calibration/v0.2/snapshot_eb_catalogs.py \
        --credentials <path to an INI file outside the repository>

The INI file has a [gaia] section with ``username`` and ``password``. The password
is read only to log in (POST https://gea.esac.esa.int/tap-server/login, the
archive's session login, as used by astroquery) and is never printed, logged,
stored elsewhere or put in an error message. The session is closed at the end
(POST .../tap-server/logout).

Progress (no secrets) is printed and also appended to .cache/eb_snapshot_v02/snapshot.log.

Outputs: .cache/eb_snapshot_v02/tess_ebs_prsa2022.tsv (not committed),
eb_snapshot/gaia_parts.json (written after every part) and eb_snapshot/retrieval.json
(index of both catalogs). ``--tess-only`` re-downloads TESS-EB and rewrites only its
entry of the index. Nothing is ever submitted.
"""

from __future__ import annotations

import configparser
import hashlib
import http.cookiejar
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SNAPSHOT_DIR = HERE / "eb_snapshot"
CACHE_DIR = ROOT / ".cache" / "eb_snapshot_v02"
USER_AGENT = "refute-calibration/0.2"

TESS_EB_URL = (
    "https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJS/258/16/tess-ebs"
    "&-out=TIC,m_TIC,RAJ2000,DEJ2000,Per&-out.max=unlimited"
)
GAIA_SERVER = "https://gea.esac.esa.int/tap-server"
GAIA_TAP = f"{GAIA_SERVER}/tap"
GAIA_COUNT_QUERY = "SELECT COUNT(*) AS n FROM gaiadr3.vari_eclipsing_binary"
GAIA_EXPECTED_ROWS = 2184477  # COUNT(*) on 2026-10-08; checked again at run time
GAIA_HEADER = "source_id,ra,dec,frequency"
# Gaia DR3 source_id = HEALPix level-12 index * 2**35 + ...: every source_id is
# below 12 * 4**12 * 2**35.
SOURCE_ID_MAX = 12 * 4**12 * 2**35
N_PARTS = 20


def gaia_part_query(lo: int, hi: int) -> str:
    return (
        "SELECT eb.source_id, gs.ra, gs.dec, eb.frequency "
        "FROM gaiadr3.vari_eclipsing_binary AS eb "
        "JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id "
        f"WHERE eb.source_id >= {lo} AND eb.source_id < {hi} "
        "ORDER BY eb.source_id"
    )


def part_bounds() -> list[tuple[int, int]]:
    edges = [SOURCE_ID_MAX * i // N_PARTS for i in range(N_PARTS + 1)]
    return list(zip(edges[:-1], edges[1:], strict=True))


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


# One opener with a cookie jar: after login, every request carries the session cookie.
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
SESSION = {"user": None}
LOG_LOCK = threading.Lock()


def log(message: str) -> None:
    """Print and append to the progress log. Never called with a secret."""
    line = f"{utc_now()} {message}"
    with LOG_LOCK:
        print(line, flush=True)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with (CACHE_DIR / "snapshot.log").open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def request(
    url: str, data: dict | None = None, timeout: int = 600, method: str | None = None
) -> tuple[bytes, str]:
    body = urllib.parse.urlencode(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers={"User-Agent": USER_AGENT}, method=method)
    with OPENER.open(req, timeout=timeout) as response:  # noqa: S310 - fixed URLs
        return response.read(), response.geturl()


def gaia_login(credentials: Path) -> None:
    """Log in to the Gaia archive. The password never leaves this function."""
    config = configparser.ConfigParser(interpolation=None)
    if not config.read(credentials, encoding="utf-8") or not config.has_section("gaia"):
        raise SystemExit(f"credentials file not found or without a [gaia] section: {credentials}")
    username = config.get("gaia", "username", fallback="").strip()
    password = config.get("gaia", "password", fallback="")
    if not username or not password:
        raise SystemExit("credentials file: username or password is empty")
    body = urllib.parse.urlencode({"username": username, "password": password}).encode()
    del password
    req = urllib.request.Request(
        f"{GAIA_SERVER}/login", data=body, headers={"User-Agent": USER_AGENT}, method="POST"
    )
    try:
        with OPENER.open(req, timeout=120) as response:  # noqa: S310 - fixed URL
            status = response.status
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Gaia login failed for user {username}: HTTP {exc.code}") from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"Gaia login failed: cannot reach the archive ({exc.reason})") from None
    finally:
        del body
    SESSION["user"] = username
    log(f"logged in to the Gaia archive as {username} (HTTP {status})")


def gaia_logout() -> None:
    if SESSION["user"] is None:
        return
    SESSION["user"] = None  # idempotent: called on interruption and at the end
    try:
        request(f"{GAIA_SERVER}/logout", {}, timeout=60, method="POST")
        log("logged out")
    except Exception:  # noqa: BLE001 - logout failure is harmless
        log("logout failed (the session will expire)")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def snapshot_tess_eb() -> dict:
    from refute.packs.tess.ebcatalog import content_sha256, parse_tess_eb

    retrieved = utc_now()
    data, _ = request(TESS_EB_URL)
    rows = len(parse_tess_eb(data))
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / "tess_ebs_prsa2022.tsv"
    path.write_bytes(data)
    return {
        "catalog_name": "TESS-EB",
        "catalog": "TESS-EB (Prsa et al. 2022, ApJS 258, 16; VizieR J/ApJS/258/16/tess-ebs)",
        "file": path.relative_to(ROOT).as_posix(),
        "cache_path": path.relative_to(ROOT / ".cache").as_posix(),
        "url": TESS_EB_URL,
        "retrieved_utc": retrieved,
        "bytes": len(data),
        "rows": rows,
        "sha256": sha256(data),
        "content_sha256": content_sha256(data),
        "content_rule": "non-empty lines not starting with '#', LF endings, final LF",
        "parser": "tess-eb-vizier-tsv",
        "redistributed": False,
    }


def gaia_count() -> int:
    data, _ = request(
        f"{GAIA_TAP}/sync",
        {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": GAIA_COUNT_QUERY},
    )
    return int(data.decode().splitlines()[1])


PARALLEL_JOBS = 2  # approved by the maintainer (2026-10-08) after a 57-minute part
STOP = threading.Event()
ACTIVE_JOBS: set[str] = set()
LOCK = threading.Lock()
RUN_STARTED = utc_now()


class RunInterruptedError(Exception):
    """The run was interrupted (Ctrl+C); completed parts are kept."""


def delete_job(job_url: str) -> bool:
    """UWS: POST ACTION=DELETE. Frees the quota and cancels a job that is still running."""
    try:
        request(job_url, {"ACTION": "DELETE"}, timeout=60)
        return True
    except Exception:  # noqa: BLE001 - recorded, not fatal
        return False


def run_gaia_job(query: str, label: str) -> tuple[bytes, dict]:
    """One asynchronous job: submit, wait, download, then delete it on the server."""
    params = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "PHASE": "RUN"}
    submitted = utc_now()
    _, job_url = request(f"{GAIA_TAP}/async", {**params, "QUERY": query})
    with LOCK:
        ACTIVE_JOBS.add(job_url)
    log(f"  {label} job {job_url}")
    try:
        for _ in range(1440):
            if STOP.is_set():
                raise RunInterruptedError(label)
            phase = request(f"{job_url}/phase", timeout=60)[0].decode().strip()
            if phase == "COMPLETED":
                break
            if phase in {"ERROR", "ABORTED"}:
                error = request(f"{job_url}/error", timeout=60)[0].decode(errors="replace")
                raise SplittableJobError(
                    f"Gaia job {job_url} ended with phase {phase}: {error[:800]}"
                )
            for _ in range(10):  # 10 s between polls, checking for an interruption
                if STOP.is_set():
                    raise RunInterruptedError(label)
                time.sleep(1)
        else:
            raise SplittableJobError(f"Gaia job {job_url} did not finish in 4 hours")
        completed = utc_now()
        data, _ = request(f"{job_url}/results/result", timeout=3600)
        downloaded = utc_now()
    except urllib.error.HTTPError as exc:
        if exc.code >= 500:
            raise SplittableJobError(f"Gaia job {job_url}: server error HTTP {exc.code}") from exc
        raise
    finally:
        deleted = delete_job(job_url)
        with LOCK:
            ACTIVE_JOBS.discard(job_url)
    return data, {
        "job": job_url,
        "submitted_utc": submitted,
        "completed_utc": completed,
        "downloaded_utc": downloaded,
        "job_deleted_after_download": deleted,
    }


MAX_SPLIT_DEPTH = 4  # a part may be halved up to 4 times (1/16 of a part)


class SplittableJobError(RuntimeError):
    """A job failed on the server (time limit or server error): its range may be halved."""


def _part_rows(data: bytes, label: str, lo: int, hi: int) -> list[str]:
    text = data.decode("utf-8").replace("\r\n", "\n")
    lines = [ln for ln in text.split("\n") if ln]
    if not lines or lines[0] != GAIA_HEADER:
        raise RuntimeError(f"part {label}: unexpected header {lines[:1]}")
    for line in lines[1:]:
        source_id = int(line.split(",", 1)[0])
        if not lo <= source_id < hi:
            raise RuntimeError(f"part {label}: row outside its source_id range: {line}")
    return lines[1:]


def _label(record: dict) -> str:
    part = record["part"]
    return f"{part:02d}" if isinstance(part, int) else str(part)


def _part_path(label: str) -> Path:
    return CACHE_DIR / "parts" / f"part_{label}.csv"


def _save_parts(records: dict[tuple[int, int], dict]) -> None:
    ordered = [records[k] for k in sorted(records)]
    (SNAPSHOT_DIR / "gaia_parts.json").write_bytes(
        (json.dumps(ordered, indent=2) + "\n").encode("utf-8")
    )


def _save_splits(splits: dict[str, dict]) -> None:
    ordered = [
        splits[k] for k in sorted(splits, key=lambda k: splits[k]["source_id_min_inclusive"])
    ]
    (SNAPSHOT_DIR / "gaia_splits.json").write_bytes(
        (json.dumps(ordered, indent=2) + "\n").encode("utf-8")
    )


def _download_part(label: str, lo: int, hi: int) -> dict:
    query = gaia_part_query(lo, hi)
    name = f"part {label}"
    log(f"{name}: source_id in [{lo}, {hi})")
    data, job = run_gaia_job(query, name)
    rows = _part_rows(data, label, lo, hi)
    _part_path(label).write_bytes(data)
    log(f"  {name}: {len(rows)} rows, sha256 {sha256(data)}")
    return {
        "part": label,
        "source_id_min_inclusive": lo,
        "source_id_max_exclusive": hi,
        "adql": query,
        **job,
        "rows": len(rows),
        "bytes": len(data),
        "sha256": sha256(data),
        "authenticated_as": SESSION["user"],
        "run_started_utc": RUN_STARTED,
    }


def _reusable(record: dict | None, lo: int, hi: int) -> bool:
    if not record:
        return False
    path = _part_path(_label(record))
    return (
        path.is_file()
        and record.get("source_id_min_inclusive") == lo
        and record.get("source_id_max_exclusive") == hi
        and record.get("adql") == gaia_part_query(lo, hi)
        and sha256(path.read_bytes()) == record.get("sha256")
    )


def _recover_from_log() -> dict[tuple[int, int], dict]:
    """Records of parts that were downloaded but never written to gaia_parts.json.

    The previous version of this script stopped recording parts after the first
    failed part, while the parts already queued kept downloading. Their files and
    the log lines that announced them remain. A part is recovered only if the log
    has its range, its job URL and a completion line, and the file's row count and
    SHA-256 equal the logged ones; the record says it was recovered from the log.
    """
    log_path = CACHE_DIR / "snapshot.log"
    if not log_path.is_file():
        return {}
    start_re = re.compile(r"^(\S+) part (\d+(?:-\d+)*)(?:/\d+)?: source_id in \[(\d+), (\d+)\)$")
    job_re = re.compile(r"^(\S+)\s+part (\d+(?:-\d+)*)(?:/\d+)? job (\S+)$")
    done_re = re.compile(
        r"^(\S+)\s+part (\d+(?:-\d+)*)(?:/\d+)?: (\d+) rows, sha256 ([0-9a-f]{64})$"
    )
    login_re = re.compile(r"^(\S+) logged in to the Gaia archive as (\S+) ")
    starts, jobs, done = {}, {}, {}
    user, login_time = None, None
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if m := login_re.match(line):
            login_time, user = m.group(1), m.group(2)
        elif m := start_re.match(line):
            starts[m.group(2)] = (m.group(1), int(m.group(3)), int(m.group(4)))
        elif m := job_re.match(line):
            jobs[m.group(2)] = m.group(3)
        elif m := done_re.match(line):
            done[m.group(2)] = (m.group(1), int(m.group(3)), m.group(4), user, login_time)
    recovered = {}
    for raw_label, (finished, rows, digest, who, run_started) in done.items():
        if raw_label not in starts or raw_label not in jobs:
            continue
        label = f"{int(raw_label):02d}" if raw_label.isdigit() else raw_label
        submitted, lo, hi = starts[raw_label]
        path = _part_path(label)
        if not path.is_file():
            continue
        data = path.read_bytes()
        if sha256(data) != digest or len(_part_rows(data, label, lo, hi)) != rows:
            continue
        recovered[(lo, hi)] = {
            "part": int(raw_label) if raw_label.isdigit() else raw_label,
            "source_id_min_inclusive": lo,
            "source_id_max_exclusive": hi,
            "adql": gaia_part_query(lo, hi),
            "job": jobs[raw_label],
            "submitted_utc": submitted,
            "completed_utc": None,
            "downloaded_utc": finished,
            "job_deleted_after_download": None,
            "rows": rows,
            "bytes": len(data),
            "sha256": digest,
            "authenticated_as": who,
            "run_started_utc": run_started,
            "recovered_from_log": True,
        }
    return recovered


def _halves(label: str, lo: int, hi: int) -> list[tuple[str, int, int]]:
    mid = lo + (hi - lo) // 2
    return [(f"{label}-1", lo, mid), (f"{label}-2", mid, hi)]


def snapshot_gaia() -> dict:
    """Download every part (resuming, 2 at a time, halving a range that fails on the server)."""
    expected = gaia_count()
    if expected != GAIA_EXPECTED_ROWS:
        raise RuntimeError(f"Gaia COUNT(*) is {expected}, expected {GAIA_EXPECTED_ROWS}")
    (CACHE_DIR / "parts").mkdir(parents=True, exist_ok=True)
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    parts_file, splits_file = SNAPSHOT_DIR / "gaia_parts.json", SNAPSHOT_DIR / "gaia_splits.json"
    previous: dict[tuple[int, int], dict] = {}
    if parts_file.is_file():
        for r in json.loads(parts_file.read_text(encoding="utf-8")):
            previous[(r["source_id_min_inclusive"], r["source_id_max_exclusive"])] = r
    for key, record in _recover_from_log().items():
        if key not in previous:
            previous[key] = record
            log(
                f"part {_label(record)}: record recovered from snapshot.log (file, rows and "
                "SHA-256 match the logged completion)"
            )
    splits: dict[str, dict] = {}
    if splits_file.is_file():
        splits = {s["part"]: s for s in json.loads(splits_file.read_text(encoding="utf-8"))}

    records: dict[tuple[int, int], dict] = {}
    todo: list[tuple[str, int, int]] = []
    queue = [(f"{i:02d}", lo, hi) for i, (lo, hi) in enumerate(part_bounds(), start=1)]
    while queue:  # resolve the plan: reuse, follow recorded splits, or download
        label, lo, hi = queue.pop(0)
        if _reusable(previous.get((lo, hi)), lo, hi):
            records[(lo, hi)] = previous[(lo, hi)]
            log(f"part {label}: reused (file and SHA-256 match)")
        elif label in splits:
            queue[0:0] = _halves(label, lo, hi)
        else:
            todo.append((label, lo, hi))
    _save_parts(records)
    log(f"{len(todo)} part(s) to download, {PARALLEL_JOBS} at a time")

    with ThreadPoolExecutor(max_workers=PARALLEL_JOBS) as pool:
        waiting = list(todo)
        running: dict = {}
        while waiting or running:
            while waiting and len(running) < PARALLEL_JOBS:
                item = waiting.pop(0)
                running[pool.submit(_download_part, *item)] = item
            done, _ = wait(set(running), timeout=1.0, return_when=FIRST_COMPLETED)
            for future in done:
                label, lo, hi = running.pop(future)
                try:
                    record = future.result()
                except SplittableJobError as exc:
                    depth = label.count("-")
                    if depth >= MAX_SPLIT_DEPTH:
                        raise RuntimeError(
                            f"part {label} still fails after {depth} halvings: STOP ({exc})"
                        ) from exc
                    children = _halves(label, lo, hi)
                    with LOCK:
                        splits[label] = {
                            "part": label,
                            "source_id_min_inclusive": lo,
                            "source_id_max_exclusive": hi,
                            "failed_utc": utc_now(),
                            "error": str(exc)[:600],
                            "children": [
                                {
                                    "part": c[0],
                                    "source_id_min_inclusive": c[1],
                                    "source_id_max_exclusive": c[2],
                                }
                                for c in children
                            ],
                        }
                        _save_splits(splits)
                    log(
                        f"part {label} failed on the server; halving it into {children[0][0]} "
                        f"and {children[1][0]}"
                    )
                    waiting[0:0] = children
                    continue
                with LOCK:
                    records[(lo, hi)] = record
                    _save_parts(records)

    ranges = sorted(records)
    edge = 0
    for lo, hi in ranges:  # the ranges must tile [0, SOURCE_ID_MAX) exactly
        if lo != edge:
            raise RuntimeError(f"source_id ranges do not tile: gap or overlap at {edge}: STOP")
        edge = hi
    if edge != SOURCE_ID_MAX:
        raise RuntimeError("source_id ranges do not reach the end of the range: STOP")
    rows_by_id: dict[int, str] = {}
    for lo, hi in ranges:
        record = records[(lo, hi)]
        label = _label(record)
        data = _part_path(label).read_bytes()
        if sha256(data) != record["sha256"]:
            raise RuntimeError(f"part {label}: file does not match its recorded SHA-256: STOP")
        for line in _part_rows(data, label, lo, hi):
            source_id = int(line.split(",", 1)[0])
            if source_id in rows_by_id:
                raise RuntimeError(f"part {label}: repeated source_id {source_id}: STOP")
            rows_by_id[source_id] = line
    total = len(rows_by_id)
    if total != expected:
        raise RuntimeError(f"joined parts have {total} rows, the table has {expected}: STOP")
    joined = GAIA_HEADER + "\n" + "\n".join(rows_by_id[k] for k in sorted(rows_by_id)) + "\n"
    data = joined.encode("utf-8")
    path = CACHE_DIR / "gaia_dr3_vari_eclipsing_binary.csv"
    path.write_bytes(data)
    return {
        "catalog_name": "Gaia-DR3-EB",
        "file": path.relative_to(ROOT).as_posix(),
        "catalog": "Gaia DR3 eclipsing-binary candidates (gaiadr3.vari_eclipsing_binary)",
        "redistributed": True,
        "url": f"{GAIA_TAP}/async",
        "retrieved_utc": max(r["downloaded_utc"] for r in records.values()),
        "bytes": len(data),
        "rows": total,
        "sha256": sha256(data),
        "count_query": GAIA_COUNT_QUERY,
        "count": expected,
        "parts": "eb_snapshot/gaia_parts.json",
        "splits": "eb_snapshot/gaia_splits.json",
        "join": "rows of all parts, sorted by ascending source_id, LF line endings, one header",
        "units": {"ra": "deg (ICRS, epoch J2016.0)", "dec": "deg", "frequency": "d**-1"},
        "note": "Too large for git; to be published as a release asset with this SHA-256.",
    }


def main() -> int:
    log(
        "Do not press Ctrl+C: it stops the download. To copy text from this window, "
        "select it with the mouse."
    )
    args = sys.argv[1:]
    if "--credentials" in args:
        position = args.index("--credentials")
        if position + 1 >= len(args):
            raise SystemExit("--credentials needs a path")
        gaia_login(Path(args[position + 1]))
    try:
        for position, arg in enumerate(args):
            if arg == "--delete-job" and position + 1 < len(args):
                job = f"{GAIA_TAP}/async/{args[position + 1]}"
                log(f"delete job {job}: {'done' if delete_job(job) else 'failed'}")
        return run(args)
    except KeyboardInterrupt:
        STOP.set()
        log(
            "Interrupted (Ctrl+C). Completed parts are kept and will be reused on the next "
            "run; jobs in progress are being cancelled."
        )
        with LOCK:
            active = sorted(ACTIVE_JOBS)
        for job in active:
            log(f"cancel job {job}: {'done' if delete_job(job) else 'failed'}")
        gaia_logout()
        os._exit(130)  # do not wait for worker threads blocked on the network
    finally:
        gaia_logout()


def run(args: list[str]) -> int:
    if "--tess-only" in args:
        index = json.loads((SNAPSHOT_DIR / "retrieval.json").read_text(encoding="utf-8"))
        tess = snapshot_tess_eb()
        others = [s for s in index if not s["catalog"].startswith("TESS-EB")]
        (SNAPSHOT_DIR / "retrieval.json").write_bytes(
            (json.dumps([tess, *others], indent=2) + "\n").encode("utf-8")
        )
        log(f"TESS-EB: {tess['rows']} rows, content sha256 {tess['content_sha256']}")
        return 0
    tess = snapshot_tess_eb()
    log(f"TESS-EB: {tess['rows']} rows, sha256 {tess['sha256']}")
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    (SNAPSHOT_DIR / "retrieval.json").write_bytes(
        (json.dumps([tess], indent=2) + "\n").encode("utf-8")
    )
    gaia = snapshot_gaia()
    gaia["authenticated_as"] = SESSION["user"]
    (SNAPSHOT_DIR / "retrieval.json").write_bytes(
        (json.dumps([tess, gaia], indent=2) + "\n").encode("utf-8")
    )
    log(f"Gaia DR3 EB: {gaia['rows']} rows, sha256 {gaia['sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
