# -*- coding: utf-8 -*-
"""Bezne predmety z pribehov (posteľ, hodiny, stolicka, stol, jedlo, lampa, plast, list, stopy,
lano, clun, svieca, flasa, cizma, kluc, radio, rebrik, stan, okno, krb).

Rovnaka stavebnica ako props.py: cierna linka INK, papierove vyplne, dotyk so zemou y=0,
centrovane na x=0, vracia (svg, sirka, vyska) pri mierke 1. Plochy predmet lezi NA zemi
(stopy, list, kluc) - kresli sa pohladom zhora na rovinu zeme, trochu pod y=0.
Registruje sa do props.PROPS / props.SIZE (pravdiva velkost voci Bobovi 1,75 m)."""
import math

import props as P
from props import BRONZE, DIRT2, INK, METAL, PAPER, STONE, SUN, WATER, WOOD

WOOD_D = "#5c3d22"
WOOD_L = "#b98a55"
IRON = "#7d8489"
OIL = "#e3b33c"          # nepremokavy plast (oilskin)
OIL_D = "#c9982a"
GLASS = "#dcebf0"


def _r(svg, w, h):
    return svg, w, h


def _plank(x0, y0, x1, y1, w, fill=WOOD, sw=6):
    """Hrubsia drevena lista/noha medzi dvoma bodmi (obrys + drevo)."""
    return (f'<path d="M{x0:.1f},{y0:.1f} L{x1:.1f},{y1:.1f}" stroke="{INK}" stroke-width="{w + sw:.1f}" stroke-linecap="round"/>'
            f'<path d="M{x0:.1f},{y0:.1f} L{x1:.1f},{y1:.1f}" stroke="{fill}" stroke-width="{w:.1f}" stroke-linecap="round"/>')


# ------------------------------------------------------------------ postel
def p_bed(pid=""):
    """Stara drevena postel z boku: vyssie celo pri hlave, nizsie pri nohach, matrac,
    vankus a ROZHADZANA deka (neustlana), cip visi cez bok."""
    head = (f'<path d="M-300,4 V-300 Q-300,-322 -278,-322 H-252 Q-230,-322 -230,-300 V4" fill="{WOOD}" stroke="{INK}" '
            f'stroke-width="9" stroke-linejoin="round"/>'
            f'<path d="M-282,-272 H-248 M-282,-232 H-248" stroke="{WOOD_D}" stroke-width="5"/>')
    rail = f'<path d="M-232,-100 H242 V-68 H-232 Z" fill="{WOOD}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
    mattress = (f'<path d="M-232,-100 V-150 Q-232,-164 -218,-164 H228 Q242,-164 242,-150 V-100 Z" fill="{PAPER}" '
                f'stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>')
    pillow = (f'<path d="M-224,-162 Q-230,-208 -190,-210 H-118 Q-84,-206 -92,-168 Q-150,-150 -224,-162 Z" fill="#ffffff" '
              f'stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
              f'<path d="M-176,-196 q20,8 44,0" stroke="#c9c2b0" stroke-width="4" fill="none" stroke-linecap="round"/>')
    blanket = (f'<path d="M-78,-160 Q-50,-200 -8,-182 Q34,-214 88,-188 Q140,-210 192,-180 Q230,-172 240,-150 '
               f'L252,-64 Q210,-44 160,-70 Q120,-54 86,-96 L-44,-98 Q-66,-122 -78,-160 Z" fill="#8fa7b3" stroke="{INK}" '
               f'stroke-width="8" stroke-linejoin="round"/>'
               f'<path d="M4,-178 q22,22 10,54 M118,-192 q18,26 8,60 M196,-172 q12,30 -4,62" stroke="#5f7a87" stroke-width="5" '
               f'fill="none" stroke-linecap="round"/>')
    foot = (f'<path d="M244,4 V-212 Q244,-230 262,-230 H282 Q300,-230 300,-212 V4" fill="{WOOD}" stroke="{INK}" '
            f'stroke-width="9" stroke-linejoin="round"/>')
    return _r(head + rail + mattress + pillow + blanket + foot, 600, 322)


# ------------------------------------------------------------------ hodiny
def p_clock(pid=""):
    """Krbove hodiny: dreveny korpus s oblúkom, biely cifernik s ciarkami, rucicky zastavene
    (7:40), okienko s kyvadlom, podstavec."""
    case = (f'<path d="M-100,-22 V-160 Q-100,-272 0,-272 Q100,-272 100,-160 V-22 Z" fill="{WOOD}" stroke="{INK}" '
            f'stroke-width="9" stroke-linejoin="round"/>'
            f'<path d="M-116,4 H116 V-24 H-116 Z" fill="{WOOD_D}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>')
    cy, r = -168, 70
    face = f'<circle cx="0" cy="{cy}" r="{r}" fill="{PAPER}" stroke="{INK}" stroke-width="8"/>'
    ticks = "".join(f'<path d="M{math.cos(a) * 55:.1f},{cy + math.sin(a) * 55:.1f} L{math.cos(a) * 63:.1f},{cy + math.sin(a) * 63:.1f}"/>'
                    for a in [k * math.pi / 6 for k in range(12)])
    ha, ma = math.radians(-90 + 7 * 30 + 20), math.radians(-90 + 40 * 6)
    # rucicky musia mat vlastny stroke - bez neho boli neviditelne (insert „STOPPED" mal cifernik bez rucicok)
    hands = (f'<path d="M0,{cy} L{math.cos(ha) * 34:.1f},{cy + math.sin(ha) * 34:.1f}" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>'
             f'<path d="M0,{cy} L{math.cos(ma) * 52:.1f},{cy + math.sin(ma) * 52:.1f}" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
             f'<circle cx="0" cy="{cy}" r="7" fill="{INK}" stroke="none"/>')
    win = (f'<path d="M-34,-36 V-70 Q-34,-88 0,-88 Q34,-88 34,-70 V-36 Z" fill="{GLASS}" stroke="{INK}" stroke-width="6" '
           f'stroke-linejoin="round"/>'
           f'<path d="M0,-88 V-56" stroke="{INK}" stroke-width="4"/><circle cx="0" cy="-52" r="10" fill="{BRONZE}" stroke="{INK}" '
           f'stroke-width="4"/>')
    return _r(case + face + f'<g stroke="{INK}" stroke-width="5" stroke-linecap="round">{ticks}</g>' + hands + win, 232, 276)


# ------------------------------------------------------------------ stolicka (aj prevrhnuta)
def _chair_body():
    far = (_plank(-40, -16, -52, -392, 12, WOOD_L) + _plank(84, -16, 84, -192, 12, WOOD_L))
    seat = (f'<path d="M-68,-182 L74,-182 L96,-198 L-46,-198 Z" fill="{WOOD_L}" stroke="{INK}" stroke-width="7" '
            f'stroke-linejoin="round"/>'
            f'<path d="M-68,-182 V-166 H74 V-182" fill="{WOOD}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>')
    slats = "".join(_plank(-66 + (y + 380) * 0.02, y, -48 + (y + 380) * 0.02, y - 12, 12, WOOD_L)
                    for y in (-252, -300, -348))
    near = (_plank(-60, 0, -72, -380, 13) + _plank(62, 0, 62, -168, 13)
            + _plank(-60, -70, 62, -70, 8))
    return far + slats + seat + near


def p_chair(pid=""):
    """Drevena stolicka s rebrikovym operadlom (mierne zo strany): operadlo, sedak, styri nohy."""
    return _r(_chair_body(), 180, 400)


def p_chair_toppled(pid=""):
    """Prevrhnuta stolicka: lezi na operadle, nohy trcia do strany."""
    return _r(f'<g transform="translate(190,-84) rotate(-90)">{_chair_body()}</g>', 420, 190)


# ------------------------------------------------------------------ stol
def p_table(pid=""):
    """Dreveny stol z boku: doska, luby so zasuvkou, dve predne a dve zadne nohy."""
    far = _plank(-178, -8, -178, -196, 16, WOOD_L) + _plank(194, -8, 194, -196, 16, WOOD_L)
    near = _plank(-196, 0, -196, -190, 18) + _plank(176, 0, 176, -190, 18)
    apron = (f'<path d="M-212,-216 H212 V-184 H-212 Z" fill="{WOOD}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
             f'<path d="M-40,-210 h80 v-2 M-40,-210 v22 h80 v-22" fill="none" stroke="{WOOD_D}" stroke-width="4"/>'
             f'<circle cx="0" cy="-199" r="4" fill="{INK}" stroke="none"/>')
    top = (f'<path d="M-232,-240 H232 V-214 H-232 Z" fill="{WOOD_L}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
           f'<path d="M-200,-232 h120 M40,-230 h140" stroke="{WOOD_D}" stroke-width="3" opacity="0.6"/>')
    return _r(far + near + apron + top, 464, 240)


