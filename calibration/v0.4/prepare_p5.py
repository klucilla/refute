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

    .venv/Scripts/python.exe calibration/v0.4/prepare_p5.py case --key <TIC-n>
            --dossier <stage-2 dossier> --human <human items JSON>
        The annex `case` (case.json, refute-tess-case-1) of a reviewed stage-2 dossier: the
        machine-built items (case.build_case), the review annexes by hash, and the drafted human
        items (questions for a human, conclusion in the closed vocabulary); refused unless the
        checklist (case.missing_items) is empty.

    .venv/Scripts/python.exe calibration/v0.4/prepare_p5.py ledger --human <human items JSON>
            --out <ledger.jsonl>
        The case ledger of every case (refute-ledger-1, chained by hash), from the records:
        opened (the selection), locked, ran (stage 1, the light entries; stage 2, the dossier's
        core hash), promoted, reviewed, concluded (drafts: the stage-1 conclusions derived from
        each entry, the others from the human items); verified with case.check_event.
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


def locked_targets() -> dict[str, dict[str, Any]]:
    from refute.core.claim import load_claim

    loaded = load_claim(ROOT / "calibration" / "v0.4" / "claim.yaml")
    return {t["key"]: t for t in loaded.pack.schema.targets_for_run(loaded)}


def review_annexes(dossier: Path) -> list[dict[str, Any]]:
    """The review annexes of a dossier (``review-*``), each by the hash of its manifest."""
    from refute.core.seal import ANNEX_DIR, ANNEX_MANIFEST, verify_annex

    found = []
    for annex in sorted((dossier / ANNEX_DIR).glob("review-*")):
        problems = verify_annex(dossier, annex.name)
        if problems:
            raise SystemExit(f"{annex}: {problems}")
        found.append(
            {
                "annex": annex.name,
                "manifest_sha256": sha256_file(annex / ANNEX_MANIFEST),
                "report": f"annexes/{annex.name}/review.md",
            }
        )
    return found


def cmd_case(key: str, dossier: Path, human_path: Path) -> int:
    from refute.core.seal import add_annex, verify_annex
    from refute.packs.tess.discover import case

    human = json.loads(human_path.read_text("utf-8"))[key]
    if verify_annex(dossier, "measurements"):
        print(f"{dossier}: the measurements annex is missing or not intact")
        return 1
    measured = dossier / "annexes" / "measurements"
    verdict = json.loads((dossier / "verdict.json").read_text("utf-8"))
    built = case.build_case(
        verdict,
        locked_targets()[key],
        json.loads((measured / "cross_match.json").read_text("utf-8")),
        json.loads((measured / "summary.json").read_text("utf-8")),
    )
    built["review"] = review_annexes(dossier)
    built["questions_for_a_human"] = human["questions_for_a_human"]
    built["conclusion"] = human["conclusion"]
    missing = case.missing_items(built)
    if missing:
        print(f"{key}: the case is incomplete: {missing}")
        return 1
    source = P5 / "annex-src" / key / "case"
    source.mkdir(parents=True)
    write_json(source / "case.json", built)
    record = add_annex(dossier, "case", source)
    print(f"annex case: {len(record['files'])} file(s), core {record['core_sha256']}")
    return 0


# the alternative explanation each fatal test points to (case.ALTERNATIVES)
ALTERNATIVE_OF = {
    "odd_even": "eclipsing binary on the target",
    "secondary_eclipse": "eclipsing binary on the target",
    "plausibility": "eclipsing binary on the target",
    "eb_catalog": "eclipsing binary on the target",
    "nearby_contamination": "background or nearby eclipsing binary",
    "centroid_shift": "background or nearby eclipsing binary",
    "aperture_depth": "background or nearby eclipsing binary",
    "systematics": "instrumental systematics",
    "period_alias": "period alias",
}


def stage1_conclusion(entry: dict[str, Any], promoted: list[str]) -> str:
    """The drafted conclusion of a funnel star that ends at stage 1, from its eligibility."""
    reason = entry["eligibility"]["reason"]
    if entry["eligibility"]["eligible"]:
        if entry["target_key"] in promoted:
            raise ValueError(f"{entry['target_key']} is promoted: its conclusion is a human item")
        return "not evaluated past stage 1: cap"
    prefix = "signal with a likely alternative explanation, by the test(s) "
    if reason.startswith(prefix):
        tests = reason[len(prefix) :].split(", ")
        return (
            f"signal with a likely alternative explanation: {ALTERNATIVE_OF[tests[0]]}, "
            f"by the test {', '.join(tests)}"
        )
    if reason == "no significant signal in these data":
        return reason
    if reason.startswith("insufficient data to decide: "):
        return reason
    if reason == "signal matches a known object":
        return "signal matches a known object: see the deduplication record"
    return f"insufficient data to decide: {reason}"


def run_finished(run_dir: Path) -> str:
    """When a run finished, from its summary.json (YYYY-MM-DDTHH:MM:SSZ)."""
    summary = json.loads((run_dir / "summary.json").read_text("utf-8"))
    return summary["run"]["finished_utc"].replace("+00:00", "Z")


