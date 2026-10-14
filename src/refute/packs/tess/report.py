"""Markdown report for one TESS dossier."""

from __future__ import annotations

from typing import Any

SCOPE_NOTE = (
    "Refute is calibrated only in an easy regime defined by pre-registered selection "
    "filters (see the claim's protocol attachment): confirmed planets with orbital periods "
    "between 0.5 and 10 days, transit depths of at least 1000 ppm, TESS magnitude 12 or "
    "brighter, a single known planet in the system, and SPOC 2-minute data in at least two "
    "calendar years; false positives with the same period, depth and magnitude limits. "
    "The calibration says nothing about longer periods, shallower transits, fainter stars, "
    "multi-planet systems or other data products."
)

EB_CATALOG_DOWNGRADE_NOTE = (
    "The `eb_catalog` match is under the target's own TIC in a catalog built from the same "
    "TESS photometry, so it is not evidence independent of the light curve: from v0.2.1 "
    "such a match is a warning, not a fatal failure."
)
NOT_A_DISCOVERY = (
    "A verdict is about a claim, never about its authors. Refute produces candidates and "
    "verdicts only: nothing here is a confirmed discovery, and nothing has been submitted "
    "to any scientific body."
)


def _fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if value != value:  # NaN
            return "n/a"
        if abs(value) >= 1e5 or (abs(value) < 1e-3 and value != 0):
            return f"{value:.{digits}e}"
        return f"{value:.{digits}f}"
    return str(value)