# ------------------------------------------------------------------ jedlo
def p_meal(pid=""):
    """Nedojedene jedlo: plytky tanier (z boku) s rybou a zemiakmi, smaltovany hrncek, vidlicka."""
    plate = (f'<path d="M-160,-6 Q-40,24 80,-6 L64,-22 Q-40,-4 -144,-22 Z" fill="#ffffff" stroke="{INK}" stroke-width="6" '
             f'stroke-linejoin="round"/>'
             f'<path d="M-146,-22 Q-40,-40 64,-22" fill="none" stroke="#c9c2b0" stroke-width="4"/>')
    fish = (f'<path d="M-118,-30 Q-80,-62 -30,-44 L-8,-58 L-10,-28 L-30,-40 Q-84,-12 -118,-30 Z" fill="#d9a15f" stroke="{INK}" '
            f'stroke-width="5" stroke-linejoin="round"/>'
            f'<circle cx="-100" cy="-36" r="3" fill="{INK}" stroke="none"/>')
    pot = "".join(f'<path d="{P.ell(x, y, rx, ry)}" fill="#e7c77c" stroke="{INK}" stroke-width="4"/>'
                  for x, y, rx, ry in ((18, -36, 16, 11), (44, -32, 14, 10)))
    fork = f'<path d="M-170,-30 l40,-38 M-136,-72 l10,-10 M-130,-66 l10,-10" stroke="{METAL}" stroke-width="5" stroke-linecap="round"/>'
    mug = (f'<path d="M100,4 V-96 H160 V4 Z" fill="#6f8fa8" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
           f'<path d="M100,-88 H160" stroke="#ffffff" stroke-width="6"/>'
           f'<path d="M160,-74 q28,0 28,26 q0,24 -28,22" fill="none" stroke="{INK}" stroke-width="8"/>'
           f'<path d="M160,-74 q28,0 28,26 q0,24 -28,22" fill="none" stroke="#6f8fa8" stroke-width="3"/>')
    return _r(plate + fish + pot + fork + mug, 360, 104)


# ------------------------------------------------------------------ lampa
def p_lantern(pid=""):
    """Petrolejova (burkova) lampa: nadrz, sklenena banka s plamenom, drotene ochranne tyce, ucho."""
    tank = (f'<path d="M-70,4 L-58,-44 Q0,-60 58,-44 L70,4 Z" fill="#b5463a" stroke="{INK}" stroke-width="8" '
            f'stroke-linejoin="round"/>')
    globe = (f'<path d="M-30,-52 Q-66,-112 -36,-176 L-24,-196 H24 L36,-176 Q66,-112 30,-52 Z" fill="{GLASS}" stroke="{INK}" '
             f'stroke-width="7" stroke-linejoin="round"/>')
    flame = (f'<path d="M0,-150 q15,26 7,44 q-7,8 -14,0 q-8,-18 7,-44 z" fill="#f39c34" stroke="{INK}" stroke-width="3"/>'
             f'<path d="M0,-132 q6,12 2,20 q-4,4 -6,0 q-2,-10 4,-20 z" fill="#ffd45a"/>')
    guards = f'<path d="M-46,-50 Q-80,-116 -42,-200 M46,-50 Q80,-116 42,-200" fill="none" stroke="{INK}" stroke-width="6"/>'
    cap = (f'<path d="M-50,-196 H50 L36,-236 H-36 Z" fill="#b5463a" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
           f'<path d="M-40,-230 Q0,-310 40,-230" fill="none" stroke="{INK}" stroke-width="7"/>')
    return _r(tank + globe + flame + guards + cap, 150, 290)


# ------------------------------------------------------------------ plast na vesiaku
def p_coat(pid=""):
    """Nepremokavy zlty plast (oilskin) na stojacom vesiaku, na druhom hacku juhozapadnik."""
    stand = (_plank(0, -8, 0, -566, 14)
             + _plank(0, -40, -70, 0, 11) + _plank(0, -40, 70, 0, 11) + _plank(0, -40, 16, 6, 9, WOOD_L)
             + f'<path d="M0,-548 q-26,-4 -40,18 M0,-548 q26,-4 40,18" fill="none" stroke="{INK}" stroke-width="7" '
               f'stroke-linecap="round"/>'
             + f'<circle cx="0" cy="-570" r="11" fill="{WOOD}" stroke="{INK}" stroke-width="6"/>')
    coat = (f'<path d="M-40,-528 Q-58,-522 -78,-500 Q-96,-470 -96,-420 L-104,-160 Q-60,-146 -20,-152 Q10,-146 34,-154 '
            f'L28,-420 Q30,-480 10,-510 Q-10,-530 -40,-528 Z" fill="{OIL}" stroke="{INK}" stroke-width="8" '
            f'stroke-linejoin="round"/>'
            f'<path d="M-78,-496 L-44,-470 L-26,-506" fill="none" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M-40,-470 V-156" stroke="{OIL_D}" stroke-width="5"/>'
            f'<path d="M-90,-420 Q-100,-330 -94,-250 M18,-420 Q24,-330 20,-260" fill="none" stroke="{OIL_D}" stroke-width="7" '
            f'stroke-linecap="round"/>'
            + "".join(f'<circle cx="-30" cy="{y}" r="5" fill="{INK}" stroke="none"/>' for y in (-440, -380, -320, -260)))
    hat = (f'<path d="M26,-514 Q30,-560 64,-560 Q94,-558 96,-518 Z" fill="{OIL}" stroke="{INK}" stroke-width="7" '
           f'stroke-linejoin="round"/>'
           f'<path d="M14,-516 Q60,-526 120,-500 Q70,-494 14,-516 Z" fill="{OIL}" stroke="{INK}" stroke-width="7" '
           f'stroke-linejoin="round"/>')
    return _r(stand + coat + hat, 240, 582)


# ------------------------------------------------------------------ list
def p_letter(pid=""):
    """List papiera lezi na zemi (pohlad zhora na rovinu zeme): riadky pisma, podpis, prehnuty roh."""
    sheet = (f'<path d="M-104,8 L84,8 L112,-58 L-72,-58 Z" fill="{PAPER}" stroke="{INK}" stroke-width="6" '
             f'stroke-linejoin="round"/>'
             f'<path d="M84,8 L112,-58 L88,-46 Z" fill="#e2d8bd" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')
    lines = "".join(f'<path d="M{-78 + i * 5.6:.0f},{-44 + i * 10} q12,-6 24,0 q12,6 24,0 q12,-6 24,0 q12,6 24,0 q10,-5 20,0" '
                    f'fill="none" stroke="#3d4a6b" stroke-width="3" stroke-linecap="round"/>' for i in range(5))
    sig = f'<path d="M14,2 q10,-14 20,-2 q8,8 18,-6" fill="none" stroke="#3d4a6b" stroke-width="3" stroke-linecap="round"/>'
    return _r(sheet + lines + sig, 224, 68)


# ------------------------------------------------------------------ stopy
def p_footprints(pid=""):
    """Stopy na zemi (v snehu/piesku): striedave odtlacky podrazky, vzdialuju sa sikmo do dialky."""
    out = ""
    for i in range(8):
        x = -276 + i * 78
        y = 44 - i * 4 + (8 if i % 2 else -8)
        s = 1.0 - i * 0.05
        rot = -8 + (i % 2) * 6
        out += (f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot}) scale({s:.2f})">'
                f'<path d="{P.ell(8, 0, 20, 9)}" fill="{INK}" fill-opacity="0.16" stroke="{INK}" stroke-opacity="0.55" '
                f'stroke-width="3"/>'
                f'<path d="{P.ell(-22, 0, 11, 7)}" fill="{INK}" fill-opacity="0.16" stroke="{INK}" stroke-opacity="0.55" '
                f'stroke-width="3"/></g>')
    return _r(out, 600, 60)


# ------------------------------------------------------------------ lano
def p_rope(pid=""):
    """Stocene lodne lano na zemi: styri kotuce nad sebou, volny koniec vpravo."""
    col, dk = "#c9a36a", "#8a6e45"
    out = ""
    for i in range(4):
        rx, ry, y = 112 - i * 8, 24, -8 - i * 17
        d = P.ell(0, y, rx, ry)
        out += (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="22"/>'
                f'<path d="{d}" fill="none" stroke="{col}" stroke-width="13"/>'
                f'<path d="{d}" fill="none" stroke="{dk}" stroke-width="3" stroke-dasharray="7 9"/>')
    end = "M100,-6 Q150,10 210,4"
    out += (f'<path d="{end}" fill="none" stroke="{INK}" stroke-width="20" stroke-linecap="round"/>'
            f'<path d="{end}" fill="none" stroke="{col}" stroke-width="12" stroke-linecap="round"/>')
    return _r(out, 330, 96)


