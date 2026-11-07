## Verdict: SURVIVED

Both round 2 objections are resolved in the current [comparison code](C:/Projetos/refute/docs/validation/v0.5.1/wp5/reproduce_dossiers.py). It checks canonical bytes after substituting only allowed values, and only allows `value` differences for the run identity and download-time fields. Added or removed fields remain regressions.

**Numbered objections:** None. No further change is required before proceeding.

## Run readiness

The sequence is viable, with the plan’s prerequisite steps:

1. **v0.2:** The current output, recorded dossier, cache, and run report are present. The `baseline` output is not present yet, so run that step before `compare`.
2. **v0.4 and v0.5:** Their preparation directories and the required archives are present. The current run outputs and baselines are not present yet, so run those steps before each comparison. The archive hashes match the values recorded in the script.
3. Follow the plan’s stop rule: stop at the first regression.

I did not run any reproduction or comparison steps. The artifact presence and archive hashes are read-only checks; they do not establish comparison results. The project guidance also treats reproduction evidence as distinct from method validation.【C:\Projetos\refute\ROADMAP.md】

