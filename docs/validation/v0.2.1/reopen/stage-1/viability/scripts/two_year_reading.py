"""The two-year barriers (two-year-declaration.md), read only: the R_min study's archived records
(the `constant` scenario, R = 8 with bs-choice's pair, the measurable band) and the injected
geometry rebuilt from the frozen generator's own functions (no engine call). Items a (the timing
rule), b (T4 at its best), c (the undetermined hidden noise) and d (the combined optimistic bound).

Integrity, every one failing the run before any output is written: the archive's SHA-256 is the
declared one; every `constant` record's bytes match the study's committed `record-digests.json`,
and the records read are exactly the committed ones, each once; every record's rounds are one per
observing year, checked before they are keyed by year; the study's committed INCONCLUSIVE counts
are reproduced; every timing message parses; the rebuilt layout's years equal the record's, and the
rebuilt parameters equal `build_case`'s on a declared stratified spot check (the only place where
a case's light curve is built, to compare its parameters; no engine call).

  python two_year_reading.py <archive.zip> <record-digests.json> <bs-choice-evaluation.json>
      <study-evaluation.json> <out reading.json> <out geometry.json>
"""

import hashlib
import json
import math
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

POP = Path(__file__).resolve().parents[4] / "population"
sys.path.insert(0, str(POP))
import population_v2 as pv2  # noqa: E402
import rmin_evaluate as ev  # noqa: E402

ARCHIVE_SHA256 = "51fa9b3fab62eda7ed8dee24dd521d251ea12cd7dab77d94902353e6624fba30"
MEMBER_PREFIX = "rmin-study-run/"
R = 8
MIN_SNR = 5.0
CADENCE = 2.0 / 1440.0
HALF_UNIT = 0.005  # the timing message prints hours with two decimals
CAPACITY = {"insufficient_capacity_train", "insufficient_capacity_hidden_noise"}
TIMING = "train-only timing uncertainty in the hidden year"
HIDDEN = "hidden_noise_undetermined"
T4_MAX = 3.0
QUOTAS = {"2 years": 150, "3+ years": 50, "3+ years, variability": 50}
G1_COUNT = {"2 years": 101, "3+ years": 37, "3+ years, variability": 37}
NEEDED = 195
SPOT_PER_STRATUM = 3  # the first 3 targets (in archive order) of each noise x layout stratum
RATIO = re.compile(r"\(([\d.]+) h\) exceeds [\d.]+ transit duration\(s\) \(([\d.]+) h\)")


def kind(reason) -> str:
    return re.split(r"[\d(]", str(reason), maxsplit=1)[0].strip()


def regime(index: int) -> str:
    if index < 100 or 150 <= index < 200:
        return "2 years"
    return "3+ years" if index < 150 else "3+ years, variability"


def parse(target: str) -> tuple[str, str, str, int]:
    prefix, case = target.split("/", 1)
    _, band, noise, index = case.split("-")
    return prefix, band, "white" if noise == "white" else "AR(1)", int(index)


def ratio_of(reason: str) -> dict:
    """The rule's sigma_T / T14 from its message: the point value and the interval compatible with
    the two-decimal rounding of both hours; T4's admission ``(1, 3]`` is then definite, excluded
    or ambiguous."""
    m = RATIO.search(str(reason))
    if m is None:
        raise ValueError(f"a timing message does not parse: {reason!r}")
    s, t = float(m.group(1)), float(m.group(2))
    lo, hi = (s - HALF_UNIT) / (t + HALF_UNIT), (s + HALF_UNIT) / max(t - HALF_UNIT, 1e-9)
    admission = "definite" if hi <= T4_MAX else "excluded" if lo > T4_MAX else "ambiguous"
    return {"point": s / t, "lo": lo, "hi": hi, "t4": admission}


def injected(case: dict) -> tuple[dict, list]:
    """The case's injected parameters and its sectors, by build_case's own steps up to the
    parameters (no noise drawn, no light curve built)."""
    from refute.packs.tess import synthetic
    from refute.packs.tess.params import HoldoutParams, SnrParams
    from refute.packs.tess.types import btjd_to_year

    gate, hidden_min = SnrParams().min_snr, HoldoutParams().min_snr
    seed = int(case["seed"])
    cadences = pv2._sector_cadences(synthetic, pv2._layout(case["mechanism"], case["extra"]))
    time = np.concatenate([t for _, t in cadences])
    years = np.concatenate([np.full(t.size, btjd_to_year(float(t.min()))) for _, t in cadences])
    for attempt in range(pv2.MAX_ATTEMPTS):
        seed_k = seed if attempt == 0 else pv2.sub_seed(seed, "redraw", attempt)
        p = pv2.draw_parameters(case, np.random.default_rng(seed_k), float(time.min()))
        reason = pv2._mechanism_condition(case, p, cadences)
        if reason is None:
            reason, _ = pv2._place_in_band(synthetic, case, p, time, years, gate, hidden_min)
        if reason is None:
            return p, [(btjd_to_year(float(t.min())), t) for _, t in cadences]
    raise RuntimeError(f"{case['id']}: no valid draw")


