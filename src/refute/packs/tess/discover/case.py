"""The case format of the v0.4 pilot (protocol, the proposal's section 4.3; issue #177): the
items every complete case has, the closed vocabulary of its conclusion, and the content rules
of the ledger's events for this pack."""

from __future__ import annotations

import re
from typing import Any

CASE_SCHEMA = "refute-tess-case-1"
CASE_ITEMS = (
    "identity",
    "question",
    "alternatives",
    "data",
    "cross_match",
    "analyses",
    "coverage_and_limits",
    "uncertainties",
    "review",
    "questions_for_a_human",
    "conclusion",
)
# The closed vocabulary of the human conclusion (protocol section 1). Each pattern is the whole
# sentence; the parts in angle brackets of the protocol are free text without line breaks.
CONCLUSIONS = (
    r"no significant signal in these data",
    r"signal with a likely alternative explanation: [^\n]+, by the test [a-z_]+(, [a-z_]+)*",
    r"signal matches a known object: [^\n]+",
    r"signal survived the declared decisive battery; temporal diagnostic: "
    r"(pass|fail|inconclusive|not_run); method not validated",
    r"not evaluated past stage 1: [^\n]+",
    r"insufficient data to decide: [^\n]+",
)
FORBIDDEN_WORDS = ("confirmed", "discovery", "true", "planet b", "planet c")


def conclusion_allowed(text: str) -> bool:
    """Whether a conclusion is one of the closed forms (and uses no forbidden word)."""
    lowered = text.lower()
    if any(re.search(rf"\b{re.escape(w)}\b", lowered) for w in FORBIDDEN_WORDS):
        return False
    return any(re.fullmatch(pattern, text) for pattern in CONCLUSIONS)


def missing_items(case: dict[str, Any]) -> list[str]:
    """The items of the case format that are absent or empty (the per-case checklist)."""
    missing = [item for item in CASE_ITEMS if not case.get(item)]
    conclusion = case.get("conclusion") or {}
    text = conclusion.get("text") if isinstance(conclusion, dict) else None
    if text is not None and not conclusion_allowed(text):
        missing.append("conclusion (not in the closed vocabulary)")
    return missing


QUESTIONS = {
    "exploration": "Is there a periodic transit-like signal in this light curve that survives "
    "the declared decisive battery?",
    "planet": "Is the catalogued signal recovered and classified as declared?",
    "false_positive": "Is the catalogued signal recovered and classified as declared?",
}
ALTERNATIVES = (
    "eclipsing binary on the target",
    "background or nearby eclipsing binary",
    "instrumental systematics",
    "stellar variability",
    "period alias",
    "noise",
)


def signal_identity(verdict: dict[str, Any], kind: str | None) -> dict[str, Any] | None:
    """Whether a control's found signal is its catalogued one (protocol section 4.3, H7 of
    v0.2.1): the planet's found period within the relative ``identity_period_tolerance`` of the
    published period (aliases not counted); the false positive's at one of
    ``fp_identity_factors``. The epoch difference is reported, not required. None for a funnel
    star."""
    from refute.packs.tess.discover.protocol import CONTROLS
    from refute.packs.tess.pipeline import matching_factor

    if kind not in ("planet", "false_positive"):
        return None
    comparison = verdict.get("period_comparison") or {}
    published = comparison.get("published_period_days")
    found = comparison.get("found_period_days")
    factors = [1.0] if kind == "planet" else list(CONTROLS.fp_identity_factors)
    factor = matching_factor(published, found, factors, CONTROLS.identity_period_tolerance)
    epoch = None
    t0_published = (verdict.get("published") or {}).get("t0_bjd")
    t0_found = (verdict.get("candidate") or {}).get("t0_bjd")
    if factor is not None and t0_published is not None and t0_found is not None and found:
        offset = (float(t0_found) - float(t0_published)) % float(found)
        epoch = offset - float(found) if offset > float(found) / 2 else offset
    return {
        "rule": "found period within the relative tolerance of the published period at a factor",
        "period_tolerance": CONTROLS.identity_period_tolerance,
        "factors": factors,
        "published_period_days": published,
        "found_period_days": found,
        "matched_factor": factor,
        "identified": factor is not None,
        "epoch_difference_days": epoch,
        "epoch_note": "reported, not required",
    }


