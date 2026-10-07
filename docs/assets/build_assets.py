# ruff: noqa: E501  (SVG markup templates are kept on single lines for readability)
"""Generate the README artwork (original SVGs, no third-party images).

Run from the repository root:

    uv run python docs/assets/build_assets.py

Writes, deterministically (fixed random seeds):

- banner-dark.svg, banner-light.svg   README hero banner (1280x400)
- transit-dark.svg, transit-light.svg "The idea in 30 seconds" diagram (800x440)
- social-preview.svg                  GitHub social preview artwork (1280x640)

The social preview PNG is rendered from social-preview.svg with a headless
Chromium browser, for example:

    msedge --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1
        --window-size=1280,640 --screenshot=docs/assets/social-preview.png
        docs/assets/social-preview.svg
"""

from __future__ import annotations

import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONT = "Inter, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', 'Cascadia Mono', Consolas, 'Courier New', monospace"

THEMES = {
    "dark": {
        "bg_top": "#030712",
        "bg_bottom": "#0b1a33",
        "nebula_a": "#7c3aed",
        "nebula_b": "#0ea5e9",
        "nebula_opacity": "0.22",
        "star": "#e2e8f0",
        "star_min": 0.25,
        "star_max": 0.95,
        "title": "#f8fafc",
        "tagline": "#cbd5e1",
        "muted": "#94a3b8",
        "points": "#7dd3fc",
        "points_opacity": "0.75",
        "model": "#fbbf24",
        "host_core": "#fffbeb",
        "host_mid": "#fcd34d",
        "host_edge": "#f59e0b",
        "planet": "#020617",
        "axis": "#475569",
        "accent": "#38bdf8",
    },
    "light": {
        "bg_top": "#f8fafc",
        "bg_bottom": "#e2e8f0",
        "nebula_a": "#a78bfa",
        "nebula_b": "#38bdf8",
        "nebula_opacity": "0.18",
        "star": "#334155",
        "star_min": 0.12,
        "star_max": 0.4,
        "title": "#0f172a",
        "tagline": "#334155",
        "muted": "#475569",
        "points": "#1d4ed8",
        "points_opacity": "0.6",
        "model": "#ea580c",
        "host_core": "#fff7ed",
        "host_mid": "#fdba74",
        "host_edge": "#f97316",
        "planet": "#0f172a",
        "axis": "#94a3b8",
        "accent": "#0369a1",
    },
}


def transit_profile(x: float, center: float, half: float, ingress: float, depth: float) -> float:
    """Transit dip in pixels (downward): linear ingress/egress and a rounded bottom."""
    distance = abs(x - center)
    if distance >= half:
        return 0.0
    flat = half - ingress
    edge_depth = 0.86 * depth  # limb darkening: the bottom is rounded, deepest at mid-transit
    if distance <= flat:
        u = distance / flat if flat > 0 else 0.0
        return edge_depth + (depth - edge_depth) * (1.0 - u * u)
    return edge_depth * (half - distance) / ingress


