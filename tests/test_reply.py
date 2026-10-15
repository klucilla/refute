"""Reply draft (docs/validation/v0.3/wp2-acceptance.md, W2.13, W2.13a, W2.14). Synthetic
sealed dossiers and a synthetic address in tmp_path; the suite runs with
--disable-socket, so the command cannot open a connection."""

import json

import pytest
import yaml
from typer.testing import CliRunner

from refute.cli import app
from refute.core.dossier import DossierWriter
from refute.core.hashing import sha256_bytes
from refute.core.reply import (
    FORBIDDEN_WORDS,
    REPLY_PERIOD_DAYS,
    VERDICT_MEANING,
    ReplyDraftError,
    address_sha256,
    render,
    write_reply_draft,
)
from refute.core.seal import read_seal, seal
from refute.core.verdict import PaperVerdict

EMAIL = "corresponding.author@example.org"  # synthetic, never a real address
CLAIM = {
    "key": "arXiv-2401.01234v2-C1",
    "statement": "Method X reaches 91.2% test accuracy on Dataset Y.",
    "source": {
        "arxiv_id": "2401.01234",
        "version": 2,
        "location": "Table 2, row 'X', column 'Acc'",
        "repository_url": "https://example.org/x/repo",
        "repository_commit": "0123456789abcdef0123456789abcdef01234567",
    },
}
REPRODUCE = "git clone https://example.org/x/repo\nuv run refute replicate claim.yaml\n"


def sealed_dossier(root, verdict="FRAGILE", claim=CLAIM):
    w = DossierWriter(root)
    w.write_text("claim.yaml", yaml.safe_dump(claim, sort_keys=False))
    w.write_json("verdict.json", {"verdict": verdict, "tests": []})
    w.write_text("REPRODUCE.md", REPRODUCE)
    w.finalize()
    seal(root)
    return root


def contact(tmp_path, **overrides):
    data = {
        "arxiv_id": "2401.01234",
        "version": "2",
        "email": EMAIL,
        "printed_at": "page 1, footnote 2",
        "retrieved_utc": "2026-10-15T12:00:00Z",
    }
    data.update(overrides)
    path = tmp_path / "private" / "contacts" / "c1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({k: v for k, v in data.items() if v is not None}), encoding="utf-8")
    return path


def out_path(tmp_path):
    return tmp_path / "private" / "drafts" / "draft.txt"


# W2.13 / W2.13a ------------------------------------------------------------------------------


@pytest.mark.parametrize("verdict", [v.value for v in PaperVerdict])
def test_draft_holds_the_claim_the_verdict_and_the_commands(tmp_path, verdict):
    d = sealed_dossier(tmp_path / "D1", verdict=verdict)
    result = write_reply_draft(d, contact(tmp_path), out_path(tmp_path))
    text = result.path.read_text(encoding="utf-8")
    assert text.startswith(f"To: {EMAIL}\n")
    for piece in (
        CLAIM["statement"],
        CLAIM["source"]["location"],
        "arXiv:2401.01234, version 2",
        CLAIM["source"]["repository_commit"],
        f"Verdict for this claim: {verdict}",
        VERDICT_MEANING[PaperVerdict(verdict)],
        REPRODUCE.strip(),
        read_seal(d)["core_sha256"],
        f"within {REPLY_PERIOD_DAYS} days",
        "publish your reply next to the verdict",
    ):
        assert piece in text
    assert result.draft_sha256 == sha256_bytes(result.path.read_bytes())
    assert result.address_sha256 == sha256_bytes(EMAIL.encode("utf-8"))


def test_address_appears_only_in_the_to_line(tmp_path):
    d = sealed_dossier(tmp_path / "D1")
    text = write_reply_draft(d, contact(tmp_path), out_path(tmp_path)).path.read_text(
        encoding="utf-8"
    )
    assert text.count(EMAIL) == 1


def test_address_hash_is_plain_sha256_of_the_printed_address():
    assert address_sha256(f"  {EMAIL} ") == sha256_bytes(EMAIL.encode("utf-8"))


def test_every_verdict_has_a_meaning_matching_the_enum():
    assert set(VERDICT_MEANING) == set(PaperVerdict)


