"""The literature reference of each pscomppars value used by the v0.5 C3 planets.

The frozen input `calibration/v0.5/inputs/pscomppars.csv` (retrieved 2026-11-04, SHA-256 in
`calibration/v0.5/inputs.json`) does not hold the reference columns of the NASA Exoplanet
Archive's Planetary Systems Composite Parameters table, and the archive asks that a value taken
from a specific paper be acknowledged through that paper. This script is the maintainer's answer
of 2026-11-06 (#199): the frozen file does not change; a new query of the same table returns,
for the planets of the locked C3 claim (`calibration/v0.5/claim-targets.yaml`, kind `planet`:
the drawn planets, the reserves and the substitute), each used value with the table's own
reference column, and records the query URL, the time, the bytes and the SHA-256.

The reference columns (`*_reflink`, `disc_refname`) were checked on 2026-11-06 in the archive's
column documentation (https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html) and in
its TAP schema (`TAP_SCHEMA.columns`, table `pscomppars`). The schema has no reference column of
its own for `pl_orbpererr1` or `dec`: the script reports for them the period's reference
(`pl_orbper_reflink`) and the position's reference column (`ra_reflink`, described by the archive
as "RA Reference"). That pairing is the agent's inference, not a reference the archive gives for
those two columns.

The run of 2026-11-06T11:22:34Z returned all 11 planets and a reference for every used value. The
check that stops before writing when a planet or a reference is missing (the maintainer's
decision) was added to this script after that run, on a Codex review; the run met it.

The table is updated by the archive: a value of today may differ from the frozen one. For each
planet and each used value, the record says whether today's value equals the frozen value; where
it does not, today's reference is the reference of today's value, not of the frozen one.

Run: .venv/Scripts/python.exe calibration/v0.5/inputs-references/fetch_references.py
It refuses to overwrite an existing output.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FROZEN = ROOT / "calibration" / "v0.5" / "inputs" / "pscomppars.csv"
TARGETS = ROOT / "calibration" / "v0.5" / "claim-targets.yaml"
OUT_CSV = HERE / "pscomppars-references.csv"
OUT_JSON = HERE / "pscomppars-references.json"
TAP = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
DOCS = "https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html"

# Each value column of the frozen query, with the column that gives its reference in pscomppars.
VALUE_REFERENCES = {
    "pl_orbper": "pl_orbper_reflink",
    "pl_orbpererr1": "pl_orbper_reflink",
    "pl_tranmid": "pl_tranmid_reflink",
    "pl_trandep": "pl_trandep_reflink",
    "pl_trandur": "pl_trandur_reflink",
    "sy_tmag": "sy_tmag_reflink",
    "ra": "ra_reflink",
    "dec": "ra_reflink",
}
# Columns of the frozen query that have no reference column in the table (identifiers, flags
# and counts kept by the archive itself).
NO_REFERENCE_COLUMN = ["pl_name", "hostname", "tic_id", "tran_flag", "sy_pnum"]


def planets() -> list[str]:
    data = yaml.safe_load(TARGETS.read_text(encoding="utf-8"))
    names = [t["name"] for t in data["targets"] if t["kind"] == "planet"]
    if len(names) != len(set(names)) or not names:
        raise SystemExit("unexpected planet list in claim-targets.yaml")
    return names


def query_url(names: list[str]) -> str:
    columns = []
    for value, ref in VALUE_REFERENCES.items():
        columns.append(value)
        if ref not in columns:
            columns.append(ref)
    columns = ["pl_name", "hostname", "tic_id", *columns, "disc_refname"]
    quoted = ",".join("'" + n.replace("'", "''") + "'" for n in names)
    adql = (
        f"select {','.join(columns)} from pscomppars where pl_name in ({quoted}) order by pl_name"
    )
    return TAP + "?" + urllib.parse.urlencode({"query": adql, "format": "csv"})


def same(a: str, b: str) -> bool:
    a, b = a.strip(), b.strip()
    if a == "" or b == "":
        return a == b
    try:
        return float(a) == float(b)
    except ValueError:
        return a == b


def main() -> int:
    for out in (OUT_CSV, OUT_JSON):
        if out.exists():
            raise SystemExit(f"refusing to overwrite {out.relative_to(ROOT).as_posix()}")
    names = planets()
    url = query_url(names)
    request = urllib.request.Request(url, headers={"User-Agent": "refute-calibration"})
    retrieved = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    with urllib.request.urlopen(request, timeout=120) as response:
        body = response.read()
    rows = list(csv.DictReader(io.StringIO(body.decode("utf-8"))))
    by_name = {r["pl_name"]: r for r in rows}
    missing = [n for n in names if n not in by_name]
    frozen = {r["pl_name"]: r for r in csv.DictReader(FROZEN.open(encoding="utf-8", newline=""))}
    planets_record = []
    for name in names:
        row = by_name.get(name)
        old = frozen.get(name)
        if row is None or old is None:
            planets_record.append(
                {"pl_name": name, "returned": row is not None, "in_frozen": old is not None}
            )
            continue
        values = []
        for value, ref in VALUE_REFERENCES.items():
            values.append(
                {
                    "column": value,
                    "frozen": old[value],
                    "today": row[value],
                    "same_as_frozen": same(old[value], row[value]),
                    "reference_column": ref,
                    "reference": row[ref],
                }
            )
        planets_record.append(
            {
                "pl_name": name,
                "returned": True,
                "in_frozen": True,
                "disc_refname": row["disc_refname"],
                "values": values,
            }
        )
    empty_refs = [
        f"{p['pl_name']}:{v['column']}"
        for p in planets_record
        if p.get("values")
        for v in p["values"]
        if v["frozen"].strip() and not v["reference"].strip()
    ]
    if missing or empty_refs:
        # The maintainer's decision: if the query does not return the references, stop.
        raise SystemExit(
            f"refusing to write: planets missing {missing}; used values without a reference "
            f"{empty_refs}"
        )
    OUT_CSV.write_bytes(body)
    record = {
        "schema": "refute-v05-pscomppars-references-1",
        "decision": "the maintainer, 2026-11-06 (#199)",
        "table": "NASA Exoplanet Archive, Planetary Systems Composite Parameters (pscomppars)",
        "query_url": url,
        "retrieved_utc": retrieved,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "file": OUT_CSV.name,
        "column_names_checked_in": [DOCS, "TAP_SCHEMA.columns where table_name = 'pscomppars'"],
        "frozen_input": {
            "path": "calibration/v0.5/inputs/pscomppars.csv",
            "sha256": hashlib.sha256(FROZEN.read_bytes()).hexdigest(),
            "retrieved_utc": "2026-11-04T13:07:54Z (calibration/v0.5/inputs.json)",
        },
        "planets_source": "calibration/v0.5/claim-targets.yaml, targets of kind planet",
        "value_reference_columns": VALUE_REFERENCES,
        "columns_without_a_reference_column": NO_REFERENCE_COLUMN,
        "planets": planets_record,
        "summary": {
            "planets": len(names),
            "returned": len(names) - len(missing),
            "missing": missing,
            "values": sum(len(p.get("values", [])) for p in planets_record),
            "values_changed_since_frozen": sum(
                1 for p in planets_record for v in p.get("values", []) if not v["same_as_frozen"]
            ),
            "used_values_without_a_reference": empty_refs,
        },
    }
    OUT_JSON.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(record["summary"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