def starfield(width: int, height: int, count: int, theme: dict, seed: int) -> str:
    rng = random.Random(seed)
    stars = []
    for _ in range(count):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        r = rng.choice([0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.5])
        opacity = rng.uniform(theme["star_min"], theme["star_max"])
        stars.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{theme["star"]}" '
            f'opacity="{opacity:.2f}"/>'
        )
    for _ in range(max(3, count // 40)):
        x, y = rng.uniform(0, width), rng.uniform(0, height)
        stars.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="url(#glow)" opacity="0.9"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.6" fill="{theme["star"]}"/>'
        )
    return "\n    ".join(stars)


def light_curve(
    x0: float,
    x1: float,
    baseline: float,
    center: float,
    half: float,
    depth: float,
    theme: dict,
    seed: int,
    n_points: int = 150,
    noise: float = 3.2,
) -> str:
    rng = random.Random(seed)
    ingress = half * 0.28
    step = (x1 - x0) / (n_points - 1)
    dots = []
    for i in range(n_points):
        x = x0 + i * step
        y = baseline + transit_profile(x, center, half, ingress, depth) + rng.gauss(0, noise)
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.1"/>')
    model = []
    for i in range(400):
        x = x0 + i * (x1 - x0) / 399
        model.append(f"{x:.1f},{baseline + transit_profile(x, center, half, ingress, depth):.1f}")
    return (
        f'<g fill="{theme["points"]}" opacity="{theme["points_opacity"]}">\n      '
        + "\n      ".join(dots)
        + "\n    </g>\n    "
        + f'<polyline points="{" ".join(model)}" fill="none" stroke="{theme["model"]}" '
        f'stroke-width="2.6" stroke-linejoin="round"/>'
    )


def defs(theme: dict, height: int) -> str:
    return f"""<defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{theme["bg_top"]}"/>
      <stop offset="1" stop-color="{theme["bg_bottom"]}"/>
    </linearGradient>
    <radialGradient id="nebulaA" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{theme["nebula_a"]}" stop-opacity="{theme["nebula_opacity"]}"/>
      <stop offset="1" stop-color="{theme["nebula_a"]}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="nebulaB" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{theme["nebula_b"]}" stop-opacity="{theme["nebula_opacity"]}"/>
      <stop offset="1" stop-color="{theme["nebula_b"]}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{theme["star"]}" stop-opacity="0.55"/>
      <stop offset="1" stop-color="{theme["star"]}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="host" cx="0.45" cy="0.42" r="0.6">
      <stop offset="0" stop-color="{theme["host_core"]}"/>
      <stop offset="0.55" stop-color="{theme["host_mid"]}"/>
      <stop offset="1" stop-color="{theme["host_edge"]}"/>
    </radialGradient>
    <radialGradient id="hostGlow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{theme["host_mid"]}" stop-opacity="0.45"/>
      <stop offset="1" stop-color="{theme["host_mid"]}" stop-opacity="0"/>
    </radialGradient>
  </defs>"""


def host_star(
    cx: float, cy: float, r: float, planet_dx: float, planet_r: float, theme: dict
) -> str:
    return f"""<circle cx="{cx}" cy="{cy}" r="{r * 2.1:.1f}" fill="url(#hostGlow)"/>
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#host)"/>
    <circle cx="{cx + planet_dx}" cy="{cy + r * 0.18:.1f}" r="{planet_r}" fill="{theme["planet"]}"/>"""


def banner(theme_name: str) -> str:
    t = THEMES[theme_name]
    width, height = 1280, 400
    star_x = 1040
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Refute: Find signals. Try to kill them. Keep what survives.</title>
  <desc id="desc">A star field with a bright star crossed by a small dark planet. Below it, a light curve of measured brightness shows the dip of a planetary transit.</desc>
  {defs(t, height)}
  <rect width="{width}" height="{height}" fill="url(#bg)"/>
  <ellipse cx="300" cy="90" rx="420" ry="190" fill="url(#nebulaA)"/>
  <ellipse cx="1000" cy="300" rx="420" ry="200" fill="url(#nebulaB)"/>
  <g>
    {starfield(width, height, 240, t, seed=20261007)}
  </g>
  <g>
    {host_star(star_x, 150, 66, -8, 13, t)}
  </g>
  <g>
    {light_curve(80, 1200, 322, star_x - 8, 62, 38, t, seed=11)}
  </g>
  <text x="80" y="178" font-family="{FONT}" font-size="112" font-weight="800" letter-spacing="-2" fill="{t["title"]}">Refute</text>
  <text x="84" y="236" font-family="{FONT}" font-size="30" font-weight="500" fill="{t["tagline"]}">Find signals. Try to kill them. Keep what survives.</text>
  <text x="84" y="276" font-family="{MONO}" font-size="16" fill="{t["muted"]}">claim → lock → gauntlet → blind holdout → dossier → verdict</text>
</svg>
"""


def social_preview() -> str:
    t = THEMES["dark"]
    width, height = 1280, 640
    star_x = 1010
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">Refute: Find signals. Try to kill them. Keep what survives.</title>
  <desc id="desc">Social preview: star field, a bright star crossed by a planet and a light curve showing a transit dip, with the Refute name and tagline.</desc>
  {defs(t, height)}
  <rect width="{width}" height="{height}" fill="url(#bg)"/>
  <ellipse cx="320" cy="160" rx="520" ry="300" fill="url(#nebulaA)"/>
  <ellipse cx="1000" cy="470" rx="520" ry="300" fill="url(#nebulaB)"/>
  <g>
    {starfield(width, height, 380, t, seed=7)}
  </g>
  <g>
    {host_star(star_x, 230, 104, -12, 20, t)}
  </g>
  <g>
    {light_curve(90, 1190, 512, star_x - 12, 92, 56, t, seed=13, n_points=170, noise=4.0)}
  </g>
  <text x="90" y="250" font-family="{FONT}" font-size="150" font-weight="800" letter-spacing="-3" fill="{t["title"]}">Refute</text>
  <text x="96" y="322" font-family="{FONT}" font-size="38" font-weight="500" fill="{t["tagline"]}">Find signals. Try to kill them.</text>
  <text x="96" y="370" font-family="{FONT}" font-size="38" font-weight="500" fill="{t["tagline"]}">Keep what survives.</text>
  <text x="96" y="420" font-family="{MONO}" font-size="20" fill="{t["muted"]}">open-source falsification framework · github.com/klucilla/refute</text>
</svg>
"""


def transit_diagram(theme_name: str) -> str:
    t = THEMES[theme_name]
    width, height = 800, 440
    star_cx, star_cy, star_r = 330, 118, 78
    planet_y = star_cy + 22
    positions = [(180, "1"), (star_cx, "2"), (480, "3")]
    baseline, depth = 292, 52
    center1, center2, half, ingress = star_cx, 650, 46, 13
    curve = []
    for i in range(600):
        x = 70 + i * (740 - 70) / 599
        dip = transit_profile(x, center1, half, ingress, depth) + transit_profile(
            x, center2, half, ingress, depth
        )
        curve.append(f"{x:.1f},{baseline + dip:.1f}")
    planets = []
    for x, label in positions:
        planets.append(
            f'<circle cx="{x}" cy="{planet_y}" r="13" fill="{t["planet"]}" '
            f'stroke="{t["accent"]}" stroke-width="1.5"/>'
            f'<text x="{x}" y="{planet_y - 24}" text-anchor="middle" font-family="{FONT}" '
            f'font-size="15" font-weight="700" fill="{t["accent"]}">{label}</text>'
            f'<line x1="{x}" y1="{planet_y + 16}" x2="{x}" y2="{baseline - 8}" '
            f'stroke="{t["axis"]}" stroke-width="1" stroke-dasharray="3 4"/>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">How a transit shows up in a light curve</title>
  <desc id="desc">Top: a planet passes in front of its star at positions 1, 2 and 3. Bottom: the star's measured brightness over time is flat at 1 and 3 and dips at 2, while the planet blocks part of the star. The dip repeats one orbital period later. The depth is about the square of the planet-to-star radius ratio.</desc>
  {defs(t, height)}
  <rect width="{width}" height="{height}" rx="18" fill="url(#bg)"/>
  <circle cx="{star_cx}" cy="{star_cy}" r="{star_r * 1.9:.0f}" fill="url(#hostGlow)"/>
  <circle cx="{star_cx}" cy="{star_cy}" r="{star_r}" fill="url(#host)"/>
  <line x1="110" y1="{planet_y}" x2="560" y2="{planet_y}" stroke="{t["muted"]}" stroke-width="1.2" stroke-dasharray="6 6"/>
  {"".join(planets)}
  <text x="600" y="{planet_y + 5}" font-family="{FONT}" font-size="15" fill="{t["muted"]}">planet's path</text>
  <line x1="70" y1="{baseline + depth + 40}" x2="745" y2="{baseline + depth + 40}" stroke="{t["axis"]}" stroke-width="1.2"/>
  <line x1="70" y1="{baseline - 40}" x2="70" y2="{baseline + depth + 40}" stroke="{t["axis"]}" stroke-width="1.2"/>
  <text x="745" y="{baseline + depth + 62}" text-anchor="end" font-family="{FONT}" font-size="15" fill="{t["muted"]}">time →</text>
  <text x="58" y="{baseline - 16}" text-anchor="end" font-family="{FONT}" font-size="15" fill="{t["muted"]}" transform="rotate(-90 58 {baseline - 16})">brightness</text>
  <polyline points="{" ".join(curve)}" fill="none" stroke="{t["model"]}" stroke-width="3" stroke-linejoin="round"/>
  <line x1="{center1}" y1="{baseline + depth}" x2="{center1 + half + 14}" y2="{baseline + depth}" stroke="{t["accent"]}" stroke-width="1.2" stroke-dasharray="4 4"/>
  <line x1="{center1 + half + 14}" y1="{baseline}" x2="{center1 + half + 14}" y2="{baseline + depth}" stroke="{t["accent"]}" stroke-width="1.5"/>
  <line x1="{center1 + half + 9}" y1="{baseline}" x2="{center1 + half + 19}" y2="{baseline}" stroke="{t["accent"]}" stroke-width="1.5"/>
  <line x1="{center1 + half + 9}" y1="{baseline + depth}" x2="{center1 + half + 19}" y2="{baseline + depth}" stroke="{t["accent"]}" stroke-width="1.5"/>
  <text x="{center1 + half + 22}" y="{baseline + depth / 2 + 5:.0f}" font-family="{FONT}" font-size="14" fill="{t["tagline"]}">depth ≈ (R_planet / R_star)²</text>
  <line x1="{center1}" y1="{baseline + depth + 22}" x2="{center2}" y2="{baseline + depth + 22}" stroke="{t["accent"]}" stroke-width="1.5"/>
  <line x1="{center1}" y1="{baseline + depth + 16}" x2="{center1}" y2="{baseline + depth + 28}" stroke="{t["accent"]}" stroke-width="1.5"/>
  <line x1="{center2}" y1="{baseline + depth + 16}" x2="{center2}" y2="{baseline + depth + 28}" stroke="{t["accent"]}" stroke-width="1.5"/>
  <text x="{(center1 + center2) / 2:.0f}" y="{baseline + depth + 16}" text-anchor="middle" font-family="{FONT}" font-size="14" fill="{t["tagline"]}">one orbital period</text>
  <text x="{center2}" y="{baseline - 14}" text-anchor="middle" font-family="{FONT}" font-size="14" fill="{t["muted"]}">it repeats</text>
</svg>
"""


def main() -> None:
    outputs = {
        "banner-dark.svg": banner("dark"),
        "banner-light.svg": banner("light"),
        "transit-dark.svg": transit_diagram("dark"),
        "transit-light.svg": transit_diagram("light"),
        "social-preview.svg": social_preview(),
    }
    for name, svg in outputs.items():
        (HERE / name).write_bytes(svg.encode("utf-8"))
        print(f"wrote docs/assets/{name}")


if __name__ == "__main__":
    main()
