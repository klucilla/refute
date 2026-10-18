# Sources of the licence statements in the selection log

Each record gives the source URL, the time it was read and the literal value read
(CLAUDE.md, rule of issue #34). The GitHub records below are the fields that
`select_main.py` extracted from the GitHub API answers and stored in the committed
batch file named (the licence GitHub reports and the names at the root); the full
answers are not stored.

| Pos | arXiv | Source URL | Read (UTC) | Literal value read | Batch file |
|---|---|---|---|---|---|
| 2 | 2310.05250 | https://api.github.com/repos/lucianoAvinas/lowrank-gnn-kernels | 2026-10-18T00:53:55Z | `license_spdx: null; licence-like root names: []` | main_walk_batch_01.json |
| 3 | 2506.00577 | https://api.github.com/repos/MasterZhou1/Recon | 2026-10-18T00:53:55Z | `license_spdx: null; licence-like root names: []` | main_walk_batch_01.json |
| 5 | 2305.00604 | https://api.github.com/repos/Felix-Petersen/isaac | 2026-10-18T00:53:55Z | `license_spdx: "MIT"; licence-like root names: ["LICENSE"]` | main_walk_batch_01.json |
| 7 | 2504.01550 | https://api.github.com/repos/AIM-Intelligence/RepBend | 2026-10-18T00:53:55Z | `license_spdx: null; licence-like root names: []` | main_walk_batch_01.json |
| 10 | 2501.18768 | https://api.github.com/repos/michael-s-yao/DynAMO | 2026-10-18T00:53:55Z | `license_spdx: "MIT"; licence-like root names: ["LICENSE"]` | main_walk_batch_01.json |
| 18 | 2405.07414 | https://api.github.com/repos/kyungeun-lee/tabularbinning | 2026-10-18T00:53:55Z | `license_spdx: null; licence-like root names: []` | main_walk_batch_01.json |
| 20 | 2505.11298 | https://api.github.com/repos/RPaolino/GenVsExp | 2026-10-18T00:53:55Z | `license_spdx: null; licence-like root names: []` | main_walk_batch_01.json |
| 32 | 2305.08676 | https://api.github.com/repos/IBM/TRAIL | 2026-10-18T00:56:07Z | `license_spdx: "Apache-2.0"; licence-like root names: ["LICENSE"]` | main_walk_batch_02.json |
| 41 | 2305.16886 | https://api.github.com/repos/eliacunegatti/mge-snn | 2026-10-18T00:56:07Z | `license_spdx: "Apache-2.0"; licence-like root names: ["LICENSE"]` | main_walk_batch_02.json |
| 44 | 2301.13139 | https://api.github.com/repos/c-alfano/Approximate-Mirror-Policy-Optimization | 2026-10-18T00:56:07Z | `license_spdx: null; licence-like root names: []` | main_walk_batch_02.json |
| 72 | 2401.15973 | https://api.github.com/repos/HamedHemati/OMSI | 2026-10-18T00:58:17Z | `license_spdx: null; licence-like root names: []` | main_walk_batch_03.json |
| 74 | 2408.16725 | https://api.github.com/repos/gpt-omni/mini-omni | 2026-10-18T00:58:17Z | `license_spdx: "MIT"; licence-like root names: ["LICENSE"]` | main_walk_batch_03.json |

## Other sources

| For | Source URL | Read (UTC) | Literal value read |
|---|---|---|---|
| 32 (TRAIL data source): licence field | https://api.github.com/repos/zsoltzombori/plcop | 2026-10-18T03:44:36Z | `{"default_branch":"master","license":null}` |
| 32 (TRAIL data source): root names | https://api.github.com/repos/zsoltzombori/plcop/contents | 2026-10-18T03:44:36Z | `.gitignore, .gitmodules, README.md, Tensorflow_models, ablations.sh, ablations_continued.sh, baseline.sh, compare.sh, convert_input.pl, count.sh, count_slowdown.sh, dagger.sh, dagger_loop.sh, def_mm.pl, distcompare.py, embed.pl, entropycount.py, eval.pl, eval_policy.pl, features.pl, foreign, gnn, hashtbl, ini, leancheck, leancop21_swi.pl, leancop_main.pl, leancop_proof.pl, leancop_step.pl, leancop_tptp2.pl, mcts.sh, mizar40.sh, montecarlo.pl, montecarlo.py, montecarlo.sh, montecarlo_aux.pl, montecarlo_dir.sh, mptp2078b.sh, params.py, params_parse.py, produce_leancop_proof.pl, pyswip, test.pl, theorems, train.py, train_xgboost.py, util.py, xgboost_test.py (48 names)` |
| 74 (Mini-Omni weights size) | https://huggingface.co/api/models/gpt-omni/mini-omni/tree/main | 2026-10-18 (about 01:05) | `"size":2777267002,"lfs":{...},"path":"lit_model.pth"` |
