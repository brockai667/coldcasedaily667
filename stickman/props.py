# -*- coding: utf-8 -*-
"""Kreslena stavebnica pre UnexplainedDaily engine.

Vsetko kresli rovnakou linkou ako Bob: cierna #1b1b1b, stroke-width 9 pre hlavnu siluetu,
5-7 pre detaily, round cap/join, vyplne z papierovej palety. Kazda rekvizita:
  - ma dotyk so zemou v y=0 a rastie hore (zaporne y),
  - je centrovana na x=0,
  - vrati sa ako (svg, width, height) pri scale 1.
Umiestnuje sa cez node()/riseNode() v engine.js -> pozicia, mierka, "vyrastie zo zeme", "zasype sa".
"""
import math
import random

PAPER, INK, RED = "#f6f1e4", "#1b1b1b", "#d62828"
GOLD, GOLD_D = "#FFCD28", "#9c6f06"
DIRT, DIRT2, STONE, SUN, HAT, PACK = "#e4d2ad", "#b9a273", "#d2cec4", "#f5c542", "#b98a4e", "#c9a36a"
GH = "#a89670"
WOOD, METAL, BRONZE, WATER, LEAF = "#7a5230", "#b5b5b5", "#c08a3e", "#8ecae6", "#4f8a3c"
SHADE = "#8f8b80"


def _g(body, fill="none", sw=9):
    return f'<g fill="{fill}" stroke="{INK}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{body}</g>'


# ============================================================ zakladne prvky sveta
def cloud(x, y, s=1.0):
    return (f'<path transform="translate({x},{y}) scale({s})" d="M-90,30 q-40,-6 -22,-40 q14,-38 56,-22 q22,-46 70,-18 '
            f'q44,-8 40,36 q34,10 8,44 Z" fill="{PAPER}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>')


def sun(pid, x, y, cls="sunray"):
    rays = "".join(f'<path d="M{math.cos(a) * 84:.1f},{math.sin(a) * 84:.1f} L{math.cos(a) * 118:.1f},{math.sin(a) * 118:.1f}"/>'
                   for a in [k * math.pi / 5 for k in range(10)])
    return (f'<g transform="translate({x},{y})" stroke="{INK}" stroke-width="8" stroke-linecap="round">'
            f'<g id="{pid}" class="{cls}">{rays}</g><circle r="62" fill="{SUN}"/></g>')


def grass(x, y, s=1.0):
    return (f'<path d="M{x - 12 * s:.0f},{y:.0f} l-7,{-24 * s:.0f} M{x:.0f},{y:.0f} l2,{-32 * s:.0f} '
            f'M{x + 12 * s:.0f},{y:.0f} l9,{-22 * s:.0f}" stroke="{LEAF}" stroke-width="6" stroke-linecap="round" fill="none"/>')


def pebbles(seed, n, x0, x1, y0, y1, avoid=None):
    r = random.Random(seed)
    out, k, guard = "", 0, 0
    while k < n and guard < n * 60:
        guard += 1
        x, y = r.uniform(x0, x1), r.uniform(y0, y1)
        if avoid and avoid(x, y):
            continue
        k += 1
        t = r.random()
        if t < 0.55:
            out += (f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r.uniform(9, 22):.0f}" ry="{r.uniform(6, 13):.0f}" '
                    f'transform="rotate({r.uniform(-30, 30):.0f} {x:.0f} {y:.0f})"/>')
        elif t < 0.85:
            out += f'<path d="M{x:.0f},{y:.0f} l{r.uniform(14, 30):.0f},{r.uniform(-8, 8):.0f}"/>'
        else:
            out += f'<path d="M{x:.0f},{y:.0f} q12,-16 24,0 q12,16 24,0"/>'
    return f'<g fill="none" stroke="{DIRT2}" stroke-width="5" stroke-linecap="round">{out}</g>'


def bone(x, y, rot=0, s=1.0):
    return (f'<g transform="translate({x},{y}) rotate({rot}) scale({s})" fill="{PAPER}" stroke="{DIRT2}" stroke-width="5">'
            f'<path d="M-40,-6 H40 a9,9 0 1 1 8,6 a9,9 0 1 1 -8,6 H-40 a9,9 0 1 1 -8,-6 a9,9 0 1 1 8,-6 Z"/></g>')


def ell(cx, cy, rx, ry):
    return f"M{cx - rx:.0f},{cy:.0f} a{rx:.0f},{ry:.0f} 0 1 0 {2 * rx:.0f},0 a{rx:.0f},{ry:.0f} 0 1 0 {-2 * rx:.0f},0"


PUFF = (f'<g fill="{PAPER}" stroke="{INK}" stroke-width="5"><circle cx="0" cy="0" r="16"/>'
        f'<circle cx="20" cy="-8" r="12"/><circle cx="-17" cy="-5" r="11"/></g>')
