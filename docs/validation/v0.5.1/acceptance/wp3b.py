"""v0.5.1 acceptance run of WP3 (b), the per-harmonic sinusoid (docs/plans/v0.5.1-acceptance.md),
on common.py. Design: docs/validation/v0.5.1/acceptance/wp3b-design.md (every choice the text
leaves open, fixed before any acceptance unit runs; reviewed by Codex). It replaces the draft of
86e0a1d, which was never run.

What the runner hands the test is what the version-3 pipeline hands it (item 3 of the
maintainer's decision of 2026-11-08, #208): ``check_sinusoid`` gets the raw curve (``data.lc``),
the plan's ``stronger`` and ``v051`` sections and ``power.candidate_seed("sinusoid", cand)``; the
phase-0.5 test of row 3.3 measures on ``series.pipeline_flat``. The proof is
tests/test_v051_accept_wp3b_series.py.

Usage (each section once, through scripts/launch_affinity.ps1, ``<used>`` the development hours
used so far):
    -Script docs/validation/v0.5.1/acceptance/wp3b.py -Arguments 'run,rows,<used>'
            -Log .cache/v051/accept/wp3b-rows.log
    then 'run,sabotage-no_extra,<used>', 'run,sabotage-v05_domain,<used>',
    'run,sabotage-no_exclusion,<used>', and 'evaluate' once all are complete.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import common as c  # noqa: E402
import series  # noqa: E402

N = 200
SIGMA = 1000e-6
P_STD, D_STD = 3.3, 0.12
LABELS = ("P/2", "P", "2P")
FACTORS = {"P/2": 0.5, "P": 1.0, "2P": 2.0}
SECTIONS = ("rows", "sabotage-no_extra", "sabotage-v05_domain", "sabotage-no_exclusion")
V05_ACCEPTANCE = HERE.parents[1] / "v0.5" / "acceptance" / "acceptance.py"


# --- the plan and v0.5's constructions -----------------------------------------------------------


@lru_cache(maxsize=1)
def _plan():
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.synthetic import discovery_v051_plan_dict

    return TessTestPlan.model_validate(discovery_v051_plan_dict())


@lru_cache(maxsize=1)
def _v05():
    """v0.5's acceptance module (rows 3.3 and 3.8, "as v0.5"), unchanged. Its box estimator runs
    with the v0.5 plan's detrend and search sections, which must equal the version-3 plan's."""
    spec = importlib.util.spec_from_file_location("v05_acceptance", V05_ACCEPTANCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    old, new = mod._plan(), _plan()
    for section in ("detrend", "search"):
        if getattr(old, section).model_dump() != getattr(new, section).model_dump():
            raise SystemExit(f"the v0.5 and version-3 plans differ in {section}: no run")
    return mod


# --- the sabotages (a patch inside the worker process, never committed) -------------------------

_PATCHED: str | None = None


def _patch(name: str) -> None:
    global _PATCHED
    if _PATCHED == name:
        return
    if _PATCHED is not None:
        raise SystemExit("a worker serves one sabotage only")
    from refute.core.verdict import Severity
    from refute.packs.tess import battery_v5 as v5
    from refute.packs.tess import battery_v51 as v51

    if name == "no_extra":
        pass  # applied by _cp(): no extra frequencies in the joint model
    elif name == "v05_domain":
        original = v51.check_sinusoid

        def v05_domain(raw, candidate, sp, cp, seed):
            if candidate.period >= 10.0:
                why = f"period {candidate.period:.2f} d: outside v0.5's domain (P < 10 d)"
                return v5._inconclusive(
                    "sinusoid", Severity.WARNING, why, inconclusive_class=v51.OUTSIDE_DOMAIN
                )
            return original(raw, candidate, sp, cp, seed)

        v51.check_sinusoid = v05_domain
    elif name == "no_exclusion":
        original_peak = v51._ls_peak

        def no_exclusion(time, resid, err, f_min, f_max, excluded, width):
            return original_peak(time, resid, err, f_min, f_max, [], width)

        v51._ls_peak = no_exclusion
    else:
        raise SystemExit(f"unknown sabotage {name}")
    _PATCHED = name


def _cp():
    cp = _plan().v051
    if _PATCHED == "no_extra":
        cp = cp.model_copy(update={"sinusoid_extra_frequencies": 0})
    return cp


# --- curves and candidates ---------------------------------------------------------------------


def _candidate(period, t0, duration, depth):
    from refute.packs.tess.types import Candidate

    return Candidate(period, t0, duration, depth, depth / 10.0, 20.0, 0.0, 10.0, 5)


def _grid():
    """The two-sector time grid of ``common.noise_curve`` (deterministic: ``sector_times``)."""
    lc, _ = c.noise_curve(0, "white", 2)
    return lc


def _depth_for(snr, period, t0, duration, time):
    dt = np.abs(np.mod(time - t0 + 0.5 * period, period) - 0.5 * period)
    n_in = int(np.count_nonzero(dt <= duration / 2.0))
    return snr * SIGMA / math.sqrt(max(n_in, 1))


def _sinusoids(t, waves):
    return sum(a * np.sin(2.0 * math.pi * t / p + ph) for p, a, ph in waves)


def _planet_curve(seed, noise, period, duration, snr, waves=(), sigma_ppm=1000.0):
    """A planet (trapezoid, ingress 0.1, t0 uniform over one period from the first cadence, the
    depth of box SNR ``snr`` at the white level) and sinusoids ``(period, semi-amplitude in units
    of the depth, phase)``, multiplicative, before the noise."""
    from refute.packs.tess import synthetic as syn

    t = _grid().time
    rng = np.random.default_rng([seed, 11])
    t0 = float(t.min() + rng.uniform(0.0, period))
    depth = _depth_for(snr, period, t0, duration, t)
    phases = [float(rng.uniform(0.0, 2.0 * math.pi)) for _ in waves]
    resolved = [(p, k * depth, ph) for (p, k), ph in zip(waves, phases, strict=True)]

    def model(time):
        return (1.0 - syn.trapezoid(time, period, t0, depth, duration, 0.1)) * (
            1.0 + _sinusoids(time, resolved)
        )

    lc, trend = c.noise_curve(seed, noise, 2, sigma_ppm=sigma_ppm, model=model)
    return lc, _candidate(period, t0, duration, depth), resolved, trend


# --- running the tests as the pipeline does -----------------------------------------------------


def _sinusoid(lc, cand):
    """``check_sinusoid`` with what ``pipeline.v05_tests`` hands it, then the engine's rule."""
    from refute.core.sensitivity import enforce_sensitivity
    from refute.packs.tess import battery_v51 as v51
    from refute.packs.tess import power

    plan = _plan()
    raw = v51.check_sinusoid(lc, cand, plan.stronger, _cp(), power.candidate_seed("sinusoid", cand))
    final = enforce_sensitivity([raw], power.registry_for(plan))[0]
    return raw, final


