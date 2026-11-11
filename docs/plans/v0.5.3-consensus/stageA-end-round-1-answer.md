**WEAKENED: the stop report preserves stage A’s main results, but needs the following corrections before approval.**

1. **Closing criterion reverses some targets.** “Point estimate below the requirement” would reject successful D4 results, including the cited 0.122 against ≤0.30. D1 also uses an upper limit, and D2 has additional rejection-rate conditions. Specify failure separately for each target. [README.md:182](C:/Projetos/refute/docs/validation/v0.5.3/stageA/README.md:182), [forecast_v4.py:249](C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_v4.py:249).

2. **Stage B’s fingerprint promise needs qualification.** Changing `src/` changes T2a’s computed fingerprint, even with the four named files untouched. Preserve the historical fingerprint through a frozen checkout and give stage B its own fingerprint. [README.md:157](C:/Projetos/refute/docs/validation/v0.5.3/stageA/README.md:157), [forecast_t2a.py:375](C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_t2a.py:375), [codehash.py:3](C:/Projetos/refute/src/refute/core/codehash.py:3).

3. **Acceptance cost is misattributed.** The cited 1,482–1,932 CPU-h covers **A0 alone**, not the complete schedules. The source table gives totals of 2,956–3,609 CPU-h, depending on sizing and rescaling. Label the component cost explicitly. [README.md:173](C:/Projetos/refute/docs/validation/v0.5.3/stageA/README.md:173), [budget.md:87](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budget.md:87).

4. **The blanket pre-run provenance claim omits the smoke exception.** The charged 0.059 CPU-h smoke ran unpinned and outside the ledger, and was already reported at the first implementation review. Disclose this exception alongside the universal review/procedure statement. [README.md:10](C:/Projetos/refute/docs/validation/v0.5.3/stageA/README.md:10), [ledger.json:4](C:/Projetos/refute/docs/validation/v0.5.3/stageA/ledger.json:4), [d2-bounds-round-1-answer.md:7](C:/Projetos/refute/docs/plans/v0.5.3-consensus/d2-bounds-round-1-answer.md:7).

5. **The `odd_even` range needs an exclusion.** The 0.97–1.0 statement must explicitly exclude planet 1075, which remained INCONCLUSIVE and reaches only 0.912. [README.md:48](C:/Projetos/refute/docs/validation/v0.5.3/stageA/README.md:48), [d2-bounds.json:353](C:/Projetos/refute/docs/validation/v0.5.3/stageA/d2-bounds.json:353).

Otherwise, reconciliation passed: counts, medians, thresholds, archive totals and **7.7830877 CPU-h** agree with the records. Cached shard hashes match. The bounds retain their assumptions and do not establish reachability; no draft infeasibility record follows.

Across all eight commits, no protected source, fingerprint file, earlier tracked record or v0.5.2 ledger changed. All stage A input paths traced to development material; (c3) has no execution artifacts. Stage B’s caps remain proposals and sum correctly to 150 CPU-h.

No workloads were rerun, no files changed, and the prohibited directory was not opened.