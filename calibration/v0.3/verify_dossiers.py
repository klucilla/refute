"""Dossier verification of the main sample of v0.3 (item (a) of plan section 10.2).

Implements docs/validation/v0.3/dossier-verification-acceptance.md. Outside the code hash of
the locks: it changes nothing in src/ and calls the frozen functions of the package
(refute.core.paper.aggregate_claim and paper_profile, refute.packs.ml.orchestrate._outcome,
the ClaimContext derivations of refute.packs.ml.integration). It reads a published dossier and
its published claim folder, runs no experiment and opens no network connection.

Usage (from the repository root):
  uv run --frozen python calibration/v0.3/verify_dossiers.py [--out DIR] [ARXIV ...]
With no arXiv id, the five papers of the main sample. Exit code 0 when every dossier is
VERIFIED, 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from refute.core import budget as bg
from refute.core.canonical import canonical_bytes
from refute.core.dossier import check_dossier
from refute.core.paper import (
    Attack,
    ClaimVerdict,
    FailureCause,
    GateFailure,
    aggregate_claim,
    paper_profile,
)
from refute.core.verdict import PaperVerdict, Severity, TestResult, TestStatus
from refute.packs.ml import integration as ig
from refute.packs.ml import orchestrate as orc
from refute.packs.ml.production import _plain

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "calibration/v0.3/main"
SAMPLE = ("2302.12465", "2305.19518", "2309.15704", "2407.11735", "2502.16782")
FORMAT = "refute-v03-dossier-verification-1"
LIMITS = (
    "The verification shows that the classification is deterministic from the recorded "
    "outputs, not that the experiment is repeatable (plan, lines 69-72).",
    "It replays the recorded check results; it does not re-read the logs and sources those "
    "checks were computed from.",
    "The completeness of the accounting is taken from the recorded status: the dossier does "
    "not record the parent cgroup's usage and the tolerance, so that comparison cannot be "
    "repeated numerically.",
    "The lock and its history are read from the published claim folder, not from the dossier.",
)
FALLBACK_STEPS = "build"  # with the data/* steps: the steps run with a fallback
REFUTE_SIDE = (
    orc.Outcome.BUDGET_EXHAUSTED,
    orc.Outcome.OPERATIONAL_GUARD,
    orc.Outcome.REFUTE_ERROR,
)


class RecordError(Exception):
    """A record that cannot be read as the frozen code wrote it."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---- rebuilding the frozen inputs from the record ----------------------------------------


