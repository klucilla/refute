"""Small file and JSON helpers.

All text is written as UTF-8 with LF line endings on every platform, so that
files written on Windows hash identically to files written on Linux.
"""

from __future__ import annotations

import dataclasses
import enum
import json
import math
from datetime import date, datetime
from pathlib import Path, PurePath
from typing import Any

import yaml


def to_jsonable(value: Any) -> Any:
    """Convert common scientific and Python types into plain JSON values.

    Non-finite floats become ``None`` so JSON output stays standard.
    """
    if value is None or isinstance(value, bool | str):
        return value
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, PurePath):
        return value.as_posix()
    if isinstance(value, datetime | date):
        return value.isoformat()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        if hasattr(value, "to_dict"):
            return to_jsonable(value.to_dict())
        return {f.name: to_jsonable(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple | set | frozenset):
        items = sorted(value) if isinstance(value, set | frozenset) else value
        return [to_jsonable(v) for v in items]
    # numpy scalars and arrays (imported lazily so the core does not need numpy)
    type_module = type(value).__module__
    if type_module == "numpy":
        if hasattr(value, "tolist"):
            return to_jsonable(value.tolist())
        return to_jsonable(value.item())
    if hasattr(value, "model_dump"):
        return to_jsonable(value.model_dump(mode="json"))
    raise TypeError(f"cannot convert {type(value).__name__} to JSON")


def dumps_json(value: Any) -> str:
    """Pretty, deterministic JSON (sorted keys, 2-space indent, trailing newline)."""
    return (
        json.dumps(
            to_jsonable(value), indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
        )
        + "\n"
    )


def write_text(path: Path | str, text: str) -> Path:
    """Write UTF-8 text with LF line endings, creating parent directories."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))
    return target


def write_json(path: Path | str, value: Any) -> Path:
    return write_text(path, dumps_json(value))


def read_json(path: Path | str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dumps_yaml(value: Any) -> str:
    return yaml.safe_dump(
        to_jsonable(value), sort_keys=False, allow_unicode=True, default_flow_style=False
    )


def read_yaml(path: Path | str) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def append_text(path: Path | str, text: str) -> None:
    """Append UTF-8 text with LF line endings."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("ab") as handle:
        handle.write(text.replace("\r\n", "\n").encode("utf-8"))