DROP = f'<path d="M0,-16 Q11,2 0,9 Q-11,2 0,-16 Z" fill="{WATER}" stroke="{INK}" stroke-width="4"/>'
CHIP = f'<path d="M0,-13 l14,7 l-6,14 l-15,-4 z" fill="{STONE}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
CLOD = (f'<path d="M-20,4 q-6,-22 12,-24 q26,-6 28,16 q-2,20 -22,20 q-14,2 -18,-12 Z" '
        f'fill="{DIRT2}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
STAR = (f'<g stroke="{RED}" stroke-width="8" stroke-linecap="round">'
        + "".join(f'<path d="M{math.cos(a) * 26:.0f},{math.sin(a) * 26:.0f} L{math.cos(a) * 58:.0f},{math.sin(a) * 58:.0f}"/>'
                  for a in [-2.6, -2.0, -1.4, -0.8, -0.2]) + '</g>')
SPARK = (f'<g stroke="{RED}" stroke-width="7" stroke-linecap="round">'
         f'<path d="M0,-44 V-16 M0,16 V44 M-44,0 H-16 M16,0 H44 M-28,-28 l10,10 M28,28 l-10,-10"/></g>')
THUMB = (f'<g fill="{PAPER}" stroke="{INK}" stroke-width="9" stroke-linejoin="round" stroke-linecap="round">'
         f'<path d="M-6,-6 q-16,-46 4,-62 q20,-10 18,16 l-4,26 h26 q20,0 14,20 l-12,44 q-6,16 -24,16 h-30 z"/>'
         f'<path d="M-40,4 h34 v58 h-34 z"/></g>')
BASKET_D = (f'<path d="M-44,-12 q14,-40 46,-40 q34,0 46,40" fill="{DIRT2}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>')
BASKET = (f'<g transform="translate(0,26)"><path d="M-52,-6 h104 l-16,72 h-72 z" fill="{PACK}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
          f'<path d="M-52,-6 h104" stroke="{INK}" stroke-width="9"/><path d="M-34,10 h68 M-30,34 h60" stroke="#8a6740" stroke-width="5"/>'
          f'__MOUND__</g>')

SHOVEL = (f'<g transform="translate(0,44) rotate(-6)"><path d="M0,-84 V118" stroke="{WOOD}" stroke-width="9"/>'
          f'<path d="M-15,-84 h30" stroke="{WOOD}" stroke-width="9"/>'
          f'<path d="M-21,116 h42 l-5,46 q-16,18 -32,0 z" fill="{METAL}" stroke-width="7"/></g>')
CHISEL = (f'<g transform="translate(0,52) rotate(28)"><path d="M-17,-8 h34 l-6,74 q-11,14 -22,0 z" fill="{STONE}" stroke-width="7" stroke-linejoin="round"/>'
          f'<path d="M-9,18 l6,26" stroke="{SHADE}" stroke-width="5"/></g>')


# ============================================================ panacik (Bob a spol.)
def rig(p, hat=True, pack=True, prop="", tuft=False, helmet=False, coat=False, shirt=None, cap=False, held="",
        fedora=False, trench=False, miner=False):
    def limb(a, b, l1, l2, foot=False, extra="", upper=""):
        # upper = kus odevu na hornom clanku (stehno) - otaca sa s nim; nad nim ostane vidno lyta
        f = f'<path d="M0,{l2} h17"/>' if foot else ""
        return (f'<g id="{p}_{a}"><path d="M0,0 V{l1}"/>{upper}<g transform="translate(0,{l1})"><g id="{p}_{b}">'
                f'<path d="M0,0 V{l2}"/>{f}{extra}</g></g></g>')
    if hat:
        head_gear = (f'<g id="{p}_hat"><path d="M-34,-77 C-37,-124 37,-126 36,-79 Z" fill="{HAT}"/>'
                     f'<path d="M-33,-90 Q0,-83 36,-92" stroke="{RED}" stroke-width="9"/>'
                     f'<path d="M-58,-74 Q0,-64 62,-78" stroke-width="10"/></g>')
    elif helmet:   # potapacska prilba (vraky, voda)
        head_gear = (f'<g id="{p}_hat"><circle cx="10" cy="-44" r="54" fill="{METAL}" stroke-width="9"/>'
                     f'<circle cx="26" cy="-48" r="26" fill="{PAPER}" stroke-width="7"/>'
                     f'<path d="M-40,-4 h84" stroke-width="8"/><path d="M-44,-92 q40,-22 84,-4" stroke-width="7"/></g>')
    elif cap:   # namornik: plocha ciapka so sirmom
        head_gear = (f'<g id="{p}_hat"><path d="M-40,-80 q40,-30 80,-2 l2,16 h-84 z" fill="#f4f4f1" stroke-width="8" stroke-linejoin="round"/>'
                     f'<path d="M-44,-66 h90 q18,0 16,12 h-106 z" fill="#2f4a63" stroke-width="7" stroke-linejoin="round"/>'
                     f'<path d="M16,-72 h30" stroke="{RED}" stroke-width="7"/></g>')
    elif fedora:   # detektiv: fedora s preliacnutou korunou, tmava stuha, predny okraj sklopeny
        head_gear = (f'<g id="{p}_hat"><path d="M-31,-77 C-35,-116 -10,-124 1,-111 C12,-125 37,-116 34,-79 Z" '
                     f'fill="#6a625b" stroke-width="8" stroke-linejoin="round"/>'
                     f'<path d="M-32,-88 Q1,-81 35,-90" stroke="#2b2724" stroke-width="11"/>'
                     f'<path d="M-3,-110 q3,10 2,20" stroke-width="4"/>'
                     f'<path d="M-62,-72 Q-22,-86 4,-81 Q42,-80 72,-64" stroke-width="9" fill="none"/></g>')
    elif miner:    # jaskyniar: prilba s celovkou (lúč svetla dopredu)
        head_gear = (f'<g id="{p}_hat"><path d="M60,-98 L290,-150 L290,-40 Z" fill="#fff2b8" stroke="none" opacity="0.5"/>'
                     f'<path d="M-45,-72 Q-47,-130 0,-132 Q47,-130 45,-72 Z" fill="#f0b429" stroke-width="8" '
                     f'stroke-linejoin="round"/>'
                     f'<path d="M-54,-72 H56" stroke-width="10"/>'
                     f'<path d="M-4,-131 Q4,-104 0,-78" stroke="#c98f12" stroke-width="5" fill="none"/>'
                     f'<path d="M34,-114 h22 q9,0 9,9 v14 q0,9 -9,9 h-22 z" fill="{METAL}" stroke-width="6" stroke-linejoin="round"/>'
                     f'<circle cx="62" cy="-98" r="7" fill="#fff4c2" stroke-width="4"/></g>')
    elif tuft:
        head_gear = (f'<g id="{p}_hat"><path d="M-30,-68 l-12,-34 l22,14 l2,-30 l16,26 l14,-22 l2,32 l20,-16 l-8,32" stroke-width="8"/></g>')
    else:
        head_gear = f'<g id="{p}_hat"></g>'
    pack_svg = (f'<path d="M-5,-94 h-27 q-15,0 -15,15 v34 q0,15 15,15 h27 z" fill="{PACK}" stroke-width="7"/>'
                f'<path d="M-46,-66 h40" stroke-width="5"/>') if pack else ""
    skirt = f'<path d="M-30,-14 h60 l10,44 h-80 z" fill="{PACK}" stroke-width="7" stroke-linejoin="round"/>' if tuft else ""
    coat_back = coat_shirt = flap_b = flap_f = ""
    if coat:   # vedec: ROZOPNUTY biely plast v silulete tela, nie biela krabica.
        # Zadna polka trupu je pod rukami a batohom, predna nad telom; medzi nimi modra kosela
        # s kravatou (plast je zjavne rozopnuty). Spodne cipy su na stehnach - pri chodzi sa
        # rozchadzaju s nohami, v predklone a klaku idu so stehnom a neprekryju celu postavu.
        cw = "#fdfdfa"

        def tail():
            # vypln bez horneho obrysu (sev by inak presiel cez polku trupu) + obrys bokov a lemu
            return (f'<path d="M-19,-14 L19,-14 L27,44 Q0,50 -27,44 Z" fill="{cw}" stroke="none"/>'
                    f'<path d="M19,-6 L27,44 Q0,50 -27,44 L-19,-6" fill="none" stroke-width="7" stroke-linejoin="round"/>')
        coat_back = (f'<path d="M-4,-95 Q-22,-96 -30,-86 L-27,8 L-5,8 L-6,-60 Z" fill="{cw}" stroke-width="7" '
                     f'stroke-linejoin="round"/>'
                     f'<path d="M-4,-95 L-14,-66 L-6,-60" stroke-width="5" stroke-linejoin="round"/>')
        flap_b = flap_f = tail()
        skirt += (f'<path d="M-7,-94 h14 v100 h-14 z" fill="#cfe0ea" stroke="none"/>'
                  f'<path d="M0,-91 l-6,8 l6,40 l6,-40 z" fill="#a33b3b" stroke-width="3" stroke-linejoin="round"/>'
                  f'<path d="M4,-95 Q22,-96 30,-86 L27,8 L5,8 L6,-60 Z" fill="{cw}" stroke-width="7" '
                  f'stroke-linejoin="round"/>'
                  f'<path d="M4,-95 L14,-66 L6,-60" stroke-width="5" stroke-linejoin="round"/>'
                  f'<path d="M12,-50 h13 v12 h-13 z" fill="none" stroke-width="4" stroke-linejoin="round"/>'
                  f'<path d="M16,-50 v-10" stroke="#2f6fb0" stroke-width="4"/>')
    if trench:  # detektiv: bezovy trenckot po kolena, opasok, klopy, gombiky
        skirt += (f'<path d="M-36,-90 h72 l16,128 h-104 z" fill="#c9b38a" stroke-width="7" stroke-linejoin="round"/>'
                  f'<path d="M-39,-40 h80" stroke="#7d6646" stroke-width="8"/>'
                  f'<path d="M-24,-90 l20,36 l16,-36" fill="none" stroke-width="6" stroke-linejoin="round"/>'
                  f'<path d="M6,-54 V36" stroke-width="5"/>'
                  f'<circle cx="16" cy="-64" r="4" fill="{INK}" stroke="none"/><circle cx="16" cy="-18" r="4" fill="{INK}" stroke="none"/>')
    if cap:    # bretonske pruhy na trupe
        skirt += (f'<path d="M-30,-86 h60 l8,72 h-76 z" fill="{PAPER}" stroke-width="7" stroke-linejoin="round"/>'
                  + "".join(f'<path d="M{-29 + k},{-72 + k * 18} h{58 - k * 2}" stroke="#2f4a63" stroke-width="8"/>' for k in range(4)))
    if shirt:  # moderny navstevnik: tricko/bunda, aby sa odlisil od pravekeho davu
        # bez pevnych "rukavov" - staticke ciary na ramenach vyzerali ako druhy par ruk
        skirt += f'<path d="M-32,-88 h64 l10,74 h-84 z" fill="{shirt}" stroke-width="7" stroke-linejoin="round"/>'
    return f'''<g id="{p}_root" fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round">
<g id="{p}_body">
  {coat_back}{coat_shirt}
  <g transform="translate(0,-92)">{limb("aR", "aR2", 48, 46)}</g>
  {limb("lR", "lR2", 60, 60, True, upper=flap_b)}
  {pack_svg}
  <path d="M0,0 V-100"/>
  {limb("lL", "lL2", 60, 60, True, upper=flap_f)}
  {skirt}
  <g transform="translate(0,-100)"><g id="{p}_head">
    <circle cx="0" cy="-42" r="40" fill="{PAPER}"/>
    <circle id="{p}_eyeL" cx="11" cy="-50" r="0" fill="#fff" stroke-width="3.5"/><circle id="{p}_eyeR" cx="31" cy="-50" r="0" fill="#fff" stroke-width="3.5"/>
    <circle cx="12" cy="-50" r="4.6" fill="{INK}" stroke="none"/><circle cx="32" cy="-50" r="4.6" fill="{INK}" stroke="none"/>
    <path id="{p}_mouth" d="M10,-25 q11,7 22,-1" stroke-width="5"/>
    <ellipse id="{p}_mouthO" cx="23" cy="-22" rx="0" ry="0" fill="{INK}" stroke="none"/>
    {head_gear}
  </g></g>
  {held}
  <g transform="translate(0,-92)">{limb("aL", "aL2", 48, 46, False, prop)}</g>
</g></g>'''


# ============================================================ zlate 3D cislo / slovo
def num3d(pid, txt, size, depth=8, anchor="middle"):
    dx, dy = size * 0.0155, size * 0.0115      # tien doprava, len mierne dole (inak bodka cita ako ciarka)
    layers = ""
    for i in range(depth, 0, -1):
        col = INK if i == depth else GOLD_D
        layers += (f'<text class="hand n3t" data-layout-allow-overlap x="{i * dx:.1f}" y="{i * dy:.1f}" font-size="{size}" '
                   f'text-anchor="{anchor}" fill="{col}" stroke="{col}" '
                   f'stroke-width="{size * (0.052 if i == depth else 0.018):.1f}" stroke-linejoin="round">{txt}</text>')
    layers += (f'<text class="hand n3t" data-layout-allow-overlap x="0" y="0" font-size="{size}" text-anchor="{anchor}" '
               f'fill="{GOLD}" stroke="{INK}" stroke-width="{size * 0.048:.1f}" stroke-linejoin="round" '
               f'paint-order="stroke">{txt}</text>')
    return f'<g id="{pid}" class="n3">{layers}</g>'


# ============================================================ REKVIZITY
# kazda: dotyk so zemou y=0, centrovana na x=0, vracia (svg, width, height)
def _ret(svg, w, h):
    return svg, w, h


def p_stone(pid=""):
    b = (f'<path d="M-104,0 L-92,-96 Q-34,-140 38,-126 L98,-44 L94,0 Z" fill="{STONE}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-40,-104 l16,34 l-12,26 M34,-108 l12,40" stroke="{SHADE}" stroke-width="6" fill="none"/>')
    return _ret(b, 208, 140)


def p_pillar(pid=""):
    top, bot, hw, hh, sw = -900, 0, 300, 140, 150
    d = (f"M{-hw / 2},{top} Q0,{top - 8} {hw / 2},{top + 4} L{hw / 2 - 4},{top + hh} H{sw / 2} L{sw / 2 + 3},{bot} "
         f"H{-sw / 2} L{-sw / 2 + 3},{top + hh} H{-hw / 2 + 5} Z")
    hatch = "".join(f'<path d="M{sw / 2 - 34},{y} l24,-22" stroke="{SHADE}" stroke-width="5"/>'
                    for y in range(int(top + hh + 70), int(bot) - 20, 95))
    return _ret(f'<path d="{d}" fill="{STONE}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>{hatch}'
                f'<path d="M{-hw / 2 + 40},{top + 6} l14,30 l-10,22" stroke="{SHADE}" stroke-width="5" fill="none"/>', 300, 900)


def p_mountain(pid=""):
    b = (f'<path d="M-450,0 L-150,-420 L-40,-300 L90,-560 L300,-250 L450,0 Z" fill="{DIRT}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M90,-560 L28,-470 L64,-440 L108,-492 L150,-450 L196,-500 Z" fill="{PAPER}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<path d="M-150,-420 L-190,-350 M300,-250 L346,-176" stroke="{SHADE}" stroke-width="6" fill="none"/>')
    return _ret(b, 900, 560)


def p_cave(pid=""):
    b = (f'<path d="M-350,0 L-320,-360 Q-120,-620 110,-600 Q340,-580 360,-300 L370,0 Z" fill="{STONE}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-118,0 Q-124,-300 10,-320 Q142,-300 136,0 Z" fill="{INK}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-230,-330 l40,-46 M212,-300 l44,-40 M-60,-430 l34,-40" stroke="{SHADE}" stroke-width="6" fill="none"/>')
    return _ret(b, 740, 620)


def p_water(pid=""):
    b = (f'<path d="{ell(0, -60, 380, 118)}" fill="{WATER}" stroke="{INK}" stroke-width="9"/>'
         + "".join(f'<path d="M{-240 + i * 120},{-110 + (i % 3) * 44} q28,-16 56,0 q28,16 56,0" '
                   f'stroke="{PAPER}" stroke-width="7" fill="none" stroke-linecap="round"/>' for i in range(5)))
    return _ret(b, 760, 180)


def p_water_ice(pid=""):
    """Zamrznute jazero: nie modra mlaka, ale ladova platna s prasklinami a snehovym okrajom."""
    b = (f'<path d="{ell(0, -60, 380, 118)}" fill="#dcecf4" stroke="{INK}" stroke-width="9"/>'
         f'<path d="{ell(0, -60, 380, 118)}" fill="none" stroke="{PAPER}" stroke-width="16" opacity="0.55"/>'
         f'<path d="M-250,-96 l84,30 l-40,44 l96,26" fill="none" stroke="#9fc0d0" stroke-width="7" stroke-linecap="round"/>'
         f'<path d="M60,-120 l70,44 l-36,34" fill="none" stroke="#9fc0d0" stroke-width="7" stroke-linecap="round"/>'
         f'<path d="M-140,-18 l60,-26" fill="none" stroke="#9fc0d0" stroke-width="6" stroke-linecap="round"/>'
         + "".join(f'<path d="M{-260 + i * 130},{-142 + (i % 2) * 18} q26,-13 52,0" stroke="{PAPER}" '
                   f'stroke-width="9" fill="none" stroke-linecap="round"/>' for i in range(5)))
    return _ret(b, 760, 180)


def p_ship(pid=""):
    """Pociatok je v kyle (y=0), paluba na y=-160, staziar z paluby nahor.
    Predtym visel staziar 240 jednotiek nad trupom a lod vyzerala rozpadnuta."""
    b = (f'<path d="M-260,-160 H260 L196,0 H-196 Z" fill="{WOOD}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-260,-160 H260" stroke="{INK}" stroke-width="8" fill="none"/>'
         f'<path d="M-160,-70 h60 M60,-70 h60" stroke="#5c3d22" stroke-width="6" fill="none"/>'
         f'<path d="M0,-160 V-680" stroke="{WOOD}" stroke-width="13" fill="none" stroke-linecap="round"/>'
         f'<path d="M14,-660 Q180,-520 14,-380 Z" fill="{PAPER}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M-14,-560 Q-150,-470 -14,-390 Z" fill="{PAPER}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M260,-160 l84,-52" stroke="{WOOD}" stroke-width="11" fill="none" stroke-linecap="round"/>')
    return _ret(b, 520, 680)


def p_ship_stern(pid=""):
    """Pohlad od kormy - ina silueta tej istej lode, aby sa zaber neopakoval."""
    b = (f'<path d="M-150,0 H150 L108,-210 H-108 Z" fill="{WOOD}" stroke="{INK}" stroke-width="9" '
         f'stroke-linejoin="round" transform="scale(1,-1)"/>'
         f'<path d="M-108,210 H108" stroke="{INK}" stroke-width="8" fill="none"/>'
         f'<path d="M-96,150 h192" stroke="#5c3d22" stroke-width="7" fill="none"/>'
         f'<path d="M0,42 V-470" stroke="{WOOD}" stroke-width="13" fill="none" stroke-linecap="round"/>'
         f'<path d="M-118,-300 H118" stroke="{WOOD}" stroke-width="10" fill="none" stroke-linecap="round"/>'
         f'<path d="M-104,-292 Q0,-190 104,-292 Z" fill="{PAPER}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M-64,96 h40 M28,96 h40" stroke="#5c3d22" stroke-width="6" fill="none"/>')
    return _ret(b, 300, 480)


def p_ship_far(pid=""):
    """Silueta na horizonte - len obrys, ziadny detail."""
    b = (f'<path d="M-150,0 H150 L112,-92 H-112 Z" fill="none" stroke="{INK}" stroke-width="7" '
         f'stroke-linejoin="round" transform="scale(1,-1)"/>'
         f'<path d="M0,-92 V-330" stroke="{INK}" stroke-width="7" fill="none" stroke-linecap="round"/>'
         f'<path d="M8,-318 Q104,-232 8,-150 Z" fill="none" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>')
    return _ret(b, 300, 330)


def p_ship_deck(pid=""):
    """Palubny inventar: sud, zvinute lano, lampas. Zabradlie tu bolo predtym
    a cely zaber vyzeral ako stol."""
    barrel = (f'<path d="M-250,0 q-26,-90 0,-180 h150 q26,90 0,180 z" fill="{WOOD}" stroke="{INK}" '
              f'stroke-width="9" stroke-linejoin="round"/>'
              f'<path d="M-256,-58 q78,16 162,0 M-256,-124 q78,-16 162,0" stroke="#5c3d22" '
              f'stroke-width="8" fill="none"/>'
              f'<path d="{ell(-175, -180, 75, 22)}" fill="{PAPER}" stroke="{INK}" stroke-width="8"/>')
    rope = (f'<path d="{ell(40, -26, 96, 34)}" fill="none" stroke="#8a6a3a" stroke-width="10"/>'
            f'<path d="{ell(40, -34, 62, 22)}" fill="none" stroke="#8a6a3a" stroke-width="9"/>'
            f'<path d="{ell(40, -42, 30, 11)}" fill="none" stroke="#8a6a3a" stroke-width="8"/>')
    lamp = (f'<path d="M232,-40 h96 v-104 h-96 z" fill="{PAPER}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
            f'<path d="M222,-144 h116 M222,-40 h116" stroke="{INK}" stroke-width="8" fill="none"/>'
            f'<path d="M280,-144 v-34" stroke="{INK}" stroke-width="7" fill="none"/>'
            f'<path d="M264,-70 q16,-40 32,0 q-16,18 -32,0 z" fill="{SUN}" stroke="{INK}" stroke-width="6"/>')
    return _ret(barrel + rope + lamp, 620, 212)


def p_deck_wheel(pid=""):
    """Kormidlo na stojane."""
    R, r0 = 150, 46
    sp = ""
    for k in range(8):
        a = math.pi * 2 * k / 8
        cx, cy = math.cos(a), math.sin(a)
        sp += (f'<path d="M{cx * r0:.0f},{-186 + cy * r0:.0f} L{cx * (R + 44):.0f},{-186 + cy * (R + 44):.0f}" '
               f'stroke="{WOOD}" stroke-width="13" stroke-linecap="round" fill="none"/>')
    b = (f'<path d="M-30,0 h60 v-96 h-60 z" fill="{WOOD}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         f'{sp}<circle cx="0" cy="-186" r="{R}" fill="none" stroke="{WOOD}" stroke-width="16"/>'
         f'<circle cx="0" cy="-186" r="{r0}" fill="{PAPER}" stroke="{INK}" stroke-width="9"/>')
    return _ret(b, 390, 380)


def p_deck_anchor(pid=""):
    """Obrys atramentom, vypln kovova - bez obrysu splyva so svetlou palubou."""
    b = (f'<path d="M0,-40 V-300" stroke="{INK}" stroke-width="24" fill="none" stroke-linecap="round"/>'
         f'<path d="M0,-40 V-300" stroke="{METAL}" stroke-width="14" fill="none" stroke-linecap="round"/>'
         f'<path d="M-96,-236 H96" stroke="{INK}" stroke-width="22" fill="none" stroke-linecap="round"/>'
         f'<path d="M-96,-236 H96" stroke="{METAL}" stroke-width="12" fill="none" stroke-linecap="round"/>'
         f'<circle cx="0" cy="-332" r="44" fill="none" stroke="{INK}" stroke-width="22"/>'
         f'<circle cx="0" cy="-332" r="44" fill="none" stroke="{METAL}" stroke-width="12"/>'
         f'<path d="M-150,-110 q4,96 150,62 q146,34 150,-62" fill="none" stroke="{INK}" stroke-width="26" stroke-linecap="round"/>'
         f'<path d="M-150,-110 q4,96 150,62 q146,34 150,-62" fill="none" stroke="{METAL}" stroke-width="15" stroke-linecap="round"/>'
         f'<path d="M-150,-110 l-46,-34 l16,62 z M150,-110 l46,-34 l-16,62 z" fill="{METAL}" '
         f'stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>')
    return _ret(b, 400, 390)


def p_deck_bell(pid=""):
    b = (f'<path d="M-26,0 h52 v-44 h-52 z" fill="{WOOD}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M-34,-44 V-206 M34,-44 V-206 M-34,-206 H34" stroke="{WOOD}" stroke-width="13" '
         f'fill="none" stroke-linecap="round"/>'
         f'<path d="M-92,-104 q0,-108 92,-108 q92,0 92,108 q-46,22 -92,22 q-46,0 -92,-22 z" '
         f'fill="{BRONZE}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<path d="M-56,-172 q56,-26 112,0" fill="none" stroke="{INK}" stroke-width="7" opacity="0.6"/>'
         f'<path d="M0,-82 v30" stroke="{INK}" stroke-width="9" fill="none"/>'
         f'<circle cx="0" cy="-42" r="19" fill="{BRONZE}" stroke="{INK}" stroke-width="8"/>')
    return _ret(b, 250, 220)


def p_deck_nets(pid=""):
    """Zavesena siet s kosostvorcovym okom - splet ciar sa citala ako ulik."""
    L, R, TOP, SAG = -200, 200, -250, -70
    mesh = ""
    for k in range(-5, 6):
        x = k * 40
        u = abs(x) / 200.0
        yb = SAG + (TOP - SAG) * u * u
        mesh += (f'<path d="M{x + 60:.0f},{TOP} L{x - 40:.0f},{yb:.0f}" stroke="#8a6a3a" '
                 f'stroke-width="7" fill="none" stroke-linecap="round"/>'
                 f'<path d="M{x - 60:.0f},{TOP} L{x + 40:.0f},{yb:.0f}" stroke="#8a6a3a" '
                 f'stroke-width="7" fill="none" stroke-linecap="round"/>')
    b = (f'<path d="M{L},0 V{TOP - 18} M{R},0 V{TOP - 18}" stroke="{WOOD}" stroke-width="14" '
         f'fill="none" stroke-linecap="round"/>'
         f'<path d="M{L},{TOP} H{R}" stroke="{INK}" stroke-width="10" fill="none" stroke-linecap="round"/>'
         f'<g clip-path="none">{mesh}</g>'
         f'<path d="M{L},{TOP} Q0,{SAG + 60} {R},{TOP}" fill="none" stroke="{INK}" stroke-width="10" '
         f'stroke-linecap="round"/>')
    return _ret(b, 440, 270)


def p_wreck(pid=""):
    b = (f'<g transform="rotate(-14)"><path d="M-260,0 H210 L150,-170 H-190 Z" fill="{WOOD}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-190,-170 H10 M40,-170 H150" stroke="{INK}" stroke-width="8" fill="none"/>'
         f'<path d="M-60,-170 L-110,-420 l44,26 l16,-60" stroke="{WOOD}" stroke-width="12" fill="none" stroke-linecap="round"/>'
         f'<path d="M-150,-60 h50 M30,-70 h60" stroke="#5c3d22" stroke-width="6" fill="none"/>'
         f'<path d="M96,-40 l40,-40 M120,-120 l46,-20" stroke="{INK}" stroke-width="7" fill="none"/></g>')
    return _ret(b, 560, 440)


def p_gear(pid=""):
    r, tr, n = 130, 168, 12
    teeth = ""
    for k in range(n):
        a = 2 * math.pi * k / n
        c, s = math.cos(a), math.sin(a)
        pc, ps = math.cos(a + 0.19), math.sin(a + 0.19)
        mc, ms = math.cos(a - 0.19), math.sin(a - 0.19)
        teeth += (f'<path d="M{mc * r:.0f},{ms * r:.0f} L{mc * tr:.0f},{ms * tr:.0f} '
                  f'L{pc * tr:.0f},{ps * tr:.0f} L{pc * r:.0f},{ps * r:.0f}" fill="{BRONZE}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>')
    b = (f'<g transform="translate(0,-200)">{teeth}<circle r="{r}" fill="{BRONZE}" stroke="{INK}" stroke-width="9"/>'
         f'<circle r="44" fill="{PAPER}" stroke="{INK}" stroke-width="8"/>'
         + "".join(f'<path d="M{math.cos(a) * 44:.0f},{math.sin(a) * 44:.0f} L{math.cos(a) * 126:.0f},{math.sin(a) * 126:.0f}" '
                   f'stroke="{INK}" stroke-width="8" fill="none" stroke-linecap="round"/>'
                   for a in [k * math.pi / 3 for k in range(6)]) + '</g>')
    return _ret(b, 336, 368)


def p_machine(pid=""):
    def small_gear(cx, cy, r):
        t = "".join(f'<path d="M{math.cos(a) * r:.0f},{math.sin(a) * r:.0f} l{math.cos(a) * 16:.0f},{math.sin(a) * 16:.0f}" '
                    f'stroke="{INK}" stroke-width="9" stroke-linecap="round"/>' for a in [k * math.pi / 5 for k in range(10)])
        return (f'<g transform="translate({cx},{cy})">{t}<circle r="{r}" fill="{BRONZE}" stroke="{INK}" stroke-width="8"/>'
                f'<circle r="{r * 0.3:.0f}" fill="{PAPER}" stroke="{INK}" stroke-width="6"/></g>')
    b = (f'<path d="M-210,0 h420 v-380 h-420 z" fill="{WOOD}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<path d="M-172,-34 h344 v-312 h-344 z" fill="{PAPER}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         + small_gear(-76, -230, 74) + small_gear(58, -160, 56) + small_gear(120, -268, 44)
         + f'<path d="M210,-200 h64 q18,0 18,18 v44" stroke="{INK}" stroke-width="10" fill="none" stroke-linecap="round"/>'
           f'<circle cx="292" cy="-126" r="20" fill="{METAL}" stroke="{INK}" stroke-width="8"/>')
    return _ret(b, 500, 380)


def p_skull(pid=""):
    b = (f'<path d="M-92,-92 Q-96,-232 0,-234 Q96,-232 92,-92 Q92,-52 52,-44 L46,0 H-46 L-52,-44 Q-92,-52 -92,-92 Z" '
         f'fill="{PAPER}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<ellipse cx="-38" cy="-132" rx="28" ry="32" fill="{INK}"/><ellipse cx="38" cy="-132" rx="28" ry="32" fill="{INK}"/>'
         f'<path d="M0,-96 l-18,30 h36 z" fill="{INK}"/>'
         f'<path d="M-30,-44 v40 M0,-44 v40 M30,-44 v40" stroke="{INK}" stroke-width="7" fill="none"/>')
    return _ret(b, 192, 240)


def p_bones(pid=""):
    b = (f'<g transform="translate(-70,0) scale(0.8)">{p_skull()[0]}</g>'
         + bone(110, -30, -18, 1.3) + bone(146, -52, 16, 1.15) + bone(56, -14, 8, 1.0))
    return _ret(b, 380, 210)


def p_door(pid=""):
    b = (f'<path d="M-190,0 v-420 q0,-130 190,-130 q190,0 190,130 V0 Z" fill="{STONE}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<path d="M-110,0 v-400 q0,-84 110,-84 q110,0 110,84 V0 Z" fill="{INK}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-154,-170 h-1 M-150,-96 l34,-30 M150,-96 l-34,-30 M-150,-300 l34,-30 M150,-300 l-34,-30" '
         f'stroke="{SHADE}" stroke-width="6" fill="none"/>')
    return _ret(b, 380, 550)


def p_chest(pid=""):
    b = (f'<path d="M-180,0 h360 v-190 h-360 z" fill="{WOOD}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<path d="M-180,-190 q0,-120 180,-120 q180,0 180,120 z" fill="#8a5c33" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<path d="M-70,-310 v310 M70,-310 v310" stroke="{METAL}" stroke-width="12" fill="none"/>'
         f'<path d="M-30,-140 h60 v72 h-60 z" fill="{SUN}" stroke="{INK}" stroke-width="8"/>'
         f'<circle cx="0" cy="-104" r="11" fill="{INK}"/>')
    return _ret(b, 360, 310)


def p_ruin(pid=""):
    col = (f'<path d="M-24,0 v-260 h48 V0 Z" fill="{STONE}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
           f'<path d="M-40,-260 h80 v-34 h-80 z" fill="{STONE}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>')
    b = (f'<path d="M-320,0 v-300 h150 v-90 h140 v300 h130 V0 Z" fill="{STONE}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-250,-60 h60 M-150,-190 h70 M40,-120 h64" stroke="{SHADE}" stroke-width="6" fill="none"/>'
         f'<g transform="translate(-390,0) scale(0.9)">{col}</g><g transform="translate(400,0) scale(0.72)">{col}</g>')
    return _ret(b, 880, 400)


def p_map(pid=""):
    b = (f'<path d="M-200,-40 h400 v-260 h-400 z" fill="{PAPER}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-200,-300 q0,-34 -30,-34 v300 q30,0 30,-34 Z M200,-300 q0,-34 30,-34 v300 q-30,0 -30,-34 Z" '
         f'fill="#e8dfc4" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         f'<path d="M-140,-250 q60,-24 120,6 q60,30 130,-8" stroke="{SHADE}" stroke-width="7" fill="none" stroke-linecap="round"/>'
         f'<path d="M-150,-170 q70,26 150,-10 q60,-28 130,10" stroke="{SHADE}" stroke-width="6" fill="none" stroke-linecap="round" stroke-dasharray="20 18"/>'
         f'<path d="M64,-140 l52,52 M116,-140 l-52,52" stroke="{RED}" stroke-width="11" stroke-linecap="round" fill="none"/>')
    return _ret(b, 460, 340)


def p_statue(pid=""):
    b = (f'<path d="M-130,0 h260 v-56 h-260 z" fill="{STONE}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-74,-56 q10,-250 -2,-330 q-16,-96 76,-96 q92,0 76,96 q-12,80 -2,330 Z" fill="{STONE}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<circle cx="0" cy="-520" r="70" fill="{STONE}" stroke="{INK}" stroke-width="9"/>'
         f'<path d="M-26,-534 h22 M8,-534 h22 M-16,-486 q18,10 34,0" stroke="{INK}" stroke-width="7" fill="none" stroke-linecap="round"/>'
         f'<path d="M-70,-360 l-60,80 M70,-360 l60,80" stroke="{STONE}" stroke-width="30" fill="none" stroke-linecap="round"/>'
         f'<path d="M-70,-360 l-60,80 M70,-360 l60,80" stroke="{INK}" stroke-width="8" fill="none" stroke-linecap="round" opacity="0.45"/>')
    return _ret(b, 280, 600)


def p_tunnel(pid=""):
    b = (f'<path d="M-300,0 v-260 q0,-260 300,-260 q300,0 300,260 V0 Z" fill="{STONE}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<path d="M-186,0 v-250 q0,-170 186,-170 q186,0 186,170 V0 Z" fill="{INK}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-250,-360 l46,-40 M250,-360 l-46,-40" stroke="{SHADE}" stroke-width="6" fill="none"/>'
         f'<path d="M-120,0 l40,-150 M120,0 l-40,-150" stroke="{WOOD}" stroke-width="9" fill="none"/>'
         + "".join(f'<path d="M{-110 + i * 6},{-16 - i * 26} h{220 - i * 12}" stroke="{WOOD}" stroke-width="7" fill="none"/>' for i in range(5)))
    return _ret(b, 600, 520)


def p_tree(pid=""):
    b = (f'<path d="M0,0 C-14,-140 18,-250 4,-330" stroke="{WOOD}" stroke-width="22" fill="none" stroke-linecap="round"/>'
         f'<path d="M4,-230 l-70,-56 M4,-280 l66,-52" stroke="{WOOD}" stroke-width="14" fill="none" stroke-linecap="round"/>'
         f'<path d="M-150,-380 q-40,-96 46,-120 q10,-96 110,-84 q100,-14 104,84 q76,28 32,120 Z" '
         f'fill="{LEAF}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>')
    return _ret(b, 320, 500)


def p_forest(pid=""):
    t = p_tree()[0]
    b = (f'<g transform="translate(-230,0) scale(0.78)">{t}</g><g transform="translate(220,10) scale(0.9)">{t}</g>'
         f'<g transform="translate(0,0)">{t}</g>')
    return _ret(b, 760, 500)


def p_car(pid=""):
    b = (f'<path d="M-230,-60 h460 v-80 q0,-30 -34,-30 h-82 l-64,-84 h-140 l-52,84 h-54 q-34,0 -34,30 z" '
         f'fill="{PACK}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-104,-170 h84 v84 h-120 z M20,-170 h72 l58,84 h-130 z" fill="{PAPER}" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
         f'<circle cx="-134" cy="-56" r="58" fill="{INK}"/><circle cx="-134" cy="-56" r="24" fill="{PAPER}" stroke="{INK}" stroke-width="7"/>'
         f'<circle cx="140" cy="-56" r="58" fill="{INK}"/><circle cx="140" cy="-56" r="24" fill="{PAPER}" stroke="{INK}" stroke-width="7"/>')
    return _ret(b, 480, 254)


def p_tablet(pid=""):
    b = (f'<path d="M-140,0 h280 v-330 q0,-70 -140,-70 q-140,0 -140,70 z" fill="{STONE}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         + "".join(f'<path d="M-88,{-78 - i * 58} q30,-16 60,0 t60,0 t34,-4" stroke="{SHADE}" stroke-width="8" fill="none" stroke-linecap="round"/>'
                   for i in range(5)))
    return _ret(b, 280, 400)


