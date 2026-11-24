"""Runner of part (f): one sandboxed worker per TOI and engine, logged before and after.

The charter's amendment (section 9) allows one run per TOI and per engine, with no repetition.
This runner refuses to start a (TOI, engine) pair that already has a ``before`` entry in the
phase log, records a ``before`` entry, runs the worker in the AppContainer (sandbox.py), and
records an ``after`` entry with the status, the CPU seconds of the whole job and the result file.

Subcommands:
- ``synthetic NAME WORKER JSON_SPEC``: a run on a synthetic injected curve (no TOI), for the
  launcher and cost checks the amendment allows before the TOI runs.
- ``toi ENGINE [TIC-...]``: the TOI runs of one engine, in the set's order.

Phase CPU is read from the log (every ``after`` entry's ``cpu_seconds``) and a run is refused
when the phase total plus the run's allowance would pass the cap of 6 CPU-h.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import phase_log  # noqa: E402
import sandbox  # noqa: E402

PROJECT = sandbox.PROJECT
CACHE = sandbox.CACHE_ROOT
LOG = HERE.parent / "log.jsonl"
SETTINGS = HERE / "settings.json"
WORKERS = CACHE / "workers"
RUNS = CACHE / "runs"
RESULTS = HERE / "results"
CAP_CPU_SECONDS = 6 * 3600.0
PY = CACHE / "engines" / "venv" / "Scripts" / "python.exe"


def phase_cpu_seconds() -> float:
    total = 0.0
    for line in LOG.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("kind") == "after" and isinstance(r.get("cpu_seconds"), (int, float)):
            total += float(r["cpu_seconds"])
    return total


def started_runs() -> set[str]:
    out = set()
    for line in LOG.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("kind") == "before":
            out.add(r["run"])
    return out


def stage_worker(worker_src: Path) -> tuple[Path, str]:
    """Copy the worker (and the shared worker_tls module) into the workers' folder."""
    WORKERS.mkdir(parents=True, exist_ok=True)
    common = HERE / "worker_tls.py"
    if worker_src.resolve() != common.resolve():
        shutil.copyfile(common, WORKERS / common.name)
    dst = WORKERS / worker_src.name
    shutil.copyfile(worker_src, dst)
    return dst, hashlib.sha256(dst.read_bytes()).hexdigest()


def run_one(
    run_name: str,
    worker: Path,
    job: dict,
    threads: int,
    allowance_s: float,
    timeout_s: float,
    note: str,
) -> dict:
    if run_name in started_runs():
        raise SystemExit(f"refused: {run_name} already has a 'before' entry (no repetition)")
    used = phase_cpu_seconds()
    if used + allowance_s > CAP_CPU_SECONDS:
        raise SystemExit(
            f"refused: phase CPU {used:.0f} s + allowance {allowance_s:.0f} s passes the cap"
        )
    wpath, wsha = stage_worker(worker)
    run_dir = RUNS / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    sandbox.grant(run_dir, write=True)
    job = dict(job)
    job["out"] = str(run_dir / "result.json")
    job["threads"] = threads
    job_path = run_dir / "job.json"
    job_path.write_text(json.dumps(job, indent=1), encoding="utf-8")
    phase_log.log(
        "before",
        run_name,
        text=note,
        worker=worker.name,
        worker_sha256=wsha,
        threads=threads,
        allowance_cpu_seconds=allowance_s,
        phase_cpu_seconds_before=round(used, 1),
    )
    rec = sandbox.run(
        [str(PY), "-I", str(wpath), str(job_path)],
        cwd=run_dir,
        run_dir=run_dir,
        workers=threads,
        timeout_s=timeout_s,
    )
    result = None
    rp = run_dir / "result.json"
    if rp.exists():
        result = json.loads(rp.read_text(encoding="utf-8"))
    status = (result or {}).get("status", "no_result")
    if rec["timed_out"]:
        status = "unavailable_timeout"
    phase_log.log(
        "after",
        run_name,
        text=f"status {status}",
        status=status,
        cpu_seconds=round(rec["cpu_seconds"], 2),
        wall_seconds=rec["wall_seconds"],
        exit_code=rec["exit_code"],
        processes=rec["processes"],
        timed_out=rec["timed_out"],
    )
    return {"run": run_name, "status": status, "launcher": rec, "result": result}


