"""Check, from the job logs of one CI run, that the shards ran every test exactly once.

v0.5.1 WP6 (#210; docs/plans/v0.5.1-plan.md, section 8). Each test job prints its JUnit test IDs
(``scripts/junit_counts.py --ids``: a line ``ids <count> <sha256>``, then ``id <test id>`` lines).
This script reads the logs of a run (``gh run view <run> --log``, read only), groups the jobs by
matrix entry (OS and Python: the job name without its shard), and reports for each entry: the
shards found, the test IDs of each, any ID that appears in two shards or twice in one, and the
union's size and SHA-256. With ``--reference <run>``, the union of each entry is compared with the
same entry of the reference run (the IDs added and removed are printed).

Exit code 0 when every entry has every shard of the matrix, no ID twice and, with a reference,
no ID removed; 1 otherwise.

Usage: .venv/Scripts/python.exe scripts/ci_ids_check.py <run id> [--reference <run id>]
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import defaultdict

SHARDS = ("heavy-a", "heavy-b", "heavy-c", "heavy-d", "heavy-e", "heavy-f", "rest")


def _gh(*args: str) -> str:
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout


def job_ids(run: str) -> dict[str, dict[str, list[str]]]:
    """{matrix entry: {shard: [test ids]}} from the run's logs, read job by job (``gh`` refuses
    the whole log of a run with many jobs)."""
    jobs = json.loads(_gh("run", "view", run, "--json", "jobs"))["jobs"]
    log = "\n".join(_gh("run", "view", "--job", str(j["databaseId"]), "--log") for j in jobs)
    out: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    # each log line: "<job name>\t<step name>\t<timestamp> <message>"
    for line in log.splitlines():
        job, _, rest = line.partition("\t")
        _, _, text = rest.partition("\t")
        message = text.split(" ", 1)[1] if " " in text else ""
        if not message.startswith("id "):
            continue
        entry, _, shard = job.rpartition(" / ")
        out[entry][shard].append(message[3:].strip())
    return out


def union_digest(ids: list[str]) -> str:
    return hashlib.sha256("".join(f"{i}\n" for i in sorted(ids)).encode("utf-8")).hexdigest()


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    run, reference = argv[0], None
    if len(argv) == 3 and argv[1] == "--reference":
        reference = argv[2]
    elif len(argv) != 1:
        print(__doc__)
        return 2
    entries = job_ids(run)
    ref_entries = job_ids(reference) if reference else {}
    ok = bool(entries)
    for entry, shards in sorted(entries.items()):
        seen: dict[str, int] = defaultdict(int)
        for ids in shards.values():
            for i in ids:
                seen[i] += 1
        twice = sorted(i for i, n in seen.items() if n > 1)
        missing = [s for s in SHARDS if s not in shards]
        union = sorted(seen)
        print(f"{entry}: shards {len(shards)}, ids {len(union)}, sha256 {union_digest(union)}")
        for s in missing:
            print(f"  missing shard: {s}")
        for i in twice:
            print(f"  twice: {i}")
        ok = ok and not missing and not twice
        if reference:
            ref = {i for ids in ref_entries.get(entry, {}).values() for i in ids}
            removed = sorted(ref - set(union))
            added = sorted(set(union) - ref)
            print(f"  against {reference}: added {len(added)}, removed {len(removed)}")
            for i in removed:
                print(f"  removed: {i}")
            ok = ok and not removed and bool(ref)
    print("OK" if ok else "NOT OK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
