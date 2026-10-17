"""metric_recompute (WP3, wp3-acceptance.md section 1.7, W3.14 to W3.18), offline.

Reference values are computed by hand in the comments; scikit-learn is the second
implementation at run time, never the oracle of these tests.
"""

import json
import math
import random
from decimal import Decimal

import numpy as np
import pytest

from refute.core.paper import EXPECTED_COVERAGE, FAILURE_ESTABLISHED, METRIC_RECOMPUTE
from refute.core.verdict import TestStatus
from refute.packs.ml import recompute as rc
from refute.packs.ml.recompute import Convention, Prepared, RecomputeError, UndefinedMetricError


def conv(metric, scale="fraction", **kw):
    c = Convention(metric=metric, scale=scale, **kw)
    c.validate()
    return c


def data(y_true, other, other_role="y_pred"):
    return {"y_true": np.array(y_true, dtype=object), other_role: np.array(other, dtype=object)}


def both(c, d):
    p = rc.prepare(c, d)
    return rc.own_metric(c, p), rc.sklearn_metric(c, p)


# ---- reference cases (W3.16) -------------------------------------------------------------

L01 = (0, 1)
L012 = (0, 1, 2)


@pytest.mark.parametrize(
    ("c", "d", "expected"),
    [
        # 3 of 4 right
        (conv("accuracy", labels=L01), data([0, 1, 1, 0], [0, 1, 0, 0]), 0.75),
        (conv("error_rate", labels=L01), data([0, 1, 1, 0], [0, 1, 0, 0]), 0.25),
        # pos 1: tp 2, fp 1, fn 1 -> P = R = F1 = 2/3
        (
            conv("precision", labels=L01, average="binary", pos_label=1, zero_division="0"),
            data([1, 1, 0, 0, 1], [1, 0, 1, 0, 1]),
            2 / 3,
        ),
        (
            conv("recall", labels=L01, average="binary", pos_label=1, zero_division="0"),
            data([1, 1, 0, 0, 1], [1, 0, 1, 0, 1]),
            2 / 3,
        ),
        (
            conv("f1", labels=L01, average="binary", pos_label=1, zero_division="0"),
            data([1, 1, 0, 0, 1], [1, 0, 1, 0, 1]),
            2 / 3,
        ),
        # class 2 absent from the data: F1 per class 2/3, 0.8, 0 (zero_division 0)
        (
            conv("f1", labels=L012, average="macro", zero_division="0"),
            data([0, 0, 1, 1], [0, 1, 1, 1]),
            (2 / 3 + 0.8 + 0.0) / 3,
        ),
        # weighted by support 2, 2, 0
        (
            conv("f1", labels=L012, average="weighted", zero_division="0"),
            data([0, 0, 1, 1], [0, 1, 1, 1]),
            (2 * 2 / 3 + 2 * 0.8) / 4,
        ),
        # micro: tp 3, fp 1, fn 1 -> 0.75
        (
            conv("f1", labels=L012, average="micro", zero_division="0"),
            data([0, 0, 1, 1], [0, 1, 1, 1]),
            0.75,
        ),
        # pairs (pos, neg): 0.35>0.1, 0.35<0.4, 0.8>0.1, 0.8>0.4 -> 3/4
        (
            conv("auroc", labels=L01, pos_label=1),
            data([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8], "y_score"),
            0.75,
        ),
        # one tie counts one half
        (conv("auroc", labels=L01, pos_label=1), data([0, 1], [0.5, 0.5], "y_score"), 0.5),
        # errors 0.5, 0.5, 0, 1 -> MAE 0.5; squares 0.25, 0.25, 0, 1 -> MSE 0.375
        (conv("mae", "native"), data([3, -0.5, 2, 7], [2.5, 0.0, 2, 8]), 0.5),
        (conv("mse", "native"), data([3, -0.5, 2, 7], [2.5, 0.0, 2, 8]), 0.375),
        (conv("rmse", "native"), data([3, -0.5, 2, 7], [2.5, 0.0, 2, 8]), math.sqrt(0.375)),
        # SS_res 1.5, mean 2.875, SS_tot 29.1875 -> 1 - 1.5 / 29.1875
        (conv("r2", "native"), data([3, -0.5, 2, 7], [2.5, 0.0, 2, 8]), 1 - 1.5 / 29.1875),
    ],
)
def test_reference_values_in_both_implementations(c, d, expected):
    own, other = both(c, d)
    assert own == pytest.approx(expected, abs=1e-12)
    assert other == pytest.approx(expected, abs=1e-12)


