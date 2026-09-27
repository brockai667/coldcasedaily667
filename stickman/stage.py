# -*- coding: utf-8 -*-
"""Inscenovanie zaberov: kto dominuje, kde je kamera, cim je vyplnena plocha.

Meradlo je rucne Gobekli (B_full): Bob ma ~25-33 % vysky obrazu a vzdy nieco robi,
velke veci presahuju ram, male su pri jeho rukach, pozadie nikdy nie je prazdny papier.

Vsetky rozmery su vo world-jednotkach pri mierke postavy s=1 (Bob = BOB_H vysoky).
Obrazovka je 1080 x 1920; zem v inscenovanych zaberoch lezi na HOR.
"""
import math
import random

import look as _look
import props
import worlds as W
import worlds_ext as _X
from props import BOB_H, DIRT, INK, PAPER, SHADE, STONE, WATER, ell

CW, CH = 1080, 1920
CAP_TOP = 1314          # horna hrana pasma titulkov - nic dolezite pod nou
HOR = 1250              # zem na obrazovke v beznom zabere (tesne nad titulkami)
HOR_SEC = 760           # zem pri priereze (jazero, jama): pod zemou musi byt miesto nad titulkami
SNOW_BLUE = "#c9d8e0"
SNOW_SHADE = "#dde7ec"
ROCK = "#9a9186"


# ------------------------------------------------------------------ kto dominuje a kamera
def dominance(key):
    """'obj' = objekt vyrazne presahuje postavu (pilier, jazero, ruina, lod),
    'bob' = objekt je pri zemi/v rukach a dominuje postava (kost, minca, tabulka)."""
    mode, r = props.SIZE.get(key, ("h", 0.8))
    return "obj" if r >= 1.5 else "bob"


ZMAX = 2.6              # vyssie priblizenie uz zhrubne linie kresby (hrubka ciar rastie so zoomom)
BOB_M = 1.75            # Bob = 1,75 m; namerane hodnoty sa prepocitavaju voci nemu


def to_meters(val, unit):
    """34 + 'cm' -> 0.34 ; 5 + 'm' -> 5 ; 103 + 'ft' -> 31.4 ; inak None."""
    try:
        v = float(val)
    except (TypeError, ValueError):
        return None
    u = (unit or "").strip().lower().rstrip(".")
    f = {"m": 1, "meter": 1, "meters": 1, "metre": 1, "metres": 1, "cm": 0.01, "mm": 0.001, "km": 1000,
         "ft": 0.3048, "foot": 0.3048, "feet": 0.3048, "in": 0.0254, "inch": 0.0254, "inches": 0.0254,
         "yd": 0.9144, "yard": 0.9144, "yards": 0.9144}.get(u)
    return v * f if f else None


def frame_z(key, ow, oh):
    """Zoom kamery (efektivny, bez ZB) tak, aby zaber drzal kontrakt:
    maly predmet -> Bob ~33 % vysky a cim mensi predmet, tym blizsie (max ZMAX);
    velky -> objekt presahuje ram, Bob 17-30 %."""
    mode, _r = props.SIZE.get(key, ("h", 0.8))
    if dominance(key) == "bob":
        return max(0.33 * CH / BOB_H, min(ZMAX, 110.0 / max(1.0, oh)))
    if mode == "h":
        z = 1.06 * HOR / max(1.0, oh)
    else:
        z = 1.12 * CW / max(1.0, ow)
    return max(0.17 * CH / BOB_H, min(0.30 * CH / BOB_H, z))


def world_span(camx, z):
    """Lava a prava hrana obrazu vo world suradniciach."""
    half = CW / 2.0 / z
    return camx - half, camx + half


