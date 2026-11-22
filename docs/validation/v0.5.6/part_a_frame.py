"""v0.5.6 part A (exploratory): the sampling frame, the split by TIC and the draw, recorded before
any light curve is read (docs/plans/v0.5.6-plan.md; the maintainer's decisions of 2026-11-21,
22:30, item 3, and 22:45, item 3; #218). Outputs are exploratory, never verdicts; every output
carries the limits label of the v0.5 battery. ``method_status: not_validated``. Codex's review of
this script (conversation ``partaframe``) is applied: the listing mirrors the adapter's filters,
transits are counted once with an edge margin, the split uses the whole digest, the exposure flag
reads a fixed commit, and each step consumes the frozen output of the one before.

Steps (each refuses to write over its output; MAST answers are cached per TIC, so the draw is
resumable):

1. ``fetch``: the NASA Exoplanet Archive's TOI table, by a TAP query that names its columns
   (``tfopwg_disp`` is a **descriptive** column only), and PSCompPars' confirmed planets. Each raw
   answer is written atomically to ``.cache/v056/frame/`` with its query, date and SHA-256.
2. ``frame``: one row per TIC with **exactly one** distinct TOI and a complete, positive ephemeris
   (period, epoch, duration, depth); every exclusion is recorded per TIC. The arm, from open
   sources only:
   - **planet**: exactly one PSCompPars planet with ``disc_facility`` equal to TESS and a positive
     period within 1 % (inclusive) of the TOI's;
   - **ambiguous** (excluded): more than one such planet;
   - **open**: none (the absence of that match, nothing more).
   The disposition never enters eligibility, the arm, the split or the draw. Prior exposure:
   every TIC that a file of commit ``EXPOSURE_COMMIT`` names (in text, or in a TIC column of a
   CSV/TSV) is flagged, with its evidence; the flag only matters for the confirmation half.
3. ``split``: ``int(sha256(seed:split:TIC), 16) % 2 == 0`` is exploration, else confirmation.
4. ``draw``: it reads the frozen frame (its SHA-256 checked). In the exploration half, per arm,
   TICs in ascending ``sha256(seed:draw:TIC)`` order; each is checked from MAST **metadata only**
   (no light curve is read), with the adapter's filters (``TessAdapter.fetch``: author SPOC,
   exposure exactly 120 s, light-curve products ``*lc.fits``, the TIC itself, sectors up to 107,
   the locked v0.5 plan's ``max_sector``), for at least two transits **predicted** inside the
   sectors' time ranges: the union of transit indices whose centre lies at least ``EDGE_DAYS``
   inside a range (MAST gives MJD; the epoch is BJD; the margin covers the barycentric and
   time-scale offsets, so an edge never creates a transit). A failed query is a failure, never an
   empty answer. The walk stops at 120 eligible per arm; the final record is written only after
   its checks (hashes, unique TICs, exploration half, 120 per arm), or as incomplete.

Usage (from the project root): ``.venv/Scripts/python.exe docs/validation/v0.5.6/part_a_frame.py
fetch|frame|draw``.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CACHE = ROOT / ".cache" / "v056" / "frame"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
TOI_COLUMNS = (
    "toi",
    "tid",
    "tfopwg_disp",
    "pl_orbper",
    "pl_tranmid",
    "pl_trandurh",
    "pl_trandep",
    "st_tmag",
    "toi_created",
    "rowupdate",
)
PS_COLUMNS = ("pl_name", "tic_id", "pl_orbper", "disc_facility")
TESS_FACILITY = "Transiting Exoplanet Survey Satellite (TESS)"
PERIOD_MATCH = 0.01
# The seed: a fixed string naming the phase, the part and the day, chosen before any data was
# read; an exploratory draw needs no drand round (the plan).
SEED = "refute-v0.5.6-part-a-2026-11-21"
PER_ARM = 120
MAX_SECTOR = 107  # calibration/v0.5/claim.yaml, test_plan.discovery.max_sector (locked)
MIN_PREDICTED = 2
EXPTIME = 120
MJD_TO_JD = 2400000.5
EDGE_DAYS = 0.01  # > the largest barycentric correction (about 0.0058 d) plus TDB-UTC (< 0.001 d)
EXPOSURE_COMMIT = "c4d6fa352c40d4ef17ae0565de80920a03b744ef"  # the last commit before part A
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
BATCH = 10  # TICs walked per step; MAST is queried one TIC at a time
QUERY_THREADS = 4  # MAST answered multi-TIC queries with errors and timeouts on 2026-11-21
ATTEMPTS = 5
BACKOFF_SECONDS = 120
CHANGES_SINCE_FRAME = (
    "after the frame was written, only the draw's querying changed: one TIC per MAST query, "
    "4 queries at a time, walked 10 TICs per step, with retries (5 attempts, 120 s apart); "
    "the frame's rules did not"
)
FRAME_FILE = HERE / "part-a-frame.csv"
FRAME_RECORD = HERE / "part-a-frame.json"
EXPOSURE_RECORD = HERE / "part-a-exposure.json"
DRAW_RECORD = HERE / "part-a-draw.json"
TIC_COLUMNS = {"tic", "ticid", "tic_id", "tid", "tic id", "tic_id_str"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_once(path: Path, text: str) -> None:
    """Write ``path`` atomically, refusing to write over it."""
    if path.exists():
        raise SystemExit(f"{path.name} exists; never written over")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, "utf-8", newline="\n")
    os.replace(tmp, path)


def write_atomic(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


# --- 1. fetch --------------------------------------------------------------------------------


def _tap(query: str) -> bytes:
    url = TAP + "?" + urllib.parse.urlencode({"query": query, "format": "csv"})
    with urllib.request.urlopen(url, timeout=300) as response:  # noqa: S310 - a fixed https URL
        return response.read()


QUERIES = {
    "toi": f"select {','.join(TOI_COLUMNS)} from toi",
    "pscomppars": f"select {','.join(PS_COLUMNS)} from pscomppars where tic_id is not null",
}


def fetch() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, query in QUERIES.items():
        path, meta = CACHE / f"{name}.csv", CACHE / f"{name}.json"
        if meta.exists():
            continue
        data = _tap(query)
        write_atomic(path, data)
        info = {"query": query, "url": TAP, "retrieved_utc": utc(), "sha256": sha256(data)}
        write_atomic(meta, json.dumps(info, indent=1).encode())
    print("fetched:", sorted(QUERIES))


def snapshots() -> dict:
    """The raw answers' records, each checked against its bytes."""
    out = {}
    for name in QUERIES:
        info = json.loads((CACHE / f"{name}.json").read_text("utf-8"))
        if sha256((CACHE / f"{name}.csv").read_bytes()) != info["sha256"]:
            raise SystemExit(f"{name}.csv does not match its recorded SHA-256")
        out[name] = info
    return out


