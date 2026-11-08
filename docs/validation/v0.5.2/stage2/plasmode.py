"""v0.5.2 stage 2: the acceptance's size from the real joint layout of A0's records (Codex's round 1
on the design replaced the Gaussian toy of ``sizing.py``). A development simulation: it resamples
the archived records of A0 round 2 of v0.5.1, a finished acceptance run (none of it is
confirmation data). It runs no estimator and decides nothing about any target. ``method_status:
not_validated``.

**The reference model.** The pulls of each family member are standardized to mean 0 and standard
deviation 1, so the world being simulated is "every member correctly calibrated", while what the
records carry stays: the shared curves, the several events per curve, the skew and tails, the
missingness. The records are version 3's, so the shapes are a proxy for version 4's.

**A dataset at size ``T``.** Whole curves are resampled with replacement inside each original run,
each run scaled by the factor that gives its component's least available priced member ``T``
expected contributing curves. The family is every member with availability at least 0.25, without
``matched_*``. Members sharing curves, or pooling several runs, form one component.

**The procedure, exactly the stage-1 specification.** ``m``, ``V``, the cluster-robust errors,
centred studentized roots, the maximum over members, parameters and tails, 2,000 replicates of
whole curves within each run, the critical value at order statistic 1,935. ``G_min`` is ``0.95
T``, a member below it is not measured and the family fails.

**Phases** (shards of the driver, each a bundle of components, per-replicate seeds):

- ``q``: the critical value at the sizes of ``Q_TARGETS``;
- ``power``: whole-family certification over many datasets at each size of ``POWER_TARGETS``, with
  the mean ``q`` plus two standard errors, interpolated in ``T``;
- ``nested``: the first evaluation, 40 datasets per size, its first rule not met (design, section
  1); kept as a record;
- ``evaluate <T>``: the evaluation that fixes ``T``, after Codex's round 2: 200 datasets on the seed
  label ``evaluation``, each running the **complete procedure of the specification**: retention
  before any resampling (a member below ``G_min`` or with an undefined error is not measured and
  the family fails), the studentized max-t with its own 2,000 replicates, the degenerate-replicate
  rule (11 or more: not measured), and the additional checks per family, a family being section x
  statistic x noise model (the concatenated mean and variance of its retained members, under the
  same whole-curve weights, with the order statistic 1,935 of their own maximum root). Sizes run
  in the fixed order of
  ``EVAL_TARGETS``; the first whose one-sided Clopper-Pearson lower bound at level ``1 - 0.05/4``
  reaches 0.90 is ``T``.

Usage: ``launch_affinity.ps1 -Script <this file> -Arguments build,...``; sub-commands ``build``,
``q``, ``power``, ``nested <T>``, ``evaluate <T>``.
"""

from __future__ import annotations

import hashlib
import json
import math
import pickle
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
import driver  # noqa: E402

DRIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/v0.5.1-closing-2026-11-08/accept")
OUT = ROOT / ".cache/v052/s2/plasmode"
TABLE = OUT / "components.pkl"
SECTIONS = ("a01", "a02", "a04", "a05", "a07", "a08")
BOX = ("box_odd", "box_even", "box_diff")
PIXEL = ("large_minus_core", "sap_minus_expected")
UNITS = {"a01": 200, "a02": 700, "a04": 700, "a05": 400, "a07": 700, "a08g": 700}
FLOOR = 0.25
REPLICATES = 2000
ORDER = 1935
G_MIN_FRACTION = 0.95
BUNDLES = 48
Q_TARGETS = (7000, 10000)
Q_REPS = 6
POWER_TARGETS = (6000, 7000, 8000, 9000, 10000, 11000, 12000, 14000)
POWER_REPS = 400
NESTED_REPS = 40
EVAL_TARGETS = (9000, 10000, 11000, 12000)
EVAL_REPS = 200
EVAL_LEVEL = 1.0 - 0.05 / len(EVAL_TARGETS)
EVAL_FLOOR = 0.90
EVAL_CAP_HOURS = 35.0
EVAL_MAX_SHARD_SECONDS = 1000.0
DEGENERATE_LIMIT = 11
BATCH = 100
CAP_HOURS = 30.0
WORKERS = 12
PIN = tuple(range(8, 32, 2))
LO_V, HI_V, MEAN_TOL = 0.81, 1.21, 0.1
CPU_PER_UNIT_KEY = {
    "a01": "a01",
    "a02": "a02",
    "a04": "a04",
    "a05": "a05",
    "a07": "a07",
    "a08e": "a08",
    "a08g": "a08",
}


