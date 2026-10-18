"""A scalar read from a TensorBoard event file (WP3 W3.11b,
docs/validation/v0.3/wp3-tensorboard-acceptance.md).

The file is a sequence of TFRecord records (``uint64 length``, masked CRC-32C of the
length, the data, masked CRC-32C of the data), each holding an ``Event`` protobuf. The
engine reads them with its own code (no new dependency): CRC-32C by a table and a small
reader of the protobuf wire format, limited to the fields of ``event.proto``,
``summary.proto``, ``tensor.proto`` and ``tensor_shape.proto`` named in the acceptance
document. Every record is checked before a value is selected; a field repeated where the
format allows one value, or two alternatives of a oneof, is refused rather than resolved
by order. Any failure raises ``ExtractionError``.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from refute.packs.ml.extract import ExtractionError

FILE_VERSION_PREFIX = b"brain.Event:"
DT_FLOAT = 1
DT_DOUBLE = 2
_MAX_FIELD = (1 << 29) - 1
_MASK_DELTA = 0xA282EAD8


def _crc_table() -> list[int]:
    table = []
    for n in range(256):
        c = n
        for _ in range(8):
            c = (c >> 1) ^ 0x82F63B78 if c & 1 else c >> 1
        table.append(c)
    return table


_TABLE = _crc_table()


def crc32c(data: bytes) -> int:
    """CRC-32C (Castagnoli, reflected polynomial 0x82F63B78)."""
    crc = 0xFFFFFFFF
    for byte in data:
        crc = _TABLE[(crc ^ byte) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFF


def masked_crc(data: bytes) -> int:
    crc = crc32c(data)
    return ((((crc >> 15) | (crc << 17)) & 0xFFFFFFFF) + _MASK_DELTA) & 0xFFFFFFFF


def records(data: bytes, where: str) -> list[bytes]:
    """The data of every record; a bad CRC, a cut record or trailing bytes refuse the file."""
    out: list[bytes] = []
    pos = 0
    while pos < len(data):
        if len(data) - pos < 12:
            raise ExtractionError(f"{where}: a record header is cut short at byte {pos}")
        header = data[pos : pos + 8]
        (length,) = struct.unpack("<Q", header)
        (crc,) = struct.unpack("<I", data[pos + 8 : pos + 12])
        if crc != masked_crc(header):
            raise ExtractionError(f"{where}: the length CRC of the record at byte {pos} is wrong")
        start = pos + 12
        if length > len(data) - start or len(data) - start - length < 4:
            raise ExtractionError(f"{where}: the record at byte {pos} is cut short")
        body = data[start : start + length]
        (crc,) = struct.unpack("<I", data[start + length : start + length + 4])
        if crc != masked_crc(body):
            raise ExtractionError(f"{where}: the data CRC of the record at byte {pos} is wrong")
        out.append(body)
        pos = start + length + 4
    if not out:
        raise ExtractionError(f"{where}: the event file holds no record")
    return out


# ---- protobuf wire format ---------------------------------------------------------------


def _varint(buf: bytes, pos: int, where: str) -> tuple[int, int]:
    value = 0
    for i in range(10):
        if pos + i >= len(buf):
            raise ExtractionError(f"{where}: a varint is not terminated")
        byte = buf[pos + i]
        if i == 9 and byte > 1:
            raise ExtractionError(f"{where}: a varint goes beyond 64 bits")
        value |= (byte & 0x7F) << (7 * i)
        if not byte & 0x80:
            return value, pos + i + 1
    raise ExtractionError(f"{where}: a varint is longer than 10 bytes")


def fields(buf: bytes, where: str) -> list[tuple[int, int, Any]]:
    """``(field number, wire type, value)`` in order: an int for wire type 0, bytes
    otherwise (8 bytes for type 1, 4 for type 5, the payload for type 2)."""
    out: list[tuple[int, int, Any]] = []
    pos = 0
    while pos < len(buf):
        key, pos = _varint(buf, pos, where)
        number, wire = key >> 3, key & 7
        if number == 0 or number > _MAX_FIELD:
            raise ExtractionError(f"{where}: field number {number} is out of range")
        if wire == 0:
            value, pos = _varint(buf, pos, where)
        elif wire in (1, 5):
            size = 8 if wire == 1 else 4
            if len(buf) - pos < size:
                raise ExtractionError(f"{where}: field {number} is cut short")
            value, pos = buf[pos : pos + size], pos + size
        elif wire == 2:
            size, pos = _varint(buf, pos, where)
            if size > len(buf) - pos:
                raise ExtractionError(f"{where}: field {number} is longer than its message")
            value, pos = buf[pos : pos + size], pos + size
        else:
            raise ExtractionError(f"{where}: wire type {wire} of field {number} is not read")
        out.append((number, wire, value))
    return out


def _message(
    buf: bytes,
    where: str,
    known: dict[int, tuple[int, ...]],
    single: set[int],
    oneof: set[int],
) -> dict[int, list[tuple[int, Any]]]:
    """The fields of one message, by number; a known field with another wire type, a
    single field given twice, or two alternatives of the oneof are refused."""
    out: dict[int, list[tuple[int, Any]]] = {}
    for number, wire, value in fields(buf, where):
        if number in known and wire not in known[number]:
            raise ExtractionError(f"{where}: field {number} has wire type {wire}")
        out.setdefault(number, []).append((wire, value))
    for number in single:
        if len(out.get(number, [])) > 1:
            raise ExtractionError(f"{where}: field {number} is given more than once")
    chosen = [n for n in oneof if n in out]
    if len(chosen) > 1 or any(len(out[n]) > 1 for n in chosen):
        raise ExtractionError(f"{where}: more than one alternative of a oneof: {sorted(chosen)}")
    return out


_EVENT_KNOWN = {1: (1,), 2: (0,), 3: (2,), 4: (2,), 5: (2,), 6: (2,), 7: (2,), 8: (2,),
                9: (2,), 10: (2,)}  # fmt: skip
_EVENT_ONEOF = {3, 4, 5, 6, 7, 8, 9}
_VALUE_KNOWN = {1: (2,), 2: (5,), 3: (2,), 4: (2,), 5: (2,), 6: (2,), 7: (2,), 8: (2,), 9: (2,)}
_VALUE_ONEOF = {2, 3, 4, 5, 6, 8}
_TENSOR_KNOWN = {1: (0,), 2: (2,), 3: (0,), 4: (2,), 5: (2, 5), 6: (2, 1)}
_SHAPE_KNOWN = {2: (2,), 3: (0,)}


def _signed64(value: int) -> int:
    return value - (1 << 64) if value >= 1 << 63 else value


@dataclass(frozen=True)
class Scalar:
    step: int
    value: float
    width: str  # "float32" or "float64"


def _floats(payloads: list[tuple[int, Any]], size: int, fmt: str, where: str) -> list[float]:
    out: list[float] = []
    for wire, raw in payloads:
        if wire == 2 and len(raw) % size:
            raise ExtractionError(f"{where}: a packed list of {len(raw)} bytes")
        out.extend(v for (v,) in struct.iter_unpack(fmt, raw))
    return out


def _tensor(buf: bytes, where: str) -> tuple[float, str]:
    t = _message(buf, where, _TENSOR_KNOWN, {1, 2, 3, 4}, set())
    others = sorted(n for n in t if 7 <= n <= 18)
    if others:
        raise ExtractionError(f"{where}: the tensor holds the typed list(s) {others}")
    dtype = t[1][0][1] if 1 in t else 0
    if dtype not in (DT_FLOAT, DT_DOUBLE):
        raise ExtractionError(f"{where}: tensor dtype {dtype} is not DT_FLOAT or DT_DOUBLE")
    if 2 not in t:
        raise ExtractionError(f"{where}: the tensor has no tensor_shape")
    shape = _message(t[2][0][1], where, _SHAPE_KNOWN, {3}, set())
    if 2 in shape:
        raise ExtractionError(f"{where}: the tensor is not of rank 0")
    if 3 in shape and shape[3][0][1] != 0:
        raise ExtractionError(f"{where}: the tensor has an unknown rank")
    size, fmt, width, own, other = (
        (4, "<f", "float32", 5, 6) if dtype == DT_FLOAT else (8, "<d", "float64", 6, 5)
    )
    if other in t:
        raise ExtractionError(f"{where}: the tensor holds the typed list of the other dtype")
    if 4 in t and own in t:
        raise ExtractionError(f"{where}: the tensor holds both tensor_content and a list")
    if 4 in t:
        content = t[4][0][1]
        if len(content) != size:
            raise ExtractionError(f"{where}: tensor_content of {len(content)} bytes")
        values = [struct.unpack(fmt, content)[0]]
    else:
        values = _floats(t.get(own, []), size, fmt, where)
    if len(values) != 1:
        raise ExtractionError(f"{where}: the tensor holds {len(values)} elements, not 1")
    return values[0], width


def scalars(data: bytes, tag: str, where: str) -> list[Scalar]:
    """Every value of ``tag`` in the file, in record order; the whole file is checked."""
    wanted = tag.encode("utf-8")
    out: list[Scalar] = []
    for index, body in enumerate(records(data, where)):
        at = f"{where}: record {index}"
        event = _message(body, at, _EVENT_KNOWN, {1, 2, 10}, _EVENT_ONEOF)
        if index == 0:
            versions = event.get(3, [])
            if not versions or not versions[0][1].startswith(FILE_VERSION_PREFIX):
                raise ExtractionError(f"{at}: not a file_version starting with brain.Event:")
            continue
        if 5 not in event:
            continue
        step = _signed64(event[2][0][1]) if 2 in event else 0  # proto3: absent is 0
        summary = _message(event[5][0][1], at, {1: (2,)}, set(), set())
        for _, raw in summary.get(1, []):
            value = _message(raw, at, _VALUE_KNOWN, {1, 7, 9}, _VALUE_ONEOF)
            name = value[1][0][1] if 1 in value else b""
            if name != wanted:
                continue
            if 2 in value:
                (number,) = struct.unpack("<f", value[2][0][1])
                out.append(Scalar(step, number, "float32"))
            elif 8 in value:
                number, width = _tensor(value[8][0][1], at)
                out.append(Scalar(step, number, width))
            else:
                raise ExtractionError(f"{at}: the value of tag {tag!r} is not a scalar")
    return out


def select(data: bytes, tag: str, step: int | str, where: str) -> Scalar:
    """The one value of ``tag`` at ``step`` (an integer, or ``"last"``: the greatest step)."""
    found = scalars(data, tag, where)
    for before, after in zip(found, found[1:], strict=False):
        if after.step <= before.step:
            raise ExtractionError(
                f"{where}: the steps of tag {tag!r} do not strictly increase "
                f"({before.step} then {after.step})"
            )
    if not found:
        raise ExtractionError(f"{where}: no value of tag {tag!r}")
    if step == "last":
        return found[-1]
    match = [s for s in found if s.step == step]
    if not match:
        raise ExtractionError(f"{where}: no value of tag {tag!r} at step {step}")
    return match[0]


def token(value: float, where: str) -> str:
    """The exact decimal expansion of a binary float, without exponent."""
    if not math.isfinite(value):
        raise ExtractionError(f"{where}: the value {value!r} is not finite")
    return format(Decimal(value), "f")
