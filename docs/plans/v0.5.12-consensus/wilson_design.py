"""Design arithmetic for #222's acceptance rule (exploratory, standard library only).

For each n: the largest k with the 95% Wilson upper bound <= 1%, and the binomial probability of
passing when the true rejection rate is p (the nominal 2*(1 - Phi(3)) and alternatives).
"""

import math

Z = 1.959963984540054  # the 0.975 quantile of the standard normal
P0 = math.erfc(3 / math.sqrt(2))  # P(|N(0,1)| > 3)


def wilson_upper(k: int, n: int, z: float = Z) -> float:
    p = k / n
    den = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre + half) / den


def binom_cdf(k: int, n: int, p: float) -> float:
    total, term = 0.0, (1 - p) ** n
    for i in range(k + 1):
        if i > 0:
            term *= (n - i + 1) / i * p / (1 - p)
        total += term
    return total


print(f"P0 = {P0:.10f}")
for n in (1000, 2000, 3000, 4000, 5000):
    kmax = max(k for k in range(n + 1) if wilson_upper(k, n) <= 0.01)
    row = [f"n={n}", f"kmax={kmax}", f"U(kmax)={wilson_upper(kmax, n):.5f}"]
    for p in (P0, 0.005, 0.0075, 0.01, 0.015, 0.02):
        row.append(f"P(pass|p={p:.4f})={binom_cdf(kmax, n, p):.4f}")
    families = 7
    row.append(f"P(all {families} pass|P0)={binom_cdf(kmax, n, P0) ** families:.4f}")
    print("  ".join(row))