def _describe(raw, final, cand):
    sp = _plan().stronger
    fits = (raw.metrics or {}).get("fits", {})
    blocks = raw.sensitivity or {}
    flagged = [
        k
        for k in LABELS
        if fits.get(k, {}).get("significance", 0.0) > sp.sinusoid_min_significance
        and fits.get(k, {}).get("semi_amplitude_ppm", 0.0)
        >= sp.sinusoid_min_amplitude_ratio * cand.depth * 1e6
    ]
    metrics = raw.metrics or {}
    rule = [k for k in LABELS if "detectable" in blocks.get(k, {})]
    return {
        "status": raw.status.value,
        "final": final.status.value,
        "severity": final.severity.value,
        "flagged": flagged,
        "applicable": rule,
        "not_applicable": [k for k in LABELS if blocks.get(k, {}).get("applicable") is False],
        "detectable": {k: bool(blocks[k]["detectable"]) for k in rule},
        "fits": fits,
        "extra": [x["frequency_per_day"] for x in metrics.get("extra_frequencies", [])],
        "inconclusive_class": metrics.get("inconclusive_class"),
        "beta": metrics.get("beta"),
    }


def _kept(lc, cand):
    """``check_sinusoid``'s fit inputs for row 3.7: its good and out-of-transit cadences, their
    sectors, the per-sector medians it divides by, and its normalized errors."""
    sp = _plan().stronger
    good = np.isfinite(lc.flux) & np.isfinite(lc.flux_err) & (lc.flux_err > 0)
    t, sec, flux, err = lc.time[good], lc.sector[good], lc.flux[good], lc.flux_err[good]
    med = np.empty(t.size)
    for s in np.unique(sec):
        sel = sec == s
        med[sel] = float(np.median(flux[sel]))
    half = cand.duration / 2.0 + sp.sinusoid_mask_durations * cand.duration
    dt = np.abs(np.mod(t - cand.t0 + 0.5 * cand.period, cand.period) - 0.5 * cand.period)
    keep = dt > half
    return t[keep], sec[keep], med[keep], (err / med)[keep]


