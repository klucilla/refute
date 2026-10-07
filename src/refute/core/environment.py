"""Environment snapshot written into every dossier."""

from __future__ import annotations

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