def p_tower(pid=""):
    b = (f'<path d="M-110,0 L-84,-700 h168 L110,0 Z" fill="{STONE}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<path d="M-118,-700 h236 v-56 h-236 z" fill="{STONE}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         + "".join(f'<path d="M{-118 + i * 60},-756 v-44 h40 v44" fill="{STONE}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>' for i in range(4))
         + "".join(f'<path d="M{-30},{-180 - i * 180} h60 v-90 q0,-34 -30,-34 q-30,0 -30,34 z" fill="{INK}" stroke="{INK}" stroke-width="7"/>' for i in range(3)))
    return _ret(b, 260, 800)


def p_coin(pid=""):
    b = (f'<g transform="translate(0,-150)"><circle r="146" fill="{BRONZE}" stroke="{INK}" stroke-width="10"/>'
         f'<circle r="112" fill="none" stroke="{INK}" stroke-width="6" stroke-dasharray="16 14"/>'
         f'<path d="M-46,52 q46,-160 92,0" stroke="{INK}" stroke-width="10" fill="none" stroke-linecap="round"/>'
         f'<circle cx="0" cy="-30" r="34" fill="{PAPER}" stroke="{INK}" stroke-width="8"/></g>')
    return _ret(b, 300, 300)


def p_meteor(pid=""):
    """Horiaci kamen z neba: kamen prave dopadol (spodok na y=0), za nim sikmo hore ohniva stopa
    a plamene, ktore sa trhaju proti smeru letu."""
    fl1, fl2 = "#f39c34", "#ffd45a"
    trail = (f'<path d="M30,-156 L468,-566 L522,-502 L98,-62 Z" fill="#fbe3a0" stroke="none" opacity="0.85"/>'
             f'<path d="M58,-126 L486,-530" stroke="{fl2}" stroke-width="18" stroke-linecap="round" fill="none"/>'
             f'<path d="M94,-86 L430,-396 M118,-148 L372,-386 M160,-74 L330,-230" stroke="{fl1}" stroke-width="9" '
             f'stroke-linecap="round" fill="none"/>')
    flames = (f'<path d="M-46,-146 Q-8,-212 66,-214 Q40,-188 62,-172 Q110,-230 176,-218 Q140,-190 150,-164 '
              f'Q190,-182 218,-214 Q226,-124 132,-70 Q96,-40 56,-44 Z" fill="{fl1}" stroke="{INK}" stroke-width="7" '
              f'stroke-linejoin="round"/>'
              f'<path d="M0,-150 Q40,-190 96,-186 Q76,-160 100,-144 Q140,-176 170,-170 Q150,-120 96,-92 Q50,-80 20,-96 Z" '
              f'fill="{fl2}" stroke="none"/>')
    rock = (f'<path d="M-106,-14 Q-124,-98 -54,-142 Q14,-176 76,-126 Q124,-80 100,-16 Q62,4 -6,2 Q-76,4 -106,-14 Z" '
            f'fill="#8f8578" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
            f'<path d="M-62,-104 l30,26 l-10,32 M24,-124 l-8,42 l36,20 M-20,-40 l40,6" stroke="{fl1}" stroke-width="7" '
            f'fill="none" stroke-linecap="round"/>')
    dust = (f'<path d="M-176,0 q34,-34 76,-10 M108,-4 q42,-32 90,-2 M-150,-40 l-24,-18 M150,-44 l26,-22" '
            f'stroke="{DIRT2}" stroke-width="7" fill="none" stroke-linecap="round"/>')
    return _ret(trail + flames + rock + dust, 700, 566)


