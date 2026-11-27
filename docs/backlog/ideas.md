# Ideas backlog

These ideas for later phases were moved here from GitHub issues by the maintainer's decision W2
(#218, recorded at comment 7229841832, 2026-11-27).

**What each section holds:**
- the issue's number, title and link;
- its body and comments, nearly in full: only the standing footer of the issues recorded during
  v0.2 is shortened. That footer reads: "Recorded during v0.2 (Gauntlet) with the maintainer's
  approval. Not implemented now: per ROADMAP.md, work happens only in the current phase."

**How the issues are closed:** each issue is closed after this file is committed, with a comment
that points to its section. An issue is reopened when a phase takes it up.

**What these are:** ideas, not findings and not gate items. Some issues name a plan document or
a milestone; those are kept as they were written.

**Phase names** are kept as each issue wrote them. Refute renumbered its phases on 2026-11-03
(ROADMAP.md, #199): v0.5 became "Stronger tests", the variable stars pack became v0.6,
mathematics v0.7, and Refute@Home v0.8.

**Milestones.** Several issues carry a triage comment of 2026-11-10, written after v0.5.2 closed
as not approved
([closing record](https://github.com/klucilla/refute/blob/2f9e41005e67ac63948b0aa540dee0c44a91465f/docs/validation/v0.5.2/closing-record.md)).
"Deferred" there means no target version.

Labels: `exploratory`, `method_status: not_validated`.

## 1. #9: Null distribution and false-alarm rate from scrambled or inverted light curves

https://github.com/klucilla/refute/issues/9

**Body (suggested phase: v0.4 Discover; recorded during v0.2).** Measure the gauntlet's false-alarm
rate on each run from the data themselves, not only from synthetic studies.
- Build null light curves for every target. Inverted light curves: flux mirrored about 1, so dips
  become bumps. Scrambled ones: for example sectors or orbits shuffled in time, or phases
  scrambled. They keep the noise and systematics but destroy a periodic transit.
- Run the same search and gauntlet on them, and record how often a "signal" survives.
- Report the resulting null distribution and false-alarm rate in every dossier, recomputed at
  each run.
- **Why:** in v0.4 Refute searches for new candidates, and a candidate is meaningful only against a
  measured false-alarm rate for that star and those data.
- Planned when the suggested phase starts.

**Comment of 2026-10-29: the amendment for the v0.4 funnel** (approved by the maintainer):
- On the N funnel stars (light curves only), the transformed curves go through the light-curve
  tests of funnel stage 1: the `snr` gate, `odd_even`, `secondary_eclipse`, `period_alias`,
  `plausibility`, `systematics` and `nearby_contamination`.
- The full battery runs on transformed curves only where pixel files exist (promoted stars and
  controls).
- **Separate denominators:** eligible stars, stars promoted by the cap, and survivors. Detections
  that pass the gate and detections that survive the declared tests are counted apart.
- **A missing test never counts as passed:** pixel tests are INCONCLUSIVE with zero coverage at
  stage 1.
- **Fixed in the protocol before the lock:** the transformations (inverted flux; block shuffles,
  seeded from the drand round) and their number.
- **The result's name:** "detections on transformed curves", not a real false-alarm rate. A
  transformation does not guarantee the absence of astrophysical signals and does not preserve
  every relevant noise structure. It is reported per curve; across curves it is descriptive only.
- Tracked in #177 (WP3), together with #175.

**Comment of 2026-10-29: the correction** (the maintainer's P1 decision). The scrambling of the
v0.4 pilot is a **cyclic rotation within each sector**, not a block shuffle.
- **What rotates:** every per-cadence column of a sector, by the same offset on the sector's raw
  cadence grid, before the quality mask. The columns are the PDCSAP and SAP flux with their errors,
  the background, the quality flags, the centroids, and the pixel cadences when present.
- **What never changes:** the time stamps, and the per-sector metadata (aperture, target position,
  CROWDSAP, FLFRCSAP). A momentum dump moves with its cadence.
- **Why:** a block shuffle moves data between sectors. It cannot keep each block's pixel geometry
  and metadata, and cannot fit orbits of unequal length into fixed slots.
- **Limits:** the rotation can reduce the phase coherence of a periodic signal between sectors, but
  this is not guaranteed; a signal with several transits inside one sector stays visible.
- **Per curve:** one inverted curve and two rotations, with offsets drawn per sector in [10 %, 90 %]
  of the sector's cadences.
- ROADMAP amendment 3 was corrected in the same batch. Tracked in #177.

**Comment of 2026-11-03: status after v0.4** (kept open).
- **Covered by the v0.4 pilot** (`calibration/v0.4/results/report-4.md`, section "Detections on
  transformed curves (not a false-alarm rate)"):
  - 3 transformed curves per star (1 inverted, 2 cyclic rotations within each sector);
  - funnel stage 1: 300 transformed curves; 64 pass the gate; 17 survive the stage-1 decisive
    tests;
  - the controls and the promoted stars also ran the full battery (stage 2) on their transformed
    curves;
  - the numbers are reported per curve, and across curves are descriptive only.
- **Still missing:**
  - a null distribution and a false-alarm rate, per star, in every dossier;
  - a validated method for which transformations make a valid null.

**Comment of 2026-11-05: v0.5 closing, exit criterion 7** (the maintainer's decision 3 of
2026-11-05, #199). Kept open, with the part left:
- done in v0.5: the report part, a descriptive transformed-curve comparison (`d03a931`);
- left: a validated null distribution and a per-star false-alarm rate (plan section 6: out of
  scope).

**Triage of 2026-11-10:** milestone none → Deferred. Reason: false-alarm calibration, not
scheduled in the current line of work.

## 2. #10: Transit-derived stellar density versus catalog density

https://github.com/klucilla/refute/issues/10

**Body (suggested phase: v0.4 Discover; recorded during v0.2).** Add a gauntlet test that compares
the stellar density implied by the transit shape with the density from the catalog.
- From the period, the transit duration, the ingress/egress time and the depth, a circular-orbit
  transit fit gives a/R* and hence the mean stellar density.
- Compare it with the density from the TIC mass and radius, with uncertainties.
- A large disagreement suggests a blend, an eclipsing binary, an eccentric orbit or the wrong
  star.
- **Why:** a classic, independent check that uses only the light curve and catalog values already
  recorded in the dossier.
- Planned when the suggested phase starts.

**Triage of 2026-11-10:** milestone v0.5.1 → v0.5.3. Reason: "a candidate D1 route for folded
eclipsing binaries, with #215."

*Scope note (this file's, not the issue's):* #215 and the D1 findings stay open as issues of their
own (`docs/validation/v0.5.13/triage-2026-11-27/README.md`, the triage of 2026-11-27).

## 3. #11: Difference-image centroid

https://github.com/klucilla/refute/issues/11

**Body (suggested phase: v0.4 Discover; recorded during v0.2).** Add a difference-image centroid test
next to the flux-weighted centroid test of v0.2.
- For each sector, average the target pixel images in transit and out of transit (local
  baselines), subtract, and locate the source of the dimming in the difference image, for example
  with a point-spread-function fit.
- Compare that position with the target and with nearby TIC sources, per sector and combined.
- **Why:** v0.2's `centroid_shift` test locates the dimming source from flux-weighted centroids
  inside the SPOC aperture. Those are biased when the source sits near the aperture edge.
  Difference images locate it directly and can name the neighbour responsible.
- Planned when the suggested phase starts.

**Triage of 2026-11-10:** milestone v0.4 → Deferred. Reason: v0.4 is closed; not in the current
line of work.

## 4. #12: Statistical validation: false positive probability (e.g. TRICERATOPS)

https://github.com/klucilla/refute/issues/12

**Body (suggested phase: v0.4 or later; recorded during v0.2).** Compute a false positive
probability for surviving candidates with an established statistical validation tool, such as
TRICERATOPS.
- Run the tool on candidates that survive the gauntlet, with the inputs recorded in the dossier:
  the light curve, contrast curves if any, and the TIC neighbours.
- Report the false positive probability and the nearby false positive probability as information.
- Decide, in a pre-registered way, whether and how it feeds a verdict. Deterministic and
  reproducible use (fixed versions and seeds) is required.
- **Why:** the gauntlet refutes. Statistical validation weighs the remaining scenarios (background
  eclipsing binaries, hierarchical triples) that the gauntlet can only flag as possible.
- Planned when the suggested phase starts.

**Triage of 2026-11-10:** milestone v0.4 → Deferred. Reason: v0.4 is closed; not in the current
line of work.

## 5. #13: Mutation testing of the gauntlet

https://github.com/klucilla/refute/issues/13

**Body (suggested phase: later, after v0.4; recorded during v0.2).** Check that the calibration
actually depends on each test, by breaking the tests on purpose.
- For each gauntlet test, build a mutant in which that test always returns PASS and, separately,
  one in which it always returns FAIL.
- Run the calibration with each mutant, and confirm that the result changes in the expected way:
  for example fewer false positives flagged, or the degeneracy guard tripping.
- A mutant that does not change anything reveals a test that the calibration does not exercise.
- **Why:** a calibration that passes with a disabled test is not evidence that the test works.
- Planned when the suggested phase starts.

## 6. #16: Use Gaia DR3 variability tables as reference catalogs

https://github.com/klucilla/refute/issues/16

**Body (suggested phases: v0.4 Discover and v0.5 Variable stars; recorded during v0.2).** From v0.2
the TESS pack already uses one Gaia DR3 variability table (`vari_eclipsing_binary`) in the
`eb_catalog` test. Other Gaia DR3 variability tables can serve as independent reference catalogs
in later phases:
- **v0.4 Discover:** cross-match every discover candidate with Gaia DR3 `vari_planetary_transit`
  before calling anything new. Report the match, or its absence, in the dossier and in the
  candidate ledger.
- **v0.5 Variable stars:** use `vari_rotation_modulation`, `vari_ms_oscillator`, `vari_rrlyrae`
  and `vari_cepheid` as reference catalogs for the variable stars pack (cross-match,
  classification checks).

**Notes for when this is planned:**
- Snapshots with source URL, retrieval time and SHA-256, attached to the claim and covered by the
  lock, as for `vari_eclipsing_binary` in v0.2 (see `calibration/v0.2/PROTOCOL.md`).
- A catalog test must report its coverage (rows scanned). It may PASS on "no match" only when the
  catalog was really searched around the target.
- Gaia data are distributed under CC BY-NC 3.0 IGO and need the ESA/Gaia/DPAC acknowledgement and
  citations.

**Comment of 2026-10-09: moved here from #3** (triage before release v0.2.0).
- **#3's proposal:** an optional, pre-registered fallback for stars whose TIC row has disposition
  `SPLIT`, `DUPLICATE` or `ARTIFACT`: take the stellar parameters from a Gaia crossmatch of the
  bright source.
- **What v0.2 implemented of #3** (commit `deaa4eb`), but not this fallback:
  - the plausibility test becomes `INCONCLUSIVE` for those dispositions;
  - a Tmag mismatch is a data-quality warning.
- **The official tool to start from:** ExoFOP's "Gaia DR3-TIC Crossmatch"
  (https://exofop.ipac.caltech.edu/tess/gaiadr3_tic_crossmatch.php; listed in the Stars section of
  the ExoFOP-TESS home page, read 2026-10-09).
  - It is described in Hardegree-Ullman et al., "Gaia DR3 IDs for TESS Input Catalog Targets",
    arXiv:2603.28850 (https://arxiv.org/abs/2603.28850; a Research Note of the AAS, accepted).
  - The code to reproduce the table is at https://github.com/kevinkhu/ticgaia.
- **Notes for when this is planned:**
  - The crossmatch maps TIC IDs to Gaia DR3 IDs. For a `SPLIT` or `DUPLICATE` row, the matched
    source may be the wrong (faint) star, which is the problem #3 found. So the rule that picks the
    bright source must be written and locked before any target is analysed.
  - A snapshot with URL, retrieval time and SHA-256, attached to the claim and covered by the lock.
    The table's terms of use are checked before anything is redistributed.
  - The fallback may never be used to rescue a target after its verdict has been seen.
  - Coverage: the fallback reports what it examined; no parameter, no PASS.

**Triage of 2026-11-10:** milestone v0.4 → v0.6. Reason: its variable-star catalog part maps to the
cross-match of ROADMAP v0.6; its planetary-transit catalog part stays unresolved.

## 7. #17: Study Gaia@home and Gaia Vari as prior art for Refute@Home and the variable stars pack

https://github.com/klucilla/refute/issues/17

**Body (suggested phases: v0.7 Refute@Home for Gaia@home, and v0.5 Variable stars for Gaia Vari;
recorded during v0.2).**
- **Gaia@home** (https://gaiaathome.eu/): a BOINC project that combines the Gaia catalogue with
  volunteer computing, with small jobs of Gaia data plus code run on volunteer machines. To
  evaluate:
  - as prior art for Refute@Home (work units, double computation, result validation);
  - as a possible partner;
  - as input to the "BOINC versus custom coordinator" decision already in the v0.7 scope of
    ROADMAP.md.

  Its public application list shows Linux only, while Refute@Home targets one-click installers
  for Windows and macOS (the cross-cutting principle "Everyone can use it" in ROADMAP.md).
- **Gaia Vari** (ESA citizen science on Zooniverse): volunteers classify Gaia variable stars. It is
  a reference for the v0.5 variable stars pack: classification classes, volunteer workflows, and
  the validation of volunteer labels against catalog classifications.

**Comment of 2026-10-09: Planet Hunters TESS** (added with the maintainer's approval; nothing
implemented).
- **The project:** a Zooniverse citizen-science project launched on 6 December 2018
  (https://www.zooniverse.org/projects/nora-dot-eisner/planet-hunters-tess). Volunteers inspect TESS
  light curves by eye and mark transit-like dips.
- **"Planet Hunters TESS II: findings from the first two years of TESS"** (Eisner et al., MNRAS 501,
  4669, 2021; https://arxiv.org/abs/2011.13944; doi:10.1093/mnras/staa3739), checked against the
  paper on 2026-10-09:
  - more than 22,000 volunteers inspected the first 26 TESS sectors;
  - recovery of known TOIs: 85 % of those with radii above 4 Earth radii, and 51 % of those between
    3 and 4 Earth radii;
  - 90 promising planet candidates not previously identified by other teams, 73 of which show a
    single transit in the TESS light curve.
- **Its first planet:** TOI-813 b (TIC 55525572 b, a Saturn-sized planet on an 84-day orbit around a
  subgiant). Volunteers first noticed it as a single transit. "Planet Hunters TESS I" (Eisner et al.,
  MNRAS 494, 750, 2020; https://arxiv.org/abs/1909.09094) describes it as "the first planet
  discovered by the Planet Hunters TESS project" and statistically validated its planetary nature.
- **Points for Refute:**
  1. **Single-transit search (v0.4).** Most of the project's new candidates are single transits, the
     case that period searches handle worst and that the v0.4 scope names ("long-period and
     single-transit search"). Its candidates and methods are a reference for that work.
  2. **A calibration reference.** Its recovery rates against TOIs, by planet radius, are an
     external benchmark of what careful human inspection achieves on the same data. A comparison
     must use the same selection (sectors, radius bins, TOI list date), and would be information,
     not a pass/fail criterion of a locked claim.
  3. **Human participation in Refute@Home (v0.7).** Besides donated CPU/GPU time: visual
     classification, possibly built with the Zooniverse project builder. Volunteers propose
     signals, and the deterministic gauntlet then attacks what people find. People propose;
     deterministic tests decide. The anti-cheat and validation rules for computing (#21) would
     apply, and no human vote ever sets a verdict.

**Comment of 2026-10-09: Windowsill Lab** (added with the maintainer's approval; nothing
implemented).
- **The project:** a home science instrument. Page https://www.brokenbranch.dev/windowsill/; code
  https://github.com/benskamps/windowsill-lab (MIT license, per the repository and the page).
  Checked on the page and in the repository's README on 2026-10-09:
  - a home lab run by AI agents: two ordinary computers take turns running experiments on a
    schedule; AI agents wrote the code and run it;
  - calibration before discovery: the first job is to re-find a known answer ("a calibration, not a
    discovery"), and nothing on the page is claimed as a new result;
  - a deterministic check plus a human sign-off: a check must pass first, then a human signs every
    promotion, and the receipt names who read the evidence;
  - errors kept visible: misses stay on the record; a pilot planet candidate that turned out to be
    an impostor keeps both the mistake and the correction in its receipt;
  - receipts with provenance (run date, seed, device, commit and more); the page notes that older
    reports keep their original provenance gaps;
  - two machines on different platforms, one Windows/CUDA and one Linux/ROCm;
  - an archive astronomy track: a blind planet search over public telescope archives, with a ledger
    (the README calls it "open-archive astronomy").
- **Points for Refute:**
  1. **External validation of our principles.** An independent project arrived at the same core
     practices: agents propose and a deterministic check plus a human decide; calibration on known
     answers comes before any discovery claim; failures stay published. This is information about
     the design, not evidence about any Refute result.
  2. **Independent reanalysis on different platforms (#28).** A second analysis on a different
     operating system and GPU/CPU stack (for example Windows and Linux, CUDA and ROCm or CPU) would
     catch platform-dependent numerical differences and environment bugs that a second
     implementation on the same machine cannot. Tolerances still have to be fixed in advance.
  3. **A living visual metaphor for the website (#20).** Their page shows each experiment as part of
     a growing scene in which misses remain visible. Refute's site could have its own living
     metaphor, designed for Refute and not copied from theirs. In it, every claim, attack and
     verdict would be visible and the failures would stay on screen (for example the v0.1 and v0.2
     self-claim FAILs). Every element would be generated from the result files and linked to its
     evidence.

**Comment of 2026-10-09: Skycruncher, HD 189733 b with a 30 mm smart telescope** (added with the
maintainer's approval; nothing implemented).
- **The page:** https://skycruncher.io/experiments/transits/hd189733b/2026-10-02/, read on
  2026-10-09.
- **The observation:** a transit of the hot Jupiter HD 189733 b on 2026-10-02 with a ZWO Seestar S30
  Pro, a 30 mm smart telescope (3.67″ per pixel, 10 s exposures, 544 frames).
- **What the page reports:**
  - **Result:** depth 2.50 % ± 0.34 % against a published value of about 2.45 %; mid-transit 1.0 ±
    3.6 minutes from the prediction. For reference, the NASA Exoplanet Archive composite table gives
    a depth of 2.40 % and V = 7.67 for this system (queried 2026-10-09).
  - **Precision:** about 3 % per 10 s frame, dominated by atmospheric scintillation (about 2.3 % per
    frame by the page's estimate), and 0.42 % per 10-minute bin out of transit.
  - **Comparison stars chosen by rule, not by hand:** Gaia DR3 stars of magnitude 7.6 to 10, with no
    bright neighbour within 37″, away from the frame edges, not flagged as variable, and steady out
    of transit. That gave 98 stars, none above 5 % of the weight. An earlier hand-picked set of 7
    stars had about 2.3 times more scatter.
  - **Tests written before each run,** including an injection test that first failed and a
    stricter, pre-written version.
  - **A development night separated from a confirmation night:** the 2 October night was used to
    choose the steps, so it "can't confirm them". The next transit (22 October 2026) was reserved
    for that.
  - **A frozen reduction published next to the final one:** a green-pixel-only reduction frozen
    before looking (2.83 % ± 0.40 %) is shown with the headline result.
  - **Stated limits:** scintillation sets a floor that only more collected light lowers; one night
    cannot pin down the transit shape; a check star showed an apparent 12 % dip attributed to an
    instrument effect; there was only 20 minutes of pre-transit baseline.
- **Points for Refute:**
  1. **The same discipline Refute applies, at the smallest scale:** rule-based inputs, tests written
     before, a development set kept apart from a confirmation set, and the frozen analysis published
     next to the final one. It matches the requirements recorded for v0.2.1 (separate development
     and reserved confirmation sets).
  2. **A follow-up channel.** Small telescopes are realistic for bright targets with deep signals,
     and for checking whether a nearby star is the real source. The idea was recorded for v0.4
     ("follow-up of predicted transits by amateur observers; see the new issue linked from the v0.4
     milestone").
  3. **Amateur data need their own validation** before they inform any test, as the check star's
     apparent 12 % dip shows.

**Comment of 2026-10-09: the aperiodic monotile and an interactive Spectre explorer** (added with
the maintainer's approval; nothing implemented). For v0.6 (the Mathematics pack, as numbered then)
and for the website's interactive drawings (#20).
- **The discovery.** David Smith, a self-taught hobbyist, found the "hat" in November 2022 while
  experimenting with shapes in a polyform puzzle program and with cardstock copies. He sent it to
  Craig S. Kaplan (University of Waterloo). With Joseph Samuel Myers and Chaim Goodman-Strauss they
  published:
  - **"An aperiodic monotile"** (https://arxiv.org/abs/2303.10798, March 2023).
    - The hat polykite forms clusters ("metatiles") with substitution rules.
    - A combinatorial, computer-assisted proof shows it tiles the plane only aperiodically.
    - It is the first "einstein" (one shape), after decades in which the smallest known aperiodic
      sets needed more tiles (for example Penrose's two).
  - **"A chiral aperiodic monotile"** (https://arxiv.org/abs/2305.17743, May 2023; Combinatorial
    Theory 4(2), 2024).
    - The hat's tilings use mirror-image copies. This paper shows that an equilateral relative is
      aperiodic when reflections are not allowed.
    - It modifies that shape's edges into the **Spectre**, a family of strictly chiral aperiodic
      monotiles whose tilings follow a hierarchical substitution system.
  - Sources checked on 2026-10-09: the two arXiv abstracts, and press coverage of the discovery (for
    example Quanta Magazine, 2023-04-04).
- **The explorer:** https://bohemian-miser.github.io/Spectre/ (code
  https://github.com/bohemian-miser/Spectre, BSD-3-Clause).
  - Its README says it builds on Craig Kaplan's Spectre app
    (https://cs.uwaterloo.ca/~csk/spectre/app.html).
  - You build supertiles, mark which edge classes carry a line, and see what happens: closed
    circuits, infinite lines, or both.
  - It has an infinite map, a view of a supertile split into its children, and a page on the parity
    condition: of the 512 sets of edge classes, 8 avoid dangling "tails".
  - The README states an open question: which choices give finitely or infinitely many infinite
    lines and circuits.
  - Every view's state is in its URL, and each screenshot links to the same view.
- **Points for Refute:**
  1. **v0.6 (the Mathematics pack).** A model case: a conjecture stated exactly, explored by a
     non-professional with software, then settled by a computer-assisted proof and checked by
     others. It fits the v0.6 scope: exact, machine-checkable predicates and verifiable
     certificates. Exploration tools like this one generate questions. A Refute claim would need
     the predicate written and locked before the search, and any "counterexample" re-verified
     independently.
  2. **The website (#20).** Interactive drawings whose whole state lives in the URL, so every
     picture can be shared and reproduced exactly, and every screenshot links to the live view.
     Refute's "How it works" drawings could do the same, with each state also linked to the result
     file it comes from; designed for Refute, not copied.

**Comment of 2026-10-09: Planet Hunters CHEOPS** (added with the maintainer's approval; nothing
implemented).
- **The page:** https://www.zooniverse.org/projects/bmerin/planet-hunters-cheops, read on 2026-10-09.
  A Zooniverse citizen-science project built on data from CHEOPS, ESA's space telescope for
  exoplanet characterization. What the page says:
  - **Data:** light curves "from thousands of background sources", extracted from "over five years
    of public observations" of the CHEOPS space telescope.
    - CHEOPS points at one target star at a time; the other stars in its field are a by-product.
    - For context, an open-source tool for photometry of CHEOPS background stars was described in
      2020: https://arxiv.org/abs/2005.12596.
  - **Task:** volunteers inspect brightness plots for dips, mark where each dip starts and ends,
    and classify it as a potential planet or noise.
  - **Redundancy:** "Each target is reviewed by many volunteers". The page mentions thousands of
    classifications per target, without giving a retirement limit.
  - **Team shown:** the researcher named on the page is Bruno Merín ("Message from the
    researcher"). The project's about section shows the ESA logo, with links to the ESA CHEOPS and
    ESA Science websites. The Adler Planetarium, University of Minnesota and University of Oxford
    logos belong to the Zooniverse platform and appear on every project.
  - **Status: not launched yet.** The statistics section reads "Project not launched", with 0
    volunteers, 0 classifications and 0 % complete, even though the banner invites people to start
    classifying. No launch date is given.
  - **Credit:** the page says that several discoveries from citizen-science projects "have led to
    peer-reviewed scientific papers, with volunteers credited as co-authors". This describes
    citizen science in general; the page makes no specific commitment for this project.
- **Points for Refute:**
  1. **A possible CHEOPS pack after the v1.0 pack SDK.** Public CHEOPS observations, especially the
     background stars in its fields, are a second source of transit-like signals, with a different
     instrument and different systematics. Like any pack it would need its own data adapter,
     gauntlet, holdout strategy and calibration on known objects. It is outside the current roadmap
     until community packs arrive with the SDK.
  2. **Redundancy between volunteers, as in #21.** Several independent volunteers per light curve
     are the human counterpart of running each work unit on at least two independent machines. The
     same principle would apply if Refute@Home ever includes human classification: agreement
     required, credit only for validated work, control items with known answers.
  3. **Crediting volunteers, as a model for v0.7.** Citizen-science projects have credited
     volunteers as co-authors of the papers their work led to. Refute@Home should define its credit
     policy before launch: how contributions are recorded, when a contribution earns acknowledgment
     or co-authorship, and how volunteers opt in or out of being named. Recorded as a question for
     v0.7, not decided.

## 8. #18: Publication path: JOSS software paper, methodology paper, then one RNAAS per candidate, then ExoFOP upload

https://github.com/klucilla/refute/issues/18

**Body (suggested phases: v0.4 Discover for the exporter and candidates, and later for
publications; recorded during v0.2; nothing implemented).** The project proceeds with the maintainer
as an independent author, without external collaboration for now.

**Why: ExoFOP no longer takes unpublished community candidates.**
- **ExoFOP home page news, 2026-08-19** (https://exofop.ipac.caltech.edu/tess/, read 2026-10-08):
  - community planet candidates must first be published in a peer-reviewed journal with online
    access before being uploaded;
  - approval to upload candidates is required (Published Candidate Upload Request).
- **IPAC Helpdesk e-mail to the maintainer, 2026-10-08:** it confirms the same (as reported by the
  maintainer).
- **Guidelines for Submitting Published Planet Candidates**
  (https://exofop.ipac.caltech.edu/tess/candidate_help.php, read 2026-10-08): candidates can also be
  presented in a Research Note of the AAS (RNAAS), if the methodology to detect and vet them was
  previously published in a peer-reviewed journal that is available online and is cited by the
  note.
- So a Refute dossier can never be uploaded to ExoFOP directly.

**The proposed path:**
1. a software paper (for example JOSS);
2. a methodology paper in a peer-reviewed journal (detection, gauntlet, blind holdout,
   calibration);
3. one RNAAS per candidate, citing the methodology paper;
4. only then, with ExoFOP's approval, the upload of each published candidate.

AI use in writing will be declared according to the policy of each journal.

**Open questions** (to confirm by e-mail with exofop-support@ipac.caltech.edu before any decision):
- which journals are acceptable for the methodology paper (for example JOSS, RASTI, PASP, AJ);
- publication costs;
- endorsement for the first arXiv submission;
- the license of ExoFOP-Tools (see below).

**Exporter requirements, from the guidelines:**
- **The parameters:** the orbital period (days), the transit epoch (BJD), the transit depth (ppm) and
  the transit duration, all with uncertainties. At least two of period, epoch and depth are
  required; all four, greater than zero, for consideration as a cTOI by the TOI working group.
- **A duplicate check** against existing community candidates, the TOI list and confirmed planets,
  before anything is proposed.
- **Period multiples:** a period equal or close to an integer multiple (2x, 3x, ...) of an existing
  candidate's period on the same star becomes an additional parameter set of that object, not a new
  candidate.
- **Supporting material:** an image of the light curve with the fitted transit, uploaded to the TIC
  host star with the same tag as the candidate.
- **No planet letter:** never assign a lowercase letter (b, c, ...) before the planet is confirmed in
  the refereed literature.
- **The upload** needs the URL of the published paper, a tag, a discovery data source and an initial
  note.

**The exporter requirement for v0.4: the duration's uncertainty.** The candidate parameter sheet
(`export/candidate_parameters.*`, since v0.2) reports `duration_err_hours` as not measured. The
ExoFOP guidelines ask for the period, epoch, depth and duration with uncertainties, so v0.4 must
measure the uncertainty of the transit duration.

**Prior art for ExoFOP access:**
- **Official:** the ExoFOP Python Utilities page (https://exofop.ipac.caltech.edu/tess/tools.php,
  read 2026-10-09) links the ExoFOP-Tools repository (https://github.com/lundmb/ExoFOP-Tools; last
  update 2022-04-28, on the page and in the repository's last commit) and documents its functions
  and notebooks. It is the reference for any TOI or CTOI-list download and duplicate check in v0.4.
  Its endpoints must be re-verified before use, since the tools date from 2022.
- **License:** the repository shows no license (GitHub API, 2026-10-09), so its code must not be
  copied into Refute. Its license is one of the open questions for exofop-support.
- **Out of scope:** its upload, disposition-update, MyTargets and cookie/login functions. Refute
  never uploads, never changes dispositions and never automates a login.

**Comment of 2026-10-09: EXOZIPPy, a reference for the exporter's uncertainty requirements** (added
with the maintainer's approval; nothing implemented).
- **The project:** https://github.com/jdeast/EXOZIPPy (BSD-3-Clause). Its repository describes it as
  "a user-friendly, general wrapper for PyMC with an exoplanet modeling implementation" that "will
  eventually be the successor to EXOFASTv2". Checked in the repository on 2026-10-09:
  - **Status:** the README says it "now has almost all features of EXOFASTv2 implemented" but "is
    not officially released yet", with features still missing and many not thoroughly tested ("Use
    at your own risk and verify your results"). Only pre-releases exist (tags `v0.1.0rc1` and
    `v0.1.0rc2`; `pip install --pre exozippy`).
  - **A global fit:** an EXOFASTv2-style joint fit of transits, radial velocities and the SED. It
    gives a parameter summary and results table, corner and trace plots, and a draft of the modeling
    section with its citations. The transit duration (T14) is among the quantities the code
    computes; the exact uncertainty outputs still need to be checked on an example fit.
  - **A citation for every prior:** each prior in the parameters file carries a `citation:` field
    that follows it into the parameter table and into restart files. Automatically generated priors
    carry a citation naming the catalog and every correction applied.
  - **Data on Zenodo with checksums:** the large model data (MIST grids, bolometric-correction
    tables, spectra) live in the EXOZIPPy Zenodo community, and are downloaded and checksum-verified
    on first use. Each data record has its own DOI to cite, and the software has a concept DOI.
  - **Platforms:** Linux and Apple Silicon macOS; Windows through a Linux environment inside Windows
    (per the README).
- **For Refute (v0.4):** evaluate it as an **optional** tool for the exporter requirement recorded in
  this issue: period, epoch, depth and duration **with uncertainties**. Points to check at that
  time:
  - it must be officially released, or the exact pre-release pinned, under the project's dependency
    planning and 7-day cooldown;
  - its results must be reproducible from the dossier (fixed seeds and sampler settings recorded) and
    validated on synthetic transits with known parameters before any real use;
  - it informs the parameter sheet for a human; it never decides a verdict;
  - its conda-based install and C compilation may not fit Refute's `uv`-based environment, so it may
    be better run as a separate, documented step.

**Triage of 2026-11-10:** milestone v0.4 → Deferred. Reason: v0.4 is closed; not in the current
line of work.

## 9. #21: Community dashboard and contribution ranking, with anti-cheat validation

https://github.com/klucilla/refute/issues/21

**Body (suggested phase: v0.7 Refute@Home; recorded during v0.2).** Nothing is built now. It is
planned on branch `claude/v0-3-planning-draft-abff23` (`docs/plans/public-site-plan.md`, a
Portuguese working document): live community features next to the static public website, namely a
contribution ranking, indicators of candidates, and live charts.

**Architecture:**
- The public website stays static (#20).
- Live data come from a read-only API on a **new, separate VPS** created for this purpose; never the
  maintainer's existing VPS.
- If the API is down, the site keeps working and shows the last static snapshot with its date.
- The community server has no write access to scientific results; it only reads what the
  coordinator has validated.

**Anti-cheat validation (a design requirement).** The ranking must never contaminate the scientific
results. It follows the approach of BOINC, the platform behind SETI@home and Einstein@Home ("BOINC: A
Platform for Volunteer Computing", https://arxiv.org/abs/1903.01699):
- **Replication:** every work unit runs on at least two independent volunteers, with different
  accounts, machines and networks, assigned at random. A result counts only when a deterministic
  validator confirms agreement within stated tolerances. A disagreement triggers another replica,
  until a quorum is reached.
- **Credit:** granted only for validated work, at a fixed value per unit, never the value a client
  claims.
- **Control units:** units with known answers (injected synthetic signals), indistinguishable from
  real ones, catch lazy or cheating clients.
- **The ranking** is derived read-only from the validation ledger. Nothing in the ranking feeds the
  science, and the science uses only validated units.
- **Revocation:** credit can be revoked, and units involving a host caught cheating are recomputed.
- **Signatures:** results are signed, with an audit log.
- **Adaptive replication** may lower the cost for hosts with a reliable history, as in BOINC.

**Wording and privacy:**
- Indicators speak of "candidates that survived the gauntlet", "refuted signals" and "validated
  units", never of discoveries. Every candidate gets human review, and nothing is submitted anywhere
  without a person deciding.
- Volunteers appear under a nickname they choose, and appearing in the ranking is optional.
- Portuguese and English from day one (the "Everyone can use it" principle in ROADMAP.md).

## 10. #24: Prospective transit predictions published with a DOI before the data exist

https://github.com/klucilla/refute/issues/24

**Body (suggested phase: v0.4 Discover; recorded during v0.2).** Every candidate that survives the
gauntlet automatically gets a public, prospective prediction of its next transits (mid-times with
uncertainties) in TESS sectors that have not been observed yet. The prediction is published with a
DOI (for example on Zenodo) **before the data exist**, together with the evaluation rule fixed in
advance. When the sector's data are released, a deterministic evaluator runs, and the outcome is
published, hit or miss.

**Proposal:**
- **What each prediction records:**
  - the candidate identifier;
  - the ephemeris (epoch, period, covariance);
  - the expected duration and depth;
  - the predicted sectors, each transit window with the propagated uncertainty;
  - the evaluation rule and thresholds;
  - the code version, and the hash of the source dossier.
- **Three outcomes, never two:**
  - **hit:** a transit detected inside the window, above a fixed SNR, with a compatible depth;
  - **miss:** the windows were covered, the expected SNR was high enough, and nothing compatible was
    detected;
  - **not evaluable:** the sector was not observed as planned, the windows fell in data gaps, or
    there was no power. Not-evaluable predictions stay in the denominators and never count as hits.
- **Timing:** published before the sector **starts**, with a recorded query showing the data were not
  yet in the public archive. The git commit and the DOI are the timestamps.

**Why:** a prediction made before the data exist cannot have leaked from them. It is the strongest
form of blind test available: noise and instrument artifacts rarely hit the time of a future
transit.

**Risks:**
- **Leakage,** if the new sector is analysed before the prediction is published. The prediction code
  uses only earlier data, and lists them.
- **Pointing plans change;** affected predictions become "not evaluable".
- **Uncertainties grow with time;** the share of evaluable predictions must be reported.
- **Early disclosure.** Publishing a prediction makes the candidate public before any paper, which
  can affect priority and the publication path (#18). What the public record contains (for example a
  sealed hash first, the content later) is the maintainer's decision. Always "candidate", never
  "discovery".

It depends on an observing calendar: which future sectors cover each candidate.

**Comment of 2026-11-10:** milestone v0.4 removed because the phase is closed (triage of 2026-11-10).
The scope of this issue is left to the maintainer's separate decision.

## 11. #25: Public prediction ledger: every prediction and outcome, including misses

https://github.com/klucilla/refute/issues/25

**Body (suggested phase: v0.4 Discover; recorded during v0.2).** A public, append-only ledger of every
prediction and its outcome (hit, miss, not evaluable), with links to the DOI of each prediction and
to the data used to evaluate it. It is the data source for the public website (#20) and the live
community features (#21).
- **The file:** a versioned data file (one row per prediction), in the repository and in each
  release, with the hash of each prediction and of each evaluation.
- **No rewriting:** nothing is deleted or rewritten; a correction is a new row that points to the old
  one.
- **Optional positive controls:** predictions for known planets, marked as controls, to measure the
  evaluator itself.
- **Why:** it shows the engine's real performance with the misses in plain view, and it makes
  publishing only the hits impossible.
- **Risks:**
  - small numbers are noisy: always show the number of predictions and the uncertainty of every
    rate;
  - a hit means the signal repeated at the predicted time, not that it is a planet; the website must
    say so.

**Comment of 2026-10-29: extended for v0.4** (the maintainer's decision, instead of a separate
case-ledger issue). The issue also covers the **public case ledger** of the v0.4 pilot (WP5 in #177).
- **Format:** an append-only JSONL file (draft name `cases/ledger.jsonl`). Each event carries:
  - `seq` and a schema version;
  - a stable `case_id`;
  - an event type: `opened`, `locked`, `ran`, `reviewed`, `corrected`, `concluded`, `embargoed` or
    `released`;
  - a reference to the event it corrects;
  - the hashes of the dossier, seal, annexes and commit;
  - `prev_hash` (a chained hash).

  The canonical serialization and the hash computation are fixed in the schema.
- **Anchor:** published commits. Limit: the chain shows continuity against a known anchor; it does
  not prove that a copy holds every later event.
- **Every case, with or without a candidate,** including a light entry for every star scanned by the
  funnel (stage-1 results, promotion recorded apart from the verdict), so no denominator is hidden.
- **Labels:** `method_status: not_validated` and `temporal_diagnostic` in every entry.
- **Corrections** are new events pointing to the old one; nothing is deleted or rewritten.
- **Embargo:** a negative case about a published claim carries only hashes and neutral metadata until
  its reply period ends.
- **Verification:** a verifier script checks the chain, and the phase's acceptance checklist runs on
  it.

The prediction rows of the original proposal (#24) stay as they were, and are not part of the v0.4
pilot.

**Comment of 2026-11-03: status after v0.4** (kept open).
- **Covered by the v0.4 pilot,** through the case ledger of the extension above:
  - the ledger is `calibration/v0.4/results/ledger.jsonl`: 429 events, chained by `prev_hash`;
  - it has an entry for every star of the funnel and every control;
  - it is checked by `refute.core.ledger.verify_file` with the pack's rules (`case.check_event`),
    and anchored in published commits (`calibration/v0.4/runs/p5_anchor*.json`);
  - corrections are new events (5 `corrected` events).
- **Limit:** the ledger was assembled at P5 (2026-11-01) from dated records, not appended live
  (`report-4.md`, "Limits").
- **Still missing:**
  - the prediction rows of the original proposal (#24): predictions with a DOI and their outcomes
    (hit, miss, not evaluable). The v0.4 pilot made no prospective prediction;
  - a ledger appended live, as events happen;
  - the website that reads it (#20).

**Comment of 2026-11-10:** milestone v0.4 removed because the phase is closed (triage of
2026-11-10). The scope of this issue is left to the maintainer's separate decision.

## 12. #26: Observing-request template generated from a dossier (sent only by the maintainer)

https://github.com/klucilla/refute/issues/26

**Body (suggested phase: v0.4 Discover; recorded during v0.2).** A proposal template generated from a
candidate's dossier, for the TESS observing programs (for example Director's Discretionary Targets
and the Guest Investigator program). **The maintainer always decides and sends; Refute only drafts
the text and the target list.**

**Proposal:**
- **The template holds:** the identifier and coordinates; the ephemeris and the predicted sectors;
  why a shorter cadence helps (for example transit shape and ingress/egress timing); a summary of the
  gauntlet; a link to the dossier; and the standard candidate wording.
- **The target list** follows the format each program asks for. Targets are checked against the
  instrument footprint before any request.
- **Program rules** (eligibility, allocations, deadlines, renewal) are read from the official pages at
  the time of use and recorded with the retrieval date; they are not assumed.

**Why:** short-cadence data in the predicted sector increase the power of prospective predictions and
of shape tests.

**Risks:**
- approved targets may be listed publicly, which discloses the candidate before any paper;
- observing time is a shared, limited resource: request it only for candidates that passed every
  test, with the prediction ledger in view;
- no agent ever sends an e-mail or a proposal.

**Triage of 2026-11-10:** milestone v0.4 → Deferred. Reason: v0.4 is closed; not in the current line
of work.

## 13. #27: Extended deduplication against TESS pipeline detections, with every source recorded

https://github.com/klucilla/refute/issues/27

**Body (suggested phase: v0.4 Discover; recorded during v0.2).** Before a signal is called a new
candidate, cross-match it with TOIs, CTOIs and confirmed planets, already in the v0.4 scope. Also
cross-match it with the automatic detections published by the TESS pipelines: for example SPOC
threshold-crossing events and their data validation reports, and any public catalog of pipeline
detections. Record **each source queried, with its retrieval date and the hash of what was
downloaded**.

**Why:** a signal that a pipeline already recorded is not new, even if it never became a TOI.
Recording the sources makes "not found in any list" verifiable, with declared coverage (no PASS
without examined data).

**Risks:**
- **Lists change:** the cross-match is valid for its date, and is repeated when the report is
  written.
- **Ambiguous matches** (period multiples, close neighbours): the same alias rules and match radius
  as the other tests, fixed in advance.
- **Terms of use:** each source's terms must be checked before keeping copies. When redistribution
  is not allowed, keep the reference and the hash only.
- **Moderate effort:** several sources and formats.

**Triage of 2026-11-10:** milestone v0.4 → Deferred. Reason: v0.4 is closed; not in the current line
of work.

## 14. #28: Independent reanalysis: a second implementation on freshly downloaded data must agree

https://github.com/klucilla/refute/issues/28

**Body (suggested phase: v0.4 Discover; recorded during v0.2).** A test in which a **second,
independent implementation**, run on **freshly downloaded data** (no cache), must agree with the
first. It must agree on the period and epoch within tolerances, on the depth and duration within
tolerances, and on the outcome of the main tests. A disagreement is not a verdict on the signal: the
outcome is an engine-side `INCONCLUSIVE`, with the reason recorded.

**Proposal:**
- **A different code path:** the second implementation follows another path for the critical steps,
  for example a different transit-search library and a different detrending. It is written from the
  specification, in a session that has not seen the first implementation.
- **Fresh downloads:** every file is downloaded again and its hash compared with the first analysis.
  A different hash already signals a data problem.
- **Tolerances:** fixed in advance, documented, and tested on synthetic data.

**Why:** it catches what no gauntlet test catches: implementation defects, corrupted cache files
(such as the truncated downloads seen in v0.1), and dependencies that changed behaviour. It is the
same idea as the double computation planned for Refute@Home (v0.7), applied earlier.

**Risks:**
- independence is partial: both implementations follow the same specification and can share a
  design error;
- it roughly doubles the CPU time per surviving candidate (few candidates);
- tolerances too wide hide errors, and too narrow flag legitimate method differences;
- new dependencies follow the phase's dependency planning and the 7-day cooldown.

**Triage of 2026-11-10:** milestone v0.4 → Deferred. Reason: v0.4 is closed; not in the current line
of work.

## 15. #29: Amateur follow-up of predicted transits to tell target from nearby stars

https://github.com/klucilla/refute/issues/29

**Body (suggested phase: v0.4 Discover; recorded during v0.2).** Amateur observers with small
telescopes follow up the predicted transits of surviving candidates (#24), mainly to tell whether the
dip comes from the target or from a nearby star.

**Why:** TESS pixels are 21″ wide, so light from several stars falls in the same aperture.
Ground-based images resolve stars a few arcseconds apart. A neighbour that would need a deep eclipse
(often tens of percent) to produce the TESS signal can be checked even with a small telescope, as
long as the neighbour is bright enough. Detecting the shallow transit on the target itself needs
much better precision.

**Proposal:**
- **An observing request per prediction,** with:
  - the target, and the nearby stars that could produce the signal, with the eclipse depth each
    would need;
  - the predicted windows, with uncertainties;
  - the minimum precision needed for each check.
- **Existing observer networks** and their protocols are preferred over building a new one. Each
  network's scope, membership rules and data policy are checked before any contact.
- **A pre-registered reduction:**
  - comparison stars chosen by rule;
  - a frozen pipeline;
  - development and confirmation observations kept apart;
  - both the frozen and the final reductions published.
- **Amateur results enter Refute** only as recorded inputs to a test whose rules are fixed in advance,
  with their own coverage and quality checks.

**Limits:**
- **Small apertures** are limited by atmospheric scintillation and photon noise: realistic for bright
  stars and deep signals, not for shallow transits on faint stars. Each request states the precision
  needed, and does not ask for observations that cannot reach it.
- **Pixel scales** of several arcseconds leave very close neighbours unresolved.

**Risks:**
- **Data quality:** scintillation, instrument effects that mimic dips, clock errors. Every dataset is
  validated before use.
- **No amateur dataset sets a verdict on its own:** at most it feeds a pre-registered test. An
  on-target or off-target claim needs independent confirmation, for example two observers or two
  nights.
- **Early disclosure:** asking for observations makes the candidate public before any paper (the same
  disclosure question as #24).
- **Credit and data rights** of observers must be clear and agreed before observing.

**Triage of 2026-11-10:** milestone v0.4 → Deferred. Reason: v0.4 is closed; not in the current line
of work. Its dependence on #24 decides nothing about #24's scope.

## 16. #167: Ideas: eclipsing binaries and stellar variability as results of their own (v0.5, not started)

https://github.com/klucilla/refute/issues/167

**Body: ideas only** (v0.5, not started; the title and this text are kept as written, see the
renumbering comment below). The issue was opened on the maintainer's decision of 2026-10-22. No
implementation front, no code, no data download and no lot until v0.5 is the current phase. Its
place in the ROADMAP is v0.5 ("Variable stars pack: EB and pulsators, catalog cross-match,
exporter"), after the v0.2.1 gate.

**Context.** In the transit pack, eclipsing binaries and stellar variability are what the gauntlet
must recognize and set aside. An eclipsing binary is a false positive to flag; variability is a
nuisance that the detrending and the holdout must survive. Stage 1 of v0.2.1 showed how much of the
engine's behaviour depends on them: the attenuation of the measured depth with variability, and the
wrong candidates without it (`docs/validation/v0.2.1/reopen/stage-1/`). The same light curves carry
information that is a result in itself.

**Ideas (none is a plan):**
- **An analysis of its own for eclipsing binaries:** what the gauntlet already measures (odd/even
  depths, a secondary eclipse, the eclipse shape), reported as an eclipsing-binary candidate with its
  own claim and verdicts, instead of only as a reason to refute a transit.
- **Variability as a measured quantity:** the fundamentals the train detrending detects, reported per
  target with their uncertainty, and checked against a held-out year like any other claim.
- **Cross-matching** against published catalogs of eclipsing binaries and variable stars. Each catalog
  is named with its source and the date it was read when the work starts; none is chosen here.
- **An exporter** in the format of the official channel for such catalogs, with a human always
  submitting.

**Rules that would apply:**
- the claims are candidates and verdicts, never confirmed discoveries;
- every identifier, period and classification comes from an authoritative source with its date;
- nothing is submitted automatically;
- the domain pack has its own gauntlet, holdout strategy and coverage rules (zero coverage is
  INCONCLUSIVE).

**Not now:** this issue starts no code, no data download and no lot. It collects ideas until v0.5 is
planned.

**Comment of 2026-11-03: renumbering note** (#199). The variable stars pack is now **v0.6**; it was
v0.5 until 2026-11-03. v0.5 is now the phase of stronger tests. The title is kept as written, and
milestone v0.5 of the repository was renamed v0.6.

**Triage of 2026-11-10:** milestone none → v0.6. Reason: eclipsing binaries and variability as
results of their own (ROADMAP, v0.6).
