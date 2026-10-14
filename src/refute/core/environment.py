"""Environment snapshot written into every dossier."""

from __future__ import annotations

import os
import platform
import sys
from importlib.metadata import PackageNotFoundError, distributions, version
from pathlib import Path
from typing import Any

import refute

KEY_PACKAGES = (
    "numpy",
    "astropy",
    "lightkurve",
    "astroquery",
    "matplotlib",
    "pydantic",
    "pyyaml",
    "typer",
)


def package_versions(names: tuple[str, ...] = KEY_PACKAGES) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for name in names:
        try:
            out[name] = version(name)
        except PackageNotFoundError:
            out[name] = None
    return out


def requirements_text() -> str:
    """Installed distributions as ``name==version`` lines (like ``pip freeze``), sorted."""
    pins = set()
    for dist in distributions():
        name = dist.metadata.get("Name")
        if name:
            pins.add(f"{name.lower().replace('_', '-')}=={dist.version}")
    return "".join(f"{line}\n" for line in sorted(pins))


THREAD_VARIABLES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def numeric_runtime() -> dict[str, Any]:
    """The numerical runtime of the current process, recorded per dossier by the process
    that analyzes the target (v0.2.1): the thread pools of the numerical libraries that
    are loaded (from ``threadpoolctl``, imported only if it is installed), NumPy's BLAS,
    the thread variables at this moment, and whether this is a spawned worker. These are
    the libraries' thread settings, not the threading of every call. Operational
    metadata: it never enters a verdict."""
    import multiprocessing

    import numpy

    blas = None
    try:
        config = numpy.show_config(mode="dicts")
        blas = config["Build Dependencies"]["blas"]["name"]
    except Exception:  # noqa: BLE001 - the record says what could not be read
        blas = None
    try:
        from threadpoolctl import threadpool_info
    except ImportError:
        pools = None
    else:
        keys = ("user_api", "internal_api", "prefix", "version", "num_threads")
        pools = [{k: info.get(k) for k in keys} for info in threadpool_info()]
    return {
        "process": "worker" if multiprocessing.parent_process() is not None else "main",
        "thread_env": {name: os.environ.get(name) for name in THREAD_VARIABLES},
        "numpy_version": numpy.__version__,
        "blas": blas,
        "threadpoolctl_available": pools is not None,
        "threadpools": pools,
    }


def snapshot(project_root: Path | None = None) -> dict[str, Any]:
    """Environment description plus the files to copy into each dossier."""
    uv_lock = None
    if project_root is not None and (project_root / "uv.lock").is_file():
        uv_lock = (project_root / "uv.lock").read_text(encoding="utf-8")
    return {
        "info": {
            "refute_version": refute.__version__,
            "python_version": sys.version.split()[0],
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "packages": package_versions(),
        },
        "requirements_txt": requirements_text(),
        "uv_lock": uv_lock,
    }
