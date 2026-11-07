"""The TESS pack's table of INCONCLUSIVE classes (v0.5.1 WP4, ``refute.core.inconclusive``).

One row for every INCONCLUSIVE return of the shared v0.4 and v0.5 test functions that a version-3
claim can reach (those functions are not edited, so v0.5 outputs keep their bytes); the v3-only
modules (``battery_v51``, ``battery_v51_diff``) set their class themselves. A row is (test name,
message prefix, class); the first matching row wins. ``tests/test_v051_wp4.py`` checks that every
INCONCLUSIVE message literal of those functions matches a row.
"""

from __future__ import annotations

from refute.core.inconclusive import (
    INSUFFICIENT_SENSITIVITY,
    MISSING_INPUT,
    NOT_ENOUGH_DATA,
    OUTSIDE_DOMAIN,
    TableRow,
)

TESS_TABLE: tuple[TableRow, ...] = (
    # pipeline._not_run: the search found no candidate to attack
    ("*", "no candidate", NOT_ENOUGH_DATA),
    # the gate (pipeline: the corrected SNR)
    ("snr", "no in-transit cadence", NOT_ENOUGH_DATA),
    ("snr", "noise model undetermined", INSUFFICIENT_SENSITIVITY),
    # secondary_eclipse (battery_v5.check_secondary_two_sided, gauntlet)
    ("secondary_eclipse", "no data covers phase 0.5", NOT_ENOUGH_DATA),
    ("secondary_eclipse", "no primary events measured", NOT_ENOUGH_DATA),
    # plausibility (gauntlet.check_plausibility)
    ("plausibility", "TIC row has disposition", MISSING_INPUT),
    ("plausibility", "no TIC stellar radius available", MISSING_INPUT),
    ("plausibility", "TIC stellar radius has no uncertainty", MISSING_INPUT),
    ("plausibility", "TIC stellar radius too uncertain", INSUFFICIENT_SENSITIVITY),
    ("plausibility", "companion radius is plausible, but no stellar mass", MISSING_INPUT),
    # centroid_shift (centroid_v5)
    ("centroid_shift", "no target pixel data", MISSING_INPUT),
    ("centroid_shift", "qualification failed", NOT_ENOUGH_DATA),
    ("centroid_shift", "single sector", NOT_ENOUGH_DATA),
    ("centroid_shift", "no qualified sector", NOT_ENOUGH_DATA),
    ("centroid_shift", "sectors disagree", INSUFFICIENT_SENSITIVITY),
    # nearby_contamination (battery.check_nearby_contamination)
    ("nearby_contamination", "no TIC neighbor query available", MISSING_INPUT),
    ("nearby_contamination", "no TIC magnitude for the target", MISSING_INPUT),
    ("nearby_contamination", "crowding not checked: no CROWDSAP value", MISSING_INPUT),
    # period_alias (battery.check_period_alias; the reason leads the message)
    ("period_alias", "noise_undetermined", NOT_ENOUGH_DATA),
    ("period_alias", "too_few_cadences", NOT_ENOUGH_DATA),
    ("period_alias", "only ", NOT_ENOUGH_DATA),
    ("period_alias", "singular_design", INSUFFICIENT_SENSITIVITY),
    ("period_alias", "non_finite_statistic", INSUFFICIENT_SENSITIVITY),
    ("period_alias", "box_depth_not_positive", INSUFFICIENT_SENSITIVITY),
    ("period_alias", "box_gain_small_dip_not_explained", INSUFFICIENT_SENSITIVITY),
    # eb_catalog (ebcatalog.check_eb_catalog)
    ("eb_catalog", "no target coordinates", MISSING_INPUT),
    ("eb_catalog", "no record of which catalogs were scanned", MISSING_INPUT),
    ("eb_catalog", "the catalogs were not scanned around", MISSING_INPUT),
    ("eb_catalog", "extraction radius", MISSING_INPUT),
    # single_event, event_consistency, edge_events (battery_v5)
    ("single_event", "only ", NOT_ENOUGH_DATA),
    ("single_event", "the total SNR is not positive", INSUFFICIENT_SENSITIVITY),
    ("event_consistency", "only ", NOT_ENOUGH_DATA),
    ("edge_events", "no measured event", NOT_ENOUGH_DATA),
    ("edge_events", "every measured event is near a segment edge", NOT_ENOUGH_DATA),
    ("edge_events", "the events away from edges give SNR", INSUFFICIENT_SENSITIVITY),
    # sinusoid of v0.5 (not used in version 3, kept for completeness)
    ("sinusoid", "period ", OUTSIDE_DOMAIN),
    ("sinusoid", "too few out-of-transit cadences", NOT_ENOUGH_DATA),
    # holdout_by_year (the temporal diagnostic): every INCONCLUSIVE outcome means that no
    # hidden year, or not every necessary one, could be tested on the data
    ("holdout_by_year", "", NOT_ENOUGH_DATA),
)