def p_book(pid=""):
    """Stara otvorena kniha s neznamym pismom (Voynich): kozena vazba, strany do oblúka, riadky cudzich
    znakov na lavej strane, kresba rastliny s korenmi na pravej."""
    pg, ink2 = "#f3e9cf", "#5a4a3a"
    cover = (f'<path d="M-240,-4 Q-120,-30 0,-14 Q120,-30 240,-4 L244,-26 Q120,-54 0,-38 Q-120,-54 -244,-26 Z" '
             f'fill="#7a4a2a" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>')
    lp = (f'<path d="M-228,-28 Q-226,-142 -216,-184 Q-110,-206 -4,-170 L0,-42 Q-112,-66 -228,-28 Z" '
          f'fill="{pg}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>')
    rp = (f'<path d="M228,-28 Q226,-142 216,-184 Q110,-206 4,-170 L0,-42 Q112,-66 228,-28 Z" '
          f'fill="{pg}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>')
    rows = ""
    for i in range(6):
        y = -160 + i * 21
        x = -200 + (i % 2) * 6
        seg = ""
        while x < -30:
            seg += f"M{x},{y + (x + 200) * 0.06:.0f} q5,-10 10,0 q4,8 9,-3 "
            x += 24 + (x % 3) * 4
        rows += seg
    glyphs = f'<path d="{rows}" stroke="{ink2}" stroke-width="4" fill="none" stroke-linecap="round"/>'
    if BOOK_STYLE != "cipher":
        # dennik / zapisnik: linajkove riadky s pismom na oboch stranach, na lavej okraj s datumami
        def page(sx):
            out = ""
            for i in range(6):
                y = -160 + i * 21
                x0, x1 = (-206, -24) if sx < 0 else (24, 206)
                out += (f'<path d="M{x0},{y + 6 + (abs(x0) - 24) * 0.0:.0f} H{x1}" stroke="#c9bfa3" stroke-width="2"/>'
                        f'<path d="M{x0 + 30 if sx < 0 else x0 + 8},{y + 2} '
                        + " ".join(f"q6,-8 12,0 q6,6 12,-2" for _ in range(5 if sx < 0 else 6))
                        + f'" fill="none" stroke="{ink2}" stroke-width="3" stroke-linecap="round"/>')
            if sx < 0:
                out += f'<path d="M-176,-172 V-44" stroke="#b5463a" stroke-width="2"/>'
            return out
        return _ret(cover + lp + rp + page(-1) + page(1), 488, 210)
    plant = (f'<path d="M122,-66 V-150" stroke="#4f8a3c" stroke-width="6" fill="none"/>'
             f'<path d="M122,-110 q-34,-20 -40,-2 q18,14 40,2 M122,-128 q34,-22 42,-4 q-18,14 -42,4 '
             f'M122,-92 q30,-14 36,2 q-16,10 -36,-2" fill="#8fbf6a" stroke="{INK}" stroke-width="4"/>'
             f'<circle cx="122" cy="-158" r="11" fill="#d98c8c" stroke="{INK}" stroke-width="4"/>'
             f'<path d="M122,-66 l-18,14 M122,-66 l4,18 M122,-66 l20,12" stroke="{WOOD}" stroke-width="4" fill="none"/>'
             f'<path d="M40,-150 q6,-9 12,0 q5,8 10,-2 M40,-130 q6,-9 12,0 M176,-160 q6,-9 12,0 q5,8 10,-2" '
             f'stroke="{ink2}" stroke-width="4" fill="none" stroke-linecap="round"/>')
    return _ret(cover + lp + rp + glyphs + plant, 488, 210)