# ------------------------------------------------------------------ pozadie sveta (screen-space)
def backdrop(p, kind, hor=HOR):
    """Vzdialene pasmo sveta: hory s cepicami, ihlicnany, hreben, duny, more.
    Kresli sa v obrazovkovych suradniciach za kamerou; zaklad lezi presne na ciare zeme,
    ktora je pri GCam vzdy na 960+up. id {p}_bd posuva GCam jemnou paralaxou.
    Varianty terenu a breh/kopec s paletou kresli look.backdrop; drobnosti a hmlu look.backdrop_extra."""
    # stabilny seed (hash() retazcov sa meni s kazdym procesom - pozadie by sa medzi buildmi lisilo)
    r = random.Random(_look._h(f"{p}|{kind}") & 0xFFFF)
    lk = _look.backdrop(kind, hor, r)
    ext = lk if lk is not None else _X.backdrop(kind, hor, r, W.VARIANT)
    extra = _look.backdrop_extra(p, kind, hor)
    if ext is not None:
        return f'<g id="{p}_bd">{ext}{extra}</g>'
    out = ""
    if kind == "snow":
        # dve vrstvy hor: vzdialena svetla, blizsia s ostrymi stitmi a snehovymi cepicami
        far = [(-200, hor - 360), (80, hor - 520), (330, hor - 300), (560, hor - 600), (820, hor - 380),
               (1060, hor - 560), (1300, hor - 320)]
        d = f"M-300,{hor + 40} " + " ".join(f"L{x},{y}" for x, y in far) + f" L1400,{hor + 40} Z"
        out += (f'<path d="{d}" fill="{_look.col("mtn_far", "#e9eef1")}" stroke="{_look.col("mtn_line", "#a7b3bb")}" '
                f'stroke-width="7" stroke-linejoin="round"/>')
        near = [(-160, hor - 140), (120, hor - 330), (300, hor - 190), (470, hor - 390), (700, hor - 170),
                (900, hor - 350), (1150, hor - 150), (1300, hor - 260)]
        d2 = f"M-300,{hor + 40} " + " ".join(f"L{x},{y}" for x, y in near) + f" L1400,{hor + 40} Z"
        out += (f'<path d="{d2}" fill="{_look.col("mtn_near", "#f4f6f7")}" stroke="{_look.col("mtn_line", "#8fa2ae")}" '
                f'stroke-width="8" stroke-linejoin="round"/>')
        # snehove cepice presne podla obrysu hrebena: horne hrany cepice LEZIA na hranach stitu
        # (30 % dlzky svahu), spodny okraj je zubaty - ziadne "dazdniky" ani prekrizene ciary
        for i in range(1, len(near) - 1):
            x, y = near[i]
            if y >= hor - 250:
                continue
            (xl, yl), (xr, yr) = near[i - 1], near[i + 1]
            k = 0.30
            ax, ay = x + (xl - x) * k, y + (yl - y) * k
            bx, by = x + (xr - x) * k, y + (yr - y) * k
            teeth = 4
            zig = ""
            for j in range(1, teeth):
                u = j / teeth
                zx = bx + (ax - bx) * u
                zy = by + (ay - by) * u + (22 if j % 2 else -6)
                zig += f" L{zx:.0f},{zy:.0f}"
            out += (f'<path d="M{ax:.0f},{ay:.0f} L{x},{y} L{bx:.0f},{by:.0f}{zig} Z" fill="{_look.col("snow", PAPER)}" '
                    f'stroke="none"/>'
                    f'<path d="M{bx:.0f},{by:.0f}{zig} L{ax:.0f},{ay:.0f}" fill="none" '
                    f'stroke="{_look.col("cap_line", "#b9c8d2")}" stroke-width="5" stroke-linejoin="round"/>')
        # ihlicnany na horizonte
        for x in (40, 150, 610, 690, 980, 1040):
            h = r.randint(70, 120)
            out += (f'<path d="M{x},{hor + 6} l-{h * 0.30:.0f},0 l{h * 0.30:.0f},-{h * 0.62:.0f} l{h * 0.30:.0f},{h * 0.62:.0f} z '
                    f'M{x},{hor - h * 0.40:.0f} l-{h * 0.24:.0f},0 l{h * 0.24:.0f},-{h * 0.55:.0f} l{h * 0.24:.0f},{h * 0.55:.0f} z" '
                    f'fill="{_look.col("pine", "#4d6b52")}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    elif kind == "desert":
        d = (f"M-300,{hor + 40} L-300,{hor - 90} q220,-130 460,-40 q220,80 440,-60 q220,-120 460,-10 "
             f"L1400,{hor + 40} Z")
        dl = _look.col("dune_line", "#bda57a")
        out += f'<path d="{d}" fill="{_look.col("far", "#efe0b8")}" stroke="{dl}" stroke-width="7" stroke-linejoin="round"/>'
        out += (f'<path d="M-300,{hor + 40} L-300,{hor - 30} q300,-70 640,-10 q300,50 620,-30 L1400,{hor + 40} Z" '
                f'fill="{_look.col("dune", "#e9d6a6")}" stroke="{dl}" stroke-width="7"/>')
    elif kind == "shore":
        out += (f'<path d="M-300,{hor - 120} H1400 V{hor + 40} H-300 Z" fill="#a9d6e8" stroke="none" opacity="0.8"/>'
                f'<path d="M-300,{hor - 120} H1400" stroke="{INK}" stroke-width="7" fill="none"/>'
                + "".join(f'<path d="M{x},{hor - 80 + (i % 3) * 30} q24,-12 48,0 q24,12 48,0" stroke="{PAPER}" '
                          f'stroke-width="6" fill="none" stroke-linecap="round"/>' for i, x in enumerate(range(-200, 1300, 260))))
    else:  # hill
        out += (f'<path d="M-300,{hor - 60} Q60,{hor - 230} 380,{hor - 110} T980,{hor - 150} T1500,{hor - 80}" '
                f'fill="none" stroke="#a39d8f" stroke-width="7" stroke-linecap="round"/>'
                f'<path d="M-300,{hor - 20} Q200,{hor - 110} 560,{hor - 50} T1400,{hor - 60}" '
                f'fill="none" stroke="#b9b2a4" stroke-width="6" stroke-linecap="round"/>')
        for x, y in ((190, hor - 150), (860, hor - 170)):
            out += (f'<path d="M{x},{y + 40} l0,-40 M{x},{y} q-26,-6 -18,-32 q18,-26 40,0 q8,26 -22,32" '
                    f'fill="none" stroke="#a39d8f" stroke-width="6"/>')
    return f'<g id="{p}_bd">{out}{extra}</g>'


# ------------------------------------------------------------------ popredie (world-space)
def foreground(kind, x0, x1, gy, seed=1):
    """Veci v popredi pri okrajoch obrazu - zaveje a kamene v snehu, kamene inde.
    Nikdy nie v strede, kde sa odohrava dej. + jedna nizka drobnost sveta (look.fore_decor)."""
    r = random.Random(seed)
    lk = _look.foreground(kind, x0, x1, gy, r)
    ext = lk if lk is not None else _X.foreground(kind, x0, x1, gy, r, W.VARIANT)
    if ext is not None:
        return ext + _look.fore_decor(kind, x0, x1, gy)
    out = ""
    w = x1 - x0
    if kind == "snow":
        # v snehu len nizke zaveje pri zemi a stopy - ziadne kopy s kamenom ("marshmallow")
        sb, ss = _look.col("line", SNOW_BLUE), _look.col("shade", SNOW_SHADE)
        for side in (0, 1):
            x = x0 + (0.06 + r.random() * 0.10) * w if side == 0 else x1 - (0.06 + r.random() * 0.10) * w
            out += (f'<path d="M{x - 160:.0f},{gy + 34} q80,-22 170,-18 q90,2 150,18" fill="none" '
                    f'stroke="{sb}" stroke-width="7" stroke-linecap="round"/>'
                    f'<path d="M{x - 90:.0f},{gy + 70} q60,-12 130,-8" fill="none" stroke="{ss}" '
                    f'stroke-width="6" stroke-linecap="round"/>')
        tx = x0 + 0.20 * w
        out += "".join(f'<path d="{ell(tx + k * 70, gy + 40 + (k % 2) * 16, 12, 6)}" fill="none" stroke="{sb}" '
                       f'stroke-width="4"/>' for k in range(5))
        return out + _look.fore_decor(kind, x0, x1, gy)
    col = _look.col("sand", "#e9d6a6") if kind == "desert" else _look.tone(STONE)
    for side in (0, 1):
        x = x0 + (0.04 + r.random() * 0.10) * w if side == 0 else x1 - (0.04 + r.random() * 0.10) * w
        out += (f'<path d="M{x - 60:.0f},{gy + 40} l16,-54 l56,-10 l40,30 l6,34 z" fill="{col}" stroke="{INK}" '
                f'stroke-width="6" stroke-linejoin="round"/>')
    return out + _look.fore_decor(kind, x0, x1, gy)


# ------------------------------------------------------------------ zvireny sneh / dazd (screen-space, deterministicky)
RAIN_H = 2240          # perioda padania kvapky (obrazovka + okraje)
RAIN_SLANT = 0.30      # sikmy dazd: posun dolava na jednotku padu


def flurry_svg(p, n=22, rain=False, color="#7c8ea3"):
    """rain=True: tenke sikme ciarky dazda namiesto vlociek (id {p}_rn*)."""
    if rain:
        return "".join(f'<path id="{p}_rn{i}" d="M0,0 l{-RAIN_SLANT * (64 + (i % 4) * 10):.1f},{64 + (i % 4) * 10}" '
                       f'stroke="{color}" stroke-width="{3 + (i % 3)}" stroke-linecap="round" opacity="0.62"/>'
                       for i in range(n))
    return "".join(f'<circle id="{p}_fl{i}" cx="0" cy="0" r="{4 + (i % 3) * 2}" fill="#b8c9d4" opacity="0.75"/>'
                   for i in range(n))


def flurry_js(p, n=22, seed=3, rain=False):
    """Vlocky su cista funkcia casu (CLK.t) - pri seeku po frameoch sa nic nerozsype.
    Dazd: rychlost kazdej kvapky je celociselny nasobok RAIN_H / TM.total, takze v case TOTAL
    su vsetky kvapky presne tam, kde vo frame 0 - neviditelna slucka ostava (aj cez strihy je dazd spojity)."""
    r = random.Random(seed)
    if rain:
        parts = [(r.random() * (1200 + RAIN_SLANT * RAIN_H) - 60, r.random() * RAIN_H, 1300 + r.random() * 700)
                 for _ in range(n)]
        arr = "[" + ",".join(f"[{a:.0f},{b:.0f},{c:.0f}]" for a, b, c in parts) + "]"
        return (f'(function(){{ var P = {arr}, E = [], H = {RAIN_H}; for (var i = 0; i < P.length; i++) E.push($("{p}_rn" + i));\n'
                f'  ctl({{ k: 0 }}, function () {{ var t = CLK.t, T = TM.total; for (var i = 0; i < P.length; i++) {{\n'
                f'    var q = P[i], k = Math.max(1, Math.round(q[2] * T / H)), y = ((q[1] + t * k * H / T) % H + H) % H - 160,\n'
                f'        x = q[0] - {RAIN_SLANT} * (y + 160);\n'
                f'    E[i].setAttribute("transform", "translate(" + x.toFixed(1) + "," + y.toFixed(1) + ")"); }} }});\n'
                f'}})();\n')
    parts = [(r.random() * 1200 - 60, r.random() * 1280, 40 + r.random() * 70, 18 + r.random() * 30,
              r.random() * 6.28) for _ in range(n)]
    arr = "[" + ",".join(f"[{a:.0f},{b:.0f},{c:.1f},{d:.1f},{e:.2f}]" for a, b, c, d, e in parts) + "]"
    return (f'(function(){{ var P = {arr}, E = []; for (var i = 0; i < P.length; i++) E.push($("{p}_fl" + i));\n'
            f'  ctl({{ k: 0 }}, function () {{ var t = CLK.t; for (var i = 0; i < P.length; i++) {{\n'
            f'    var q = P[i], x = ((q[0] + t * q[2]) % 1200 + 1200) % 1200 - 60, y = (q[1] + t * q[3] + 14 * Math.sin(t * 1.3 + q[4])) % 1280;\n'
            f'    E[i].setAttribute("cx", x.toFixed(1)); E[i].setAttribute("cy", y.toFixed(1)); }} }});\n'
            f'}})();\n')


# ------------------------------------------------------------------ kopcek, pod ktorym je predmet (akcia find)
def cover_mound(pid, kind, cx, gy, w):
    """Kopa snehu/hliny nad predmetom. Postava ju odhrnie a predmet sa ukaze pod jej rukami -
    namiesto toho, aby vyrastal zo zeme s visiacou ciarou."""
    if kind == "snow":
        # naviaty zavej: dlhy mierny nabeh a strmsi zlom, nizky - nie okruhla "marshmallow" kopa
        h = w * 0.34
        sf, sl, ss = _look.mound_colors(kind, (PAPER, SNOW_BLUE, SNOW_SHADE))
        return (f'<g id="{pid}"><path d="M{cx - w / 2:.0f},{gy + 6} q{w * 0.30:.0f},-{h * 0.55:.0f} {w * 0.58:.0f},-{h * 0.95:.0f} '
                f'q{w * 0.17:.0f},-{h * 0.08:.0f} {w * 0.27:.0f},{h * 0.03:.0f} q{w * 0.07:.0f},{h * 0.42:.0f} {w * 0.15:.0f},{h * 0.98:.0f} z" '
                f'fill="{sf}" stroke="{sl}" stroke-width="7" stroke-linejoin="round"/>'
                f'<path d="M{cx - w * 0.30:.0f},{gy - h * 0.18:.0f} q{w * 0.22:.0f},-{h * 0.36:.0f} {w * 0.44:.0f},-{h * 0.62:.0f}" '
                f'stroke="{ss}" stroke-width="7" fill="none" stroke-linecap="round"/></g>')
    h = w * 0.42
    if kind in ("desert", "shore"):
        fill, line, shade = _look.mound_colors(kind, ("#e9d6a6", "#bda57a", "#d6c193"))
    else:
        fill, line, shade = _look.mound_colors(kind, (DIRT, INK, "#b89e74"))
    return (f'<g id="{pid}"><path d="M{cx - w / 2:.0f},{gy + 6} q{w * 0.08:.0f},-{h * 0.9:.0f} {w * 0.36:.0f},-{h:.0f} '
            f'q{w * 0.30:.0f},-{h * 0.12:.0f} {w * 0.50:.0f},{h * 0.30:.0f} q{w * 0.12:.0f},{h * 0.34:.0f} {w * 0.14:.0f},{h * 0.70:.0f} z" '
            f'fill="{fill}" stroke="{line}" stroke-width="8" stroke-linejoin="round"/>'
            f'<path d="M{cx - w * 0.22:.0f},{gy - h * 0.55:.0f} q{w * 0.16:.0f},-{h * 0.18:.0f} {w * 0.34:.0f},-{h * 0.04:.0f}" '
            f'stroke="{shade}" stroke-width="9" fill="none" stroke-linecap="round"/></g>')


def chunks(pid, kind, n=6):
    """Hrudky snehu/hliny, ktore odletia pri odhrnuti."""
    col = PAPER if kind == "snow" else ("#e9d6a6" if kind in ("desert", "shore") else DIRT)
    line = SNOW_BLUE if kind == "snow" else INK
    col, line = _look.mound_colors(kind, (col, line, col))[:2]
    if kind != "snow":
        line = INK
    return "".join(f'<g id="{pid}{i}" opacity="0"><path d="M-14,4 q-4,-16 10,-18 q18,-4 20,12 q-2,14 -16,14 q-10,2 -14,-8 z" '
                   f'fill="{col}" stroke="{line}" stroke-width="5"/></g>' for i in range(n))


# ------------------------------------------------------------------ prierez jazerom
def lake_bottom(x0, x1, gy, depth):
    """Funkcia x -> vyska dna kotliny (presne podla Bezierovej krivky brehu)."""
    w = x1 - x0
    cxm = (x0 + x1) / 2
    P0, C1, C2, P3 = (x0 - 60, gy), (x0 + w * 0.10, gy + depth * 0.9), (x0 + w * 0.30, gy + depth), (cxm, gy + depth)

    def bottom_y(x):
        xl = x if x <= cxm else 2 * cxm - x
        if xl <= P0[0]:
            return gy
        lo, hi = 0.0, 1.0
        for _ in range(40):
            t = (lo + hi) / 2
            bx_ = ((1 - t) ** 3 * P0[0] + 3 * (1 - t) ** 2 * t * C1[0] + 3 * (1 - t) * t * t * C2[0] + t ** 3 * P3[0])
            lo, hi = (t, hi) if bx_ < xl else (lo, t)
        t = (lo + hi) / 2
        return (1 - t) ** 3 * P0[1] + 3 * (1 - t) ** 2 * t * C1[1] + 3 * (1 - t) * t * t * C2[1] + t ** 3 * P3[1]
    return bottom_y


def lake_section(p, x0, x1, gy, depth, frozen=True, bones=5, seed=4):
    """Jazero v reze: brehy, voda do hlbky, na hladine lad, na dne kostry.
    Vrati (svg_pod, svg_nad): pod = voda a kosti, nad = lad, praskliny, zakal (animuju sa)."""
    r = random.Random(seed)
    w = x1 - x0
    cxm = (x0 + x1) / 2
    basin = (f"M{x0 - 60:.0f},{gy} C{x0 + w * 0.10:.0f},{gy + depth * 0.9:.0f} {x0 + w * 0.30:.0f},{gy + depth:.0f} "
             f"{cxm:.0f},{gy + depth:.0f} C{x1 - w * 0.30:.0f},{gy + depth:.0f} {x1 - w * 0.10:.0f},{gy + depth * 0.9:.0f} "
             f"{x1 + 60:.0f},{gy}")
    bottom_y = lake_bottom(x0, x1, gy, depth)

    # rez zeminou cez celu sirku: tenka vrstva snehu/zeme hore, pod nou horniny -
    # aby bolo jasne, ze sa divame "cez zem" do kotliny
    # rez zeminou je len uzky pas okolo kotliny (zvlneny spodok), pod nim pokracuje sneh -
    # hneda nesmie zabrat vacsinu obrazu
    band = depth + 90
    wave = " ".join(f"Q{2800 - k * 230 - 115:.0f},{gy + band + (16 if k % 2 else -12)} {2800 - (k + 1) * 230:.0f},{gy + band}"
                    for k in range(20))
    rim = (f'<path d="M-1800,{gy + 34} H2800 V{gy + band} {wave} Z" fill="#b7aa98" stroke="none"/>'
           f'<path d="M-1800,{gy + 34} H2800" stroke="#8e8272" stroke-width="6" fill="none"/>'
           f'<path d="M2800,{gy + band} {wave}" stroke="#8e8272" stroke-width="6" fill="none"/>'
           + "".join(f'<path d="M{-1700 + k * 190:.0f},{gy + 60 + (k % 3) * 22:.0f} l30,-10 l24,14 l20,-6" '
                     f'stroke="#8e8272" stroke-width="6" fill="none" stroke-linecap="round"/>' for k in range(24)))
    water = f'<path d="{basin} Z" fill="{WATER}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
    # kostry na dne (presne na krivke dna, mierne natocene)
    bn = ""
    for i in range(bones):
        u = (i + 0.5) / bones
        bx = x0 + w * (0.14 + 0.72 * u) + r.uniform(-24, 24)
        by = bottom_y(bx) - 6
        if i % 2 == 0:
            s = 0.26
            bn += (f'<g transform="translate({bx:.0f},{by:.0f}) rotate({r.uniform(-18, 18):.0f}) scale({s})">'
                   f'{props.PROPS["skull"]("x")[0]}</g>')
        else:
            s = 0.24
            bn += (f'<g transform="translate({bx:.0f},{by + 6:.0f}) rotate({r.uniform(-10, 10):.0f}) scale({s})">'
                   f'{props.PROPS["bones"]("x")[0]}</g>')
    under = f'<g id="{p}_lk">{rim}{water}<g id="{p}_lkb" opacity="0.92">{bn}</g></g>'
    # zakal (voda pod ladom je spociatku kalna, kostry nevidno) + lad + praskliny
    murk = (f'<path id="{p}_murk" d="{basin} Z" fill="#6f95a8" stroke="none" opacity="0.0"/>')
    ice = ""
    if frozen:
        ice = (f'<g id="{p}_ice"><path d="M{x0 - 30:.0f},{gy - 4} H{x1 + 30:.0f} L{x1 - 10:.0f},{gy + 30} H{x0 + 10:.0f} Z" '
               f'fill="#e3f0f6" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
               f'<path d="M{x0 + 40:.0f},{gy + 8} H{x1 - 60:.0f}" stroke="{PAPER}" stroke-width="10" '
               f'stroke-linecap="round" opacity="0.8"/></g>')
    cracks = ""
    for k in range(4):
        sx = x0 + w * (0.18 + 0.2 * k)
        cracks += (f'<path id="{p}_ck{k}" class="pen" pathLength="1" d="M{sx:.0f},{gy - 2} l{r.uniform(20, 40):.0f},14 '
                   f'l{r.uniform(-30, -10):.0f},10 l{r.uniform(24, 44):.0f},8" fill="none" stroke="#6f95a8" '
                   f'stroke-width="6" stroke-linecap="round"/>')
    over = f'{murk}{ice}{cracks}'
    return under, over


def water_front_section(x0, x1, gy, depth):
    """Nic - v reze je voda uz kreslena v kotline (placeholder pre symetriu API)."""
    return ""


# ------------------------------------------------------------------ pomocne cislo z textu ("three deep")
_NUMW = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
         "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}


def depth_from_text(text):
    """'forty meters wide, three deep' -> 3.0 ; '3 m deep' -> 3.0 ; inak None."""
    import re
    low = text.lower()
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|meters|metres|ft|feet)?\s*(?:deep|depth)", low)
    if m:
        return float(m.group(1))
    m = re.search(r"\b(" + "|".join(_NUMW) + r")\b\s*(?:m|meters|metres|ft|feet)?\s*(?:deep|depth)", low)
    if m:
        return float(_NUMW[m.group(1)])
    return None
