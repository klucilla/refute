"""Independent check of the expected SNR (population-study.md, section 3) for a few
self-test cases of the manifest. Written by the Phase G reviewer; does not import the
harness. Only numpy and the standard library."""

import ctypes
import json
import math
import sys

import numpy as np

k32 = ctypes.windll.kernel32
k32.GetCurrentProcess.restype = ctypes.c_void_p
k32.SetProcessAffinityMask(ctypes.c_void_p(k32.GetCurrentProcess()), ctypes.c_size_t(0xFFFFFF00))

S = 600e-6
A = 600e-6
TAU = 1.0 / 24.0
STEP = 2.0 / 1440.0
GATE, HID = 7.1, 5.0
YEAR_OF = {1325.0: 2018, 1700.0: 2019, 1690.25: 2019, 2061.0: 2020, 2055.5: 2020, 2420.75: 2021}


def sector(start, first_only=False):
    a = np.arange(start, start + 13.0, STEP)
    if first_only:
        return a
    b = np.arange(start + 14.0, start + 27.0, STEP)
    return np.concatenate([a, b])


def layout(c):
    mech = c["mechanism"]
    if mech in ("three_years", "variability_some_years"):
        return [(1325.0, False), (1700.0, False), (2061.0, False)]
    if mech == "few_train":
        far = {1: 1690.25, 2: 2055.5, 3: 2420.75}[c["extra"]["distance_years"]]
        return [(1325.0, True), (far, False)]
    return [(1325.0, False), (2061.0, False)]


def psf(xy, sigma=0.9, n=11):
    sc = math.sqrt(2.0) * sigma

    def edges(center):
        cdf = [0.5 * (1 + math.erf((b - 0.5 - center) / sc)) for b in range(n + 1)]
        return np.diff(cdf)

    return np.outer(edges(xy[1]), edges(xy[0]))


def blend_dilution(p):
    t = psf((5.0, 5.0))
    ap = t >= 0.02
    d, a = p["neighbor_distance_px"], p["neighbor_angle"]
    nb = psf((5.0 + d * math.cos(a), 5.0 + d * math.sin(a)))
    ft, fn = t[ap].sum(), p["neighbor_ratio"] * nb[ap].sum()
    c = ft / (ft + fn)
    extra = 5e-5 * math.sqrt(ap.sum()) / t[ap].sum()  # pixel noise after normalization and /c
    return (1 - c) / c, c, extra


def snr_unit(t, unit, inside, sel, noise):
    """Closed form: S_t = s^2 m + a^2 (m + 2 sum_{k=1}^{m-1} (m-k) phi^k) per transit."""
    mask = inside & sel
    if not mask.any():
        return 0.0
    idx = np.flatnonzero(mask)
    # split into transits: consecutive in-transit cadences on the regular grid
    breaks = np.flatnonzero(np.diff(t[idx]) > 1.5 * STEP)
    groups = np.split(idx, breaks + 1)
    phi = math.exp(-STEP / TAU)
    total = 0.0
    for g in groups:
        m = g.size
        if np.any(np.abs(np.diff(t[g]) - STEP) > 1e-9):
            raise SystemExit("irregular cadence inside a transit")
        v = S * S * m
        if noise == "correlated":
            k = np.arange(1, m)
            v += A * A * (m + 2.0 * float(np.sum((m - k) * phi**k)))
        total += v
    return float(unit[mask].sum() / math.sqrt(total)), len(groups)


def check(c):
    p = c["parameters"]
    parts = [(sector(s, fo), YEAR_OF[s]) for s, fo in layout(c)]
    t = np.concatenate([x for x, _ in parts])
    yr = np.concatenate([np.full(x.size, y) for x, y in parts])
    P, t0, D, fi = p["period"], p["t0"], p["duration"], p["ingress_fraction"]
    dt = np.mod(t - t0 + 0.5 * P, P) - 0.5 * P
    unit = np.clip((D / 2 - np.abs(dt)) / max(fi * D, 1e-6), 0, 1)
    if c["mechanism"] == "eb_odd_even":
        ep = np.round((t - t0) / P).astype(int)
        unit = np.where(ep % 2 != 0, unit * p["odd_factor"], unit)
    note = ""
    if c["mechanism"] == "blend":
        dil, cr, extra = blend_dilution(p)
        unit = unit * dil
        note = (
            f" dilution={dil:.6f} (harness {p['dilution']:.6f}) crowdsap={cr:.4f}"
            f" pixel-noise term={extra * 1e6:.0f} ppm -> white sigma "
            f"{math.hypot(600, extra * 1e6):.0f} ppm"
        )
    inside = np.abs(dt) <= D / 2
    g, ng = snr_unit(t, unit, inside, np.ones(t.size, bool), c["noise"])
    ratios = [g / GATE]
    out = {"global": (g, c["expected_snr"]["global"])}
    for y in sorted(set(yr.tolist())):
        tr, _ = snr_unit(t, unit, inside, yr != y, c["noise"])
        hi, _ = snr_unit(t, unit, inside, yr == y, c["noise"])
        out[f"train {y}"] = (tr, c["expected_snr"]["train"][str(y)])
        out[f"hidden {y}"] = (hi, c["expected_snr"]["hidden"][str(y)])
        ratios += [tr / GATE, hi / HID]
    rmin = min(ratios)
    worst = max(abs(a / b - 1) for a, b in out.values())
    r = p["depth"] * rmin
    line = (
        f"{c['id']} ({c['mechanism']}, {ng} transits): max rel. diff of unit SNRs "
        f"{worst:.2e}; r from depth = {r:.6f}, r_target = {p['r_target']:.6f}; "
        f"SNR_global = {g * p['depth']:.2f}{note}"
    )
    if c["class"] == "planet":
        k = math.sqrt(p["depth"])
        a_au = (P / 365.25) ** (2 / 3)
        x = (0.00465047 / a_au) * math.sqrt((1 + k) ** 2 - p["impact"] ** 2)
        t14 = min(max(P / math.pi * math.asin(min(1, x)), 1 / 24), 4 / 24)
        fi2 = min(max(k / (1 - p["impact"] ** 2), 0.05), 0.5)
        line += (
            f"; T14 at final depth {t14 * 24:.5f} h vs harness {D * 24:.5f} h;"
            f" ingress {fi2:.5f} vs {fi:.5f}"
        )
    print(line)


def monte_carlo(m, trials, seed):
    """Variance of the in-transit mean of m cadences, white + stationary AR(1)."""
    rng = np.random.default_rng(seed)
    phi = math.exp(-STEP / TAU)
    x = rng.normal(0, A, trials)
    acc = x.copy()
    for _ in range(1, m):
        x = phi * x + A * math.sqrt(1 - phi * phi) * rng.normal(0, 1, trials)
        acc += x
    acc += rng.normal(0, S, (trials, m)).sum(axis=1)
    sim = float(np.var(acc / m))
    k = np.arange(1, m)
    form = (S * S * m + A * A * (m + 2 * float(np.sum((m - k) * phi**k)))) / m**2
    return sim, form


if __name__ == "__main__":
    manifest = json.load(open(sys.argv[1], encoding="utf-8"))
    wanted = sys.argv[2:]
    by_id = {c["id"]: c for c in manifest["cases"]}
    for w in wanted:
        check(by_id[w])
    for m, seed in ((75, 11), (75, 12), (112, 13)):
        sim, form = monte_carlo(m, 400_000, seed)
        print(f"Monte Carlo m={m} seed={seed}: simulated {sim:.5e}, formula {form:.5e}, ratio {sim / form:.4f}")