def p_fallen_tree(pid=""):
    """Vyvrateny strom lezi na zemi (Tunguska): koren s hlinou trci hore vlavo, kmen sa zuzuje
    doprava, zlomene konare trcia sikmo hore, spic odlomeny."""
    trunk = (f'<path d="M-330,2 L-330,-66 Q60,-52 452,-30 L470,-44 L474,-20 L462,-6 Q60,-2 -330,2 Z" '
             f'fill="{WOOD}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
             f'<path d="M-280,-40 Q40,-36 380,-22 M-200,-20 Q60,-18 300,-12" stroke="#5c3d22" stroke-width="5" '
             f'fill="none" stroke-dasharray="40 30"/>')
    stubs = "".join(f'<path d="M{x},{y} l{dx},{dy}" stroke="{INK}" stroke-width="17" stroke-linecap="round"/>'
                    f'<path d="M{x},{y} l{dx},{dy}" stroke="{WOOD}" stroke-width="9" stroke-linecap="round"/>'
                    for x, y, dx, dy in ((-90, -58, 40, -70), (80, -48, 50, -60), (230, -40, 34, -50), (330, -34, 30, -34)))
    plate = (f'<path d="M-392,4 Q-430,-110 -396,-190 Q-350,-262 -300,-196 Q-266,-120 -290,4 Z" fill="{DIRT2}" '
             f'stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
             f'<path d="M-366,-200 l-18,-40 M-326,-214 l10,-44 M-296,-172 l34,-22 M-408,-120 l-30,-10 '
             f'M-300,-110 l34,4 M-390,-60 l-26,14" stroke="{WOOD}" stroke-width="8" stroke-linecap="round" fill="none"/>'
             f'<path d="M-372,-150 q20,-10 34,8 M-360,-90 q18,-6 30,10" stroke="#8a6e45" stroke-width="5" fill="none"/>')
    return _ret(trunk + stubs + plate, 900, 262)


