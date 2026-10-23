"""The CI's consumption since a date (the maintainer's decisions of 2026-10-22, item 4): for every
GitHub Actions run of the repository created on or after it, each job's duration from its start and
end times (public run metadata only, through ``gh``; no configuration is read), the longest job,
and the Actions storage at the time of reading (the caches' count and size, the artifacts kept).
Runner minutes are GitHub's machines, kept apart from the local logical-processor hours. The
account's billing is not read.

  python ci_minutes.py <since YYYY-MM-DD> <out.json>
"""

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def gh(*args: str) -> str:
    return subprocess.run(
        ["gh", *args], capture_output=True, text=True, encoding="utf-8", check=True
    ).stdout


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def main() -> int:
    since, out = sys.argv[1], Path(sys.argv[2])
    runs = json.loads(
        gh(
            "run",
            "list",
            "--limit",
            "1000",
            "--created",
            f">={since}",
            "--json",
            "databaseId,workflowName,headSha,createdAt,conclusion,event",
        )
    )
    rows, total = [], 0.0
    for run in sorted(runs, key=lambda r: r["createdAt"]):
        jobs = json.loads(gh("run", "view", str(run["databaseId"]), "--json", "jobs"))["jobs"]
        minutes = [
            (ts(j["completedAt"]) - ts(j["startedAt"])).total_seconds() / 60
            for j in jobs
            if j.get("startedAt") and j.get("completedAt")
        ]
        rows.append(
            {
                "run": run["databaseId"],
                "workflow": run["workflowName"],
                "sha": run["headSha"],
                "created": run["createdAt"],
                "event": run["event"],
                "conclusion": run["conclusion"],
                "jobs": len(jobs),
                "job_minutes": round(sum(minutes), 2),
                "longest_job_minutes": round(max(minutes), 2) if minutes else None,
            }
        )
        total += sum(minutes)
    longest = [r["longest_job_minutes"] for r in rows if r["longest_job_minutes"] is not None]
    repo = json.loads(gh("repo", "view", "--json", "nameWithOwner"))["nameWithOwner"]
    cache = json.loads(gh("api", f"repos/{repo}/actions/cache/usage"))
    artifacts = json.loads(gh("api", f"repos/{repo}/actions/artifacts", "--jq", "{total_count}"))
    result = {
        "read_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "storage": {
            "active_caches_count": cache.get("active_caches_count"),
            "active_caches_size_in_bytes": cache.get("active_caches_size_in_bytes"),
            "artifacts": artifacts.get("total_count"),
        },
        "billing": "not read (not available to this token's scope)",
        "since": since,
        "runs": len(rows),
        "job_minutes": round(total, 1),
        "longest_job_minutes": max(longest) if longest else None,
        "runs_with_a_job_over_15_minutes": sum(1 for x in longest if x > 15),
        "rows": rows,
    }
    out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(rows)} runs since {since}: {total:.1f} job-minutes ({total / 60:.1f} job-hours)")
    print(
        f"longest job {result['longest_job_minutes']} min; runs with a job over 15 min: "
        f"{result['runs_with_a_job_over_15_minutes']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
