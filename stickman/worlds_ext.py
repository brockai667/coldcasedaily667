# -*- coding: utf-8 -*-
"""Svety cave / forest / city (+ varianty: forest "fallen" = Tunguska, city "library" = interier
kniznice). Kreslene rovnakou linkou ako hill/snow/desert (INK obrys, papierove vyplne, ziadne
cierne plochy). Kazda funkcia vracia cisty SVG retazec; dispatch je vo worlds/stage/shots.

Suradnice:
  far_*       vzdialena vrstva uvodu/slucky (world_far): x -900..2400, zem vrstvy ~1160-1190,
              obrazovkova horna hrana ~ y 0-160 (paralaxa 0.18, mierka zf)
  walk_*      blizka vrstva hill_world (world suradnice, teren hy(x))
  backdrop_*  pozadie inscenovanych zaberov (obrazovka, zem na `hor`)
  top_*       staticke pozadie interieru (jaskyna/kniznica) namiesto oblohy so slnkom
  ground_* / dressing_* / fore_*  zem a drobnosti inscenovanych zaberov (world, zem na y)
"""
import math
import random

from props import DIRT2, INK, LEAF, METAL, PAPER, WOOD, ell, grass

# ------------------------------------------------------------------ palety
CAVE_WALL = "#ddd3c0"      # zadna stena jaskyne - svetly teply kamen (papier, nie tma)
CAVE_ROCK = "#c5b89f"      # strop, stlpy
CAVE_FAR_FLOOR = "#cdc0a7"
CAVE_FLOOR = "#d4c9b4"
CAVE_SUB = "#bdb098"
CAVE_LINE = "#a5987f"
CAVE_HOLE = "#a1947d"      # otvor chodby: tmavsi kamen, nie cierna
CAVE_HOLE2 = "#8c806b"
GLOW = "#ffd98a"
FLAME, FLAME2 = "#f39c34", "#ffd45a"

PINE = "#4d6b52"
PINE_MID = ("#6f8f6a", "#627f5e")
PINE_NEAR = "#7e9b73"
PINE_FAR, PINE_FAR_LINE = "#bdcab6", "#94a68f"
FOREST_FLOOR, FOREST_SUB, NEEDLE = "#d8d4aa", "#bba77c", "#b5ac7a"
BURNT_FLOOR = "#d6ccab"
BARK = "#5c3d22"

WALLS = ("#efe3c8", "#e7d4b1", "#e0d9c9", "#ecdcc0")
ROOFS = ("#c98b6b", "#b87458", "#9aa3aa", "#c27d5f")
WIN = "#a9c0cb"
SKYLINE, SKYLINE_LINE = "#e6dfcf", "#b9af9b"
COBBLE, COBBLE_SUB, COBBLE_LINE = "#d8d0c1", "#bfb5a3", "#aea38e"

LIB_WALL = "#ecdfc6"
SHELF, SHELF_BACK = "#a8743f", "#caa77b"
BOOKS = ("#b5543c", "#3f6f8f", "#6f8f4f", "#c9a24a", "#8a5c7a", "#7a5230", "#d9c9a0", "#4f7a78")
WOODF, WOODF_SUB, WOODF_LINE = "#ddc298", "#c8a778", "#a98655"
BEAM = "#8a5c33"


WX0 = -3400          # pevny zaciatok generovania blizkej vrstvy (nezavisi od x0 zaberu)


def _sm(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


# ================================================================== spolocne kusy
def pine(x, y, h, fill=PINE, sw=5, trunk=True):
    """Ihlican stojaci na (x, y) - kmen + tri stupne, rovnaky tvar ako borovice v snehu."""
    out = ""
    if trunk:
        tw = max(8.0, h * 0.075)
        out += (f'<path d="M{x - tw / 2:.0f},{y + 6:.0f} V{y - h * 0.24:.0f} H{x + tw / 2:.0f} V{y + 6:.0f}" '
                f'fill="{WOOD}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')
    for base, apex, hw in ((0.16, 0.60, 0.30), (0.38, 0.80, 0.235), (0.58, 1.0, 0.17)):
        out += (f'<path d="M{x - h * hw:.0f},{y - h * base:.0f} L{x:.0f},{y - h * apex:.0f} L{x + h * hw:.0f},{y - h * base:.0f} Z" '
                f'fill="{fill}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')
    return out


def stalagmite(x, y, h, w, fill=CAVE_FLOOR, sw=6):
    """Kvapel rastuci zo zeme: spodok je otvoreny a zapusteny pod ciaru zeme, takze
    vyrasta z podlahy - nie je nalepeny na nej."""
    return (f'<path d="M{x - w / 2:.0f},{y + 14:.0f} Q{x - w * 0.30:.0f},{y - h * 0.45:.0f} {x - w * 0.07:.0f},{y - h * 0.93:.0f} '
            f'Q{x + w * 0.02:.0f},{y - h - 4:.0f} {x + w * 0.10:.0f},{y - h * 0.90:.0f} '
            f'Q{x + w * 0.32:.0f},{y - h * 0.40:.0f} {x + w / 2:.0f},{y + 14:.0f}" '
            f'fill="{fill}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')


def stalactite(x, y, h, w, fill=CAVE_ROCK, sw=6):
    """Kvapel visiaci zo stropu: vrch je otvoreny a zasahuje do stropu (kresli sa po strope)."""
    return (f'<path d="M{x - w / 2:.0f},{y - 6:.0f} Q{x - w * 0.24:.0f},{y + h * 0.45:.0f} {x - w * 0.05:.0f},{y + h * 0.94:.0f} '
            f'Q{x + w * 0.04:.0f},{y + h + 3:.0f} {x + w * 0.09:.0f},{y + h * 0.90:.0f} '
            f'Q{x + w * 0.28:.0f},{y + h * 0.42:.0f} {x + w / 2:.0f},{y - 6:.0f}" '
            f'fill="{fill}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')


def torch(x, y, s=1.0):
    """Fakla na stene: teply svit (tri priesvitne kruhy), drziak, drevo, plamen."""
    glow = "".join(f'<circle cx="{x:.0f}" cy="{y - 46 * s:.0f}" r="{rr * s:.0f}" fill="{GLOW}" opacity="{o}"/>'
                   for rr, o in ((200, 0.13), (132, 0.15), (74, 0.22)))
    stick = (f'<path d="M{x + 14 * s:.0f},{y + 74 * s:.0f} L{x:.0f},{y - 12 * s:.0f}" stroke="{INK}" '
             f'stroke-width="{19 * s:.1f}" stroke-linecap="round"/>'
             f'<path d="M{x + 14 * s:.0f},{y + 74 * s:.0f} L{x:.0f},{y - 12 * s:.0f}" stroke="{WOOD}" '
             f'stroke-width="{11 * s:.1f}" stroke-linecap="round"/>'
             f'<path d="M{x + 36 * s:.0f},{y + 36 * s:.0f} h{-30 * s:.0f}" stroke="{INK}" stroke-width="{7 * s:.1f}" '
             f'stroke-linecap="round"/>')
    flame = (f'<path d="M{x:.0f},{y - 86 * s:.0f} q{28 * s:.0f},{36 * s:.0f} {15 * s:.0f},{62 * s:.0f} '
             f'q{-15 * s:.0f},{17 * s:.0f} {-30 * s:.0f},0 q{-13 * s:.0f},{-28 * s:.0f} {15 * s:.0f},{-62 * s:.0f} z" '
             f'fill="{FLAME}" stroke="{INK}" stroke-width="{5 * s:.1f}" stroke-linejoin="round"/>'
             f'<path d="M{x:.0f},{y - 56 * s:.0f} q{12 * s:.0f},{17 * s:.0f} {6 * s:.0f},{29 * s:.0f} '
             f'q{-6 * s:.0f},{8 * s:.0f} {-12 * s:.0f},0 q{-5 * s:.0f},{-12 * s:.0f} {6 * s:.0f},{-29 * s:.0f} z" '
             f'fill="{FLAME2}" stroke="none"/>')
    return glow + stick + flame


def fern(x, y, s=1.0, col=LEAF):
    """Paprad / podrast: vejar oblukov s listkami."""
    out = ""
    for a, L in ((-62, 52), (-32, 70), (-4, 78), (26, 66), (56, 48)):
        rad = math.radians(a - 90)
        ex, ey = x + math.cos(rad) * L * s, y + math.sin(rad) * L * s
        cx, cy = x + math.cos(rad) * L * s * 0.5 - 8 * s, y + math.sin(rad) * L * s * 0.5 - 10 * s
        out += f'<path d="M{x:.0f},{y:.0f} Q{cx:.0f},{cy:.0f} {ex:.0f},{ey:.0f}"/>'
    return f'<g fill="none" stroke="{col}" stroke-width="{6 * s:.1f}" stroke-linecap="round">{out}</g>'


def stump(x, y, w=46, h=38, jag=False):
    out = (f'<path d="M{x - w / 2 - 8:.0f},{y + 12:.0f} Q{x - w / 2:.0f},{y - h * 0.4:.0f} {x - w / 2:.0f},{y - h:.0f} '
           + (f"l10,-12 l10,10 l8,-16 l9,14 L{x + w / 2:.0f},{y - h:.0f} " if jag else f"H{x + w / 2:.0f} ")
           + f'Q{x + w / 2:.0f},{y - h * 0.4:.0f} {x + w / 2 + 8:.0f},{y + 12:.0f}" fill="{WOOD}" stroke="{INK}" '
           f'stroke-width="6" stroke-linejoin="round"/>')
    if not jag:
        out += f'<path d="{ell(x, y - h, w / 2, 8)}" fill="#c9a36a" stroke="{INK}" stroke-width="5"/>'
    return out


def log_along(hy, xa, xb, r=22, cut_right=True):
    """Kmen lezi na zemi pozdlz terenu (od xa po xb) - obrys + drevo + rezana cela."""
    pts = [(x, hy(x) - r + 4) for x in range(int(xa), int(xb) + 1, 20)]
    d = "M" + " L".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    ex, ey = pts[-1] if cut_right else pts[0]
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{2 * r + 10}" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{WOOD}" stroke-width="{2 * r - 2}" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{BARK}" stroke-width="4" stroke-dasharray="26 34" opacity="0.7"/>'
            f'<path d="{ell(ex, ey, r * 0.62, r)}" fill="#c9a36a" stroke="{INK}" stroke-width="5"/>'
            f'<path d="{ell(ex, ey, r * 0.28, r * 0.45)}" fill="none" stroke="{BARK}" stroke-width="3"/>')


