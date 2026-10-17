# Pilot triage, additional round 6561628

Under `calibration/v0.3/pilot/PROTOCOL.md` (commit `d7dfc40`), on the draw of
`pilot_draw_additional.json` (commit `80abc00`): round 6561628, the first published at
least one hour after the push run of the triage commit `2f0146a` (run 39075388034, created
2026-10-17T22:30:57Z). Metadata and README only. **No code was run.** The agent proposed
each decision with its evidence on 2026-10-17; the maintainer approved them on 2026-10-17
(about 23:45 UTC, in the working conversation), and decided how the development papers are
chosen instead (plan 4.5, note of 2026-10-17: the accepted papers in positions 6 and 7 of
the main walk).

## Mechanical rejections (the script)

16 papers: `category_outside_list`: #1 2402.18152 eess.IV; #2 2304.13989 cs.CL;
#3 2403.17692 cs.CV; #5 2312.00507 cs.PL; #6 2407.05244 cs.AI; #7 2506.07982 cs.AI;
#8 2505.13307 cs.CL; #9 2301.11916 cs.CL; #10 2310.14870 cs.CL; #11 2412.17210 cs.CV;
#12 2403.10289 stat.ME; #13 2504.04537 cs.SE; #14 2306.03651 cs.SI; #16 2403.14514 math.DS;
#18 2501.08049 cs.AI; #20 2501.03765 cs.CV. (cs.AI is outside the pilot's list; the
adjustment `add-cs-ai` applies to the main protocol only.)

## Pilot triage of the other 4 (metadata and README)

| # | arXiv | Decision | Reason | Evidence |
|---|---|---|---|---|
| 4 | 2402.11922 (cs.LG) | rejected | `no_license` | `license_spdx` null; the README (145 lines) states no license or authorization; no license-like file at the repository's root (`.gitignore`, `Data`, `GPD`, `Pretrain`, `README.md`, `assets`, `requirements.txt`) |
| 15 | 2504.05490 (cs.LG) | rejected | `no_license` | `license_spdx` null; the README states no license; root: `.gitignore`, `README.md`, `example`, `src` |
| 17 | 2410.20483 (cs.LG) | rejected | `no_license` | `license_spdx` null; the README (87 lines) states no license; root: `Data`, `Experiments`, `README.md`, `SEV`, `Scripts`, `requirements.txt` |
| 19 | 2412.20193 (cs.LG) | rejected | `no_license` | `license_spdx` null; the README (64 lines) states no license; root: `README.md`, `collect_d4rl.py`, `hyperparam.yaml`, `ilmar`, `requirements.txt`, `run.sh`, `train_expert.py`, `train_imitation.py`, `weights` |

**Provisional acceptances of the additional round: 0 of 20. Development papers: 0.**

With the first round (0 development papers), the pilot gives none of the 2 development
papers the plan needs (D-3). By plan 4.5 ("if that is still not enough, the phase stops
for the maintainer's decision") the phase stops here for the maintainer's decision.

## Rejection profile of the additional round

`category_outside_list` 16; `no_license` 4.

## Both rounds together (40 papers)

`category_outside_list` 31; `no_license` 7; `data_requires_registration_or_terms` 1;
`requires_gpu` 1 (at the full triage).
