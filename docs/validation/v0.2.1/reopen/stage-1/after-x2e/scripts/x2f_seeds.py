"""X2f's seeds (x2f-declaration.md): the 63 000 realization seeds of its three sub-lots, and their
check against each other and against the seeds of the earlier lots (each case's seed and the noise
seed of its first draw: bs-choice, the R_min study's prefixes, the timing lot, X2's, X2e's and X2f's
own prefixes; X2's and X2e's realization seeds). Writes the summary (counts, collisions and the
SHA-256 of the full list's canonical JSON) to x2f-seeds.json, and the full list (63 000 rows, about
12 MB, regenerable by this script) to a second path, kept in `.cache`. No light curve is built.

  python x2f_seeds.py <out x2f-seeds.json> <out full list>
"""

import hashlib
import json
import sys
from pathlib import Path

POP = Path(__file__).resolve().parents[4] / "population"
sys.path.insert(0, str(POP))
import x2_study as x2  # noqa: E402

rs, pv2 = x2.rs, x2.pv2


def earlier_seeds() -> dict[str, set[int]]:
    prefixes = [
        rs.BS_CHOICE_PREFIX,
        rs.TIMING_PREFIX,
        x2.X2.prefix,
        x2.X2E.prefix,
        x2.X2F_PREFIX,
    ] + [f"{rs.STUDY_PREFIX}-{k}" for k in range(1, max(rs.STUDY_PREFIXES.values()) + 1)]
    out = {}
    for prefix in prefixes:
        seeds = set()
        for case in pv2.population_cases("confirm:" + prefix):
            s = int(case["seed"])
            seeds.add(s)
            seeds.add(pv2.sub_seed(s, "noise"))
        out[prefix] = seeds
    for spec in (x2.X2, x2.X2E):
        out[f"{spec.name} realizations"] = {
            x2.realization_seed(rs.group_of(c), c["id"], j, spec) for c, j in x2.all_tasks(spec)
        }
    return out


def main() -> int:
    out, full = Path(sys.argv[1]), Path(sys.argv[2])
    rows = [
        {
            "lot": name,
            "group": rs.group_of(c),
            "case_id": c["id"],
            "mechanism": c["mechanism"],
            "realization": j,
            "seed": str(x2.realization_seed(rs.group_of(c), c["id"], j, x2.LOTS[name])),
        }
        for name in x2.X2F_SEQUENCE
        for c, j in x2.all_tasks(x2.LOTS[name])
    ]
    seeds = [int(r["seed"]) for r in rows]
    earlier = earlier_seeds()
    collisions = {p: sorted(str(s) for s in set(seeds) & e) for p, e in earlier.items()}
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(canonical + "\n", encoding="utf-8", newline="\n")
    payload = {
        "rule": "first 8 bytes, big-endian, of SHA-256('refute/v0.2.1/stage-1/X2f/"
        "refute-v0.2.1-x2-3/<group>/<case id>/<j>')",
        "sequence": list(x2.X2F_SEQUENCE),
        "n": len(rows),
        "per_lot": {n: sum(1 for r in rows if r["lot"] == n) for n in x2.X2F_SEQUENCE},
        "distinct": len(set(seeds)),
        "checked_against": {p: len(e) for p, e in earlier.items()},
        "collisions": {p: c for p, c in collisions.items() if c},
        "seeds_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "seeds_canonical_form": "json.dumps(rows, sort_keys=True, separators=(',', ':'))",
        "first_rows": rows[:3],
    }
    out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: payload[k] for k in ("n", "per_lot", "distinct", "collisions")}))
    print("checked against", sum(payload["checked_against"].values()), "earlier seeds")
    return 1 if payload["collisions"] or payload["distinct"] != payload["n"] else 0


if __name__ == "__main__":
    sys.exit(main())
