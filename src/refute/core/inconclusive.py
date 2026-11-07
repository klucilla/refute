"""The classes of an INCONCLUSIVE test result (v0.5.1 WP4, docs/plans/v0.5.1-acceptance.md).

Domain-agnostic: a claim whose plan asks for classes (TESS discovery version 3) gets one class on
every INCONCLUSIVE test result, in ``metrics["inconclusive_class"]``, with where it came from in
``metrics["inconclusive_class_source"]``. Earlier claims never pass through here, so their outputs
keep their bytes.

The classes:

- ``outside_domain``: a declared domain excludes the candidate before data are read;
- ``insufficient_sensitivity``: the engine refused a PASS, or the data cannot reach the test's
  required precision;
- ``missing_input``: a required input is absent (stellar parameters, pixel data, a catalog scan);
- ``not_enough_data``: zero coverage, too few events or pseudo-events, or a test not run at this
  stage.

The class of a result, in this order (Claude and Codex, WP4 design review, 2026-11-07): a test not
run at this stage (``not_enough_data``, source ``stage``); the class the test set itself (source
``test``); the coverage rule's refusal (``not_enough_data``); the sensitivity rule's refusal
(``insufficient_sensitivity``); the domain pack's table of messages (source ``table``); otherwise
a fallback (``not_enough_data`` with zero coverage, ``insufficient_sensitivity`` with some), source
``fallback``, counted apart in the tallies so that an unknown message is seen.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import replace

from refute.core.verdict import TestResult, TestStatus

OUTSIDE_DOMAIN = "outside_domain"
INSUFFICIENT_SENSITIVITY = "insufficient_sensitivity"
MISSING_INPUT = "missing_input"
NOT_ENOUGH_DATA = "not_enough_data"
CLASSES = (OUTSIDE_DOMAIN, INSUFFICIENT_SENSITIVITY, MISSING_INPUT, NOT_ENOUGH_DATA)
# the verdict's class when the decisive INCONCLUSIVE tests differ: a missing input explains the
# rest; insufficient sensitivity is the residual class
PRIORITY = (MISSING_INPUT, OUTSIDE_DOMAIN, NOT_ENOUGH_DATA, INSUFFICIENT_SENSITIVITY)

CLASS_KEY = "inconclusive_class"
SOURCE_KEY = "inconclusive_class_source"
SOURCES = ("stage", "test", "coverage_rule", "sensitivity_rule", "table", "fallback")

# the fixed prefixes of the engine's refusals (core/verdict.enforce_coverage,
# core/sensitivity.enforce_sensitivity)
COVERAGE_PREFIX = "PASS refused: the check "
SENSITIVITY_PREFIX = "PASS refused: "

# a table row: (test name, message prefix, class); the name "*" matches every test, the prefix ""
# every message
TableRow = tuple[str, str, str]


def _check_class(value: object, where: str) -> str:
    if value not in CLASSES:
        raise ValueError(f"{where}: unknown INCONCLUSIVE class {value!r}")
    return str(value)


def classify(
    result: TestResult, table: Sequence[TableRow], deferred: bool = False
) -> tuple[str, str]:
    """The class of an INCONCLUSIVE ``result`` and its source (see the module's docstring)."""
    if result.status is not TestStatus.INCONCLUSIVE:
        raise ValueError(f"{result.name} is {result.status.value}, not INCONCLUSIVE")
    if deferred:
        return NOT_ENOUGH_DATA, "stage"
    explicit = result.metrics.get(CLASS_KEY)
    if explicit is not None:
        return _check_class(explicit, f"{result.name} (set by the test)"), "test"
    message = result.message or ""
    if message.startswith(COVERAGE_PREFIX):
        return NOT_ENOUGH_DATA, "coverage_rule"
    if message.startswith(SENSITIVITY_PREFIX):
        return INSUFFICIENT_SENSITIVITY, "sensitivity_rule"
    for name, prefix, cls in table:
        if name in ("*", result.name) and message.startswith(prefix):
            return _check_class(cls, f"table row {name!r}, {prefix!r}"), "table"
    zero = not (result.coverage is not None and result.coverage > 0)
    return (NOT_ENOUGH_DATA if zero else INSUFFICIENT_SENSITIVITY), "fallback"


def annotate(
    results: Iterable[TestResult], table: Sequence[TableRow], deferred: Iterable[str] = ()
) -> list[TestResult]:
    """Every INCONCLUSIVE result with its class and source in its metrics (a copy; the other
    results unchanged)."""
    later = set(deferred)
    out = []
    for result in results:
        if result.status is TestStatus.INCONCLUSIVE:
            cls, source = classify(result, table, result.name in later)
            result = replace(result, metrics={**result.metrics, CLASS_KEY: cls, SOURCE_KEY: source})
        out.append(result)
    return out


def classes_of(results: Iterable[TestResult]) -> dict[str, str]:
    """Test name -> class, for the annotated INCONCLUSIVE results."""
    return {
        r.name: r.metrics[CLASS_KEY]
        for r in results
        if r.status is TestStatus.INCONCLUSIVE and CLASS_KEY in r.metrics
    }


def verdict_class(decisive: Iterable[TestResult]) -> str | None:
    """The class of an INCONCLUSIVE verdict: the first of ``PRIORITY`` among its decisive
    INCONCLUSIVE tests' classes; None when no decisive test is INCONCLUSIVE."""
    found = set(classes_of(decisive).values())
    for cls in PRIORITY:
        if cls in found:
            return cls
    return None


VERDICTS = ("SURVIVED", "WEAKENED", "REFUTED", "INCONCLUSIVE")


def tally(records: Iterable[dict]) -> dict:
    """The tallies of WP4 (row 4.3) over one battery's records, each ``{"verdict": ...,
    "v051": <the v051 object of verdict.json>}``: the four verdict counts; the INCONCLUSIVE
    verdicts per class and, apart, per condition (``gate_not_passed``, ``expected_tests_missing``)
    and without either; the INCONCLUSIVE tests per class; the tests classified by the fallback."""
    verdicts = dict.fromkeys(VERDICTS, 0)
    by_class = dict.fromkeys(CLASSES, 0)
    by_condition: dict[str, int] = {}
    unclassified = 0
    tests_by_class = dict.fromkeys(CLASSES, 0)
    fallback = 0
    for record in records:
        verdict = record["verdict"]
        verdicts[verdict] += 1
        v051 = record.get("v051") or {}
        for entry in (v051.get("inconclusive_classes") or {}).values():
            tests_by_class[_check_class(entry["class"], "tally")] += 1
            fallback += entry.get("source") == "fallback"
        if verdict != "INCONCLUSIVE":
            continue
        cls, condition = v051.get("inconclusive_class"), v051.get("inconclusive_condition")
        if cls is not None:
            by_class[_check_class(cls, "tally")] += 1
        elif condition is not None:
            by_condition[condition] = by_condition.get(condition, 0) + 1
        else:
            unclassified += 1
    return {
        "verdicts": verdicts,
        "inconclusive_by_class": by_class,
        "inconclusive_by_condition": by_condition,
        "inconclusive_unclassified": unclassified,
        "inconclusive_tests_by_class": tests_by_class,
        "tests_classified_by_fallback": fallback,
    }


def with_classes(reason: str, results: Iterable[TestResult]) -> str:
    """The aggregation's "could not be decided: a, b" reason with each test's class:
    "could not be decided: a (class), b (class)"; any other reason unchanged."""
    head = "could not be decided: "
    if not reason.startswith(head):
        return reason
    classes = classes_of(results)
    names = [n.strip() for n in reason[len(head) :].split(",")]
    return head + ", ".join(f"{n} ({classes[n]})" if n in classes else n for n in names)
