"""Check the Wilson numbers quoted by Codex for the v5 specification draft (two-sided 95 %)."""

import math

Z = 1.959963984540054


def wilson(k: int, n: int) -> tuple[float, float]:
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return c - h, c + h


print("5/107 upper", wilson(5, 107)[1])
for n in (60, 100, 150, 200, 250, 300, 400):
    kmax = max((k for k in range(n + 1) if wilson(k, n)[1] <= 0.10), default=None)
    print(f"n={n}: largest k with upper <= 0.10: {kmax}")
print("224/250 lower", wilson(224, 250)[0], "223/250", wilson(223, 250)[0])
print("235/250 lower", wilson(235, 250)[0], "234/250", wilson(234, 250)[0])
print("12/250 point", 12 / 250, "upper", wilson(12, 250)[1], "13/250 point", 13 / 250)
print("0/250 upper", wilson(0, 250)[1])
# the decision-rate guard: E decisions at 600 draws and a 10 % rate
print("600 x 0.10 =", 600 * 0.10)
