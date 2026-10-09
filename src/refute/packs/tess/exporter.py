"""Candidate parameter sheet. It writes files for a human. It never submits anything.

The output gathers the parameters of the signal (period, epoch, depth, duration,
with their uncertainties where they were measured) and points to the evidence in
the dossier. It is a parameter sheet for a person, never a submission: ExoFOP accepts
community candidates only after they are published in a peer-reviewed journal (or
in a Research Note of the AAS that cites a peer-reviewed methodology), and only with
its approval (ExoFOP news of 2026-08-19; issue #18). This module contains no network
code on purpose.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from refute.core.io import write_json, write_text

JSON_NAME = "candidate_parameters.json"
MARKDOWN_NAME = "candidate_parameters.md"

DISCLAIMER = (
    "NOTHING HAS BEEN SUBMITTED. This is a parameter sheet for a human, never a "
    "submission: Refute never submits anything to ExoFOP or any other body, and a dossier "
    "cannot be uploaded to ExoFOP. ExoFOP accepts community candidates only after they are "
    "published in a peer-reviewed journal (or in a Research Note of the AAS that cites a "
    "peer-reviewed methodology), and only with its approval. This is a candidate signal and "
    "a verdict on a claim, never a confirmed discovery; no planet letter is assigned."
)


def _fields(result: dict[str, Any]) -> dict[str, Any]:
    cand = result.get("candidate") or {}
    eph = result.get("global_ephemeris") or {}
    tests = {t["name"]: t for t in result.get("tests", [])}
    data = result.get("data_summary", {})
    notes = [
        f"Refute verdict {result.get('verdict')} ({result.get('verdict_reason')}).",
        "Tests: " + ", ".join(f"{name} {t['status']}" for name, t in tests.items()) + ".",
    ]
    if result.get("target_kind") in {"planet", "false_positive", "development"}:
        notes.append("Calibration target: already catalogued; it is not a new candidate.")
    return {
        "submitted": False,
        "sheet": "candidate parameters for a human; not a submission",
        "tic_id": result.get("tic_id"),
        "period_days": cand.get("period"),
        "period_err_days": eph.get("period_err"),
        "epoch_bjd_tdb": eph.get("t_ref_bjd", cand.get("t0_bjd")),
        "epoch_err_days": eph.get("t_ref_err"),
        "duration_hours": cand.get("duration_hours"),
        "duration_err_hours": None,  # not measured by this version
        "depth_ppm": cand.get("depth_ppm"),
        "depth_err_ppm": (cand.get("depth_err") or 0) * 1e6 if cand else None,
        "snr": cand.get("snr"),
        "verdict": result.get("verdict"),
        "data_used": (
            f"TESS {data.get('product', {}).get('author', '')} "
            f"{data.get('product', {}).get('exptime_seconds', '')}-s "
            f"{data.get('product', {}).get('flux_column', '')}, sectors {data.get('sectors')}"
        ),
        "notes": " ".join(notes),
        "disclaimer": DISCLAIMER,
    }


class CandidateParameterExporter:
    def export(self, result: dict[str, Any], out_dir: Path) -> list[Path]:
        out_dir = Path(out_dir)
        fields = _fields(result)
        lines = [
            f"# Candidate parameter sheet: {result.get('target_key')}",
            "",
            f"> {DISCLAIMER}",
            "",
            "| Field | Value |",
            "|---|---|",
        ]
        for key, value in fields.items():
            if key == "disclaimer":
                continue
            shown = "not measured" if value is None and key.endswith("_err_hours") else value
            lines.append(f"| {key} | {shown} |")
        lines.append("")
        lines.append("Evidence: see `report.md`, `verdict.json` and `plots/` in this dossier.")
        lines.append("")
        return [
            write_json(out_dir / JSON_NAME, fields),
            write_text(out_dir / MARKDOWN_NAME, "\n".join(lines)),
        ]
