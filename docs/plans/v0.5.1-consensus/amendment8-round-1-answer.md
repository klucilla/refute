## A. Amendment 8, round 1

**Verdict: WEAKENED.** The maintainer’s comparison decision is preserved. The plan and acceptance wording largely agree, but the implementation does not yet guarantee several stated conditions.

1. **Important, tag import is not fully protected.** `baseline()` verifies the tag commit and checks `refute.__file__`, but its Git status check uses `--untracked-files=no`. An untracked file under `src/` could shadow a tag module while the top-level package still appears to come from the worktree. The inspected worktree is at `b6249b5` and showed no status entries, but the guard would not detect such files. **Change required:** reject untracked files that could be imported from `src/`, and verify loaded `refute.*` modules resolve under the tag worktree, or verify the imported source tree against the tag’s tracked tree. Evidence: [reproduce_dossiers.py](/C:/Projetos/refute/docs/validation/v0.5.1/wp5/reproduce_dossiers.py:489).

2. **Important, the project virtual environment is not enforced.** The inspected tag worktree is at the required commit. Its `uv.lock` differs from the project lock only in Refute’s own package version line, consistent with using the project environment. But `baseline` uses whichever interpreter invokes the script; the code and instructions do not require or check the project venv. **Change required:** specify the exact project-venv invocation and check `sys.executable` and installed dependency versions before analysis. Evidence: [runner instructions](/C:/Projetos/refute/docs/validation/v0.5.1/wp5/reproduce_dossiers.py:53), [baseline implementation](/C:/Projetos/refute/docs/validation/v0.5.1/wp5/reproduce_dossiers.py:479).

3. **Important, “nothing is written into the worktree” is not enforced.** `sys.dont_write_bytecode` prevents Python bytecode writes. The task’s dossier output is directed outside the worktree, and the inspected code path shows no intended worktree output. That does not make the worktree read-only or prevent other runtime writes. **Change required:** run with the tag worktree made read-only and direct runtime caches outside it. Evidence: [baseline setup](/C:/Projetos/refute/docs/validation/v0.5.1/wp5/reproduce_dossiers.py:496).

4. **Important, the allowed timestamp comparison is broader than the decision.** `is_download_time()` allows every JSON path ending in `.retrieved_utc`, without establishing that the value belongs to data downloaded that day. **Change required:** allow only identified download timestamp paths and verify each against the current run’s downloaded inputs. The exact run-identity paths are constrained correctly. Evidence: [comparison helpers](/C:/Projetos/refute/docs/validation/v0.5.1/wp5/reproduce_dossiers.py:581).

5. **Important, the commit-of-origin lookup is only a candidate.** `git log -S <key name> -- src/` finds the oldest source change containing that string, which can be unrelated to adding that serialized field. It does not verify the origin recorded on #213. **Change required:** report this as an unverified candidate, then map each affected output key to the commit that actually introduced it and verify that commit against #213. Evidence: [key_origin()](/C:/Projetos/refute/docs/validation/v0.5.1/wp5/reproduce_dossiers.py:601).

6. **Minor, the “clean checkout” check omits untracked files.** This overlaps objection 1, but also makes the error message stronger than the check warrants. **Change required:** use a full status check and state precisely which files may be present. Evidence: [baseline status check](/C:/Projetos/refute/docs/validation/v0.5.1/wp5/reproduce_dossiers.py:489).

7. **Minor, the check-dossier reporting link is implicit.** Acceptance row 5.2 asks for the `check-dossier --against` result. The existing `run` step records the `check_dossier` result, while the new `compare` report does not include or validate it. The reports can be read together, but the amendment does not identify that linkage. **Change required:** name the `run` report as the source of that result, or include it in the comparison report. Evidence: [amendment 8](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:603), [acceptance row 5.2](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:502).

The ordering and stop rule are coherent in the plan. The runner itself permits invoking versions and steps out of order, so following the plan’s sequence remains an operational requirement. **No reproduction step was run.**

