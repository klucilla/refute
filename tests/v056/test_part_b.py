"""v0.5.6 part B: the evaluation's statistics and verdict, the strata and the draw order, the
runner's identity with part A's, and the claim's test plan (``calibration/v0.5.6``). Offline:
synthetic records and the committed files only."""

from __future__ import annotations

import ast
import copy
import csv
import importlib.util
import io
import json
from fractions import Fraction
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "calibration/v0.5.6"
A = ROOT / "docs/validation/v0.5.6"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def ev():
    return _load(B / "part_b_evaluate.py", "part_b_evaluate_under_test")


@pytest.fixture(scope="module")
def dr():
    return _load(B / "part_b_draw.py", "part_b_draw_under_test")


# --- statistics ------------------------------------------------------------------------------


def test_fisher_tea_tasting(ev):
    # The lady tasting tea: 3 of 4 right; P(X >= 3) = (16 + 1) / 70.
    assert ev.fisher_greater(3, 1, 1, 3) == Fraction(17, 70)


def test_fisher_edges(ev):
    assert ev.fisher_greater(0, 10, 0, 10) == 1
    assert ev.fisher_greater(0, 0, 0, 0) == 1
    assert ev.fisher_greater(10, 0, 0, 10) == Fraction(1, 184756)  # 1 / C(20, 10)
    with pytest.raises(ValueError):
        ev.fisher_greater(-1, 1, 1, 1)


def test_fisher_part_a_matched_table(ev):
    # Part A's exploratory table (5 of 21 against 1 of 120): small, as the review computed.
    p = ev.fisher_greater(5, 16, 1, 119)
    assert 0.0001 < float(p) < 0.001


def test_wilson(ev):
    lo, hi = ev.wilson(0, 10)
    assert lo == 0.0 and hi == pytest.approx(0.2775, abs=1e-4)
    assert ev.wilson(0, 0) is None
    lo, hi = ev.wilson(5, 100)
    assert lo == pytest.approx(0.0215, abs=1e-4) and hi == pytest.approx(0.1118, abs=1e-4)


# --- records and verdict ---------------------------------------------------------------------


def _rec(outcome="SURVIVED", matched=True, status="OK", coverage=5, fatal=None):
    tests = {"snr": {"status": "PASS", "severity": "gate", "coverage": coverage}}
    if fatal:
        tests[fatal] = {"status": "FAIL", "severity": "fatal", "coverage": coverage}
    return {"status": status, "outcome": outcome, "identity": {"matched": matched},
            "tests": tests, "decisive": ["snr", *( [fatal] if fatal else [])]}  # fmt: skip


def test_classify(ev):
    assert ev.classify(None) == ("excluded", True)
    assert ev.classify({"status": "ERROR"}) == ("non_event", True)
    assert ev.classify({"status": "MISSING_PRODUCTS"}) == ("excluded", True)
    assert ev.classify(_rec(coverage=0)) == ("excluded", True)
    assert ev.classify(_rec("REFUTED", matched=False)) == ("non_event", False)
    assert ev.classify(_rec("REFUTED", matched=True, fatal="odd_even")) == ("event", False)
    assert ev.classify(_rec("INCONCLUSIVE")) == ("non_event", False)


def _stratum(ev, events, non_events, losses=0, errors=0):
    drawn, records = [], {}
    i = 0
    for kind, count in (("e", events), ("n", non_events), ("l", losses), ("x", errors)):
        for _ in range(count):
            i += 1
            drawn.append({"tic_id": i})
            if kind == "e":
                records[f"TIC-{i}"] = _rec("REFUTED", True, fatal="odd_even")
            elif kind == "n":
                records[f"TIC-{i}"] = _rec("INCONCLUSIVE")
            elif kind == "x":
                records[f"TIC-{i}"] = {"status": "ERROR"}
    return ev.stratum_summary(drawn, records)


def test_stratum_summary_counts(ev):
    s = _stratum(ev, events=3, non_events=140, losses=5, errors=2)
    assert s["drawn"] == 150
    assert s["losses"] == 7 and s["loss_cap"] == 15
    assert s["denominator"] == 145  # events + non-events + ERROR
    assert s["events"] == 3
    assert s["event_first_decisive_fatal_fail"] == {"odd_even": 3}


