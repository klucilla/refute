"""The funnel of the v0.4 pilot: stage-1 eligibility, the promotion draw, and the (N, K) rule
(protocol sections 4.4 and 7).

- Eligibility reads a stage-1 ``verdict.json`` and its deduplication: the gate passes; every
  decisive stage-1 test is present and is PASS with coverage, or a FAIL whose *emitted* severity
  is warning; none is INCONCLUSIVE or a fatal FAIL; and deduplication is ``no_match`` in every
  catalog. The diagnostic never enters.
- The promotion takes every eligible star when there are at most ``cap``; otherwise it sorts the
  eligible by TIC ID and shuffles them with the promotion seed, then takes the first ``cap``.
  A promoted star that falls at stage 2 is never replaced.
- The (N, K) rule uses only the controls' measured costs, before any funnel star runs.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from refute.drand import shuffled
from refute.packs.tess.discover.dedup import NO_MATCH
from refute.packs.tess.discover.protocol import BUDGET, PROMOTION, Budget

ELIGIBLE = "eligible"


def stage1_eligibility(verdict: dict[str, Any], dedup: dict[str, Any] | None) -> dict[str, Any]:
    """Whether a stage-1 star may be promoted, and why (protocol section 7)."""
    discovery = verdict.get("discovery") or {}
    if verdict.get("status") != "OK":
        return {"eligible": False, "reason": "insufficient data to decide: analysis error"}
    if discovery.get("stage") != 1:
        return {"eligible": False, "reason": "not a stage-1 record"}
    tests = {t["name"]: t for t in verdict.get("tests", [])}
    gate = tests.get("snr")
    if gate is None or gate["status"] != "PASS":
        return {"eligible": False, "reason": "no significant signal in these data"}
    deferred = set(discovery.get("deferred_tests") or [])
    decisive = [n for n in verdict.get("expected_tests", []) if n not in deferred]
    missing = [n for n in decisive if n not in tests]
    if missing:
        return {"eligible": False, "reason": "stage-1 test(s) missing: " + ", ".join(missing)}
    fatal = [
        n for n in decisive if tests[n]["status"] == "FAIL" and tests[n]["severity"] == "fatal"
    ]
    if fatal:
        return {
            "eligible": False,
            "reason": "signal with a likely alternative explanation, by the test(s) "
            + ", ".join(fatal),
        }
    undecided = [n for n in decisive if tests[n]["status"] == "INCONCLUSIVE"]
    if undecided:
        return {
            "eligible": False,
            "reason": "insufficient data to decide: " + ", ".join(undecided),
        }
    if dedup is None or dedup.get("overall") != NO_MATCH:
        overall = None if dedup is None else dedup.get("overall")
        if overall == "match":
            return {"eligible": False, "reason": "signal matches a known object"}
        return {"eligible": False, "reason": "deduplication not decided in every catalog"}
    warnings = [n for n in decisive if tests[n]["status"] == "FAIL"]
    return {"eligible": True, "reason": ELIGIBLE, "warning_fails": warnings}


def promote(eligible: Sequence[int], seed: int | None, cap: int = PROMOTION.cap) -> dict[str, Any]:
    """The promotion of the eligible TIC IDs. A seed is needed only when there are more than
    ``cap``; it is the promotion round's seed (protocol section 8)."""
    ordered = sorted(set(eligible))
    if len(ordered) != len(eligible):
        raise ValueError("an eligible star is listed twice")
    if len(ordered) <= cap:
        return {"promoted": ordered, "not_promoted": [], "draw": None}
    if seed is None:
        raise ValueError(f"{len(ordered)} eligible stars and a cap of {cap}: a seed is needed")
    order = shuffled(ordered, seed, key=lambda tic: tic)
    return {
        "promoted": sorted(order[:cap]),
        "not_promoted": sorted(order[cap:]),
        "draw": {"order": order, "cap": cap},
    }


PROMOTION_SCHEMA = "refute-promotion-1"


def promotion_seed(randomness_hex: str) -> int:
    """The promotion seed of R_prom (protocol section 8, as approved at P1):
    ``int(sha256(randomness_hex + "|v0.4|promotion"), 16)``."""
    from refute.packs.tess.discover.transforms import stream_seed

    return stream_seed(randomness_hex, "v0.4", "promotion")


