"""The observation hook of coverage route (b) (wp3-acceptance.md, 1.5a, W3.12c): it is
observation only, and a failure of its own never changes the call (offline)."""

import hashlib

import pytest

from refute.core.canonical import canonical_bytes
from refute.packs.ml.coverage_hook import HOOK_FAILURE, observe


class Result:
    """A return value whose identity can be checked."""


def accuracy(y_true, y_pred, **kwargs):
    """A synthetic metric function: it records the objects it received and returns a fresh
    object each call, plus the plain value."""
    accuracy.seen = (y_true, y_pred, kwargs)
    value = sum(a == b for a, b in zip(y_true, y_pred, strict=True)) / len(y_true)
    accuracy.last = Result()
    accuracy.last.value = value
    return accuracy.last


def test_the_hook_returns_exactly_the_original_return_and_passes_the_same_arguments():
    y_true, y_pred = [0, 1, 1, 0], [0, 1, 0, 0]
    events = []
    wrapped = observe(accuracy, events.append)
    returned = wrapped(y_true, y_pred, normalize=True)
    assert returned is accuracy.last  # the very object the function returned
    seen_true, seen_pred, kwargs = accuracy.seen
    assert seen_true is y_true and seen_pred is y_pred and kwargs == {"normalize": True}
    assert y_true == [0, 1, 1, 0] and y_pred == [0, 1, 0, 0]  # nothing was changed


def test_the_value_is_identical_with_and_without_the_hook():
    """The same call with and without the hook gives the same value, of the same type."""

    def plain(y_true, y_pred):
        return sum(a == b for a, b in zip(y_true, y_pred, strict=True)) / len(y_true)

    args = ([0, 1, 1, 0, 2], [0, 1, 0, 0, 2])
    without = plain(*args)
    with_hook = observe(plain, lambda event: None)(*args)
    assert type(with_hook) is type(without) and repr(with_hook) == repr(without)
    assert with_hook == without


def test_the_event_records_the_count_and_the_canonical_labels_hash():
    y_true = [2, 0, 1, 1]
    events = []
    observe(accuracy, events.append)(y_true, [2, 0, 1, 0])
    (event,) = events
    assert event["n_examples"] == 4
    assert event["labels_sha256"] == hashlib.sha256(canonical_bytes(y_true)).hexdigest()
    assert event["function"].endswith("accuracy")
    assert event["call_site"]["file"].endswith("test_ml_coverage_hook.py")
    assert event["result"] == repr(accuracy.last)


def test_string_labels_hash_like_refute_canonical_json():
    y_true = ["cat", "dog", "Ångström"]
    events = []
    observe(lambda t, p: 1.0, events.append)(y_true, y_true)
    assert events[0]["labels_sha256"] == hashlib.sha256(canonical_bytes(y_true)).hexdigest()


def test_an_iterator_is_never_read_and_the_failure_is_recorded():
    """Reading a generator would consume it: the hook leaves it alone and records a
    failure (the gate is then INCONCLUSIVE); the function's own result is unchanged."""

    def first(y_true, y_pred):
        return next(y_true)

    events = []
    labels = iter([7, 8, 9])
    assert observe(first, events.append)(labels, None) == 7
    assert list(labels) == [8, 9]  # the hook took nothing from it
    assert HOOK_FAILURE in events[0] and "iterator" in events[0][HOOK_FAILURE]


def test_labels_the_hook_cannot_read_give_a_failure_record_not_a_changed_call():
    events = []
    weird = [object(), object()]
    returned = observe(accuracy, events.append)(weird, weird)
    assert returned is accuracy.last
    assert HOOK_FAILURE in events[0]


def test_a_failing_sink_leaves_no_event_and_the_call_unchanged():
    def sink(event):
        raise OSError("disk full")

    returned = observe(accuracy, sink)([0, 1], [0, 1])
    assert returned is accuracy.last


def test_the_function_s_own_exception_propagates_unchanged():
    error = ValueError("bad input")

    def failing(y_true, y_pred):
        raise error

    events = []
    with pytest.raises(ValueError) as caught:
        observe(failing, events.append)([0], [0])
    assert caught.value is error
    assert events == []