def synthetic(name: str, worker_name: str, spec_json: str, threads: int = 10) -> None:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    spec = json.loads(spec_json)
    job = {
        "synthetic": spec,
        "catalog": {
            "period_days": spec["period"],
            "epoch_btjd": spec["epoch"],  # the synthetic transits are at epoch + n P
            "duration_hours": spec["duration_hours"],
            "depth_ppm": spec["depth_ppm"],
        },
        "settings": settings,
    }
    worker = ENGINES.get(worker_name, HERE / worker_name)
    if worker_name in ("leo", "triceratops"):
        job.update(synthetic_inputs())
    out = run_one(
        f"synthetic-{name}",
        worker,
        job,
        threads=threads,
        allowance_s=1800.0,
        timeout_s=1800.0,
        note=f"synthetic run (no TOI), launcher and cost check: {spec_json}",
    )
    RESULTS.mkdir(exist_ok=True)
    keep = {k: v for k, v in out.items() if k != "launcher"}
    keep["cpu_seconds"] = out["launcher"]["cpu_seconds"]
    keep["wall_seconds"] = out["launcher"]["wall_seconds"]
    (RESULTS / f"synthetic-{name}.json").write_text(json.dumps(keep, indent=1), encoding="utf-8")
    print(json.dumps({k: keep[k] for k in ("status", "cpu_seconds", "wall_seconds")}))
    if out["result"]:
        print(json.dumps(out["result"].get("metrics"), indent=0)[:1500])
        if out["result"].get("error"):
            print(out["result"]["error"])
            print(out["result"].get("traceback", "")[-1500:])


GPL = CACHE / "workers_gpl"
ENGINES = {
    "tls": HERE / "worker_tls.py",
    "exovetter": HERE / "worker_exovetter.py",
    "leo": GPL / "worker_leo.py",
    "triceratops": GPL / "worker_triceratops.py",
}
DRAWS = (
    PROJECT / "docs/validation/v0.5.6/part-a-draw.json",
    PROJECT / "calibration/v0.5.6/part-b-draw.json",
)
SET = PROJECT / "docs/validation/v0.5.9/prototype-set.json"
DATA_CHECK = HERE / "data-check.json"
STAGED = CACHE / "staged"
LOCK = threading.Lock()
IN_FLIGHT = [0.0]


def catalog() -> dict[str, dict]:
    out = {}
    for path in DRAWS:
        d = json.loads(path.read_text(encoding="utf-8"))
        for arm in d["arms"].values():
            for c in arm["chosen"]:
                out[f"TIC-{c['tic_id']}"] = {
                    "toi": c["toi"],
                    "period_days": float(c["period_days"]),
                    "epoch_btjd": float(c["epoch_bjd"]) - 2457000.0,
                    "duration_hours": float(c["duration_hours"]),
                    "depth_ppm": float(c["depth_ppm"]),
                }
    return out


def files() -> dict[str, dict[str, list[str]]]:
    d = json.loads(DATA_CHECK.read_text(encoding="utf-8"))
    out: dict[str, dict[str, list[str]]] = {}
    for r in d["records"]:
        if r["status"] != "match":
            continue
        kind = "light_curves" if r["kind"] == "lc" else "pixel_files"
        path = str(CACHE / "data" / r["target"] / r["name"])
        out.setdefault(r["target"], {"light_curves": [], "pixel_files": []})[kind].append(path)
    return out


def toi(engine: str, only: list[str]) -> None:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    order = json.loads(SET.read_text(encoding="utf-8"))["order"]
    if only:
        order = [k for k in order if k in only]
    cat = catalog()
    fls = files()
    sandbox.grant(STAGED)
    threads = settings["threads"][engine]
    allowance = float(settings["allowances_cpu_seconds"][engine])
    parallel = 1 if threads > 1 else 10
    worker = ENGINES[engine]
    out_dir = RESULTS / engine
    out_dir.mkdir(parents=True, exist_ok=True)

    def one(key: str) -> dict:
        job = {
            "target": key,
            "tic_id": int(key.split("-")[1]),
            "catalog": cat[key],
            "light_curves": fls[key]["light_curves"],
            "pixel_files": fls[key]["pixel_files"],
            "staged_tic": str(STAGED / "tic" / f"{key}.ecsv"),
            "staged_gaia": str(STAGED / "gaia" / f"{key}.ecsv"),
            "settings": settings,
        }
        with LOCK:
            used = phase_cpu_seconds() + IN_FLIGHT[0]
            if used + allowance > CAP_CPU_SECONDS:
                print(key, "not run: the cap would be passed", flush=True)
                return {"run": key, "status": "not_run_cap"}
            IN_FLIGHT[0] += allowance
        try:
            r = run_one(
                f"{engine}:{key}",
                worker,
                job,
                threads=threads,
                allowance_s=allowance,
                timeout_s=allowance,
                note=f"part (f) named rerun (charter section 9): {engine} on {key} "
                f"(TOI {cat[key]['toi']}), once, settings.json as committed",
            )
        finally:
            with LOCK:
                IN_FLIGHT[0] -= allowance
        rec = {
            "target": key,
            "toi": cat[key]["toi"],
            "engine": engine,
            "status": r["status"],
            "cpu_seconds": round(r["launcher"]["cpu_seconds"], 2),
            "wall_seconds": r["launcher"]["wall_seconds"],
            "result": r["result"],
        }
        (out_dir / f"{key}.json").write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
        print(key, r["status"], rec["cpu_seconds"], flush=True)
        return rec

    with ThreadPoolExecutor(max_workers=parallel) as ex:
        list(ex.map(one, order))


