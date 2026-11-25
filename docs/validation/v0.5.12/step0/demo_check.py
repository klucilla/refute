"""Check the meter's demonstration (v0.5.12, charter step 0) from the journal and the run outputs.

Reads ``docs/validation/v0.5.12/log.jsonl`` and each demonstration unit's stdout, and writes
``demo-check.json`` (to the run's out folder; the launcher copies it to step0/). Each fixture's
check, and ``passed`` only if every check holds:
- **cpu:** the unit's job CPU covers this process's and its child's own CPU, with 2 processes or
  more;
- **transient:** the job's written bytes cover the 50 MiB written and deleted, and so does the
  bound;
- **retained:** the second retain unit starts with at least 30 MiB more occupancy than the first
  one started with;
- **network:** every attempt failed, from the process and from its child;
- **commit:** the container's commit-check unit committed (status ok).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LOG = ROOT / "docs" / "validation" / "v0.5.12" / "log.jsonl"
MIB = 1 << 20


def main() -> int:
    entries = [json.loads(x) for x in LOG.read_text(encoding="utf-8").splitlines() if x.strip()]
    befores = {e["attempt_id"]: e for e in entries if e["event"] == "before"}
    afters = [e for e in entries if e["event"] == "after"]

    def runs(unit: str, label: str | None = None) -> list[tuple[dict, dict, dict]]:
        out = []
        for a in afters:
            b = befores[a["attempt_id"]]
            if a["unit"] == unit and (label is None or b.get("label") == label):
                run = ROOT / ".cache" / "v0512" / "runs" / f"{unit}__{a['attempt_id'][:12]}"
                text = (run / "stdout.txt").read_text(encoding="utf-8", errors="replace").strip()
                last = json.loads(text.splitlines()[-1]) if text else {}
                out.append((b, a, last))
        return out

    checks = []

    def check(name: str, holds: bool, evidence: dict) -> None:
        checks.append({"check": name, "holds": bool(holds), "evidence": evidence})

    b, a, s = runs("demo", "cpu")[-1]
    child = json.loads(s.get("child") or "{}")
    own = s.get("own_cpu_s", 0) + child.get("child_cpu_s", 0)
    ev = {"job_cpu_s": a["unit_cpu_s"], "own_plus_child_cpu_s": own}
    ev.update({"processes": a["processes"], "launcher_total_cpu_s": a["cpu_s"]})
    check("cpu", a["unit_cpu_s"] >= own - 0.1 and a["processes"] >= 2, ev)

    b, a, s = runs("demo", "transient")[-1]
    w = s.get("written_then_deleted", 0)
    ev = {"written_then_deleted": w, "job_write_bytes": a["write_bytes"], "o_start": b["o_start"]}
    ev.update({"o_end": a["o_end"], "bound": a["disk_bound_bytes"]})
    ok = w >= 50 * MIB and a["write_bytes"] >= w and a["disk_bound_bytes"] >= b["o_start"] + w
    check("transient", ok, ev)

    r1 = runs("demo", "retain-a")[-1]
    r2 = runs("demo", "retain-b")[-1]
    ev = {"retain_a_o_start": r1[0]["o_start"], "retain_a_o_end": r1[1]["o_end"]}
    ev["retain_b_o_start"] = r2[0]["o_start"]
    ok = r2[0]["o_start"] >= r1[0]["o_start"] + 30 * MIB
    check("retained", ok and r1[1]["o_end"] >= r1[0]["o_start"] + 30 * MIB, ev)

    b, a, s = runs("demo", "network")[-1]
    tried = {**s.get("process", {}), **s.get("child", {})}
    ev = {"status": a["status"], "attempts": tried, "sandbox": b["sandbox"]}
    check("network", a["status"] == "ok" and not s.get("succeeded") and len(tried) >= 8, ev)

    commits = [(b, a) for b, a, _ in runs("commit-check")]
    ev = {"commit_check_runs": len(commits)}
    ev["sandbox"] = commits[-1][0]["sandbox"] if commits else None
    check("commit", bool(commits) and commits[-1][1]["status"] == "ok", ev)

    doc = {"schema": "refute-v0512-meter-demo-1", "checks": checks}
    doc["passed"] = all(c["holds"] for c in checks)
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "demo-check.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": doc["passed"], **{c["check"]: c["holds"] for c in checks}}))
    return 0 if doc["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
