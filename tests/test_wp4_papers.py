"""WP4 synthetic papers, end to end (docs/validation/v0.3/wp4-acceptance.md, W4.1 to W4.3a,
W4.5): each paper of tests/wp4_papers.py, fixed with its expected verdict before its first
run, runs through the WP3 integration (#46) on the subprocess backend, with cataloged
fixtures only, and must give its expected verdict and the checks that decide it."""

from __future__ import annotations

import json
import os
import re
import sys

import pytest

from ml_papers import dataset_bytes
from refute.packs.ml import integration as ig
from refute.packs.ml import orchestrate as orc
from refute.packs.ml import sandbox as sb
from refute.packs.ml import synthetic as sy
from refute.packs.ml.schema import MlClaimSchema, MlTarget, MlTestPlan
from synthetic_harness import fixture
from test_ml_integration import (
    ALL_RUNGS,
    SPLITS,
    dataset_evidence,
    plan_dict,
    split_sha256,
    value_target,
)
from wp4_papers import BASE_CONFIG, PAPERS, PHASES, SyntheticPaper

N = {"n_train": 2000, "n_val": 500, "n_test": 4000}


def _target(paper: SyntheticPaper, data: bytes, key_number: int = 1) -> dict:
    target = value_target(
        dict.fromkeys(paper.attacks, True), recompute=paper.recompute, routes=list(paper.routes)
    )
    # the split's identity from this paper's own dataset (a leak changes the splits)
    identity = target["coverage_evidence"]["method"].get("split_identity")
    if identity is not None:
        identity["labels_sha256"] = split_sha256("test", data)
        identity["other_splits"] = [
            {"name": s, "labels_sha256": split_sha256(s, data)} for s in SPLITS if s != "test"
        ]
    target["metric"]["reported"] = paper.reported
    target["key"] = target["key"][:-1] + str(key_number)
    target["inventory"]["position"] = key_number
    target["inventory"]["candidate_id"] = f"c{key_number}"
    if not paper.seed_argument:
        target["run"]["seed_argument"] = None
        target["metric"]["reported_n_seeds"] = None
        target["seeds"] = {"base": [0], "base_cap": 1, "base_source": "documented"}
        if paper.recompute:
            target["metric_recompute"]["predictions"]["file"] = "preds/base.npy"
    for entry in target["attacks"]:
        if entry["name"] in paper.not_applicable:
            entry["reason"] = paper.not_applicable[entry["name"]]
    return target


def _claim_file(paper: SyntheticPaper, data: bytes, targets: list[dict]) -> dict:
    plan = plan_dict(data)
    for stage, limits in paper.stages.items():
        plan["stages"][stage].update(limits)
    plan_model = MlTestPlan.model_validate(plan)
    resolved = []
    for target in targets:
        model = MlTarget.model_validate(target)
        resolved.append(MlClaimSchema._derive(plan_model, model, model.resolved()))  # noqa: SLF001
    return {"test_plan": plan_model.model_dump(mode="json", by_alias=True), "targets": resolved}


def _config(paper: SyntheticPaper, claim: dict, extra: dict) -> dict:
    """The trainer's configuration; a value like "attack[:2]" names claim seeds."""
    out = {**BASE_CONFIG, **paper.config, **extra}
    for key, value in list(out.items()):
        if isinstance(value, str) and (m := re.fullmatch(r"(\w+)\[:(\d+)\]", value)):
            out[key] = claim["seeds"][m.group(1)][: int(m.group(2))]
    return out


def build(paper: SyntheticPaper, claims: int = 1) -> tuple[bytes, dict]:
    """The paper's dataset and its resolved claim file (both deterministic)."""
    data = dataset_bytes(seed=7, leak=paper.leak, **N)
    targets = [_target(paper, data, k) for k in range(1, claims + 1)]
    return data, _claim_file(paper, data, targets)


