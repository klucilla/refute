"""From a resolved ML claim file to the verdict of each claim (WP3, issue #46).

The claim file (validated by ``schema.py``) is turned into a plan of containers, run by the
``PaperRunner`` with the WP2 accountant, and every check of WP2/WP3 is then read from the
evidence the runs left: the exit codes, the logs, the files each run wrote, the fetched
datasets. The verdict of each claim is ``refute.core.paper.aggregate_claim``; the result
of the paper is ``paper_profile``. No LLM output enters anything here.

**What the harness gives** (``Harness``): the backend; one fresh folder per container
(``workspaces``, prepared by the harness before the run, so no run reads an output of
another, requirement 10); the folder of the logs (outside every workspace); how a claim's
command becomes the backend's (``command``); the evidence of every declared dataset
(``DatasetEvidence``: the fetch result and what the pack's reader counted, requirement 5);
the inputs of the build ladder found in the repository and how a rung is built and
classified; the margin M and the V22 maxima.

**Requirements of the interim review** (``.cache``-free summary, PR description):

1. a proven absence reaches NOT_REPRODUCIBLE only with its HTTP evidence (#106);
2. the build ladder is one setup step (a fallback step of the orchestrator), every rung
   accounted;
3. identity per claim, seed, role (method or reference), attack and attempt: container
   ids name them, values keep their positions with ``None``, methods are paired by seed;
4. the same extracted token feeds ``metric_recompute``; values are converted to the
   claim's unit before any predicate; differences keep the claim's orientation;
5. gates from evidence: ``data_present`` checks every declared split against its
   expected size, and ``metric_extracted`` claims examples only through the coverage
   routes the claim declared (1.5a: saved predictions, sufficient statistics, a printed
   count, the hook), for every base seed and every method, all agreeing; a printed
   value alone shows no examples, and with no route that closes the chain the gate is
   ``INCONCLUSIVE``;
6. the coverage minimums of 1.0.7 come from the resolved claim;
7. an attack keeps its valid failures when some of its runs did not end (its
   prerequisites are the runs and values it used);
8. an exit code 0 means the command ended, never that a predicate holds;
9. F is the grant's (checked by the orchestrator); M, the V22 maxima and, with a parent
   cgroup, its usage and T are given by the harness; a paper whose accounting is invalid
   gets no verdict but ``INCONCLUSIVE``. Partly met: the subprocess backend has no parent
   cgroup (the completeness check is not applicable there), and ``metric_recompute`` runs
   in this process, not yet in the trusted verifier container of W3.18 (docker, on the VM);
10. one folder of its own per container, and the files a run is read from must not exist
    before it starts, so every value read was written by that run;
11. a failure of the setup or of one dataset is attributed only to the claims that use
    it.

**Not done here** (recorded as pending): the retries of ``stages.*.retries``; an
ablation switched by a configuration file (``disable.config_file``, INCONCLUSIVE here);
the docker backend.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
from collections.abc import Callable, Hashable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from pathlib import Path, PurePosixPath
from typing import Any

from refute.core import budget as bg
from refute.core.canonical import canonical_bytes
from refute.core.paper import (
    BASE_GATES,
    BASE_REPRODUCTION,
    METRIC_RECOMPUTE,
    Attack,
    ClaimVerdict,
    CoverageMinimum,
    FailureCause,
    GateFailure,
    PaperProfile,
    aggregate_claim,
    paper_profile,
    prerequisite_names,
)
from refute.core.verdict import PaperVerdict, Severity, TestResult, TestStatus
from refute.packs.ml import attacks as at
from refute.packs.ml import coverage_hook as ch
from refute.packs.ml import extract as ex
from refute.packs.ml import ladder as ld
from refute.packs.ml import orchestrate as orc
from refute.packs.ml import predicates as pr
from refute.packs.ml import recompute as rc
from refute.packs.ml import reproduction as rp
from refute.packs.ml.fetch import FetchResult, absence_evidence
from refute.packs.ml.sandbox import RunResult, RunSpec, TimingMaxima

HOUR_S = 3600.0
CONTAINER_ATTACKS = ("seeds", "data_split", "ablation", "holdout")
HOST_ATTACKS = ("leakage", "trivial_baseline")
ACCOUNTING_INVALID = "the accounting of the paper is invalid"

# How a container that did not complete is attributed (WP2 attribution; item D of the
# maintainer's review of 2026-10-16: a failed run or extraction is never the artifact's)
_STOPS = {
    orc.Outcome.BUDGET_EXHAUSTED: FailureCause.BUDGET_EXHAUSTED,
    orc.Outcome.OPERATIONAL_GUARD: FailureCause.OPERATIONAL_GUARD,
    orc.Outcome.REFUTE_ERROR: FailureCause.REFUTE_ERROR,
    orc.Outcome.NOT_EXECUTED: FailureCause.INTERRUPTED,
    orc.Outcome.FAILED: FailureCause.UNDETERMINED,
}


# ---- what the harness gives ---------------------------------------------------------------


@dataclass(frozen=True)
class DatasetEvidence:
    """One declared dataset: the fetch result of Refute's own fetcher and what the pack's
    reader found in the fetched file. ``split_counts`` is the number of examples of every
    split read from the file (None when it could not be read); ``labels`` and
    ``example_hashes`` read a split's labels (``trivial_baseline``) and the SHA-256 of
    each of its examples as stored (``leakage``)."""

    fetch: FetchResult
    split_counts: Mapping[str, int] | None
    labels: Callable[[str], Sequence[Hashable]] | None = None
    example_hashes: Callable[[str], Sequence[str]] | None = None


@dataclass(frozen=True)
class Harness:
    backend: orc.Backend
    workspaces: Mapping[str, Path]  # container id -> its fresh folder
    logs: Path  # outside every workspace
    command: Callable[[Sequence[str]], list[str]]  # the claim's argv for this backend
    datasets: Mapping[str, DatasetEvidence]
    ladder_inputs: tuple[str | None, str | None]  # own environment file, requirements file
    build_command: Callable[[ld.Rung], list[str]]
    classify_build: Callable[[ld.Rung, RunResult | None], ld.RungResult]
    margin_usec: int
    timing_maxima: TimingMaxima | None = None
    second: Callable[..., float] = rc.sklearn_metric  # the second recompute implementation
    base_env: Mapping[str, str] = field(default_factory=dict)  # under the claim's threads
    # the usage of the paper's parent cgroup and the tolerance T (1.4a): given only by a
    # backend with a parent cgroup per paper (docker, on the VM); the subprocess backend
    # has none, so the completeness check is recorded as not applicable there
    parent_usage: Callable[[], int] | None = None
    tolerance_usec: int | None = None


# ---- the claims ---------------------------------------------------------------------------


def _uncertainty(record: Mapping[str, Any] | None) -> pr.PublishedUncertainty:
    if record is None:
        return pr.NONE
    if record["status"] == "converted":
        return pr.PublishedUncertainty("converted", record["sd"])
    return pr.PublishedUncertainty(record["status"])


@dataclass
class ClaimContext:
    """One resolved claim and what the integration derives from it."""

    claim: dict[str, Any]
    plan: dict[str, Any]

    @property
    def key(self) -> str:
        return self.claim["key"]

    @property
    def comparison(self) -> dict[str, Any] | None:
        return self.claim.get("comparison")

    @property
    def separate_reference(self) -> bool:
        c = self.comparison
        return c is not None and not c["reference_run"].get("same", False)

    def roles(self) -> list[str]:
        return ["method", "reference"] if self.separate_reference else ["method"]

    def attack(self, name: str) -> dict[str, Any]:
        return next(a for a in self.claim["attacks"] if a["name"] == name)

    def applicable(self) -> list[str]:
        """The applicable attacks, in the order of the claim (the effective order)."""
        return [a["name"] for a in self.claim["attacks"] if a["applies"]]

    def params(self) -> pr.ToleranceParams:
        t = self.claim["tolerance"]
        return pr.ToleranceParams(t["rel_tol"], t["k_sd"], t["abs_floor"])

    def tolerance(self) -> pr.Tolerance | None:
        """The claim's tolerance: one number for a value claim, ``tol_d`` for ``margin``
        and ``magnitude``, none for ``direction``."""
        mode, c = self.claim["comparison_mode"], self.comparison
        if c is None:
            m = self.claim["metric"]
            return pr.one_number(
                m["reported"], self.params(), _uncertainty(m["reported_uncertainty"])
            )
        if mode == "direction":
            return None
        p = c["d_pub"] if mode == "magnitude" else c["g_pub"]
        return pr.difference_tolerance(
            p,
            self.params(),
            c["reported_method"],
            c["reported_reference"],
            _uncertainty(c["uncertainty_method"]),
            _uncertainty(c["uncertainty_reference"]),
            _uncertainty(c["paired_uncertainty"]),
        )

    def predicate(self, tol: pr.Tolerance | None = None) -> Callable[[Decimal], pr.Outcome]:
        """The claim's predicate (plan 6.2), with its own tolerance or ``tol``."""
        mode, c = self.claim["comparison_mode"], self.comparison
        tol = tol if tol is not None else self.tolerance()
        if c is None:
            reported = self.claim["metric"]["reported"]
            return lambda x: pr.value_predicate(x, reported, mode, tol)
        return lambda d: pr.comparison_predicate(
            d, mode, tol, g_pub=c.get("g_pub"), d_pub=c.get("d_pub")
        )

    def minimums(self) -> dict[str, CoverageMinimum]:
        return {
            name: CoverageMinimum(v["positive"], v["negative"])
            for name, v in self.claim["coverage_minimum"].items()
        }

    def stage(self, name: str) -> tuple[float, float]:
        s = self.plan["stages"][name]
        return s["active_time_limit_hours"] * HOUR_S, s["no_progress_hours"] * HOUR_S