def train_epochs(t: np.ndarray, p: dict) -> list[int]:
    """Train epochs whose [t_c - T14/2, t_c + T14/2] is at least half covered by cadences (as
    Amendment 28's diagnosis)."""
    period, t0, dur = p["period"], p["t0"], p["duration"]
    n0, n1 = math.ceil((t.min() - t0) / period - 1), math.floor((t.max() - t0) / period + 1)
    out = []
    for n in range(n0, n1 + 1):
        c = t0 + n * period
        if np.count_nonzero(np.abs(t - c) <= dur / 2.0) * CADENCE >= 0.5 * dur:
            out.append(n)
    return out


def hidden_epochs(t: np.ndarray, p: dict) -> list[int]:
    """Hidden epochs whose injected centre lies in the hidden sector's span (as Amendment 28's
    diagnosis and the engine's predictions from the spans, before any cadence coverage)."""
    period, t0 = p["period"], p["t0"]
    lo, hi = float(t.min()), float(t.max())
    return list(range(math.ceil((lo - t0) / period), math.floor((hi - t0) / period) + 1))


def geometry(p: dict, cadences: list, hidden_year: int) -> dict:
    train = np.concatenate([t for y, t in cadences if y != hidden_year])
    hidden = np.concatenate([t for y, t in cadences if y == hidden_year])
    n_train, n_hidden = train_epochs(train, p), hidden_epochs(hidden, p)
    lever = None
    if len(n_train) >= 2 and n_hidden and np.var(n_train) > 0:
        mean = float(np.mean(n_train))
        m = max(abs(n - mean) for n in n_hidden)
        lever = math.sqrt(1.0 + m * m / float(np.var(n_train)))
    return {"n_train": len(n_train), "n_hidden": len(n_hidden), "g_sqrt_n": lever}


def bin_right(x: float, edges: list[float]) -> str:
    """Right-closed bins (a, b]; below the first edge and above the last named apart."""
    if x <= edges[0]:
        return f"<= {edges[0]:g}"
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        if lo < x <= hi:
            return f"({lo:g}, {hi:g}]"
    return f"> {edges[-1]:g}"


def bin_left(x: float, edges: list[float]) -> str:
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        if lo <= x < hi:
            return f"[{lo:g}, {hi:g})"
    return f">= {edges[-1]:g}"


def substituted(rounds, two_years: bool, *, capacity=False, timing=None, hidden=False):
    """The rounds with the named INCONCLUSIVE kinds counted as PASS. ``timing``: None (kept),
    "t4_definite" or "t4_with_ambiguous" (T4's admission, curves with exactly two observing years
    only), or "all"."""
    out = []
    for y, st, rs, rat in rounds:
        k = kind(rs)
        t4 = (
            two_years
            and rat is not None
            and (
                rat["t4"] == "definite"
                or (timing == "t4_with_ambiguous" and rat["t4"] == "ambiguous")
            )
        )
        if st == "INCONCLUSIVE" and (
            (capacity and str(rs) in CAPACITY)
            or (hidden and k == HIDDEN)
            or (timing == "all" and k == TIMING)
            or (timing in ("t4_definite", "t4_with_ambiguous") and k == TIMING and t4)
        ):
            st = "PASS"
        out.append((y, st, rs, rat))
    return out


def status(rounds, years, aggregation: str) -> str:
    plain = [(y, st, rs) for y, st, rs, _ in rounds]
    if aggregation == "legacy":
        return ev.aggregate([st for _, st, _ in sorted(plain)])
    return ev._holdout.spec_b_outcome(plain, years)["status"]


READINGS = {
    "as_read": {},
    "b_t4_definite": {"timing": "t4_definite"},
    "b_t4_with_ambiguous": {"timing": "t4_with_ambiguous"},
    "capacity_only": {"capacity": True},
    "d1_capacity_t4_hidden": {"capacity": True, "timing": "t4_with_ambiguous", "hidden": True},
    "d2_capacity_all_timing_hidden": {"capacity": True, "timing": "all", "hidden": True},
}


