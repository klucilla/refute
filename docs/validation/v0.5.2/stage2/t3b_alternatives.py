"""v0.5.2 stage 2: how many stars other definitions of T3b's population would admit (the
maintainer's decision of 2026-11-09, #216, item 3 (b)). **Counts only:** no draw, no light
curve, no identifier, name or row leaves this script, and no definition here is adopted: an
amendment of the sampling frame needs the maintainer's approval. ``method_status:
not_validated``.

The population asked about: a TOI false positive that is an eclipsing binary on the target. A
nearby eclipsing binary does not enter T3b. The inputs are the refreshed TOI table
(``toi-fetch.json``), the ExoFOP observing notes (``obsnotes-fetch.json``) and the frozen v0.5
inputs. Every set starts from the frame's own pool (``selection.fp_pool`` without already
known targets).

**A, B and C are screening sets, not populations** (Codex's answer,
``t3b-frame-round-1-answer.md``): a TESS disposition of EB or a word in the comments does not
say which star eclipses. **E is a lexical screen for the positive-evidence branch** that
answer asks for: a follow-up note filed on the same TIC whose sentence states an eclipsing
binary on the target (the TFOP spectroscopic codes SEB1 and SEB2, or an explicit on-target
statement), not negated or hedged, naming no other TIC, on a star with no unrefuted note of a
nearby binary. It is a frozen lexical rule, reproducible and **not adjudicated**: it reads
sentences alone, so it loses a note's subject, qualifications and chronology, and its
``nearby`` flag counts mentions (requests and clearances too). Its counts are candidates for
the maintainer, not a certificate (``t3b-status.md``).

**The yields are scenarios under an assumed transport, not forecasts.** ``flat`` scales the
mean rate of v0.5's walk (11 of 41, a metadata-acceptance rate over TESS-EB members);
``strata`` keeps both strata of a proxy of the domain rules (7 of the 11 walked stars that
pass it, 4 of the 30 that fail it). The proxy reads the TOI table's stellar parameters and
sector numbers instead of the TIC and the MAST products, misses D-3, D-8 and D-2's calendar
years, and rejected 4 accepted stars: it must never serve as a domain exclusion. The intervals
are two-sided Clopper-Pearson intervals of the historical rate; they are not prediction
intervals for an accepted count, and correct nothing for contamination or for the change of
population.

Usage (from the project root): ``.venv/Scripts/python.exe <this file>``; writes
``t3b-alternatives.json``.
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
INPUTS = ROOT / ".cache/v05/inputs-attempts/attempt-01"
SELECTION = ROOT / "calibration/v0.5/selection/selection.json"
NEED_ACCEPT = 11

NEB_TEXT = re.compile(
    r"\bN?BEBs?\b|\bNEBs?\b|\bNPC\b|nearby|neighbou?r|off.?target|centroid|contaminat|background"
    r"|blend|companion star|\bSEB\s*on\b",
    re.IGNORECASE,
)
EB_TEXT = re.compile(r"\bEB\b|eclipsing binar|\bSB[12]\b|\bSB\b|\bSEB[12]?\b", re.IGNORECASE)
SPAN_SECTORS = 12  # about 300 days between the first and the last sector

SENTENCE = re.compile(r"(?<=[.;!?\n])\s+")
POSITIVE = re.compile(
    r"\bSEB[12]\b|on.target\s+(?:EB|eclips)|(?:\bEB\b|eclipsing binary)\s+on.target"
    r"|target\s+is\s+an?\s+(?:EB\b|eclipsing)",
    re.IGNORECASE,
)
HEDGE = re.compile(
    r"\b(?:not|no|non|rule[sd]?\s+out|unlikely|possibl[ey]|maybe|perhaps|might|could|if|whether"
    r"|suspect\w*|candidate)\b",
    re.IGNORECASE,
)
NEARBY = re.compile(r"\bN?BEBs?\b|\bNEBs?\b|off.?target", re.IGNORECASE)
OTHER_TIC = re.compile(r"TIC[\s-]*(\d+)", re.IGNORECASE)


def number(value: str | None) -> float | None:
    try:
        out = float(value) if value not in (None, "") else None
    except ValueError:
        return None
    return out


def proxy_passes(row: dict[str, str]) -> bool:
    """D-1, D-2 and D-4 to D-7, approximated from the TOI table's columns (docstring)."""
    sectors = sorted({int(s) for s in re.findall(r"\d+", row.get("Sectors") or "")})
    logg = number(row.get("Stellar log(g) (cm/s^2)"))
    radius = number(row.get("Stellar Radius (R_Sun)"))
    radius_err = number(row.get("Stellar Radius (R_Sun) err"))
    teff = number(row.get("Stellar Eff Temp (K)"))
    tmag = number(row.get("TESS Mag"))
    return (
        len(sectors) >= 3
        and sectors[-1] - sectors[0] >= SPAN_SECTORS
        and logg is not None
        and logg >= 4.0
        and radius is not None
        and radius > 0
        and radius_err is not None
        and radius_err / radius <= 0.25
        and teff is not None
        and 3200.0 <= teff <= 7000.0
        and tmag is not None
        and 8.0 <= tmag <= 12.0
    )


