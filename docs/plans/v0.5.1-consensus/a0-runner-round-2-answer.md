## Verdict: WEAKENED

Five round 1 objections are adequately resolved in the answers and current code: freeze checks guard seed use, A0.2 will measure both estimators separately, the lag estimator is tied to the stated segment grid with its missing-pair fraction reported, A0.8 follows the battery’s red-noise branch inputs, and failed units retain processor time. The current design document still needs to record the A0.2 and A0.8 clarifications.

One issue remains that could make the runner fail A0.3 on valid windows.

## Remaining objection

1. **High, exact-boundary cadence overlap.**  
   **Evidence:** A0 requires a regular grid spaced `2h` apart with no shared cadence ([acceptance text](</C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:102>)). The generator rejects overlap only when centre distance is **less than** `2h` ([`a0.py`](</C:/Projetos/refute/src/refute/packs/tess/a0.py:106>)). At exact equality, adjacent window intervals touch. The box estimator includes both endpoints: it selects through `centre + outer` and includes the left endpoint too ([`a0.py`](</C:/Projetos/refute/src/refute/packs/tess/a0.py:320>)). With the design’s duration and cadence, `h = 0.2 d`, which is 144 two-minute cadences, so the grid spacing is 288 cadences. An exactly aligned cadence at a shared endpoint can therefore be used by both windows. The same equality issue applies to the event and phase-0.5 overlap filters.

   **Exact change required:** Before the run, define and implement a consistent endpoint rule that gives each boundary cadence to at most one window, or change the grid/window convention so cadence-index sets are disjoint. Keep A0.3’s independent cadence-index check. An assertion alone is insufficient: it would detect the conflict but leave the acceptance requirement unmet.

## Readiness

This is the only technical blocker I found for writing the runner. Before its first run, also update the design’s A0.2 and A0.8 descriptions to match the accepted separate estimator measurements and the battery’s own error inputs. The runner itself is not present yet, so its wiring cannot be reviewed. I made no file changes and ran no tests. The current `git status` also shows `common.py` as untracked.