## B. Estimate from the recorded v0.2 outputs

**Estimate: 3 changed, 14 unchanged, 3 undecidable.** No SURVIVED/WEAKENED/REFUTED audit verdict applies to this estimate. It is derived only from the 20 recorded verdicts and current rules, with no reruns.

The principal uncertainty is that the recorded holdout rounds do not include `train_validity.hidden_window_fraction`. For candidates that pass the logged SNR and duration checks, the outputs therefore cannot establish whether the hidden-window rule would reclassify a failed round.

**Changed, 3**

- **TIC-158561566:** Recorded verdict REFUTED solely for fatal `eb_catalog`. Its output records an own-TIC TESS-EB period match at factor 1.0, with no other period match. Under the current same-photometry default, this becomes a warning, so the verdict changes to WEAKENED.
- **TIC-317507345:** Same evidence pattern as TIC-158561566. The fatal `eb_catalog` match is downgraded, changing REFUTED to WEAKENED.
- **TIC-48506505:** Recorded verdict REFUTED solely for `holdout_by_year`. Its failing round has train SNR 7.0518, below the recorded 7.1 gate, and duration/period 0.8371, above 0.2. The new rule makes that round INCONCLUSIVE; the other recorded rounds pass, so the old holdout failure is removed. The verdict changes from REFUTED.

**Undecidable, 3**

- **TIC-118327550:** REFUTED solely for a holdout failure. The failing round’s logged train SNR and duration/period pass the new checks. The record omits hidden-window fraction, so it cannot establish whether that failure remains or becomes INCONCLUSIVE.
- **TIC-194736418:** REFUTED solely for holdout. The 2023 failing round has train SNR 20.9995 and duration/period 0.0329, both within the new limits; its hidden-window fraction is absent. The outputs do not decide whether the verdict changes.
- **TIC-315755496:** REFUTED solely for holdout. Its failing round’s logged SNR and duration/period pass the new checks; the missing hidden-window fraction leaves the outcome undecidable.

**Unchanged verdict, 14**

| Dossier | Recorded verdict | Why the verdict stays the same |
|---|---|---|
| TIC-139528693 | WEAKENED | Holdout passes; no EB match recorded. |
| TIC-151825527 | SURVIVED | Holdout passes; no EB match recorded. |
| TIC-154459165 | REFUTED | Holdout may change, but `centroid_shift` remains fatal. |
| TIC-158588995 | SURVIVED | Holdout passes; no EB match recorded. |
| TIC-158916431 | REFUTED | `centroid_shift` and `aperture_depth` remain fatal. |
| TIC-19028197 | SURVIVED | Holdout passes; no EB match recorded. |
| TIC-193754373 | WEAKENED | Recorded warning is `nearby_contamination`; holdout passes. |
| TIC-197650870 | REFUTED | Holdout may move from PASS to INCONCLUSIVE because both logged duration ratios exceed 0.2, but `plausibility` and `period_alias` remain fatal. |
| TIC-231670397 | SURVIVED | Holdout passes; no EB match recorded. |
| TIC-294179389 | WEAKENED | Recorded warning is `nearby_contamination`; holdout passes. |
| TIC-316916655 | REFUTED | Its own-TIC TESS-EB match is downgraded, but `odd_even` and `centroid_shift` remain fatal. |
| TIC-33153766 | REFUTED | `centroid_shift` and `aperture_depth` remain fatal. |
| TIC-350445771 | REFUTED | Its own-TIC TESS-EB match is downgraded, but `secondary_eclipse` remains fatal. |
| TIC-374200604 | INCONCLUSIVE | Holdout is already inconclusive; no EB match recorded. |

These counts describe verdict changes, not every possible test-status change. For example, TIC-197650870’s holdout status may change while its verdict remains REFUTED. The recorded index and verdicts are in [index.json](/C:/Projetos/refute/.cache/v051/wp5/b/v02-all/index.json); the reviewed current defaults are in [params.py](/C:/Projetos/refute/src/refute/packs/tess/params.py).