def uprooted(hy, x, length, r=20, top_right=True):
    """Vyvrateny kmen (Tunguska): koren s hlinou trci hore na jednom konci, kmen lezi po zemi."""
    sgn = 1 if top_right else -1
    xb = x + sgn * length
    xa, xz = (x, xb) if top_right else (xb, x)
    pts = [(xx, hy(xx) - r + 4) for xx in range(int(xa), int(xz) + 1, 20)]
    d = "M" + " L".join(f"{a:.0f},{b:.0f}" for a, b in pts)
    # koren: zvisly kotuc hliny s korenmi dookola, stred na osi kmena, spodok zapadnuty v jame
    rx, ry = x, hy(x) - r + 4
    pr = r * 4.6
    roots = " ".join(f"M{rx + math.cos(a) * pr * 0.92:.0f},{ry + math.sin(a) * pr * 1.05:.0f} "
                     f"l{math.cos(a) * pr * 0.55:.0f},{math.sin(a) * pr * 0.55:.0f}"
                     for a in [k * math.pi / 5 - math.pi / 2 for k in range(10)] if math.sin(a) < 0.55)
    plate = (f'<path d="{roots}" stroke="{WOOD}" stroke-width="6" stroke-linecap="round" fill="none"/>'
             f'<path d="{ell(rx, ry, pr * 0.82, pr)}" fill="{DIRT2}" stroke="{INK}" stroke-width="6"/>'
             f'<path d="{ell(rx, ry, pr * 0.40, pr * 0.52)}" fill="#8a6e45" stroke="none" opacity="0.7"/>'
             f'<path d="M{rx - pr * 0.5:.0f},{ry - pr * 0.3:.0f} l{-pr * 0.3:.0f},{-pr * 0.1:.0f} M{rx + pr * 0.3:.0f},{ry + pr * 0.5:.0f} '
             f'l{pr * 0.2:.0f},{pr * 0.2:.0f}" stroke="{WOOD}" stroke-width="5" stroke-linecap="round" fill="none"/>')
    stubs = "".join(f'<path d="M{xx:.0f},{hy(xx) - r * 1.5:.0f} l{sgn * 22:.0f},-30" stroke="{INK}" stroke-width="7" '
                    f'stroke-linecap="round" fill="none"/>' for xx in (x + sgn * length * 0.45, x + sgn * length * 0.72))
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{2 * r + 10}" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{WOOD}" stroke-width="{2 * r - 2}" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{BARK}" stroke-width="4" stroke-dasharray="30 28" opacity="0.7"/>'
            + stubs + plate)


def fallen_fan(cx, cy, rx, ry, n, r, sw=8.0):
    """Vyvratene kmene do kruhu okolo epicentra - pohlad na rovinu zeme (Tunguska):
    koren k stredu, koruna von; vzdialenejsie (hore) tensie, blizsie hrubsie."""
    items = []
    for i in range(n):
        a = (i + r.random() * 0.7) / n * 2 * math.pi
        r1 = 0.30 + r.random() * 0.16
        r2 = r1 + 0.40 + r.random() * 0.30
        x1, y1 = cx + math.cos(a) * r1 * rx, cy + math.sin(a) * r1 * ry
        x2, y2 = cx + math.cos(a) * r2 * rx, cy + math.sin(a) * r2 * ry
        k = 0.65 + 0.7 * (math.sin(a) + 1) / 2
        items.append(((y1 + y2) / 2, x1, y1, x2, y2, k))
    items.sort()
    out = ""
    for _, x1, y1, x2, y2, k in items:
        w = sw * k
        L = math.hypot(x2 - x1, y2 - y1) or 1.0
        nx, ny = -(y2 - y1) / L, (x2 - x1) / L
        w1, w2 = w * 0.62, w * 0.22
        out += (f'<path d="M{x1 + nx * w1:.1f},{y1 + ny * w1:.1f} L{x2 + nx * w2:.1f},{y2 + ny * w2:.1f} '
                f'L{x2 - nx * w2:.1f},{y2 - ny * w2:.1f} L{x1 - nx * w1:.1f},{y1 - ny * w1:.1f} Z" fill="{WOOD}" '
                f'stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
                f'<path d="{ell(x1, y1, w * 1.25, w * 1.05)}" fill="{DIRT2}" stroke="{INK}" stroke-width="3"/>')
    return out


def bare_pole(x, y, h, sw=9):
    """Stojaci mrtvy kmen bez konarov (stred vybuchu)."""
    return (f'<path d="M{x:.0f},{y + 4:.0f} V{y - h:.0f}" stroke="{INK}" stroke-width="{sw + 7}" stroke-linecap="round"/>'
            f'<path d="M{x:.0f},{y + 4:.0f} V{y - h:.0f}" stroke="{WOOD}" stroke-width="{sw}" stroke-linecap="round"/>'
            f'<path d="M{x:.0f},{y - h * 0.62:.0f} l{h * 0.12:.0f},{-h * 0.10:.0f} M{x:.0f},{y - h * 0.40:.0f} '
            f'l{-h * 0.10:.0f},{-h * 0.08:.0f}" stroke="{INK}" stroke-width="5" stroke-linecap="round" fill="none"/>')


