# The counts of 2302.12465 before the lock

Committed before the claim file is written (the maintainer's decision of 2026-10-19, item 3:
count K twice, once per dataset name, and N with the dgl reader; only the integer K is read,
no AUROC).

## K: the population counted before the lock (W3.12f)

`population_count_record.json` (the dataset entry "UserItemAttr (synthetic,
datasets/synthetic)") and `population_count_record_comparison.json` (the entry
"UserItemAttr"): canonical JSON, format `refute-ml-population-count-1`, each written by
`scripts/vm/count_population.py` at Refute `5039bdc5f4e1799cbbf40d111c361783827b1d62`
(wp3-population-count-acceptance.md; wp3-repository-weights-acceptance.md). Each ran the
count script `../population_count.py` (SHA-256
`edae1ced3336732c2173554019c5219c2aa7dfa46b9f7beefb2d16e824d44ee6`) twice, in independent
containers of the claim's environment, and kept only the line
`refute-population-count <K>`:

| Record | K | Runs (UTC) |
|---|---|---|
| `population_count_record.json` | 129 | 12:09:53-12:10:00 and 12:10:00-12:10:07, 2026-10-19, both 129 |
| `population_count_record_comparison.json` | 129 | 12:10:08-12:10:15 and 12:10:15-12:10:22, 2026-10-19, both 129 |

The two K are equal and not 0. (A first pair of records, made at `c820bb6` at 12:00Z with the
same K in all four runs, was replaced: Codex's review of the code asked the record to name,
in its `weights` field, the weights the count's containers read from Refute's verified copy,
and a claim now binds only with that field.) The environment: the clone at
`cdb7160f9a2fd90bded8cefa8f591f9a0e47ee6c` with the two allowed patches, the engine's base
image, the rung `requirements_compiled` (its build on the VM at 2026-10-19T11:41:31Z, exit
0, through the allowlist proxy in the profile build), no network, the profile pull. Each
record's `configuration` binds the files the selection reads: `datasets/synthetic` and the
repository's trained link predictor `saved_models/synthetic_model.pth`, which the two count
containers read from Refute's copy verified as a regular blob of the commit and mounted
read only. The specs given to the count are `count_spec_value.json` and
`count_spec_comparison.json`.

## N: the edges of the file's split

`likes_edges_record.json`: the edges of the canonical type `user,likes,item` in
`datasets/synthetic` (SHA-256 `a368d8f6...`, 93,724 bytes): **714**, counted by the engine's
dgl container reader (`src/refute/packs/ml/container_reader.py`, SHA-256 `4b64c5ed...`) in
the same image, as a production reader runs (a fresh folder holding the reader only, the
dataset's checked copy mounted read only, no network), by `count_likes_edges.py` (this
folder, SHA-256 `b7b29293b4ea769d97bccca9aa79119b19bdd46554b524f5bb175b2076c61b77`) at Refute
`c820bb6`, on 2026-10-19T12:02:07Z, exit 0. (A first run at 11:48:17Z, by an earlier form of
the same script, also gave 714; its bytes did not pass ruff, so the committed script was run
again.)
