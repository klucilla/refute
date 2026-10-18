"""A scalar read from a TensorBoard event file (docs/validation/v0.3/
wp3-tensorboard-acceptance.md, W3.11b), offline.

The event files are built here by an encoder of this module (a bitwise CRC-32C, not the
reader's table), checked against published vectors, so a shared mistake of the reader
and the encoder would show."""

from __future__ import annotations

import struct
from decimal import Decimal

import pytest

from refute.packs.ml import extract as ex
from refute.packs.ml import tbevents as tb
from refute.packs.ml.schema import CountSelector, Extraction

TAG = "ood/auroc"

# ---- the encoder of the tests ---------------------------------------------------------------


def crc32c_bitwise(data: bytes) -> int:
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x82F63B78 if crc & 1 else crc >> 1
    return crc ^ 0xFFFFFFFF


def masked(data: bytes) -> int:
    crc = crc32c_bitwise(data)
    rotated = ((crc >> 15) | (crc << 17)) % 2**32
    return (rotated + 0xA282EAD8) % 2**32


def varint(n: int) -> bytes:
    n &= 2**64 - 1  # an int64 as protobuf writes it
    out = bytearray()
    while True:
        low, n = n & 0x7F, n >> 7
        out.append(low | (0x80 if n else 0))
        if not n:
            return bytes(out)


def key(number: int, wire: int) -> bytes:
    return varint(number << 3 | wire)


def f_varint(number: int, n: int) -> bytes:
    return key(number, 0) + varint(n)


def f_len(number: int, payload: bytes) -> bytes:
    return key(number, 2) + varint(len(payload)) + payload


def f_32(number: int, raw: bytes) -> bytes:
    return key(number, 5) + raw


def f_64(number: int, raw: bytes) -> bytes:
    return key(number, 1) + raw


def record(data: bytes) -> bytes:
    length = struct.pack("<Q", len(data))
    return length + struct.pack("<I", masked(length)) + data + struct.pack("<I", masked(data))


VERSION = f_64(1, struct.pack("<d", 1.0)) + f_len(3, b"brain.Event:2")


def event(step: int | None, *values: bytes, wall: float = 2.0, extra: bytes = b"") -> bytes:
    out = f_64(1, struct.pack("<d", wall))
    if step is not None:
        out += f_varint(2, step)
    return out + f_len(5, b"".join(f_len(1, v) for v in values)) + extra


def simple(value: float, tag: str = TAG) -> bytes:
    return f_len(1, tag.encode()) + f_32(2, struct.pack("<f", value))


def tensor_value(body: bytes, tag: str = TAG) -> bytes:
    return f_len(1, tag.encode()) + f_len(8, body)


def tensor(dtype: int | None = 1, shape: bytes | None = b"", rest: bytes = b"") -> bytes:
    out = b"" if dtype is None else f_varint(1, dtype)
    if shape is not None:
        out += f_len(2, shape)
    return out + rest


def f32(value: float) -> bytes:
    return struct.pack("<f", value)


def f64(value: float) -> bytes:
    return struct.pack("<d", value)


def events_file(*events: bytes, first: bytes = VERSION) -> bytes:
    return b"".join(record(e) for e in (first, *events))


def read(data: bytes, step=2, tag: str = TAG) -> tb.Scalar:
    return tb.select(data, tag, step, "file:test")


def as_float32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


# ---- the vectors ----------------------------------------------------------------------------


def test_crc32c_matches_the_published_check_values():
    assert tb.crc32c(b"123456789") == 0xE3069283 == crc32c_bitwise(b"123456789")
    assert tb.crc32c(bytes(32)) == 0x8A9136AA  # RFC 3720, appendix B.4
    assert tb.crc32c(b"\xff" * 32) == 0x62A8AB43
    for data in (b"", b"a", b"brain.Event:2", bytes(range(256))):
        assert tb.masked_crc(data) == masked(data)


# ---- must pass ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (simple(0.75), (0.75, "float32")),
        (tensor_value(tensor(1, b"", f_len(4, f32(0.5)))), (0.5, "float32")),
        (tensor_value(tensor(1, b"", f_len(5, f32(0.25)))), (0.25, "float32")),  # packed
        (tensor_value(tensor(1, b"", f_32(5, f32(0.125)))), (0.125, "float32")),  # not packed
        (tensor_value(tensor(2, b"", f_len(4, f64(0.1)))), (0.1, "float64")),
        (tensor_value(tensor(2, b"", f_len(6, f64(0.3)))), (0.3, "float64")),  # packed
        (tensor_value(tensor(2, b"", f_64(6, f64(0.7)))), (0.7, "float64")),  # not packed
    ],
)
def test_each_scalar_form_is_read(value, expected):
    got = read(events_file(event(2, value)))
    assert (got.value, got.width) == expected and got.step == 2