def _test(d: Any) -> TestResult | None:
    if d is None:
        return None
    try:
        return TestResult(
            d["name"],
            TestStatus(d["status"]),
            Severity(d["severity"]),
            d["message"],
            metrics=dict(d.get("metrics") or {}),
            thresholds=dict(d.get("thresholds") or {}),
            inputs=dict(d.get("inputs") or {}),
            coverage=d.get("coverage"),
            coverage_unit=d.get("coverage_unit") or "",
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RecordError(f"a check record cannot be read: {type(exc).__name__}: {exc}") from None


def _attack(d: Mapping[str, Any]) -> Attack:
    return Attack(d["name"], _test(d.get("run")), _test(d.get("metric")), _test(d.get("result")))


def _failure(d: Mapping[str, Any]) -> GateFailure:
    cause = d["cause"]
    try:
        cause = FailureCause(cause)
    except ValueError:
        pass  # an unknown cause is kept as recorded; known_cause decides
    return GateFailure(cause, d["attempts_completed"], d["attempts_required"])


# ---- the checks ---------------------------------------------------------------------------


def check_hashes(dossier: Path, claim_dir: Path, findings: list[str]) -> None:
    """V1: the manifest, the seal, the claim's bytes and the lock's hash."""
    result = check_dossier(dossier)
    findings += [f"V1 manifest: {p}" for p in result.integrity_problems]
    if result.seal is None:
        findings.append("V1 seal: the dossier has no SEAL.json")
    elif not result.seal.ok:
        findings += [
            f"V1 seal: {p}" for p in result.seal.core_problems + result.seal.annex_problems
        ]
        for name, problems in result.seal.annexes.items():
            findings += [f"V1 annex {name}: {p}" for p in problems]
    claim_file = (dossier / "claim_file.json").read_bytes()
    claim_input = (dossier / "claim_input.json").read_bytes()
    if claim_file != claim_input:
        findings.append("V1 claim: claim_input.json and claim_file.json differ")
    record = json.loads((dossier / "dossier.json").read_bytes())
    if record.get("claim_file_sha256") != _sha(claim_file):
        findings.append("V1 claim: dossier.json's claim_file_sha256 is not claim_file.json's")
    lock = json.loads((claim_dir / "claim.lock.json").read_bytes())
    if lock.get("claim_sha256") != _sha(claim_input):
        findings.append("V1 lock: the resolved claim's SHA-256 is not the lock's claim_sha256")


def check_verdicts(claim_file: Mapping[str, Any], outcome: Mapping[str, Any], findings: list[str]):
    """V2 and V3: each claim's verdict and the paper's profile, recomputed."""
    plan = claim_file["test_plan"]
    targets = claim_file["targets"]
    claims = outcome["claims"]
    keys = [t["key"] for t in targets]
    if [c["key"] for c in claims] != keys:
        findings.append(f"V2 claims: recorded {[c['key'] for c in claims]}, expected {keys}")
        return
    run = outcome.get("run")
    for target, rec in zip(targets, claims, strict=True):
        ctx = ig.ClaimContext(target, plan)
        key = ctx.key
        try:
            computed = aggregate_claim(
                [_test(t) for t in rec["base"]],
                [_attack(a) for a in rec["attacks"]],
                ctx.applicable(),
                metric_recompute_applies=target["metric_recompute"]["applies"],
                failures={k: _failure(v) for k, v in rec["failures"].items()},
                minimums=ctx.minimums(),
                not_applicable=ctx.not_applicable(),
            )
        except (RecordError, KeyError, TypeError, ValueError) as exc:
            findings.append(f"V2 {key}: cannot recompute: {type(exc).__name__}: {exc}")
            continue
        if computed.verdict.value != rec["computed"]:
            findings.append(
                f"V2 {key}: recomputed {computed.verdict.value}, "
                f"recorded computed {rec['computed']}"
            )
        expected = computed
        if run is not None and not run["accounting_valid"]:
            reasons = "; ".join(run["invalid_reasons"]) or "unknown"
            expected = ClaimVerdict(
                PaperVerdict.INCONCLUSIVE,
                f"{ig.ACCOUNTING_INVALID}: {reasons}",
                gates_not_applicable=dict(computed.gates_not_applicable),
            )
        if _plain(expected) != rec["verdict"]:
            findings.append(
                f"V2 {key}: expected verdict {_plain(expected)}, recorded {rec['verdict']}"
            )
    profile = paper_profile([(c["key"], c["verdict"]["verdict"]) for c in claims])
    if _plain(profile) != outcome["profile"]:
        findings.append(f"V3 profile: recomputed {_plain(profile)}, recorded {outcome['profile']}")


def expected_steps(claim_file: Mapping[str, Any]) -> list[tuple[str, str | None, str]]:
    """The plan's steps, in the order of execution (integration.build_plan)."""
    plan = claim_file["test_plan"]
    out: list[tuple[str, str | None, str]] = [(orc.SETUP, None, "build")]
    out += [(orc.SETUP, None, f"data/{n}") for n in ig.container_datasets(plan)]
    contexts = [ig.ClaimContext(t, plan) for t in claim_file["targets"]]
    out += [(orc.BASE, c.key, "base") for c in contexts]
    for c in contexts:
        for name in c.applicable():
            if name not in ig.CONTAINER_ATTACKS:
                continue
            if name == "ablation" and "config_file" in c.attack("ablation")["params"]["disable"]:
                continue
            out.append((orc.ATTACKS, c.key, name))
    return out


def _records(step: Mapping[str, Any]) -> list[Any]:
    """The step's containers as the frozen _outcome reads them."""
    out = []
    for c in step["containers"]:
        r = c["result"]
        result = (
            None if r is None else SimpleNamespace(stopped=r["stopped"], exit_code=r["exit_code"])
        )
        out.append(SimpleNamespace(container_id=c["container_id"], result=result, error=c["error"]))
    return out


def _not_executed_reason_ok(step, claims_by_key, steps_by_id) -> bool:
    reason = step["reason"]
    if reason in ("the setup did not complete", f"{bg.BUDGET_EXHAUSTED} ({bg.Pool.SETUP})"):
        return step["phase"] == orc.BASE
    if reason == "not eligible for attacks (base not obtained or no applicable attack)":
        return step["phase"] == orc.ATTACKS
    if reason == "not reached" or reason.startswith("the paper stopped: "):
        return True
    if reason.startswith("step ") and " did not complete (" in reason:
        name = reason[len("step ") : reason.index(" did not complete (")]
        prior = steps_by_id.get((step["phase"], step["claim"], name))
        return prior is not None and reason.endswith(f"({prior['outcome']})")
    # the claim not run on Refute's side: the same reason is among the claim's notes
    claim = claims_by_key.get(step["claim"])
    return step["phase"] == orc.BASE and claim is not None and reason in claim["notes"]


def check_steps(claim_file: Mapping[str, Any], outcome: Mapping[str, Any], findings: list[str]):
    """V4 and V5: the execution states and the reasons of every interruption, from the step
    records themselves."""
    run, ladder = outcome.get("run"), outcome["ladder"]
    attempts = ladder.get("attempts") or []
    if run is None:
        if any(a.get("applicable") for a in attempts):
            findings.append("V4 run: no run recorded although a rung of the ladder applies")
        return
    steps = run["steps"]
    ids = [(s["phase"], s["claim"], s["step"]) for s in steps]
    plan_ids = expected_steps(claim_file)
    if len(set(ids)) != len(ids):
        findings.append("V4 steps: a step is recorded twice")
    missing = [i for i in plan_ids if i not in ids]
    extra = [i for i in ids if i not in plan_ids]
    if missing:
        findings.append(f"V4 steps: missing {missing}")
    if extra:
        findings.append(f"V4 steps: not in the plan {extra}")
    # order: the steps that ran (with containers) follow the plan's order
    ran = [i for i, s in zip(ids, steps, strict=True) if s["containers"]]
    positions = [plan_ids.index(i) for i in ran if i in plan_ids]
    if positions != sorted(positions):
        findings.append(f"V4 order: the steps that ran are not in the plan's order: {ran}")
    claims_by_key = {c["key"]: c for c in outcome["claims"]}
    steps_by_id = dict(zip(ids, steps, strict=True))
    for s in steps:
        where = " ".join(p for p in (s["phase"], s["claim"] or "", s["step"]) if p)
        try:
            out = orc.Outcome(s["outcome"])
        except ValueError:
            findings.append(f"V4 {where}: unknown outcome {s['outcome']!r}")
            continue
        if out is not orc.Outcome.COMPLETED and not s["reason"]:
            findings.append(f"V4 {where}: {out} with no reason")
        for c in s["containers"]:
            if c["result"] is None and not c["error"]:
                findings.append(
                    f"V4 {where}: container {c['container_id']} has no result and no error"
                )
        if not s["containers"]:
            if out not in (
                orc.Outcome.NOT_EXECUTED,
                orc.Outcome.BUDGET_EXHAUSTED,
                orc.Outcome.REFUTE_ERROR,
            ):
                findings.append(f"V4 {where}: {out} with no container")
            elif out is orc.Outcome.NOT_EXECUTED and not _not_executed_reason_ok(
                s, claims_by_key, steps_by_id
            ):
                findings.append(
                    f"V4 {where}: not executed with a reason the runner never gives: "
                    f"{s['reason']!r}"
                )
            continue
        records = _records(s)
        if s["step"] == FALLBACK_STEPS or s["step"].startswith("data/"):
            last, last_reason = orc._outcome(records[-1:])
            if last in REFUTE_SIDE:
                ok = out is last or out is orc.Outcome.REFUTE_ERROR
            elif out is orc.Outcome.COMPLETED:
                ok = records[-1].result.exit_code == 0
            else:
                ok = out in (orc.Outcome.FAILED, orc.Outcome.REFUTE_ERROR)
            earlier = [r for r in records[:-1] if r.result is None or r.result.exit_code == 0]
            if earlier:
                findings.append(f"V4 {where}: an earlier rung exited 0 or has no result")
        else:
            want, want_reason = orc._outcome(records)
            if out is orc.Outcome.REFUTE_ERROR and want is not orc.Outcome.REFUTE_ERROR:
                ok = bool(s["reason"]) and (not want_reason or want_reason in s["reason"])
            else:
                ok = out is want and s["reason"] == want_reason
        if not ok:
            findings.append(
                f"V4 {where}: recorded {out} {s['reason']!r} does not follow from its containers"
            )
    # the run's own record
    for key, obtained in run["base_obtained"].items():
        base = steps_by_id.get((orc.BASE, key, "base"))
        if obtained and (base is None or base["outcome"] != orc.Outcome.COMPLETED):
            findings.append(
                f"V4 run: base_obtained true for {key} whose base step did not complete"
            )
    if sorted(run["base_obtained"]) != sorted(claims_by_key):
        findings.append("V4 run: base_obtained does not name exactly the claims")
    if run["stopped"]:
        if run["accounting_valid"]:
            findings.append("V4 run: stopped, yet the accounting is valid")
        if run["stopped"] not in run["invalid_reasons"]:
            findings.append("V4 run: the stop is not among the invalid reasons")
    has_attack = {k for (p, k, _) in plan_ids if p == orc.ATTACKS}
    for key in run["attack_claims"]:
        if not run["base_obtained"].get(key) or key not in has_attack:
            findings.append(
                f"V4 run: {key} eligible for attacks without its base or an attack step"
            )
    if run["setup_exhausted"]:
        for s in steps:
            if s["phase"] == orc.BASE and s["outcome"] != orc.Outcome.NOT_EXECUTED:
                findings.append("V4 run: the setup budget was exhausted, yet a base step ran")
    # V5: the ladder
    build = steps_by_id.get((orc.SETUP, None, "build"))
    applicable = [f"setup/build/{a['rung']}" for a in attempts if a.get("applicable")]
    if build is not None:
        cids = [c["container_id"] for c in build["containers"]]
        if cids != applicable[: len(cids)]:
            findings.append(f"V5 ladder: build containers {cids}, applicable rungs {applicable}")
        built = ladder.get("built_with")
        if build["outcome"] == orc.Outcome.COMPLETED:
            if not cids or built is None or cids[-1] != f"setup/build/{built}":
                findings.append(
                    f"V5 ladder: a completed build names {built!r}, last container {cids[-1:]}"
                )
        elif built is not None:
            findings.append(f"V5 ladder: built_with {built!r}, yet the build did not complete")


def verify(
    arxiv: str, dossier: Path | None = None, claim_dir: Path | None = None
) -> dict[str, Any]:
    dossier = dossier or MAIN / "dossiers" / arxiv / "dossier"
    claim_dir = claim_dir or MAIN / "claims" / arxiv / "claim"
    findings: list[str] = []
    try:
        check_hashes(dossier, claim_dir, findings)
        claim_file = json.loads((dossier / "claim_file.json").read_bytes())
        record = json.loads((dossier / "dossier.json").read_bytes())
        outcome = record["outcome"]
        check_verdicts(claim_file, outcome, findings)
        check_steps(claim_file, outcome, findings)
    except (OSError, ValueError, KeyError, TypeError, RecordError) as exc:
        findings.append(f"the dossier cannot be read as recorded: {type(exc).__name__}: {exc}")
        outcome = None
    profile = (outcome or {}).get("profile") if isinstance(outcome, dict) else None
    return {
        "format": FORMAT,
        "paper": arxiv,
        "result": "NOT VERIFIED" if findings else "VERIFIED",
        "findings": findings,
        "profile": profile,
        "claims": [
            {"key": c["key"], "verdict": c["verdict"]["verdict"]}
            for c in (outcome or {}).get("claims", [])
        ]
        if isinstance(outcome, dict)
        else [],
        "limits": list(LIMITS),
    }


def markdown(report: Mapping[str, Any], core_sha256: str | None) -> str:
    lines = [
        f"# Dossier verification of {report['paper']}",
        "",
        "Item (a) of section 10.2 of docs/plans/v0.3-plan.md, by "
        "calibration/v0.3/verify_dossiers.py",
        "(docs/validation/v0.3/dossier-verification-acceptance.md), with the frozen code of "
        "the locks.",
        "",
        f"**Result: {report['result']}.**",
        "",
    ]
    if core_sha256:
        lines += [f"Sealed core: `{core_sha256}`.", ""]
    lines += ["## Claims (recomputed and recorded)", ""]
    lines += [f"- `{c['key']}`: {c['verdict']}" for c in report["claims"]]
    if report["profile"]:
        lines += ["", f"Profile: {report['profile']['headline']}"]
    lines += ["", "## Findings", ""]
    lines += [f"- {f}" for f in report["findings"]] or ["None: checks V1 to V5 passed."]
    lines += ["", "## Limits", ""] + [f"- {x}" for x in report["limits"]]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("papers", nargs="*", default=list(SAMPLE))
    parser.add_argument("--out", type=Path, help="a folder for one report per paper")
    args = parser.parse_args(argv)
    ok = True
    for arxiv in args.papers:
        report = verify(arxiv)
        ok = ok and report["result"] == "VERIFIED"
        print(f"{arxiv}: {report['result']}" + "".join(f"\n  {f}" for f in report["findings"]))
        if args.out:
            folder = args.out / arxiv
            folder.mkdir(parents=True, exist_ok=False)
            seal = MAIN / "dossiers" / arxiv / "dossier" / "SEAL.json"
            core = json.loads(seal.read_bytes())["core_sha256"] if seal.is_file() else None
            (folder / "verification.json").write_bytes(canonical_bytes(report))
            (folder / "verification.md").write_text(
                markdown(report, core), encoding="utf-8", newline="\n"
            )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
