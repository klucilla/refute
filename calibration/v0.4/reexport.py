"""Sheet version 2 of the candidate parameter sheet (defects #179 and #194), re-exported from the
sealed dossiers of the v0.4 pilot as the annex `export-2`, without re-running any analysis.

Approved by the maintainer on 2026-11-01 (a new exporter version, a deterministic re-export from
the sealed dossiers, no re-run of discover, no verdict changed; checked with Codex). This script is
outside the code hash on purpose: the locked exporter (src/refute/packs/tess/exporter.py) stays as
locked until the phase closes, and the same fix enters src/ with the v0.5 code.

What version 2 changes, and nothing else (every other field keeps its version-1 value, checked):

- #179: `duration_method` names the method of the value shown (`bls-grid-search`); the
  trapezoid fit, not accepted, moves to `duration_fit` with no value; `duration_note` says that
  the duration shown is the BLS value and why the fit is not reported; the Markdown row of a
  missing duration uncertainty says "not reported" instead of "not estimable".
- #194: for the controls, the catalogued period and its uncertainty from the catalog row stored
  in `target.json`, with the catalog, the columns, the URL and the retrieval time.

Steps (nothing is attached until every dossier passes steps 1 to 3):
1. the inventory: the 107 sealed dossiers of the phase, each core checked against its seal and
   against the core hash recorded in calibration/v0.4/runs/;
2. the equivalence gate: the locked exporter, run on `verdict.json`, gives the core's `export/`
   files byte for byte;
3. version 2 generated twice (byte-identical), and compared with version 1 field by field;
4. `--attach`: the annex `export-2` (never overwritten; an existing one must equal the new files),
   then the core and every annex checked again.

usage: reexport.py --scratch <dir in .cache> [--attach] [--summary <json>]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "calibration" / "v0.4" / "runs"
PILOT = ROOT / ".cache" / "v04" / "pilot"
SHEET_VERSION = "candidate-parameters-2"
ANNEX = "export-2"
SUPERSEDES = "export/ of the sealed core (candidate-parameters-1); defects #179 and #194"
BLS_METHOD = "bls-grid-search"
# the fields version 2 may add or change; any other difference stops the re-export
ALLOWED = {
    "sheet_version",
    "duration_method",
    "duration_note",
    "duration_fit",
    "supersedes",
    "published_period_days",
    "published_period_err_days",
    "published_period_err_kind",
    "published_period_source",
}
# the catalog columns of a control's period and its uncertainty, by the source of its row
PERIOD_COLUMNS = {
    "ExoFOP TOI table": ("Period (days)", "Period (days) err", "uncertainty as catalogued"),
    "NASA Exoplanet Archive pscomppars": (
        "pl_orbper",
        "pl_orbpererr1",
        "upper uncertainty as catalogued (pl_orbpererr1), not a symmetric error",
    ),
}
LF = "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inventory() -> list[tuple[str, str, Path, str]]:
    """(run id, key, dossier, recorded core SHA-256) of the 107 sealed dossiers."""
    controls = json.loads((RUNS / "controls_seals.json").read_text("utf-8"))["runs"]
    funnel = json.loads((RUNS / "stage1" / "seals.json").read_text("utf-8"))["core_sha256"]
    anchor = json.loads((RUNS / "p5_anchor.json").read_text("utf-8"))["stage2_dossiers"]
    promotion = json.loads((RUNS / "promotion.json").read_text("utf-8"))
    out = []
    for stage, run in (("stage1", controls["stage1"]), ("stage2", controls["stage2"])):
        for key, core in sorted(run["core_sha256"].items()):
            out.append((run["run_id"], key, PILOT / stage / run["run_id"] / key, core))
    for key, core in sorted(funnel.items()):
        out.append(("funnel-s1", key, PILOT / "stage1" / "funnel-s1" / key, core))
    for key in sorted(promotion["promoted"]):
        core = anchor[key]["core_sha256"]
        out.append(("promoted-s2", key, PILOT / "stage2" / "promoted-s2" / key, core))
    counts: dict[str, int] = {}
    for run_id, _key, _dossier, _core in out:
        counts[run_id] = counts.get(run_id, 0) + 1
    expected = {"controls-s1": 2, "controls-s2": 2, "funnel-s1": 100, "promoted-s2": 3}
    if counts != expected or len({(r, k) for r, k, _d, _c in out}) != len(out):
        raise SystemExit(f"the inventory is not the 107 dossiers of the phase: {counts}")
    for key, core in controls["stage2"]["core_sha256"].items():
        if anchor[key]["core_sha256"] != core:
            raise SystemExit(f"{key}: the stage-2 seal differs between the records")
    return out


def published_period(target: dict[str, Any]) -> dict[str, Any]:
    """#194: a control's catalogued period and its uncertainty, from its stored catalog row."""
    if target.get("kind") not in ("planet", "false_positive"):
        return {}  # a funnel star has no catalogued signal
    source = target.get("source") or {}
    columns = PERIOD_COLUMNS.get(source.get("name"))
    row = target.get("catalog") or {}
    if columns is None or columns[0] not in row:
        raise SystemExit(f"{target.get('key')}: no known period columns for {source.get('name')!r}")
    value_col, err_col, kind = columns
    err = row.get(err_col)
    return {
        "published_period_days": float(row[value_col]),
        "published_period_err_days": float(err) if err not in (None, "") else None,
        "published_period_err_kind": kind if err not in (None, "") else "not catalogued",
        "published_period_source": {
            "catalog": source.get("name"),
            "value_column": value_col,
            "uncertainty_column": err_col,
            "url": source.get("url"),
            "retrieved_utc": source.get("retrieved_utc"),
        },
    }