def test_step_n_and_last_select_among_steps_and_other_records_are_ignored():
    image = f_len(1, b"images/x") + f_len(4, b"\x08\x01")
    data = events_file(
        event(1, simple(0.5), image),
        f_varint(2, 2) + f_len(4, b"graph bytes"),
        event(2, simple(0.6), simple(9.0, "other")),
        event(5, simple(0.7)),
    )
    assert read(data, 1).value == 0.5
    assert read(data, 2).value == as_float32(0.6)
    assert read(data, "last").value == as_float32(0.7) and read(data, "last").step == 5


def test_an_absent_step_is_step_zero_and_a_negative_step_stays_negative():
    data = events_file(event(-3, simple(0.1)), event(None, simple(0.2)), event(4, simple(0.3)))
    assert read(data, 0).value == as_float32(0.2)
    assert [s.step for s in tb.scalars(data, TAG, "f")] == [-3, 0, 4]


def test_unknown_fields_are_skipped_and_unknown_rank_false_is_absent():
    unknown = f_varint(99, 7) + f_len(100, b"xyz") + f_32(101, b"abcd") + f_64(102, bytes(8))
    shape = f_varint(3, 0)
    value = tensor_value(tensor(1, shape, f_len(4, f32(0.5)) + f_varint(3, 1)) + unknown)
    assert read(events_file(event(2, value, extra=unknown))).value == 0.5


def test_the_order_of_fields_and_independent_records_and_the_wall_time_do_not_matter():
    a = f_len(1, TAG.encode()) + f_32(2, f32(0.5))
    b = f_32(2, f32(0.5)) + f_len(1, TAG.encode())
    for value in (a, b):
        first = event(1, value, wall=9.0)
        second = f_len(5, f_len(1, simple(0.9))) + f_varint(2, 3) + f_64(1, f64(1.0))
        other = event(2, simple(1.0, "x"), wall=0.5)
        for order in ((first, other, second), (other, first, second), (first, second, other)):
            data = events_file(*order)
            assert read(data, "last").value == as_float32(0.9)
            assert read(data, 1).value == 0.5


def test_the_token_is_the_exact_expansion_of_the_binary_float():
    tenth = as_float32(0.1)
    assert tb.token(tenth, "f") == "0.100000001490116119384765625"
    assert Decimal(tb.token(tenth, "f")) == Decimal(tenth)
    assert tb.token(-0.0, "f") == "-0"
    subnormal = struct.unpack("<f", b"\x01\x00\x00\x00")[0]
    assert Decimal(tb.token(subnormal, "f")) == Decimal(subnormal)
    largest = struct.unpack("<f", b"\xff\xff\x7f\x7f")[0]
    assert tb.token(largest, "f") == str(int(largest))
    assert Decimal(tb.token(1.7976931348623157e308, "f")) == Decimal(1.7976931348623157e308)


def test_an_event_file_named_by_the_run_is_read_through_its_pattern(tmp_path):
    folder = tmp_path / "train" / "summaries"
    folder.mkdir(parents=True)
    (folder / "events.out.tfevents.1729.host.42.0.v2").write_bytes(
        events_file(event(2, simple(0.875)))
    )
    spec = {
        "from": "file",
        "file": "train/summaries/*",
        "tensorboard": {"tag": TAG, "step": "last"},
        "unit": "fraction",
    }
    Extraction.model_validate(spec)
    got = ex.extract(spec, tmp_path, "", None)
    assert got.token == "0.875" and got.binary == "float32"
    assert got.source == "file:train/summaries/events.out.tfevents.1729.host.42.0.v2"
    (folder / "events.out.tfevents.1730.host.43.0.v2").write_bytes(
        events_file(event(2, simple(0.875)))
    )
    with pytest.raises(ex.ExtractionError, match="2 paths match"):
        ex.extract(spec, tmp_path, "", None)


# ---- must fail: the records -----------------------------------------------------------------


def _good() -> bytes:
    return events_file(event(2, simple(0.5)))


