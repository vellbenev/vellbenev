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
    cell, gap, pad = 10, 3, 16
    step = cell + gap
    weeks = cal["weeks"]
    width = pad * 2 + len(weeks) * step - gap
    height = pad * 2 + 7 * step - gap
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="100%" role="img" shape-rendering="crispEdges" '
        f'aria-label="{cal["totalContributions"]} contributions in the last year">',
        f'<rect width="{width}" height="{height}" fill="#101310"/>',
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" fill="none" stroke="#222920" stroke-width="2"/>',
    ]
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            color = LEVELS.get(day["contributionLevel"], LEVELS["NONE"])
            out.append(
                f'<rect x="{pad + wi * step}" y="{pad + di * step}" '
                f'width="{cell}" height="{cell}" fill="{color}"/>'
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