# ------------------------------------------------------------------ clun
def p_boat(pid=""):
    """Maly drevený veslovy clun na brehu: trup s doskami, lem, stavka, dve vesla cez okraj."""
    hull = (f'<path d="M-322,-172 Q-160,-126 0,-126 Q170,-126 326,-186 Q310,-96 250,-48 Q170,4 0,6 Q-170,4 -250,-44 '
            f'Q-306,-100 -322,-172 Z" fill="{WOOD_L}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>')
    planks = "".join(f'<path d="M{-300 + k * 12},{-146 + k * 26} Q0,{-104 + k * 30} {300 - k * 14},{-156 + k * 28}" fill="none" '
                     f'stroke="{WOOD_D}" stroke-width="4" opacity="0.7"/>' for k in range(1, 5))
    gunwale = (f'<path d="M-322,-172 Q-160,-126 0,-126 Q170,-126 326,-186" fill="none" stroke="{INK}" stroke-width="16" '
               f'stroke-linecap="round"/>'
               f'<path d="M-322,-172 Q-160,-126 0,-126 Q170,-126 326,-186" fill="none" stroke="{WOOD}" stroke-width="8" '
               f'stroke-linecap="round"/>')
    oars = (_plank(-230, -250, 190, -108, 9, WOOD) + f'<path d="M150,-122 l84,-8 l-4,34 l-84,6 z" fill="{WOOD}" stroke="{INK}" '
            f'stroke-width="5" stroke-linejoin="round"/>')
    return _r(hull + planks + gunwale + oars, 650, 256)


# ------------------------------------------------------------------ svieca
def p_candle(pid=""):
    """Svieca v mosadznom svietniku s uchom: kvapky vosku, knot, maly plamen."""
    dish = (f'<path d="M-62,-6 Q0,12 62,-6 L56,-20 Q0,-6 -56,-20 Z" fill="{BRONZE}" stroke="{INK}" stroke-width="6" '
            f'stroke-linejoin="round"/>'
            f'<path d="M58,-14 q30,-4 28,-26 q-2,-18 -22,-14" fill="none" stroke="{INK}" stroke-width="7"/>'
            f'<path d="M-18,-20 h36 v-14 h-36 z" fill="{BRONZE}" stroke="{INK}" stroke-width="5"/>')
    wax = (f'<path d="M-16,-32 V-166 Q-10,-174 -4,-166 Q2,-176 8,-166 Q12,-172 16,-166 V-32 Z" fill="#f3ecd9" stroke="{INK}" '
           f'stroke-width="6" stroke-linejoin="round"/>'
           f'<path d="M-10,-166 v24 q0,6 4,0 v-18 M10,-166 v36 q0,6 4,0 v-30" fill="#f3ecd9" stroke="{INK}" stroke-width="3"/>')
    flame = (f'<path d="M0,-176 V-190" stroke="{INK}" stroke-width="4"/>'
             f'<path d="M0,-232 q16,24 8,40 q-8,8 -16,0 q-8,-16 8,-40 z" fill="#f39c34" stroke="{INK}" stroke-width="3"/>'
             f'<path d="M0,-214 q6,10 3,18 q-3,4 -6,0 q-3,-8 3,-18 z" fill="#ffd45a"/>')
    return _r(dish + wax + flame, 150, 234)


# ------------------------------------------------------------------ flasa
def p_bottle(pid=""):
    """Zelena sklenena flasa s korkom a zvinutym papierom vnutri."""
    b = (f'<path d="M-40,2 V-172 Q-40,-208 -18,-228 V-270 H18 V-228 Q40,-208 40,-172 V2 Z" fill="#8fb89a" stroke="{INK}" '
         f'stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M-24,-200 V-40" stroke="#ffffff" stroke-width="6" stroke-linecap="round" opacity="0.7"/>'
         f'<path d="M-16,-270 h32 v-24 h-32 z" fill="{WOOD}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
         f'<path d="M-12,-150 h24 v70 h-24 z" fill="{PAPER}" stroke="{INK}" stroke-width="4" opacity="0.85"/>'
         f'<path d="M-12,-150 q-8,4 0,8 M12,-150 q8,4 0,8" fill="none" stroke="{INK}" stroke-width="3"/>')
    return _r(b, 92, 296)


# ------------------------------------------------------------------ cizma
def p_boot(pid=""):
    """Gumena cizma z boku: holenka, pata, spicka dopredu, hruba podrazka."""
    b = (f'<path d="M-72,-240 H26 V-96 Q84,-86 118,-58 Q136,-40 130,-12 H-72 Z" fill="#3f4a4f" stroke="{INK}" '
         f'stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M-78,-240 H32" stroke="{INK}" stroke-width="14" stroke-linecap="round"/>'
         f'<path d="M-50,-220 V-40" stroke="#6d7a80" stroke-width="7" stroke-linecap="round" opacity="0.8"/>'
         f'<path d="M-76,-12 H134 V4 H-76 Z" fill="#2b2724" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>')
    return _r(b, 214, 244)


# ------------------------------------------------------------------ kluc
def p_key(pid=""):
    """Stary kovany kluc lezi na zemi (pohlad zhora): ucko, driek, zuby."""
    b = (f'<path d="{P.ell(-78, -26, 36, 26)}" fill="none" stroke="{INK}" stroke-width="16"/>'
         f'<path d="{P.ell(-78, -26, 36, 26)}" fill="none" stroke="{IRON}" stroke-width="8"/>'
         f'<path d="M-42,-24 H86" stroke="{INK}" stroke-width="16" stroke-linecap="round"/>'
         f'<path d="M-42,-24 H86" stroke="{IRON}" stroke-width="8" stroke-linecap="round"/>'
         f'<path d="M58,-22 v24 h12 v-12 h10 v12 h12 v-24" fill="{IRON}" stroke="{INK}" stroke-width="6" '
         f'stroke-linejoin="round"/>')
    return _r(b, 250, 60)


# ------------------------------------------------------------------ radio
def p_radio(pid=""):
    """Stare lampove radio: dreveny korpus s oblúkom, latkova mriezka, stupnica, gombiky."""
    b = (f'<path d="M-124,4 V-190 Q-124,-266 0,-266 Q124,-266 124,-190 V4 Z" fill="{WOOD}" stroke="{INK}" stroke-width="9" '
         f'stroke-linejoin="round"/>'
         f'<path d="M-84,-104 V-182 Q-84,-230 0,-230 Q84,-230 84,-182 V-104 Z" fill="#d8c09a" stroke="{INK}" stroke-width="6" '
         f'stroke-linejoin="round"/>'
         + "".join(f'<path d="M{x},-110 V{-180 - (40 - abs(x)) * 0.6:.0f}" stroke="#a88a5e" stroke-width="4"/>' for x in range(-64, 70, 16))
         + f'<path d="M-72,-88 H72 V-58 H-72 Z" fill="{PAPER}" stroke="{INK}" stroke-width="5"/>'
           + "".join(f'<path d="M{x},-84 v8" stroke="{INK}" stroke-width="3"/>' for x in range(-60, 64, 12))
           + f'<path d="M-6,-88 v28" stroke="#b5463a" stroke-width="4"/>'
           + f'<circle cx="-70" cy="-28" r="16" fill="{WOOD_D}" stroke="{INK}" stroke-width="5"/>'
           + f'<circle cx="70" cy="-28" r="16" fill="{WOOD_D}" stroke="{INK}" stroke-width="5"/>')
    return _r(b, 248, 270)


# ------------------------------------------------------------------ rebrik
def p_ladder(pid=""):
    """Dreveny stojaci rebrik (A) mierne zo strany: predne stupadla, zadna podpera, retiazka."""
    back = _plank(20, -548, 150, 0, 14, WOOD_L)
    rails = _plank(-120, 0, -20, -556, 16) + _plank(-40, 0, 38, -556, 16)
    rungs = ""
    for k in range(1, 8):
        u = k / 8.0
        xl, xr = -120 + 100 * u, -40 + 78 * u
        y = -556 * u
        rungs += _plank(xl + 6, y, xr - 6, y, 10)
    top = f'<path d="M-30,-562 H46 V-580 H-30 Z" fill="{WOOD}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
    chain = f'<path d="M-60,-250 Q40,-236 110,-190" fill="none" stroke="{IRON}" stroke-width="4" stroke-dasharray="8 6"/>'
    return _r(back + chain + rails + rungs + top, 300, 580)


# ------------------------------------------------------------------ stan
def p_tent(pid=""):
    """Plátenny stan (sikmy pohlad): stit so vchodom, bocna strecha, lana s kolikmi."""
    canvas, side = "#d9c28e", "#c4aa74"
    b = (f'<path d="M-60,-300 L276,-276 L320,4 L124,4 Z" fill="{side}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M-250,4 L-60,-300 L124,4 Z" fill="{canvas}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-60,-300 L-112,4 H-8 Z" fill="#8a7550" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
         f'<path d="M-60,-300 L-150,4 M-60,-300 L-40,4" fill="none" stroke="{INK}" stroke-width="5"/>'
         f'<path d="M-60,-300 V-330" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>'
         f'<path d="M-60,-326 L-300,4 M276,-278 L380,4" fill="none" stroke="#8a7550" stroke-width="3"/>'
         f'<path d="M-306,-6 l12,14 M374,-6 l12,14" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
         f'<path d="M40,-160 l120,10 M60,-80 l140,10" stroke="#a88a5e" stroke-width="4" opacity="0.7"/>')
    return _r(b, 700, 334)


