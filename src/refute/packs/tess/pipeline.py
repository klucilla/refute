"""Analysis of one target: search, gauntlet a-d, v0.2 battery, blind holdout, verdict.

The holdout (test e) is called with the raw light curve and sector metadata only.
It never receives the candidate found by the global search, nor the pixel data,
auxiliary columns, neighbors or catalogs used by the v0.2 battery.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from refute.core.verdict import Severity, TestResult, TestStatus, aggregate, enforce_coverage
from refute.packs.tess.battery import (
    check_aperture_depth,
    check_centroid_shift,
    check_nearby_contamination,
    check_period_alias,
    check_systematics,
)
from refute.packs.tess.detrend import detrend
from refute.packs.tess.ebcatalog import EbEntry, check_eb_catalog, load_catalogs, load_scan
from refute.packs.tess.ephemeris import Ephemeris, fit_linear_ephemeris, measure_transit_times
from refute.packs.tess.events import EventDepths, per_event_depths, per_point_sigma, transit_mask
from refute.packs.tess.gauntlet import (
    check_odd_even,
    check_plausibility,
    check_secondary_eclipse,
    check_snr,
    star_inputs,
)
from refute.packs.tess.holdout import HoldoutOutcome, run_holdout
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.search import SearchResult, finalize_candidate, search_period
from refute.packs.tess.types import BTJD_OFFSET, Candidate, LightCurveData, TessData

SearchFn = Callable[[LightCurveData, Any], SearchResult]


@dataclass
class GauntletOutcome:
    candidate: Candidate | None
    flattened: LightCurveData | None
    primary: EventDepths | None
    secondary: EventDepths | None
    tests: list[TestResult]
    ephemeris: Ephemeris | None


@dataclass
class Analysis:
    search: SearchResult
    flattened_search: LightCurveData
    gauntlet: GauntletOutcome
    holdout: HoldoutOutcome
    tests: list[TestResult]
    verdict: str
    verdict_reason: str
    extras: dict[str, Any] = field(default_factory=dict)


def _not_run(name: str, severity: Severity, reason: str) -> TestResult:
    return TestResult(name, TestStatus.INCONCLUSIVE, severity, reason)


BATTERY_TESTS = (
    ("centroid_shift", Severity.FATAL),
    ("aperture_depth", Severity.FATAL),
    ("nearby_contamination", Severity.WARNING),
    ("period_alias", Severity.FATAL),
    ("systematics", Severity.WARNING),
)


def battery_tests(
    data: TessData,
    candidate: Candidate,
    plan: TessTestPlan,
    catalogs: list[EbEntry] | None = None,
    catalog_scan: dict | None = None,
) -> list[TestResult]:
    """The v0.2 battery against the final candidate (see docs/gauntlet-tess-v0.2.md)."""
    aux = data.aux
    pixels = aux.pixels if aux else []
    crowds = [a.crowdsap for a in aux.sectors if a.crowdsap is not None] if aux else []
    tests = [
        check_centroid_shift(pixels, candidate, plan),
        check_aperture_depth(pixels, candidate, plan),
        check_nearby_contamination(
            aux.neighbors if aux else None,
            data.star,
            candidate.depth,
            crowds,
            plan.gauntlet.nearby_contamination,
            aux.neighbor_radius_arcsec if aux else None,
        ),
        check_period_alias(data.lc, candidate, plan),
        check_systematics(aux.sectors if aux else [], candidate, plan),
    ]
    if catalogs is not None:
        tests.append(
            check_eb_catalog(
                catalogs,
                catalog_scan,
                data.target_key,
                data.star,
                candidate.period,
                plan.gauntlet.eb_catalog,
            )
        )
    return tests


def attack_candidate(
    data: TessData,
    candidate: Candidate | None,
    plan: TessTestPlan,
    catalogs: list[EbEntry] | None = None,
    catalog_scan: dict | None = None,
) -> GauntletOutcome:
    """Gauntlet tests a-d and the v0.2 battery against a candidate found on all data.

    ``catalogs`` is None when the claim has no eclipsing-binary catalog attached;
    the ``eb_catalog`` test is then not part of the gauntlet (the report says so).
    """
    gp = plan.gauntlet
    if candidate is None:
        tests = [
            check_snr(None, gp.snr),
            _not_run("odd_even", Severity.FATAL, "no candidate"),
            _not_run("secondary_eclipse", Severity.FATAL, "no candidate"),
            _not_run("plausibility", Severity.FATAL, "no candidate"),
            *(_not_run(name, severity, "no candidate") for name, severity in BATTERY_TESTS),
        ]
        if catalogs is not None:
            tests.append(_not_run("eb_catalog", Severity.FATAL, "no candidate"))
        return GauntletOutcome(None, None, None, None, tests, None)

    cadence = plan.data.exptime_seconds / 86400.0
    mask_half = plan.detrend.transit_mask_half_width_durations * candidate.duration
    mask = transit_mask(data.lc.time, candidate.period, candidate.t0, mask_half)
    flat = detrend(data.lc, plan.detrend, mask=mask)
    sigma = per_point_sigma(
        flat, transit_mask(flat.time, candidate.period, candidate.t0, mask_half)
    )
    final = finalize_candidate(
        flat, candidate.period, candidate.duration, plan.search, candidate.sde, sigma
    )
    primary = per_event_depths(
        flat, final.period, final.t0, final.duration, cadence, gp.events, 0.0, sigma
    )
    secondary = per_event_depths(
        flat, final.period, final.t0, final.duration, cadence, gp.events, 0.5, sigma
    )
    tests = [
        check_snr(final, gp.snr),
        check_odd_even(primary, gp.odd_even),
        check_secondary_eclipse(primary, secondary, gp.secondary_eclipse),
        check_plausibility(final, data.star, gp.plausibility),
        *battery_tests(data, final, plan, catalogs, catalog_scan),
    ]
    times = measure_transit_times(
        flat,
        final.period,
        final.t0,
        final.duration,
        final.depth,
        sigma,
        cadence_days=cadence,
        step_minutes=gp.holdout_by_year.timing_step_minutes,
        scan_half_width_durations=gp.holdout_by_year.timing_scan_half_width_durations,
    )
    ephemeris = fit_linear_ephemeris(times) if len(times) >= 2 else None
    return GauntletOutcome(final, flat, primary, secondary, tests, ephemeris)


def expected_tests(catalogs_configured: bool) -> list[str]:
    """Every test a complete TESS analysis must contain."""
    names = ["snr", "odd_even", "secondary_eclipse", "plausibility"]
    names += [name for name, _ in BATTERY_TESTS]
    if catalogs_configured:
        names.append("eb_catalog")
    return [*names, "holdout_by_year"]


def analyze_data(
    data: TessData,
    plan: TessTestPlan,
    search_fn: SearchFn = search_period,
    catalogs: list[EbEntry] | None = None,
    catalog_scan: dict | None = None,
) -> Analysis:
    flat = detrend(data.lc, plan.detrend)
    search = search_fn(flat, plan.search)
    gauntlet = attack_candidate(data, search.candidate, plan, catalogs, catalog_scan)
    # Blind holdout: raw data and sector metadata only. Never the global candidate.
    holdout = run_holdout(data.lc, data.sectors, plan)
    # Domain-agnostic coverage rule: a PASS that examined nothing is INCONCLUSIVE.
    tests = enforce_coverage([*gauntlet.tests, holdout.test])
    verdict, reason = aggregate(tests, expected=expected_tests(catalogs is not None))
    return Analysis(search, flat, gauntlet, holdout, tests, verdict.value, reason)


def period_comparison(
    published: float | None, found: float | None, tolerance: float | None
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "published_period_days": published,
        "found_period_days": found,
        "relative_error": None,
        "tolerance": tolerance,
        "within_tolerance": None,
        "alias": None,
    }
    if published is None or found is None or published <= 0:
        return out
    out["relative_error"] = abs(found - published) / published
    check = tolerance if tolerance is not None else 0.001
    for name, factor in (("P", 1.0), ("2P", 2.0), ("P/2", 0.5), ("3P", 3.0), ("P/3", 1.0 / 3.0)):
        if abs(found - factor * published) / (factor * published) <= check:
            out["alias"] = name
            break
    if tolerance is not None:
        out["within_tolerance"] = out["relative_error"] <= tolerance
    return out


def data_manifest(data: TessData) -> dict[str, Any]:
    files_by_name = {f["name"]: f for f in data.manifest.get("files", [])}
    files = []
    for sector in data.sectors:
        record = files_by_name.get(sector.filename, {})
        files.append(
            {
                "name": sector.filename,
                "sha256": record.get("sha256", sector.sha256),
                "sector": sector.sector,
                "year": sector.year,
                "t_start_btjd": sector.t_start,
                "t_end_btjd": sector.t_end,
                "n_cadences_used": sector.n_points,
                "url": record.get("url", sector.url),
                "data_uri": record.get("data_uri"),
            }
        )
    for record in data.manifest.get("pixel_files", []):
        files.append(
            {
                "name": record["name"],
                "sha256": record["sha256"],
                "sector": record["sector"],
                "kind": "target pixel file",
                "url": record.get("url"),
                "data_uri": record.get("data_uri"),
            }
        )
    return {
        "schema": "refute-tess-data-manifest-2",
        "target_key": data.target_key,
        "retrieved_utc": data.manifest.get("retrieved_utc"),
        "query": data.manifest.get("query"),
        "product": data.product.to_dict(),
        "files": files,
        "star": data.star.to_dict() if data.star else None,
        "neighbors": data.manifest.get("neighbors"),
        "software": data.manifest.get("software"),
    }


def data_quality_warnings(target: dict[str, Any], data: TessData, plan: TessTestPlan) -> list[str]:
    """Warnings for the report. They are not tests and never change a verdict."""
    warnings = []
    star = data.star
    catalog = target.get("catalog") or {}
    reference = None
    for key in ("sy_tmag", "TESS Mag"):
        try:
            reference = float(catalog[key])
            break
        except (KeyError, TypeError, ValueError):
            continue
    limit = plan.gauntlet.plausibility.max_tmag_mismatch
    if star is not None and star.tmag is not None and reference is not None:
        if abs(star.tmag - reference) > limit:
            warnings.append(
                f"TIC Tmag {star.tmag:.2f} differs from the target's catalog Tmag "
                f"{reference:.2f} by more than {limit:g} mag: the TIC row may describe "
                "another source"
            )
    if star is not None and star.disposition:
        warnings.append(f"TIC row disposition: {star.disposition}")
    return warnings


def build_result(
    target: dict[str, Any],
    data: TessData,
    plan: TessTestPlan,
    analysis: Analysis,
    context: dict[str, Any],
) -> dict[str, Any]:
    candidate = analysis.gauntlet.candidate
    criteria = context.get("pass_criteria") or {}
    published = target.get("published", {}).get("period_days")
    comparison = period_comparison(
        published, candidate.period if candidate else None, criteria.get("period_tolerance")
    )
    key_values: dict[str, Any] = {}
    if candidate is not None:
        key_values.update(
            {
                "period_days": candidate.period,
                "t0_btjd": candidate.t0,
                "duration_days": candidate.duration,
                "depth": candidate.depth,
                "snr": candidate.snr,
            }
        )
    for round_ in analysis.holdout.rounds:
        key_values[f"holdout_{round_.hidden_year}_snr"] = round_.metrics.get("hidden_snr")
    ephemeris = analysis.gauntlet.ephemeris
    return {
        "schema": "refute-tess-verdict-1",
        "target_key": target["key"],
        "tic_id": int(target["tic_id"]),
        "target_kind": target.get("kind"),
        "target_name": target.get("name"),
        "status": "OK",
        "error": None,
        "verdict": analysis.verdict,
        "verdict_reason": analysis.verdict_reason,
        "candidate": candidate.to_dict() if candidate else None,
        "global_ephemeris": (
            {**ephemeris.to_dict(), "t_ref_bjd": ephemeris.t_ref + BTJD_OFFSET}
            if ephemeris
            else None
        ),
        "published": target.get("published"),
        "period_comparison": comparison,
        "tests": [t.to_dict() for t in analysis.tests],
        "holdout_rounds": [r.to_dict() for r in analysis.holdout.rounds],
        "search_diagnostics": analysis.search.diagnostics,
        "data_summary": {
            "n_cadences": len(data.lc),
            "sectors": [s.sector for s in data.sectors],
            "years": data.lc.years,
            "product": data.product.to_dict(),
            "star": star_inputs(data.star),
        },
        "key_values": key_values,
        "data_quality_warnings": data_quality_warnings(target, data, plan),
        "eb_catalog_configured": analysis.extras.get("eb_catalog_configured", False),
        "expected_tests": expected_tests(analysis.extras.get("eb_catalog_configured", False)),
        "test_plan": plan.model_dump(mode="json"),
        "provenance": {
            k: context.get(k)
            for k in (
                "claim_id",
                "claim_sha256",
                "code_sha256",
                "run_id",
                "lock_git_commit",
                "run_git_commit",
                "refute_version",
                "pack",
            )
        },
    }


class TessSearch:
    def run(self, data: TessData, params: dict[str, Any]) -> SearchResult:
        plan = TessTestPlan.model_validate(params)
        return search_period(detrend(data.lc, plan.detrend), plan.search)


class TessGauntlet:
    def run(
        self, data: TessData, candidate: Candidate | None, target: dict, params: dict
    ) -> list[TestResult]:
        return attack_candidate(data, candidate, TessTestPlan.model_validate(params)).tests


class TessHoldout:
    def run(self, data: TessData, params: dict[str, Any]) -> HoldoutOutcome:
        return run_holdout(data.lc, data.sectors, TessTestPlan.model_validate(params))


class TessAnalyzer:
    def analyze(
        self,
        target: dict[str, Any],
        data: TessData,
        test_plan: dict[str, Any],
        context: dict[str, Any],
        writer: Any,
    ) -> dict[str, Any]:
        from refute.packs.tess import plots

        plan = TessTestPlan.model_validate(test_plan)
        writer.write_json("data/manifest.json", data_manifest(data))
        catalog_paths = [
            writer.root / "attachments" / a["path"]
            for a in context.get("attachments", [])
            if a.get("role") == "eb-catalog"
        ]
        catalogs = load_catalogs(catalog_paths) if catalog_paths else None
        scan_paths = [
            writer.root / "attachments" / a["path"]
            for a in context.get("attachments", [])
            if a.get("role") == "eb-catalog-scan"
        ]
        catalog_scan = load_scan(scan_paths[0]) if scan_paths else None
        analysis = analyze_data(data, plan, catalogs=catalogs, catalog_scan=catalog_scan)
        analysis.extras["eb_catalog_configured"] = catalogs is not None
        result = build_result(target, data, plan, analysis, context)
        result["plots"] = plots.write_all(writer, data, analysis, plan)
        return result

    def error_result(
        self, target: dict[str, Any], error: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        criteria = context.get("pass_criteria") or {}
        return {
            "schema": "refute-tess-verdict-1",
            "target_key": target["key"],
            "tic_id": int(target["tic_id"]),
            "target_kind": target.get("kind"),
            "target_name": target.get("name"),
            "status": "ERROR",
            "error": error,
            "verdict": "INCONCLUSIVE",
            "verdict_reason": "the analysis could not be completed (see error)",
            "candidate": None,
            "global_ephemeris": None,
            "published": target.get("published"),
            "period_comparison": period_comparison(
                target.get("published", {}).get("period_days"),
                None,
                criteria.get("period_tolerance"),
            ),
            "tests": [],
            "holdout_rounds": [],
            "key_values": {},
            "plots": [],
            "provenance": {
                k: context.get(k)
                for k in ("claim_id", "claim_sha256", "code_sha256", "run_id", "refute_version")
            },
        }

    def report(self, result: dict[str, Any], context: dict[str, Any]) -> str:
        from refute.packs.tess.report import render_report

        return render_report(result, context)