# --- 2. the frame ----------------------------------------------------------------------------


def _rows(name: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO((CACHE / f"{name}.csv").read_text("utf-8"))))


def _float(value: str | None) -> float | None:
    try:
        x = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _tic(value: str | None) -> int | None:
    m = re.fullmatch(r"\s*(?:TIC\s*)?(\d{1,12})\s*", value or "")
    return int(m.group(1)) if m else None


def _git(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=True).stdout


TEXT_TIC = re.compile(rb"TIC[-_ ]?(\d{3,12})|tic_id\D{1,4}(\d{3,12})")


def prior_exposure() -> tuple[dict[int, str], dict]:
    """Every TIC a file of ``EXPOSURE_COMMIT`` names: in text (``TIC 123``, ``tic_id: 123``) or in
    a TIC column of a CSV/TSV. Returns the first evidence per TIC (path and line, or path and
    field) and the scan's totals; a file that cannot be read is counted, never skipped silently."""
    names = _git("ls-tree", "-r", "-z", "--name-only", EXPOSURE_COMMIT).decode("utf-8").split("\0")
    evidence: dict[int, str] = {}
    failed = 0
    for path in (n for n in names if n):
        try:
            data = _git("show", f"{EXPOSURE_COMMIT}:{path}")
        except subprocess.CalledProcessError:
            failed += 1
            continue
        for n, line in enumerate(data.split(b"\n"), 1):
            for m in TEXT_TIC.finditer(line):
                evidence.setdefault(int(m.group(1) or m.group(2)), f"{path}:{n}")
        if path.lower().endswith((".csv", ".tsv")):
            text = data.decode("utf-8", "replace")
            delimiter = "\t" if path.lower().endswith(".tsv") else ","
            lines = [x for x in text.splitlines() if x and not x.startswith("#")]
            if not lines:
                continue
            reader = csv.DictReader(io.StringIO("\n".join(lines)), delimiter=delimiter)
            columns = [c for c in (reader.fieldnames or []) if c.strip().lower() in TIC_COLUMNS]
            for row in reader:
                for c in columns:
                    tic = _tic(row.get(c))
                    if tic is not None:
                        evidence.setdefault(tic, f"{path}:{c}")
    return evidence, {"commit": EXPOSURE_COMMIT, "files": len(names), "unreadable": failed}


