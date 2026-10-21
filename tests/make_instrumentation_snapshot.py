"""Generate the snapshot of AC5 (docs/validation/v0.2.1/reopen/stage-1/
instrumentation-acceptance.md): for every case of ``instrumentation_cases.cases()``, the
calibration record and the ``run_holdout`` outcome, as JSON, made **with the code before the
instrumentation**, committed with the tests. Run by hand once, never by the suite:

    .venv/Scripts/python.exe tests/make_instrumentation_snapshot.py

It refuses to overwrite an existing snapshot."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from refute.core.io import dumps_json, to_jsonable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import instrumentation_cases as ic  # noqa: E402

OUT = HERE / "fixtures" / "instrumentation_snapshot.json"


def snapshot() -> dict:
    out = {}
    for case in ic.cases():
        with ic.replaced(case):
            record = ic.holdout.calibration_measurement(
                case.lc, case.sectors, case.hidden_year, case.plan, identity=ic.identity(case.plan)
            )
            outcome = ic.holdout.run_holdout(case.lc, case.sectors, case.plan)
        out[case.name] = {
            "row": case.row,
            "record": json.loads(dumps_json(to_jsonable(record))),
            "run_holdout": json.loads(dumps_json(to_jsonable(outcome.to_dict()))),
        }
    return out


def main() -> int:
    if OUT.exists():
        raise SystemExit(f"{OUT} exists; not replaced")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=HERE, capture_output=True, text=True, check=True
    ).stdout.strip()
    # added after Codex's review of the round (the first snapshot recorded HEAD only): the
    # engine's source must be the committed one, and its identity and the environment recorded
    dirty = subprocess.run(
        # from the repository's root (Codex's second review: cwd=tests/ checked tests/src/)
        ["git", "status", "--porcelain", "--", ":(top)src"],
        cwd=HERE.parent,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if dirty:
        raise SystemExit(
            f"src/ has uncommitted changes; the snapshot needs the committed code:\n{dirty}"
        )
    import hashlib
    import platform

    holdout_file = Path(ic.holdout.__file__)
    data = {
        "made_with_commit": head,
        "holdout_sha256": hashlib.sha256(holdout_file.read_bytes()).hexdigest(),
        "environment": [platform.system(), platform.python_version()],
        "cases": snapshot(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(OUT, "cases", len(data["cases"]))
    for name, c in data["cases"].items():
        print(name, c["row"], "|", c["record"].get("stage"), c["record"].get("reason"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
