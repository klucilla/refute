"""The allowed patches of a claim: the grammar and the application in memory
(docs/validation/v0.3/wp3-allowed-patches-acceptance.md, W3.9a), offline."""

from __future__ import annotations

import pytest

from refute.packs.ml import patches as pt

SRC = b"".join(b"line %d\n" % i for i in range(1, 21))


def modify(path: str, *hunks: bytes, index: bytes | None = None) -> bytes:
    out = b"diff --git a/%s b/%s\n" % (path.encode(), path.encode())
    if index is not None:
        out += index + b"\n"
    out += b"--- a/%s\n+++ b/%s\n" % (path.encode(), path.encode())
    return out + b"".join(hunks)


def create(path: str, body: list[bytes]) -> bytes:
    p = path.encode()
    head = b"diff --git a/%s b/%s\nnew file mode 100644\n--- /dev/null\n+++ b/%s\n" % (p, p, p)
    return head + b"@@ -0,0 +1,%d @@\n" % len(body) + b"".join(b"+" + x + b"\n" for x in body)


def one(data: bytes, original: bytes | None = SRC) -> bytes:
    (fp,) = pt.parse(data)
    return pt.apply_text(original, fp)


# ---- must pass --------------------------------------------------------------------------------


def test_one_changed_line_with_gits_function_context():
    patch = modify(
        "a.py", b"@@ -4,3 +4,3 @@ def load_data():\n line 4\n-line 5\n+LINE 5\n line 6\n"
    )
    assert one(patch) == SRC.replace(b"line 5\n", b"LINE 5\n")


def test_several_hunks_follow_the_shift_of_earlier_insertions():
    patch = modify(
        "a.py",
        b"@@ -2,2 +2,3 @@\n line 2\n+new A\n line 3\n",
        b"@@ -10,2 +11,2 @@\n line 10\n-line 11\n+LINE 11\n",
    )
    out = one(patch)
    assert b"line 2\nnew A\nline 3\n" in out and b"LINE 11\n" in out


def test_insertion_and_deletion_with_no_context():
    assert one(modify("a.py", b"@@ -3,0 +4 @@\n+inserted\n")).startswith(
        b"line 1\nline 2\nline 3\ninserted\nline 4\n"
    )
    assert b"line 5\n" not in one(modify("a.py", b"@@ -5 +4,0 @@\n-line 5\n"))


def test_a_creation_and_an_executable_file_keeping_its_mode():
    assert one(create("new/dir/x.txt", [b"a", b"b"]), None) == b"a\nb\n"
    patch = modify(
        "run.sh",
        b"@@ -1 +1 @@\n-line 1\n+LINE 1\n",
        index=b"index 1234567..89abcde 100755",
    )
    (fp,) = pt.parse(patch)
    assert fp.mode == "100755"


def test_crlf_and_no_final_newline_are_kept_byte_for_byte():
    crlf = b"a\r\nb\r\nc\r\n"
    assert one(modify("w.txt", b"@@ -2 +2 @@\n-b\r\n+B\r\n"), crlf) == b"a\r\nB\r\nc\r\n"
    tail = b"x\ny"
    patch = modify("t.txt", b"@@ -2 +2 @@\n-y\n\\ No newline at end of file\n+Y\n")
    assert one(patch, tail) == b"x\nY\n"


def test_two_patches_on_two_files_are_planned_in_order():
    a = modify("a.py", b"@@ -1 +1 @@\n-line 1\n+L1\n")
    b = modify("b.py", b"@@ -1 +1 @@\n-line 1\n+L1\n")
    parsed = pt.plan([("p1.patch", a), ("p2.patch", b)], ["data/d.csv"])
    assert [fp.path for p in parsed for fp in p] == ["a.py", "b.py"]