def p_object(pid=""):
    """Neutralny fallback - debna s otaznikom."""
    b = (f'<path d="M-150,0 h300 v-250 q0,-40 -40,-40 h-220 q-40,0 -40,40 z" fill="{PACK}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<path d="M-150,-190 h300 M-40,0 v-290 M60,0 v-290" stroke="#8a6740" stroke-width="7" fill="none"/>'
         f'<path d="M-96,-96 h192" stroke="#8a6740" stroke-width="7" fill="none"/>')
    return _ret(b, 300, 290)


BOOK_STYLE = "cipher"         # "log" = dennik (pripravene, zatial nezapojene v build_spec)

PROPS = {
    "stone": p_stone, "pillar": p_pillar, "mountain": p_mountain, "cave": p_cave, "water": p_water,
    "water_ice": p_water_ice,
    "ship": p_ship, "ship_stern": p_ship_stern, "ship_far": p_ship_far,
    "deck_wheel": p_deck_wheel, "deck_anchor": p_deck_anchor,
    "deck_bell": p_deck_bell, "deck_nets": p_deck_nets,
    "ship_deck": p_ship_deck, "wreck": p_wreck, "gear": p_gear, "machine": p_machine, "skull": p_skull,
    "bones": p_bones, "door": p_door, "chest": p_chest, "ruin": p_ruin, "map": p_map,
    "statue": p_statue, "tunnel": p_tunnel, "tree": p_tree, "forest": p_forest, "car": p_car,
    "tablet": p_tablet, "tower": p_tower, "coin": p_coin, "object": p_object,
    "meteor": p_meteor, "book": p_book, "fallen_tree": p_fallen_tree,
}