def interval(k: int, n: int) -> list[float]:
    from scipy import stats

    low = float(stats.beta.ppf(0.025, k, n - k + 1)) if k else 0.0
    high = float(stats.beta.ppf(0.975, k + 1, n - k)) if k < n else 1.0
    return [low, high]


def note_verdict(tic: int, text: str) -> tuple[bool, bool]:
    """(states an eclipsing binary on this target, states a nearby binary), sentence by sentence."""
    positive, nearby = False, False
    for sentence in SENTENCE.split(text):
        others = {int(n) for n in OTHER_TIC.findall(sentence)} - {tic}
        hedged = bool(HEDGE.search(sentence))
        if NEARBY.search(sentence) and not hedged:
            nearby = True
        if POSITIVE.search(sentence) and not hedged and not others:
            positive = True
    return positive, nearby


def noted_sets(path: Path, pool: set[int]) -> tuple[set[int], set[int], int]:
    csv.field_size_limit(100_000_000)
    positive: set[int] = set()
    nearby: set[int] = set()
    notes = 0
    text = path.read_bytes().decode("utf-8", errors="replace")
    for row in csv.DictReader(io.StringIO(text, newline="")):
        cell = (row.get("TIC ID") or "").strip()
        if not cell.isdigit() or int(cell) not in pool:
            continue
        notes += 1
        is_positive, is_nearby = note_verdict(int(cell), row.get("notes") or "")
        if is_positive:
            positive.add(int(cell))
        if is_nearby:
            nearby.add(int(cell))
    return positive, nearby, notes


