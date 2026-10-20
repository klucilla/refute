"""Dossier verification of the main sample of v0.3 (item (a) of plan section 10.2).

Implements docs/validation/v0.3/dossier-verification-acceptance.md (with its section 4a).
Outside the code hash of the locks: it changes nothing in src/ and calls the frozen functions of
the package (refute.core.paper.aggregate_claim and paper_profile, refute.packs.ml.orchestrate
._outcome, the ClaimContext derivations and not_run_reason of refute.packs.ml.integration). It
reads a published dossier, its published claim folder and the committed seal and annex records,
runs no experiment and opens no network connection.

Usage (from the repository root):
  uv run --frozen python calibration/v0.3/verify_dossiers.py [--out DIR] [ARXIV ...]
With no arXiv id, the five papers of the main sample. Exit code 0 when every dossier is
VERIFIED, 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
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
from refute.core.seal import ANNEX_DIR, ANNEX_MANIFEST, SEAL_NAME
from refute.core.verdict import PaperVerdict, Severity, TestResult, TestStatus
from refute.packs.ml import integration as ig
from refute.packs.ml import ladder as ld
from refute.packs.ml import orchestrate as orc
from refute.packs.ml.production import _plain

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "calibration/v0.3/main"
SEAL_RECORD = MAIN / "SEAL-RECORD.md"
ANNEX_RECORD = MAIN / "ANNEX-RECORD.md"
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
    "The lock (claim.lock.json) is read from the published claim folder, not from the "
    "dossier; its history file is not read.",
    "The sample has no executed attack: the rebuilding of attack records is shown by a "
    "round-trip test on synthetic records.",
)
REFUTE_SIDE = (
    orc.Outcome.BUDGET_EXHAUSTED,
    orc.Outcome.OPERATIONAL_GUARD,
    orc.Outcome.REFUTE_ERROR,
)
NOT_ELIGIBLE = "not eligible for attacks (base not obtained or no applicable attack)"
SETUP_INCOMPLETE = "the setup did not complete"
NOT_SUCCESS = "the container ended but is not a success"
RUNNER_STOPS = ("unexpected error: ", "the completeness check failed: ")
# the refusals of the frozen accountant (budget.Accountant.authorized), kept by _refused
ACCOUNTING_REFUSAL = "the accounting is invalid ("
REFUSALS = (
    ACCOUNTING_REFUSAL,
    "unknown account ",
    "the setup account is closed",
    "the setup account is still open",
    "no transfer from the attacks to the base reproduction",
    "the attack pool is not open",
    "claims run in the drawn order; the current claim is ",
)
NOT_ELIGIBLE_REFUSAL = " is not eligible for attacks"
BUDGET_POOLS = {
    orc.SETUP: (bg.Pool.SETUP,),
    orc.BASE: (bg.Pool.BASE, bg.Pool.SETUP),
    orc.ATTACKS: (bg.Pool.ATTACKS,),
}
_HEX = re.compile(r"`([0-9a-f]{64})`")


class RecordError(Exception):
    """A record that cannot be read as the frozen code wrote it."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---- the committed records (V1 anchors) ---------------------------------------------------


def seal_record(path: Path = SEAL_RECORD) -> dict[str, str]:
    """paper -> core SHA-256, from the table of SEAL-RECORD.md."""
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 4 and re.fullmatch(r"\d{4}\.\d{4,5}", cells[1]):
            found = _HEX.findall(cells[3])
            if found:
                out[cells[1]] = found[0]
    return out


