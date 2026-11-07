"""v0.5.1 WP5, row 5.4: the packaging rehearsal (docs/plans/v0.5.1-acceptance.md).

A version-3 calibration claim written by the code to be frozen (``calib051.claim.write_claim``)
for synthetic targets, committed, locked (``create_lock``) and verified (``verify_claim``) in a
temporary git repository, loaded, and each calibration step that the plan fixes run once on
synthetic data, offline: ``refute discover`` (the CLI path) on the locked claim at stage 2; C1'
(one planet curve, one non-planet curve); C2' (one new star: the original, one transformed curve,
one injection); C3' (one planet and one false positive, with and without the catalog test, the
replacement and the targets); the WP4 tallies. A smoke test: one minimal path per step, no
calibration-sized run, nothing measured.

Rehearsal scaffolding, marked as such: the protocol file is a placeholder, the catalog inputs are
synthetic (their own content SHA-256 and row count are passed to ``eb_attachments``), the targets'
data come from ``synthetic.write_synthetic_cache`` (SPOC-like FITS light curves and pixel files,
read by the production adapter from the cache path its manifest names), and the round's
randomness is a fixed string. The selection walks, the drand draws and the protocol's steps are
added after the calibration protocol is approved, and this rehearsal runs again before the freeze.

Across platforms only the candidate, the verdict and the test statuses would be compared (#212);
this test compares no number with a recorded value.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from conftest import git, target_entry
from refute.core.claim import load_claim
from refute.core.dossier import check_dossier
from refute.core.inconclusive import tally
from refute.core.io import read_json
from refute.core.lock import VerifyStatus, create_lock, verify_claim
from refute.core.run import execute_run
from refute.packs.tess.calib05 import c3run, runner
from refute.packs.tess.calib051 import claim as claim51
from refute.packs.tess.calib051 import tasks as t51
from refute.packs.tess.calib051.values import C1, C2, PROTOCOL_ID, STEP_DIR
from refute.packs.tess.ebcatalog import content_sha256
from refute.packs.tess.synthetic import discovery_plan_dict, scenario_data, write_synthetic_cache

# rehearsal scaffolding: synthetic catalog inputs (the frozen editions are the protocol's)
TESS_EB = (
    b"TIC\tm_TIC\tRAJ2000\tDEJ2000\tPer\n\t\tdeg\tdeg\td\n--\t--\t--\t--\t--\n"
    b"3\t\t40.0\t10.0\t2.9\n"
)
# two rows: numpy.genfromtxt gives a zero-dimensional array for one row
GAIA = b"source_id,ra,dec,frequency\n904,50.0,10.0,0.2\n905,60.0,10.0,0.3\n"
RANDOMNESS = "ab" * 32  # rehearsal scaffolding: the round's randomness comes from the protocol
PLANET, FP, NEW_STAR = 1, 3, 2


def _target(tic: int, kind: str, period: float, place: str) -> dict:
    entry = target_entry(tic, kind, period)
    entry["mast"] = {"tic_ra": 40.0 if tic == FP else 150.0, "tic_dec": 10.0}
    entry["c3_place"] = place
    return entry


@pytest.fixture(scope="module")
def rehearsal(tmp_path_factory):
    """The claim written, committed, locked, committed again and verified; the synthetic cache."""
    from refute.packs.tess.discover import pilot

    repo = tmp_path_factory.mktemp("rehearsal") / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    step = repo / STEP_DIR
    inputs_dir = step / "inputs"
    inputs_dir.mkdir(parents=True)
    records = []
    for name, data in (("tess_eb.tsv", TESS_EB), ("gaia_dr3_eb.csv", GAIA)):
        (inputs_dir / name).write_bytes(data)
        records.append(pilot.record(name, f"synthetic:{name}", data, "2026-11-07T00:00:00Z"))
    (step / claim51.INPUTS_NAME).write_text(
        json.dumps({"files": records, "s_max": 99}, indent=2) + "\n", encoding="utf-8"
    )
    (step / claim51.PROTOCOL_NAME).write_text(
        f"# {PROTOCOL_ID}: REHEARSAL placeholder, not the calibration protocol\n",
        encoding="utf-8",
    )
    targets_doc = {
        "schema": "refute-tess-targets-1",
        "generated_utc": "2026-11-07T00:00:00Z",
        "generator": "tests/test_v051_rehearsal.py (rehearsal scaffolding)",
        "selection": {"note": "synthetic"},
        "targets": [
            _target(PLANET, "planet", 3.7, "chosen"),
            _target(FP, "false_positive", 2.9, "chosen"),
        ],
    }
    written = claim51.write_claim(
        step,
        targets_doc,
        inputs_dir,
        discovery_plan_dict(catalogs=True),
        "2026-11-07",
        claim_id="tess-calibration-v0.5.1-rehearsal",
        title="Refute v0.5.1 calibration: packaging rehearsal (synthetic)",
        hypothesis="The version-3 claim is written, loaded, locked and run end to end.",
        eb_options={"tess_eb_content_sha256": content_sha256(TESS_EB), "gaia_rows": 2},
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "claim")
    claim_path = step / claim51.CLAIM_NAME
    create_lock(claim_path)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "lock")
    cache = tmp_path_factory.mktemp("cache")
    for tic, scenario in ((PLANET, "planet"), (NEW_STAR, "planet"), (FP, "eb_secondary")):
        data = scenario_data(scenario)
        write_synthetic_cache(cache, tic, data.lc, data.star, aux=data.aux)
    from refute.packs.tess.ebcatalog import external_snapshots

    for snap in external_snapshots(written["scan"]):
        dest = cache / snap["cache_path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(TESS_EB)
    return {
        "repo": repo,
        "step": step,
        "claim": claim_path,
        "cache": cache,
        "document": written["claim"],
        "scan": written["scan"],
    }


def test_the_claim_is_written_locked_and_verified(rehearsal):
    verified = verify_claim(rehearsal["claim"])
    assert verified.status is VerifyStatus.PASS, verified.messages
    loaded = load_claim(rehearsal["claim"])
    plan = loaded.claim.test_plan
    # the v051 section is written resolved, with its defaults (as `stronger` in v0.5)
    assert plan["discovery"]["version"] == 3 and isinstance(plan["v051"], dict) and plan["v051"]
    assert set(plan["discovery"]["inputs"]) == {
        "protocol",
        "inputs_json",
        "selection_targets",
        "targets",
    }
    # the claim's targets file is the projection; the selection's document keeps its places
    claim_targets = (rehearsal["step"] / claim51.TARGETS_NAME).read_text(encoding="utf-8")
    assert "c3_place" not in claim_targets
    selection = (rehearsal["step"] / claim51.SELECTION_TARGETS_NAME).read_text(encoding="utf-8")
    assert selection.count("c3_place") == 2
    assert plan["discovery"]["max_sector"] == 99
    roles = {a.role for a in loaded.claim.attachments}
    assert {
        "targets",
        "selection-targets",
        "protocol",
        "snapshot-index",
        "eb-catalog",
        "eb-catalog-scan",
    } <= roles
    # the catalog data the claim carries: rows near the targets and the external TESS-EB snapshot
    catalog = (rehearsal["step"] / claim51.EB_CATALOG).read_text(encoding="utf-8")
    assert "TESS-EB" in catalog
    assert any(s["catalog_name"] == "TESS-EB" for s in rehearsal["scan"]["snapshots"])
    assert len(loaded.pack.schema.targets_for_run(loaded)) == 2


def test_the_cli_runs_the_locked_claim_offline(rehearsal, tmp_path):
    outcome = execute_run(
        rehearsal["claim"],
        mode="discover",
        targets=[f"TIC-{PLANET}"],
        out_dir=tmp_path / "out",
        workers=1,
        offline=True,
        cache_dir=rehearsal["cache"],
        stage=2,
        run_id="rehearsal",
    )
    assert outcome.exit_code == 0, outcome.messages
    dossier = outcome.run_dir / f"TIC-{PLANET}"
    verdict = read_json(dossier / "verdict.json")
    assert verdict["v05"]["discovery_version"] == 3
    assert "v051" in verdict and verdict["method_status"] == "not_validated"
    assert verdict["discovery"]["stage"] == 2
    assert check_dossier(dossier).ok


def _v04_plan(rehearsal) -> dict:
    """The v0.4 compatibility plan the claim was written from, with the claim's inputs and
    ``max_sector`` (as ``calib05.c3run.v04_plan_for``)."""
    claimed = yaml.safe_load(rehearsal["claim"].read_text(encoding="utf-8"))["test_plan"]
    plan = discovery_plan_dict(catalogs=True)
    plan["discovery"]["inputs"] = dict(claimed["discovery"]["inputs"])
    plan["discovery"]["max_sector"] = claimed["discovery"]["max_sector"]
    return plan


def test_c1_prime_one_path(rehearsal, tmp_path):
    assert sum(C1.sizes.values()) == 2400
    tasks = [
        t51.C1Task(f, 0, t51.development_seed(f, 0), _v04_plan(rehearsal)) for f in ("P", "SE")
    ]
    prov = runner.provenance(Path.cwd(), step="rehearsal-c1")
    records = runner.run_tasks(t51.run_c1, tasks, t51.c1_task_id, tmp_path / "c1", None, prov)
    assert [r["status"] for r in records] == ["OK", "OK"], [r.get("reason") for r in records]
    assert runner.read_manifest(tmp_path / "c1")["function"].endswith("tasks.run_c1")
    second = [r["chain"]["v05"] for r in records]
    assert all("v051" in b for b in second)
    counts = tally(second)
    assert sum(counts["verdicts"].values()) == 2


def test_c2_prime_one_star(rehearsal, tmp_path):
    assert (C2.stars, C2.transformed_per_star, C2.injections_per_curve) == (50, 3, 10)
    step = rehearsal["step"]
    target = {"key": f"TIC-{NEW_STAR}", "tic_id": NEW_STAR, "kind": "exploration"}
    tasks = t51.c2_tasks_for(
        target,
        _v04_plan(rehearsal),
        rehearsal["cache"],
        RANDOMNESS,
        ((step / claim51.EB_CATALOG).as_posix(),),
        (step / claim51.EB_SCAN).as_posix(),
        k=1,
        transformed=1,
    )
    assert [t.kind for t in tasks] == ["original", "transform", "injection"]
    # the default worker count, as the calibration's runs (the tasks run in parallel processes)
    records = runner.run_tasks(t51.run_c2, tasks, t51.c2_task_id, tmp_path / "c2", None, {})
    assert all(r["status"] in ("OK", "INCONCLUSIVE") for r in records), records
    ok = [r for r in records if r["status"] == "OK"]
    assert ok and all("v051" in r["chain"]["v05"] for r in ok)
    assert "recovery" in next(r for r in records if r["kind"] == "injection")


def test_c3_prime_one_control_per_pool(rehearsal, tmp_path):
    step = rehearsal["step"]
    targets = yaml.safe_load((step / claim51.SELECTION_TARGETS_NAME).read_text("utf-8"))["targets"]
    tasks = [
        t51.C3Task(
            t,
            _v04_plan(rehearsal),
            str(rehearsal["cache"]),
            {"state": "present"},
            ((step / claim51.EB_CATALOG).as_posix(),),
            (step / claim51.EB_SCAN).as_posix(),
        )
        for t in targets
    ]
    records = runner.run_tasks(t51.run_c3, tasks, t51.c3_task_id, tmp_path / "c3", None, {})
    assert [r["status"] for r in records] == ["OK", "OK"], [r.get("reason") for r in records]
    by_key = {r["target_key"]: r for r in records}
    for r in records:
        assert "v051" in r["with_catalog"]["v05"] and "v051" in r["without_catalog"]["v05"]
    assigned = c3run.assign(targets, by_key)
    result = c3run.targets(assigned, by_key)
    # one control per pool: the targets need 8, so neither is decidable in a rehearsal
    assert result["T3a"]["result"] == result["T3b"]["result"] == "NOT DECIDABLE"
    missing = t51.run_c3(t51.C3Task(targets[0], {}, "", {"state": "missing", "reason": "x"}))
    assert missing["status"] == t51.MISSING
