"""The viability diagnosis after gate 3b (declared in ../README.md, committed before it runs).

Offline: it reads only the files gate 3b saved (.cache/real-controls/pscomppars.csv,
exofop_toi.csv and mast-rows.json), after checking each one's SHA-256 against
../real-controls/result.json, and recomputes the gate's pools and classifications, which must equal
the recorded ones. No download, no engine, no light curve; the domain is not changed, and the
hypothetical rules of section 8 are counted, never adopted.

Per class (the 464 planets and 447 false positives of gate 3b), from the SPOC 120-s light-curve
sectors (each dated by its t_min, its year the UTC calendar year of t_min):
 1. the distinct years, the sectors, and the sectors per observed year;
 2. the spacings: between consecutive sectors' t_min, and between consecutive observed years' first
    sectors, in the declared bins;
 3. the temporal extent: the latest t_max of any sector (its t_min if absent) minus the earliest
    t_min;
 4. the intersections of D1, D2, D3's products and D5, each evaluated on its own;
 5. the coverage patterns (sectors per year from the first to the last observed year);
 6. the sensitivity of the metadata proxy (starts near a New Year, separations near a bound);
 7. descriptive quantities of the pools for the representativeness limits (TESS magnitude and
    period, from the catalogues);
 8. the counts under hypothetical rules H1 to H6.

python viability.py <out.json>
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import math
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[6]
GATE = REPO / "docs/validation/v0.2.1/reopen/stage-1/real-controls"
CACHE = REPO / ".cache" / "real-controls"
CLASSES = ("planets", "false_positives")
NAMES = ("D1", "D2", "D3p", "D5")
# D5's bands are closed: [345, 385] and [710, 750]; the bins between them are open there.
SPACING_LABELS = ("<30 d (adjacent)", "30 to <345 d", "345-385 d (1 yr)", ">385 to <710 d",
                  "710-750 d (2 yr)", ">750 d")  # fmt: skip
EXTENT_LABELS = ("0-1 yr", "1-2 yr", "2-3 yr", "3-4 yr", "4-5 yr", "5-6 yr", "6 yr or more")
NEAR_DAYS = 2.0
BOUNDS = (345.0, 385.0, 710.0, 750.0)
QUANTILES = (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)
HYPOTHESES = ("H1", "H2", "H3", "H4", "H5", "H6")
COMBOS = tuple(
    "".join(("+" if (k >> (3 - j)) & 1 else "-") + c for j, c in enumerate(NAMES))
    for k in range(15, -1, -1)
)

spec = importlib.util.spec_from_file_location("rcc", GATE / "scripts/real_controls_check.py")
rcc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rcc)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_checked() -> tuple[dict, str, str, dict]:
    result = json.loads((GATE / "result.json").read_text(encoding="utf-8"))
    src = result["sources"]
    expected = {
        "pscomppars.csv": src["pscomppars"]["sha256"],
        "exofop_toi.csv": src["exofop_toi"]["sha256"],
        "mast-rows.json": src["mast"]["rows_sha256"],
    }
    for name, digest in expected.items():
        if sha(CACHE / name) != digest:
            raise SystemExit(f"{name}: SHA-256 differs from gate 3b's record")
    ps = (CACHE / "pscomppars.csv").read_text(encoding="utf-8-sig")
    toi = (CACHE / "exofop_toi.csv").read_text(encoding="utf-8-sig")
    rows = json.loads((CACHE / "mast-rows.json").read_text(encoding="utf-8"))
    return result, ps, toi, rows


def spacing_bin(x: float) -> str:
    """The bin of a separation; D5's two bands closed, as D5 judges them."""
    if not math.isfinite(x) or x < 0:
        raise ValueError(f"invalid separation {x!r}")
    if x < 30:
        return SPACING_LABELS[0]
    if x < 345:
        return SPACING_LABELS[1]
    if x <= 385:
        return SPACING_LABELS[2]
    if x < 710:
        return SPACING_LABELS[3]
    if x <= 750:
        return SPACING_LABELS[4]
    return SPACING_LABELS[5]


def extent_bin(days: float) -> str:
    years = days / 365.25
    return EXTENT_LABELS[min(int(years), len(EXTENT_LABELS) - 1)]


def quantiles(values: list[float]) -> dict | None:
    """Nearest-rank on (n - 1) q, halves rounded up (no interpolation); values to 3 decimals."""
    if not values:
        return None
    v = sorted(values)
    return {f"q{int(q * 100)}": round(v[min(len(v) - 1, int(q * (len(v) - 1) + 0.5))], 3)
            for q in QUANTILES}  # fmt: skip


def sectors_of(found: dict) -> tuple[dict[int, float], dict[int, float], set[int]]:
    starts, ends = {}, {}
    for row in found["light_curves"]:
        s, t0 = int(row["sequence_number"]), float(row["t_min"])
        t1 = float(row["t_max"]) if row.get("t_max") is not None else t0
        if not math.isfinite(t1) or t1 < t0:
            raise ValueError(f"invalid t_max {row.get('t_max')!r} for t_min {t0!r}")
        starts[s] = min(t0, starts.get(s, t0))
        ends[s] = max(t1, ends.get(s, t1))
    tpfs = {int(row["sequence_number"]) for row in found["pixel_files"]}
    return starts, ends, tpfs


