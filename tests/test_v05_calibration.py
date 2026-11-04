"""The v0.5 calibration code (refute.packs.tess.calib05; calibration/v0.5/PROTOCOL.md): values,
plans, the C1 generator and metrics, the C3 selection, replacement and targets, the C2
compatibility and summary, and the task runner. Offline, on synthetic inputs."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest
import yaml

from refute.packs.tess.calib05 import c1, c2, c3run, c3select, runner
from refute.packs.tess.calib05.plans import pair, v05_plan
from refute.packs.tess.calib05.values import C1, C3, V05_DECISIVE, V05_DIAGNOSTIC

ROOT = Path(__file__).resolve().parents[1]


def _v04_plan() -> dict:
    claim = yaml.safe_load((ROOT / "calibration/v0.4/claim.yaml").read_text(encoding="utf-8"))
    return claim["test_plan"]


# --- values and plans ---------------------------------------------------------------------


def test_values_and_roles():
    assert sum(C1.sizes.values()) == 2400
    assert not set(V05_DECISIVE) & set(V05_DIAGNOSTIC)
    assert "centroid_shift" in V05_DIAGNOSTIC and "centroid_shift" not in V05_DECISIVE
    assert {"single_event", "event_consistency"} <= set(V05_DIAGNOSTIC)
    assert C3.planets == C3.false_positives == 8 and C3.reserves == 3


def test_the_protocol_states_the_code_values():
    """calibration/v0.5/PROTOCOL.md, section 11, equals calib05/values.py."""
    from dataclasses import asdict

    from refute.packs.tess.calib05.values import BUDGET, C2

    text = (ROOT / "calibration/v0.5/PROTOCOL.md").read_text(encoding="utf-8")
    block = text.split("## 11.")[1].split("```yaml")[1].split("```")[0]
    stated = yaml.safe_load(block)
    code = {
        "c3": {**asdict(C3), "fp_identity_factors": list(C3.fp_identity_factors)},
        "c1": asdict(C1),
        "c2": asdict(C2),
        "budget": asdict(BUDGET),
        "roles": {"decisive": list(V05_DECISIVE), "diagnostic": list(V05_DIAGNOSTIC)},
    }
    assert stated == code


def test_the_v05_plan_pairs_with_the_v04_claim():
    p04, p05 = pair(_v04_plan())
    assert not p04.v05 and p05.v05
    assert p05.discovery.roles["centroid_shift"] == "diagnostic"
    assert p04.discovery.roles["centroid_shift"] == "decisive"
    assert p05.detrend == p04.detrend and p05.search == p04.search
    with pytest.raises(ValueError, match="discovery version 1"):
        v05_plan(v05_plan(_v04_plan()))


# --- C1 -----------------------------------------------------------------------------------


def test_c1_seeds():
    assert c1.development_seed("P", 0) == int(
        hashlib.sha256(b"refute-v05-c1-dev:P:0").hexdigest()[:16], 16
    )
    r = "ab" * 32
    assert c1.confirmation_seed(r, "PX", 7) == int(
        hashlib.sha256((r + "refute-v05-c1:PX:7").encode()).hexdigest()[:16], 16
    )


@pytest.mark.parametrize("family", c1.FAMILIES)
def test_c1_every_family_generates_deterministically(family):
    seed = c1.development_seed(family, 1)
    try:
        data, truth = c1.generate(family, seed)
    except c1.GenerationFailedError:
        pytest.skip("a recorded generation failure for this seed")
    again, truth2 = c1.generate(family, seed)
    assert np.array_equal(data.lc.flux, again.lc.flux) and truth == truth2
    assert truth["family"] == family
    n_sectors = len(data.lc.sectors)
    assert n_sectors == 3 if family == "PA" else 2 <= n_sectors <= 4
    assert data.aux is not None and len(data.aux.pixels) == n_sectors
    if family == "NW":
        assert not truth["correlated"] and truth["trend"] is None
    if family == "NR":
        assert truth["correlated"] and truth["trend"] is None


def test_c1_the_depth_meets_its_target_snr():
    data, truth = c1.generate("P", c1.development_seed("P", 3))
    sigma_r = truth["sigma_white_ppm"] * 1e-6 / 2 if truth["correlated"] else 0.0
    var = c1.window_variances(
        data.lc.time,
        truth["period_days"],
        truth["t0_btjd"],
        truth["duration_days"],
        truth["sigma_white_ppm"] * 1e-6,
        sigma_r,
    )
    assert truth["depth"] / c1.sigma_total(var) == pytest.approx(truth["target_snr"], rel=1e-5)
    k = math.sqrt(truth["depth"])
    total, _ = c1.durations(truth["period_days"], k, truth["impact"])
    assert total == pytest.approx(truth["duration_days"])


def test_c1_generation_failures():
    with pytest.raises(c1.GenerationFailedError, match="no transit"):
        c1.durations(3.0, 0.0, 1.0)
    with pytest.raises(c1.GenerationFailedError, match="no transit window"):
        c1.sigma_total([])


def test_c1_eb2_and_px_truth():
    _, eb2 = c1.generate("EB2", c1.development_seed("EB2", 0))
    assert eb2["true_period_days"] == pytest.approx(2 * eb2["period_days"])
    try:
        _, px = c1.generate("PX", c1.development_seed("PX", 0))
    except c1.GenerationFailedError:
        pytest.skip("generation failure")
    c = px["crowdsap"]
    assert px["neighbor_depth"] == pytest.approx(px["depth"] * c / (1 - c))
    assert 1.5 <= px["separation_px"] <= 3.0


def test_c1_identity():
    truth = {"period_days": 3.0, "t0_btjd": 100.0, "duration_days": 0.1}
    assert c1.identity(truth, {"period_days": 3.01, "t0_btjd": 103.04})
    assert not c1.identity(truth, {"period_days": 3.1, "t0_btjd": 100.0})
    assert not c1.identity(truth, {"period_days": 3.0, "t0_btjd": 100.2})
    assert not c1.identity(truth, None)


def _chain(v04: str, v05: str, gate: bool = True) -> dict:
    return {"v04": {"verdict": v04, "gate_passed": gate}, "v05": {"verdict": v05}}


def test_c1_metrics_and_rules():
    records = []
    for f in c1.FAMILIES:
        for _i in range(40):
            r = {"family": f, "status": "OK", "truth": {"target_snr": 20.0}}
            r["chain"] = _chain("SURVIVED", "REFUTED" if f == "PX" else "WEAKENED")
            r["identity"] = True
            records.append(r)
    records.append({"family": "P", "status": "GENERATION_FAILURE"})
    out = c1.metrics(records)
    assert out["families"]["P"]["outside"] == {"generation_failure": 1}
    assert out["families"]["P"]["eligible"] == 40
    rules = out["decision_rules"]
    assert rules["D1"]["NW"]["result"] == "PASS"  # 0 SURVIVED in v0.5
    assert rules["D5"]["result"] == "PASS"
    assert rules["D4"]["result"] == "PASS"
    few = [r for r in records if r["family"] != "SE" or r is records[0]]
    assert c1.metrics(few)["decision_rules"]["D1"]["SE"]["result"] == "NOT DECIDABLE"


# --- C3 selection -------------------------------------------------------------------------


def _inputs(tmp_path: Path) -> tuple[Path, dict]:
    toi = [
        "TIC ID,TOI,TFOPWG Disposition,Period (days),Period (days) err,Depth (ppm),"
        "Epoch (BJD),Duration (hours)"
    ]
    ps = [
        "pl_name,tic_id,tran_flag,sy_pnum,pl_orbper,pl_orbpererr1,pl_trandep,pl_tranmid,pl_trandur"
    ]
    eb = ["TIC\tm_TIC\tPer", "\t\td", "--\t--\t--"]
    for i in range(60):
        tic = 900000 + i
        toi.append(f"{tic},{5000 + i}.01,FP,{1.0 + i * 0.19},0.001,{2000 + i},2459000.5,2.0")
        if i % 2 == 0:
            eb.append(f"{tic}\t\t{1.0 + i * 0.19}")
        ps.append(f"P{i} b,TIC {800000 + i},1,1,{1.0 + i * 0.19},0.0001,0.5,2459000.1,2.5")
    files = {
        "toi.csv": "\n".join(toi) + "\n",
        "pscomppars.csv": "\n".join(ps) + "\n",
        "tess_eb.tsv": "\n".join(eb) + "\n",
    }
    records = []
    for name, text in files.items():
        data = text.encode()
        (tmp_path / name).write_bytes(data)
        records.append(
            {"name": name, "sha256": hashlib.sha256(data).hexdigest(), "retrieved_utc": "t"}
        )
    return tmp_path, {"files": records, "s_max": 90}


def test_c3_pools_and_order(tmp_path):
    inputs_dir, inputs = _inputs(tmp_path)
    built, _ = c3select.read_pools(ROOT, inputs_dir, inputs)
    assert len(built["planet"]) == 60
    assert len(built["false_positive"]) == 30  # only the TICs in TESS-EB
    assert all(p.tic_id % 2 == 0 for p in built["false_positive"])
    r = "cd" * 32
    a = c3select.pool_order(built["planet"], r, "planet-pool")
    assert a == c3select.pool_order(built["planet"], r, "planet-pool")
    assert a != c3select.pool_order(built["planet"], r, "eb-fp-pool")
    assert sorted(a) == sorted(p.tic_id for p in built["planet"])


def test_c3_known_targets_include_v04():
    known = c3select.known_targets(ROOT)
    doc = yaml.safe_load(
        (ROOT / "calibration/v0.4/selection/targets.yaml").read_text(encoding="utf-8")
    )
    assert all(int(t["tic_id"]) in known for t in doc["targets"])


def test_c3_selection_walk_ledger_and_targets(tmp_path):
    inputs_dir, inputs = _inputs(tmp_path)

    def triage(tic, domain, s_max):
        ok = tic % 3 != 0
        return ok, "accepted" if ok else "D-7: Tmag", {"tic": tic, "s_max": s_max}

    out = c3select.run_selection(inputs_dir, inputs, "ef" * 32, ROOT, triage, lambda s: None)
    for kind in ("planet", "false_positive"):
        pool = out["pools"][kind]
        assert len(pool["chosen"]) == 8 and len(pool["reserves"]) == 3
        assert all(t % 3 != 0 for t in pool["chosen"] + pool["reserves"])
    assert out["complete"]
    ledger = c3select.ledger(out)
    assert {r["place"] for r in ledger} >= {"chosen", "reserve 1", "reserve 3", None}
    assert all(r["reason"].startswith("D-7") for r in ledger if r["decision"] == "rejected")
    doc = c3select.targets_document({**out, "round": 1, "protocol_commit": "x"}, inputs)
    places = [t["c3_place"] for t in doc["targets"]]
    assert places.count("chosen") == 16 and places.count("reserve 1") == 2
    fp = [t for t in doc["targets"] if t["kind"] == "false_positive"]
    assert all(t["fp_class"].startswith("eclipsing_binary") for t in fp)
    assert all(t["published"]["period_days"] for t in doc["targets"])


# --- C3 run: identity, replacement, targets -------------------------------------------------


def test_c3_identity():
    assert c3run.identity("planet", 3.0, 3.002)["matched"]
    assert not c3run.identity("planet", 3.0, 6.0)["matched"]
    assert c3run.identity("false_positive", 3.0, 6.0)["factor"] == 2.0


def _target(kind, n, place):
    return {"key": f"{kind}-{n}", "kind": kind, "c3_place": place}


def _ok(matched=True, v05="SURVIVED"):
    chain = {"v04": {"verdict": "SURVIVED"}, "v05": {"verdict": v05}}
    return {
        "status": "OK",
        "identity": {"matched": matched},
        "without_catalog": chain,
        "with_catalog": chain,
    }


def test_c3_replacement_reads_identity_and_products_only():
    targets = [_target("planet", i, "chosen") for i in range(8)]
    targets += [_target("planet", 10 + i, f"reserve {i + 1}") for i in range(3)]
    targets += [_target("false_positive", i, "chosen") for i in range(8)]
    records = {t["key"]: _ok(v05="REFUTED") for t in targets}
    records["planet-2"] = _ok(matched=False)
    records["planet-10"] = {"status": "MISSING_PRODUCTS"}
    records["planet-5"] = {"status": "ERROR", "reason": "x"}  # an error is not replaced
    out = c3run.assign(targets, records)
    planet = out["planet"]
    assert planet["final"][2] == "planet-11" and planet["replacements"] == 2
    assert "planet-5" in planet["final"]
    assert [e["reason"] for e in planet["ledger"]] == [
        "signal identity not matched",
        "products missing",
    ]
    t = c3run.targets(out, records)
    assert t["T3a"]["result"] == "NOT DECIDABLE"  # 7 valid of 8: the error counts
    assert t["T3b"]["result"] == "PASS" and t["T3b"]["observed"] == 0


def test_c3_reserves_run_out():
    targets = [_target("planet", i, "chosen") for i in range(8)]
    targets += [_target("planet", 10 + i, f"reserve {i + 1}") for i in range(3)]
    targets += [_target("false_positive", i, "chosen") for i in range(8)]
    records = {t["key"]: _ok() for t in targets}
    for i in range(4):
        records[f"planet-{i}"] = _ok(matched=False)
    out = c3run.assign(targets, records)
    assert out["planet"]["replacements"] == 3 and out["planet"]["short"] == 1
    assert c3run.targets(out, records)["T3a"]["result"] == "NOT DECIDABLE"


# --- C2 -------------------------------------------------------------------------------


def test_c2_input_problems():
    old = {"files": [{"name": "a", "sha256": "1"}, {"name": "b", "sha256": "2"}]}
    assert c2.input_problems(old, old) == []
    new = {"files": [{"name": "a", "sha256": "1"}, {"name": "b", "sha256": "3"}]}
    assert c2.input_problems(new, old) == ["other bytes: b"]
    assert c2.input_problems({"files": []}, old) == ["missing now: a", "missing now: b"]


def test_c2_compatibility():
    verdict = {
        "candidate": {"period": 2.0, "t0": 100.0, "snr": 9.0},
        "tests": [
            {"name": "snr", "status": "PASS", "severity": "gate"},
            {"name": "holdout_by_year", "status": "INCONCLUSIVE", "severity": "warning"},
        ],
        "verdict": "INCONCLUSIVE",
    }
    ref = c2.dossier_reference(verdict)
    assert "holdout_by_year" not in ref["tests"]
    v04 = {
        "candidate": {"period_days": 2.0 * (1 + 1e-12), "t0_btjd": 100.0, "snr": 9.0},
        "tests": {"snr": {"status": "PASS", "severity": "gate"}},
        "verdict": "INCONCLUSIVE",
    }
    rec = {"kind": "original", "status": "OK", "chain": {"v04": v04}}
    assert c2.compat_problems(rec, ref) == []
    v04["candidate"]["period_days"] = 2.1
    assert c2.compat_problems(rec, ref)
    assert c2.compat_problems({"status": "ERROR", "reason": "x"}, ref)


def _c2_record(kind, key, slot, gate, v04, v05):
    chain = {
        b: {"gate_passed": gate, "stage_verdict": v, "verdict": "INCONCLUSIVE"}
        for b, v in (("v04", v04), ("v05", v05))
    }
    rec = {"kind": kind, "target_key": key, "slot": slot, "status": "OK", "chain": chain}
    if kind == "injection":
        rec["recovery"] = {"recovered": True, "alias": None, "gate_passed": gate}
    return rec


def test_c2_summary_and_targets():
    records = []
    for s in range(30):
        key = f"TIC-{s}"
        records.append(_c2_record("original", key, 0, s < 3, "SURVIVED", "WEAKENED"))
        for p in range(3):
            records.append(_c2_record("transform", key, p, True, "WEAKENED", "REFUTED"))
        records.append(_c2_record("injection", key, 0, True, "SURVIVED", "SURVIVED"))
    compat = {f"{r['target_key']}/{r['kind']}/{r['slot']}": [] for r in records}
    out = c2.summarize(records, {}, {"TIC-0"}, compat)
    assert out["compatibility"]["state"] == "established"
    t = out["targets"]
    assert t["T2a"]["result"] == "PASS" and t["T2a"]["denominator"] == 27
    assert t["T2b-inverted"]["result"] == "PASS" and t["T2b-rotated"]["denominator"] == 60
    assert t["T2c"]["v05_survived"] == 0 and t["T2c"]["result"] == "PASS"
    compat["TIC-1/original/0"] = ["candidate.snr: 1 != 2"]
    blocked = c2.summarize(records, {}, {"TIC-0"}, compat)
    assert blocked["compatibility"]["state"] == "blocked"
    assert "not evaluated" in blocked["targets"]["state"]


# --- the runner -------------------------------------------------------------------------


def _double(x: int) -> dict:
    return {"value": 2 * x, "cpu_seconds": 0.0, "status": "OK"}


URL = "https://github.com/klucilla/refute/issues/199#issuecomment-1"


def test_runner_runs_once_with_its_manifest(tmp_path):
    out = tmp_path / "run"
    prov = {"code_sha256": "c", "step": "s"}
    records = runner.run_tasks(_double, [1, 2, 3], str, out, workers=1, prov=prov)
    assert [r["value"] for r in records] == [2, 4, 6]
    manifest = runner.read_manifest(out)
    assert manifest["tasks"] == ["1", "2", "3"] and manifest["provenance"] == prov
    assert manifest["function"].endswith("_double")
    assert manifest["tasks_sha256"] == runner.tasks_sha256([1, 2, 3])
    assert not (out / "running.marker").exists()
    with pytest.raises(FileExistsError):
        runner.run_tasks(_double, [1], str, out, workers=1)
    assert len(runner.all_records(out)) == 3
    with pytest.raises(ValueError, match="ended normally"):
        runner.resume(_double, [1, 2, 3], str, out, URL, workers=1, prov=prov)


def _interrupted(tmp_path: Path, keep: int = 2) -> tuple[Path, dict]:
    """A run whose process ended after ``keep`` of its three records (the marker left behind,
    the later records missing, the last kept record's cost line missing)."""
    out = tmp_path / "run"
    prov = {"code_sha256": "c", "step": "s"}
    runner.run_tasks(_double, [1, 2, 3], str, out, workers=1, prov=prov)
    lines = (out / "records.jsonl").read_text().splitlines()
    (out / "records.jsonl").write_text("\n".join(lines[:keep]) + "\n")
    cost = (out / "cost.jsonl").read_text().splitlines()
    (out / "cost.jsonl").write_text("\n".join(cost[: keep - 1]) + "\n")
    (out / "running.marker").write_text(json.dumps({"pid": 1, "utc": "t"}))
    return out, prov


def test_runner_resumes_only_the_same_experiment(tmp_path):
    out, prov = _interrupted(tmp_path)
    with pytest.raises(ValueError, match="running or interrupted"):
        runner.all_records(out)
    with pytest.raises(ValueError, match="approval"):
        runner.resume(_double, [1, 2, 3], str, out, "not a url", workers=1, prov=prov)
    with pytest.raises(ValueError, match="tasks"):
        runner.resume(_double, [1, 2, 3, 4], str, out, URL, workers=1, prov=prov)
    with pytest.raises(ValueError, match="provenance"):
        runner.resume(_double, [1, 2, 3], str, out, URL, workers=1, prov={"code_sha256": "x"})
    done = runner.resume(_double, [1, 2, 3], str, out, URL, workers=1, prov=prov)
    assert [r["task"] for r in done] == ["3"]
    assert len(runner.all_records(out)) == 3  # the lost cost line restored
    log = json.loads((out / "resumptions.jsonl").read_text())
    assert log["tasks"] == 1 and log["costs_restored"] == 1


def test_runner_finalizes_a_run_interrupted_at_its_last_write(tmp_path):
    out, prov = _interrupted(tmp_path, keep=3)  # every record, a cost line and the marker lost
    done = runner.resume(_double, [1, 2, 3], str, out, URL, workers=1, prov=prov)
    assert done == []
    assert len(runner.all_records(out)) == 3
    assert json.loads((out / "resumptions.jsonl").read_text())["finalization_only"] is True


def test_runner_keeps_the_marker_when_the_records_are_invalid(tmp_path):
    out, prov = _interrupted(tmp_path, keep=3)
    lines = (out / "records.jsonl").read_text().splitlines()
    (out / "records.jsonl").write_text("\n".join([*lines, lines[0]]) + "\n")  # a task twice
    with pytest.raises(ValueError, match="twice"):
        runner.resume(_double, [1, 2, 3], str, out, URL, workers=1, prov=prov)
    assert (out / "running.marker").exists()
    assert not (out / "resumptions.jsonl").exists()  # refused before any write


def test_c2_references_are_authenticated(tmp_path):
    from refute.core.seal import core_sha256

    stage1 = tmp_path / "calibration/v0.4/runs/stage1"
    stage1.mkdir(parents=True)
    dossier = tmp_path / c2.V04_DOSSIERS / "TIC-1"
    (dossier / "data").mkdir(parents=True)
    (dossier / "verdict.json").write_text("{}")
    (dossier / "data/manifest.json").write_text('{"files": []}')
    measurements = tmp_path / c2.V04_MEASUREMENTS
    measurements.parent.mkdir(parents=True)
    measurements.write_bytes(b"")
    seals = {"core_sha256": {"TIC-1": core_sha256(dossier)}}
    (stage1 / "seals.json").write_text(json.dumps(seals))
    sha = hashlib.sha256(b"").hexdigest()
    records = {"records_sha256": {c2.MEASUREMENTS_KEY: sha}}
    (stage1 / "records.json").write_text(json.dumps(records))
    assert c2.reference_problems(tmp_path) == []
    (dossier / "data/manifest.json").write_text('{"files": [1]}')
    assert any("sealed core" in p for p in c2.reference_problems(tmp_path))
    with pytest.raises(ValueError, match="not authenticated"):
        c2.references(tmp_path)
    (tmp_path / c2.V04_DOSSIERS / "TIC-2").mkdir()
    assert "unexpected dossier: TIC-2" in c2.reference_problems(tmp_path)


def test_runner_refuses_a_run_another_process_owns(tmp_path):
    out, prov = _interrupted(tmp_path)
    with runner.owned(out), pytest.raises(runner.OwnershipError):
        runner.resume(_double, [1, 2, 3], str, out, URL, workers=1, prov=prov)


def test_c3_product_state(tmp_path):
    from refute.packs.tess.adapter import FETCH_SCHEMA

    def rec(sector, fmt="spoc-fits"):
        return {"sector": sector, "path": f"{sector}.fits", "sha256": "0" * 64, "format": fmt}

    assert c3run.product_state(None)["state"] == "missing"
    assert c3run.product_state({"files": []})["state"] == "error"  # no schema: invalid
    base = {"schema": FETCH_SCHEMA, "tic_id": 7, "target_key": "TIC-7"}
    assert c3run.product_state(base)["state"] == "error"  # no 'files' list: invalid
    assert c3run.product_state({**base, "files": []})["state"] == "missing"
    unsupported = {**base, "files": [rec(5, "unsupported")], "pixel_files": []}
    assert c3run.product_state(unsupported)["state"] == "error"  # never absence
    no_format = {**base, "files": [{"sector": 5, "path": "a", "sha256": "0" * 64}]}
    assert c3run.product_state(no_format)["state"] == "error"
    manifest = {**base, "files": [rec(5), rec(9)], "pixel_files": [rec(5, "spoc-tpf")]}
    state = c3run.product_state(manifest)
    assert state["state"] == "missing" and "[9]" in state["reason"]
    manifest["pixel_files"].append(rec(9, "spoc-tpf"))
    assert c3run.product_state(manifest)["state"] == "present"
    target = {"key": "TIC-8", "tic_id": 8}
    assert c3run.product_state(manifest, target)["state"] == "error"  # another target
    data = b"fits"
    (tmp_path / "a.fits").write_bytes(data)
    good = {
        "sector": 5,
        "path": "a.fits",
        "sha256": hashlib.sha256(data).hexdigest(),
        "format": "spoc-fits",
    }
    bad = {**good, "sha256": "0" * 64}
    checked = {**base, "files": [good], "pixel_files": []}
    assert c3run.product_state(checked, None, tmp_path)["state"] == "missing"
    corrupt = {**base, "files": [bad], "pixel_files": []}
    assert c3run.product_state(corrupt, None, tmp_path)["state"] == "error"  # never absence


def test_c3_absent_products_only_from_the_fetch_state():
    task = c3run.C3Task(
        {"key": "TIC-1", "kind": "planet", "tic_id": 1},
        {},
        "x",
        {"state": "missing", "reason": "r"},
    )
    assert c3run.run_task(task)["status"] == "MISSING_PRODUCTS"
    task = c3run.C3Task(
        {"key": "TIC-1", "kind": "planet", "tic_id": 1}, {}, "x", {"state": "error", "reason": "r"}
    )
    assert c3run.run_task(task)["status"] == "ERROR"  # never a replacement reason


def test_attempts_after_the_first_need_approval(tmp_path):
    first = runner.reserve_attempt(tmp_path / "attempts", None, "R_c3")
    assert first.name == "attempt-01" and (first / "exposure.json").is_file()
    with pytest.raises(ValueError, match="approval"):
        runner.reserve_attempt(tmp_path / "attempts", None, "R_c3")
    assert runner.reserve_attempt(tmp_path / "attempts", URL, "R_c3").name == "attempt-02"


def test_projected_hours():
    prefix = [{"family": "A", "cpu_seconds": 36.0}, {"family": "B", "cpu_seconds": 72.0}]
    assert runner.projected_hours(prefix, {"A": 100, "B": 50}, "family") == pytest.approx(2.0)
    with pytest.raises(ValueError):
        runner.projected_hours(prefix, {"C": 1}, "family")