def _corrupt(data: bytes, index: int) -> bytes:
    out = bytearray(data)
    out[index] ^= 0x01
    return bytes(out)


def test_a_wrong_length_crc_or_data_crc_refuses_the_file():
    data = _good()
    first = len(record(VERSION))
    with pytest.raises(ex.ExtractionError, match="length CRC"):
        read(_corrupt(data, first + 8))
    with pytest.raises(ex.ExtractionError, match="data CRC"):
        read(_corrupt(data, len(data) - 1))
    with pytest.raises(ex.ExtractionError, match="data CRC"):
        read(_corrupt(data, first + 14))  # a byte of the data


@pytest.mark.parametrize("cut", [1, 4, 6, 11])
def test_a_record_cut_short_or_trailing_bytes_refuse_the_file(cut):
    data = _good()
    with pytest.raises(ex.ExtractionError):
        read(data[:-cut])
    with pytest.raises(ex.ExtractionError):
        read(data + b"\x00" * cut)


def test_an_empty_file_or_a_file_that_does_not_start_with_its_version_is_refused():
    with pytest.raises(ex.ExtractionError, match="no record"):
        read(b"")
    with pytest.raises(ex.ExtractionError, match="file_version"):
        read(events_file(event(2, simple(0.5)), first=event(1, simple(0.4))))
    with pytest.raises(ex.ExtractionError, match="file_version"):
        read(events_file(event(2, simple(0.5)), first=f_len(3, b"other:2")))
    with pytest.raises(ex.ExtractionError, match="oneof"):
        read(events_file(event(2, simple(0.5)), first=VERSION + f_len(5, b"")))


def test_a_corrupt_record_after_the_selected_value_still_refuses_the_file():
    data = events_file(event(2, simple(0.5)), event(3, simple(0.6)))
    with pytest.raises(ex.ExtractionError, match="CRC"):
        read(_corrupt(data, len(data) - 1), 2)


# ---- must fail: the wire format -------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "match"),
    [
        (b"\x10" + b"\xff" * 10 + b"\x00", "longer than 10 bytes|beyond 64 bits"),
        (b"\x10" + b"\xff" * 9 + b"\x02", "beyond 64 bits"),
        (b"\x10\xff\xff", "not terminated"),
        (b"\x00\x01", "field number 0"),
        (varint(2**29 << 3), "out of range"),
        (b"\x09\x00\x00", "cut short"),  # fixed64 of field 1
        (b"\x2a\x05ab", "longer than its message"),
        (key(9, 3), "wire type 3"),
        (key(9, 4), "wire type 4"),
        (key(9, 6) + b"\x00", "wire type 6"),
        (key(9, 7) + b"\x00", "wire type 7"),
        (f_varint(1, 5), "field 1 has wire type 0"),  # wall_time must be a double
        (f_32(2, b"abcd"), "field 2 has wire type 5"),
    ],
)
def test_malformed_wire_format_refuses_the_file(raw, match):
    with pytest.raises(ex.ExtractionError, match=match):
        read(events_file(event(2, simple(0.5)), raw))


@pytest.mark.parametrize(
    "bad",
    [
        f_varint(2, 2) + f_varint(2, 2) + f_len(5, f_len(1, simple(0.5))),  # step twice
        f_64(1, f64(1)) + f_64(1, f64(2)) + f_len(5, f_len(1, simple(0.5))),  # wall_time
        f_len(5, f_len(1, simple(0.5))) + f_len(5, f_len(1, simple(0.6))),  # summary twice
        f_len(5, f_len(1, simple(0.5))) + f_len(3, b"brain.Event:2"),  # two alternatives
        f_len(4, b"graph") + f_len(5, f_len(1, simple(0.5))),
        f_len(5, f_len(1, simple(0.5))) + f_len(7, b""),  # summary and session_log
    ],
)
def test_a_repeated_single_field_or_two_alternatives_of_event_what_are_refused(bad):
    with pytest.raises(ex.ExtractionError, match="more than once|oneof"):
        read(events_file(bad))


