"""Pre-registered selection of the v0.2 calibration targets (needs network).

Implements calibration/v0.2/PROTOCOL.md exactly. It refuses to run before the
drand round fixed in the protocol has been published. Run from the repository
root (py_ecc, the BLS verifier, is in the locked "calibration" dependency group):

    uv run --frozen python calibration/v0.2/select_targets.py

Outputs (all inside calibration/v0.2/):

- pool_snapshot/*.csv and pool_snapshot/retrieval.json: raw catalog responses with
  URL, retrieval time (UTC) and SHA-256;
- targets.yaml: the selected targets, every value copied from the snapshots;
- eb_catalog.csv: the eb-catalog attachment (format refute-eb-catalog-1), the
  entries of the eclipsing-binary snapshots within 120 arcsec of every selected
  target, and eb_catalog_scan.json (role eb-catalog-scan, format
  refute-eb-catalog-scan-1): the snapshots scanned with their hashes and row
  counts, the radius and the targets, which proves the catalogs were examined;
- selection_log.md: the drand round (number, randomness, signature, URL,
  verification), the seed, the exclusions and every candidate examined.

Nothing here submits anything anywhere: it only reads public catalogs.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import random
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, datetime, timedelta
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SNAPSHOT_DIR = HERE / "pool_snapshot"

# --- randomness: drand mainnet, default chain (fixed before the round is published) ---
DRAND_URL = "https://api.drand.sh"
DRAND_CHAIN_HASH = "8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce"
DRAND_PUBLIC_KEY = (
    "868f005eb8e6e4ca0a47c8a77ceaa5309a47978a7c71bc5cce96366b5d7a569937c529eeda66c7293784"
    "a9402801af31"
)
DRAND_GENESIS = 1595431050
DRAND_PERIOD = 30
TARGET_ROUND = 6537566  # published at 2026-10-09T15:00:00Z

# --- selection sizes and data rule (same as v0.1, plus target pixel files) ------------
N_PLANETS = 11  # 10 calibration planets + 1 development target
N_CALIBRATION_PLANETS = 10
N_FALSE_POSITIVES = 10
MIN_YEARS = 2
MIN_SPAN_DAYS = 300.0
EXTRACT_RADIUS_ARCSEC = 120.0

# --- the 14 known targets of v0.1 (13 calibration targets + development target) -------
KNOWN_TARGETS = {
    207141131: "HD 18599 b",
    138819293: "GJ 436 b",
    77031414: "WASP-173 A b",
    440872576: "TOI-3160 A b",
    36592530: "WASP-75 b",
    369327947: "LHS 475 b",
    398572544: "WASP-28 b",
    283621618: "TOI-5806 b",
    374530847: "WASP-2 b",
    36452991: "TOI-2969 b",
    207339000: "TOI-4427 b (v0.1 development target)",
    285524410: "TOI-2848.01",
    404610583: "TOI-5966.01",
    95129101: "TOI-1704.01",
}

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


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "refute-calibration/0.2"})
    with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310 - fixed URLs
        return response.read()


# --- drand ---------------------------------------------------------------------------


def round_time(number: int) -> datetime:
    return datetime.fromtimestamp(DRAND_GENESIS + (number - 1) * DRAND_PERIOD, UTC)


def verify_beacon(number: int, beacon: dict[str, Any]) -> int:
    """Verify one drand beacon of the protocol's chain and return the seed (offline).

    Scheme pedersen-bls-chained: the signature is a BLS signature on G2 by the
    chain's public key over sha256(previous_signature || round as 8 big-endian
    bytes), checked with py_ecc's G2Basic ciphersuite, and the randomness must
    equal sha256(signature). The seed is the randomness read as one big-endian
    integer: seed = int(randomness_hex, 16). Raises RuntimeError on any mismatch.
    """
    from py_ecc.bls import G2Basic

    if int(beacon["round"]) != number:
        raise RuntimeError(f"drand returned round {beacon['round']}, expected {number}")
    signature = bytes.fromhex(beacon["signature"])
    message = hashlib.sha256(
        bytes.fromhex(beacon["previous_signature"]) + number.to_bytes(8, "big")
    ).digest()
    if not G2Basic.Verify(bytes.fromhex(DRAND_PUBLIC_KEY), message, signature):
        raise RuntimeError(f"drand round {number}: BLS signature does not verify")
    if hashlib.sha256(signature).hexdigest() != beacon["randomness"]:
        raise RuntimeError(f"drand round {number}: randomness != sha256(signature)")
    return int(beacon["randomness"], 16)


def drand_seed(number: int) -> tuple[int, dict[str, Any]]:
    """Fetch and verify a drand round of the protocol's chain. Raises on any problem."""
    if datetime.now(UTC) < round_time(number):
        raise RuntimeError(
            f"drand round {number} is published at {round_time(number).isoformat()}; "
            "it is not available yet"
        )
    info = json.loads(download(f"{DRAND_URL}/{DRAND_CHAIN_HASH}/info"))
    if info.get("hash") != DRAND_CHAIN_HASH or info.get("public_key") != DRAND_PUBLIC_KEY:
        raise RuntimeError(f"drand chain info does not match the protocol: {info}")
    url = f"{DRAND_URL}/{DRAND_CHAIN_HASH}/public/{number}"
    beacon = json.loads(download(url))
    seed = verify_beacon(number, beacon)
    record = {
        "chain_hash": DRAND_CHAIN_HASH,
        "scheme": info.get("schemeID"),
        "round": number,
        "round_time_utc": round_time(number).isoformat(),
        "url": url,
        "retrieved_utc": utc_now(),
        "randomness": beacon["randomness"],
        "signature": beacon["signature"],
        "previous_signature": beacon["previous_signature"],
        "signature_verified": True,
        "verifier": f"py_ecc {version('py_ecc')} (G2Basic)",
    }
    return seed, record


