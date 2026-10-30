"""The v0.4 pilot's frozen inputs and selection (calibration/v0.4/PROTOCOL.md, sections 4 and 12).

A wrapper: it parses its arguments and calls ``refute.packs.tess.discover.steps``, so every line
the steps execute is inside the lock's code hash. Three steps, each run once:

    .venv/Scripts/python.exe calibration/v0.4/run_selection.py freeze
        Before the protocol commit: download the frozen inputs into a new attempt folder,
        .cache/v04/inputs-attempts/attempt-NN/, copy the small ones (not the per-sector lists,
        the frame, the TESS-EB table nor the Gaia asset) to calibration/v0.4/inputs/ and write
        calibration/v0.4/inputs.json.

    .venv/Scripts/python.exe calibration/v0.4/run_selection.py assemble --approval <comment URL>
        Instead of freeze (the maintainer's decision of 2026-10-30): an attempt assembled from
        the files of attempt 4, the TESS-EB static edition and the Gaia DR3 EB asset; the same
        copy and inputs.json. The approval is the URL of its comment in an issue.

    .venv/Scripts/python.exe calibration/v0.4/run_selection.py archive
        Archive every frozen input to the Drive with a checked SHA-256 manifest (#172).

    .venv/Scripts/python.exe calibration/v0.4/run_selection.py select --protocol-commit <full SHA>
        After the protocol commit is pushed and its round is published; refused unless the code,
        the protocol and the inputs are that commit's bytes. Writes calibration/v0.4/selection/.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from refute.packs.tess.discover import steps

ROOT = Path(__file__).resolve().parent.parent.parent


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="step", required=True)
    sub.add_parser("freeze")
    sub.add_parser("assemble").add_argument("--approval", required=True)
    sub.add_parser("archive")
    run = sub.add_parser("select")
    run.add_argument("--protocol-commit", required=True)
    args = parser.parse_args(argv)
    if args.step in ("freeze", "assemble"):
        if args.step == "freeze":
            inputs = steps.freeze_step(ROOT)
        else:
            inputs = steps.assemble_step(ROOT, args.approval)
        print(f"S_max {inputs['s_max']}; frame of {inputs['frame_stars']} stars; "
              f"{len(inputs['files'])} files, {inputs['total_bytes']} bytes")  # fmt: skip
        return 0
    if args.step == "archive":
        problems = steps.archive_step(ROOT, script=Path(__file__))
        print("problems:", problems or "none")
        return 1 if problems else 0
    out = steps.select_step(ROOT, args.protocol_commit)
    print(f"round {out['round']}: complete {out['complete']}")
    return 0 if out["complete"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