def _tag(seed: int | None) -> str:
    return "s-" if seed is None else f"s{seed}"


def container_id(key: str, step: str, role: str, seed: int | None) -> str:
    """Identity per claim, step (base or attack), role and seed (requirement 3)."""
    return f"{key}/{step}/{role}/{_tag(seed)}"


def _runs(ctx: ClaimContext, step: str) -> list[tuple[str, str, int | None, list[str]]]:
    """The containers of one step: (id, role, seed, extra arguments)."""
    seeds = ctx.claim["seeds"]
    base_seed = seeds["base"][0] if ctx.claim["run"]["seed_argument"] else None
    if step == "base":
        plan = [(s if ctx.claim["run"]["seed_argument"] else None, []) for s in seeds["base"]]
    elif step == "seeds":
        plan = [(s, []) for s in seeds["attack"]]
    elif step == "data_split":
        arg = ctx.attack("data_split")["params"]["split_argument"]
        plan = [(base_seed, [arg.replace("{seed}", str(s))]) for s in seeds["data_split"]]
        # one container per re-split, named by the split seed
        return [
            (container_id(ctx.key, step, role, None) + f"/split{s}", role, base_seed, extra)
            for (_, extra), s in zip(plan, seeds["data_split"], strict=True)
            for role in ctx.roles()
        ]
    elif step == "ablation":
        disable = ctx.attack("ablation")["params"]["disable"]
        extra = list(disable.get("argv", []))
        plan = [(s if ctx.claim["run"]["seed_argument"] else None, extra) for s in seeds["base"]]
        return [(container_id(ctx.key, step, "method", s), "method", s, e) for s, e in plan]
    elif step == "holdout":
        arg = ctx.attack("holdout")["params"]["split_argument"]
        plan = [(base_seed, [arg.replace("{seed}", str(seeds["holdout"][0]))])]
    else:
        raise ValueError(f"no containers for {step}")
    return [
        (container_id(ctx.key, step, role, s), role, s, extra)
        for s, extra in plan
        for role in ctx.roles()
    ]


def _argv(ctx: ClaimContext, role: str, seed: int | None, extra: Sequence[str]) -> list[str]:
    run = ctx.claim["run"] if role == "method" else ctx.comparison["reference_run"]
    argv = list(run["argv"])
    if seed is not None and run["seed_argument"]:
        argv.append(run["seed_argument"].replace("{seed}", str(seed)))
    return argv + list(extra)


def _read_roles(ctx: ClaimContext, role: str) -> list[str]:
    """The roles whose readings a container of ``role`` carries: the reference too when it
    comes from the same runs as the method."""
    if role == "method" and ctx.comparison is not None and not ctx.separate_reference:
        return ["method", "reference"]
    return [role]


def _coverage_files(ctx: ClaimContext, role: str, seed: int | None) -> list[str]:
    """The files the coverage routes of ``role`` read from a run's folder: the count files
    of (d) and (a), and the hook's log of (b)."""
    out = []
    for name in _read_roles(ctx, role):
        evidence = ctx.claim["coverage_evidence"].get(name)
        for route in (evidence or {}).get("routes", []):
            for field_name in ("count", "correct", "total"):
                selector = route.get(field_name)
                if selector is not None and selector["from"] == "file":
                    out.append(selector["file"].replace("{seed}", str(seed)))
            if route["route"] == "hook":
                out.append(ch.HOOK_LOG)
    return out


def _outputs(ctx: ClaimContext, role: str, seed: int | None) -> list[str]:
    """The files a run of ``role`` is read from: its extraction file (``from: file``), the
    files of its coverage routes and, for a base run when ``metric_recompute`` applies,
    its predictions."""
    out = _coverage_files(ctx, role, seed)
    run = ctx.claim["run"] if role == "method" else ctx.comparison["reference_run"]
    readings = [run["metric_extraction"]]
    if role == "method" and ctx.comparison is not None and not ctx.separate_reference:
        readings.append(ctx.comparison["reference_run"]["metric_extraction"])
    for extraction in readings:
        if extraction["from"] == "file":
            out.append(extraction["file"].replace("{seed}", str(seed)))
    mr = ctx.claim["metric_recompute"]
    if mr["applies"]:
        names = [(ctx.comparison or {}).get("method"), (ctx.comparison or {}).get("reference")]
        if role == "reference":
            names = names[1:]
        elif ctx.separate_reference:
            names = names[:1]
        for name in names:
            file = mr["predictions"]["file"].replace("{seed}", str(seed))
            out.append(file.replace("{method}", str(name)) if name is not None else file)
    return sorted(set(out))


def plan_container_ids(claim_file: Mapping[str, Any]) -> list[str]:
    """Every container id of the paper, for the harness to prepare one fresh folder each
    (the ladder's rungs are named ``setup/build/<rung>``)."""
    ids = [f"setup/build/{name}" for name in ld.RUNGS]
    for target in claim_file["targets"]:
        ctx = ClaimContext(target, claim_file["test_plan"])
        ids += [cid for cid, *_ in _runs(ctx, "base")]
        for name in ctx.applicable():
            if name in CONTAINER_ATTACKS:
                ids += [cid for cid, *_ in _runs(ctx, name)]
    return ids


# ---- reading the evidence of one container ---------------------------------------------------


@dataclass
class Value:
    """What one container gave: its outcome, and the extracted token and value (in the
    claim's unit) of each extraction it carries."""

    outcome: orc.Outcome
    reason: str
    tokens: dict[str, ex.Extracted] = field(default_factory=dict)  # by role read
    errors: dict[str, str] = field(default_factory=dict)

    def value(self, role: str) -> Decimal | None:
        token = self.tokens.get(role)
        return None if token is None else token.value


def _convert(value: Decimal, from_unit: str, to_unit: str) -> Decimal:
    """× 100 or ÷ 100, exactly (1.0.3): the decimal exponent is moved by 2 on the value's
    own digits, so no decimal context can round it (Codex review of #110)."""
    if from_unit == to_unit:
        return value
    shift = 2 if (from_unit, to_unit) == ("fraction", "percent") else -2
    sign, digits, exponent = value.as_tuple()
    return Decimal((sign, digits, exponent + shift))


