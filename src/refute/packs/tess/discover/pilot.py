"""The steps of the v0.4 pilot that touch the network (protocol sections 4.0 and 4.2 to 4.4):
freezing the frame and the catalogs before the selection round, and the live per-star queries
of the walk. ``calibration/v0.4/select.py`` calls these; every value comes from ``protocol.py``.

Frozen inputs (before the protocol commit): the target lists page and the all-targets lists of
sectors 1 to ``S_max``, the frame built from them, the TOI, CTOI and ``pscomppars`` tables, the
TESS-EB table and the Gaia DR3 EB snapshot of v0.2 (a release asset of v0.2.0, checked against
its recorded SHA-256). Each file's URL, retrieval time, size and SHA-256 go into
``inputs.json``; a file above 5 MB is never committed (#172).
"""

from __future__ import annotations

import hashlib
import json
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from refute.drand import shuffled
from refute.packs.tess.discover import selection as sel
from refute.packs.tess.discover.protocol import CONTROLS, DOMAIN, SELECTION
from refute.packs.tess.discover.transforms import stream_seed

TARGET_LISTS_PAGE = "https://tess.mit.edu/public/target_lists/target_lists.html"
TOI_URL = "https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv"
CTOI_URL = "https://exofop.ipac.caltech.edu/tess/download_ctoi.php?sort=ctoi&output=csv"
PSCOMPPARS_QUERY = (
    "select pl_name,hostname,tic_id,tran_flag,sy_pnum,pl_orbper,pl_orbpererr1,pl_tranmid,"
    "pl_trandep,pl_trandur,sy_tmag,ra,dec from pscomppars"
)
NEA_TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
TESS_EB_URL = (
    "https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJS/258/16/tess-ebs"
    "&-out=TIC,m_TIC,RAJ2000,DEJ2000,Per&-out.max=unlimited"
)
GAIA_EB_URL = (
    "https://github.com/klucilla/refute/releases/download/v0.2.0/gaia_dr3_vari_eclipsing_binary.csv"
)
GAIA_EB_SHA256 = "5183528b8984d16b305b1fb3ce62b96cf7160961f9a59b0cbb85497e5454c3df"
GIT_LIMIT_BYTES = 5 * 1000**2
USER_AGENT = "refute-discover/0.4"


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def download(url: str, timeout: float = 600.0) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed URLs
        return response.read()


def in_git(name: str, size: int) -> bool:
    """Whether a frozen input is committed: at most 5 MB (#172), and neither a per-sector
    target list nor the frame (about a hundred files that git would carry for nothing: the
    frame is rebuilt from the lists, and both are archived with their hashes)."""
    return size <= GIT_LIMIT_BYTES and not name.startswith("lists/") and name != "frame.csv"


def record(name: str, url: str, data: bytes, retrieved: str) -> dict[str, Any]:
    return {
        "name": name,
        "url": url,
        "retrieved_utc": retrieved,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "in_git": in_git(name, len(data)),
    }


