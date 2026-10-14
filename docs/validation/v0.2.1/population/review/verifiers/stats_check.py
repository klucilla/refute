"""Independent check of the one-sided 95% Clopper-Pearson bounds and the exact McNemar
test of the population harness. Written by the Phase G reviewer."""

import ctypes
import importlib.util
import math
import sys
from fractions import Fraction

k32 = ctypes.windll.kernel32
k32.GetCurrentProcess.restype = ctypes.c_void_p
k32.SetProcessAffinityMask(ctypes.c_void_p(k32.GetCurrentProcess()), ctypes.c_size_t(0xFFFFFF00))

spec = importlib.util.spec_from_file_location("population_under_review", sys.argv[1])
pop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pop)
from scipy.stats import binomtest  # noqa: E402


def cdf(k, n, p):
    """P(X <= k), X ~ Binomial(n, p), summed in log space."""
    if p <= 0:
        return 1.0
    if p >= 1:
        return 1.0 if k >= n else 0.0
    lp, lq = math.log(p), math.log1p(-p)
    terms = [math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq for i in range(k + 1)]
    m = max(terms)
    return min(1.0, math.exp(m) * sum(math.exp(t - m) for t in terms))


def bisect(f, lo=0.0, hi=1.0):
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid):
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def upper(k, n):  # P(X <= k; p_u) = 0.05
    return 1.0 if k >= n else bisect(lambda p: cdf(k, n, p) <= 0.05)


def lower(k, n):  # P(X >= k; p_l) = 0.05
    return 0.0 if k <= 0 else bisect(lambda p: 1 - cdf(k - 1, n, p) >= 0.05)


cases = [(0, 1), (1, 1), (0, 10), (10, 10), (0, 250), (250, 250), (16, 250), (17, 250),
         (163, 250), (164, 250), (39, 250), (40, 250), (14, 2200), (15, 2200), (20, 600), (21, 600), (1, 2)]
worst = 0.0
for k, n in cases:
    hu, hl = pop.cp_upper(k, n), pop.cp_lower(k, n)
    mu, ml = upper(k, n), lower(k, n)
    ci = binomtest(k, n).proportion_ci(confidence_level=0.90, method="exact")
    worst = max(worst, abs(hu - mu), abs(hl - ml), abs(hu - ci.high), abs(hl - ci.low))
    print(f"k={k:4d} n={n:5d}  upper harness {hu:.6f} mine {mu:.6f} scipy-ci {ci.high:.6f} | "
          f"lower harness {hl:.6f} mine {ml:.6f} scipy-ci {ci.low:.6f}")
print(f"largest absolute difference: {worst:.2e}")


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(Fraction(math.comb(n, i), 2**n) for i in range(min(b, c) + 1))
    return float(min(Fraction(1), 2 * tail))


for b, c in ((0, 0), (0, 1), (1, 0), (0, 5), (5, 0), (3, 3), (2, 9), (10, 30), (0, 40), (7, 8)):
    n = b + c
    harness = binomtest(b, n, 0.5).pvalue if n else 1.0  # the expression of paired()
    print(f"McNemar became_true={b:2d} became_false={c:2d}: harness {harness:.6g}, exact {mcnemar_exact(b, c):.6g}")
