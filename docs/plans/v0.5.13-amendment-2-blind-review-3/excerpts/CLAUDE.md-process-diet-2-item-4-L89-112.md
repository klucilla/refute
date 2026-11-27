4. **Exploration and reruns.** Within the charter and all applicable stops, explore on synthetic
   development data or on public data already exposed. A public target not yet exposed may be
   looked at only inside a pool the charter names; the choice and its reason are logged, and from
   then on it is exposed and unusable for confirmation. Without a higher cap in the charter,
   exploration stays within 5 CPU-h and 20 GB of downloads per phase, cumulatively; above 5 CPU-h
   the caps ledger applies. A rerun is any execution that gives a case a new value of an output it
   already has on record (a test status, class, score, door or criterion), on all or part of a
   recorded run's cases, including failed or incomplete ones, whatever the code, seed, threshold,
   input or entry mode. Every rerun needs issue approval of its reason and exact procedure before
   it runs, in the charter or later. A reviewer's read-only recount, `refute verify` and
   `refute check-dossier` are verification, not reruns. A new diagnostic may reuse exposed data
   without that approval only if (i) it yields a quantity no recorded run yielded for those
   cases, (ii) its question, quantity and cases are logged before it runs, and (iii) its result
   replaces or re-scores no recorded result and is reported beside it as exploratory and post
   hoc. In doubt, it is a rerun. The runner writes one append-only log per phase: before each
   run, the question and choices with a machine timestamp; after it, provenance, coverage and
   every outcome, including failures and abandoned attempts. The phase report links that log.
   Label outputs `exploratory` and carry applicable limits. Use findings only to generate
   hypotheses. Claims, acceptance and verdicts require locked, pre-registered confirmation on
   targets or data that are unexposed and did not inform the choices, or on prospective data; a
   claim that follows a failed or weakened one on the same question cites every earlier attempt
   in its pre-registration. No holdout, hidden window or reserved confirmation set is read before
   its own lock reveals it, whether its phase is open, paused or closed. Preserve the original
   results and stop decisions.
