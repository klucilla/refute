"""Blind holdout by observing year (gauntlet test e).

Isolation rule: :func:`run_holdout` receives only the raw normalized light curve,
the sector metadata (time spans, no flux) and the test plan. It has no parameter
for the candidate found on all data, and it never imports a global result. For
each observing year H, in turn:

1. Train = all other years, detrended without a mask; full two-stage search.
2. Train is re-detrended with a mask at the *train-only* ephemeris; individual
   transit times are measured and a linear ephemeris is fitted.
3. Transit windows in H are predicted from the train ephemeris and the hidden
   sectors' time spans (metadata only): half-width = duration/2 + k * sigma_T.
4. The hidden year is wrapped in :class:`HiddenYear`, which detrends the raw
   hidden data with a mask made only of the predicted windows and then gives
   access only to the registered windows and their local baseline bands.
5. A box of the train duration is scanned inside the windows with one period
   correction dP in +-k * sigma_P (train-only uncertainty). Each window's depth is
   measured against a line fitted to its own out-of-box points; window depths
   are stacked with an error that includes their scatter. The stacked SNR must
   reach ``min_snr`` at the best dP. The same scan at phase 0.5 is a control:
   reported, not judged.

A round is INCONCLUSIVE when train data cannot produce an ephemeris, when the
train-only timing uncertainty in the hidden year exceeds
``max_timing_sigma_durations`` transit durations (v0.2, issue #2), or when fewer
than ``min_predicted_transits`` windows contain data. From v0.2 the hidden year is
detrended with a window at least ``hidden_detrend_window_factor`` times the widest
masked span. The test PASSES if every
conclusive round passes, FAILS if any round fails, and is INCONCLUSIVE if no
round is conclusive or there are fewer than two observing years.

From v0.2.1 (H4) a round is also INCONCLUSIVE, never FAIL, when its train-only
candidate is not a valid basis for a prediction: (a) it fails the SNR gate of the
full analysis, (b) its duration exceeds ``max_train_duration_period_ratio`` of its
period, or (c) its transit windows cover more than ``max_hidden_window_fraction`` of
the hidden sectors' time spans. (a) and (b) are checked right after the train
search; (c) after the windows are predicted and the timing rule is applied. All
three use only the train data, the plan and the hidden sectors' metadata, and are
decided by :func:`plan_round`, which never receives hidden-year flux: an invalid
round never builds :class:`HiddenYear`. ``require_valid_train: false`` reports the
three rules without applying them.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from statistics import NormalDist
from typing import Any

import numpy as np

from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.tess.detrend import detrend, detrend_parts, robust_sigma
from refute.packs.tess.ephemeris import (
    Ephemeris,
    fit_linear_ephemeris,
    measure_transit_times,
)
from refute.packs.tess.events import per_point_sigma, transit_mask
from refute.packs.tess.gauntlet import check_snr
from refute.packs.tess.params import HoldoutParams, TessTestPlan
from refute.packs.tess.search import search_period
from refute.packs.tess.timing import corrected_transit_times
from refute.packs.tess.types import Candidate, LightCurveData, SectorInfo

TEST_NAME = "holdout_by_year"
REASON_TRAIN_SNR = "train_snr_below_gate"
REASON_DURATION_RATIO = "duration_period_ratio_above_max"
REASON_WINDOW_FRACTION = "hidden_window_fraction_above_max"


class HoldoutAccessError(RuntimeError):
    """Raised when code tries to read hidden-year data outside a registered window."""


@dataclass(frozen=True)
class PredictedWindow:
    kind: str  # "transit" or "control"
    epoch: int
    t_pred: float
    half_width: float
    baseline_inner: float
    baseline_outer: float


class HiddenYear:
    """Guarded access to one hidden observing year.

    The raw hidden data are detrended in the constructor, with a mask made only of
    the registered windows (computed beforehand from the train-only ephemeris).
    After construction, data can only be read inside a registered window or its
    registered baseline band, and every access is logged.
    """

    def __init__(
        self,
        raw_hidden: LightCurveData,
        windows: Sequence[PredictedWindow],
        plan: TessTestPlan,
    ):
        self._windows = {(w.t_pred, w.half_width): w for w in windows}
        mask = np.zeros(len(raw_hidden), dtype=bool)
        for window in windows:
            mask |= np.abs(raw_hidden.time - window.t_pred) <= window.baseline_inner
        # Issue #2: when a masked span is as wide as the detrending window, the knots
        # inside it have no data and the trend there is extrapolated. The window grows
        # to a multiple of the widest masked span (from the registered windows only).
        factor = plan.gauntlet.holdout_by_year.hidden_detrend_window_factor
        widest = max((2.0 * w.baseline_inner for w in windows), default=0.0)
        self.detrend_window_days = max(plan.detrend.window_days, factor * widest)
        params = plan.detrend.model_copy(update={"window_days": self.detrend_window_days})
        flat = detrend(raw_hidden, params, mask=mask)
        self.__time = flat.time
        self.__flux = flat.flux
        self.access_log: list[dict[str, Any]] = []
        # the R_min study's twin (map Amendment 26, 4) repeats this detrending for its parts
        self.__detrending = (raw_hidden, params, mask)

    def twin(self, model_hidden: np.ndarray) -> HiddenYear:
        """The noiseless twin (calibration only): the same registered windows, the flux
        ``model_hidden / trend`` of this year's noisy detrending on the cadences it kept (the
        detrending repeated by ``detrend_parts`` on the same inputs, checked identical)."""
        raw_hidden, params, mask = self.__detrending
        model = np.asarray(model_hidden, dtype=float)
        if model.shape != (len(raw_hidden),):
            raise ValueError("the twin model must have one value per cadence of the hidden year")
        flat, trend, keep = detrend_parts(raw_hidden, params, mask=mask)
        if not (np.array_equal(flat.time, self.__time) and np.array_equal(flat.flux, self.__flux)):
            raise RuntimeError("the repeated detrending differs from the noisy one")
        twin = object.__new__(HiddenYear)
        twin._windows = dict(self._windows)
        twin.detrend_window_days = self.detrend_window_days
        twin._HiddenYear__time = self.__time.copy()
        twin._HiddenYear__flux = model[keep] / trend[keep]
        twin.access_log = []
        twin._HiddenYear__detrending = self.__detrending
        return twin

    def _registered(self, t_pred: float, half_width: float) -> PredictedWindow:
        window = self._windows.get((t_pred, half_width))
        if window is None:
            raise HoldoutAccessError(
                f"access to hidden data at t={t_pred} (half-width {half_width}) "
                "is not a registered predicted window"
            )
        return window

    def window(self, t_pred: float, half_width: float) -> tuple[np.ndarray, np.ndarray]:
        window = self._registered(t_pred, half_width)
        lo, hi = window.t_pred - window.half_width, window.t_pred + window.half_width
        self.access_log.append({"kind": f"{window.kind}-window", "t_lo": lo, "t_hi": hi})
        sel = (self.__time >= lo) & (self.__time <= hi)
        return self.__time[sel].copy(), self.__flux[sel].copy()

    def local_baseline(self, t_pred: float, half_width: float) -> tuple[np.ndarray, np.ndarray]:
        window = self._registered(t_pred, half_width)
        inner, outer = window.baseline_inner, window.baseline_outer
        self.access_log.append(
            {
                "kind": f"{window.kind}-baseline",
                "t_lo": window.t_pred - outer,
                "t_hi": window.t_pred + outer,
                "excluded_half_width": inner,
            }
        )
        dt = np.abs(self.__time - window.t_pred)
        sel = (dt > inner) & (dt <= outer)
        return self.__time[sel].copy(), self.__flux[sel].copy()


@dataclass
class RoundResult:
    hidden_year: int
    status: TestStatus
    message: str
    metrics: dict[str, Any] = field(default_factory=dict)
    train_ephemeris: dict[str, Any] | None = None
    windows: list[dict[str, Any]] = field(default_factory=list)
    access_log: list[dict[str, Any]] = field(default_factory=list)
    stacked: dict[str, np.ndarray] = field(default_factory=dict)  # for plots only

    def to_dict(self) -> dict[str, Any]:
        return {
            "hidden_year": self.hidden_year,
            "status": self.status.value,
            "message": self.message,
            "metrics": self.metrics,
            "train_ephemeris": self.train_ephemeris,
            "windows": self.windows,
            "access_log": self.access_log,
        }


@dataclass
class HoldoutOutcome:
    test: TestResult
    rounds: list[RoundResult]

    def to_dict(self) -> dict[str, Any]:
        return {"test": self.test.to_dict(), "rounds": [r.to_dict() for r in self.rounds]}


def _window_depth(
    t_all: np.ndarray, f_all: np.ndarray, in_window: np.ndarray, center: float, half: float
) -> tuple[float, int, int, np.ndarray] | None:
    """Box depth at ``center`` relative to a line fitted to the window's out-of-box points."""
    box = in_window & (np.abs(t_all - center) <= half)
    out = ~box
    n_in, n_out = int(box.sum()), int(out.sum())
    if n_in == 0 or n_out < 10:
        return None
    x = t_all - center
    coef = np.polyfit(x[out], f_all[out], 1)
    line = np.polyval(coef, x)
    depth = float(np.mean(line[box] - f_all[box]))
    return depth, n_in, n_out, f_all[out] - line[out]


