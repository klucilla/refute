"""The comparator of amendment 2, revision 6, section 3.1 (v0.5.13, the maintainer's decision L4(b),
#218 comment 7223634913). Frozen with the margin manifest before it reads any golden file.

    python -I -B docs/validation/v0.5.13/tools/comparator.py <freeze.json> <ref label> <alt label> \
        <schema.json> <ref record> <ref dir> <alt record> <alt dir> \
        <ref claim-hash record> <alt claim-hash record>

**Corrections under the maintainer's decision P2** (#218 comment 7225754254, Codex's items 6 and 7
that bear on decision identity):
- no shortcut on equal bytes: every file is decoded and validated, and a malformed file fails even
  when both settings hold it;
- a duplicate key in any JSON object is malformed;
- a report line matched by more than one template fails, equal or not;
- a number is exact when its last key matches the schema's ``exact_key_regex`` (thresholds named
  ``required_*``, ``min_*``, ``max_*``, ``*_threshold``, ``*_limit``), whatever pattern it sits
  under; the global ``exact_keys`` do not apply under ``keys_not_exact_under`` (a fit's error
  named like a plan field);
- the claim check requires every value to be a SHA-256 except the approved exceptions, present with
  their exact text in both records;
- the command checks the schema and the four records against the freeze list's SHA-256 first.

It compares one alternate setting with the reference (ID-BEFORE), never two alternates. It
writes one JSON result to stdout, and exits 0 only when the setting meets section 3.1.

**What it checks** (section 3.1, Codex round 1, item 1, as written):
1. **Inventory.** The files in each folder are exactly the files of that setting's recorded
   payload (``payload.files_sha256``), and each file's SHA-256 equals the recorded value. The two
   settings have the same inventory and the same ``payload.error_outputs``.
2. **Exact files.** ``plan-*`` (configuration) and ``error-*`` (error records), and any output
   that is an ``ERROR`` text, must be equal byte for byte.
3. **JSON** (``chain-*.json`` and the part of ``verdict-*.txt`` before the report separator). Both
   texts are cut into tokens: whitespace runs, structural characters, strings, numbers and the
   literals ``true``, ``false`` and ``null``. The two sequences must have the same length and the
   same kinds. Every token other than a number must be equal byte for byte, whitespace and line
   endings included. A number token may differ only when:
   - both tokens are in float form (they hold ``.``, ``e`` or ``E``; an integer token is an
     integer count and compares exactly);
   - its path matches a measurement pattern of the schema and no exact pattern;
   - its last key is not one of the schema's exact keys (thresholds and configuration), and no
     key of its path is one of the schema's exact subtree keys (a mapping of thresholds);
   - and ``abs(a - b) <= 0.000001 * max(abs(a), abs(b))``, in exact rational arithmetic from the
     decimal tokens. Zero equals only zero.
   ``dumps_json`` writes a nonfinite float as ``null``, so a nonfinite value is accepted only
   where both settings hold ``null`` at the same place.
4. **The report** (after the separator). Both parts must have the same number of lines. A line
   pair that is equal byte for byte passes. Otherwise exactly one template of the schema must
   match each line in full, the same template for both, and every group must agree: an ``exact``
   group byte for byte, a ``measurement`` group as a number within the budget above (both in the
   same printed form). ``n/a`` is a nonfinite or absent value and matches only ``n/a``.

Anything malformed, missing, extra or ambiguous fails. The claim inventory is compared by
``compare_claims``.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

BUDGET = Fraction(1, 1_000_000)
SEPARATOR = "\n---report---\n"
TOKEN = re.compile(
    r'(?P<ws>[ \t\r\n]+)|(?P<struct>[{}\[\]:,])|(?P<str>"(?:[^"\\]|\\.)*")'
    r"|(?P<num>-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)|(?P<lit>true|false|null)"
)


class MalformedError(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_float_form(token: str) -> bool:
    return any(c in token for c in ".eE")


def within_budget(a: str, b: str) -> bool:
    try:
        x, y = Fraction(Decimal(a)), Fraction(Decimal(b))
    except (InvalidOperation, ValueError) as exc:
        raise MalformedError(f"not a finite decimal: {a!r} or {b!r}") from exc
    return abs(x - y) <= BUDGET * max(abs(x), abs(y))


def lex(text: str) -> list[tuple[str, str, str]]:
    """The JSON tokens as (kind, raw text, path). The path of a value is its keys and indices,
    joined by ``.``, with ``[i]`` for list items; structural tokens and whitespace carry the path
    of the value they sit in."""
    tokens: list[tuple[str, str, str]] = []
    stack: list[list] = []  # [kind, key or index, expecting key]
    pos = 0

    def path() -> str:
        parts = []
        for frame in stack:
            if frame[0] == "obj" and frame[1] is not None:
                parts.append("." + frame[1] if parts else frame[1])
            elif frame[0] == "arr":
                parts.append(f"[{frame[1]}]")
        return "".join(parts)

    while pos < len(text):
        m = TOKEN.match(text, pos)
        if m is None:
            raise MalformedError(f"unexpected character at offset {pos}")
        kind, raw = m.lastgroup, m.group()
        pos = m.end()
        if kind == "struct":
            if raw == "{":
                tokens.append((kind, raw, path()))
                stack.append(["obj", None, True])
                continue
            if raw == "[":
                tokens.append((kind, raw, path()))
                stack.append(["arr", 0, False])
                continue
            if raw in "}]":
                if not stack:
                    raise MalformedError("unbalanced close")
                stack.pop()
                tokens.append((kind, raw, path()))
                continue
            if raw == ":":
                tokens.append((kind, raw, path()))
                stack[-1][2] = False
                continue
            if raw == ",":
                tokens.append((kind, raw, path()))
                if stack and stack[-1][0] == "arr":
                    stack[-1][1] += 1
                elif stack:
                    stack[-1][2] = True
                continue
        if kind == "str" and stack and stack[-1][0] == "obj" and stack[-1][2]:
            stack[-1][1] = json.loads(raw)
            tokens.append(("key", raw, path()))
            continue
        tokens.append((kind, raw, path()))
    if stack:
        raise MalformedError("unbalanced open")
    strict_loads(text)  # the text must also be valid JSON, with no duplicate key
    return tokens


def _no_duplicates(pairs: list[tuple[str, object]]) -> dict:
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise MalformedError(f"duplicate JSON key in an object: {sorted(set(keys))[:5]}")
    return dict(pairs)


def strict_loads(text: str):
    """``json.loads`` that rejects a duplicate key in any object (P2, Codex's item 7)."""
    try:
        return json.loads(text, object_pairs_hook=_no_duplicates)
    except ValueError as exc:
        if isinstance(exc, MalformedError):
            raise
        raise MalformedError(f"not valid JSON: {exc}") from exc


def _pattern(glob: str) -> re.Pattern:
    out, i = [], 0
    while i < len(glob):
        if glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob[i] == "*":
            out.append(r"[^.\[\]]*")
            i += 1
        else:
            out.append(re.escape(glob[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def key_segments(path: str) -> list[str]:
    """Every key of a path, without the list indices."""
    return [p for p in re.split(r"[.\[]", path) if p and not p.rstrip("]").isdigit()]


def last_key(path: str) -> str:
    """The nearest key of a path, skipping list indices: ``a.b[2][0]`` gives ``b``."""
    keys = [p for p in re.split(r"[.\[]", path) if p and not p.rstrip("]").isdigit()]
    return keys[-1] if keys else ""


def compare_json(a: str, b: str, kind: str, schema: dict) -> list[str]:
    problems: list[str] = []
    ta, tb = lex(a), lex(b)
    if len(ta) != len(tb):
        return [f"{kind}: token counts differ ({len(ta)} and {len(tb)})"]
    measure = [_pattern(p) for p in schema["json"][kind]["measurement"]]
    exact = [_pattern(p) for p in schema["json"][kind].get("exact", [])]
    exact_keys = set(schema["exact_keys"])
    subtrees = set(schema.get("exact_subtree_keys", []))
    key_rx = re.compile(schema["exact_key_regex"]) if schema.get("exact_key_regex") else None
    free = [_pattern(p) for p in schema.get("keys_not_exact_under", [])]

    def is_exact(path: str) -> bool:
        if subtrees & set(key_segments(path)) or any(p.match(path) for p in exact):
            return True
        if key_rx is not None and key_rx.search(last_key(path)):
            return True
        return last_key(path) in exact_keys and not any(p.match(path) for p in free)

    for i, ((ka, ra, pa), (kb, rb, pb)) in enumerate(zip(ta, tb, strict=True)):
        if ka != kb or pa != pb:
            problems.append(f"{kind}: token {i} differs in kind or location ({pa!r})")
            continue
        if ra == rb:
            continue
        if ka != "num":
            problems.append(f"{kind}: token {i} at {pa!r} differs ({ka})")
            continue
        if not (is_float_form(ra) and is_float_form(rb)):
            problems.append(f"{kind}: integer token at {pa!r} differs")
        elif is_exact(pa):
            problems.append(f"{kind}: exact number at {pa!r} differs")
        elif not any(p.match(pa) for p in measure):
            problems.append(f"{kind}: number at {pa!r} is not a schema measurement and differs")
        elif not within_budget(ra, rb):
            problems.append(f"{kind}: measurement at {pa!r} differs beyond the budget")
    return problems


NUMBER = re.compile(r"-?[0-9]+(?:\.[0-9]+)?(?:e[+-][0-9]+)?\Z")


def compare_report(a: str, b: str, schema: dict) -> list[str]:
    la, lb = a.split("\n"), b.split("\n")
    if len(la) != len(lb):
        return [f"report: line counts differ ({len(la)} and {len(lb)})"]
    templates = [(t["name"], re.compile(t["regex"]), t["groups"]) for t in schema["report"]]
    problems: list[str] = []
    for n, (x, y) in enumerate(zip(la, lb, strict=True), 1):
        mx = [(name, rx.fullmatch(x), g) for name, rx, g in templates if rx.fullmatch(x)]
        my = [(name, rx.fullmatch(y), g) for name, rx, g in templates if rx.fullmatch(y)]
        if len(mx) > 1 or len(my) > 1:
            # an ambiguous mapping is a failure even on equal lines (P2, Codex's item 7)
            problems.append(f"report line {n}: more than one template matches")
            continue
        if x == y:
            continue
        if len(mx) != 1 or len(my) != 1 or mx[0][0] != my[0][0]:
            problems.append(f"report line {n}: differs and no single shared template matches")
            continue
        _, gx, groups = mx[0]
        gy = my[0][1]
        for group, role in groups.items():
            u, v = gx.group(group), gy.group(group)
            if u == v:
                continue
            if role != "measurement":
                problems.append(f"report line {n}: exact group {group!r} differs")
            elif u == "n/a" or v == "n/a" or not (NUMBER.match(u) and NUMBER.match(v)):
                problems.append(f"report line {n}: group {group!r} is not a pair of numbers")
            elif is_float_form(u) != is_float_form(v) or ("e" in u) != ("e" in v):
                problems.append(f"report line {n}: group {group!r} changes printed form")
            elif not within_budget(u, v):
                problems.append(f"report line {n}: group {group!r} differs beyond the budget")
    return problems


def compare_file(name: str, a: bytes, b: bytes, schema: dict) -> list[str]:
    """No shortcut on equal bytes (P2, Codex's item 7): every file is decoded and its structure
    validated, so that a malformed file never passes because both settings hold it."""
    try:
        ta, tb = a.decode("utf-8"), b.decode("utf-8")
    except UnicodeDecodeError:
        return [f"{name}: not UTF-8"]
    if name.startswith(("plan-", "error-")) or ta.startswith("ERROR") or tb.startswith("ERROR"):
        if a != b:
            return [f"{name}: an exact file differs"]
        if name.startswith(("plan-", "error-")) and not ta.startswith("ERROR"):
            try:
                strict_loads(ta)
            except MalformedError as exc:
                return [f"{name}: malformed: {exc}"]
        return []
    try:
        if name.startswith("chain-") and name.endswith(".json"):
            return [f"{name}: {p}" for p in compare_json(ta, tb, "chain", schema)]
        if name.startswith("verdict-") and name.endswith(".txt"):
            if ta.count(SEPARATOR) != 1 or tb.count(SEPARATOR) != 1:
                return [f"{name}: the report separator is not there exactly once"]
            ja, ra = ta.split(SEPARATOR)
            jb, rb = tb.split(SEPARATOR)
            out = compare_json(ja, jb, "verdict", schema) + compare_report(ra, rb, schema)
            return [f"{name}: {p}" for p in out]
    except MalformedError as exc:
        return [f"{name}: malformed: {exc}"]
    return [f"{name}: a file of no known kind differs"]


def compare_setting(schema: dict, ref_rec: dict, ref_dir: Path, alt_rec: dict, alt_dir: Path):
    problems: list[str] = []
    files: dict[str, list[str]] = {}
    ref_files = ref_rec["payload"]["files_sha256"]
    alt_files = alt_rec["payload"]["files_sha256"]
    if sorted(ref_files) != sorted(alt_files):
        problems.append("the recorded inventories differ")
    if ref_rec["payload"]["error_outputs"] != alt_rec["payload"]["error_outputs"]:
        problems.append("the recorded error outputs differ")
    for folder, recorded in ((ref_dir, ref_files), (alt_dir, alt_files)):
        present = sorted(p.name for p in folder.iterdir() if p.is_file())
        if present != sorted(recorded):
            problems.append(f"{folder.name}: the files present are not the recorded inventory")
        for name, digest in recorded.items():
            path = folder / name
            if not path.is_file() or sha(path.read_bytes()) != digest:
                problems.append(f"{folder.name}/{name}: missing, or SHA-256 not as recorded")
    if problems:
        return {"result": "FAIL", "problems": problems, "files": files}
    for name in sorted(ref_files):
        found = compare_file(name, (ref_dir / name).read_bytes(), (alt_dir / name).read_bytes(),
                             schema)  # fmt: skip
        files[name] = found
        problems += found
    return {"result": "PASS" if not problems else "FAIL", "problems": problems, "files": files}


HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def compare_claims(ref_rec: dict, alt_rec: dict, exceptions: dict[str, str]) -> list[str]:
    """Section 3.1: the exact protected claim inventory and identical resolved SHA-256 values.
    Every value is a SHA-256 (64 lowercase hex digits), except the approved baseline exceptions
    (``exceptions``: path -> the exact recorded text), which must be present with that text in
    both records. Two records that share a gap or a malformed value fail (P2, Codex's item 7)."""
    a, b = ref_rec["payload"]["claims"], alt_rec["payload"]["claims"]
    problems = []
    if sorted(a) != sorted(b):
        problems.append("the claim inventories differ")
    for path, text in exceptions.items():
        for label, rec in (("reference", a), ("alternate", b)):
            if rec.get(path) != text:
                problems.append(f"claim {path}: the approved exception is not in the {label}")
    for label, rec in (("reference", a), ("alternate", b)):
        for k, v in rec.items():
            if k not in exceptions and not (isinstance(v, str) and HEX64.match(v)):
                problems.append(f"claim {k}: the {label} value is not a SHA-256")
    problems += [f"claim {k}: resolved value differs" for k in sorted(a) if k in b and a[k] != b[k]]
    return problems


def check_bound(freeze: dict, label_ref: str, label_alt: str, files: dict[str, Path]) -> list[str]:
    """Each file the command uses must have the SHA-256 the freeze list records (P2): the schema,
    and for each of the two settings its golden record and its claim-hash record."""
    expected = {
        "schema": freeze["schema"]["sha256"],
        "ref_record": freeze["settings"][label_ref]["record_sha256"],
        "alt_record": freeze["settings"][label_alt]["record_sha256"],
        "ref_claims": freeze["settings"][label_ref]["claim_record_sha256"],
        "alt_claims": freeze["settings"][label_alt]["claim_record_sha256"],
    }
    return [
        f"{name}: SHA-256 is not the frozen one"
        for name, path in files.items()
        if sha(path.read_bytes()) != expected[name]
    ]


def main() -> int:
    """Arguments: the freeze list, the reference and alternate setting labels (as in the freeze
    list), the schema, the reference golden record and folder, the alternate golden record and
    folder, then the reference and alternate claim-hash records. Every file is first checked
    against the SHA-256 the freeze list records; a mismatch fails before any golden is read."""
    freeze = strict_loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    label_ref, label_alt = sys.argv[2], sys.argv[3]
    paths = {
        "schema": Path(sys.argv[4]),
        "ref_record": Path(sys.argv[5]),
        "alt_record": Path(sys.argv[7]),
        "ref_claims": Path(sys.argv[9]),
        "alt_claims": Path(sys.argv[10]),
    }
    bound = check_bound(freeze, label_ref, label_alt, paths)
    if bound:
        print(json.dumps({"result": "FAIL", "problems": bound}, indent=1))
        return 1
    schema = strict_loads(paths["schema"].read_text(encoding="utf-8"))
    ref_rec = strict_loads(paths["ref_record"].read_text(encoding="utf-8"))
    alt_rec = strict_loads(paths["alt_record"].read_text(encoding="utf-8"))
    out = compare_setting(schema, ref_rec, Path(sys.argv[6]), alt_rec, Path(sys.argv[8]))
    ref_claims = strict_loads(paths["ref_claims"].read_text(encoding="utf-8"))
    alt_claims = strict_loads(paths["alt_claims"].read_text(encoding="utf-8"))
    out["claims"] = compare_claims(ref_claims, alt_claims, schema.get("claim_exceptions", {}))
    if out["claims"]:
        out["result"] = "FAIL"
    print(json.dumps(out, indent=1))
    return 0 if out["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
