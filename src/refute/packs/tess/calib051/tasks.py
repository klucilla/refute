"""The paired tasks of the v0.5.1 calibration: C1' (one synthetic curve), C2' (one curve of one new
star: the original, a transformed curve or an injection) and C3' (one real control, with and
without the catalog test). Each mirrors its v0.5 counterpart (``calib05.c1.run_task``,
``calib05.c2.run_task``, ``calib05.c3run.run_task``) with the v0.4 compatibility battery paired
with the version-3 battery (``calib051.plans.pair``) instead of the v0.5 one; the generation, the
transformations, the injections, the identity rules and the record fields are v0.5's. The chain's
second battery keeps the key ``v05`` (``discover.paired.paired_chain``) and carries the WP4
``v051`` object. ``cpu_seconds`` covers the whole task, also when it fails."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from refute.packs.tess.calib05.c3run import MISSING
from refute.packs.tess.calib051.values import C1, C2


def development_seed(family: str, i: int) -> int:
    """C1' development seeds: ``int(SHA-256("refute-v051-c1-dev:<family>:<i>")[:16], 16)``."""
    text = f"{C1.development_prefix}:{family}:{i}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def confirmation_seed(randomness_hex: str, family: str, i: int) -> int:
    """C1' confirmation seeds from the round's randomness:
    ``int(SHA-256(<randomness hex> + "refute-v051-c1:<family>:<i>")[:16], 16)``."""
    text = f"{randomness_hex}{C1.seed_prefix}:{family}:{i}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


# --- C1' ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class C1Task:
    family: str
    index: int
    seed: int
    test_plan_v04: dict


def c1_task_id(task: C1Task) -> str:
    return f"{task.family}/{task.index}"


def run_c1(task: C1Task) -> dict[str, Any]:
    """One C1' curve (``calib05.c1.run_task`` with the version-3 pair)."""
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.calib051.plans import pair
    from refute.packs.tess.discover.paired import paired_chain

    started = time.process_time()
    record: dict[str, Any] = {"family": task.family, "index": task.index, "seed": str(task.seed)}
    try:
        data, truth = c1.generate(task.family, task.seed)
    except c1.GenerationFailedError as exc:
        record.update({"status": "GENERATION_FAILURE", "reason": str(exc)})
        record["cpu_seconds"] = time.process_time() - started
        return record
    record["truth"] = truth
    try:
        p04, p51 = pair(task.test_plan_v04)
        chain = paired_chain(data, p04, p51, stage=2)
        record["chain"] = chain
        record["status"] = "OK"
        if task.family in c1.PLANET_FAMILIES:
            record["identity"] = c1.identity(truth, chain["v05"]["candidate"])
    except Exception as exc:  # noqa: BLE001 - recorded: the task stays in its denominators
        record.update({"status": "ERROR", "reason": f"{type(exc).__name__}: {exc}"})
    record["cpu_seconds"] = time.process_time() - started
    return record


# --- C2' ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class C2Task:
    """One curve of one new star (picklable); as ``calib05.c2.C2Task``."""

    kind: str  # original, transform (slot = position 0, 1, 2) or injection (slot = index)
    target: dict[str, Any]
    test_plan_v04: dict[str, Any]
    cache_dir: str
    slot: int = 0
    seed: int = 0
    k: int = C2.injections_per_curve
    catalog_paths: tuple[str, ...] = field(default_factory=tuple)
    scan_path: str | None = None


def c2_task_id(task: C2Task) -> str:
    return f"{task.target['key']}/{task.kind}/{task.slot}"


def c2_tasks_for(
    target: dict[str, Any],
    test_plan_v04: dict[str, Any],
    cache_dir: Path,
    randomness_inj: str,
    catalog_paths: tuple[str, ...],
    scan_path: str | None,
    k: int = C2.injections_per_curve,
    transformed: int = C2.transformed_per_star,
) -> list[C2Task]:
    """The original curve, the transformed curves and the ``k`` injections of one star, with the
    v0.4 seed streams (``calib05.c2.tasks_for``) of the round's randomness."""
    from refute.packs.tess.discover import injection as inj
    from refute.packs.tess.discover.transforms import stream_seed

    tic = int(target["tic_id"])
    common = {
        "target": target,
        "test_plan_v04": test_plan_v04,
        "cache_dir": str(cache_dir),
        "catalog_paths": tuple(catalog_paths),
        "scan_path": scan_path,
    }
    tr_seed = stream_seed(randomness_inj, "v0.4", "transform", tic)
    inj_seed = inj.stage1_chain_seed(randomness_inj, tic)
    out = [C2Task("original", **common)]
    out += [C2Task("transform", slot=p, seed=tr_seed, **common) for p in range(transformed)]
    out += [C2Task("injection", slot=i, seed=inj_seed, k=k, **common) for i in range(k)]
    return out


