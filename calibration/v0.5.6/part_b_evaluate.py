"""v0.5.6 part B (confirmatory): the claim's verdict, computed only from the drawn targets' records
(docs/plans/v0.5.6-plan-amendment-1.md; the maintainer's decisions of 2026-11-22, 13:00, item 3;
#218). Deterministic: exact arithmetic for the test, no randomness. ``method_status:
not_validated``. Limits label: 'WEAKENED; does not meet D1, D2, D4, T2a'.

**What it measures:** agreement of the labelled v0.5 battery with TFOPWG dispositions on
photometry that overlaps theirs; never that it "detects false positives".

**Per drawn target** (``part-b-draw.json``, strata ``planet`` and ``fp``), from its record:
- **event**: status OK, nonzero coverage (a decisive test examined data), outcome REFUTED and
  ``identity.matched`` (the battery's own signal is the TOI's: period factor 1 within 0.1 %, epoch
  within half the TOI's duration);
- **non-event**: status OK with nonzero coverage and no event; or status ERROR (counted as a
  non-event in the denominator, by the decision's ERROR rule);
- **loss**: status ERROR, MISSING_PRODUCTS, OK with zero coverage, or no record (a run stopped
  by a cap). ERROR is both a non-event in the denominator and a loss for the cap.

**The data rule:** the draw's status must be ``complete`` or ``short``; in each stratum the losses
must be at most ``floor(MAX_LOSS_FRACTION * drawn)``. Otherwise the claim is **INCONCLUSIVE**.

**The primary test:** Fisher's exact test, one-sided (the event rate of ``fp`` above that of
``planet``), on the 2 x 2 table of events and non-events over the denominators; ``p`` is the
hypergeometric upper tail, computed with integers. ``ALPHA = 0.05``.

**The guard on the planet stratum** (in D2's style): the event rate at most ``GUARD_RATE`` (0.05)
and its upper Wilson 95 % bound at most ``GUARD_UPPER`` (0.10).

**The verdict:**
- INCONCLUSIVE: the data rule fails;
- SURVIVED: ``p <= ALPHA`` and the guard holds;
- WEAKENED: ``p <= ALPHA`` and the guard fails;
- REFUTED: ``p > ALPHA``.

**Secondary endpoints** (reported, never part of the verdict): plain REFUTED (one-sided, ``fp``
above ``planet``), SURVIVED (one-sided, ``planet`` above ``fp``), Wilson 95 % intervals, the first
decisive fatal FAIL of each event, and the outcomes per stratum with signal identity.

Usage (from the project root): ``.venv/Scripts/python.exe -B calibration/v0.5.6/part_b_evaluate.py``
(reads ``.cache/v056/partb/records``; writes ``part-b-verdict.json`` and ``part-b-verdict.md``
next to this script, refusing to write over them).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import time
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DRAW = HERE / "part-b-draw.json"
LOCK = HERE / "claim.lock.json"
RECORDS = ROOT / ".cache/v056/partb/records"
OUT_JSON = HERE / "part-b-verdict.json"
OUT_MD = HERE / "part-b-verdict.md"
CLAIM_ID = "tess-v0.5.6-part-b-fp-agreement"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
STRATA = ("planet", "fp")
OUTCOMES = ("SURVIVED", "WEAKENED", "REFUTED", "INCONCLUSIVE")
ALPHA = Fraction(5, 100)
GUARD_RATE = Fraction(5, 100)
GUARD_UPPER = 0.10
MAX_LOSS_FRACTION = Fraction(10, 100)
Z95 = 1.959963984540054


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- statistics (pure) -----------------------------------------------------------------------


def fisher_greater(a: int, b: int, c: int, d: int) -> Fraction:
    """One-sided Fisher exact p-value that the first row's rate a/(a+b) exceeds the second's
    c/(c+d): P(X >= a) for X hypergeometric with the table's margins. Exact (a Fraction)."""
    if min(a, b, c, d) < 0:
        raise ValueError("negative cell")
    n1, n2, k = a + b, c + d, a + c
    total = math.comb(n1 + n2, k)
    if total == 0:
        return Fraction(1)
    hi = min(n1, k)
    tail = sum(math.comb(n1, x) * math.comb(n2, k - x) for x in range(a, hi + 1))
    return Fraction(tail, total)


