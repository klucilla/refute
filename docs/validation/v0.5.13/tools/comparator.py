"""The comparator of amendment 2, section 3.1 (v0.5.13; written under the maintainer's decision
L4(b), #218 comment 7223634913, for revision 6; used under revision 8, adopted in decision R1,
#218 comment 7226818333). Frozen with its schema and span mapping by the freeze commit of
revision 8, section 4, before it reads any golden file.

    python -I -B docs/validation/v0.5.13/tools/comparator.py <freeze.json> <alt label> \
        <ref golden dir> <alt golden dir>

The reference is always ID-BEFORE (``id-before``). The alternate is a setting the freeze list
records (NR-A1's three settings) or the prospective setting it names (``nr-a2-t2``). Every other
input (the schema and the four records) comes from the freeze list's paths and is bound to it.

**Corrections under the maintainer's decision S1** (#218 comment 7227283917; Codex's round of R3,
``r3/codex/answer.md``, items 1 to 6):
1. A number whose key is listed in the schema's ``computed_keys_despite_name`` (a computed
   measurement whose name starts with ``max_``, ``min_`` or ``required_``) is a measurement: the
   name rule ``exact_key_regex`` does not apply to it. The global ``exact_keys`` do not apply at
   the exact paths of ``exact_key_exempt_paths`` (a fit's error named like a plan field), and
   nowhere else.
2. Configuration is always exact: the schema's exact patterns name the configuration echoed under
   broad measurement patterns, and ``exact_by_sibling`` makes a sensitivity block's
   ``alternative`` exact when its ``effect`` is one that the plan alone sets.
3. (Decision S2) Message lines are compared byte for byte, with no tolerance: in the JSON every
   string is exact, and in the report a line matched by a template whose groups are all
   ``exact`` (``exact_line``) is exact. A changed message is a failure.
4. Every measurement group of a templated report line is validated, equal or not: a number, or
   one of the template's markers of absence or non-finiteness (``n/a``, ``inf``, ``-inf``), and a
   marker only against the same marker. A valid change of printed form of a measurement (for
   example ``99999.9999`` against ``1.0000e+05``) is compared by value. JSON's non-standard
   constants (``NaN``, ``Infinity``) are malformed.
5. Every claim value, the approved exception included, is compared by its serialized bytes in the
   two records, and decoded; the exception's text must equal the approved text.
6. (Decision S3) There is no unbound path. The reference is fixed. A frozen setting's records are
   bound by the freeze list's SHA-256. NR-A2's records are bound by the prospective entry of the
   freeze list: its manifest (frozen SHA-256, committed, with a passed order-proof receipt), the
   records committed after the manifest, the frozen SHA-256 of ``identity_v2.py`` in their
   provenance, its label, and its two-thread setting. Every file is read once: the bytes whose
   SHA-256 is checked are the bytes compared.

**Kept from decisions P2 and R2:** no shortcut on equal bytes; a duplicate JSON key is malformed;
an ambiguous template fails even on equal lines; the coverage report (``coverage``,
``coverage_by_file``): files compared, numeric pairs compared and differing, the largest relative
difference (exact rational arithmetic, 6 significant digits); zero files compared is
``INCONCLUSIVE``, never ``PASS`` (decision S4).

**What it checks** (section 3.1, Codex round 1, item 1, as written):
1. **Inventory.** The files in each folder are exactly the files of that setting's record
   (``payload.files_sha256``), and each file's SHA-256 equals the recorded value. The two settings
   have the same inventory and the same ``payload.error_outputs``.
2. **Exact files.** ``plan-*`` (configuration) and ``error-*`` (error records), and any output
   that is an ``ERROR`` text, must be equal byte for byte, and valid.
3. **JSON** (``chain-*.json`` and the part of ``verdict-*.txt`` before the report separator). Both
   texts are cut into tokens: whitespace runs, structural characters, strings, numbers and the
   literals ``true``, ``false`` and ``null``. The two sequences must have the same length and the
   same kinds. Every token other than a number must be equal byte for byte. A number token may
   differ only when both are in float form, its path matches a measurement pattern and is not
   exact (item 1 and 2 above), and ``abs(a - b) <= 0.000001 * max(abs(a), abs(b))`` in exact
   rational arithmetic. Zero equals only zero.
4. **The report** (after the separator). Both parts must have the same number of lines. Each line
   matched by a template is validated (item 4); equal lines then pass. Otherwise one template
   must match both lines, every ``exact`` group must be equal, and every ``measurement`` group
   must be within the budget above.

Anything malformed, missing, extra or ambiguous fails.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REFERENCE = "id-before"
RECEIPTS = "docs/validation/v0.5.13/order-proofs"
BUDGET = Fraction(1, 1_000_000)
SEPARATOR = "\n---report---\n"
TOKEN = re.compile(
    r'(?P<ws>[ \t\r\n]+)|(?P<struct>[{}\[\]:,])|(?P<str>"(?:[^"\\]|\\.)*")'
    r"|(?P<num>-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)|(?P<lit>true|false|null)"
)
NUMBER = re.compile(r"-?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z")
MARKERS = ("n/a", "inf", "-inf")


class MalformedError(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_float_form(token: str) -> bool:
    return any(c in token for c in ".eE")


def _fraction(a: str) -> Fraction:
    try:
        return Fraction(Decimal(a))
    except (InvalidOperation, ValueError) as exc:
        raise MalformedError(f"not a finite decimal: {a!r}") from exc


def within_budget(a: str, b: str) -> bool:
    x, y = _fraction(a), _fraction(b)
    return abs(x - y) <= BUDGET * max(abs(x), abs(y))


class Coverage:
    """The counts of decision R2: numeric pairs compared and differing, and the largest relative
    difference among them, in exact rational arithmetic."""

    def __init__(self) -> None:
        self.compared = 0
        self.differing = 0
        self.largest = Fraction(0)

    def add(self, a: str, b: str) -> None:
        self.compared += 1
        if a == b:
            return
        self.differing += 1
        x, y = _fraction(a), _fraction(b)
        if x != y:
            self.largest = max(self.largest, abs(x - y) / max(abs(x), abs(y)))

    def merge(self, other: Coverage) -> None:
        self.compared += other.compared
        self.differing += other.differing
        self.largest = max(self.largest, other.largest)

    def as_dict(self) -> dict:
        largest = Decimal(self.largest.numerator) / Decimal(self.largest.denominator)
        return {
            "numeric_tokens_compared": self.compared,
            "numeric_tokens_differing": self.differing,
            "largest_relative_difference": "0" if not self.largest else f"{largest:.5e}",
        }


def _no_duplicates(pairs: list[tuple[str, object]]) -> dict:
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise MalformedError(f"duplicate JSON key in an object: {sorted(set(keys))[:5]}")
    return dict(pairs)


def _no_constant(name: str):
    raise MalformedError(f"non-standard JSON constant {name!r}")


def strict_loads(text: str):
    """``json.loads`` that rejects a duplicate key in any object (P2) and the non-standard
    constants ``NaN``, ``Infinity`` and ``-Infinity`` (S1, item 4)."""
    try:
        return json.loads(text, object_pairs_hook=_no_duplicates, parse_constant=_no_constant)
    except ValueError as exc:
        if isinstance(exc, MalformedError):
            raise
        raise MalformedError(f"not valid JSON: {exc}") from exc


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
    strict_loads(text)  # the text must also be valid JSON, with no duplicate key or constant
    return tokens


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
    keys = key_segments(path)
    return keys[-1] if keys else ""


def _parent(path: str) -> str:
    return path.rsplit(".", 1)[0] if "." in path else ""


def exactness(schema: dict, kind: str):
    """The function that says whether a number at a path is compared exactly."""
    exact = [_pattern(p) for p in schema["json"][kind].get("exact", [])]
    exact_keys = set(schema["exact_keys"])
    subtrees = set(schema.get("exact_subtree_keys", []))
    key_rx = re.compile(schema["exact_key_regex"]) if schema.get("exact_key_regex") else None
    computed = set(schema.get("computed_keys_despite_name", {}))
    exempt = set(schema.get("exact_key_exempt_paths", []))
    by_sibling = [
        (_pattern(r["pattern"]), r["sibling"], set(r["values"]))
        for r in schema.get("exact_by_sibling", [])
    ]

    def is_exact(path: str, strings: dict[str, str]) -> bool:
        if subtrees & set(key_segments(path)) or any(p.match(path) for p in exact):
            return True
        for pat, sibling, values in by_sibling:
            if pat.match(path):
                raw = strings.get(f"{_parent(path)}.{sibling}")
                if raw is None or json.loads(raw) in values:
                    return True  # an unknown sibling is exact, the conservative side
        key = last_key(path)
        if key_rx is not None and key_rx.search(key) and key not in computed:
            return True
        return key in exact_keys and path not in exempt

    return is_exact


def compare_json(a: str, b: str, kind: str, schema: dict, cov: Coverage | None = None) -> list[str]:
    cov = cov if cov is not None else Coverage()
    problems: list[str] = []
    ta, tb = lex(a), lex(b)
    if len(ta) != len(tb):
        return [f"{kind}: token counts differ ({len(ta)} and {len(tb)})"]
    measure = [_pattern(p) for p in schema["json"][kind]["measurement"]]
    is_exact = exactness(schema, kind)
    strings = {p: r for k, r, p in ta if k == "str"}
    for i, ((ka, ra, pa), (kb, rb, pb)) in enumerate(zip(ta, tb, strict=True)):
        if ka != kb or pa != pb:
            problems.append(f"{kind}: token {i} differs in kind or location ({pa!r})")
            continue
        if ka == "num":
            cov.add(ra, rb)
        if ra == rb:
            continue
        if ka != "num":
            problems.append(f"{kind}: token {i} at {pa!r} differs ({ka})")
            continue
        if not (is_float_form(ra) and is_float_form(rb)):
            problems.append(f"{kind}: integer token at {pa!r} differs")
        elif is_exact(pa, strings):
            problems.append(f"{kind}: exact number at {pa!r} differs")
        elif not any(p.match(pa) for p in measure):
            problems.append(f"{kind}: number at {pa!r} is not a schema measurement and differs")
        elif not within_budget(ra, rb):
            problems.append(f"{kind}: measurement at {pa!r} differs beyond the budget")
    return problems


def _check_group(value: str | None, markers: tuple[str, ...]) -> bool:
    return value is not None and (bool(NUMBER.match(value)) or value in markers)


def compare_report(a: str, b: str, schema: dict, cov: Coverage | None = None) -> list[str]:
    cov = cov if cov is not None else Coverage()
    la, lb = a.split("\n"), b.split("\n")
    if len(la) != len(lb):
        return [f"report: line counts differ ({len(la)} and {len(lb)})"]
    templates = [
        (t["name"], re.compile(t["regex"]), t["groups"], tuple(t.get("markers", MARKERS)))
        for t in schema["report"]
    ]
    problems: list[str] = []
    for n, (x, y) in enumerate(zip(la, lb, strict=True), 1):
        mx = [(name, rx.fullmatch(x), g, mk) for name, rx, g, mk in templates if rx.fullmatch(x)]
        my = [(name, rx.fullmatch(y), g, mk) for name, rx, g, mk in templates if rx.fullmatch(y)]
        if len(mx) > 1 or len(my) > 1:
            # an ambiguous mapping is a failure even on equal lines (P2)
            problems.append(f"report line {n}: more than one template matches")
            continue
        malformed = [
            group
            for found in (mx, my)
            for _, match, groups, markers in found
            for group, role in groups.items()
            if role == "measurement" and not _check_group(match.group(group), markers)
        ]
        if malformed:
            # a measurement group that is neither a number nor a marker fails, equal or not (S1)
            problems.append(
                f"report line {n}: malformed measurement group(s) {sorted(set(malformed))}"
            )
            continue
        shared = len(mx) == 1 and len(my) == 1 and mx[0][0] == my[0][0]
        if shared:
            for group in mx[0][2]:
                u, v = mx[0][1].group(group), my[0][1].group(group)
                if u is not None and v is not None and NUMBER.match(u) and NUMBER.match(v):
                    cov.add(u, v)
        if x == y:
            continue
        if not shared:
            problems.append(f"report line {n}: differs and no single shared template matches")
            continue
        _, gx, groups, _markers = mx[0]
        gy = my[0][1]
        for group, role in groups.items():
            u, v = gx.group(group), gy.group(group)
            if u == v:
                continue
            if role != "measurement":
                problems.append(f"report line {n}: exact group {group!r} differs")
            elif not (NUMBER.match(u) and NUMBER.match(v)):
                problems.append(f"report line {n}: group {group!r}: a marker against another value")
            elif not within_budget(u, v):
                problems.append(f"report line {n}: group {group!r} differs beyond the budget")
    return problems


def compare_file(
    name: str, a: bytes, b: bytes, schema: dict, cov: Coverage | None = None
) -> list[str]:
    """No shortcut on equal bytes (P2): every file is decoded and its structure validated, so that
    a malformed file never passes because both settings hold it. Exact files (``plan-``,
    ``error-``, ``ERROR`` texts) add no numeric pair to ``cov``: they compare as bytes."""
    cov = cov if cov is not None else Coverage()
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
            return [f"{name}: {p}" for p in compare_json(ta, tb, "chain", schema, cov)]
        if name.startswith("verdict-") and name.endswith(".txt"):
            if ta.count(SEPARATOR) != 1 or tb.count(SEPARATOR) != 1:
                return [f"{name}: the report separator is not there exactly once"]
            ja, ra = ta.split(SEPARATOR)
            jb, rb = tb.split(SEPARATOR)
            out = compare_json(ja, jb, "verdict", schema, cov)
            out += compare_report(ra, rb, schema, cov)
            return [f"{name}: {p}" for p in out]
    except MalformedError as exc:
        return [f"{name}: malformed: {exc}"]
    return [f"{name}: a file of no known kind differs"]


def read_folder(folder: Path, recorded: dict[str, str]) -> tuple[dict[str, bytes], list[str]]:
    """Each file read once; its bytes are kept only if their SHA-256 is the recorded one."""
    problems: list[str] = []
    present = sorted(p.name for p in folder.iterdir() if p.is_file()) if folder.is_dir() else []
    if present != sorted(recorded):
        problems.append(f"{folder.name}: the files present are not the recorded inventory")
    data: dict[str, bytes] = {}
    for name, digest in recorded.items():
        path = folder / name
        raw = path.read_bytes() if path.is_file() else None
        if raw is None or sha(raw) != digest:
            problems.append(f"{folder.name}/{name}: missing, or SHA-256 not as recorded")
        else:
            data[name] = raw
    return data, problems


def compare_setting(schema: dict, ref_rec: dict, ref_dir: Path, alt_rec: dict, alt_dir: Path):
    problems: list[str] = []
    files: dict[str, list[str]] = {}
    total = Coverage()
    by_file: dict[str, dict] = {}

    def done(result: str) -> dict:
        return {"result": result, "problems": problems, "files": files,
                "coverage": {"files_compared": len(by_file), **total.as_dict()},
                "coverage_by_file": by_file}  # fmt: skip

    ref_files = ref_rec["payload"]["files_sha256"]
    alt_files = alt_rec["payload"]["files_sha256"]
    if sorted(ref_files) != sorted(alt_files):
        problems.append("the recorded inventories differ")
    if ref_rec["payload"]["error_outputs"] != alt_rec["payload"]["error_outputs"]:
        problems.append("the recorded error outputs differ")
    ref_data, p1 = read_folder(ref_dir, ref_files)
    alt_data, p2 = read_folder(alt_dir, alt_files)
    problems += p1 + p2
    if problems:
        return done("FAIL")
    for name in sorted(ref_files):
        cov = Coverage()
        found = compare_file(name, ref_data[name], alt_data[name], schema, cov)
        files[name] = found
        by_file[name] = cov.as_dict()
        total.merge(cov)
        problems += found
    if problems:
        return done("FAIL")
    if not by_file:
        problems.append("no file was compared")
        return done("INCONCLUSIVE")  # zero coverage is never a PASS (S4)
    return done("PASS")


HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def claim_values(text: str) -> dict[str, str]:
    """The raw serialized string of each claim value (``payload.claims.<path>``)."""
    prefix = "payload.claims."
    return {p[len(prefix) :]: r for k, r, p in lex(text) if k == "str" and p.startswith(prefix)}


def compare_claims(ref_text: str, alt_text: str, exceptions: dict[str, str]) -> list[str]:
    """Section 3.1: the exact protected claim inventory and identical resolved SHA-256 values,
    compared by their serialized bytes in the two records (S1, item 5) and decoded. Every value is
    a SHA-256 (64 lowercase hex digits), except the approved baseline exceptions (``exceptions``:
    path -> the exact approved text), present in both records with that text."""
    problems: list[str] = []
    try:
        a, b = claim_values(ref_text), claim_values(alt_text)
        da = strict_loads(ref_text)["payload"]["claims"]
        db = strict_loads(alt_text)["payload"]["claims"]
    except (MalformedError, KeyError, TypeError) as exc:
        return [f"claim records malformed: {exc}"]
    if sorted(a) != sorted(da) or sorted(b) != sorted(db):
        problems.append("a claim value is not a JSON string")
    if sorted(da) != sorted(db):
        problems.append("the claim inventories differ")
    for path, text in exceptions.items():
        for label, rec in (("reference", da), ("alternate", db)):
            if rec.get(path) != text:
                problems.append(f"claim {path}: the approved exception is not in the {label}")
    for label, rec in (("reference", da), ("alternate", db)):
        for k, v in rec.items():
            if k not in exceptions and not (isinstance(v, str) and HEX64.match(v)):
                problems.append(f"claim {k}: the {label} value is not a SHA-256")
    problems += [
        f"claim {k}: serialized value differs" for k in sorted(a) if k in b and a[k] != b[k]
    ]
    return problems


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def committed(rel: str, data: bytes) -> bool:
    """The bytes are the committed blob of ``rel`` at the checked-out commit."""
    try:
        return git("show", f"@:{rel}") == data
    except subprocess.CalledProcessError:
        return False


def is_ancestor(older: str, newer: str) -> bool:
    done = subprocess.run(["git", "merge-base", "--is-ancestor", older, newer], cwd=ROOT,
                          capture_output=True)  # fmt: skip
    return done.returncode == 0


def last_commit(rel: str) -> str:
    return git("log", "-1", "--format=%H", "--", rel).decode().strip()


def receipt_passed(manifest_sha: str) -> bool:
    path = ROOT / RECEIPTS / f"{manifest_sha}.v2.json"
    if not path.is_file():
        return False
    receipt = strict_loads(path.read_text(encoding="utf-8"))
    return receipt.get("passed") is True and receipt.get("manifest_sha256") == manifest_sha


def bind_prospective(entry: dict, label: str, rec: dict, claims: dict, raw: dict) -> list[str]:
    """Decision S3: NR-A2's records are bound to its manifest and to its setting."""
    problems: list[str] = []
    manifest = (ROOT / entry["manifest"]["path"]).read_bytes()
    if sha(manifest) != entry["manifest"]["sha256"]:
        problems.append("the NR-A2 manifest's SHA-256 is not the frozen one")
    if not committed(entry["manifest"]["path"], manifest):
        problems.append("the NR-A2 manifest is not committed")
    if not receipt_passed(entry["manifest"]["sha256"]):
        problems.append("the NR-A2 manifest has no passed order-proof receipt")
    m_commit = last_commit(entry["manifest"]["path"])
    for key in ("record", "claim_record"):
        rel = entry[key]
        if not committed(rel, raw[key]):
            problems.append(f"{rel}: not committed with these bytes")
            continue
        r_commit = last_commit(rel)
        if not (m_commit and r_commit != m_commit and is_ancestor(m_commit, r_commit)):
            problems.append(f"{rel}: not committed after the NR-A2 manifest")
    want = entry["script_sha256"]
    for name, doc in (("golden record", rec), ("claim record", claims)):
        if doc.get("label") != label:
            problems.append(f"the {name} is not labelled {label!r}")
        if doc.get("provenance", {}).get("script_sha256") != want:
            problems.append(f"the {name} was not written by the frozen identity script")
        env = doc.get("provenance", {}).get("blas", {}).get("thread_env", {})
        if env != entry["thread_env"]:
            problems.append(f"the {name}'s thread variables are not the frozen setting")
    info = rec.get("provenance", {}).get("blas", {}).get("child_threadpool_info") or []
    if not info or any(d.get("num_threads") != entry["threads"] for d in info):
        problems.append("the companion process does not show the setting's thread count")
    return problems