# ------------------------------------------------------------------ okno
def window_pane(w=200, h=260):
    """Samotne okno (bez steny): ram, sklo s odleskom, priecky, parapet - na stenu v interieri.
    Spodok (parapet) na y=0."""
    return (f'<path d="M{-w / 2 - 22},0 H{w / 2 + 22} V-18 H{-w / 2 - 22} Z" fill="{WOOD}" stroke="{INK}" stroke-width="7" '
            f'stroke-linejoin="round"/>'
            f'<path d="M{-w / 2},-18 V{-18 - h} H{w / 2} V-18 Z" fill="{GLASS}" stroke="{INK}" stroke-width="10" '
            f'stroke-linejoin="round"/>'
            f'<path d="M0,-18 V{-18 - h} M{-w / 2},{-18 - h * 0.5:.0f} H{w / 2}" stroke="{WOOD}" stroke-width="12"/>'
            f'<path d="M0,-18 V{-18 - h} M{-w / 2},{-18 - h * 0.5:.0f} H{w / 2}" stroke="{INK}" stroke-width="3" opacity="0.6"/>'
            f'<path d="M{-w / 2 + 16},{-60} l{w * 0.26:.0f},{-h * 0.3:.0f}" stroke="#ffffff" stroke-width="8" stroke-linecap="round"/>')


def p_window(pid=""):
    """Kus kamennej steny s oknom (zvonku): omietka a kamene, okenice, parapet."""
    wall = (f'<path d="M-210,4 V-560 H210 V4 Z" fill="#e4ddcd" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
            + "".join(f'<path d="M{x},{y} h{w}" stroke="#b9ae98" stroke-width="5" stroke-linecap="round"/>'
                      for x, y, w in ((-180, -520, 70), (-60, -500, 90), (100, -530, 80), (-190, -120, 80), (90, -90, 90),
                                      (-150, -60, 60), (40, -40, 70))))
    shut = (f'<path d="M-170,-176 V-460 H-112 V-176 Z" fill="#6f8fa8" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M112,-176 V-460 H170 V-176 Z" fill="#6f8fa8" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            + "".join(f'<path d="M{x},-{y} h46" stroke="#4f6f86" stroke-width="4"/>' for x in (-164, 118) for y in range(206, 460, 34)))
    return _r(wall + shut + f'<g transform="translate(0,-160)">{window_pane(210, 280)}</g>', 420, 564)


# ------------------------------------------------------------------ krb
def p_fireplace(pid=""):
    """Kamenný krb pri stene: komínove teleso, drevena rimsa, ohnisko s polenami, zeravy popol."""
    breast = (f'<path d="M-200,4 V-680 H200 V4 Z" fill="#d6cfbf" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
              + "".join(f'<path d="M{x},{y} h{w} v36 h{-w} z" fill="none" stroke="#b3aa97" stroke-width="4"/>'
                        for x, y, w in ((-180, -640, 90), (-70, -620, 110), (60, -650, 100), (-160, -520, 120), (10, -540, 150),
                                        (-190, -420, 70), (120, -440, 60))))
    box = (f'<path d="M-136,4 V-190 Q-136,-262 -66,-262 H66 Q136,-262 136,-190 V4 Z" fill="#8c806b" stroke="{INK}" '
           f'stroke-width="8" stroke-linejoin="round"/>'
           f'<path d="M-104,4 V-176 Q-104,-226 -50,-226 H50 Q104,-226 104,-176 V4 Z" fill="#6f6556" stroke="none"/>')
    logs = (f'<path d="M-80,-10 Q0,-50 80,-18 Q0,-26 -80,-10 Z" fill="#b8b0a2" stroke="none"/>'
            + _plank(-70, -30, 60, -54, 22, WOOD) + _plank(-50, -58, 74, -30, 20, WOOD_D)
            + "".join(f'<circle cx="{x}" cy="{y}" r="{rr}" fill="#f39c34" stroke="none" opacity="0.9"/>'
                      for x, y, rr in ((-20, -24, 6), (12, -18, 5), (36, -26, 4), (-44, -20, 4))))
    mantel = (f'<path d="M-236,-300 H236 V-268 H-236 Z" fill="{WOOD}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
              f'<path d="M-236,4 H236 V-12 H-236 Z" fill="#b3aa97" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>')
    return _r(breast + box + logs + mantel, 472, 684)


NEW = {
    "bed": p_bed, "clock": p_clock, "chair": p_chair, "chair_toppled": p_chair_toppled, "table": p_table,
    "meal": p_meal, "lantern": p_lantern, "coat": p_coat, "letter": p_letter, "footprints": p_footprints,
    "rope": p_rope, "boat": p_boat, "candle": p_candle, "bottle": p_bottle, "boot": p_boot, "key": p_key,
    "radio": p_radio, "ladder": p_ladder, "tent": p_tent, "window": p_window, "fireplace": p_fireplace,
}
# pravdiva velkost voci Bobovi (1,75 m = 1,0): ("h", vyska) alebo ("w", sirka)
SIZES = {
    "bed": ("w", 1.14),            # 2,0 m dlha, celo ~1,1 m
    "clock": ("h", 0.20),          # krbove hodiny ~35 cm
    "chair": ("h", 0.54),          # operadlo ~95 cm
    "chair_toppled": ("w", 0.54),
    "table": ("w", 0.80),          # 1,4 m dlhy, 0,75 m vysoky
    "meal": ("w", 0.20),           # tanier 26 cm + hrncek
    "lantern": ("h", 0.21),        # 37 cm
    "coat": ("h", 1.00),           # vesiak 1,75 m, plast ~1,1 m
    "letter": ("w", 0.13),         # 21 x 30 cm
    "footprints": ("w", 1.14),     # ~2 m stop
    "rope": ("w", 0.34),           # kotuc ~0,6 m
    "boat": ("w", 2.10),           # clun ~3,7 m
    "candle": ("h", 0.14),         # 25 cm so svietnikom
    "bottle": ("h", 0.18),         # 32 cm
    "boot": ("h", 0.21),           # 37 cm
    "key": ("w", 0.14),            # 14 cm v skutocnosti (0,08) - pri 0,08 bol necitatelny aj z blizka
    "radio": ("w", 0.26),          # 45 cm
    "ladder": ("h", 1.07),         # 1,9 m
    "tent": ("w", 1.60),           # 2,8 m s lanami
    "window": ("h", 1.30),         # kus steny 2,3 m, okno ~1 x 1,3 m
    "fireplace": ("h", 1.40),      # s komínovým telesom 2,45 m
}


def register():
    P.PROPS.update(NEW)
    P.SIZE.update(SIZES)


register()


# ------------------------------------------------------------------ debna (zasobovacia) + rozbita
# „supply box" vychadzal ako piratska truhla s pokladom (p_chest) - to user vytkol pri Flannane.
def _crate_body(w=300, h=250):
    x0, y0 = -w / 2, -h
    planks = "".join(f'<path d="M{x0:.0f},{y0 + h * (k + 1) / 3:.0f} H{x0 + w:.0f}" stroke="{INK}" stroke-width="5" opacity="0.55"/>'
                     for k in range(2))
    nails = "".join(f'<circle cx="{x:.0f}" cy="{y0 + h * (k + 0.5) / 3:.0f}" r="5" fill="{INK}"/>'
                    for k in range(3) for x in (x0 + 18, x0 + w - 18))
    return (f'<path d="M{x0:.0f},0 V{y0:.0f} H{x0 + w:.0f} V0 Z" fill="{WOOD_L}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
            f'{planks}'
            f'<path d="M{x0 + 18:.0f},-4 V{y0 + 4:.0f} M{x0 + w - 18:.0f},-4 V{y0 + 4:.0f}" stroke="{WOOD_D}" stroke-width="16"/>'
            f'{nails}')


def p_crate(pid=""):
    """Drevena zasobovacia debna (0,6 x 0,5 m): dosky, bocne laty, klince."""
    return _r(_crate_body(), 300, 250)


def p_crate_broken(pid=""):
    """Rozbita debna: vrchna doska vylamana na triesky, jedna doska lezi vedla, triesky okolo."""
    w, h = 300, 250
    x0, y0 = -w / 2, -h
    top = y0 + h / 3
    b = (f'<path d="M{x0:.0f},0 V{top:.0f} H{x0 + w:.0f} V0 Z" fill="{WOOD_L}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M{x0:.0f},{top + h / 3:.0f} H{x0 + w:.0f}" stroke="{INK}" stroke-width="5" opacity="0.55"/>'
         f'<path d="M{x0:.0f},{top:.0f} l0,-46 l28,18 l22,-42 l30,32 l26,-54 l24,36 l20,-22 l10,78 z" fill="{WOOD_L}" '
         f'stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M{x0 + w:.0f},{top:.0f} l0,-32 l-24,14 l-18,-38 l-22,32 l-14,24 z" fill="{WOOD_L}" stroke="{INK}" '
         f'stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M{x0 + 18:.0f},-4 V{top - 26:.0f} M{x0 + w - 18:.0f},-4 V{top - 14:.0f}" stroke="{WOOD_D}" stroke-width="16"/>'
         + "".join(f'<circle cx="{x:.0f}" cy="{top + h * (k + 0.5) / 3:.0f}" r="5" fill="{INK}"/>'
                   for k in range(2) for x in (x0 + 18, x0 + w - 18))
         + f'<path d="M{x0 + w + 24:.0f},0 l150,-62 l12,22 l-150,62 z" fill="{WOOD_L}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M{x0 - 40:.0f},0 l-32,-26 l54,4 z M{x0 + w + 76:.0f},-74 l24,-42 l12,46 z M{x0 + 84:.0f},{y0 + 26:.0f} l18,-42 l16,34 z" '
         f'fill="{WOOD_L}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>')
    return _r(b, w + 200, h)


def p_body(pid=""):
    """Mrtvy clovek = telo pod bielou plachtou (bez krvi): hlava vlavo, topanky trcia vpravo, tien na zemi.
    Kostra/lebka je spravna len pri starych kostiach; pri cerstvych obetiach (Dyatlov, Somerton) bola lebka nezmysel."""
    shadow = f'<path d="{_ell_path(-8, 8, 200, 16)}" fill="#d9d2c0" opacity="0.55"/>'
    boots = "".join(f'<path d="M{146 + k * 6},{-18 + k * 8} h42 q16,0 16,12 v8 h-58 z" fill="#4a4038" stroke="{INK}" '
                    f'stroke-width="6" stroke-linejoin="round"/>' for k in range(2))
    sheet = (f'<path d="M-174,4 C-194,-40 -162,-86 -120,-84 C-94,-82 -86,-60 -60,-58 L60,-52 C110,-50 140,-30 150,-12 L156,4 Z" '
             f'fill="#ffffff" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
             f'<path d="M-104,-30 q10,-20 4,-40 M-20,-12 q14,-18 10,-38 M92,-16 q6,-14 0,-30" fill="none" stroke="{INK}" '
             f'stroke-width="4" opacity="0.5"/>')
    return _r(shadow + boots + sheet, 410, 90)


def _ell_path(cx, cy, rx, ry):
    return f"M{cx - rx},{cy} a{rx},{ry} 0 1 0 {2 * rx},0 a{rx},{ry} 0 1 0 {-2 * rx},0"


def p_wave(pid=""):
    """Velka vlna s kučerou a penou - teoria „obrovska vlna" (bublina) aj scena; predtym sa kreslilo jazero."""
    b = (f'<path d="M-230,0 C-230,-110 -160,-215 -40,-232 C70,-248 190,-200 210,-120 C222,-70 190,-46 150,-70 '
         f'C118,-90 116,-134 152,-150 C110,-170 60,-160 40,-120 C20,-80 60,-40 120,-40 L230,0 Z" fill="{WATER}" '
         f'stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-170,-60 C-150,-130 -90,-180 -20,-190" fill="none" stroke="#ffffff" stroke-width="7" '
         f'stroke-linecap="round" opacity="0.8"/>'
         + "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#ffffff" stroke="{INK}" stroke-width="5"/>'
                   for x, y, r in ((160, -168, 16), (196, -150, 12), (128, -186, 11), (212, -182, 9))))
    return _r(b, 460, 250)


