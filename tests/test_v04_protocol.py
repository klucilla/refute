"""The v0.4 protocol text states the values of refute.packs.tess.discover.protocol (section 13
of calibration/v0.4/PROTOCOL.md): the two must agree."""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import yaml

from refute.packs.tess.discover import protocol as p
from refute.packs.tess.synthetic import V04_SURVIVED_MEANING

PROTOCOL = Path(__file__).resolve().parents[1] / "calibration" / "v0.4" / "PROTOCOL.md"
OBJECTS = {
    "domain": p.DOMAIN,
    "selection": p.SELECTION,
    "controls": p.CONTROLS,
    "dedup": p.DEDUP,
    "promotion": p.PROMOTION,
    "injection": p.INJECTION,
    "transforms": p.TRANSFORMS,
    "budget": p.BUDGET,
}


def _values() -> dict:
    text = PROTOCOL.read_text(encoding="utf-8")
    block = text.split("## 13.")[1]
    return yaml.safe_load(re.search(r"```yaml\n(.*?)```", block, re.S).group(1))


def test_every_stated_value_is_the_code_value():
    stated = _values()
    assert set(stated) == set(OBJECTS)
    for name, values in stated.items():
        code = dataclasses.asdict(OBJECTS[name])
        for key, value in values.items():
            expected = code[key]
            if isinstance(expected, tuple):
                expected = [list(x) if isinstance(x, tuple) else x for x in expected]
            assert value == expected, (name, key, value, expected)


def test_every_scalar_code_value_is_stated():
    stated = _values()
    for name, obj in OBJECTS.items():
        for key, value in dataclasses.asdict(obj).items():
            if isinstance(value, tuple) and name != "budget":
                continue  # factor lists are stated in the text (sections 4.3, 6 and 9)
            assert key in stated[name], (name, key)


def test_the_survived_meaning_is_the_same_everywhere():
    assert p.SURVIVED_MEANING == V04_SURVIVED_MEANING
    assert p.SURVIVED_MEANING in PROTOCOL.read_text(encoding="utf-8").replace("\n", " ")
