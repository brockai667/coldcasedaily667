# -*- coding: utf-8 -*-
"""Faza 2: svety podla spec["world"], varianty hrdinu podla spec["hero"],
porovnavacie objekty pre timeline_compare podla spec["vs"] a vynimky vo vybere rekvizit.

Vsetko kresli rovnakou linkou ako zvysok stavebnice (props.py).
"""
import math
import re

import look as _look
import worlds_ext as _X
from props import (DIRT, DIRT2, GH, INK, LEAF, PAPER, SHADE, STONE, SUN, WATER, WOOD,
                   PROPS, ell, p_coin, p_ship, p_ship_far, rig)

# ============================================================ HRDINA
HERO_STYLE = {
    "archaeologist": dict(hat=True, pack=True),
    "diver": dict(hat=False, pack=True, helmet=True),
    "ranger": dict(hat=True, pack=True),
    "scientist": dict(hat=False, pack=True, coat=True),
    "sailor": dict(hat=False, pack=False, cap=True),
    # kriminalne zahady: fedora + trenckot, bez batohu
    "detective": dict(hat=False, pack=False, fedora=True, trench=True),
    # jaskyne: prilba s celovkou + batoh
    "caver": dict(hat=False, pack=True, miner=True),
}


def hero_rig(p, hero="archaeologist", prop=""):
    kw = dict(HERO_STYLE.get((hero or "").strip().lower(), HERO_STYLE["archaeologist"]))
    kw["prop"] = prop
    return rig(p, **kw)


# ============================================================ POROVNAVACIE OBJEKTY (pole "vs")
def v_pyramid(label=""):
    base, apex = 0, -580
    b = (f'<path d="M-370,{base} L0,{apex} L370,{base} Z" fill="{SUN}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<path d="M0,{apex} V{base}" stroke="{INK}" stroke-width="7" opacity="0.5" fill="none"/>'
         + "".join(f'<path d="M{-370 + 370 * k / 6:.0f},{base + apex * k / 6:.0f} H{370 - 370 * k / 6:.0f}" '
                   f'stroke="{INK}" stroke-width="5" opacity="0.4" fill="none"/>' for k in range(1, 6))
         + f'<path d="M-50,{base} h100 v-90 h-100 z" fill="{DIRT}" stroke="{INK}" stroke-width="7"/>')
    return b, 740, 580


def v_trilithon(label=""):
    post = f'<path d="M-46,0 v-430 h92 V0 Z" fill="{STONE}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
    b = (f'<g transform="translate(-170,0)">{post}</g><g transform="translate(170,0)">{post}</g>'
         f'<path d="M-250,-430 h500 v-90 h-500 z" fill="{STONE}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<path d="M-200,-300 l30,-40 M190,-260 l30,-40" stroke="{SHADE}" stroke-width="6" fill="none"/>')
    return b, 500, 520


def v_clock(label=""):
    r = 190
    ticks = "".join(f'<path d="M{math.cos(a) * (r - 34):.0f},{math.sin(a) * (r - 34):.0f} '
                    f'L{math.cos(a) * (r - 8):.0f},{math.sin(a) * (r - 8):.0f}"/>' for a in [k * math.pi / 6 for k in range(12)])
    b = (f'<path d="M-40,0 h80 v-90 h-80 z" fill="{WOOD}" stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>'
         f'<g transform="translate(0,-300)"><circle r="{r}" fill="{PAPER}" stroke="{INK}" stroke-width="11"/>'
         f'<g stroke="{INK}" stroke-width="8" stroke-linecap="round">{ticks}</g>'
         f'<path d="M0,0 V-110 M0,0 L86,52" stroke="{INK}" stroke-width="12" stroke-linecap="round" fill="none"/>'
         f'<circle r="16" fill="{INK}"/></g>')
    return b, 380, 490


