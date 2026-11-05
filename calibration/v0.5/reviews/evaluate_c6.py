"""Exit criterion 6: evaluate a reproduction record (``reproduce.json`` of ``reproduce_c6.py`` or
``deviation/reproduce_c6_mirror.py``) before its result is relied on (Codex's S5 stage review,
2026-11-05: a run's PASS must not rest on its commands' exit codes alone).

The criterion is PASS only when every check holds:

1. the dossier is the one RULE.md fixes for criterion 6: the draw's ``eb-fp-inconclusive``
   dossier (``calibration/v0.5/reviews/draw.json``);
2. the record's own result is PASS and every step exited 0;
3. the instructions' ``uv run refute verify`` ran before ``uv run refute discover``;
4. a ``uv run refute check-dossier <reproduced> --against <the dossier>`` step ran, exited 0,
   and its log has the line ``OK: manifest intact; key results reproduced`` (what
   ``refute.cli.check_dossier_command`` prints on success with ``--against``) and no
   ``integrity:`` or ``difference:`` line (``check-dossier`` requires identical input data
   hashes, identical verdict and test statuses, and key results within a relative 1e-6);
5. for the mirror deviation: exactly one placement step, exited 0, with the content SHA-256
   equal to the claim's; and the added ``refute verify`` after the instructions exited 0.

Usage, from the repository root:
``.venv/Scripts/python.exe calibration/v0.5/reviews/evaluate_c6.py <work-folder>``
Prints the checks as JSON; exit 0 only when the criterion's run is PASS.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

DRAW = Path("calibration/v0.5/reviews/draw.json")
VERIFY = "uv run refute verify calibration/v0.5/claim.yaml"


def evaluate(root: Path, work: Path) -> dict:
    record = json.loads((work / "reproduce.json").read_text(encoding="utf-8"))
    draw = json.loads((root / DRAW).read_text(encoding="utf-8"))["draw"]
    expected = draw["eb-fp-inconclusive"]["drawn"]
    steps = record["steps"]
    commands = [s["command"] for s in steps]
    checks: dict[str, bool] = {}
    checks["dossier_is_the_fixed_one"] = record["dossier"] == expected
    checks["record_result_pass"] = record["result"] == "PASS"
    checks["every_step_exit_0"] = all(s.get("exit") == 0 for s in steps)
    first_discover = next(
        (i for i, c in enumerate(commands) if c.startswith("uv run refute discover")), None
    )
    first_verify = next((i for i, c in enumerate(commands) if c == VERIFY), None)
    checks["verify_before_discover"] = (
        first_discover is not None and first_verify is not None and first_verify < first_discover
    )
    every_check = [s for s in steps if "check-dossier" in s["command"]]
    compare = [
        s
        for s in every_check
        if s["command"].startswith("uv run refute check-dossier")
        and "--against" in s["command"]
        and s["command"].rstrip("/").endswith(f"/{expected}")
    ]
    # exactly one check-dossier call in the whole record, and it is the expected comparison
    checks["check_dossier_ran_and_exit_0"] = (
        len(every_check) == 1 and len(compare) == 1 and compare[0]["exit"] == 0
    )
    log_ok = False
    if len(compare) == 1 and compare[0].get("log"):
        text = (work / compare[0]["log"]).read_text(encoding="utf-8", errors="replace")
        lines = [line.strip() for line in text.splitlines()]
        log_ok = "OK: manifest intact; key results reproduced" in lines and not any(
            line.startswith(("integrity:", "difference:")) for line in lines
        )
    checks["check_dossier_log_ok"] = log_ok
    placements = [s for s in steps if s["command"].startswith("(deviation) place")]
    if "deviation" in record:
        checks["one_placement_exit_0"] = len(placements) == 1 and placements[0]["exit"] == 0
        checks["placement_content_hash_is_the_claims"] = len(placements) == 1 and placements[0].get(
            "content_sha256"
        ) == placements[0].get("claim_content_sha256")
        last_verify = max((i for i, c in enumerate(commands) if c == VERIFY), default=None)
        checks["verify_after_exit_0"] = (
            last_verify is not None
            and first_discover is not None
            and last_verify > first_discover
            and steps[last_verify]["exit"] == 0
        )
    else:
        checks["no_placement"] = not placements
    return {
        "work": work.as_posix(),
        "dossier": record["dossier"],
        "checks": checks,
        "criterion_run": "PASS" if all(checks.values()) else "FAIL",
    }


def main(argv: list[str]) -> int:
    result = evaluate(Path.cwd(), Path(argv[0]))
    print(json.dumps(result, indent=2))
    return 0 if result["criterion_run"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
