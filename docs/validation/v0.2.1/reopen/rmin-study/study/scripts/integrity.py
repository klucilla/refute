"""Integrity of the R_min study's lot, with the code of the study (wt-v021 at 2e4ff99), writing
nothing there: the lot's problems by rmin_study.lot_problems (Amendment 27, 1 and 3; the
manifest prescribed by lot_manifest("study")), the SHA-256 of every record file, the run reports.

Run with the wt-v021 venv, PYTHONDONTWRITEBYTECODE=1 and REFUTE_M4_CONFIGURATION set to the
study's configuration. Usage: python integrity.py <run folder> <out folder (new)>
"""

import hashlib
import json
import sys
from pathlib import Path

WT = Path("C:/Projetos/refute/.cache/wt-v021")
sys.path.insert(0, str(WT / "docs/validation/v0.2.1/population"))
import rmin_study as rs  # noqa: E402


def main() -> int:
    run_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=False)
    if rs.v3.STATE["problem"] is not None:
        raise SystemExit(f"the M4 configuration is not loaded: {rs.v3.STATE['problem']}")
    plan = rs.v3._plan()
    config_problems = rs.study_configuration_problems(rs.v3.STATE["identity"], plan)
    configuration = rs.v3.STATE["identity"]
    data = rs.load_lot(run_dir)
    problems = rs.lot_problems(run_dir, "study", configuration, data)
    reports = {}
    for path in sorted(run_dir.glob("run-report-*.json")):
        reports[path.name] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "content": json.loads(path.read_text(encoding="utf-8")),
        }
    manifest_file = run_dir / "manifest.json"
    result = {
        "code": "claude/v0-2-1-reopen 2e4ff998ca1596c281abf915222714e1276173f3 (.cache/wt-v021)",
        "configuration_problems": config_problems,
        "lot_problems": problems,
        "expected": len(data["manifest"].get("expected", [])),
        "record_files": len(data["files"]),
        "manifest_file_sha256": hashlib.sha256(manifest_file.read_bytes()).hexdigest(),
        "source": rs._source("study", data),
        "run_reports": reports,
    }
    (out / "integrity.json").write_text(
        json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    (out / "record-digests.json").write_text(
        json.dumps(data["files"], indent=0, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({k: v for k, v in result.items() if k != "run_reports"}, indent=1)[:4000])
    for name, rep in reports.items():
        c = rep["content"]
        print(
            name,
            {
                k: c.get(k)
                for k in (
                    "complete",
                    "dispatched",
                    "submitted",
                    "deadline_reached",
                    "dispatch_error",
                    "elapsed_hours",
                )
            },
            "failures",
            len(c.get("failures", [])),
            "integrity",
            len(c.get("integrity_problems", [])),
        )
    return 0 if not problems and not config_problems else 1


if __name__ == "__main__":
    sys.exit(main())
