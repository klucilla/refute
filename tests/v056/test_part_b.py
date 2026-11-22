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
    doc = gen.claim(gen.current_round())
    text = gen.HEADER + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=96)
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
    # run_one (the battery chain) and the deletion and admission code are part A's; run_batch and
    # _finish differ only by the bindings listed in the runner's docstring (see the diff test).
    for name in ("run_one", "release_tpfs", "delete_literal", "_pick", "sweep"):
        fa = _function_source(A / "part_a_run.py", name)
        fb = _function_source(B / "part_b_run.py", name)
        fb = fb.replace(B_MODE, A_MODE)
        assert fa == fb, name


def test_runner_diff_is_current():
    import difflib

    a = (A / "part_a_run.py").read_text("utf-8").splitlines(keepends=True)
    b = (B / "part_b_run.py").read_text("utf-8").splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(a, b, "docs/validation/v0.5.6/part_a_run.py",
                                        "calibration/v0.5.6/part_b_run.py"))  # fmt: skip
    assert (B / "part_b_run.diff").read_text("utf-8") == diff


@pytest.fixture(scope="module")
def rb():
    return _load(B / "part_b_run.py", "part_b_run_under_test")


def test_stop_kinds(rb, monkeypatch):
    small = {"sectors": [1], "key": "TIC-1"}
    huge = {"sectors": list(range(70)), "key": "TIC-2"}  # 65 + 25 x 70 s > the 28-min window
    monkeypatch.setattr(rb, "_charged", lambda: 1.0)
    monkeypatch.setattr(rb, "disk_bytes", lambda root=None: 1)
    assert rb.stop_kind("the cap of 15.0 CPU-h is reached", [small]) == "cap_cpu"
    assert rb.stop_kind("the disk peak passed 20 GB", [small]) == "cap_disk"
    assert rb.stop_kind("no remaining target fits (disk 1 GB)", [huge]) == "window"
    assert rb.stop_kind("no remaining target fits (disk 1 GB)", [small]) == "other"
    monkeypatch.setattr(rb, "_charged", lambda: 14.999)
    assert rb.stop_kind("no remaining target fits (disk 1 GB)", [small]) == "cap_cpu"
    monkeypatch.setattr(rb, "_charged", lambda: 1.0)
    monkeypatch.setattr(rb, "disk_bytes", lambda root=None: 18e9)
    assert rb.stop_kind("no remaining target fits (disk 18 GB)", [small]) == "cap_disk"
    assert rb.stop_kind("a worker failed on TIC-1", [small]) == "other"


