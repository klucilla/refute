"""Independent reviewer reports attached to a dossier (from v0.2).

A reviewer is a fresh, read-only agent session that receives only the dossier and
tries to refute it (procedure: ``docs/reviewer-protocol.md``). Its report is a
Markdown file. Reviewers raise objections; they never set or change a verdict.

``attach_review`` copies a report to ``review/<reviewer>.md`` and records it in
``review/index.json`` together with two fingerprints of the dossier as it was
before any review:

- ``analysis_manifest_sha256``: SHA-256 of the manifest lines of every file
  outside ``review/`` (the analysis and its evidence);
- ``verdict_sha256``: SHA-256 of ``verdict.json``.

It then rewrites ``MANIFEST.sha256`` so the review files are covered too.
``verify_reviews`` (run by ``refute check-dossier``) recomputes both fingerprints
and every report hash, so a report cannot be attached to a dossier whose analysis
or verdict was changed, and a report cannot be edited unnoticed.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from refute.core.dossier import REVIEW_DIR, read_manifest, verify_manifest, write_manifest
from refute.core.hashing import sha256_bytes, sha256_file
from refute.core.io import read_json, write_json, write_text

INDEX_SCHEMA = "refute-review-index-1"
_REVIEWER_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


class ReviewError(Exception):
    """A review cannot be attached."""


def _analysis_fingerprint(manifest: dict[str, str]) -> str:
    lines = [
        f"{digest}  {rel}\n"
        for rel, digest in sorted(manifest.items())
        if not rel.startswith(f"{REVIEW_DIR}/")
    ]
    return sha256_bytes("".join(lines).encode("utf-8"))


def _index_path(dossier: Path) -> Path:
    return dossier / REVIEW_DIR / "index.json"


def _index_markdown(index: dict[str, Any]) -> str:
    lines = [
        "# Independent reviews",
        "",
        "Reports by fresh, read-only reviewer sessions that received only this dossier",
        "(procedure: `docs/reviewer-protocol.md` in the Refute repository). Reviewers",
        "raise objections; they never set or change the verdict, which comes only from",
        "the deterministic tests in `verdict.json`.",
        "",
        f"- Analysis fingerprint at review time: `{index['analysis_manifest_sha256']}`",
        f"- `verdict.json` SHA-256 at review time: `{index['verdict_sha256']}`",
        "",
        "| Reviewer | Model | Report | Attached (UTC) |",
        "|---|---|---|---|",
    ]
    for entry in index["reviews"]:
        name = Path(entry["file"]).name
        lines.append(
            f"| {entry['reviewer']} | {entry['model']} | [{name}]({name}) | "
            f"{entry['attached_utc']} |"
        )
    lines.append("")
    return "\n".join(lines)


def attach_review(
    dossier: Path | str,
    report: Path | str,
    *,
    reviewer: str,
    model: str,
    now: str | None = None,
) -> dict[str, Any]:
    dossier, report = Path(dossier), Path(report)
    if not _REVIEWER_RE.match(reviewer):
        raise ReviewError("reviewer id must be lowercase letters, digits, '.', '_' or '-'")
    if not model.strip():
        raise ReviewError("the model name is required")
    if not report.is_file():
        raise ReviewError(f"report not found: {report}")
    if not (dossier / "verdict.json").is_file():
        raise ReviewError(f"not a dossier (no verdict.json): {dossier}")
    problems = verify_manifest(dossier)
    if _index_path(dossier).is_file():
        problems += verify_reviews(dossier)
    if problems:
        raise ReviewError("the dossier is not intact: " + "; ".join(problems))

    manifest = read_manifest(dossier)
    fingerprint = _analysis_fingerprint(manifest)
    verdict_sha = sha256_file(dossier / "verdict.json")
    if _index_path(dossier).is_file():
        index = read_json(_index_path(dossier))
    else:
        index = {
            "schema": INDEX_SCHEMA,
            "analysis_manifest_sha256": fingerprint,
            "verdict_sha256": verdict_sha,
            "reviews": [],
        }
    target = f"{REVIEW_DIR}/{reviewer}.md"
    if any(entry["file"] == target for entry in index["reviews"]):
        raise ReviewError(f"a report from reviewer '{reviewer}' is already attached")

    content = report.read_bytes()
    (dossier / REVIEW_DIR).mkdir(parents=True, exist_ok=True)
    (dossier / target).write_bytes(content)
    entry = {
        "reviewer": reviewer,
        "model": model.strip(),
        "file": target,
        "sha256": sha256_bytes(content),
        "attached_utc": now or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    index["reviews"].append(entry)
    write_json(_index_path(dossier), index)
    write_text(dossier / REVIEW_DIR / "index.md", _index_markdown(index))
    write_manifest(dossier)
    return entry


def verify_reviews(dossier: Path | str) -> list[str]:
    """Problems with the attached reviews (empty list = consistent)."""
    dossier = Path(dossier)
    try:
        index = read_json(_index_path(dossier))
    except (OSError, ValueError) as exc:
        return [f"review index unreadable: {exc}"]
    problems = []
    if index.get("schema") != INDEX_SCHEMA:
        problems.append("review index has an unknown schema")
    try:
        manifest = read_manifest(dossier)
    except OSError as exc:
        return [f"cannot read the manifest: {exc}"]
    if _analysis_fingerprint(manifest) != index.get("analysis_manifest_sha256"):
        problems.append("the analysis files changed after the reviews were attached")
    verdict = dossier / "verdict.json"
    if not verdict.is_file() or sha256_file(verdict) != index.get("verdict_sha256"):
        problems.append("verdict.json changed after the reviews were attached")
    for entry in index.get("reviews", []):
        path = dossier / entry["file"]
        if not path.is_file():
            problems.append(f"review report missing: {entry['file']}")
        elif sha256_file(path) != entry["sha256"]:
            problems.append(f"review report modified: {entry['file']}")
    return problems
