You are Codex, the project's second agent for verdict and validation, in a read-only sandbox. Repository: C:\Projetos\refute at main 4a704f0f ("v0.5.8 closed, gate WEAKENED"). Do not write, edit, commit, run downloads or contact the network. Never open K:\Meu Drive\Pessoal\Segurança. You may read any file under C:\Projetos\refute and run read-only commands (git log/show/grep, reading JSON with the project's .venv Python in isolated mode, without writing files).

## Task
One review round (design decision, no lock yet) of a plan for the NEXT phase of Refute. The plan was written by an independent read-only Claude Fable 5.2 session that did not build any earlier phase. It is in Brazilian Portuguese:

C:\Projetos\refute\.cache\v059\plan-review\fable-plan.md (SHA-256 dc5756a4169cebe47441e6dea75122f90670727bfe59615536eef5985fc71386)

Summary: open v0.5.9 "Ephemeris entry" = battery discovery.version 5 in src/ (TOI ephemeris as entry with a bounded, declared refit; simulation seed independent of the fit; output valid only if its class is the same under six declared perturbations, else INCONCLUSIVE; centroid_v5 guards so numeric failures become INCONCLUSIVE, never ERROR; version 2 byte-identical). Stage 0 exploratory; synthetic acceptance S1-S8 written before code; part A exploratory on 108 exposed TOIs with doors P1-P4; part B confirmatory under a lock and drand round on 600 unexposed PCs of the confirmation half: primary criterion Wilson 95% upper bound of E-vs-S class flips <= 0.10, decidability guard >= 0.10, minimum denominator 60.

## Check, against the repository (cite path:line)
1. Gate: is advancing allowed under ROADMAP's amendment of 2026-11-21, and under which case?
2. Facts and recounts in the plan: the pool counts (197 / 44 / 2,098 PCs; part-b-exposure.md), the v0.5.8 cause split (group A 7 TOIs with seeded SNR > 10% lower; group B 6 near-identical fits, 4 in systematics.background), the 5 ERROR runs and their causes, and the claimed minor error in docs/reports/v0.5.8-report.md:105 (12 vs 13 SNRs lower). Say which hold, which are wrong.
3. Design soundness: is the src/ change list (section 4) complete and minimal for the question? Can the tests run on a fixed ephemeris without touching more code than listed? Does the new `entry` section risk leaking into the resolved dump of old claims (claim hash of existing locks; issue #30)? Are the perturbation sizes justified by the fit's own resolution?
4. Claim design (section 3): is it well posed and non-circular? Denominator, flip definition (S runs only when E is decided; is that asymmetric or biased?), primary 0.10, guard 0.10, minimum 60, stop rule at 200 TOIs reading only the decided count. Is a stability claim on PCs a good use of the unexposed pool, given the later prospective second reading of PCs?
5. Process: does the plan satisfy CLAUDE.md (exploratory vs confirmatory, Codex rounds, blind review for rule changes, every rerun approved in an issue before it runs, dependencies planned before the lock, no old verdict or lock changes)?
6. Proportion: budget 56 CPU-h (cap 95), 224 GB downloads, 7 maintainer stops, 2 Claude subagents. Is there a smaller phase that answers the same question with the same rigour? If yes, describe it concretely.
7. The three open decisions in section 11 (phase format; claim targets; consensus as rule or as label): give your recommendation for each, with one-line reasons.

## Answer format (English, concise, at most ~150 lines)
- OVERALL: SURVIVED / WEAKENED / REFUTED (for the plan as a design).
- BLOCKING items (numbered, each with path:line evidence and the exact change).
- NON-BLOCKING items.
- Fact check table: claim | holds? | evidence.
- Decisions 1-3: your choice and reason.
- A smaller alternative, if any.
Do not soften; if something is wrong, say so.