# --- the units -----------------------------------------------------------------------------------


def unit(arg):
    row, case, noise, i, seed, sabotage = arg
    if sabotage:
        _patch(sabotage)
    out = {"row": row, "case": case, "noise": noise, "i": i}
    if row == "3.1":
        out.update(_row_31(case, noise, seed))
    elif row == "3.2":
        lc, cand, _, _ = _planet_curve(seed, noise, P_STD, D_STD, int(case))
        out.update(_describe(*_sinusoid(lc, cand), cand))
    elif row == "3.3":
        out.update(_row_33(case, noise, seed))
    elif row == "3.4":
        out.update(_row_34(noise, seed))
    elif row == "3.5":
        lc, cand, _, _ = _planet_curve(seed, noise, float(case), 0.25, 15)
        out.update(_describe(*_sinusoid(lc, cand), cand))
    elif row == "3.6":
        out.update(_row_36(noise, seed))
    elif row == "3.7":
        out.update(_row_37(noise, seed))
    elif row == "3.8":
        out.update(_row_38(case, noise, seed))
    else:
        raise ValueError(row)
    return out


def _row_31(case, noise, seed):
    v05 = _v05()
    if case == "box":  # v0.5 row 3.8: the box only
        depth = 2000e-6
        lc = v05._std_lc(seed, noise, lambda t: v05._box(t, v05.P, v05.T0, v05.DUR, depth))
        cand = _candidate(v05.P, v05.T0, v05.DUR, depth)
        d = _describe(*_sinusoid(lc, cand), cand)
        d["constructed"] = bool(d["applicable"]) and all(d["detectable"].values())
        return d
    # v0.5 row 3.3: the variability at SIN_P, found as a box by the engine
    amp = v05.SIN_AMP["a"]
    cand = v05._sin_box(amp)
    lc = v05._std_lc(seed, noise, lambda t: amp * np.cos(2 * np.pi * (t - v05.T0) / v05.SIN_P))
    d = _describe(*_sinusoid(lc, cand), cand)
    err = d["fits"].get("P", {}).get("semi_amplitude_err_ppm")
    design = amp * 1e6 / err if err else None
    ratio = amp / cand.depth
    geometry = 1.9 <= ratio <= 2.1 and abs(cand.t0 - v05.T0) <= cand.duration / 2.0
    d.update(
        constructed=bool(geometry and design is not None and design > 15.0),
        amplitude_over_depth=ratio,
        design_significance=design,
        box_t0=cand.t0,
        box_depth=cand.depth,
    )
    return d