def _read(ctx: ClaimContext, record: orc.ContainerRecord | None, workdir: Path, role: str, seed):
    """The container's outcome and its extracted values (requirement 8: an exit code 0
    only means the command ended)."""
    if record is None or record.result is None:
        reason = "not executed" if record is None else record.error
        return Value(
            orc.Outcome.NOT_EXECUTED if record is None else orc.Outcome.REFUTE_ERROR, reason
        )
    outcome, reason = orc._outcome([record])  # noqa: SLF001 - the orchestrator's own rule
    out = Value(outcome, reason)
    if outcome is not orc.Outcome.COMPLETED:
        return out
    log = record.result.log_path.read_text(encoding="utf-8", errors="replace")
    unit = ctx.claim["metric"]["unit"]
    reads = {role: (ctx.claim["run"] if role == "method" else ctx.comparison["reference_run"])}
    if role == "method" and ctx.comparison is not None and not ctx.separate_reference:
        reads["reference"] = ctx.comparison["reference_run"]  # the same run, its own reading
    for name, run in reads.items():
        extraction = run["metric_extraction"]
        try:
            got = ex.extract(extraction, workdir, log, seed)
            value = _convert(got.value, extraction["unit"], unit)
            out.tokens[name] = ex.Extracted(got.token, value, got.source)
        except ex.ExtractionError as exc:
            out.errors[name] = str(exc)
    return out


# ---- the checks ------------------------------------------------------------------------------


def _gate(name, status, message, coverage, unit, metrics=None) -> TestResult:
    return TestResult(
        name,
        status,
        Severity.GATE,
        message,
        metrics=dict(metrics or {}),
        coverage=coverage,
        coverage_unit=unit,
    )


def data_present(ctx: ClaimContext, evidence: DatasetEvidence | None):
    """The claim's own dataset only (requirement 11): the fetch result must be for the
    declared artifact (name, URL, SHA-256, size), an absence counts only against the
    attempts the claim fixed (``absent_artifact.attempts``), and every declared split must
    be of its expected size within its tolerance (requirement 5; #15)."""
    name = ctx.claim["dataset"]
    if evidence is None:
        gate = _gate(
            "data_present", TestStatus.INCONCLUSIVE, f"no evidence for {name}", 0, "examples"
        )
        return gate, GateFailure(FailureCause.UNDETERMINED)
    declared = next(d for d in ctx.plan["datasets"] if d["name"] == name)
    spec = evidence.fetch.spec
    if (spec.name, spec.url, spec.sha256, spec.size_bytes) != (
        declared["name"],
        declared["url"],
        declared["sha256"],
        declared["size_bytes"],
    ):
        gate = _gate(
            "data_present",
            TestStatus.INCONCLUSIVE,
            f"the fetch result is not for the declared artifact {name}",
            0,
            "examples",
        )
        return gate, GateFailure(FailureCause.UNDETERMINED)
    if not evidence.fetch.ok:
        metrics = absence_evidence(evidence.fetch)
        gate = _gate(
            "data_present", TestStatus.FAIL, f"{name} was not fetched", 0, "examples", metrics
        )
        failure = evidence.fetch.failure
        if failure is not None and failure.known_cause is FailureCause.ARTIFACT_ABSENT:
            # the attempts are those the claim fixed before the lock, never the fetcher's
            required = int(ctx.plan["absent_artifact"]["attempts"])
            done = min(failure.attempts_completed, len(metrics.get("absent_http_statuses", [])))
            failure = GateFailure(FailureCause.ARTIFACT_ABSENT, done, required)
        return gate, failure
    if evidence.split_counts is None:
        gate = _gate(
            "data_present",
            TestStatus.INCONCLUSIVE,
            f"the splits of {name} were not read",
            0,
            "examples",
        )
        return gate, GateFailure(FailureCause.UNDETERMINED)
    tolerance = declared["size_tolerance"]
    wrong = []
    for split, spec in declared["splits"].items():
        count = evidence.split_counts.get(split)
        if count is None or count < 1 or abs(count - spec["expected_examples"]) > tolerance:
            wrong.append(f"{split}: {count} examples, expected {spec['expected_examples']}")
    counts = {s: evidence.split_counts.get(s) for s in declared["splits"]}
    own = evidence.split_counts.get(ctx.claim["metric"]["split"]) or 0
    if wrong:
        gate = _gate(
            "data_present", TestStatus.FAIL, "; ".join(wrong), own, "examples", {"splits": counts}
        )
        return gate, GateFailure(FailureCause.UNDETERMINED)  # never an artifact cause
    gate = _gate(
        "data_present",
        TestStatus.PASS,
        "every split at its size",
        own,
        "examples",
        {"splits": counts},
    )
    return gate, None


def _stop_cause(values: Sequence[Value]) -> FailureCause:
    for outcome in (
        orc.Outcome.REFUTE_ERROR,
        orc.Outcome.NOT_EXECUTED,
        orc.Outcome.BUDGET_EXHAUSTED,
        orc.Outcome.OPERATIONAL_GUARD,
        orc.Outcome.FAILED,
    ):
        if any(v.outcome is outcome for v in values):
            return _STOPS[outcome]
    return FailureCause.UNDETERMINED


def run_completed(values: Sequence[Value]):
    done = sum(1 for v in values if v.outcome is orc.Outcome.COMPLETED)
    if done == len(values):
        return _gate("run_completed", TestStatus.PASS, "every base run ended", done, "runs"), None
    cause = _stop_cause([v for v in values if v.outcome is not orc.Outcome.COMPLETED])
    reasons = "; ".join(v.reason for v in values if v.reason)
    if cause is FailureCause.UNDETERMINED and all(
        v.outcome in (orc.Outcome.COMPLETED, orc.Outcome.FAILED) for v in values
    ):
        # a failed run: INCONCLUSIVE by default (item D), whatever its exit code
        gate = _gate("run_completed", TestStatus.FAIL, reasons, done, "runs")
        return gate, GateFailure(FailureCause.UNDETERMINED)
    return _gate("run_completed", TestStatus.INCONCLUSIVE, reasons, done, "runs"), GateFailure(
        cause
    )


# ---- the coverage of metric_extracted (1.5a, W3.12a to W3.12e) ---------------------------------

_COUNT = re.compile(r"^\d+$")
_WS = re.compile(r"[ \t\n\r]*")


@dataclass(frozen=True)
class Piece:
    """One piece of evidence a route read: its source (a file of the run's folder, the
    run's log, or the hook's log) and what it read there: a span of characters, the
    position of a hook event, or the whole file (``end`` None). Two pieces are the same
    evidence when they read overlapping parts of one source, whatever the selectors that
    reached them (W3.12a: the gate compares what the routes resolve to)."""

    source: str
    start: int
    end: int | None

    def overlaps(self, other: Piece) -> bool:
        if self.source != other.source:
            return False
        mine = self.end if self.end is not None else float("inf")
        theirs = other.end if other.end is not None else float("inf")
        return self.start < theirs and other.start < mine


@dataclass(frozen=True)
class RouteReading:
    """What one coverage route showed for one base run of one method: the examples it
    counted (None: the route gave no evidence, with its reason), the metric it gives in
    the claim's unit (when it gives one), the pieces it read, and whether it found a
    conflict or a failure of the hook, which makes the gate ``INCONCLUSIVE`` whatever the
    other routes show."""

    route: str
    count: int | None = None
    value: Decimal | None = None
    pieces: tuple[Piece, ...] = ()
    note: str = ""
    blocking: bool = False


def _relative_file(spec: str, seed: int | None) -> PurePosixPath:
    relative = spec.replace("{seed}", str(seed)) if "{seed}" in spec else spec
    posix = PurePosixPath(relative)
    if posix.is_absolute() or ".." in posix.parts or "\\" in relative:
        raise ex.ExtractionError(f"a coverage file must be relative, without '..': {relative!r}")
    return posix


def _json_span(text: str, steps: Sequence[str | int]) -> tuple[int, int]:
    """The span of the value a JSON path names, in the document's own text."""
    decoder = json.JSONDecoder()

    def skip(i: int) -> int:
        return _WS.match(text, i).end()

    def expect(i: int, char: str) -> int:
        if i >= len(text) or text[i] != char:
            raise ValueError(f"expected {char!r} at {i}")
        return skip(i + 1)

    i = skip(0)
    for step in steps:
        if isinstance(step, int):
            i = expect(i, "[")
            for _ in range(step):
                _, i = decoder.raw_decode(text, i)
                i = expect(skip(i), ",")
            continue
        i = expect(i, "{")
        while True:
            if i >= len(text) or text[i] != '"':
                raise ValueError(f"expected a key at {i}")
            key, i = json.decoder.scanstring(text, i + 1)
            i = expect(skip(i), ":")
            if key == step:
                break
            _, i = decoder.raw_decode(text, i)
            i = expect(skip(i), ",")
    _, end = decoder.raw_decode(text, i)
    return i, end


