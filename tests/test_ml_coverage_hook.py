"""The observation hook of coverage route (b) (wp3-acceptance.md, 1.5a, W3.12c): it is
observation only, it runs no code of objects it does not trust, and the records let the
gate see any failure of its own (offline)."""

import hashlib
import sys

import numpy as np
import pytest

from refute.core.canonical import canonical_bytes
from refute.packs.ml.coverage_hook import (
    COMMITTED,
    FINAL,
    HOOK_FAILURE,
    Observer,
    committed_events,
)

NAME = "sklearn.metrics.accuracy_score"


class Result:
    """A return value whose identity, and whose untouched repr, can be checked."""

    repr_calls = 0

    def __repr__(self):
        Result.repr_calls += 1
        return "Result()"


def accuracy(y_true, y_pred, **kwargs):
    """A synthetic metric function: it records the objects it received and returns a fresh
    object each call."""
    accuracy.seen = (y_true, y_pred, kwargs)
    accuracy.last = Result()
    return accuracy.last


def plain(y_true, y_pred):
    return sum(a == b for a, b in zip(y_true, y_pred, strict=True)) / len(y_true)


def run(function, *args, sink=None, **kwargs):
    """One observed call and the final record; returns (result, records)."""
    records = []
    observer = Observer(sink or records.append)
    result = observer.wrap(function, NAME)(*args, **kwargs)
    observer.finish()
    return result, records


# ---- the call is unchanged -------------------------------------------------------------------


def test_the_hook_returns_exactly_the_original_object_and_passes_the_same_arguments():
    """Identity: the returned object is the very one the function returned, and the
    function received the very argument objects, unchanged."""
    y_true, y_pred = [0, 1, 1, 0], [0, 1, 0, 0]
    returned, _ = run(accuracy, y_true, y_pred, normalize=True)
    assert returned is accuracy.last
    seen_true, seen_pred, kwargs = accuracy.seen
    assert seen_true is y_true and seen_pred is y_pred and kwargs == {"normalize": True}
    assert y_true == [0, 1, 1, 0] and y_pred == [0, 1, 0, 0]


@pytest.mark.parametrize(
    "args",
    [
        ([0, 1, 1, 0, 2], [0, 1, 0, 0, 2]),
        ((3, 3, 1), (3, 2, 1)),
        (np.array([0, 1, 1]), np.array([0, 1, 0])),
    ],
)
def test_the_value_is_the_same_with_and_without_the_hook(args):
    """Value: the same call with and without the hook gives a value of the same type and
    the same text, for a list, a tuple and a numpy array."""
    without = plain(*args)
    with_hook, _ = run(plain, *args)
    assert type(with_hook) is type(without) and repr(with_hook) == repr(without)


def test_the_function_s_own_exception_propagates_unchanged():
    error = ValueError("bad input")

    def failing(y_true, y_pred):
        raise error

    records = []
    with pytest.raises(ValueError) as caught:
        Observer(records.append).wrap(failing, NAME)([0], [0])
    assert caught.value is error and records == []


# ---- what is recorded ------------------------------------------------------------------------


def test_a_committed_event_records_the_declared_name_count_hash_and_value():
    y_true = [2, 0, 1, 1]
    _, records = run(plain, y_true, [2, 0, 1, 0])
    events, failures = committed_events(records)
    assert failures == [] and len(events) == 1
    event = events[0]
    assert event["function"] == NAME  # the declared public name, compared with the claim
    assert event["n_examples"] == 4
    assert event["labels_sha256"] == hashlib.sha256(canonical_bytes(y_true)).hexdigest()
    assert event["result"] == repr(0.75)
    assert event["call_site"]["file"].endswith("test_ml_coverage_hook.py")
    assert records[1] == {COMMITTED: 1} and records[2] == {FINAL: {"calls": 1, "failed": False}}


@pytest.mark.parametrize("y_true", [["cat", "dog", "Ångström"], np.array([4, 4, 2]), (0, 1, 2)])
def test_labels_hash_like_refute_canonical_json(y_true):
    _, records = run(lambda t, p: 1.0, y_true, y_true)
    (event,), failures = committed_events(records)
    expected = y_true.tolist() if isinstance(y_true, np.ndarray) else list(y_true)
    assert failures == []
    assert event["labels_sha256"] == hashlib.sha256(canonical_bytes(expected)).hexdigest()


def test_a_numpy_result_is_read_through_numpy_itself():
    _, records = run(lambda t, p: np.float64(0.5), [0, 1], [0, 1])
    (event,), _ = committed_events(records)
    assert event["result"] == "0.5"


# ---- no code of an untrusted object runs -------------------------------------------------------


class Counted:
    calls = 0


class EqMeta(type):
    """A metaclass whose comparison and attribute protocols count their calls."""

    def __eq__(cls, other):
        Counted.calls += 1
        return True

    __hash__ = type.__hash__

    def __getattribute__(cls, name):
        if name not in ("__flags__", "__mro__", "__dict__", "__class__"):
            Counted.calls += 1
        return super().__getattribute__(name)


class Sneaky(metaclass=EqMeta):
    def __iter__(self):
        Counted.calls += 1
        return iter([0, 1])

    def __len__(self):
        Counted.calls += 1
        return 2