# Vyska postavy pri mierke 1 (chodidla y=0, vrch klobuka ~ -310).
BOB_H = 310.0

# Cielova velkost kazdej rekvizity ako NASOBOK VYSKY POSTAVY.
# ("h", r) = vyska rekvizity je r * vyska Boba;  ("w", r) = to iste pre sirku
# (ploche veci ako jazero alebo ruina sa merajú na sirku, nie na vysku).
# Bez tohto pravidla vychadzala lebka dvakrat vyssia nez clovek.
SIZE = {
    # mensie nez Bob (0,2-0,6)
    # lebka ~ velkost hlavy postavy (hlava ma ~0,26 vysky); kopa kosti = lebka + tri kosti
    # male artefakty v pravdivom pomere k postave (Bob ~1,75 m): 13 cm koliesko ~ dlan, nie hlava.
    # Blizko ich ukaze kamera (frame_z), nie zvacsenie.
    "coin": ("h", 0.10), "skull": ("h", 0.30), "bones": ("w", 0.62),
    "map": ("h", 0.30), "gear": ("h", 0.10), "chest": ("h", 0.35),
    "object": ("h", 0.35), "stone": ("h", 0.58), "tablet": ("h", 0.40),
    "deck_bell": ("h", 0.50), "deck_nets": ("w", 1.10), "deck_anchor": ("h", 0.65),
    "deck_wheel": ("h", 0.72), "ship_deck": ("w", 1.60),
    # okolo postavy
    "machine": ("h", 0.30), "car": ("h", 1.20), "vitrine": ("h", 1.40),
    "door": ("h", 1.50), "statue": ("h", 1.70), "wreck": ("w", 2.20),
    "ship_far": ("h", 1.00),
    # vyrazne vacsie nez Bob
    "tunnel": ("h", 2.30), "cave": ("h", 2.40), "ship_stern": ("h", 2.40),
    "tree": ("h", 2.60), "pillar": ("h", 2.70), "ship": ("h", 2.80),
    "tower": ("h", 3.20), "mountain": ("h", 3.60),
    # ploche a siroke: mieru drzi sirka
    "ruin": ("w", 3.00), "forest": ("w", 3.20),
    "water": ("w", 3.20), "water_ice": ("w", 3.20),
    # nove: kniha (Voynich 23,5 x 16 cm -> otvorena ~32 cm), meteorit (kamen ~0,5 m + stopa),
    # vyvrateny strom (~9 m smrek/borovica lezi na zemi)
    "book": ("w", 0.18), "meteor": ("h", 1.00), "fallen_tree": ("w", 5.00),
}


def human_scale(key, pw, ph, bob_s=1.0):
    """Mierka rekvizity odvodena od vysky postavy v danom zabere."""
    mode, r = SIZE.get(key, ("h", 0.80))
    target = r * BOB_H * float(bob_s or 1.0)
    base = ph if mode == "h" else pw
    return target / max(1.0, base)


# Varianty pohladu na tu istu vec. Pri opakovani rekvizity sa striedaju, aby
# nebola 11x rovnaka silueta na rovnakom mieste.
# Striedaju sa len pohlady na CELY objekt. `ship_deck` je detail paluby a prideluje
# ho build_spec podla typu zaberu - keby sa striedal tu, vysiel by sud namiesto lode
# v zabere, ktory ma lod prave odhalit.
VIEWS = {"ship": ("ship", "ship_stern")}


