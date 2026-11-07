## Verdict: SURVIVED

**Numbered objections:** None. I found no supported correctness bug or rule break in the reviewed range.

The version 3 checks are isolated: `schema.py` expects the v0.5 roles for versions 2 and 3, while the additional missing-role refusal in `params.py` applies only to version 3. The differential tests compare earlier-plan outputs against the v0.5.0 code on the same machine, including verdicts, reports, errors, cases and the paired chain. Evidence: [schema.py](/C:/Projetos/refute/src/refute/packs/tess/schema.py:70), [params.py](/C:/Projetos/refute/src/refute/packs/tess/params.py:499), [test_v051_wp5.py](/C:/Projetos/refute/tests/test_v051_wp5.py:40).

The rehearsal exercises the claim writer, lock and verification, offline CLI run, and one task path for each calibration component. The C2 and C3 task bodies follow their v0.5 counterparts while pairing the v0.4 plan with the version 3 plan. The cross-platform assertions avoid comparing numeric measurements. Evidence: [claim.py](/C:/Projetos/refute/src/refute/packs/tess/calib051/claim.py:43), [tasks.py](/C:/Projetos/refute/src/refute/packs/tess/calib051/tasks.py:100), [test_v051_rehearsal.py](/C:/Projetos/refute/tests/test_v051_rehearsal.py:132).

The reproduction script’s documented `run`, `baseline`, and `compare` steps check the dossier, use the recorded claim and attachments, analyze the fetched inputs, and classify differences against both the tag and recorded dossier. The v0.1 and v0.2 outcomes and amendments 7 and 8 are accepted review constraints, not objections here. Evidence: [reproduce_dossiers.py](/C:/Projetos/refute/docs/validation/v0.5.1/wp5/reproduce_dossiers.py:365), [reproduce_dossiers.py](/C:/Projetos/refute/docs/validation/v0.5.1/wp5/reproduce_dossiers.py:520), [reproduce_dossiers.py](/C:/Projetos/refute/docs/validation/v0.5.1/wp5/reproduce_dossiers.py:709).

**Execution note:** This was a read-only source review. I did not run tests or reproduction scripts.