@pytest.mark.parametrize(
    "value",
    [
        simple(0.5) + f_len(8, tensor(1, b"", f_len(4, f32(0.5)))),
        f_len(8, tensor(1, b"", f_len(4, f32(0.5)))) + f_32(2, f32(0.5)) + f_len(1, b"x"),
        simple(0.5) + f_len(4, b"\x08\x01"),  # an image
        simple(0.5) + f_len(5, b""),  # a histogram
        simple(0.5) + f_len(6, b""),  # audio
        simple(0.5) + f_32(2, f32(0.6)),  # simple_value twice
        simple(0.5) + f_len(1, TAG.encode()),  # tag twice
    ],
)
def test_two_alternatives_of_the_value_or_a_repeated_field_are_refused(value):
    with pytest.raises(ex.ExtractionError, match="more than once|oneof"):
        read(events_file(event(2, value)))


# ---- must fail: the values of the tag -------------------------------------------------------


def test_an_absent_tag_or_step_gives_no_value():
    data = events_file(event(2, simple(0.5, "other")))
    with pytest.raises(ex.ExtractionError, match="no value of tag"):
        read(data)
    with pytest.raises(ex.ExtractionError, match="at step 3"):
        read(events_file(event(2, simple(0.5))), 3)


@pytest.mark.parametrize(
    "events",
    [
        (event(2, simple(0.5), simple(0.5)),),  # two values in one event, equal
        (event(2, simple(0.5)), event(2, simple(0.6))),  # two events at one step
        (event(3, simple(0.5)), event(2, simple(0.6))),  # a decreasing step
        (event(1, simple(0.4)), event(5, simple(0.5)), event(2, simple(0.6))),  # a restart
    ],
)
def test_steps_that_do_not_strictly_increase_are_refused(events):
    for step in (2, "last"):
        with pytest.raises(ex.ExtractionError, match="strictly increase"):
            read(events_file(*events), step)


@pytest.mark.parametrize(
    ("value", "match"),
    [
        (f_len(1, TAG.encode()) + f_len(4, b"\x08\x01"), "not a scalar"),
        (f_len(1, TAG.encode()) + f_len(5, b""), "not a scalar"),
        (f_len(1, TAG.encode()) + f_len(6, b""), "not a scalar"),
        (f_len(1, TAG.encode()), "not a scalar"),
        (tensor_value(tensor(3, b"", f_len(4, b"\x01\x00\x00\x00"))), "dtype 3"),  # DT_INT32
        (tensor_value(tensor(19, b"", f_len(4, b"\x00\x3c"))), "dtype 19"),  # DT_HALF
        (tensor_value(tensor(None, b"", f_len(4, f32(0.5)))), "dtype 0"),  # DT_INVALID
        (tensor_value(tensor(1, None, f_len(4, f32(0.5)))), "no tensor_shape"),
        (tensor_value(tensor(1, f_varint(3, 1), f_len(4, f32(0.5)))), "unknown rank"),
        (tensor_value(tensor(1, f_len(2, f_varint(1, 1)), f_len(4, f32(0.5)))), "rank 0"),
        (tensor_value(tensor(1, b"", f_len(5, f32(0.5) + f32(0.6)))), "2 elements"),
        (tensor_value(tensor(1, b"", f_32(5, f32(0.5)) + f_32(5, f32(0.6)))), "2 elements"),
        (tensor_value(tensor(1, b"", f_len(5, f32(0.5)) + f_32(5, f32(0.6)))), "2 elements"),
        (tensor_value(tensor(1, b"", b"")), "0 elements"),
        (tensor_value(tensor(1, b"", f_len(5, b"\x00" * 6))), "packed list of 6 bytes"),
        (tensor_value(tensor(2, b"", f_len(6, b"\x00" * 12))), "packed list of 12 bytes"),
        (tensor_value(tensor(1, b"", f_len(4, b"\x00" * 3))), "3 bytes"),
        (tensor_value(tensor(1, b"", f_len(4, b"\x00" * 5))), "5 bytes"),
        (tensor_value(tensor(2, b"", f_len(4, b"\x00" * 7))), "7 bytes"),
        (tensor_value(tensor(2, b"", f_len(4, b"\x00" * 9))), "9 bytes"),
        (tensor_value(tensor(1, b"", f_len(4, f32(0.5)) + f_len(5, f32(0.5)))), "both"),
        (tensor_value(tensor(2, b"", f_len(5, f32(0.5)))), "other dtype"),
        (tensor_value(tensor(1, b"", f_len(6, f64(0.5)))), "other dtype"),
        (
            tensor_value(tensor(1, b"", f_len(4, f32(0.5)) + f_varint(7, 1))),
            r"typed list\(s\) \[7\]",
        ),
        (tensor_value(tensor(1, b"", f_len(4, f32(0.5)) + f_len(18, b"\x00"))), r"\[18\]"),
        (tensor_value(tensor(1, b"", f_len(5, f32(0.5)) + f_len(13, b"\x00"))), r"\[13\]"),
        (tensor_value(tensor(1, b"", f_32(5, f32(0.5)) + f_varint(1, 1))), "more than once"),
        (tensor_value(tensor(1, b"", f_len(4, f32(0.5)) + f_len(4, f32(0.5)))), "more than once"),
        (tensor_value(tensor(1, b"", f_len(4, f32(0.5)))) + f_len(9, b"") * 2, "more than once"),
    ],
)
def test_a_value_of_the_tag_that_is_not_a_supported_scalar_is_refused(value, match):
    with pytest.raises(ex.ExtractionError, match=match):
        read(events_file(event(2, value)))


