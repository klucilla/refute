"""Fetcher of the declared datasets and model weights of an ML paper (WP3 W3.6, W3.7).

Plan section 6.1 (docs/plans/v0.3-plan.md, lines 365-368 and 390-392): "Declared
datasets and model weights are downloaded by Refute's own fetcher, not by repository
code, and hashed before any repository code runs." Each artifact of the resolved claim
(``test_plan.datasets`` and ``test_plan.weights``) has a URL, a SHA-256 and a size; the
fetched bytes must match both.

**Network only here, in one explicit call** (W3.7): ``fetch_artifact`` opens the URL
through the ``opener`` it is given, by default ``https_opener()``: urllib with redirects
followed only to ``https`` URLs. Nothing else in the pack touches the network, and the
tests pass a fake opener (the suite runs with ``--disable-socket``).

**Attribution** (plan section 8.2, lines 675-676): "a declared artifact answers as
absent (for example HTTP 404 or 410) in all of the N attempts fixed before the lock,
spaced by an interval fixed before the lock" is a failure of the artifact
(``artifact_absent``). Here:

- an attempt answered with HTTP 404 or 410 is ``absent``;
- any other HTTP error, a connection error, a timeout or a cut transfer is
  ``transient``;
- bytes of another SHA-256 or size are a ``mismatch``: the artifact at the URL is not
  the one locked; the fetch stops, and the cause is ``undetermined`` (never an artifact
  cause: Refute cannot tell a changed host from a wrong record);
- a redirect to a URL that is not ``https`` is ``refused``; the fetch stops, cause
  ``undetermined``;
- a failure of the cache folder or file (create, read, write, close, publish) is a
  Refute error (``refute_error``); the fetch stops.

Every attempt records the URL that answered (after redirects). ``attempts`` and
``interval_s`` come from ``test_plan.absent_artifact`` (fixed before the lock). The
fetch succeeds at the first matching download. It fails with ``artifact_absent`` only
when **every** one of the N attempts was ``absent``; with any ``transient`` attempt and
no success the cause is ``transient_network``. The URL itself is part of the locked
claim, approved before the lock with its reference; a 404 caused by a wrong transcription
is guarded by that approval, not by this module.

**Cache.** Each call writes to its own new temporary file in the cache folder, hashes the
bytes while it writes them, and publishes the file under its SHA-256 by a hard link,
which fails when the name already exists: an existing file is never overwritten, and two
calls for the same hash cannot publish each other's bytes. A file already in the cache
with the right hash and size is used without opening the network.
"""

from __future__ import annotations

import hashlib
import http.client
import os
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from refute.core.paper import ABSENT_HTTP_STATUSES, ABSENT_STATUSES, FailureCause, GateFailure

ABSENT_STATUS = ABSENT_STATUSES  # 404 and 410, the same set the WP2 core accepts
CHUNK = 1 << 20
TIMEOUT_S = 60.0

OK, ABSENT, TRANSIENT, MISMATCH = "ok", "absent", "transient", "mismatch"
REFUSED = "refused"  # a redirect away from https
LOCAL_ERROR = "refute_error"  # the cache could not be created, read, written or published


@dataclass(frozen=True)
class ArtifactSpec:
    name: str
    url: str
    sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        if not self.url.startswith("https://"):
            raise ValueError(f"{self.name}: only https URLs are fetched")
        if len(self.sha256) != 64 or any(c not in "0123456789abcdef" for c in self.sha256):
            raise ValueError(f"{self.name}: sha256 is 64 lowercase hex digits")
        if type(self.size_bytes) is not int or self.size_bytes < 1:
            raise ValueError(f"{self.name}: size_bytes is a positive integer")


@dataclass(frozen=True)
class FetchAttempt:
    number: int
    outcome: str  # ok, absent, transient, mismatch, refused or refute_error
    http_status: int | None
    url: str  # the URL that answered, after redirects
    detail: str


