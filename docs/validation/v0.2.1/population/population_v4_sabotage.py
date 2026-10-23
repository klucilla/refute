"""The sabotages of population_v4 (acceptance record ``population-v4-acceptance.md``, section 5).

Each sabotage breaks one acceptance criterion once and runs the matching check; it is caught
only if the check fails for the named reason, and its control (the same check on the unbroken
generator and the same cases) passes with positive coverage. Each runs in its own process
(``one <id>``); a sabotage of the generator patches it in a separate process (``make <id>``),
which writes its cases under the work folder, and the check reads them in an unpatched process,
so the check never runs patched code.

``python population_v4_sabotage.py all --work DIR --out FILE`` runs S1 to S9 one after the other.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import band_check_v4 as band  # noqa: E402
import population_v4 as v4  # noqa: E402
import population_v4_check as chk  # noqa: E402

pv2 = v4.pv2
IDS = ("S1", "S2", "S3", "S4", "S5a", "S5b", "S6", "S7", "S8", "S9")
WORKERS = 22


# --- the patches (only ever applied in a ``make`` process or a pool worker of one) -------------


def _patch(sid: str) -> None:
    if sid == "S2":
        v4.ONE_YEAR_DAYS = 365.25 / 3.0
    elif sid == "S3":
        v4.geometry_of = lambda j: (
            {"geometry": "G-a"}
            if j % 3 == 0
            else {"geometry": "G-b", "order": "short-long" if j % 3 == 1 else "long-short"}
        )
    elif sid == "S4":
        v4.map_absent_year = lambda p, labels: None
    elif sid == "S6":
        real = v4._place_in_band

        def filtered(synthetic, case, p, *args):
            if p["period"] < 2.0:
                return "band", {}
            return real(synthetic, case, p, *args)

        v4._place_in_band = filtered
    elif sid == "S7":
        real_seed = v4.sub_seed

        def mixed(seed, *parts):
            if parts == ("noise",):
                return real_seed(seed, "noise", os.getpid())
            return real_seed(seed, *parts)

        v4.sub_seed = mixed


def _layout_record(case: dict) -> dict:
    return chk.layout_record(case, v4.draw_layout(case))


def _digest(case: dict) -> str:
    return hashlib.sha256(v4.build_case(case)[0]).hexdigest()


def _records(cases: list[dict], sid: str | None) -> list[dict]:
    with cf.ProcessPoolExecutor(WORKERS, initializer=_patch, initargs=(sid or "",)) as pool:
        return list(pool.map(_layout_record, cases, chunksize=8))


def _manifest(cases: list[dict], workers: int, sid: str | None) -> dict[str, str]:
    with cf.ProcessPoolExecutor(workers, initializer=_patch, initargs=(sid or "",)) as pool:
        return dict(
            zip([c["id"] for c in cases], pool.map(_digest, cases, chunksize=4), strict=True)
        )


# --- choosing the cases -------------------------------------------------------------------------


def _s4_case() -> dict:
    """A variability_some_years planet whose drawn year (2018 to 2020) is not one of its labels."""
    for case in v4.population_cases("selftest"):
        if case["mechanism"] != "variability_some_years":
            continue
        meta, _ = pv2.deserialize(v4.build_case(case)[0])
        drawn = v4.ABSENT_YEARS[meta["parameters"]["var_absent_position"]]
        if drawn not in [s["year"] for s in meta["data"]["sectors"]]:
            return case
    raise SystemExit("S4: no selftest case whose drawn year is not a label")


def _s6_case() -> dict:
    """A planet whose first parameter attempt draws a period below 2 d and is accepted."""
    for case in v4.population_cases("selftest"):
        if case["class"] != "planet":
            continue
        meta, _ = pv2.deserialize(v4.build_case(case)[0])
        if meta["attempt_seed"] == case["seed"] and meta["parameters"]["period"] < 2.0:
            return case
    raise SystemExit("S6: no selftest planet accepted at its first attempt with a period < 2 d")


# --- make (patched) -----------------------------------------------------------------------------


def make(sid: str, work: Path) -> None:
    work.mkdir(parents=True, exist_ok=True)
    if sid == "S2":
        records = _records(v4.population_cases("acceptance"), "S2")
        (work / "records.json").write_text(json.dumps(records), encoding="utf-8")
        return
    if sid in ("S4", "S6"):
        case = _s4_case() if sid == "S4" else _s6_case()
        _patch(sid)
        (work / "case.json").write_text(json.dumps(case), encoding="utf-8")
        (work / "case.bin").write_bytes(v4.build_case(case)[0])
        return
    _patch(sid)
    if sid == "S3":
        (work / "cases.json").write_text(
            json.dumps(v4.population_cases("acceptance")), encoding="utf-8"
        )
        return
    raise SystemExit(f"{sid} has no make step")


def _make(sid: str, work: Path) -> None:
    """The ``make`` step in its own process; ``work`` is this sabotage's folder (``<DIR>/<id>``)."""
    subprocess.run(
        [sys.executable, str(Path(__file__)), "make", sid, "--work", str(work.parent)], check=True
    )