def render_report(result: dict[str, Any], context: dict[str, Any]) -> str:
    lines = [
        f"# {result.get('target_key')}: {result.get('verdict')}",
        "",
        f"**Verdict: `{result.get('verdict')}`.** {result.get('verdict_reason', '')}",
        "",
        f"> {NOT_A_DISCOVERY}",
        "",
    ]
    if context.get("claim_kind") == "calibration":
        lines += [f"> **Scope.** {SCOPE_NOTE}", ""]

    lines += [
        "## Claim",
        "",
        f"- Claim: `{context.get('claim_id')}` ({context.get('claim_kind')})",
        f"- Hypothesis: {context.get('hypothesis', '').strip()}",
        f"- Target: {result.get('target_name') or result.get('target_key')} "
        f"(TIC {result.get('tic_id')}, calibration role: {result.get('target_kind')})",
        "",
    ]
    if result.get("status") == "ERROR":
        lines += ["## Error", "", "```", str(result.get("error", "")).strip(), "```", ""]

    cand = result.get("candidate")
    comparison = result.get("period_comparison") or {}
    lines += ["## Signal", ""]
    if cand:
        lines += [
            "| Quantity | Found | Published |",
            "|---|---|---|",
            f"| Period (d) | {_fmt(cand['period'], 7)} | "
            f"{_fmt(comparison.get('published_period_days'), 7)} |",
            f"| Epoch (BJD_TDB) | {_fmt(cand['t0_bjd'], 5)} | "
            f"{_fmt((result.get('published') or {}).get('t0_bjd'), 5)} |",
            f"| Duration (h) | {_fmt(cand['duration_hours'], 3)} | "
            f"{_fmt((result.get('published') or {}).get('duration_hours'), 3)} |",
            f"| Depth (ppm) | {_fmt(cand['depth_ppm'], 1)} | "
            f"{_fmt((result.get('published') or {}).get('depth_ppm'), 1)} |",
            f"| SNR | {_fmt(cand['snr'], 1)} | |",
            "",
            f"- Relative period error: {_fmt(comparison.get('relative_error'), 3)} "
            f"(tolerance {_fmt(comparison.get('tolerance'))}, within: "
            f"{_fmt(comparison.get('within_tolerance'))}, "
            f"alias: {comparison.get('alias') or 'none'})",
            "",
        ]
    else:
        lines += ["No candidate signal was found.", ""]

    lines += ["## Gauntlet", "", "| Test | Status | Severity | Result |", "|---|---|---|---|"]
    for test in result.get("tests", []):
        lines.append(
            f"| {test['name']} | {test['status']} | {test['severity']} | {test['message']} |"
        )
    lines.append("")
    if any(
        t["name"] == "eb_catalog" and (t.get("metrics") or {}).get("downgraded")
        for t in result.get("tests", [])
    ):
        lines += [EB_CATALOG_DOWNGRADE_NOTE, ""]
    if not result.get("eb_catalog_configured"):
        lines += [
            "The `eb_catalog` test is not part of this gauntlet: the claim attaches no "
            "eclipsing-binary catalog.",
            "",
        ]
    warnings = result.get("data_quality_warnings") or []
    if warnings:
        lines += ["## Data-quality warnings (not tests)", ""] + [f"- {w}" for w in warnings] + [""]

    rounds = result.get("holdout_rounds") or []
    if rounds:
        lines += [
            "## Blind holdout by year",
            "",
            "Each year is hidden in turn. The ephemeris is fitted on the other years only;",
            "the hidden year is read only inside the predicted windows.",
            "",
            "| Hidden year | Status | Windows with data | Hidden SNR | Control SNR (phase 0.5) |",
            "|---|---|---|---|---|",
        ]
        for r in rounds:
            m = r.get("metrics", {})
            lines.append(
                f"| {r['hidden_year']} | {r['status']} | {_fmt(m.get('n_windows_with_data'))} | "
                f"{_fmt(m.get('hidden_snr'), 1)} | {_fmt(m.get('control_phase05_snr'), 1)} |"
            )
        lines.append("")

    data = result.get("data_summary") or {}
    product = data.get("product") or {}
    star = data.get("star") or {}
    lines += [
        "## Data",
        "",
        f"- Product: {product.get('product')}, flux column `{product.get('flux_column')}`, "
        f"quality bitmask `{product.get('quality_bitmask')}` "
        f"(value {product.get('quality_bitmask_value')}), read with {product.get('reader')}",
        f"- Sectors: {data.get('sectors')}; observing years: {data.get('years')}; "
        f"cadences used: {data.get('n_cadences')}",
        f"- Stellar parameters: {star.get('stellar_parameters_source')}, TIC version "
        f"{star.get('tic_version')}, retrieved {star.get('retrieved_utc')}: "
        f"R = {_fmt(star.get('radius_rsun'), 3)} +- {_fmt(star.get('radius_err_rsun'), 3)} Rsun, "
        f"M = {_fmt(star.get('mass_msun'), 3)} Msun",
        "- File hashes and source URLs: `data/manifest.json`",
        "",
    ]
    plots = result.get("plots") or []
    if plots:
        lines += ["## Plots", ""] + [f"- [{p}]({p})" for p in plots] + [""]
    lines += [
        "## Independent review",
        "",
        "Reports by fresh, read-only reviewer sessions are attached after the verdict, in",
        "`review/` (index: [review/index.md](review/index.md)), following",
        "`docs/reviewer-protocol.md`. Reviewers raise objections; they never change the",
        "verdict. `refute check-dossier` verifies that the analysis and `verdict.json` are",
        "unchanged since the reviews were attached. No `review/` folder means no review.",
        "",
    ]
    provenance = result.get("provenance") or {}
    lines += [
        "## Provenance",
        "",
        f"- Claim SHA-256: `{provenance.get('claim_sha256')}`",
        f"- Code SHA-256: `{provenance.get('code_sha256')}`",
        f"- Lock commit: `{context.get('lock_git_commit')}`; run commit: "
        f"`{context.get('run_git_commit')}`",
        f"- Run: `{provenance.get('run_id')}`, Refute {provenance.get('refute_version')}",
        "- Reproduce: see `REPRODUCE.md`. Integrity: `MANIFEST.sha256`.",
        "",
    ]
    return "\n".join(lines)