def annex_record(path: Path = ANNEX_RECORD) -> dict[str, dict[str, str]]:
    """paper -> {annex name: ANNEX.json SHA-256}, from the tables of ANNEX-RECORD.md."""
    out: dict[str, dict[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 4 and re.fullmatch(r"\d{4}\.\d{4,5}", cells[1]):
            name = re.fullmatch(rf"`{ANNEX_DIR}/([a-z0-9-]+)/`", cells[2])
            found = _HEX.findall(cells[3])
            if name and found:
                out.setdefault(cells[1], {})[name.group(1)] = found[0]
    return out


# ---- rebuilding the frozen inputs from the record ----------------------------------------


def _test(d: Any) -> TestResult | None:
    if d is None:
        return None
    try:
        coverage = d.get("coverage")
        if coverage is not None and type(coverage) is not int:
            raise TypeError(f"coverage {coverage!r} is not an integer")
        return TestResult(
            d["name"],
            TestStatus(d["status"]),
            Severity(d["severity"]),
            d["message"],
            metrics=dict(d.get("metrics") or {}),
            thresholds=dict(d.get("thresholds") or {}),
            inputs=dict(d.get("inputs") or {}),
            coverage=coverage,
            coverage_unit=d.get("coverage_unit") or "",
        )
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise RecordError(f"a check record cannot be read: {type(exc).__name__}: {exc}") from None


def _attack(d: Mapping[str, Any]) -> Attack:
    return Attack(d["name"], _test(d.get("run")), _test(d.get("metric")), _test(d.get("result")))


def _failure(d: Mapping[str, Any]) -> GateFailure:
    cause = d["cause"]
    try:
        cause = FailureCause(cause)
    except ValueError:
        pass  # an unknown cause is kept as recorded; known_cause decides
    for field in ("attempts_completed", "attempts_required"):
        if type(d[field]) is not int:
            raise RecordError(f"a gate failure's {field} is not an integer")
    return GateFailure(cause, d["attempts_completed"], d["attempts_required"])


# ---- V1 -----------------------------------------------------------------------------------


def check_hashes(arxiv: str, dossier: Path, claim_dir: Path, findings: list[str]) -> None:
    """V1: the manifest, the seal against the committed record, the annexes against theirs,
    the claim's bytes and the lock's hash."""
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
    if (dossier / SEAL_NAME).is_file():
        core = json.loads((dossier / SEAL_NAME).read_bytes()).get("core_sha256")
        committed = seal_record().get(arxiv)
        if committed is None or core != committed:
            findings.append(f"V1 seal: core {core} is not the one SEAL-RECORD.md commits")
    present = {}
    annexes = dossier / ANNEX_DIR
    if annexes.is_dir():
        for entry in sorted(annexes.iterdir()):
            manifest = entry / ANNEX_MANIFEST
            present[entry.name] = _sha(manifest.read_bytes()) if manifest.is_file() else ""
    listed = annex_record().get(arxiv, {})
    if present != listed:
        findings.append(f"V1 annexes: present {present}, ANNEX-RECORD.md lists {listed}")
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


# ---- shapes -------------------------------------------------------------------------------


def _need(cond: bool, what: str) -> None:
    if not cond:
        raise RecordError(what)


def check_shapes(outcome: Any) -> None:
    """The fields the checks decide on, with their recorded types (section 4a)."""
    _need(isinstance(outcome, dict), "outcome is not an object")
    for key in ("claims", "profile", "ladder"):
        _need(key in outcome, f"outcome has no {key}")
    _need(isinstance(outcome["claims"], list), "outcome.claims is not a list")
    for c in outcome["claims"]:
        _need(isinstance(c, dict), "a claim record is not an object")
        for key in ("key", "verdict", "computed", "base", "attacks", "failures", "notes"):
            _need(key in c, f"a claim record has no {key}")
        _need(isinstance(c["base"], list) and isinstance(c["attacks"], list), "claim lists")
        _need(isinstance(c["failures"], dict), "a claim's failures is not an object")
        _need(isinstance(c["notes"], list), "a claim's notes is not a list")
        _need(isinstance(c["verdict"], dict), "a claim's verdict is not an object")
    _need(isinstance(outcome["profile"], dict), "outcome.profile is not an object")
    ladder = outcome["ladder"]
    _need(isinstance(ladder, dict), "outcome.ladder is not an object")
    _need(isinstance(ladder.get("attempts"), list), "outcome.ladder.attempts is not a list")
    _need(all(isinstance(a, dict) for a in ladder["attempts"]), "a ladder attempt")
    _need(
        [a.get("rung") for a in ladder["attempts"]] == list(ld.RUNGS),
        f"the ladder does not list the frozen rungs {list(ld.RUNGS)}",
    )
    _need(all(type(a.get("applicable")) is bool for a in ladder["attempts"]), "applicable")
    run = outcome.get("run")
    if run is None:
        return
    _need(isinstance(run, dict), "outcome.run is not an object")
    for key in ("accounting_valid", "setup_exhausted", "no_distribution"):
        _need(type(run.get(key)) is bool, f"run.{key} is not a boolean")
    _need(isinstance(run.get("stopped"), str), "run.stopped is not a string")
    for key in ("steps", "attack_claims", "invalid_reasons"):
        _need(isinstance(run.get(key), list), f"run.{key} is not a list")
    _need(all(isinstance(r, str) for r in run["invalid_reasons"]), "an invalid reason")
    _need(isinstance(run.get("base_obtained"), dict), "run.base_obtained is not an object")
    _need(all(type(v) is bool for v in run["base_obtained"].values()), "base_obtained values")
    for s in run["steps"]:
        _need(isinstance(s, dict), "a step is not an object")
        for key in ("phase", "claim", "step", "outcome", "reason", "containers"):
            _need(key in s, f"a step has no {key}")
        _need(isinstance(s["reason"], str), "a step's reason is not a string")
        _need(isinstance(s["containers"], list), "a step's containers is not a list")
        for c in s["containers"]:
            _need(isinstance(c, dict) and "container_id" in c and "error" in c, "a container")
            r = c.get("result")
            _need(r is None or isinstance(r, dict), "a container result")
            if r is not None:
                _need(r.get("stopped") is None or isinstance(r["stopped"], str), "a stop")
                # a run stopped by supervision has no exit code (section 4b)
                code = r.get("exit_code")
                _need(type(code) is int or (code is None and r["stopped"]), "an exit_code")


# ---- V2, V3 -------------------------------------------------------------------------------


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
        if run is not None and run["accounting_valid"] is not True:
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


# ---- V4, V5 -------------------------------------------------------------------------------


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


FALLBACK_FAILED = "the fallback failed: "


def _candidates(
    step: Mapping[str, Any], records: list[Any], rungs: int
) -> tuple[set[tuple[str, str]], set[tuple[str, str]]] | str:
    """What the frozen runner can record for a step with containers: exact (outcome, reason)
    pairs and (outcome, reason prefix) pairs; or a finding. ``rungs`` is the number of
    applicable rungs of the ladder."""
    name = step["step"]
    if name == "build":
        for i, rec in enumerate(records):
            out, reason = orc._outcome([rec])
            last = i == len(records) - 1
            if rec.result is None or out in REFUTE_SIDE:
                if not last:
                    return "a rung after a stop on Refute's side ran"
                return {(str(out), reason)}, set()
            if not last:
                if out is not orc.Outcome.FAILED:
                    return f"rung {rec.container_id} is followed by another but did not fail"
                continue
            # the classifier of the last rung may raise (section 4b)
            prefixes = {(str(orc.Outcome.REFUTE_ERROR), FALLBACK_FAILED)}
            if out is orc.Outcome.COMPLETED:
                exact = {(str(orc.Outcome.COMPLETED), ""), (str(orc.Outcome.FAILED), NOT_SUCCESS)}
                return exact, prefixes
            exact = {(str(orc.Outcome.FAILED), reason)}
            if len(records) < rungs:
                # classified "next", then the next rung's grant refused (section 4b)
                exact.add(
                    (str(orc.Outcome.BUDGET_EXHAUSTED), f"{bg.BUDGET_EXHAUSTED} ({bg.Pool.SETUP})")
                )
                # the setup account's only other refusal (budget.authorized)
                prefixes.add((str(orc.Outcome.REFUTE_ERROR), ACCOUNTING_REFUSAL))
            return exact, prefixes
    if name.startswith("data/"):
        if len(records) != 1:
            return "a container reader's step has one container"
        out, reason = orc._outcome(records)
        if records[0].result is None or out in REFUTE_SIDE:
            return {(str(out), reason)}, set()
        return {(str(orc.Outcome.COMPLETED), "")}, set()
    out, reason = orc._outcome(records)
    return {(str(out), reason)}, set()


def _override_ok(reason: str, base: str, step, run) -> bool:
    """A REFUTE_ERROR closing the step (_close_step): its containers' reason, then rejected
    records of its own containers or entries of the run's invalid reasons."""
    parts = reason.split("; ")
    if base:
        if parts[: len(base.split("; "))] != base.split("; "):
            return False
        parts = parts[len(base.split("; ")) :]
    if not parts:
        return False
    cids = [c["container_id"] for c in step["containers"]]
    return all(
        p in run["invalid_reasons"]
        or any(p.startswith(f"{cid}: record rejected: ") for cid in cids)
        for p in parts
    )


def _where(s: Mapping[str, Any]) -> str:
    return " ".join(p for p in (s["phase"], s["claim"] or "", s["step"]) if p)


def _weights(setup: Mapping[str, Any]) -> dict[str, ig.WeightsEvidence]:
    out = {}
    for name, e in (setup.get("repository_weights") or {}).items():
        copy = Path(e["path"]) if e.get("verified") is True else None
        out[name] = ig.WeightsEvidence(e["path"], e["sha256"], copy, e.get("reason"))
    return out


def check_steps(
    claim_file: Mapping[str, Any],
    outcome: Mapping[str, Any],
    setup: Mapping[str, Any],
    findings: list[str],
) -> None:
    """V4 and V5: the execution states and the reasons of every interruption, from the step
    records themselves (section 4a)."""
    plan = claim_file["test_plan"]
    run, ladder = outcome.get("run"), outcome["ladder"]
    attempts = ladder["attempts"]
    if run is None:
        if any(a["applicable"] for a in attempts):
            findings.append("V4 run: no run recorded although a rung of the ladder applies")
        for c in outcome["claims"]:
            for t in c["base"]:
                if t.get("name") == "environment_build" and t.get("status") == "PASS":
                    findings.append(f"V4 run: no run, yet {c['key']}'s environment_build passed")
        return
    steps = run["steps"]
    ids = [(s["phase"], s["claim"], s["step"]) for s in steps]
    plan_ids = expected_steps(claim_file)
    contexts = {t["key"]: ig.ClaimContext(t, plan) for t in claim_file["targets"]}
    if len(set(ids)) != len(ids):
        findings.append("V4 steps: a step is recorded twice")
    missing = [i for i in plan_ids if i not in ids]
    extra = [
        i
        for i, s in zip(ids, steps, strict=True)
        if i not in plan_ids
        and not (
            i[0] == orc.BASE
            and i[2] == "base_obtained"
            and i[1] in contexts
            and s["outcome"] == orc.Outcome.REFUTE_ERROR
            and s["reason"].startswith("the base evaluation failed: ")
            and not s["containers"]
        )
    ]
    if missing:
        findings.append(f"V4 steps: missing {missing}")
    if extra:
        findings.append(f"V4 steps: not in the plan {extra}")
    ran = [i for i, s in zip(ids, steps, strict=True) if s["containers"]]
    positions = [plan_ids.index(i) for i in ran if i in plan_ids]
    if positions != sorted(positions):
        findings.append(f"V4 order: the steps that ran are not in the plan's order: {ran}")
    by_id = dict(zip(ids, steps, strict=True))
    stopped = run["stopped"]
    # the stop and its consequences
    errors = [s for s in steps if s["outcome"] == orc.Outcome.REFUTE_ERROR]
    if errors:
        want = f"{_where(errors[0])}: {errors[0]['reason'] or 'Refute error'}"
        if stopped != want:
            findings.append(f"V4 run: stopped {stopped!r}, the first Refute error gives {want!r}")
    elif stopped and not stopped.startswith(RUNNER_STOPS):
        findings.append(f"V4 run: stopped {stopped!r} with no Refute error step")
    if stopped:
        if run["accounting_valid"]:
            findings.append("V4 run: stopped, yet the accounting is valid")
        if stopped not in run["invalid_reasons"]:
            findings.append("V4 run: the stop is not among the invalid reasons")
    setup_ok = all(
        by_id.get(i, {}).get("outcome") == orc.Outcome.COMPLETED
        for i in plan_ids
        if i[0] == orc.SETUP
    )
    weights = _weights(setup)
    rungs = sum(1 for a in attempts if a["applicable"])
    for s in steps:
        where = _where(s)
        try:
            out = orc.Outcome(s["outcome"])
        except ValueError:
            findings.append(f"V4 {where}: unknown outcome {s['outcome']!r}")
            continue
        if out is not orc.Outcome.COMPLETED and not s["reason"]:
            findings.append(f"V4 {where}: {out} with no reason")
        for c in s["containers"]:
            if c["result"] is None and not c["error"]:
                findings.append(f"V4 {where}: container {c['container_id']} has no result or error")
            stop = (c["result"] or {}).get("stopped")
            if stop and stop not in orc._KNOWN_STOPS:
                findings.append(f"V4 {where}: container {c['container_id']} stop cause {stop!r}")
        if s["containers"]:
            records = _records(s)
            cands = _candidates(s, records, rungs)
            if isinstance(cands, str):
                findings.append(f"V4 {where}: {cands}")
                continue
            exact, prefixes = cands
            ok = (
                (str(out), s["reason"]) in exact
                or any(
                    str(out) == o and s["reason"].startswith(p) and s["reason"] != p
                    for o, p in prefixes
                )
                or (
                    out is orc.Outcome.REFUTE_ERROR
                    and any(_override_ok(s["reason"], r, s, run) for _, r in exact)
                )
            )
            if not ok:
                findings.append(
                    f"V4 {where}: recorded {out} {s['reason']!r} does not follow from its "
                    "containers"
                )
            continue
        if out is orc.Outcome.BUDGET_EXHAUSTED:
            pools = BUDGET_POOLS.get(s["phase"], ())
            if s["reason"] not in {f"{bg.BUDGET_EXHAUSTED} ({p})" for p in pools}:
                findings.append(f"V4 {where}: a refused grant without its budget reason")
            continue
        if out is orc.Outcome.REFUTE_ERROR:
            # a refused grant (budget.authorized's reasons) or the base evaluation; its stop
            # and accounting are checked above
            known = REFUSALS if s["phase"] != orc.SETUP else (ACCOUNTING_REFUSAL,)
            evaluation = s["step"] == "base_obtained" and s["phase"] == orc.BASE
            eligible_refusal = s["phase"] == orc.ATTACKS and s["reason"].endswith(
                NOT_ELIGIBLE_REFUSAL
            )
            if not evaluation and not eligible_refusal and not s["reason"].startswith(known):
                findings.append(
                    f"V4 {where}: a refusal the accountant never gives: {s['reason']!r}"
                )
            if s["reason"].startswith(ACCOUNTING_REFUSAL) and run["accounting_valid"]:
                findings.append(f"V4 {where}: refused for invalid accounting, yet it is valid")
            continue
        if out is not orc.Outcome.NOT_EXECUTED:
            findings.append(f"V4 {where}: {out} with no container")
            continue
        why = _not_executed_problem(s, by_id, plan_ids, run, setup_ok, contexts, plan, weights)
        if why:
            findings.append(f"V4 {where}: not executed: {why}")
    # what a step needs before it may run (section 4c): nothing runs after the first Refute
    # error; a setup step runs only after the earlier ones completed; the base and the attacks
    # only after a completed setup (and the base not after an exhausted setup budget); an
    # attack only for a claim eligible for attacks
    seen_error = False
    setup_broken = False
    for s, i in zip(steps, ids, strict=True):
        where = _where(s)
        if s["containers"] and seen_error:
            findings.append(f"V4 {where}: ran after the paper stopped on a Refute error")
        if s["outcome"] == orc.Outcome.REFUTE_ERROR:
            seen_error = True
        if s["phase"] == orc.SETUP and i in plan_ids:
            if s["containers"] and setup_broken:
                findings.append(f"V4 {where}: ran after an earlier setup step did not complete")
            if s["outcome"] != orc.Outcome.COMPLETED:
                setup_broken = True
        elif s["containers"]:
            if not setup_ok:
                findings.append(f"V4 {where}: ran although the setup did not complete")
            if s["phase"] == orc.ATTACKS and s["claim"] not in run["attack_claims"]:
                findings.append(f"V4 {where}: ran for a claim not eligible for attacks")
    # what each claim's base step must say when it did not run
    for key, ctx in contexts.items():
        base = by_id.get((orc.BASE, key, "base"))
        if setup_ok and run["setup_exhausted"] and base is not None and base["containers"]:
            findings.append(f"V4 base {key} base: ran although the setup's budget was exhausted")
        if base is None or base["outcome"] != orc.Outcome.NOT_EXECUTED or stopped:
            continue
        if not setup_ok:
            want = SETUP_INCOMPLETE
        elif run["setup_exhausted"]:
            want = f"{bg.BUDGET_EXHAUSTED} ({bg.Pool.SETUP})"
        else:
            want = ig.not_run_reason(ctx.claim, plan, weights)
        if base["reason"] != want:
            findings.append(f"V4 base {key} base: reason {base['reason']!r}, expected {want!r}")
    # the run's own record
    if sorted(run["base_obtained"]) != sorted(contexts):
        findings.append("V4 run: base_obtained does not name exactly the claims")
    for key, obtained in run["base_obtained"].items():
        base = by_id.get((orc.BASE, key, "base"))
        if obtained and (base is None or base["outcome"] != orc.Outcome.COMPLETED):
            findings.append(f"V4 run: base_obtained true for {key}, whose base did not complete")
    has_attack = {k for (p, k, _) in plan_ids if p == orc.ATTACKS}
    eligible = {k for k, v in run["base_obtained"].items() if v and k in has_attack}
    if not stopped and set(run["attack_claims"]) != eligible:
        findings.append(
            f"V4 run: attack_claims {run['attack_claims']}, expected {sorted(eligible)}"
        )
    # V5: the ladder
    build = by_id.get((orc.SETUP, None, "build"))
    applicable = [f"setup/build/{a['rung']}" for a in attempts if a["applicable"]]
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


def _not_executed_problem(s, by_id, plan_ids, run, setup_ok, contexts, plan, weights) -> str:
    """Why a NOT_EXECUTED reason is not one the frozen runner gives for this state, or ''."""
    reason, phase, claim = s["reason"], s["phase"], s["claim"]
    stopped = run["stopped"]
    if reason.startswith("the paper stopped: "):
        return (
            "" if stopped and reason == f"the paper stopped: {stopped}" else "a stop not recorded"
        )
    if reason == "not reached":
        return "'not reached' in a run that did not stop"
    if reason == SETUP_INCOMPLETE:
        return "" if phase == orc.BASE and not setup_ok else "the setup completed"
    if reason == f"{bg.BUDGET_EXHAUSTED} ({bg.Pool.SETUP})":
        ok = phase == orc.BASE and setup_ok and run["setup_exhausted"]
        return "" if ok else "the setup's budget was not exhausted"
    if reason == NOT_ELIGIBLE:
        ok = phase == orc.ATTACKS and claim not in run["attack_claims"]
        return "" if ok else "the claim is eligible for attacks"
    m = re.fullmatch(r"step (.+) did not complete \((.+)\)", reason)
    if m:
        prior_id = (phase, claim, m.group(1))
        prior = by_id.get(prior_id)
        own = (phase, claim, s["step"])
        ok = (
            prior is not None
            and prior_id != own
            and prior_id in plan_ids
            and own in plan_ids
            and plan_ids.index(prior_id) < plan_ids.index(own)
            and prior["outcome"] == m.group(2)
            and prior["outcome"] != orc.Outcome.COMPLETED
        )
        return "" if ok else "no earlier step of its phase and claim ended so"
    ctx = contexts.get(claim)
    if phase == orc.BASE and ctx is not None and setup_ok and not run["setup_exhausted"]:
        if reason == ig.not_run_reason(ctx.claim, plan, weights):
            return ""
    return f"a reason the runner never gives here: {reason!r}"


# ---- one dossier ----------------------------------------------------------------------------


def verify(
    arxiv: str, dossier: Path | None = None, claim_dir: Path | None = None
) -> dict[str, Any]:
    dossier = dossier or MAIN / "dossiers" / arxiv / "dossier"
    claim_dir = claim_dir or MAIN / "claims" / arxiv / "claim"
    findings: list[str] = []
    outcome: Any = None
    try:
        check_hashes(arxiv, dossier, claim_dir, findings)
        claim_file = json.loads((dossier / "claim_file.json").read_bytes())
        record = json.loads((dossier / "dossier.json").read_bytes())
        outcome = record.get("outcome") if isinstance(record, dict) else None
        check_shapes(outcome)
        check_verdicts(claim_file, outcome, findings)
        check_steps(claim_file, outcome, record.get("setup") or {}, findings)
    except Exception as exc:  # any record the frozen code could not have written is a finding
        findings.append(f"the dossier cannot be read as recorded: {type(exc).__name__}: {exc}")
    readable = isinstance(outcome, dict) and isinstance(outcome.get("claims"), list)
    claims = []
    if readable:
        for c in outcome["claims"]:
            if isinstance(c, dict) and isinstance(c.get("verdict"), dict):
                claims.append({"key": c.get("key"), "verdict": c["verdict"].get("verdict")})
    profile = outcome.get("profile") if readable else None
    return {
        "format": FORMAT,
        "paper": arxiv,
        "result": "NOT VERIFIED" if findings else "VERIFIED",
        "findings": findings,
        "profile": profile if isinstance(profile, dict) else None,
        "claims": claims,
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
        lines += ["", f"Profile: {report['profile'].get('headline')}"]
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
            seal = MAIN / "dossiers" / arxiv / "dossier" / SEAL_NAME
            core = json.loads(seal.read_bytes())["core_sha256"] if seal.is_file() else None
            (folder / "verification.json").write_bytes(canonical_bytes(report))
            (folder / "verification.md").write_text(
                markdown(report, core), encoding="utf-8", newline="\n"
            )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