def house(x, base, w, h, r, wall=None, roof=None, sw=6):
    """Mestsky dom (x = lava hrana): stena, stit so strechou, okna s kriz, niekedy dvere,
    komin a hrazdenie."""
    wall = wall or r.choice(WALLS)
    roof = roof or r.choice(ROOFS)
    rh = h * r.uniform(0.34, 0.52)
    out = (f'<path d="M{x:.0f},{base + 8:.0f} V{base - h:.0f} H{x + w:.0f} V{base + 8:.0f}" fill="{wall}" stroke="{INK}" '
           f'stroke-width="{sw}" stroke-linejoin="round"/>')
    if r.random() < 0.3:
        out += (f'<path d="M{x:.0f},{base - h * 0.55:.0f} L{x + w * 0.5:.0f},{base - h * 0.95:.0f} L{x + w:.0f},{base - h * 0.55:.0f} '
                f'M{x + w * 0.5:.0f},{base - h * 0.55:.0f} V{base - h * 0.95:.0f}" stroke="{WOOD}" stroke-width="{sw - 1}" fill="none"/>')
    if r.random() < 0.5:
        cxh = x + w * r.uniform(0.62, 0.78)
        out += (f'<path d="M{cxh - 12:.0f},{base - h - rh * 0.25:.0f} v{-rh * 0.55:.0f} h26 v{rh * 0.40:.0f}" fill="{wall}" '
                f'stroke="{INK}" stroke-width="{sw - 1}" stroke-linejoin="round"/>')
    out += (f'<path d="M{x - 14:.0f},{base - h:.0f} L{x + w / 2:.0f},{base - h - rh:.0f} L{x + w + 14:.0f},{base - h:.0f} Z" '
            f'fill="{roof}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')
    cols = max(1, int(w // 78))
    rows = max(1, int((h - 70) // 92))
    gx = w / cols
    for i in range(rows):
        for j in range(cols):
            wx, wy = x + gx * (j + 0.5), base - h + 44 + i * 92
            if i == rows - 1 and cols >= 2 and j == cols // 2 and r.random() < 0.6:
                out += (f'<path d="M{wx - 20:.0f},{base + 4:.0f} V{base - 60:.0f} q20,-24 40,0 V{base + 4:.0f}" '
                        f'fill="{WOOD}" stroke="{INK}" stroke-width="{sw - 1}" stroke-linejoin="round"/>')
                continue
            out += (f'<path d="M{wx - 16:.0f},{wy:.0f} h32 v44 h-32 z" fill="{WIN}" stroke="{INK}" stroke-width="{sw - 2}" '
                    f'stroke-linejoin="round"/><path d="M{wx:.0f},{wy:.0f} v44 M{wx - 16:.0f},{wy + 20:.0f} h32" '
                    f'stroke="{PAPER}" stroke-width="3" fill="none"/>')
    return out


def lamp_post(x, y, h=400, s=1.0):
    """Poulicna lampa: podstavec, stlp, lucerna so svetlym sklom."""
    return (f'<path d="M{x - 22 * s:.0f},{y + 6:.0f} h{44 * s:.0f} l{-8 * s:.0f},{-34 * s:.0f} h{-28 * s:.0f} z" fill="{METAL}" '
            f'stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x:.0f},{y - 30 * s:.0f} V{y - h + 40 * s:.0f}" stroke="{INK}" stroke-width="{11 * s:.1f}" stroke-linecap="round"/>'
            f'<path d="M{x - 26 * s:.0f},{y - h + 40 * s:.0f} h{52 * s:.0f} l{-8 * s:.0f},{-58 * s:.0f} h{-36 * s:.0f} z" '
            f'fill="#fff1c2" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x - 26 * s:.0f},{y - h - 18 * s:.0f} h{52 * s:.0f} l{-26 * s:.0f},{-22 * s:.0f} z" fill="{INK}" '
            f'stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')


def bookshelf(x, base, w, h, r, sw=6):
    """Regal s knihami (x = lava hrana): zadna stena, bocnice, police, farebne chrbty,
    obcas naklonena kniha alebo medzera."""
    out = (f'<path d="M{x:.0f},{base + 6:.0f} V{base - h:.0f} H{x + w:.0f} V{base + 6:.0f} Z" fill="{SHELF_BACK}" '
           f'stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')
    sh = 104
    y = base - 26
    while y - sh > base - h + 20:
        bx = x + 16
        while bx < x + w - 34:
            bw = r.randint(14, 26)
            bh = r.randint(58, 88)
            if r.random() < 0.08:
                bx += bw + 10
                continue
            col = r.choice(BOOKS)
            if r.random() < 0.07 and bx + bw + 30 < x + w - 16:
                out += (f'<path d="M{bx:.0f},{y:.0f} l{bw:.0f},0 l{bh * 0.30:.0f},{-bh * 0.95:.0f} l{-bw:.0f},0 z" fill="{col}" '
                        f'stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
                bx += bw + bh * 0.3 + 4
                continue
            out += (f'<path d="M{bx:.0f},{y:.0f} h{bw} v{-bh} h{-bw} z" fill="{col}" stroke="{INK}" stroke-width="3" '
                    f'stroke-linejoin="round"/><path d="M{bx + 2:.0f},{y - bh * 0.78:.0f} h{bw - 4}" stroke="{PAPER}" '
                    f'stroke-width="3" opacity="0.6"/>')
            bx += bw + 2
        out += (f'<path d="M{x:.0f},{y:.0f} h{w} v12 h{-w} z" fill="{SHELF}" stroke="{INK}" stroke-width="4" '
                f'stroke-linejoin="round"/>')
        y -= sh
    out += (f'<path d="M{x - 10:.0f},{base - h - 26:.0f} h{w + 20} v26 h{-(w + 20)} z" fill="{SHELF}" stroke="{INK}" '
            f'stroke-width="{sw}" stroke-linejoin="round"/>'
            f'<path d="M{x:.0f},{base + 6:.0f} V{base - h:.0f} M{x + w:.0f},{base + 6:.0f} V{base - h:.0f}" stroke="{SHELF}" '
            f'stroke-width="{sw + 8}" fill="none"/>'
            f'<path d="M{x - 7:.0f},{base + 6:.0f} V{base - h:.0f} M{x + 7:.0f},{base + 6:.0f} V{base - h:.0f} '
            f'M{x + w - 7:.0f},{base + 6:.0f} V{base - h:.0f} M{x + w + 7:.0f},{base + 6:.0f} V{base - h:.0f}" '
            f'stroke="{INK}" stroke-width="4" fill="none"/>')
    return out


def arch_window(x, base, w, h):
    """Vysoke oblúkove okno kniznice so svetlom."""
    top = base - h
    return (f'<path d="M{x - w / 2:.0f},{base:.0f} V{top + w / 2:.0f} Q{x - w / 2:.0f},{top:.0f} {x:.0f},{top:.0f} '
            f'Q{x + w / 2:.0f},{top:.0f} {x + w / 2:.0f},{top + w / 2:.0f} V{base:.0f} Z" fill="#dcebf0" stroke="{INK}" '
            f'stroke-width="7" stroke-linejoin="round"/>'
            f'<path d="M{x:.0f},{top:.0f} V{base:.0f} M{x - w / 2:.0f},{top + h * 0.45:.0f} H{x + w / 2:.0f}" '
            f'stroke="{INK}" stroke-width="5" fill="none"/>'
            f'<path d="M{x - w / 2 + 14:.0f},{top + w * 0.7:.0f} l{w * 0.3:.0f},{-w * 0.3:.0f}" stroke="{PAPER}" '
            f'stroke-width="7" stroke-linecap="round" fill="none"/>')


def hanging_lamp(x, y_top, y, s=1.0):
    """Zavesna lampa: retiazka od stropu, tienidlo, teply svit."""
    return (f'<circle cx="{x:.0f}" cy="{y + 30 * s:.0f}" r="{110 * s:.0f}" fill="{GLOW}" opacity="0.18"/>'
            f'<circle cx="{x:.0f}" cy="{y + 30 * s:.0f}" r="{60 * s:.0f}" fill="{GLOW}" opacity="0.22"/>'
            f'<path d="M{x:.0f},{y_top:.0f} V{y:.0f}" stroke="{INK}" stroke-width="4" stroke-dasharray="8 6"/>'
            f'<path d="M{x - 40 * s:.0f},{y + 36 * s:.0f} q{40 * s:.0f},{-56 * s:.0f} {80 * s:.0f},0 z" fill="#c9a24a" '
            f'stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x - 20 * s:.0f},{y + 36 * s:.0f} q{20 * s:.0f},{24 * s:.0f} {40 * s:.0f},0" fill="#fff1c2" '
            f'stroke="{INK}" stroke-width="4"/>')


def bats():
    one = ('<path d="M-26,0 q8,-12 15,-4 q4,-11 11,-1 q7,-10 11,1 q7,-8 15,4 q-11,2 -15,8 q-6,-6 -11,0 '
           'q-6,-7 -11,0 q-5,-6 -15,-8 z"/>')
    return (f'<g fill="{INK}" stroke="{INK}" stroke-width="2" stroke-linejoin="round">'
            f'<g transform="translate(470,430) scale(1.1)">{one}</g><g transform="translate(560,470) scale(0.8)">{one}</g>'
            f'<g transform="translate(1520,380) scale(0.9)">{one}</g></g>')


def birds():
    """Vtaky v dialke - len cez den bez dazda (look.birds; bez LOOK-u povodne dva vtaky)."""
    import look
    return look.birds()


def clouds_group(p):
    """Rovnake oblaky ako hill/snow (poloha je v simulacii final_walk, aby nesli cez slnko);
    oblohu podla casu/pocasia epizody kresli look.walk_clouds."""
    import look
    return look.walk_clouds(p)


# ================================================================== JASKYNA
def cave_edge(x):
    """Spodna hrana stropu vo vzdialenej vrstve."""
    return 215 + 26 * math.sin(x / 173.0) + 14 * math.sin(x / 61.0 + 1.3)


def far_cave(p):
    r = random.Random(11)
    X0, X1 = -900, 2400
    out = f'<path d="M{X0},-700 H{X1} V1460 H{X0} Z" fill="{CAVE_WALL}" opacity="0.94"/>'
    for y0 in (430, 580, 720, 880, 1010):
        x = X0 + r.randint(0, 220)
        while x < X1:
            L = r.randint(160, 420)
            out += (f'<path d="M{x},{y0 + r.randint(-24, 24)} q{L // 2},{r.randint(-18, 18)} {L},{r.randint(-10, 10)}" '
                    f'stroke="{CAVE_LINE}" stroke-width="6" fill="none" stroke-linecap="round" opacity="0.5"/>')
            x += L + r.randint(90, 280)
    for x in (-430, 350, 1110, 1880):
        w, h, b = r.randint(180, 230), r.randint(250, 310), 1168
        out += (f'<path d="M{x - w / 2:.0f},{b} V{b - h * 0.55:.0f} Q{x - w / 2:.0f},{b - h} {x},{b - h} '
                f'Q{x + w / 2:.0f},{b - h} {x + w / 2:.0f},{b - h * 0.55:.0f} V{b} Z" fill="{CAVE_ROCK}" stroke="{INK}" '
                f'stroke-width="6" stroke-linejoin="round"/>'
                f'<path d="M{x - w * 0.31:.0f},{b} V{b - h * 0.45:.0f} Q{x - w * 0.31:.0f},{b - h * 0.80:.0f} {x},{b - h * 0.80:.0f} '
                f'Q{x + w * 0.31:.0f},{b - h * 0.80:.0f} {x + w * 0.31:.0f},{b - h * 0.45:.0f} V{b} Z" fill="{CAVE_HOLE}" '
                f'stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
                f'<path d="M{x - w * 0.18:.0f},{b} V{b - h * 0.36:.0f} Q{x - w * 0.18:.0f},{b - h * 0.60:.0f} {x},{b - h * 0.60:.0f} '
                f'Q{x + w * 0.18:.0f},{b - h * 0.60:.0f} {x + w * 0.18:.0f},{b - h * 0.36:.0f} V{b} Z" fill="{CAVE_HOLE2}" '
                f'stroke="none"/>')
    fl = " ".join(f"L{x},{1165 + 10 * math.sin(x / 90.0):.0f}" for x in range(X0, X1 + 1, 40))
    out += (f'<path d="M{X0},1460 {fl} L{X1},1460 Z" fill="{CAVE_FAR_FLOOR}" stroke="none"/>'
            f'<path d="M{X0},1165 {fl[fl.index("L", 1):] if fl.count("L") > 1 else fl}" fill="none" stroke="{CAVE_LINE}" '
            f'stroke-width="6" stroke-linecap="round"/>')
    for x in range(X0 + 60, X1, 170):
        if r.random() < 0.55:
            h = r.randint(40, 110)
            out += stalagmite(x + r.randint(-40, 40), 1168, h, h * r.uniform(0.45, 0.65), CAVE_FAR_FLOOR, 5)
    # fakle nizsie (plamen pod hlavou postavy aj pod zlatym textom konca) a mimo miesta Boba vo frame 0
    for x in (560, 1300, 2050):
        out += torch(x, 900, 1.0)
    # strop: spodna hrana nepravidelna, potom stlpy a kvaple "vtiahnute" do stropu
    edge = " ".join(f"L{x},{cave_edge(x):.0f}" for x in range(X1, X0 - 1, -20))
    out += (f'<path d="M{X0},-700 H{X1} V{cave_edge(X1):.0f} {edge} Z" fill="{CAVE_ROCK}" stroke="{INK}" '
            f'stroke-width="7" stroke-linejoin="round"/>')
    for x in (40, 760, 1500, 2150):
        w = r.randint(90, 128)
        mid = r.randint(640, 760)
        xl, xr = x - w * 0.95, x + w * 0.95
        out += (f'<path d="M{xl:.0f},{cave_edge(xl) - 4:.0f} Q{x - w * 0.22:.0f},{mid - 150} {x - w * 0.28:.0f},{mid} '
                f'Q{x - w * 0.30:.0f},{mid + 170} {x - w * 0.85:.0f},1176 H{x + w * 0.85:.0f} '
                f'Q{x + w * 0.30:.0f},{mid + 170} {x + w * 0.28:.0f},{mid} Q{x + w * 0.22:.0f},{mid - 150} {xr:.0f},{cave_edge(xr) - 4:.0f}" '
                f'fill="{CAVE_ROCK}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
                f'<path d="M{x - w * 0.20:.0f},{mid - 60} q{w * 0.2:.0f},12 {w * 0.4:.0f},0 M{x - w * 0.24:.0f},{mid + 90} '
                f'q{w * 0.24:.0f},14 {w * 0.48:.0f},0" stroke="{CAVE_LINE}" stroke-width="5" fill="none" stroke-linecap="round"/>')
    x = X0 + 20
    while x < X1:
        if r.random() < 0.8:
            w, h = r.randint(26, 58), r.randint(40, 150)
            out += stalactite(x, cave_edge(x), h, w, CAVE_ROCK, 6)
        x += r.randint(55, 150)
    return f'<g id="{p}_far">{out}<g id="{p}_cloud">{bats()}</g></g>'


def top_cave(p):
    """Inscenovane zabery v jaskyni: zadna stena + strop s kvaplami + fakle (obrazovka, staticke)."""
    r = random.Random(5)
    out = f'<path d="M-40,-80 H1120 V1420 H-40 Z" fill="{CAVE_WALL}" opacity="0.94"/>'
    for y0 in (420, 560, 700, 860, 1010):
        x = -40 + r.randint(0, 160)
        while x < 1120:
            L = r.randint(140, 360)
            out += (f'<path d="M{x},{y0 + r.randint(-20, 20)} q{L // 2},{r.randint(-16, 16)} {L},{r.randint(-8, 8)}" '
                    f'stroke="{CAVE_LINE}" stroke-width="6" fill="none" stroke-linecap="round" opacity="0.5"/>')
            x += L + r.randint(80, 240)
    out += torch(330, 700, 0.9) + torch(770, 660, 0.9)

    def edge(x):
        return 150 + 22 * math.sin(x / 150.0 + 0.4) + 12 * math.sin(x / 53.0)
    e = " ".join(f"L{x},{edge(x):.0f}" for x in range(1120, -41, -20))
    out += (f'<path d="M-40,-100 H1120 V{edge(1120):.0f} {e} Z" fill="{CAVE_ROCK}" stroke="{INK}" stroke-width="7" '
            f'stroke-linejoin="round"/>')
    x = -20
    while x < 1110:
        if r.random() < 0.8:
            w, h = r.randint(24, 52), r.randint(34, 130)
            out += stalactite(x, edge(x), h, w, CAVE_ROCK, 6)
        x += r.randint(50, 130)
    return out


def backdrop_cave(hor, r):
    """Vzdialena cast jaskyne v inscenovanych zaberoch: dno, otvory chodieb, stlpy-kvaple."""
    out = ""
    for x in (300, 870):
        w, h, b = 200, 270, hor - 40
        out += (f'<path d="M{x - w / 2:.0f},{b + 40} V{b - h * 0.55:.0f} Q{x - w / 2:.0f},{b - h} {x},{b - h} '
                f'Q{x + w / 2:.0f},{b - h} {x + w / 2:.0f},{b - h * 0.55:.0f} V{b + 40} Z" fill="{CAVE_ROCK}" stroke="{INK}" '
                f'stroke-width="6" stroke-linejoin="round"/>'
                f'<path d="M{x - w * 0.31:.0f},{b + 40} V{b - h * 0.45:.0f} Q{x - w * 0.31:.0f},{b - h * 0.8:.0f} {x},{b - h * 0.8:.0f} '
                f'Q{x + w * 0.31:.0f},{b - h * 0.8:.0f} {x + w * 0.31:.0f},{b - h * 0.45:.0f} V{b + 40} Z" fill="{CAVE_HOLE}" '
                f'stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    fl = " ".join(f"L{x},{hor - 42 + 9 * math.sin(x / 80.0):.0f}" for x in range(-300, 1401, 40))
    out += (f'<path d="M-300,{hor + 60} {fl} L1400,{hor + 60} Z" fill="{CAVE_FAR_FLOOR}" stroke="none"/>'
            f'<path d="M-300,{hor - 42} {fl}" fill="none" stroke="{CAVE_LINE}" stroke-width="6"/>')
    for x, h, w in ((70, 560, 120), (1010, 520, 110), (560, 150, 64), (190, 110, 52), (930, 130, 56)):
        out += stalagmite(x, hor - 40, h, w, CAVE_ROCK, 6)
    return out


def ground_cave(y, x0, x1):
    cracks = "".join(f'<path d="M{x},{y + 60 + (i % 3) * 90} l24,18 l-10,24 l30,16" fill="none" stroke="{CAVE_LINE}" '
                     f'stroke-width="5" stroke-linecap="round"/>' for i, x in enumerate(range(x0 + 150, x1, 380)))
    return (f'<path d="M{x0},{y} H{x1} V4200 H{x0} Z" fill="{CAVE_FLOOR}" stroke="{INK}" stroke-width="9"/>'
            f'<path d="M{x0},{y + 230} H{x1} V4200 H{x0} Z" fill="{CAVE_SUB}" stroke="none" opacity="0.6"/>{cracks}')


def dressing_cave(seed, y, xs):
    r = random.Random(seed)
    out = "".join(stalagmite(x, y, r.randint(60, 110), r.randint(40, 64), CAVE_FLOOR, 6) for x in xs[::2])
    return out


def fore_cave(x0, x1, gy, r):
    w = x1 - x0
    return (stalagmite(x0 + (0.05 + r.random() * 0.06) * w, gy, r.randint(90, 150), r.randint(60, 90), CAVE_FLOOR, 6)
            + stalagmite(x1 - (0.05 + r.random() * 0.06) * w, gy, r.randint(70, 130), r.randint(50, 80), CAVE_FLOOR, 6))


def walk_cave(hy, x0, x1):
    r = random.Random(21)
    out = ""
    x = WX0 + 120
    while x < x1:
        if not (40 < x < 200):
            h = r.randint(70, 150)
            out += stalagmite(x, hy(x), h, h * r.uniform(0.45, 0.62), CAVE_FLOOR, 7)
        x += r.randint(360, 640)
    return out


# ================================================================== LES (tajga) + variant "fallen"
def far_forest(p, variant=""):
    r = random.Random(13)
    X0, X1 = -900, 2400
    fallen = variant == "fallen"
    base_far = 1070 if fallen else 1150
    pts, x = [], X0
    while x < X1:
        w = r.randint(36, 62)
        h = r.randint(55, 115) if not fallen else r.randint(35, 80)
        pts += [(x, base_far - h * 0.22), (x + w / 2, base_far - h), (x + w, base_far - h * 0.22)]
        x += w - r.randint(4, 14)
    d = f"M{X0},1460 L{X0},{base_far - 30} " + " ".join(f"L{a:.0f},{b:.0f}" for a, b in pts) + f" L{X1},{base_far - 30} L{X1},1460 Z"
    out = f'<path d="{d}" fill="{PINE_FAR}" stroke="{PINE_FAR_LINE}" stroke-width="5" stroke-linejoin="round"/>'
    gb = 1182
    gtop = 1076 if fallen else gb - 6
    out += (f'<path d="M{X0},{gtop} Q{X0 + 600},{gtop - 14} {X0 + 1400},{gtop + 2} T{X1},{gtop - 2} V1460 H{X0} Z" '
            f'fill="{BURNT_FLOOR if fallen else "#dcd9b3"}" stroke="{PINE_FAR_LINE}" stroke-width="5"/>')
    if not fallen:
        x = X0 + 30
        while x < X1:
            h = r.randint(210, 360)
            out += pine(x, gb, h, PINE_MID[r.randint(0, 1)], 5)
            x += r.randint(90, 170)
    else:
        out += fallen_fan(700, 1146, 860, 84, 44, r, 11.0)
        for x in (610, 670, 740, 800):
            out += bare_pole(x, 1146, r.randint(140, 220), 8)
        x = X0 + 40
        while x < X1:
            if abs(x - 700) > 1050:
                out += pine(x, gtop + 4, r.randint(120, 190), PINE_MID[r.randint(0, 1)], 5)
            x += r.randint(120, 200)
    return f'<g id="{p}_far">{out}{clouds_group(p)}{birds()}</g>'


def backdrop_forest(hor, r, variant=""):
    fallen = variant == "fallen"
    tb = hor - (190 if fallen else 40)
    pts, x = [], -300
    while x < 1400:
        w = r.randint(40, 66)
        h = r.randint(70, 150) if not fallen else r.randint(30, 70)
        pts += [(x, tb - h * 0.2), (x + w / 2, tb - h), (x + w, tb - h * 0.2)]
        x += w - r.randint(4, 14)
    d = f"M-300,{hor + 60} L-300,{tb - 20} " + " ".join(f"L{a:.0f},{b:.0f}" for a, b in pts) + f" L1400,{tb - 20} L1400,{hor + 60} Z"
    out = f'<path d="{d}" fill="{PINE_FAR}" stroke="{PINE_FAR_LINE}" stroke-width="5" stroke-linejoin="round"/>'
    if not fallen:
        for x, h in ((-10, 560), (120, 470), (230, 380), (860, 420), (975, 540), (1090, 480)):
            out += pine(x, hor - 20, h, PINE_MID[int(x) % 2], 6)
    else:
        out += (f'<path d="M-300,{tb + 6} Q540,{tb - 10} 1400,{tb + 6} V{hor + 60} H-300 Z" fill="{BURNT_FLOOR}" '
                f'stroke="{PINE_FAR_LINE}" stroke-width="5"/>')
        out += fallen_fan(540, hor - 92, 760, 92, 36, r, 12.0)
        for x, h in ((490, 170), (525, 220), (575, 200), (615, 150)):
            out += bare_pole(x, hor - 92, h, 8)
    return out


def ground_forest(y, x0, x1, variant=""):
    fill = BURNT_FLOOR if variant == "fallen" else FOREST_FLOOR
    lit = "".join(f'<path d="M{x},{y + 40 + (i % 4) * 70} l{18 + (i % 3) * 8},{-6 + (i % 2) * 10}" stroke="{NEEDLE}" '
                  f'stroke-width="4" stroke-linecap="round" fill="none"/>' for i, x in enumerate(range(x0 + 40, x1, 70)))
    return (f'<path d="M{x0},{y} H{x1} V4200 H{x0} Z" fill="{fill}" stroke="{INK}" stroke-width="9"/>'
            f'<path d="M{x0},{y + 260} H{x1} V4200 H{x0} Z" fill="{FOREST_SUB}" stroke="none" opacity="0.45"/>{lit}')


def dressing_forest(seed, y, xs, variant=""):
    r = random.Random(seed)
    if variant == "fallen":
        return "".join(stump(x, y, 44, r.randint(30, 60), True) for x in xs[::2])
    return "".join(fern(x, y + 4, r.uniform(0.8, 1.2)) + grass(x + 60, y + 3) for x in xs)


def fore_forest(x0, x1, gy, r, variant=""):
    w = x1 - x0
    xa, xb = x0 + (0.05 + r.random() * 0.05) * w, x1 - (0.05 + r.random() * 0.05) * w
    if variant == "fallen":
        return stump(xa, gy, 60, 70, True) + stump(xb, gy, 54, 52, True)
    return fern(xa, gy + 6, 1.4) + fern(xa + 70, gy + 6, 1.0) + stump(xb, gy, 60, 44)


def walk_forest(hy, x0, x1, variant=""):
    r = random.Random(23)
    out = ""
    if variant == "fallen":
        x = WX0 + 100
        while x < x1:
            if not (-60 < x < 260):
                out += uprooted(hy, x, r.randint(900, 1400), r.randint(16, 22), True)
            x += r.randint(900, 1300)
        x = WX0 + 360
        while x < x1:
            if not (40 < x < 200):
                out += stump(x, hy(x), 44, r.randint(40, 70), True)
            x += r.randint(640, 900)
        return out
    x = WX0 + 60
    while x < x1:
        # za Bobom vo frame 0 (a teda aj na konci slucky) ziadny blizky strom - postava ostane citatelna
        if not (-260 < x < 470):
            out += pine(x, hy(x) + 4, r.randint(300, 430), PINE_NEAR, 6)
        x += r.randint(300, 460)
    x = WX0 + 250
    while x < x1:
        out += log_along(hy, x, x + r.randint(220, 330), r.randint(18, 24))
        x += r.randint(1100, 1500)
    x = WX0 + 20
    while x < x1:
        out += fern(x, hy(x) + 4, r.uniform(0.8, 1.25))
        if r.random() < 0.5:
            out += grass(x + 50, hy(x + 50) + 3)
        x += r.randint(150, 260)
    return out


# ================================================================== MESTO + variant "library"
def far_city(p, variant=""):
    r = random.Random(17)
    X0, X1 = -900, 2400
    if variant == "library":
        return far_library(p)
    b = 1150
    pts, x = [], X0
    while x < X1:
        w = r.randint(90, 180)
        h = r.randint(130, 250)
        if r.random() < 0.12:     # vezicka / kostolna vez
            pts += [(x, b - h), (x + w * 0.35, b - h), (x + w * 0.5, b - h - r.randint(120, 200)), (x + w * 0.65, b - h), (x + w, b - h)]
        elif r.random() < 0.5:     # stit
            pts += [(x, b - h), (x + w / 2, b - h - 60), (x + w, b - h)]
        else:
            pts += [(x, b - h), (x + w, b - h)]
        x += w
    d = f"M{X0},1460 L{X0},{b} " + " ".join(f"L{a:.0f},{c:.0f}" for a, c in pts) + f" L{X1},{b} L{X1},1460 Z"
    out = f'<path d="{d}" fill="{SKYLINE}" stroke="{SKYLINE_LINE}" stroke-width="5" stroke-linejoin="round"/>'
    gb = 1186
    out += f'<path d="M{X0},{gb} H{X1} V1460 H{X0} Z" fill="#ddd6c7" stroke="{SKYLINE_LINE}" stroke-width="5"/>'
    LX0, LW = 720, 360          # kniznica, ku ktorej Bob kraca (len variant "books")
    x = X0
    while x < X1:
        w = r.randint(170, 260)
        h = r.randint(230, 340)
        if variant == "books" and x + w > LX0 - 20 and x < LX0 + LW + 20:
            x = LX0 + LW + 24
            continue
        out += house(x, gb, w, h, r, sw=5)
        x += w + r.randint(0, 26)
    if variant == "books":
        out += library_facade(LX0, gb, LW)
    x = X0 + 120
    while x < X1:
        if not (variant == "books" and LX0 - 40 < x < LX0 + LW + 40):
            out += lamp_post(x, gb + 4, 150, 0.42)
        x += r.randint(300, 420)
    return f'<g id="{p}_far">{out}{clouds_group(p)}{birds()}</g>'


def library_facade(x0, base, w):
    """Budova kniznice na konci ulice: schody, stlpy, kladie, tympanon so znakom knihy, dvere.
    Vrch tympanonu ~ base-510: pri kazdom zabere uvodu/slucky ostava pod slnkom."""
    stone = "#e9e3d5"
    out = "".join(f'<path d="M{x0 - 20 + i * 12},{base + 6 - i * 18} h{w + 40 - i * 24} v-18 h{-(w + 40 - i * 24)} z" '
                  f'fill="{stone}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>' for i in range(3))
    ts = base - 48
    col_h = 300
    dx = x0 + w / 2
    out += (f'<path d="M{x0 + 10},{ts} V{ts - col_h} H{x0 + w - 10} V{ts} Z" fill="#ddd5c3" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M{dx - 42:.0f},{ts} V{ts - 120} Q{dx - 42:.0f},{ts - 172} {dx:.0f},{ts - 172} Q{dx + 42:.0f},{ts - 172} '
            f'{dx + 42:.0f},{ts - 120} V{ts} Z" fill="{WOOD}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="M{dx:.0f},{ts - 172} V{ts}" stroke="{INK}" stroke-width="4"/>')
    n = 6
    for i in range(n):
        cx = x0 + 22 + i * (w - 44) / (n - 1)
        if abs(cx - dx) < 50:
            continue
        out += (f'<path d="M{cx - 15:.0f},{ts} V{ts - col_h} h30 V{ts} Z" fill="{stone}" stroke="{INK}" stroke-width="5"/>'
                f'<path d="M{cx - 21:.0f},{ts - col_h} h42 v-12 h-42 z" fill="{stone}" stroke="{INK}" stroke-width="4"/>'
                f'<path d="M{cx - 21:.0f},{ts} h42 v-10 h-42 z" fill="{stone}" stroke="{INK}" stroke-width="4"/>')
    ent = ts - col_h - 12
    out += (f'<path d="M{x0 - 6},{ent} h{w + 12} v-34 h{-(w + 12)} z" fill="{stone}" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M{x0 - 16},{ent - 34} L{dx:.0f},{ent - 120} L{x0 + w + 16},{ent - 34} Z" fill="{stone}" stroke="{INK}" '
            f'stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="M{dx - 30:.0f},{ent - 58} q15,-12 30,-4 q15,-8 30,4 v-22 q-15,-12 -30,-4 q-15,-8 -30,4 z" fill="{PAPER}" '
            f'stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')
    return out


def backdrop_city(hor, r, variant=""):
    if variant in ("library", "books"):
        return backdrop_library(hor, r)
    b = hor - 30
    pts, x = [], -300
    while x < 1400:
        w = r.randint(90, 170)
        h = r.randint(150, 260)
        pts += [(x, b - h), (x + w / 2, b - h - (50 if r.random() < 0.5 else 0)), (x + w, b - h)]
        x += w
    d = f"M-300,{hor + 60} L-300,{b} " + " ".join(f"L{a:.0f},{c:.0f}" for a, c in pts) + f" L1400,{b} L1400,{hor + 60} Z"
    out = f'<path d="{d}" fill="{SKYLINE}" stroke="{SKYLINE_LINE}" stroke-width="5" stroke-linejoin="round"/>'
    x = -120
    while x < 1250:
        w = r.randint(180, 250)
        h = r.randint(250, 360)
        out += house(x, hor - 10, w, h, r, sw=6)
        x += w + r.randint(0, 20)
    return out


def ground_city(y, x0, x1):
    cob = ""
    for row in range(3):
        yy = y + 22 + row * 30
        off = 0 if row % 2 == 0 else 22
        cob += "".join(f'<path d="M{x},{yy} q11,-9 22,0" stroke="{COBBLE_LINE}" stroke-width="4" fill="none" '
                       f'stroke-linecap="round"/>' for x in range(x0 + off, x1, 46))
    return (f'<path d="M{x0},{y} H{x1} V4200 H{x0} Z" fill="{COBBLE}" stroke="{INK}" stroke-width="9"/>'
            f'<path d="M{x0},{y + 250} H{x1} V4200 H{x0} Z" fill="{COBBLE_SUB}" stroke="none" opacity="0.5"/>{cob}')


def bollard(x, y, h=150):
    """Liatinovy stlpik pri chodniku (~0,9 m) - v priblizeni nikdy nesiahne k slnku ako lampa."""
    return (f'<path d="M{x - 17:.0f},{y + 6:.0f} V{y - h + 26:.0f} Q{x - 17:.0f},{y - h:.0f} {x:.0f},{y - h:.0f} '
            f'Q{x + 17:.0f},{y - h:.0f} {x + 17:.0f},{y - h + 26:.0f} V{y + 6:.0f} Z" fill="#4a4a4a" stroke="{INK}" '
            f'stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x - 21:.0f},{y - h * 0.62:.0f} h42" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>'
            f'<path d="M{x - 9:.0f},{y - h + 20:.0f} v{h * 0.3:.0f}" stroke="#8a8a8a" stroke-width="4" stroke-linecap="round"/>')


def fore_city(x0, x1, gy, r):
    w = x1 - x0
    return bollard(x0 + (0.05 + r.random() * 0.05) * w, gy) + bollard(x1 - (0.05 + r.random() * 0.05) * w, gy)


def walk_city(hy, x0, x1):
    r = random.Random(29)
    out = ""
    for row in range(3):
        off = 0 if row % 2 == 0 else 22
        out += "".join(f'<path d="M{x},{hy(x) + 24 + row * 30:.0f} q11,-9 22,0" stroke="{COBBLE_LINE}" stroke-width="4" '
                       f'fill="none" stroke-linecap="round"/>' for x in range(WX0 + off, x1, 46))
    # liatinove stlpiky pri chodniku (0,9 m pri postave 1,75 m = 215 jednotiek pri s=1,35).
    # Lampa v pravej mierke (3,5 m) by v blizkej vrstve pretala slnko - lampy su vo vzdialenej ulici.
    x = WX0 + 200
    while x < x1:
        if not (0 < x < 240) and not (1350 < x < 2000):
            out += bollard(x, hy(x), 200)
        x += r.randint(420, 560)
    return out


# ---- kniznica (interier: bez slnka a oblakov)
def far_library(p):
    r = random.Random(19)
    X0, X1 = -900, 2400
    b = 1188
    out = f'<path d="M{X0},-700 H{X1} V1460 H{X0} Z" fill="{LIB_WALL}" opacity="0.95"/>'
    x = X0
    k = 0
    while x < X1:
        # nizsie regale: zlaty text konca (y ~540-720 vo vzdialenej vrstve) aj hlava postavy ostanu
        # na pokojnej stene, nie na pestrych chrbtoch knih
        if k % 3 == 2:
            out += arch_window(x + 90, b - 150, 150, 430)
            x += 180
        else:
            w = r.randint(260, 320)
            out += bookshelf(x, b, w, r.randint(400, 430), r, 5)
            x += w + 18
        k += 1
    out += f'<path d="M{X0},{b} H{X1} V1460 H{X0} Z" fill="{WOODF}" stroke="{INK}" stroke-width="6"/>'
    out += (f'<path d="M{X0},-700 H{X1} V210 H{X0} Z" fill="{BEAM}" stroke="{INK}" stroke-width="7"/>'
            + "".join(f'<path d="M{x},210 v24 h60 v-24" fill="{BEAM}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
                      for x in range(X0 + 40, X1, 300)))
    for x in range(X0 + 190, X1, 600):
        out += hanging_lamp(x, 230, 380, 1.0)
    return f'<g id="{p}_far">{out}<g id="{p}_cloud"></g></g>'


def top_library(p):
    r = random.Random(7)
    out = f'<path d="M-40,-80 H1120 V1420 H-40 Z" fill="{LIB_WALL}" opacity="0.95"/>'
    out += (f'<path d="M-40,-100 H1120 V120 H-40 Z" fill="{BEAM}" stroke="{INK}" stroke-width="7"/>'
            + "".join(f'<path d="M{x},120 v22 h56 v-22" fill="{BEAM}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
                      for x in range(10, 1100, 260)))
    out += hanging_lamp(250, 140, 196, 0.9) + hanging_lamp(830, 140, 186, 0.9)
    return out


def backdrop_library(hor, r):
    out = ""
    b = hor - 20
    for x, w in ((-150, 300), (170, 280), (650, 280), (950, 300)):
        out += bookshelf(x, b, w, 760, r, 6)
    out += arch_window(540, b - 190, 170, 560)
    return out


def library_room(p):
    """Exhibit v kniznici: regale a okna na zadnej stene, dreveny parket - rovnaka geometria ako galeria
    (stena konci na y=760, pod nou podlaha), aby sedela vitrina, podstavec aj kamera zaberu."""
    wall_y = 760
    r = random.Random(3)
    out = f'<path d="M-1400,{wall_y} H2400 V-900 H-1400 Z" fill="{LIB_WALL}" stroke="none"/>'
    x, k = -1300, 0
    while x < 2300:
        if k % 4 == 3:
            out += arch_window(x + 110, wall_y - 140, 170, 540)
            x += 220
        else:
            out += bookshelf(x, wall_y, 300, 700, r, 6)
            x += 324
        k += 1
    out += (f'<path d="M-1400,{wall_y} H2400 V2600 H-1400 Z" fill="{WOODF}" stroke="none"/>'
            f'<path d="M-1400,{wall_y} H2400" stroke="{INK}" stroke-width="9" fill="none"/>'
            + "".join(f'<path d="M{-1200 + k * 420},{wall_y} l{-190 - k * 26},760" stroke="{WOODF_LINE}" '
                      f'stroke-width="5" fill="none" opacity="0.55"/>' for k in range(9))
            + "".join(f'<path d="M-1400,{wall_y + h} H2400" stroke="{WOODF_LINE}" stroke-width="4" opacity="0.45"/>'
                      for h in (60, 150, 270, 420)))
    return out


def ground_library(y, x0, x1):
    planks = "".join(f'<path d="M{x0},{y + h} H{x1}" stroke="{WOODF_LINE}" stroke-width="5" opacity="0.6"/>'
                     for h in (46, 104, 176, 262, 364))
    seams = "".join(f'<path d="M{x},{y} l{(x - 540) * 0.45:.0f},700" stroke="{WOODF_LINE}" stroke-width="4" opacity="0.4" '
                    f'fill="none"/>' for x in range(x0 + 60, x1, 260))
    return (f'<path d="M{x0},{y} H{x1} V4200 H{x0} Z" fill="{WOODF}" stroke="{INK}" stroke-width="9"/>{planks}{seams}')


def book_stack(x, y, n=3, s=1.0):
    out, yy = "", y
    for i in range(n):
        w, h = (120 - i * 12) * s, 26 * s
        col = BOOKS[(i * 3 + int(x)) % len(BOOKS)]
        dx = (i % 2) * 8 * s - 4 * s
        out += (f'<path d="M{x - w / 2 + dx:.0f},{yy:.0f} h{w:.0f} v{-h:.0f} h{-w:.0f} z" fill="{col}" stroke="{INK}" '
                f'stroke-width="5" stroke-linejoin="round"/>'
                f'<path d="M{x - w / 2 + dx + 6:.0f},{yy - h * 0.5:.0f} h{w - 12:.0f}" stroke="{PAPER}" stroke-width="4" opacity="0.7"/>')
        yy -= h
    return out


def fore_library(x0, x1, gy, r):
    w = x1 - x0
    return book_stack(x0 + 0.08 * w, gy + 4, 4, 1.0) + book_stack(x1 - 0.09 * w, gy + 4, 3, 0.9)


def walk_library(hy, x0, x1):
    r = random.Random(31)
    y = hy(0)
    out = "".join(f'<path d="M{x0},{y + h} H{x1}" stroke="{WOODF_LINE}" stroke-width="5" opacity="0.6"/>'
                  for h in (40, 92, 160, 248, 350))
    x = WX0 + 300
    while x < x1:
        if not (-80 < x < 320):
            out += book_stack(x, hy(x) + 4, r.randint(2, 4), 1.0)
        x += r.randint(520, 820)
    # pult s otvorenou knihou na konci uvodu (Bob k nemu prichadza)
    tx = 1560
    ty = hy(tx)
    out += (f'<path d="M{tx - 150},{ty + 6} v-156 M{tx + 150},{ty + 6} v-156" stroke="{INK}" stroke-width="10"/>'
            f'<path d="M{tx - 150},{ty + 6} v-156 M{tx + 150},{ty + 6} v-156" stroke="{WOOD}" stroke-width="5"/>'
            f'<path d="M{tx - 190},{ty - 156} h380 v-26 h-380 z" fill="{WOOD}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
            f'<path d="M{tx - 90},{ty - 182} q45,-22 90,-6 q45,-16 90,6 v-8 q-45,-26 -90,-10 q-45,-16 -90,10 z" fill="{PAPER}" '
            f'stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    return out


# ================================================================== DUCHOVIA (hacik uvodu a slucky)
def _ghost_group(p, paths, lead_in, color, dx=-604):
    ids = ["g0", "g1"] + [f"gp{k}" for k in range(7)]
    assert len(paths) == len(ids)
    out = "".join(f'<path id="{p}_{i}" class="pen" pathLength="1" d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" '
                  f'stroke-linecap="round" stroke-linejoin="round"/>' for i, (d, sw) in zip(ids, paths))
    extra = ""
    if lead_in:
        extra = (f'<g transform="translate({dx},0)">'
                 + "".join(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" '
                           f'stroke-linejoin="round"/>' for d, sw in paths) + '</g>')
    return f'<g id="{p}_ghost" opacity="0">{out}{extra}</g>'


def _arch(x, y, w, h):
    return (f"M{x - w / 2:.0f},{y:.0f} V{y - h * 0.62:.0f} Q{x - w / 2:.0f},{y - h:.0f} {x:.0f},{y - h:.0f} "
            f"Q{x + w / 2:.0f},{y - h:.0f} {x + w / 2:.0f},{y - h * 0.62:.0f} V{y:.0f}")


def ghost_cave(p, hy, lead_in=False):
    """Pod dnom jaskyne: schody dolu, klenuta miestnost s troma vychodmi, valcovy kamenny
    uzaver a vetracia sachta - podzemne mesto."""
    cx, cy = 360, 1500
    s0 = hy(cx - 560) + 10
    paths = [
        (f"M{cx - 270},{cy + 150} V{cy - 30} Q{cx - 270},{cy - 150} {cx - 150},{cy - 150} H{cx + 150} "
         f"Q{cx + 270},{cy - 150} {cx + 270},{cy - 30} V{cy + 150}", 9),
        (f"M{cx - 560},{s0:.0f} h60 v{(cy - 40 - s0) / 4:.0f} h60 v{(cy - 40 - s0) / 4:.0f} h60 v{(cy - 40 - s0) / 4:.0f} "
         f"h60 v{(cy - 40 - s0) / 4:.0f} h50", 8),
        (_arch(cx - 150, cy + 150, 70, 130), 8), (_arch(cx, cy + 150, 86, 170), 8), (_arch(cx + 150, cy + 150, 70, 130), 8),
        (ell(cx + 360, cy + 80, 62, 62) + f" M{cx + 348},{cy + 80} h24", 8),
        (f"M{cx + 50},{hy(cx + 50) + 12:.0f} V{cy - 150} M{cx + 104},{hy(cx + 104) + 12:.0f} V{cy - 150}", 7),
        (f"M{cx + 270},{cy + 150} h56 v44 h56 v44 h56 v44", 8),
        (f"M{cx - 270},{cy + 150} H{cx + 270}", 8),
    ]
    return _ghost_group(p, paths, lead_in, "#9d8f76")


def ghost_forest(p, hy, lead_in=False):
    """Pod lesom: korene, ktore obopinaju zasypany kamen z neba (s prasklinami okolo)."""
    cx, cy = 360, 1560
    pts = []
    for k in range(18):
        a = k / 18 * 2 * math.pi
        rr = 1 + 0.13 * math.sin(3 * a + 0.7) + 0.07 * math.cos(5 * a)
        pts.append((cx + 118 * rr * math.cos(a), cy + 92 * rr * math.sin(a)))
    rock = "M" + " L".join(f"{x:.0f},{y:.0f}" for x, y in pts) + " Z"
    rays = " ".join(f"M{cx + 150 * math.cos(a):.0f},{cy + 120 * math.sin(a):.0f} L{cx + 205 * math.cos(a):.0f},{cy + 165 * math.sin(a):.0f}"
                    for a in [k * math.pi / 5 + 0.3 for k in range(10)])
    roots = []
    for dx, bend in ((-330, 40), (-210, -30), (-90, 30), (70, -40), (190, 36), (300, -26), (420, 30)):
        x = cx + dx
        y0 = hy(x) + 16
        ex = cx + dx * 0.45
        ey = cy - 60 - abs(dx) * 0.12
        roots.append((f"M{x:.0f},{y0:.0f} C{x + bend:.0f},{y0 + 90:.0f} {ex - bend:.0f},{ey - 120:.0f} {ex:.0f},{ey:.0f} "
                      f"M{x + bend * 0.5:.0f},{y0 + 60:.0f} l{-bend * 0.9:.0f},46", 7))
    paths = [(rock, 9), (rays, 7)] + roots
    return _ghost_group(p, paths, lead_in, "#948d66")


def ghost_city(p, hy, lead_in=False):
    """Pod dlazbou: klenuta pivnica s arkadami, schody z ulice, truhlica s knihou, mreza."""
    cx, cy = 360, 1520
    s0 = hy(cx - 600) + 12
    vault = (f"M{cx - 330},{cy + 130} V{cy - 20} Q{cx - 330},{cy - 120} {cx - 220},{cy - 120} Q{cx - 110},{cy - 120} {cx - 110},{cy - 20} "
             f"Q{cx - 110},{cy - 120} {cx},{cy - 120} Q{cx + 110},{cy - 120} {cx + 110},{cy - 20} "
             f"Q{cx + 110},{cy - 120} {cx + 220},{cy - 120} Q{cx + 330},{cy - 120} {cx + 330},{cy - 20} V{cy + 130}")
    step = (cy - 60 - s0) / 4
    paths = [
        (vault, 9),
        (f"M{cx - 600},{s0:.0f} h58 v{step:.0f} h58 v{step:.0f} h58 v{step:.0f} h58 v{step:.0f} h40", 8),
        (f"M{cx - 330},{cy + 130} H{cx + 330}", 8),
        (f"M{cx - 64},{cy + 130} v-66 h128 v66 M{cx - 64},{cy + 64} q64,-44 128,0", 8),
        (f"M{cx - 44},{cy + 40} q22,-14 44,-4 q22,-10 44,4", 7),
        (f"M{cx - 110},{cy - 20} V{cy + 130} M{cx + 110},{cy - 20} V{cy + 130}", 7),
        (f"M{cx + 170},{cy + 130} V{cy - 40} M{cx + 220},{cy + 130} V{cy - 70} M{cx + 270},{cy + 130} V{cy - 40}", 7),
        (f"M{cx + 50},{cy + 64} v-26 M{cx + 50},{cy + 34} q-7,-10 0,-18 q7,8 0,18", 6),
        (f"M{cx - 300},{cy + 40} h56 M{cx - 280},{cy + 84} h56 M{cx - 300},{cy + 0} h40", 6),
    ]
    return _ghost_group(p, paths, lead_in, "#9a8f7c")


# ================================================================== dispatch
def far(p, kind, variant=""):
    if kind == "cave":
        return far_cave(p)
    if kind == "forest":
        return far_forest(p, variant)
    if kind == "city":
        return far_city(p, variant)
    return None


def backdrop(kind, hor, r, variant=""):
    if kind == "cave":
        return backdrop_cave(hor, r)
    if kind == "forest":
        return backdrop_forest(hor, r, variant)
    if kind == "city":
        return backdrop_city(hor, r, variant)
    return None


def foreground(kind, x0, x1, gy, r, variant=""):
    if kind == "cave":
        return fore_cave(x0, x1, gy, r)
    if kind == "forest":
        return fore_forest(x0, x1, gy, r, variant)
    if kind == "city":
        return fore_library(x0, x1, gy, r) if variant in ("library", "books") else fore_city(x0, x1, gy, r)
    return None


def walk(kind, hy, x0, x1, variant=""):
    if kind == "cave":
        return walk_cave(hy, x0, x1)
    if kind == "forest":
        return walk_forest(hy, x0, x1, variant)
    if kind == "city":
        return walk_library(hy, x0, x1) if variant == "library" else walk_city(hy, x0, x1)
    return ""


def ghost(p, kind, hy, lead_in=False):
    if kind == "cave":
        return ghost_cave(p, hy, lead_in)
    if kind == "forest":
        return ghost_forest(p, hy, lead_in)
    if kind == "city":
        return ghost_city(p, hy, lead_in)
    return None


def ground(surface, y, x0, x1, variant=""):
    if surface == "cave":
        return ground_cave(y, x0, x1)
    if surface == "forest":
        return ground_forest(y, x0, x1, variant)
    if surface == "city":
        return ground_city(y, x0, x1)
    if surface == "library":
        return ground_library(y, x0, x1)
    return None


def dressing(surface, seed, y, xs, variant=""):
    if surface == "cave":
        return dressing_cave(seed, y, xs)
    if surface == "forest":
        return dressing_forest(seed, y, xs, variant)
    if surface in ("city", "library"):
        return ""
    return None


def top(p, kind, variant=""):
    """Staticke pozadie interieru namiesto oblohy so slnkom (None = bezna obloha)."""
    if kind == "cave":
        return top_cave(p)
    if kind == "city" and variant in ("library", "books"):
        return top_library(p)
    return None
