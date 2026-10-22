"""X2's seeds (x2-declaration.md, section 3): the 8000 realization seeds, and their check against
the seeds of the earlier lots of the population harness (each case's seed and the noise seed of its
first draw: bs-choice, the R_min study's 64 prefixes, the timing lot, and X2's own cases).
Writes x2-seeds.json. No light curve is built.

  python x2_seeds.py <out x2-seeds.json>
"""

import json
import sys
from pathlib import Path

POP = Path(__file__).resolve().parents[4] / "population"
sys.path.insert(0, str(POP))
import x2_study as x2  # noqa: E402

rs, pv2 = x2.rs, x2.pv2


def earlier_seeds() -> dict[str, set[int]]:
    prefixes = [rs.BS_CHOICE_PREFIX, rs.TIMING_PREFIX, x2.PREFIX] + [
        f"{rs.STUDY_PREFIX}-{k}" for k in range(1, max(rs.STUDY_PREFIXES.values()) + 1)
    ]
    out = {}
    for prefix in prefixes:
        seeds = set()
        for case in pv2.population_cases("confirm:" + prefix):
            s = int(case["seed"])
            seeds.add(s)
            seeds.add(pv2.sub_seed(s, "noise"))
        out[prefix] = seeds
    return out


def main() -> int:
    out = Path(sys.argv[1])
    rows = [
        {
            "group": rs.group_of(c),
            "case_id": c["id"],
            "realization": j,
            "seed": str(x2.realization_seed(rs.group_of(c), c["id"], j)),
        }
        for c, j in x2.all_tasks()
    ]
    seeds = [int(r["seed"]) for r in rows]
    earlier = earlier_seeds()
    collisions = {p: sorted(str(s) for s in set(seeds) & e) for p, e in earlier.items()}
    payload = {
        "rule": "first 8 bytes, big-endian, of SHA-256('refute/v0.2.1/stage-1/X2/<group>/<case id>/<j>')",  # noqa: E501
        "n": len(rows),
        "distinct": len(set(seeds)),
        "checked_against": {p: len(e) for p, e in earlier.items()},
        "collisions": {p: c for p, c in collisions.items() if c},
        "seeds": rows,
    }
    out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: payload[k] for k in ("n", "distinct", "collisions")}))
    print("checked against", sum(payload["checked_against"].values()), "earlier seeds")
    return 1 if payload["collisions"] or payload["distinct"] != payload["n"] else 0


if __name__ == "__main__":
    sys.exit(main())