def main() -> None:
    from refute.packs.tess.calib05 import c3select
    from refute.packs.tess.calib05.values import C3
    from refute.packs.tess.discover import selection as sel

    fetched = json.loads((HERE / "toi-fetch.json").read_text("utf-8"))
    notes_fetch = json.loads((HERE / "obsnotes-fetch.json").read_text("utf-8"))
    cache = ROOT / ".cache/v052/toi"
    toi = sel.toi_rows((cache / fetched["sha256"] / "toi.csv").read_bytes())
    planets = sel.pscomppars_rows((INPUTS / "pscomppars.csv").read_bytes())
    planet_tics = {t for t in (sel.parse_tic(r.get("tic_id")) for r in planets) if t}
    eb = sel.tess_eb_tics((INPUTS / "tess_eb.tsv").read_bytes())
    known = set(c3select.known_targets(ROOT))
    pool = [p for p in sel.fp_pool(toi, planet_tics, C3.fp_min_depth_ppm) if p.tic_id not in known]
    walk = json.loads(SELECTION.read_text("utf-8"))["pools"]["false_positive"]["walk"]
    walked = {int(d["tic_id"]) for d in walk["decisions"]}
    accepted = {int(d["tic_id"]) for d in walk["decisions"] if d["reason"] == "accepted"}

    by_tic = {p.tic_id: p.row for p in pool}
    passes = {t for t, r in by_tic.items() if proxy_passes(r)}
    walked_in = walked & set(by_tic)
    n_pass, n_fail = len(walked_in & passes), len(walked_in - passes)
    k_pass, k_fail = len(accepted & walked_in & passes), len(accepted & walked_in - passes)
    flat = len(accepted) / len(walked)
    rate_pass, rate_fail = k_pass / n_pass, k_fail / n_fail

    def text(tic: int) -> str:
        return by_tic[tic].get("Comments") or ""

    neb = {t for t in by_tic if NEB_TEXT.search(text(t))}
    flagged = {t for t, r in by_tic.items() if (r.get("TESS Disposition") or "").strip() == "EB"}
    worded = {t for t in by_tic if EB_TEXT.search(text(t))}
    in_frame = set(by_tic) & eb
    positive, nearby, n_notes = noted_sets(
        cache / notes_fetch["sha256"] / "obsnotes.csv", set(by_tic)
    )
    e_set = positive - nearby
    definitions = {
        "the_approved_frame_tess_eb": in_frame,
        "A_screening_tess_disposition_eb_without_neb_text": flagged - neb,
        "B_screening_eb_in_comments_without_neb_text": worded - neb,
        "C_screening_both_A_and_B": (flagged & worded) - neb,
        "E_positive_tfop_note_on_the_target": e_set,
        "the_approved_frame_union_E": in_frame | e_set,
    }
    rows = {}
    for name, members in definitions.items():
        never = members - walked
        screened = never & passes
        rows[name] = {
            "members": len(members),
            "kept_from_the_approved_frame": len(members & in_frame),
            "dropped_from_the_approved_frame": len(in_frame - members),
            "beyond_the_approved_frame": len(members - in_frame),
            "never_walked": len(never),
            "never_walked_passing_the_proxy": len(screened),
            "scenario_flat_rate": len(never) * flat,
            "scenario_two_strata": len(screened) * rate_pass + len(never - screened) * rate_fail,
            "scenario_proxy_passing_subset_only": len(screened) * rate_pass,
        }
    doc = {
        "label": "T3b: other definitions of the population; counts only; none is adopted",
        "method_status": "not_validated",
        "toi_table": f"toi-fetch.json, retrieved {fetched['retrieved_utc']}",
        "observing_notes": {
            "source": f"obsnotes-fetch.json, retrieved {notes_fetch['retrieved_utc']}",
            "notes_on_pool_stars": n_notes,
            "stars_with_a_positive_note": len(positive),
            "stars_with_a_lexical_nearby_flag": len(nearby),
            "stars_with_both_left_out_of_E": len(positive & nearby),
        },
        "pool": {
            "toi_false_positives": len(by_tic),
            "with_tess_disposition_eb": len(flagged),
            "with_neb_text": len(neb),
            "with_eb_text": len(worded),
            "tess_eb_members_with_neb_text": len(in_frame & neb),
            "tess_eb_members_with_tess_disposition_eb": len(in_frame & flagged),
            "tess_eb_members_with_a_positive_note": len(in_frame & positive),
            "tess_eb_members_with_a_nearby_note": len(in_frame & nearby),
        },
        "historical_rates_not_forecasts": {
            "flat": {
                "accepted": len(accepted),
                "walked": len(walked),
                "interval": interval(len(accepted), len(walked)),
            },  # fmt: skip
            "proxy_passes": {
                "accepted": k_pass,
                "walked": n_pass,
                "interval": interval(k_pass, n_pass),
            },
            "proxy_fails": {
                "accepted": k_fail,
                "walked": n_fail,
                "interval": interval(k_fail, n_fail),
            },
        },
        "needed_acceptances": NEED_ACCEPT,
        "definitions": rows,
    }
    (HERE / "t3b-alternatives.json").write_text(
        json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps(doc, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