def _measure(
    hidden: HiddenYear,
    windows: Sequence[PredictedWindow],
    ephemeris: Ephemeris,
    duration: float,
    cadence_days: float,
    params: HoldoutParams,
) -> dict[str, Any]:
    """Stacked box depth inside the predicted windows, scanning one period correction.

    The ephemeris error is dominated by the period error, so the transit in window
    m is expected near ``t_pred(m) + (m - n_ref) * dP``. ``dP`` is scanned over
    +-``timing_sigma`` times the train period error, with steps that move the
    farthest window by at most duration/8 (at most 1001 steps).

    For each ``dP`` and window, the depth is the mean in-box deficit relative to a
    straight line fitted to the window's out-of-box points (rest of the window plus
    its baseline bands). Window depths are combined with inverse-variance weights;
    the error is the larger of the white-noise error and the window-to-window
    scatter divided by sqrt(n) (when n >= 3), so correlated noise does not
    masquerade as a detection. The reported SNR is the maximum over the scan. The
    phase-0.5 control windows use the same procedure: their SNR shows the
    false-alarm level of this look-elsewhere search.
    """
    eligible = []
    for window in windows:
        t_in, f_in = hidden.window(window.t_pred, window.half_width)
        t_b, f_b = hidden.local_baseline(window.t_pred, window.half_width)
        expected_in = 2.0 * window.half_width / cadence_days
        expected_b = 2.0 * (window.baseline_outer - window.baseline_inner) / cadence_days
        if f_in.size < params.min_window_coverage * expected_in:
            continue
        if f_b.size < params.min_window_coverage * expected_b:
            continue
        t_all = np.concatenate([t_in, t_b])
        f_all = np.concatenate([f_in, f_b])
        in_window = np.concatenate([np.ones(t_in.size, bool), np.zeros(t_b.size, bool)])
        eligible.append((window, t_all, f_all, in_window))
    if not eligible:
        return {"n_windows_with_data": 0}

    lever = max(abs(item[0].epoch - ephemeris.n_ref) for item in eligible)
    span = params.timing_sigma * ephemeris.period_err
    if span > 0 and lever > 0:
        n_steps = int(min(1001, np.ceil(2.0 * span * lever / (duration / 8.0)) + 1))
        grid = np.linspace(-span, span, max(n_steps, 3))
    else:
        grid = np.zeros(1)

    half = duration / 2.0
    best: dict[str, Any] | None = None
    for dp in grid:
        rows = []
        for window, t_all, f_all, in_window in eligible:
            center = window.t_pred + (window.epoch - ephemeris.n_ref) * dp
            measured = _window_depth(t_all, f_all, in_window, center, half)
            if measured is not None:
                rows.append(measured)
        if not rows:
            continue
        sigma = robust_sigma(np.concatenate([r[3] for r in rows]))
        if not (sigma > 0):
            continue
        depths = np.array([r[0] for r in rows])
        errors = np.array([sigma * math.sqrt(1.0 / r[1] + 1.0 / r[2]) for r in rows])
        weights = 1.0 / errors**2
        depth = float(np.sum(weights * depths) / np.sum(weights))
        white = float(1.0 / math.sqrt(np.sum(weights)))
        scatter = (
            float(np.std(depths, ddof=1) / math.sqrt(depths.size)) if depths.size >= 3 else 0.0
        )
        error = max(white, scatter)
        snr = depth / error
        if best is None or snr > best["snr"]:
            best = {
                "snr": snr,
                "depth": depth,
                "error": error,
                "white_error": white,
                "scatter_error": scatter,
                "dp": float(dp),
                "n_windows": len(rows),
                "n_in": int(sum(r[1] for r in rows)),
            }
    if best is None:
        # No window could be measured at any period correction: nothing was examined.
        return {"n_windows_with_data": 0, "n_windows_unmeasurable": len(eligible)}

    stacked_dt, stacked_flux = [], []
    for window, t_all, f_all, in_window in eligible:
        center = window.t_pred + (window.epoch - ephemeris.n_ref) * best["dp"]
        out = ~(in_window & (np.abs(t_all - center) <= half))
        if out.sum() >= 10:
            line = np.polyval(np.polyfit(t_all[out] - center, f_all[out], 1), t_all - center)
            stacked_dt.extend((t_all - center).tolist())
            stacked_flux.extend((f_all / line).tolist())
    return {
        "n_windows_with_data": best["n_windows"],
        "depth_ppm": best["depth"] * 1e6,
        "depth_err_ppm": best["error"] * 1e6,
        "white_err_ppm": best["white_error"] * 1e6,
        "scatter_err_ppm": best["scatter_error"] * 1e6,
        "snr": best["snr"],
        "best_period_correction_days": best["dp"],
        "period_correction_scan_days": float(span),
        "n_scan_steps": int(grid.size),
        "n_in_box_points": best["n_in"],
        "stacked_dt": np.asarray(stacked_dt),
        "stacked_flux": np.asarray(stacked_flux),
    }


def _predict_windows(
    ephemeris: Ephemeris, duration: float, spans: list[tuple[float, float]], params: HoldoutParams
) -> list[PredictedWindow]:
    windows: list[PredictedWindow] = []
    for kind, phase in (("transit", 0.0), ("control", 0.5)):
        for start, end in spans:
            first = math.ceil((start - ephemeris.t_ref) / ephemeris.period - phase)
            last = math.floor((end - ephemeris.t_ref) / ephemeris.period - phase)
            for m in range(first, last + 1):
                epoch = ephemeris.n_ref + m
                t_pred, sigma_t = ephemeris.predict(epoch)
                t_pred += phase * ephemeris.period
                half = duration / 2.0 + params.timing_sigma * sigma_t
                windows.append(
                    PredictedWindow(
                        kind=kind,
                        epoch=epoch,
                        t_pred=float(t_pred),
                        half_width=float(half),
                        baseline_inner=float(half + params.baseline_gap_durations * duration),
                        baseline_outer=float(half + params.baseline_outer_durations * duration),
                    )
                )
    return windows


def hidden_window_fraction(
    windows: Sequence[PredictedWindow], spans: Sequence[tuple[float, float]]
) -> float:
    """Fraction of the hidden sectors' time spans covered by the union of the transit
    windows (control windows do not count). Metadata only: no hidden cadence is used."""
    total = sum(max(0.0, end - start) for start, end in spans)
    if total <= 0:
        return 0.0
    covered = 0.0
    for start, end in spans:
        pieces = sorted(
            (max(start, w.t_pred - w.half_width), min(end, w.t_pred + w.half_width))
            for w in windows
            if w.kind == "transit"
        )
        lo = hi = None
        for a, b in pieces:
            if b <= a:
                continue
            if hi is None or a > hi:
                if hi is not None:
                    covered += hi - lo
                lo, hi = a, b
            else:
                hi = max(hi, b)
        if hi is not None:
            covered += hi - lo
    return covered / total


# --- M4 piece 4: replica spans and the hidden-window variance by empirical replicas -------------
# Revision 4 of the corrections plan, section 1, with the readings of
# docs/validation/v0.2.1/reopen/m4-implementation-map.md, Amendments 6, 10 and 11. Used only with
# gauntlet.corrections.active; the M3 path above is unchanged.

REPLICA_PHASE_DENOMINATORS = (4, 8, 16, 32, 64)
MIN_BASELINE_PER_PARAMETER = 20
MAX_CONDITION = 1e6
MAD_SCALE = 1.4826


def replica_phases() -> list[float]:
    """0.25, 0.75, then each dyadic level in increasing phase, down to a spacing of 1/64."""
    out: list[float] = []
    for d in REPLICA_PHASE_DENOMINATORS:
        out += [j / d for j in range(1, d, 2)]
    return out


def _closed_overlap(a0: float, a1: float, intervals: Sequence[tuple[float, float]]) -> bool:
    return any(a0 <= b1 and b0 <= a1 for b0, b1 in intervals)


def _union_length(intervals: Sequence[tuple[float, float]], lo: float, hi: float) -> float:
    pieces = sorted((max(lo, a), min(hi, b)) for a, b in intervals if min(hi, b) > max(lo, a))
    total, start, end = 0.0, None, None
    for a, b in pieces:
        if end is None or a > end:
            if end is not None:
                total += end - start
            start, end = a, b
        else:
            end = max(end, b)
    if end is not None:
        total += end - start
    return total


