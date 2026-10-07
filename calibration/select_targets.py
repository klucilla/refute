"""Pre-registered selection of the v0.1 calibration targets (needs network).

Implements calibration/PROTOCOL.md exactly. Run from the repository root:

    uv run python calibration/select_targets.py

Outputs (all inside calibration/):

- pool_snapshot/*.csv and pool_snapshot/retrieval.json: raw catalog responses,
  with URL, retrieval time (UTC) and SHA-256;
- targets.yaml: the selected targets, every value copied from the snapshots;
- selection_log.md: every candidate examined, accepted or rejected, with reason.

Nothing here submits anything anywhere: it only reads public catalogs.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import random
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

SEED = 20261007
N_PLANETS = 11  # 10 calibration planets + 1 development target
N_CALIBRATION_PLANETS = 10
N_FALSE_POSITIVES = 3
MIN_YEARS = 2
MIN_SPAN_DAYS = 300.0

TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
PLANET_COLUMNS = [
    "pl_name",
    "hostname",
    "tic_id",
    "pl_orbper",
    "pl_orbpererr1",
    "pl_orbpererr2",
    "pl_orbper_reflink",
    "pl_tranmid",
    "pl_tranmid_reflink",
    "pl_trandep",
    "pl_trandep_reflink",
    "pl_trandur",
    "pl_trandur_reflink",
    "pl_rade",
    "sy_tmag",
    "sy_pnum",
    "st_rad",
    "st_mass",
    "tran_flag",
    "disc_facility",
]
PLANET_FILTER = (
    "tran_flag = 1 and tic_id is not null and pl_orbper > 0.5 and pl_orbper < 10 "
    "and pl_trandep >= 0.1 and sy_tmag <= 12 and sy_pnum = 1"
)
PLANET_QUERY = f"select {', '.join(PLANET_COLUMNS)} from pscomppars where {PLANET_FILTER}"
HOSTS_QUERY = "select distinct tic_id from pscomppars where tic_id is not null"
TOI_URL = "https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv"

HERE = Path(__file__).resolve().parent
SNAPSHOT_DIR = HERE / "pool_snapshot"


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def tap_url(query: str) -> str:
    return f"{TAP}?{urllib.parse.urlencode({'query': query, 'format': 'csv'})}"


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "refute-calibration/0.1"})
    with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310 - fixed URLs
        return response.read()


def snapshot(name: str, url: str) -> tuple[bytes, dict[str, Any]]:
    data = download(url)
    if data.lstrip().startswith(b"<?xml"):
        raise RuntimeError(f"query failed for {name}: {data[:500]!r}")
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    (SNAPSHOT_DIR / name).write_bytes(data)
    record = {
        "file": f"pool_snapshot/{name}",
        "url": url,
        "retrieved_utc": utc_now(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }
    return data, record


def read_csv(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))


def parse_tic(value: str) -> int | None:
    match = re.search(r"(\d+)", value or "")
    return int(match.group(1)) if match else None


def to_float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def strip_html(value: str | None) -> str | None:
    if not value:
        return None
    text = re.sub(r"<[^>]+>", "", value).strip()
    href = re.search(r"href=(\S+)", value)
    return f"{text} ({href.group(1)})" if href else text


def mjd_year(mjd: float) -> int:
    return (datetime(1858, 11, 17, tzinfo=UTC) + timedelta(days=float(mjd))).year


def mast_availability(tic: int) -> dict[str, Any]:
    import lightkurve as lk

    result = lk.search_lightcurve(f"TIC {tic}", mission="TESS", author="SPOC", exptime=120)
    table = result.table
    rows = [i for i in range(len(table)) if str(table["target_name"][i]).strip() == str(tic)]
    sectors, starts = [], []
    for i in rows:
        match = re.search(r"Sector (\d+)", str(table["mission"][i]))
        sectors.append(int(match.group(1)) if match else None)
        starts.append(float(table["t_min"][i]))
    years = sorted({mjd_year(t) for t in starts})
    span = (max(starts) - min(starts)) if starts else 0.0
    accepted = len(years) >= MIN_YEARS and span >= MIN_SPAN_DAYS
    reason = (
        "accepted"
        if accepted
        else f"data rule not met: {len(rows)} SPOC 120-s light curves, years {years}, "
        f"span {span:.0f} d (need >= {MIN_YEARS} years and >= {MIN_SPAN_DAYS:.0f} d)"
    )
    return {
        "service": "MAST via lightkurve.search_lightcurve (author=SPOC, exptime=120)",
        "retrieved_utc": utc_now(),
        "n_light_curves": len(rows),
        "sectors": sorted(s for s in sectors if s is not None),
        "years": years,
        "first_start_mjd": min(starts) if starts else None,
        "last_start_mjd": max(starts) if starts else None,
        "span_days": round(span, 3),
        "accepted": accepted,
        "reason": reason,
    }


def walk(pool: list[dict], needed: int, label: str, log: list[str]) -> list[tuple[dict, dict]]:
    accepted = []
    for position, row in enumerate(pool, start=1):
        tic = row["_tic"]
        try:
            mast = mast_availability(tic)
        except Exception as exc:  # noqa: BLE001 - logged, candidate rejected
            mast = {"accepted": False, "reason": f"MAST query failed: {exc}"}
        decision = "ACCEPTED" if mast["accepted"] else "rejected"
        log.append(
            f"| {label} | {position} | TIC {tic} | {row['_name']} | {decision} | {mast['reason']} |"
        )
        print(
            f"{label} #{position} TIC {tic} {row['_name']}: {decision} ({mast['reason']})",
            flush=True,
        )
        if mast["accepted"]:
            accepted.append((row, mast))
            if len(accepted) == needed:
                break
    if len(accepted) < needed:
        raise RuntimeError(f"pool exhausted: only {len(accepted)} {label} targets accepted")
    return accepted


def main() -> int:
    retrieval = []
    planet_data, record = snapshot("pscomppars_planet_pool.csv", tap_url(PLANET_QUERY))
    retrieval.append({**record, "query": PLANET_QUERY})
    hosts_data, record = snapshot("pscomppars_host_tic_ids.csv", tap_url(HOSTS_QUERY))
    retrieval.append({**record, "query": HOSTS_QUERY})
    toi_data, record = snapshot("exofop_toi.csv", TOI_URL)
    retrieval.append(record)
    (SNAPSHOT_DIR / "retrieval.json").write_bytes(
        (json.dumps(retrieval, indent=2) + "\n").encode("utf-8")
    )
    by_file = {r["file"]: r for r in retrieval}

    # --- planet pool
    planets = []
    for row in read_csv(planet_data):
        tic = parse_tic(row["tic_id"])
        if tic is None:
            continue
        planets.append({**row, "_tic": tic, "_name": row["pl_name"]})
    planets.sort(key=lambda r: (r["_tic"], r["_name"]))
    random.Random(SEED).shuffle(planets)

    # --- false-positive pool
    host_tics = {parse_tic(r["tic_id"]) for r in read_csv(hosts_data)}
    tois = read_csv(toi_data)
    toi_count = Counter(parse_tic(r["TIC ID"]) for r in tois)
    fps = []
    for row in tois:
        tic = parse_tic(row["TIC ID"])
        tfop = (row.get("TFOPWG Disposition") or "").strip()
        tess = (row.get("TESS Disposition") or "").strip()
        period = to_float(row.get("Period (days)"))
        depth = to_float(row.get("Depth (ppm)"))
        tmag = to_float(row.get("TESS Mag"))
        disposition_ok = tfop == "FP" or (tess == "EB" and tfop not in {"CP", "KP", "PC", "APC"})
        if not (
            tic is not None
            and disposition_ok
            and period is not None
            and 0.5 < period < 10
            and depth is not None
            and depth >= 1000
            and tmag is not None
            and tmag <= 12
            and toi_count[tic] == 1
            and tic not in host_tics
        ):
            continue
        fps.append({**row, "_tic": tic, "_name": f"TOI-{row['TOI']}"})
    fps.sort(key=lambda r: (r["_tic"], float(r["TOI"])))
    random.Random(SEED).shuffle(fps)

    print(f"planet pool: {len(planets)}; false-positive pool: {len(fps)}", flush=True)
    log: list[str] = []
    accepted_planets = walk(planets, N_PLANETS, "planet", log)
    accepted_fps = walk(fps, N_FALSE_POSITIVES, "false_positive", log)

    planet_source = by_file["pool_snapshot/pscomppars_planet_pool.csv"]
    toi_source = by_file["pool_snapshot/exofop_toi.csv"]
    targets = []
    for index, (row, mast) in enumerate(accepted_planets):
        err1, err2 = to_float(row["pl_orbpererr1"]), to_float(row["pl_orbpererr2"])
        errors = [abs(e) for e in (err1, err2) if e is not None]
        depth_pct = to_float(row["pl_trandep"])
        targets.append(
            {
                "key": f"TIC-{row['_tic']}",
                "tic_id": row["_tic"],
                "kind": "planet" if index < N_CALIBRATION_PLANETS else "development",
                "name": row["pl_name"],
                "published": {
                    "period_days": to_float(row["pl_orbper"]),
                    "period_err_days": max(errors) if errors else None,
                    "t0_bjd": to_float(row["pl_tranmid"]),
                    "depth_ppm": depth_pct * 1e4 if depth_pct is not None else None,
                    "duration_hours": to_float(row["pl_trandur"]),
                },
                "source": {
                    "name": "NASA Exoplanet Archive, Planetary Systems Composite Parameters",
                    "url": planet_source["url"],
                    "retrieved_utc": planet_source["retrieved_utc"],
                    "reference": strip_html(row["pl_orbper_reflink"]),
                },
                "catalog": {k: v for k, v in row.items() if not k.startswith("_")},
                "mast": mast,
            }
        )
    for row, mast in accepted_fps:
        errors = to_float(row.get("Period (days) err"))
        targets.append(
            {
                "key": f"TIC-{row['_tic']}",
                "tic_id": row["_tic"],
                "kind": "false_positive",
                "name": row["_name"],
                "published": {
                    "period_days": to_float(row["Period (days)"]),
                    "period_err_days": errors,
                    "t0_bjd": to_float(row["Epoch (BJD)"]),
                    "depth_ppm": to_float(row["Depth (ppm)"]),
                    "duration_hours": to_float(row["Duration (hours)"]),
                },
                "source": {
                    "name": "ExoFOP-TESS TOI table",
                    "url": toi_source["url"],
                    "retrieved_utc": toi_source["retrieved_utc"],
                    "reference": f"TOI {row['TOI']}",
                },
                "catalog": {k: v for k, v in row.items() if not k.startswith("_")},
                "mast": mast,
                "fp_reason": (row.get("Comments") or "").strip() or None,
            }
        )

    document = {
        "schema": "refute-tess-targets-1",
        "generated_utc": utc_now(),
        "generator": "calibration/select_targets.py",
        "selection": {
            "protocol": "calibration/PROTOCOL.md",
            "seed": SEED,
            "planet_filter_adql": PLANET_FILTER,
            "false_positive_filter": (
                "(TFOPWG Disposition == FP) or (TESS Disposition == EB and TFOPWG Disposition "
                "not in {CP, KP, PC, APC}); 0.5 < Period (days) < 10; Depth (ppm) >= 1000; "
                "TESS Mag <= 12; exactly one TOI for the TIC; TIC hosts no planet in pscomppars"
            ),
            "data_rule": (
                f"SPOC 120-s light curves in >= {MIN_YEARS} calendar years with >= "
                f"{MIN_SPAN_DAYS:.0f} days between first and last sector start"
            ),
            "pool_sizes": {"planets": len(planets), "false_positives": len(fps)},
            "snapshots": retrieval,
        },
        "targets": targets,
    }
    (HERE / "targets.yaml").write_bytes(
        yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=100).encode("utf-8")
    )
    header = [
        "# Selection log",
        "",
        f"Generated {document['generated_utc']} by `calibration/select_targets.py` following",
        "`calibration/PROTOCOL.md` (seed 20261007). Every candidate examined is listed, in",
        "the order of the shuffled pool.",
        "",
        f"- Planet pool: {len(planets)} rows; false-positive pool: {len(fps)} rows.",
        "",
        "| Pool | Position | Target | Name | Decision | Reason |",
        "|---|---|---|---|---|---|",
    ]
    (HERE / "selection_log.md").write_bytes(("\n".join(header + log) + "\n").encode("utf-8"))
    print(f"wrote {len(targets)} targets to calibration/targets.yaml", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