def wilson(k: int, n: int, z: float = Z95) -> tuple[float, float] | None:
    """The Wilson score interval of k successes in n trials, or None when n is 0."""
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


# --- records (pure) --------------------------------------------------------------------------


def covered(r: dict) -> bool:
    """Part A's rule: status OK and a decisive test with coverage above zero."""
    if r.get("status") != "OK":
        return False
    return any((r["tests"].get(n, {}).get("coverage") or 0) > 0 for n in r["decisive"])


def matched(r: dict) -> bool:
    return bool((r.get("identity") or {}).get("matched"))


def first_fatal(r: dict) -> str | None:
    for name, t in r.get("tests", {}).items():
        if name in r.get("decisive", []) and t["status"] == "FAIL" and t["severity"] == "fatal":
            return name
    return None


def classify(r: dict | None) -> tuple[str, bool]:
    """(class, is_loss): class is ``event``, ``non_event`` or ``excluded``."""
    if r is None:
        return "excluded", True
    if r.get("status") == "ERROR":
        return "non_event", True
    if not covered(r):
        return "excluded", True
    if r.get("outcome") == "REFUTED" and matched(r):
        return "event", False
    return "non_event", False


def stratum_summary(drawn: list[dict], records: dict[str, dict]) -> dict:
    events = non_events = losses = 0
    refuted = survived = 0
    outcomes: Counter = Counter()
    by_identity: Counter = Counter()
    statuses: Counter = Counter()
    event_causes: Counter = Counter()
    for t in drawn:
        r = records.get(f"TIC-{t['tic_id']}")
        cls, loss = classify(r)
        statuses[r.get("status", "?") if r else "no record"] += 1
        losses += loss
        if cls == "excluded":
            continue
        if cls == "event":
            events += 1
            event_causes[first_fatal(r) or "(none)"] += 1
        else:
            non_events += 1
        if r.get("status") == "OK":
            outcomes[r["outcome"]] += 1
            by_identity[(r["outcome"], matched(r))] += 1
            refuted += r["outcome"] == "REFUTED"
            survived += r["outcome"] == "SURVIVED"
    n = events + non_events
    return {
        "drawn": len(drawn),
        "statuses": dict(statuses),
        "losses": losses,
        "loss_cap": math.floor(MAX_LOSS_FRACTION * len(drawn)),
        "denominator": n,
        "events": events,
        "event_rate": events / n if n else None,
        "event_wilson95": wilson(events, n),
        "event_first_decisive_fatal_fail": dict(event_causes),
        "refuted": refuted,
        "refuted_wilson95": wilson(refuted, n),
        "survived": survived,
        "survived_wilson95": wilson(survived, n),
        "outcomes": {o: outcomes.get(o, 0) for o in OUTCOMES},
        "outcomes_by_identity": {
            f"{o}/{'matched' if m else 'not matched'}": by_identity.get((o, m), 0)
            for o in OUTCOMES
            for m in (True, False)
        },
    }