def hidden_cause(rec_round: dict) -> str:
    flag = rec_round.get("hidden_noise_undetermined")
    counts = rec_round.get("hidden_n_rep")
    if flag is True:
        return "(i) noise model undetermined"
    if flag is False and isinstance(counts, list) and counts and min(counts) < R:
        return "(ii) noise determined, replicas below R at some dP"
    return "(iii) fields missing or inconsistent"


def main() -> int:
    archive, digests_path, bs, study, out_reading, out_geometry = (Path(p) for p in sys.argv[1:7])
    h = hashlib.sha256()
    with open(archive, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    if h.hexdigest() != ARCHIVE_SHA256:
        print("the archive is not the declared one:", h.hexdigest())
        return 1
    digests = json.loads(digests_path.read_text(encoding="utf-8"))
    expected = {k: v for k, v in digests.items() if k.endswith(".constant.json")}
    pair = json.loads(bs.read_text(encoding="utf-8"))["pairs"][str(R)]
    b, s = float(pair["b"]), float(pair["s"])
    committed = json.loads(study.read_text(encoding="utf-8"))["results"][str(R)]
    cases: dict = {}
    reproduce: dict = defaultdict(Counter)
    statuses: dict = defaultdict(lambda: defaultdict(Counter))
    blocks: dict = defaultdict(lambda: defaultdict(Counter))
    timing: dict = defaultdict(lambda: defaultdict(Counter))
    ratios: dict = defaultdict(Counter)
    admission: dict = defaultdict(Counter)
    hidden: dict = defaultdict(lambda: defaultdict(Counter))
    years_unequal = 0
    spot: dict = defaultdict(list)
    read: set = set()
    with zipfile.ZipFile(archive) as z:
        names = sorted(n for n in z.namelist() if n.endswith(".constant.json"))
        for name in names:
            key = name.removeprefix(MEMBER_PREFIX)
            data = z.read(name)
            if key in read or expected.get(key) != hashlib.sha256(data).hexdigest():
                print("a record is not the committed one, or is read twice:", key)
                return 1
            read.add(key)
            rec = json.loads(data)
            hidden_years = [r["hidden_year"] for r in rec["rounds"]]
            if sorted(hidden_years) != sorted(rec["years"]) or len(set(rec["years"])) != len(
                rec["years"]
            ):
                print("a record's rounds are not one per observing year:", key)
                return 1
            out = ev.target_outcomes(rec, R, b, s, MIN_SNR)
            reproduce[rec["group"]]["targets"] += 1
            reproduce[rec["group"]]["inconclusive"] += out["status"] == "INCONCLUSIVE"
            prefix, band, noise, index = parse(rec["target"])
            if band != "measurable":
                continue
            reg = regime(index)
            cell = f"{noise} | {reg}"
            two = len(rec["years"]) == 2
            rounds = []
            for d in out["rounds"]:
                rat = ratio_of(d["reason"]) if kind(d["reason"]) == TIMING else None
                rounds.append((d["record"]["hidden_year"], d["status"], d["reason"], rat))
            for label, kw in READINGS.items():
                hope = substituted(rounds, two, **kw)
                for agg in ("legacy", "spec_b"):
                    statuses[cell][f"{label}|{agg}"][status(hope, rec["years"], agg)] += 1
                if label != "as_read" and status(hope, rec["years"], "spec_b") == "INCONCLUSIVE":
                    left = sorted({kind(rs) for _, st, rs, _ in hope if st == "INCONCLUSIVE"})
                    blocks[cell][label][" + ".join(left)] += 1
            if reg != "2 years":
                continue
            if prefix not in cases:
                cases[prefix] = {c["id"]: c for c in pv2.population_cases("confirm:" + prefix)}
            case = cases[prefix][rec["target"].split("/", 1)[1]]
            p, cadences = injected(case)
            years_unequal += sorted({y for y, _ in cadences}) != sorted(rec["years"])
            layout = case["mechanism"]
            if layout == "few_train":
                layout += f", {case['extra']['distance_years']} yr"
            stratum = f"{noise} | {layout}"
            if len(spot[stratum]) < SPOT_PER_STRATUM:
                meta, _ = pv2.deserialize(pv2.build_case(case)[0])
                q = meta["parameters"]
                spot[stratum].append(
                    all(abs(q[k] - p[k]) < 1e-12 for k in ("period", "t0", "duration"))
                )
            pbin = bin_left(p["period"], [1.5, 2.5, 3.5, 4.5, 5.5])
            for (y, st, rs, rat), d in zip(rounds, out["rounds"], strict=True):
                g = geometry(p, cadences, y)
                stopped = st == "INCONCLUSIVE" and kind(rs) == TIMING
                lever = g["g_sqrt_n"]
                lbin = "none" if lever is None else bin_left(lever, [0, 10, 30, 60, 100, 200])
                for axis, value in (
                    ("layout", layout),
                    ("hidden year", str(y)),
                    ("train transits", str(g["n_train"])),
                    ("period (d)", pbin),
                    ("g_sqrt_n", lbin),
                    ("hidden epochs", "none" if g["n_hidden"] == 0 else "some"),
                ):
                    timing[noise][f"{axis}: {value}"]["rounds"] += 1
                    timing[noise][f"{axis}: {value}"]["stopped"] += stopped
                if stopped:
                    ratios[noise][bin_right(rat["point"], [1.0, 1.5, 2.0, 3.0])] += 1
                    admission[noise][rat["t4"]] += 1
                if st == "INCONCLUSIVE" and kind(rs) == HIDDEN:
                    r0 = d["record"]
                    counts = r0.get("hidden_n_rep") or []
                    cause = hidden_cause(r0)
                    hc = hidden[noise]
                    hc["cause"][cause] += 1
                    hc["cause by layout and hidden year"][f"{cause} | {layout} | {y}"] += 1
                    hc["grid size"][
                        f"{cause} | {bin_left(len(counts), [0, 1, 20, 40, 60, 80])}"
                    ] += 1
                    low = sum(1 for c in counts if c < R)
                    share = (
                        "empty"
                        if not counts
                        else bin_left(low / len(counts), [0, 0.25, 0.5, 0.75, 1.0])
                    )
                    hc["dP points below R"][f"{cause} | {share}"] += 1
                    zero = "empty" if not counts else str(all(c == 0 for c in counts))
                    hc["every count zero"][f"{cause} | {zero}"] += 1
                    mx = max(counts) if counts else None
                    hc["largest count"][
                        f"{cause} | {'empty' if mx is None else bin_left(mx, [0, 1, 4, 8, 16, 32])}"
                    ] += 1
    if read != set(expected):
        print("the records read are not the committed ones:", len(read), len(expected))
        return 1
    check = {
        g: [c["inconclusive"], c["targets"]]
        == [
            committed[g]["inconclusive"]["constant"]["inconclusive_targets"],
            committed[g]["inconclusive"]["constant"]["targets"],
        ]
        for g, c in reproduce.items()
    }
    if sorted(check) != sorted(ev.GROUPS) or not all(check.values()):
        print("the reading does not reproduce the study's committed counts", check)
        return 1
    if years_unequal or not all(v for vs in spot.values() for v in vs):
        print("the rebuilt geometry does not match", years_unequal, dict(spot))
        return 1
    combined = {}
    for noise in ("white", "AR(1)"):
        combined[noise] = {}
        for label in READINGS:
            for agg in ("legacy", "spec_b"):
                key = f"{label}|{agg}"
                per, total = {}, 0.0
                for reg, q in QUOTAS.items():
                    c = statuses[f"{noise} | {reg}"][key]
                    frac = c.get("PASS", 0) / sum(c.values())
                    per[reg] = {
                        "pass_fraction": frac,
                        "g1_count_reached_at_quota": frac * q >= G1_COUNT[reg],
                    }
                    total += frac * q
                combined[noise][key] = {
                    "pass_of_250": total,
                    "reaches_195": total >= NEEDED,
                    "regimes": per,
                }
    reading = {
        "note": __doc__.split("\n\n")[0],
        "integrity": {
            "archive_sha256": ARCHIVE_SHA256,
            "records_read": len(read),
            "reproduction_check": check,
            "rebuilt_years_unequal": years_unequal,
            "build_case_spot_check": dict(spot),
        },
        "statuses": {c: {k: dict(v) for k, v in d.items()} for c, d in sorted(statuses.items())},
        "still_inconclusive_spec_b": {
            c: {k: dict(v) for k, v in d.items()} for c, d in sorted(blocks.items())
        },
        "combined_at_quotas": combined,
    }
    geo = {
        "timing_by_axis": {
            n: {k: dict(v) for k, v in sorted(d.items())} for n, d in timing.items()
        },
        "stopped_ratio_bins": {n: dict(v) for n, v in ratios.items()},
        "t4_admission_of_stopped_rounds": {n: dict(v) for n, v in admission.items()},
        "hidden_noise": {
            n: {k: dict(sorted(v.items())) for k, v in d.items()} for n, d in hidden.items()
        },
    }
    for path, data in ((out_reading, reading), (out_geometry, geo)):
        path.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(reading["integrity"]))
    for noise, d in combined.items():
        for key, v in d.items():
            print(noise, key, round(v["pass_of_250"], 1), v["reaches_195"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
