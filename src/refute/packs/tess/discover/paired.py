"""The paired comparison of the v0.5 calibration (#198; docs/plans/v0.5-plan.md, section 4;
docs/plans/v0.5-acceptance.md, WP7 and WP10).

The candidate is generated once per curve (detrending, the global prewhitening, the search) and
both batteries attack it: "the v0.4 battery" is the v0.4 claim's plan run by the v0.4 code path
of ``attack_candidate`` (the same outputs as ``measure.chain``, case 10.1), and "the v0.5
battery" is the v0.5 claim's plan with the sensitivity rule. The two plans must share every
parameter of the candidate generation; otherwise the comparison is refused.

Reporting rules (case 10.3; WP7; #9, #180): the four verdict counts per battery, never a merged
"survival"; the paired transition table; the star is the cluster unit (curves of one star are
not independent); zero denominators are reported as such; injected hosts whose own signal
passes the gate, and inverted and rotated curves, are reported apart (cases 7.1, 7.2); counts
are named after what they count (failed tasks apart from INCONCLUSIVE verdicts, case 6.5). An
alias match needs the epoch as well as the period (case 6.7).
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from refute.core.verdict import TestStatus, aggregate, defer_tests, enforce_coverage
from refute.packs.tess.detrend import detrend
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import attack_candidate, expected_by_role, global_prewhitening
from refute.packs.tess.search import search_period
from refute.packs.tess.types import TessData

VERDICTS = ("SURVIVED", "WEAKENED", "REFUTED", "INCONCLUSIVE")
SHARED = ("data", "detrend", "search")


def check_pairing(plan_v04: TessTestPlan, plan_v05: TessTestPlan) -> None:
    """Refuse a pair of plans that would not generate the same candidate."""
    if plan_v04.v05 or not plan_v05.v05:
        raise ValueError("the pair is a v0.4 plan (discovery version 1) and a v0.5 plan")
    for name in SHARED:
        if getattr(plan_v04, name) != getattr(plan_v05, name):
            raise ValueError(f"the plans differ in `{name}`: the candidate would not be shared")
    # the finalization of the candidate and its gate read these too (Codex's review of round 2)
    for name in ("corrections", "events", "snr"):
        if getattr(plan_v04.gauntlet, name) != getattr(plan_v05.gauntlet, name):
            raise ValueError(
                f"the plans differ in `gauntlet.{name}`: the candidate would not be shared"
            )


def _outcome(data, candidate, plan: TessTestPlan, stage: int, catalogs, scan, pw) -> dict:
    """One battery on the shared candidate, at ``stage``: the fields of ``measure.chain``."""
    gauntlet = attack_candidate(data, candidate, plan, catalogs, scan, pw)
    tests = enforce_coverage(gauntlet.tests)
    if plan.v05:
        from refute.core.sensitivity import enforce_sensitivity
        from refute.packs.tess.power import registry_for

        tests = enforce_sensitivity(tests, registry_for(plan))
    tests, deferred = defer_tests(tests, dict(plan.discovery.stages), stage)
    if plan.is_v051:
        # v0.5.1 WP5 (Codex's WP5 design review): a version-3 battery classifies its
        # INCONCLUSIVE results after the deferral, as conclude_analysis does (WP4)
        from refute.packs.tess.pipeline import classify_v051

        tests = classify_v051(tests, deferred)
    decisive, _ = expected_by_role(plan, catalogs is not None)
    verdict, reason = aggregate([t for t in tests if t.name in decisive], expected=decisive)
    staged = [n for n in decisive if n not in deferred]
    stage_verdict, stage_reason = aggregate([t for t in tests if t.name in staged], expected=staged)
    gate = next((t for t in tests if t.name == "snr"), None)
    final = gauntlet.candidate
    out = {
        "candidate": None
        if final is None
        else {"period_days": final.period, "t0_btjd": final.t0, "snr": final.snr},
        "tests": {t.name: {"status": t.status.value, "severity": t.severity.value} for t in tests},
        "deferred": deferred,
        "catalog_test": catalogs is not None,
        "verdict": verdict.value,
        "verdict_reason": reason,
        "stage_tests": staged,
        "stage_verdict": stage_verdict.value,
        "stage_verdict_reason": stage_reason,
        "gate_passed": gate is not None and gate.status is TestStatus.PASS,
    }
    if plan.is_v051:
        # version 3 only, so the v0.4 and v0.5 records keep their keys and bytes
        from refute.core.inconclusive import CLASS_KEY, SOURCE_KEY, with_classes
        from refute.packs.tess.pipeline import v051_fields

        for t in tests:
            if CLASS_KEY in t.metrics:
                out["tests"][t.name][CLASS_KEY] = t.metrics[CLASS_KEY]
                out["tests"][t.name][SOURCE_KEY] = t.metrics[SOURCE_KEY]
        chosen = [t for t in tests if t.name in decisive]
        out["verdict_reason"] = with_classes(reason, chosen)
        out["stage_verdict_reason"] = with_classes(stage_reason, chosen)
        out["v051"] = v051_fields(verdict.value, reason, chosen, tests)
    return out


def paired_chain(
    data: TessData,
    plan_v04: TessTestPlan,
    plan_v05: TessTestPlan,
    stage: int,
    catalogs: list | None = None,
    catalog_scan: dict | None = None,
) -> dict[str, Any]:
    """The candidate generated once and attacked by both batteries."""
    check_pairing(plan_v04, plan_v05)
    flat = detrend(data.lc, plan_v04.detrend)
    pw, searched = global_prewhitening(data, plan_v04, flat)
    search = search_period(searched, plan_v04.search)
    candidate = search.candidate
    v04 = _outcome(data, candidate, plan_v04, stage, catalogs, catalog_scan, pw)
    v05 = _outcome(data, candidate, plan_v05, stage, catalogs, catalog_scan, pw)
    if v04["candidate"] != v05["candidate"]:
        raise ValueError("the two batteries did not attack the same final candidate")
    return {
        "search_candidate": None
        if candidate is None
        else {"period_days": candidate.period, "t0_btjd": candidate.t0, "snr": candidate.snr},
        "v04": v04,
        "v05": v05,
    }


# --- recovery with the epoch for aliases (case 6.7) ---------------------------------------


def recovery_v05(
    injected: dict[str, float],
    found: dict[str, Any] | None,
    gate_passed: bool,
    period_tolerance: float,
    epoch_tolerance_durations: float,
    alias_factors: tuple[float, ...] = (2.0, 0.5, 3.0, 1.0 / 3.0),
) -> dict[str, Any]:
    """Whether the found candidate is the injected signal, or a declared alias of it; an alias
    needs its epoch to fall on the injected transits (on the shorter of the two periods), not
    the period alone. ``injected`` has ``period_days``, ``t0_btjd`` and ``duration_days``."""
    out = {"recovered": False, "alias": None, "gate_passed": gate_passed}
    if not found or found.get("period_days") is None:
        return out
    p_inj, t_inj, dur = injected["period_days"], injected["t0_btjd"], injected["duration_days"]
    period, t0 = float(found["period_days"]), float(found["t0_btjd"])

    def aligned(reference_period: float) -> bool:
        phase = (t0 - t_inj) / reference_period
        return abs(phase - round(phase)) * reference_period <= epoch_tolerance_durations * dur

    if abs(period - p_inj) / p_inj <= period_tolerance:
        out["recovered"] = bool(aligned(p_inj) and gate_passed)
        return out
    for factor in alias_factors:
        target = factor * p_inj
        if abs(period - target) / target <= period_tolerance and aligned(min(period, p_inj)):
            out["alias"] = factor
            break
    return out


# --- reporting rules (cases 10.3, 7.1, 7.2, 6.5) ------------------------------------------


def verdict_counts(verdicts: list[str]) -> dict[str, int]:
    """The four verdict counts, each apart (never a merged "survival")."""
    counts = Counter(verdicts)
    unknown = set(counts) - set(VERDICTS)
    if unknown:
        raise ValueError(f"unknown verdicts: {sorted(unknown)}")
    return {v: int(counts.get(v, 0)) for v in VERDICTS}


def transitions(pairs: list[tuple[str, str]]) -> dict[str, dict[str, int]]:
    """The paired transition table: v0.4 verdict -> v0.5 verdict -> count."""
    table = {a: dict.fromkeys(VERDICTS, 0) for a in VERDICTS}
    for a, b in pairs:
        table[a][b] += 1
    return table


def summarize(records: list[dict[str, Any]], group: str) -> dict[str, Any]:
    """One group of task records (each with ``target_key``, ``status``, and for an OK task
    ``chain`` = a ``paired_chain`` output): failed tasks apart from INCONCLUSIVE verdicts; the
    gate-passing detections; the four stage-verdict counts per battery among them; the paired
    transitions; the stars (the cluster unit). An empty group is reported with zeros, never
    dropped."""
    ok = [r for r in records if r.get("status") == "OK"]
    gated = [r for r in ok if r["chain"]["v04"]["gate_passed"]]
    return {
        "group": group,
        "tasks": len(records),
        "failed_tasks": len(records) - len(ok),
        "stars": len({r["target_key"] for r in records}),
        "gate_passed": len(gated),
        "stars_with_gate_passed": len({r["target_key"] for r in gated}),
        "v04_stage_verdicts": verdict_counts([r["chain"]["v04"]["stage_verdict"] for r in gated]),
        "v05_stage_verdicts": verdict_counts([r["chain"]["v05"]["stage_verdict"] for r in gated]),
        "transitions": transitions(
            [
                (r["chain"]["v04"]["stage_verdict"], r["chain"]["v05"]["stage_verdict"])
                for r in gated
            ]
        ),
        "note": "detections on transformed or injected curves; not a false-alarm rate; curves of "
        "one star are not independent",
    }


def transformed_groups(records: list[dict[str, Any]], own_signal: set[str]) -> dict[str, Any]:
    """Transformed curves by kind (inverted, rotated) and by host (signal-bearing: the star's
    own signal passes the gate; original-gate-negative), each group apart (case 7.2)."""
    groups: dict[str, list] = {}
    for r in records:
        kind = "inverted" if r.get("position") == 0 else "rotated"
        host = "signal_bearing" if r["target_key"] in own_signal else "original_gate_negative"
        groups.setdefault(f"{kind}/{host}", []).append(r)
    names = [
        f"{k}/{h}"
        for k in ("inverted", "rotated")
        for h in ("signal_bearing", "original_gate_negative")
    ]
    return {name: summarize(groups.get(name, []), name) for name in names}


def summarize_injections(records: list[dict[str, Any]], group: str) -> dict[str, Any]:
    """Injections (each record with ``recovery``, from ``recovery_v05`` on the shared final
    candidate): the two numbers of the plan's section 4 (Codex's review of round 2), never a
    merged survival:

    - among the **recovered, gate-passing** injections (the identity matched): the four
      stage-verdict counts per battery and the paired transitions (the conditional cost);
    - the same counts over **all attempted** injections as the denominator (end to end), with
      the injections not recovered (failed tasks included) counted apart."""
    attempted = len(records)
    ok = [r for r in records if r.get("status") == "OK"]
    recovered = [r for r in ok if (r.get("recovery") or {}).get("recovered")]
    v04 = verdict_counts([r["chain"]["v04"]["stage_verdict"] for r in recovered])
    v05 = verdict_counts([r["chain"]["v05"]["stage_verdict"] for r in recovered])
    return {
        "group": group,
        "attempted": attempted,
        "failed_tasks": attempted - len(ok),
        "stars": len({r["target_key"] for r in records}),
        "recovered": len(recovered),
        "not_recovered": attempted - len(recovered),
        "among_recovered": {
            "denominator": len(recovered),
            "v04_stage_verdicts": v04,
            "v05_stage_verdicts": v05,
            "transitions": transitions(
                [
                    (r["chain"]["v04"]["stage_verdict"], r["chain"]["v05"]["stage_verdict"])
                    for r in recovered
                ]
            ),
        },
        "among_attempted": {
            "denominator": attempted,
            "v04_recovered_with_stage_verdict": v04,
            "v05_recovered_with_stage_verdict": v05,
        },
        "note": "injections into one star are not independent; not a false-alarm rate",
    }


def injection_groups(records: list[dict[str, Any]], own_signal: set[str]) -> dict[str, Any]:
    """Injections by host: original-gate-negative hosts, and hosts whose own signal passes the
    gate, apart and never pooled (case 7.1); the latter measure competition, not sensitivity."""
    neg = [r for r in records if r["target_key"] not in own_signal]
    own = [r for r in records if r["target_key"] in own_signal]
    return {
        "original_gate_negative": summarize_injections(neg, "original_gate_negative"),
        "signal_bearing": {
            **summarize_injections(own, "signal_bearing"),
            "caveat": "the host's own signal passes the gate: recovery here measures whether "
            "an injection outranks it, not sensitivity (#180)",
        },
    }