def test_verdicts(ev):
    fp_strong = _stratum(ev, events=20, non_events=130)
    planet_low = _stratum(ev, events=1, non_events=149)
    planet_high = _stratum(ev, events=12, non_events=138)
    fp_weak = _stratum(ev, events=2, non_events=148)
    v, _, t = ev.verdict("complete", {"planet": planet_low, "fp": fp_strong})
    assert v == "SURVIVED" and t["guard"]["holds"]
    v, _, t = ev.verdict("complete", {"planet": planet_high, "fp": _stratum(ev, 40, 110)})
    assert v == "WEAKENED" and not t["guard"]["holds"]
    v, _, _ = ev.verdict("short", {"planet": planet_low, "fp": fp_weak})
    assert v == "REFUTED"
    v, why, _ = ev.verdict("incomplete", {"planet": planet_low, "fp": fp_strong})
    assert v == "INCONCLUSIVE" and "incomplete" in why
    lossy = _stratum(ev, events=20, non_events=114, losses=16)
    v, why, _ = ev.verdict("complete", {"planet": planet_low, "fp": lossy})
    assert v == "INCONCLUSIVE" and "fp" in why


def test_error_counts_in_the_denominator(ev):
    # 15 ERROR records: at the cap, still decided, each a non-event.
    s = _stratum(ev, events=20, non_events=115, errors=15)
    assert s["losses"] == 15 and s["denominator"] == 150
    v, _, _ = ev.verdict("complete", {"planet": _stratum(ev, 1, 149), "fp": s})
    assert v == "SURVIVED"


# --- strata and the draw order ---------------------------------------------------------------


def _row(tic, half="confirmation", arm="open", disp="FP"):
    return {"tic_id": str(tic), "half": half, "arm": arm, "tfopwg_disp_descriptive": disp}


def test_strata_rules(dr):
    rows = [
        _row(1), _row(2, disp="PC"), _row(3, disp="FA"), _row(4, disp="KP"),
        _row(5, arm="planet", disp="CP"), _row(6, half="exploration"), _row(7),
    ]  # fmt: skip
    s = dr.strata(rows, exposed={7})
    assert [int(r["tic_id"]) for r in s["fp"]] == [1]
    assert [int(r["tic_id"]) for r in s["planet"]] == [5]


def test_order_is_a_reproducible_permutation(dr):
    rows = [_row(t) for t in (40, 10, 30, 20, 50)]
    a = dr.order(rows, "ab" * 32, "fp")
    b = dr.order(list(reversed(rows)), "ab" * 32, "fp")
    assert [r["tic_id"] for r in a] == [r["tic_id"] for r in b]
    assert sorted(int(r["tic_id"]) for r in a) == [10, 20, 30, 40, 50]
    assert dr.stratum_seed("ab" * 32, "fp") != dr.stratum_seed("ab" * 32, "planet")


# --- the committed pool, claim and runner ----------------------------------------------------


def test_pool_matches_the_frozen_inputs(dr):
    pool = yaml.safe_load((B / "pool-targets.yaml").read_text("utf-8"))
    exposure = json.loads((A / "part-b-exposure.json").read_text("utf-8"))
    exposed = set(exposure["exposed_tics"])
    frame = {
        int(r["tic_id"]): r
        for r in csv.DictReader(io.StringIO((A / "part-a-frame.csv").read_text("utf-8")))
    }
    kinds = {"planet": "planet", "fp": "false_positive"}
    counts = {"planet": 0, "fp": 0}
    for t in pool["targets"]:
        row = frame[t["tic_id"]]
        s = dr.stratum_of(row)
        assert s is not None and t["catalog"]["stratum"] == s and t["kind"] == kinds[s]
        assert t["tic_id"] not in exposed
        counts[s] += 1
    expected = dr.strata(list(frame.values()), exposed)
    assert counts == {s: len(expected[s]) for s in dr.STRATA}
    assert pool["selection"]["counts"] == counts


def test_claim_is_current_and_valid():
    gen = _load(B / "part_b_claim.py", "part_b_claim_under_test")
    text = gen.HEADER + yaml.safe_dump(gen.claim(), sort_keys=False, allow_unicode=True, width=96)
    assert (B / "claim.yaml").read_text("utf-8") == text  # every input's SHA-256 is current
    from refute.core.claim import load_claim

    loaded = load_claim(B / "claim.yaml")
    assert loaded.claim.id == "tess-v0.5.6-part-b-fp-agreement"


def test_test_plan_is_part_as(tmp_path):
    from refute.packs.tess.discover.measure import stage_plan
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.pipeline import expected_by_role

    v05 = yaml.safe_load((ROOT / "calibration/v0.5/claim.yaml").read_text("utf-8"))["test_plan"]
    b = yaml.safe_load((B / "claim.yaml").read_text("utf-8"))["test_plan"]
    pa, pb = copy.deepcopy(stage_plan(v05, 2)), copy.deepcopy(stage_plan(b, 2))
    for p in (pa, pb):
        for k in ("decisive", "survived_meaning", "inputs"):
            p["discovery"].pop(k)
    assert pa == pb
    ra = expected_by_role(TessTestPlan.model_validate(stage_plan(v05, 2)), False)
    rb = expected_by_role(TessTestPlan.model_validate(stage_plan(b, 2)), False)
    assert ra == rb


