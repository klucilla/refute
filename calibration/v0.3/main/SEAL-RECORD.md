# Seal of the experimental cores of the main sample of v0.3

The record that section 9.1, item 1 of [docs/plans/v0.3-plan.md](../../../docs/plans/v0.3-plan.md)
asks for: the SHA-256 of a deterministic archive of each dossier's experimental core, and of the
set. Made on 2026-10-19 (UTC), with the maintainer's approval of the same day, by
`refute seal` (algorithm `refute-seal-1`, src/refute/core/seal.py at the frozen code f7601b9),
run once on each published dossier.

**What was sealed.** Exactly the published bytes: before each seal, `refute check-dossier`
confirmed every line of the dossier's `MANIFEST.sha256`; the seal added one new file,
`SEAL.json`, to each `dossier/` folder, and no existing byte changed (the core excludes
`SEAL.json` and `annexes/`). After the seal, `refute check-dossier` reports "core: intact
against its seal" for all five. The same core hashes came from sealing byte-identical copies
before the published folders were touched.

| Paper | Published dossier | Core SHA-256 | `SEAL.json` SHA-256 |
|---|---|---|---|
| 2302.12465 | `calibration/v0.3/main/dossiers/2302.12465/dossier/` | `d18e74776aa886de1ec271c3d31f40dc7f9001452b4aaca41031a674e20366f1` | `e3728066e54bbad2ca723f5b0458fab4d97d87c767ca8039569930ed69df3ddd` |
| 2305.19518 | `calibration/v0.3/main/dossiers/2305.19518/dossier/` | `e4f2ca2d352f66f33b48cf014936f8270625e4994d06f4ba72fc5689f4559435` | `b12b84ab3db8ad9ca19ab126510a90b17b46316ec464a13f68af820464c207da` |
| 2309.15704 | `calibration/v0.3/main/dossiers/2309.15704/dossier/` | `314ec1920c6fb593c4ecdb6b8582b891e0436d5fb522af265f7845b2541e7d3f` | `611ec6a51636902445d2574c686a9662aece304bb7056f029e2ce5bad610d05d` |
| 2407.11735 | `calibration/v0.3/main/dossiers/2407.11735/dossier/` | `dc84b305a59e2a3ea8ede04d0702412ed565f834ef616fdd2c20c896e43fb9cb` | `56639ef6f255b768fc3af524048b73233adb31afdced38ea0761d2e920b0081b` |
| 2502.16782 | `calibration/v0.3/main/dossiers/2502.16782/dossier/` | `490a819b6b2c1fb80cc3e3176887eb1f5ff2d7cd9b22fed42d39f81cbe43301c` | `6ee89d862a1682e50aa29bc84e50d357abc8c441220f3ba8d55ce3c5ceaa65d2` |

**The set.** `combined_sha256` (src/refute/core/seal.py) of the mapping whose keys are the
arXiv ids above and whose values are the core hashes:

`22814a7e0cb3d2a0f648d2da6dfe27096520302749e0610b91d7208c78a1fcb6`

The keys are the arXiv ids, not the folder names: every published folder is called `dossier/`,
and `refute seal` given the five folders at once would refuse the repeated name. To check:

```
uv run --frozen python -c "import json, pathlib; from refute.core.seal import combined_sha256; print(combined_sha256({a: json.loads(pathlib.Path(f'calibration/v0.3/main/dossiers/{a}/dossier/SEAL.json').read_text())['core_sha256'] for a in ['2302.12465', '2305.19518', '2309.15704', '2407.11735', '2502.16782']}))"
```

**Deviation from section 9.1 (recorded by the maintainer's decision of 2026-10-19).** Section
9.1 asks for the seal "when a locked run finishes", with its hash committed and pushed "at
once". The runs ended between 2026-10-19T15:13Z (2302.12465) and 2026-10-19T23:33Z
(2309.15704). The production dossiers were written without a `SEAL.json`, and the cores were
sealed only in this commit, after the five dossiers had been published in full (commits
ca2b7f1, ec29309, 33122ef, 48682b7 and 4d0e9c2). What fixes their bytes before the seal is
those commits and the `MANIFEST.sha256` SHA-256 recorded for each run on issue #158. This
record does not establish the "at once" timing retroactively.
