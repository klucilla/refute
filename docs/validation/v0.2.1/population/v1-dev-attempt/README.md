# The failed v1 attempt at the development manifest (2026-10-12)

The record of the attempt that Amendment 4 describes ("What happened"): the v1 harness
(`population.py`, SHA-256 `408020676340322f4728ce3a8b4eecae505bfbec7ec34643ad9afed0e5a76225`)
generated the development population several times, hash only, in separate processes; the
manifests did not all agree. These generations are diagnostics: none is a frozen manifest and
none is ever approved retroactively. They consume no set of the development chain.

| File | SHA-256 | Content |
|---|---|---|
| `manifest-a.json` | `206d7af1c0618fab778c68b575d569ff8a9789bdaa61e8f8adbbeed86dcfcfc3` | generation A (24 workers, index order): differs from B in 2 of 5200 cases |
| `manifest-b.json` | `4073d96a0bce901a31241d5c2dd3d7b46192a4731a4ec3996ea1077039b833e9` | generation B (12 workers, `shuffle:20261012`): manifest B, the value repeated by B, A2, A3, B2 and D, the blocking reference of development campaign 1 |
| `generation-log.txt` | `6948c566c4e4e3d802ce4191b53822a0d1a78dffb5238fc184d68066e56a0fc5` | the v1 log of generations A and B |
| `D7-report.md` | `a254caf24c4deef09553ea6bb9c4ac84e2c8de6ef7af93755e96fc4a3efa20d5` | the diagnosis D7 of the divergence, translated from Portuguese |
| `D7-errata.md` | `d71ecbb343b75a6b601c4fee5a0341b5a160fc17cd3c724cf38af11c7caafc5e` | its errata, translated from Portuguese |

The manifests and the log are byte-identical to the files of the attempt (they contain no
user name; the paths `C:/Users/runneradmin/...` are the build paths recorded by the NumPy
wheel). The two D7 documents are English translations, line for line, of the maintainer's
diagnostic records `D7-relatorio.md` (SHA-256
`c603eb340edc44d5fd39fca02791066b5a010ee89e07d98b36d50568cdc6b192`) and `D7-errata.md`
(SHA-256 `43480ebef5b7a8f15b0724fca2b59871be76617cf560241217867ee6f19ebe07`), which are not
published; the line numbers cited in the errata refer to both the original and the
translation. The files they mention (`d3_compare.py`, `codex-D7.md`, `dev-gen-SHA256SUMS`,
the D2 runs) are diagnostic records, not published.