def synthetic_inputs() -> dict:
    """Synthetic TIC rows, Gaia rows and a pixel file (no real target), for the GPL smoke runs."""
    import numpy as np
    from astropy.io import fits
    from astropy.table import Table

    d = CACHE / "synthetic"
    d.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(7)
    ra0, dec0 = 120.0, -40.0
    n = 4
    tic = Table(
        {
            "ID": np.array([900000001, 900000002, 900000003, 900000004], dtype="int64"),
            "Tmag": [10.0, 13.5, 14.2, 15.0],
            "Vmag": [10.5, 14.0, 14.8, 15.6],
            "GAIAmag": [10.3, 13.8, 14.5, 15.3],
            "gaiabp": [10.6, 14.1, 14.9, 15.7],
            "gaiarp": [9.9, 13.4, 14.1, 14.9],
            "Jmag": [9.4, 12.9, 13.6, 14.4],
            "Hmag": [9.1, 12.6, 13.3, 14.1],
            "Kmag": [9.0, 12.5, 13.2, 14.0],
            "ebv": [0.02] * n,
            "ra": [ra0, ra0 + 0.010, ra0 - 0.015, ra0 + 0.020],
            "dec": [dec0, dec0 + 0.008, dec0 - 0.010, dec0 - 0.020],
            "mass": [1.0, 0.8, 0.7, 0.6],
            "rad": [1.0, 0.8, 0.7, 0.6],
            "Teff": [5800.0, 5000.0, 4500.0, 4000.0],
            "logg": [4.44, 4.53, 4.59, 4.66],
            "plx": [5.0, 2.0, 1.5, 1.0],
            "rho": [1.41, 2.2, 2.9, 3.9],
            "e_rad": [0.05] * n,
            "e_mass": [0.05] * n,
            "e_Teff": [100.0] * n,
            "e_logg": [0.1] * n,
            "e_rho": [0.1] * n,
            "disposition": [""] * n,
            "duplicate_id": [""] * n,
        }
    )
    tic.write(d / "tic.ecsv", format="ascii.ecsv", overwrite=True)
    m = 400
    g = rng.uniform(12.0, 20.9, m)
    gaia = Table(
        {
            "phot_g_mean_mag": g,
            "phot_bp_mean_mag": g + rng.uniform(0.3, 1.2, m),
            "phot_rp_mean_mag": g - rng.uniform(0.3, 0.9, m),
            "parallax": rng.uniform(0.1, 3.0, m),
            "parallax_over_error": rng.uniform(1.0, 30.0, m),
        }
    )
    gaia.write(d / "gaia.ecsv", format="ascii.ecsv", overwrite=True)
    ny = nx = 11
    nt = 2000
    cube = np.full((nt, ny, nx), 50.0) + rng.normal(0, 1.0, (nt, ny, nx))
    cube[:, 5, 5] += 5000.0
    prim = fits.PrimaryHDU()
    prim.header["SECTOR"] = 1
    col = fits.Column(
        name="FLUX", format=f"{ny * nx}E", dim=f"({nx},{ny})", array=cube.astype("float32")
    )
    tab = fits.BinTableHDU.from_columns(fits.ColDefs([col]))
    tab.header["1CRV4P"] = 500
    tab.header["2CRV4P"] = 600
    ap = np.zeros((ny, nx), dtype="int32")
    ap[4:7, 4:7] = 3
    aph = fits.ImageHDU(ap)
    wcs = {
        "CTYPE1": "RA---TAN",
        "CTYPE2": "DEC--TAN",
        "CRVAL1": ra0,
        "CRVAL2": dec0,
        "CRPIX1": 6.0,
        "CRPIX2": 6.0,
        "CDELT1": -20.25 / 3600,
        "CDELT2": 20.25 / 3600,
    }
    for k, v in wcs.items():
        aph.header[k] = v
    fits.HDUList([prim, tab, aph]).writeto(d / "tpf.fits", overwrite=True)
    sandbox.grant(d)
    return {
        "staged_tic": str(d / "tic.ecsv"),
        "staged_gaia": str(d / "gaia.ecsv"),
        "pixel_files": [str(d / "tpf.fits")],
        "tic_id": 900000001,
    }


def main() -> int:
    if sys.argv[1] == "synthetic":
        threads = int(sys.argv[5]) if len(sys.argv) > 5 else 10
        synthetic(sys.argv[2], sys.argv[3], sys.argv[4], threads)
        return 0
    if sys.argv[1] == "toi":
        toi(sys.argv[2], sys.argv[3:])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