def _csv_fields(text: str) -> list[tuple[int, int, int, int, str]]:
    """(row, column, start, end, value) of every field, in the csv module's default
    dialect (comma, double quote, a doubled quote inside a quoted field)."""
    out, i, row, col, n = [], 0, 0, 0, len(text)
    while i < n:
        start = i
        if text[i] == '"':
            parts, j = [], i + 1
            while True:
                k = text.index('"', j)
                parts.append(text[j:k])
                if text.startswith('""', k):
                    parts.append('"')
                    j = k + 2
                    continue
                j = k + 1
                break
            if j < n and text[j] not in ",\r\n":
                # the csv module keeps text after a closing quote; this locator does not
                raise ValueError(f"text after a closing quote at {j}")
            value = "".join(parts)
        else:
            j = i
            while j < n and text[j] not in ",\r\n":
                j += 1
            value = text[i:j]
        out.append((row, col, start, j, value))
        if j >= n:
            break
        if text[j] == ",":
            i, col = j + 1, col + 1
            if i == n:
                out.append((row, col, i, i, ""))
            continue
        i = j + 2 if text.startswith("\r\n", j) else j + 1
        row, col = row + 1, 0
    return out


def _csv_span(text: str, column: str, row_spec: Mapping[str, str]) -> tuple[int, int]:
    """The span of the one cell the CSV selector reads. The locator's fields must be
    exactly the rows the csv module reads (the reader of ``metric_extraction``); any
    difference abandons the span (Codex review)."""
    by_row: dict[int, dict[int, tuple[int, int, str]]] = {}
    for r, c, s, e, v in _csv_fields(text):
        by_row.setdefault(r, {})[c] = (s, e, v)
    located = [
        [cell[2] for _, cell in sorted(cells.items())] for _, cells in sorted(by_row.items())
    ]
    if located != list(csv.reader(io.StringIO(text, newline=""))):
        raise ValueError("the locator and the csv module read different rows")
    names = [cell[2] for _, cell in sorted(by_row.get(0, {}).items())]
    at, key = names.index(column), names.index(row_spec["column"])
    hits = [
        cells[at]
        for r, cells in by_row.items()
        if r > 0 and at in cells and key in cells and cells[key][2] == row_spec["equals"]
    ]
    if len(hits) != 1:
        raise ValueError(f"{len(hits)} rows match")
    return hits[0][0], hits[0][1]


def _piece(selector: Mapping[str, Any], source: str, text: str) -> Piece:
    """What a selector read, as a span of its source's text. When the span cannot be
    found, the piece is the whole source, so it overlaps anything read there."""
    try:
        if selector.get("json_path") is not None:
            start, end = _json_span(text, ex.parse_json_path(selector["json_path"]))
        elif selector.get("csv") is not None:
            start, end = _csv_span(text, selector["csv"]["column"], selector["csv"]["row"])
        else:
            regex = selector["regex"]
            (match,) = list(re.finditer(regex["pattern"], text))
            start, end = match.start(regex["group"]), match.end(regex["group"])
    except (ValueError, IndexError, ex.ExtractionError):
        return Piece(source, 0, None)
    return Piece(source, start, end)


def _file_source(path: Path) -> str:
    """The identity of a file actually read: its resolved path, case-normalized, so two
    spellings of one file (``preds/./x``, ``preds/x``) are one source (Codex review)."""
    return "file:" + os.path.normcase(str(path.resolve()))


def _count(selector: Mapping[str, Any], workdir: Path, log: str, seed: int | None):
    """One count, read like ``metric_extraction`` reads a value (W3.11), and the piece it
    read. The token must be a non-negative integer."""
    got = ex.extract(dict(selector), workdir, log, seed)
    if not _COUNT.match(got.token):
        raise ex.ExtractionError(f"{got.source}: {got.token!r} is not a count of examples")
    text, source = log, "log"
    if selector["from"] == "file":
        path = workdir.joinpath(*_relative_file(selector["file"], seed).parts)
        text, source = path.read_text(encoding="utf-8"), _file_source(path)
    return int(got.token), _piece(selector, source, text)


def _interval(token: str, rounding: str) -> tuple[Decimal, Decimal]:
    """The values that print as ``token`` (section 1.7), in the token's unit: the link of
    one route's value to the printed value. ``unknown`` is section 1.7's interval, which
    holds both the rounded and the truncated readings. It never decides agreement between
    two routes: with no rounding known only identical values agree (``metric_extracted``)."""
    interval = rc.printed_interval(token, rounding)
    return interval.lower, interval.upper


def _inside(value: Decimal, token: str, token_unit: str, rounding: str) -> bool:
    """Whether a fraction prints as ``token`` (``_interval``), widened by the epsilon of the
    decision table."""
    lower, upper = _interval(token, rounding)
    x = value * rc.unit_factor("fraction", token_unit)
    eps = Decimal("1e-9") * max(Decimal(1), abs(x))
    return lower - eps <= x <= upper + eps


def _labels_sha256(values: Sequence[Any]) -> str | None:
    """The SHA-256 of the canonical JSON array of labels (W3.12d), or None when a label is
    not an int or a str."""
    out = []
    for v in values:
        if type(v) is not int and type(v) is not str:
            return None
        out.append(v)
    return hashlib.sha256(canonical_bytes(out)).hexdigest()


@dataclass(frozen=True)
class _RunEvidence:
    """One base run of one method, as the coverage routes see it."""

    role: str  # the method whose evidence this is
    seed: int | None
    workdir: Path  # the folder of the container that ran it
    log: str
    token: ex.Extracted | None  # what metric_extraction read for this method
    token_unit: str


def _rounding(ctx: ClaimContext) -> str:
    """The printed rounding the routes' values are judged with: the claim's
    ``metric_recompute.printed_rounding``, or ``unknown`` when ``metric_recompute`` does not
    apply, since no rounding is then declared. ``unknown`` never loosens all_must_agree:
    two routes' values agree only when they are identical (``metric_extracted``; the
    maintainer's condition of 2026-10-16). The link of one route's value to the printed
    value uses section 1.7's interval for ``unknown`` (``_interval``)."""
    mr = ctx.claim["metric_recompute"]
    return mr["printed_rounding"] if mr["applies"] else "unknown"


def _as_claim_unit(fraction: Decimal, ctx: ClaimContext) -> Decimal:
    return fraction * rc.unit_factor("fraction", ctx.claim["metric"]["unit"])


