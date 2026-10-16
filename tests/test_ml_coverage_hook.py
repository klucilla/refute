"""The observation hook of coverage route (b) (wp3-acceptance.md, 1.5a, W3.12c): it is
observation only, it runs no code of the objects it does not know, and a failure of its
own never changes the call (offline)."""

import hashlib
import sys

import numpy as np
import pytest

from refute.core.canonical import canonical_bytes
from refute.packs.ml.coverage_hook import COMMITTED, HOOK_FAILURE, committed_events, observe

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


def test_the_hook_returns_exactly_the_original_object_and_passes_the_same_arguments():
    y_true, y_pred = [0, 1, 1, 0], [0, 1, 0, 0]
    records = []
    returned = observe(accuracy, records.append, NAME)(y_true, y_pred, normalize=True)
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
def test_the_value_is_identical_with_and_without_the_hook(args):
    without = plain(*args)
    with_hook = observe(plain, lambda record: None, NAME)(*args)
    assert type(with_hook) is type(without) and repr(with_hook) == repr(without)


def test_a_committed_event_records_the_declared_name_count_hash_and_value():
    y_true = [2, 0, 1, 1]
    records = []
    observe(plain, records.append, NAME)(y_true, [2, 0, 1, 0])
    events, failures = committed_events(records)
    assert failures == [] and len(events) == 1
    event = events[0]
    assert event["function"] == NAME  # the declared public name, compared with the claim
    assert event["n_examples"] == 4
    assert event["labels_sha256"] == hashlib.sha256(canonical_bytes(y_true)).hexdigest()
    assert event["result"] == repr(0.75)
    assert event["call_site"]["file"].endswith("test_ml_coverage_hook.py")
    assert records[1] == {COMMITTED: 1}


@pytest.mark.parametrize(
    "y_true",
    [["cat", "dog", "Ångström"], np.array([4, 4, 2]), (0, 1, 2)],
)
def test_labels_hash_like_refute_canonical_json(y_true):
    records = []
    observe(lambda t, p: 1.0, records.append, NAME)(y_true, y_true)
    (event,), _ = committed_events(records)
    expected = list(y_true.tolist()) if isinstance(y_true, np.ndarray) else list(y_true)
    assert event["labels_sha256"] == hashlib.sha256(canonical_bytes(expected)).hexdigest()


class Watched(list):
    """A list subclass whose protocols count their calls: the hook must run none."""

    calls = 0

    def __iter__(self):
        Watched.calls += 1
        return super().__iter__()

    def __len__(self):
        Watched.calls += 1
        return super().__len__()

    def __getattr__(self, name):
        Watched.calls += 1
        raise AttributeError(name)


def test_an_unknown_argument_type_is_refused_without_running_its_code():
    labels = Watched([0, 1, 1])
    Watched.calls = 0
    records = []
    returned = observe(lambda t, p: 0.5, records.append, NAME)(labels, labels)
    assert returned == 0.5
    assert Watched.calls == 0  # neither __iter__, __len__ nor any attribute ran
    events, failures = committed_events(records)
    assert events == [] and len(failures) == 1 and "Watched" in failures[0]


def test_an_iterator_is_never_read():
    def first(y_true, y_pred):
        return next(y_true)

    records = []
    labels = iter([7, 8, 9])
    assert observe(first, records.append, NAME)(labels, None) == 7
    assert list(labels) == [8, 9]  # the hook took nothing from it
    _, failures = committed_events(records)
    assert failures and "are not read" in failures[0]


def test_the_result_repr_never_runs_for_an_unknown_type():
    Result.repr_calls = 0
    records = []
    returned = observe(accuracy, records.append, NAME)([0, 1], [0, 1])
    assert returned is accuracy.last and Result.repr_calls == 0
    (event,), failures = committed_events(records)
    assert failures == [] and event["result_type"] == "Result" and "result" not in event


def test_a_sink_that_writes_then_fails_leaves_an_uncommitted_event():
    """The commit protocol: the event the sink wrote before failing has no commit record,
    so the gate counts a failure (INCONCLUSIVE), and the call is unchanged."""
    written = []

    def sink(record):
        written.append(record)
        raise OSError("disk full")

    returned = observe(accuracy, sink, NAME)([0, 1], [0, 1])
    assert returned is accuracy.last
    events, failures = committed_events(written)
    assert events == [] and failures == ["event 1 without its commit record"]


def test_a_failure_of_getframe_is_recorded_and_the_call_is_unchanged(monkeypatch):
    def broken(depth=0):
        raise RuntimeError("no frame")

    records = []
    wrapped = observe(accuracy, records.append, NAME)
    monkeypatch.setattr(sys, "_getframe", broken)
    returned = wrapped([0, 1], [0, 1])
    monkeypatch.undo()
    assert returned is accuracy.last
    _, failures = committed_events(records)
    assert failures == ["hook failure: RuntimeError: no frame"]


class OddCallable:
    """A callable whose metadata cannot be copied by functools.wraps."""

    def __call__(self, y_true, y_pred):
        return 1.0

    @property
    def __module__(self):  # noqa: PLW3201 - a deliberately broken attribute
        raise RuntimeError("broken metadata")


def test_metadata_that_cannot_be_copied_never_stops_the_installation():
    wrapped = observe(OddCallable(), lambda record: None, NAME)
    assert wrapped([0], [0]) == 1.0


def test_the_function_s_own_exception_propagates_unchanged():
    error = ValueError("bad input")

    def failing(y_true, y_pred):
        raise error

    records = []
    with pytest.raises(ValueError) as caught:
        observe(failing, records.append, NAME)([0], [0])
    assert caught.value is error and records == []


def test_an_interrupt_during_the_hook_s_work_is_not_swallowed():
    """The policy for BaseException: an interrupt while the hook records is an
    interruption of the run, not a hook fault; the observed call had already returned."""

    def sink(record):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        observe(accuracy, sink, NAME)([0, 1], [0, 1])
    assert accuracy.seen[0] == [0, 1]


def test_a_commit_without_its_event_is_a_failure():
    assert committed_events([{COMMITTED: 3}]) == ([], ["a commit record with no event: 3"])
    assert committed_events([{"seq": 1, HOOK_FAILURE: "x"}, {COMMITTED: 1}]) == (
        [],
        ["hook failure: x"],
    )
