"""The caps ledger of v0.5.10 (Process diet 2, item 4: required above 5 CPU-h).

Sums the CPU of every run the phase log records with ``cpu_seconds`` (the engine and synthetic
runs, measured by a Windows Job object over all their processes), and records the downloads and
the disk peak from the committed records. The project-side scripts of parts (a) to (d), the
catalog staging, the data fetch and the cleanup were not metered; they are listed as such.
Writes caps-ledger.json.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAP = {"cpu_hours": 6.0, "downloads_bytes": 10_000_000_000, "disk_peak_bytes": 10_000_000_000}


def main() -> int:
    runs = {}
    for line in (HERE / "log.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["kind"] == "after" and isinstance(r.get("cpu_seconds"), (int, float)):
            group = r["run"].split(":")[0] if ":" in r["run"] else "synthetic and checks"
            runs.setdefault(group, 0.0)
            runs[group] += float(r["cpu_seconds"])
    cpu = sum(runs.values())
    wheel = json.loads((HERE / "engines/wheelhouse-manifest.json").read_text(encoding="utf-8"))
    data = json.loads((HERE / "engines/data-check.json").read_text(encoding="utf-8"))
    downloads = {
        "wheelhouse": wheel["total_bytes"],
        "light curves and pixel files": data["downloaded_bytes"],
        "catalog staging (TIC, Gaia), measured on disk": 16_384_426,
        "census and route (e) caches, measured on disk": 19_706_986 + 10_019_855,
    }
    disk = {
        ".cache/v0510/data": 5_845_999_680,
        ".cache/v0510/engines": 957_283_811,
        ".cache/v0510/runs": 252_718_111,
        "the rest of .cache/v0510": 16_384_426 + 19_706_986 + 10_019_855 + 2_948_727,
    }
    doc = {
        "schema": "refute-v0510-caps-ledger-1",
        "mode": "exploratory",
        "caps": CAP,
        "cpu_seconds_metered": round(cpu, 1),
        "cpu_hours_metered": round(cpu / 3600, 3),
        "cpu_by_group_seconds": {k: round(v, 1) for k, v in sorted(runs.items())},
        "cpu_not_metered": "parts (a) to (d), the catalog staging, the data fetch, the wheelhouse "
        "and the cleanup ran in the project's environment and were not metered (metadata "
        "queries and hashing; minutes of wall time each)",
        "downloads_bytes": downloads,
        "downloads_total_bytes": sum(downloads.values()),
        "disk_peak_bytes_measured": disk,
        "disk_peak_total_bytes": sum(disk.values()),
        "disk_note": "measured with du -sb after the last engine run, when .cache/v0510 held "
        "everything at once; the first install was hardlinked and took no extra space",
        "within_caps": cpu / 3600 < CAP["cpu_hours"]
        and sum(downloads.values()) < CAP["downloads_bytes"]
        and sum(disk.values()) < CAP["disk_peak_bytes"],
    }
    (HERE / "caps-ledger.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("cpu_hours_metered", "downloads_total_bytes",
                                          "disk_peak_total_bytes", "within_caps")}))  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
