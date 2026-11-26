"""Check the meter's demonstration over its five fixtures (v0.5.12, charter step 0), version 3:
approved by the maintainer's decision of 2026-11-26 (#218, comment 7190454518), item 1.
``demo_check2.py`` is not edited (rule (c)); see ``demo-check2-findings.md`` for its defect.

The five checks and the records are those of ``demo_check2.py``. One change: it reads a unit's
stdout as JSON only for the units that print JSON (``demo`` and ``demo-net2``). For
``commit-check`` it uses the journal's ``after`` entry alone. The repetitions are identified by
their recorded approval (``repetition_approval`` in their ``before`` entry):
- **cpu, retained:** the original ``demo`` attempts (labels cpu, retain-a, retain-b);
- **transient:** the approved repetition of ``demo`` labelled transient;
- **network:** the ``demo-net2`` attempt. Every counted attempt failed, from the process and its
  child, and the launcher's outside listener accepted 0 connections;
- **commit:** the approved repetition of ``commit-check``, run by ``launch_v2.py`` in the
  container.

It writes ``demo-check3.json`` (copied by the launcher to step0/). ``passed`` holds only if every
check holds.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LOG = ROOT / "docs" / "validation" / "v0.5.12" / "log.jsonl"
MIB = 1 << 20
JSON_UNITS = {"demo", "demo-net2"}


def main() -> int:
    entries = [json.loads(x) for x in LOG.read_text(encoding="utf-8").splitlines() if x.strip()]
    befores = {e["attempt_id"]: e for e in entries if e["event"] == "before"}
    afters = [e for e in entries if e["event"] == "after"]

    def runs(unit: str, label: str | None = None, approved: bool | None = None) -> list:
        out = []
        for a in afters:
            b = befores[a["attempt_id"]]
            if a["unit"] != unit or (label is not None and b.get("label") != label):
                continue
            if approved is not None and bool(b.get("repetition_approval")) != approved:
                continue
            last = {}
            if unit in JSON_UNITS:
                run = ROOT / ".cache" / "v0512" / "runs" / f"{unit}__{a['attempt_id'][:12]}"
                text = (run / "stdout.txt").read_text(encoding="utf-8", errors="replace").strip()
                last = json.loads(text.splitlines()[-1]) if text else {}
            out.append((b, a, last))
        return out

    checks = []

    def check(name: str, holds: bool, evidence: dict) -> None:
        checks.append({"check": name, "holds": bool(holds), "evidence": evidence})

    b, a, s = runs("demo", "cpu", approved=False)[0]
    child = json.loads(s.get("child") or "{}")
    own = s.get("own_cpu_s", 0) + child.get("child_cpu_s", 0)
    ev = {"attempt": a["attempt_id"], "job_cpu_s": a["unit_cpu_s"], "own_plus_child_cpu_s": own}
    ev["processes"] = a["processes"]
    check("cpu", a["unit_cpu_s"] >= own - 0.1 and a["processes"] >= 2, ev)

    b, a, s = runs("demo", "transient", approved=True)[-1]
    w = s.get("written_then_deleted", 0)
    ev = {"attempt": a["attempt_id"], "written_then_deleted": w}
    ev.update({"job_write_bytes": a["write_bytes"], "o_start": b["o_start"]})
    ev.update({"o_end": a["o_end"], "bound": a["disk_bound_bytes"]})
    ok = a["status"] == "ok" and w >= 50 * MIB and a["write_bytes"] >= w
    check("transient", ok and a["disk_bound_bytes"] >= b["o_start"] + w, ev)

    r1 = runs("demo", "retain-a", approved=False)[0]
    r2 = runs("demo", "retain-b", approved=False)[0]
    ev = {"retain_a_o_start": r1[0]["o_start"], "retain_a_o_end": r1[1]["o_end"]}
    ev["retain_b_o_start"] = r2[0]["o_start"]
    ok = r2[0]["o_start"] >= r1[0]["o_start"] + 30 * MIB
    check("retained", ok and r1[1]["o_end"] >= r1[0]["o_start"] + 30 * MIB, ev)

    b, a, s = runs("demo-net2")[-1]
    counted = s.get("counted", {})
    ev = {"attempt": a["attempt_id"], "status": a["status"], "counted": counted}
    ev["information"] = s.get("information")
    ev["listener_accepted"] = a.get("listener_accepted")
    ok = a["status"] == "ok" and not s.get("succeeded") and len(counted) >= 8
    check("network", ok and a.get("listener_accepted") == 0, ev)

    commits = runs("commit-check", approved=True)
    ev = {"approved_commit_check_runs": len(commits)}
    if commits:
        b, a, _ = commits[-1]
        ev.update({"attempt": a["attempt_id"], "launcher": b.get("launcher")})
        ev.update({"sandbox": b.get("sandbox"), "status": a["status"]})
    ok = bool(commits) and commits[-1][1]["status"] == "ok"
    check("commit", ok and commits[-1][0].get("launcher") == "launch_v2.py", ev)

    doc = {"schema": "refute-v0512-meter-demo-3", "checks": checks}
    doc["passed"] = all(c["holds"] for c in checks)
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "demo-check3.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": doc["passed"], **{c["check"]: c["holds"] for c in checks}}))
    return 0 if doc["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
