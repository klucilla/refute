"""C3 of the v0.5 calibration after the selection (calibration/v0.5/PROTOCOL.md, sections 5 and 6):
the claim, the paired tasks of the controls, the replacement by the reserves, and the targets.

- ``write_claim``: one v0.5 ``discover`` claim for the chosen controls and their reserves of
  ``selection/targets.yaml`` (the v0.4 claim's thresholds; discovery version 2 with the roles of
  the S2 decisions; ``max_sector`` the frozen S_max; the SHA-256 of the protocol, the inputs and the
  selection), with its eclipsing-binary attachments (``discover.claim.eb_attachments``). It is
  the claim ``refute discover`` runs (the dossiers, the reproduction).
- ``run_task``: one control at stage 2 (the full battery), both batteries on the same candidate,
  twice: with the claim's catalogs (as in the dossiers) and without them (the targets: the eight
  false positives are drawn from TESS-EB, so a catalog test that looks them up is not evidence of
  the battery; its own-TIC match is a warning, H9a, which alone keeps a control from SURVIVED);
  the signal identity of the shared candidate.
- ``assign``: per pool, the chosen controls in order; one that fails the signal identity, or
  whose products are missing, is replaced by the next reserve, at most ``C3.reserves`` times; the
  decision reads only the identity and the product state, never a verdict.
- ``targets``: T3a and T3b on the battery without the catalog test; PASS only with all 8 valid,
  identity-qualified outcomes of the group, else NOT DECIDABLE; the four verdict counts always.
"""

from __future__ import annotations

import copy
import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from refute.packs.tess.calib05.values import C3, PROTOCOL_ID, STEP_DIR

CLAIM_ID = "tess-calibration-v0.5-c3"
CLAIM_NAME = "claim.yaml"
EB_CATALOG = "eb_catalog.csv"
EB_SCAN = "eb_catalog_scan.json"
REPOSITORY_INPUTS = {
    "protocol": "PROTOCOL.md",
    "inputs_json": "inputs.json",
    "selection": "selection/selection.json",
    "ledger": "selection/ledger.json",
}
RECORDED_INPUTS = {
    "target_lists_page": "target_lists.html",
    "toi": "toi.csv",
    "pscomppars": "pscomppars.csv",
    "tess_eb": "tess_eb.tsv",
    "gaia_dr3_eb": "gaia_dr3_eb.csv",
}
V04_CLAIM = "calibration/v0.4/claim.yaml"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def v04_plan_for(root: Path, inputs: dict[str, Any], step_dir: Path) -> dict[str, Any]:
    """The v0.4 battery for the C3 controls: the v0.4 claim's plan with C3's ``max_sector`` and
    ``inputs`` (every other parameter unchanged)."""
    import yaml

    plan = copy.deepcopy(
        yaml.safe_load((Path(root) / V04_CLAIM).read_text(encoding="utf-8"))["test_plan"]
    )
    recorded = {i["name"]: i["sha256"] for i in inputs["files"]}
    inputs_hashes = {k: _sha((step_dir / p).read_bytes()) for k, p in REPOSITORY_INPUTS.items()}
    for key, name in RECORDED_INPUTS.items():
        inputs_hashes[key] = recorded[name]
    plan["discovery"]["inputs"] = inputs_hashes
    plan["discovery"]["max_sector"] = int(inputs["s_max"])
    return plan