B_MODE = '"mode": "confirmatory",\n        "claim_id": CLAIM_ID,'
A_MODE = '"mode": "exploratory",'


def _function_source(path: Path, name: str) -> str:
    text = path.read_text("utf-8")
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(text, node)
    raise AssertionError(name)


def test_runner_battery_chain_unchanged():
    a = _function_source(A / "part_a_run.py", "run_one")
    b = _function_source(B / "part_b_run.py", "run_one")
    b = b.replace(
        '"mode": "confirmatory",\n        "claim_id": CLAIM_ID,', '"mode": "exploratory",'
    )
    assert a == b
    for name in ("release_tpfs", "delete_literal", "run_batch", "_pick", "_finish", "sweep"):
        fa = _function_source(A / "part_a_run.py", name)
        fb = _function_source(B / "part_b_run.py", name)
        fb = fb.replace(
            '"mode": "confirmatory",\n        "claim_id": CLAIM_ID,', '"mode": "exploratory",'
        )
        assert fa == fb, name


def test_runner_diff_is_current():
    import difflib

    a = (A / "part_a_run.py").read_text("utf-8").splitlines(keepends=True)
    b = (B / "part_b_run.py").read_text("utf-8").splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(a, b, "docs/validation/v0.5.6/part_a_run.py",
                                        "calibration/v0.5.6/part_b_run.py"))  # fmt: skip
    assert (B / "part_b_run.diff").read_text("utf-8") == diff


# --- the draw's offline validation -----------------------------------------------------------


SIGNATURE = "ab" * 48
LOCK_BYTES = b'{"a synthetic lock": true}\n'


def _synthetic_draw(dr):
    """A draw built from the real frozen inputs, a synthetic beacon and synthetic listings that
    make every walked TIC eligible."""
    import hashlib

    randomness = hashlib.sha256(bytes.fromhex(SIGNATURE)).hexdigest()
    rows, exposed, _, _ = dr.frozen_inputs()
    groups = dr.strata(rows, exposed)
    paf = dr.frame_module()
    arms = {}
    for s in dr.STRATA:
        trail, chosen = [], []
        for position, r in enumerate(dr.order(groups[s], randomness, s)[: dr.PER_STRATUM]):
            tic, epoch = int(r["tic_id"]), float(r["epoch_bjd"]) - 2400000.5
            name = f"tess-s0001-{tic:016d}-0001-s_lc.fits"
            window = {"sector": 1, "exptime": 120.0, "obs_id": "x", "productFilename": name,
                      "dataURI": "mast:x", "t_min_mjd": epoch - 0.5,
                      "t_max_mjd": epoch + 3.5 * float(r["period_days"])}  # fmt: skip
            listing = {"tic_id": tic, "queried_utc": "2026-11-22T00:00:00Z", "products": [window]}
            reason, n = dr.reason_for(paf, r, [window])
            entry = {"position": position, "tic_id": tic, "toi": r["toi"], "reason": reason,
                     "predicted_transits": n, "sectors": [1], "products": [name],
                     "listing": listing,
                     "listing_sha256": hashlib.sha256(
                         json.dumps(listing, indent=1).encode()).hexdigest()}  # fmt: skip
            trail.append(entry)
            chosen.append({k: v for k, v in entry.items() if k != "listing"})
        arms[s] = {"pool": len(groups[s]), "checked": len(trail), "eligible": len(chosen),
                   "chosen": chosen, "trail": trail}  # fmt: skip
    lock_sha = hashlib.sha256(LOCK_BYTES).hexdigest()
    return {
        "schema": "refute-v056-part-b-draw-2",
        "status": "complete",
        "lock_sha256": lock_sha,
        "round": {"round": 7, "lock_sha256": lock_sha},
        "beacon": {"round": 7, "signature": SIGNATURE, "randomness": randomness},
        "arms": arms,
    }


@pytest.fixture(scope="module")
def synthetic(dr):
    return _synthetic_draw(dr)


def test_validate_draw_accepts_a_valid_draw(dr, synthetic):
    assert all(t["reason"] == "eligible" for s in dr.STRATA for t in synthetic["arms"][s]["trail"])
    assert dr.validate_draw(synthetic, LOCK_BYTES) == []