# ---- must fail --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "patch",
    [
        b"",
        b"diff --git a/a.py b/b.py\n--- a/a.py\n+++ b/b.py\n@@ -1 +1 @@\n-line 1\n+x\n",
        b"diff --git a/a.py b/a.py\nrename from a.py\nrename to b.py\n",
        b"diff --git a/a.py b/a.py\ndeleted file mode 100644\n--- a/a.py\n+++ /dev/null\n",
        b"diff --git a/a.py b/a.py\nold mode 100644\nnew mode 100755\n",
        b"diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\nGIT binary patch\n",
        b'diff --git "a/a b.py" "b/a b.py"\n',
        b"diff --git a/a.py b/a.py\nindex 1234567..89abcde\nindex 1234567..89abcde\n",
        b"diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n",  # no hunk
        modify("a.py", b"@@ -1 +1 @@\n-line 1\n+x\n") * 2,  # one file twice
        modify("../a.py", b"@@ -1 +1 @@\n-line 1\n+x\n"),
        modify("./a.py", b"@@ -1 +1 @@\n-line 1\n+x\n"),
        modify(".git/config", b"@@ -1 +1 @@\n-line 1\n+x\n"),
        modify(".refute/x", b"@@ -1 +1 @@\n-line 1\n+x\n"),
        modify("a.py", b"@@ -1 +1 @@\n-line 1\n+x\n", index=b"index 1234567..89abcde 100600"),
        modify("a.py", b"@@ -5,2 +5,2 @@\n line 5\n-line 6\n+x\n", b"@@ -3 +3 @@\n-line 3\n+y\n"),
        modify("a.py", b"@@ -1,2 +1,2 @@\n-line 1\n+x\n"),  # counts not met
        modify("a.py", b"@@ -1 +1 @@\n-line 1\n+x\n+y\n"),  # more lines than counted
        modify("a.py", b"@@ -1 +1 @@\n?line 1\n+x\n"),
        modify("a.py", b"@@ -2,0 +2 @@\n+x\n"),  # c does not follow (expected +3)
        modify("t.txt", b"@@ -1,2 +1,2 @@\n-x\n\\ No newline at end of file\n-y\n+X\n+y\n"),
    ],
)
def test_patches_outside_the_grammar_are_refused(patch):
    with pytest.raises(pt.PatchError):
        pt.parse(patch)


def test_a_creation_with_mode_100755_is_refused():
    patch = create("x.sh", [b"a"]).replace(
        b"new file mode 100644\n", b"new file mode 100644\nindex 0000000..1234567 100755\n"
    )
    with pytest.raises(pt.PatchError, match="100644"):
        pt.parse(patch)


@pytest.mark.parametrize(
    ("patch", "original"),
    [
        (modify("a.py", b"@@ -5 +5 @@\n-line 6\n+x\n"), SRC),  # matches only at line 6
        (modify("a.py", b"@@ -1 +1 @@\n-line 1\n+x\n"), None),  # missing file
        (create("a.py", [b"x"]), SRC),  # existing file
        (modify("a.py", b"@@ -1 +1 @@\n-line 1\n+x\x00\n"), SRC),  # NUL after
        (modify("a.py", b"@@ -1 +1 @@\n-line 1\n+x\n"), b"line 1\n\xff\n"),  # not UTF-8
        (modify("a.py", b"@@ -25 +25 @@\n-line 25\n+x\n"), SRC),  # outside the file
    ],
)
def test_a_patch_that_does_not_apply_exactly_is_refused(patch, original):
    with pytest.raises(pt.PatchError):
        one(patch, original)


def test_the_claims_patches_are_refused_together():
    a = modify("a.py", b"@@ -1 +1 @@\n-line 1\n+L1\n")
    with pytest.raises(pt.PatchError, match="two patches"):
        pt.plan([("p1", a), ("p2", a)], [])
    up = modify("A.py", b"@@ -1 +1 @@\n-line 1\n+L1\n")
    with pytest.raises(pt.PatchError, match="case"):
        pt.plan([("p1", a), ("p2", up)], [])
    for data in ("a.py", "a.py/x", ""):
        if not data:
            continue
        with pytest.raises(pt.PatchError, match="data path"):
            pt.plan([("p1", a)], [data])
    nested = modify("data/sub/f.txt", b"@@ -1 +1 @@\n-line 1\n+x\n")
    with pytest.raises(pt.PatchError, match="data path"):
        pt.plan([("p1", nested)], ["data"])
    with pytest.raises(pt.PatchError, match="over"):
        pt.plan([("p1", b"x" * (pt.MAX_CLAIM_BYTES + 1))], [])