def half_of(tic: int) -> str:
    digest = sha256(f"{SEED}:split:{tic}".encode())
    return "exploration" if int(digest, 16) % 2 == 0 else "confirmation"


def draw_key(tic: int) -> str:
    return sha256(f"{SEED}:draw:{tic}".encode())


FRAME_FIELDS = (
    "tic_id",
    "toi",
    "arm",
    "pl_name",
    "period_days",
    "epoch_bjd",
    "duration_hours",
    "depth_ppm",
    "tmag",
    "toi_created",
    "tfopwg_disp_descriptive",
    "prior_exposure",
    "half",
)


def build_frame(tois, planets_rows, exposed: set[int]):
    """The frame rows and the exclusions per TIC (pure: the tests call it)."""
    by_tic: dict[int, dict[str, dict[str, str]]] = {}
    excluded: dict[str, list[int]] = {"bad_tic": [], "several_tois": [], "ephemeris": [],
                                      "ambiguous": []}  # fmt: skip
    for row in tois:
        tic = _tic(row.get("tid"))
        if tic is None:
            excluded["bad_tic"].append(-1)
            continue
        by_tic.setdefault(tic, {})[row["toi"]] = row  # duplicate rows of one TOI collapse
    planets: dict[int, list[dict[str, str]]] = {}
    for row in planets_rows:
        tic = _tic(row.get("tic_id"))
        if tic is not None and row.get("disc_facility") == TESS_FACILITY:
            planets.setdefault(tic, []).append(row)
    rows = []
    for tic in sorted(by_tic):
        group = by_tic[tic]
        if len(group) != 1:
            excluded["several_tois"].append(tic)
            continue
        r = next(iter(group.values()))
        eph = {k: _float(r[k]) for k in ("pl_orbper", "pl_tranmid", "pl_trandurh", "pl_trandep")}
        if any(v is None or v <= 0 for v in eph.values()):
            excluded["ephemeris"].append(tic)
            continue
        matches = []
        for p in planets.get(tic, []):
            pp = _float(p.get("pl_orbper"))
            if pp is not None and pp > 0 and abs(eph["pl_orbper"] - pp) / pp <= PERIOD_MATCH:
                matches.append(p)
        if len(matches) > 1:
            excluded["ambiguous"].append(tic)
            continue
        rows.append(
            {
                "tic_id": tic,
                "toi": r["toi"],
                "arm": "planet" if matches else "open",
                "pl_name": matches[0]["pl_name"] if matches else "",
                "period_days": repr(eph["pl_orbper"]),
                "epoch_bjd": repr(eph["pl_tranmid"]),
                "duration_hours": repr(eph["pl_trandurh"]),
                "depth_ppm": repr(eph["pl_trandep"]),
                "tmag": r["st_tmag"],
                "toi_created": r["toi_created"],
                "tfopwg_disp_descriptive": r["tfopwg_disp"],
                "prior_exposure": tic in exposed,
                "half": half_of(tic),
            }
        )
    return rows, excluded


def frame() -> None:
    if FRAME_RECORD.exists():
        raise SystemExit("the frame is recorded; never written over")
    sources = snapshots()
    evidence, scan = prior_exposure()
    rows, excluded = build_frame(_rows("toi"), _rows("pscomppars"), set(evidence))
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(FRAME_FIELDS), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    write_once(FRAME_FILE, buf.getvalue())
    in_frame = {int(r["tic_id"]) for r in rows}
    write_once(
        EXPOSURE_RECORD,
        json.dumps(
            {
                "scan": scan,
                "evidence": {str(t): evidence[t] for t in sorted(evidence) if t in in_frame},
            },
            indent=1,
        )
        + "\n",  # fmt: skip
    )
    counts: dict[str, int] = {"frame": len(rows)}
    for arm in ("planet", "open"):
        for half in ("exploration", "confirmation"):
            sel = [x for x in rows if x["arm"] == arm and x["half"] == half]
            counts[f"{arm}_{half}"] = len(sel)
            counts[f"{arm}_{half}_prior_exposure"] = sum(1 for x in sel if x["prior_exposure"])
    record = {
        "schema": "refute-v056-part-a-frame-2",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "decision": "the maintainer's decisions of 2026-11-21 (22:30, item 3; 22:45, item 3), #218",
        "sources": sources,
        "rules": {
            "single_toi_tics": True,
            "period_match_inclusive": PERIOD_MATCH,
            "tess_facility": TESS_FACILITY,
            "seed": SEED,
            "split": "int(sha256(seed:split:tic), 16) % 2 == 0 is exploration",
            "draw_order": "sha256(seed:draw:tic) ascending, per arm, exploration half only",
            "disposition": "descriptive only: never eligibility, arm, split or draw",
            "exposure_commit": EXPOSURE_COMMIT,
        },
        "biases_declared": [
            "only stars with exactly one catalogued TOI (multi-TOI systems excluded)",
            "only TOIs with a published, complete ephemeris",
            "eligibility favours stars with SPOC two-minute data and more transit opportunities",
            "'open' means only the absence of the defined match to a TESS-discovered planet",
        ],
        "excluded_counts": {k: len(v) for k, v in excluded.items()},
        "excluded": excluded,
        "counts": counts,
        "exposure_record": EXPOSURE_RECORD.name,
        "exposure_sha256": sha256(EXPOSURE_RECORD.read_bytes()),
        "frame_file": FRAME_FILE.name,
        "frame_sha256": sha256(FRAME_FILE.read_bytes()),
        "code_sha256": sha256(Path(__file__).read_bytes()),
        "written_utc": utc(),
    }
    write_once(FRAME_RECORD, json.dumps(record, indent=1) + "\n")
    print(json.dumps(counts, indent=1))