def test_metrics_do_not_depend_on_the_order_of_examples():
    rng = random.Random(3)
    y_true = [rng.randrange(3) for _ in range(50)]
    y_pred = [rng.randrange(3) for _ in range(50)]
    c = conv("f1", labels=L012, average="macro", zero_division="0")
    reference = both(c, data(y_true, y_pred))
    order = list(range(50))
    rng.shuffle(order)
    shuffled = both(c, data([y_true[i] for i in order], [y_pred[i] for i in order]))
    assert shuffled == pytest.approx(reference)


def test_zero_denominator_under_undefined_is_undefined_in_both():
    c = conv("precision", labels=L012, average="macro", zero_division="undefined")
    p = rc.prepare(c, data([0, 0, 1, 1], [0, 1, 1, 1]))  # class 2 never predicted
    with pytest.raises(UndefinedMetricError):
        rc.own_metric(c, p)
    with pytest.raises(UndefinedMetricError):
        rc.sklearn_metric(c, p)


def test_zero_division_one():
    c = conv("precision", labels=L012, average="macro", zero_division="1")
    own, other = both(c, data([0, 0, 1, 1], [0, 1, 1, 1]))
    assert own == pytest.approx((1 + 2 / 3 + 1) / 3) and other == pytest.approx(own)


def test_r2_of_a_constant_target_is_undefined():
    c = conv("r2", "native")
    p = rc.prepare(c, data([1, 1, 1], [1, 2, 3]))
    with pytest.raises(UndefinedMetricError):
        rc.own_metric(c, p)
    with pytest.raises(UndefinedMetricError):
        rc.sklearn_metric(c, p)


@pytest.mark.parametrize(
    "bad",
    [
        dict(metric="top5", scale="fraction", labels=L01),
        dict(metric="accuracy", scale="native", labels=L01),
        dict(metric="mae", scale="fraction"),
        dict(metric="accuracy", scale="fraction", labels=(0,)),
        dict(metric="accuracy", scale="fraction", labels=(0, 0)),
        dict(metric="accuracy", scale="fraction", labels=(0.0, 1.0)),
        dict(metric="f1", scale="fraction", labels=L01, average="samples", zero_division="0"),
        dict(metric="f1", scale="fraction", labels=L01, average="binary", zero_division="0"),
        dict(
            metric="f1",
            scale="fraction",
            labels=L012,
            average="binary",
            pos_label=1,
            zero_division="0",
        ),
        dict(metric="f1", scale="fraction", labels=L01, average="macro"),
        dict(metric="auroc", scale="fraction", labels=L012, pos_label=1),
        dict(metric="auroc", scale="fraction", labels=L01, pos_label=7),
        # #59, Codex review of the #85 items: a float pos_label matched a label by its text
        dict(
            metric="f1",
            scale="fraction",
            labels=("inf", "negative"),
            average="binary",
            pos_label=float("inf"),
            zero_division="0",
        ),
        dict(metric="auroc", scale="fraction", labels=("1", "0"), pos_label=1.0),
        dict(metric="auroc", scale="fraction", labels=(1, 0), pos_label=True),
        # round 2: a label that is not an integer or a string
        dict(
            metric="f1",
            scale="fraction",
            labels=({"nested": float("inf")}, "negative"),
            average="macro",
            zero_division="0",
        ),
    ],
)
def test_unsupported_conventions_are_refused(bad):
    with pytest.raises(ValueError):
        Convention(**bad).validate()