def verdict(draw_status: str, s: dict[str, dict]) -> tuple[str, str, dict]:
    """The claim's verdict, its reason and the tests (pure)."""
    p, f = s["planet"], s["fp"]
    tests: dict = {}
    if draw_status not in ("complete", "short"):
        return "INCONCLUSIVE", f"the draw is {draw_status}", tests
    over = [k for k in STRATA if s[k]["losses"] > s[k]["loss_cap"]]
    if over:
        return "INCONCLUSIVE", "losses above the cap in: " + ", ".join(over), tests
    pv = fisher_greater(f["events"], f["denominator"] - f["events"], p["events"],
                        p["denominator"] - p["events"])  # fmt: skip
    rate = Fraction(p["events"], p["denominator"]) if p["denominator"] else Fraction(1)
    upper = (p["event_wilson95"] or (0.0, 1.0))[1]
    guard = rate <= GUARD_RATE and upper <= GUARD_UPPER
    tests = {
        "primary_fisher_one_sided_p": float(pv),
        "primary_fisher_one_sided_p_exact": f"{pv.numerator}/{pv.denominator}",
        "alpha": float(ALPHA),
        "guard": {
            "planet_event_rate": float(rate),
            "rate_max": float(GUARD_RATE),
            "wilson95_upper": upper,
            "upper_max": GUARD_UPPER,
            "holds": guard,
        },  # fmt: skip
        "secondary_refuted_fisher_one_sided_p": float(
            fisher_greater(
                f["refuted"],
                f["denominator"] - f["refuted"],
                p["refuted"],
                p["denominator"] - p["refuted"],
            )  # fmt: skip
        ),
        "secondary_survived_planet_above_fp_p": float(
            fisher_greater(
                p["survived"],
                p["denominator"] - p["survived"],
                f["survived"],
                f["denominator"] - f["survived"],
            )  # fmt: skip
        ),
    }
    if pv > ALPHA:
        return "REFUTED", f"Fisher one-sided p = {float(pv):.4g} > {float(ALPHA)}", tests
    if not guard:
        return "WEAKENED", f"p = {float(pv):.4g} <= {float(ALPHA)}, but the guard fails", tests
    return "SURVIVED", f"p = {float(pv):.4g} <= {float(ALPHA)} and the guard holds", tests


# --- main ------------------------------------------------------------------------------------


def write_once(path: Path, text: str) -> None:
    if path.exists():
        raise SystemExit(f"{path.name} exists; never written over")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, "utf-8", newline="\n")
    os.replace(tmp, path)


def main() -> None:
    draw = json.loads(DRAW.read_text("utf-8"))
    if draw.get("lock_sha256") != sha256(LOCK.read_bytes()):
        raise SystemExit("the draw does not name this lock")
    records, files = {}, []
    for f in sorted(RECORDS.glob("*.json")):
        raw = f.read_bytes()
        r = json.loads(raw)
        if r.get("claim_id") != CLAIM_ID:
            raise SystemExit(f"{f.name} is not a record of {CLAIM_ID}")
        records[r["target_key"]] = r
        files.append({"file": f.name, "sha256": sha256(raw)})
    s = {k: stratum_summary(draw["arms"][k]["chosen"], records) for k in STRATA}
    v, reason, tests = verdict(draw["status"], s)
    doc = {
        "schema": "refute-v056-part-b-verdict-1",
        "claim_id": CLAIM_ID,
        "verdict": v,
        "reason": reason,
        "limits_label": LABEL,
        "method_status": "not_validated",
        "measures": "agreement with TFOPWG dispositions on overlapping photometry",
        "draw_status": draw["status"],
        "lock_sha256": draw["lock_sha256"],
        "code_sha256": sha256(Path(__file__).read_bytes()),
        "tests": tests,
        "strata": s,
        "records": files,
        "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    write_once(OUT_JSON, json.dumps(doc, indent=1) + "\n")
    lines = [
        "# v0.5.6 part B: the claim's verdict",
        "",
        f"**{v}** ({reason}). Limits label: '{LABEL}'. `method_status: not_validated`. The claim "
        "measures agreement with TFOPWG dispositions on overlapping photometry, never that the "
        "battery detects false positives.",
        "",
        "| Stratum | Drawn | Losses (cap) | Denominator | Events | Rate | Wilson 95 % |",
        "|---|---|---|---|---|---|---|",
    ]
    for k in STRATA:
        x = s[k]
        w = x["event_wilson95"]
        lines.append(
            f"| {k} | {x['drawn']} | {x['losses']} ({x['loss_cap']}) | {x['denominator']} | "
            f"{x['events']} | {'n/a' if x['event_rate'] is None else f'{x["event_rate"]:.3f}'} | "
            f"{'n/a' if w is None else f'{w[0]:.3f} to {w[1]:.3f}'} |"
        )
    lines += ["", "```", json.dumps(tests, indent=1), "```", ""]
    write_once(OUT_MD, "\n".join(lines))
    print(v, reason)


if __name__ == "__main__":
    main()
