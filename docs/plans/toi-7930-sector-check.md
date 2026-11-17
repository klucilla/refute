# TOI-7930 (TIC 4206066): the check of future TESS sectors (item 3a), and the questions it leaves

**The decision asked.** The maintainer's decision of 2026-11-16 (#217), item 3a: "Primeiro,
confira se o TESS observará o alvo num setor futuro (fonte oficial [...]), com URL e data de
leitura. Se não houver setor futuro com dados utilizáveis, registre e pare este item."

**What this page is.** The record of that check, written on 2026-11-16, and the questions it
leaves for the maintainer.
- **The item stops here.** No sector that has not started is confirmed for the target. The scope
  of item 3b (the evaluation rule, what would be locked, the calendar and the price) is **not
  written**.
- It measures nothing: no TESS data were read. It locks nothing, and it selects no target for a
  run.
- Every external fact carries its URL and the date it was read. The local copies are in
  `.cache/pub1119/toi7930/` (not in git); their SHA-256 values are in the last section.
- The objects are **candidates**: TOI-7930.01 and TOI-7930.02, with the TESS project's own
  designations. Nothing here calls either one a planet.
- #24 and #25 are marked `future-phase`, and no phase is open. This page proposes no way around
  the phase rule.

## 1. The check

**Sources** (all read on 2026-11-16):
- The Web TESS Viewing Tool, v2.6 (NASA TESS Science Support Center), queried by the target's
  coordinates:
  <https://heasarc.gsfc.nasa.gov/wsgi-scripts/TESS/TESS-point_Web_Tool/TESS-point_Web_Tool/wtv_v2.0.py/>.
  Its page says: "updated with Cycle 9 Sectors 108 - 121".
- The sector table of the TESS Science Support Center: <https://heasarc.gsfc.nasa.gov/docs/tess/sector.html>
- The orbit times of the TESS Science Office (MIT): <https://tess.mit.edu/public/files/TESS_orbit_times.csv>

**What they say:**
- **The sectors of the target.** The tool lists four sectors for RA 80.859827°, Dec −1.326974°:

  | Sector | Camera | CCD | Midpoint |
  |---|---|---|---|
  | 6 | 1 | 1 | December 2018 |
  | 32 | 1 | 2 | December 2020 |
  | 98 | 1 | 2 | December 2025 |
  | 110 | 1 | 2 | November 2026 |

- **Sector 110 is in progress.** It runs from 2026-10-31 to 2026-11-26. So it started 16 days
  before this check.
- **No later sector is listed for the target,** within what the tool says it covers (to sector
  121, which ends on 2027-09-19 by the sector table).
- **Sectors 122 to 134** (Cycle 10, to September 2028) are in the sector table, as
  northern-hemisphere pointings and two ecliptic pointings. The tool does not cover them, so
  **no coverage of the target after sector 110 is confirmed, and none is excluded** for those
  sectors.

**The result of item 3a.** There is no confirmed future sector for the target. The only sector
not yet complete is sector 110, and it has already started. By the decision's condition, the
item is recorded and stops.

## 2. The facts behind question 2 (a doubt about the condition, not a scope)

One doubt about the condition is for the maintainer, because it has a date: sector 110 is not
over. The facts below are the least needed to answer it. They are not a scope.

**The ephemeris,** from the NASA Exoplanet Archive, table `toi`, queried by `tid = 4206066`
through its TAP service on 2026-11-16:
<https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+*+from+toi+where+tid=4206066&format=json>.
ExoFOP-TESS gives the same values (<https://exofop.ipac.caltech.edu/tess/target.php?id=4206066>,
read the same day).

| | TOI-7930.01 | TOI-7930.02 |
|---|---|---|
| Disposition (TFOPWG) | PC (planet candidate) | PC (planet candidate) |
| Mid-transit time, BJD | 2461034.264547 ± 0.001813 | 2461040.113969 ± 0.001825 |
| Period, days | 11.1327267 ± 0.0000126 | 3.1827878 ± 0.0000040 |
| Duration, hours | 1.52 ± 0.61 | 1.78 ± 0.35 |
| Depth, ppm | 910 ± 77 | 462 ± 39 |
| TOI created; row updated | 2026-11-06; 2026-11-07 | 2026-11-06; 2026-11-07 |

- **ExoFOP's notes on the TOI:** source `qlp-s98-ffi`; sectors 6, 32, 98; "potential multi;
  variable host".
- **The ephemeris is the TESS project's.** It is not a Refute result: Refute has run nothing on
  this target. The v0.4 pilot's plan set the target aside as "later, archive data only, labelled
  as a non-independent reproduction" (`docs/plans/v0.4-pilot-plan.md`, section 2).
- **The time standard.** The tables say BJD. The arithmetic below assumes BJD in the TDB scale.

**The sector's four observing segments,** from the orbit times file (UTC):

| Segment | From | To | Its full-frame images at MAST on 2026-11-16 |
|---|---|---|---|
| 1a | 2026-10-31 23:55 | 2026-11-06 21:35 | **public** (TICA, including camera 1, CCD 2) |
| 1b | 2026-11-07 02:35 | 2026-11-13 19:55 | not listed |
| 2a | 2026-11-14 00:55 | 2026-11-19 20:45 | not listed (the segment was in progress) |
| 2b | 2026-11-20 01:45 | 2026-11-26 04:15 | not listed (the segment had not started) |

