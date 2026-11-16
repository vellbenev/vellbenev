#!/usr/bin/env python3
"""Render the contribution calendar as a pixel-art SVG (assets/journey/journey.svg).

Usage: GH_TOKEN=... python3 scripts/generate_journey.py [login]
Stdlib only, so the GitHub Action needs no install step.
"""
import json
import os
import sys
import urllib.request

LOGIN = sys.argv[1] if len(sys.argv) > 1 else "vellbenev"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "journey", "journey.svg")

# Void -> Rune -> Relic Gold, from the profile palette.
LEVELS = {
    "NONE": "#1a211a",
    "FIRST_QUARTILE": "#2f3d2a",
    "SECOND_QUARTILE": "#526B46",
    "THIRD_QUARTILE": "#A4B77B",
    "FOURTH_QUARTILE": "#C6A66B",
}

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionLevel date } }
      }
    }
  }
}
"""


def fetch(token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "journey-generator"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def render(cal):
    # Same 640-wide stone plate as the other assets, so they share one pixel scale.
    from build_assets import REDUCED, W, frame

    cell, gap = 9, 2
    step = cell + gap
    weeks = cal["weeks"]
    grid_w = len(weeks) * step - gap
    pad_x, pad_y = (W - grid_w) // 2, 22
    height = pad_y * 2 + 7 * step - gap
    # A band of lantern light sweeps across the map; the brightest days pulse.
    # Frame 0 (and any renderer that freezes animation) shows the full grid.
    style = (
        ".sweep{animation:sweep 7s ease-in-out 1s infinite;transform:translateX(-40px)}"
        f"@keyframes sweep{{0%{{transform:translateX(-40px)}}45%,100%{{transform:translateX({W}px)}}}}"
        ".hot{animation:hot 3.2s ease-in-out infinite}"
        "@keyframes hot{0%,100%{opacity:1}50%{opacity:.65}}" + REDUCED
    )
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" '
        f'width="100%" role="img" shape-rendering="crispEdges" '
        f'aria-label="{cal["totalContributions"]} contributions in the last year">',
        f"<style>{style}</style>",
        frame(W, height),
    ]
    for wi, week in enumerate(weeks):
        out.append("<g>")
        for di, day in enumerate(week["contributionDays"]):
            level = day["contributionLevel"]
            color = LEVELS.get(level, LEVELS["NONE"])
            hot = ' class="hot"' if level == "FOURTH_QUARTILE" else ""
            out.append(
                f'<rect{hot} x="{pad_x + wi * step}" y="{pad_y + di * step}" '
                f'width="{cell}" height="{cell}" fill="{color}"/>'
            )
        out.append("</g>")
    out.append(
        f'<rect class="sweep" x="0" y="{pad_y - 4}" width="28" height="{7 * step + 6}" '
        f'fill="#E6CF94" opacity=".09"/>'
    )
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Set GH_TOKEN or GITHUB_TOKEN")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write(render(fetch(token)))
    print("wrote", os.path.normpath(OUT))
