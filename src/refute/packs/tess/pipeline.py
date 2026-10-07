"""Analysis of one target: search, gauntlet a-d, blind holdout, verdict.

The holdout (test e) is called with the raw light curve and sector metadata only.
It never receives the candidate found by the global search.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from refute.core.verdict import Severity, TestResult, TestStatus, aggregate
from refute.packs.tess.detrend import detrend
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


def attack_candidate(
    data: TessData, candidate: Candidate | None, plan: TessTestPlan
) -> GauntletOutcome:
    """Gauntlet tests a-d against a candidate found on all data."""
    gp = plan.gauntlet
    if candidate is None:
        tests = [
            check_snr(None, gp.snr),
            _not_run("odd_even", Severity.FATAL, "no candidate"),
            _not_run("secondary_eclipse", Severity.FATAL, "no candidate"),
            _not_run("plausibility", Severity.FATAL, "no candidate"),
        ]
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


def analyze_data(
    data: TessData, plan: TessTestPlan, search_fn: SearchFn = search_period
) -> Analysis:
    flat = detrend(data.lc, plan.detrend)
    search = search_fn(flat, plan.search)
    gauntlet = attack_candidate(data, search.candidate, plan)
    # Blind holdout: raw data and sector metadata only. Never the global candidate.
    holdout = run_holdout(data.lc, data.sectors, plan)
    tests = [*gauntlet.tests, holdout.test]
    verdict, reason = aggregate(tests)
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
    return {
        "schema": "refute-tess-data-manifest-1",
        "target_key": data.target_key,
        "retrieved_utc": data.manifest.get("retrieved_utc"),
        "query": data.manifest.get("query"),
        "product": data.product.to_dict(),
        "files": files,
        "star": data.star.to_dict() if data.star else None,
        "software": data.manifest.get("software"),
    }


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
        analysis = analyze_data(data, plan)
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