def bind(freeze: dict, label: str) -> tuple[dict, list[str]]:
    """Read once, and bind, the schema and the four records of a comparison."""
    problems: list[str] = []
    raw: dict[str, bytes] = {}
    schema_raw = (ROOT / freeze["schema"]["path"]).read_bytes()
    if sha(schema_raw) != freeze["schema"]["sha256"]:
        problems.append("schema: SHA-256 is not the frozen one")
    ref = freeze["settings"][REFERENCE]
    raw["ref_record"] = (ROOT / ref["record"]).read_bytes()
    raw["ref_claims"] = (ROOT / ref["claim_record"]).read_bytes()
    if sha(raw["ref_record"]) != ref["record_sha256"]:
        problems.append("ref_record: SHA-256 is not the frozen one")
    if sha(raw["ref_claims"]) != ref["claim_record_sha256"]:
        problems.append("ref_claims: SHA-256 is not the frozen one")
    entry = None
    if label in freeze["settings"] and label != REFERENCE:
        alt = freeze["settings"][label]
        raw["record"] = (ROOT / alt["record"]).read_bytes()
        raw["claim_record"] = (ROOT / alt["claim_record"]).read_bytes()
        if sha(raw["record"]) != alt["record_sha256"]:
            problems.append("alt_record: SHA-256 is not the frozen one")
        if sha(raw["claim_record"]) != alt["claim_record_sha256"]:
            problems.append("alt_claims: SHA-256 is not the frozen one")
    elif label in freeze.get("prospective", {}):
        entry = freeze["prospective"][label]
        raw["record"] = (ROOT / entry["record"]).read_bytes()
        raw["claim_record"] = (ROOT / entry["claim_record"]).read_bytes()
    else:
        return {}, [f"{label!r} is neither a frozen setting nor the frozen prospective one"]
    docs = {"schema": schema_raw}
    docs.update(raw)
    parsed = {}
    try:
        parsed = {k: strict_loads(v.decode("utf-8")) for k, v in docs.items()}
    except (MalformedError, UnicodeDecodeError) as exc:
        return {}, problems + [f"a bound file is malformed: {exc}"]
    if entry is not None:
        problems += bind_prospective(entry, label, parsed["record"], parsed["claim_record"], raw)
    parsed["raw"] = raw
    return parsed, problems


