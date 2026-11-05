# Source for the CDS incident and the VizieR mirror used in exit criterion 6 (2026-11-05)

Statement supported: VizieR at the CDS did not answer on 2026-11-05 because of a cybersecurity
incident on the CDS network in Strasbourg, and the TESS-EB table of exit criterion 6 was taken
from an official VizieR mirror (`vizier.cfa.harvard.edu`), checked by the claim's content
SHA-256 (#199; `calibration/v0.5/reviews/criterion6/`). The integrity of the table does not rest
on these sources: it rests on the content hash.

## S1. CDS, official Facebook page, post of 2026-10-28

- URL: https://web.facebook.com/share/p/19bcWaB197/
- Read by the maintainer on 2026-11-05 (about 14:00 BRT). As reported by the maintainer: it
  announces a cybersecurity incident on the Strasbourg network, with services down, and lists
  mirrors, among them `https://vizier.cfa.harvard.edu/viz-bin/VizieR`.
- Excerpt: **not available to the agent**: the page could not be read by the agent's tools on
  2026-11-05 (Firecrawl: "this site ... is currently not supported"). The content above is the
  maintainer's reading; **not confirmed by the agent from this page**. A literal excerpt can be
  added by the maintainer as a new record.

## S2. CDS, official Bluesky account, post of 2026-10-28 (corroborates S1)

- URL: https://bsky.app/profile/cdsportal.bsky.social/post/3myx3gzqoak2w
- Published 2026-10-28T15:38:16.685Z (the page's `article:published_time`); read by the agent on
  2026-11-05 (Firecrawl, live fetch, HTTP 200). Already recorded on 2026-11-02 in
  [calibration/v0.4/sources/data-licenses-2026-11-01.md](../../v0.4/sources/data-licenses-2026-11-01.md), L9.
- Excerpt: "CDS is experiencing a cybersecurity incident within its network of servers located in
  Strasbourg."
- It does not list the mirrors.

## S3. The mirror list

- The VizieR mirrors page, recorded on 2026-11-02 in
  [calibration/v0.4/sources/vizier-mirrors-2026-11-02.md](../../v0.4/sources/vizier-mirrors-2026-11-02.md)
  (M1: the live page served by the IDIA mirror; M2: an archived capture of the CDS copy of
  2026-08-15), lists "VizieR at CFA Harvard": `https://vizier.cfa.harvard.edu/vizier/` and "VizieR
  at IDIA": `http://vizier.idia.ac.za/vizier/`.

## What the agent observed itself

- 2026-11-05, 15:54Z to 16:05Z: five attempts to reach `vizier.cds.unistra.fr` from the
  maintainer's machine timed out (#199); a HEAD request at 15:55:28Z failed; Firecrawl could not
  reach VizieR or the CDS portal either ("ERR_TUNNEL_CONNECTION_FAILED"; whether the failure was
  Firecrawl's or the CDS's is not confirmed).
- 2026-11-05T17:32:39Z: `vizier.cfa.harvard.edu` answered the scan's TESS-EB query (only the host
  replaced) with a table whose content SHA-256 equals the claim's
  (`calibration/v0.5/reviews/criterion6/attempt-02/mirror-fetch.json`).