# --- one sabotage (unpatched) -------------------------------------------------------------------


def _verdict(control: list[str], sabotaged: list[str], must: str, coverage: int) -> dict:
    caught = bool(sabotaged) and any(must in p for p in sabotaged)
    return {
        "control": {"passed": not control, "problems": control[:5], "coverage": coverage},
        "sabotaged": {"problems": sabotaged[:5], "n_problems": len(sabotaged)},
        "reason_required": must,
        "caught": caught and not control and coverage > 0,
    }


def one(sid: str, work: Path) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    if sid == "S1":
        cases = v4.population_cases("selftest")
        control, sabotaged, n = [], [], 0
        for case in cases:
            lay = v4.draw_layout(case)
            result = v4.domain.check_domain(lay["times"])
            n += sum(t.size for t in lay["times"])
            if not result.inside:
                control.append(f"{case['id']}: {result.reason}")
            moved = []
            for t in lay["times"]:
                og = int(np.argmax(np.diff(t)))
                moved.append(np.concatenate([t[: og + 1], t[og + 1 :] + 2.0]))
            bad = v4.domain.check_domain(moved)
            others = [c for c in ("D1", "D2", "D3", "D5") if not bad.conditions[c]]
            if bad.failed != "D4" or "orbit gap" not in (bad.reason or "") or others:
                sabotaged.append(f"{case['id']}: not caught as D4 alone ({bad.reason}, {others})")
            else:
                sabotaged.append(f"{case['id']}: D4 orbit gap")
        missed = [p for p in sabotaged if "not caught" in p]
        out = _verdict(control, sabotaged, "D4 orbit gap", n)
        out["caught"] = out["caught"] and not missed and len(sabotaged) == len(cases)
        out["sabotaged"]["missed"] = missed[:5]
        return out
    if sid == "S2":
        _make("S2", work)
        broken = json.loads((work / "records.json").read_text(encoding="utf-8"))
        clean = _records(v4.population_cases("acceptance"), None)
        control = chk.coverage_problems(clean)
        sabotaged = chk.coverage_problems(broken)
        return _verdict(control, sabotaged, "first_start", len(clean))
    if sid == "S3":
        _make("S3", work)
        broken = json.loads((work / "cases.json").read_text(encoding="utf-8"))
        clean = v4.population_cases("acceptance")
        return _verdict(
            chk.allocation_problems(clean),
            chk.allocation_problems(broken),
            "allocation",
            len(clean),
        )
    if sid in ("S4", "S6"):
        _make(sid, work)
        case = json.loads((work / "case.json").read_text(encoding="utf-8"))
        blob = (work / "case.bin").read_bytes()
        clean = v4.build_case(case)[0]
        c_report = chk.built_report(case, clean)
        control = c_report["problems"] + band.check(clean)["problems"]
        if sid == "S4":
            sabotaged = chk.built_report(case, blob)["problems"] + band.check(blob)["problems"]
            out = _verdict(control, sabotaged, "[4] var_absent_year", c_report["cadences"])
            out["caught"] = out["caught"] and any("is not a label" in p for p in sabotaged)
        else:
            sabotaged = chk.built_report(case, blob)["problems"]
            out = _verdict(control, sabotaged, "[6] redraws", c_report["cadences"])
        out["case"] = case["id"]
        return out
    if sid in ("S5a", "S5b"):
        picks = (
            [
                next(c for c in v4.population_cases("selftest") if c["class"] == "planet"),
                next(
                    c
                    for c in v4.population_cases("selftest")
                    if c["class"] == "false_positive" and c["mechanism"] != "blend"
                ),
            ]
            if sid == "S5a"
            else [next(c for c in v4.population_cases("selftest") if c["class"] == "no_transit")]
        )
        control, sabotaged, n = [], [], 0
        for case in picks:
            blob = v4.build_case(case)[0]
            report = band.check(blob)
            control += report["problems"]
            n += report["snr_checked"] + report["flux_checked"]
            meta, arrays = pv2.deserialize(blob)
            if sid == "S5a":
                meta["expected_snr"]["global"] *= 1.0 + 1e-6
            else:
                flux = arrays["lc/flux"].copy()
                flux[1000:1060] -= 1000e-6
                arrays["lc/flux"] = flux
            index = meta.pop("arrays")
            bad = pv2.serialize(meta, [(name, arrays[name], dtype) for name, dtype, _ in index])
            sabotaged += band.check(bad)["problems"]
        must = "expected SNR global" if sid == "S5a" else "the rebuilt flux differs"
        out = _verdict(control, sabotaged, must, n)
        if sid == "S5a":
            out["caught"] = out["caught"] and sum(must in p for p in sabotaged) == len(picks)
        return out
    if sid == "S7":
        cases = v4.population_cases("selftest")
        clean = [_manifest(cases, 1, None), _manifest(cases, 2, None)]
        broken = [_manifest(cases, 1, "S7"), _manifest(cases, 2, "S7")]
        control = [] if clean[0] == clean[1] else ["the unbroken generations differ"]
        diff = sum(broken[0][k] != broken[1][k] for k in broken[0])
        sabotaged = [f"{diff} of {len(cases)} digests differ"] if diff else []
        return _verdict(control, sabotaged, "digests differ", len(cases))
    if sid == "S8":
        control = chk.x2f_report()["problems"]
        real = v4.domain.ONE_YEAR_DAYS
        v4.domain.ONE_YEAR_DAYS = (345.0, 370.0)
        try:
            sabotaged = chk.x2f_report()["problems"]
        finally:
            v4.domain.ONE_YEAR_DAYS = real
        return _verdict(control, sabotaged, "D5", 3)
    if sid == "S9":
        history = chk.git_history()
        control = chk.order_problems(history)
        code = next(h for h in history if any(p in chk.CODE_FILES for p in h[1]))
        tests = next(h for h in history if any(p in chk.TEST_FILES for p in h[1]))
        invented = [h for h in history if h not in (code, tests)]
        invented.insert(1, code)
        invented.insert(2, tests)
        return _verdict(control, chk.order_problems(invented), "order", len(history))
    raise SystemExit(f"unknown sabotage {sid}")


