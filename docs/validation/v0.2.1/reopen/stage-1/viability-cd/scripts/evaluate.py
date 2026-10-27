"""The C/D viability lot's evaluation (README.md, sections 3 to 6 and 9): reads the two sub-lots'
run folders and the committed geometry list, calls ``viability_cd_evaluate.evaluate`` (the code,
plan, configuration, environment and geometry list checked against each manifest), and writes the
result once. No logic of its own; no engine call; nothing generated. The M4 configuration must be
loaded (``REFUTE_M4_CONFIGURATION``, the R_min study's).

  python evaluate.py <viability-c run folder> <viability-d run folder> <out.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(REPO / "docs/validation/v0.2.1/population"))
import viability_cd as vc  # noqa: E402
import viability_cd_evaluate as ev  # noqa: E402


def summary(out: dict) -> dict:
    keep = {}
    for alt, s in out["alternatives"].items():
        keep[alt] = {
            "outcome": s["outcome"],
            "per_noise": {
                noise: {
                    k: x[k]
                    for k in ("n", "missing", "pass", "fail", "pass_r2ktn", "R3_pass")
                    if k in x
                }
                for noise, x in s.get("per_noise", {}).items()
            },
        }
    return {
        "alternatives": keep,
        "destination": out["destination"],
        "steps": {
            k: (None if v is None else {x: v.get(x) for x in ("closure", "succeeds")})
            for k, v in out["steps"].items()
        },  # fmt: skip
        "final": out["final"],
    }


def main(argv: list[str]) -> int:
    if vc.v3.STATE["problem"] is not None:
        raise SystemExit(vc.v3.STATE["problem"])
    run_c, run_d, out_path = Path(argv[0]), Path(argv[1]), Path(argv[2])
    out = ev.evaluate({"viability-c": run_c, "viability-d": run_d}, vc.GEOMETRY_LIST)
    text = vc.x2.record_text(out)
    with open(out_path, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(json.dumps(summary(json.loads(text)), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
