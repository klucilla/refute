"""The C3 claim's targets attachment, projected under the deviation approved on 2026-11-04 (#199).

Why: the frozen selection step (``refute.packs.tess.calib05.c3select.targets_document``) writes
two fields per target into ``selection/targets.yaml``, ``c3_place`` (every target) and
``fp_class`` (the false positives), that the TESS targets schema (``TargetsFile``, extra fields
forbidden) refuses; so the claim written by the frozen ``run_calibration.py claim`` cannot be
loaded, locked or run. The code, the protocol and the selection stay as frozen; this script only
repackages the claim (calibration/v0.5/deviation/README.md):

- ``calibration/v0.5/claim-targets.yaml``: the bytes of ``selection/targets.yaml`` with exactly
  the target-level lines ``  c3_place: ...`` and ``  fp_class: ...`` removed, every other line
  kept in order; ``selection/targets.yaml`` is only read (the C3 steps keep reading it);
- ``calibration/v0.5/claim.yaml``: the bytes of the claim the frozen code wrote (kept as
  ``deviation/claim.generated.yaml``) with two header comment lines added and its targets
  attachment pointing at ``claim-targets.yaml``; ``selection/targets.yaml`` stays attached under
  the role ``selection-targets``, so the lock covers it too;
- ``deviation/projection.json``: the SHA-256 of every input and output, every removed line with
  its line number, and the result of each check; ``deviation/claim-targets.diff`` and
  ``deviation/claim.diff``: the complete unified diffs.

Checks, all before anything is written (a failure writes nothing): the removed lines are exactly
one ``c3_place`` per target and one ``fp_class`` per false positive, each a one-line scalar; the
parsed projection equals the parsed original with those two keys removed from each target (the
other top-level keys, the 22 targets and their order unchanged); the parsed claim equals the
generated one except the attachments; the diffs hold only removed lines (targets) or the
declared changes (claim); the claim, with the projection and a byte copy of every other
attachment, loads with ``refute.core.claim.load_claim`` (the TESS schema included) in a staging
folder under ``.cache/v05/deviation-staging``. After writing, the repository's claim is loaded
again and the targets a run reads must be the selection's 22, in order. Outputs are created
exclusively: an existing file is never written over.

Run from the repository root:
``.venv/Scripts/python.exe calibration/v0.5/deviation/project_targets.py``
"""

from __future__ import annotations

import copy
import difflib
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

STEP = Path("calibration/v0.5")
SOURCE_TARGETS = STEP / "selection" / "targets.yaml"
GENERATED_CLAIM = STEP / "deviation" / "claim.generated.yaml"
OUT_TARGETS = STEP / "claim-targets.yaml"
OUT_CLAIM = STEP / "claim.yaml"
RECORD = STEP / "deviation" / "projection.json"
TARGETS_DIFF = STEP / "deviation" / "claim-targets.diff"
CLAIM_DIFF = STEP / "deviation" / "claim.diff"

REMOVED_KEYS = ("c3_place", "fp_class")
LINE = re.compile(r"^  (c3_place|fp_class): (\S.*)$")
OLD_ATTACHMENT = "- path: selection/targets.yaml\n  role: targets\n"
NEW_ATTACHMENT = (
    "- path: claim-targets.yaml\n"
    "  role: targets\n"
    "- path: selection/targets.yaml\n"
    "  role: selection-targets\n"
)
HEADER_END = "# the selection; locked with `refute lock` from a clean tree at S4.\n"
HEADER_ADDED = (
    "# Targets attachment: claim-targets.yaml, projected from selection/targets.yaml by\n"
    "# deviation/project_targets.py (the deviation approved on 2026-11-04, #199).\n"
)
APPROVAL = "the maintainer's choice of option C on 2026-11-04, recorded on #199 before any commit"