def main() -> int:
    """Arguments: the freeze list, the alternate label, the reference golden folder and the
    alternate golden folder. Every bound file is checked before any golden file is read."""
    freeze_path = Path(sys.argv[1])
    freeze_raw = freeze_path.read_bytes()
    freeze = strict_loads(freeze_raw.decode("utf-8"))
    label, ref_dir, alt_dir = sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
    problems: list[str] = []
    rel = freeze_path.resolve().relative_to(ROOT).as_posix()
    if not committed(rel, freeze_raw) or not receipt_passed(sha(freeze_raw)):
        problems.append("the freeze list is not committed with a passed order-proof receipt")
    parsed, bound = bind(freeze, label)
    problems += bound
    if problems:
        print(json.dumps({"result": "FAIL", "problems": problems}, indent=1))
        return 1
    out = compare_setting(parsed["schema"], parsed["ref_record"], ref_dir, parsed["record"],
                          alt_dir)  # fmt: skip
    out["claims"] = compare_claims(
        parsed["raw"]["ref_claims"].decode("utf-8"),
        parsed["raw"]["claim_record"].decode("utf-8"),
        parsed["schema"].get("claim_exceptions", {}),
    )
    if out["claims"]:
        out["result"] = "FAIL"
    out.update({"reference": REFERENCE, "alternate": label, "freeze_sha256": sha(freeze_raw)})
    print(json.dumps(out, indent=1))
    return 0 if out["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