class FakeArray:
    """A class that only calls itself numpy.ndarray."""

    def tolist(self):
        Counted.calls += 1
        return [0, 1]


FakeArray.__module__ = "numpy"
FakeArray.__name__ = FakeArray.__qualname__ = "ndarray"


class Watched(list):
    def __iter__(self):
        Counted.calls += 1
        return super().__iter__()


@pytest.mark.parametrize(
    "labels",
    [Sneaky(), FakeArray(), Watched([0, 1]), [Sneaky(), 1], iter([7, 8])],
    ids=["metaclass", "fake-numpy", "list-subclass", "untrusted-element", "iterator"],
)
def test_untrusted_labels_are_refused_without_running_their_code(labels):
    Counted.calls = 0
    returned, records = run(lambda t, p: 0.5, labels, labels)
    assert returned == 0.5
    assert Counted.calls == 0  # no __eq__, attribute, __iter__, __len__ or tolist ran
    events, failures = committed_events(records)
    assert events == [] and failures


def test_a_fake_numpy_scalar_result_is_not_read():
    class FakeScalar:
        def item(self):
            Counted.calls += 1
            return 0.5

    FakeScalar.__module__ = "numpy"
    FakeScalar.__name__ = FakeScalar.__qualname__ = "float64"
    Counted.calls = 0
    value = FakeScalar()
    returned, records = run(lambda t, p: value, [0, 1], [0, 1])
    assert returned is value and Counted.calls == 0
    (event,), _ = committed_events(records)
    assert event["result"] == "unread"


def test_the_result_repr_never_runs_for_an_unknown_type():
    Result.repr_calls = 0
    returned, records = run(accuracy, [0, 1], [0, 1])
    assert returned is accuracy.last and Result.repr_calls == 0
    (event,), failures = committed_events(records)
    assert failures == [] and event["result"] == "unread"


# ---- every failure reaches the gate -------------------------------------------------------------


def test_a_sink_that_writes_then_fails_is_reported_by_the_final_record():
    written = []

    def sink(record):
        written.append(record)
        if COMMITTED in record:
            raise OSError("disk full")  # after the commit record was written

    returned, _ = run(accuracy, [0, 1], [0, 1], sink=sink)
    assert returned is accuracy.last
    events, failures = committed_events(written)
    assert events == [] and failures == ["the final record reports {'calls': 1, 'failed': True}"]


def test_a_failure_of_getframe_is_recorded_and_the_call_is_unchanged(monkeypatch):
    def broken(depth=0):
        raise RuntimeError("no frame")

    records = []
    observer = Observer(records.append)
    wrapped = observer.wrap(accuracy, NAME)
    monkeypatch.setattr(sys, "_getframe", broken)
    returned = wrapped([0, 1], [0, 1])
    monkeypatch.undo()
    observer.finish()
    assert returned is accuracy.last
    _, failures = committed_events(records)
    assert "hook failure 1: the hook could not read the call" in failures


class OddCallable:
    def __call__(self, y_true, y_pred):
        return 1.0

    @property
    def __module__(self):  # noqa: PLW3201 - a deliberately broken attribute
        raise RuntimeError("broken metadata")


def test_metadata_that_cannot_be_copied_never_stops_the_installation():
    assert Observer(lambda record: None).wrap(OddCallable(), NAME)([0], [0]) == 1.0


def test_an_interrupt_during_the_hook_s_work_is_not_swallowed():
    def sink(record):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        Observer(sink).wrap(accuracy, NAME)([0, 1], [0, 1])
    assert accuracy.seen[0] == [0, 1]


EVENT = {
    "seq": 1,
    "function": NAME,
    "call_site": {"file": "x.py", "line": 1},
    "n_examples": 2,
    "labels_sha256": "0" * 64,
}
FINAL_OK = {FINAL: {"calls": 1, "failed": False}}


@pytest.mark.parametrize(
    ("records", "reason"),
    [
        ([EVENT, FINAL_OK], "event 1 without its commit record"),
        ([{COMMITTED: 1}, FINAL_OK], "a commit record with no event: 1"),
        (
            [{"seq": 1, HOOK_FAILURE: "x"}, EVENT, {COMMITTED: 1}, FINAL_OK],
            "record 1: a sequence number repeated",
        ),
        ([{"seq": 1}, {COMMITTED: 1}, FINAL_OK], "event 1 is incomplete"),
        ([EVENT, {COMMITTED: 1}], "no final record"),
        ([EVENT, {COMMITTED: 1}, FINAL_OK, EVENT], "after the final record"),
        ([EVENT, {COMMITTED: 1}, {FINAL: {"calls": 2, "failed": False}}], "final record reports"),
    ],
    ids=[
        "uncommitted",
        "commit-without-event",
        "duplicate-seq",
        "incomplete",
        "no-final",
        "after-final",
        "final-count",
    ],  # fmt: skip
)
def test_the_gate_parser_refuses_every_malformed_or_partial_record_set(records, reason):
    events, failures = committed_events(records)
    assert events == [] and any(reason in f for f in failures), failures


def test_a_complete_record_set_is_accepted():
    events, failures = committed_events([EVENT, {COMMITTED: 1}, FINAL_OK])
    assert failures == [] and events == [EVENT]