@dataclass(frozen=True)
class FetchResult:
    spec: ArtifactSpec
    path: Path | None  # the verified file, or None
    from_cache: bool
    attempts: tuple[FetchAttempt, ...]
    failure: GateFailure | None  # its cause when the fetch failed

    @property
    def ok(self) -> bool:
        return self.path is not None


class RedirectRefusedError(urllib.error.URLError):
    """A redirect to a URL that is not https."""


class _HttpsOnlyRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.startswith("https://"):
            raise RedirectRefusedError(f"redirect to {newurl!r} refused: not https")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def https_opener() -> Callable[..., object]:
    """The default opener: urllib, following redirects only to https URLs."""
    return urllib.request.build_opener(_HttpsOnlyRedirect).open


def cache_path(spec: ArtifactSpec, cache_dir: Path) -> Path:
    """Where the verified file of ``spec`` is kept: named by its SHA-256."""
    return cache_dir / spec.sha256


class _LocalError(Exception):
    """The cache folder or file failed: a Refute error, never a network or artifact
    cause."""


def _matches(path: Path, spec: ArtifactSpec) -> bool:
    try:
        if not path.is_file() or path.stat().st_size != spec.size_bytes:
            return False
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(CHUNK), b""):
                digest.update(chunk)
    except OSError as exc:
        raise _LocalError(f"cannot read {path}: {exc}") from exc
    return digest.hexdigest() == spec.sha256


def _download(response, spec: ArtifactSpec, out) -> tuple[str, str]:
    """Streams the response into the open file ``out``, hashing it; stops beyond the
    declared size."""
    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = response.read(CHUNK)  # a network error here is transient
        if not chunk:
            break
        size += len(chunk)
        if size > spec.size_bytes:
            return MISMATCH, f"more than the declared {spec.size_bytes} bytes"
        digest.update(chunk)
        try:
            out.write(chunk)
        except OSError as exc:
            raise _LocalError(f"cannot write the temporary file: {exc}") from exc
    if size != spec.size_bytes:
        return MISMATCH, f"{size} bytes, not the declared {spec.size_bytes}"
    if digest.hexdigest() != spec.sha256:
        return MISMATCH, f"sha256 {digest.hexdigest()}, not the locked {spec.sha256}"
    return OK, f"{size} bytes, sha256 matches"


def _attempt(
    spec: ArtifactSpec, cache_dir: Path, opener, timeout_s: float, number: int
) -> tuple[FetchAttempt, Path | None]:
    """One download into a new temporary file of this call only. Returns the attempt and,
    when it matched, the temporary file (still to be published)."""
    try:
        fd, name = tempfile.mkstemp(prefix=f"{spec.sha256}.", suffix=".part", dir=cache_dir)
    except OSError as exc:
        raise _LocalError(f"cannot create a temporary file in {cache_dir}: {exc}") from exc
    temp = Path(name)
    status: int | None = None
    url = spec.url
    keep = False
    try:
        try:
            out = os.fdopen(fd, "wb")
        except OSError as exc:
            os.close(fd)
            raise _LocalError(f"cannot write {temp}: {exc}") from exc
        try:
            with opener(spec.url, timeout=timeout_s) as response:
                status = getattr(response, "status", None)
                url = getattr(response, "url", None) or spec.url
                outcome, detail = _download(response, spec, out)
        except _LocalError:
            raise
        except RedirectRefusedError as exc:
            outcome, detail = REFUSED, str(exc.reason)
        except urllib.error.HTTPError as exc:
            status, url = exc.code, getattr(exc, "url", None) or spec.url
            outcome = ABSENT if exc.code in ABSENT_STATUS else TRANSIENT
            detail = f"HTTP {exc.code}"
        except (OSError, http.client.HTTPException) as exc:  # URLError, timeouts, cut reads
            outcome, detail = TRANSIENT, f"{type(exc).__name__}: {exc}"
        finally:
            try:
                out.close()
            except OSError as exc:
                raise _LocalError(f"cannot close {temp}: {exc}") from exc
        keep = outcome == OK
        return FetchAttempt(number, outcome, status, url, detail), temp if keep else None
    finally:
        if not keep:
            _remove(temp)