def new_year_mjd(year: int) -> float:
    """The MJD of 1 January of ``year``, 00:00 UTC."""
    return (datetime(year, 1, 1, tzinfo=UTC) - rcc.MJD0).total_seconds() / 86400.0


def in_band(x: float) -> tuple[bool, bool]:
    """(within one of D5's bands, within the two-year band)."""
    short = rcc.ONE_YEAR[0] <= x <= rcc.ONE_YEAR[1]
    long_ = rcc.TWO_YEARS[0] <= x <= rcc.TWO_YEARS[1]
    return short or long_, long_


def spacing_ok(seps: list[float], limit_long: bool) -> bool:
    flags = [in_band(x) for x in seps]
    if not all(ok for ok, _ in flags):
        return False
    return not limit_long or sum(long_ for _, long_ in flags) <= 1


def describe(tic: int, found: dict) -> dict:
    starts, ends, tpfs = sectors_of(found)
    order = sorted(starts, key=lambda s: starts[s])
    t = [starts[s] for s in order]
    years = [rcc._year(x) for x in t]
    per_year = Counter(years)
    observed = sorted(per_year)
    firsts = [min(starts[s] for s in order if rcc._year(starts[s]) == y) for y in observed]
    seps = [b - a for a, b in zip(t[:-1], t[1:], strict=True)]
    year_seps = [b - a for a, b in zip(firsts[:-1], firsts[1:], strict=True)]
    products = set(starts) <= tpfs
    d = {
        "D1": len(observed) == 3,
        "D2": len(order) == 3,
        "D3p": products,
        "D5": len(seps) == 2 and spacing_ok(seps, limit_long=True),
    }
    pattern = (
        "-".join(str(per_year.get(y, 0)) for y in range(observed[0], observed[-1] + 1))
        if observed
        else "none"
    )
    extent = (max(ends.values()) - t[0]) if t else None
    near_new_year = any(
        abs(new_year_mjd(y) - x) <= NEAR_DAYS or abs(new_year_mjd(y + 1) - x) <= NEAR_DAYS
        for x, y in zip(t, years, strict=True)
    )
    near_bound = any(abs(x - b) <= NEAR_DAYS for x in seps for b in BOUNDS)
    hyp = {
        "H1": len(observed) == 3 and products and spacing_ok(year_seps, limit_long=True),
        "H2": d["D1"] and d["D2"] and products and len(seps) == 2
        and spacing_ok(seps, limit_long=False),
        "H3": len(observed) == 3 and products and spacing_ok(year_seps, limit_long=False),
        "H4": len(observed) >= 3 and products and spacing_ok(year_seps, limit_long=False),
        "H5": len(observed) >= 3 and products,
        "H6": d["D1"] and d["D2"] and products,
    }  # fmt: skip
    return {
        "tic": tic,
        "n_sectors": len(order),
        "n_years": len(observed),
        "per_year": [per_year[y] for y in observed],
        "max_per_year": max(per_year.values()) if per_year else 0,
        "seps": seps,
        "year_seps": year_seps,
        "extent": extent,
        "pattern": pattern,
        "years": observed,
        "conditions": d,
        "inside": all(d.values()),
        "first_failing": next((n for n in NAMES if not d[n]), None),
        "near_new_year": near_new_year,
        "near_bound": near_bound,
        "hyp": hyp,
    }


def catalogue_values(ps: str, toi: str) -> dict[str, dict[int, tuple[float | None, float | None]]]:
    out = {"planets": {}, "false_positives": {}}
    for row in csv.DictReader(io.StringIO(ps)):
        tic = rcc._tic_of(row.get("tic_id"))
        if tic is not None:
            out["planets"].setdefault(
                tic, (rcc._float(row.get("sy_tmag")), rcc._float(row.get("pl_orbper")))
            )
    for row in csv.DictReader(io.StringIO(toi)):
        tic = rcc._tic_of(row.get("TIC ID"))
        if tic is not None:
            out["false_positives"].setdefault(
                tic, (rcc._float(row.get("TESS Mag")), rcc._float(row.get("Period (days)")))
            )
    return out