def v_column(label=""):
    flut = "".join(f'<path d="M{-52 + k * 26},-70 V-430" stroke="{SHADE}" stroke-width="5" fill="none"/>' for k in range(5))
    b = (f'<path d="M-96,0 h192 v-70 h-192 z" fill="{STONE}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<path d="M-70,-70 v-360 h140 V-70 Z" fill="{STONE}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>{flut}'
         f'<path d="M-100,-430 h200 v-56 h-200 z" fill="{STONE}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<circle cx="-70" cy="-460" r="30" fill="none" stroke="{INK}" stroke-width="9"/>'
         f'<circle cx="70" cy="-460" r="30" fill="none" stroke="{INK}" stroke-width="9"/>')
    return b, 200, 490


def v_milestone(label=""):
    txt = (label or "THEN").upper()[:16]
    fs = int(min(54, 300 / (0.62 * max(1, len(txt)))))
    b = (f'<path d="M-150,0 h300 v-300 q0,-96 -150,-96 q-150,0 -150,96 z" fill="{STONE}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<path d="M-104,-244 h208" stroke="{SHADE}" stroke-width="7" fill="none"/>'
         f'<text x="0" y="-140" class="hand" font-size="{fs}" text-anchor="middle" fill="{INK}" stroke="none">{txt}</text>')
    return b, 300, 400


VS_PROPS = [
    (("pyramid", "pyramids", "giza", "egypt", "egyptian"), v_pyramid),
    (("stonehenge", "henge", "megalith", "megaliths", "trilithon", "dolmen"), v_trilithon),
    (("clock", "clocks", "watch", "watches", "clockwork", "mechanical"), v_clock),
    (("rome", "roman", "greece", "greek", "athens", "temple", "parthenon", "column", "acropolis"), v_column),
]


def vs_known(vs_text):
    """Znama porovnavacia vec (pyramida, Stonehenge, hodiny, stlp, lod) ako kresba, inak None.
    Nic ine sa nekresli - nahrobok s napisom nie je rekvizita, je to popisok."""
    low = " " + "".join(c.lower() if c.isalnum() or c.isspace() else " " for c in (vs_text or "")) + " "
    for words, fn in VS_PROPS:
        if any(f" {w} " in low for w in words):
            return fn(vs_text)
    if any(f" {w} " in low for w in ("ship", "ships", "boat", "boats", "fleet", "galley")):
        return p_ship()
    return None


def vs_object(vs_text, fallback_label=""):
    low = " " + "".join(c.lower() if c.isalnum() or c.isspace() else " " for c in (vs_text or "")) + " "
    for words, fn in VS_PROPS:
        if any(f" {w} " in low for w in words):
            return fn(vs_text)
    if any(f" {w} " in low for w in ("ship", "ships", "boat", "boats", "fleet", "galley")):
        b, w, h = p_ship()
        return b, w, h
    return v_milestone(vs_text or fallback_label)


# ============================================================ VITRINA + VYNIMKY VO VYBERE
def p_vitrine(pid=""):
    b = (f'<path d="M-170,0 h340 v-56 h-340 z" fill="{WOOD}" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<path d="M-150,-56 h300 v-330 h-300 z" fill="none" stroke="{INK}" stroke-width="10" stroke-linejoin="round"/>'
         f'<path d="M-150,-386 h300" stroke="{INK}" stroke-width="10"/>'
         f'<path d="M-150,-330 l90,-56 M-150,-190 l150,-96" stroke="#cfe4ea" stroke-width="9" fill="none"/>'
         f'<path d="M-52,-56 h104 v-44 h-104 z" fill="{STONE}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
         f'<g transform="translate(0,-100) scale(0.46)">{p_coin()[0]}</g>')
    return b, 340, 400


PROPS["vitrine"] = p_vitrine

# slovo -> rekvizita; bije zoznam KEYWORDS (napr. "case" inak spadne na pirátsku truhlu)
OVERRIDES = {
    "case": "vitrine", "cases": "vitrine", "exhibit": "vitrine", "exhibits": "vitrine",
    "display": "vitrine", "museum": "vitrine", "collection": "vitrine",
    "piece": "object", "pieces": "object", "fragment": "object", "fragments": "object",
    "site": "ruin", "sites": "ruin", "enclosure": "ruin", "enclosures": "ruin",
    "device": "machine", "mechanism": "machine",
    "specimen": "object", "specimens": "object",
}


