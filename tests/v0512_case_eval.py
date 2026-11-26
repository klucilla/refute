"""The evaluator of v0.5.12 step 2's case record (``docs/validation/v0.5.12/step2/cases.json``),
shared by the standalone probe (``step2/probe.py``) and #223's suite
(``tests/test_v0512_223_cases.py``). Test-only. It runs the screen of ``src/`` on each case's
fixture, with the case's patches (fault injection only), and returns one outcome per assertion.
Exploratory, ``method_status: not_validated``.
"""

from __future__ import annotations

import copy
import json
import math
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs" / "validation" / "v0.5.12" / "step2" / "cases.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import v0512_fixtures as fx  # noqa: E402

RESERVED = {"state", "reason", "reason_prefix", "coverage", "values", "paper_threshold_crossed"}


def load() -> dict:
    return json.loads(CASES.read_text(encoding="utf-8"))


def screen():
    import importlib

    return importlib.import_module("refute.packs.tess.screen_d5")


def _gate():
    from refute.core.verdict import Severity, TestResult, TestStatus

    return [
        TestResult("snr", TestStatus.PASS, Severity.GATE, "gate", coverage=10, coverage_unit="u")
    ]


@contextmanager
def patched(mod, patches):
    saved = {}
    try:
        for p in patches:
            name = p["target"]
            saved[name] = getattr(mod, name)
            setattr(mod, name, _fake(p))
        yield
    finally:
        for name, fn in saved.items():
            setattr(mod, name, fn)


def _fake(p):
    if "raises" in p:
        exc = {"ValueError": ValueError, "TypeError": TypeError}[p["raises"]]

        def boom(*args, **kwargs):
            raise exc("fault injection (v0.5.12 step 2)")

        return boom
    ret = p["returns"]
    if p["target"] == "_trapezoid":
        return lambda *args, **kwargs: (dict(ret), 50)

    def parity_fit(t, f, s, period, t0c, duration, overall, parity):
        return tuple(ret["odd" if parity == 1 else "even"]), 50

    return parity_fit


def records(case: dict) -> tuple[dict, dict]:
    """(records by name, extras) for one case on the current screen code."""
    s = screen()
    fixture = fx.build(case["recipe"])
    flat = SimpleNamespace(time=fixture["t"], flux=fixture["f"], flux_err=fixture["s"])
    cand = SimpleNamespace(period=fixture["period"], t0=fixture["t0"], duration=fixture["duration"])
    star = SimpleNamespace(**fixture["star"]) if fixture["star"] else None
    args = (fixture["t"], fixture["f"], fixture["s"], cand.period, cand.t0, cand.duration)
    entry, extras = case["entry"], {}
    with patched(s, case["patches"]):
        if entry == "f1_box":
            return {"F1": s.f1_box(*args)}, extras
        if entry == "report_only":
            return s.report_only(flat, cand, star), extras
        if entry == "report_only+f1_box":
            return {"F1": s.f1_box(*args), **s.report_only(flat, cand, star)}, extras
        gate = _gate()
        before = copy.deepcopy([vars(r) for r in gate])
        rec = s.compute_screen(None if entry.endswith("no_curve") else flat, cand, gate, star)
        extras = {
            "outcome": rec["outcome"],
            "core": rec["core"],
            "gate_unchanged": before == [vars(r) for r in gate],
        }
        return {"F1": rec["core"].get("F1"), **rec["report_only"]}, extras


def _close(got, spec) -> bool:
    exp = spec["expected"]
    if got is None or exp is None:
        return got == exp
    bound = max(spec["atol"], spec["rtol"] * abs(exp))
    return math.isfinite(got) and abs(got - exp) <= bound


def evaluate(case: dict, all_cases: dict) -> list[dict]:
    """One outcome per assertion: {'assertion', 'ok', 'got', 'expected'}."""
    recs, extras = records(case)
    out = []

    def add(name, ok, got, expected):
        out.append({"assertion": name, "ok": bool(ok), "got": got, "expected": expected})

    for rname, exp in case["expect"].items():
        if rname == "isolation":
            _, ref_extras = records(all_cases[exp["same_core_and_outcome_as"]])
            add("isolation.core", extras["core"] == ref_extras["core"], extras["core"], "C06")
            same = extras["outcome"] == ref_extras["outcome"] == exp["outcome"]
            add("isolation.outcome", same, extras["outcome"], exp["outcome"])
            unchanged = extras["gate_unchanged"]
            add("isolation.gate_unchanged", unchanged, unchanged, True)
            continue
        rec = recs.get(rname) or {}
        metrics = rec.get("metrics", {})
        add(f"{rname}.state", rec.get("state") == exp["state"], rec.get("state"), exp["state"])
        if "reason" in exp:
            got = rec.get("reason")
            add(f"{rname}.reason", got == exp["reason"], got, exp["reason"])
        if "reason_prefix" in exp:
            got = rec.get("reason") or ""
            add(f"{rname}.reason_prefix", got.startswith(exp["reason_prefix"]), got, "OE_box ")
        if "coverage" in exp:
            got = rec.get("coverage")
            add(f"{rname}.coverage", got == exp["coverage"], got, exp["coverage"])
        if "paper_threshold_crossed" in exp:
            thr = rec.get("paper_thresholds", {}).get("Rp_earth")
            got = metrics.get("Rp_earth") is not None and metrics["Rp_earth"] > thr
            want = exp["paper_threshold_crossed"]
            add(f"{rname}.paper_threshold_crossed", got == want, got, want)
        for key, val in exp.items():
            if key not in RESERVED:
                add(f"{rname}.{key}", metrics.get(key) == val, metrics.get(key), val)
        for key, spec in exp.get("values", {}).items():
            got = metrics.get(key)
            add(f"{rname}.values.{key}", _close(got, spec), got, spec["expected"])
    return out


def documented_match(case: dict, outcome: dict) -> bool:
    """A failed assertion is documented only if the case record names it, with the value the
    approval code was expected to give."""
    for d in case["documented"]:
        if d["assertion"] == outcome["assertion"] and d["approval"] == outcome["got"]:
            return True
    return False
