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
# v0.2.1, issue #23: how blind the holdout is, stated as the code does it (in a round that
# reaches the measurement, the whole hidden year is detrended, each window masked out to
# the inner edge of its baseline band, before any logged read).
HOLDOUT_BLINDNESS_NOTE = (
    "Each year is hidden in turn, and the ephemeris is fitted on the other years only. "
    "In each round that reaches the measurement, the whole hidden year is detrended once "
    "before any logged read, with each predicted window masked out to the inner edge of "
    "its baseline band; that step is not logged, and its outlier clipping can drop hidden "
    "cadences. After it, the test reads only the predicted transit windows, the phase-0.5 "
    "control windows and their baseline bands, and every such read is logged."
)
# Issue #23 after M4 pieces 4 and 5 (docs/validation/v0.2.1/reopen/m4-implementation-map.md,
# Amendment 17): only for reports with a round whose access log shows a replica read (the
# Codex stage review of 2026-10-18: a round of the corrections' holdout can stop before it).
HOLDOUT_REPLICA_NOTE = (
    "In rounds that reach hidden-noise estimation (v0.2.1 corrections switched on), replica "
    "spans placed from the same metadata away from the windows are masked in that detrending "
    "too and are read, logged, before any window, to measure the hidden year's noise."
)


def _read_replicas(rounds: list[dict]) -> bool:
    """Whether any round's access log shows a read of a replica span."""
    return any(
        str(entry.get("kind", "")).startswith("replica-")
        for r in rounds
        for entry in (r.get("access_log") or [])
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


METHOD_NOT_VALIDATED_NOTE = (
    "**Method status: `not_validated`.** No discovery method of Refute is validated: the v0.1 "
    "and v0.2 calibrations failed, and v0.2.1 ended as not approved ({reference}). A verdict "
    "here is the deterministic outcome of the declared tests, not a validated measurement."
)


def _discovery_lines(result: dict[str, Any]) -> list[str]:
    """The v0.4 block of a discover claim's report (issue #174)."""
    discovery = result.get("discovery") or {}
    temporal = result.get("temporal_diagnostic") or {}
    lines = [
        "> " + METHOD_NOT_VALIDATED_NOTE.format(reference=result.get("method_status_reference")),
        "",
        "## Roles and stage",
        "",
        f"- Meaning of SURVIVED in this claim: {discovery.get('survived_meaning', 'n/a')}",
        f"- Stage of this run: {discovery.get('stage')} of {discovery.get('last_stage')}",
        "- Decisive tests (the verdict aggregates only these): "
        + (", ".join(discovery.get("decisive_tests") or []) or "none"),
        "- Diagnostic tests (reported, never part of the verdict): "
        + (", ".join(discovery.get("diagnostic_tests") or []) or "none"),
    ]
    deferred = discovery.get("deferred_tests") or []
    if deferred:
        lines.append(
            "- Not run at this stage (INCONCLUSIVE with zero coverage, never PASS): "
            + ", ".join(deferred)
        )
    missing = discovery.get("missing_diagnostics") or []
    if missing:
        lines.append("- **Case incomplete:** required diagnostic(s) missing: " + ", ".join(missing))
    lines += [
        f"- Temporal diagnostic (`holdout_by_year`): **{temporal.get('state', 'not_run')}**. "
        "It never changes the verdict; a `pass` is not a signal confirmed in time, and a `fail` "
        "is not evidence against the signal, because the holdout is not validated.",
        "",
    ]
    return lines


BLEND_CAVEAT = (
    "A PASS of the pixel tests (`centroid_shift`, `aperture_depth`) does not exclude unresolved "
    "blends closer than the minimum offset of `centroid_shift` ({offset})."
)


def _bjd(value: Any) -> str:
    """v0.5 (#186): a BJD at full precision, never in short scientific notation."""
    return "n/a" if value is None else f"{float(value):.6f}"


def _v05_lines(result: dict[str, Any]) -> list[str]:
    """The v0.5 sections of a report (WP6): the sensitivity rule, the period and epoch from one
    fit, the SDE label, the cadences used per sector and the blend caveat."""
    v05 = result["v05"]
    lines = [
        "## v0.5 rules",
        "",
        "- Sensitivity rule (#185): a fatal or warning test PASSes only when it could have "
        "detected its declared alternative; otherwise it is INCONCLUSIVE, with the reason. A "
        "PASS means no failure was detected with the declared sensitivity, never that an effect "
        "is absent. Each test's sensitivity is in `verdict.json` (`tests[].sensitivity`).",
        f"- SDE: {v05.get('sde_note')}.",
    ]
    params = v05.get("parameters")
    if params:
        lines.append(
            f"- Period {params['period_days']!r} d (error {params['period_err_days']!r}) and epoch "
            f"{_bjd(params['epoch_bjd_tdb'])} BJD_TDB (error {params['epoch_err_days']!r}), from: "
            f"{params['source']}."
        )
    centroid = next((t for t in result.get("tests", []) if t["name"] == "centroid_shift"), None)
    offset = (centroid or {}).get("metrics", {}).get("min_offset_arcsec")
    shown = f"{offset:.1f} arcsec" if isinstance(offset, (int, float)) else "see its thresholds"
    lines += ["- " + BLEND_CAVEAT.format(offset=shown), "", "### Cadences used per sector", ""]
    lines += ["| Sector | Used | In span | Fraction |", "|---|---|---|---|"]
    for sector, row in (v05.get("cadences_per_sector") or {}).items():
        lines.append(
            f"| {sector} | {row['cadences_used']} | {row['cadences_in_span']} | "
            f"{row['fraction_used']:.3f} |"
        )
    lines.append("")
    return lines


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
    if "method_status" in result:
        lines += _discovery_lines(result)

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
    v05 = "v05" in result
    lines += ["## Signal", ""]
    if cand:
        published_t0 = (result.get("published") or {}).get("t0_bjd")
        epoch = (
            f"| Epoch (BJD_TDB) | {_bjd(cand['t0_bjd'])} | {_bjd(published_t0)} |"
            if v05
            else f"| Epoch (BJD_TDB) | {_fmt(cand['t0_bjd'], 5)} | {_fmt(published_t0, 5)} |"
        )
        lines += [
            "| Quantity | Found | Published |",
            "|---|---|---|",
            f"| Period (d) | {_fmt(cand['period'], 7)} | "
            f"{_fmt(comparison.get('published_period_days'), 7)} |",
            epoch,
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
    diagnostic = (
        set((result.get("discovery") or {}).get("diagnostic_tests") or []) if v05 else set()
    )
    for test in result.get("tests", []):
        # v0.5 (#186): a diagnostic test is labelled as such, never by its severity
        severity = "diagnostic" if test["name"] in diagnostic else test["severity"]
        lines.append(f"| {test['name']} | {test['status']} | {severity} | {test['message']} |")
    lines.append("")
    if v05:
        lines += _v05_lines(result)
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
        replicas = _read_replicas(rounds)
        lines += [
            "## Blind holdout by year",
            "",
            HOLDOUT_BLINDNESS_NOTE + (" " + HOLDOUT_REPLICA_NOTE if replicas else ""),
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
        if v05:
            # v0.5 (#190): whether a round tests the candidate's own ephemeris, and the depth
            # consistency it computed
            lines += [
                "| Hidden year | Train ephemeris matches the candidate "
                "| Depth consistency (sigma) |",
                "|---|---|---|",
            ]
            for row in result["v05"].get("holdout_rounds", []):
                lines.append(
                    f"| {row['hidden_year']} | {_fmt(row['train_matches_candidate'])} | "
                    f"{_fmt(row['depth_consistency_sigma'], 2)} |"
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