Source of the last column: <https://archive.stsci.edu/hlsp/tica> (page updated 2026-11-12). One
of the four segments is public. How long a segment's images take to appear is not established:
one case was seen (1a ended on 11-06 and was listed by 11-12).

**The mid-times `T0 + n·P` from the check's date to the sector's end, and the first one after it.**
- `σ` treats `T0` and `P` as independent: `sqrt(σ_T0² + (n·σ_P)²)`.
- `σ_max` is the linear bound `σ_T0 + n·σ_P`, since the table gives no covariance.
- The UTC times are the barycentric times corrected for the light travel time to the Earth's
  centre. They are approximate, and for the calendar only.
- A transit begins about half its duration before its mid-time, and the durations' errors are
  large.

| Candidate | n | Mid-time, BJD | UTC (approx.) | σ, min | σ_max, min | Segment |
|---|---|---|---|---|---|---|
| .02 | 101 | 2461361.57554 | 2026-11-17 01:40 | 2.7 | 3.2 | 2a, in progress |
| .02 | 102 | 2461364.75832 | 2026-11-20 06:03 | 2.7 | 3.2 | 2b, not started |
| .02 | 103 | 2461367.94111 | 2026-11-23 10:27 | 2.7 | 3.2 | 2b, not started |
| .01 | 30 | 2461368.24635 | 2026-11-23 17:46 | 2.7 | 3.2 | 2b, not started |
| .02 | 104 | 2461371.12390 | 2026-11-26 14:50 | 2.7 | 3.2 | after the sector's end |

So, on the check's date:
- one predicted mid-time was still ahead inside a segment in progress (2a);
- three were ahead inside a segment that had not started (2b, from 2026-11-20 01:45 UTC, which is
  2026-11-19 22:45 in Brasília);
- one falls after the sector.

## 3. What #24 asks about timing

#24: "Timing: published before the sector **starts**, with a recorded query showing the data
were not yet in the public archive." Sector 110 has started, and one of its four segments is
public. So a prediction for sector 110 cannot meet #24's timing rule as written, whatever its
form.

#24 and #25 also fix three outcomes (hit, miss, not evaluable), a ledger with nothing deleted,
and optional positive controls, which #25 defines as "predictions for known planets, marked as
controls". Neither candidate here is established as a known planet.

## 4. Questions for the maintainer

1. **The phase rule.** #24 and #25 are `future-phase`, and no phase is open. Does the maintainer
   want to record an exception for this one case? This page proposes none.
2. **The condition of item 3a.** By the check, no confirmed future sector exists, and the item
   stops. The doubt is whether the segment of sector 110 that has not started (2b, from
   2026-11-20 01:45 UTC) counts as "a future sector with usable data" for the maintainer's
   purpose. If it does not, nothing else is to be done. If it does, the scope of item 3b would
   be written only on the maintainer's instruction, and it would have to state that #24's timing
   rule is not met.
3. **The label, if the case ever goes on.** The ephemeris is the TESS project's, and the
   candidates are not known planets. So the case fits neither a Refute candidate (#24) nor a
   positive control as #25 defines it. What it would be called is the maintainer's choice.

## Sources and local copies

Read on 2026-11-16 (UTC 23:22 to 23:39). The local copies are in `.cache/pub1119/toi7930/`:

| What | URL | SHA-256 of the copy |
|---|---|---|
| NASA Exoplanet Archive, `toi` rows of TIC 4206066 | the TAP URL of section 2 | `587ec59f1336e601f77fecf0e0c105e696ca87d8e05bb316ddd9a07de6d05480` |
| ExoFOP-TESS target record (JSON) | <https://exofop.ipac.caltech.edu/tess/target.php?id=4206066&json> | `da9a1ba67d6d1326013957fb8df34298222d932302da926d0289c121e7221663` |
| Web TESS Viewing Tool, its form page | the tool's URL of section 1 | `d11ec6eb673ab4f752e19194bf57a4a7d1c9ee637742124f2b4c1e70be0614c1` |
| Web TESS Viewing Tool, the result for the coordinates | the same URL (form `RADec_result`) | `079862ed4c21e3fedaff3dbd459399a275862c5caa11b07f12ed263ba9168c0d` |
| TESS sector table (TESS Science Support Center) | <https://heasarc.gsfc.nasa.gov/docs/tess/sector.html> | `ecf1150e5a1f4a50b323808efc6b8efdad9a8670a3c6f6c3871f3ce241e0e9d1` |
| TESS orbit times (TESS Science Office, MIT) | <https://tess.mit.edu/public/files/TESS_orbit_times.csv> | `b15ae6e0dcbc28722312efdc464f734a7878886e268286cf0a6d5290048500ba` |
| TICA full-frame images at MAST | <https://archive.stsci.edu/hlsp/tica> | `f83a77d194f6a4464fadf42372a5b8e06368a14cc68b2369593731d3fd62f3b6` |

- **ExoFOP's data use policy** is recorded in
  [`sources/v0.5.4-exofop-data-use-policy-2026-11-12.md`](sources/v0.5.4-exofop-data-use-policy-2026-11-12.md).
  This page quotes values of one target with their source, and redistributes no table.
- **A stale line.** The MIT observations page still read "TESS is in Orbit 229, Sector 109" on
  that day. The sector table and the orbit times file are the sources used here.
- **Unconfirmed:**
  - any coverage of the target in sectors 122 to 134;
  - the delay between a segment's end and its images' release;
  - the time scale of the tables' BJD (assumed TDB).