def run_paper(tmp_path, paper: SyntheticPaper, claims: int = 1):
    data, claim_file = build(paper, claims)
    (tmp_path / "fetched").mkdir(parents=True)
    fetched = tmp_path / "fetched" / "synthetic.npz"
    fetched.write_bytes(data)
    expectations = sy.BuildExpectations(
        {r: ("ok" if a == "ok" else "procedure_error") for r, a in paper.ladder.items()}
    )
    workspaces, auths = {}, []
    for cid in ig.plan_container_ids(claim_file):
        folder = tmp_path / "ws" / re.sub(r"[^A-Za-z0-9_.-]", "_", cid)
        if cid.startswith("setup/build/"):
            data_files = {
                "ladder.json": json.dumps(paper.ladder).encode(),
                "Dockerfile": b"FROM scratch\n",
                "requirements.txt": b"numpy\n",
            }
            auth = fixture("ladder-build", folder, data_files)
        else:
            step = cid.split("/")[1]
            claim = next(t for t in claim_file["targets"] if cid.startswith(t["key"] + "/"))
            extra = dict(paper.step_config.get(step, {}))
            for name, overrides in paper.seed_config.items():
                m = re.fullmatch(r"(\w+)\[(\d+)\]", name)
                seed = claim["seeds"][m.group(1)][int(m.group(2))]
                if step == "seeds" and cid.endswith(f"/s{seed}"):
                    extra.update(overrides)
            settings = {"data": "data/dataset.npz", **_config(paper, claim, extra)}
            auth = fixture(
                "ml-paper",
                folder,
                {"config.json": json.dumps(settings).encode(), "data/dataset.npz": data},
            )
        workspaces[cid] = auth.root
        auths.append(auth)

    def classify(rung, result):
        text = result.log_path.read_text(encoding="utf-8", errors="replace")
        return sy.classify_synthetic_build(
            result.exit_code, result.stopped, text, expectations.by_rung[rung.name]
        )

    harness = ig.Harness(
        backend=sb.SubprocessBackend(auths),
        workspaces=workspaces,
        logs=tmp_path / "logs",
        command=lambda argv: (
            [sys.executable, "-I", *argv[1:]] if argv[0] == "python" else list(argv)
        ),
        datasets={"synthetic": dataset_evidence(fetched, data)},
        ladder_inputs=("Dockerfile", "requirements.txt"),
        build_command=lambda rung: [
            sys.executable,
            "-I",
            "build.py",
            rung.name,
            rung.python or "-",
        ],
        classify_build=classify,
        margin_usec=1_000_000,
        base_env=dict(os.environ),
    )
    return ig.run_paper(claim_file, harness)


def _statuses(claim: ig.ClaimOutcome) -> dict[str, str]:
    out = {c.name: c.status.value for c in claim.base}
    for attack in claim.attacks:
        out[attack.name] = attack.result.status.value if attack.result else "NOT_EXECUTED"
    return out


@pytest.mark.parametrize("paper", PAPERS, ids=[p.name for p in PAPERS])
def test_each_synthetic_paper_gives_its_expected_verdict(tmp_path, paper):
    outcome = run_paper(tmp_path, paper)
    (claim,) = outcome.claims
    statuses = _statuses(claim)
    assert claim.verdict.verdict.value == paper.expected, (claim.verdict.reason, statuses)
    for name, status in paper.expected_checks.items():
        assert statuses[name] == status, (name, statuses, claim.verdict.reason)
    for gate, cause in paper.expected_failures.items():
        assert claim.failures[gate].cause.value == cause, claim.failures
    # a route paper fails for the reason its case names, with every earlier gate passing,
    # and one that shows the examples does so through every route it declares, run by run
    # (Codex review of #111)
    base = {c.name: c for c in claim.base}
    if paper.expected_reason:
        for gate in ("environment_build", "data_present", "run_completed"):
            assert base[gate].status.value == "PASS", (gate, base[gate].message)
        assert paper.expected_reason in base["metric_extracted"].message, base[
            "metric_extracted"
        ].message
    if paper.expected_checks.get("metric_extracted") == "PASS":
        shown = base["metric_extracted"].metrics["routes_with_evidence"]
        assert shown and all(v == sorted(paper.routes) for v in shown.values()), shown
    # the claim profile (W4.4): one claim, its verdict as the headline
    assert outcome.profile.headline == f"1 of 1 drawn claims: {paper.expected}"
    if outcome.run is not None:
        assert outcome.run.accounting_valid or paper.expected == "INCONCLUSIVE"
    # the status flags (W4.4) and the attacks recorded as incomplete
    flags = (claim.verdict.basic_reproduction_obtained, claim.verdict.incomplete_coverage)
    assert flags == paper.flags, claim.verdict
    assert tuple(claim.verdict.attacks_incomplete) == paper.incomplete, claim.verdict
    # the counts of each attack's own result: what the injected effect must give
    attacks = {a.name: a for a in claim.attacks}
    for name, (valid, failures) in paper.expected_counts.items():
        metrics = attacks[name].result.metrics
        assert (metrics["valid_runs"], metrics["valid_failures"]) == (valid, failures), metrics
    # the runs a guard must stop, and only those
    resolved = build(paper)[1]["targets"][0]
    steps = outcome.run.steps if outcome.run is not None else ()
    records = {c.container_id: c for s in steps for c in s.containers}
    stopped = {
        cid
        for cid, record in records.items()
        if record.result is not None
        and record.result.stopped in (sb.STOP_ACTIVE_TIME, sb.STOP_NO_PROGRESS)
    }
    expected = set()
    for name in paper.interrupted:
        m = re.fullmatch(r"(\w+)\[(\d+)\]", name)
        seed = resolved["seeds"][m.group(1)][int(m.group(2))]
        expected.add(ig.container_id(claim.key, "seeds", "method", seed))
    planned = ig.plan_container_ids(build(paper)[1])
    for step in paper.interrupted_steps:
        expected.update(c for c in planned if f"/{step}/" in c)
        (record,) = [s for s in steps if s.phase == "attacks" and s.step == step]
        assert record.outcome is orc.Outcome.OPERATIONAL_GUARD, record
    # every attack run a guard stopped, and only those (the setup's rungs are checked by
    # their failure cause)
    assert {c for c in stopped if not c.startswith("setup/")} == expected
    # an attack that does not apply is recorded so in the claim, with its reason, and
    # never runs
    entries = {e["name"]: e for e in resolved["attacks"]}
    for name, reason in paper.not_applicable.items():
        assert entries[name]["applies"] is False and entries[name]["reason"] == reason
        assert name not in attacks
        assert not any(f"/{name}/" in cid for cid in records)