def _route_reading(
    ctx: ClaimContext,
    route: Mapping[str, Any],
    evidence: Mapping[str, Any],
    run: _RunEvidence,
    recomputed: Decimal | None,
) -> RouteReading:
    name = route["route"]
    rounding = _rounding(ctx)
    identity = evidence.get("split_identity") or {}
    try:
        if name == "printed_count":
            count, piece = _count(route["count"], run.workdir, run.log, run.seed)
            return RouteReading(name, count, pieces=(piece,))
        if name == "sufficient_statistics":
            correct, piece_c = _count(route["correct"], run.workdir, run.log, run.seed)
            total, piece_t = _count(route["total"], run.workdir, run.log, run.seed)
            if total < 1 or correct > total:
                return RouteReading(name, note=f"correct {correct} of total {total}", blocking=True)
            right = correct if ctx.claim["metric"]["name"] == "accuracy" else total - correct
            fraction = Decimal(right) / Decimal(total)
            if run.token is not None and not _inside(
                fraction, run.token.token, run.token_unit, rounding
            ):
                return RouteReading(
                    name,
                    note=f"{right}/{total} is not the printed {run.token.token}",
                    blocking=True,
                )
            value = _as_claim_unit(fraction, ctx)
            return RouteReading(name, total, value, (piece_c, piece_t))
        if name == "saved_predictions":
            mr = ctx.claim["metric_recompute"]
            file = mr["predictions"]["file"].replace("{seed}", str(run.seed))
            method_name = (ctx.comparison or {}).get(run.role)
            if method_name is not None:
                file = file.replace("{method}", str(method_name))
            path = run.workdir.joinpath(*_relative_file(file, run.seed).parts)
            data = rc.read_predictions(
                path, mr["predictions"]["format"], mr["predictions"]["fields"]
            )
            labels = data["y_true"].tolist()
            digest = _labels_sha256(labels)
            if digest != identity.get("labels_sha256"):
                # another split, or the claim's split in another order (W3.12d, limitation)
                return RouteReading(name, note="the saved labels are not the split's, in its order")
            # its value is the metric recomputed from these predictions (1.7), so it is
            # compared with the other routes' values (W3.12e)
            whole = Piece(_file_source(path), 0, None)
            return RouteReading(name, len(labels), recomputed, (whole,))
        return _hook_reading(ctx, route, identity, run, rounding)
    except (ex.ExtractionError, rc.RecomputeError, OSError, ValueError, KeyError) as exc:
        # a hook whose log could not be examined is a failure of the hook (W3.12c): it
        # blocks whatever the other routes show (Codex review)
        return RouteReading(name, note=str(exc), blocking=name == "hook")


def _hook_reading(ctx, route, identity, run: _RunEvidence, rounding: str) -> RouteReading:
    """(b): exactly one committed event of the run's hook log bound to the metric (the
    declared function), the split (its labels), the run, and the selected evaluation (the
    cited call site). Anything else is INCONCLUSIVE whatever the other routes show
    (W3.12c): no log (no final record), a failure of the hook, none or several bound
    events, or a returned value outside the printed interval."""
    path = run.workdir.joinpath(*PurePosixPath(ch.HOOK_LOG).parts)
    if not path.is_file():
        return RouteReading("hook", note="no hook log (no final record)", blocking=True)
    records, failures = ch.read_log(path.read_bytes())
    if not failures:
        events, failures = ch.committed_events(records)
    if failures:
        return RouteReading("hook", note="; ".join(failures), blocking=True)
    site = route["call_site"]
    root = run.workdir.resolve()

    def bound(event: Mapping[str, Any]) -> bool:
        try:
            file = Path(event["call_site"]["file"]).resolve().relative_to(root).as_posix()
        except ValueError:
            return False
        first, last = site["lines"]
        return (
            event["function"] == route["function"]
            and file == site["file"]
            and first <= event["call_site"]["line"] <= last
            and event["labels_sha256"] == identity.get("labels_sha256")
        )

    matching = [e for e in events if bound(e)]
    if len(matching) != 1:
        return RouteReading(
            "hook",
            note=f"{len(matching)} events bound to the metric, split and call site",
            blocking=True,
        )
    event = matching[0]
    value = None
    if event["result"] != "unread" and run.token is not None:
        try:
            returned = Decimal(event["result"])
            agrees = _inside(returned, run.token.token, run.token_unit, rounding)
        except (ArithmeticError, ValueError):
            agrees = False
        if not agrees:
            return RouteReading(
                "hook",
                note=f"the call returned {event['result']}, not the printed {run.token.token}",
                blocking=True,
            )
        value = _as_claim_unit(returned, ctx)
    piece = Piece("hook:" + os.path.normcase(str(path.resolve())), event["seq"], event["seq"] + 1)
    return RouteReading("hook", event["n_examples"], value, (piece,))


@dataclass(frozen=True)
class RunCoverage:
    """The readings of one base run of one method, and the interval of values that print
    as its token, in the claim's unit (``printed_rounding``, or ``unknown``)."""

    readings: list[RouteReading]
    interval: tuple[Decimal, Decimal] | None


def _printed(ctx: ClaimContext, run: _RunEvidence) -> tuple[Decimal, Decimal] | None:
    if run.token is None:
        return None
    lower, upper = _interval(run.token.token, _rounding(ctx))
    factor = rc.unit_factor(run.token_unit, ctx.claim["metric"]["unit"])
    return lower * factor, upper * factor


def coverage_readings(ctx: ClaimContext, harness: Harness, values, ids, records, recomputed):
    """Every declared route of every base run of every method (W3.12a), by (seed, method).
    ``recomputed`` gives, by (seed, method), the metric recomputed from that run's saved
    predictions (in the claim's unit), when ``metric_recompute`` computed it."""
    out: dict[tuple[int | None, str], RunCoverage] = {}
    for seed, by_role in values.items():
        for role in ["method", "reference"] if ctx.comparison is not None else ["method"]:
            holder_role = (
                "reference" if role == "reference" and ctx.separate_reference else "method"
            )
            value = by_role[holder_role]
            evidence = ctx.claim["coverage_evidence"][role]
            if value.outcome is not orc.Outcome.COMPLETED:
                out[(seed, role)] = RunCoverage(
                    [RouteReading(r["route"], note=value.reason) for r in evidence["routes"]],
                    None,
                )
                continue
            cid = ids[(seed, holder_role)]
            record = records[cid]
            run_spec = ctx.claim["run"] if role == "method" else ctx.comparison["reference_run"]
            run = _RunEvidence(
                role,
                seed,
                harness.workspaces[cid],
                record.result.log_path.read_text(encoding="utf-8", errors="replace"),
                value.tokens.get(role),
                run_spec["metric_extraction"]["unit"],
            )
            mine = recomputed.get((seed, role))
            out[(seed, role)] = RunCoverage(
                [_route_reading(ctx, r, evidence, run, mine) for r in evidence["routes"]],
                _printed(ctx, run),
            )
    return out


def metric_extracted(ctx: ClaimContext, values: Sequence[Value], readings):
    """Every base run gave a finite value for every reading, and its coverage is shown
    (1.5a): for every base seed and every method, at least one declared route gives a count
    of examples; every route that gives one agrees (``all_must_agree``) with the others on
    the count, with the split's declared size, and, among the routes that give a value
    (the recomputed metric of (c), the ratio of (d), the returned value of (b)), on the value
    within the printed rounding, or exactly when no rounding is known; no route found a
    conflict or a failure of the hook; and,
    with the same runs, the method and the reference never read overlapping evidence. A
    printed value alone shows no examples: with no route that closes the chain, the gate
    is ``INCONCLUSIVE``, never a raw PASS."""
    roles = ["method", "reference"] if ctx.comparison is not None else ["method"]
    errors = [f"{r}: {v.errors[r]}" for v in values for r in roles if r in v.errors]
    if errors:
        gate = _gate("metric_extracted", TestStatus.FAIL, "; ".join(errors), 0, "examples")
        return gate, GateFailure(FailureCause.UNDETERMINED)
    expected = ctx.claim["metric"]["n_examples"]
    problems, shown = [], {}
    for (seed, role), run in readings.items():
        where = f"{role} seed={seed}"
        found = run.readings
        for r in found:
            if r.blocking:
                problems.append(f"{where}: {r.route}: {r.note}")
        counts = {r.route: r.count for r in found if r.count is not None}
        shown[where] = sorted(counts)
        if not counts:
            notes = "; ".join(f"{r.route}: {r.note}" for r in found)
            problems.append(f"{where}: no route shows the examples ({notes})")
        elif len(set(counts.values())) > 1:
            problems.append(f"{where}: the routes disagree on the count {counts}")
        elif next(iter(counts.values())) != expected:
            problems.append(
                f"{where}: {next(iter(counts.values()))} examples, the split declares {expected}"
            )
        # with two routes or more that give a value, each must print as the token (W3.12e);
        # with (c) alone, its value against the printed one is metric_recompute (1.7, fatal)
        given = {r.route: r.value for r in found if r.count is not None and r.value is not None}
        if len(given) > 1 and run.interval is not None:
            lower, upper = run.interval
            outside = {
                k: str(v)
                for k, v in given.items()
                if not (
                    lower - Decimal("1e-9") * max(Decimal(1), abs(v))
                    <= v
                    <= upper + Decimal("1e-9") * max(Decimal(1), abs(v))
                )
            }
            if outside:
                problems.append(
                    f"{where}: the routes disagree on the value: {outside} outside the "
                    f"printed interval [{lower}, {upper}]"
                )
            elif _rounding(ctx) == "unknown" and len(set(given.values())) > 1:
                # no rounding known: only identical values agree (all_must_agree is never
                # loosened, the maintainer's condition of 2026-10-16)
                shown_values = {k: str(v) for k, v in given.items()}
                problems.append(
                    f"{where}: the routes disagree on the value {shown_values} (no rounding "
                    "is known, so only identical values agree)"
                )
    if ctx.comparison is not None and not ctx.separate_reference:
        for seed in sorted({s for s, _ in readings}, key=str):

            def pieces(role: str, seed=seed) -> list[Piece]:
                found = readings[(seed, role)].readings
                return [p for r in found if r.count is not None for p in r.pieces]

            if any(a.overlaps(b) for a in pieces("method") for b in pieces("reference")):
                problems.append(f"seed={seed}: the method and the reference count one evidence")
    if problems:
        gate = _gate(
            "metric_extracted",
            TestStatus.INCONCLUSIVE,
            "; ".join(problems),
            0,
            "examples",
            {"routes_with_evidence": shown},
        )
        return gate, GateFailure(FailureCause.UNDETERMINED)
    return _gate(
        "metric_extracted",
        TestStatus.PASS,
        "every run gave its value; its examples are shown by the declared routes",
        expected,
        "examples",
        {"routes_with_evidence": shown},
    ), None