def _error_line(stderr: str, returncode: int | None = None) -> str:
    """Only the exception's type (and the exit code), never its free message, so that no path,
    user, host or share name reaches the output; the full error stays in the console."""
    lines = [x for x in stderr.strip().splitlines() if x.strip()]
    found = re.match(r"([A-Za-z_][A-Za-z0-9_.]*)", lines[-1].strip()) if lines else None
    kind = found.group(1) if found else "no output"
    return f"{kind} (exit {returncode})" if returncode is not None else kind


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("all", "one", "make"))
    parser.add_argument("sid", nargs="?")
    parser.add_argument("--work", required=True)
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    work = Path(args.work)
    if args.mode == "make":
        make(args.sid, work / args.sid)
        return 0
    if args.mode == "one":
        print(json.dumps({"id": args.sid, **one(args.sid, work / args.sid)}, sort_keys=True))
        return 0
    results = []
    for sid in IDS:
        done = subprocess.run(
            [sys.executable, str(Path(__file__)), "one", sid, "--work", str(work)],
            capture_output=True,
            text=True,
        )
        lines = [x for x in done.stdout.splitlines() if x.startswith("{")]
        if done.returncode != 0 or not lines:
            print(done.stderr, file=sys.stderr)
            error = _error_line(done.stderr, done.returncode)
            results.append({"id": sid, "caught": False, "error": error})
        else:
            results.append(json.loads(lines[-1]))
        print(sid, results[-1].get("caught"), flush=True)
    out = {
        "format": "refute-population-v4-sabotages/1",
        "all_caught": all(r.get("caught") for r in results),
        "sabotages": results,
    }
    Path(args.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if out["all_caught"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
