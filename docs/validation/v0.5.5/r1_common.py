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


def unfrozen_modules(root, frozen) -> list[str]:
    """The project's Python modules loaded in this process (under ``root``, outside ``src/``,
    which the code hash covers, and outside the virtual environment) that are not in ``frozen``:
    a frozen list is complete only when this is empty (the maintainer's decision of 2026-11-20,
    night, 4c). Read at the time of the call, so a module imported later is checked then. **This
    is a conservative guard of loaded modules and recognized static imports, not a general proof
    of the dependencies' closure** (Codex, night round 1): relative imports, local packages and
    dynamic loading are not resolved in full, and a process that loaded modules foreign to the
    check is refused (so each check runs in a process of its own)."""
    import sys
    from pathlib import Path

    base = Path(root).resolve()
    listed = {Path(p).resolve() for p in frozen}
    missing = set()
    for name, mod in list(sys.modules.items()):
        f = getattr(mod, "__file__", None)
        # a check run as a script is in its own list already (``__mp_main__`` is the name
        # multiprocessing gives the main script on Windows)
        if not f or name in ("__main__", "__mp_main__"):
            continue
        path = Path(f).resolve()
        try:
            rel = path.relative_to(base)
        except ValueError:
            continue
        if rel.parts[0] in ("src", ".venv", "tests") or path in listed:
            continue
        missing.add(rel.as_posix())
    # imports inside functions run only in the workers: a static pass over every frozen module's
    # import statements, resolved on the project's folders of ``sys.path`` (transitively)
    dirs = []
    for entry in sys.path:
        try:
            d = Path(entry or ".").resolve()
            rel = d.relative_to(base)
        except (ValueError, OSError):
            continue
        if rel.parts[:1] not in (("src",), (".venv",)):
            dirs.append(d)
    # a folder a module puts on sys.path only inside a function (v0.5.3's d2_bounds._wp1 does so
    # for v0.5.1's forecast.py) is not on it here: a name found on no folder of sys.path is looked
    # for in every project folder of scripts, and every match counts (the conservative side)
    scripts = sorted(
        {p.parent for top in ("docs", "calibration") for p in base.joinpath(top).rglob("*.py")}
    )
    todo = [p for p in listed if p.suffix == ".py"]
    seen = set(todo)
    while todo:
        for name in sorted(_imported_names(todo.pop())):
            found = [(d / f"{name}.py").resolve() for d in dirs if (d / f"{name}.py").is_file()]
            if not found and not _importable_elsewhere(name):
                found = [d / f"{name}.py" for d in scripts if (d / f"{name}.py").is_file()]
            for f in found[:1] if found and found[0].parent in dirs else found:
                if f not in listed:
                    missing.add(f.relative_to(base).as_posix())
                if f not in seen:
                    seen.add(f)
                    todo.append(f)
    return sorted(missing)


def _importable_elsewhere(name: str) -> bool:
    """A module of the standard library, of an installed package or of ``src/`` (outside the
    project's script folders)."""
    import importlib.util
    import sys

    if name in sys.builtin_module_names or name in sys.stdlib_module_names:
        return True
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, ValueError):
        return False
    origin = getattr(spec, "origin", None) or ""
    return spec is not None and ("site-packages" in origin or "/src/" in origin.replace("\\", "/"))


def _imported_names(path) -> set[str]:
    """The top-level module names a Python file imports, anywhere in it (absolute imports)."""
    import ast

    names = set()
    for node in ast.walk(ast.parse(path.read_text("utf-8"))):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def require_frozen(root, frozen) -> None:
    """Refuses (a STOP) when ``unfrozen_modules`` is not empty."""
    missing = unfrozen_modules(root, frozen)
    if missing:
        raise SystemExit("modules loaded but not frozen: " + ", ".join(missing) + ": STOP")


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


def d1p_set_reading(expected: float, k: int, p05: float) -> str:
    """One seed set, one family, one view, one exit price, under the primary reading: "route"
    if the expected SURVIVED count at the projection is at most k - 2 and the bootstrap 5th
    percentile of the pass probability is at least 0.5; "unresolved" otherwise. "closed" is not
    an outcome: B0's own numbers make it practically unreachable (the maintainer's decision of
    2026-11-20, night, 4a)."""
    if expected <= k - 2 and p05 >= 0.5:
        return "route"
    return "unresolved"


D1P_VIEWS = ("survivors", "all_eligible")
D1P_SETS = ("A", "B")
D1P_FAMILIES = ("EB1", "EB2")