def _row_33(case, noise, seed):
    from refute.core.sensitivity import enforce_sensitivity
    from refute.packs.tess import battery_v5 as v5
    from refute.packs.tess import power

    plan = _plan()
    waves = [(2.37 * P_STD, 3.0)] if case == "unrelated" else [(P_STD, 1.0)]
    lc, cand, _, _ = _planet_curve(seed, noise, P_STD, D_STD, 15, waves)
    raw, final = _sinusoid(lc, cand)
    flat = series.pipeline_flat(lc, cand, plan)
    _, ev, evh = series.event_measurements(flat, cand, plan)
    sec = v5.check_secondary_two_sided(
        ev, evh, plan.gauntlet.secondary_eclipse, plan.stronger,
        power.candidate_seed("secondary_eclipse", cand),
    )  # fmt: skip
    duty = v5.check_duty_cycle(cand, plan.stronger)
    sec_f, duty_f = enforce_sensitivity([sec, duty], power.registry_for(plan))
    out = _describe(raw, final, cand)
    out["wp3"] = {
        t.name: {"final": t.status.value, "severity": t.severity.value}
        for t in (final, sec_f, duty_f)
    }
    return out


def _row_34(noise, seed):
    from refute.core.sensitivity import enforce_sensitivity
    from refute.packs.tess import battery_v5 as v5
    from refute.packs.tess import power

    rng = np.random.default_rng([seed, 13])
    pv = math.exp(rng.uniform(math.log(0.7), math.log(10.0)))
    amp = math.exp(rng.uniform(math.log(0.5), math.log(5.0))) * SIGMA
    f0 = 1.0 / pv
    d1, d2 = float(rng.uniform(0.01, 0.05)), float(rng.uniform(0.01, 0.05))
    waves = [(1.0 / f, amp / math.sqrt(3.0), float(rng.uniform(0.0, 2 * math.pi)))
             for f in (f0, f0 * (1.0 + d1), f0 * (1.0 + d2))]  # fmt: skip
    lc, _ = c.noise_curve(seed, noise, 2, model=lambda t: 1.0 + _sinusoids(t, waves))
    first = float(lc.time.min())
    fine = first + np.arange(0.0, pv, 1.0 / 1440.0)
    t0 = float(fine[int(np.argmin(_sinusoids(fine, waves)))])
    cand = _candidate(pv, t0, 0.1, amp / 2.0)
    raw, final = _sinusoid(lc, cand)
    old = v5.check_sinusoid(lc, cand, _plan().stronger, power.candidate_seed("sinusoid", cand))
    old_final = enforce_sensitivity([old], power.TESS_REGISTRY)[0]
    out = _describe(raw, final, cand)
    out.update(v05_final=old_final.status.value, period=pv, amplitude=amp)
    return out


@lru_cache(maxsize=1)
def _box_14():
    """Row 3.6's candidate: the engine's box estimator at P = 14 d (hint 0.3 d) on the noise-free
    undetrended curve (the design: the detrended curve keeps 0.1 ppm of it)."""
    from refute.packs.tess.search import finalize_candidate
    from refute.packs.tess.types import LightCurveData

    g = _grid()
    flux = _model_14(g.time)
    lc = LightCurveData(g.time, flux, np.full(g.time.size, SIGMA), g.sector, g.year)
    return finalize_candidate(lc, 14.0, 0.3, _plan().search, 10.0, np.full(g.time.size, SIGMA))


def _model_14(t):
    return 1.0 + 2000e-6 * np.cos(2.0 * math.pi * (t - 2003.0) / 14.0)


def _row_36(noise, seed):
    cand = _box_14()
    lc, _ = c.noise_curve(seed, noise, 2, model=_model_14)
    d = _describe(*_sinusoid(lc, cand), cand)
    d.update(box_period=cand.period, box_t0=cand.t0, box_duration=cand.duration,
             box_depth=cand.depth)  # fmt: skip
    return d