def p_lighthouse(pid=""):
    """Majak: biela kuzelovita veza s cervenymi pasmi, galeria, lampova komora so sklom a strieskou.
    Vseobecna „tower" je hradna veza s cimburim - pri „island lighthouse" to bolo zle."""
    b = (f'<path d="M-95,0 L-62,-560 H62 L95,0 Z" fill="#ffffff" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<path d="M-84,-150 L-78,-250 H78 L84,-150 Z M-72,-360 L-68,-450 H68 L72,-360 Z" fill="#d94a3a" stroke="{INK}" '
         f'stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M-96,-560 h192 v-26 h-192 z" fill="{INK}"/>'
         f'<path d="M-52,-586 v-110 h104 v110 z" fill="{GLASS}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-18,-586 v-110 M18,-586 v-110" stroke="{INK}" stroke-width="6"/>'
         f'<circle cx="0" cy="-640" r="22" fill="{SUN}" stroke="{INK}" stroke-width="6"/>'
         f'<path d="M-66,-696 L0,-760 L66,-696 Z" fill="#d94a3a" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-30,0 v-90 q30,-30 60,0 V0 Z" fill="{INK}"/>'
         f'<path d="M-14,-300 h28 v-40 h-28 z M-12,-480 h24 v-36 h-24 z" fill="{INK}"/>')
    return _r(b, 190, 760)


NEW.update({"crate": p_crate, "crate_broken": p_crate_broken, "body": p_body, "wave": p_wave, "lighthouse": p_lighthouse})
SIZES.update({"lighthouse": ("h", 3.4)})
SIZES.update({"crate": ("h", 0.32), "crate_broken": ("h", 0.32),   # ~0,55 m, oba v rovnakej mierke
              "body": ("w", 1.05),                                  # leziaci clovek ~1,8 m aj s topankami
              "wave": ("h", 2.2)})                                  # vlna vyssia nez clovek
register()


# ------------------------------------------------------------------ plast na haku (bez stojana) + kniha s vytrhnutou stranou
# insert-varianty pre archetyp `insert` (detail SAMOTNEHO PREDMETU): rovnaky plast ako p_coat, ale
# visiaci rovno na jednom haku (ziadny stojan) a otvorena kniha, ktorej pravu stranu niekto vytrhol.
def p_coat_hanging(pid=""):
    """Zlty oilskin plast visiaci rovno na haku: kovove ocko, golier, telo, rukavy volne dole.
    Dotyk so zemou v y=0 je lem (spodok) plasta, hore rastie ku ocku na haku (rovnaky dohovor ako
    ostatne rekvizity - len "zem" je tu vyska lemu, nie skutocna podlaha)."""
    ring = (f'<circle cx="0" cy="-478" r="13" fill="none" stroke="{INK}" stroke-width="6"/>'
            f'<path d="M0,-465 V-444" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>')
    body = (f'<path d="M-92,-444 Q-96,-420 -86,0 L86,0 Q96,-420 92,-444 Q60,-460 0,-458 Q-60,-460 -92,-444 Z" '
            f'fill="{OIL}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>')
    collar = (f'<path d="M-52,-446 L-14,-402 L0,-430 L14,-402 L52,-446" fill="none" stroke="{INK}" stroke-width="8" '
              f'stroke-linejoin="round" stroke-linecap="round"/>'
              f'<path d="M-52,-446 L-14,-402 L0,-430 Z" fill="{OIL_D}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
              f'<path d="M52,-446 L14,-402 L0,-430 Z" fill="{OIL_D}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>')
    placket = (f'<path d="M0,-420 V-16" stroke="{OIL_D}" stroke-width="5"/>'
               + "".join(f'<circle cx="0" cy="{y}" r="6" fill="{INK}" stroke="none"/>'
                         for y in (-360, -300, -240, -180, -120, -60)))
    folds = (f'<path d="M-70,-360 Q-84,-220 -68,-40 M70,-360 Q84,-220 68,-40" fill="none" stroke="{OIL_D}" '
             f'stroke-width="6" stroke-linecap="round"/>')
    sleeveL = (f'<path d="M-96,-436 Q-146,-424 -150,-330 Q-152,-240 -136,-156 Q-118,-146 -104,-158 '
               f'Q-116,-250 -112,-330 Q-108,-400 -80,-424 Z" fill="{OIL}" stroke="{INK}" stroke-width="8" '
               f'stroke-linejoin="round"/>'
               f'<path d="M-136,-156 Q-120,-138 -104,-158" fill="none" stroke="{OIL_D}" stroke-width="5"/>')
    sleeveR = (f'<path d="M96,-436 Q146,-424 150,-330 Q152,-240 136,-156 Q118,-146 104,-158 '
               f'Q116,-250 112,-330 Q108,-400 80,-424 Z" fill="{OIL}" stroke="{INK}" stroke-width="8" '
               f'stroke-linejoin="round"/>'
               f'<path d="M136,-156 Q120,-138 104,-158" fill="none" stroke="{OIL_D}" stroke-width="5"/>')
    return _r(ring + sleeveL + sleeveR + body + collar + placket + folds, 310, 500)