def _base_series(ctx: ClaimContext, values: Mapping[int | None, Mapping[str, Value]]):
    """The compared value of each base seed, in the order of the claim's seeds, with None
    for a run that gave nothing (requirement 3): ``x`` for a value claim, the oriented
    ``d`` for a comparison, paired by seed."""
    seeds = list(values)
    if ctx.comparison is None:
        return [values[s]["method"].value("method") for s in seeds]
    method = [values[s]["method"].value("method") for s in seeds]
    reader = "reference" if ctx.separate_reference else "method"
    reference = [values[s][reader].value("reference") for s in seeds]
    return rp.oriented_differences(method, reference, ctx.comparison["orientation"])


def _recompute(
    ctx: ClaimContext, harness: Harness, base: Mapping[int | None, Mapping[str, Value]], ids
):
    """``metric_recompute`` over every base run (1.7), with the same token the base read
    (requirement 4), and the metric each run's predictions give (Refute's own
    implementation, in the claim's unit) by (seed, method), for the coverage routes."""
    mr = ctx.claim["metric_recompute"]
    conv_raw = mr["convention"]
    labels = conv_raw.get("labels")
    conv = rc.Convention(
        metric=conv_raw.get("metric", ""),
        scale=conv_raw.get("scale", ""),
        labels=tuple(labels) if isinstance(labels, list) else labels,
        average=conv_raw.get("average"),
        pos_label=conv_raw.get("pos_label"),
        zero_division=conv_raw.get("zero_division"),
    )
    n_examples = ctx.claim["metric"]["n_examples"]
    unit = ctx.claim["metric"]["unit"]
    methods = [("method", ctx.claim["run"])]
    if ctx.comparison is not None:
        methods.append(("reference", ctx.comparison["reference_run"]))
    names = {
        "method": (ctx.comparison or {}).get("method"),
        "reference": (ctx.comparison or {}).get("reference"),
    }
    outcomes, expected, recomputed = [], [], {}
    for seed, by_role in base.items():
        for role, run in methods:
            label = f"seed={seed}" if ctx.comparison is None else f"{names[role]}:seed={seed}"
            expected.append(label)
            holder = by_role[
                "reference" if role == "reference" and ctx.separate_reference else "method"
            ]
            token = holder.tokens.get(role)
            if token is None:
                continue  # no printed value: not recomputed (INCONCLUSIVE by the rule)
            cid = ids[
                (seed, "reference" if role == "reference" and ctx.separate_reference else "method")
            ]
            file = mr["predictions"]["file"].replace("{seed}", str(seed))
            if names[role] is not None:
                file = file.replace("{method}", str(names[role]))
            path = harness.workspaces[cid] / file
            try:
                data = rc.read_predictions(
                    path, mr["predictions"]["format"], mr["predictions"]["fields"]
                )
            except (rc.RecomputeError, OSError, ValueError) as exc:
                outcomes.append(
                    rc.RunOutcome(label, TestStatus.INCONCLUSIVE, f"predictions: {exc}")
                )
                continue
            outcome = rc.recompute_run(
                label,
                conv,
                token.token,
                run["metric_extraction"]["unit"],
                unit,
                mr["printed_rounding"],
                data,
                n_examples,
                harness.second,
            )
            outcomes.append(outcome)
            if "own" in outcome.details:
                recomputed[(seed, role)] = Decimal(repr(outcome.details["own"]))
    return rc.metric_recompute_result(outcomes, expected), recomputed


# ---- the attacks -----------------------------------------------------------------------------


def _prerequisites(name: str, values: Sequence[Value], used: Sequence[Decimal | None]):
    """The run and the metric of an attack, from the evidence it used (requirement 7):
    the runs that ended, and the values they gave."""
    run_name, metric_name = prerequisite_names(name)
    ended = sum(1 for v in values if v.outcome is orc.Outcome.COMPLETED)
    valid = sum(1 for u in used if u is not None)

    def check(n, count, unit, what):
        status = TestStatus.PASS if count > 0 else TestStatus.INCONCLUSIVE
        return TestResult(
            n, status, Severity.GATE, f"{count} {what}", coverage=count, coverage_unit=unit
        )

    return check(run_name, ended, "runs", "runs ended"), check(
        metric_name, valid, "values", "values read"
    )


def _series(
    ctx: ClaimContext, step_values: Mapping[str, Mapping[str, Value]], order: Sequence[str]
):
    """The compared values of an attack's runs, in a fixed order, with None for a run that
    gave nothing; for a comparison, the oriented differences of the pair of each run."""
    out = []
    for tag in order:
        by_role = step_values[tag]
        x = by_role["method"].value("method")
        if ctx.comparison is None:
            out.append(x)
            continue
        reader = "reference" if ctx.separate_reference else "method"
        y = by_role[reader].value("reference") if reader in by_role else None
        out.append(rp.oriented_differences([x], [y], ctx.comparison["orientation"])[0])
    return out


def _complete(evidence: DatasetEvidence, split: str, items: Sequence | None) -> bool:
    """A read of a split covers every example the dataset check counted (Codex review of
    #110): a partial read is never taken for the split."""
    counts = evidence.split_counts
    return items is not None and counts is not None and counts.get(split) == len(items) > 0


def _mean_bracket(values: Sequence[Decimal]) -> tuple[Decimal, Decimal]:
    mean = rp.exact_mean(values)
    exact = rp._finite_decimal(mean)  # noqa: SLF001 - the exact path of reproduction.py
    if exact is not None:
        return exact, exact
    return rp._rounded(mean, ROUND_FLOOR), rp._rounded(mean, ROUND_CEILING)  # noqa: SLF001


def _host_trivial_baseline(ctx: ClaimContext, evidence: DatasetEvidence | None, base_values):
    params = ctx.attack("trivial_baseline")["params"]
    metric = ctx.claim["metric"]
    if evidence is None or evidence.labels is None:
        return None, "the labels could not be read"
    try:
        train = list(evidence.labels("train")) if params["kind"] == "majority" else None
        test = list(evidence.labels(metric["split"])) if params["kind"] == "majority" else None
        if params["kind"] == "majority" and not (
            _complete(evidence, "train", train) and _complete(evidence, metric["split"], test)
        ):
            return None, "the labels read are not every example of their split"
        baseline = at.trivial_baseline_value(
            params["kind"], params["labels"], metric["name"], metric["unit"], train, test
        )
    except (ValueError, OSError, KeyError) as exc:
        return None, f"the baseline could not be computed: {exc}"
    if ctx.comparison is None:
        tol = ctx.tolerance()
    else:
        c = ctx.comparison
        tol = pr.one_number(
            c["reported_method"], ctx.params(), _uncertainty(c["uncertainty_method"])
        )
    xs = [v for v in base_values if v is not None]
    if not xs or len(xs) < len(base_values):
        return None, "the base mean needs every base run"
    low, high = _mean_bracket(xs)
    first = at.trivial_baseline(low, baseline, metric["higher_is_better"], tol)
    second = at.trivial_baseline(high, baseline, metric["higher_is_better"], tol)
    if first.status is not second.status:
        result = at.attack_result(
            "trivial_baseline", TestStatus.INCONCLUSIVE, baseline.coverage, rp.UNDECIDABLE_MEAN
        )
        result.coverage_unit = baseline.coverage_unit
        return result, ""
    return first, ""


