"""ML pack: the fetcher of declared datasets and weights (WP3 W3.6, W3.7), offline with a
fake opener (the suite runs with --disable-socket). Each failure goes through the WP2
core to show the verdict path of the data_present gate."""

import hashlib
import http.client
import io
import urllib.error
import urllib.request

import pytest

from refute.core.paper import FailureCause, aggregate_claim
from refute.core.verdict import PaperVerdict, Severity, TestResult, TestStatus
from refute.packs.ml import fetch as fe

DATA = b"synthetic dataset bytes\n" * 100
URL = "https://example.org/data.bin"


def spec(data=DATA):
    return fe.ArtifactSpec("data", URL, hashlib.sha256(data).hexdigest(), len(data))


class Response(io.BytesIO):
    status = 200


class Opener:
    """Answers each call with the next item: bytes (a 200 response), an int (an HTTP
    error with that code) or an exception instance (raised)."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = 0

    def __call__(self, url, timeout):
        self.calls += 1
        answer = self.answers.pop(0)
        if isinstance(answer, bytes):
            return Response(answer)
        if isinstance(answer, int):
            raise urllib.error.HTTPError(url, answer, "error", {}, None)
        raise answer


def fetch(tmp_path, opener, attempts=3, **kw):
    slept = []
    result = fe.fetch_artifact(
        kw.pop("spec", spec()),
        tmp_path / "cache",
        attempts=attempts,
        interval_s=60.0,
        opener=opener,
        sleep=slept.append,
        **kw,
    )
    return result, slept


def data_present_verdict(result):
    """The gate of a failed fetch: FAIL with zero examples (nothing was obtained) and, for
    a proven absence, the HTTP statuses of every attempt (Codex review: a fixed coverage
    of 1 would have counted an attempt as an example)."""
    gate = TestResult(
        "data_present",
        TestStatus.PASS if result.ok else TestStatus.FAIL,
        Severity.GATE,
        "fetch",
        metrics=fe.absence_evidence(result),
        coverage=1 if result.ok else 0,
        coverage_unit="examples",
    )
    base = [TestResult("environment_build", TestStatus.PASS, Severity.GATE, "ok", coverage=1), gate]
    failures = {"data_present": result.failure} if result.failure else None
    return aggregate_claim(base, [], [], metric_recompute_applies=False, failures=failures).verdict


def test_a_matching_download_is_verified_and_kept_by_its_hash(tmp_path):
    result, slept = fetch(tmp_path, Opener(DATA))
    assert result.ok and not result.from_cache and slept == []
    assert result.path.name == spec().sha256 and result.path.read_bytes() == DATA
    assert [a.outcome for a in result.attempts] == ["ok"]
    assert not list((tmp_path / "cache").glob("*.part"))


def test_a_verified_cache_is_used_without_the_network(tmp_path):
    fetch(tmp_path, Opener(DATA))
    opener = Opener()
    result, _ = fetch(tmp_path, opener)
    assert result.ok and result.from_cache and opener.calls == 0


def test_a_cached_file_that_does_not_match_is_never_overwritten(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / spec().sha256).write_bytes(b"something else")
    opener = Opener(DATA)
    result, _ = fetch(tmp_path, opener)
    assert not result.ok and opener.calls == 0
    assert result.failure.cause is FailureCause.UNDETERMINED
    assert (cache / spec().sha256).read_bytes() == b"something else"


def test_absent_in_every_attempt_is_the_artifact_absent_cause(tmp_path):
    result, slept = fetch(tmp_path, Opener(404, 410, 404))
    assert [a.http_status for a in result.attempts] == [404, 410, 404]
    assert slept == [60.0, 60.0]  # spaced by the interval fixed before the lock
    assert result.failure == fe.GateFailure(FailureCause.ARTIFACT_ABSENT, 3, 3)
    assert data_present_verdict(result) is PaperVerdict.NOT_REPRODUCIBLE


@pytest.mark.parametrize(
    "answers",
    [
        (404, 503, 404),
        (404, urllib.error.URLError("no route"), 404),
        (TimeoutError("timed out"), 404, 404),
        (http.client.IncompleteRead(b"x", 10), 404, 404),
        (403, 403, 403),
    ],
)
def test_any_other_failure_is_transient_and_never_absent(tmp_path, answers):
    result, _ = fetch(tmp_path, Opener(*answers))
    assert result.failure.cause is FailureCause.TRANSIENT_NETWORK
    assert data_present_verdict(result) is PaperVerdict.INCONCLUSIVE


def test_the_first_matching_download_ends_the_attempts(tmp_path):
    opener = Opener(404, 503, DATA)
    result, slept = fetch(tmp_path, opener, attempts=5)
    assert result.ok and opener.calls == 3 and len(slept) == 2


@pytest.mark.parametrize(
    ("served", "reason"),
    [
        (DATA[:-1], "bytes, not the declared"),
        (DATA + b"x", "more than the declared"),
        (DATA[:-1] + b"?", "not the locked"),
    ],
)
def test_other_bytes_stop_the_fetch_with_no_artifact_cause(tmp_path, served, reason):
    opener = Opener(served, DATA)
    result, _ = fetch(tmp_path, opener)
    assert opener.calls == 1 and reason in result.attempts[0].detail
    assert result.failure.cause is FailureCause.UNDETERMINED
    assert data_present_verdict(result) is PaperVerdict.INCONCLUSIVE
    assert not (tmp_path / "cache" / spec().sha256).exists()


def test_a_cache_that_cannot_be_written_is_a_refute_error(tmp_path, monkeypatch):
    def refuse(*args, **kwargs):
        raise PermissionError("read-only cache")

    monkeypatch.setattr(fe.tempfile, "mkstemp", refuse)
    result, _ = fetch(tmp_path, Opener(DATA))
    assert result.failure.cause is FailureCause.REFUTE_ERROR
    assert result.attempts[-1].outcome == fe.LOCAL_ERROR
    assert data_present_verdict(result) is PaperVerdict.INCONCLUSIVE


def test_a_cache_folder_that_cannot_be_created_is_a_refute_error(tmp_path):
    (tmp_path / "file").write_text("not a folder")
    result = fe.fetch_artifact(
        spec(), tmp_path / "file" / "cache", attempts=1, interval_s=1, opener=Opener(DATA)
    )
    assert result.failure.cause is FailureCause.REFUTE_ERROR


def test_a_failed_publication_is_a_refute_error(tmp_path, monkeypatch):
    def refuse(src, dst):
        raise PermissionError("no hard links here")

    monkeypatch.setattr(fe.os, "link", refuse)
    result, _ = fetch(tmp_path, Opener(DATA))
    assert result.failure.cause is FailureCause.REFUTE_ERROR
    assert not list((tmp_path / "cache").iterdir())  # no temporary file left


class Racing(Opener):
    """Another call publishes the final file while this one downloads (Codex review)."""

    def __init__(self, cache, published, *answers):
        super().__init__(*answers)
        self.cache, self.published = cache, published

    def __call__(self, url, timeout):
        (self.cache / spec().sha256).write_bytes(self.published)
        return super().__call__(url, timeout)


def test_a_file_published_meanwhile_is_used_only_if_it_matches(tmp_path):
    cache = tmp_path / "cache"
    cache.mkdir()
    same, _ = fetch(tmp_path, Racing(cache, DATA, DATA))
    assert same.ok and same.from_cache
    (cache / spec().sha256).unlink()
    other, _ = fetch(tmp_path, Racing(cache, b"other bytes", DATA))
    assert not other.ok and other.failure.cause is FailureCause.UNDETERMINED
    assert (cache / spec().sha256).read_bytes() == b"other bytes"  # never overwritten
    assert not list(cache.glob("*.part"))


def test_a_redirect_away_from_https_is_refused(tmp_path):
    opener = Opener(fe.RedirectRefusedError("redirect to 'http://x' refused: not https"), DATA)
    result, _ = fetch(tmp_path, opener)
    assert opener.calls == 1 and result.attempts[0].outcome == fe.REFUSED
    assert result.failure.cause is FailureCause.UNDETERMINED
    handler = fe._HttpsOnlyRedirect()
    request = urllib.request.Request(URL)
    with pytest.raises(fe.RedirectRefusedError):
        handler.redirect_request(request, None, 302, "Found", {}, "http://example.org/x")
    follow = handler.redirect_request(request, None, 302, "Found", {}, "https://cdn.example.org/x")
    assert follow.full_url == "https://cdn.example.org/x"


def test_the_url_that_answered_is_recorded(tmp_path):
    class Moved(Opener):
        def __call__(self, url, timeout):
            response = super().__call__(url, timeout)
            response.url = "https://cdn.example.org/data.bin"
            return response

    result, _ = fetch(tmp_path, Moved(DATA))
    assert result.attempts[0].url == "https://cdn.example.org/data.bin"


@pytest.mark.parametrize(
    "bad",
    [
        dict(url="http://example.org/x"),
        dict(sha256="ABC"),
        dict(size_bytes=0),
    ],
)
def test_invalid_specs_are_refused(bad):
    values = dict(name="d", url=URL, sha256="a" * 64, size_bytes=1)
    values.update(bad)
    with pytest.raises(ValueError):
        fe.ArtifactSpec(**values)


def test_attempts_and_interval_are_required(tmp_path):
    with pytest.raises(ValueError, match="attempts"):
        fetch(tmp_path, Opener(), attempts=0)
    with pytest.raises(ValueError, match="interval"):
        fe.fetch_artifact(spec(), tmp_path, attempts=1, interval_s=0, opener=Opener())