def _complete(cells: dict, keys: tuple) -> bool:
    return isinstance(cells, dict) and set(cells) == set(keys)


def d1p_exit_outcome(readings: dict[str, dict[str, dict[str, str]]]) -> str:
    """``readings[view][set][family]``. **Missing or incomplete coverage returns INCONCLUSIVE;
    "route" needs the eight expected cells (two views, sets A and B, EB1 and EB2), all "route"**
    (Codex, night round 1); "unresolved" otherwise. Zero coverage is never a route."""
    if not _complete(readings, D1P_VIEWS):
        return "INCONCLUSIVE"
    for sets in readings.values():
        if not _complete(sets, D1P_SETS):
            return "INCONCLUSIVE"
        if not all(_complete(fams, D1P_FAMILIES) for fams in sets.values()):
            return "INCONCLUSIVE"
    cells = [c for sets in readings.values() for fams in sets.values() for c in fams.values()]
    return "route" if all(c == "route" for c in cells) else "unresolved"


def d1p_futile_after_first(first: dict[str, dict[str, dict[str, str]]]) -> bool:
    """After set A, ``first[exit][view][family]``: the second set runs only if some exit already
    reads "route" in all four of set A's cells (two views, EB1 and EB2); an exit with missing or
    incomplete coverage never justifies running set B."""
    for views in first.values():
        if not _complete(views, D1P_VIEWS):
            continue
        if not all(_complete(fams, D1P_FAMILIES) for fams in views.values()):
            continue
        if all(c == "route" for fams in views.values() for c in fams.values()):
            return False
    return True


# --- D2-F: the frozen outcome per variant ------------------------------------------------------
# Codex (r0r1, round 1): a certificate's failure does not exclude a warning FAIL, which keeps the
# planet, so these counts are not demonstrated lower bounds on unavoidable retention losses. D2-F
# therefore has no "closed" outcome: it reads "route under the variant" or "unresolved".

D2_ALLOWED = 22  # 178 - 156 (round 3's population)
D2_ROUTE = 14 / 178  # the count must leave 8 of 22 for the estimators
D2_REQUIRED_DROP = 0.10  # D2: version 5's kept fraction at least v0.4's kept fraction less 0.10
D2_ESTIMATOR_ROOM = 8 / 178  # round 3: 8 of D2's 22 losses left for the estimators


def d2f_route_fraction(v04_kept: int, eligible: int) -> float:
    """The route threshold as a fraction of the eligible planets **in the population's own unit**
    (the redesign, 3b): D2's allowance from that population's own v0.4 kept fraction (the
    integer requirement ``ceil((f04 - 0.10) n)``), less the estimators' room of round 3 (8/178);
    never above the fixed 14/178, so the stricter of the two decides (no goal is loosened)."""
    if eligible <= 0:
        raise ValueError("a threshold needs eligible planets")
    required = math.ceil((v04_kept / eligible - D2_REQUIRED_DROP) * eligible - 1e-9)
    allowed = eligible - max(required, 0)
    return min(D2_ROUTE, allowed / eligible - D2_ESTIMATOR_ROOM)


def d2f_variant_outcome(upper: dict[str, tuple[int, int, int]]) -> str:
    """``upper[set] = (count, eligible, v04_kept)``, counted with every uncertain and unknown
    planet: "route under the variant" if the pooled Wilson upper end is at most the pooled
    threshold and every set's point fraction at most its own (``d2f_route_fraction``), on two sets
    at least; "unresolved" otherwise."""
    if len(upper) < 2 or any(n <= 0 for _, n, _ in upper.values()):
        return "unresolved"
    n_all = sum(n for _, n, _ in upper.values())
    k_all = sum(k for k, _, _ in upper.values())
    v_all = sum(v for _, _, v in upper.values())
    pooled_ok = wilson(k_all, n_all)[1] <= d2f_route_fraction(v_all, n_all)
    if pooled_ok and all(k / n <= d2f_route_fraction(v, n) for k, n, v in upper.values()):
        return "route under the variant"
    return "unresolved"


def d2f_futile_after_first(first_upper: dict[str, tuple[int, int, int]]) -> bool:
    """After set A, ``first_upper[variant] = (count, eligible, v04_kept)``: "route" is still
    possible only if set A's point fraction (upper counting) is at most its own threshold. Futile
    when it is not, for every variant."""
    return not any(n > 0 and k / n <= d2f_route_fraction(v, n) for k, n, v in first_upper.values())


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
