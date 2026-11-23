"""Check part B's draw from public sources: anyone can run it in a clone of the repository.

What it checks (every check of `calibration/v0.5.6/part_b_draw.py`'s `validate_draw`, unchanged):
- the draw names the lock, and its round is the one the locked claim fixed before the lock;
- the beacon's BLS signature verifies against the drand mainnet public key (offline, py_ecc), and
  its randomness is sha256(signature);
- the order of each stratum is rebuilt from the randomness: the stratum sorted by TIC, then
  `random.Random(int(sha256(randomness + '|v0.5.6|part-b|' + stratum), 16)).shuffle`; the trail
  must be its prefix and the chosen TOIs must be rebuilt from the frozen frame and the trail;
- the lock commit is the only commit that touches the lock (from git);
- with the network (the default): the round's time is after the lock commit's CI push run on
  GitHub, and the round read again from the drand network has the draw's randomness.

Usage (from the project root):
    .venv/Scripts/python.exe -B docs/validation/v0.5.6/verify_part_b_draw.py [--offline]

``--offline`` skips the two network checks (GitHub and drand). Exit status 0 when every check
passes, 1 otherwise. It reads no light curve and changes no file.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DRAW_CODE = ROOT / "calibration/v0.5.6/part_b_draw.py"


def draw_module():
    spec = importlib.util.spec_from_file_location("part_b_draw", DRAW_CODE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def main(argv: list[str]) -> int:
    offline = "--offline" in argv
    pbd = draw_module()
    from refute.drand import round_time

    draw = json.loads(pbd.DRAW.read_text("utf-8"))
    beacon = draw["beacon"]
    number = int(beacon["round"])
    print(f"drand round {number}, published at {round_time(number).isoformat()} "
          "(genesis 1595431050 + 30 s x (round - 1))")  # fmt: skip
    print(f"public address: {beacon['url']}")
    print(f"randomness in the draw: {beacon['randomness']}")
    problems = pbd.validate_draw(draw, check_ci=not offline)
    if not offline:
        from refute.drand import drand_seed

        try:
            seed, _ = drand_seed(number)
            if seed != int(beacon["randomness"], 16):
                problems.append("the drand network's randomness differs from the draw's")
            else:
                print("the drand network returns the same randomness")
        except Exception as exc:  # noqa: BLE001 - any failure is a problem
            problems.append(f"the round cannot be read from the drand network: {exc}")
    rows, exposed, _, _ = pbd.frozen_inputs()
    groups = pbd.strata(rows, exposed)
    for s in pbd.STRATA:
        ordered = pbd.order(groups[s], beacon["randomness"], s)
        chosen = draw["arms"][s]["chosen"]
        first = ", ".join(str(r["tic_id"]) for r in ordered[:5])
        print(f"{s}: pool {len(ordered)}, chosen {len(chosen)}; replayed order starts {first}")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(f"- {p}")
        return 1
    print("OK: every check passes" + (" (offline: GitHub and drand not read)" if offline else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