def test_a_failure_prevails_over_a_cap(rb, tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.json"
    monkeypatch.setattr(rb, "LEDGER", ledger)
    monkeypatch.setattr(rb, "_charged", lambda: 1.0)
    monkeypatch.setattr(rb, "disk_bytes", lambda root=None: 1)
    small = {"sectors": [1], "key": "TIC-1"}
    ledger.write_text(json.dumps({"batches": [{"failures": []}]}), "utf-8")
    assert rb.terminal("stopped", "the disk peak passed 20 GB", [small]) == "cap_disk"
    ledger.write_text(json.dumps({"batches": [{"failures": ["TIC-1: OSError"]}]}), "utf-8")
    assert rb.terminal("stopped", "the disk peak passed 20 GB", [small]) == "other"
    term = json.loads(ledger.read_text("utf-8"))["terminal"]
    assert term["kind"] == "other" and term["failures"] == ["TIC-1: OSError"]


# --- the draw's offline validation -----------------------------------------------------------


SIGNATURE = "ab" * 48
LOCK_BYTES = b'{"a synthetic lock": true}\n'
ROUND_NUMBER = 20_000_000


def _synthetic_draw(dr):
    """A draw built from the real frozen inputs, a synthetic beacon and commit, and synthetic
    listings that make every walked TIC eligible."""
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
            chosen.append(dr.chosen_entry(paf, entry, r))
        arms[s] = {"pool": len(groups[s]), "checked": len(trail), "eligible": len(chosen),
                   "chosen": chosen, "trail": trail}  # fmt: skip
    lock_sha = hashlib.sha256(LOCK_BYTES).hexdigest()
    number = ROUND_NUMBER
    return {
        "schema": "refute-v056-part-b-draw-2",
        "status": "complete",
        "lock_sha256": lock_sha,
        "round": {
            "round": number,
            "lock_commit": "c" * 40,
            "github_time_utc": "2026-11-23T10:00:00Z",
        },  # fmt: skip
        "beacon": {
            "round": number,
            "signature": SIGNATURE,
            "previous_signature": "00",
            "randomness": randomness,
        },  # fmt: skip
        "arms": arms,
    }


@pytest.fixture(scope="module")
def synthetic(dr):
    return _synthetic_draw(dr)


CLAIM_RND = {"round": ROUND_NUMBER}


def _validate(dr, d, lock=LOCK_BYTES):
    off = {"verify_signature": False, "check_commit": False, "check_ci": False}
    return dr.validate_draw(d, lock, claim_rnd=CLAIM_RND, **off)


def test_validate_draw_accepts_a_valid_draw(dr, synthetic):
    assert all(t["reason"] == "eligible" for s in dr.STRATA for t in synthetic["arms"][s]["trail"])
    assert _validate(dr, synthetic) == []


def test_validate_draw_checks_the_signature_and_the_commit(dr, synthetic):
    off = {"claim_rnd": CLAIM_RND, "check_commit": False, "check_ci": False}
    assert dr.validate_draw(synthetic, LOCK_BYTES, **off)  # a synthetic beacon: no BLS signature
    off = {"claim_rnd": CLAIM_RND, "verify_signature": False, "check_ci": False}
    assert dr.validate_draw(synthetic, LOCK_BYTES, **off)  # no commit adds the lock


def _rehash(t):
    import hashlib

    t["listing_sha256"] = hashlib.sha256(json.dumps(t["listing"], indent=1).encode()).hexdigest()


def test_validate_draw_refuses_tampering(dr, synthetic):
    def bad(change):
        d = copy.deepcopy(synthetic)
        change(d)
        return _validate(dr, d)

    assert _validate(dr, synthetic, b"another lock")
    assert bad(lambda d: d["arms"]["fp"]["trail"].reverse())
    assert bad(lambda d: d["arms"]["planet"]["trail"][0].update(reason="1 predicted transit(s)"))
    assert bad(lambda d: d["arms"]["planet"]["chosen"].pop())
    assert bad(lambda d: d.update(status="short"))
    assert bad(lambda d: d["beacon"].update(randomness="00" * 32))
    # the claim's round and no other: the draw's and the beacon's must both be it
    assert bad(lambda d: d["round"].update(round=ROUND_NUMBER + 1))
    assert bad(lambda d: d["beacon"].update(round=ROUND_NUMBER + 1))
    # the fields the run uses are rebuilt from the frame and the trail
    assert bad(lambda d: d["arms"]["planet"]["chosen"][0].update(period_days="1.0"))
    assert bad(lambda d: d["arms"]["planet"]["chosen"][0].update(epoch_bjd="2459000.0"))
    assert bad(lambda d: d["arms"]["fp"]["chosen"][0].update(sectors=[1, 2]))

    def listing_change(field, value, on_window=True):
        def change(d):
            t = d["arms"]["fp"]["trail"][0]
            target = t["listing"]["products"][0] if on_window else t["listing"]
            target[field] = value
            _rehash(t)

        return change

    assert bad(listing_change("tic_id", 1, on_window=False))
    assert bad(listing_change("sector", 0))
    assert bad(listing_change("exptime", float("nan")))
    assert bad(listing_change("t_max_mjd", float("nan")))

    def ephemeris_in_both(d):
        t, c = d["arms"]["planet"]["trail"][0], d["arms"]["planet"]["chosen"][0]
        for x in (t, c):
            x.update(period_days="1.0", epoch_bjd="2459000.0", duration_hours="9.0")

    assert bad(ephemeris_in_both)
    assert bad(listing_change("exptime", 1800.0))
    assert bad(listing_change("sector", 108))
    assert bad(listing_change("productFilename", "tess-s0001-0000000000000001-0001-s_lc.fits"))

    def part_a_product(d):
        a = json.loads((A / "part-a-draw.json").read_text("utf-8"))
        d["arms"]["fp"]["trail"][0]["products"] = [a["arms"]["open"]["trail"][0]["products"][0]]

    assert bad(part_a_product)


def test_round_is_after(dr):
    from refute.drand import round_time

    when = round_time(ROUND_NUMBER).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert not dr.round_is_after(ROUND_NUMBER, when)  # published at that second: not after
    assert dr.round_is_after(ROUND_NUMBER + 1, when)
    assert not dr.round_is_after(ROUND_NUMBER - 1, when)


def test_claim_round(dr, tmp_path, monkeypatch):
    from refute.drand import DRAND_CHAIN_HASH, round_time

    claim = tmp_path / "claim.yaml"
    monkeypatch.setattr(dr, "CLAIM", claim)

    def write(**d):
        claim.write_text(yaml.safe_dump({"definitions": d}), "utf-8")

    good = {"drand_chain_hash": DRAND_CHAIN_HASH, "drand_round": str(ROUND_NUMBER),
            "drand_round_time_utc": round_time(ROUND_NUMBER).isoformat()}  # fmt: skip
    write(**good)
    assert dr.claim_round()["round"] == ROUND_NUMBER
    for bad in ({"drand_round": "unset"}, {"drand_chain_hash": "0" * 64},
                {"drand_round_time_utc": round_time(ROUND_NUMBER + 1).isoformat()}):  # fmt: skip
        write(**{**good, **bad})
        with pytest.raises(SystemExit):
            dr.claim_round()


def test_claim_round_state_before_the_lock():
    # Before the lock the claim holds either no round yet, or the round fixed by
    # ``--drand-round auto`` just before the lock (a legitimate state, round 4's item 2).
    from refute.drand import round_time

    gen = _load(B / "part_b_claim.py", "part_b_claim_round_under_test")
    d = yaml.safe_load((B / "claim.yaml").read_text("utf-8"))["definitions"]
    if d["drand_round"].isdigit():
        assert d["drand_round_time_utc"] == round_time(int(d["drand_round"])).isoformat()
    else:
        assert d["drand_round"] == gen.UNSET and not (B / "claim.lock.json").exists()
    assert gen.drand_definitions(ROUND_NUMBER)["drand_round"] == str(ROUND_NUMBER)


def test_the_claim_generator_never_writes_after_the_lock(tmp_path, monkeypatch):
    # The decision of 2026-11-22, 19:30, item 1: no relock, no ``--drand-round N`` at all, and no
    # rewrite of any kind once the lock exists.
    gen = _load(B / "part_b_claim.py", "part_b_claim_lock_under_test")
    monkeypatch.setattr(gen, "HERE", tmp_path)
    (tmp_path / "claim.lock.json").write_text("{}", "utf-8")
    for argv in ([], ["--drand-round", "auto"], ["--drand-round", str(ROUND_NUMBER)]):
        monkeypatch.setattr(gen.sys, "argv", ["part_b_claim.py", *argv])
        with pytest.raises(SystemExit):
            gen.main()
        assert not (tmp_path / "claim.yaml").exists()
    (tmp_path / "claim.lock.json").unlink()
    monkeypatch.setattr(gen.sys, "argv", ["part_b_claim.py", "--drand-round", str(ROUND_NUMBER)])
    with pytest.raises(SystemExit):
        gen.main()  # a number is never accepted, even before the lock
    assert not (tmp_path / "claim.yaml").exists()


def test_lock_commit_refuses_a_relock(dr, monkeypatch):
    # The lock commit is the one commit that touches the lock file; a second commit that
    # touches it (a relock, a removal and a new addition) is refused (19:30, item 1).
    def fake(history):
        def _git(*args):
            if "--diff-filter=A" in args:
                return "".join(c + "\n" for c, kind in history if kind == "A").encode()
            return "".join(c + "\n" for c, _ in history).encode()

        return _git

    monkeypatch.setattr(dr, "_git", fake([("c1", "A")]))
    assert dr.lock_commit() == "c1"
    for history in ([("c2", "M"), ("c1", "A")], [("c3", "A"), ("c2", "D"), ("c1", "A")], []):
        monkeypatch.setattr(dr, "_git", fake(history))
        with pytest.raises(SystemExit):
            dr.lock_commit()


def test_check_verifies_the_lock_before_reading_the_round(dr, monkeypatch):
    import refute.core.lock as core_lock

    class Failed:
        class status:  # noqa: N801 - mirrors the result's shape
            value = "TAMPERED"

        messages = ["synthetic"]

    def never(*_a, **_k):
        raise AssertionError("the round was read before the lock verified")

    monkeypatch.setattr(core_lock, "verify_claim", lambda _path: Failed)
    monkeypatch.setattr(dr, "claim_round", never)
    monkeypatch.setattr(dr, "lock_commit", never)
    with pytest.raises(SystemExit):
        dr.check()


def test_validate_draw_refuses_a_boolean_sector(dr, synthetic):
    # Round 4's item 3: ``True == 1`` in Python, so a boolean sector equals sector 1 everywhere
    # else; the listing filter itself must refuse it.
    d = copy.deepcopy(synthetic)
    t = d["arms"]["fp"]["trail"][0]
    t["listing"]["products"][0]["sector"] = True
    _rehash(t)
    assert any("sector" in p for p in _validate(dr, d))


def test_a_recorded_failure_prevails_over_complete(rb, tmp_path, monkeypatch):
    # Round 4's item 4: on a resumed run with every record present and a failure already in the
    # ledger, the terminal kind is ``other``, never ``complete``.
    ledger = tmp_path / "ledger.json"
    monkeypatch.setattr(rb, "LEDGER", ledger)
    monkeypatch.setattr(rb, "_charged", lambda: 1.0)
    ledger.write_text(json.dumps({"batches": [{"failures": []}]}), "utf-8")
    assert rb.terminal("complete", None, []) == "complete"
    ledger.write_text(
        json.dumps({"batches": [{"failures": ["TIC-1: OSError"]}, {"failures": []}]}), "utf-8"
    )
    assert rb.terminal("complete", None, []) == "other"
    assert json.loads(ledger.read_text("utf-8"))["terminal"]["kind"] == "other"


# --- the evaluation's checks before counting -------------------------------------------------


def test_empty_denominator_is_inconclusive(ev):
    empty = _stratum(ev, events=0, non_events=0)
    empty["drawn"], empty["loss_cap"] = 0, 0
    v, why, _ = ev.verdict("complete", {"planet": empty, "fp": _stratum(ev, 20, 130)})
    assert v == "INCONCLUSIVE" and "empty" in why


def _write(path: Path, obj) -> None:
    path.write_text(json.dumps(obj), "utf-8")


LK, DW = "1" * 64, "2" * 64


def test_records_are_bound(ev, tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "RECORDS", tmp_path)
    good = {"claim_id": ev.CLAIM_ID, "mode": "confirmatory", "target_key": "TIC-1",
            "lock_sha256": LK, "draw_sha256": DW}  # fmt: skip
    drawn = {"TIC-1", "TIC-2"}
    _write(tmp_path / "TIC-1.json", good)
    records, files = ev.load_records(drawn, LK, DW)
    assert set(records) == {"TIC-1"} and len(files) == 1
    with pytest.raises(SystemExit):
        ev.load_records(drawn, LK, "3" * 64)  # another draw
    _write(tmp_path / "TIC-3.json", {**good, "target_key": "TIC-3"})
    with pytest.raises(SystemExit):
        ev.load_records(drawn, LK, DW)  # not drawn
    (tmp_path / "TIC-3.json").unlink()
    _write(tmp_path / "TIC-2.json", {**good, "target_key": "TIC-1"})
    with pytest.raises(SystemExit):
        ev.load_records(drawn, LK, DW)  # a file not named after its key
    _write(tmp_path / "TIC-2.json", {**good, "target_key": "TIC-2", "mode": "exploratory"})
    with pytest.raises(SystemExit):
        ev.load_records(drawn, LK, DW)


def test_run_state_needs_a_terminal_state(ev, tmp_path, monkeypatch):
    claim, runner, ledger = tmp_path / "c.yaml", tmp_path / "r.py", tmp_path / "l.json"
    claim.write_text("claim", "utf-8")
    runner.write_text("runner", "utf-8")
    for name, value in (("CLAIM", claim), ("RUNNER", runner), ("LEDGER", ledger)):
        monkeypatch.setattr(ev, name, value)
    batch = {"claim_sha256": ev.sha256(b"claim"), "code_sha256": ev.sha256(b"runner"),
             "lock_sha256": LK, "draw_sha256": DW, "stop": None}  # fmt: skip
    term = {"state": "complete", "kind": "complete", "unrecorded": [], "batches": 1,
            "lock_sha256": LK, "draw_sha256": DW}  # fmt: skip
    one, two = {"TIC-1"}, {"TIC-1", "TIC-2"}
    recs = {"TIC-1": {}}

    def state(doc, drawn):
        _write(ledger, doc)
        return ev.run_state(drawn, recs, LK, DW)

    assert state({"batches": [batch], "terminal": term}, one)["missing_records"] == []
    with pytest.raises(SystemExit):
        state({"batches": [batch]}, one)  # no terminal state
    with pytest.raises(SystemExit):
        state({"batches": [batch], "terminal": term}, two)  # complete, yet a record is missing
    cap = {**term, "state": "stopped", "kind": "cap_cpu", "unrecorded": ["TIC-2"]}
    assert state({"batches": [batch], "terminal": cap}, two)["missing_records"] == ["TIC-2"]
    with pytest.raises(SystemExit):
        state({"batches": [batch, batch], "terminal": cap}, two)  # a batch after the end
    with pytest.raises(SystemExit):
        state({"batches": [batch], "terminal": {**cap, "kind": "other"}}, two)
    with pytest.raises(SystemExit):
        state({"batches": [batch], "terminal": {**cap, "unrecorded": []}}, two)
    with pytest.raises(SystemExit):
        state({"batches": [{**batch, "draw_sha256": "3" * 64}], "terminal": term}, one)
    with pytest.raises(SystemExit):
        state({"batches": [batch], "terminal": {**term, "lock_sha256": "3" * 64}}, one)
    with pytest.raises(SystemExit):  # a failure during the drain, then a cap stop
        state({"batches": [{**batch, "failures": ["TIC-2: OSError"]}], "terminal": cap}, two)


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