@dataclass
class ClaimOutcome:
    key: str
    verdict: ClaimVerdict
    base: list[TestResult]
    attacks: list[Attack]
    failures: dict[str, GateFailure]
    computed: PaperVerdict  # the verdict before the accounting check
    notes: list[str] = field(default_factory=list)


@dataclass
class PaperOutcome:
    run: orc.PaperRun | None
    ladder: ld.LadderResult
    claims: list[ClaimOutcome]
    profile: PaperProfile


# ---- the paper -------------------------------------------------------------------------------


class PaperIntegration:
    """Runs one resolved claim file on a harness and reads every check from the evidence."""

    def __init__(self, claim_file: Mapping[str, Any], harness: Harness) -> None:
        self.file = claim_file
        self.plan = claim_file["test_plan"]
        self.harness = harness
        self.contexts = [ClaimContext(t, self.plan) for t in claim_file["targets"]]
        found_env, found_req = harness.ladder_inputs
        self.rungs = ld.ladder_rungs(found_env, found_req, self.plan["build"]["python_ladder"])
        self._runner: orc.PaperRunner | None = None
        self._rung_results: dict[str, ld.RungResult] = {}
        # one folder of its own per container (requirement 10)
        folders = [Path(p).resolve() for p in harness.workspaces.values()]
        if len(set(folders)) != len(folders):
            raise ValueError("every container needs a folder of its own")
        self._outputs: dict[str, list[str]] = {}
        for ctx in self.contexts:
            for step in ["base", *[n for n in ctx.applicable() if n in CONTAINER_ATTACKS]]:
                for cid, role, seed, _ in _runs(ctx, step):
                    self._outputs[cid] = _outputs(ctx, role, seed)

    # -- specs

    def _spec(self, cid: str, argv: Sequence[str], stage: tuple[float, float]):
        active, no_progress = stage
        env = {**self.harness.base_env, **{k: str(v) for k, v in self.plan["threads"].items()}}
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", cid)

        def make(threshold: int) -> RunSpec:
            # the outputs this run is read from must not exist before it starts, so every
            # value read afterwards was written by this run (requirement 10)
            stale = [
                p for p in self._outputs.get(cid, []) if (self.harness.workspaces[cid] / p).exists()
            ]
            if stale:
                raise ValueError(f"{cid}: outputs present before the run: {stale}")
            return RunSpec(
                argv=self.harness.command(argv),
                workdir=self.harness.workspaces[cid],
                env=dict(env),
                log_path=self.harness.logs / f"{safe}.log",
                threshold_usec=threshold,
                active_time_limit_s=active,
                no_progress_s=no_progress,
            )

        return orc.Container(cid, make)

    def _setup(self) -> orc.Step | None:
        applicable = [r for r in self.rungs if r.applicable]
        if not applicable:
            return None
        stage = (
            self.plan["stages"]["build"]["active_time_limit_hours"] * HOUR_S,
            self.plan["stages"]["build"]["no_progress_hours"] * HOUR_S,
        )
        containers = [
            self._spec(f"setup/build/{r.name}", self.harness.build_command(r), stage)
            for r in applicable
        ]
        by_id = {f"setup/build/{r.name}": r for r in applicable}

        def fallback(record: orc.ContainerRecord) -> str:
            # each rung is classified once; the ladder's gate reads the same result
            # (Codex review of #110)
            result = self.harness.classify_build(by_id[record.container_id], record.result)
            self._rung_results[record.container_id] = result
            if result.outcome is orc.Outcome.COMPLETED:
                return "completed"
            if result.outcome is orc.Outcome.FAILED and result.cause is FailureCause.BUILD_LADDER:
                return "next"
            return "stop"

        return orc.Step("build", containers, fallback=fallback)

    def _step(self, ctx: ClaimContext, step: str, stage: str) -> orc.Step:
        containers = [
            self._spec(cid, _argv(ctx, role, seed, extra), ctx.stage(stage))
            for cid, role, seed, extra in _runs(ctx, step)
        ]
        return orc.Step(step, containers)

    def build_plan(self) -> orc.PaperPlan | None:
        setup = self._setup()
        if setup is None:
            return None
        claims = []
        for ctx in self.contexts:
            attacks = [
                self._step(ctx, name, "attack_run")
                for name in ctx.applicable()
                if name in CONTAINER_ATTACKS
                and not (
                    name == "ablation"
                    and "config_file" in ctx.attack("ablation")["params"]["disable"]
                )
            ]
            claims.append(
                orc.ClaimPlan(
                    ctx.key,
                    [self._step(ctx, "base", "base_run")],
                    attacks,
                    lambda records, ctx=ctx: self._base_obtained(ctx, records),
                )
            )
        return orc.PaperPlan([setup], claims)

    # -- evaluation

    def _records(self, run: orc.PaperRun | None) -> dict[str, orc.ContainerRecord]:
        if run is None:
            return {}
        return {c.container_id: c for s in run.steps for c in s.containers}

    def _values(self, ctx: ClaimContext, step: str, records) -> dict[Any, dict[str, Value]]:
        """The values of one step, by seed (base, seeds, ablation) or by split seed
        (data_split) or by the single run (holdout), then by role."""
        out: dict[Any, dict[str, Value]] = {}
        for cid, role, seed, _ in _runs(ctx, step):
            tag = cid.split("/")[-1] if step == "data_split" else seed
            workdir = self.harness.workspaces[cid]
            out.setdefault(tag, {})[role] = _read(ctx, records.get(cid), workdir, role, seed)
        return out

    def _base_checks(self, ctx: ClaimContext, records, ladder: ld.LadderResult):
        values = self._values(ctx, "base", records)
        flat = [v for by_role in values.values() for v in by_role.values()]
        failures: dict[str, GateFailure] = {}
        checks: list[TestResult] = [ladder.gate]
        if ladder.failure is not None:
            failures["environment_build"] = ladder.failure
        gate, failure = data_present(ctx, self.harness.datasets.get(ctx.claim["dataset"]))
        checks.append(gate)
        if failure is not None:
            failures["data_present"] = failure
        gate, failure = run_completed(flat)
        checks.append(gate)
        if failure is not None:
            failures["run_completed"] = failure
        ids = {(seed, role): cid for cid, role, seed, _ in _runs(ctx, "base")}
        recompute_result, recomputed = None, {}
        if ctx.claim["metric_recompute"]["applies"]:
            recompute_result, recomputed = _recompute(ctx, self.harness, values, ids)
        readings = coverage_readings(ctx, self.harness, values, ids, records, recomputed)
        gate, failure = metric_extracted(ctx, flat, readings)
        checks.append(gate)
        if failure is not None:
            failures["metric_extracted"] = failure
        series = _base_series(ctx, values)
        reported_n = ctx.claim["metric"].get("reported_n_seeds")
        checks.append(rp.base_reproduction(series, ctx.predicate(), reported_n))
        if recompute_result is not None:
            checks.append(recompute_result)
        return checks, failures, values, series

    def _base_obtained(self, ctx: ClaimContext, records: Sequence[orc.StepRecord]) -> bool:
        """Asked by the runner after the claim's base step: the base reproduction is
        obtained when its gates and fatal checks pass (the attacks then run)."""
        setup = {
            c.container_id: c
            for s in (self._runner.run_record.steps if self._runner else [])
            if s.phase == orc.SETUP
            for c in s.containers
        }
        by_id = {c.container_id: c for s in records for c in s.containers}
        checks, failures, _, _ = self._base_checks(ctx, by_id, self._ladder_result(setup))
        base_names = set(BASE_GATES) | {BASE_REPRODUCTION, METRIC_RECOMPUTE}
        verdict = aggregate_claim(
            checks,
            [],
            [],
            metric_recompute_applies=ctx.claim["metric_recompute"]["applies"],
            failures=failures,
            minimums={k: v for k, v in ctx.minimums().items() if k in base_names},
        )
        return verdict.basic_reproduction_obtained

    def _ladder_result(self, records: Mapping[str, orc.ContainerRecord]) -> ld.LadderResult:
        def build(rung: ld.Rung) -> ld.RungResult:
            cid = f"setup/build/{rung.name}"
            record = records.get(cid)
            if record is None:
                return ld.RungResult(orc.Outcome.NOT_EXECUTED, None, "not reached")
            if record.result is None:
                return ld.RungResult(orc.Outcome.REFUTE_ERROR, None, record.error)
            outcome, reason = orc._outcome([record])  # noqa: SLF001
            if outcome in (
                orc.Outcome.BUDGET_EXHAUSTED,
                orc.Outcome.OPERATIONAL_GUARD,
                orc.Outcome.REFUTE_ERROR,
            ):
                # a stop on Refute's side keeps its own cause, whatever a classifier says
                return ld.RungResult(outcome, None, reason)
            if cid not in self._rung_results:  # a record the fallback did not classify
                return ld.RungResult(orc.Outcome.REFUTE_ERROR, None, "rung not classified")
            return self._rung_results[cid]

        return ld.run_ladder(self.rungs, build)

    def _attack(self, ctx, name, records, base_values, base_series) -> tuple[Attack, str]:
        evidence = self.harness.datasets.get(ctx.claim["dataset"])
        if name == "leakage":
            if evidence is None or evidence.example_hashes is None:
                return Attack(name), "the examples could not be hashed"
            try:
                train = list(evidence.example_hashes("train"))
                test = list(evidence.example_hashes(ctx.claim["metric"]["split"]))
            except (OSError, ValueError, KeyError) as exc:
                return Attack(name), f"the examples could not be hashed: {exc}"
            if not (
                _complete(evidence, "train", train)
                and _complete(evidence, ctx.claim["metric"]["split"], test)
            ):
                return Attack(name), "the hashes are not every example of their split"
            limit = ctx.attack("leakage")["params"]["max_overlap_fraction"]
            result = at.leakage(train, test, limit)
            run = TestResult(
                f"{name}:run",
                TestStatus.PASS if train and test else TestStatus.INCONCLUSIVE,
                Severity.GATE,
                "examples hashed",
                coverage=len(train) + len(test),
                coverage_unit="examples hashed",
            )
            metric = TestResult(
                f"{name}:metric",
                run.status,
                Severity.GATE,
                "overlap computed",
                coverage=len(test),
                coverage_unit="test examples",
            )
            return Attack(name, run, metric, result), ""
        if name == "trivial_baseline":
            # the claim's own value: x for a value claim, the method's value for a comparison
            own = [by_role["method"].value("method") for by_role in base_values.values()]
            result, why = _host_trivial_baseline(ctx, evidence, own)
            if result is None:
                return Attack(name), why
            ok = TestStatus.PASS if result.coverage else TestStatus.INCONCLUSIVE
            run = TestResult(
                f"{name}:run",
                ok,
                Severity.GATE,
                "labels read",
                coverage=result.coverage,
                coverage_unit=result.coverage_unit,
            )
            metric = TestResult(
                f"{name}:metric",
                ok,
                Severity.GATE,
                "baseline computed",
                coverage=1 if ok is TestStatus.PASS else 0,
                coverage_unit="baselines",
            )
            return Attack(name, run, metric, result), ""
        if name == "ablation" and "config_file" in ctx.attack("ablation")["params"]["disable"]:
            return Attack(name), "an ablation switched by a configuration file is not supported yet"
        values = self._values(ctx, name, records)
        flat = [v for by_role in values.values() for v in by_role.values()]
        if not any(v.outcome is not orc.Outcome.NOT_EXECUTED for v in flat):
            return Attack(name), "not executed"
        if name == "seeds":
            series = _series(ctx, values, list(values))
            result = at.seeds(series, ctx.predicate())
        elif name == "data_split":
            series = _series(ctx, values, list(values))
            result = at.data_split(series, ctx.predicate())
        elif name == "holdout":
            series = _series(ctx, values, list(values))
            params = ctx.attack("holdout")["params"]
            tol = ctx.tolerance()
            widened = pr.widen(tol, params["factor"]) if tol is not None else None
            result = at.holdout(series[0], ctx.predicate(widened), params["factor"])
        else:  # ablation, on the base seeds: d per seed, oriented
            params = ctx.attack("ablation")["params"]
            ablated = [values[s]["method"].value("method") for s in values]
            full = [base_values[s]["method"].value("method") for s in values]
            if params["orientation"] == "full_minus_ablated":
                series = rp.oriented_differences(full, ablated, "method_minus_reference")
            else:
                series = rp.oriented_differences(full, ablated, "reference_minus_method")
            tol_abl = None
            if params["mode"] == "margin":
                tol_abl = pr.ablation_tolerance(
                    params["reported_full"],
                    params["reported_ablated"],
                    ctx.params(),
                    params.get("reported_sd_full"),
                    params.get("reported_sd_ablated"),
                )
            result = at.ablation(series, params["mode"], tol_abl, params.get("g_abl"))
        run, metric = _prerequisites(name, flat, series)
        return Attack(name, run, metric, result), ""

    def evaluate(self, run: orc.PaperRun | None) -> PaperOutcome:
        records = self._records(run)
        ladder = self._ladder_result(records)
        outcomes = []
        for ctx in self.contexts:
            checks, failures, base_values, base_series = self._base_checks(ctx, records, ladder)
            attacks, notes = [], []
            obtained = bool(run and run.base_obtained.get(ctx.key))
            for name in ctx.applicable():
                if not obtained:
                    attacks.append(Attack(name))
                    continue
                attack, why = self._attack(ctx, name, records, base_values, base_series)
                attacks.append(attack)
                if why:
                    notes.append(f"{name}: {why}")
            verdict = aggregate_claim(
                checks,
                attacks,
                ctx.applicable(),
                metric_recompute_applies=ctx.claim["metric_recompute"]["applies"],
                failures=failures,
                minimums=ctx.minimums(),
            )
            computed = verdict.verdict
            if run is not None and not run.accounting_valid:
                reasons = "; ".join(run.invalid_reasons) or "unknown"
                verdict = ClaimVerdict(
                    PaperVerdict.INCONCLUSIVE, f"{ACCOUNTING_INVALID}: {reasons}"
                )
            outcomes.append(
                ClaimOutcome(ctx.key, verdict, checks, attacks, failures, computed, notes)
            )
        profile = paper_profile([(o.key, o.verdict.verdict) for o in outcomes])
        return PaperOutcome(run, ladder, outcomes, profile)

    def run(self) -> PaperOutcome:
        plan = self.build_plan()
        if plan is None:  # no rung applies: nothing can be built, nothing runs
            return self.evaluate(None)
        accountant = bg.Accountant(
            [c.key for c in self.contexts],
            margin_usec=self.harness.margin_usec,
            # the profiles are whole CPU-hours (384 / 192 / 192 or 96 / 48 / 48)
            base_pool_usec=bg.cpu_hours(int(self.plan["budget"]["base_cpu_hours"])),
            attack_pool_base_usec=bg.cpu_hours(int(self.plan["budget"]["attacks_cpu_hours"])),
        )
        self._runner = orc.PaperRunner(
            plan,
            self.harness.backend,
            accountant,
            parent_usage=self.harness.parent_usage,
            tolerance_usec=self.harness.tolerance_usec,
            timing_maxima=self.harness.timing_maxima,
        )
        return self.evaluate(self._runner.run())


def run_paper(claim_file: Mapping[str, Any], harness: Harness) -> PaperOutcome:
    """The verdict of every claim of one resolved claim file, and the paper's profile."""
    return PaperIntegration(claim_file, harness).run()