def test_labels_match_by_text_and_unknown_labels_are_refused():
    c = conv("accuracy", labels=("cat", "dog"))
    assert both(c, data(["cat", "dog"], ["cat", "cat"])) == (0.5, 0.5)
    with pytest.raises(RecomputeError):
        rc.prepare(c, data(["cat", "bird"], ["cat", "cat"]))
    c = conv("accuracy", labels=L01)
    with pytest.raises(RecomputeError):
        rc.prepare(c, data([0.0, 1.0], [0, 1]))  # float labels are not classes


# ---- printed interval ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("token", "rounding", "lower", "upper"),
    [
        ("0.50", "nearest", "0.495", "0.505"),
        ("91.2", "nearest", "91.15", "91.25"),
        ("5.0e-1", "nearest", "0.495", "0.505"),
        ("0.5", "truncate", "0.5", "0.6"),
        ("-0.0", "truncate", "-0.1", "0.0"),
        ("0.0", "truncate", "-0.1", "0.1"),
        ("+0.0", "truncate", "0.0", "0.1"),  # a sign is given: not the unsigned-zero case
        ("-0.4", "truncate", "-0.5", "-0.4"),
        ("0.50", "unknown", "0.49", "0.51"),
        ("1", "nearest", "0.5", "1.5"),
    ],
)
def test_printed_interval(token, rounding, lower, upper):
    i = rc.printed_interval(token, rounding)
    assert (i.lower, i.upper) == (Decimal(lower), Decimal(upper))


@pytest.mark.parametrize("token", ["", "abc", "1,5", "nan", "inf", "0x10", "1e"])
def test_printed_values_that_are_not_decimals_are_refused(token):
    with pytest.raises(RecomputeError):
        rc.printed_interval(token, "nearest")


# ---- decision table -----------------------------------------------------------------------


def interval(token, rounding="nearest"):
    return rc.printed_interval(token, rounding)


def test_decision_table():
    i = interval("0.50")
    assert rc.decide(0.5050000004, 0.5049999996, i, "nearest")[0] is TestStatus.PASS
    assert rc.decide(0.5050000014, 0.5050000006, i, "nearest")[0] is TestStatus.INCONCLUSIVE
    assert rc.decide(0.52, 0.52, i, "nearest")[0] is TestStatus.FAIL
    assert rc.decide(0.48, 0.48, i, "nearest")[0] is TestStatus.FAIL
    assert rc.decide(0.52, 0.51, i, "nearest")[0] is TestStatus.INCONCLUSIVE  # disagree
    assert (
        rc.decide(0.52, 0.52, interval("0.50", "unknown"), "unknown")[0] is TestStatus.INCONCLUSIVE
    )
    assert rc.decide(-0.04, -0.04, interval("-0.0", "truncate"), "truncate")[0] is TestStatus.PASS


def run(c, token, d, n, channel="fraction", unit="fraction", rounding="nearest", **kw):
    return rc.recompute_run("seed=1", c, token, channel, unit, rounding, d, n, **kw)


def test_run_in_percent_from_a_fraction_channel():
    c = conv("accuracy", "percent", labels=L01)
    d = data([0, 1, 1, 0], [0, 1, 0, 0])  # 75%
    outcome = run(c, "0.75", d, 4, channel="fraction", unit="percent")
    assert outcome.status is TestStatus.PASS and outcome.details["own"] == pytest.approx(75.0)
    assert run(c, "75.0", d, 4, channel="percent", unit="percent").status is TestStatus.PASS
    assert run(c, "80.0", d, 4, channel="percent", unit="percent").status is TestStatus.FAIL


def test_a_disagreeing_second_implementation_gives_inconclusive():
    c = conv("accuracy", labels=L01)
    d = data([0, 1, 1, 0], [0, 1, 0, 0])

    def broken(conv_, prepared: Prepared) -> float:
        return 0.70

    outcome = run(c, "0.80", d, 4, second=broken)
    assert outcome.status is TestStatus.INCONCLUSIVE and "disagree" in outcome.reason