def test_validate_draw_refuses_tampering(dr, synthetic):
    def bad(change):
        d = copy.deepcopy(synthetic)
        change(d)
        return dr.validate_draw(d, LOCK_BYTES)

    assert dr.validate_draw(synthetic, b"another lock")
    assert bad(lambda d: d["arms"]["fp"]["trail"].reverse())
    assert bad(lambda d: d["arms"]["planet"]["trail"][0].update(reason="1 predicted transit(s)"))
    assert bad(lambda d: d["arms"]["planet"]["chosen"].pop())
    assert bad(lambda d: d.update(status="short"))
    assert bad(lambda d: d["beacon"].update(randomness="00" * 32))
    assert bad(lambda d: d["round"].update(lock_sha256="0" * 64))

    def part_a_product(d):
        d["arms"]["fp"]["chosen"][0]["products"] = [
            json.loads((A / "part-a-draw.json").read_text("utf-8"))["arms"]["open"]["trail"][0][
                "products"
            ][0]
        ]

    assert bad(part_a_product)


# --- the evaluation's checks before counting -------------------------------------------------


def test_empty_denominator_is_inconclusive(ev):
    empty = _stratum(ev, events=0, non_events=0)
    empty["drawn"], empty["loss_cap"] = 0, 0
    v, why, _ = ev.verdict("complete", {"planet": empty, "fp": _stratum(ev, 20, 130)})
    assert v == "INCONCLUSIVE" and "empty" in why


def _write(path: Path, obj) -> None:
    path.write_text(json.dumps(obj), "utf-8")


def test_records_are_bound(ev, tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "RECORDS", tmp_path)
    good = {"claim_id": ev.CLAIM_ID, "mode": "confirmatory", "target_key": "TIC-1"}
    _write(tmp_path / "TIC-1.json", good)
    records, files = ev.load_records({"TIC-1", "TIC-2"})
    assert set(records) == {"TIC-1"} and len(files) == 1
    _write(tmp_path / "TIC-3.json", {**good, "target_key": "TIC-3"})
    with pytest.raises(SystemExit):
        ev.load_records({"TIC-1", "TIC-2"})  # not drawn
    (tmp_path / "TIC-3.json").unlink()
    _write(tmp_path / "TIC-2.json", {**good, "target_key": "TIC-1"})
    with pytest.raises(SystemExit):
        ev.load_records({"TIC-1", "TIC-2"})  # a file not named after its key
    _write(tmp_path / "TIC-2.json", {**good, "target_key": "TIC-2", "mode": "exploratory"})
    with pytest.raises(SystemExit):
        ev.load_records({"TIC-1", "TIC-2"})


def test_missing_records_need_a_cap_stop(ev, tmp_path, monkeypatch):
    claim, runner, ledger = tmp_path / "c.yaml", tmp_path / "r.py", tmp_path / "l.json"
    claim.write_text("claim", "utf-8")
    runner.write_text("runner", "utf-8")
    for name, value in (("CLAIM", claim), ("RUNNER", runner), ("LEDGER", ledger)):
        monkeypatch.setattr(ev, name, value)
    batch = {"claim_sha256": ev.sha256(b"claim"), "code_sha256": ev.sha256(b"runner"),
             "stop": None}  # fmt: skip
    _write(ledger, {"batches": [batch]})
    assert ev.run_state({"TIC-1"}, {"TIC-1": {}})["missing_records"] == []
    with pytest.raises(SystemExit):
        ev.run_state({"TIC-1", "TIC-2"}, {"TIC-1": {}})
    _write(ledger, {"batches": [{**batch, "stop": "the cap of 15.0 CPU-h is reached"}]})
    assert ev.run_state({"TIC-1", "TIC-2"}, {"TIC-1": {}})["missing_records"] == ["TIC-2"]
    _write(ledger, {"batches": [{**batch, "code_sha256": "0" * 64}]})
    with pytest.raises(SystemExit):
        ev.run_state({"TIC-1"}, {"TIC-1": {}})


# --- the exposure scan, second version -------------------------------------------------------


def test_exposure_patterns():
    ex = _load(A / "part_b_exposure.py", "part_b_exposure_under_test")
    paf = ex._frame_module()
    assert ex.text_tics(paf, b'{"tic": 123456}') == {123456}
    assert ex.text_tics(paf, b"tic=7777 and TIC-12345") == {7777, 12345}
    assert ex.text_tics(paf, b"tess-s0008-0000000001003831-0136-s_lc.fits") == {1003831}
    assert ex.text_tics(paf, b"statistic 12345; ticket 4444") == set()
    assert ex.json_tics({"a": [{"TIC": "TIC 5555"}, {"tid": 6666, "x": {"tics": [1, "2"]}}]}) == {
        1,
        2,
        5555,
        6666,
    }
    assert ex.klass("calibration/v0.5/inputs/toi.csv") == "catalogue_copy"
    assert ex.klass("calibration/v0.5/inputs-references/pscomppars-references.csv") == "record"
    assert ex.klass(".cache/v05/x/tess-0000000000000001-") == "light_curve"
