"""v0.5.2 stage 2: the distribution of one family member's variance estimate in the plasmode, under
the seed labels of the power phase and of the nested phase, at several sizes. It exists to explain
why every failure of the nested evaluation is the same member (``plasmode-diag.json``) and to look
at that member's source records. Development records only; it decides nothing.
``method_status: not_validated``.

Usage: ``launch_affinity.ps1 -Script <this file>``.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plasmode as pm  # noqa: E402

WORKERS = 12
TARGETS = (9000, 10000, 14000)
REPS = 400
Q = 4.58
NAME = "('a08g', 'hetero', 'hetero', 'partial', 2, '2.5', 'included', 'box_odd')"


def one(arg):
    label, target, rep, c, j = arg
    comp = pm._load()[c]
    rng = np.random.default_rng(pm.seed_of(label, target, rep, c))
    data = pm.draw(comp, target, rng)
    m, v, se_m2, se_v2, g = pm.estimates(pm.features(*data[:3]).sum(axis=1))
    return float(m[j]), float(v[j]), float(np.sqrt(se_m2[j])), float(np.sqrt(se_v2[j])), float(g[j])


def provenance() -> dict:
    """The source record of the largest pull of this member, without its arrays."""
    path = pm.DRIVE / "a0r2-a08" / "records.jsonl"
    best, keep = 0.0, None
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if (
                r.get("shape") != "hetero"
                or r.get("noise") != "hetero"
                or r.get("sectors") != 2
                or r.get("stratum") != "partial"
                or r.get("branch") != "included"
                or f"{r.get('multiple', 0):g}" != "2.5"
            ):
                continue
            value = (r.get("pulls") or {}).get("box_odd")
            if value is not None and abs(value) > best:
                best, keep = abs(value), r
    return {k: v for k, v in keep.items() if not isinstance(v, list | dict)} | {"box_odd": best}


def sensitivity(arg):
    """One dataset with the largest curve's selection weight or its pull scaled. Without
    ``restandardize`` this perturbs location, scale and tail together; with it, the perturbed
    reference is brought back to mean 0 and variance 1, so that only the tail's shape differs."""
    target, rep, c, j, index, weight, scale, restandardize = arg
    comp = pm._load()[c]
    rng = np.random.default_rng(pm.seed_of("tail", target, rep, weight, scale, restandardize))
    run = comp["runs"][0]
    size = int(np.ceil(run["n"].shape[0] * target / comp["min_g"]))
    p = np.ones(run["n"].shape[0])
    p[index] = weight
    p /= p.sum()
    idx = rng.choice(run["n"].shape[0], size=size, p=p)
    n, s1, s2 = run["n"][idx].copy(), run["s1"][idx].copy(), run["s2"][idx].copy()
    hit = idx == index
    s1[hit, j] *= scale
    s2[hit, j] *= scale * scale
    if restandardize:
        used = run["n"][:, j] > 0
        z = run["s1"][:, j].astype(float)
        z[index] *= scale
        w = p[used] / p[used].sum()
        mu = float(np.sum(w * z[used]))
        var = float(np.sum(w * (z[used] - mu) ** 2))
        new_s2 = (s2[:, j] - 2.0 * mu * s1[:, j] + n[:, j] * mu * mu) / var
        s1[:, j] = (s1[:, j] - n[:, j] * mu) / np.sqrt(var)
        s2[:, j] = new_s2
    _, v, _, se_v2, _ = pm.estimates(pm.features(n, s1, s2).sum(axis=1))
    return float(v[j] + Q * np.sqrt(se_v2[j]) >= pm.HI_V)


def tail_sensitivity(c, j, pool) -> dict:
    """The member's failure rate as the frequency and the size of its largest pull change."""
    run = pm._load()[c]["runs"][0]
    index = int(np.argmax(run["s2"][:, j]))
    out = {}
    for target in (9000, 10000):
        for label, weight, scale in (
            ("frequency_x0", 0.0, 1.0),
            ("frequency_x0.5", 0.5, 1.0),
            ("as_recorded", 1.0, 1.0),
            ("frequency_x2", 2.0, 1.0),
            ("size_x0.75", 1.0, 0.75),
            ("size_x1.25", 1.0, 1.25),
        ):
            for restandardize in (False, True):
                work = [(target, r, c, j, index, weight, scale, restandardize) for r in range(REPS)]
                rate = float(np.mean(list(pool.map(sensitivity, work, chunksize=20))))
                name = "tail_only_restandardized" if restandardize else "location_scale_and_tail"
                out[f"{target}-{label}-{name}"] = rate
                print(target, label, name, rate, flush=True)
    return out


def main() -> None:
    table = pm._load()
    c = next(i for i, comp in enumerate(table) if NAME in [repr(x) for x in comp["members"]])
    comp = table[c]
    j = [repr(x) for x in comp["members"]].index(NAME)
    out: dict = {
        "component": c,
        "member": NAME,
        "members_in_component": len(comp["members"]),
        "source_min_g": comp["min_g"],
        "runs": [],
    }
    z2_all = []
    for run in comp["runs"]:
        n, s2 = run["n"][:, j], run["s2"][:, j]
        used = n > 0
        out["runs"].append(
            {
                "key": repr(run["key"]),
                "curves": int(n.shape[0]),
                "contributing": int(used.sum()),
                "max_events_per_curve": int(n.max()),
                "max_s2_per_curve": float(s2.max()),
            }
        )
        z2_all.extend(s2[used].tolist())
    z2 = np.sort(np.asarray(z2_all))[::-1]
    out["largest_per_curve_s2"] = [float(x) for x in z2[:12]]
    out["share_of_s2_in_top_5_curves"] = float(z2[:5].sum() / z2.sum())
    work = [
        (label, t, r, c, j) for label in ("power", "nested") for t in TARGETS for r in range(REPS)
    ]
    out["largest_pull_record"] = provenance()
    with ProcessPoolExecutor(WORKERS, initializer=pm._load) as pool:
        rows = list(pool.map(one, work, chunksize=20))
        out["upper_variance_crossing_rate_at_q_4_58"] = tail_sensitivity(c, j, pool)
    out["by_label_and_size"] = {}
    for i in range(0, len(work), REPS):
        label, t = work[i][0], work[i][1]
        block = np.asarray(rows[i : i + REPS])
        v, se_v = block[:, 1], block[:, 3]
        fail = float(np.mean(v + Q * se_v >= pm.HI_V))
        out["by_label_and_size"][f"{label}-{t}"] = {
            "mean_v": float(v.mean()),
            "sd_v": float(v.std(ddof=1)),
            "max_v": float(v.max()),
            "mean_se_v": float(se_v.mean()),
            "fails_v_high_at_q_4_58": fail,
            "mean_g": float(block[:, 4].mean()),
        }
        print(f"{label}-{t}", out["by_label_and_size"][f"{label}-{t}"], flush=True)
    (HERE / "plasmode-member.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print({k: out[k] for k in ("runs", "largest_per_curve_s2", "share_of_s2_in_top_5_curves")})


if __name__ == "__main__":
    main()