def test_refute_side_problems_are_inconclusive_never_fail():
    c = conv("accuracy", labels=L01)
    d = data([0, 1, 1, 0], [0, 1, 0, 0])
    assert run(c, "0.80", d, 5).status is TestStatus.INCONCLUSIVE  # wrong count of examples
    assert run(c, "not a number", d, 4).status is TestStatus.INCONCLUSIVE
    zero = conv("precision", labels=L012, average="macro", zero_division="undefined")
    assert run(zero, "0.10", data([0, 0, 1, 1], [0, 1, 1, 1]), 4).status is TestStatus.INCONCLUSIVE
    r2 = conv("r2", "native")
    assert (
        run(r2, "0.5", data([1, 1, 1], [1, 2, 3]), 3, channel="native", unit="native").status
        is TestStatus.INCONCLUSIVE
    )


# ---- readers (W3.18) ----------------------------------------------------------------------


def test_readers_give_the_same_arrays(tmp_path):
    y_true, y_pred = [0, 1, 1, 0], [0, 1, 0, 0]
    arr = np.zeros(4, dtype=[("t", "i8"), ("p", "i8")])
    arr["t"], arr["p"] = y_true, y_pred
    np.save(tmp_path / "p.npy", arr)
    (tmp_path / "p.csv").write_text(
        "t,p\n" + "".join(f"{a},{b}\n" for a, b in zip(y_true, y_pred, strict=True))
    )
    (tmp_path / "p.jsonl").write_text(
        "".join(json.dumps({"t": a, "p": b}) + "\n" for a, b in zip(y_true, y_pred, strict=True))
    )
    c = conv("accuracy", labels=L01)
    fields = {"y_true": "t", "y_pred": "p"}
    for name, fmt in (("p.npy", "npy"), ("p.csv", "csv"), ("p.jsonl", "jsonl")):
        d = rc.read_predictions(tmp_path / name, fmt, fields)
        assert both(c, d) == (0.75, 0.75), fmt


def test_readers_refuse_pickles_missing_fields_and_non_finite_values(tmp_path):
    np.save(tmp_path / "obj.npy", np.array([{"a": 1}], dtype=object), allow_pickle=True)
    with pytest.raises(RecomputeError):
        rc.read_predictions(tmp_path / "obj.npy", "npy", {"y_true": "t"})
    (tmp_path / "p.csv").write_text("t\n0\n")
    with pytest.raises(RecomputeError):
        rc.read_predictions(tmp_path / "p.csv", "csv", {"y_true": "t", "y_pred": "p"})
    (tmp_path / "p.jsonl").write_text('{"t": 0, "s": NaN}\n')
    with pytest.raises(RecomputeError):
        rc.read_predictions(tmp_path / "p.jsonl", "jsonl", {"y_true": "t", "y_score": "s"})
    (tmp_path / "q.jsonl").write_text('{"t": 0, "p": 1}\n{"t": 1}\n')
    with pytest.raises(RecomputeError):
        rc.read_predictions(tmp_path / "q.jsonl", "jsonl", {"y_true": "t", "y_pred": "p"})
    with pytest.raises(RecomputeError):
        rc.read_predictions(tmp_path / "p.csv", "parquet", {"y_true": "t"})


# ---- the check over the runs ---------------------------------------------------------------


SEEDS = ["seed=1", "seed=2", "seed=3"]


def outcome(label, status, full=True):
    return rc.RunOutcome(label, status, "r", full)


def test_check_passes_only_when_every_expected_run_passes():
    r = rc.metric_recompute_result([outcome(s, TestStatus.PASS) for s in SEEDS], SEEDS)
    assert (r.name, r.status, r.coverage) == (METRIC_RECOMPUTE, TestStatus.PASS, 3)
    assert r.metrics[EXPECTED_COVERAGE] == 3 and r.metrics[FAILURE_ESTABLISHED] is False
    r = rc.metric_recompute_result([outcome(s, TestStatus.PASS) for s in SEEDS[:2]], SEEDS)
    assert r.status is TestStatus.INCONCLUSIVE


def test_one_valid_failure_establishes_the_failure():
    r = rc.metric_recompute_result(
        [outcome("seed=1", TestStatus.FAIL), outcome("seed=2", TestStatus.INCONCLUSIVE, False)],
        SEEDS,
    )
    assert r.status is TestStatus.FAIL and r.metrics[FAILURE_ESTABLISHED] is True
    assert r.coverage == 1


