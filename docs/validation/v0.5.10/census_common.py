"""Shared helpers of the v0.5.10 censuses (parts (c) and (d)): public catalogs and metadata only,
no light curve or pixel read. Queries are cached under .cache/v0510/census/ so a run resumes; each
query's URL and UTC time are recorded with its result."""

from __future__ import annotations

import csv
import io
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / ".cache/v0510/census"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def tap(name: str, query: str) -> tuple[list[dict], dict]:
    """A NASA Exoplanet Archive TAP query, cached by name; returns rows and provenance."""
    CACHE.mkdir(parents=True, exist_ok=True)
    data_p, meta_p = CACHE / f"{name}.csv", CACHE / f"{name}.meta.json"
    url = TAP + "?" + urllib.parse.urlencode({"query": query, "format": "csv"})
    if not data_p.exists():
        with urllib.request.urlopen(url, timeout=600) as r:
            data_p.write_bytes(r.read())
        meta_p.write_text(json.dumps({"url": url, "retrieved_utc": now()}), "utf-8")
    meta = json.loads(meta_p.read_text("utf-8"))
    rows = list(csv.DictReader(io.StringIO(data_p.read_text("utf-8"))))
    return rows, {"url": meta["url"], "retrieved_utc": meta["retrieved_utc"], "rows": len(rows)}


def tic_of(value: str) -> int | None:
    v = (value or "").replace("TIC", "").strip()
    return int(v) if v.isdigit() else None


def exposed_tics() -> tuple[set[int], dict]:
    """TICs already exposed to Refute: the v0.5.6 part-B exposure scan (its exposed_tics), and every
    tic_id in the run records of v0.5.6 to v0.5.9 (conservative: a TIC in any run record counts)."""
    scan = json.loads((ROOT / "docs/validation/v0.5.6/part-b-exposure.json").read_text("utf-8"))
    out = set(scan["exposed_tics"])
    files = []
    for v in ("v0.5.6", "v0.5.7", "v0.5.8", "v0.5.9"):
        for p in sorted((ROOT / "docs/validation" / v).glob("*.json")):
            text = p.read_text("utf-8", errors="replace")
            if '"tic_id"' not in text:
                continue
            files.append(p.relative_to(ROOT).as_posix())
            _collect(json.loads(text), out)
    return out, {
        "rule": "v0.5.6 part-b-exposure.json exposed_tics, plus every tic_id in the JSON records "
        "of docs/validation/v0.5.6 to v0.5.9",
        "files": files,
        "tics": len(out),
    }


def _collect(obj, out: set[int]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "tic_id" and isinstance(v, (int, str)) and str(v).isdigit():
                out.add(int(v))
            else:
                _collect(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect(v, out)


def mast_targets(name: str, tics: list[int], **criteria) -> tuple[set[int], dict]:
    """The TICs among ``tics`` that have a MAST observation matching ``criteria`` (target_name is
    the TIC number); queried in batches of 200, the result cached per TIC under ``name`` (so a
    later call with another TIC list reuses only what was asked), metadata only."""
    from astroquery.mast import Observations

    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{name}.json"
    done = json.loads(p.read_text("utf-8")) if p.exists() else {"by_tic": {}, "started": now()}
    want = sorted(set(tics))
    todo = [t for t in want if str(t) not in done["by_tic"]]
    for i in range(0, len(todo), 200):
        batch = [str(t) for t in todo[i : i + 200]]
        for attempt in range(3):
            try:
                res = Observations.query_criteria(target_name=batch, **criteria)
                break
            except Exception:  # noqa: BLE001 - retried, then raised
                if attempt == 2:
                    raise
                time.sleep(10)
        names = {str(x) for x in res["target_name"]}
        for t in batch:
            done["by_tic"][t] = t in names
        p.write_text(json.dumps(done), "utf-8")
    have = {t for t in want if done["by_tic"].get(str(t))}
    return have, {
        "criteria": criteria,
        "service": "MAST CAOM via astroquery.mast.Observations",
        "started_utc": done["started"],
        "targets_queried": len(want),
    }


def quantiles(values: list[float]) -> dict:
    v = sorted(x for x in values if x is not None)
    if not v:
        return {"n": 0}

    def q(p):
        return v[min(len(v) - 1, int(round(p * (len(v) - 1))))]

    return {"n": len(v), "p10": q(0.1), "p50": q(0.5), "p90": q(0.9)}


def fnum(x) -> float | None:
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return f if f == f else None
