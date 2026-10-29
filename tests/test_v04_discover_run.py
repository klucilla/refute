"""v0.4 WP1 (issue #174) end to end: ``refute discover`` stages and the promotion record, on a
synthetic cache, from a committed and locked discover claim. Synthetic data only."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import git, target_entry, targets_file, write_yaml
from refute.core.io import read_json
from refute.core.lock import LockError, create_lock
from refute.core.run import execute_run
from refute.packs.tess.discover.funnel import PROMOTION_SCHEMA
from refute.packs.tess.synthetic import discovery_plan_dict, scenario_data, write_synthetic_cache

CATALOGS = {
    "toi.csv": b"TOI,TIC ID,RA,Dec,Period (days)\n900.01,900,10:00:00,+10:00:00,5.5\n",
    "ctoi.csv": b"CTOI,TIC ID,RA,Dec,Period (days)\n901.01,901,20.0,10.0,5.5\n",
    "pscomppars.csv": b"pl_name,tic_id,ra,dec,pl_orbper\nX b,TIC 902,30.0,10.0,5.5\n",
    "tess_eb.tsv": b"TIC\tRAJ2000\tDEJ2000\tPer\n\t\t\td\n--\t--\t--\t--\n903\t40.0\t10.0\t5.5\n",
    "gaia_dr3_eb.csv": b"source_id,ra,dec,frequency\n904,50.0,10.0,0.2\n",
}


def _inputs(root: Path) -> str:
    import hashlib

    from refute.packs.tess.discover import pilot

    folder = root / "inputs"
    folder.mkdir(parents=True, exist_ok=True)
    records = []
    for name, data in CATALOGS.items():
        (folder / name).write_bytes(data)
        records.append(pilot.record(name, "synthetic", data, "2026-10-29T00:00:00Z"))
    content = json.dumps({"files": records, "s_max": 99}, indent=2).encode()
    (root / "inputs.json").write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def _discover_claim(inputs_sha: str | None = None) -> dict:
    plan = discovery_plan_dict()
    if inputs_sha:
        plan["discovery"]["inputs"] = {"inputs_json": inputs_sha}
    return {
        "schema_version": 1,
        "id": "synthetic-discover",
        "kind": "discover",
        "pack": "tess",
        "title": "Synthetic discover pilot",
        "hypothesis": "The funnel runs its stages as declared.",
        "created": "2026-10-29",
        "authors": ["Refute test suite"],
        "attachments": [{"path": "targets.yaml", "role": "targets"}],
        "test_plan": plan,
    }


@pytest.fixture
def discover(git_repo: Path, tmp_path: Path):
    claim_dir = git_repo / "claims"
    exploration = target_entry(2, "exploration", None)
    exploration["mast"] = {"tic_ra": 150.0, "tic_dec": -30.0}  # as the selection walk records
    targets = [target_entry(1, "planet", 3.7), exploration]
    write_yaml(claim_dir / "targets.yaml", targets_file(targets))
    claim = write_yaml(claim_dir / "claim.yaml", _discover_claim(_inputs(git_repo)))
    git(git_repo, "add", "-A")
    git(git_repo, "commit", "-q", "-m", "claim")
    create_lock(claim)
    cache = tmp_path / "cache"
    data = scenario_data("planet")
    for tic in (1, 2):
        write_synthetic_cache(cache, tic, data.lc, data.star, aux=data.aux)
    return claim, cache


def _run(claim, cache, out, **kw):
    return execute_run(
        claim, mode="discover", out_dir=out, workers=1, offline=True, cache_dir=cache, **kw
    )


def test_a_discover_claim_is_locked_only_from_a_clean_commit(git_repo: Path):
    claim_dir = git_repo / "claims"
    write_yaml(claim_dir / "targets.yaml", targets_file([target_entry(1, "planet", 3.7)]))
    claim = write_yaml(claim_dir / "claim.yaml", _discover_claim())
    with pytest.raises(LockError, match="discover claim"):
        create_lock(claim)


def test_stage_1_reads_no_pixel_file_and_defers_the_pixel_tests(discover, tmp_path):
    claim, cache = discover
    outcome = _run(claim, cache, tmp_path / "out", stage=1, run_id="s1")
    assert outcome.exit_code == 0, outcome.messages
    for key in ("TIC-1", "TIC-2"):
        verdict = read_json(outcome.run_dir / key / "verdict.json")
        assert verdict["test_plan"]["data"]["target_pixel_files"] is False
        tests = {t["name"]: t for t in verdict["tests"]}
        assert tests["centroid_shift"]["status"] == "INCONCLUSIVE"
        assert tests["centroid_shift"]["coverage"] == 0
        assert verdict["discovery"]["stage"] == 1
        assert verdict["method_status"] == "not_validated"
        report = (outcome.run_dir / key / "report.md").read_text(encoding="utf-8")
        assert "not_validated" in report
        reproduce = (outcome.run_dir / key / "REPRODUCE.md").read_text(encoding="utf-8")
        assert "refute discover" in reproduce and "--stage 1" in reproduce
    assert outcome.summary["stage"] == 1


def test_stage_2_of_a_funnel_star_needs_a_promotion_record(discover, tmp_path):
    claim, cache = discover
    refused = _run(claim, cache, tmp_path / "out", stage=2, run_id="no-record")
    assert refused.exit_code == 1
    assert any("--promotion" in m and "TIC-2" in m for m in refused.messages)
    assert not (tmp_path / "out" / "no-record").exists()


def test_a_control_runs_stage_2_without_a_promotion_record(discover, tmp_path):
    claim, cache = discover
    outcome = _run(claim, cache, tmp_path / "out", stage=2, run_id="ctl", targets=["TIC-1"])
    assert outcome.exit_code == 0, outcome.messages
    verdict = read_json(outcome.run_dir / "TIC-1" / "verdict.json")
    assert verdict["test_plan"]["data"]["target_pixel_files"] is True
    assert verdict["discovery"]["deferred_tests"] == []


def test_5_8_the_dossier_carries_its_selection_evidence_and_checks_whole(discover, tmp_path):
    from refute.core.dossier import check_dossier
    from refute.packs.tess.discover.case import build_case, missing_items

    claim, cache = discover
    outcome = _run(claim, cache, tmp_path / "out", stage=2, run_id="ctl5", targets=["TIC-1"])
    dossier = outcome.run_dir / "TIC-1"
    targets = (dossier / "attachments" / "targets.yaml").read_text(encoding="utf-8")
    assert "TIC-1" in targets  # the target's selection record is inside the core
    assert check_dossier(dossier).integrity_problems == []
    verdict = read_json(dossier / "verdict.json")
    case = build_case(verdict, read_json(dossier / "target.json"), {"overall": "no_match"}, {})
    assert set(missing_items(case)) == {"review", "questions_for_a_human", "conclusion"}
    (dossier / "attachments" / "targets.yaml").unlink()
    assert check_dossier(dossier).integrity_problems


def _binding(claim: Path) -> tuple[dict, dict]:
    """The locked claim's targets by key and its identity (claim id, claim hash, code hash)."""
    from refute.core.claim import load_claim
    from refute.core.lock import lock_path_for

    loaded = load_claim(claim)
    targets = {t["key"]: t for t in loaded.pack.schema.targets_for_run(loaded)}
    lock = read_json(lock_path_for(claim))
    identity = {
        "claim_id": loaded.claim.id,
        "claim_sha256": loaded.sha256(),
        "code_sha256": lock["code"]["sha256"],
    }
    return targets, identity