# --- 4. the draw (MAST metadata only) --------------------------------------------------------


def _listing(tics: list[int]) -> dict[int, list[dict]]:
    """SPOC 120-s light-curve products per TIC from MAST metadata, with the adapter's filters
    (author SPOC, exposure exactly 120 s, ``*lc.fits`` products, the TIC itself, sectors up to
    ``MAX_SECTOR``). No file is read. A failure raises; an empty list is a successful answer."""
    from astroquery.mast import Observations

    obs = Observations.query_criteria(
        project="TESS",
        provenance_name="SPOC",
        dataproduct_type="timeseries",
        target_name=[str(t) for t in tics],
    )
    out: dict[int, list[dict]] = {t: [] for t in tics}
    keep = [i for i, row in enumerate(obs) if abs(float(row["t_exptime"]) - EXPTIME) < 1e-6]
    if not keep:
        return out
    obs = obs[keep]
    products = Observations.get_product_list(obs)
    by_obsid = {str(row["obsid"]): row for row in obs}
    for p in products:
        name = str(p["productFilename"])
        if not name.endswith("lc.fits"):
            continue
        row = by_obsid.get(str(p["obsID"])) or by_obsid.get(str(p["parent_obsid"]))
        if row is None:
            continue
        tic = _tic(str(row["target_name"]))
        sector = int(row["sequence_number"])
        if tic not in out or sector > MAX_SECTOR:
            continue
        t_min, t_max = float(row["t_min"]), float(row["t_max"])
        if not (math.isfinite(t_min) and math.isfinite(t_max) and t_min < t_max):
            raise SystemExit(f"TIC {tic} sector {sector}: invalid time range")
        out[tic].append(
            {
                "sector": sector,
                "exptime": float(row["t_exptime"]),
                "obs_id": str(row["obs_id"]),
                "productFilename": name,
                "dataURI": str(p["dataURI"]),
                "t_min_mjd": t_min,
                "t_max_mjd": t_max,
            }
        )
    return out


def _one_with_retries(tic: int) -> list[dict]:
    """``_listing`` of one TIC with ``ATTEMPTS`` attempts ``BACKOFF_SECONDS`` apart; exhausted
    retries stop the draw (resumable), and a failure is never an empty answer."""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            return _listing([tic])[tic]
        except Exception as exc:  # noqa: BLE001 - retried, then the draw stops
            print(f"TIC {tic}: MAST attempt {attempt} failed: {type(exc).__name__}: {exc}"[:240])
            if attempt == ATTEMPTS:
                raise SystemExit(
                    f"TIC {tic}: MAST failed after the retries; the draw stops (resumable)"
                ) from exc
            time.sleep(BACKOFF_SECONDS)
    raise AssertionError("unreachable")


def _listing_with_retries(tics: list[int]) -> dict[int, list[dict]]:
    """One MAST query per TIC, ``QUERY_THREADS`` at a time."""
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=QUERY_THREADS) as pool:
        return dict(zip(tics, pool.map(_one_with_retries, tics), strict=True))