def write_claim(root: Path, inputs_dir: Path, created: str) -> dict[str, Any]:
    """Write ``eb_catalog.csv``, ``eb_catalog_scan.json`` and ``claim.yaml`` in
    ``calibration/v0.5``, once (an existing file is never written over)."""
    import yaml

    from refute.packs.tess.calib05.plans import v05_plan
    from refute.packs.tess.discover.claim import eb_attachments

    root = Path(root)
    step = root / STEP_DIR
    paths = [step / name for name in (CLAIM_NAME, EB_CATALOG, EB_SCAN)]
    existing = [p.name for p in paths if p.exists()]
    if existing:
        raise FileExistsError("already written, never written over: " + ", ".join(existing))
    inputs = json.loads((step / "inputs.json").read_text(encoding="utf-8"))
    targets_doc = yaml.safe_load((step / "selection" / "targets.yaml").read_text("utf-8"))
    catalog, scan = eb_attachments(targets_doc["targets"], inputs_dir, inputs)
    test_plan = v05_plan(v04_plan_for(root, inputs, step))
    retrieved = {i["name"]: i["retrieved_utc"] for i in inputs["files"]}
    document = {
        "schema_version": 1,
        "id": CLAIM_ID,
        "kind": "discover",
        "pack": "tess",
        "title": "Refute v0.5 calibration, C3: newly drawn real controls, the v0.5 battery",
        "hypothesis": (
            "Each control of calibration/v0.5/selection/targets.yaml (8 confirmed planets and 8 "
            "eclipsing-binary false positives, newly drawn; their reserves) is attacked by the "
            "declared decisive v0.5 battery; each case ends in SURVIVED, WEAKENED, REFUTED or "
            "INCONCLUSIVE. A feasibility sample, not a class-wise validation; method not validated."
        ),
        "created": created,
        "authors": ["Klauber Lucilla"],
        "definitions": {
            "protocol": f"{PROTOCOL_ID}, calibration/v0.5/PROTOCOL.md (sections 5 and 6).",
            "signal_identity": (
                "The planet's found period within a relative tolerance of "
                f"{C3.identity_period_tolerance:g} of the published period; the false positive's "
                f"at one of the factors {list(C3.fp_identity_factors)}. Decided before any "
                "disposition is scored; a failure is replaced by the next reserve (section 6)."
            ),
            "verdict": (
                "Aggregated from the decisive tests only, with the severity each test emits "
                "(docs/verdicts.md). Never 'confirmed', 'discovery', 'TRUE' or a planet letter."
            ),
            "method_status": "not_validated",
            "max_sector": f"S_max = {inputs['s_max']} (test_plan.discovery.max_sector).",
        },
        "data_sources": [
            {
                "name": "NASA Exoplanet Archive, Planetary Systems Composite Parameters",
                "url": "https://exoplanetarchive.ipac.caltech.edu/TAP/sync",
                "retrieved": retrieved["pscomppars.csv"],
                "notes": "The planet pool; inputs.json.",
            },
            {
                "name": "ExoFOP-TESS TOI table",
                "url": "https://exofop.ipac.caltech.edu/tess/download_toi.php",
                "retrieved": retrieved["toi.csv"],
                "notes": "The false-positive pool (TFOPWG FP); inputs.json.",
            },
            {
                "name": "TESS-EB, Prsa et al. 2022 (VizieR J/ApJS/258/16/tess-ebs)",
                "url": "https://vizier.cds.unistra.fr/viz-bin/VizieR?-source=J/ApJS/258/16",
                "retrieved": retrieved["tess_eb.tsv"],
                "notes": "The static edition obtained 2026-10-18; not redistributed (#33).",
            },
            {
                "name": "Gaia DR3 eclipsing-binary candidates (the v0.2.0 release asset)",
                "url": "https://github.com/klucilla/refute/releases/tag/v0.2.0",
                "retrieved": retrieved["gaia_dr3_eb.csv"],
                "notes": "Rows near the targets, in the catalog attachment.",
            },
            {
                "name": "MAST: TIC fields and SPOC 120-s listings",
                "url": "https://mast.stsci.edu",
                "retrieved": "the selection walk (selection/selection.json)",
                "notes": "Queried live during the walk; each answer is in the selection record.",
            },
        ],
        "attachments": [
            {"path": "selection/targets.yaml", "role": "targets"},
            {"path": "PROTOCOL.md", "role": "protocol"},
            {"path": "inputs.json", "role": "snapshot-index"},
            {"path": "selection/selection.json", "role": "selection-log"},
            {"path": EB_CATALOG, "role": "eb-catalog"},
            {"path": EB_SCAN, "role": "eb-catalog-scan"},
        ],
        "test_plan": test_plan,
    }
    header = (
        "# Refute v0.5 calibration, C3 claim (calibration/v0.5/PROTOCOL.md, section 5).\n"
        "# Written by calibration/v0.5/run_calibration.py (refute.packs.tess.calib05.c3run) after\n"
        "# the selection; locked with `refute lock` from a clean tree at S4.\n"
    )
    contents = {
        EB_CATALOG: catalog,
        EB_SCAN: json.dumps(scan, indent=2, sort_keys=True) + "\n",
        CLAIM_NAME: header + yaml.safe_dump(document, sort_keys=False, allow_unicode=True),
    }
    for name, text in contents.items():
        with open(step / name, "x", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    return {"claim": document, "scan": scan}


# --- the paired tasks ---------------------------------------------------------------------


def identity(kind: str, published: float | None, found: float | None) -> dict[str, Any]:
    """The signal identity of a control (protocol section 5)."""
    from refute.packs.tess.pipeline import matching_factor

    factors = [1.0] if kind == "planet" else list(C3.fp_identity_factors)
    factor = matching_factor(published, found, factors, C3.identity_period_tolerance)
    return {
        "published_period_days": published,
        "found_period_days": found,
        "factors": factors,
        "factor": factor,
        "matched": factor is not None,
    }


@dataclass(frozen=True)
class C3Task:
    target: dict[str, Any]
    test_plan_v04: dict[str, Any]
    cache_dir: str
    catalog_paths: tuple[str, ...] = field(default_factory=tuple)
    scan_path: str | None = None


def task_id(task: C3Task) -> str:
    return f"{task.target['key']}/c3"


def run_task(task: C3Task) -> dict[str, Any]:
    """One control at stage 2, with and without the catalog test; missing products are their
    own status (a replacement reason), any other failure an error record."""
    from refute.packs.tess.adapter import DataError, TessAdapter
    from refute.packs.tess.calib05.plans import pair
    from refute.packs.tess.discover.measure import load_catalogs, stage_plan
    from refute.packs.tess.discover.paired import paired_chain

    started = time.process_time()
    record: dict[str, Any] = {
        "target_key": task.target["key"],
        "kind": task.target["kind"],
        "place": task.target.get("c3_place"),
    }
    try:
        test_plan = stage_plan(task.test_plan_v04, 2)
        p04, p05 = pair(test_plan)
        cache = Path(task.cache_dir)
        try:
            data = TessAdapter().load(task.target, test_plan, cache)
        except DataError as exc:
            record.update({"status": "MISSING_PRODUCTS", "reason": str(exc)})
            record["cpu_seconds"] = time.process_time() - started
            return record
        catalogs, scan = load_catalogs(task.catalog_paths, task.scan_path, cache)
        with_catalog = paired_chain(data, p04, p05, 2, catalogs, scan)
        without = paired_chain(data, p04, p05, 2, None, None)
        found = (without["v05"]["candidate"] or {}).get("period_days")
        published = (task.target.get("published") or {}).get("period_days")
        record.update(
            {
                "status": "OK",
                "with_catalog": with_catalog,
                "without_catalog": without,
                "identity": identity(task.target["kind"], published, found),
            }
        )
    except Exception as exc:  # noqa: BLE001 - recorded: the control stays in its group
        record.update({"status": "ERROR", "reason": f"{type(exc).__name__}: {exc}"})
    record["cpu_seconds"] = time.process_time() - started
    return record


# --- replacement and targets ------------------------------------------------------------------


def _replaceable(record: dict[str, Any] | None) -> str | None:
    """Why a control is replaced (identity or products), or None; never a verdict."""
    if record is None:
        return "no record"
    if record["status"] == "MISSING_PRODUCTS":
        return "products missing"
    if record["status"] == "OK" and not record["identity"]["matched"]:
        return "signal identity not matched"
    return None


def assign(targets: list[dict[str, Any]], records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Per pool: the chosen controls in walk order, each replaced, when ``_replaceable``, by the
    next reserve in order, at most ``C3.reserves`` replacements per pool; a pool that runs out is
    short. Returns the final controls and the ordered replacement ledger."""
    out = {}
    for kind in ("planet", "false_positive"):
        chosen = [t["key"] for t in targets if t["kind"] == kind and t["c3_place"] == "chosen"]
        reserves = [
            t["key"]
            for t in sorted(
                (t for t in targets if t["kind"] == kind and t["c3_place"] != "chosen"),
                key=lambda t: int(t["c3_place"].split()[1]),
            )
        ]
        final, ledger, used = [], [], 0
        queue = list(reserves)
        for key in chosen:
            current = key
            why = _replaceable(records.get(current))
            while why is not None and used < C3.reserves and queue:
                nxt = queue.pop(0)
                used += 1
                ledger.append({"replaced": current, "reason": why, "by": nxt})
                current = nxt
                why = _replaceable(records.get(current))
            if why is None:
                final.append(current)
            else:
                ledger.append({"replaced": current, "reason": why, "by": None})
        out[kind] = {
            "final": final,
            "ledger": ledger,
            "replacements": used,
            "short": len(chosen) - len(final),
        }
    return out


def targets(assigned: dict[str, Any], records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """T3a (planets REFUTED at most ``C3.max_planets_refuted``) and T3b (false positives
    SURVIVED at most ``C3.max_fp_survived``), on the v0.5 battery without the catalog test; each
    PASS only with all 8 valid, identity-qualified outcomes, else NOT DECIDABLE. The four verdict
    counts per battery, with and without the catalog test, are always reported."""
    from refute.packs.tess.discover.paired import transitions, verdict_counts

    out = {}
    for kind, name, needed, limit, verdict in (
        ("planet", "T3a", C3.planets, C3.max_planets_refuted, "REFUTED"),
        ("false_positive", "T3b", C3.false_positives, C3.max_fp_survived, "SURVIVED"),
    ):
        keys = assigned[kind]["final"]
        valid = [records[k] for k in keys if records[k]["status"] == "OK"]
        counts = {}
        for variant in ("without_catalog", "with_catalog"):
            counts[variant] = {
                b: verdict_counts([r[variant][b]["verdict"] for r in valid]) for b in ("v04", "v05")
            }
            counts[variant]["transitions"] = transitions(
                [(r[variant]["v04"]["verdict"], r[variant]["v05"]["verdict"]) for r in valid]
            )
        observed = counts["without_catalog"]["v05"][verdict]
        decidable = len(valid) == needed
        out[name] = {
            "group": kind,
            "valid_outcomes": len(valid),
            "needed": needed,
            "errors": sum(records[k]["status"] == "ERROR" for k in keys),
            "short": assigned[kind]["short"],
            "rule": f"v0.5 {verdict} (without the catalog test) at most {limit} of {needed}",
            "observed": observed,
            "counts": counts,
            "result": "NOT DECIDABLE"
            if not decidable
            else ("PASS" if observed <= limit else "FAIL"),
        }
    return out