@pytest.fixture
def promoted(discover, tmp_path):
    """A stage-1 run, its entries and the (N, K) decision committed, and the promotion record
    the protocol produces from them."""
    from refute.core.claim import load_claim
    from refute.packs.tess.discover import funnel, pilot, runs
    from refute.packs.tess.discover.funnel import promotion_record

    claim, cache = discover
    root = claim.parent.parent
    # the (N, K) decision first, committed before any stage-1 run (only (50, 5) fits)
    decision = funnel.choose_n_k(funnel.ControlCosts(0.1, 0.15, 0.04, 0.05, 10e6), 2.0, 1e9)
    assert decision["chosen"] == {"N": 50, "K": 5}
    (root / "n_k.json").write_text(json.dumps(decision), "utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "(N, K) decision")
    n_k_commit = git(root, "rev-parse", "HEAD").strip()
    stage1 = _run(claim, cache, tmp_path / "stage1", stage=1, run_id="s1")
    inputs = json.loads((root / "inputs.json").read_text(encoding="utf-8"))
    indexes = pilot.catalog_indexes(root / "inputs", inputs)
    entries = runs.stage1_entries(stage1.run_dir, ["TIC-2"], indexes, *_binding(claim))
    assert entries[0]["eligibility"]["eligible"], entries[0]["eligibility"]  # the premise
    (root / "stage1").mkdir()
    (root / "stage1" / "entries.json").write_text(json.dumps({"entries": entries}), "utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "stage-1 results")
    provenance = {
        "results_commit": git(root, "rev-parse", "HEAD").strip(),
        "entries_path": "stage1/entries.json",
        "n_k_commit": n_k_commit,
        "n_k_path": "n_k.json",
        "inputs_json": "inputs.json",
        "inputs_dir": str(root / "inputs"),
        "stage1_run_dir": str(stage1.run_dir),
    }
    record = promotion_record(
        "synthetic-discover", load_claim(claim).sha256(), 50, entries, None, provenance
    )
    return claim, cache, record


def _write(tmp_path: Path, record: dict) -> Path:
    path = tmp_path / "promotion.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def test_stage_2_runs_a_promoted_star_and_records_the_record_hash(promoted, tmp_path):
    claim, cache, record = promoted
    assert record["schema"] == PROMOTION_SCHEMA and record["promoted"] == ["TIC-2"]
    path = _write(tmp_path, record)
    outcome = _run(claim, cache, tmp_path / "out", stage=2, run_id="s2", promotion=path)
    assert outcome.exit_code == 0, outcome.messages
    assert outcome.summary["promotion_sha256"] is not None
    reproduce = (outcome.run_dir / "TIC-2" / "REPRODUCE.md").read_text(encoding="utf-8")
    assert "--stage 2" in reproduce and "--promotion" in reproduce


def _entry_not_eligible(record):
    entries = [dict(e, eligible=False, reason="gate") for e in record["entries"]]
    return {"entries": entries, "eligible": []}


@pytest.mark.parametrize(
    ("change", "match"),
    [
        (lambda r: {"claim_id": "other"}, "another claim"),
        (lambda r: {"promoted": []}, "not the protocol's draw"),
        (_entry_not_eligible, "recomputed from the stage-1 dossiers"),
        (lambda r: {"entries": []}, "run set"),
        (lambda r: {"claim_sha256": "0" * 64}, "locked claim"),
        (lambda r: {"n_chosen": 7}, "n_chosen"),
        (lambda r: {"n_chosen": 100}, "committed (N, K) decision"),
        (lambda r: {"provenance": {}}, "provenance lacks"),
        (
            lambda r: {"provenance": {**r["provenance"], "results_commit": "0" * 40}},
            "not an ancestor",
        ),
        (
            lambda r: {"entries": [dict(e, verdict_sha256="a" * 64) for e in r["entries"]]},
            "recomputed",
        ),
    ],
)
def test_a_record_the_protocol_would_not_produce_is_refused(promoted, tmp_path, change, match):
    claim, cache, record = promoted
    path = _write(tmp_path, {**record, **change(record)})
    refused = _run(claim, cache, tmp_path / "out", stage=2, run_id="bad", promotion=path)
    assert refused.exit_code == 1
    assert any(match in m for m in refused.messages), refused.messages


def _refused(claim, cache, tmp_path, record, match):
    refused = _run(
        claim, cache, tmp_path / "out", stage=2, run_id="bad", promotion=_write(tmp_path, record)
    )
    assert refused.exit_code == 1
    assert any(match in m for m in refused.messages), refused.messages


@pytest.mark.parametrize(
    ("field", "value"),
    [("claim_sha256", "0" * 64), ("code_sha256", "0" * 64), ("claim_id", "other-claim")],
)
def test_a_stage_1_dossier_of_another_claim_or_code_is_never_used(promoted, tmp_path, field, value):
    claim, cache, record = promoted
    path = Path(record["provenance"]["stage1_run_dir"]) / "TIC-2" / "verdict.json"
    verdict = json.loads(path.read_text(encoding="utf-8"))
    verdict["provenance"][field] = value
    path.write_text(json.dumps(verdict), encoding="utf-8")
    _refused(claim, cache, tmp_path, record, "recomputed from the stage-1 dossiers")


def test_a_stage_1_dossier_of_another_star_is_never_used(promoted, tmp_path):
    claim, cache, record = promoted
    path = Path(record["provenance"]["stage1_run_dir"]) / "TIC-2" / "verdict.json"
    verdict = json.loads(path.read_text(encoding="utf-8"))
    verdict["tic_id"] = 9
    path.write_text(json.dumps(verdict), encoding="utf-8")
    _refused(claim, cache, tmp_path, record, "recomputed from the stage-1 dossiers")


def test_a_decision_changed_after_its_commit_is_refused(promoted, tmp_path):
    claim, cache, record = promoted
    root = claim.parent.parent
    decision = json.loads((root / "n_k.json").read_text(encoding="utf-8"))
    decision["chosen"] = {"N": 100, "K": 20}
    (root / "n_k.json").write_text(json.dumps(decision), "utf-8")
    git(root, "commit", "-q", "-am", "a later decision")
    _refused(claim, cache, tmp_path, record, "changed after its commit")


def test_a_decision_committed_after_the_stage_1_runs_is_refused(promoted, tmp_path):
    claim, cache, record = promoted
    later = record["provenance"]["results_commit"]  # after the stage-1 run
    provenance = {**record["provenance"], "n_k_commit": later}
    _refused(claim, cache, tmp_path, {**record, "provenance": provenance}, "before every stage-1")


def test_a_decision_its_costs_do_not_give_is_refused(git_repo):
    from refute.packs.tess.discover import funnel, steps

    decision = funnel.choose_n_k(funnel.ControlCosts(0.1, 0.15, 0.04, 0.05, 10e6), 2.0, 1e9)
    decision["chosen"] = {"N": 100, "K": 20}
    (git_repo / "n_k.json").write_text(json.dumps(decision), "utf-8")
    git(git_repo, "add", "-A")
    git(git_repo, "commit", "-q", "-m", "decision")
    commit = git(git_repo, "rev-parse", "HEAD").strip()
    provenance = {"n_k_commit": commit, "n_k_path": "n_k.json"}
    _, problems = steps.n_k_problems(git_repo, provenance, [commit])
    assert any("recorded costs" in p for p in problems)


def test_a_draw_offline_uses_the_recorded_push_run_and_makes_no_query(promoted, monkeypatch):
    from refute.packs.tess.discover import runs, steps

    claim, cache, record = promoted
    targets, identity = _binding(claim)
    eligible = {"eligible": True, "reason": "eligible"}
    many = [{"target_key": k, "verdict_sha256": "b" * 64, "eligibility": eligible} for k in "ABCD"]
    monkeypatch.setattr(runs, "stage1_entries", lambda *a, **k: many)

    def no_network(_commit):
        raise AssertionError("an offline check made a network query")

    from refute.core.claim import load_claim

    root = claim.parent.parent
    inputs_sha = load_claim(claim).claim.test_plan["discovery"]["inputs"]["inputs_json"]
    args = (root, identity, ["TIC-2"], targets, inputs_sha)
    problems = steps.promotion_problems(record, *args, offline=True, push_run=no_network)
    assert any("push run time" in p for p in problems)
    recorded = {**record["provenance"], "push_run_created_at": "2026-11-20T10:00:00Z"}
    problems = steps.promotion_problems(
        {**record, "provenance": recorded}, *args, offline=True, push_run=no_network
    )
    assert not any("push run" in p for p in problems)


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ([], "--stage 1 or 2"),
        (["--stage", "2"], "--promotion"),
    ],
)
def test_fetch_of_a_discover_claim_follows_the_stage_rules(discover, args, message):
    from typer.testing import CliRunner

    from refute.cli import app

    claim, cache = discover
    result = CliRunner().invoke(app, ["fetch", str(claim), "--cache-dir", str(cache), *args])
    assert result.exit_code == 1
    assert message in result.output


@pytest.mark.parametrize("stage", [None, 0, 3])
def test_discover_needs_stage_1_or_2(discover, tmp_path, stage):
    claim, cache = discover
    refused = _run(claim, cache, tmp_path / "out", stage=stage, run_id="x")
    assert refused.exit_code == 1


def test_stage1_entries_record_every_star_with_its_verdict_hash(discover, tmp_path):
    from refute.core.ledger import make_event
    from refute.packs.tess.discover import dedup, runs
    from refute.packs.tess.discover.case import check_event

    claim, cache = discover
    outcome = _run(claim, cache, tmp_path / "out", stage=1, run_id="s1e")
    indexes = {name: dedup.CatalogIndex([]) for name in dedup.DEDUP.catalogs}
    entries = runs.stage1_entries(outcome.run_dir, ["TIC-2", "TIC-404"], indexes, *_binding(claim))
    assert [e["target_key"] for e in entries] == ["TIC-2", "TIC-404"]
    assert len(entries[0]["verdict_sha256"]) == 64
    assert entries[1]["eligibility"] == {"eligible": False, "reason": "no stage-1 dossier"}
    event = make_event(None, "TIC-2", "ran", "2026-10-29T00:00:00Z", entries[0]["ledger"])
    assert check_event(event) == []