def _row_37(noise, seed):
    from refute.packs.tess import battery_v51 as v51

    lc, cand, waves, _ = _planet_curve(seed, noise, P_STD, D_STD, 15, [(P_STD * 1.002, 2.0)])
    d = _describe(*_sinusoid(lc, cand), cand)
    t, sec, med, err = _kept(lc, cand)
    span = float(t.max() - t.min())
    # the trial's own fit (design r3): the tested harmonics and the extra frequencies the test
    # selected, weighted by its normalized errors, applied to the injected sinusoid alone
    periods = [P_STD * FACTORS[k] for k in LABELS] + [1.0 / f for f in d["extra"]]
    x = v51._design(t, sec, periods)
    coef, _, _ = v51._wls(x, _sinusoids(t, waves) / med, err)
    n_off = len(np.unique(sec))
    j = LABELS.index("P")
    expected = math.hypot(float(coef[n_off + 2 * j]), float(coef[n_off + 2 * j + 1]))
    fit = d["fits"].get("P", {})
    d.update(
        span=span,
        near_p=[f for f in d["extra"] if abs(f - 1.0 / P_STD) <= 1.0 / span],
        expected_ppm=expected * 1e6,
        carried=bool(
            fit.get("semi_amplitude_err_ppm")
            and abs(fit["semi_amplitude_ppm"] - expected * 1e6)
            <= 3.0 * fit["semi_amplitude_err_ppm"]
        ),
    )
    return d


def _row_38(case, noise, seed):
    """(a) a planet and a sinusoid at the sub-check's period Q, semi-amplitude 2 x the depth;
    (b) the same with the noise 25 times larger (the alternative below the rule); (c) the planet
    only, shared by the three sub-checks."""
    kind, _, label = case.partition("-")
    waves = [] if kind == "c" else [(P_STD * FACTORS[label], 2.0)]
    sigma_ppm = 25000.0 if kind == "b" else 1000.0
    lc, cand, _, _ = _planet_curve(seed, noise, P_STD, D_STD, 20, waves, sigma_ppm)
    return _describe(*_sinusoid(lc, cand), cand)


# --- the schedule --------------------------------------------------------------------------------


def _cases(section):
    if section == "rows":
        out = [("3.1", k, n) for k in ("sin", "box") for n in ("white", "red")]
        out += [("3.2", s, n) for s in ("12", "20") for n in ("trend", "correlated_trend")]
        out += [("3.3", k, n) for k in ("unrelated", "rotation") for n in c.NOISES]
        out += [("3.4", "v2", n) for n in c.NOISES]
        out += [("3.5", p, n) for p in ("12", "15") for n in c.NOISES]
        out += [("3.6", "sin14", n) for n in c.NOISES]
        out += [("3.7", "near", n) for n in c.NOISES]
        out += [("3.8", f"{k}-{q}", n) for k in ("a", "b") for q in LABELS for n in c.NOISES]
        out += [("3.8", "c", n) for n in c.NOISES]
        return out
    if section == "sabotage-no_extra":
        return [("3.2", "20", n) for n in ("trend", "correlated_trend")]
    if section == "sabotage-v05_domain":
        return [("3.5", p, n) for p in ("12", "15") for n in c.NOISES]
    if section == "sabotage-no_exclusion":
        return [("3.7", "near", n) for n in c.NOISES]
    raise SystemExit(f"unknown section {section}")


def _seed_case(row, case, noise):
    """The seed's case string. Row 3.8's (a) and (b) of one sub-check share it (Codex's round 3,
    objection 2): the same planet, sinusoid and standardized noise draws, (b) with the noise level
    25 times larger; their records stay apart."""
    if row == "3.8" and case[0] in "ab":
        return f"wp3b-3.8-ab-{case[2:]}-{noise}"
    return f"wp3b-{row}-{case}-{noise}"


def schedule(section):
    """Unit order: trial index outermost, so every case's first trials come first (the 5 %
    projection sees every case). A sabotage reuses its row's seeds (the same curves)."""
    sabotage = section[len("sabotage-") :] if section.startswith("sabotage-") else None
    units = []
    for i in range(N):
        for row, case, noise in _cases(section):
            seed = c.accept_seed(_seed_case(row, case, noise), i)
            units.append((f"{row}|{case}|{noise}|{i}", (row, case, noise, i, seed, sabotage)))
    return units


# --- evaluation ----------------------------------------------------------------------------------