def prop_view(key, i=0):
    v = VIEWS.get(key)
    return key if not v else v[i % len(v)]


# ------------------------------------------------------------------ vyber rekvizity z textu vety
# poradie ROZHODUJE: prva zhoda vyhrava, preto specifickejsie slova hore
KEYWORDS = [
    # bezne predmety z pribehov (props_story) - konkretnejsie nez vseobecne kluce nizsie
    ("clock", ("clock", "clocks", "timepiece")),
    ("bed", ("bed", "beds", "bunk", "bunks", "mattress", "bedding")),
    ("chair", ("chair", "chairs", "stool", "stools")),
    ("table", ("table", "tables", "desk", "desks")),
    ("meal", ("meal", "meals", "dinner", "supper", "breakfast", "lunch", "food", "plate", "plates", "dishes")),
    ("lantern", ("lantern", "lanterns", "lamp", "lamps", "kerosene")),
    ("coat", ("coat", "coats", "oilskin", "oilskins", "raincoat", "jacket", "jackets", "cloak")),
    ("bottle", ("bottle", "bottles", "flask", "flasks")),
    ("letter", ("letter", "letters", "note", "notes", "telegram", "envelope")),
    ("footprints", ("footprint", "footprints", "footsteps", "tracks", "prints")),
    ("rope", ("rope", "ropes", "rigging", "noose")),
    ("candle", ("candle", "candles")),
    ("boot", ("boot", "boots", "shoe", "shoes")),
    ("key", ("key", "keys", "keyhole")),
    ("radio", ("radio", "radios", "transmitter", "wireless")),
    ("ladder", ("ladder", "ladders")),
    ("tent", ("tent", "tents", "campsite")),
    ("window", ("window", "windows", "windowsill")),
    ("fireplace", ("fireplace", "fireplaces", "hearth", "stove")),
    ("boat", ("boat", "boats", "rowboat", "dinghy", "lifeboat", "lifeboats", "canoe", "skiff")),
    ("meteor", ("meteor", "meteors", "meteorite", "meteorites", "comet", "asteroid", "fireball", "airburst", "bolide")),
    ("gear", ("gear", "cog", "teeth", "tooth", "clockwork", "dial", "mesh")),
    ("machine", ("mechanism", "machine", "device", "computer", "engine", "instrument", "apparatus")),
    ("wreck", ("wreck", "shipwreck", "sunken", "sank", "sunk", "capsized")),
    ("ship", ("ship", "vessel", "cargo", "sail", "sails", "hull", "deck", "fleet", "galley", "steamer")),
    ("wave", ("wave", "waves", "tsunami", "swell", "breaker", "breakers")),
    ("water", ("lake", "water", "sea", "ocean", "river", "pond", "dive", "diver", "divers", "underwater", "flood")),
    ("skull", ("skull", "skulls", "cranium")),
    ("body", ("corpse", "corpses", "bodies", "body")),
    ("bones", ("bone", "bones", "skeleton", "skeletons", "remains")),
    ("cave", ("cave", "cavern", "grotto", "chamber", "shaft")),
    ("tunnel", ("tunnel", "passage", "corridor", "mine")),
    ("door", ("door", "doorway", "gate", "entrance", "portal", "threshold", "seal")),
    ("crate", ("crate", "crates", "box", "boxes")),
    ("chest", ("chest", "case", "container", "coffin", "casket")),
    ("book", ("book", "books", "manuscript", "manuscripts", "codex", "volume", "pages", "page", "cipher", "vellum",
              "logbook", "journal", "diary", "ledger")),
    ("map", ("map", "chart", "document", "letter", "scroll")),
    ("tablet", ("tablet", "inscription", "carving", "carvings", "script", "writing", "symbols", "glyphs", "text")),
    ("coin", ("coin", "coins", "medallion", "disc", "disk", "artifact", "artefact", "relic", "treasure")),
    ("statue", ("statue", "statues", "idol", "figure", "figurine", "sculpture", "head", "moai")),
    ("pillar", ("pillar", "pillars", "monolith", "obelisk", "column", "columns", "megalith", "standing")),
    ("ruin", ("ruin", "ruins", "temple", "city", "settlement", "village", "palace", "wall", "walls", "building")),
    ("lighthouse", ("lighthouse", "lighthouses")),
    ("tower", ("tower", "spire", "minaret")),
    ("mountain", ("mountain", "peak", "summit", "cliff", "volcano", "plateau", "hill", "hills", "slope")),
    ("fallen_tree", ("flattened", "uprooted", "felled", "toppled")),
    ("forest", ("forest", "jungle", "woods", "trees")),
    ("tree", ("tree", "trunk", "branch")),
    ("car", ("car", "truck", "vehicle", "train", "plane", "aircraft")),
    ("stone", ("stone", "stones", "rock", "rocks", "boulder", "slab", "granite", "limestone")),
]


# "remains" je podstatne meno (kosti) len ked pred nim stoji urcovac/pridavne meno:
# "human remains", "the remains". Inak je to sloveso: "cargo remains sealed",
# "the abandonment remains unexplained" - inak z kazdej zahady vyjde kostra.
_REM_NOUN_BEFORE = ("the", "human", "humans", "skeletal", "their", "his", "her", "its", "our",
                    "these", "those", "some", "more", "other", "charred", "mummified", "buried",
                    "ancient", "scattered", "preserved", "frozen", "found", "no", "any", "few")


def rank_props(text):
    """Vsetky rekvizity, na ktore veta sedi, v poradi specifickosti."""
    low = " " + "".join(c.lower() if c.isalnum() or c.isspace() else " " for c in text) + " "
    tok = low.split()
    for i, w in enumerate(tok):
        if w == "remains" and (i == 0 or tok[i - 1] not in _REM_NOUN_BEFORE):
            tok[i] = "__rem__"
    low = " " + " ".join(tok) + " "
    out = []
    for key, words in KEYWORDS:
        if any(f" {w} " in low for w in words) and key not in out:
            out.append(key)
    return out


def pick_prop(text, fallback="object"):
    r = rank_props(text)
    return r[0] if r else fallback


# Rekvizity, ktore su v podstate ta ista vec v inom stave - striedat ich nema zmysel
# a niekedy si priamo odporuju (lod najdena neporusena vs. vrak).
_FAMILY = (("ship", "wreck"), ("stone", "pillar"), ("bones", "skull"), ("cave", "tunnel"),
           ("forest", "tree", "fallen_tree"), ("ruin", "tower"), ("machine", "gear"), ("book", "map"))


def _same_family(a, b):
    return any(a in f and b in f for f in _FAMILY)


def pick_prop_seq(text, topic_text="", prev=None, fallback="object"):
    """Ako pick_prop, ale nezopakuje rekvizitu z predchadzajuceho zaberu, ak existuje ina zhoda.
    Bez toho vyjde napr. Roopkund ako 8x 'water' za sebou = vizualna jednotvarnost."""
    r = rank_props(text)
    for k in r:
        if k != prev:
            return k
    if r:
        return r[0]
    t = rank_props(topic_text)
    if not t:
        return fallback
    # Veta sama nepomenuva nic - drz sa hlavnej rekvizity temy. Striedat smie len
    # rekvizitu z inej rodiny (Roopkund: voda/kosti), nie variant toho isteho
    # (lod/vrak), inak by v pribehu o neporusenej lodi zrazu plavali kosti.
    for k in t[1:]:
        if k != prev and not _same_family(k, t[0]):
            return k
    return t[0]


def prop_svg(pid, key, extra_cls=""):
    fn = PROPS.get(key, p_object)
    body, w, h = fn(pid)
    return f'<g id="{pid}" class="prop {extra_cls}">{body}</g>', w, h


def prop_size(key):
    _, w, h = PROPS.get(key, p_object)("")
    return w, h


# bezne predmety z pribehov - registracia do PROPS/SIZE (musi byt az na konci, props_story importuje props)
import props_story  # noqa: E402,F401
