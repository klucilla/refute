"""The v0.4 pilot of ``refute discover`` for TESS (issue #177): the sampling frame and the
selection walk, deduplication, the funnel's promotion rule, injection-recovery, transformed
curves and their costs. Every function here is deterministic given its inputs; the network
is reached only through the query functions that the callers pass in, so the tests run
offline (CLAUDE.md). The values of the pilot protocol live in ``protocol.py``."""