def comparable(entries: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """The part of each stage-1 entry that the promotion rests on: the star, the SHA-256 of
    its stage-1 ``verdict.json``, and its eligibility (eligible and reason)."""
    return [
        {
            "target_key": e.get("target_key"),
            "verdict_sha256": e.get("verdict_sha256"),
            "eligible": (e.get("eligibility") or {}).get("eligible"),
            "reason": (e.get("eligibility") or {}).get("reason"),
        }
        for e in entries
    ]


def promotion_record(
    claim_id: str,
    claim_sha256: str,
    n_chosen: int,
    entries: Sequence[dict[str, Any]],
    beacon: dict[str, Any] | None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The committed promotion record (protocol section 7): every funnel star of the run set
    with the SHA-256 of its stage-1 ``verdict.json`` and its eligibility, the R_prom beacon
    when a draw is needed, the promoted stars, and where everything it rests on is
    (``provenance``: the commit of the stage-1 results and the path of their entries in it,
    the committed (N, K) decision, the stage-1 run directory, the frozen inputs).
    ``verify_promotion`` recomputes it."""
    eligible = [e["target_key"] for e in entries if e["eligibility"]["eligible"]]
    tics = [int(k.split("-")[1]) for k in eligible]
    seed = promotion_seed(beacon["randomness"]) if beacon else None
    draw = promote(tics, seed)
    return {
        "schema": PROMOTION_SCHEMA,
        "claim_id": claim_id,
        "claim_sha256": claim_sha256,
        "n_chosen": n_chosen,
        "entries": comparable(entries),
        "eligible": eligible,
        "beacon": beacon,
        "promoted": [f"TIC-{t}" for t in draw["promoted"]],
        "not_promoted": [f"TIC-{t}" for t in draw["not_promoted"]],
        "provenance": provenance or {},
    }


def verify_promotion(
    record: dict[str, Any],
    claim_id: str,
    claim_sha256: str,
    run_set: Sequence[str],
    recomputed: Sequence[dict[str, Any]],
    committed: Sequence[dict[str, Any]] | None,
    n_k_chosen: int | None,
    expected_round: int | None,
) -> list[str]:
    """Problems of a promotion record; empty only when it is the record the protocol produces.

    ``recomputed``: the stage-1 entries recomputed from the stage-1 dossiers' bytes (their
    ``verdict.json`` hashes, deduplication and eligibility). ``committed``: the entries in the
    commit of the stage-1 results. ``n_k_chosen``: N of the committed (N, K) decision.
    ``expected_round``: R_prom computed from the CI push run of the results commit. The record's
    entries must equal both, its N the committed one, its eligible list and draw must follow,
    and a draw needs the beacon of exactly R_prom, with its signature verified."""
    from refute.drand import verify_beacon

    problems = []
    if record.get("schema") != PROMOTION_SCHEMA:
        return [f"not a {PROMOTION_SCHEMA} record"]
    if record.get("claim_id") != claim_id or record.get("claim_sha256") != claim_sha256:
        problems.append("the record is not for the locked claim")
    if n_k_chosen is None or record.get("n_chosen") != n_k_chosen:
        problems.append("n_chosen is not the N of the committed (N, K) decision")
    entries = list(record.get("entries") or [])
    if [e.get("target_key") for e in entries] != list(run_set):
        problems.append("the entries are not exactly the funnel stars of the run set, in order")
    if entries != comparable(recomputed):
        problems.append("the entries differ from those recomputed from the stage-1 dossiers")
    if committed is None or entries != comparable(committed):
        problems.append("the entries differ from those of the stage-1 results commit")
    eligible = [e["target_key"] for e in entries if e.get("eligible")]
    if record.get("eligible") != eligible:
        problems.append("the eligible list does not follow from the entries")
    seed = None
    if len(eligible) > PROMOTION.cap:
        beacon = record.get("beacon")
        if not beacon:
            return [*problems, "more eligible stars than the cap and no beacon"]
        if expected_round is None or int(beacon.get("round", -1)) != expected_round:
            return [*problems, f"the beacon is not R_prom (round {expected_round})"]
        try:
            verify_beacon(int(beacon["round"]), beacon)
        except (KeyError, ValueError, RuntimeError) as exc:
            return [*problems, f"the beacon does not verify: {exc}"]
        seed = promotion_seed(beacon["randomness"])
    draw = promote([int(k.split("-")[1]) for k in eligible], seed)
    if record.get("promoted") != [f"TIC-{t}" for t in draw["promoted"]]:
        problems.append("the promoted stars are not the protocol's draw")
    return problems


@dataclass(frozen=True)
class ControlCosts:
    """Mean logical-processor hours of one run of each kind on the two control curves, and
    mean bytes of one control's light-curve files (protocol section 4.4)."""

    h_stage1: float
    h_holdout: float
    h_injection: float
    h_transform: float
    bytes_light_curves: float


def choose_n_k(
    costs: ControlCosts, hours_used: float, bytes_used: float, budget: Budget = BUDGET
) -> dict[str, Any]:
    """The first ``(N, K)`` of the sequence whose projected cost fits, or none."""
    hours_left = budget.max_logical_processor_hours - hours_used
    bytes_left = budget.max_cache_bytes - bytes_used
    evaluations = []
    chosen = None
    for n, k in budget.sequence:
        hours = (
            budget.margin
            * n
            * (costs.h_stage1 + costs.h_holdout + k * costs.h_injection + 3 * costs.h_transform)
        )
        data = budget.margin * n * costs.bytes_light_curves
        hours = math.ceil(hours * 100) / 100  # rounded up to 0.01 h
        data = math.ceil(data / 1e6) * 1e6  # rounded up to 1 MB
        fits = hours <= budget.share_of_remaining * hours_left and (
            data <= budget.share_of_remaining * bytes_left
        )
        evaluations.append(
            {"N": n, "K": k, "projected_hours": hours, "projected_bytes": data, "fits": fits}
        )
        if fits and chosen is None:
            chosen = {"N": n, "K": k}
    return {
        "inputs": costs.__dict__,
        "hours_used": hours_used,
        "bytes_used": bytes_used,
        "hours_left": hours_left,
        "bytes_left": bytes_left,
        "evaluations": evaluations,
        "chosen": chosen,
    }