def build_case(
    verdict: dict[str, Any],
    target: dict[str, Any],
    cross_match: dict[str, Any] | None,
    measurements: dict[str, Any] | None,
) -> dict[str, Any]:
    """The machine-built items of ``case.json`` for one dossier. The review, the questions for a
    human and the conclusion are written by people after the review (P4 and P5); until then
    they are empty, so the checklist reports the case as incomplete. A control's identity
    carries its signal identity (``signal_identity``)."""
    tests = verdict.get("tests", [])
    data = verdict.get("data_summary") or {}
    return {
        "schema": CASE_SCHEMA,
        "identity": {
            "target_key": verdict.get("target_key"),
            "tic_id": verdict.get("tic_id"),
            "kind": target.get("kind"),
            "name": target.get("name"),
            "star": data.get("star"),
            "source": target.get("source"),
            "signal_identity": signal_identity(verdict, target.get("kind")),
        },
        "question": QUESTIONS.get(str(target.get("kind")), QUESTIONS["exploration"]),
        "alternatives": list(ALTERNATIVES),
        "data": {
            "sectors": data.get("sectors"),
            "years": data.get("years"),
            "product": data.get("product"),
            "manifest": "data/manifest.json",
            "selection_evidence": target.get("mast"),
        },
        "cross_match": cross_match,
        "analyses": {
            "verdict": verdict.get("verdict"),
            "verdict_reason": verdict.get("verdict_reason"),
            "tests": [{k: t[k] for k in ("name", "status", "severity")} for t in tests],
            "temporal_diagnostic": verdict.get("temporal_diagnostic"),
            "measurements": measurements,
        },
        "coverage_and_limits": [
            {
                "test": t["name"],
                "coverage": t.get("coverage"),
                "coverage_unit": t.get("coverage_unit"),
                "message": t.get("message"),
            }
            for t in tests
        ],
        "uncertainties": {
            "candidate": verdict.get("candidate"),
            "ephemeris": verdict.get("global_ephemeris"),
            "duration": verdict.get("duration_estimate"),
        },
        "method_status": verdict.get("method_status", "not_validated"),
        "review": None,
        "questions_for_a_human": None,
        "conclusion": None,
    }


LIGHT_ENTRY_FIELDS = ("method_status", "temporal_diagnostic", "stage1", "promotion")


TEMPORAL_STATES = ("pass", "fail", "inconclusive", "not_run")


def _hex64(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def check_event(event: dict[str, Any]) -> list[str]:
    """Content rules of this pack's ledger events, by type (``refute.core.ledger.verify_events``
    with ``check=check_event``; the phase's ledger is always verified with it):

    - ``ran``: ``stage`` 1 or 2, ``method_status`` exactly ``not_validated``, and a
      ``temporal_diagnostic`` state; at stage 1 the stage-1 results and the promotion state, the
      promotion apart from the verdict; at stage 2 the dossier's hash;
    - ``promoted``: the SHA-256 of the committed promotion record and the promoted stars;
    - ``concluded``: a conclusion in the closed vocabulary.
    """
    data = event.get("data") if isinstance(event.get("data"), dict) else {}
    kind = event.get("type")
    problems = []
    if kind == "ran":
        stage = data.get("stage")
        if stage not in (1, 2):
            problems.append("a run names its stage (1 or 2)")
        if data.get("method_status") != "not_validated":
            problems.append("method_status must be present and equal to not_validated")
        if data.get("temporal_diagnostic") not in TEMPORAL_STATES:
            problems.append("temporal_diagnostic must be one of " + ", ".join(TEMPORAL_STATES))
        if stage == 1:
            missing = [f for f in LIGHT_ENTRY_FIELDS if f not in data]
            if missing:
                problems.append("a stage-1 entry lacks " + ", ".join(missing))
            if "verdict" in (data.get("promotion") or {}):
                problems.append("the promotion is recorded apart from the verdict")
        if stage == 2 and not _hex64((event.get("hashes") or {}).get("dossier")):
            problems.append("a stage-2 run records its dossier's SHA-256")
    elif kind == "promoted":
        if not _hex64(data.get("promotion_sha256")):
            problems.append("a promotion records the SHA-256 of its record")
        if not isinstance(data.get("promoted"), list):
            problems.append("a promotion lists the promoted stars")
    elif kind == "concluded":
        text = (data.get("conclusion") or {}).get("text")
        if text is None or not conclusion_allowed(text):
            problems.append("a conclusion outside the closed vocabulary")
    return problems


def light_entry(verdict: dict[str, Any], eligibility: dict[str, Any], dedup: Any) -> dict[str, Any]:
    """The ledger content of one funnel star after stage 1 (no dossier): the method status,
    the temporal diagnostic, the stage-1 results, the deduplication, and the promotion state,
    which is kept apart from the verdict."""
    return {
        "stage": 1,
        "target_key": verdict.get("target_key"),
        "method_status": verdict.get("method_status", "not_validated"),
        "temporal_diagnostic": (verdict.get("temporal_diagnostic") or {}).get("state", "not_run"),
        "stage1": {
            "verdict": verdict.get("verdict"),
            "verdict_reason": verdict.get("verdict_reason"),
            "tests": {t["name"]: t["status"] for t in verdict.get("tests", [])},
            "candidate": verdict.get("candidate"),
        },
        "deduplication": dedup,
        "promotion": {
            "eligible": eligibility.get("eligible"),
            "reason": eligibility.get("reason"),
        },
    }
