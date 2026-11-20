"""v0.5.5, R1: what the four checks share (#218; ``docs/plans/v0.5.5-r1-designs.md``).
``method_status: not_validated``.

- **The frozen outcome rules and futility rules**, as pure functions (tested offline in
  ``tests/v055/``): D1-P per exit, D2-F per variant, T2a-E.
- **The machine policy** (the maintainer's rule): processors 0 to 7 always free; on working
  hours (Monday to Friday, 08:00 to 18:00, local time UTC-3) at most 10 workers, otherwise up
  to 22; BelowNormal priority (``launch_detached.py``); batches of at most 30 minutes. **R1 uses
  at most 10 workers at all hours** (Codex, r0r1 round 2, the conservative option): "up to 22" is
  a ceiling, not an obligation, and a shard that passed its declared 1,200 s (the driver checks a
  shard's time only after it ends) could otherwise cross 08:00 with more than 10 workers. So no
  pause is needed (``NO_PAUSE``).
- **Seeds**: new, disjoint, and named per check and set; never a development seed used before
  and never a confirmation seed.

Nothing here reads data or runs a check.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import math
from statistics import NormalDist

BRT = dt.timezone(dt.timedelta(hours=-3))
WORKING_START, WORKING_END = 8, 18
WORKERS_WORKING, WORKERS_OFF = 10, 22
PIN_FIRST, PIN_LAST = 8, 31  # processors 0 to 7 stay free
MAX_SHARD_SECONDS = 1200.0  # a shard ends well inside the driver's 30-minute batch
REQUIRED = 0.95  # the battery's sensitivity rule (power at least 0.95)
Z95 = 1.959964


# --- seeds ------------------------------------------------------------------------------------


def seed(check: str, set_name: str, family: str, i: int) -> int:
    """``int(SHA-256("refute-v055-<check>-<set>:<family>:<i>")[:16], 16)``: new strings, so new
    seeds, disjoint between checks and sets (C1's development and confirmation strings differ)."""
    text = f"refute-v055-{check}-{set_name}:{family}:{i}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


# --- the frozen identity ----------------------------------------------------------------------


def identity(root, paths) -> dict:
    """The SHA-256 of every file a check executes or reads as configuration (its code, the
    earlier stages' modules, the driver, the frozen inputs), keyed by its path under ``root``,
    and one hash over them: recorded in every summary, and checked by a second set or stage
    against the first's before it uses the first's futility or counts (Codex, r0r1 round 1)."""
    from pathlib import Path

    files = {
        Path(p).resolve().relative_to(Path(root).resolve()).as_posix(): hashlib.sha256(
            Path(p).read_bytes()
        ).hexdigest()
        for p in paths
    }
    combined = hashlib.sha256("".join(f"{k}={v}\n" for k, v in sorted(files.items())).encode())
    return {"files": files, "sha256": combined.hexdigest()}


def digest(ident: dict) -> str:
    """One digest over a complete identity document (every field but ``digest``), so that a
    second set or stage refuses any difference, the current source and dependency hash included
    (Codex, r0r1 round 2)."""
    import json

    body = {k: v for k, v in ident.items() if k != "digest"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


# --- the machine policy -----------------------------------------------------------------------


def working_hours(now: dt.datetime) -> bool:
    local = now.astimezone(BRT)
    return local.weekday() < 5 and WORKING_START <= local.hour < WORKING_END


def workers_now(now: dt.datetime) -> int:
    """At most 10 at every hour (the conservative option); ``now`` is kept for the record."""
    return WORKERS_WORKING


def next_working_start(now: dt.datetime) -> dt.datetime:
    """The next 08:00 local of a weekday after ``now`` (``now`` itself if it is one)."""
    local = now.astimezone(BRT)
    day = local.replace(hour=WORKING_START, minute=0, second=0, microsecond=0)
    if local > day:
        day += dt.timedelta(days=1)
    while day.weekday() >= 5:
        day += dt.timedelta(days=1)
    return day


NO_PAUSE = dt.datetime(2100, 1, 1, tzinfo=BRT)  # the driver compares a datetime, never None


def pause_at(now: dt.datetime) -> dt.datetime:
    """When dispatching stops: never, for R1's 10 workers (``NO_PAUSE``, a far-future datetime,
    because the driver compares ``moment >= pause_at`` and has no case for None)."""
    return NO_PAUSE


def pin() -> tuple[int, ...]:
    """One processor per worker, from 8 to 31 (every second one first, as the earlier phases)."""
    evens = tuple(range(PIN_FIRST, PIN_LAST + 1, 2))
    odds = tuple(range(PIN_FIRST + 1, PIN_LAST + 1, 2))
    return evens + odds


# --- intervals --------------------------------------------------------------------------------


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float]:
    """The Wilson score interval (two-sided 95 % by default)."""
    if n <= 0:
        raise ValueError("an interval needs n > 0")
    p = k / n
    d = 1.0 + z * z / n
    c = p + z * z / (2.0 * n)
    h = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return (c - h) / d, (c + h) / d


def non_rejection(distance: float, level: float) -> float:
    """B0's oracle reading: a binary at Mahalanobis distance ``d`` from the nearest planet is not
    rejected, by a test whose false-failure rate on that planet is ``level``, with probability
    ``Phi(z_level - d)``. For D1-P, this formula supplies a nominal surrogate score; planet-side
    calibration is not established."""
    nd = NormalDist()
    return nd.cdf(nd.inv_cdf(1.0 - level) - distance)


# --- D1-P: the frozen outcome per exit --------------------------------------------------------


def d1p_set_reading(expected: float, k: int, p05: float, p95: float) -> str:
    """One seed set, one family, one exit price, under the primary reading:
    - "route": the expected SURVIVED count at the projection is at most k - 2 and the
      bootstrap 5th percentile of the pass probability is at least 0.5;
    - "closed": the expected count exceeds k and the 95th percentile is below 0.05;
    - "unresolved" otherwise."""
    if expected <= k - 2 and p05 >= 0.5:
        return "route"
    if expected > k and p95 < 0.05:
        return "closed"
    return "unresolved"


def d1p_exit_outcome(readings: dict[str, dict[str, str]]) -> str:
    """``readings[set][family]``. "route" if every family reads "route" on both sets; "closed"
    if some family reads "closed" on both sets; "unresolved" otherwise (a missing set is
    "unresolved")."""
    sets = list(readings)
    families = {f for r in readings.values() for f in r}
    if len(sets) < 2:
        return "unresolved"
    if all(readings[s].get(f) == "route" for s in sets for f in families):
        return "route"
    if any(all(readings[s].get(f) == "closed" for s in sets) for f in families):
        return "closed"
    return "unresolved"


def d1p_futile_after_first(first: dict[str, dict[str, str]]) -> bool:
    """After set A, per exit ``first[exit][family]``: the second set is futile when no exit can
    still end "route" or "closed" (each needs set A to read so already)."""
    for fams in first.values():
        if all(v == "route" for v in fams.values()):
            return False
        if any(v == "closed" for v in fams.values()):
            return False
    return True


# --- D2-F: the frozen outcome per variant ------------------------------------------------------
# Codex (r0r1, round 1): a certificate's failure does not exclude a warning FAIL, which keeps the
# planet, so these counts are not demonstrated lower bounds on unavoidable retention losses. D2-F
# therefore has no "closed" outcome: it reads "route under the variant" or "unresolved".

D2_ALLOWED = 22  # 178 - 156 (round 3's population)
D2_ROUTE = 14 / 178  # the count must leave 8 of 22 for the estimators


def d2f_variant_outcome(upper: dict[str, tuple[int, int]]) -> str:
    """``upper[set] = (count, eligible)``, counted with every uncertain and unknown planet:
    "route under the variant" if the pooled Wilson upper end is at most 14/178 and every set's
    point fraction at most 14/178, on two sets at least; "unresolved" otherwise."""
    if len(upper) < 2 or any(n <= 0 for _, n in upper.values()):
        return "unresolved"
    n_all = sum(n for _, n in upper.values())
    k_all = sum(k for k, _ in upper.values())
    if wilson(k_all, n_all)[1] <= D2_ROUTE and all(k / n <= D2_ROUTE for k, n in upper.values()):
        return "route under the variant"
    return "unresolved"


def d2f_futile_after_first(first_upper: dict[str, tuple[int, int]]) -> bool:
    """After set A, per variant: "route" is still possible only if set A's point fraction (upper
    counting) is at most 14/178. Futile when it is not, for every variant."""
    return not any(n > 0 and k / n <= D2_ROUTE for k, n in first_upper.values())


# --- T2a-E: the frozen outcome ------------------------------------------------------------------

T2A_MAX_UNK = 20


def t2ae_outcome(freed: int, valid: int, unknown: int) -> str:
    """ "INCONCLUSIVE (too many unknown)" above 20 unknown of 102; otherwise, with V valid:
    "an error model is worth building" if freed >= 0.8 V; "empirically limited for this estimator
    class" if freed <= 0.4 V; "unresolved" otherwise."""
    if unknown > T2A_MAX_UNK or valid == 0:
        return "INCONCLUSIVE (too many unknown)"
    if freed >= 0.8 * valid:
        return "an error model is worth building"
    if freed <= 0.4 * valid:
        return "empirically limited for this estimator class"
    return "unresolved"


def t2ae_futile_after_first(freed: int, valid: int, unknown: int, remaining: int) -> bool:
    """After the first stage: futile when the unknown already pass 20, or when no completion of
    the ``remaining`` injections can reach either decisive outcome."""
    if unknown > T2A_MAX_UNK:
        return True
    for extra_valid in range(remaining + 1):
        for extra_freed in (0, extra_valid):
            v, f = valid + extra_valid, freed + extra_freed
            if v and (f >= 0.8 * v or f <= 0.4 * v):
                return False
    return True


def chi2_upper_factor(k: int, alpha: float = 0.05) -> float:
    """``sqrt((k - 1) / chi2_alpha(k - 1))``: for ``k`` independent normal values, the factor
    that turns their sample standard deviation into a one-sided ``1 - alpha`` upper confidence
    bound. **For T2a-E's dependent placebo estimates it is a heuristic inflation; 95 % coverage
    has not been established there** (Codex, r0r1 round 1)."""
    from scipy.stats import chi2

    if k < 2:
        raise ValueError("needs at least two values")
    return math.sqrt((k - 1) / chi2.ppf(alpha, k - 1))
