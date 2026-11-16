#!/usr/bin/env python3
"""Build the animated SVG assets for the profile README.

Run from anywhere: python3 scripts/build_assets.py
Sources (edit these, then rebuild):
  assets/banner/dungeon-header.png   background art, embedded in header.svg
  assets/character/explorer.png      character art, embedded in hero.svg
  assets/icons/*.svg                 16x16 icons, inlined into section headings
Text is drawn with the 5x7 pixel font below, so no font files are needed.

Every animation sits on top of a finished still frame: with
prefers-reduced-motion (or a renderer without CSS animation) the
assets still look complete.
"""
import base64
import os
import re

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
A = os.path.join(ROOT, "assets")

# Palette
VOID = "#0c0d0b"   # matches the flat background baked into the art
DUNGEON = "#222920"
MOSS = "#526B46"
RUNE = "#A4B77B"
GOLD = "#C6A66B"
GOLD_HI = "#E6CF94"
GOLD_LO = "#8C7240"
PARCH = "#D9D3BF"

W = 640  # shared viewBox width: everything shown at width=100% gets the same pixel scale

REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"

# ---------------------------------------------------------------- pixel font
FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    " ": ["....."] * 7,
    ".": ["....."] * 6 + ["..#.."],
    ",": ["....."] * 5 + ["..#..", ".#..."],
    ":": [".....", "..#..", ".....", ".....", ".....", "..#..", "....."],
    "·": [".....", ".....", ".....", "..#..", ".....", ".....", "....."],
    "-": [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
    "~": [".....", ".....", ".#...", "#.#.#", "...#.", ".....", "....."],
    "/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
}
ADV = 6  # monospace advance in font units (5 px glyph + 1 px gap)


def text_width(s, scale):
    return (len(s) * ADV - 1) * scale


def text_rects(s, x, y, scale):
    """Pixel text as merged horizontal runs: one <rect> per run, not per pixel."""
    out = []
    for i, ch in enumerate(s.upper()):
        rows = FONT[ch]
        gx = x + i * ADV * scale
        for r, row in enumerate(rows):
            c = 0
            while c < 5:
                if row[c] == "#":
                    start = c
                    while c < 5 and row[c] == "#":
                        c += 1
                    out.append(
                        f'<rect x="{gx + start * scale}" y="{y + r * scale}" '
                        f'width="{(c - start) * scale}" height="{scale}"/>'
                    )
                else:
                    c += 1
    return "".join(out)


# ---------------------------------------------------------------- helpers
def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def icon_rects(name):
    with open(os.path.join(A, "icons", f"{name}.svg")) as f:
        return "".join(re.findall(r"<rect [^>]*/>", f.read()))


def svg(w, h, body, style="", label=""):
    aria = f'role="img" aria-label="{label}"' if label else 'aria-hidden="true"'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" '
        f'{aria} shape-rendering="crispEdges">'
        f"<style>{style}{REDUCED}</style>{body}</svg>\n"
    )


