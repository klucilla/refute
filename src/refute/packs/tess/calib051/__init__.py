"""The v0.5.1 calibration (docs/plans/v0.5.1-plan.md, sections 5 and 6): the values the plan fixes
(C1', C2', C3' sizes as minimums, seeds, the two batteries), the version-3 plan paired with the
v0.4 compatibility plan, the paired tasks of C1', C2' and C3', and the version-3 claim writer.

Written before the calibration protocol (a mandatory stop): the pools of new stars and controls,
the drand rounds, the replacement and corrupted-run rules and the steps that read them are the
protocol's and are added after its approval; the packaging rehearsal
(``tests/test_v051_rehearsal.py``, acceptance row 5.4) runs again before the freeze.
``refute.packs.tess.calib05`` (the v0.5 calibration) is not changed: its task dataclasses are
hashed into the v0.5 run manifests that authenticate the v0.5 records."""
