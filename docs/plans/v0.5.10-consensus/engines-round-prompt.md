You are reviewing, read-only, the plan for part (f) of the v0.5.10 phase of Refute (working tree
at C:\Projetos\refute). Do not edit anything. Never open K:\Meu Drive\Pessoal\Segurança. Answer in
English, at most about 100 lines.

## Scope of this round (the maintainer's decision of 2026-11-24, #218 comment 7136727624, item 3)

One round on the final charter BEFORE the first run, ONLY on part (f), the engine trial, and its
isolation: **supply chain, licences, exposure**. A blocking item is applied without a new round;
if a fix would change the phase's scope, say so explicitly (that is a stop for the maintainer).

## Read

- `docs/plans/v0.5.10-charter.md`, part (f) and sections 3, 5 (criteria 9 and 10) and 7.
- `docs/validation/v0.5.10/engines/README.md` (the isolation and the plan),
  `engines/requirements.in`, `engines/requirements.txt` (119 packages with hashes),
  `engines/licences.json` (declared licences of all 119, from PyPI).
- `docs/sources/engines-licences-2026-11-24.md`.
- For exposure: `docs/validation/v0.5.9/prototype-set.json`, the fetch units' manifests in
  `docs/validation/v0.5.9/prototype-units.json`, and CLAUDE.md, "Process diet 2", item 4.
- For data terms: `docs/data-publication.md`, `docs/third-party-data.md`.

## Questions

1. **Supply chain.**
   - Are the pins and hashes sufficient?
   - Is the 7-day rule met for every one of the 119 packages, not only the five tools? Check
     `--exclude-newer` against upload times where you can.
   - Is the `fbpca` sdist exception acceptable?
   - Is anything in the install or run plan able to fetch or execute code outside the pinned set
     (for example numba caches, pytransit or triceratops downloading data or code at run time,
     astroquery, lightkurve)?
2. **Licences.** Is the GPL handling compatible with the charter and with Refute's Apache-2.0
   licence?
   - LEO-Vetter: its driver is not committed.
   - TRICERATOPS: a committed driver imports MIT code that imports GPLv2 pytransit at run time.
   - Anything else in the 119 that matters (an unlicensed or unknown package, or a licence that
     forbids the planned use)?
3. **Exposure.** Does the plan keep to the 24 already-exposed TOIs and look at no new target?
   Think of TRICERATOPS's neighbour stars, TLS searching the whole light curve, and any engine
   that queries catalogs. Is re-fetching and checking against the v0.5.9 manifests correct? Is
   committing Gaia-derived probabilities (but no Gaia rows) compatible with the project's
   recorded data terms?
4. **Anything that would make an output look like a verdict, or that re-scores a recorded
   result,** contrary to Process diet 2, item 4.

Give a verdict (SURVIVED, WEAKENED or REFUTED), then numbered findings marked BLOCKING or
NON-BLOCKING, each with the file and line and the exact fix, and say for each blocking fix
whether it changes the phase's scope.