def version2(result: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    from refute.packs.tess import exporter
    from refute.packs.tess.duration import METHOD_ACCEPTED, NOT_ACCEPTED_REASON

    if METHOD_ACCEPTED:
        raise SystemExit("the duration method is accepted in this code: version 2 does not apply")
    v1 = exporter._fields(result)
    fields: dict[str, Any] = {"sheet_version": SHEET_VERSION}
    fields.update(v1)
    estimate = result.get("duration_estimate")
    if result.get("candidate"):
        fields["duration_method"] = BLS_METHOD
    else:
        fields.pop("duration_method", None)
    if estimate is not None:
        fields["duration_fit"] = {
            "method": estimate.get("method"),
            "accepted": False,
            "estimable": estimate.get("estimable"),
            "not_reported_reason": NOT_ACCEPTED_REASON,
        }
        fields["duration_note"] = (
            "the duration shown is the BLS grid value; the trapezoid fit's duration and "
            "uncertainty are not reported: " + NOT_ACCEPTED_REASON
        )
    fields.update(published_period(target))
    fields["supersedes"] = SUPERSEDES
    return fields


def check_allowed(v1: dict[str, Any], v2: dict[str, Any]) -> list[str]:
    """Fields that differ between the versions outside ALLOWED (empty = only approved changes)."""
    bad = [
        k
        for k in sorted(set(v1) | set(v2))
        if k not in ALLOWED and ((k in v1) != (k in v2) or v1.get(k) != v2.get(k))
    ]
    if v1.get("duration_hours") != v2.get("duration_hours"):
        bad.append("duration_hours")
    return bad


def markdown(result: dict[str, Any], fields: dict[str, Any]) -> str:
    from refute.packs.tess.exporter import DISCLAIMER

    lines = [
        f"# Candidate parameter sheet: {result.get('target_key')} ({SHEET_VERSION})",
        "",
        f"> {DISCLAIMER}",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for key, value in fields.items():
        if key == "disclaimer":
            continue
        shown = value
        if key == "duration_err_hours" and value is None:
            shown = (
                "not reported (trapezoid fit not accepted; no uncertainty is given for the BLS "
                "value)"
                if "duration_fit" in fields
                else "not measured"
            )
        elif isinstance(value, dict):
            shown = json.dumps(value, sort_keys=True)
        lines.append(f"| {key} | {shown} |")
    lines += ["", "Evidence: see `report.md`, `verdict.json` and `plots/` in this dossier.", ""]
    return LF.join(lines)


def render(result: dict[str, Any], target: dict[str, Any]) -> dict[str, bytes]:
    fields = version2(result, target)
    text = json.dumps(fields, indent=2, sort_keys=True, ensure_ascii=False) + LF
    return {
        "candidate_parameters.json": text.encode("utf-8"),
        "candidate_parameters.md": markdown(result, fields).encode("utf-8"),
    }


def git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def provenance_problems() -> tuple[str, list[str]]:
    """The commit this run comes from, and why it cannot attach (empty = it can): the code,
    the claim and the inputs of this script must be the committed bytes (untracked files
    included), this script must be the committed one, and the locked claim must verify."""
    from refute.core.lock import VerifyStatus, verify_claim

    commit = git("rev-parse", "HEAD").stdout.decode().strip()
    problems = []
    paths = ("src", "pyproject.toml", "uv.lock", "calibration/v0.4")
    if git("status", "--porcelain", "--untracked-files=all", "--", *paths).stdout.strip():
        problems.append("uncommitted or untracked changes under " + ", ".join(paths))
    committed = git("show", f"{commit}:calibration/v0.4/reexport.py").stdout
    if committed != Path(__file__).read_bytes():
        problems.append("this script is not the committed calibration/v0.4/reexport.py")
    integrity = verify_claim(ROOT / "calibration" / "v0.4" / "claim.yaml")
    if integrity.status is not VerifyStatus.PASS:
        problems.append(f"refute verify: {integrity.status.value}")
    return commit, problems


def annex_matches(existing: Path, source: Path) -> bool:
    """An existing annex holds exactly the source's files (its own manifest aside), byte for
    byte."""
    from refute.core.seal import ANNEX_MANIFEST

    have = {p.name for p in existing.iterdir()} - {ANNEX_MANIFEST}
    want = {p.name for p in source.iterdir()}
    return have == want and all(
        (existing / n).read_bytes() == (source / n).read_bytes() for n in want
    )


def main(argv: list[str]) -> int:
    from refute.core.seal import ANNEX_DIR, add_annex, check_sealed, read_seal
    from refute.packs.tess.exporter import JSON_NAME, MARKDOWN_NAME, CandidateParameterExporter

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--attach", action="store_true")
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args(argv)
    scratch = args.scratch.resolve()
    if not scratch.is_relative_to(ROOT / ".cache") or scratch.exists():
        print(f"the scratch folder must be new and inside .cache: {scratch}")
        return 1
    summary_path = args.summary.resolve() if args.summary else None
    if summary_path is not None and (
        summary_path.parent != (RUNS).resolve() or summary_path.exists()
    ):
        print(f"the summary must be a new file directly in {RUNS}: {summary_path}")
        return 1
    commit, problems = provenance_problems()
    if args.attach and problems:
        print("attach refused: " + "; ".join(problems))
        return 1
    tool_sha = sha256_bytes(Path(__file__).read_bytes())
    plan = []
    for run_id, key, dossier, core in inventory():
        check = check_sealed(dossier)
        if not check.ok or read_seal(dossier)["core_sha256"] != core:
            print(f"{run_id}/{key}: the core is not intact against the recorded seal")
            return 1
        verdict_bytes = (dossier / "verdict.json").read_bytes()
        target_bytes = (dossier / "target.json").read_bytes()
        result = json.loads(verdict_bytes)
        target = json.loads(target_bytes)
        v1_dir = scratch / "v1" / run_id / key
        CandidateParameterExporter().export(result, v1_dir)
        originals = {}
        for name in (JSON_NAME, MARKDOWN_NAME):
            sealed = (dossier / "export" / name).read_bytes()
            if (v1_dir / name).read_bytes() != sealed:
                print(f"{run_id}/{key}: the locked exporter does not reproduce export/{name}")
                return 1
            originals[name] = sha256_bytes(sealed)
        first, second = render(result, target), render(result, target)
        if first != second:
            print(f"{run_id}/{key}: version 2 is not deterministic")
            return 1
        bad = check_allowed(
            json.loads((dossier / "export" / JSON_NAME).read_bytes()),
            json.loads(first[JSON_NAME]),
        )
        if bad:
            print(f"{run_id}/{key}: fields outside the approved changes differ: {bad}")
            return 1
        source = scratch / "v2" / run_id / key
        source.mkdir(parents=True)
        for name, data in first.items():
            (source / name).write_bytes(data)
        record = {
            "sheet_version": SHEET_VERSION,
            "supersedes": SUPERSEDES,
            "inputs_sha256": {
                "verdict.json": sha256_bytes(verdict_bytes),
                "target.json": sha256_bytes(target_bytes),
            },
            "version1_sha256": originals,
            "version2_sha256": {name: sha256_bytes(data) for name, data in first.items()},
            "tool": {
                "path": "calibration/v0.4/reexport.py",
                "sha256": tool_sha,
                "commit": commit,
            },
            "analysis_rerun": False,
            "note": "re-exported from the sealed core's verdict.json and target.json; the core "
            "is not rewritten and no verdict depends on the sheet",
        }
        (source / "reexport.json").write_bytes(
            (json.dumps(record, indent=2, sort_keys=True) + LF).encode("utf-8")
        )
        plan.append((run_id, key, dossier, core, source, record))
    print(f"{len(plan)} dossiers: equivalence, determinism and approved changes checked")
    if args.attach:
        # every existing annex is checked before the first one is attached (resume)
        for run_id, key, dossier, _core, source, _record in plan:
            existing = dossier / ANNEX_DIR / ANNEX
            if existing.exists() and not annex_matches(existing, source):
                print(f"{run_id}/{key}: an existing {ANNEX} differs from this run's files")
                return 1
        attached = 0
        for _run_id, _key, dossier, _core, source, _record in plan:
            if not (dossier / ANNEX_DIR / ANNEX).exists():
                add_annex(dossier, ANNEX, source)
                attached += 1
        for run_id, key, dossier, core, source, _record in plan:
            check = check_sealed(dossier)
            ok = check.ok and read_seal(dossier)["core_sha256"] == core
            if not ok or not annex_matches(dossier / ANNEX_DIR / ANNEX, source):
                print(f"{run_id}/{key}: not intact after the annex")
                return 1
        print(f"{attached} annexes {ANNEX} attached; all {len(plan)} dossiers checked again")
    if summary_path is not None and args.attach:
        summary = {
            "sheet_version": SHEET_VERSION,
            "tool_sha256": tool_sha,
            "tool_commit": commit,
            "dossiers": {
                f"{run_id}/{key}": {
                    "core_sha256": core,
                    "version1_sha256": record["version1_sha256"],
                    "version2_sha256": record["version2_sha256"],
                }
                for run_id, key, _d, core, _s, record in plan
            },
        }
        with open(summary_path, "xb") as handle:
            handle.write((json.dumps(summary, indent=2, sort_keys=True) + LF).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
