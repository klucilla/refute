"""Exposure check before the v0.5.13 charter (#218, comment 7203695669, item B1 c).

Question, logged before the run: has any target of the KELT-FP arm, of the planets found from
the ground, or of the Kepler-field (KOI) arms already been examined with tests in this
repository's records? A target examined with tests is exposed, and unusable for v0.6.

Method (the v0.5.10 recheck's, `docs/validation/v0.5.10/recheck_after_codex.py`, read again at
the current HEAD, with no new query and no new target looked at):
- The target lists are the v0.5.10 census tables archived on the Drive on 2026-11-24; each file's
  SHA-256 is checked against `docs/validation/v0.5.10/cleanup/manifest.json` before use. They
  are read only.
- TIC ids are read from every git-tracked text file in the forms TIC-123, TIC 123, TIC123,
  "tic_id": 123 and "tic": 123.
  - **Examined (run records):** a file under docs/validation/ or calibration/ whose path holds
    record, draw, candidate, ledger, units, set, selection or frame. This is v0.5.10's rule.
  - **Mentioned anywhere:** any tracked file, the upper bound.
- Excluded, as in v0.5.10, are the census's own records (docs/validation/v0.5.10/) and this
  folder; they list targets without testing them.
- Dallas et al. 2026 (arXiv:2610.32949) publish no per-target list (read on 2026-11-26). Their
  KOI reference sample is a subset of the KOI hosts, so the Kepler-field arms below cover it.
  Their no-KOI control sample (177,850 stars) cannot be enumerated from the paper: NOT
  DETERMINED.

Output: exposure-check.json next to this file. Labels: exploratory, method_status
not_validated; the counts come from v0.5.10's tables, and so carry that phase's limits label.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARCHIVE = Path("K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24-v0510/v0510/census")
EXPECTED = {
    "census-d1-targets.json": "f7d89ce7e1affe8d3b4e0899a1b88a80398b76acb66ccb6572ec915040739a0f",
    "census-kepler-targets.json": (
        "227cc26d3ec32692c406a2d61e26a81d161941596c4aa1a573934b2437955350"
    ),
}
FORMS = [
    re.compile(r"TIC[-_ ]?(\d{4,10})\b"),
    re.compile(r'"tic_id"\s*:\s*"?(\d{4,10})'),
    re.compile(r'"tic"\s*:\s*"?(\d{4,10})'),
]
RECORD_HINTS = ("record", "draw", "candidate", "ledger", "units", "set", "selection", "frame")
EXCLUDED = ("docs/validation/v0.5.10/", "docs/plans/v0.5.13-charter-prep/")
SPACE = ("Kepler", "K2", "CoRoT", "Spitzer", "Hubble", "James Webb", "CHEOPS", "Gaia")
AMBIGUOUS = {"Multiple Observatories", "Multiple Facilities"}


def load(name: str):
    data = (ARCHIVE / name).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED[name]:
        raise SystemExit(f"{name}: SHA-256 {digest} differs from the manifest")
    return json.loads(data.decode("utf-8")), digest


def tic_sets() -> tuple[set[int], set[int], int]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)
    files = [p for p in out.stdout.decode("utf-8").split("\0") if p]
    anywhere: set[int] = set()
    records: set[int] = set()
    for rel in files:
        if rel.startswith(EXCLUDED):
            continue
        try:
            data = (ROOT / rel).read_bytes()
        except OSError:
            continue
        if b"\0" in data[:4096]:
            continue
        text = data.decode("utf-8", errors="replace")
        found = {int(m.group(1)) for f in FORMS for m in f.finditer(text)}
        anywhere |= found
        name = rel.lower()
        if name.startswith(("docs/validation/", "calibration/")) and any(
            h in name for h in RECORD_HINTS
        ):
            records |= found
    return anywhere, records, len(files)


def main() -> int:
    d1, d1_sha = load("census-d1-targets.json")
    kep, kep_sha = load("census-kepler-targets.json")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, check=True, text=True
    ).stdout.strip()
    anywhere, records, n_files = tic_sets()

    def usable(rows, extra=None):
        return {
            r["tic"]
            for r in rows
            if r.get("spoc_2min") and not r.get("exposed") and (extra is None or extra(r))
        }

    def ground(r, strict=False):
        f = r.get("facility") or ""
        if any(s in f for s in SPACE):
            return False
        return not (strict and f in AMBIGUOUS)

    def count(tics: set[int]) -> dict:
        return {
            "distinct_tics": len(tics),
            "examined_in_run_records": sorted(tics & records),
            "mentioned_anywhere": sorted(tics & anywhere),
        }

    kelt = [r for r in d1 if r["arm"] == "kelt_fp"]
    planets = [r for r in d1 if r["arm"] == "planets_not_tess"]
    arms = {
        "kelt_fp_all": count({r["tic"] for r in kelt}),
        "kelt_fp_usable": count(usable(kelt)),
        "planets_ground_usable": count(usable(planets, ground)),
        "planets_ground_usable_strict": count(usable(planets, lambda r: ground(r, True))),
    }
    for arm in ("certified_fp", "kepler_planets"):
        rows = [r for r in kep if r["arm"] == arm]
        arms[f"kepler_{arm}_all"] = count({r["tic"] for r in rows if r.get("tic")})
        arms[f"kepler_{arm}_spoc_2min"] = count(
            {r["tic"] for r in rows if r.get("tic") and r.get("spoc_2min")}
        )
    result = {
        "schema": "refute-v0513-exposure-check-1",
        "mode": "exploratory",
        "method_status": "not_validated",
        "limits_label_of_the_counts": (
            "v0.5.10: closed with declared limits (gate REFUTED); does not meet criteria 1, 2, "
            "3, 4, 5, 7, 8, 9, 10"
        ),
        "head": head,
        "tracked_files_scanned": n_files,
        "excluded_prefixes": list(EXCLUDED),
        "tic_ids_in_run_records": len(records),
        "tic_ids_mentioned_anywhere": len(anywhere),
        "inputs": {
            "census-d1-targets.json": d1_sha,
            "census-kepler-targets.json": kep_sha,
            "manifest": "docs/validation/v0.5.10/cleanup/manifest.json",
        },
        "dallas_2026": {
            "source": "https://arxiv.org/abs/2610.32949 (read 2026-11-26)",
            "koi_reference_sample": "covered by the kepler_* arms (KOI hosts with a TIC)",
            "no_koi_control_sample": "NOT DETERMINED: no per-target list is published",
        },
        "arms": arms,
    }
    (HERE / "exposure-check.json").write_text(json.dumps(result, indent=1) + "\n", "utf-8")
    print(
        json.dumps(
            {
                k: {
                    "n": v["distinct_tics"],
                    "examined": len(v["examined_in_run_records"]),
                    "mentioned": len(v["mentioned_anywhere"]),
                }
                for k, v in arms.items()
            },
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