def p_book_torn(pid=""):
    """Otvorena kniha spredu: lava strana cela s riadkami pisma, prava strana vytrhnuta -
    zostal len zubaty pruzok pri chrbte a volny odtrhnuty kus papiera lezi vedla knihy."""
    pg, ink2 = "#f3e9cf", "#5a4a3a"
    cover = (f'<path d="M-240,-4 Q-120,-30 0,-14 Q120,-30 240,-4 L244,-26 Q120,-54 0,-38 Q-120,-54 -244,-26 Z" '
             f'fill="#7a4a2a" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>')
    lp = (f'<path d="M-228,-28 Q-226,-142 -216,-184 Q-110,-206 -4,-170 L0,-42 Q-112,-66 -228,-28 Z" '
          f'fill="{pg}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>')
    lines = "".join(f'<path d="M{-204 + (i % 2) * 4:.0f},{-172 + i * 21} q10,-8 20,0 q10,8 20,0 q10,-8 20,0 '
                    f'q10,8 18,0" fill="none" stroke="{ink2}" stroke-width="3" stroke-linecap="round"/>'
                    for i in range(6))
    stub = (f'<path d="M4,-170 Q56,-188 92,-172 L72,-144 L90,-118 L62,-96 L78,-68 L46,-50 Q18,-58 0,-42 Z" '
            f'fill="{pg}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
            f'<path d="M72,-144 L90,-118 L62,-96 L78,-68 L46,-50" fill="none" stroke="{ink2}" stroke-width="3" '
            f'stroke-dasharray="2 6" opacity="0.6"/>')
    shreds = "".join(f'<path d="M{x},{y} l{dx},{dy} l{-dx * 0.4:.0f},{dy * 0.6:.0f} z" fill="{pg}" stroke="{INK}" '
                     f'stroke-width="4" stroke-linejoin="round"/>'
                     for x, y, dx, dy in ((6, -166, 16, -10), (8, -118, 20, 8), (10, -78, 14, -6)))
    scrap = (f'<g transform="translate(300,-16) rotate(9)">'
             f'<path d="M-56,0 L-34,-56 L-12,-38 L6,-62 L28,-42 L46,-6 L18,10 Q-20,18 -56,0 Z" fill="{pg}" '
             f'stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
             f'<path d="M-32,-8 q10,-8 20,-2 q10,6 18,-2" fill="none" stroke="{ink2}" stroke-width="3" '
             f'stroke-linecap="round"/></g>')
    return _r(cover + lp + stub + shreds + lines + scrap, 600, 216)


NEW.update({"coat_hanging": p_coat_hanging, "book_torn": p_book_torn})
SIZES.update({"coat_hanging": ("h", 0.62),    # plast bez stojana, o niecu kratsi nez na vesiaku
              "book_torn": ("w", 0.18)})      # rovnaka velkost ako cela kniha (book)
register()


# ================================================================== JAVY (UnexplainedDaily)
# Kanal rozprava o javoch (svetla na oblohe, hucanie, signaly, hmla, blesky, kratery), nie len o predmetoch -
# bez nich kritik dal obrazu 3/10 (katalog mal kamen, lod, lebku..., ale nic pre svetlo, zvuk ani signal).
# Vsetko STATICKE (ziadna animacia) - neviditelna slucka ostava nedotknuta, "zivot" dava boil filter ako
# vsetkym ciaram. Ciary INK maju pod sebou polopriesvitny svetly podklad (PAPER): cez den na papieri ho nevidno,
# v noci na tmavej oblohe obrys "svieti" (rovnaky trik ako biely lem titulkov).
# Vsetkych sest je "obj" (stage.dominance): insert ich ukaze v krajine s oblohou (insert_shots._big_focus),
# nie na plochej zemi ako male predmety. P.FOCUS = ohnisko (kam ide kruh/krizik/sipka, co musi byt v zabere).
GLOW_CORE = "#fffdf2"
GLOW_IN = "#ffe680"
GLOW_MID = "#ffd84f"
GLOW_OUT = "#ffcf40"
GLOW_RAY = "#f5a623"
BOLT = "#fffbe3"
STORM = "#a3aab5"
STORM_D = "#7f8794"
SOIL = "#c2a579"
SOIL_D = "#6b5439"
SOIL_W = "#9a7b55"
SOIL_F = "#4a3a28"
DISH_W = "#f3f1ea"
DISH_B = "#cfcbc1"
CONCRETE = "#d8d2c4"


def _glow_line(d, w, sw_ink=7, halo=0.55):
    """Svetly podklad pod ciaru INK (v noci sa obrys od tmavej oblohy odlisi, cez den nevidno)."""
    return (f'<path d="{d}" fill="none" stroke="{PAPER}" stroke-width="{sw_ink + w}" stroke-linecap="round" '
            f'stroke-linejoin="round" opacity="{halo}"/>')


def _poly(pts, close=False):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + (" Z" if close else "")


# ------------------------------------------------------------------ svetelna gula
LIGHT_Y = -420          # stred gule nad zemou - vznasa sa vo vyske ~2,3 m


def _sparkle(x, y, s):
    """Styrcipa iskra (ako hviezdy v noci), s obrysom - cez den na papieri nezmizne."""
    q = s * 0.26
    return (f'<path d="M{x:.0f},{y - s:.0f} L{x + q:.1f},{y - q:.1f} L{x + s:.0f},{y:.0f} L{x + q:.1f},{y + q:.1f} '
            f'L{x:.0f},{y + s:.0f} L{x - q:.1f},{y + q:.1f} L{x - s:.0f},{y:.0f} L{x - q:.1f},{y - q:.1f} Z" '
            f'fill="#fff6cc" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>')


def p_light(pid=""):
    """Svetelna gula vo vzduchu (Hessdalen, bludicka, "orb"): biele jadro s obrysom, makka zlta ziara (tri vrstvy
    bez obrysu), dva prerusovane "pulzujuce" kruhy a styri iskry - ziadne luce, cez den nesmie vyzerat ako druhe
    slnko. Dotyk so zemou (y=0) je svetelna skvrna pod gulou, nie predmet - gula visi vo vzduchu."""
    cy = LIGHT_Y
    pool = (f'<path d="{P.ell(0, 0, 124, 18)}" fill="{GLOW_MID}" opacity="0.40"/>'
            f'<path d="{P.ell(0, 0, 66, 10)}" fill="{GLOW_IN}" opacity="0.70"/>')
    halo = (f'<circle cx="0" cy="{cy}" r="150" fill="{GLOW_OUT}" opacity="0.16"/>'
            f'<circle cx="0" cy="{cy}" r="116" fill="{GLOW_MID}" opacity="0.30"/>'
            f'<circle cx="0" cy="{cy}" r="84" fill="{GLOW_IN}" opacity="0.62"/>')
    rings = (f'<circle cx="0" cy="{cy}" r="104" fill="none" stroke="{GLOW_RAY}" stroke-width="6" '
             f'stroke-dasharray="18 14" stroke-linecap="round"/>'
             f'<circle cx="0" cy="{cy}" r="138" fill="none" stroke="{GLOW_RAY}" stroke-width="5" '
             f'stroke-dasharray="10 22" stroke-linecap="round" opacity="0.8"/>')
    sparks = "".join(_sparkle(x, cy + y, s) for x, y, s in ((-118, -104, 17), (126, -78, 13), (112, 110, 15),
                                                            (-128, 84, 11)))
    core = (f'<circle cx="0" cy="{cy}" r="52" fill="{GLOW_CORE}" stroke="{INK}" stroke-width="7"/>'
            f'<circle cx="0" cy="{cy}" r="52" fill="none" stroke="{GLOW_IN}" stroke-width="10" opacity="0.8"/>'
            f'<circle cx="0" cy="{cy}" r="52" fill="none" stroke="{INK}" stroke-width="7"/>'
            f'<circle cx="-6" cy="{cy - 6}" r="27" fill="#ffffff"/>'
            f'<path d="M-30,{cy - 14} q8,-19 28,-23" fill="none" stroke="#ffffff" stroke-width="6" '
            f'stroke-linecap="round"/>')
    return _r(pool + halo + rings + sparks + core, 300, 570)


# ------------------------------------------------------------------ blesk z burkoveho mraku
_CLOUD_Q = ((-40, -6, -22, -40), (14, -38, 56, -22), (22, -46, 70, -18), (44, -8, 40, 36), (34, 10, 8, 44))


def _cloud_d(cx, cy, sx, sy):
    """Obrys rucne kresleneho oblaku (props.cloud) natiahnuty bez transformacie - hrubka ciary ostane rovnaka."""
    return (f"M{cx - 90 * sx:.1f},{cy + 30 * sy:.1f}"
            + "".join(f" q{a * sx:.1f},{b * sy:.1f} {c * sx:.1f},{e * sy:.1f}" for a, b, c, e in _CLOUD_Q) + " Z")


