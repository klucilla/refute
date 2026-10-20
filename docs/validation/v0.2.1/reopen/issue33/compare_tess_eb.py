"""Read-only comparison of two copies of the TESS-EB catalog (Prsa et al. 2022, ApJS 258, 16),
for issue #33 (the maintainer's decision of 2026-10-17, item 8): is the MAST high-level science
product v1.0 semantically equivalent to the VizieR snapshot that the v0.2 calibration uses?

The identity of a row is (TIC, signal): ``tess_id`` and ``signal_id`` in the MAST file, ``TIC`` and
``m_TIC`` in VizieR (``refute.packs.tess.ebcatalog.parse_tess_eb`` keys it as ``TIC <tic> (<m>)``).
Nothing is compared by line order or by bytes of the files.

Checks, each reported in the output:
1. The VizieR file has the content SHA-256 recorded by the v0.2 calibration
   (``calibration/v0.2/eb_snapshot/retrieval.json``), so it is that snapshot.
2. Its header and units line (VizieR's own description of the columns).
3. The keys: count, duplicates in each copy (a duplicate would be overwritten by the parser), keys
   only in one copy, and every TIC's set of signals.
4. For every common key: the period (missing in either, absolute and relative difference), the
   coordinates (the separation in arcsec), and the number of decimals of each value (precision).
5. The view the gauntlet consumes: ``parse_tess_eb`` applied to the VizieR bytes, against the same
   mapping built from the MAST file as floats, and the reference rows of the v0.2 claim
   (``calibration/v0.2/eb_catalog.csv``) in both.

Usage: uv run python docs/validation/v0.2.1/reopen/issue33/compare_tess_eb.py <vizier.tsv>
           <mast_cat.csv> <out.json>
The output is written once (never overwritten). Exit code 0 if the script ran; the verdict is in
the output.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
from pathlib import Path

from refute.packs.tess.ebcatalog import parse_tess_eb, vizier_content

ROOT = Path(__file__).resolve().parents[5]
RETRIEVAL = ROOT / "calibration" / "v0.2" / "eb_snapshot" / "retrieval.json"
V02_CATALOG = ROOT / "calibration" / "v0.2" / "eb_catalog.csv"
LIST_CAP = 50


def decimals(text: str) -> int | None:
    text = text.strip()
    if not text:
        return None
    mantissa = text.lower().split("e")[0]
    return len(mantissa.split(".")[1]) if "." in mantissa else 0


def separation_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    c = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(r1 - r2)
    return math.degrees(math.acos(max(-1.0, min(1.0, c)))) * 3600.0


def read_vizier(data: bytes) -> tuple[list[str], list[str], dict, list]:
    lines = vizier_content(data).decode("utf-8").splitlines()
    header = lines[0].split("\t")
    units = lines[1].split("\t")
    rows, duplicates = {}, []
    for line in lines[3:]:
        tic, m, ra, dec, per = (f.strip() for f in line.split("\t"))
        key = (int(tic), int(m))
        if key in rows:
            duplicates.append(key)
        rows[key] = {"ra": ra, "dec": dec, "period": per}
    return header, units, rows, duplicates


def read_mast(data: bytes) -> tuple[dict, list]:
    reader = csv.DictReader(io.StringIO(data.decode("utf-8")))
    rows, duplicates = {}, []
    for row in reader:
        key = (int(row["tess_id"]), int(row["signal_id"]))
        if key in rows:
            duplicates.append(key)
        rows[key] = {"ra": row["ra"], "dec": row["dec"], "period": row["period"]}
    return rows, duplicates


def as_float(text: str) -> float | None:
    text = text.strip()
    return float(text) if text else None


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    vizier_path, mast_path, out = Path(argv[0]), Path(argv[1]), Path(argv[2])
    if out.exists():
        print(f"refusing to overwrite {out}")
        return 1
    vizier_bytes, mast_bytes = vizier_path.read_bytes(), mast_path.read_bytes()
    recorded = next(
        r
        for r in json.loads(RETRIEVAL.read_text(encoding="utf-8"))
        if r["catalog_name"] == "TESS-EB"
    )
    content = hashlib.sha256(vizier_content(vizier_bytes)).hexdigest()
    header, units, viz, viz_dup = read_vizier(vizier_bytes)
    mast, mast_dup = read_mast(mast_bytes)

    only_viz = sorted(set(viz) - set(mast))
    only_mast = sorted(set(mast) - set(viz))
    common = sorted(set(viz) & set(mast))
    signals_viz, signals_mast = {}, {}
    for tic, m in viz:
        signals_viz.setdefault(tic, set()).add(m)
    for tic, m in mast:
        signals_mast.setdefault(tic, set()).add(m)
    tic_signal_diff = sorted(
        t for t in set(signals_viz) | set(signals_mast) if signals_viz.get(t) != signals_mast.get(t)
    )

    period_missing = {"vizier_only": [], "mast_only": [], "both": []}
    period_diffs, separations, precision = [], [], {"vizier": {}, "mast": {}}
    beyond_rounding = []  # differences larger than half a unit of the less precise copy
    for key in common:
        v, m = viz[key], mast[key]
        for field in ("ra", "dec", "period"):
            a, b = as_float(v[field]), as_float(m[field])
            if a is None or b is None:
                continue
            places = min(decimals(v[field]), decimals(m[field]))
            bound = 0.5 * 10.0 ** (-places) * (1.0 + 1e-9) + 1e-15 * max(abs(a), abs(b))
            if abs(a - b) > bound:
                beyond_rounding.append(
                    {"key": list(key), "field": field, "vizier": v[field], "mast": m[field]}
                )
        pv, pm = as_float(v["period"]), as_float(m["period"])
        if pv is None and pm is None:
            period_missing["both"].append(key)
        elif pv is None:
            period_missing["vizier_only"].append(key)
        elif pm is None:
            period_missing["mast_only"].append(key)
        else:
            period_diffs.append((abs(pv - pm) / pm if pm else math.inf, abs(pv - pm), key))
        separations.append(
            (
                separation_arcsec(float(v["ra"]), float(v["dec"]), float(m["ra"]), float(m["dec"])),
                key,
            )
        )
        for name, row in (("vizier", v), ("mast", m)):
            for field in ("ra", "dec", "period"):
                d = decimals(row[field])
                bucket = precision[name].setdefault(field, {})
                bucket[str(d)] = bucket.get(str(d), 0) + 1

    # The gauntlet's view: the parser on the VizieR bytes, and the same mapping from MAST.
    gauntlet_viz = parse_tess_eb(vizier_bytes)
    gauntlet_mast = {
        f"TIC {tic} ({m})": (float(r["ra"]), float(r["dec"]), as_float(r["period"]))
        for (tic, m), r in mast.items()
    }
    view_keys_equal = set(gauntlet_viz) == set(gauntlet_mast)

    def view_diff(key: str) -> dict:
        a, b = gauntlet_viz.get(key), gauntlet_mast.get(key)
        if a is None or b is None:
            return {"key": key, "vizier": a, "mast": b}
        sep = separation_arcsec(a[0], a[1], b[0], b[1])
        rel = None if a[2] is None or b[2] is None else abs(a[2] - b[2]) / b[2]
        return {"key": key, "separation_arcsec": sep, "period_relative_difference": rel}

    references = []
    for line in V02_CATALOG.read_text(encoding="utf-8").splitlines()[1:]:
        fields = line.split(",")
        if fields and fields[0] == "TESS-EB":
            references.append(view_diff(fields[1]))

    period_diffs.sort(reverse=True)
    separations.sort(reverse=True)
    report = {
        "vizier": {
            "file": vizier_path.name,
            "content_sha256": content,
            "recorded_content_sha256": recorded["content_sha256"],
            "is_the_v02_snapshot": content == recorded["content_sha256"],
            "header": header,
            "units": units,
            "rows": len(viz),
            "duplicate_keys": [list(k) for k in viz_dup],
        },
        "mast": {
            "file": mast_path.name,
            "sha256": hashlib.sha256(mast_bytes).hexdigest(),
            "rows": len(mast),
            "duplicate_keys": [list(k) for k in mast_dup],
        },
        "keys": {
            "common": len(common),
            "only_vizier": [list(k) for k in only_viz[:LIST_CAP]],
            "only_vizier_count": len(only_viz),
            "only_mast": [list(k) for k in only_mast[:LIST_CAP]],
            "only_mast_count": len(only_mast),
            "tics_whose_signal_sets_differ": tic_signal_diff[:LIST_CAP],
            "tics_whose_signal_sets_differ_count": len(tic_signal_diff),
            "tics_with_more_than_one_signal_vizier": sum(
                1 for s in signals_viz.values() if len(s) > 1
            ),
            "tics_with_more_than_one_signal_mast": sum(
                1 for s in signals_mast.values() if len(s) > 1
            ),
        },
        "period": {
            "missing": {k: [list(x) for x in v[:LIST_CAP]] for k, v in period_missing.items()},
            "missing_counts": {k: len(v) for k, v in period_missing.items()},
            "max_relative_difference": period_diffs[0][0] if period_diffs else None,
            "max_absolute_difference_days": max((d[1] for d in period_diffs), default=None),
            "largest": [
                {"key": list(k), "relative": r, "absolute_days": a} for r, a, k in period_diffs[:20]
            ],
            "count_relative_above_1e-6": sum(1 for d in period_diffs if d[0] > 1e-6),
            "count_relative_above_1e-3": sum(1 for d in period_diffs if d[0] > 1e-3),
        },
        "coordinates": {
            "max_separation_arcsec": separations[0][0] if separations else None,
            "largest": [{"key": list(k), "arcsec": s} for s, k in separations[:20]],
            "count_above_0.1_arcsec": sum(1 for s in separations if s[0] > 0.1),
            "count_above_1_arcsec": sum(1 for s in separations if s[0] > 1.0),
        },
        "precision_decimals": precision,
        "rounding": {
            "rule": "for every common key and each of ra, dec and period present in both, "
            "|vizier - mast| <= half a unit of the last decimal of the less precise copy",
            "differences_beyond_rounding_count": len(beyond_rounding),
            "differences_beyond_rounding": beyond_rounding[:LIST_CAP],
        },
        "gauntlet_view": {
            "keys_equal": view_keys_equal,
            "vizier_keys": len(gauntlet_viz),
            "mast_keys": len(gauntlet_mast),
            "v02_reference_rows": references,
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({k: report[k] for k in ("keys",)}, indent=1)[:2000])
    print("vizier is the v0.2 snapshot:", report["vizier"]["is_the_v02_snapshot"])
    print("period max rel diff:", report["period"]["max_relative_difference"])
    print("max separation arcsec:", report["coordinates"]["max_separation_arcsec"])
    print("beyond rounding:", report["rounding"]["differences_beyond_rounding_count"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