# Refusals -----------------------------------------------------------------------------------


def refusals(tmp_path):
    """(name, dossier, contact path, out path) for every refusal case."""
    cases = []
    good = sealed_dossier(tmp_path / "good")
    unsealed = tmp_path / "unsealed"
    w = DossierWriter(unsealed)
    w.write_text("claim.yaml", yaml.safe_dump(CLAIM))
    w.write_json("verdict.json", {"verdict": "FRAGILE"})
    w.write_text("REPRODUCE.md", REPRODUCE)
    w.finalize()
    cases.append(("unsealed", unsealed, contact(tmp_path), out_path(tmp_path)))
    tampered = sealed_dossier(tmp_path / "tampered")
    (tampered / "REPRODUCE.md").write_text("changed\n", encoding="utf-8")
    cases.append(("tampered", tampered, contact(tmp_path), out_path(tmp_path)))
    for name, override in (
        ("no-email", {"email": None}),
        ("not-an-address", {"email": "nobody"}),
        ("other-paper", {"arxiv_id": "2401.99999"}),
        ("other-version", {"version": "3"}),
        ("printed-at-with-address", {"printed_at": f"footnote: {EMAIL}"}),
        ("no-retrieved", {"retrieved_utc": None}),
    ):
        sub = tmp_path / name
        sub.mkdir()
        cases.append((name, good, contact(sub, **override), out_path(sub)))
    cases.append(("out-not-private", good, contact(tmp_path), tmp_path / "public" / "d.txt"))
    cases.append(("out-in-dossier", good, contact(tmp_path), good / "private" / "d.txt"))
    no_field = dict(CLAIM)
    no_field["source"] = {k: v for k, v in CLAIM["source"].items() if k != "repository_commit"}
    cases.append(
        (
            "claim-without-commit",
            sealed_dossier(tmp_path / "nofield", claim=no_field),
            contact(tmp_path),
            out_path(tmp_path),
        )
    )
    bad_verdict = sealed_dossier(tmp_path / "badverdict", verdict="SURVIVED")
    cases.append(("discovery-verdict", bad_verdict, contact(tmp_path), out_path(tmp_path)))
    broken = tmp_path / "broken-contact" / "private" / "c.json"
    broken.parent.mkdir(parents=True)
    broken.write_text(f"{{not json {EMAIL}", encoding="utf-8")
    cases.append(("broken-contact", good, broken, out_path(tmp_path)))
    return cases


def test_every_refusal_writes_nothing_and_never_shows_the_address(tmp_path):
    runner = CliRunner()
    for name, dossier, contact_path, out in refusals(tmp_path):
        with pytest.raises(ReplyDraftError) as refused:
            write_reply_draft(dossier, contact_path, out)
        assert EMAIL not in str(refused.value), name
        assert not out.exists(), name
        result = runner.invoke(
            app,
            ["reply-draft", str(dossier), "--contact", str(contact_path), "--out", str(out)],
        )
        assert result.exit_code == 1, name
        assert EMAIL not in result.output, name
        assert "example.org" not in result.output.replace("https://example.org", ""), name


def test_cli_prints_only_the_two_hashes(tmp_path):
    d = sealed_dossier(tmp_path / "D1")
    out = out_path(tmp_path)
    result = CliRunner().invoke(
        app, ["reply-draft", str(d), "--contact", str(contact(tmp_path)), "--out", str(out)]
    )
    assert result.exit_code == 0, result.output
    assert EMAIL not in result.output
    assert sha256_bytes(out.read_bytes()) in result.output
    assert address_sha256(EMAIL) in result.output
    assert "Dear authors" not in result.output


# W2.14 --------------------------------------------------------------------------------------


@pytest.mark.parametrize("verdict", list(PaperVerdict))
def test_template_has_no_words_about_people(verdict):
    claim = {
        "key": "K",
        "statement": "S",
        "arxiv_id": "1",
        "version": "1",
        "location": "L",
        "repository_url": "U",
        "repository_commit": "C",
    }
    text = render(claim, verdict, "0" * 64, "R", "e@x").lower()
    for word in FORBIDDEN_WORDS:
        assert word not in text, word