def run_c2(task: C2Task) -> dict[str, Any]:
    """One C2' curve at stage 1 (``calib05.c2.run_task`` with the version-3 pair)."""
    from refute.packs.tess.adapter import TessAdapter
    from refute.packs.tess.calib051.plans import pair
    from refute.packs.tess.discover import injection as inj
    from refute.packs.tess.discover.measure import load_catalogs, stage_plan, transforms_of
    from refute.packs.tess.discover.paired import paired_chain

    started = time.process_time()
    record: dict[str, Any] = {
        "kind": task.kind,
        "target_key": task.target["key"],
        "slot": task.slot,
    }
    try:
        test_plan = stage_plan(task.test_plan_v04, 1)
        p04, p51 = pair(test_plan)
        cache = Path(task.cache_dir)
        catalogs, scan = load_catalogs(task.catalog_paths, task.scan_path, cache)
        adapter = TessAdapter()
        if task.kind == "original":
            data = adapter.load(task.target, test_plan, cache)
        elif task.kind == "transform":
            transforms, rotations = transforms_of(task.target, cache, task.seed, p04)
            transform = transforms[task.slot]
            record["transform"] = transform.to_dict()
            if transform.kind == "rotate" and (task.slot - 1) in rotations.inconclusive:
                record.update({"status": "INCONCLUSIVE", "reason": "no distinct offsets drawn"})
                record["cpu_seconds"] = time.process_time() - started
                return record
            data = adapter.load(task.target, test_plan, cache, transform=transform)
        elif task.kind == "injection":
            base = adapter.load(task.target, test_plan, cache)
            star = base.star
            drawn = inj.draw_injections(
                task.seed,
                task.k,
                inj.first_time(base),
                star.radius_rsun if star else None,
                star.logg_cgs if star else None,
            )[task.slot]
            record["injection"] = drawn.to_dict()
            data = inj.inject(base, drawn)
        else:
            raise ValueError(f"unknown kind {task.kind!r}")
        chain = paired_chain(data, p04, p51, 1, catalogs, scan)
        record.update({"status": "OK", "chain": chain})
        if task.kind == "injection":
            v04 = chain["v04"]
            record["recovery"] = inj.recovery(drawn, v04["candidate"], v04["gate_passed"])
    except Exception as exc:  # noqa: BLE001 - recorded; the curve stays in its denominators
        record.update({"status": "ERROR", "reason": f"{type(exc).__name__}: {exc}"})
    record["cpu_seconds"] = time.process_time() - started
    return record


# --- C3' ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class C3Task:
    """One control (picklable); as ``calib05.c3run.C3Task``."""

    target: dict[str, Any]
    test_plan_v04: dict[str, Any]
    cache_dir: str
    products: dict[str, Any]
    catalog_paths: tuple[str, ...] = field(default_factory=tuple)
    scan_path: str | None = None


def c3_task_id(task: C3Task) -> str:
    return f"{task.target['key']}/c3"


def run_c3(task: C3Task) -> dict[str, Any]:
    """One C3' control at stage 2, with and without the catalog test
    (``calib05.c3run.run_task`` with the version-3 pair)."""
    from refute.packs.tess.adapter import TessAdapter
    from refute.packs.tess.calib05.c3run import identity
    from refute.packs.tess.calib051.plans import pair
    from refute.packs.tess.discover.measure import load_catalogs, stage_plan
    from refute.packs.tess.discover.paired import paired_chain

    started = time.process_time()
    record: dict[str, Any] = {
        "target_key": task.target["key"],
        "kind": task.target["kind"],
        "place": task.target.get("c3_place"),
        "products": task.products,
    }
    if task.products.get("state") == "missing":
        record.update({"status": MISSING, "reason": task.products.get("reason")})
        record["cpu_seconds"] = time.process_time() - started
        return record
    try:
        if task.products.get("state") != "present":
            raise ValueError(f"the products could not be fetched: {task.products.get('reason')}")
        test_plan = stage_plan(task.test_plan_v04, 2)
        p04, p51 = pair(test_plan)
        cache = Path(task.cache_dir)
        data = TessAdapter().load(task.target, test_plan, cache)
        catalogs, scan = load_catalogs(task.catalog_paths, task.scan_path, cache)
        with_catalog = paired_chain(data, p04, p51, 2, catalogs, scan)
        without = paired_chain(data, p04, p51, 2, None, None)
        if with_catalog["search_candidate"] != without["search_candidate"]:
            raise ValueError("the two variants did not share the search candidate")
        for battery in ("v04", "v05"):
            if with_catalog[battery]["candidate"] != without[battery]["candidate"]:
                raise ValueError("the two variants did not attack the same final candidate")
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