def register_replicas(
    ephemeris: Ephemeris,
    windows: Sequence[PredictedWindow],
    spans: Sequence[tuple[float, float]],
) -> list[PredictedWindow]:
    """The replica spans of revision 4, 1, from metadata only (Amendment 11): ``L = 2
    max(baseline_outer)``, the mask ``max(baseline_inner)`` and the box half-width
    ``max(half_width)`` over the transit windows; closed intervals for every overlap."""
    transit = [w for w in windows if w.kind == "transit"]
    if not transit or not ephemeris.period > 0:
        return []
    outer = max(w.baseline_outer for w in transit)
    inner = max(w.baseline_inner for w in transit)
    half = max(w.half_width for w in transit)
    measured = [(w.t_pred - w.baseline_outer, w.t_pred + w.baseline_outer) for w in windows]
    masks = [
        [(w.t_pred - w.baseline_inner, w.t_pred + w.baseline_inner) for w in windows] for _ in spans
    ]
    accepted: list[PredictedWindow] = []
    taken: list[tuple[float, float]] = []
    for phase in replica_phases():
        centers = []
        for i, (lo, hi) in enumerate(spans):
            m0 = math.ceil((lo - ephemeris.t_ref) / ephemeris.period - phase)
            m1 = math.floor((hi - ephemeris.t_ref) / ephemeris.period - phase)
            for m in range(m0, m1 + 1):
                centers.append((ephemeris.t_ref + (m + phase) * ephemeris.period, i, m))
        for center, i, m in sorted(centers):
            lo, hi = spans[i]
            a0, a1 = center - outer, center + outer
            if a0 < lo or a1 > hi:
                continue
            if _closed_overlap(a0, a1, measured) or _closed_overlap(a0, a1, taken):
                continue
            trial = [*masks[i], (center - inner, center + inner)]
            if _union_length(trial, lo, hi) / (hi - lo) > 0.5:
                continue
            masks[i] = trial
            taken.append((a0, a1))
            accepted.append(
                PredictedWindow("replica", ephemeris.n_ref + m, float(center), half, inner, outer)
            )
    return accepted