def predicted(period: float, epoch_bjd: float, windows: list[dict]) -> int:
    """The number of distinct transit indices whose centre lies at least ``EDGE_DAYS`` inside one
    of the windows (a union: overlapping or repeated windows count a transit once)."""
    indices: set[int] = set()
    for w in windows:
        lo = w["t_min_mjd"] + MJD_TO_JD + EDGE_DAYS
        hi = w["t_max_mjd"] + MJD_TO_JD - EDGE_DAYS
        if hi < lo:
            continue
        indices.update(range(math.ceil((lo - epoch_bjd) / period),
                             math.floor((hi - epoch_bjd) / period) + 1))  # fmt: skip
    return len(indices)


def draw() -> None:
    if DRAW_RECORD.exists():
        raise SystemExit("the draw is recorded; never written over")
    record = json.loads(FRAME_RECORD.read_text("utf-8"))
    if sha256(FRAME_FILE.read_bytes()) != record["frame_sha256"]:
        raise SystemExit("the frame does not match its recorded SHA-256")
    rows = list(csv.DictReader(io.StringIO(FRAME_FILE.read_text("utf-8"))))
    mast_dir = CACHE / "mast"
    mast_dir.mkdir(parents=True, exist_ok=True)
    arms, complete = {}, True
    for arm in ("planet", "open"):
        pool = sorted(
            (r for r in rows if r["arm"] == arm and r["half"] == "exploration"),
            key=lambda r: draw_key(int(r["tic_id"])),
        )
        trail, chosen, k = [], [], 0
        while len(chosen) < PER_ARM and k < len(pool):
            batch = pool[k : k + BATCH]
            todo = [
                int(r["tic_id"]) for r in batch if not (mast_dir / f"{r['tic_id']}.json").exists()
            ]
            if todo:
                listed = _listing_with_retries(todo)
                for tic, items in listed.items():
                    payload = {"tic_id": tic, "queried_utc": utc(), "products": items}
                    write_atomic(mast_dir / f"{tic}.json", json.dumps(payload, indent=1).encode())
            for position, r in enumerate(batch, start=k):
                if len(chosen) >= PER_ARM:
                    break
                tic = int(r["tic_id"])
                listing = json.loads((mast_dir / f"{tic}.json").read_text("utf-8"))
                windows = listing["products"]
                n = predicted(float(r["period_days"]), float(r["epoch_bjd"]), windows)
                if not windows:
                    reason = f"no SPOC 120-s light curve up to sector {MAX_SECTOR}"
                elif n < MIN_PREDICTED:
                    reason = f"{n} predicted transit(s) inside the sectors' time ranges"
                else:
                    reason = "eligible"
                entry = {
                    "position": position,
                    "draw_key": draw_key(tic),
                    "tic_id": tic,
                    "toi": r["toi"],
                    "reason": reason,
                    "predicted_transits": n,
                    "sectors": sorted({w["sector"] for w in windows}),
                    "products": [w["productFilename"] for w in windows],
                    "listing_sha256": sha256((mast_dir / f"{tic}.json").read_bytes()),
                }
                trail.append(entry)
                if reason == "eligible":
                    chosen.append({**entry, **{f: r[f] for f in FRAME_FIELDS if f not in entry}})
            k += len(batch)
        tics = [c["tic_id"] for c in chosen]
        if len(set(tics)) != len(tics) or any(c["half"] != "exploration" for c in chosen):
            raise SystemExit(f"{arm}: the draw failed its checks")
        if len(chosen) < PER_ARM:
            complete = False
        arms[arm] = {"pool": len(pool), "checked": len(trail), "eligible": len(chosen),
                     "chosen": chosen, "trail": trail}  # fmt: skip
    out = {
        "schema": "refute-v056-part-a-draw-2",
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "status": "complete" if complete else "incomplete",
        "frame_sha256": record["frame_sha256"],
        "code_sha256": sha256(Path(__file__).read_bytes()),
        "listing": "MAST metadata (astroquery Observations), the adapter's filters",
        "changes_since_frame": CHANGES_SINCE_FRAME,
        "prior_exposure_note": (
            "the flag is a superset: catalog snapshots in the repository name nearly every TOI; "
            "part B fixes which evidence counts, from the reproducible scan, before its drand draw"
        ),
        "edge_days": EDGE_DAYS,
        "written_utc": utc(),
        "arms": arms,
    }
    write_once(DRAW_RECORD, json.dumps(out, indent=1) + "\n")
    print({a: v["eligible"] for a, v in arms.items()}, out["status"])


if __name__ == "__main__":
    {"fetch": fetch, "frame": frame, "draw": draw}[sys.argv[1]]()
