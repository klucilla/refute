"""The v0.4 pilot's prepared material (P4 and P5 of docs/plans/v0.4-pilot-plan.md): the annexes
of the stage-2 dossiers, the case files and the case ledger. Nothing here is published.

A wrapper like run_pilot.py: the content comes from the locked code (``refute.core.seal``,
``refute.core.ledger``, ``refute.packs.tess.discover.case``, ``runs``, ``injection``) and from
the records the runs wrote; it adds where things go.

    .venv/Scripts/python.exe calibration/v0.4/prepare_p5.py annex-measurements --key <TIC-n>
            --dossier <stage-2 dossier> --stage1-dossier <stage-1 dossier> --measure <name> ...
        The annex `measurements` of a sealed stage-2 dossier, added before its review: this
        star's injection and transformed-curve records from the named measurement folders, their
        summaries (injections at stage 1; transformed curves per stage, counted apart), the
        stage-1 dossier's core hash and verdict.json hash, and the star's deduplication from
        calibration/v0.4/runs/stage1/entries.json (funnel stars) or its signal identity
        (controls).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
PILOT = ROOT / ".cache" / "v04" / "pilot"
P5 = ROOT / ".cache" / "v04" / "p5"
ENTRIES = ROOT / "calibration" / "v0.4" / "runs" / "stage1" / "entries.json"
CONTROL_KINDS = {"TIC-86396382": "planet", "TIC-393911494": "false_positive"}
LF = "\n"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8", newline=LF) as out:
        out.write(json.dumps(value, indent=2, sort_keys=True) + LF)


def cmd_annex_measurements(
    key: str, dossier: Path, stage1_dossier: Path, measures: list[str]
) -> int:
    from refute.core.seal import add_annex, read_seal, verify_seal
    from refute.packs.tess.discover import case, runs
    from refute.packs.tess.discover import injection as inj
    from refute.packs.tess.discover.measure import summarize_transforms

    for folder in (dossier, stage1_dossier):
        problems = verify_seal(folder)
        if problems:
            print(f"{folder}: not sealed and intact: {problems}")
            return 1
    records: list[dict[str, Any]] = []
    sources = {}
    for name in measures:
        path = PILOT / "measure" / name / "measurements.jsonl"
        sources[f"measure/{name}/measurements.jsonl"] = sha256_file(path)
        records += [r for r in runs.read_records(path) if r["target_key"] == key]
    runs.summarize_records(records)  # refuses the same task recorded twice
    injections = [r for r in records if r["kind"] == "injection"]
    stages = sorted({r["stage"] for r in records if r["kind"] == "transform"})
    summary = {
        "target_key": key,
        "injections": inj.summarize(injections),
        "transformed_curves_by_stage": {
            str(stage): summarize_transforms(
                [r for r in records if r["kind"] == "transform" and r["stage"] == stage]
            )
            for stage in stages
        },
        "cpu_seconds": sum(float(r.get("cpu_seconds") or 0.0) for r in records),
        "sources_sha256": sources,
        "note": "per curve, descriptive; detections on transformed curves are not a "
        "false-alarm rate; method_status: not_validated",
    }
    stage1 = {
        "dossier": stage1_dossier.relative_to(ROOT).as_posix(),
        "core_sha256": read_seal(stage1_dossier)["core_sha256"],
        "verdict_sha256": sha256_file(stage1_dossier / "verdict.json"),
    }
    if key in CONTROL_KINDS:
        verdict = json.loads((dossier / "verdict.json").read_text("utf-8"))
        cross = {
            "control": True,
            "signal_identity": case.signal_identity(verdict, CONTROL_KINDS[key]),
        }
    else:
        entries = json.loads(ENTRIES.read_text("utf-8"))["entries"]
        entry = next(e for e in entries if e["target_key"] == key)
        cross = {"control": False, "deduplication": entry.get("deduplication")}
    source = P5 / "annex-src" / key / "measurements"
    if source.exists():
        print(f"{source} exists; the annex source is written once")
        return 1
    source.mkdir(parents=True)
    with open(source / "records.jsonl", "x", encoding="utf-8", newline=LF) as out:
        for record in records:
            out.write(json.dumps(record, sort_keys=True, default=str) + LF)
    write_json(source / "summary.json", summary)
    write_json(source / "stage1.json", stage1)
    write_json(source / "cross_match.json", cross)
    record = add_annex(dossier, "measurements", source)
    print(f"annex measurements: {len(record['files'])} files, core {record['core_sha256']}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="step", required=True)
    annex = sub.add_parser("annex-measurements")
    annex.add_argument("--key", required=True)
    annex.add_argument("--dossier", required=True, type=Path)
    annex.add_argument("--stage1-dossier", required=True, type=Path)
    annex.add_argument("--measure", action="append", required=True)
    args = parser.parse_args(argv)
    return cmd_annex_measurements(
        args.key, args.dossier.resolve(), args.stage1_dossier.resolve(), args.measure
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