VERBISH = ("sealed", "untouched", "intact", "unknown", "unclear", "hidden", "a", "an", "the",
           "in", "on", "at", "to", "of", "one", "only", "largely", "mostly", "still")


def apply_overrides(text):
    low = " " + "".join(c.lower() if c.isalnum() or c.isspace() else " " for c in text) + " "
    for w, k in OVERRIDES.items():
        if f" {w} " in low:
            return k
    return None


# ============================================================ SVETY
def _sm(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


WORLD_ALIAS = {"mountain": "snow",
               "lake": "shore", "water": "shore", "ice": "snow", "sand": "desert", "beach": "shore",
               "ocean": "sea", "atlantic": "sea", "pacific": "sea", "open sea": "sea",
               "underground": "cave", "cavern": "cave", "catacomb": "cave", "catacombs": "cave", "mine": "cave",
               "jungle": "forest", "woods": "forest", "taiga": "forest", "tunguska": "forest", "fallen_forest": "forest",
               "town": "city", "street": "city", "library": "city", "archive": "city", "scriptorium": "city"}
KINDS = ("hill", "shore", "snow", "desert", "sea", "cave", "forest", "city")

# Varianta sveta pre aktualny build (nastavi build_spec podla spec-u):
#   forest "fallen"  = vyvratene kmene do kruhu (Tunguska)
#   city   "books"   = ulica ku kniznici; inscenovane zabery a exhibit v interieri kniznice
#   city   "library" = cele video v kniznici (aj uvod/slucka)
VARIANT = ""


def world_kind(w):
    w = (w or "hill").strip().lower()
    w = WORLD_ALIAS.get(w, w)
    return w if w in KINDS else "hill"


_FALLEN_RX = r"\b(flatten\w*|uproot\w*|toppled|felled|fallen trees|knocked down|blown down|airburst|tunguska)\b"
_BOOKS_RX = (r"\b(books?|manuscripts?|codex|codices|library|libraries|librar\w*|scrolls?|pages?|ciphers?|"
             r"undeciphered|vellum|parchment)\b")


def world_variant(world, spec=None):
    """Varianta sveta: explicitne meno (library, tunguska) alebo kluce slova v texte spec-u."""
    w = (world or "").strip().lower()
    if w in ("library", "archive", "scriptorium"):
        return "library"
    if w in ("tunguska", "fallen_forest"):
        return "fallen"
    kind = world_kind(world)
    if spec and kind in ("forest", "city"):
        blob = " ".join([str(spec.get("title", "")), str(spec.get("topic", ""))]
                        + [str(l.get("say", "")) for l in spec.get("lines", [])]).lower()
        if kind == "forest" and re.search(_FALLEN_RX, blob):
            return "fallen"
        if kind == "city" and re.search(_BOOKS_RX, blob):
            return "books"
    return ""


def interior(kind, walk=False):
    """Bez oblohy a slnka: jaskyna vzdy; kniznica v inscenovanych zaberoch (books) aj v uvode (library)."""
    if kind == "cave":
        return True
    if kind == "city":
        return VARIANT == "library" or (VARIANT == "books" and not walk)
    return False


def terrain(kind):
    """Vrati (python fn, JS vyraz) profilu terenu. Varianta terenu z LOOK-u (utes, molo, tundra...)
    ma vlastny profil - uvod, zaverecna chodza aj slucka ho maju spolocny."""
    lk = _look.terrain_fn(kind)
    if lk:
        return lk
    if kind == "sea":
        # hladina je takmer rovna a lezi vyssie ako pevnina - pod nou je vidno viac vody
        return (lambda x: 1168 - 12 * _sm(x / 2400.0)), "1168 - 12 * smooth(x / 2400)"
    if kind == "shore":
        return (lambda x: 1286 - 54 * _sm(x / 1600.0)), "1286 - 54 * smooth(x / 1600)"
    if kind == "snow":
        return (lambda x: 1268 - 400 * _sm(x / 1300.0)), "1268 - 400 * smooth(x / 1300)"
    if kind == "desert":
        return (lambda x: 1282 - 66 * _sm(x / 1700.0)), "1282 - 66 * smooth(x / 1700)"
    if kind == "cave":
        # dno jaskyne mierne stupa k vyssej sieni
        return (lambda x: 1266 - 170 * _sm(x / 1400.0)), "1266 - 170 * smooth(x / 1400)"
    if kind == "forest":
        return (lambda x: 1264 - 260 * _sm(x / 1400.0)), "1264 - 260 * smooth(x / 1400)"
    if kind == "city":
        if VARIANT == "library":
            return (lambda x: 1268.0), "1268"          # podlaha je rovna
        return (lambda x: 1270 - 120 * _sm(x / 1500.0)), "1270 - 120 * smooth(x / 1500)"
    return (lambda x: 1260 - 360 * _sm(x / 1300.0)), "1260 - 360 * smooth(x / 1300)"


STYLE = {
    "hill": dict(fill=DIRT, sub=None, sub_from=0, grass=True, ghost="land", dust=PAPER),
    "shore": dict(fill="#ecdcb4", sub=None, sub_from=0, grass=False, ghost="sea", dust=PAPER),
    "snow": dict(fill="#f4f4f1", sub="#dde7ec", sub_from=300, grass=False, ghost="bones", dust=PAPER),
    "desert": dict(fill="#e9d6a6", sub=DIRT2, sub_from=320, grass=False, ghost="buried", dust=PAPER),
    # more: hladina miesto zeme, pod nou tmavsia hlbka, na nej pena; duch = vrak
    "sea": dict(fill=WATER, sub="#6ba8c4", sub_from=210, grass=False, ghost="sea", dust=PAPER, foam=True),
    # jaskyna: svetle skalne dno, hlbsie tmavsi kamen (nie cierna)
    "cave": dict(fill=_X.CAVE_FLOOR, sub=_X.CAVE_SUB, sub_from=260, grass=False, ghost="cave", dust=PAPER),
    "forest": dict(fill=_X.FOREST_FLOOR, sub=_X.FOREST_SUB, sub_from=300, grass=False, ghost="forest", dust=PAPER),
    "city": dict(fill=_X.COBBLE, sub=_X.COBBLE_SUB, sub_from=280, grass=False, ghost="city", dust=PAPER),
}


def style_for(kind):
    """STYLE podla sveta aj varianty (kniznica ma dreveny parket, spaleny les sucho zem),
    prefarbeny paletou epizody (look)."""
    if kind == "city" and VARIANT == "library":
        return _look.style(kind, dict(STYLE["city"], fill=_X.WOODF, sub=_X.WOODF_SUB, sub_from=320))
    if kind == "forest" and VARIANT == "fallen":
        return _look.style(kind, dict(STYLE["forest"], fill=_X.BURNT_FLOOR))
    return _look.style(kind, STYLE[kind])


def foam(x, y, i=0):
    """Penovy hrebenik na hladine - nahrada travy vo svete `sea`."""
    w = 54 + (i % 3) * 16
    return (f'<path d="M{x},{y} q{w * 0.3:.0f},-13 {w * 0.55:.0f},0 q{w * 0.3:.0f},13 {w * 0.45:.0f},0" '
            f'fill="none" stroke="{PAPER}" stroke-width="8" stroke-linecap="round"/>')


def world_far(p, kind):
    """Vzdialena vrstva uvodu/slucky. Breh a nove varianty terenu kresli look.far; ostatnym
    look.decorate_far doplni vecerne slnko, drobnosti (decor) a hmlu."""
    lk = _look.far(p, kind)
    if lk is not None:
        return lk
    return _look.decorate_far(p, kind, _world_far_base(p, kind))


def _world_far_base(p, kind):
    ext = _X.far(p, kind, VARIANT)
    if ext is not None:
        return ext
    cl = _look.walk_clouds(p)
    birds = _look.birds()
    if kind == "sea":
        # otvoreny horizont: ziadna pevnina, len pas vody, vzdialena plachta a vtaky
        band = (f'<path d="M-900,1086 H2400 V1330 H-900 Z" fill="{_look.tone("#a9d6e8")}" stroke="none" opacity="0.75"/>'
                f'<path d="M-900,1086 H2400" stroke="{INK}" stroke-width="8" fill="none"/>'
                + "".join(f'<path d="M{-800 + i * 280},{1132 + (i % 3) * 40} q26,-14 52,0 q26,14 52,0" '
                          f'stroke="{PAPER}" stroke-width="6" fill="none" stroke-linecap="round"/>' for i in range(12)))
        far_sail = f'<g transform="translate(1520,1086) scale(0.30)">{p_ship_far()[0]}</g>'
        return f'<g id="{p}_far">{band}{far_sail}{cl}{birds}</g>'
    if kind == "shore":
        sea = (f'<path d="M-900,1120 H2400 V1360 H-900 Z" fill="{WATER}" stroke="none" opacity="0.8"/>'
               f'<path d="M-900,1120 H2400" stroke="{INK}" stroke-width="8" fill="none"/>'
               + "".join(f'<path d="M{-800 + i * 250},{1168 + (i % 3) * 44} q30,-16 60,0 q30,16 60,0" '
                         f'stroke="{PAPER}" stroke-width="7" fill="none" stroke-linecap="round"/>' for i in range(13)))
        boats = (f'<g transform="translate(1330,1108) scale(0.32)">{p_ship()[0]}</g>'
                 f'<g transform="translate(320,1116) scale(0.19)">{p_ship()[0]}</g>')
        return f'<g id="{p}_far">{sea}{boats}{cl}{birds}</g>'
    if kind == "snow":
        ridge = (f'<path d="M-800,1160 L-300,820 L-60,980 L260,700 L620,990 L1000,780 L1400,1100 L2200,1010 V1420 H-800 Z" '
                 f'fill="{_look.col("mtn_far", PAPER)}" stroke="{_look.col("mtn_line", "#a7b3bb")}" stroke-width="8" '
                 f'stroke-linejoin="round"/>')
        pines = "".join(f'<path d="M{x},1124 l-44,0 l44,-100 l44,100 z M{x},1024 l-34,0 l34,-82 l34,82 z" '
                        f'fill="{_look.col("pine", "#4d6b52")}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
                        for x in (120, 780, 1500))
        return f'<g id="{p}_far">{ridge}{pines}{cl}</g>'
    if kind == "desert":
        dunes = (f'<path d="M-900,1180 q300,-120 620,-20 q280,86 560,-30 q300,-124 620,-10 q260,96 520,-20 V1420 H-900 Z" '
                 f'fill="{_look.col("dune", DIRT)}" stroke="{_look.col("dune_line", "#bda57a")}" stroke-width="7" '
                 f'stroke-linejoin="round"/>')
        palm = (f'<g transform="translate(1450,1150) scale(0.58)"><path d="M0,0 C-8,-90 10,-170 4,-250" stroke="{WOOD}" stroke-width="13" fill="none" stroke-linecap="round"/>'
                f'<path d="M4,-250 q-70,-40 -120,-10 M4,-250 q70,-46 124,-12 M4,-250 q-40,-70 -94,-84 M4,-250 q46,-66 100,-76" '
                f'stroke="{LEAF}" stroke-width="11" fill="none" stroke-linecap="round"/></g>')
        return f'<g id="{p}_far">{dunes}{palm}{cl}{birds}</g>'
    rc = _look.col("ridge", "#a39d8f")
    trees = ("" if "trees" in _look.decor() else
             f'<path d="M640,1010 l0,-46 M640,964 q-30,-6 -22,-36 q22,-30 46,0 q10,30 -24,36" fill="none" stroke="{rc}" stroke-width="6"/>'
             f'<path d="M1180,1046 l0,-40 M1180,1006 q-26,-6 -18,-32 q18,-26 40,0 q8,26 -22,32" fill="none" stroke="{rc}" stroke-width="6"/>')
    ridge = (f'<path d="M-400,1130 Q0,930 380,1075 T980,1030 T1600,1090 T2300,1050" fill="none" stroke="{rc}" '
             f'stroke-width="7" stroke-linecap="round"/>')
    return f'<g id="{p}_far">{ridge}{trees}{cl}{birds}</g>'


def ghost_land(p):
    cx, cy = 330, 1530
    out = (f'<path id="{p}_g0" class="pen" pathLength="1" d="{ell(cx, cy, 200, 62)}" fill="none" stroke="{GH}" stroke-width="8"/>'
           f'<path id="{p}_g1" class="pen" pathLength="1" d="{ell(cx, cy + 40, 390, 120)}" fill="none" stroke="{GH}" stroke-width="8"/>')
    for k, (dx, dy, h, w) in enumerate(((0, -14, 132, 46), (-170, 6, 108, 40), (172, 4, 112, 40),
                                        (-330, 74, 92, 34), (334, 70, 96, 34), (-78, 96, 84, 32), (96, 100, 86, 32))):
        x, y = cx + dx, cy + dy
        out += (f'<path id="{p}_gp{k}" class="pen" pathLength="1" d="M{x - w / 2:.0f},{y:.0f} V{y - h + 22:.0f} '
                f'Q{x:.0f},{y - h:.0f} {x + w / 2:.0f},{y - h + 24:.0f} V{y:.0f}" fill="none" stroke="{GH}" '
                f'stroke-width="8" stroke-linejoin="round"/>')
    return f'<g id="{p}_ghost" opacity="0">{out}</g>'


GH_SEA = "#5d8494"


def ghost_sea(p):
    """Podvodny ekvivalent duchov: silueta vraku (trup, rebra, zlomeny staziar).
    Cela kresba musi sediet do pasma ~330 jednotiek pod hladinou, inak staziar trci nad plaz."""
    cx, deck = 340, 1482
    out = (f'<path id="{p}_g0" class="pen" pathLength="1" d="M{cx - 258},{deck} q28,142 258,142 q230,0 258,-142" '
           f'fill="none" stroke="{GH_SEA}" stroke-width="10" stroke-linecap="round"/>'
           f'<path id="{p}_g1" class="pen" pathLength="1" d="M{cx - 258},{deck} H{cx + 258}" fill="none" stroke="{GH_SEA}" stroke-width="10"/>')
    for k, dx in enumerate((-176, -88, 0, 88, 176)):
        out += (f'<path id="{p}_gp{k}" class="pen" pathLength="1" d="M{cx + dx},{deck + 8} q-16,-56 4,-96" '
                f'fill="none" stroke="{GH_SEA}" stroke-width="9" stroke-linecap="round"/>')
    out += (f'<path id="{p}_gp5" class="pen" pathLength="1" d="M{cx - 24},{deck - 86} l-34,-84 l42,26 l14,-44" '
            f'fill="none" stroke="{GH_SEA}" stroke-width="10" stroke-linecap="round"/>')
    out += (f'<path id="{p}_gp6" class="pen" pathLength="1" d="{ell(cx - 380, deck + 118, 54, 22)}{ell(cx + 396, deck + 108, 46, 19)}" '
            f'fill="none" stroke="{GH_SEA}" stroke-width="9"/>')
    return f'<g id="{p}_ghost" opacity="0">{out}</g>'


GH_COLD = "#8fa6b4"


def _bones_paths(p, cx, cy, ids=True):
    """Kostra pod snehom (lebka, rebra, tri dlhe kosti). ids=False: staticka kopia bez
    kreslenia perom (class pen by ju bez animacie skryl)."""
    def at(i):
        return f'id="{p}_{i}" class="pen" pathLength="1" ' if ids else ""
    sk = (f'<path {at("g0")}'
          f'd="M{cx - 120},{cy - 40} q0,-130 120,-130 q120,0 120,130 q0,74 -50,96 l0,58 h-140 l0,-58 q-50,-22 -50,-96 z" '
          f'fill="none" stroke="{GH_COLD}" stroke-width="10" stroke-linejoin="round"/>'
          f'<path {at("g1")}'
          f'd="{ell(cx - 52, cy - 60, 30, 34)}{ell(cx + 52, cy - 60, 30, 34)}" '
          f'fill="none" stroke="{GH_COLD}" stroke-width="9"/>')
    ribs = ""
    for k in range(4):
        y = cy + 150 + k * 66
        ribs += (f'<path {at("gp" + str(k))}'
                 f'd="M{cx - 150},{y} q150,{58 + k * 8} 300,0" fill="none" stroke="{GH_COLD}" '
                 f'stroke-width="9" stroke-linecap="round"/>')
    for k, (x0, y0, dx) in enumerate(((cx - 420, cy + 210, 260), (cx + 300, cy + 300, 240), (cx - 380, cy + 420, 300))):
        ribs += (f'<path {at("gp" + str(k + 4))}'
                 f'd="M{x0},{y0} q18,-26 44,-14 l{dx},52 q28,10 18,38 q-16,24 -42,10 l-{dx},-52 q-28,-8 -20,-34 z" '
                 f'fill="none" stroke="{GH_COLD}" stroke-width="9" stroke-linejoin="round"/>')
    return sk + ribs


def ghost_bones(p, lead_in=False):
    """Pod ladom: lebka, rebra a dve dlhe kosti. Duch v snehu ma byt to, co je
    pod povrchom zamrznute, nie kamenne kruhy z kopca.
    lead_in=True (zaverecne zabery slucky): druha, staticka kostra vlavo pri x=-244 - kamera
    uvodneho zaberu slucky je tam hned po strihu, takze strih z ponoru ku kostiam ukaze kosti aj
    na druhej strane. Pri nultom snimku je mimo obrazu, slucku nemeni."""
    extra = _bones_paths(p, -244, 1520, ids=False) if lead_in else ""
    return f'<g id="{p}_ghost" opacity="0">{_bones_paths(p, 360, 1520)}{extra}</g>'


GH_SAND = "#b9a173"


def ghost_buried(p):
    """Pod pieskom: obrys zasypaneho telesa - dlazba, schody a nadoba."""
    cx, cy = 360, 1500
    out = (f'<path id="{p}_g0" class="pen" pathLength="1" '
           f'd="M{cx - 400},{cy} l400,-120 l400,120 l-400,120 z" fill="none" stroke="{GH_SAND}" '
           f'stroke-width="10" stroke-linejoin="round"/>'
           f'<path id="{p}_g1" class="pen" pathLength="1" '
           f'd="M{cx - 400},{cy} v150 l400,120 v-150 M{cx + 400},{cy} v150 l-400,120" '
           f'fill="none" stroke="{GH_SAND}" stroke-width="10" stroke-linejoin="round"/>')
    for k in range(3):
        s = 1 - k * 0.26
        out += (f'<path id="{p}_gp{k}" class="pen" pathLength="1" '
                f'd="M{cx - 300 * s:.0f},{cy + 300 + k * 90} l{300 * s:.0f},-{90 * s:.0f} '
                f'l{300 * s:.0f},{90 * s:.0f}" fill="none" stroke="{GH_SAND}" stroke-width="9" '
                f'stroke-linejoin="round"/>')
    out += (f'<path id="{p}_gp3" class="pen" pathLength="1" '
            f'd="M{cx + 520},{cy + 250} q-70,90 0,170 q70,80 140,0 q70,-80 0,-170 z" '
            f'fill="none" stroke="{GH_SAND}" stroke-width="9" stroke-linejoin="round"/>')
    for k in (4, 5, 6):
        out += f'<path id="{p}_gp{k}" class="pen" pathLength="1" d="M0,0" fill="none" stroke="none"/>'
    return f'<g id="{p}_ghost" opacity="0">{out}</g>'


def ghosts(p, kind, lead_in=False):
    ext = _X.ghost(p, kind, terrain(kind)[0], lead_in)
    if ext is not None:
        return ext
    g = STYLE[kind]["ghost"]
    if g == "sea":
        return ghost_sea(p)
    if g == "bones":
        return ghost_bones(p, lead_in)
    if g == "buried":
        return ghost_buried(p)
    return ghost_land(p)


# ============================================================ ERA: davove a vedlajsie postavy
SHIRTS = ("#8ab6d6", "#d99a9a", "#9ec9a0", "#e0c078")


def crowd_rig(p, era="ancient", i=0, prop="", held=""):
    """Tri stupne: praveki panacikovia (kozusina), historicki (klobuk + kosela, 1700+)
    a moderni navstevnici (tricko). Posadka z roku 1872 nema byt ani jedno z krajnych.
    held = to, co drzi pred sebou oboma rukami (sucast tela - hybe sa s nim)."""
    e = (era or "ancient").strip().lower()
    if e == "modern":
        return rig(p, hat=False, pack=False, shirt=SHIRTS[i % len(SHIRTS)], prop=prop, held=held)
    if e == "historic":
        return rig(p, hat=True, pack=False, shirt=SHIRTS[i % len(SHIRTS)], prop=prop, held=held)
    return rig(p, hat=False, pack=False, tuft=True, prop=prop, held=held)


def is_modern(era):
    return (era or "ancient").strip().lower() == "modern"


# ---- interier (muzeum/laborator) pre archetyp exhibit
def gallery(p):
    """Jednoducha galeria: podlaha, zadna stena, obrazy - jasne odlisne od exterieru.
    Pri knihach/rukopisoch (mesto, varianta books/library) interier kniznice s regalmi."""
    if VARIANT in ("books", "library"):
        return _X.library_room(p)
    wall_y = 760
    frames = ""
    for k, (x, w, h) in enumerate(((-260, 190, 150), (140, 150, 190), (560, 210, 140), (960, 160, 170))):
        frames += (f'<path d="M{x - w / 2:.0f},{wall_y - 190 - h:.0f} h{w} v{h} h{-w} z" fill="{PAPER}" '
                   f'stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
                   f'<path d="M{x - w / 2 + 22:.0f},{wall_y - 216 - h + 30:.0f} h{w - 44} v{h - 52} h{-(w - 44)} z" '
                   f'fill="none" stroke="{SHADE}" stroke-width="6"/>')
    return (f'<path d="M-1400,{wall_y} H2400 V-900 H-1400 Z" fill="#f2eee1" stroke="none"/>'
            f'<path d="M-1400,{wall_y} H2400" stroke="{INK}" stroke-width="9" fill="none"/>'
            f'{frames}'
            f'<path d="M-1400,{wall_y} H2400 V2600 H-1400 Z" fill="#e6e0cf" stroke="none"/>'
            + "".join(f'<path d="M{-1200 + k * 420},{wall_y} l{-190 - k * 26},760" stroke="{SHADE}" '
                      f'stroke-width="5" fill="none" opacity="0.5"/>' for k in range(9)))


def plinth(x, top_y, w=300, h=150):
    return (f'<path d="M{x - w / 2:.0f},{top_y + h:.0f} h{w} v{-h} h{-w} z" fill="{STONE}" stroke="{INK}" '
            f'stroke-width="10" stroke-linejoin="round"/>'
            f'<path d="M{x - w / 2 - 14:.0f},{top_y:.0f} h{w + 28} v-22 h{-(w + 28)} z" fill="{STONE}" '
            f'stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>')


def glass_case(x, base_y, w=340, h=400):
    return (f'<path d="M{x - w / 2:.0f},{base_y:.0f} h{w} v{-h} h{-w} z" fill="none" stroke="{INK}" '
            f'stroke-width="10" stroke-linejoin="round"/>'
            f'<path d="M{x - w / 2:.0f},{base_y - h:.0f} h{w}" stroke="{INK}" stroke-width="10"/>'
            f'<path d="M{x - w / 2 + 16:.0f},{base_y - 60:.0f} l{w * 0.42:.0f},{-h * 0.62:.0f} '
            f'M{x - w / 2 + 16:.0f},{base_y - h * 0.62:.0f} l{w * 0.3:.0f},{-h * 0.32:.0f}" '
            f'stroke="#cfe4ea" stroke-width="9" fill="none"/>')


def placard(x, y, text):
    txt = (text or "").upper()[:16]
    fs = int(min(40, 250 / (0.62 * max(1, len(txt)))))
    return (f'<path d="M{x - 130},{y} h260 v80 h-260 z" fill="{PAPER}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
            f'<text x="{x}" y="{y + 52}" class="hand" font-size="{fs}" text-anchor="middle" fill="{INK}" stroke="none">{txt}</text>')