def _contributions(section: str, r: dict):
    """(run key, [(member key, pull), ...]) of one record."""
    if section == "a01":
        return ("a01", r["noise"], r["kind"]), [
            (("a01", r["noise"], st), p) for st, p in (r.get("pulls") or [])
        ]
    if section in ("a02", "a04"):
        run = (section, r["noise"], r["kind"], r["sectors"])
        if r.get("stratum") is None:
            return run, []
        names = BOX + (PIXEL if section == "a02" else ())
        return run, [
            ((section, r["noise"], r["stratum"], r["sectors"], n), (r.get("pulls") or {}).get(n))
            for n in names
        ]
    if section == "a05":
        run = ("a05", r["pattern"], r["spacing"], r["combo"], r["noise"], r["kind"], r["sectors"])
        if r.get("stratum") is None:
            return run, []
        head = ("a05", r["pattern"], r["spacing"], r["combo"], r["noise"], r["stratum"])
        return run, [((*head, r["sectors"], n), (r.get("pulls") or {}).get(n)) for n in BOX]
    if section == "a07":
        run = ("a07", r["sectors"])
        if r.get("stratum") is None or len(r.get("strata_of_events") or []) < 2:
            return run, []
        return run, [
            (("a07", r["sectors"], r["stratum"], n), (r.get("pulls") or {}).get(n)) for n in BOX
        ]
    if "shape" not in r:
        return None, []
    multiple = f"{r['multiple']:g}"
    if r["shape"] == "event":
        run = ("a08e", r["noise"], r["kind"], multiple)
        return run, [
            (("a08e", r["noise"], st, multiple, r["branch"]), p) for st, p in (r.get("pulls") or [])
        ]
    run = ("a08g", r["shape"], r["noise"], r["kind"], r["sectors"], multiple)
    if r.get("stratum") is None:
        return run, []
    head = ("a08g", r["shape"], r["noise"], r["stratum"], r["sectors"], multiple, r["branch"])
    return run, [((*head, n), (r.get("pulls") or {}).get(n)) for n in BOX]


def _units(run) -> int:
    if run[0] == "a08e":
        return 100
    return UNITS[run[0]]


