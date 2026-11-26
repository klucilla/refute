"""v0.5.12 step 2 (#223): build the case record ``cases.json`` BEFORE any probe. It runs only the
independent oracles of ``tests/v0512_oracles.py`` on the fixtures of ``tests/v0512_fixtures.py``;
it imports nothing from ``src/`` and runs no screen code.

    launch_v3 unit step2-cases:
        {python} -I -B docs/validation/v0.5.12/step2/cases_build.py

Each case: its recipe, natural witness or fault injection, the branches of ``inventory.json`` it
reaches, its entry point, its patches (fault injection only), and its assertions: the expected
state and reason of each asserted record and each value with its source, ``atol`` and ``rtol``
(the charter's rule: |value - expected| <= max(atol, rtol*|expected|)). ``documented`` names, before
the probe, each assertion expected to fail on the approval code, with the reason and the exception;
it is never filled after a probe. The builder checks that each oracle reaches its intended
branch, and stops otherwise.
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tests"))
import v0512_fixtures as fx  # noqa: E402
import v0512_oracles as oc  # noqa: E402
from screen_reference import f1_reference  # noqa: E402

NOISE = "noise unavailable (baseline or bins)"
PINK_ODD = "depth or pink noise unavailable for the odd parity"
PINK_EVEN = "depth or pink noise unavailable for the even parity"
CLOSED = {"rtol": 1e-9}
FITTED_MODEL = {"rtol": 1e-3}
FITTED_ORACLE = {"rtol": 1e-6}
RO = ("F1_trap", "F2", "F3", "F4", "U1")
STAR = {"disposition": None, "radius_rsun": 2.0, "radius_err_rsun": 0.1}
TRAP_GRAZE = {"depth": 0.05, "q": 0.03, "q_in": 0.45, "f0": 1.0}
TRAP_GIANT = {"depth": 0.04, "q": 0.03, "q_in": 0.1, "f0": 1.0}
OVERALL = {"t0": fx.T0, "depth": 0.01, "q": 0.03, "q_in": 0.2, "f0": 1.0}


def numf(name):
    return f"numerical failure: {name}"


def ro_all(reason):
    return {r: {"state": "unavailable", "reason": reason} for r in RO}


def case(cid, title, kind, branches, entry, recipe, expect, patches=None, documented=None):
    return {
        "id": cid,
        "title": title,
        "kind": kind,
        "branches": branches,
        "entry": entry,
        "recipe": recipe,
        "patches": patches or [],
        "expect": expect,
        "documented": documented or [],
    }


def f1_na(reason):
    return {"F1": {"state": "not_assessed", "reason": reason}}


def cases() -> list[dict]:
    box = {"model": "box", "depth": 0.002, "seed": 11}
    nat, flt = "natural", "fault_injection"
    out = [
        # --- the charter's cases (v0.5.11 charter, step 1) ---
        case("C01", "a planet", nat, [], "compute_screen", {**box, "star": STAR}, {}),
        case(
            "C02",
            "a binary with unequal depths at half the period",
            nat,
            [],
            "f1_box",
            {"model": "box", "depth": 0.005, "depth_odd": 0.01, "seed": 12},
            {},
        ),
        case(
            "C03",
            "a binary with a secondary away from phase 0.5",
            nat,
            [],
            "report_only",
            {
                "model": "box",
                "depth": 0.01,
                "seed": 13,
                "secondary": {"offset_days": 1.6, "depth": 0.004},
            },
            {},
        ),
        case(
            "C04",
            "an occultation that meets F2's exception",
            nat,
            [],
            "report_only",
            {
                "model": "box",
                "depth": 0.01,
                "seed": 14,
                "secondary": {"offset_days": 1.85, "depth": 0.0005},
            },
            {},
        ),
        case(
            "C05",
            "a grazing binary (F4)",
            nat,
            [],
            "report_only",
            {"model": "trapezoid", "trapezoid": TRAP_GRAZE, "sigma": 1e-7, "seed": 15},
            {},
        ),
        case(
            "C06",
            "a giant with a star record (F3): the paper-threshold crossing",
            nat,
            [],
            "compute_screen",
            {
                "model": "trapezoid",
                "trapezoid": TRAP_GIANT,
                "sigma": 5e-5,
                "seed": 16,
                "star": STAR,
            },
            {},
        ),
        case(
            "C07",
            "the crossing's isolation: C06 without the star record",
            nat,
            [],
            "compute_screen",
            {"model": "trapezoid", "trapezoid": TRAP_GIANT, "sigma": 5e-5, "seed": 16},
            {},
        ),
        case("C08", "a null (noise only)", nat, [], "compute_screen", {"seed": 18}, {}),
        # --- F1 (the core) ---
        case(
            "N01",
            "the epoch index is not exactly representable",
            nat,
            ["B01", "B02"],
            "f1_box",
            {**box, "t0": fx.T0 + 1e16 * fx.P},
            f1_na(numf("ValueError")),
        ),
        case(
            "N02",
            "period NaN",
            nat,
            ["B03"],
            "f1_box",
            {**box, "period": float("nan")},
            f1_na("candidate not finite or not positive"),
        ),
        case(
            "N03",
            "one sigma above 1e3",
            nat,
            ["B04"],
            "f1_box",
            {**box, "mods": [{"name": "sigma_at", "index": 7, "value": 2e3}]},
            f1_na("invalid_uncertainty"),
        ),
        case(
            "N04",
            "15 cadences",
            nat,
            ["B05"],
            "f1_box",
            {**box, "mods": [{"name": "first", "count": 15}]},
            f1_na("fewer than 20 valid points"),
        ),
        case(
            "N05",
            "no baseline (T = 3.5 d)",
            nat,
            ["B06", "B12", "B13"],
            "report_only+f1_box",
            {**box, "duration": 3.5},
            {
                **f1_na(NOISE),
                "F2": {"state": "unavailable", "reason": "noise unavailable"},
                "U1": {"state": "unavailable", "reason": "noise unavailable"},
            },
        ),
        case(
            "N06",
            "fewer than 3 baseline bins",
            nat,
            ["B06"],
            "f1_box",
            {
                **box,
                "mods": [
                    {"name": "window", "start": fx.T0 - 2.2 * fx.T, "end": fx.T0 + 0.5 * fx.T}
                ],
            },
            f1_na(NOISE),
        ),
        case(
            "N07",
            "a constant baseline: s2 = 0 (corrected); the pink noise is 0 (approval)",
            nat,
            ["B06"],
            "f1_box",
            {**box, "mods": [{"name": "constant_baseline"}]},
            f1_na(NOISE),
            documented=[
                {
                    "assertion": "F1.reason",
                    "approval": PINK_ODD,
                    "raises": "AssertionError",
                    "why": "approval: sigma_w = sigma_r = 0, so _pink returns None "
                    "(line 245); corrected: s2 = 0 (revision 1, section 4)",
                }
            ],
        ),
        case(
            "N08",
            "one baseline flux 1e300 at sigma 1e-12: the weighted sum overflows",
            nat,
            ["B06"],
            "f1_box",
            {
                **box,
                "mods": [{"name": "set", "where": "baseline_first", "flux": 1e300, "sigma": 1e-12}],
            },
            f1_na(NOISE),
        ),
        case(
            "N10",
            "no odd in-transit cadence",
            nat,
            ["B10"],
            "f1_box",
            {**box, "mods": [{"name": "drop", "where": "odd_in"}]},
            f1_na("too few in-transit points for the odd parity"),
        ),
        case(
            "N11",
            "no even in-transit cadence",
            nat,
            ["B10"],
            "f1_box",
            {**box, "mods": [{"name": "drop", "where": "even_in"}]},
            f1_na("too few in-transit points for the even parity"),
        ),
        case(
            "N12",
            "odd in-transit flux 1e300 at sigma 1e-12",
            nat,
            ["B11"],
            "f1_box",
            {**box, "mods": [{"name": "set", "where": "odd_in", "flux": 1e300, "sigma": 1e-12}]},
            f1_na(PINK_ODD),
        ),
        case(
            "N13",
            "even in-transit flux 1e300 at sigma 1e-12",
            nat,
            ["B11"],
            "f1_box",
            {**box, "mods": [{"name": "set", "where": "even_in", "flux": 1e300, "sigma": 1e-12}]},
            f1_na(PINK_EVEN),
        ),
        case(
            "N14",
            "flux 0 but one baseline point 3e-162, sigma 1e-12: the variances underflow",
            nat,
            ["B08"],
            "f1_box",
            {
                "model": "null",
                "sigma": 1e-12,
                "mods": [
                    {"name": "set", "where": "all", "flux": 0.0},
                    {"name": "set", "where": "baseline_first", "flux": 3e-162},
                ],
            },
            f1_na("denominator not positive"),
            documented=[
                {
                    "assertion": "F1.reason",
                    "approval": PINK_ODD,
                    "raises": "AssertionError",
                    "why": "approval: sigma_w rounds to 0, so _pink returns None "
                    "(line 245); corrected: both variances round to 0 and the "
                    "denominator is 0 (line 251's guard)",
                }
            ],
        ),
        case(
            "N15",
            "odd in-transit flux -1.6e308 and even +1.6e308 at sigma 1e3",
            nat,
            ["B09"],
            "f1_box",
            {
                **box,
                "mods": [
                    {"name": "set", "where": "odd_in", "flux": -1.6e308, "sigma": 1e3},
                    {"name": "set", "where": "even_in", "flux": 1.6e308, "sigma": 1e3},
                ],
            },
            f1_na("OE_box not finite"),
        ),  # --- report-only ---
        case(
            "R14",
            "400 cadences, T = 0.03 d: the MES grid exceeds N",
            nat,
            ["B14", "B15"],
            "report_only",
            {**box, "duration": 0.03, "mods": [{"name": "first", "count": 400}]},
            {
                r: {
                    "state": "unavailable",
                    "reason": "the MES grid exceeds the number of valid cadences",
                }
                for r in ("F2", "U1")
            },
        ),
        case(
            "R16",
            "T = P/3.5: no cell 2T from the primary",
            nat,
            ["B16", "B17"],
            "report_only",
            {**box, "duration": fx.P / 3.5},
            {
                r: {
                    "state": "unavailable",
                    "reason": "an event (pri, sec, ter or pos) has no candidate cell",
                }
                for r in ("F2", "U1")
            },
        ),
        case(
            "R20",
            "T/P just above 0.1, with a secondary 1.0 d away",
            nat,
            ["B20"],
            "report_only",
            {
                "model": "box",
                "depth": 0.006,
                "seed": 20,
                "duration": 0.371,
                "model_duration": 0.371,
                "secondary": {"offset_days": 1.0, "depth": 0.003},
            },
            {"F2": {"state": "unavailable", "reason": "T/P above 0.1"}},
        ),
        case(
            "R21",
            "no cadence within 2T of a transit",
            nat,
            ["B21", "B25", "B28"],
            "report_only",
            {**box, "star": STAR, "mods": [{"name": "drop", "where": "near_transit"}]},
            {
                "F1_trap": {
                    "state": "unavailable",
                    "reason": "the overall trapezoid did not converge",
                },
                "F3": {"state": "unavailable", "reason": "no converged trapezoid with 0 < dF < 1"},
                "F4": {"state": "unavailable", "reason": "no converged trapezoid with 0 < dF < 1"},
            },
        ),
        case(
            "R22",
            "three odd fit cadences",
            nat,
            ["B22"],
            "report_only",
            {
                "model": "trapezoid",
                "trapezoid": TRAP_GIANT,
                "sigma": 1e-7,
                "seed": 22,
                "mods": [{"name": "drop_odd_fit_but", "keep": 3}],
            },
            {
                "F1_trap": {
                    "state": "unavailable",
                    "reason": "a parity fit or its uncertainties were refused",
                }
            },
        ),
        case(
            "R23",
            "zero parity sigma (fault)",
            flt,
            ["B23"],
            "report_only",
            {"model": "trapezoid", "trapezoid": TRAP_GIANT, "sigma": 1e-7, "seed": 23},
            {"F1_trap": {"state": "unavailable", "reason": "a denominator is not positive"}},
            patches=[
                {
                    "target": "_parity_fit",
                    "returns": {"odd": [fx.T0, 0.04, 0.0, 0.0], "even": [fx.T0, 0.04, 0.0, 0.0]},
                }
            ],
        ),
        case(
            "R24",
            "parity t0 of +-1e308 (fault)",
            flt,
            ["B24"],
            "report_only",
            {"model": "trapezoid", "trapezoid": TRAP_GIANT, "sigma": 1e-7, "seed": 24},
            {"F1_trap": {"state": "unavailable", "reason": "a statistic is not finite"}},
            patches=[
                {
                    "target": "_parity_fit",
                    "returns": {"odd": [1e308, 0.04, 1.0, 1.0], "even": [-1e308, 0.04, 1.0, 1.0]},
                }
            ],
        ),
        case(
            "R26",
            "no star record",
            nat,
            ["B26"],
            "report_only",
            {"model": "trapezoid", "trapezoid": TRAP_GIANT, "sigma": 1e-7, "seed": 26},
            {"F3": {"state": "unavailable", "reason": "no reliable stellar radius (legacy rule)"}},
        ),
        case(
            "R27",
            "a stellar radius of 1.7e308: Rp overflows",
            nat,
            ["B27"],
            "report_only",
            {
                "model": "trapezoid",
                "trapezoid": TRAP_GIANT,
                "sigma": 1e-7,
                "seed": 27,
                "star": {"disposition": None, "radius_rsun": 1.7e308, "radius_err_rsun": 1.7e306},
            },
            {"F3": {"state": "unavailable", "reason": "Rp not finite"}},
        ),
        case(
            "R29",
            "q_in = 0.5 (fault)",
            flt,
            ["B29"],
            "report_only",
            box,
            {"F4": {"state": "unavailable", "reason": "no flat bottom (q_in = 0.5)"}},
            patches=[{"target": "_trapezoid", "returns": {**OVERALL, "q_in": 0.5}}],
        ),
        case(
            "R30",
            "a flat interval between cadences (fault)",
            flt,
            ["B30"],
            "report_only",
            box,
            {"F4": {"state": "unavailable", "reason": "no cadence inside the flat interval"}},
            patches=[
                {"target": "_trapezoid", "returns": {**OVERALL, "q": 1e-6, "t0": fx.T0 + 0.0013}}
            ],
        ),
        case(
            "R31",
            "q = 1e-320 on a cadence (fault)",
            flt,
            ["B31"],
            "report_only",
            box,
            {"F4": {"state": "unavailable", "reason": "Eq. 7 ratio undefined"}},
            patches=[
                {
                    "target": "_trapezoid",
                    "returns": {
                        **OVERALL,
                        "q": 1e-320,
                        "q_in": 0.0,
                        "t0": fx.T_START + 100 * fx.DT,
                    },
                }
            ],
        ),
        case(
            "R32",
            "q_in = 0 (fault)",
            flt,
            ["B32"],
            "report_only",
            box,
            {"F4": {"state": "unavailable", "reason": "Eq. 7 denominator not positive"}},
            patches=[{"target": "_trapezoid", "returns": {**OVERALL, "q_in": 0.0}}],
        ),
        case(
            "R33",
            "dF = 0.25, q_in = 0.1 (fault)",
            flt,
            ["B33"],
            "report_only",
            box,
            {"F4": {"state": "unavailable", "reason": "Eq. 7 bracket negative"}},
            patches=[{"target": "_trapezoid", "returns": {**OVERALL, "depth": 0.25, "q_in": 0.1}}],
        ),
        case(
            "R34",
            "_noise raises (fault)",
            flt,
            ["B34", "B35"],
            "report_only",
            box,
            {r: {"state": "unavailable", "reason": numf("ValueError")} for r in ("F2", "U1")},
            patches=[{"target": "_noise", "raises": "ValueError"}],
        ),
        case(
            "R36",
            "_trapezoid raises (fault)",
            flt,
            ["B36", "B57", "B58"],
            "report_only",
            {**box, "star": STAR},
            {
                r: {"state": "unavailable", "reason": numf("ValueError")}
                for r in ("F1_trap", "F3", "F4")
            },
            patches=[{"target": "_trapezoid", "raises": "ValueError"}],
        ),
        case(
            "R37",
            "_mes raises (fault)",
            flt,
            ["B37", "B38"],
            "report_only",
            box,
            {r: {"state": "unavailable", "reason": numf("ValueError")} for r in ("F2", "U1")},
            patches=[{"target": "_mes", "raises": "ValueError"}],
        ),
        case(
            "R39",
            "_parity_fit raises (fault)",
            flt,
            ["B39"],
            "report_only",
            box,
            {"F1_trap": {"state": "unavailable", "reason": numf("ValueError")}},
            patches=[
                {"target": "_trapezoid", "returns": OVERALL},
                {"target": "_parity_fit", "raises": "ValueError"},
            ],
        ),
        case(
            "R40",
            "_reliable_radius raises (fault)",
            flt,
            ["B40"],
            "report_only",
            {**box, "star": STAR},
            {"F3": {"state": "unavailable", "reason": numf("ValueError")}},
            patches=[
                {"target": "_trapezoid", "returns": OVERALL},
                {"target": "_reliable_radius", "raises": "ValueError"},
            ],
        ),
        case(
            "R41",
            "q_in None: TypeError in F4 only (fault)",
            flt,
            ["B41"],
            "report_only",
            box,
            {"F4": {"state": "unavailable", "reason": numf("TypeError")}},
            patches=[{"target": "_trapezoid", "returns": {**OVERALL, "q_in": None}}],
        ),
        case(
            "R42",
            "period NaN",
            nat,
            [f"B{i}" for i in range(42, 47)],
            "report_only",
            {**box, "period": float("nan")},
            ro_all("candidate or curve not usable"),
        ),
        case(
            "R47",
            "one sigma above 1e3",
            nat,
            [f"B{i}" for i in range(47, 52)],
            "report_only",
            {**box, "mods": [{"name": "sigma_at", "index": 7, "value": 2e3}]},
            ro_all("invalid_uncertainty"),
        ),
        case(
            "R52",
            "15 cadences",
            nat,
            [f"B{i}" for i in range(52, 57)],
            "report_only",
            {**box, "mods": [{"name": "first", "count": 15}]},
            ro_all("candidate or curve not usable"),
        ),
        case(
            "R59",
            "eligible, no flattened curve",
            nat,
            [f"B{i}" for i in range(59, 65)],
            "compute_screen:no_curve",
            box,
            {**f1_na("no flattened curve"), **ro_all("no flattened curve")},
        ),
        case(
            "R65",
            "a flux that holds a string",
            nat,
            [f"B{i}" for i in range(65, 70)],
            "compute_screen",
            {**box, "mods": [{"name": "flux_text", "index": 5}]},
            {**f1_na(numf("ValueError")), **ro_all(numf("ValueError"))},
        ),
    ]
    return out


def tol(source, atol, spec):
    return {"source": source, "atol": atol, **spec}


def check(cid, got, want):
    if got != want:
        raise SystemExit(f"{cid}: the oracle gives {got!r}, the case intends {want!r}")


def fill(c) -> dict:
    fixture = fx.build(c["recipe"])
    t, f, s = fixture["t"], fixture["f"], fixture["s"]
    p, t0, d = fixture["period"], fixture["t0"], fixture["duration"]
    exp = c["expect"]
    values = {}
    f1_entry = c["entry"] in ("f1_box", "report_only+f1_box", "compute_screen")
    if "F1" in exp and f1_entry and c["id"] != "R59":
        got = oc.f1_corrected(t, f, s, p, t0, d)
        check(c["id"], (got["state"], got["reason"]), (exp["F1"]["state"], exp["F1"]["reason"]))
    if c["id"] in ("N05", "R14", "R16", "R20"):
        mes = oc.mes_f2_u1(np.asarray(t, float), np.asarray(f, float), s, p, t0, d)
        for r in ("F2", "U1"):
            if r in exp:
                check(
                    c["id"],
                    (mes[r]["state"], mes[r]["reason"]),
                    (exp[r]["state"], exp[r]["reason"]),
                )
    if c["id"] == "R27":
        rp = fx.rp_earth(c["recipe"]["star"]["radius_rsun"], 0.04)
        check(c["id"], math.isfinite(rp), False)
    if c["id"] == "R30":
        q = 1e-6
        t_f = q * fx.P * (1 - 2 * 0.2)
        dt = np.abs(np.mod(t - (fx.T0 + 0.0013) + fx.P / 2, fx.P) - fx.P / 2)
        check(c["id"], bool(np.any(dt < t_f / 2.0)), False)
    if c["id"] in ("C01", "C02", "C05", "C06", "C07", "C08"):
        got = oc.f1_corrected(t, f, s, p, t0, d)
        frozen = f1_reference(t, f, s, p, t0, d)
        # #218 comment 7198110621, item 1: C05's entry is report-only and produces no F1 record,
        # so its two F1 assertions are removed; its oracle values stay, for information
        if c["id"] != "C05":
            exp["F1"] = {"state": got["state"], "reason_prefix": "OE_box "}
        intended = {"C01": "pass", "C02": "fail", "C06": "pass", "C07": "pass"}
        if c["id"] in intended:
            check(c["id"], got["state"], intended[c["id"]])
        values["F1"] = {
            "corrected_oe_box": got["metrics"]["oe_box"],
            "frozen_oe_box": frozen.metrics.get("oe_box"),
        }
        if frozen.state != got["state"]:
            c["documented"].append(
                {
                    "assertion": "F1.state",
                    "approval": frozen.state,
                    "raises": "AssertionError",
                    "why": "the frozen estimator decides otherwise",
                }
            )
    if c["id"] in ("C01", "C03", "C04", "C08"):
        mes = oc.mes_f2_u1(t, f, s, p, t0, d)
        for r in ("F2", "U1"):
            m = mes[r]
            exp[r] = {"state": m["state"], "reason": m["reason"]}
            if m["state"] == "computed":
                exp[r]["coverage"] = m["coverage"]
                vals = {}
                for k, v in m["metrics"].items():
                    if isinstance(v, bool) or v is None:
                        exp[r][k] = v
                    else:
                        vals[k] = {"expected": v, **tol("oracle", 1e-12, CLOSED)}
                exp[r]["values"] = vals
    if c["id"] == "C01":
        tf = oc.trap_fits(t, f, s, p, t0, d)["F1_trap"]
        exp["F1_trap"] = {
            "state": "computed",
            "values": {
                "fit_cadences_odd": {
                    "expected": tf["fit_cadences_odd"],
                    "atol": 0,
                    "rtol": 0,
                    "source": "oracle",
                },
                "fit_cadences_even": {
                    "expected": tf["fit_cadences_even"],
                    "atol": 0,
                    "rtol": 0,
                    "source": "oracle",
                },
                "OE_trap": {"expected": tf["OE_trap"], **tol("oracle", 1e-9, FITTED_ORACLE)},
                "OE_trap_T": {"expected": tf["OE_trap_T"], **tol("oracle", 1e-9, FITTED_ORACLE)},
            },
        }
    if c["id"] == "C05":
        g = TRAP_GRAZE
        f4 = oc.f4_closed_form(g["depth"] / g["f0"], g["q"], g["q_in"], fx.P)
        exp["F4"] = {
            "state": "computed",
            "values": {
                k: {"expected": v, **tol("model", 1e-6, FITTED_MODEL)} for k, v in f4.items()
            },
        }
    if c["id"] in ("C06", "C07"):
        g = TRAP_GIANT
        if c["id"] == "C06":
            rp = fx.rp_earth(STAR["radius_rsun"], g["depth"] / g["f0"])
            exp["F3"] = {
                "state": "computed",
                "paper_threshold_crossed": rp > 22.0,
                "values": {
                    "dF": {"expected": g["depth"] / g["f0"], **tol("model", 1e-6, FITTED_MODEL)},
                    "R_star_rsun": {"expected": 2.0, "atol": 0.0, "rtol": 0.0, "source": "model"},
                    "Rp_earth": {"expected": rp, **tol("model", 1e-3, FITTED_MODEL)},
                },
            }
            check(c["id"], rp > 22.0, True)
        else:
            exp["F3"] = {
                "state": "unavailable",
                "reason": "no reliable stellar radius (legacy rule)",
            }
            exp["isolation"] = {
                "same_core_and_outcome_as": "C06",
                "outcome": "retained",
                "gate_results_unchanged": True,
            }
    c["oracle_values"] = values
    return c


def main() -> int:
    built = [fill(c) for c in cases()]
    doc = {
        "schema": "refute-v0512-step2-cases",
        "labels": ["exploratory", "method_status: not_validated"],
        "decision": "#218 comment 7197519001, item 3; the charter, step 2",
        "inventory": "docs/validation/v0.5.12/step2/inventory.json",
        "approval_code": "f18d6f8",
        "f1_expectations": "correction 2 revision 1 (SHA-256 c24e7fd9...), tests/v0512_oracles.py",
        "report_only_expectations": "the frozen section 5, tests/v0512_oracles.py",
        "tolerance_rule": "|value - expected| <= max(atol, rtol * |expected|)",
        "tolerances": {
            "oracle arithmetic on the realized fixture": {"rtol": 1e-9},
            "oracle fit values (OE_trap, OE_trap_T)": {"rtol": 1e-6},
            "model fit values: C05 at sigma 1e-7 (depth 0.05, noiseless in effect); C06 at "
            "sigma 5e-5 (depth 0.04: about 84 flat cadences give SE(dF) near 5.5e-6, so 1e-3 "
            "is about seven standard errors; a sigma of 1e-7 made F1 fail on the cadence "
            "sampling alone, OE_box 44, and the isolation case needs F1 to pass)": {"rtol": 1e-3},
        },
        "unreachable": {
            "B07": "line 231 repeats _wmean(f[base], w[base]); _noise returned sigma_w only "
            "after _wstd's own _wmean of the same arrays was not None (lines 89 to 91, 149)",
            "B18 B19": "erfcinv(T/P) is finite for 0 < T/P < 2; T/P >= 2 leaves no cell 2T from "
            "the primary (_cell_distance <= P/2 < 2T), so line 378 returns first",
            "B23": "_uncertainties returns sqrt(var) with finite var > 0, so each sigma >= "
            "sqrt(4.9e-324) and its square is not 0; the sum is never NaN (also witnessed by "
            "fault injection, R23)",
            "corrected C <= 0": "revision 1, section 4 and its bound in section 6 (defensive)",
        },
        "cases": built,
    }
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "cases.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"cases": len(built), "documented": sum(len(c["documented"]) for c in built)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