def cmd_ledger(human_path: Path, out: Path) -> int:
    from refute.core.io import read_json
    from refute.core.ledger import make_event, verify_events
    from refute.core.seal import read_seal
    from refute.packs.tess.discover import case

    if out.exists():
        print(f"{out} exists; a ledger is only appended to")
        return 1
    v04 = ROOT / "calibration" / "v0.4"
    human = json.loads(human_path.read_text("utf-8"))
    targets = locked_targets()
    selection = json.loads((v04 / "selection" / "selection.json").read_text("utf-8"))
    targets_doc = (v04 / "selection" / "targets.yaml").read_text("utf-8")
    lock = read_json(v04 / "claim.lock.json")
    entries_doc = json.loads(ENTRIES.read_text("utf-8"))
    entries = {e["target_key"]: e for e in entries_doc["entries"]}
    promotion = json.loads((v04 / "runs" / "promotion.json").read_text("utf-8"))
    promoted = list(promotion["promoted"])
    stage2 = human["_stage2_dossiers"]  # key -> stage-2 dossier path (controls and promoted)
    controls_s1 = human["_controls_stage1_dossiers"]
    events: list[tuple[str, str, str, dict, dict]] = []  # utc, case, type, data, hashes
    opened_utc = "2026-10-30T19:03:29Z"  # targets.yaml generated_utc
    for key, target in targets.items():
        events.append(
            (
                opened_utc,
                key,
                "opened",
                {
                    "kind": target["kind"],
                    "name": target.get("name"),
                    "selection_round": selection.get("round"),
                    "protocol_commit": "0000018f1f99d413a211d00f557bf5d60b01858b",
                },
                {"targets_yaml": hashlib.sha256(targets_doc.encode("utf-8")).hexdigest()},
            )
        )
        events.append(
            (
                lock["locked_at_utc"],
                key,
                "locked",
                {"claim_id": "tess-discover-v0.4-pilot", "lock_commit_b": human["_commit_b"]},
                {"claim": lock["claim_sha256"], "code": lock["code"]["sha256"]},
            )
        )
    for key in [k for k in targets if k in controls_s1]:
        folder = ROOT / controls_s1[key]
        verdict = json.loads((folder / "verdict.json").read_text("utf-8"))
        eligibility = {"eligible": None, "reason": "control: runs every stage, never promoted"}
        data = case.light_entry(verdict, eligibility, None)
        hashes = {"verdict": sha256_file(folder / "verdict.json")}
        hashes["dossier"] = read_seal(folder)["core_sha256"]
        events.append((run_finished(folder.parent), key, "ran", data, hashes))
    funnel_finished = run_finished(ROOT / entries_doc["stage1_run_dir"])
    for key, entry in entries.items():
        data = dict(entry["ledger"])
        hashes = {"verdict": entry["verdict_sha256"], "commit": human["_results_commit"]}
        events.append((funnel_finished, key, "ran", data, hashes))
    events.append(
        (
            human["_promotion_utc"],
            "funnel",
            "promoted",
            {
                "promotion_sha256": sha256_file(v04 / "runs" / "promotion.json"),
                "promoted": promoted,
                "eligible": promotion["eligible"],
                "beacon_round": (promotion.get("beacon") or {}).get("round"),
            },
            {"commit": human["_promotion_commit"]},
        )
    )
    for key, folder_text in stage2.items():
        folder = ROOT / folder_text
        verdict = json.loads((folder / "verdict.json").read_text("utf-8"))
        data = {
            "stage": 2,
            "method_status": verdict.get("method_status", "not_validated"),
            "temporal_diagnostic": (verdict.get("temporal_diagnostic") or {}).get(
                "state", "not_run"
            ),
            "verdict": verdict.get("verdict"),
            "tests": {t["name"]: t["status"] for t in verdict.get("tests", [])},
        }
        hashes = {"dossier": read_seal(folder)["core_sha256"]}
        events.append((run_finished(folder.parent), key, "ran", data, hashes))
        for review in review_annexes(folder):
            events.append(
                (
                    human["_review_utc"][key],
                    key,
                    "reviewed",
                    {"annex": review["annex"], "assessment": human[key]["review_assessment"]},
                    {"annex_manifest": review["manifest_sha256"], "dossier": hashes["dossier"]},
                )
            )
    for key in targets:
        if key in stage2:
            conclusion = human[key]["conclusion"]
        else:
            conclusion = {
                "text": stage1_conclusion(entries[key], promoted),
                "drafted_by": "agent, from the stage-1 entry (funnel.stage1_eligibility)",
                "status": "draft for the maintainer's approval (P5)",
            }
        events.append((human["_conclusion_utc"], key, "concluded", {"conclusion": conclusion}, {}))
    events.sort(key=lambda e: e[0])  # stable: the order above within a time
    chain: list[dict[str, Any]] = []
    for utc, key, kind, data, hashes in events:
        chain.append(make_event(chain[-1] if chain else None, key, kind, utc, data, None, hashes))
    problems = verify_events(chain, check=case.check_event)
    if problems:
        print("the ledger does not verify: " + "; ".join(problems[:10]))
        return 1
    from refute.core.canonical import canonical_bytes

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "xb") as handle:
        for event in chain:
            handle.write(canonical_bytes(event) + b"\n")
    print(f"{len(chain)} events; last hash {chain[-1]['hash']}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="step", required=True)
    annex = sub.add_parser("annex-measurements")
    annex.add_argument("--key", required=True)
    annex.add_argument("--dossier", required=True, type=Path)
    annex.add_argument("--stage1-dossier", required=True, type=Path)
    annex.add_argument("--measure", action="append", required=True)
    case_step = sub.add_parser("case")
    case_step.add_argument("--key", required=True)
    case_step.add_argument("--dossier", required=True, type=Path)
    case_step.add_argument("--human", required=True, type=Path)
    ledger = sub.add_parser("ledger")
    ledger.add_argument("--human", required=True, type=Path)
    ledger.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.step == "case":
        return cmd_case(args.key, args.dossier.resolve(), args.human)
    if args.step == "ledger":
        return cmd_ledger(args.human, args.out)
    return cmd_annex_measurements(
        args.key, args.dossier.resolve(), args.stage1_dossier.resolve(), args.measure
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
