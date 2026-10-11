"""Evaluation of a TESS calibration claim from per-target results.

Definitions (also written into the claim):

- *recovered*: a known planet whose found period is within ``period_tolerance``
  (relative) of the published period. Aliases (2P, P/2, ...) do not count.
- *flagged*: a known false positive whose verdict is ``REFUTED``. From v0.2 the
  claim may list ``flag_excluded_tests``: the verdict used for this count is then
  recomputed with the same deterministic rules from the other tests only (the
  "signal verdict"). The count with every test is reported as information.
  From v0.2.1 the claim may set ``flag_requires_signal_recovery``: a false positive
  then counts as flagged only if its signal is also *recovered*, that is, the found
  period matches the catalogued period at one of ``flag_signal_period_factors``
  (default P, 2P, P/2) within ``period_tolerance``. A false positive whose
  catalogued signal was not the one analyzed stays in the denominator. The count
  under the v0.2 definition is reported as information.
- *refuted planet*: a known planet whose verdict is ``REFUTED``.

The claim passes only if all three criteria hold, on a complete run of every
calibration target. Errors count against the claim (not recovered, not flagged).
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from refute.core.claim import LoadedClaim
from refute.core.verdict import Severity, TestResult, aggregate
from refute.packs.tess.params import DEFAULT_SIGNAL_PERIOD_FACTORS
from refute.packs.tess.pipeline import matching_factor
from refute.packs.tess.report import SCOPE_NOTE
from refute.packs.tess.schema import load_targets_file


def signal_verdict(result: dict[str, Any], excluded: list[str]) -> str | None:
    """Verdict recomputed without the ``excluded`` tests (same aggregation rules,
    including the coverage rule and the expected-test check)."""
    if not excluded:
        return result.get("verdict")
    tests = [TestResult.from_dict(t) for t in result.get("tests", []) if t["name"] not in excluded]
    if not any(t.severity is Severity.GATE for t in tests):
        return result.get("verdict")
    expected = [n for n in result.get("expected_tests") or [] if n not in excluded]
    return aggregate(tests, expected=expected)[0].value


def _recovered(result: dict[str, Any], tolerance: float) -> bool:
    comparison = result.get("period_comparison") or {}
    error = comparison.get("relative_error")
    return error is not None and error <= tolerance


def signal_recovered(result: dict[str, Any], tolerance: float, factors: list[float]) -> bool:
    """Whether the analyzed signal is the catalogued one: the found period matches the
    published period at one of ``factors``. A missing period is not recovered."""
    comparison = result.get("period_comparison") or {}
    factor = matching_factor(
        comparison.get("published_period_days"),
        comparison.get("found_period_days"),
        factors,
        tolerance,
    )
    return factor is not None


def _format_factors(factors: list[float]) -> str:
    return ", ".join(format(f, "g") for f in factors)


class TessCalibrator:
    def evaluate(
        self, loaded: LoadedClaim, results: list[dict[str, Any]], complete: bool
    ) -> dict[str, Any]:
        criteria = loaded.claim.pass_criteria or {}
        tolerance = float(criteria["period_tolerance"])
        planets = [r for r in results if r.get("target_kind") == "planet"]
        fps = [r for r in results if r.get("target_kind") == "false_positive"]
        excluded = list(criteria.get("flag_excluded_tests") or [])
        identity = bool(criteria.get("flag_requires_signal_recovery", False))
        factors = list(criteria.get("flag_signal_period_factors") or DEFAULT_SIGNAL_PERIOD_FACTORS)
        recovered = [r for r in planets if _recovered(r, tolerance)]
        flagged_v02 = [r for r in fps if signal_verdict(r, excluded) == "REFUTED"]
        not_recovered = [r for r in fps if not signal_recovered(r, tolerance, factors)]
        flagged = flagged_v02
        if identity:
            flagged = [r for r in flagged_v02 if signal_recovered(r, tolerance, factors)]
        flagged_all = [r for r in fps if r.get("verdict") == "REFUTED"]
        refuted_planets = [r for r in planets if r.get("verdict") == "REFUTED"]
        qualifiers = ["signal recovered"] if identity else []
        if excluded:
            qualifiers.append(f"without {', '.join(excluded)}")
        flag_name = "flagged false positives"
        if qualifiers:
            flag_name += f" ({'; '.join(qualifiers)})"

        checks = [
            {
                "criterion": "recovered planets",
                "value": len(recovered),
                "of": len(planets),
                "requirement": f">= {criteria['min_recovered_planets']}",
                "passed": len(recovered) >= criteria["min_recovered_planets"],
            },
            {
                "criterion": flag_name,
                "value": len(flagged),
                "of": len(fps),
                "requirement": f">= {criteria['min_flagged_false_positives']}",
                "passed": len(flagged) >= criteria["min_flagged_false_positives"],
            },
            {
                "criterion": "refuted planets (degeneracy guard)",
                "value": len(refuted_planets),
                "of": len(planets),
                "requirement": f"<= {criteria['max_refuted_planets']}",
                "passed": len(refuted_planets) <= criteria["max_refuted_planets"],
            },
        ]
        population_ok = (
            len(planets) == criteria["expected_planets"]
            and len(fps) == criteria["expected_false_positives"]
        )
        if not complete:
            outcome = "NOT_EVALUATED"
            note = "partial run (--target): the self-claim is evaluated only on a complete run"
        elif not population_ok:
            outcome = "NOT_EVALUATED"
            note = (
                f"population mismatch: {len(planets)} planets and {len(fps)} false positives, "
                f"expected {criteria['expected_planets']} and "
                f"{criteria['expected_false_positives']}"
            )
        else:
            outcome = "PASS" if all(c["passed"] for c in checks) else "FAIL"
            note = "all criteria hold" if outcome == "PASS" else "at least one criterion failed"

        rows = []
        for r in results:
            comparison = r.get("period_comparison") or {}
            row = {
                "target": r.get("target_key"),
                "name": r.get("target_name"),
                "kind": r.get("target_kind"),
                "published_period_days": comparison.get("published_period_days"),
                "found_period_days": comparison.get("found_period_days"),
                "relative_error": comparison.get("relative_error"),
                "alias": comparison.get("alias"),
                "recovered": _recovered(r, tolerance) if r.get("target_kind") == "planet" else None,
                "verdict": r.get("verdict"),
                "signal_verdict": signal_verdict(r, excluded),
                "status": r.get("status"),
                "tests": {t["name"]: t["status"] for t in r.get("tests", [])},
            }
            if identity:
                row["signal_recovered"] = (
                    signal_recovered(r, tolerance, factors)
                    if r.get("target_kind") == "false_positive"
                    else None
                )
            rows.append(row)
        verdicts = Counter((r.get("target_kind"), r.get("verdict")) for r in results)
        inconclusive_reasons = {
            r.get("target_key"): [
                f"{t['name']}: {t['message']}"
                for t in r.get("tests", [])
                if t["status"] == "INCONCLUSIVE"
            ]
            or [r.get("verdict_reason")]
            for r in results
            if r.get("verdict") == "INCONCLUSIVE"
        }
        holdout = [
            t["status"]
            for r in results
            for t in r.get("tests", [])
            if t["name"] == "holdout_by_year"
        ]
        targets_attachment = loaded.attachment_by_role("targets")
        selection = {}
        if targets_attachment is not None:
            selection = load_targets_file(loaded.attachment_path(targets_attachment)).selection
        information: dict[str, Any] = {
            "flag_excluded_tests": excluded,
            "flagged_false_positives_with_every_test": len(flagged_all),
            "of": len(fps),
        }
        if identity:
            information["flag_signal_period_factors"] = factors
            information["false_positives_signal_not_recovered"] = {
                "count": len(not_recovered),
                "targets": [r.get("target_key") for r in not_recovered],
            }
            information["flagged_without_signal_identity"] = len(flagged_v02)
        return {
            "schema": "refute-tess-calibration-summary-1",
            "claim_id": loaded.claim.id,
            "hypothesis": loaded.claim.hypothesis.strip(),
            "definitions": loaded.claim.definitions,
            "pass_criteria": criteria,
            "self_claim": {"result": outcome, "note": note, "criteria": checks},
            "information": information,
            "complete_run": complete,
            "targets": rows,
            "diagnostics": {
                "verdicts_by_kind": {
                    f"{k}:{v}": n for (k, v), n in sorted(verdicts.items(), key=str)
                },
                "planets_survived": sum(1 for r in planets if r.get("verdict") == "SURVIVED"),
                "holdout_statuses": dict(Counter(holdout)),
                "errors": [r.get("target_key") for r in results if r.get("status") == "ERROR"],
                "inconclusive_reasons": inconclusive_reasons,
                "eb_catalog_downgraded": [
                    r.get("target_key")
                    for r in results
                    if any(
                        t["name"] == "eb_catalog" and (t.get("metrics") or {}).get("downgraded")
                        for t in r.get("tests", [])
                    )
                ],
            },
            "scope_note": SCOPE_NOTE,
            "selection_filters": selection,
        }

    def summary_markdown(self, summary: dict[str, Any]) -> str:
        claim = summary["self_claim"]
        lines = [
            f"# Calibration summary: {summary['claim_id']}",
            "",
            f"## Self-claim result: **{claim['result']}**",
            "",
            f"> {summary['hypothesis']}",
            "",
            f"{claim['note']}.",
            "",
            "| Criterion | Value | Requirement | Passed |",
            "|---|---|---|---|",
        ]
        for check in claim["criteria"]:
            lines.append(
                f"| {check['criterion']} | {check['value']} of {check['of']} | "
                f"{check['requirement']} | {'yes' if check['passed'] else 'no'} |"
            )
        lines += [
            "",
            f"> **Scope.** {summary['scope_note']}",
            "",
        ]
        info = summary.get("information") or {}
        if info.get("flag_excluded_tests"):
            lines += [
                "Information (not a criterion): "
                f"{info['flagged_false_positives_with_every_test']} of {info['of']} false "
                "positives are REFUTED when every test counts, including "
                f"{', '.join(info['flag_excluded_tests'])}.",
                "",
            ]
        identity = "flagged_without_signal_identity" in info
        if identity:
            missed = info["false_positives_signal_not_recovered"]
            lines += [
                "Definition change since v0.2: a false positive counts as flagged only if the "
                "analyzed period matches the catalogued period "
                f"(factors {_format_factors(info['flag_signal_period_factors'])}). "
                f"{missed['count']} of {info['of']} false positives were not recovered; under "
                f"the v0.2 definition {info['flagged_without_signal_identity']} would count as "
                "flagged.",
                "",
            ]
        signal_header = " Signal recovered |" if identity else ""
        lines += [
            "## Targets",
            "",
            "| Target | Name | Kind | Published P (d) | Found P (d) | Rel. error | Alias | "
            f"Recovered |{signal_header} Verdict | Signal verdict | Tests not passed |",
            "|---|---|---|---|---|---|---|---|---|---|---|" + ("---|" if identity else ""),
        ]
        for row in summary["targets"]:
            tests = row["tests"]

            def num(value: Any, fmt: str) -> str:
                return format(value, fmt) if isinstance(value, int | float) else "n/a"

            marks = {True: "yes", False: "no", None: "-"}
            recovered = marks[row["recovered"]]
            signal_cell = f" {marks[row.get('signal_recovered')]} |" if identity else ""
            not_passed = ", ".join(f"{k} {v}" for k, v in tests.items() if v != "PASS") or "-"
            lines.append(
                f"| {row['target']} | {row['name'] or ''} | {row['kind']} | "
                f"{num(row['published_period_days'], '.6f')} | "
                f"{num(row['found_period_days'], '.6f')} | {num(row['relative_error'], '.2e')} | "
                f"{row['alias'] or '-'} | {recovered} |{signal_cell} {row['verdict']} | "
                f"{row.get('signal_verdict') or '-'} | {not_passed} |"
            )
        diag = summary["diagnostics"]
        lines += [
            "",
            "## Diagnostics (not part of the claim)",
            "",
            f"- Planets with verdict SURVIVED: {diag['planets_survived']}",
            f"- Holdout test statuses: {diag['holdout_statuses']}",
            f"- Verdicts by kind: {diag['verdicts_by_kind']}",
            f"- Analysis errors: {diag['errors'] or 'none'}",
        ]
        if diag.get("eb_catalog_downgraded"):
            lines.append(
                "- eb_catalog downgraded to a warning (own TIC in a same-photometry catalog, "
                f"v0.2.1): {', '.join(diag['eb_catalog_downgraded'])}"
            )
        for key, reasons in diag["inconclusive_reasons"].items():
            lines.append(f"- {key} INCONCLUSIVE: {'; '.join(str(r) for r in reasons)}")
        lines.append("")
        return "\n".join(lines)