def period_grid(
    ephemeris: Ephemeris, windows: Sequence[PredictedWindow], duration: float, params: HoldoutParams
) -> np.ndarray:
    """The period-correction grid, from metadata before any read (Amendment 6): the extent and
    step of ``_measure``, odd, exactly symmetric, containing 0."""
    transit = [w for w in windows if w.kind == "transit"]
    lever = max((abs(w.epoch - ephemeris.n_ref) for w in transit), default=0)
    span = params.timing_sigma * ephemeris.period_err
    if not (span > 0 and lever > 0):
        return np.zeros(1)
    n = int(min(1001, np.ceil(2.0 * span * lever / (duration / 8.0)) + 1))
    n = max(n, 3)
    if n % 2 == 0:
        n += 1
    side = np.linspace(0.0, span, n // 2 + 1)
    return np.concatenate([-side[:0:-1], side])


def best_dp_index(snr: np.ndarray, grid: np.ndarray) -> int | None:
    """The index of the largest finite SNR; ties to the smaller |dP|, then the negative side."""
    snr = np.asarray(snr, dtype=float)
    finite = np.isfinite(snr)
    if not finite.any():
        return None
    top = np.max(snr[finite])
    candidates = [i for i in range(snr.size) if finite[i] and snr[i] == top]
    return min(candidates, key=lambda i: (abs(grid[i]), grid[i] > 0))


@dataclass(frozen=True)
class WindowDepth:
    depth: float | None
    n_in: int
    n_base: int
    n_params: int
    reason: str | None


def window_depth(
    t: np.ndarray,
    f: np.ndarray,
    in_window: np.ndarray,
    center: float,
    half: float,
    frequencies: Sequence[float] = (),
    *,
    cadence: float,
    coverage: float = 0.5,
) -> WindowDepth:
    """Revision 3, 4.1 at one center (Amendment 11): the box ``|t - c| <= half`` within the
    window's cadences, the baseline model fitted to every other cadence (a line plus the given
    frequencies, in decreasing train amplitude), the degeneracy rule and its fallback, and
    ``d = mean over the box of (model - flux)``. With one noise level per window, the weights
    1/sigma_w,hidden^2 are equal, so the fit is the unweighted one."""
    t = np.asarray(t, dtype=float)
    f = np.asarray(f, dtype=float)
    box = np.asarray(in_window, dtype=bool) & (np.abs(t - center) <= half)
    base = ~box
    n_in, n_base = int(box.sum()), int(base.sum())
    if n_in < coverage * 2.0 * half / cadence or n_in == 0:
        return WindowDepth(None, n_in, n_base, 0, "box_coverage")
    x = t - center

    def design(n_freq: int, line: bool) -> np.ndarray:
        cols = [np.ones_like(x)]
        if line:
            cols.append(x)
        for nu in list(frequencies)[:n_freq]:
            cols += [np.sin(2 * np.pi * nu * t), np.cos(2 * np.pi * nu * t)]
        return np.column_stack(cols)

    options = [(k, True) for k in range(len(frequencies), -1, -1)] + [(0, False)]
    for n_freq, line in options:
        full = design(n_freq, line)
        k = full.shape[1]
        if n_base < MIN_BASELINE_PER_PARAMETER * k:
            continue
        xb = full[base]
        scale = np.linalg.norm(xb, axis=0)
        if not np.all(scale > 0):
            continue
        normal = (xb / scale).T @ (xb / scale)
        if not np.linalg.cond(normal) <= MAX_CONDITION:
            continue
        coef, *_ = np.linalg.lstsq(xb, f[base], rcond=None)
        model = full[box] @ coef
        return WindowDepth(float(np.mean(model - f[box])), n_in, n_base, k, None)
    return WindowDepth(None, n_in, n_base, 0, "degenerate_baseline")


@dataclass
class ReplicaPoint:
    dp: float
    depths: list[float | None]
    n_rep: int
    var_rep: float


@dataclass
class ReplicaStats:
    status: str  # "ok" or "hidden_noise_undetermined"
    per_dp: list[ReplicaPoint]
    noise: Any
    excluded_sectors: list[int]
    dropped: dict[str, int]
    # M4 piece 7: how many window fits (over the replicas and the dP grid) used how many baseline
    # parameters, keyed by that number (the degeneracy fallback can drop sinusoids: Amendment 22)
    terms: dict[str, int] = field(default_factory=dict)
    # the R_min study (map Amendment 26, 3): the noise estimate alone undetermined, apart from the
    # replica counts against r_min
    noise_undetermined: bool = False


def _count_terms(terms: dict[str, int], d: WindowDepth) -> None:
    if d.depth is not None:
        key = str(d.n_params)
        terms[key] = terms.get(key, 0) + 1


def _sector_of(t: float, sectors: Sequence[SectorInfo]) -> int | None:
    for s in sectors:
        if s.t_start <= t <= s.t_end:
            return int(s.sector)
    return None


def _read(hidden: HiddenYear, w: PredictedWindow):
    t_in, f_in = hidden.window(w.t_pred, w.half_width)
    t_b, f_b = hidden.local_baseline(w.t_pred, w.half_width)
    t = np.concatenate([t_in, t_b])
    f = np.concatenate([f_in, f_b])
    order = np.argsort(t, kind="stable")
    in_window = np.concatenate([np.ones(t_in.size, bool), np.zeros(t_b.size, bool)])
    return t[order], f[order], in_window[order], t_b, f_b


def _band_covered(w: PredictedWindow, n_band: int, cadence: float, coverage: float) -> bool:
    return n_band >= coverage * 2.0 * (w.baseline_outer - w.baseline_inner) / cadence


def _robust_var(values: Sequence[float]) -> float:
    v = np.asarray(values, dtype=float)
    if v.size == 0:
        return float("nan")
    return float((MAD_SCALE * np.median(np.abs(v - np.median(v)))) ** 2)


def replica_stats(
    hidden: HiddenYear,
    replicas: Sequence[PredictedWindow],
    ephemeris: Ephemeris,
    duration: float,
    cadence: float,
    plan: TessTestPlan,
    sectors: Sequence[SectorInfo],
    grid: np.ndarray,
    frequencies: Sequence[float] = (),
) -> ReplicaStats:
    """The hidden noise of O2 (Amendment 10) and the replica depths at every dP of the grid
    (Amendment 11). Reads the replicas only."""
    from refute.packs.tess.rednoise import estimate

    c = plan.gauntlet.corrections
    params = plan.gauntlet.holdout_by_year
    dropped: dict[str, int] = {}
    reads = []
    band_t, band_f, band_s = [], [], []
    for r in replicas:
        t, f, in_window, t_b, f_b = _read(hidden, r)
        sector = _sector_of(r.t_pred, sectors)
        ok = _band_covered(r, t_b.size, cadence, params.min_window_coverage)
        if not ok:
            dropped["band_coverage"] = dropped.get("band_coverage", 0) + 1
        reads.append((r, t, f, in_window, sector, ok))
        if ok and sector is not None:
            band_t.append(t_b)
            band_f.append(f_b)
            band_s.append(np.full(t_b.size, sector))
    noise = None
    excluded: list[int] = []
    if band_t:
        tt = np.concatenate(band_t)
        order = np.argsort(tt, kind="stable")
        tt = tt[order]
        ff = np.concatenate(band_f)[order]
        ss = np.concatenate(band_s)[order]
        n_t = max(1, int(round(duration / cadence)))
        noise = estimate(
            tt, ff - 1.0, ss, np.ones(tt.size, bool), n_t, c.gap_split, cadence, c.b_min
        )
        excluded = noise.excluded_sectors
    undetermined = noise is None or noise.undetermined
    per_dp: list[ReplicaPoint] = []
    terms: dict[str, int] = {}
    for dp in grid:
        depths: list[float | None] = []
        for r, t, f, in_window, sector, ok in reads:
            if not ok or sector is None or sector in excluded or undetermined:
                depths.append(None)
                continue
            center = r.t_pred + (r.epoch - ephemeris.n_ref) * dp
            d = window_depth(
                t,
                f,
                in_window,
                center,
                duration / 2.0,
                frequencies,
                cadence=cadence,
                coverage=params.min_window_coverage,
            )
            _count_terms(terms, d)
            depths.append(d.depth)
        values = [d for d in depths if d is not None]
        per_dp.append(ReplicaPoint(float(dp), depths, len(values), _robust_var(values)))
    noise_undetermined = undetermined
    if not undetermined and any(p.n_rep < c.r_min for p in per_dp):
        undetermined = True
    for _, _, _, _, sector, ok in reads:
        if ok and sector in excluded:
            dropped["excluded_sector"] = dropped.get("excluded_sector", 0) + 1
    status = "hidden_noise_undetermined" if undetermined else "ok"
    return ReplicaStats(status, per_dp, noise, excluded, dropped, terms, noise_undetermined)


def measure_windows(
    hidden: HiddenYear,
    windows: Sequence[PredictedWindow],
    ephemeris: Ephemeris,
    duration: float,
    cadence: float,
    plan: TessTestPlan,
    sectors: Sequence[SectorInfo],
    grid: np.ndarray,
    stats: ReplicaStats,
    frequencies: Sequence[float] = (),
) -> dict[str, Any]:
    """The windows' stack at every dP with the replicas' variance (revision 4, 1; Amendment 11).
    Called only after ``replica_stats`` (and, from piece 5, decision 2)."""
    params = plan.gauntlet.holdout_by_year
    static: dict[str, int] = {}
    kept = []
    last_span: tuple[float, float] | None = None
    for w in sorted(windows, key=lambda w: w.t_pred):
        sector = _sector_of(w.t_pred, sectors)
        if sector is None or sector in stats.excluded_sectors:
            static["excluded_sector"] = static.get("excluded_sector", 0) + 1
            continue
        span = (w.t_pred - w.baseline_outer, w.t_pred + w.baseline_outer)
        if last_span is not None and _closed_overlap(span[0], span[1], [last_span]):
            static["shared_cadences"] = static.get("shared_cadences", 0) + 1
            continue
        t, f, in_window, t_b, _ = _read(hidden, w)
        if not _band_covered(w, t_b.size, cadence, params.min_window_coverage):
            static["band_coverage"] = static.get("band_coverage", 0) + 1
            continue
        last_span = span
        kept.append((w, t, f, in_window))
    per_dp = []
    reasons_at = []
    terms: dict[str, int] = {}
    for k, dp in enumerate(grid):
        depths, reasons = [], {}
        for w, t, f, in_window in kept:
            center = w.t_pred + (w.epoch - ephemeris.n_ref) * dp
            d = window_depth(
                t,
                f,
                in_window,
                center,
                duration / 2.0,
                frequencies,
                cadence=cadence,
                coverage=params.min_window_coverage,
            )
            _count_terms(terms, d)
            if d.depth is None:
                reasons[d.reason] = reasons.get(d.reason, 0) + 1
            else:
                depths.append(d.depth)
        n = len(depths)
        var_rep = stats.per_dp[k].var_rep
        row = {"dp": float(dp), "n_valid": n, "depth": None, "error": None, "snr": float("nan")}
        if n >= params.min_predicted_transits and var_rep > 0:
            mean = float(np.mean(depths))
            error = math.sqrt(var_rep / n)
            if n >= 3:
                error = max(error, float(np.std(depths, ddof=1)) / math.sqrt(n))
            row.update(depth=mean, error=error, snr=mean / error)
        per_dp.append(row)
        reasons_at.append(reasons)
    best = best_dp_index(np.array([r["snr"] for r in per_dp]), grid)
    if best is None:
        dropped = dict(static)
        for key, value in reasons_at[0].items():
            dropped[key] = dropped.get(key, 0) + value
        return {
            "status": "too_few_windows",
            "depth": None,
            "n_valid": per_dp[0]["n_valid"],
            "per_dp": per_dp,
            "dropped": dropped,
            "terms": terms,
        }
    dropped = dict(static)
    for key, value in reasons_at[best].items():
        dropped[key] = dropped.get(key, 0) + value
    row = per_dp[best]
    return {
        "status": "ok",
        "dp": row["dp"],
        "depth": row["depth"],
        "error": row["error"],
        "snr": row["snr"],
        "n_valid": row["n_valid"],
        "n_rep": stats.per_dp[best].n_rep,
        "var_rep": stats.per_dp[best].var_rep,
        "per_dp": per_dp,
        "dropped": dropped,
        "terms": terms,
    }


def measure_with_replicas(
    hidden: HiddenYear,
    windows: Sequence[PredictedWindow],
    replicas: Sequence[PredictedWindow],
    ephemeris: Ephemeris,
    duration: float,
    cadence: float,
    plan: TessTestPlan,
    sectors: Sequence[SectorInfo],
    grid: np.ndarray,
    barrier=None,
    frequencies: Sequence[float] = (),
) -> dict[str, Any]:
    """Replicas first (the whole grid), then the barrier (``barrier(stats)`` returns a reason to
    stop, piece 5's decision 2), and only then the windows (Amendment 11)."""
    stats = replica_stats(
        hidden, replicas, ephemeris, duration, cadence, plan, sectors, grid, frequencies
    )
    if stats.status != "ok":
        return {"status": stats.status, "depth": None, "stats": stats, "dropped": stats.dropped}
    if barrier is not None:
        reason = barrier(stats)
        if reason is not None:
            return {"status": reason, "depth": None, "stats": stats, "dropped": stats.dropped}
    result = measure_windows(
        hidden, windows, ephemeris, duration, cadence, plan, sectors, grid, stats, frequencies
    )
    result["stats"] = stats
    return result


def _empty_validity(plan: TessTestPlan) -> dict[str, Any]:
    params = plan.gauntlet.holdout_by_year
    return {
        "applied": params.require_valid_train,
        "train_snr": None,
        "min_train_snr": plan.gauntlet.snr.min_snr,
        "duration_period_ratio": None,
        "max_duration_period_ratio": params.max_train_duration_period_ratio,
        "hidden_window_fraction": None,
        "max_hidden_window_fraction": params.max_hidden_window_fraction,
        "reasons": [],
    }


def train_validity(
    candidate: Candidate,
    plan: TessTestPlan,
    windows: Sequence[PredictedWindow] | None = None,
    spans: Sequence[tuple[float, float]] | None = None,
) -> dict[str, Any]:
    """Rules (a)-(c) for a train-only candidate. (c) is evaluated only when the
    predicted windows and the hidden sectors' spans are given."""
    params = plan.gauntlet.holdout_by_year
    out = _empty_validity(plan)
    ratio = candidate.duration / candidate.period
    out["train_snr"] = float(candidate.snr)
    out["duration_period_ratio"] = float(ratio)
    reasons = []
    if check_snr(candidate, plan.gauntlet.snr).status is not TestStatus.PASS:
        reasons.append(REASON_TRAIN_SNR)
    if not ratio <= params.max_train_duration_period_ratio:
        reasons.append(REASON_DURATION_RATIO)
    if windows is not None and spans is not None:
        fraction = hidden_window_fraction(windows, spans)
        out["hidden_window_fraction"] = float(fraction)
        if not fraction <= params.max_hidden_window_fraction:
            reasons.append(REASON_WINDOW_FRACTION)
    out["reasons"] = reasons
    return out


def _invalid_message(validity: dict[str, Any]) -> str:
    parts = []
    for reason in validity["reasons"]:
        if reason == REASON_TRAIN_SNR:
            parts.append(f"train SNR {validity['train_snr']:.2f} < {validity['min_train_snr']:g}")
        elif reason == REASON_DURATION_RATIO:
            parts.append(
                f"duration/period {validity['duration_period_ratio']:.3f} > "
                f"{validity['max_duration_period_ratio']:g}"
            )
        else:
            parts.append(
                f"transit windows cover {validity['hidden_window_fraction']:.3f} of the hidden "
                f"year > {validity['max_hidden_window_fraction']:g}"
            )
    return "the train-only candidate is not a valid basis for a prediction: " + "; ".join(parts)


def _minus_raw(curve: LightCurveData, model: np.ndarray) -> LightCurveData:
    return LightCurveData(curve.time, curve.flux - model, curve.flux_err, curve.sector, curve.year)


@dataclass
class RoundPlan:
    """Everything a round decides before the hidden year is read."""

    decided: RoundResult | None
    train: Candidate | None = None
    ephemeris: Ephemeris | None = None
    windows: list[PredictedWindow] = field(default_factory=list)
    train_info: dict[str, Any] = field(default_factory=dict)
    # M4 piece 5 (switch on): the masked train curve and its per-point sigma, for the replicas
    # (from piece 7 the masked train curve without S'_train: map Amendment 22).
    train_flat: LightCurveData | None = None
    train_sigma: np.ndarray | None = None
    # M4 piece 7: the train fundamentals in decreasing train amplitude, for every window's
    # baseline (the hidden replicas, the transit and control windows, the train replicas).
    frequencies: list[float] = field(default_factory=list)


def plan_round(
    train_raw: LightCurveData,
    hidden_spans: Sequence[tuple[float, float]],
    hidden_year: int,
    plan: TessTestPlan,
) -> RoundPlan:
    """The pre-read part of a round, from the train data and the hidden sectors' time
    spans only. ``decided`` is set when the round ends here (INCONCLUSIVE)."""
    params = plan.gauntlet.holdout_by_year
    cadence = plan.data.exptime_seconds / 86400.0
    empty = {"train_validity": _empty_validity(plan)}
    if len(train_raw) == 0:
        return RoundPlan(
            RoundResult(hidden_year, TestStatus.INCONCLUSIVE, "no training data", metrics=empty)
        )

    corrections_on = plan.gauntlet.corrections.active
    train_flat = detrend(train_raw, plan.detrend)
    search_curve = train_flat
    pw_train = None
    pw_record: dict[str, Any] = {}
    if corrections_on:
        # M4 piece 7 (map Amendments 22 and 23): the train components found on the train curve,
        # refitted on the raw train curve and subtracted before its detrending, for the search
        from refute.packs.tess.prewhiten import prewhiten
        from refute.packs.tess.prewhiten import refit as refit_components

        pw_train = prewhiten(train_flat, plan)
        pw_record = pw_train.to_dict()
        if pw_train.components:
            no_mask = np.zeros(train_raw.time.size, bool)
            fitted = refit_components(train_raw, pw_train.components, no_mask, plan)
            pw_record["search_refit_reason"] = fitted.reason
            pw_record["search_left_out"] = list(fitted.sectors_left_out)
            if fitted.reason is None:
                search_curve = detrend(_minus_raw(train_raw, fitted.model), plan.detrend)
        empty = {**empty, "prewhitening": pw_record}
    search = search_period(search_curve, plan.search)
    train: Candidate | None = search.candidate
    if train is None or not (train.depth > 0):
        return RoundPlan(
            RoundResult(
                hidden_year,
                TestStatus.INCONCLUSIVE,
                "the train-only search found no candidate",
                metrics=empty,
            )
        )

    extra: dict[str, Any] = {}
    if corrections_on:
        # M4 piece 5 (map Amendment 12 and its addendum): the train candidate refitted on the
        # masked train curve, then the gate of Amendment 7; an undetermined gate ends the round.
        from refute.packs.tess.pipeline import _bls_gate
        from refute.packs.tess.rednoise import event_noise
        from refute.packs.tess.search import finalize_candidate

        mask_half = plan.detrend.transit_mask_half_width_durations * train.duration
        train_mask = transit_mask(train_raw.time, train.period, train.t0, mask_half)
        train_flat2 = detrend(train_raw, plan.detrend, mask=train_mask)
        replicas_curve = train_flat2  # the train replicas: without S'_train (Amendment 22)
        if pw_train is not None and pw_train.components:
            # Amendment 23: S'_train refitted on the raw train curve with the train candidate's
            # mask, subtracted before the masked detrending
            fitted = refit_components(train_raw, pw_train.components, train_mask, plan)
            pw_record["refit_reason"] = fitted.reason
            pw_record["refit_left_out"] = list(fitted.sectors_left_out)
            if fitted.reason is None:
                train_flat2 = detrend(
                    _minus_raw(train_raw, fitted.model), plan.detrend, mask=train_mask
                )
        sigma = per_point_sigma(
            train_flat2, transit_mask(train_flat2.time, train.period, train.t0, mask_half)
        )
        refit = finalize_candidate(
            train_flat2, train.period, train.duration, plan.search, train.sde, sigma
        )
        noise = event_noise(train_flat2, None, refit.period, refit.t0, refit.duration, plan)
        corrected, gate = _bls_gate(refit, train_flat2, sigma, noise, None, plan.gauntlet)
        extra = {
            "train_bls_snr": refit.snr,
            "train_gate": gate.to_dict(),
            # the marker of map Amendment 17: this round ran the M4 holdout path
            "corrections_path": "m4_holdout",
            "prewhitening": pw_record,
        }
        if gate.status is TestStatus.INCONCLUSIVE:
            return RoundPlan(
                RoundResult(
                    hidden_year,
                    TestStatus.INCONCLUSIVE,
                    f"train_noise_undetermined: {gate.message}",
                    metrics={**empty, **extra, "reason": "train_noise_undetermined"},
                )
            )
        train = corrected

    validity = train_validity(train, plan)
    if validity["reasons"] and params.require_valid_train:
        metrics = {"train_candidate": train.to_dict(), "train_validity": validity, **extra}
        if corrections_on:
            metrics["reason"] = validity["reasons"][0]
        return RoundPlan(
            RoundResult(
                hidden_year,
                TestStatus.INCONCLUSIVE,
                _invalid_message(validity),
                metrics=metrics,
            ),
            train=train,
        )

    if not corrections_on:
        mask_half = plan.detrend.transit_mask_half_width_durations * train.duration
        train_mask = transit_mask(train_raw.time, train.period, train.t0, mask_half)
        train_flat2 = detrend(train_raw, plan.detrend, mask=train_mask)
        sigma = per_point_sigma(
            train_flat2, transit_mask(train_flat2.time, train.period, train.t0, mask_half)
        )
    train_timing = None
    if plan.gauntlet.corrections.active:
        # M4 piece 3: the train timing with the trapezoid template of the train candidate.
        corrected = corrected_transit_times(
            train_flat2, train.period, train.t0, train.duration, sigma, plan
        )
        times, train_timing = corrected.times, corrected.to_dict()
    else:
        times = measure_transit_times(
            train_flat2,
            train.period,
            train.t0,
            train.duration,
            train.depth,
            sigma,
            cadence_days=cadence,
            step_minutes=params.timing_step_minutes,
            scan_half_width_durations=params.timing_scan_half_width_durations,
        )
    train_info: dict[str, Any] = {
        "train_candidate": train.to_dict(),
        "n_transit_times": len(times),
        "train_validity": validity,
    }
    if train_timing is not None:
        train_info["train_timing"] = train_timing  # switch on only (M4 piece 3)
    train_info.update(extra)  # switch on only (M4 piece 5); empty otherwise
    if len(times) < params.min_train_transits:
        return RoundPlan(
            RoundResult(
                hidden_year,
                TestStatus.INCONCLUSIVE,
                f"only {len(times)} train transit times (< {params.min_train_transits})",
                metrics=train_info,
            ),
            train=train,
        )
    ephemeris = fit_linear_ephemeris(times)

    windows = _predict_windows(ephemeris, train.duration, list(hidden_spans), params)
    transit_windows = [w for w in windows if w.kind == "transit"]

    max_sigma_t = max(
        ((w.half_width - train.duration / 2) / params.timing_sigma for w in transit_windows),
        default=0.0,
    )
    if max_sigma_t > params.max_timing_sigma_durations * train.duration:
        # Issue #2: the train-only ephemeris cannot place the hidden transits to
        # within a transit duration, so a non-detection would not be informative.
        return RoundPlan(
            RoundResult(
                hidden_year,
                TestStatus.INCONCLUSIVE,
                f"train-only timing uncertainty in the hidden year ({max_sigma_t * 24:.2f} h) "
                f"exceeds {params.max_timing_sigma_durations:g} transit duration(s) "
                f"({train.duration * 24:.2f} h)",
                metrics={
                    **train_info,
                    "max_timing_sigma_days": max_sigma_t,
                    "n_predicted_transits": len(transit_windows),
                },
                train_ephemeris=ephemeris.to_dict(),
            ),
            train=train,
            ephemeris=ephemeris,
            windows=windows,
        )

    validity = train_validity(train, plan, windows, hidden_spans)
    train_info["train_validity"] = validity
    if validity["reasons"] and params.require_valid_train:
        metrics = {
            **train_info,
            "max_timing_sigma_days": max_sigma_t,
            "n_predicted_transits": len(transit_windows),
        }
        if corrections_on:
            metrics["reason"] = validity["reasons"][0]
        return RoundPlan(
            RoundResult(
                hidden_year,
                TestStatus.INCONCLUSIVE,
                _invalid_message(validity),
                metrics=metrics,
                train_ephemeris=ephemeris.to_dict(),
            ),
            train=train,
            ephemeris=ephemeris,
            windows=windows,
        )
    if corrections_on:
        freqs = pw_train.fundamentals if pw_train is not None else []
        return RoundPlan(None, train, ephemeris, windows, train_info, replicas_curve, sigma, freqs)
    return RoundPlan(None, train, ephemeris, windows, train_info)


def _round(
    raw: LightCurveData,
    sectors: Sequence[SectorInfo],
    hidden_year: int,
    plan: TessTestPlan,
) -> RoundResult:
    params = plan.gauntlet.holdout_by_year
    cadence = plan.data.exptime_seconds / 86400.0
    spans = [(s.t_start, s.t_end) for s in sectors if s.year == hidden_year]
    prepared = plan_round(raw.select(raw.year != hidden_year), spans, hidden_year, plan)
    if prepared.decided is not None:
        return prepared.decided
    if plan.gauntlet.corrections.active:
        return _round_corrected(raw, sectors, hidden_year, plan, prepared, enforce=True)[0]
    train, ephemeris, windows = prepared.train, prepared.ephemeris, prepared.windows
    assert train is not None and ephemeris is not None
    train_info = prepared.train_info
    transit_windows = [w for w in windows if w.kind == "transit"]
    control_windows = [w for w in windows if w.kind == "control"]

    hidden = HiddenYear(raw.select(raw.year == hidden_year), windows, plan)
    measured = _measure(hidden, transit_windows, ephemeris, train.duration, cadence, params)
    control = _measure(hidden, control_windows, ephemeris, train.duration, cadence, params)

    metrics: dict[str, Any] = {
        **train_info,
        "n_predicted_transits": len(transit_windows),
        "n_windows_with_data": measured.get("n_windows_with_data", 0),
        "n_windows_unmeasurable": measured.get("n_windows_unmeasurable", 0),
        "hidden_depth_ppm": measured.get("depth_ppm"),
        "hidden_depth_err_ppm": measured.get("depth_err_ppm"),
        "hidden_white_err_ppm": measured.get("white_err_ppm"),
        "hidden_scatter_err_ppm": measured.get("scatter_err_ppm"),
        "hidden_snr": measured.get("snr"),
        "train_depth_ppm": train.depth * 1e6,
        "best_period_correction_days": measured.get("best_period_correction_days"),
        "period_correction_scan_days": measured.get("period_correction_scan_days"),
        "n_scan_steps": measured.get("n_scan_steps"),
        "hidden_detrend_window_days": hidden.detrend_window_days,
        "control_phase05_depth_ppm": control.get("depth_ppm"),
        "control_phase05_snr": control.get("snr"),
        "max_timing_sigma_days": max((w.half_width - train.duration / 2) for w in transit_windows)
        / params.timing_sigma
        if transit_windows
        else None,
    }
    if measured.get("depth_ppm") is not None and measured.get("depth_err_ppm"):
        metrics["depth_consistency_sigma"] = abs(
            measured["depth_ppm"] - train.depth * 1e6
        ) / math.hypot(measured["depth_err_ppm"], train.depth_err * 1e6)

    result = RoundResult(
        hidden_year,
        TestStatus.INCONCLUSIVE,
        "",
        metrics=metrics,
        train_ephemeris=ephemeris.to_dict(),
        windows=[
            {"kind": w.kind, "epoch": w.epoch, "t_pred": w.t_pred, "half_width": w.half_width}
            for w in transit_windows
        ],
        access_log=hidden.access_log,
    )
    if "stacked_dt" in measured:
        result.stacked = {"dt": measured["stacked_dt"], "flux": measured["stacked_flux"]}
    n_used = metrics["n_windows_with_data"]
    if n_used < params.min_predicted_transits:
        result.message = (
            f"only {n_used} predicted transit window(s) contain data "
            f"(< {params.min_predicted_transits})"
        )
        return result
    snr = measured["snr"]
    if math.isfinite(snr) and snr >= params.min_snr:
        result.status = TestStatus.PASS
        result.message = f"transits found at {n_used} predicted windows, SNR {snr:.1f}"
    else:
        result.status = TestStatus.FAIL
        result.message = (
            f"no significant signal at {n_used} predicted windows (SNR {snr:.1f} < "
            f"{params.min_snr})"
        )
    return result


# --- M4 piece 5: the capacity decisions and the FAIL rule -------------------------------------
# Revision 3, 4.3 to 4.6, with revision 4, 1 and 2; map Amendment 12 and its addendum.

# b and s are the plan settings capacity_b and capacity_s (package 25, map Amendment 25; until
# then module settings, Amendment 12); k = 1 stays a module constant (a decision threshold).
CAPACITY_K = 1.0
ALPHA_RULE = 0.005


def capacity_threshold(min_snr: float, b: float, s: float, n_years: int) -> float:
    """``min_snr - b + Phi^-1(1 - alpha_round) s``, ``alpha_round = 0.005 / R``."""
    z = NormalDist().inv_cdf(1.0 - ALPHA_RULE / n_years)
    return float(min_snr - b + z * s)


def count_n_pred(windows: Sequence[PredictedWindow], spans: Sequence[tuple[float, float]]) -> int:
    """The transit windows whose measurement span lies inside one hidden sector span (closed)."""
    n = 0
    for w in windows:
        if w.kind != "transit":
            continue
        a0, a1 = w.t_pred - w.baseline_outer, w.t_pred + w.baseline_outer
        if any(lo <= a0 and a1 <= hi for lo, hi in spans):
            n += 1
    return n


def predicted_error(var_rep: Sequence[float], n_pred: int, margin: float = 1.0) -> float:
    """``margin * max over the grid of sqrt(var_rep(dP) / N_pred)``; NaN if undefined."""
    v = np.asarray(var_rep, dtype=float)
    if v.size == 0 or n_pred <= 0 or not np.all(np.isfinite(v)) or np.any(v < 0):
        return float("nan")
    return float(margin * np.sqrt(np.max(v) / n_pred))


def replicas_enough(counts: Sequence[int], r_min: int) -> bool:
    return len(counts) > 0 and all(c >= r_min for c in counts)


def fail_rule(
    snr: float,
    min_snr: float,
    d_train: float,
    e_train: float,
    d_hidden: float,
    e_hidden: float,
) -> tuple[str, str | None, float]:
    """Revision 3, 4.5 (Amendment 12): PASS if ``snr >= min_snr``; FAIL if not and ``Z = (d_train
    - d_hidden) / sqrt(e_train^2 + e_hidden^2) > 3`` (signed); otherwise INCONCLUSIVE
    ``not_detected_not_inconsistent``. A zero or non-finite error or statistic: INCONCLUSIVE."""
    values = (snr, d_train, e_train, d_hidden, e_hidden)
    if not all(math.isfinite(v) for v in values) or not e_hidden > 0 or not e_train > 0:
        return "INCONCLUSIVE", "non_finite_statistic", float("nan")
    z = (d_train - d_hidden) / math.sqrt(e_train**2 + e_hidden**2)
    if not math.isfinite(z):
        return "INCONCLUSIVE", "non_finite_statistic", float("nan")
    if snr >= min_snr:
        return "PASS", None, z
    if z > 3.0:
        return "FAIL", "inconsistent_with_train", z
    return "INCONCLUSIVE", "not_detected_not_inconsistent", z


def _train_spans(flat: LightCurveData) -> list[tuple[float, float]]:
    out = []
    for s in np.unique(flat.sector):
        t = flat.time[flat.sector == s]
        out.append((float(t.min()), float(t.max())))
    return out


def train_replica_stats(
    flat: LightCurveData,
    replicas: Sequence[PredictedWindow],
    ephemeris: Ephemeris,
    duration: float,
    cadence: float,
    plan: TessTestPlan,
    grid: np.ndarray,
    frequencies: Sequence[float] = (),
    terms: dict[str, int] | None = None,
) -> tuple[list[int], list[float]]:
    """The train replicas' depths on the masked train curve (Amendment 12), at every dP:
    ``(n_rep(dP), var_rep(dP))``; from piece 7 the window baseline carries the train
    fundamentals, as the hidden windows' does (Amendment 22)."""
    params = plan.gauntlet.holdout_by_year
    reads = []
    for r in replicas:
        dt = np.abs(flat.time - r.t_pred)
        in_w = dt <= r.half_width
        band = (dt > r.baseline_inner) & (dt <= r.baseline_outer)
        if not _band_covered(r, int(band.sum()), cadence, params.min_window_coverage):
            continue
        sel = in_w | band
        reads.append((r, flat.time[sel], flat.flux[sel], in_w[sel]))
    counts, variances = [], []
    for dp in grid:
        values = []
        for r, t, f, in_window in reads:
            center = r.t_pred + (r.epoch - ephemeris.n_ref) * dp
            d = window_depth(
                t,
                f,
                in_window,
                center,
                duration / 2.0,
                frequencies,
                cadence=cadence,
                coverage=params.min_window_coverage,
            )
            if terms is not None:
                _count_terms(terms, d)
            if d.depth is not None:
                values.append(d.depth)
        counts.append(len(values))
        variances.append(_robust_var(values))
    return counts, variances


def _twin_depth(
    hidden: HiddenYear,
    twin_model: np.ndarray,
    transit: Sequence[PredictedWindow],
    ephemeris: Ephemeris,
    duration: float,
    cadence: float,
    plan: TessTestPlan,
    sectors: Sequence[SectorInfo],
    result: dict[str, Any],
    frequencies: Sequence[float],
) -> float | None:
    """The noiseless twin's depth (map Amendment 26, 4): the same windows, cadences, baseline form
    and frequencies, the replica statistics cut and re-indexed to the ``dP`` chosen; the window
    coefficients estimated again."""
    stats = result["stats"]
    best = next(i for i, p in enumerate(stats.per_dp) if p.dp == result["dp"])
    one = ReplicaStats(
        stats.status,
        [stats.per_dp[best]],
        stats.noise,
        stats.excluded_sectors,
        stats.dropped,
        {},
        stats.noise_undetermined,
    )
    measured = measure_windows(
        hidden.twin(twin_model),
        transit,
        ephemeris,
        duration,
        cadence,
        plan,
        sectors,
        np.array([result["dp"]]),
        one,
        frequencies,
    )
    return measured.get("depth") if measured["status"] == "ok" else None


def _empty_derivation_fields() -> dict[str, Any]:
    """The fields of a calibration record that ``derive_round`` reads, before they are known."""
    return {
        "stage": None,
        "n_years": None,
        "train_n_rep": None,
        "hidden_n_rep": None,
        "hidden_noise_undetermined": None,
        "d_train": None,
        "e_train": None,
        "d_hidden": None,
        "e_hidden": None,
        "dp": None,
        "measurement_status": None,
    }


def _round_corrected(
    raw: LightCurveData,
    sectors: Sequence[SectorInfo],
    hidden_year: int,
    plan: TessTestPlan,
    prepared: RoundPlan,
    enforce: bool,
    twin_model: np.ndarray | None = None,
) -> tuple[RoundResult, dict[str, Any]]:
    """A round with the switch on (pieces 4 and 5). With ``enforce`` false (the calibration-only
    measurement) the two capacity decisions are recorded but do not stop the measurement."""
    params = plan.gauntlet.holdout_by_year
    c = plan.gauntlet.corrections
    cadence = plan.data.exptime_seconds / 86400.0
    train, eph, windows = prepared.train, prepared.ephemeris, prepared.windows
    assert train is not None and eph is not None and prepared.train_flat is not None
    hidden_sectors = [s for s in sectors if s.year == hidden_year]
    spans = [(s.t_start, s.t_end) for s in hidden_sectors]
    transit = [w for w in windows if w.kind == "transit"]
    control = [w for w in windows if w.kind == "control"]
    n_years = len(raw.years)
    threshold = capacity_threshold(params.min_snr, c.capacity_b, c.capacity_s, n_years)
    replicas = register_replicas(eph, windows, spans)
    grid = period_grid(eph, windows, train.duration, params)
    n_pred = count_n_pred(transit, spans)
    d_c = train.depth - CAPACITY_K * train.depth_err
    cap: dict[str, Any] = {
        "d_train": train.depth,
        "e_train": train.depth_err,
        "k": CAPACITY_K,
        "d_c": d_c,
        "n_pred": n_pred,
        "threshold": threshold,
        "n_years": n_years,
        "b": c.capacity_b,
        "s": c.capacity_s,
        "m_beta": c.m_beta,
        "grid": grid.tolist(),
        "n_replicas_hidden": len(replicas),
    }
    metrics: dict[str, Any] = {
        **prepared.train_info,
        "capacity": cap,
        "n_predicted_transits": len(transit),
    }
    record: dict[str, Any] = {
        "calibration_only": True,
        "hidden_year": hidden_year,
        "decision_1": None,
        "decision_2": None,
        "s_pred_1": None,
        "s_pred_2": None,
        "s_meas": None,
        "threshold": threshold,
        "reason": None,
        # the R_min study (map Amendment 26, 3): what derive_round reads
        **_empty_derivation_fields(),
        "n_years": n_years,
        "d_train": train.depth,
        "e_train": train.depth_err,
        "d_twin": None,
    }

    def stop(
        reason: str, access_log=None, stage: str | None = None
    ) -> tuple[RoundResult, dict[str, Any]]:
        metrics["reason"] = reason
        record["reason"] = reason
        record["stage"] = stage
        result = RoundResult(
            hidden_year,
            TestStatus.INCONCLUSIVE,
            reason,
            metrics=metrics,
            train_ephemeris=eph.to_dict(),
            access_log=access_log or [],
        )
        return result, record

    if n_pred == 0:
        cap["decision_1"] = record["decision_1"] = "no_predicted_window"
        return stop("no_predicted_window", stage="before_capacity")
    train_spans = _train_spans(prepared.train_flat)
    train_windows = _predict_windows(eph, train.duration, train_spans, params)
    train_reps = register_replicas(eph, train_windows, train_spans)
    freqs = list(prepared.frequencies)  # M4 piece 7: the train fundamentals (Amendment 22)
    # the frequencies requested and the baseline parameters each kind of window fit used
    window_terms: dict[str, Any] = {"requested_frequencies": freqs, "train_replicas": {}}
    metrics["window_terms"] = window_terms
    counts, variances = train_replica_stats(
        prepared.train_flat,
        train_reps,
        eph,
        train.duration,
        cadence,
        plan,
        grid,
        frequencies=freqs,
        terms=window_terms["train_replicas"],
    )
    cap["train_n_rep"] = counts
    cap["train_var_rep"] = variances
    record["train_n_rep"] = list(counts)
    if not replicas_enough(counts, c.r_min):
        cap["decision_1"] = record["decision_1"] = "train_replicas_below_r_min"
        return stop("train_replicas_below_r_min", stage="train_counts")
    e_pred_1 = predicted_error(variances, n_pred, c.m_beta)
    s_pred_1 = d_c / e_pred_1 if e_pred_1 > 0 else float("nan")
    decision_1 = (
        "pass"
        if math.isfinite(s_pred_1) and s_pred_1 >= threshold
        else "insufficient_capacity_train"
    )
    cap.update(e_pred_1=e_pred_1, s_pred_1=s_pred_1, decision_1=decision_1)
    record.update(decision_1=decision_1, s_pred_1=s_pred_1)
    if decision_1 != "pass" and enforce:
        return stop("insufficient_capacity_train")

    hidden = HiddenYear(raw.select(raw.year == hidden_year), windows + replicas, plan)

    def record_hidden(stats: ReplicaStats) -> None:
        record["hidden_n_rep"] = [p.n_rep for p in stats.per_dp]
        record["hidden_noise_undetermined"] = stats.noise_undetermined
        cap["hidden_n_rep"] = [p.n_rep for p in stats.per_dp]
        cap["hidden_var_rep"] = [p.var_rep for p in stats.per_dp]
        cap["hidden_noise"] = None if stats.noise is None else stats.noise.to_dict()
        cap["hidden_excluded_sectors"] = list(stats.excluded_sectors)

    def barrier(stats: ReplicaStats) -> str | None:
        record_hidden(stats)
        e_pred_2 = predicted_error(cap["hidden_var_rep"], n_pred)
        s_pred_2 = d_c / e_pred_2 if e_pred_2 > 0 else float("nan")
        decision_2 = (
            "pass"
            if math.isfinite(s_pred_2) and s_pred_2 >= threshold
            else "insufficient_capacity_hidden_noise"
        )
        cap.update(e_pred_2=e_pred_2, s_pred_2=s_pred_2, decision_2=decision_2)
        record.update(decision_2=decision_2, s_pred_2=s_pred_2)
        if decision_2 != "pass" and enforce:
            return decision_2
        return None

    result = measure_with_replicas(
        hidden,
        transit,
        replicas,
        eph,
        train.duration,
        cadence,
        plan,
        hidden_sectors,
        grid,
        barrier,
        frequencies=freqs,
    )
    if result.get("stats") is not None:
        window_terms["hidden_replicas"] = dict(result["stats"].terms)
    if "terms" in result:
        window_terms["transit"] = dict(result["terms"])
    if "hidden_n_rep" not in cap and result.get("stats") is not None:
        record_hidden(result["stats"])
    record["measurement_status"] = result["status"]
    if result["status"] != "ok":
        stats = result.get("stats")
        stage = "hidden_noise" if stats is not None and stats.status != "ok" else "measurement"
        return stop(result["status"], hidden.access_log, stage=stage)
    record.update(d_hidden=result["depth"], e_hidden=result["error"], dp=result["dp"])
    if twin_model is not None:
        record["d_twin"] = _twin_depth(
            hidden,
            twin_model,
            transit,
            eph,
            train.duration,
            cadence,
            plan,
            hidden_sectors,
            result,
            freqs,
        )

    status, reason, z = fail_rule(
        result["snr"],
        params.min_snr,
        train.depth,
        train.depth_err,
        result["depth"],
        result["error"],
    )
    record["s_meas"] = result["snr"]
    metrics.update(
        {
            "n_windows_with_data": result["n_valid"],
            "hidden_depth_ppm": result["depth"] * 1e6,
            "hidden_depth_err_ppm": result["error"] * 1e6,
            "hidden_snr": result["snr"],
            "best_period_correction_days": result["dp"],
            "n_replicas_used": result["n_rep"],
            "var_rep": result["var_rep"],
            "windows_dropped": result["dropped"],
            "z_inconsistency": z,
            "train_depth_ppm": train.depth * 1e6,
            "hidden_detrend_window_days": hidden.detrend_window_days,
        }
    )
    if control:
        ctl = measure_windows(
            hidden,
            control,
            eph,
            train.duration,
            cadence,
            plan,
            hidden_sectors,
            grid,
            result["stats"],
            frequencies=freqs,
        )
        window_terms["control"] = dict(ctl.get("terms", {}))
        metrics["control_phase05_snr"] = ctl.get("snr")
        metrics["control_phase05_depth_ppm"] = (
            None if ctl.get("depth") is None else ctl["depth"] * 1e6
        )
    if reason is not None:
        metrics["reason"] = reason
    record["reason"] = reason
    message = {
        "PASS": f"transits found at {result['n_valid']} predicted windows, SNR {result['snr']:.1f}",
        "FAIL": (
            f"no significant signal at {result['n_valid']} predicted windows (SNR "
            f"{result['snr']:.1f} < {params.min_snr}) and the hidden depth is inconsistent "
            f"with the train one (Z = {z:.1f} > 3)"
        ),
    }.get(status, reason or "")
    round_result = RoundResult(
        hidden_year,
        TestStatus(status),
        message,
        metrics=metrics,
        train_ephemeris=eph.to_dict(),
        windows=[
            {"kind": w.kind, "epoch": w.epoch, "t_pred": w.t_pred, "half_width": w.half_width}
            for w in transit
        ],
        access_log=hidden.access_log,
    )
    return round_result, record


def calibration_measurement(
    raw: LightCurveData,
    sectors: Sequence[SectorInfo],
    hidden_year: int,
    plan: TessTestPlan,
    *,
    identity: dict[str, Any],
    twin_model: np.ndarray | None = None,
) -> dict[str, Any]:
    """Map Amendments 9 and 12: for the population harness only, never for ``run_holdout``. The
    round measured despite the two capacity decisions (recorded), with its own ``HiddenYear``;
    a measurement impediment leaves ``s_meas`` absent with its reason. Returns a record marked
    ``calibration_only``; nothing of an official result is touched. From package 25 (Amendment
    25) every return carries the pair ``capacity_b``, ``capacity_s`` used and the configuration
    ``identity`` given by the caller (its ``block_sha256`` must be the plan's resolved block).
    The R_min study (Amendment 26, 4): ``twin_model``, one value per cadence of ``raw`` (the
    evaluator's noiseless model; only the hidden year's values are read), gives ``d_twin``, the
    twin's depth at the ``dP`` chosen, read after the measurement and never in a decision."""
    from refute.core.canonical import canonical_sha256

    c = plan.gauntlet.corrections
    if not c.active:
        raise ValueError("the calibration measurement needs the corrections switch on")
    # the identity is required and complete (the Codex review of the package): the configuration
    # file's repository path, its bytes' SHA-256 and its resolved block's SHA-256
    hexdigits = set("0123456789abcdef")
    if (
        not isinstance(identity, dict)
        or set(identity) != {"path", "sha256", "block_sha256"}
        or not (isinstance(identity["path"], str) and identity["path"])
        or not all(
            isinstance(identity[k], str)
            and len(identity[k]) == 64
            and set(identity[k]) <= hexdigits
            for k in ("sha256", "block_sha256")
        )
    ):
        raise ValueError("the configuration identity must give path, sha256 and block_sha256")
    if identity["block_sha256"] != canonical_sha256(c.model_dump(mode="json")):
        raise ValueError("the configuration identity names another corrections block")
    stamp = {"capacity_b": c.capacity_b, "capacity_s": c.capacity_s, "configuration": identity}
    if twin_model is not None:
        twin_model = np.asarray(twin_model, dtype=float)
        if twin_model.shape != (len(raw),):
            raise ValueError("the twin model must have one value per cadence of the curve")
    spans = [(s.t_start, s.t_end) for s in sectors if s.year == hidden_year]
    prepared = plan_round(raw.select(raw.year != hidden_year), spans, hidden_year, plan)
    if prepared.decided is not None:
        return {
            "calibration_only": True,
            "hidden_year": hidden_year,
            "decision_1": None,
            "decision_2": None,
            "s_pred_1": None,
            "s_pred_2": None,
            "s_meas": None,
            "reason": prepared.decided.metrics.get("reason", prepared.decided.message),
            **_empty_derivation_fields(),
            "stage": "before_capacity",
            "d_twin": None,
            **stamp,
        }
    twin = None if twin_model is None else twin_model[raw.year == hidden_year]
    record = _round_corrected(
        raw, sectors, hidden_year, plan, prepared, enforce=False, twin_model=twin
    )[1]
    return {**record, **stamp}


ELIGIBLE_INCONCLUSIVE = "not_detected_not_inconsistent"


def derive_round(
    record: dict[str, Any], r_min: int, b: float, s: float, min_snr: float
) -> dict[str, Any]:
    """The ``R_min`` study (map Amendments 19 and 26, 3): the round at ``r_min`` and the pair
    ``(b, s)`` derived from a calibration record made at a smaller ``r_min`` (8), in this order:
    the impediments before the capacity rule; the train counts; decision 1; the hidden noise (the
    estimate, then the counts); decision 2; the measurement's impediments; the FAIL rule. A round
    is eligible when both decisions pass and the FAIL rule reads a measurement (PASS, FAIL or
    INCONCLUSIVE ``not_detected_not_inconsistent``). For the population harness only."""

    def out(status, reason, d1=None, d2=None, eligible=False):
        return {
            "status": status,
            "reason": reason,
            "decision_1": d1,
            "decision_2": d2,
            "eligible": eligible,
        }

    if record["stage"] == "before_capacity":
        return out("INCONCLUSIVE", record["reason"], record.get("decision_1"))
    if not replicas_enough(record["train_n_rep"], r_min):
        return out("INCONCLUSIVE", "train_replicas_below_r_min", "train_replicas_below_r_min")
    threshold = capacity_threshold(min_snr, b, s, record["n_years"])
    s1 = record["s_pred_1"]
    if not (s1 is not None and math.isfinite(s1) and s1 >= threshold):
        return out("INCONCLUSIVE", "insufficient_capacity_train", "insufficient_capacity_train")
    counts = record["hidden_n_rep"]
    if (
        record["stage"] == "hidden_noise"
        or record["hidden_noise_undetermined"]
        or not replicas_enough(counts or [], r_min)
    ):
        return out("INCONCLUSIVE", "hidden_noise_undetermined", "pass")
    s2 = record["s_pred_2"]
    if not (s2 is not None and math.isfinite(s2) and s2 >= threshold):
        return out(
            "INCONCLUSIVE",
            "insufficient_capacity_hidden_noise",
            "pass",
            "insufficient_capacity_hidden_noise",
        )
    if record["measurement_status"] != "ok":
        return out("INCONCLUSIVE", record["measurement_status"], "pass", "pass")
    status, reason, _ = fail_rule(
        record["s_meas"],
        min_snr,
        record["d_train"],
        record["e_train"],
        record["d_hidden"],
        record["e_hidden"],
    )
    eligible = status in ("PASS", "FAIL") or reason == ELIGIBLE_INCONCLUSIVE
    return out(status, reason, "pass", "pass", eligible)


def run_holdout(
    raw: LightCurveData, sectors: Sequence[SectorInfo], plan: TessTestPlan
) -> HoldoutOutcome:
    """Blind holdout by year. Receives raw data and metadata only; never a candidate."""
    for argument in (raw, sectors, plan):
        if isinstance(argument, Candidate):
            raise TypeError("run_holdout must not receive the global candidate")
    if not isinstance(raw, LightCurveData):
        raise TypeError("raw must be LightCurveData")
    if not isinstance(plan, TessTestPlan):
        raise TypeError("plan must be TessTestPlan")
    if any(isinstance(s, Candidate) for s in sectors):
        raise TypeError("run_holdout must not receive the global candidate")

    params = plan.gauntlet.holdout_by_year
    thresholds = params.model_dump(mode="json")
    years = raw.years
    if len(years) < 2:
        test = TestResult(
            TEST_NAME,
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            f"data from {len(years)} observing year(s); at least 2 are needed",
            metrics={"years": years},
            thresholds=thresholds,
        )
        return HoldoutOutcome(test, [])

    rounds = [_round(raw, sectors, year, plan) for year in years]
    statuses = [r.status for r in rounds]
    summary = {
        "years": years,
        "rounds": {str(r.hidden_year): r.status.value for r in rounds},
        "n_pass": statuses.count(TestStatus.PASS),
        "n_fail": statuses.count(TestStatus.FAIL),
        "n_inconclusive": statuses.count(TestStatus.INCONCLUSIVE),
    }
    if TestStatus.FAIL in statuses:
        failed = [str(r.hidden_year) for r in rounds if r.status is TestStatus.FAIL]
        status, message = (
            TestStatus.FAIL,
            "prediction failed for hidden year(s) " + ", ".join(failed),
        )
    elif TestStatus.PASS in statuses:
        status = TestStatus.PASS
        message = f"predictions confirmed in {summary['n_pass']} of {len(rounds)} hidden years"
        if summary["n_inconclusive"]:
            message += f" ({summary['n_inconclusive']} inconclusive)"
    else:
        status, message = TestStatus.INCONCLUSIVE, "no hidden year could be tested"
    examined = sum(
        int(r.metrics.get("n_windows_with_data") or 0)
        for r in rounds
        if r.status is not TestStatus.INCONCLUSIVE
    )
    test = TestResult(
        TEST_NAME,
        status,
        Severity.FATAL,
        message,
        metrics=summary,
        thresholds=thresholds,
        coverage=examined,
        coverage_unit="hidden-year windows measured in conclusive rounds",
    )
    return HoldoutOutcome(test, rounds)