def _ordered(section):
    """The section's records in schedule order. Every record must name a scheduled unit, and no
    unit may have two records (Codex's round 3, objection 3): otherwise nothing is evaluated.
    Missing units are counted by identity."""
    ids = [u for u, _ in schedule(section)]
    pos = {u: k for k, u in enumerate(ids)}
    recs = c._records(c.OUT / f"wp3b-{section}" / "records.jsonl")
    unknown = sorted({r["unit"] for r in recs if r["unit"] not in pos})
    seen: set = set()
    duplicates = sorted({r["unit"] for r in recs if r["unit"] in seen or seen.add(r["unit"])})
    if unknown or duplicates:
        raise SystemExit(f"{section}: unknown units {unknown[:5]}, duplicates {duplicates[:5]}")
    recs.sort(key=lambda r: pos[r["unit"]])
    errors = [r for r in recs if r.get("status") == "ERROR"]
    info = {
        "scheduled": len(ids),
        "recorded": len(recs),
        "missing": len(set(ids) - seen),
        "errors": len(errors),
        "error_reasons": sorted({str(r.get("reason"))[:120] for r in errors})[:10],
        "cpu_hours": sum(float(r.get("cpu_seconds", 0.0)) for r in recs) / 3600.0,
    }
    return recs, info


def _decide(case_recs, fn):
    """NOT DECIDABLE when a unit of the case is missing or ended in ERROR; else ``fn``."""
    if len(case_recs) < N or any(r.get("status") == "ERROR" for r in case_recs):
        return {"result": "NOT DECIDABLE", "units": len(case_recs),
                "errors": sum(r.get("status") == "ERROR" for r in case_recs)}  # fmt: skip
    out = fn(case_recs)
    passed = out.pop("pass")
    if out.pop("undecided", False):
        out["result"] = "NOT DECIDABLE"
    else:
        out["result"] = "PASS" if passed else "FAIL"
    return out


def _judge(row, case, recs):
    fails = sum(r["final"] == "FAIL" for r in recs)
    if row == "3.1":
        built = [r for r in recs if r["constructed"]]
        if len(built) < len(recs):  # v0.5's rule: decided only when every trial is constructed
            return {"pass": False, "not_constructed": len(recs) - len(built), "undecided": True}
        k = sum(r["final"] == "FAIL" for r in built)
        band = (
            c.at_least(k, len(built), 0.95) if case == "sin" else c.at_most(k, len(built), 0.0027)
        )
        return {"pass": band["pass"], "band": band}
    if row == "3.2":
        band = c.at_most(fails, len(recs), 0.0027)
        out = {"pass": band["pass"], "false_failure": band}
        if case == "20":
            det = sum(bool(r["applicable"]) and all(r["detectable"].values()) for r in recs)
            out["every_applicable_detectable"] = c.at_least(det, len(recs), 0.95)
            out["pass"] = band["pass"] and out["every_applicable_detectable"]["pass"]
        return out
    if row == "3.3":
        fatal = sum(
            any(v["final"] == "FAIL" and v["severity"] == "fatal" for v in r["wp3"].values())
            for r in recs
        )
        per = {}
        for r in recs:
            for name, v in r["wp3"].items():
                d = per.setdefault(name, {"FAIL": 0, "severities": {}})
                d["FAIL"] += v["final"] == "FAIL"
                d["severities"][v["severity"]] = d["severities"].get(v["severity"], 0) + 1
        return {"pass": fatal == 0, "trials_with_a_fatal_fail": fatal, "per_test": per}
    if row == "3.4":
        old = sum(r["v05_final"] == "FAIL" for r in recs)
        return {"pass": fails >= old, "v3_fails": fails, "v05_fails": old}
    if row == "3.5":
        bad = sum(
            r["applicable"] != ["P/2", "P"] or r["not_applicable"] != ["2P"]
            or (r["final"] == "INCONCLUSIVE" and r["inconclusive_class"] == "outside_domain")
            for r in recs
        )  # fmt: skip
        return {"pass": bad == 0, "violations": bad}
    if row == "3.6":
        det = [r for r in recs if r["detectable"].get("P")]
        band = c.at_least(sum(r["final"] == "FAIL" for r in det), len(det), 0.95)
        return {"pass": band["pass"], "band": band, "not_detectable": len(recs) - len(det)}
    if row == "3.7":
        near = sum(bool(r["near_p"]) for r in recs)
        carried = c.at_least(sum(r["carried"] for r in recs), len(recs), 0.95)
        return {"pass": near == 0 and carried["pass"], "extra_near_p": near, "carried": carried}
    if row == "3.8":
        kind, _, label = case.partition("-")
        if kind == "c":
            out = {"pass": True}
            for q in LABELS:
                built = [r for r in recs if r["detectable"].get(q)]
                band = c.at_most(sum(q in r["flagged"] for r in built), len(built), 0.0027)
                out[q] = {**band, "not_constructed": len(recs) - len(built)}
                out["pass"] = out["pass"] and band["pass"]
            return out
        if kind == "a":
            built = [r for r in recs if r["detectable"].get(label)]
            band = c.at_least(sum(label in r["flagged"] for r in built), len(built), 0.95)
            return {"pass": band["pass"], "band": band, "not_constructed": len(recs) - len(built)}
        built = [r for r in recs if not r["detectable"].get(label, False)]
        passes = sum(r["final"] == "PASS" for r in built)
        return {
            "pass": bool(built) and passes == 0,
            "final_pass": passes,
            "constructed": len(built),
            "not_constructed": len(recs) - len(built),
        }
    raise ValueError(row)


