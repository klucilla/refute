"""The open Dependabot alerts numbered above a given one (filtered fields only: number, package,
severity, GHSA id and link, summary, patched version, creation time; no configuration), with the
time of reading. python new_alerts.py <after> <out.json>"""

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    after, out = int(sys.argv[1]), Path(sys.argv[2])
    raw = subprocess.run(
        ["gh", "api", "repos/klucilla/refute/dependabot/alerts?state=open&per_page=100"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout
    rows = []
    for a in sorted(json.loads(raw), key=lambda a: a["number"]):
        if a["number"] <= after:
            continue
        adv = a["security_advisory"]
        rows.append(
            {
                "number": a["number"],
                "package": a["dependency"]["package"]["name"],
                "severity": adv["severity"],
                "ghsa": adv["ghsa_id"],
                "url": f"https://github.com/advisories/{adv['ghsa_id']}",
                "summary": adv["summary"],
                "patched": (a["security_vulnerability"].get("first_patched_version") or {}).get(
                    "identifier"
                ),
                "created": a["created_at"],
            }
        )
    payload = {"read_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), "alerts": rows}
    out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8", newline="\n")
    for r in rows:
        print(r["number"], r["package"], r["severity"], r["ghsa"], r["patched"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