def build() -> None:
    """Read the archived records once and write the standardized per-curve aggregates."""
    curves: dict = {}
    sources: dict = {}
    for section in SECTIONS:
        path = DRIVE / f"a0r2-{section}" / "records.jsonl"
        digest = hashlib.sha256()
        lines, not_ok = 0, 0
        with path.open("rb") as fh:
            for raw in fh:
                digest.update(raw)
                lines += 1
                r = json.loads(raw)
                run, parts = _contributions(section, r)
                if run is None:
                    raise SystemExit(f"{section}: a record without its scheduled run")
                row: dict = {}
                if r.get("status") == "OK":
                    for member, p in parts:
                        if p is not None and math.isfinite(p):
                            row.setdefault(member, []).append(float(p))
                else:
                    not_ok += 1  # a scheduled curve that gave nothing stays in its denominators
                curves.setdefault(run, []).append(row)
        sources[section] = {"sha256": digest.hexdigest(), "records": lines, "not_ok": not_ok}
        print("read", section, flush=True)
    short = {
        repr(run): len(rows) for run, rows in curves.items() if len(rows) != _units(run)
    }  # fmt: skip
    if short:
        raise SystemExit(f"runs whose curves differ from the schedule: {short}")
    (HERE / "plasmode-sources.json").write_text(
        json.dumps(sources, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    pulls: dict = {}
    contributors: dict = {}
    runs_of: dict = {}
    for run, rows in curves.items():
        for row in rows:
            for member, values in row.items():
                pulls.setdefault(member, []).extend(values)
                contributors[member] = contributors.get(member, 0) + 1
                runs_of.setdefault(member, set()).add(run)
    priced = {
        m
        for m, g in contributors.items()
        if min(g / max(_units(r) for r in runs_of[m]), 1.0) >= FLOOR and len(pulls[m]) > 2
    }
    scale = {m: (float(np.mean(pulls[m])), float(np.std(pulls[m]))) for m in priced}
    parent: dict = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for m in priced:
        for r in runs_of[m]:
            parent[find(("run", r))] = find(("member", m))
    groups: dict = {}
    for m in priced:
        groups.setdefault(find(("member", m)), {"members": [], "runs": set()})
        groups[find(("member", m))]["members"].append(m)
        groups[find(("member", m))]["runs"].update(runs_of[m])
    table = []
    for group in groups.values():
        members = sorted(group["members"], key=repr)
        index = {m: j for j, m in enumerate(members)}
        runs = []
        for run in sorted(group["runs"], key=repr):
            rows = curves[run]
            n = np.zeros((len(rows), len(members)), dtype=np.int32)
            s1 = np.zeros_like(n, dtype=float)
            s2 = np.zeros_like(n, dtype=float)
            for i, row in enumerate(rows):
                for m, values in row.items():
                    j = index.get(m)
                    if j is None:
                        continue
                    mean, sd = scale[m]
                    z = (np.asarray(values) - mean) / sd
                    n[i, j], s1[i, j], s2[i, j] = z.size, float(z.sum()), float(np.sum(z * z))
            runs.append({"key": run, "n": n, "s1": s1, "s2": s2})
        g_orig = sum((r["n"] > 0).sum(axis=0) for r in runs)
        table.append({"members": members, "runs": runs, "min_g": int(g_orig.min())})
    table.sort(key=lambda comp: repr(comp["members"][0]))  # seeds are per component index
    OUT.mkdir(parents=True, exist_ok=True)
    with TABLE.open("wb") as fh:
        pickle.dump(table, fh, protocol=5)
    print("components", len(table), "members", sum(len(c["members"]) for c in table), flush=True)


_TABLE = None


def _load():
    global _TABLE
    if _TABLE is None:
        with TABLE.open("rb") as fh:
            _TABLE = pickle.load(fh)  # noqa: S301 - written by this script, in the local cache
    return _TABLE


def seed_of(*parts) -> int:
    text = "refute-v052-dev:plasmode:" + ":".join(str(p) for p in parts)
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def draw(component, target, rng):
    """A dataset: the concatenated per-curve aggregates and each run's slice."""
    factor = target / component["min_g"]
    ns, s1s, s2s, slices, start = [], [], [], [], 0
    for run in component["runs"]:
        size = int(math.ceil(run["n"].shape[0] * factor))
        idx = rng.integers(0, run["n"].shape[0], size=size)
        ns.append(run["n"][idx])
        s1s.append(run["s1"][idx])
        s2s.append(run["s2"][idx])
        slices.append((start, start + size))
        start += size
    return np.concatenate(ns), np.concatenate(s1s), np.concatenate(s2s), slices


def features(n, s1, s2):
    """The per-curve quantities whose weighted sums give every statistic, shape (10, curves, M)."""
    n = n.astype(float)
    return np.stack([n, s1, s2, s1 * s1, s1 * n, n * n, s2 * s2, s2 * s1, s2 * n, (n > 0) * 1.0])


def estimates(totals):
    """``m``, ``V``, their squared cluster-robust errors and ``G``, from the weighted sums."""
    nn, a1, a2, a11, a1n, ann, b22, b21, b2n, g = totals
    with np.errstate(divide="ignore", invalid="ignore"):
        m = a1 / nn
        v = (a2 - 2.0 * m * a1 + nn * m * m) / nn
        factor = g / (g - 1.0)
        se_m2 = factor * (a11 - 2.0 * m * a1n + m * m * ann) / (nn * nn)
        a, c = -2.0 * m, m * m - v
        u2 = b22 + a * a * a11 + c * c * ann + 2.0 * a * b21 + 2.0 * c * b2n + 2.0 * a * c * a1n
        se_v2 = factor * u2 / (nn * nn)
    return m, v, se_m2, se_v2, g


def bootstrap_max(component, data, rng, replicates=REPLICATES):
    """The per-replicate maximum root of a dataset."""
    n, s1, s2, slices = data
    x = features(n, s1, s2)
    m, v, _, _, _ = estimates(x.sum(axis=1))
    out = np.empty(replicates)
    size = x.shape[1]
    for b in range(replicates):
        weight = np.zeros(size)
        for lo, hi in slices:
            weight[lo:hi] = np.bincount(rng.integers(0, hi - lo, size=hi - lo), minlength=hi - lo)
        totals = np.einsum("fcm,c->fm", x, weight)
        ms, vs, se_m2, se_v2, _ = estimates(totals)
        with np.errstate(divide="ignore", invalid="ignore"):
            roots = np.concatenate(
                [np.abs(ms - m) / np.sqrt(se_m2), np.abs(vs - v) / np.sqrt(se_v2)]
            )
        out[b] = np.inf if not np.all(np.isfinite(roots)) else float(roots.max())
    return out


def certified(data, q, target):
    """Per member: the size is enough and both intervals lie inside the tolerances."""
    m, v, se_m2, se_v2, g = estimates(features(*data[:3]).sum(axis=1))
    half_m, half_v = q * np.sqrt(se_m2), q * np.sqrt(se_v2)
    return (
        (g >= G_MIN_FRACTION * target)
        & (np.abs(m) + half_m < MEAN_TOL)
        & (v - half_v > LO_V)
        & (v + half_v < HI_V)
    )


def bootstrap_totals(x, slices, rng, replicates=REPLICATES):
    """The weighted sums of every feature and column in every replicate, shape (10, M, B): whole
    curves resampled within each run, in blocks so that the products are dense-matrix ones."""
    features_n, size, members = x.shape
    flat = x.transpose(0, 2, 1).reshape(features_n * members, size)
    out = np.empty((features_n, members, replicates))
    for start in range(0, replicates, BATCH):
        count = min(BATCH, replicates - start)
        weights = np.zeros((count, size))
        for b in range(count):
            for lo, hi in slices:
                draws = rng.integers(0, hi - lo, size=hi - lo)
                weights[b, lo:hi] = np.bincount(draws, minlength=hi - lo)
        out[:, :, start : start + count] = (flat @ weights.T).reshape(features_n, members, count)
    return out


def _roots(est, boot):
    """The per-replicate centred studentized roots, shape (2 * M, B); non-finite when degenerate."""
    m, v = est
    ms, vs, se_m2, se_v2, _ = estimates(boot)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.concatenate(
            [np.abs(ms - m[:, None]) / np.sqrt(se_m2), np.abs(vs - v[:, None]) / np.sqrt(se_v2)]
        )


def _inside(m, v, se_m2, se_v2, q):
    half_m, half_v = q * np.sqrt(se_m2), q * np.sqrt(se_v2)
    return (np.abs(m) + half_m < MEAN_TOL) & (v - half_v > LO_V) & (v + half_v < HI_V)


def aggregate_key(member) -> tuple:
    """The additional checks' family: statistic x noise model, within a section (no pooling
    across sections, so that a deviation in one cannot be diluted by another)."""
    section = member[0]
    if section == "a01":
        return (section, "pull", member[1])
    if section in ("a02", "a04"):
        return (section, member[4], member[1])
    if section == "a05":
        return (section, member[7], member[4])
    if section == "a07":
        return (section, member[3], "all")
    if section == "a08e":
        return (section, "event", member[1])
    return (section, member[7], member[2])


def complete_procedure(target, rep, label) -> dict:
    """One dataset through the whole acceptance procedure of the specification."""
    table = _load()
    best = np.zeros(REPLICATES)
    observed, aggregate_obs, aggregate_boot = [], {}, {}
    not_measured = 0
    for c, comp in enumerate(table):
        rng = np.random.default_rng(seed_of(label, target, rep, c))
        n, s1, s2, slices = draw(comp, target, rng)
        x = features(n, s1, s2)
        m, v, se_m2, se_v2, g = estimates(x.sum(axis=1))
        keep = (g >= G_MIN_FRACTION * target) & (se_m2 > 0) & (se_v2 > 0)
        not_measured += int(np.count_nonzero(~keep))
        if not keep.any():
            continue
        by_key: dict = {}
        for j in np.flatnonzero(keep):
            by_key.setdefault(aggregate_key(comp["members"][j]), []).append(int(j))
        keys = sorted(by_key, key=repr)
        wholes = [
            features(*(a[:, by_key[k]].sum(axis=1) for a in (n, s1, s2))) for k in keys
        ]  # fmt: skip
        retained = int(np.count_nonzero(keep))
        columns = np.concatenate([x[:, :, keep], np.stack(wholes, axis=2)], axis=2)
        boot = bootstrap_totals(columns, slices, rng)
        roots = _roots((m[keep], v[keep]), boot[:, :retained, :])
        degenerate = ~np.all(np.isfinite(roots), axis=0)
        largest = np.where(degenerate, np.inf, np.nan_to_num(roots, posinf=np.inf).max(axis=0))
        best = np.maximum(best, largest)
        observed.append((m[keep], v[keep], se_m2[keep], se_v2[keep]))
        for i, key in enumerate(keys):
            aggregate_obs[key] = aggregate_obs.get(key, 0.0) + wholes[i].sum(axis=1)
            aggregate_boot[key] = aggregate_boot.get(key, 0.0) + boot[:, retained + i, :]
    degenerate_count = int(np.count_nonzero(np.isinf(best)))
    q = float(np.sort(best)[ORDER - 1])
    failed = sum(int(np.count_nonzero(~_inside(*o, q))) for o in observed)
    names = sorted(aggregate_obs, key=repr)
    obs = np.stack([aggregate_obs[s] for s in names], axis=1)
    m, v, se_m2, se_v2, _ = estimates(obs)
    boot = np.stack([aggregate_boot[s] for s in names], axis=1)
    roots = _roots((m, v), boot)
    largest = np.where(np.all(np.isfinite(roots), axis=0), roots.max(axis=0), np.inf)
    q_aggregate = float(np.sort(largest)[ORDER - 1])
    failed_aggregate = int(np.count_nonzero(~_inside(m, v, se_m2, se_v2, q_aggregate)))
    return {
        "rep": rep,
        "q": q,
        "q_aggregate": q_aggregate,
        "not_measured": not_measured,
        "failed_members": failed,
        "failed_aggregate": failed_aggregate,
        "degenerate_replicates": degenerate_count,
        "certified": bool(
            not_measured == 0
            and failed == 0
            and failed_aggregate == 0
            and degenerate_count < DEGENERATE_LIMIT
        ),
    }


def shard_evaluate(arg) -> bytes:
    target, rep = arg
    row = complete_procedure(target, rep, "evaluation")
    return json.dumps(row, sort_keys=True).encode() + b"\n"


def _bundle(i: int) -> list[int]:
    return list(range(len(_load())))[i::BUNDLES]


def shard_q(arg) -> bytes:
    phase, target, rep, bundle = arg
    table = _load()
    best = np.zeros(REPLICATES)
    for c in _bundle(bundle):
        rng = np.random.default_rng(seed_of(phase, target, rep, c))
        data = draw(table[c], target, rng)
        best = np.maximum(best, bootstrap_max(table[c], data, rng))
    return best.astype("<f8").tobytes()


def shard_power(arg) -> bytes:
    target, q, reps, bundle = arg
    table = _load()
    fails = np.zeros(reps, dtype="<i4")
    for c in _bundle(bundle):
        for rep in range(reps):
            rng = np.random.default_rng(seed_of("power", target, rep, c))
            ok = certified(draw(table[c], target, rng), q, target)
            fails[rep] += int(np.count_nonzero(~ok))
    return fails.tobytes()


def shard_nested(arg) -> bytes:
    target, rep = arg
    table = _load()
    best = np.zeros(REPLICATES)
    datasets = []
    for c in range(len(table)):
        rng = np.random.default_rng(seed_of("nested", target, rep, c))
        data = draw(table[c], target, rng)
        best = np.maximum(best, bootstrap_max(table[c], data, rng))
        datasets.append(data)
    q = float(np.sort(best)[ORDER - 1])
    fails = sum(int(np.count_nonzero(~certified(d, q, target))) for d in datasets)
    return json.dumps({"q": q, "fails": fails, "rep": rep}, sort_keys=True).encode() + b"\n"


def fingerprint() -> str:
    """The code, the table's bytes, the source manifest, the environment's lock and the versions."""
    h = hashlib.sha256()
    for path in (
        Path(__file__),
        HERE / "driver.py",
        TABLE,
        HERE / "plasmode-sources.json",
        ROOT / "uv.lock",
    ):
        h.update(hashlib.sha256(path.read_bytes()).digest())
    h.update(f"{sys.version_info[:3]}:{np.__version__}".encode())
    return h.hexdigest()[:16]


def _run(name, fn, shards, cap, **kwargs):
    fp = fingerprint()
    run = driver.Run(
        OUT / name / fp, fn, shards, fp, cap, WORKERS, initializer=_load, pin=PIN, **kwargs
    )
    print(name, len(shards), run.execute(), flush=True)
    return run


def q_phase():
    shards = [
        (f"q-{t}-{r}-{b:02d}", ("q", t, r, b))
        for t in Q_TARGETS
        for r in range(Q_REPS)
        for b in range(BUNDLES)
    ]
    run = _run("q", shard_q, shards, CAP_HOURS)
    done = run._done()
    if len(done) < len(shards):
        return
    values = {}
    for t in Q_TARGETS:
        qs = []
        for r in range(Q_REPS):
            maxima = np.zeros(REPLICATES)
            for b in range(BUNDLES):
                data = run._paths(f"q-{t}-{r}-{b:02d}")[0].read_bytes()
                maxima = np.maximum(maxima, np.frombuffer(data, dtype="<f8"))
            qs.append(float(np.sort(maxima)[ORDER - 1]))
        values[str(t)] = qs
    (OUT / "q.json").write_text(json.dumps(values, indent=1) + "\n", "utf-8")
    print(values, flush=True)


def design_q(target) -> float:
    values = json.loads((OUT / "q.json").read_text("utf-8"))
    points = sorted((int(k), float(np.mean(v) + 2.0 * np.std(v, ddof=1) / math.sqrt(len(v))))
                    for k, v in values.items())  # fmt: skip
    return float(np.interp(target, [p[0] for p in points], [p[1] for p in points]))


def power_phase():
    shards = [
        (f"p-{t}-{b:02d}", (t, design_q(t), POWER_REPS, b))
        for t in POWER_TARGETS
        for b in range(BUNDLES)
    ]
    run = _run("power", shard_power, shards, CAP_HOURS)
    if len(run._done()) < len(shards):
        return
    out = {}
    for t in POWER_TARGETS:
        fails = np.zeros(POWER_REPS, dtype=int)
        for b in range(BUNDLES):
            fails += np.frombuffer(run._paths(f"p-{t}-{b:02d}")[0].read_bytes(), dtype="<i4")
        out[str(t)] = {
            "q": design_q(t),
            "whole_family": float(np.mean(fails == 0)),
            "mean_members_not_certified": float(np.mean(fails)),
        }
        print(t, out[str(t)], flush=True)
    (OUT / "power.json").write_text(json.dumps(out, indent=1) + "\n", "utf-8")


def nested_phase(target):
    shards = [(f"n-{target}-{r:03d}", (target, r)) for r in range(NESTED_REPS)]
    run = _run(f"nested-{target}", shard_nested, shards, CAP_HOURS)
    if len(run._done()) == len(shards):
        rows = [json.loads(line) for line in run.assemble().splitlines()]
        print("whole-family", sum(r["fails"] == 0 for r in rows), "of", len(rows), flush=True)


def evaluate_phase(target):
    """The evaluation that fixes ``T``; the rule is in the module's docstring."""
    from scipy import stats

    if target not in EVAL_TARGETS:
        raise SystemExit("not a candidate size")
    shards = [(f"e-{target}-{r:03d}", (target, r)) for r in range(EVAL_REPS)]
    run = _run(
        f"evaluate-{target}",
        shard_evaluate,
        shards,
        EVAL_CAP_HOURS,
        max_shard_seconds=EVAL_MAX_SHARD_SECONDS,
    )
    if not run.completed():
        print("not complete: no result is published", flush=True)
        return
    rows = [json.loads(line) for line in run.assemble().splitlines()]
    k = sum(r["certified"] for r in rows)
    lower = float(stats.beta.ppf(1.0 - EVAL_LEVEL, k, EVAL_REPS - k + 1)) if k else 0.0
    doc = {
        "target": target,
        "datasets": EVAL_REPS,
        "certified": k,
        "one_sided_level": EVAL_LEVEL,
        "lower_bound": lower,
        "passes": lower >= EVAL_FLOOR,
        "q_min_max": [min(r["q"] for r in rows), max(r["q"] for r in rows)],
        "not_measured_datasets": sum(r["not_measured"] > 0 for r in rows),
        "failed_member_datasets": sum(r["failed_members"] > 0 for r in rows),
        "failed_aggregate_datasets": sum(r["failed_aggregate"] > 0 for r in rows),
        "degenerate_datasets": sum(r["degenerate_replicates"] >= DEGENERATE_LIMIT for r in rows),
        "spent_cpu_hours": run.spent_seconds() / 3600.0,
        "fingerprint": fingerprint(),
    }
    (HERE / f"plasmode-evaluate-{target}.json").write_text(
        json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(doc, flush=True)


if __name__ == "__main__":
    command = sys.argv[1:] or [""]
    if command[0] == "build":
        build()
    elif command[0] == "q":
        q_phase()
    elif command[0] == "power":
        power_phase()
    elif command[0] == "nested":
        nested_phase(int(command[1]))
    elif command[0] == "evaluate":
        evaluate_phase(int(command[1]))
    elif command[0] == "check":
        # the new code against the first evaluation's on the same seeds: the same critical value
        import time

        started = time.process_time()
        new = complete_procedure(9000, 10, "nested")
        spent = time.process_time() - started
        old = json.loads(shard_nested((9000, 10)))
        print(new, old, "cpu of the new code", spent, flush=True)
        if abs(new["q"] - old["q"]) > 1e-9 or new["failed_members"] != old["fails"]:
            raise SystemExit("the new code differs from the first evaluation's")
        print("the same critical value and the same failures", flush=True)
    else:
        raise SystemExit("usage: plasmode.py build|q|power|nested <T>|evaluate <T>")