def test_an_unreadable_run_makes_the_check_inconclusive():
    r = rc.metric_recompute_result(
        [outcome("seed=1", TestStatus.PASS), outcome("seed=2", TestStatus.INCONCLUSIVE, False)],
        SEEDS[:2],
    )
    assert r.status is TestStatus.INCONCLUSIVE and r.coverage == 1


@pytest.mark.parametrize(
    "outcomes",
    [
        # one PASS repeated cannot stand for three runs
        [outcome("seed=1", TestStatus.PASS)] * 3,
        # a run that is not expected
        [outcome(s, TestStatus.PASS) for s in SEEDS] + [outcome("seed=9", TestStatus.FAIL)],
        # a decided outcome that was not recomputed in full
        [outcome("seed=1", TestStatus.FAIL, False), outcome("seed=2", TestStatus.PASS)],
        [outcome("seed=1", TestStatus.PASS, False)],
    ],
)
def test_outcomes_must_name_distinct_expected_runs_recomputed_in_full(outcomes):
    """Codex review of PR #81, blocker 3: the check counts runs, not outcomes."""
    with pytest.raises(ValueError):
        rc.metric_recompute_result(outcomes, SEEDS)


@pytest.mark.parametrize("expected", [[], ["seed=1", "seed=1"]])
def test_expected_runs_are_a_non_empty_list_of_distinct_labels(expected):
    with pytest.raises(ValueError):
        rc.metric_recompute_result([], expected)


# ---- numeric safety (Codex review of PR #81, blockers 1 and 2) -----------------------------


def test_integers_beyond_2_53_are_refused_not_collapsed():
    # 2**53 and 2**53 + 1 are the same 64-bit float: MAE would be 0 instead of 1 in both
    # implementations, and a printed "1.0" would look like a valid failure
    c = conv("mae", "native")
    big = data([2**53], [2**53 + 1])
    with pytest.raises(RecomputeError):
        rc.prepare(c, big)
    outcome_ = run(c, "1.0", big, 1, channel="native", unit="native")
    assert outcome_.status is TestStatus.INCONCLUSIVE
    numpy_ints = {
        "y_true": np.array([2**53], dtype=np.int64),
        "y_pred": np.array([2**53 + 1], dtype=np.int64),
    }
    with pytest.raises(RecomputeError):
        rc.prepare(c, numpy_ints)
    assert both(c, data([2**53], [2**53 - 1])) == (1.0, 1.0)  # distinct floats: exact


@pytest.mark.parametrize(
    ("y_true", "y_pred", "ok"),
    [
        ("0.1", "0.2", True),
        ("0.1000000000000000000001", "0", True),  # rounded, but nothing collides
        ("9007199254740992", "9007199254740993", False),  # 2**53 and 2**53 + 1
        ("1e-400", "0", False),  # underflows to zero
        ("0.1", "0.10000000000000001", False),  # two texts, one float
        (1.5, "1.5", True),  # equal values are not a collision
    ],
)
def test_conversion_must_keep_distinct_values_distinct(y_true, y_pred, ok):
    c = conv("mae", "native")
    d = data([y_true], [y_pred])
    if ok:
        rc.prepare(c, d)
    else:
        with pytest.raises(RecomputeError):
            rc.prepare(c, d)


def test_rounding_that_keeps_the_order_but_moves_a_distance_is_inconclusive():
    # Codex round 3: 2**53 + 1 rounds to 2**53 while 2**53 + 2 is exact; no collision and
    # no change of order, but the MAE becomes 2 instead of 1
    c = conv("mae", "native")
    d = data(["9007199254740993"], ["9007199254740994"])
    outcome_ = run(c, "1.0", d, 1, channel="native", unit="native")
    assert outcome_.status is TestStatus.INCONCLUSIVE and "rounding" in outcome_.reason