def freeze(
    out_dir: Path,
    s_max: int | None = None,
    fetch: Callable[[str], bytes] = download,
    now: Callable[[], str] = utc_now,
    sector_count: Callable[[int], int] | None = None,
) -> dict[str, Any]:
    """Download every frozen input once into ``out_dir`` and write ``inputs.json``. Without
    ``s_max`` it is found from MAST (``latest_spoc_sector``), below the highest sector on the
    page. The Gaia EB snapshot must have its recorded SHA-256, or the freeze stops."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []

    def keep(name: str, url: str, data: bytes) -> bytes:
        (out_dir / name).write_bytes(data)
        records.append(record(name, url, data, now()))
        return data

    page = keep("target_lists.html", TARGET_LISTS_PAGE, fetch(TARGET_LISTS_PAGE)).decode("utf-8")
    s_max_record = {"s_max": s_max, "queries": [], "given": s_max is not None}
    if s_max is None:
        s_max_record = latest_spoc_sector(
            highest_listed_sector(page), sector_count or spoc_sector_count
        )
        s_max = s_max_record["s_max"]
    lists = {}
    for sector, url in sel.list_urls(page, s_max).items():
        lists[sector] = keep(f"lists/{Path(url).name}", url, _mkdir_fetch(out_dir, url, fetch))
        lists[sector] = lists[sector].decode("utf-8")
    frame = sel.build_frame(lists)
    keep(
        "frame.csv",
        "derived: refute.packs.tess.discover.selection.build_frame",
        sel.frame_csv(frame),
    )
    keep("toi.csv", TOI_URL, fetch(TOI_URL))
    keep("ctoi.csv", CTOI_URL, fetch(CTOI_URL))
    nea = f"{NEA_TAP}?{urllib.parse.urlencode({'query': PSCOMPPARS_QUERY, 'format': 'csv'})}"
    keep("pscomppars.csv", nea, fetch(nea))
    keep("tess_eb.tsv", TESS_EB_URL, fetch(TESS_EB_URL))
    gaia = fetch(GAIA_EB_URL)
    if hashlib.sha256(gaia).hexdigest() != GAIA_EB_SHA256:
        raise sel.SelectionError("the Gaia DR3 EB asset does not match its recorded SHA-256")
    keep("gaia_dr3_eb.csv", GAIA_EB_URL, gaia)
    inputs = {
        "schema": "refute-tess-discover-inputs-1",
        "s_max": s_max,
        "s_max_record": s_max_record,
        "frame_stars": len(frame),
        "files": records,
        "total_bytes": sum(r["bytes"] for r in records),
    }
    (out_dir / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n", encoding="utf-8")
    return inputs


def _mkdir_fetch(out_dir: Path, url: str, fetch: Callable[[str], bytes]) -> bytes:
    (out_dir / "lists").mkdir(parents=True, exist_ok=True)
    return fetch(url)


def verify_inputs(out_dir: Path, inputs: dict[str, Any]) -> None:
    """Every frozen file still has its recorded SHA-256, or the selection stops."""
    for item in inputs["files"]:
        data = (Path(out_dir) / item["name"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise sel.SelectionError(f"{item['name']} does not match its recorded SHA-256")


def spoc_sector_count(sector: int) -> int:
    """How many SPOC 120-s light-curve observations MAST lists for a sector (network)."""
    from astroquery.mast import Observations

    return int(
        sel.transient(
            lambda: Observations.query_criteria_count(
                obs_collection="TESS",
                provenance_name="SPOC",
                dataproduct_type="timeseries",
                t_exptime=120,
                sequence_number=int(sector),
            ),
            f"MAST sector {sector}",
        )
    )


def latest_spoc_sector(
    highest_listed: int, count: Callable[[int], int] = spoc_sector_count
) -> dict:
    """S_max: the highest sector, at or below the highest sector on the target lists page, for
    which MAST lists SPOC 120-s light curves (protocol section 3, D-9). Every query is kept."""
    queries = []
    for sector in range(highest_listed, 0, -1):
        n = count(sector)
        queries.append({"sector": sector, "spoc_120s_light_curves": n, "utc": utc_now()})
        if n > 0:
            return {"s_max": sector, "queries": queries}
    raise sel.SelectionError("MAST lists no SPOC 120-s light curve for any sector")


def highest_listed_sector(page_html: str) -> int:
    return max(int(s) for _name, s, _v in sel.TARGET_LIST_LINK.findall(page_html))


# --- live per-star queries (the walk) --------------------------------------------------------


def tic_fields(tic_id: int) -> dict[str, float | None]:
    """The TIC fields of the domain (network). A missing column stops the selection: the
    protocol cannot be applied as written without it."""
    from astroquery.mast import Catalogs

    table = sel.transient(
        lambda: Catalogs.query_criteria(catalog="Tic", ID=int(tic_id)), f"TIC {tic_id}"
    )
    if len(table) == 0:
        return {f: None for f in sel.TIC_FIELDS}
    missing = [f for f in sel.TIC_FIELDS if f not in table.colnames]
    if missing:
        raise sel.SelectionError("the TIC table lacks the column(s): " + ", ".join(missing))
    row = table[0]
    return {f: sel._float(str(row[f])) for f in sel.TIC_FIELDS}


def listing(tic_id: int) -> sel.Listing:
    """What MAST lists for the star: SPOC 120-s light curves and target pixel files (network)."""
    import re

    import lightkurve as lk

    query = {"mission": "TESS", "author": "SPOC", "exptime": 120}

    def rows(search):
        table = search.table
        out = []
        for i in range(len(table)):
            if str(table["target_name"][i]).strip() != str(tic_id):
                continue
            match = re.search(r"Sector (\d+)", str(table["mission"][i]))
            if match:
                out.append((int(match.group(1)), float(table["t_min"][i])))
        return tuple(sorted(out))

    lcs = sel.transient(lambda: lk.search_lightcurve(f"TIC {tic_id}", **query), f"MAST {tic_id}")
    tpfs = sel.transient(
        lambda: lk.search_targetpixelfile(f"TIC {tic_id}", **query), f"MAST {tic_id}"
    )
    return sel.Listing(rows(lcs), rows(tpfs))


def up_to(found: sel.Listing, s_max: int) -> sel.Listing:
    """Only the products of sectors up to S_max (protocol D-9)."""
    return sel.Listing(
        tuple(r for r in found.light_curves if r[0] <= s_max),
        tuple(r for r in found.pixel_files if r[0] <= s_max),
    )


def triage(
    tic_id: int, domain: Any = DOMAIN, s_max: int | None = None
) -> tuple[bool, str, dict[str, Any]]:
    """The domain of one star from live queries (each answer kept in the evidence); only the
    products of sectors up to S_max count."""
    if s_max is None:
        raise sel.SelectionError("the triage needs S_max")
    fields = tic_fields(tic_id)
    found = listing(tic_id)
    ok, reason, evidence = sel.domain_check(fields, up_to(found, s_max), domain)
    evidence["listed_sectors_after_s_max"] = sorted({s for s, _ in found.light_curves if s > s_max})
    evidence["retrieved_utc"] = utc_now()
    return ok, reason, evidence


# --- the draws -------------------------------------------------------------------------------


def funnel_order(kept: list[sel.FrameStar], randomness_hex: str) -> list[int]:
    """Sort by TIC ID, then shuffle with ``int(randomness, 16)`` (protocol section 4.2)."""
    return shuffled([s.tic_id for s in kept], int(randomness_hex, 16), key=lambda tic: tic)


def pool_order(pool: list[sel.PoolRow], randomness_hex: str, label: str) -> list[int]:
    """A control pool's order: ``int(sha256(randomness_hex + "|v0.4|<label>"), 16)``, with
    ``label`` ``planet-pool`` or ``fp-pool`` (protocol section 8)."""
    seed = stream_seed(randomness_hex, "v0.4", label)
    return shuffled([p.tic_id for p in pool], seed, key=lambda tic: tic)


CI_WORKFLOW = "ci.yml"
REPOSITORY = "klucilla/refute"


def push_run_created_at(commit: str, fetch: Callable[[str], bytes] = download) -> str:
    """The creation time of "the CI push run" of ``commit``: the run of workflow ``ci.yml`` with
    event ``push``, ``head_sha`` equal to the commit and ``run_attempt`` 1 (protocol section
    8). No such run, or more than one, stops the step for the maintainer."""
    url = (
        f"https://api.github.com/repos/{REPOSITORY}/actions/workflows/{CI_WORKFLOW}/runs?"
        + urllib.parse.urlencode({"event": "push", "head_sha": commit, "per_page": 100})
    )
    runs = json.loads(fetch(url))["workflow_runs"]
    first = [r for r in runs if r.get("head_sha") == commit and r.get("run_attempt") == 1]
    if len(first) != 1:
        raise sel.SelectionError(
            f"{len(first)} first-attempt CI push runs for {commit}; the maintainer decides"
        )
    return str(first[0]["created_at"])


def control_domain(step: int):
    """The domain of the control walks at ladder step 0, 1 or 2 (protocol section 4.3)."""
    from dataclasses import replace

    if step == 0:
        return DOMAIN
    return replace(DOMAIN, tmag_max=CONTROLS.ladder_tmag_max)


def _read(inputs_dir: Path, name: str) -> bytes:
    return (Path(inputs_dir) / name).read_bytes()


def run_selection(
    inputs_dir: Path,
    inputs: dict[str, Any],
    randomness_hex: str,
    root: Path,
    triage_fn: Callable[[int, Any, int], tuple[bool, str, dict[str, Any]]] = triage,
    sleep: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    """The selection after the round (protocol sections 4.1 to 4.3), from the frozen inputs:
    exclusions, the funnel walk (100 accepted) and the two control walks with their ladder.
    Only products up to the frozen S_max count. Returns everything the selection commit
    records."""
    import time

    sleep = sleep or time.sleep
    verify_inputs(inputs_dir, inputs)
    s_max = int(inputs["s_max"])
    frame = sel.read_frame_csv(_read(inputs_dir, "frame.csv"))
    toi = sel.toi_rows(_read(inputs_dir, "toi.csv"))
    pscomppars = sel.pscomppars_rows(_read(inputs_dir, "pscomppars.csv"))
    tic_sets = {
        "TOI": {t for t in (sel.parse_tic(r["TIC ID"]) for r in toi) if t is not None},
        "CTOI": sel.ctoi_tics(_read(inputs_dir, "ctoi.csv")),
        "pscomppars": {t for t in (sel.parse_tic(r["tic_id"]) for r in pscomppars) if t},
        "TESS-EB": sel.tess_eb_tics(_read(inputs_dir, "tess_eb.tsv")),
    }
    gaia = sel.gaia_eb_positions(_read(inputs_dir, "gaia_dr3_eb.csv"))
    known = sel.known_targets(root)
    exclusions = sel.apply_exclusions(frame, set(known), tic_sets, gaia)
    retry = sel.policy()
    funnel_walk = sel.walk(
        "funnel",
        funnel_order(exclusions.kept, randomness_hex),
        lambda tic: triage_fn(tic, DOMAIN, s_max),
        SELECTION.funnel_accepted,
        retry,
        sleep,
    )
    controls = {}
    for kind, label in (("planet", "planet-pool"), ("false_positive", "fp-pool")):
        attempts = []
        for step in range(3):
            planet_depth = CONTROLS.planet_min_depth_percent
            fp_depth = CONTROLS.fp_min_depth_ppm
            if step == 2:
                planet_depth = CONTROLS.ladder_planet_min_depth_percent
                fp_depth = CONTROLS.ladder_fp_min_depth_ppm
            if kind == "planet":
                pool = sel.planet_pool(pscomppars, planet_depth)
            else:
                pool = sel.fp_pool(toi, tic_sets["pscomppars"], fp_depth)
            pool = [p for p in pool if p.tic_id not in known]
            domain = control_domain(step)
            walked = sel.walk(
                f"{kind} (ladder step {step})",
                pool_order(pool, randomness_hex, label),
                lambda tic, d=domain: triage_fn(tic, d, s_max),
                SELECTION.controls_per_pool,
                retry,
                sleep,
            )
            attempts.append({"step": step, "pool_size": len(pool), "walk": walked.to_dict()})
            if walked.stopped or walked.accepted:
                break
        rows = {p.tic_id: p for p in pool}
        chosen = walked.accepted[0] if walked.accepted else None
        controls[kind] = {
            "attempts": attempts,
            "accepted": chosen,
            "row": rows[chosen].row if chosen is not None else None,
            "name": rows[chosen].name if chosen is not None else None,
            "stopped": walked.stopped,
        }
    return {
        "schema": "refute-tess-discover-selection-1",
        "randomness": randomness_hex,
        "s_max": s_max,
        "frame_stars": len(frame),
        "kept_after_exclusions": len(exclusions.kept),
        "exclusion_counts": exclusions.counts(),
        "known_targets": {str(k): v for k, v in sorted(known.items())},
        "funnel": funnel_walk.to_dict(),
        "controls": controls,
        "complete": (
            funnel_walk.outcome == "sample_filled"
            and all(c["accepted"] is not None for c in controls.values())
        ),
    }


def needed() -> dict[str, int]:
    return {
        "funnel": SELECTION.funnel_accepted,
        "planet": SELECTION.controls_per_pool,
        "false_positive": SELECTION.controls_per_pool,
    }


# --- catalog indexes for the deduplication (protocol section 6) ------------------------------


def parse_angle(value: str | None, hours: bool) -> float | None:
    """Degrees from a decimal value, or from sexagesimal ``h:m:s`` / ``d m s`` (hours for RA)."""
    import re

    text = (value or "").strip()
    if not text:
        return None
    parts = re.split(r"[:\s]+", text)
    try:
        if len(parts) == 1:
            return float(parts[0])
        sign = -1.0 if parts[0].startswith("-") else 1.0
        numbers = [abs(float(p)) for p in parts[:3]] + [0.0] * (3 - len(parts[:3]))
        degrees = numbers[0] + numbers[1] / 60.0 + numbers[2] / 3600.0
        return sign * degrees * (15.0 if hours else 1.0)
    except ValueError:
        return None


CATALOG_FILES = ("toi.csv", "ctoi.csv", "pscomppars.csv", "tess_eb.tsv", "gaia_dr3_eb.csv")


def catalog_indexes(inputs_dir: Path, inputs: dict[str, Any]) -> dict[str, Any]:
    """The five catalogs of the deduplication from the frozen snapshots, each as a
    ``dedup.CatalogIndex`` (period in days; the Gaia period is 1 / frequency). Every snapshot
    is checked against its SHA-256 in ``inputs`` first; a missing record or a different file
    stops the step."""
    import numpy as np

    from refute.packs.tess.discover.dedup import CatalogEntry, CatalogIndex

    recorded = {i["name"]: i["sha256"] for i in inputs.get("files", [])}
    for name in CATALOG_FILES:
        if name not in recorded:
            raise sel.SelectionError(f"{name} has no recorded SHA-256")
        if hashlib.sha256(_read(inputs_dir, name)).hexdigest() != recorded[name]:
            raise sel.SelectionError(f"{name} does not match its recorded SHA-256")

    def rows(name: str) -> list[dict[str, str]]:
        return sel.read_csv_rows(_read(inputs_dir, name))

    toi = [
        CatalogEntry(
            f"TOI-{r.get('TOI')}",
            sel.parse_tic(r.get("TIC ID")),
            parse_angle(r.get("RA"), hours=":" in (r.get("RA") or "")),
            parse_angle(r.get("Dec"), hours=False),
            sel._float(r.get("Period (days)")),
        )
        for r in rows("toi.csv")
    ]
    ctoi = [
        CatalogEntry(
            f"CTOI-{r.get('CTOI')}",
            sel.parse_tic(r.get("TIC ID")),
            parse_angle(r.get("RA"), hours=":" in (r.get("RA") or "")),
            parse_angle(r.get("Dec"), hours=False),
            sel._float(r.get("Period (days)")),
        )
        for r in rows("ctoi.csv")
    ]
    planets = [
        CatalogEntry(
            r.get("pl_name") or "",
            sel.parse_tic(r.get("tic_id")),
            sel._float(r.get("ra")),
            sel._float(r.get("dec")),
            sel._float(r.get("pl_orbper")),
        )
        for r in rows("pscomppars.csv")
    ]
    lines = [
        line
        for line in _read(inputs_dir, "tess_eb.tsv").decode("utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    header = [h.strip() for h in lines[0].split("\t")]
    eb = []
    for line in lines[3:]:
        cells = dict(zip(header, (c.strip() for c in line.split("\t")), strict=False))
        tic = cells.get("TIC")
        eb.append(
            CatalogEntry(
                f"TESS-EB TIC {tic}",
                int(tic) if tic and tic.isdigit() else None,
                parse_angle(cells.get("RAJ2000"), hours=" " in (cells.get("RAJ2000") or "")),
                parse_angle(cells.get("DEJ2000"), hours=False),
                sel._float(cells.get("Per")),
            )
        )
    gaia_text = _read(inputs_dir, "gaia_dr3_eb.csv").decode("utf-8")
    _, _, body = gaia_text.partition("\n")
    table = (
        np.loadtxt(body.splitlines(), delimiter=",", ndmin=2) if body.strip() else np.zeros((0, 4))
    )
    gaia = [
        CatalogEntry(
            f"Gaia DR3 {int(row[0])}",
            None,
            float(row[1]),
            float(row[2]),
            (1.0 / float(row[3])) if row[3] > 0 else None,
        )
        for row in table
    ]
    return {
        "TOI": CatalogIndex(toi),
        "CTOI": CatalogIndex(ctoi),
        "pscomppars": CatalogIndex(planets),
        "TESS-EB": CatalogIndex(eb),
        "Gaia-DR3-EB": CatalogIndex(gaia),
    }
