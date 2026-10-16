"""The observation hook of coverage route (b) (wp3-acceptance.md, 1.5a, W3.12c): it is
observation only, it runs no code of objects it does not trust, and the records let the
gate see any failure of its own (offline)."""

import hashlib
import sys
import threading
import types

import numpy as np
import pytest

from refute.core.canonical import canonical_bytes
from refute.packs.ml.coverage_hook import (
    _NUMPY_NUMBERS,
    COMMITTED,
    FINAL,
    HOOK_FAILURE,
    Observer,
    _trusted_numpy,
    committed_events,
    file_sink,
    read_log,
    record_line,
)


def final_for(records, calls, failed=False):
    """The final record the hook would write after these records."""
    digest = hashlib.sha256(b"".join(record_line(r) for r in records)).hexdigest()
    return {FINAL: {"calls": calls, "failed": failed, "records_sha256": digest}}


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
    observer = Observer(records.append)
    with pytest.raises(ValueError) as caught:
        observer.wrap(failing, NAME)([0], [0])
    assert caught.value is error and records == []
    finisher = threading.Thread(target=observer.finish)
    finisher.start()
    finisher.join(5)
    assert not finisher.is_alive()  # the raising call is no longer counted as in progress
    assert records == [final_for([], 0)]


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
    assert records[1] == {COMMITTED: 1} and records[2] == final_for(records[:2], 1)


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
    assert events == [] and failures == [
        "the final record does not match the log: calls 1, failed True, digest equal"
    ]


def test_a_sink_that_fails_after_writing_the_final_record_leaves_a_valid_log():
    """Judged by content: the log is complete and matches its digest, so the exception the
    sink raised after the last write changes nothing in the evidence."""
    written = []

    def sink(record):
        written.append(record)
        if FINAL in record:
            raise OSError("close failed")

    run(plain, [0, 1], [0, 1], sink=sink)
    events, failures = committed_events(written)
    assert failures == [] and len(events) == 1


def test_a_log_written_in_part_does_not_match_its_digest():
    written = []

    def sink(record):
        if COMMITTED in record:  # the commit record never reaches the log
            raise OSError("disk full")
        written.append(record)

    run(plain, [0, 1], [0, 1], sink=sink)
    _, failures = committed_events(written)
    assert "event 1 without its commit record" in failures
    assert any("digest different" in f for f in failures)


def test_finish_waits_for_a_call_in_progress():
    """A call still inside the sink when finish() starts is counted, and its failure is
    reported: finish() waits until no call is in progress."""
    written = []
    inside = threading.Event()
    release = threading.Event()

    def sink(record):
        written.append(record)
        if COMMITTED in record:
            inside.set()
            release.wait(5)
            raise OSError("late failure")

    observer = Observer(sink)
    wrapped = observer.wrap(plain, NAME)
    worker = threading.Thread(target=wrapped, args=([0, 1], [0, 1]))
    worker.start()
    assert inside.wait(5)
    finisher = threading.Thread(target=observer.finish)
    finisher.start()
    finisher.join(0.2)
    assert finisher.is_alive()  # waiting for the call in progress
    release.set()
    worker.join(5)
    finisher.join(5)
    assert written[-1][FINAL]["failed"] is True
    _, failures = committed_events(written)
    assert failures


def test_finish_waits_for_a_call_still_inside_the_observed_function():
    """A call is counted from its entry into the wrapper, so finish() also waits for a
    call that has not yet returned from the observed function, and the final record
    counts it."""
    written = []
    inside = threading.Event()
    release = threading.Event()

    def slow(y_true, y_pred):
        inside.set()
        release.wait(5)
        return 0.5

    observer = Observer(written.append)
    worker = threading.Thread(target=observer.wrap(slow, NAME), args=([0, 1], [0, 1]))
    worker.start()
    assert inside.wait(5)
    finisher = threading.Thread(target=observer.finish)
    finisher.start()
    finisher.join(0.2)
    assert finisher.is_alive()  # waiting for the call inside the function
    release.set()
    worker.join(5)
    finisher.join(5)
    events, failures = committed_events(written)
    assert failures == [] and len(events) == 1 and written[-1][FINAL]["calls"] == 1


def test_a_call_after_finish_is_written_after_the_final_record_and_refused():
    """finish() closes the observer: a second finish() writes nothing, and a later call is
    still observed, unchanged, with its records after the final record, which the gate
    refuses."""
    records = []
    observer = Observer(records.append)
    wrapped = observer.wrap(plain, NAME)
    wrapped([0, 1], [0, 1])
    observer.finish()
    observer.finish()
    assert [FINAL in r for r in records] == [False, False, True]
    assert wrapped([0, 1], [0, 0]) == 0.5
    events, failures = committed_events(records)
    assert events == [] and "record 3 after the final record" in failures


def test_a_compiled_type_of_another_module_under_numpy_s_name_is_not_trusted(monkeypatch):
    """A numpy module whose ndarray is a compiled type of another module (here the type
    of Python functions) does not make a function argument trusted labels: neither its
    ndim nor its tolist is read."""

    def labels():
        return None

    def tolist():
        Counted.calls += 1
        return [0, 1]

    labels.ndim = 1
    labels.tolist = tolist
    fake = types.ModuleType("numpy")
    fake.ndarray = types.FunctionType
    monkeypatch.setitem(sys.modules, "numpy", fake)
    Counted.calls = 0
    returned, records = run(lambda t, p: 0.5, labels, labels)
    monkeypatch.undo()
    assert returned == 0.5 and Counted.calls == 0
    events, failures = committed_events(records)
    assert events == [] and "hook failure 1: labels of an unread type" in failures