def test_the_no_seed_repository_runs_once_and_never_the_seeds_attack(tmp_path):
    paper = next(p for p in PAPERS if p.name == "no-seed-option")
    outcome = run_paper(tmp_path, paper)
    ids = [c.container_id for s in outcome.run.steps for c in s.containers]
    base = [i for i in ids if "/base/" in i]
    # one base run with no seed: the claim has no seed argument, so none is passed
    assert base == [f"{outcome.claims[0].key}/base/method/s-"]
    assert not any("/seeds/" in i for i in ids)


def test_n_attack_zero_is_recorded_as_no_distribution(tmp_path):
    paper = next(p for p in PAPERS if p.name == "no-attack")
    outcome = run_paper(tmp_path, paper)
    assert outcome.run.no_distribution and outcome.run.attack_claims == []


def test_every_base_reproduction_ends_before_the_first_attack(tmp_path):
    """W4.3a, execution in phases (WP3 D-S4): three claims, every base reproduction in
    the drawn order before the first attack of any claim."""
    paper = SyntheticPaper(
        "phases", "W4.3a: execution in phases", "REPRODUCED", attacks=PHASES["attacks"]
    )
    outcome = run_paper(tmp_path, paper, claims=PHASES["claims"])
    phases = [(s.phase, s.claim) for s in outcome.run.steps if s.phase != "setup"]
    keys = [c.key for c in outcome.claims]
    assert phases == [("base", k) for k in keys] + [("attacks", k) for k in keys]
    assert [c.verdict.verdict.value for c in outcome.claims] == PHASES["expected"]


@pytest.mark.parametrize("paper", PAPERS, ids=[p.name for p in PAPERS])
def test_each_paper_run_twice_gives_the_same_profile(tmp_path, paper):
    """W4.5: the experimental reproduction of each controlled case gives the same claim
    profile (verdicts, headline) and the same status of every check."""
    first = run_paper(tmp_path / "first", paper)
    second = run_paper(tmp_path / "second", paper)
    assert [(c.key, c.verdict.verdict) for c in first.claims] == [
        (c.key, c.verdict.verdict) for c in second.claims
    ]
    assert first.profile.headline == second.profile.headline
    assert [_statuses(c) for c in first.claims] == [_statuses(c) for c in second.claims]


def test_the_definitions_cover_the_verdict_paths():
    assert {p.expected for p in PAPERS} == {
        "REPRODUCED",
        "FRAGILE",
        "NOT_REPRODUCED",
        "NOT_REPRODUCIBLE",
        "INCONCLUSIVE",
    }
    assert set(ALL_RUNGS) == set(PAPERS[0].ladder)


def test_each_coverage_route_has_papers_on_both_sides():
    """1.5a: every route shows the examples in one paper (REPRODUCED) and fails to close
    the chain, or finds a conflict, in another (metric_extracted INCONCLUSIVE)."""
    for name in ("saved_predictions", "sufficient_statistics", "printed_count", "hook"):
        alone = [p for p in PAPERS if p.routes == (name,)]
        sides = {p.expected_checks.get("metric_extracted") for p in alone}
        assert {"PASS", "INCONCLUSIVE"} <= sides, (name, sides)
    # every INCONCLUSIVE route paper names its reason
    for p in PAPERS:
        if (
            p.name.startswith("route")
            and p.expected_checks.get("metric_extracted") == "INCONCLUSIVE"
        ):
            assert p.expected_reason, p.name
