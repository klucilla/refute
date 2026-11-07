## Amendment 8

**Verdict: WEAKENED.** The plan’s comparison decision and run order are coherent. The seven round 1 objections are addressed in the plan and script, but two gaps in the comparison logic still block relying on it for the planned run.

1. **Important, comparison (a) checks parsed JSON equality, not byte equality.** The script computes differences from decoded JSON at [reproduce_dossiers.py](/C:/Projetos/refute/docs/validation/v0.5.1/wp5/reproduce_dossiers.py:713). If the only change is whitespace, key order, or another serialization difference, `a_regressions` stays empty even though the plan requires byte identity outside the exceptions. **Change required:** compare the serialized outputs while permitting changes only to the specified field values, and treat any other byte difference as a regression.

2. **Minor, the run identity exemption also accepts a missing field.** The `RUN_IDENTITY` path check accepts any difference at those paths, including a field present in one output and absent in the other. The plan permits differences in the identity fields’ values, not their removal. **Change required:** allow only value differences when both paths exist; classify field addition or removal as a regression.

The round 1 fixes otherwise look resolved: the baseline uses archived tag code and checks loaded module origins; checks the project interpreter and lock; uses the run’s cache offline; shares the same `context_for`; restricts timestamp exceptions to retrieval values found for that target; labels origin lookup as an unverified candidate; and includes the `run` report’s `check-dossier --against` result in the comparison report. The observed `sys.path[0]` check supports the import approach. See the plan’s implementation description and sequence at [v0.5.1-plan.md](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:613) and the report assembly at [reproduce_dossiers.py](/C:/Projetos/refute/docs/validation/v0.5.1/wp5/reproduce_dossiers.py:752).

**Run order:** coherent as written: v0.2 comparison (a), then v0.4 and v0.5, stopping at the first regression. I did not run any reproduction step. Fix the two comparison gaps before relying on these steps.

## Question B estimate

The revised estimate is **3 changed, 15 unchanged, 2 undecidable**. That is consistent with the additional observation: TIC-194736418 was rerun with current code, stayed REFUTED for the same reason, and therefore moves from undecidable to unchanged, with one observed result. The remaining two undecidable dossiers are TIC-118327550 and TIC-315755496.