def test_rounding_of_the_arithmetic_with_exact_inputs_is_inconclusive():
    # Codex round 4: every input is exactly a float, but the mean of 1e16 and 1e16 + 2
    # rounds to 1e16, so the float r2 is 0 while the exact r2 is -1
    c = conv("r2", "native")
    d = data([10000000000000000, 10000000000000002], [10000000000000000, 10000000000000000])
    outcome_ = run(c, "-1.0", d, 2, channel="native", unit="native")
    assert outcome_.status is TestStatus.INCONCLUSIVE and "rounding" in outcome_.reason


@pytest.mark.parametrize("metric", ["mae", "mse", "rmse", "r2"])
def test_ordinary_regression_values_pass_the_exact_check(metric):
    y_true = ["3", "-0.5", "2", "7"]
    y_pred = ["2.5", "0.0", "2", "8"]
    c = conv(metric, "native")
    p = rc.prepare(c, data(y_true, y_pred))
    assert p.exact is not None  # every regression run is checked against exact arithmetic
    expected = {
        "mae": 0.5,
        "mse": 0.375,
        "rmse": math.sqrt(0.375),
        "r2": 1 - 1.5 / 29.1875,
    }[metric]
    token = repr(round(expected, 6))
    outcome_ = run(c, token, data(y_true, y_pred), 4, channel="native", unit="native")
    assert outcome_.status is TestStatus.PASS


def test_texts_that_are_not_floats_get_the_exact_check():
    c = conv("mae", "native")
    p = rc.prepare(c, data(["0.1", "0.2"], ["0.3", "0.2"]))
    assert p.exact is not None
    assert rc.exact_regression_metric("mae", *p.exact) == pytest.approx(0.1)
    outcome_ = run(
        c, "0.1", data(["0.1", "0.2"], ["0.3", "0.2"]), 2, channel="native", unit="native"
    )
    assert outcome_.status is TestStatus.PASS and "exact" in outcome_.details


@pytest.mark.parametrize(
    "scores",
    [
        ["0.1000000000000000000001", "0.1000000000000000000002"],
        ["1e-400", "2e-400"],  # both underflow: a tie would give AUROC 0.5 instead of 1
        ["0.1", "0.10000000000000001"],
    ],
)
def test_auroc_scores_that_would_tie_are_refused(scores):
    c = conv("auroc", labels=L01, pos_label=1)
    d = data([0, 1], scores, "y_score")
    with pytest.raises(RecomputeError):
        rc.prepare(c, d)
    assert run(c, "1.0", d, 2).status is TestStatus.INCONCLUSIVE


def test_jsonl_numbers_keep_their_text(tmp_path):
    (tmp_path / "p.jsonl").write_text('{"t": 9007199254740992.0, "p": 9007199254740993.0}\n')
    d = rc.read_predictions(tmp_path / "p.jsonl", "jsonl", {"y_true": "t", "y_pred": "p"})
    with pytest.raises(RecomputeError):
        rc.prepare(conv("mae", "native"), d)
    (tmp_path / "q.jsonl").write_text('{"t": 1.5, "p": 2}\n')
    d = rc.read_predictions(tmp_path / "q.jsonl", "jsonl", {"y_true": "t", "y_pred": "p"})
    assert both(conv("mae", "native"), d) == (0.5, 0.5)
    with pytest.raises(RecomputeError):  # a JSON float is never a class label
        rc.prepare(conv("accuracy", labels=L01), data([Decimal("1.0")], [1]))


def test_r2_of_equal_targets_is_undefined_whatever_the_rounding_of_the_mean():
    # three 0.1: the mean rounds to 0.10000000000000002 and the summed squares are ~6e-34,
    # which passed a "variance == 0" guard and gave r2 ~ -5e31
    c = conv("r2", "native")
    d = data([0.1, 0.1, 0.1], [0.2, 0.2, 0.2])
    p = rc.prepare(c, d)
    with pytest.raises(UndefinedMetricError):
        rc.own_metric(c, p)
    with pytest.raises(UndefinedMetricError):
        rc.sklearn_metric(c, p)
    outcome_ = run(c, "0.0", d, 3, channel="native", unit="native")
    assert outcome_.status is TestStatus.INCONCLUSIVE
