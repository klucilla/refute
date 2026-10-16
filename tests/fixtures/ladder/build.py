"""Synthetic build of one rung of the build ladder (WP3 W3.9 under the subprocess backend,
design A' of the maintainer's review of 2026-10-16): a cataloged fixture
(src/refute/packs/ml/synthetic.py) that plays the build of a rung in CI, where no image
can be built.

    build.py RUNG PYTHON

``ladder.json`` (a data file the harness writes) maps each rung to what this build does:

- ``ok``: writes ``out/built-<rung>.txt`` and exits 0;
- ``procedure_error``: prints the deliberate failure line and exits 86 (the deliberate,
  recognised and expected failure of the fixture);
- ``crash``: raises an exception (exit 1: an unexpected failure);
- ``exit86``: exits 86 without the deliberate failure line (an unexpected failure that
  only looks like the deliberate one);
- ``busy``: uses CPU time until it is stopped (for the threshold and the guards).

Whether a failure counts as an error of the procedure is decided by the harness from what
it declared before the run, never by this script (synthetic.classify_synthetic_build).
"""

import json
import sys
import time
from pathlib import Path

DELIBERATE_LINE = "synthetic build: deliberate procedure error"
DELIBERATE_EXIT = 86


def main(argv):
    rung = argv[0]
    plan = json.loads(Path("ladder.json").read_text(encoding="utf-8"))
    action = plan[rung]
    if action == "ok":
        Path("out").mkdir(exist_ok=True)
        Path("out", f"built-{rung}.txt").write_text(f"{rung} {argv[1]}\n")
        return 0
    if action == "procedure_error":
        print(DELIBERATE_LINE, flush=True)
        return DELIBERATE_EXIT
    if action == "crash":
        raise RuntimeError(f"unexpected failure while building {rung}")
    if action == "exit86":
        return DELIBERATE_EXIT
    if action == "busy":
        end = time.process_time() + 60
        while time.process_time() < end:
            pass
        return 0
    print(f"unknown action {action!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
