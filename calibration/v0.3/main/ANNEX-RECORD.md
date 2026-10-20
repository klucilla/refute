# Annexes of the main-sample dossiers of v0.3

The public list that section 9.1, item 2 of [docs/plans/v0.3-plan.md](../../../docs/plans/v0.3-plan.md)
asks for: the SHA-256 of each annex's manifest (`ANNEX.json`), committed and pushed when the
annex is added. Each annex cites the hash of its dossier's sealed core
([SEAL-RECORD.md](SEAL-RECORD.md)). Comparing a dossier against this list shows an annex that
was replaced or removed; `refute check-dossier` checks each annex against its own manifest only.

## Independent reviews (section 10.3), primary reviewer

Reviewer: Claude Opus 5.5 (`claude-opus-5-5`), one fresh read-only session per dossier, with the
prompt for paper dossiers of [docs/reviewer-protocol.md](../../../docs/reviewer-protocol.md);
each received only its dossier and the reviewer protocol (the maintainer's decision of
2026-10-19). Added with `refute annex <dossier> review-opus <folder>` on 2026-10-20 (UTC).

| Paper | Annex | `ANNEX.json` SHA-256 | Assessment |
|---|---|---|---|
| 2302.12465 | `annexes/review-opus/` | `2ebca253a5e1ac785408a30c464a8d59de84de929de77744c6c6ffe7ac5274e3` | OBJECTIONS (6 minor) |
| 2305.19518 | `annexes/review-opus/` | `c733136101fb7983ed61f01f101f3b972d9a107b753e04de6d7db3038110f043` | OBJECTIONS (2 important, 6 minor) |
| 2407.11735 | `annexes/review-opus/` | `974bdfc147ead0933a594bc4205c86131f294d1556d331d5360852f567504e9a` | OBJECTIONS (2 important, 5 minor) |
| 2502.16782 | `annexes/review-opus/` | `7313772139904fe1897734205b761006f6e6de6174dfe038aa2e8c9bc9405f88` | OBJECTIONS (2 important, 2 minor) |

**2309.15704: held under the right of reply.** Its report discusses the cause of the run's
failure, whose analysis is under the right of reply of the protocol (section 9; #158). The
report is not attached or published before the reply period ends. Its bytes are fixed now by
their SHA-256: `e2e16a804a59ccd601f0027ab03617743a0c88558bc25ba6ead72a19d079e2f4` (9,039 bytes,
`review-opus.md`). It will be attached as `annexes/review-opus/` with these same bytes.

Objections never change a verdict (docs/reviewer-protocol.md, "What happens with objections").

## Independent reviews (section 10.3), second reviewer

Reviewer: Codex (another model family, decision D-20), one fresh read-only session per dossier.
It received the same task as the primary reviewer and nothing of the primary reviews. All five
dossiers were reviewed, because the protocol of the main sample did not fix the rule that draws
"1 dossier with no negative claim"; reviewing all five covers that requirement with no draw (the
maintainer's decision of 2026-10-19). Added with
`refute annex <dossier> review-codex <folder>` on 2026-10-20 (UTC).

| Paper | Annex | `ANNEX.json` SHA-256 | Assessment |
|---|---|---|---|
| 2302.12465 | `annexes/review-codex/` | `16a56f56159674c50ceefb6ee7be0cd77129aa756f90e77b529fa020af3ccfdf` | OBJECTIONS (3 important) |
| 2305.19518 | `annexes/review-codex/` | `b80995cb491cd88e2428e0da3336dfa1d3c2ac44581054e476d24a593f4795d5` | OBJECTIONS (3 important) |
| 2407.11735 | `annexes/review-codex/` | `6c3d3dd8dc5316f9701a1b4f06c1b244c3f73e4b6e5da2d36d345523b2e5f21a` | OBJECTIONS (3 important) |
| 2502.16782 | `annexes/review-codex/` | `8f73d42081d1f3c39e880082d3e4403f00cbb759ea3e361f7cad7ab0afce184d` | OBJECTIONS (2 important) |

**2309.15704: held under the right of reply**, for the same reason as its primary review: it
discusses the cause of the run's failure. SHA-256 of the held report (`review-codex.md`, 6,702
bytes): `c34c8724ab14255814be8813b26b805a8a9a189b347a6ce7f6c18f9aba5c2fd0`.

## Dossier verification (section 10.2, item a)

The report of `calibration/v0.3/verify_dossiers.py` at commit e5d4aed
([docs/validation/v0.3/dossier-verification-acceptance.md](../../../docs/validation/v0.3/dossier-verification-acceptance.md),
sections 1 to 4d), run with the frozen code of the locks on 2026-10-20 (UTC): `verification.md`
and `verification.json`. Added with `refute annex <dossier> verification <folder>`.

| Paper | Annex | `ANNEX.json` SHA-256 | Result |
|---|---|---|---|
| 2302.12465 | `annexes/verification/` | `0e4f199e510e8f0fc342153690b545972658dfc527d234f1bd791037466244aa` | VERIFIED |
| 2305.19518 | `annexes/verification/` | `527ee8cca8a15440eb1143fae8d7c35532ac89b2716a8af65a1bf1700126d860` | VERIFIED |
| 2309.15704 | `annexes/verification/` | `94f1612f96ffb79dd3c7d4aa50a609a231967c9219554aea2759e32c22b064e5` | VERIFIED |
| 2407.11735 | `annexes/verification/` | `2723f095ac8ab85dba66b6f6c20a54d1192b4d888e41f1f702a3b2a17ea88470` | VERIFIED |
| 2502.16782 | `annexes/verification/` | `242def66e64b5d106aada5da610de7325a73d4a88829a527071fadddb1896ee3` | VERIFIED |
