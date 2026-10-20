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