def frame(w, h):
    """Dark stone plate with a 2px border and gold pixel corners."""
    c = [f'<rect width="{w}" height="{h}" fill="{VOID}"/>',
         f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" fill="none" stroke="{DUNGEON}" stroke-width="2"/>']
    for cx, cy, sx, sy in ((4, 4, 1, 1), (w - 4, 4, -1, 1), (4, h - 4, 1, -1), (w - 4, h - 4, -1, -1)):
        x0 = cx if sx > 0 else cx - 8
        y0 = cy if sy > 0 else cy - 2
        c.append(f'<rect x="{x0}" y="{y0}" width="8" height="2" fill="{GOLD_LO}"/>')
        x1 = cx if sx > 0 else cx - 2
        y1 = cy if sy > 0 else cy - 8
        c.append(f'<rect x="{x1}" y="{y1}" width="2" height="8" fill="{GOLD_LO}"/>')
    return "".join(c)


def gem(cx, cy, cls="gem"):
    """A small rune gem: dark socket, gold diamond, bright core."""
    return (
        f'<g class="{cls}"><rect x="{cx - 5}" y="{cy - 5}" width="10" height="10" fill="{DUNGEON}"/>'
        f'<rect x="{cx - 3}" y="{cy - 3}" width="6" height="6" fill="{GOLD}"/>'
        f'<rect x="{cx - 1}" y="{cy - 1}" width="2" height="2" fill="{GOLD_HI}"/></g>'
    )


def gold_gradient(gid):
    """Hard-banded vertical gradient: reads as pixel shading, not a smooth blur."""
    return (
        f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{GOLD_HI}"/><stop offset=".3" stop-color="{GOLD_HI}"/>'
        f'<stop offset=".3" stop-color="{GOLD}"/><stop offset=".72" stop-color="{GOLD}"/>'
        f'<stop offset=".72" stop-color="{GOLD_LO}"/><stop offset="1" stop-color="{GOLD_LO}"/>'
        f"</linearGradient>"
    )


# ---------------------------------------------------------------- 1. header
def build_header():
    w, h = 1400, 467
    # Light sources measured from the art (brightest connected regions).
    lights = [
        (276, 174, 46, 3.1, 0.0),   # hanging lantern
        (629, 293, 52, 2.7, 0.6),   # desk lantern
        (248, 289, 30, 1.9, 0.3),   # candles, left table
        (552, 285, 34, 4.2, 1.1),   # open book
        (955, 328, 30, 2.3, 0.9),   # candles, centre
        (1245, 326, 28, 2.0, 0.2),  # candle by the map
        (1283, 322, 20, 1.6, 1.4),
    ]
    glows = "".join(
        f'<circle class="fl" cx="{x}" cy="{y}" r="{r}" fill="url(#glow)" '
        f'style="animation-duration:{d}s;animation-delay:-{dl}s"/>'
        for x, y, r, d, dl in lights
    )
    # Dust motes drifting up through the lamplight.
    motes = []
    seeds = [(180, 380, 9, 0), (300, 320, 11, 2), (420, 400, 10, 5), (560, 360, 12, 1),
             (700, 410, 9, 6), (760, 300, 13, 3), (880, 380, 10, 7), (1010, 340, 11, 4),
             (1120, 400, 12, 8), (1200, 300, 9, 2), (1330, 380, 10, 5), (640, 250, 14, 9),
             (230, 230, 12, 6), (980, 230, 13, 1)]
    for i, (x, y, d, dl) in enumerate(seeds):
        size = 3 if i % 3 == 0 else 2
        color = GOLD_HI if i % 2 else RUNE
        motes.append(
            f'<rect class="mote" x="{x}" y="{y}" width="{size}" height="{size}" fill="{color}" '
            f'style="animation-duration:{d}s;animation-delay:-{dl}s"/>'
        )
    # Falling light streaks on the waterfall at the right edge.
    falls = "".join(
        f'<rect class="fall" x="{x}" y="96" width="2" height="18" fill="{RUNE}" '
        f'style="animation-duration:{d}s;animation-delay:-{dl}s"/>'
        for x, d, dl in ((1312, 1.6, 0), (1319, 2.1, 0.7), (1326, 1.8, 1.2), (1316, 2.4, 1.6), (1330, 1.5, 0.4))
    )
    style = (
        ".fl{animation:flick 3s ease-in-out infinite;transform-box:fill-box;transform-origin:center}"
        "@keyframes flick{0%,100%{opacity:.55;transform:scale(1)}18%{opacity:.85}"
        "33%{opacity:.6;transform:scale(1.06)}52%{opacity:.95}70%{opacity:.5;transform:scale(.97)}86%{opacity:.8}}"
        ".mote{opacity:0;animation:rise 10s linear infinite}"
        "@keyframes rise{0%{opacity:0;transform:translate(0,0)}15%{opacity:.75}"
        "50%{transform:translate(8px,-60px)}85%{opacity:.5}100%{opacity:0;transform:translate(-4px,-120px)}}"
        ".fall{opacity:0;animation:fall 2s linear infinite}"
        "@keyframes fall{0%{opacity:0;transform:translateY(0)}20%{opacity:.6}100%{opacity:0;transform:translateY(130px)}}"
    )
    body = (
        f'<defs><radialGradient id="glow"><stop offset="0" stop-color="{GOLD_HI}" stop-opacity=".55"/>'
        f'<stop offset=".45" stop-color="{GOLD}" stop-opacity=".18"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/>'
        f'</radialGradient><linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset=".78" stop-color="{VOID}" stop-opacity="0"/><stop offset="1" stop-color="{VOID}"/></linearGradient></defs>'
        f'<image href="data:image/png;base64,{b64(os.path.join(A, "banner", "dungeon-header.png"))}" '
        f'width="{w}" height="{h}" style="image-rendering:pixelated"/>'
        f"{glows}{falls}{''.join(motes)}"
        f'<rect width="{w}" height="{h}" fill="url(#fade)"/>'
    )
    return svg(w, h, body, style)


# ---------------------------------------------------------------- 2. hero
def build_hero():
    h = 320
    # Character: 420x592 source drawn at 206x290; lantern centre at (344,345) in source.
    cw, ch_ = 206, 290
    k = cw / 420
    cx0, cy0 = 22, 15
    lx, ly = cx0 + 344 * k, cy0 + 345 * k

    col = 240
    wm = "VELLBENEV"
    sub = "BUILDER · THINKER · EXPLORER"
    l1, l2 = "I BUILD THINGS", "I WISH EXISTED."
    now = "NOW · UNCHAIN FOUNDATION"

    y_wm, y_sub, y_rule = 40, 108, 136
    y_l1, y_l2, y_now = 158, 198, 266
    s_l = 4
    t1 = 0.11 * len(l1)  # seconds to type each line
    t2 = 0.11 * len(l2)
    gap = 0.5

    def typer(line, y, n, dur, delay, cls, last):
        lw = text_width(line, s_l)
        end = lw + 6
        cursor = f'<rect x="-2" y="{y}" width="{s_l * 4}" height="{s_l * 7}" fill="{GOLD}" class="{"blink" if last else ""}"/>'
        cover = f'<rect x="{s_l * 4}" y="{y - 2}" width="{lw + 40}" height="{s_l * 7 + 4}" fill="{VOID}"/>'
        anim = f"type{cls} {dur}s steps({n}) {delay}s both"
        if not last:
            anim += f",gone .01s {delay + dur + 0.15}s both"
        else:
            anim += f",blink 1.1s step-end {delay + dur}s infinite"
        # Still frame (no animation): cover parked past the line end; only the last cursor shows.
        rest = f"transform:translateX({end}px)" + ("" if last else ";opacity:0")
        # Clip to the line's own box so the parked cover never paints over the frame.
        clip = (f'<clipPath id="c{cls}"><rect x="-4" y="{y - 2}" width="{end + s_l * 4 + 4}" '
                f'height="{s_l * 7 + 4}"/></clipPath>')
        return (
            f'{clip}<g transform="translate({col},0)" clip-path="url(#c{cls})">'
            f'<g style="{rest};animation:{anim}">{cursor}{cover}</g></g>',
            f"@keyframes type{cls}{{from{{transform:translateX(0)}}to{{transform:translateX({end}px)}}}}",
        )

    g1, k1 = typer(l1, y_l1, len(l1), t1, 0.6, "a", False)
    g2, k2 = typer(l2, y_l2, len(l2), t2, 0.6 + t1 + gap, "b", True)

    wm_w = text_width(wm, 7)
    style = (
        ".ember{opacity:0;animation:ember 3.2s ease-out infinite}"
        "@keyframes ember{0%{opacity:0;transform:translate(0,0)}12%{opacity:1}100%{opacity:0;transform:translate(var(--dx),-46px)}}"
        ".halo{animation:halo 2.6s ease-in-out infinite;transform-box:fill-box;transform-origin:center}"
        "@keyframes halo{0%,100%{opacity:.7;transform:scale(1)}40%{opacity:1;transform:scale(1.08)}65%{opacity:.6;transform:scale(.96)}}"
        ".sheen{animation:sheen 7s ease-in-out 1s infinite;transform:translateX(-120px)}"
        "@keyframes sheen{0%{transform:translateX(-120px)}35%,100%{transform:translateX(" + str(wm_w + 60) + "px)}}"
        ".gem{animation:pulse 3s ease-in-out infinite}"
        "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.55}}"
        "@keyframes gone{to{opacity:0}}"
        "@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}"
        + k1 + k2
    )
    embers = "".join(
        f'<rect class="ember" x="{lx + ox:.0f}" y="{ly - 8:.0f}" width="2" height="2" fill="{GOLD_HI}" '
        f'style="--dx:{dx}px;animation-delay:{dl}s;animation-duration:{d}s"/>'
        for ox, dx, dl, d in ((-3, -6, 0, 3.2), (2, 5, 1.1, 2.8), (0, -2, 2.0, 3.6), (4, 8, 2.7, 3.0))
    )
    body = (
        f'<defs>{gold_gradient("g")}<radialGradient id="lg"><stop offset="0" stop-color="{GOLD_HI}" stop-opacity=".45"/>'
        f'<stop offset=".5" stop-color="{GOLD}" stop-opacity=".12"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>'
        f'<clipPath id="wm">{text_rects(wm, col, y_wm, 7)}</clipPath></defs>'
        + frame(W, h)
        + f'<circle class="halo" cx="{lx:.0f}" cy="{ly:.0f}" r="44" fill="url(#lg)"/>'
        f'<image href="data:image/png;base64,{b64(os.path.join(A, "character", "explorer.png"))}" '
        f'x="{cx0}" y="{cy0}" width="{cw}" height="{ch_}" style="image-rendering:pixelated"/>'
        f'<circle class="halo" cx="{lx:.0f}" cy="{ly:.0f}" r="16" fill="url(#lg)" style="animation-delay:-1.3s"/>'
        + embers
        # wordmark: drop shadow, banded gold, moving sheen clipped to the letters
        + f'<g fill="#2a2418" transform="translate(4,4)">{text_rects(wm, col, y_wm, 7)}</g>'
        f'<g clip-path="url(#wm)"><rect x="{col}" y="{y_wm}" width="{wm_w}" height="49" fill="url(#g)"/>'
        f'<rect class="sheen" x="{col}" y="{y_wm - 4}" width="28" height="60" fill="#fff4d6" opacity=".55" transform="skewX(-20)"/></g>'
        f'<g fill="{RUNE}">{text_rects(sub, col, y_sub, 2)}</g>'
        f'<rect x="{col}" y="{y_rule}" width="{wm_w}" height="2" fill="{DUNGEON}"/>'
        f'<rect x="{col}" y="{y_rule}" width="60" height="2" fill="{MOSS}"/>'
        + gem(col + wm_w - 6, y_rule + 1)
        + f'<g fill="{PARCH}">{text_rects(l1, col, y_l1, s_l)}{text_rects(l2, col, y_l2, s_l)}</g>'
        + g1 + g2
        + gem(col + 5, y_now + 7)
        + f'<g fill="{GOLD}">{text_rects(now, col + 18, y_now, 2)}</g>'
    )
    label = "VELLBENEV. Builder, thinker, explorer. I build things I wish existed. Now: Unchain Foundation."
    return svg(W, h, body, style, label)


# ---------------------------------------------------------------- 3. headings
def build_heading(num, title, icon):
    h = 60
    s = 3
    y = (h - 7 * s) // 2
    x_icon, x_num = 18, 62
    x_title = x_num + text_width(num, s) + 18
    tw = text_width(title, s)
    line_x = x_title + tw + 20
    style = (
        ".gem{animation:pulse 3.4s ease-in-out infinite}"
        "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}"
        ".spark{animation:spark 5s ease-in-out infinite;opacity:0}"
        f"@keyframes spark{{0%{{opacity:0;transform:translateX(0)}}10%{{opacity:1}}60%{{opacity:1}}"
        f"75%,100%{{opacity:0;transform:translateX({W - 46 - line_x}px)}}}}"
    )
    body = (
        frame(W, h)
        + f'<g transform="translate({x_icon},{(h - 32) // 2}) scale(2)">{icon_rects(icon)}</g>'
        + f'<g fill="{GOLD}">{text_rects(num, x_num, y, s)}</g>'
        + f'<rect x="{x_num + text_width(num, s) + 7}" y="{y + 9}" width="3" height="3" fill="{MOSS}"/>'
        + f'<g fill="{PARCH}">{text_rects(title, x_title, y, s)}</g>'
        + f'<rect x="{line_x}" y="{h // 2 - 1}" width="{W - 34 - line_x}" height="2" fill="{DUNGEON}"/>'
        + f'<rect class="spark" x="{line_x}" y="{h // 2 - 1}" width="14" height="2" fill="{RUNE}"/>'
        + gem(W - 26, h // 2)
    )
    return svg(W, h, body, style, f"{num} · {title.title()}")


# ---------------------------------------------------------------- 4. divider
def build_divider():
    h = 24
    mid = W // 2
    style = (
        ".gem{animation:pulse 3s ease-in-out infinite}@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}"
        ".l{animation:runL 6s ease-in-out infinite;opacity:0}.r{animation:runR 6s ease-in-out infinite;opacity:0}"
        f"@keyframes runL{{0%{{opacity:0;transform:translateX(0)}}15%{{opacity:1}}55%,100%{{opacity:0;transform:translateX(-{mid - 40}px)}}}}"
        f"@keyframes runR{{0%{{opacity:0;transform:translateX(0)}}15%{{opacity:1}}55%,100%{{opacity:0;transform:translateX({mid - 40}px)}}}}"
    )
    body = (
        f'<rect x="8" y="11" width="{W - 16}" height="2" fill="{DUNGEON}"/>'
        f'<rect x="{mid - 70}" y="11" width="140" height="2" fill="{MOSS}"/>'
        f'<rect x="{mid - 24}" y="11" width="10" height="2" fill="{RUNE}"/><rect x="{mid + 14}" y="11" width="10" height="2" fill="{RUNE}"/>'
        f'<rect class="l" x="{mid - 20}" y="11" width="10" height="2" fill="{GOLD_HI}"/>'
        f'<rect class="r" x="{mid + 10}" y="11" width="10" height="2" fill="{GOLD_HI}"/>'
        + gem(mid, 12)
    )
    return svg(W, h, body, style)


# ---------------------------------------------------------------- 5. footer
def build_footer():
    h = 92
    l1, l2 = "BUILD WHAT SHOULD EXIST.", "SHARE WHAT OTHERS CAN USE."
    s = 3
    style = (
        ".fl{animation:flick 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center bottom}"
        "@keyframes flick{0%,100%{transform:scaleY(1);opacity:1}30%{transform:scaleY(1.2);opacity:.85}"
        "55%{transform:scaleY(.9)}80%{transform:scaleY(1.1);opacity:.95}}"
    )

    def candle(x):
        return (
            f'<rect x="{x - 1}" y="38" width="4" height="7" fill="{GOLD_HI}" class="fl"/>'
            f'<rect x="{x}" y="41" width="2" height="4" fill="#fff4d6" class="fl"/>'
            f'<rect x="{x - 3}" y="46" width="8" height="20" fill="{PARCH}"/>'
            f'<rect x="{x - 3}" y="46" width="2" height="20" fill="#b9b29b"/>'
            f'<rect x="{x - 6}" y="66" width="14" height="3" fill="{GOLD_LO}"/>'
        )

    body = (
        frame(W, h)
        + candle(52) + candle(W - 54)
        + f'<g fill="{GOLD}">{text_rects(l1, (W - text_width(l1, s)) // 2, 18, s)}</g>'
        + f'<g fill="{RUNE}">{text_rects(l2, (W - text_width(l2, s)) // 2, 52, s)}</g>'
    )
    return svg(W, h, body, style, "Build what should exist. Share what others can use.")


HEADINGS = [
    ("01", "THE CODEX", "research"),
    ("02", "THE WORKSHOP", "building"),
    ("03", "ACTIVE QUESTS", "lantern"),
    ("04", "RESEARCH NOTES", "privacy"),
    ("05", "THE JOURNEY", "decentralization"),
]


def write(rel, content):
    path = os.path.join(A, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"{rel:32s} {len(content) / 1024:7.1f} KB")


if __name__ == "__main__":
    write("banner/header.svg", build_header())
    write("hero/hero.svg", build_hero())
    write("dividers/rune-divider.svg", build_divider())
    write("dividers/footer.svg", build_footer())
    for num, title, icon in HEADINGS:
        slug = title.lower().replace(" ", "-")
        write(f"headings/{num}-{slug}.svg", build_heading(num, title, icon))
