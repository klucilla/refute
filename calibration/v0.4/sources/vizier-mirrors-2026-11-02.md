# Source for the VizieR servers of `reproduce_inputs.py` (read 2026-11-02)

`calibration/v0.4/reproduce_inputs.py` asks these VizieR servers for the TESS-EB table, in this
order: the CDS, then the CfA, IDIA, NAOJ and China-VO mirrors. The list and the order were set by
the maintainer on 2026-11-02 (#177). The URLs come from VizieR's own mirrors page, recorded here.

## M1. VizieR mirrors page, served by the IDIA mirror (live)

- URL: https://vizier.idia.ac.za/vizier/mirrors.gml (the CDS copy,
  https://vizier.cds.unistra.fr/vizier/mirrors.gml, did not answer: the CDS incident of L9 in
  [data-licenses-2026-11-01.md](data-licenses-2026-11-01.md)).
- Read 2026-11-02T19:21:59Z: 8022 bytes, SHA-256
  `c8d97b690f9e73a3da92fe85136bf54baeaf961351082c8d0407ef38128c15c3`.
- Excerpt: "The VizieR service is installed on a set of countries and universities listed bellow."
- The active entries (the CADC, Cambridge and JAC entries are commented out in the HTML) link to:
  - "VizieR at CDS": `https://vizier.cds.unistra.fr/`
  - "VizieR at ADAC": Tokyo, Japan: `http://vizier.nao.ac.jp/vizier/`
  - "VizieR at IUCAA": Pune, India: `https://vizier.iucaa.in/vizier/`
  - "VizieR at INASAN": Moscow, Russia: `https://vizier.inasan.ru/vizier/`
  - "VizieR at NAOC": Beijng, China: `http://vizier.china-vo.org/vizier/`
  - "VizieR at CFA Harvard": Cambridge, USA: `https://vizier.cfa.harvard.edu/vizier/`
  - "VizieR at IDIA": IDIA, South Africa: `http://vizier.idia.ac.za/vizier/`

## M2. The same page at the CDS, archived capture of 2026-08-15

- URL: http://web.archive.org/web/20260815011737/https://vizier.cds.unistra.fr/vizier/mirrors.gml
- Original bytes (`id_` form), downloaded 2026-11-02: 7919 bytes, SHA-256
  `4e90c79d2986e9f93bd7dd4f4fe864fcebc6cd12953a9dd113d3d733610bb965` (base32 SHA-1
  `Q2LLYXWT2R5H5BP3IL2GWY6OYXEDJTWQ`, the Wayback index's digest for this capture).
- Same active entries as M1. Two schemes differ: it links the CDS as `http://` and IDIA as
  `https://`.

## The servers used, and their schemes

| Order | Server | Base used | Why this scheme |
|---|---|---|---|
| 1 | CDS | `https://vizier.cds.unistra.fr` | M1; the URL of `inputs.json` |
| 2 | CfA | `https://vizier.cfa.harvard.edu` | M1, M2 |
| 3 | IDIA | `https://vizier.idia.ac.za` | M2; it answered over HTTPS on 2026-11-02 |
| 4 | NAOJ (ADAC) | `http://vizier.nao.ac.jp` | M1, M2; HTTPS timed out on 2026-11-02 |
| 5 | China-VO (NAOC) | `http://vizier.china-vo.org` | M1, M2; HTTPS was refused on 2026-11-02 |

IUCAA and INASAN are listed on the page but are not in the maintainer's list.

The scheme does not carry the integrity: a table is accepted only if its content SHA-256 and,
after the header's metadata is restored, its raw SHA-256 equal those of the frozen edition in
`calibration/v0.4/inputs.json`.

## Answers on 2026-11-02, about 19:20 UTC (the full TESS-EB query)

- CDS: no answer (timeout).
- CfA: HTTP 502.
- IDIA: 254384 bytes; the content SHA-256 equals the frozen edition's.
- NAOJ: an error and no table, in two requests (712 bytes, then 1805 bytes). Excerpt: "The
  database is not currently reachable."
- China-VO: 254608 bytes; the content SHA-256 differs. Its `#Column` lines carry other UCDs, and
  four rows come in another order. The tool refuses such an answer.
