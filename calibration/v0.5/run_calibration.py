"""The steps of the v0.5 calibration (calibration/v0.5/PROTOCOL.md, section 8).

A wrapper: it parses its arguments and calls ``refute.packs.tess.calib05``, so every line it
executes is inside the lock's code hash. Each step runs once; its outputs are never written over.

    .venv/Scripts/python.exe calibration/v0.5/run_calibration.py freeze
    .venv/Scripts/python.exe calibration/v0.5/run_calibration.py select --protocol-commit <sha>
    .venv/Scripts/python.exe calibration/v0.5/run_calibration.py claim
    .venv/Scripts/python.exe calibration/v0.5/run_calibration.py c1-prefix
    .venv/Scripts/python.exe calibration/v0.5/run_calibration.py c1-confirm \
        --commit-b <sha> --prefix <report>
    .venv/Scripts/python.exe calibration/v0.5/run_calibration.py c2-fetch
    .venv/Scripts/python.exe calibration/v0.5/run_calibration.py c2-prefix
    .venv/Scripts/python.exe calibration/v0.5/run_calibration.py c2-run --k 20
    .venv/Scripts/python.exe calibration/v0.5/run_calibration.py c3-run --cache <dir>

Network: ``freeze`` (the inputs, MAST), ``select`` (GitHub API, drand, MAST and the TIC),
``c1-confirm`` (GitHub API, drand) and ``c2-fetch`` (MAST). Every step after the protocol commit
needs the maintainer's approval at its stop (S3 to S6).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def main(argv: list[str]) -> int:
    from refute.packs.tess.calib05 import c3select, steps

    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="step", required=True)
    sub.add_parser("freeze")
    sel = sub.add_parser("select")
    sel.add_argument("--protocol-commit", required=True)
    sub.add_parser("claim")
    for name in ("c1-prefix", "c2-prefix"):
        p = sub.add_parser(name)
        p.add_argument("--workers", type=int)
    conf = sub.add_parser("c1-confirm")
    conf.add_argument("--commit-b", required=True)
    conf.add_argument("--prefix", required=True)
    conf.add_argument("--workers", type=int)
    sub.add_parser("c2-fetch")
    run = sub.add_parser("c2-run")
    run.add_argument("--k", type=int, required=True)
    run.add_argument("--workers", type=int)
    c3 = sub.add_parser("c3-run")
    c3.add_argument("--cache", required=True)
    c3.add_argument("--workers", type=int)
    args = ap.parse_args(argv)

    if args.step == "freeze":
        out = c3select.freeze_step(ROOT)
        summary = {"s_max": out["s_max"], "files": len(out["files"]), "pools": out["pool_preview"]}
    elif args.step == "select":
        out = c3select.select_step(ROOT, args.protocol_commit)
        summary = {
            "round": out["round"],
            "complete": out["complete"],
            "chosen": {k: p["chosen"] for k, p in out["pools"].items()},
        }
    elif args.step == "claim":
        out = steps.c3_claim(ROOT)
        summary = {"claim": out["claim"]["id"], "rows": out["scan"]["rows"]}
    elif args.step == "c1-prefix":
        out = steps.c1_prefix(ROOT, args.workers)
        summary = {k: out[k] for k in ("projected_processor_hours", "sizes")}
    elif args.step == "c1-confirm":
        out = steps.c1_confirmation(ROOT, args.commit_b, Path(args.prefix), args.workers)
        summary = {"round": out["round"], "rules": out["decision_rules"]}
    elif args.step == "c2-fetch":
        out = steps.c2_fetch(ROOT)
        summary = {"input_changed": sorted(out["input_changed"])}
    elif args.step == "c2-prefix":
        out = steps.c2_prefix(ROOT, args.workers)
        summary = {"stars": out["stars"], "mismatches": len(out["compatibility"])}
    elif args.step == "c2-run":
        out = steps.c2_run(ROOT, args.k, args.workers)
        summary = {"compatibility": out["compatibility"]["state"], "targets": out["targets"]}
    else:
        out = steps.c3_run(ROOT, Path(args.cache), args.workers)
        summary = {k: v["result"] for k, v in out["targets"].items()}
    print(json.dumps(summary, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