def test_numpy_s_own_types_are_trusted():
    """Every numpy type the hook reads is trusted with the real numpy, on each platform of
    CI, so a renamed type shows here instead of silently reading as unread."""
    assert _trusted_numpy("ndarray") == (np.ndarray,)
    assert _trusted_numpy(*_NUMPY_NUMBERS) == tuple(getattr(np, n) for n in _NUMPY_NUMBERS)


@pytest.mark.parametrize(
    "y_true",
    [np.array(5), np.array([[0, 1], [1, 0]]), np.array([0, 1], dtype=object)],
    ids=["0-d", "2-d", "object-1d"],
)
def test_numpy_labels_must_be_a_one_dimensional_array_of_int_or_str(y_true):
    _, records = run(lambda t, p: 1.0, y_true, y_true)
    events, failures = committed_events(records)
    if y_true.ndim == 1:
        # a 1-D object array of Python ints is read like a list of ints
        assert failures == [] and events[0]["n_examples"] == 2
    else:
        assert events == [] and failures


def test_a_zero_d_object_array_never_runs_the_object_it_holds():
    class Inner:
        def __iter__(self):
            Counted.calls += 1
            return iter([0, 1])

        def __len__(self):
            Counted.calls += 1
            return 2

    Counted.calls = 0
    holder = np.empty((), dtype=object)
    holder[()] = Inner()
    _, records = run(lambda t, p: 1.0, holder, holder)
    assert Counted.calls == 0
    _, failures = committed_events(records)
    assert failures


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
    "result": "0.5",
}
COMMIT = {COMMITTED: 1}
GOOD = [EVENT, COMMIT]
BAD_EVENT = {
    "seq": 1,
    "function": None,
    "call_site": None,
    "n_examples": -1,
    "labels_sha256": "x",
    "result": "0.5",
}


def with_final(records, calls=1):
    return [*records, final_for(records, calls)]


@pytest.mark.parametrize(
    ("records", "reason"),
    [
        (with_final([EVENT]), "event 1 without its commit record"),
        (with_final([COMMIT], 0), "a commit record without its event before it"),
        (with_final([COMMIT, EVENT]), "a commit record without its event before it"),
        (
            with_final([{"seq": 1, HOOK_FAILURE: "x"}, EVENT, COMMIT]),
            "record 1: a sequence number repeated",
        ),
        (with_final([{"seq": 1}, COMMIT]), "not an event as the hook writes it"),
        (with_final([BAD_EVENT, COMMIT]), "not an event as the hook writes it"),
        (with_final([dict(EVENT, extra=1), COMMIT]), "not an event as the hook writes it"),
        (with_final([dict(EVENT, seq=2), {COMMITTED: 2}]), "not 1 to n"),
        (GOOD, "no final record"),
        ([*GOOD, {FINAL: None}], "the final record is malformed"),
        ([*GOOD, {FINAL: {"calls": 1, "failed": 0, "records_sha256": "0" * 64}}], "malformed"),
        ([*with_final(GOOD), EVENT], "after the final record"),
        (with_final(GOOD, 2), "the final record does not match the log: calls 2"),
        ([EVENT, COMMIT, final_for([EVENT], 1)], "digest different"),
    ],
    ids=[
        "uncommitted",
        "commit-without-event",
        "commit-before-event",
        "duplicate-seq",
        "incomplete",
        "bad-types",
        "extra-field",
        "gap",
        "no-final",
        "final-null",
        "final-types",
        "after-final",
        "final-count",
        "digest",
    ],
)
def test_the_gate_parser_refuses_every_malformed_or_partial_record_set(records, reason):
    events, failures = committed_events(records)
    assert events == [] and any(reason in f for f in failures), failures


def test_a_complete_record_set_is_accepted():
    events, failures = committed_events(with_final(GOOD))
    assert failures == [] and events == [EVENT]


# ---- the log on disk (installation and reading) --------------------------------------------------


def test_a_file_log_reads_back_to_the_records_the_gate_accepts(tmp_path):
    path = str(tmp_path / "refute-hook" / "coverage.jsonl")
    observer = Observer(file_sink(path))
    observer.wrap(plain, NAME)([0, 1, 1], [0, 1, 0])
    observer.finish()
    records, failures = read_log((tmp_path / "refute-hook" / "coverage.jsonl").read_bytes())
    assert failures == []
    events, failures = committed_events(records)
    assert failures == [] and events[0]["n_examples"] == 3


@pytest.mark.parametrize(
    ("data", "reason"),
    [
        (b"", "empty"),
        (b'{"committed":1}', "cut short"),
        (b'{"seq":1,"seq":2}\n', "line 1"),
        (b'{"x":NaN}\n', "line 1"),
        (b"\xff\n", "line 1"),
        (b'{"committed":1}\nnot json\n', "line 2"),
    ],
    ids=["empty", "cut-short", "repeated-key", "nan", "not-utf8", "not-json"],
)
def test_a_malformed_log_is_a_failure(data, reason):
    records, failures = read_log(data)
    assert records == [] and any(reason in f for f in failures), failures