def summarize(items: list[dict], cat: dict) -> dict:
    n = len(items)
    with_data = [i for i in items if i["n_sectors"] > 0]
    combos = Counter(
        "".join(("+" if i["conditions"][c] else "-") + c for c in NAMES) for i in items
    )
    spacing = Counter(spacing_bin(x) for i in items for x in i["seps"])
    year_spacing = Counter(spacing_bin(x) for i in items for x in i["year_seps"])
    extents = [i["extent"] for i in with_data]
    extent_bins = Counter(extent_bin(x) for x in extents)
    patterns = Counter(i["pattern"] for i in items)
    year_sets = Counter(",".join(map(str, i["years"])) for i in items if i["n_years"] == 3)

    def mags(group):
        return quantiles([cat[i["tic"]][0] for i in group if cat[i["tic"]][0] is not None])

    def periods(group):
        return quantiles([cat[i["tic"]][1] for i in group if cat[i["tic"]][1] is not None])

    three = [i for i in items if i["n_years"] == 3]
    inside = [i for i in items if i["inside"]]
    return {
        "tics": n,
        "with_any_sector": len(with_data),
        "distinct_years": dict(sorted(Counter(i["n_years"] for i in items).items())),
        "sectors": dict(sorted(Counter(i["n_sectors"] for i in items).items())),
        "sectors_per_observed_year": dict(
            sorted(Counter(k for i in items for k in i["per_year"]).items())
        ),
        "max_sectors_in_one_year": dict(sorted(Counter(i["max_per_year"] for i in items).items())),
        "spacings_consecutive_sectors": {lab: spacing.get(lab, 0) for lab in SPACING_LABELS},
        "spacings_consecutive_years_first_sectors": {
            lab: year_spacing.get(lab, 0) for lab in SPACING_LABELS
        },
        "extent_days_quantiles": quantiles(extents),
        "extent_years": {lab: extent_bins.get(lab, 0) for lab in EXTENT_LABELS},
        "each_condition_passing": {c: sum(i["conditions"][c] for i in items) for c in NAMES},
        "each_condition_passing_with_data": {
            c: sum(i["conditions"][c] for i in with_data) for c in NAMES
        },
        "intersections": {c: combos.get(c, 0) for c in COMBOS},
        "first_failing": dict(
            sorted(Counter(i["first_failing"] or "inside" for i in items).items())
        ),
        "patterns_top": dict(patterns.most_common(20)),
        "patterns_distinct": len(patterns),
        "patterns_outside_top": n - sum(c for _, c in patterns.most_common(20)),
        "three_year_calendar_sets": dict(year_sets.most_common(15)),
        "proxy_sensitivity": {
            "a_start_within_2_d_of_new_year": sum(i["near_new_year"] for i in items),
            "a_separation_within_2_d_of_a_bound": sum(i["near_bound"] for i in items),
            "inside_and_either": sum(
                i["inside"] and (i["near_new_year"] or i["near_bound"]) for i in items
            ),  # fmt: skip
            "three_sectors_three_years_and_either": sum(
                i["conditions"]["D1"]
                and i["conditions"]["D2"]
                and (i["near_new_year"] or i["near_bound"])
                for i in items
            ),  # fmt: skip
        },
        "catalogue_tess_mag": {
            "pool": mags(items),
            "with_any_sector": mags(with_data),
            "three_years": mags(three),
            "inside": mags(inside),
        },  # fmt: skip
        "catalogue_period_days": {
            "pool": periods(items),
            "with_any_sector": periods(with_data),
            "three_years": periods(three),
            "inside": periods(inside),
        },  # fmt: skip
        "hypothetical": {h: sum(i["hyp"][h] for i in items) for h in HYPOTHESES},
    }


def main(argv: list[str]) -> int:
    result, ps, toi, rows = load_checked()
    pooled = rcc.pools(ps, toi, set(result["exclusions"]["union"]))
    cat = catalogue_values(ps, toi)
    out = {
        "format": "refute-v0.2.1-viability-3b/1",
        "computed_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "inputs_sha256_checked": True,
        "classes": {},
    }
    union = set(pooled["planets"]) | set(pooled["false_positives"])
    if {str(t) for t in union} != set(rows) or len(union) != result["searched_tics"]:
        raise SystemExit("the pools' TICs differ from the TICs gate 3b searched")
    for name in CLASSES:
        recorded = result["pools"][name]
        if len(pooled[name]) != recorded["candidates"]:
            raise SystemExit(f"{name}: pool size differs from gate 3b's record")
        items = [describe(tic, rows[str(tic)]) for tic in sorted(pooled[name])]
        firsts = Counter(i["first_failing"] for i in items if i["first_failing"])
        gate = {k.replace("D3 products", "D3p"): v for k, v in recorded["failing_first"].items()}
        eligible = sorted(i["tic"] for i in items if i["inside"])
        if dict(firsts) != gate or eligible != sorted(r["tic_id"] for r in recorded["eligible"]):
            raise SystemExit(f"{name}: classification differs from gate 3b's record")
        out["classes"][name] = summarize(items, cat[name])
        out["classes"][name]["hypothetical_tics"] = {
            h: [i["tic"] for i in items if i["hyp"][h]] for h in ("H1", "H2", "H3", "H6")
        }
    Path(argv[1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for name in CLASSES:
        c = out["classes"][name]
        print(name, json.dumps({k: c[k] for k in ("tics", "with_any_sector", "hypothetical",
                                                   "each_condition_passing")}))  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