def p_lightning(pid=""):
    """Blesk z burkoveho mraku do zeme: dva tmavosive oblaky, lomeny blesk (ziara, obrys, svetle jadro), dve
    bocne vetvy, na zemi zablesk, iskry a dva odletene kamienky v mieste zasahu. Mrak je sucast kresby - blesk
    sa cita aj v bubline teorie a v detaile bez oblohy."""
    clouds = (f'<path d="{_cloud_d(140, -912, 1.9, 1.25)}" fill="{STORM_D}" stroke="{INK}" stroke-width="8" '
              f'stroke-linejoin="round"/>'
              f'<path d="{_cloud_d(-10, -882, 2.3, 1.55)}" fill="{STORM}" stroke="{INK}" stroke-width="8" '
              f'stroke-linejoin="round"/>'
              f'<path d="M-150,-866 q70,18 150,4 q60,-8 120,8" fill="none" stroke="{STORM_D}" stroke-width="7" '
              f'stroke-linecap="round"/>')
    main = ((-6, -858), (38, -700), (-16, -610), (42, -452), (-8, -362), (34, -204), (4, -126), (22, 0))
    b1 = ((-16, -610), (-74, -532), (-62, -488), (-116, -418))
    b2 = ((42, -452), (98, -386), (90, -344), (136, -286))

    def bolt(pts, glow, ink, core):
        d = "M" + " L".join(f"{x},{y}" for x, y in pts)
        return (f'<path d="{d}" fill="none" stroke="{GLOW_IN}" stroke-width="{glow}" stroke-linecap="round" '
                f'stroke-linejoin="round" opacity="0.45"/>'
                f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{ink}" stroke-linecap="round" '
                f'stroke-linejoin="miter" stroke-miterlimit="3"/>'
                f'<path d="{d}" fill="none" stroke="{BOLT}" stroke-width="{core}" stroke-linecap="round" '
                f'stroke-linejoin="miter" stroke-miterlimit="3"/>')
    sx = 22
    strike = (f'<path d="{P.ell(sx, 0, 96, 15)}" fill="{GLOW_IN}" opacity="0.55"/>'
              + "".join(f'<path d="M{sx + math.cos(a) * 34:.0f},{-8 + math.sin(a) * 34:.0f} '
                        f'L{sx + math.cos(a) * 64:.0f},{-8 + math.sin(a) * 64:.0f}" stroke="{INK}" stroke-width="6" '
                        f'stroke-linecap="round"/>' for a in [math.radians(v) for v in (200, 226, 250, 290, 314, 340)])
              + f'<path d="M{sx - 70},4 l14,-18 l16,6 l4,14 z M{sx + 58},6 l10,-14 l14,4 l2,12 z" fill="{STONE}" '
                f'stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    return _r(clouds + bolt(b1, 28, 15, 6) + bolt(b2, 28, 15, 6) + bolt(main, 52, 26, 14) + strike, 560, 990)


# ------------------------------------------------------------------ zvuk (hucanie, dunenie, tresk)
def p_sound(pid=""):
    """Zvuk zo zeme (alebo z mora): styri sustredne oblúky stupajuce z bodu na zemi, jemne sa "chveju"
    (sinusovka po obvode - zvuk, nie hladky signal ako pri anténe), vonkajsi prerusovany (doznieva);
    pri zdroji chvenie zeme (ciarky, vlnovky), po stranach kratke ciarky pohybu."""
    cy = -8
    arcs = ""
    a0, a1 = math.radians(-134), math.radians(-46)
    for i, (R, sw) in enumerate(((96, 10), (172, 9), (248, 8), (324, 7))):
        waves = max(2, round(R * (a1 - a0) / 90.0))
        amp = 2.2 + i * 0.5
        pts = []
        for k in range(65):
            rr = R + amp * math.sin(2 * math.pi * waves * k / 64)
            a = a0 + (a1 - a0) * k / 64
            pts.append((rr * math.cos(a), cy + rr * math.sin(a)))
        d = _poly(pts)
        dash = ' stroke-dasharray="26 18"' if i == 3 else ""
        arcs += (_glow_line(d, 10, sw)
                 + f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{sw}" stroke-linecap="round"{dash}/>')
    ticks = ""
    for s in (-1, 1):
        a = math.radians(-90 + s * 54)
        for R0, R1 in ((150, 178), (228, 256)):
            ticks += (f"M{R0 * math.cos(a):.1f},{cy + R0 * math.sin(a):.1f} "
                      f"L{R1 * math.cos(a):.1f},{cy + R1 * math.sin(a):.1f} ")
        for a_deg in (200, 222, 244):
            b = math.radians(a_deg if s < 0 else 540 - a_deg)
            ticks += (f"M{26 * math.cos(b):.1f},{-6 + 26 * math.sin(b):.1f} "
                      f"L{50 * math.cos(b):.1f},{-6 + 50 * math.sin(b):.1f} ")
    ticks = ticks.strip()
    wig = "M44,2 q10,-8 20,0 q10,8 20,0 q10,-8 20,0 M-44,2 q-10,-8 -20,0 q-10,8 -20,0 q-10,-8 -20,0"
    src = (_glow_line(ticks, 8, 6)
           + f'<path d="{ticks}" fill="none" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
           + f'<path d="{P.ell(0, 0, 30, 8)}" fill="{INK}"/>'
           + f'<path d="{wig}" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')
    return _r(arcs + src, 450, 340)


# ------------------------------------------------------------------ radioteleskop (signal, antena)
def _ellipse_pts(c, u, v, a, b, n, t0=0.0, t1=2 * math.pi):
    return [(c[0] + a * u[0] * math.cos(t) + b * v[0] * math.sin(t), c[1] + a * u[1] * math.cos(t) + b * v[1] * math.sin(t))
            for t in [t0 + (t1 - t0) * k / n for k in range(n + 1)]]


def p_dish(pid=""):
    """Radioteleskop: betonovy podstavec, stlp s dvierkami, otocna hlava a velka parabola natocena doprava hore
    (zadna miska aj osvetlena plocha s prstencami panelov), v ohnisku prijimac na troch vzperach a z neho
    tri vlny signalu (vonkajsia prerusovana)."""
    dx = -60
    ang = math.radians(-40)
    n = (math.cos(ang), math.sin(ang))              # kam miera parabola (doprava hore)
    u = (-n[1], n[0])                               # hlavna os okraja (kolmo na n)
    C = (dx + n[0] * 90, -400.0 + n[1] * 90)        # stred okraja paraboly (90 od otocneho uchytu)
    A, B, D = 230.0, 80.0, 150.0                    # polosi okraja, hlbka misky
    base = (f'<path d="M{-190 + dx},6 L{-160 + dx},-54 H{160 + dx} L{190 + dx},6 Z" fill="{CONCRETE}" '
            f'stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
            f'<path d="M{-150 + dx},-30 H{150 + dx}" stroke="#b3ab99" stroke-width="5"/>')
    tower = (f'<path d="M{-62 + dx},-54 L{-36 + dx},-380 H{36 + dx} L{62 + dx},-54 Z" fill="#e9e6de" stroke="{INK}" '
             f'stroke-width="8" stroke-linejoin="round"/>'
             f'<path d="M{-16 + dx},-54 V-124 H{16 + dx} V-54" fill="#b9b4a8" stroke="{INK}" stroke-width="5" '
             f'stroke-linejoin="round"/>'
             f'<path d="M{-44 + dx},-210 H{44 + dx} M{-40 + dx},-300 H{40 + dx}" stroke="#bdb7aa" stroke-width="5"/>')
    hub = (f'<path d="M{-64 + dx},-372 H{64 + dx} V-424 Q{dx},-446 {-64 + dx},-424 Z" fill="{METAL}" stroke="{INK}" '
           f'stroke-width="8" stroke-linejoin="round"/>')
    back = [(C[0] + A * u[0] * math.cos(t) - D * n[0] * math.sin(t), C[1] + A * u[1] * math.cos(t) - D * n[1] * math.sin(t))
            for t in [math.pi * k / 18 for k in range(19)]]
    shell = f'<path d="{_poly(back, True)}" fill="{DISH_B}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
    rim = _ellipse_pts(C, u, n, A, B, 36)
    face = f'<path d="{_poly(rim, True)}" fill="{DISH_W}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
    rings = "".join(f'<path d="{_poly(_ellipse_pts(C, u, n, A * k, B * k, 28), True)}" fill="none" '
                    f'stroke="#bdb8ab" stroke-width="4"/>' for k in (0.36, 0.68))
    spokes = "".join(f'<path d="M{C[0]:.1f},{C[1]:.1f} L{p[0]:.1f},{p[1]:.1f}" stroke="#bdb8ab" stroke-width="4"/>'
                     for p in (rim[0], rim[9], rim[18], rim[27]))
    F = (C[0] + n[0] * 150, C[1] + n[1] * 150)      # ohnisko s prijimacom
    struts = "".join(f'<path d="M{p[0]:.1f},{p[1]:.1f} L{F[0]:.1f},{F[1]:.1f}" stroke="{INK}" stroke-width="5" '
                     f'stroke-linecap="round"/>' for p in (rim[4], rim[16], rim[28]))
    feed = (f'<circle cx="{F[0]:.1f}" cy="{F[1]:.1f}" r="26" fill="{GLOW_IN}" opacity="0.6"/>'
            f'<circle cx="{F[0]:.1f}" cy="{F[1]:.1f}" r="14" fill="{METAL}" stroke="{INK}" stroke-width="6"/>')
    waves = ""
    for i, R in enumerate((52, 90, 128)):
        w0, w1 = ang - math.radians(34), ang + math.radians(34)
        d = (f"M{F[0] + R * math.cos(w0):.1f},{F[1] + R * math.sin(w0):.1f} "
             f"A{R},{R} 0 0 1 {F[0] + R * math.cos(w1):.1f},{F[1] + R * math.sin(w1):.1f}")
        waves += (_glow_line(d, 10, 7)
                  + f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"'
                  + (' stroke-dasharray="20 14"' if i == 2 else "") + "/>")
    return _r(base + tower + shell + hub + face + rings + spokes + struts + feed + waves, 500, 680)


# ------------------------------------------------------------------ hmla / opar
def _fog_band(x0, x1, H, ramp, bumps, base=6):
    """Hmlovy pas: dlha plosina (nie kopula) s makko klesajucimi koncami + nepravidelne chuchvalce na hornej
    hrane. Vrati (d vyplne uzavretej po zemi, d hornej hrany)."""
    n = len(bumps)
    xs = [x0 + (x1 - x0) * i / n for i in range(n + 1)]

    def yb(x):
        u = max(0.0, min(1.0, min(x - x0, x1 - x) / ramp))
        return base - H * u * u * (3 - 2 * u)
    top = f"M{xs[0]:.0f},{base}"
    for i in range(n):
        xa, xb = xs[i], xs[i + 1]
        top += f" Q{(xa + xb) / 2:.0f},{min(yb(xa), yb(xb)) - bumps[i]:.0f} {xb:.0f},{yb(xb):.0f}"
    return top + " Z", top


def p_fog(pid=""):
    """Nizka hmla / opar plaziaci sa po zemi (po hrud postavy): tri dlhe polopriesvitne pasy s chuchvalcami
    (zadny najvyssi a najbledsi, kazdy posunuty inam), obrys len na hornej hrane (spodok splyva so zemou),
    po stranach a vpredu odtrhnute pramene - hmla sa hybe do stran."""
    layers = ((-450, 400, 226, 300, (18, 30, 22, 34, 20, 28, 36, 22, 30, 18, 26), "#e3e8ec", 0.55, 5, 0.40),
              (-380, 470, 150, 280, (16, 26, 20, 30, 18, 24, 28, 20, 26, 16), "#eceff2", 0.62, 6, 0.62),
              (-480, 430, 74, 240, (12, 20, 16, 22, 14, 20, 18, 22, 14, 18, 12), "#f5f6f7", 0.76, 7, 0.85))
    out = ""
    for x0, x1, H, ramp, bumps, fill, op, sw, sop in layers:
        fd, td = _fog_band(x0, x1, H, ramp, bumps)
        out += (f'<path d="{fd}" fill="{fill}" opacity="{op}"/>'
                f'<path d="{td}" fill="none" stroke="{INK}" stroke-width="{sw}" stroke-linecap="round" '
                f'stroke-linejoin="round" opacity="{sop}"/>')
    wisps = ("M-560,-26 h110 M-540,-78 h86 M-516,-132 h60 M-470,-190 h40 M470,-40 h96 M494,-96 h66 M468,-150 h46 "
             "M-300,-14 q50,-12 100,0 M80,-20 q50,-12 100,0 M-150,-70 q40,-10 80,0 M200,-104 q36,-10 72,0")
    out += (f'<path d="{wisps}" fill="none" stroke="#ffffff" stroke-width="12" stroke-linecap="round" opacity="0.55"/>'
            f'<path d="{wisps}" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round" opacity="0.45"/>')
    return _r(out, 1120, 244)


# ------------------------------------------------------------------ krater
def _rock(x, y, s):
    return (f'<path d="M{x - s:.0f},{y:.0f} L{x - s * 0.6:.0f},{y - s * 0.9:.0f} L{x + s * 0.4:.0f},{y - s:.0f} '
            f'L{x + s:.0f},{y - s * 0.3:.0f} L{x + s * 0.7:.0f},{y:.0f} Z" fill="{STONE}" stroke="{INK}" '
            f'stroke-width="6" stroke-linejoin="round"/>')


# nepravidelnost vonkajsieho okraja valu - pevne cisla (build musi byt deterministicky, ziadny random)
_RIM_JIT = (0, 9, -4, 11, 2, -7, 10, -3, 7, -9, 4, 8, -6, 3, 10, -4, 6, -8, 9, 1, -3, 7, -6, 5)


def p_crater(pid=""):
    """Krater = jama V ZEMI (mierne zhora): plocha elipsa otvoru, okolo nizky zubaty val vyhodenej hliny
    (vzadu nad jamou, vpredu ako okraj), vnutri osvetlena protilahla stena a tmave dno; na zemi okolo svetle
    luce vyvrhnutej hliny, praskliny a rozhadzane kamene. Nie kopa s dierou - val je len o malo vyssi nez zem."""
    hy, rx, ry = -64, 246, 58            # otvor jamy
    orx, ory = 304, 90                   # vonkajsi okraj valu
    n = len(_RIM_JIT)
    ring = [(math.cos(2 * math.pi * k / n) * (orx + j * 1.6), hy + math.sin(2 * math.pi * k / n) * (ory + j))
            for k, j in enumerate(_RIM_JIT)]
    rays = ("M-300,-30 L-430,-22 M-296,-4 L-410,18 M-270,16 L-352,40 M300,-30 L432,-24 M296,-4 L414,16 "
            "M268,18 L350,38 M-150,22 L-188,38 M150,22 L188,38 M-230,-130 L-286,-150 M226,-132 L284,-150")
    rim = (f'<path d="{_poly(ring, True)}" fill="{SOIL}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
           f'<path d="M{-orx + 40},{hy - 30} Q0,{hy - ory - 26} {orx - 40},{hy - 30}" fill="none" stroke="#d9c297" '
           f'stroke-width="9" stroke-linecap="round"/>')
    cracks = ("M-262,-86 l-30,-10 M-270,-40 l-30,6 M-196,-128 l-16,-18 M264,-84 l30,-10 M272,-42 l30,8 "
              "M200,-126 l16,-20 M-90,6 l-8,18 M96,4 l10,18 M4,8 l0,18")
    hole = f'<path d="{P.ell(0, hy, rx, ry)}" fill="{SOIL_D}"/>'
    wall = f'<path d="M{-rx},{hy} A{rx},{ry} 0 0 1 {rx},{hy} Q0,{hy - 30} {-rx},{hy} Z" fill="{SOIL_W}"/>'
    floor = f'<path d="{P.ell(0, hy + 20, 124, 20)}" fill="{SOIL_F}"/>'
    edge = f'<path d="{P.ell(0, hy, rx, ry)}" fill="none" stroke="{INK}" stroke-width="8"/>'
    lip = (f'<path d="M{-rx + 26},{hy + 22} Q0,{hy + ry + 30} {rx - 26},{hy + 22}" fill="none" stroke="#e2cda3" '
           f'stroke-width="8" stroke-linecap="round"/>')
    rocks = "".join(_rock(x, y, s) for x, y, s in ((-376, 12, 30), (-318, 28, 20), (-432, -2, 16), (362, 14, 28),
                                                   (314, 28, 18), (424, 2, 15), (-158, -150, 16), (196, -142, 13),
                                                   (48, 28, 13)))
    return _r(f'<path d="{rays}" fill="none" stroke="#d8c193" stroke-width="9" stroke-linecap="round"/>'
              + rim + f'<path d="{cracks}" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
              + hole + wall + floor + lip + edge + rocks, 890, 170)


NEW.update({"light": p_light, "lightning": p_lightning, "sound": p_sound, "dish": p_dish, "fog": p_fog,
            "crater": p_crater})
SIZES.update({"light": ("h", 1.8),        # gula ~0,55 m vo vyske ~2,3 m (vratane ziary nad nou ~3,1 m)
              "lightning": ("h", 3.2),    # mrak ~5,6 m nad zemou - blesk ide z neba, v zabere presahuje ram
              "sound": ("h", 1.6),        # oblúky ~2,8 m nad zdrojom
              "dish": ("h", 2.6),         # radioteleskop ~4,5 m (skutocne su vacsie - v zabere musi ostat cely)
              "fog": ("w", 4.0),          # pas ~6 m dlhy, po hrud postavy
              "crater": ("w", 3.0)})      # jama ~3,8 m s valom a kamenmi, val nizsie nez koleno
# ohnisko (x, y, sirka, vyska) pri mierke 1 - vid props.FOCUS
P.FOCUS.update({"light": (0, LIGHT_Y, 300, 300), "lightning": (0, -494, 560, 988), "sound": (0, -165, 450, 340),
                "dish": (0, -338, 500, 680), "fog": (0, -118, 960, 244), "crater": (0, -64, 660, 200)})
register()