def _remove(temp: Path) -> None:
    try:
        temp.unlink(missing_ok=True)
    except OSError as exc:  # a Refute error, recorded by the caller
        raise _LocalError(f"cannot remove {temp}: {exc}") from exc


def _publish(temp: Path, final: Path) -> bool:
    """Gives the verified temporary file its final name, never replacing an existing
    file. Returns False when the name already exists."""
    try:
        os.link(temp, final)
    except FileExistsError:
        return False
    except OSError as exc:
        raise _LocalError(f"cannot publish {final}: {exc}") from exc
    finally:
        _remove(temp)
    return True


def fetch_artifact(
    spec: ArtifactSpec,
    cache_dir: Path,
    *,
    attempts: int,
    interval_s: float,
    opener: Callable[..., object] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    timeout_s: float = TIMEOUT_S,
) -> FetchResult:
    """Fetches one declared artifact into ``cache_dir`` and verifies it (see the module
    docstring for the attempts and the causes). Never raises for a network, artifact or
    cache failure: the cause is in the result."""
    if type(attempts) is not int or attempts < 1:
        raise ValueError("attempts is a positive integer (absent_artifact.attempts)")
    if not interval_s > 0:
        raise ValueError("interval_s is positive (absent_artifact.interval_minutes)")
    opener = opener or https_opener()
    final = cache_path(spec, cache_dir)
    log: list[FetchAttempt] = []

    def failed(cause: FailureCause, from_cache: bool = False) -> FetchResult:
        return FetchResult(spec, None, from_cache, tuple(log), GateFailure(cause))

    try:
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise _LocalError(f"cannot create {cache_dir}: {exc}") from exc
        if final.exists():
            if _matches(final, spec):
                return FetchResult(spec, final, True, (), None)
            # never overwritten: the maintainer inspects a cached file that does not match
            detail = "the cached file does not match the locked sha256 and size"
            log.append(FetchAttempt(0, MISMATCH, None, str(final), detail))
            return failed(FailureCause.UNDETERMINED, from_cache=True)

        for number in range(1, attempts + 1):
            if number > 1:
                sleep(interval_s)
            attempt, temp = _attempt(spec, cache_dir, opener, timeout_s, number)
            log.append(attempt)
            if temp is not None:
                if not _publish(temp, final):  # another call published meanwhile
                    if _matches(final, spec):
                        return FetchResult(spec, final, True, tuple(log), None)
                    return failed(FailureCause.UNDETERMINED)
                return FetchResult(spec, final, False, tuple(log), None)
            if attempt.outcome in (MISMATCH, REFUSED):
                return failed(FailureCause.UNDETERMINED)
    except _LocalError as exc:
        log.append(FetchAttempt(len(log) + 1, LOCAL_ERROR, None, spec.url, str(exc)))
        return failed(FailureCause.REFUTE_ERROR)

    if all(a.outcome == ABSENT for a in log):
        return FetchResult(
            spec,
            None,
            False,
            tuple(log),
            GateFailure(FailureCause.ARTIFACT_ABSENT, attempts, attempts),
        )
    return failed(FailureCause.TRANSIENT_NETWORK)


def absence_evidence(result: FetchResult) -> dict[str, list[int]]:
    """The evidence a ``data_present`` gate records for a proven absence: one HTTP status
    per attempt, for the procedural coverage rule of the WP2 core
    (``refute.core.paper.proven_absence``). Empty unless the cause is ``artifact_absent``."""
    if result.failure is None or result.failure.known_cause is not FailureCause.ARTIFACT_ABSENT:
        return {}
    return {ABSENT_HTTP_STATUSES: [a.http_status for a in result.attempts]}
