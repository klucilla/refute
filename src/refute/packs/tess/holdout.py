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
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.tess.detrend import detrend, robust_sigma
from refute.packs.tess.ephemeris import (
    Ephemeris,
    fit_linear_ephemeris,
    measure_transit_times,
)
from refute.packs.tess.events import per_point_sigma, transit_mask
from refute.packs.tess.params import HoldoutParams, TessTestPlan
from refute.packs.tess.search import search_period
from refute.packs.tess.types import Candidate, LightCurveData, SectorInfo

TEST_NAME = "holdout_by_year"


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
        return {"n_windows_with_data": len(eligible)}

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


def _round(
    raw: LightCurveData,
    sectors: Sequence[SectorInfo],
    hidden_year: int,
    plan: TessTestPlan,
) -> RoundResult:
    params = plan.gauntlet.holdout_by_year
    cadence = plan.data.exptime_seconds / 86400.0
    train_raw = raw.select(raw.year != hidden_year)
    if len(train_raw) == 0:
        return RoundResult(hidden_year, TestStatus.INCONCLUSIVE, "no training data")

    train_flat = detrend(train_raw, plan.detrend)
    search = search_period(train_flat, plan.search)
    train: Candidate | None = search.candidate
    if train is None or not (train.depth > 0):
        return RoundResult(
            hidden_year, TestStatus.INCONCLUSIVE, "the train-only search found no candidate"
        )

    mask_half = plan.detrend.transit_mask_half_width_durations * train.duration
    train_mask = transit_mask(train_raw.time, train.period, train.t0, mask_half)
    train_flat2 = detrend(train_raw, plan.detrend, mask=train_mask)
    sigma = per_point_sigma(
        train_flat2, transit_mask(train_flat2.time, train.period, train.t0, mask_half)
    )
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
    train_info = {
        "train_candidate": train.to_dict(),
        "n_transit_times": len(times),
    }
    if len(times) < params.min_train_transits:
        return RoundResult(
            hidden_year,
            TestStatus.INCONCLUSIVE,
            f"only {len(times)} train transit times (< {params.min_train_transits})",
            metrics=train_info,
        )
    ephemeris = fit_linear_ephemeris(times)

    spans = [(s.t_start, s.t_end) for s in sectors if s.year == hidden_year]
    windows = _predict_windows(ephemeris, train.duration, spans, params)
    transit_windows = [w for w in windows if w.kind == "transit"]
    control_windows = [w for w in windows if w.kind == "control"]

    max_sigma_t = max(
        ((w.half_width - train.duration / 2) / params.timing_sigma for w in transit_windows),
        default=0.0,
    )
    if max_sigma_t > params.max_timing_sigma_durations * train.duration:
        # Issue #2: the train-only ephemeris cannot place the hidden transits to
        # within a transit duration, so a non-detection would not be informative.
        return RoundResult(
            hidden_year,
            TestStatus.INCONCLUSIVE,
            f"train-only timing uncertainty in the hidden year ({max_sigma_t * 24:.2f} h) exceeds "
            f"{params.max_timing_sigma_durations:g} transit duration(s) "
            f"({train.duration * 24:.2f} h)",
            metrics={
                **train_info,
                "max_timing_sigma_days": max_sigma_t,
                "n_predicted_transits": len(transit_windows),
            },
            train_ephemeris=ephemeris.to_dict(),
        )

    hidden = HiddenYear(raw.select(raw.year == hidden_year), windows, plan)
    measured = _measure(hidden, transit_windows, ephemeris, train.duration, cadence, params)
    control = _measure(hidden, control_windows, ephemeris, train.duration, cadence, params)

    metrics: dict[str, Any] = {
        **train_info,
        "n_predicted_transits": len(transit_windows),
        "n_windows_with_data": measured.get("n_windows_with_data", 0),
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
    test = TestResult(
        TEST_NAME, status, Severity.FATAL, message, metrics=summary, thresholds=thresholds
    )
    return HoldoutOutcome(test, rounds)