class ProjectionError(Exception):
    """A check failed: nothing is written."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def project_targets(text: str) -> tuple[str, list[dict]]:
    """The projected text and the removed lines (1-based numbers in the original)."""
    kept, removed = [], []
    for number, line in enumerate(text.splitlines(keepends=True), start=1):
        match = LINE.match(line.rstrip("\n"))
        if match:
            removed.append({"line": number, "text": line.rstrip("\n"), "key": match.group(1)})
        else:
            kept.append(line)
    return "".join(kept), removed


def check_targets(original: str, projected: str, removed: list[dict]) -> dict:
    import yaml

    if "\r" in original:
        raise ProjectionError("selection/targets.yaml has CR characters")
    for line in removed:  # a removed line must be a plain one-line scalar, never a block's head
        value = line["text"].split(": ", 1)[1]
        if value[:1] in ("|", ">", "'", '"', "&", "*", "!", "[", "{"):
            raise ProjectionError(f"line {line['line']} is not a plain one-line scalar")
    try:
        before, after = yaml.safe_load(original), yaml.safe_load(projected)
    except yaml.YAMLError as error:
        raise ProjectionError(f"the projection does not parse: {error}") from error
    targets = before["targets"]
    places = [r for r in removed if r["key"] == "c3_place"]
    classes = [r for r in removed if r["key"] == "fp_class"]
    false_positives = [t for t in targets if t.get("kind") == "false_positive"]
    if len(places) != len(targets) or len(classes) != len(false_positives):
        raise ProjectionError(
            f"removed {len(places)} c3_place and {len(classes)} fp_class lines for "
            f"{len(targets)} targets and {len(false_positives)} false positives"
        )
    lacking = [t["key"] for t in targets if "c3_place" not in t]
    lacking += [t["key"] for t in false_positives if "fp_class" not in t]
    if lacking:
        raise ProjectionError("a target lacks a field the projection removes")
    expected = copy.deepcopy(before)
    for target in expected["targets"]:
        for key in REMOVED_KEYS:
            target.pop(key, None)
    if after != expected:
        raise ProjectionError("the parsed projection is not the original minus the two fields")
    for key in REMOVED_KEYS:
        if any(key in t for t in after["targets"]):
            raise ProjectionError(f"the projection still holds {key}")
    keys_before = [t["key"] for t in targets]
    if [t["key"] for t in after["targets"]] != keys_before:
        raise ProjectionError("the targets or their order changed")
    diff = list(difflib.ndiff(original.splitlines(), projected.splitlines()))
    changed = [d for d in diff if d[:2] in ("- ", "+ ", "? ")]
    if any(not d.startswith("- ") for d in changed) or len(changed) != len(removed):
        raise ProjectionError("the line diff holds more than the removed lines")
    return {
        "targets": len(targets),
        "false_positives": len(false_positives),
        "removed_c3_place": len(places),
        "removed_fp_class": len(classes),
        "target_keys_in_order": keys_before,
        "parsed_equal_minus_two_fields": True,
        "diff_only_removed_lines": True,
    }


def patch_claim(generated: str) -> str:
    if generated.count(OLD_ATTACHMENT) != 1 or generated.count(HEADER_END) != 1:
        raise ProjectionError("the generated claim is not the one this script expects")
    patched = generated.replace(OLD_ATTACHMENT, NEW_ATTACHMENT)
    return patched.replace(HEADER_END, HEADER_END + HEADER_ADDED)


def check_claim(generated: str, patched: str) -> dict:
    import yaml

    before, after = yaml.safe_load(generated), yaml.safe_load(patched)
    rest_before = {k: v for k, v in before.items() if k != "attachments"}
    rest_after = {k: v for k, v in after.items() if k != "attachments"}
    if rest_before != rest_after:
        raise ProjectionError("the claim changed outside its attachments")
    expected = [
        {"path": "claim-targets.yaml", "role": "targets"} if a["role"] == "targets" else a
        for a in before["attachments"]
    ]
    expected.insert(1, {"path": "selection/targets.yaml", "role": "selection-targets"})
    if after["attachments"] != expected:
        raise ProjectionError("the attachments are not the declared ones")
    diff = difflib.unified_diff(generated.splitlines(), patched.splitlines(), lineterm="", n=0)
    changed = [d for d in diff if d[:1] in "+-" and not d.startswith(("+++", "---"))]
    added = [d[1:] for d in changed if d.startswith("+")]
    dropped = [d[1:] for d in changed if d.startswith("-")]
    declared_added = (HEADER_ADDED + NEW_ATTACHMENT).splitlines()
    declared_dropped = OLD_ATTACHMENT.splitlines()
    # the diff may pair the lines differently (a line dropped and added again); as multisets,
    # what it adds minus what it drops must be the declared additions minus the declared removals
    if Counter(added) + Counter(declared_dropped) != Counter(dropped) + Counter(declared_added):
        raise ProjectionError("the claim diff holds more than the declared changes")
    return {
        "parsed_equal_except_attachments": True,
        "attachments": after["attachments"],
        "diff_only_declared_changes": True,
    }


def unified(a: str, b: str, name_a: str, name_b: str) -> str:
    lines = difflib.unified_diff(
        a.splitlines(keepends=True), b.splitlines(keepends=True), name_a, name_b, n=3
    )
    return "".join(lines)


def write_new(path: Path, text: str) -> None:
    with open(path, "x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def staged_load(root: Path, projected: str, patched: str) -> dict:
    """``load_claim`` on a copy (the claim, the projection and every other attachment, byte for
    byte) in a new folder under ``.cache/v05/deviation-staging``, before anything is written to
    the repository; the folder is kept (regenerable; listed in the round's summary)."""
    import yaml

    from refute.packs.tess.schema import TargetsFile

    TargetsFile.model_validate(yaml.safe_load(projected))  # the TESS targets schema first
    base = root / ".cache" / "v05" / "deviation-staging"
    base.mkdir(parents=True, exist_ok=True)
    number = 1
    while (base / f"stage-{number:02d}").exists():
        number += 1
    stage = base / f"stage-{number:02d}" / STEP
    stage.mkdir(parents=True)
    write_new(stage / OUT_CLAIM.name, patched)
    write_new(stage / OUT_TARGETS.name, projected)
    for attachment in yaml.safe_load(patched)["attachments"]:
        if attachment["path"] == OUT_TARGETS.name:
            continue
        target = stage / attachment["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "xb") as handle:
            handle.write((root / STEP / attachment["path"]).read_bytes())
    return {"staging": stage.relative_to(root).as_posix(), **loaded_summary(stage / OUT_CLAIM.name)}


def loaded_summary(claim_path: Path) -> dict:
    """``load_claim`` (the TESS schema included) and the targets a run would read, in order."""
    from refute.core.claim import load_claim
    from refute.packs.tess.schema import TessClaimSchema

    loaded = load_claim(claim_path)
    keys = [t["key"] for t in TessClaimSchema().targets_for_run(loaded)]
    return {"id": loaded.claim.id, "run_target_keys": keys}


def main(root: Path) -> int:
    root = Path(root)
    outputs = [OUT_TARGETS, OUT_CLAIM, RECORD, TARGETS_DIFF, CLAIM_DIFF]
    existing = [p.as_posix() for p in outputs if (root / p).exists()]
    if existing:
        raise ProjectionError("already written, never written over: " + ", ".join(existing))
    source_bytes = (root / SOURCE_TARGETS).read_bytes()
    generated_bytes = (root / GENERATED_CLAIM).read_bytes()
    original, generated = source_bytes.decode("utf-8"), generated_bytes.decode("utf-8")
    projected, removed = project_targets(original)
    targets_checks = check_targets(original, projected, removed)
    patched = patch_claim(generated)
    claim_checks = check_claim(generated, patched)
    targets_diff = unified(original, projected, SOURCE_TARGETS.as_posix(), OUT_TARGETS.as_posix())
    claim_diff = unified(generated, patched, GENERATED_CLAIM.as_posix(), OUT_CLAIM.as_posix())
    staged = staged_load(root, projected, patched)
    write_new(root / OUT_TARGETS, projected)
    write_new(root / OUT_CLAIM, patched)
    write_new(root / TARGETS_DIFF, targets_diff)
    write_new(root / CLAIM_DIFF, claim_diff)

    repository = loaded_summary(root / OUT_CLAIM)
    if repository["run_target_keys"] != targets_checks["target_keys_in_order"]:
        raise ProjectionError("the claim's run targets are not the selection's, in order")
    record = {
        "format": "refute-v05-c3-projection-1",
        "approval": APPROVAL,
        "script": "calibration/v0.5/deviation/project_targets.py",
        "script_sha256": sha256((root / STEP / "deviation" / "project_targets.py").read_bytes()),
        "inputs": {
            SOURCE_TARGETS.as_posix(): sha256(source_bytes),
            GENERATED_CLAIM.as_posix(): sha256(generated_bytes),
        },
        "outputs": {
            p.as_posix(): sha256((root / p).read_bytes())
            for p in (OUT_TARGETS, OUT_CLAIM, TARGETS_DIFF, CLAIM_DIFF)
        },
        "removed_lines": removed,
        "targets_checks": targets_checks,
        "claim_checks": claim_checks,
        "load_claim": {
            "staged": staged,
            "repository": repository,
        },
    }
    write_new(root / RECORD, json.dumps(record, indent=2) + "\n")
    print(json.dumps({"outputs": record["outputs"], "load_claim": record["load_claim"]}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(Path.cwd()))
    except ProjectionError as error:
        print(f"STOP: {error}", file=sys.stderr)
        sys.exit(1)