def evaluate_section(section):
    recs, info = _ordered(section)
    groups: dict = {}
    for r in recs:
        groups.setdefault((r["row"], r["case"], r["noise"]), []).append(r)
    cases = {}
    for row, case, noise in _cases(section):
        g = groups.get((row, case, noise), [])
        cases[f"{row}|{case}|{noise}"] = _decide(
            g, lambda x, row=row, case=case: _judge(row, case, x)
        )
    out = {"run": info, "cases": cases}
    if section.startswith("sabotage-"):
        out.update(_sabotage(section, cases))
    return out


def _sabotage(section, cases):
    """Detected when the frozen text's target fails in at least one decided case (Codex's round
    3, objection 1): no_extra, 3.2's detectable fraction (not its false-failure bound); v05_domain,
    3.5's applicability and domain condition; no_exclusion, 3.7's extra frequency near P (the
    mechanism the sabotage removes). Void when every case is NOT DECIDABLE."""
    decided = {k: v for k, v in cases.items() if v["result"] != "NOT DECIDABLE"}
    if section == "sabotage-no_extra":
        hits = [k for k, v in decided.items() if not v["every_applicable_detectable"]["pass"]]
    elif section == "sabotage-v05_domain":
        hits = [k for k, v in decided.items() if v["violations"] > 0]
    else:
        hits = [k for k, v in decided.items() if v["extra_near_p"] > 0]
    out = {"sabotage_detected": bool(hits), "target_failed_in": hits}
    if not decided:
        out["void"] = "every target case NOT DECIDABLE"
    return out


def evaluate():
    result = {"code_sha256": c.check_freeze(), "sections": {}}
    for section in SECTIONS:
        out = evaluate_section(section)
        if out["run"]["missing"]:
            raise SystemExit(f"section {section} not complete; nothing written")
        result["sections"][section] = out
    rows = result["sections"]["rows"]["cases"]
    result["rows_pass"] = all(v["result"] == "PASS" for v in rows.values())
    result["sabotage_detected"] = {
        s: result["sections"][s]["sabotage_detected"] for s in SECTIONS if s.startswith("sab")
    }
    result["method_status"] = "not_validated"
    print(c.write_result("wp3b", result))


if __name__ == "__main__":
    c.env_threads()
    if sys.argv[1:] == ["evaluate"]:
        evaluate()
        sys.exit(0)
    if len(sys.argv) >= 3 and sys.argv[1] == "run" and sys.argv[2] in SECTIONS:
        c.check_freeze()
        section = sys.argv[2]
        used = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
        c.run_section(f"wp3b-{section}", schedule(section), unit, used, 0.0)
    else:
        raise SystemExit(f"usage: wp3b.py run <{'|'.join(SECTIONS)}> [used hours] | evaluate")