def test_an_unsupported_value_at_a_step_not_selected_still_refuses_the_file():
    image = f_len(1, TAG.encode()) + f_len(4, b"\x08\x01")
    with pytest.raises(ex.ExtractionError, match="not a scalar"):
        read(events_file(event(1, image), event(2, simple(0.5))), 2)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_a_value_that_is_not_finite_is_refused(tmp_path, value):
    (tmp_path / "ev").write_bytes(events_file(event(2, simple(value))))
    spec = {"from": "file", "file": "ev", "tensorboard": {"tag": TAG, "step": 2}, "unit": "native"}
    with pytest.raises(ex.ExtractionError, match="not finite"):
        ex.extract(spec, tmp_path, "", None)


def test_a_file_over_the_limit_is_not_read(tmp_path, monkeypatch):
    (tmp_path / "ev").write_bytes(_good())
    monkeypatch.setattr(ex, "MAX_BYTES", 10)
    spec = {"from": "file", "file": "ev", "tensorboard": {"tag": TAG, "step": 2}, "unit": "native"}
    with pytest.raises(ex.ExtractionError, match="larger than"):
        ex.extract(spec, tmp_path, "", None)


# ---- validation -----------------------------------------------------------------------------


def _spec(**changes) -> dict:
    spec = {
        "from": "file",
        "file": "ev",
        "tensorboard": {"tag": TAG, "step": "last"},
        "unit": "fraction",
    }
    spec.update(changes)
    return {k: v for k, v in spec.items() if v is not None}


@pytest.mark.parametrize(
    "spec",
    [
        _spec(**{"from": "log", "file": None}),
        _spec(json_path="$.a"),
        _spec(regex={"pattern": "a=(1)", "group": 1}),
        _spec(tensorboard={"tag": "", "step": 1}),
        _spec(tensorboard={"tag": TAG, "step": -1}),
        _spec(tensorboard={"tag": TAG, "step": True}),
        _spec(tensorboard={"tag": TAG, "step": "first"}),
        _spec(tensorboard={"tag": TAG, "step": "3"}),
        _spec(tensorboard={"tag": TAG, "step": 1.0}),
        _spec(tensorboard={"tag": TAG}),
        _spec(tensorboard={"tag": TAG, "step": 1, "other": 1}),
    ],
)
def test_invalid_tensorboard_selectors_are_refused_at_validation(spec):
    with pytest.raises(ValueError):
        Extraction.model_validate(spec)


def test_a_count_selector_takes_no_tensorboard_and_parse_refuses_it():
    with pytest.raises(ValueError):
        CountSelector.model_validate(
            {"from": "file", "file": "ev", "tensorboard": {"tag": TAG, "step": 1}}
        )
    with pytest.raises(ex.ExtractionError, match="not a text"):
        ex.parse({"tensorboard": {"tag": TAG, "step": 1}}, "", "log")
    with pytest.raises(ex.ExtractionError, match="from a file"):
        ex.extract({"from": "log", "tensorboard": {"tag": TAG, "step": 1}}, None, "", None)


def test_an_extraction_without_tensorboard_is_written_as_before():
    spec = {"from": "log", "regex": {"pattern": "a=(1)", "group": 1}, "unit": "native"}
    dumped = Extraction.model_validate(spec).model_dump(mode="json", by_alias=True)
    assert "tensorboard" not in dumped
    board = Extraction.model_validate(_spec()).model_dump(mode="json", by_alias=True)
    assert board["tensorboard"] == {"tag": TAG, "step": "last"}