# --- catalogs ------------------------------------------------------------------------


def tap_url(query: str) -> str:
    return f"{TAP}?{urllib.parse.urlencode({'query': query, 'format': 'csv'})}"


def snapshot(name: str, url: str) -> tuple[bytes, dict[str, Any]]:
    data = download(url)
    if data.lstrip().startswith(b"<?xml"):
        raise RuntimeError(f"query failed for {name}: {data[:500]!r}")
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    (SNAPSHOT_DIR / name).write_bytes(data)
    return data, {
        "file": f"pool_snapshot/{name}",
        "url": url,
        "retrieved_utc": utc_now(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


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


def _rule(table: Any, tic: int, label: str) -> dict[str, Any]:
    rows = [i for i in range(len(table)) if str(table["target_name"][i]).strip() == str(tic)]
    sectors, starts = [], []
    for i in rows:
        match = re.search(r"Sector (\d+)", str(table["mission"][i]))
        sectors.append(int(match.group(1)) if match else None)
        starts.append(float(table["t_min"][i]))
    years = sorted({mjd_year(t) for t in starts})
    span = (max(starts) - min(starts)) if starts else 0.0
    return {
        f"n_{label}": len(rows),
        f"{label}_sectors": sorted(s for s in sectors if s is not None),
        f"{label}_years": years,
        f"{label}_span_days": round(span, 3),
        f"{label}_ok": len(years) >= MIN_YEARS and span >= MIN_SPAN_DAYS,
    }


def mast_availability(tic: int) -> dict[str, Any]:
    """SPOC 120-s light curves AND target pixel files must each meet the data rule."""
    import lightkurve as lk

    query = {"mission": "TESS", "author": "SPOC", "exptime": 120}
    lcs = lk.search_lightcurve(f"TIC {tic}", **query).table
    tpfs = lk.search_targetpixelfile(f"TIC {tic}", **query).table
    out = {
        "service": "MAST via lightkurve search_lightcurve and search_targetpixelfile "
        "(author=SPOC, exptime=120)",
        "retrieved_utc": utc_now(),
        **_rule(lcs, tic, "light_curves"),
        **_rule(tpfs, tic, "pixel_files"),
    }
    out["accepted"] = out["light_curves_ok"] and out["pixel_files_ok"]
    out["reason"] = (
        "accepted"
        if out["accepted"]
        else (
            f"data rule not met: light curves years {out['light_curves_years']} span "
            f"{out['light_curves_span_days']:.0f} d; pixel files years "
            f"{out['pixel_files_years']} span {out['pixel_files_span_days']:.0f} d (need >= "
            f"{MIN_YEARS} years and >= {MIN_SPAN_DAYS:.0f} d for both)"
        )
    )
    return out


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
        print(f"{label} #{position} TIC {tic} {row['_name']}: {decision}", flush=True)
        if mast["accepted"]:
            accepted.append((row, mast))
            if len(accepted) == needed:
                break
    if len(accepted) < needed:
        raise RuntimeError(f"pool exhausted: only {len(accepted)} {label} targets accepted")
    return accepted


# --- eclipsing-binary attachment -----------------------------------------------------


def _verified_snapshot(entry: dict[str, Any]) -> bytes:
    data = (ROOT / entry["file"]).read_bytes()
    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise RuntimeError(f"{entry['file']} does not match its recorded SHA-256")
    return data


def tic_coordinates(tic: int) -> tuple[float, float]:
    from astroquery.mast import Catalogs

    row = Catalogs.query_criteria(catalog="Tic", ID=int(tic))[0]
    return float(row["ra"]), float(row["dec"])


def _separation_arcsec(ra1, dec1, ra2, dec2) -> np.ndarray:
    r1, d1, r2, d2 = map(np.radians, (ra1, dec1, ra2, dec2))
    h = np.sin((d2 - d1) / 2) ** 2 + np.cos(d1) * np.cos(d2) * np.sin((r2 - r1) / 2) ** 2
    return np.degrees(2 * np.arcsin(np.minimum(1.0, np.sqrt(h)))) * 3600.0


def build_eb_attachment(targets: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    """refute-eb-catalog-1 rows within EXTRACT_RADIUS_ARCSEC of the selected targets.

    Gaia DR3 rows are written in full. TESS-EB is not redistributed (maintainer's
    decision, see eb_snapshot/DATA_LICENSE.md): its entries are written as reference
    rows (catalog and identifier only); the analysis resolves them from the local
    snapshot whose content SHA-256 is recorded in the scan file and checked before
    any analysis.
    """
    from refute.packs.tess.ebcatalog import (
        content_sha256,
        parse_tess_eb,
        prepare_external_snapshots,
    )

    snapshots = json.loads((HERE / "eb_snapshot" / "retrieval.json").read_text("utf-8"))
    tess = next(s for s in snapshots if s["catalog_name"] == "TESS-EB")
    gaia = next(s for s in snapshots if s["catalog_name"] == "Gaia-DR3-EB")
    tess_scan = {k: tess[k] for k in TESS_SCAN_KEYS}
    cache_root = ROOT / ".cache"
    prepare_external_snapshots({"snapshots": [tess_scan]}, cache_root, offline=False)
    tess_data = (cache_root / tess["cache_path"]).read_bytes()
    assert content_sha256(tess_data) == tess["content_sha256"]
    tess_table = parse_tess_eb(tess_data)
    tess_keys = sorted(tess_table)
    t_ra = np.array([tess_table[k][0] for k in tess_keys])
    t_dec = np.array([tess_table[k][1] for k in tess_keys])
    t_tic = np.array([int(k.split()[1]) for k in tess_keys])

    gaia_table = np.genfromtxt(
        io.BytesIO(_verified_snapshot(gaia)),
        delimiter=",",
        names=True,
        dtype=[("source_id", "i8"), ("ra", "f8"), ("dec", "f8"), ("frequency", "f8")],
    )
    rows: list[tuple] = []
    per_target = {}
    for target in targets:
        ra, dec = target["coordinates"]["ra_deg"], target["coordinates"]["dec_deg"]
        near_t = set(
            np.nonzero(_separation_arcsec(ra, dec, t_ra, t_dec) <= EXTRACT_RADIUS_ARCSEC)[
                0
            ].tolist()
        )
        near_t |= set(np.nonzero(t_tic == target["tic_id"])[0].tolist())
        for i in sorted(near_t):
            key = tess_keys[i]
            rows.append(("TESS-EB", key, int(t_tic[i]), None, None, None))
        sep_g = _separation_arcsec(ra, dec, gaia_table["ra"], gaia_table["dec"])
        near_g = np.nonzero(sep_g <= EXTRACT_RADIUS_ARCSEC)[0]
        for i in near_g:
            g = gaia_table[i]
            freq = float(g["frequency"])
            per = 1.0 / freq if math.isfinite(freq) and freq > 0 else None
            rows.append(
                (
                    "Gaia-DR3-EB",
                    str(int(g["source_id"])),
                    None,
                    float(g["ra"]),
                    float(g["dec"]),
                    per,
                )
            )
        per_target[target["key"]] = {"tess_eb": len(near_t), "gaia": len(near_g)}
    unique = sorted(set(rows), key=lambda r: (r[0], r[1]))

    def number(value: float | None, fmt: str) -> str:
        return "" if value is None else format(value, fmt)

    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["catalog", "source_id", "tic_id", "ra_deg", "dec_deg", "period_days"])
    for cat, sid, tic, r_ra, r_dec, per in unique:
        writer.writerow(
            [
                cat,
                sid,
                "" if tic is None else tic,
                number(r_ra, ".9f"),
                number(r_dec, ".9f"),
                number(per, ".9g"),
            ]
        )
    meta = {
        "format": "refute-eb-catalog-scan-1",
        "attachment": "eb_catalog.csv (format refute-eb-catalog-1; TESS-EB as reference rows)",
        "radius_arcsec": EXTRACT_RADIUS_ARCSEC,
        "snapshots": [
            {**tess_scan, "rows": tess["rows"]},
            {
                "catalog_name": gaia["catalog_name"],
                "file": gaia["file"],
                "sha256": gaia["sha256"],
                "rows": gaia["rows"],
                "redistributed": True,
            },
        ],
        "rows": len(unique),
        "per_target": per_target,
    }
    return out.getvalue(), meta


TESS_SCAN_KEYS = (
    "catalog_name",
    "file",
    "cache_path",
    "url",
    "parser",
    "content_sha256",
    "redistributed",
)


# --- main ----------------------------------------------------------------------------


def main() -> int:
    seed, drand = drand_seed(TARGET_ROUND)
    known = load_known_targets()

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

    excluded: list[str] = []
    planets = []
    for row in read_csv(planet_data):
        tic = parse_tic(row["tic_id"])
        if tic is None:
            continue
        if tic in known:
            excluded.append(f"planet pool: TIC {tic} {row['pl_name']}")
            continue
        planets.append({**row, "_tic": tic, "_name": row["pl_name"]})
    planets.sort(key=lambda r: (r["_tic"], r["_name"]))
    random.Random(seed).shuffle(planets)

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
        if tic in known:
            excluded.append(f"false-positive pool: TIC {tic} TOI-{row['TOI']}")
            continue
        fps.append({**row, "_tic": tic, "_name": f"TOI-{row['TOI']}"})
    fps.sort(key=lambda r: (r["_tic"], float(r["TOI"])))
    random.Random(seed).shuffle(fps)

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
        targets.append(
            {
                "key": f"TIC-{row['_tic']}",
                "tic_id": row["_tic"],
                "kind": "false_positive",
                "name": row["_name"],
                "published": {
                    "period_days": to_float(row["Period (days)"]),
                    "period_err_days": to_float(row.get("Period (days) err")),
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

    coordinates = []
    for target in targets:
        ra, dec = tic_coordinates(target["tic_id"])
        coordinates.append(
            {
                "key": target["key"],
                "tic_id": target["tic_id"],
                "coordinates": {"ra_deg": ra, "dec_deg": dec},
            }
        )
    eb_text, eb_meta = build_eb_attachment(coordinates)
    (HERE / "eb_catalog.csv").write_bytes(eb_text.encode("utf-8"))
    (HERE / "eb_catalog_scan.json").write_bytes(
        (json.dumps(eb_meta, indent=2, sort_keys=True) + chr(10)).encode("utf-8")
    )

    document = {
        "schema": "refute-tess-targets-1",
        "generated_utc": utc_now(),
        "generator": "calibration/v0.2/select_targets.py",
        "selection": {
            "protocol": "calibration/v0.2/PROTOCOL.md",
            "seed_source": drand,
            "seed": str(seed),
            "excluded_known_targets": sorted(known),
            "planet_filter_adql": PLANET_FILTER,
            "false_positive_filter": (
                "(TFOPWG Disposition == FP) or (TESS Disposition == EB and TFOPWG Disposition "
                "not in {CP, KP, PC, APC}); 0.5 < Period (days) < 10; Depth (ppm) >= 1000; "
                "TESS Mag <= 12; exactly one TOI for the TIC; TIC hosts no planet in pscomppars"
            ),
            "data_rule": (
                f"SPOC 120-s light curves and SPOC 120-s target pixel files, each in >= "
                f"{MIN_YEARS} calendar years with >= {MIN_SPAN_DAYS:.0f} days between first "
                "and last sector start"
            ),
            "pool_sizes": {"planets": len(planets), "false_positives": len(fps)},
            "snapshots": retrieval,
            "eb_attachment": eb_meta,
        },
        "targets": targets,
    }
    (HERE / "targets.yaml").write_bytes(
        yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=100).encode("utf-8")
    )
    header = [
        "# Selection log (v0.2)",
        "",
        f"Generated {document['generated_utc']} by `calibration/v0.2/select_targets.py`",
        "following `calibration/v0.2/PROTOCOL.md`.",
        "",
        "## Seed",
        "",
        f"- drand chain `{drand['chain_hash']}` ({drand['scheme']}), round {drand['round']}, "
        f"published {drand['round_time_utc']}",
        f"- URL: {drand['url']} (retrieved {drand['retrieved_utc']})",
        f"- randomness: `{drand['randomness']}`",
        f"- signature verified with {drand['verifier']}: {drand['signature_verified']}",
        f"- seed = int(randomness, 16) = {seed}",
        "",
        "## Exclusions (the 14 known v0.1 targets found in the pools)",
        "",
        *(f"- {e}" for e in excluded),
        "",
        f"- Planet pool after exclusions: {len(planets)} rows; false-positive pool: {len(fps)}.",
        "",
        "## Candidates, in shuffled order",
        "",
        "| Pool | Position | Target | Name | Decision | Reason |",
        "|---|---|---|---|---|---|",
    ]
    (HERE / "selection_log.md").write_bytes(("\n".join(header + log) + "\n").encode("utf-8"))
    print(f"wrote {len(targets)} targets and {eb_meta['rows']} eb-catalog rows", flush=True)
    return 0


def load_known_targets() -> dict[int, str]:
    """The 14 known targets, checked against calibration/targets.yaml (v0.1)."""
    v01 = yaml.safe_load((ROOT / "calibration" / "targets.yaml").read_text(encoding="utf-8"))
    found = {int(t["tic_id"]) for t in v01["targets"]}
    if found != set(KNOWN_TARGETS):
        raise RuntimeError(f"known-target list does not match calibration/targets.yaml: {found}")
    return dict(KNOWN_TARGETS)


if __name__ == "__main__":
    sys.exit(main())
