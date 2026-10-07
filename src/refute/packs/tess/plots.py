"""Dossier figures (matplotlib object API with the Agg backend, no pyplot state)."""

from __future__ import annotations

from typing import Any

import numpy as np
from matplotlib.figure import Figure

from refute.packs.tess.events import phase_offset_days
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.types import Candidate, LightCurveData, TessData

_DPI = 100


def _binned(x: np.ndarray, y: np.ndarray, width: float) -> tuple[np.ndarray, np.ndarray]:
    if x.size == 0:
        return x, y
    index = np.floor((x - x.min()) / width).astype(int)
    _, inverse, counts = np.unique(index, return_inverse=True, return_counts=True)
    good = counts >= 3
    xb = np.bincount(inverse, weights=x) / counts
    yb = np.bincount(inverse, weights=y) / counts
    return xb[good], yb[good]


def _save(fig: Figure, writer: Any, name: str) -> str:
    path = writer.path(f"plots/{name}")
    fig.savefig(path, dpi=_DPI, metadata={"Software": None})
    return f"plots/{name}"


def plot_full(writer: Any, data: TessData, flat: LightCurveData, cand: Candidate | None) -> str:
    sectors = sorted(data.sectors, key=lambda s: s.t_start)
    fig = Figure(figsize=(12, 4.5))
    axes = fig.subplots(2, 1, sharex=True)
    offset, ticks, labels = 0.0, [], []
    for sector in sectors:
        raw_sel = data.lc.sector == sector.sector
        flat_sel = flat.sector == sector.sector
        x_raw = data.lc.time[raw_sel] - sector.t_start + offset
        x_flat = flat.time[flat_sel] - sector.t_start + offset
        axes[0].plot(x_raw, data.lc.flux[raw_sel], ",", color="0.3")
        axes[1].plot(x_flat, flat.flux[flat_sel], ",", color="0.3")
        if cand is not None:
            t = flat.time[flat_sel]
            if t.size:
                first = np.ceil((t.min() - cand.t0) / cand.period)
                last = np.floor((t.max() - cand.t0) / cand.period)
                for n in np.arange(first, last + 1):
                    axes[1].axvline(
                        cand.t0 + n * cand.period - sector.t_start + offset,
                        color="tab:red",
                        alpha=0.25,
                        lw=0.8,
                    )
        ticks.append(offset + 0.5 * (sector.t_end - sector.t_start))
        labels.append(f"S{sector.sector}\n{sector.year}")
        offset += (sector.t_end - sector.t_start) + 3.0
    axes[0].set_ylabel("normalized flux")
    axes[1].set_ylabel("detrended flux")
    axes[1].set_xticks(ticks, labels, fontsize=7)
    axes[0].set_title(f"{data.target_key}: sectors laid side by side (gaps removed)")
    fig.tight_layout()
    return _save(fig, writer, "full.png")


def _fold_axis(ax: Any, lc: LightCurveData, cand: Candidate, phase: float, title: str) -> None:
    shift = phase * cand.period
    dt = phase_offset_days(lc.time, cand.period, cand.t0 + shift)
    window = 3.0 * cand.duration
    sel = np.abs(dt) <= window
    hours = dt[sel] * 24.0
    ax.plot(hours, lc.flux[sel], ",", color="0.6")
    xb, yb = _binned(hours, lc.flux[sel], max(cand.duration * 24.0 / 12.0, 5.0 / 60.0))
    ax.plot(xb, yb, "o", ms=2.5, color="tab:blue")
    ax.set_title(title, fontsize=9)
    ax.set_xlabel("hours from predicted center")


def plot_phase(writer: Any, flat: LightCurveData, cand: Candidate) -> str:
    fig = Figure(figsize=(7, 4))
    ax = fig.subplots()
    _fold_axis(ax, flat, cand, 0.0, f"P = {cand.period:.6f} d, depth {cand.depth * 1e6:.0f} ppm")
    half = cand.duration * 12.0
    ax.hlines(1.0 - cand.depth, -half, half, color="tab:red", lw=1.5, label="box model")
    ax.set_ylabel("detrended flux")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return _save(fig, writer, "phase.png")


def plot_odd_even(writer: Any, flat: LightCurveData, cand: Candidate) -> str:
    epoch = np.round((flat.time - cand.t0) / cand.period).astype(int)
    fig = Figure(figsize=(10, 4))
    axes = fig.subplots(1, 2, sharey=True)
    for ax, parity, name in ((axes[0], 0, "even"), (axes[1], 1, "odd")):
        _fold_axis(ax, flat.select(epoch % 2 == parity), cand, 0.0, f"{name} transits")
        ax.axhline(1.0 - cand.depth, color="tab:red", lw=0.8)
    axes[0].set_ylabel("detrended flux")
    fig.tight_layout()
    return _save(fig, writer, "odd_even.png")


def plot_secondary(writer: Any, flat: LightCurveData, cand: Candidate) -> str:
    fig = Figure(figsize=(7, 4))
    ax = fig.subplots()
    _fold_axis(ax, flat, cand, 0.5, "phase 0.5 (secondary eclipse search)")
    ax.axhline(1.0, color="tab:red", lw=0.8)
    ax.set_ylabel("detrended flux")
    fig.tight_layout()
    return _save(fig, writer, "secondary.png")


def plot_holdout_round(writer: Any, round_: Any, duration: float) -> str | None:
    if not round_.stacked:
        return None
    dt = np.asarray(round_.stacked["dt"]) * 24.0
    flux = np.asarray(round_.stacked["flux"])
    fig = Figure(figsize=(7, 4))
    ax = fig.subplots()
    ax.plot(dt, flux, ",", color="0.6")
    xb, yb = _binned(dt, flux, max(duration * 24.0 / 12.0, 5.0 / 60.0))
    ax.plot(xb, yb, "o", ms=2.5, color="tab:blue")
    ax.axvspan(-duration * 12.0, duration * 12.0, color="tab:orange", alpha=0.15)
    ax.set_title(
        f"hidden year {round_.hidden_year}: {round_.status.value} "
        f"(SNR {round_.metrics.get('hidden_snr') or float('nan'):.1f})",
        fontsize=9,
    )
    ax.set_xlabel("hours from predicted center (train-only ephemeris)")
    ax.set_ylabel("flux / local baseline")
    fig.tight_layout()
    return _save(fig, writer, f"holdout_{round_.hidden_year}.png")


def write_all(writer: Any, data: TessData, analysis: Any, plan: TessTestPlan) -> list[str]:
    cand = analysis.gauntlet.candidate
    flat = analysis.gauntlet.flattened or analysis.flattened_search
    written = [plot_full(writer, data, flat, cand)]
    if cand is not None:
        written.append(plot_phase(writer, flat, cand))
        written.append(plot_odd_even(writer, flat, cand))
        written.append(plot_secondary(writer, flat, cand))
    for round_ in analysis.holdout.rounds:
        train = round_.metrics.get("train_candidate") or {}
        duration = train.get("duration") or (cand.duration if cand else 0.1)
        path = plot_holdout_round(writer, round_, duration)
        if path:
            written.append(path)
    return written
