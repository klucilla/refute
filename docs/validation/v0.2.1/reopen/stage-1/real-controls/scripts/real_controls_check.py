"""The early check of the real controls' availability (plan B, section 5; gate 3b). Committed with
its declaration (../README.md) before any query. Catalogues and archive metadata only: no light
curve is downloaded or analysed, and nothing here reads an output of the engine.

1. The exclusions: every TIC of calibration/targets.yaml (v0.1, with its development target),
   calibration/v0.2/targets.yaml (v0.2, with its development target and its exclusion list) and
   docs/validation/v0.2.1/reopen/audit-known-targets.json.
2. The catalogues, each saved under .cache/real-controls/ with its URL, time and SHA-256: the NASA
   Exoplanet Archive's pscomppars (confirmed planets) and the ExoFOP-TESS TOI table (dispositions).
3. The pools: the classes and filters of v0.2's protocol (calibration/v0.2/PROTOCOL.md, "Pools"),
   without v0.2's data rule, which the domain replaces. The classes without the period, depth,
   magnitude and multiplicity filters are counted from the catalogues only, as information.
4. For every TIC of the two pools, MAST's SPOC 120-s light curves and target pixel files, searched
   with the arguments the adapter gives lightkurve's search_lightcurve / search_targetpixelfile
   ("TIC <id>", mission TESS, author SPOC, exptime 120; rows kept only when their target_name is
   the TIC). The search calls the body those two wrappers run, lightkurve.search._search_products,
   with the same arguments, because the wrappers turn a failed name resolution into an empty
   result and memoize it. Four searches at a time, each in its own process (astroquery's
   Observations keeps shared parser state). A search raising a network or archive error is retried
   twice, then the TIC is listed with its error and never counted; any other exception (an
   unexpected table, a missing column) stops the check.
5. The screening by metadata (plan B, section 5), on all the TIC's sectors (never a selection of
   three out of more): D1 (exactly three distinct years, each the UTC calendar year of the sector's
   t_min), D2 (exactly three sectors), D3's exposure (120 s, searched; a target pixel file for each
   light-curve sector) and D5 (the two separations between consecutive sectors' t_min, unrounded,
   each 345 to 385 d or 710 to 750 d, at most one long). D3's measured intervals and D4 need the
   products' time stamps and stay pending until the calibration's own selection.

python real_controls_check.py <out.json>   (network; run once, after the declaration's commit)
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
import time
import urllib.parse
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import requests
import yaml

REPO = Path(__file__).resolve().parents[7]
CACHE = REPO / ".cache" / "real-controls"
MINIMUM = 20
ONE_YEAR = (345.0, 385.0)
TWO_YEARS = (710.0, 750.0)
PROCESSES = 4
ATTEMPTS = 3
PSCOMPPARS_URL = (
    "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query="
    + urllib.parse.quote(
        "select pl_name,hostname,tic_id,tran_flag,pl_orbper,pl_trandep,sy_tmag,sy_pnum "
        "from pscomppars"
    )
    + "&format=csv"
)
TOI_URL = "https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv"
SEARCH = {"mission": "TESS", "provenance_name": "SPOC", "exptime": 120}
FILETYPES = {"light_curves": "Lightcurve", "pixel_files": "Target Pixel"}
ROW_COLUMNS = ("target_name", "sequence_number", "obs_id", "t_min", "t_max", "exptime",
               "productFilename")  # fmt: skip
REQUIRED = ("target_name", "sequence_number", "t_min")  # read by the screening; the rest recorded
MJD0 = datetime(1858, 11, 17, tzinfo=UTC)


# --- 1. the exclusions -------------------------------------------------------------------------


def _tic_of(text) -> int | None:
    digits = str(text if text is not None else "").replace("TIC", "").strip()
    return int(digits) if digits.isdigit() else None


def _tics(value) -> set[int]:
    out: set[int] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "tic_id" and _tic_of(item) is not None:
                out.add(_tic_of(item))
            elif key == "excluded_known_targets" and isinstance(item, list):
                out |= {_tic_of(x) for x in item if _tic_of(x) is not None}
            else:
                out |= _tics(item)
    elif isinstance(value, list):
        for item in value:
            out |= _tics(item)
    return out


def exclusions() -> dict[str, list[int]]:
    sources = {}
    for rel in ("calibration/targets.yaml", "calibration/v0.2/targets.yaml"):
        sources[rel] = sorted(_tics(yaml.safe_load((REPO / rel).read_text(encoding="utf-8"))))
    audit = "docs/validation/v0.2.1/reopen/audit-known-targets.json"
    known = json.loads((REPO / audit).read_text(encoding="utf-8"))["targets"]
    sources[audit] = sorted(int(k) for k in known)
    return sources


# --- 2. the catalogues ---------------------------------------------------------------------------


def _utc() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def fetch(url: str, name: str) -> tuple[str, dict]:
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    body = response.content
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / name).write_bytes(body)
    record = {
        "url": url,
        "retrieved_utc": _utc(),
        "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": len(body),
        "cache_path": f".cache/real-controls/{name}",
    }
    return body.decode("utf-8-sig"), record


def _float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# --- 3. the pools ---------------------------------------------------------------------------------


def pools(ps_text: str, toi_text: str, excluded: set[int]) -> dict[str, dict[int, dict]]:
    planets, planets_classes, hosts = {}, {}, set()
    for row in csv.DictReader(io.StringIO(ps_text)):
        tic = _tic_of(row.get("tic_id"))
        if tic is None:
            continue
        hosts.add(tic)
        if row.get("tran_flag") != "1" or tic in excluded:
            continue
        period, depth = _float(row.get("pl_orbper")), _float(row.get("pl_trandep"))
        tmag, npl = _float(row.get("sy_tmag")), _float(row.get("sy_pnum"))
        entry = {"name": row["pl_name"], "period_days": period}
        planets_classes.setdefault(tic, entry)
        if (
            period is not None and 0.5 < period < 10
            and depth is not None and depth >= 0.1
            and tmag is not None and tmag <= 12
            and npl == 1
        ):  # fmt: skip
            planets.setdefault(tic, entry)
    rows = list(csv.DictReader(io.StringIO(toi_text)))
    tois_per_tic: dict[int, int] = {}
    for row in rows:
        tic = _tic_of(row.get("TIC ID"))
        if tic is not None:
            tois_per_tic[tic] = tois_per_tic.get(tic, 0) + 1
    fps, fp_classes = {}, {}
    for row in rows:
        tic = _tic_of(row.get("TIC ID"))
        if tic is None or tic in excluded or tic in hosts:
            continue
        tfop = (row.get("TFOPWG Disposition") or "").strip()
        tess = (row.get("TESS Disposition") or "").strip()
        if not (tfop == "FP" or (tess == "EB" and tfop not in {"CP", "KP", "PC", "APC"})):
            continue
        period, depth = _float(row.get("Period (days)")), _float(row.get("Depth (ppm)"))
        tmag = _float(row.get("TESS Mag"))
        entry = {"name": f"TOI-{row.get('TOI')}", "period_days": period}
        fp_classes.setdefault(tic, entry)
        if (
            period is not None and 0.5 < period < 10
            and depth is not None and depth >= 1000
            and tmag is not None and tmag <= 12
            and tois_per_tic.get(tic) == 1
        ):  # fmt: skip
            fps.setdefault(tic, entry)
    return {
        "planets": planets,
        "false_positives": fps,
        "planets_classes_only": planets_classes,
        "false_positives_classes_only": fp_classes,
    }


# --- 4. MAST's products, as the adapter searches them --------------------------------------------


def _value(item):
    if hasattr(item, "mask") and bool(item.mask):
        return None
    if hasattr(item, "item"):
        item = item.item()
    return item.decode() if isinstance(item, bytes) else item


def _rows(result, tic: int) -> list[dict]:
    """The rows whose target_name is the TIC (the adapter's rule), with the columns recorded."""
    if result is None or len(result.table) == 0:
        return []
    table = result.table
    missing = [c for c in REQUIRED if c not in table.colnames]
    if missing:
        raise KeyError(f"the search table lacks {missing}")
    out = [
        {c: _value(table[c][i]) if c in table.colnames else None for c in ROW_COLUMNS}
        for i in range(len(table))
        if str(table["target_name"][i]).strip() == str(tic)
    ]
    for row in out:  # a masked or invalid value the screening reads is unexpected: fatal
        sector, start = row["sequence_number"], row["t_min"]
        if not isinstance(sector, int | np.integer) or isinstance(sector, bool) or sector <= 0:
            raise ValueError(f"invalid sector {sector!r} in {row}")
        if not isinstance(start, float | int | np.floating) or not math.isfinite(start):
            raise ValueError(f"invalid t_min {start!r} in {row}")
    return out


def _retryable() -> tuple[type[BaseException], ...]:
    import astroquery.exceptions as aqe
    from lightkurve.search import SearchError

    names = ("RemoteServiceError", "TimeoutError", "ResolverError")
    found = tuple(getattr(aqe, n) for n in names if hasattr(aqe, n))
    return (requests.RequestException, OSError, SearchError, *found)


def products(tic: int) -> dict:
    """One TIC's searches, in a worker process: rows, an error after the retries, or fatal."""
    from lightkurve.search import _search_products

    retryable = _retryable()
    query = f"TIC {tic}"
    last = None
    for attempt in range(ATTEMPTS):
        try:
            out = {"retrieved_utc": _utc(), "attempts": attempt + 1}
            for key, filetype in FILETYPES.items():
                out[key] = _rows(_search_products(query, filetype=filetype, **SEARCH), tic)
            return out
        except retryable as exc:
            last = exc
            time.sleep(5.0 * (attempt + 1))
        except Exception as exc:  # noqa: BLE001 - anything unexpected stops the whole check
            return {"fatal": f"{type(exc).__name__}: {exc}"[:500]}
    return {"error": f"{type(last).__name__}: {last}"[:500], "attempts": ATTEMPTS}


# --- 5. the screening by metadata ----------------------------------------------------------------


def _year(mjd: float) -> int:
    return (MJD0 + timedelta(days=mjd)).year


def _starts(rows: list[dict]) -> dict[int, float]:
    out: dict[int, float] = {}
    for row in rows:
        sector, start = int(row["sequence_number"]), float(row["t_min"])
        out[sector] = min(start, out.get(sector, start))
    return out


def screen(found: dict) -> tuple[str | None, dict]:
    """D1, D2, D3's products and D5 on the sectors' metadata: the first condition failing."""
    lcs, tpfs = _starts(found["light_curves"]), _starts(found["pixel_files"])
    sectors = sorted(lcs, key=lambda s: lcs[s])
    starts = [lcs[s] for s in sectors]
    years = [_year(t) for t in starts]
    seps = [b - a for a, b in zip(starts[:-1], starts[1:], strict=True)]
    summary = {
        "sectors": sectors,
        "t_min_mjd": starts,
        "years": years,
        "separations_days": [round(x, 4) for x in seps],
        "pixel_file_sectors": sorted(tpfs),
    }
    if len(set(years)) != 3:
        return "D1", summary
    if len(sectors) != 3:
        return "D2", summary
    if not set(lcs) <= set(tpfs):
        return "D3 products", summary
    long_ = [TWO_YEARS[0] <= x <= TWO_YEARS[1] for x in seps]
    short = [ONE_YEAR[0] <= x <= ONE_YEAR[1] for x in seps]
    if not all(a or b for a, b in zip(long_, short, strict=True)) or sum(long_) > 1:
        return "D5", summary
    return None, summary


def main(argv: list[str]) -> int:
    import astroquery
    import astroquery.mast
    import lightkurve

    started = _utc()
    excluded_sources = exclusions()
    excluded = set().union(*map(set, excluded_sources.values()))
    ps_text, ps_record = fetch(PSCOMPPARS_URL, "pscomppars.csv")
    toi_text, toi_record = fetch(TOI_URL, "exofop_toi.csv")
    pooled = pools(ps_text, toi_text, excluded)
    tics = sorted(set(pooled["planets"]) | set(pooled["false_positives"]))
    print(f"{len(tics)} TICs to search", flush=True)
    with ProcessPoolExecutor(PROCESSES) as pool:
        found = dict(zip(tics, pool.map(products, tics, chunksize=4), strict=True))
    rows_bytes = (json.dumps({str(t): f for t, f in found.items()}, indent=1) + "\n").encode()
    (CACHE / "mast-rows.json").write_bytes(rows_bytes)
    fatal = {str(t): f["fatal"] for t, f in found.items() if "fatal" in f}
    errors = {str(t): f["error"] for t, f in found.items() if "error" in f}
    times = sorted(f["retrieved_utc"] for f in found.values() if "retrieved_utc" in f)
    result = {
        "format": "refute-v0.2.1-real-controls-check/1",
        "started_utc": started,
        "finished_utc": _utc(),
        "minimum_per_class": MINIMUM,
        "sources": {
            "pscomppars": ps_record,
            "exofop_toi": toi_record,
            "mast": {
                "server": str(astroquery.mast.conf.server),
                "client": "lightkurve.search._search_products (the body of search_lightcurve and "
                "search_targetpixelfile), astroquery.mast.Observations",
                "arguments": {"target": "TIC <id>", **SEARCH, "filetype": list(FILETYPES.values())},
                "match": "target_name equal to the TIC",
                "first_search_utc": times[0] if times else None,
                "last_search_utc": times[-1] if times else None,
                "rows_file": ".cache/real-controls/mast-rows.json",
                "rows_sha256": hashlib.sha256(rows_bytes).hexdigest(),
            },
        },
        "versions": {"lightkurve": lightkurve.__version__, "astroquery": astroquery.__version__},
        "exclusions": {"by_source": excluded_sources, "union": sorted(excluded)},
        "searched_tics": len(tics),
        "search_errors": errors,
        "fatal_errors": fatal,
        "information_classes_only": {
            name: len(pooled[name])
            for name in ("planets_classes_only", "false_positives_classes_only")
        },
        "pools": {},
    }
    for name in ("planets", "false_positives"):
        rows, fails = [], {}
        for tic, entry in sorted(pooled[name].items()):
            if "light_curves" not in found[tic]:
                fails["search error"] = fails.get("search error", 0) + 1
                continue
            try:
                failed, summary = screen(found[tic])
            except Exception as exc:  # noqa: BLE001 - unexpected: the check stops, recorded
                fatal[str(tic)] = f"screening: {type(exc).__name__}: {exc}"[:500]
                continue
            if failed is None:
                rows.append({"tic_id": tic, **entry, **summary})
            else:
                fails[failed] = fails.get(failed, 0) + 1
        result["pools"][name] = {
            "candidates": len(pooled[name]),
            "inside_by_metadata": len(rows),
            "failing_first": dict(sorted(fails.items())),
            "eligible": rows,
        }
    counts = [result["pools"][n]["inside_by_metadata"] for n in ("planets", "false_positives")]
    result["minimum_reached"] = not fatal and min(counts) >= MINIMUM
    result["outcome"] = (
        "stopped by an unexpected error (no result)" if fatal
        else "minimum reached" if result["minimum_reached"]
        else "short, with search errors (incomplete)" if errors
        else "short"
    )  # fmt: skip
    Path(argv[1]).write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
    brief = {n: {k: v for k, v in p.items() if k != "eligible"} for n, p in result["pools"].items()}
    print(json.dumps(brief, indent=1))
    print("outcome:", result["outcome"], "| search errors:", len(errors), "| fatal:", len(fatal))
    return 1 if fatal else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
