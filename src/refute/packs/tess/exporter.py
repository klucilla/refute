"""CTOI-oriented exporter. It writes files for a human. It never submits anything.

The output lists the fields a person needs to prepare an ExoFOP-TESS Community
TOI (CTOI) entry by hand, plus the evidence behind them. This module contains no
network code on purpose.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from refute.core.io import write_json, write_text

DISCLAIMER = (
    "NOTHING HAS BEEN SUBMITTED. Refute never submits anything to ExoFOP or any other "
    "body. This file only helps a human prepare a submission. A person must review the "
    "full dossier, check the target against the current TOI and CTOI lists, and decide. "
    "This is a candidate signal and a verdict on a claim, never a confirmed discovery."
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
        notes.append(
            "Calibration target: already catalogued; a CTOI submission is not appropriate."
        )
    return {
        "submitted": False,
        "tic_id": result.get("tic_id"),
        "period_days": cand.get("period"),
        "period_err_days": eph.get("period_err"),
        "epoch_bjd_tdb": eph.get("t_ref_bjd", cand.get("t0_bjd")),
        "epoch_err_days": eph.get("t_ref_err"),
        "duration_hours": cand.get("duration_hours"),
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


class CtoiExporter:
    def export(self, result: dict[str, Any], out_dir: Path) -> list[Path]:
        out_dir = Path(out_dir)
        fields = _fields(result)
        lines = [
            f"# CTOI preparation sheet: {result.get('target_key')}",
            "",
            f"> {DISCLAIMER}",
            "",
            "| Field | Value |",
            "|---|---|",
        ]
        for key, value in fields.items():
            if key == "disclaimer":
                continue
            lines.append(f"| {key} | {value} |")
        lines.append("")
        lines.append("Evidence: see `report.md`, `verdict.json` and `plots/` in this dossier.")
        lines.append("")
        return [
            write_json(out_dir / "ctoi_fields.json", fields),
            write_text(out_dir / "ctoi_summary.md", "\n".join(lines)),
        ]
