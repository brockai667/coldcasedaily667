# -*- coding: utf-8 -*-
"""HiddenEarth miesta: 5 prostredi, ktore sa od seba lisia horizontom, oblohou, zemou aj drobnostami.

Su to varianty terenu (LOOK terrain) existujucich svetov: uvod, inscenovane zabery aj slucka ich dostanu
cez hacky v look.py. Zapina ich explicitne meno sveta v spec-e (worlds.world_variant) alebo
spec["look"]["terrain"]; nahodny seed ich nikdy nevyberie -> existujuce epizody vyzeraju presne ako predtym.

  spec["world"]                           svet    teren     horizont | obloha | zem | drobnosti
  island, isle, lighthouse_island         shore   isle      otvorene more, ostroh s majakom | kopovite oblaky,
                                                            cajky | zulove platne, trsy s kvetmi | balvany, jazierko
  canyon, red_desert, rock_arch           desert  canyon    ROVNY horizont, stena kanona, skalny oblúk | bez
                                                            oblakov, tetelenie | cervena zem s prasklinami | hoodoos
  jungle, rainforest, jungle_ruins        forest  jungle    bez horizontu: stena stromov a stupnovity chram |
                                                            koruny, liany, luce svetla | tmava hlina s listim | stela
  geyser, volcano, volcanic, lava         hill    geyser    jedna dymiaca sopka | popol a para | cadic so sirou |
                                                            gejzir, horuce jazierko, fumaroly, vystraha
  arctic, antarctic, ice_shelf, polar     snow    iceshelf  more s ladovcami, nizke slnko na horizonte | pasy
                                                            oblakov | sastrugi | tlakovy val, vlajky

Suradnice ako v worlds_ext: far_* = vzdialena vrstva uvodu (x -900..2400, horizont ~1100-1150),
*_near = blizka vrstva (world, teren hy(x), generovane od pevneho WX0 -> slucka sedi),
bd_* = pozadie inscenovanych zaberov (obrazovka, zem na `hor`), ground/dressing/fore = zem inscenovanych zaberov.
"""
import math
import random

import look as L
from props import INK, PAPER, WOOD, ell

TERRAINS = {"shore": ("isle",), "desert": ("canyon",), "forest": ("jungle",), "hill": ("geyser",),
            "snow": ("iceshelf",)}
ALL = tuple(t for v in TERRAINS.values() for t in v)
KIND_OF = {t: k for k, v in TERRAINS.items() for t in v}
NAMES = {"island": "isle", "isle": "isle", "lighthouse_island": "isle",
         "canyon": "canyon", "red_desert": "canyon", "rock_arch": "canyon",
         "jungle": "jungle", "rainforest": "jungle", "jungle_ruins": "jungle",
         "geyser": "geyser", "volcano": "geyser", "volcanic": "geyser", "lava": "geyser",
         "arctic": "iceshelf", "antarctic": "iceshelf", "ice_shelf": "iceshelf", "iceshelf": "iceshelf",
         "polar": "iceshelf"}
# y0 - rise * smooth((x - xo) / span) - ako look.TERRAIN_FN
TERRAIN_FN = {("shore", "isle"): (1266, 130, 0, 1400), ("desert", "canyon"): (1282, 50, 0, 1500),
              ("forest", "jungle"): (1268, 150, 0, 1400), ("hill", "geyser"): (1274, 80, 0, 1500),
              ("snow", "iceshelf"): (1278, 24, 0, 1600)}
# horizont inscenovanych pozadi nad ciarou zeme (look.stage_hz)
STAGE_HZ = {"isle": 210, "canyon": 130, "jungle": 560, "geyser": 170, "iceshelf": 110}
WX0 = -3400

# palety (3 na miesto); kluce zakladneho sveta (sand, rock, floor, ground, snow...) prekryju jeho paletu,
# takze aj stary kod (piesok, mohyly, makro zem, okno) dostane farby miesta
PAL = {
    # siva zula + tyrkysove more | tmava bridlica + sivozelene Atlantic | ruzova zula + hlboke modre more
    "isle": (
        dict(rock="#c3bdb3", rock_d="#aaa295", rock_line="#857d71", sand="#a3b46c", sand_line="#7d8c4e", turf="#a3b46c", turf_d="#8a9a58",
             sea="#3f93b0", sea_far="#7cbfd2", grass="#88ad5b", grass_d="#65893f", thrift="#e58fb0",
             lichen="#e0b43c", island="#8fae9a", tower="#f6f3ec", band="#c0392b", roof="#b5543c",
             sky="#cfe7f0", pebble="#8f877b", soil="#b3a58c"),
        dict(rock="#a4a7a6", rock_d="#8b8f90", rock_line="#626768", sand="#8f9f66", sand_line="#6a7848", turf="#8f9f66", turf_d="#78874f",
             sea="#4f7f86", sea_far="#86aab0", grass="#7f9a55", grass_d="#5f7a3c", thrift="#d98fb2",
             lichen="#d9c04a", island="#7f958a", tower="#f4f1ea", band="#2f3a44", roof="#2f3a44",
             sky="#d7e2e6", pebble="#6f7475", soil="#9c9585"),
        dict(rock="#d6b3a0", rock_d="#c09c88", rock_line="#94705f", sand="#b0b872", sand_line="#858d52", turf="#b0b872", turf_d="#969e5c",
             sea="#2f78b7", sea_far="#6fa7d8", grass="#8fb45e", grass_d="#6b9040", thrift="#f09bb8",
             lichen="#e8a33c", island="#9db39c", tower="#f6f3ec", band="#d62828", roof="#d62828",
             sky="#d2e5f4", pebble="#a07c69", soil="#b89a84"),
    ),
    # cerveny piesocnik (Arches) | ruzovooranzovy s fialovou skalou (Wadi Rum) | okrovy (Colorado)
    "canyon": (
        dict(sand="#e2a06c", sand_d="#d18a59", sand_line="#bb7446", crack="#a8603a", rock="#c8643c",
             rock_d="#a64d2c", rock_l="#dd8659", rock_line="#7e3a1e", far="#ecbd92", far_line="#c98b5f",
             dune="#ecbd92", dune_line="#c98b5f", scrub="#8d9a6a", scrub_d="#6b7a4c", sky="#f8dcb8",
             sky_top="#c3e1e6", pebble="#a8603a"),
        dict(sand="#eab08a", sand_d="#da9a74", sand_line="#c98460", crack="#b06a4a", rock="#b8605a",
             rock_d="#94474a", rock_l="#d08070", rock_line="#6e3036", far="#f0c6a4", far_line="#cf9474",
             dune="#f0c6a4", dune_line="#cf9474", scrub="#9aa070", scrub_d="#737a4e", sky="#f9dfc8",
             sky_top="#cde0ea", pebble="#b06a4a"),
        dict(sand="#e6c07c", sand_d="#d6aa64", sand_line="#bf9148", crack="#a67a3a", rock="#d08a42",
             rock_d="#b06e30", rock_l="#e2a860", rock_line="#80501e", far="#efd4a2", far_line="#c9a468",
             dune="#efd4a2", dune_line="#c9a468", scrub="#8a9660", scrub_d="#687444", sky="#f8e4bc",
             sky_top="#c8e0e2", pebble="#a67a3a"),
    ),
    # sviezo zelena | hmlista tyrkysova | suche obdobie (zltozelena)
    "jungle": (
        dict(floor="#8a7048", floor_sub="#6e5634", needle="#a38b5e", pine="#2e5a36",
             pine_mid=("#3f7a44", "#356c3c"), pine_near="#4b8a4c", pine_far="#a3c296", pine_far_line="#7a9a70",
             canopy="#4f8f45", canopy_d="#2f6a35", leaf="#5a9a48", leaf_d="#3a7236", haze="#d9e6cb",
             haze_top="#bcd3b0", stone="#bdb89e", stone_d="#9d977c", stone_line="#77715a", moss="#7ea44a",
             vine="#3d6b2f", trunk="#8a6a4a", trunk_d="#6a4e34", ray="#fff4c2", pebble="#5e4a2e"),
        dict(floor="#7a6a4e", floor_sub="#5e5038", needle="#958566", pine="#2a5a52",
             pine_mid=("#3a7468", "#326a5e"), pine_near="#448676", pine_far="#abc6be", pine_far_line="#7f9e96",
             canopy="#3f8472", canopy_d="#2a6254", leaf="#4c9480", leaf_d="#2f6e5e", haze="#dae7e3",
             haze_top="#bfd6d0", stone="#b4b6a8", stone_d="#95978a", stone_line="#6e7064", moss="#6e9e6a",
             vine="#35645a", trunk="#7a6650", trunk_d="#5c4a38", ray="#f4f8e0", pebble="#54483a"),
        dict(floor="#9a7a4c", floor_sub="#7c6038", needle="#b39868", pine="#5a6a2e",
             pine_mid=("#7a8a3a", "#6c7c32"), pine_near="#8a9a48", pine_far="#cbd1a2", pine_far_line="#a0a678",
             canopy="#8aa040", canopy_d="#62762c", leaf="#94aa44", leaf_d="#6c7e2e", haze="#ede7ca",
             haze_top="#dad6aa", stone="#c9bc98", stone_d="#a99c78", stone_line="#80745a", moss="#9aaa4a",
             vine="#5c6a2c", trunk="#8e6c46", trunk_d="#6c5032", ray="#fff0b8", pebble="#6a5434"),
    ),
    # Island: tmavy cadic | Yellowstone: svetly sinter | Dallol: zltozelena kyselina
    "geyser": (
        dict(ground="#5f5955", ground_sub="#4b4541", grass="#7f9a55", ridge="#4b4541", ridge2="#6f6964",
             rock="#6d6660", rock_line="#3b3532", crust="#e0bf4a", rust="#c9763c", pool="#58c3c8",
             pool_d="#2f8f9e", sinter="#e9e2cf", sinter_line="#b9ae94", steam="#f7f5f0", ash="#a39c96",
             ash_l="#c4beb8", cone="#6b635d", cone_line="#4a433e", plain="#7a736c", lava="#e8663c",
             sky="#eadfd8", sky_top="#d3ccd0", pebble="#3f3935"),
        dict(ground="#cfc6b2", ground_sub="#b9ae96", grass="#8aa05a", ridge="#9a9282", ridge2="#b8b0a0",
             rock="#bdb4a2", rock_line="#8a8170", crust="#e6b83c", rust="#d9772e", pool="#3fa8d8",
             pool_d="#2a78b0", sinter="#f2ecde", sinter_line="#c8bca0", steam="#f7f5f0", ash="#b4aea8",
             ash_l="#d0cbc6", cone="#8c847a", cone_line="#605850", plain="#a89f8e", lava="#e8663c",
             sky="#ece6de", sky_top="#d9dbe2", pebble="#8a8170"),
        dict(ground="#d8c768", ground_sub="#c2ae4c", grass="#9ab04a", ridge="#a8963e", ridge2="#c8b85a",
             rock="#c9a860", rock_line="#8a6e2c", crust="#f0dc5a", rust="#d98a3c", pool="#7fd6a0",
             pool_d="#3fae7a", sinter="#f4eab8", sinter_line="#cbbd7a", steam="#f8f6ee", ash="#b8b09a",
             ash_l="#d4ceb8", cone="#8a7a52", cone_line="#5e5236", plain="#c4b070", lava="#e8663c",
             sky="#f2e8cf", sky_top="#dfdfd2", pebble="#8a6e2c"),
    ),
    # ruzovozlte nizke slnko | bledy polarny den | fialovy suumrak
    "iceshelf": (
        dict(snow="#f5f7f8", shade="#d3e2ec", line="#aac6d8", ice="#d6ebf4", ice_line="#86b3cc",
             berg="#f2f8fb", berg_d="#bcd9e8", berg_line="#7fa9c2", sea="#35607f", sea_l="#5b86a4",
             sky="#f9dccb", sky_top="#d1e3ee", sun="#fbcf8c", sun_glow="#fde6c0", streak="#fae9e2",
             pebble="#9dbfd4", flag="#e8702a"),
        dict(snow="#f4f7f9", shade="#cfe0ea", line="#a4c2d6", ice="#d4eaf5", ice_line="#7fadc8",
             berg="#f1f7fa", berg_d="#b6d6e8", berg_line="#7aa6c0", sea="#2f5876", sea_l="#557f9c",
             sky="#e6eff5", sky_top="#c9deeb", sun="#fbe7b0", sun_glow="#fdf4d8", streak="#f4f7f9",
             pebble="#98bad0", flag="#d62828"),
        dict(snow="#f6f4f8", shade="#dcd6ea", line="#b9aed4", ice="#e0dcf0", ice_line="#9a8fc0",
             berg="#f4f2f9", berg_d="#cbc4e2", berg_line="#948ab8", sea="#3e4f78", sea_l="#65709a",
             sky="#f3d6de", sky_top="#d5d6ee", sun="#f8c49a", sun_glow="#fbdcc4", streak="#f8e6ec",
             pebble="#b0a6cc", flag="#e8702a"),
    ),
}


def on():
    """Je LOOK epizody jedno z miest HiddenEarth?"""
    cur = L.CUR
    return bool(cur) and cur.get("terrain") in ALL and cur.get("world") == KIND_OF[cur["terrain"]]


def T():
    return L.CUR["terrain"] if on() else ""


def c(name, default=None):
    return L.col(name, default)


def clear_day():
    return L.time() == "day" and L.weather() == "clear"


def _sm(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def _poly(pts, close=True):
    return "M" + " L".join(f"{x:.0f},{y:.0f}" for x, y in pts) + (" Z" if close else "")


def puffs(circles, fill, sw=6, rects=()):
    """Obrys len okolo ZJEDNOTENIA kruhov/obdlznikov (atrament pod vyplnou): oblak, para, koruna, ker."""
    ol = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r + sw / 2:.1f}"/>' for x, y, r in circles)
    ol += "".join(f'<rect x="{x - sw / 2:.0f}" y="{y - sw / 2:.0f}" width="{w + sw:.0f}" height="{h + sw:.0f}"/>'
                  for x, y, w, h in rects)
    fl = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}"/>' for x, y, r in circles)
    fl += "".join(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}"/>' for x, y, w, h in rects)
    return f'<g fill="{INK}" stroke="none">{ol}</g><g fill="{fill}" stroke="none">{fl}</g>'


def cumulus(x, y, w, h, fill=None, sw=6):
    """Kopovity oblak s plochou spodnou hranou a tienom (iny tvar nez stale rovnake props.cloud)."""
    fill = fill or L.cloud_fill()
    shade = L.mix(fill, "#8397ab", 0.2)
    rb = h * 0.2
    cs = [(x - w / 2 + rb, y - rb, rb), (x + w / 2 - rb, y - rb, rb),
          (x - w * 0.29, y - h * 0.40, h * 0.36), (x - w * 0.07, y - h * 0.56, h * 0.44),
          (x + w * 0.17, y - h * 0.50, h * 0.40), (x + w * 0.33, y - h * 0.33, h * 0.30)]
    base = [(x - w / 2 + rb, y - 2 * rb, w - 2 * rb, 2 * rb)]
    hl = L.mix(fill, "#ffffff", 0.55)
    return (puffs(cs, fill, sw, base)
            + f'<path d="M{x - w / 2 + rb:.0f},{y - h * 0.13:.0f} H{x + w / 2 - rb:.0f} V{y - 1:.0f} H{x - w / 2 + rb:.0f} Z" '
              f'fill="{shade}" stroke="none"/>'
            + f'<path d="M{x - w * 0.16:.0f},{y - h * 0.80:.0f} q{h * 0.16:.0f},{-h * 0.14:.0f} {h * 0.34:.0f},{-h * 0.04:.0f}" '
              f'fill="none" stroke="{hl}" stroke-width="{max(3.0, sw - 2)}" stroke-linecap="round"/>')


def cumulus_spec(x, y, w, h):
    """Ten isty oblak ako (x, y, s, sx, sy) pre stage_shots._cloud_k (box x-120..x+90, y-65..y+30)."""
    sx, sy = w / 210.0, h / 95.0
    return (x - w / 2 + 120 * sx, y - 30 * sy, 1.0, sx, sy)


def streak(x, y, w, h, fill, sw=3.5):
    """Pas nizkych plochych oblakov (polarne slnko): 2-3 prekryte dlhe sosovky roznej dlzky."""
    def lens(cx, cy, ww, hh):
        return (f'<path d="M{cx - ww / 2:.0f},{cy:.0f} Q{cx - ww * 0.12:.0f},{cy - hh:.0f} {cx + ww / 2:.0f},{cy - hh * 0.2:.0f} '
                f'Q{cx + ww * 0.1:.0f},{cy + hh * 0.4:.0f} {cx - ww / 2:.0f},{cy:.0f} Z" fill="{fill}" stroke="{INK}" '
                f'stroke-width="{sw}" stroke-linejoin="round"/>')
    return (lens(x + w * 0.22, y - h * 0.55, w * 0.55, h * 0.7) + lens(x, y, w, h)
            + lens(x - w * 0.18, y + h * 0.62, w * 0.6, h * 0.6))


def gulls(pts):
    return L.gulls(pts)


def plates(hy, x0, x1, d0, d1, fill, line, seed=5, size=(60, 110), sw=3.5, flat=0.55, rnd=0.25):
    """Popraskana zem: nepravidelne polygonove platne (vyschnute bahno, lavova kora) oddelene
    prasklinami - hlbsie v zabere (blizsie ku kamere) su vacsie. Nie tehlova stena."""
    r = random.Random(seed)
    out = []
    d, row = d0, 0
    while d < d1:
        s = size[0] + (size[1] - size[0]) * (d - d0) / max(1.0, d1 - d0)
        x = x0 + (row % 2) * s * 0.5 + r.uniform(0, s * 0.3)
        while x < x1:
            cx, cy = x + r.uniform(-s * 0.1, s * 0.1), hy(x) + d + r.uniform(-s * 0.08, s * 0.08)
            n = r.choice((5, 6, 6, 7))
            a0 = r.uniform(0, 6.28)
            pts = []
            for k in range(n):
                a = a0 + k * 2 * math.pi / n + r.uniform(-rnd, rnd)
                rr = s * 0.5 * r.uniform(0.8, 0.96)
                pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * flat))
            out.append(f'<path d="{_poly(pts)}"/>')
            x += s * r.uniform(0.98, 1.08)
        d += s * flat * 1.02
        row += 1
    return f'<g fill="{fill}" stroke="{line}" stroke-width="{sw}" stroke-linejoin="round">{"".join(out)}</g>'


# ================================================================== spolocne: obloha
def sky_rect(p):
    """Jasny den: kazde miesto ma vlastnu farbu vzduchu (prechod hore -> horizont), papier presvita."""
    t = T()
    top, bot, op = {"isle": (c("sky"), "#f6f1e4", 0.75), "canyon": (c("sky_top"), c("sky"), 0.8),
                    "jungle": (c("haze_top"), c("haze"), 0.9), "geyser": (c("sky_top"), c("sky"), 0.85),
                    "iceshelf": (c("sky_top"), c("sky"), 0.85)}[t]
    return (f'<defs><linearGradient id="{p}_hsky" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{top}"/><stop offset="0.62" stop-color="{bot}"/></linearGradient></defs>'
            f'<path d="M-80,-80 H1160 V2000 H-80 Z" fill="url(#{p}_hsky)" opacity="{op}"/>')


def hazy_sun(x, y, r=64):
    """Slnko cez popol/paru: bez lucov, bledy kotuc so svatozarou."""
    return (f'<circle cx="{x}" cy="{y}" r="{r * 1.9:.0f}" fill="#fff6e0" opacity="0.35"/>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="#f8e8c4" stroke="{INK}" stroke-width="6" opacity="0.95"/>')


def walk_sun(p, cls, default):
    """Obsah {p}_sun uvodu: None = standard (look), '' = bez slnka na oblohe."""
    t = T()
    if t == "jungle" or (t == "iceshelf" and L.time() != "night"):
        return ""                      # prales ma nad sebou koruny; polarne slnko sedi na horizonte (far)
    if t == "geyser" and L.time() == "day" and L.weather() in ("clear", "fog"):
        return hazy_sun(220, 330)
    return None


# oblaky vzdialenej vrstvy uvodu (jasny den): kopovite oblaky na ostrove, pasy nad ladom, popol pri sopke
ISLE_CL = ((-560, 640, 380, 190), (140, 600, 340, 170), (640, 770, 280, 130), (1500, 590, 420, 210),
           (2100, 700, 300, 150))
ICE_CL = ((-600, 520, 480, 34), (100, 560, 520, 40), (560, 780, 380, 26), (980, 470, 620, 36),
          (1720, 620, 560, 38), (2200, 500, 420, 30))
ASH_CL = ((-420, 860, 260, 120), (1560, 830, 300, 130), (2200, 880, 240, 100))


def far_clouds(p):
    """Skupina {p}_cloud (drift oblakov riesi engine.js); iny tvar oblakov pre kazde miesto (aj vecer,
    v noci a pri zamracenom pocasi - farbu im da cas/pocasie). Kanon ma oblaky len ked nie je jasno."""
    t = T()
    if t == "canyon" and not clear_day():
        return L.walk_clouds(p)
    body = ""
    if t == "isle":
        body = "".join(cumulus(x, y, w, h) for x, y, w, h in ISLE_CL)
    elif t == "iceshelf":
        body = "".join(streak(x, y, w, h, c("streak")) for x, y, w, h in ICE_CL)
    elif t == "geyser":
        body = "".join(puffs([(x - w * 0.3, y - h * 0.3, h * 0.36), (x, y - h * 0.5, h * 0.5), (x + w * 0.3, y - h * 0.28, h * 0.32)],
                             c("ash_l"), 6, [(x - w * 0.42, y - h * 0.3, w * 0.84, h * 0.3)]) for x, y, w, h in ASH_CL)
    elif t == "jungle":
        # hmla medzi stromami (drift ako oblaky)
        body = "".join(f'<ellipse cx="{x}" cy="{y}" rx="{w}" ry="{h}" fill="#ffffff" opacity="0.32"/>'
                       for x, y, w, h in ((-500, 1060, 420, 26), (300, 1000, 380, 22), (1100, 1080, 460, 28),
                                          (1900, 1020, 400, 24)))
    return f'<g id="{p}_cloud">{body}</g>'


def cloud_spec():
    """(oblaky, slnko/mesiac) pre stage_shots._cloud_k - presne to, co kreslia far_clouds a walk_sun;
    None = standard look (kanon pri nejasnom pocasi)."""
    t = T()
    if t == "canyon" and not clear_day():
        return None
    cl = {"isle": tuple(cumulus_spec(*k) for k in ISLE_CL), "geyser": tuple(cumulus_spec(*k) for k in ASH_CL)}.get(t, ())
    tm, w = L.time(), L.weather()
    if t == "jungle":
        sun = None
    elif tm == "night":
        sun = None if w == "rain" else (float(L.MOON_WALK[0]), float(L.MOON_WALK[1]), 118.0)
    elif t == "geyser" and tm == "day" and w in ("clear", "fog"):
        sun = (220.0, 330.0, 124.0)
    elif t in ("isle", "canyon") and clear_day():
        sun = (880.0, 330.0, 134.0)
    else:
        sun = None
    return cl, sun


# ================================================================== 1) OSTROV S MAJAKOM (shore/isle)
def lighthouse(x, y, s=1.0, sw=6.0):
    """Zavality biely majak s pasom, ciernou galeriou a kupolou (iny nez rekvizita props_story)."""
    tw, tt, h = 70 * s, 48 * s, 210 * s
    band, roof = c("band"), c("roof")
    lit = "#ffe066" if L.night() else "#f7e7a0"
    out = (f'<path d="M{x - tw / 2:.0f},{y:.0f} L{x - tt / 2:.0f},{y - h:.0f} H{x + tt / 2:.0f} L{x + tw / 2:.0f},{y:.0f} Z" '
           f'fill="{c("tower")}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'
           f'<path d="M{x - tw * 0.46:.0f},{y - h * 0.32:.0f} L{x - tw * 0.42:.0f},{y - h * 0.5:.0f} H{x + tw * 0.42:.0f} '
           f'L{x + tw * 0.46:.0f},{y - h * 0.32:.0f} Z" fill="{band}" stroke="{INK}" stroke-width="{sw * 0.8:.1f}"/>'
           f'<path d="M{x - 9 * s:.0f},{y:.0f} v{-26 * s:.0f} q{9 * s:.0f},{-10 * s:.0f} {18 * s:.0f},0 v{26 * s:.0f}" '
           f'fill="{INK}"/>'
           f'<path d="M{x - 5 * s:.0f},{y - h * 0.68:.0f} h{10 * s:.0f} v{-14 * s:.0f} h{-10 * s:.0f} z" fill="{INK}"/>'
           # galeria + zabradlie
           f'<path d="M{x - tt / 2 - 12 * s:.0f},{y - h:.0f} h{tt + 24 * s:.0f} v{-9 * s:.0f} h{-(tt + 24 * s):.0f} z" '
           f'fill="{INK}"/>'
           f'<path d="M{x - tt / 2 - 10 * s:.0f},{y - h - 9 * s:.0f} v{-16 * s:.0f} h{tt + 20 * s:.0f} v{16 * s:.0f} '
           + "".join(f'M{x - tt / 2 - 10 * s + k * (tt + 20 * s) / 5:.0f},{y - h - 9 * s:.0f} v{-16 * s:.0f} ' for k in range(1, 5))
           + f'" fill="none" stroke="{INK}" stroke-width="{sw * 0.6:.1f}"/>'
           # lampova komora + kupola
           f'<path d="M{x - 18 * s:.0f},{y - h - 9 * s:.0f} v{-34 * s:.0f} h{36 * s:.0f} v{34 * s:.0f} z" fill="{lit}" '
           f'stroke="{INK}" stroke-width="{sw * 0.8:.1f}"/>'
           f'<path d="M{x:.0f},{y - h - 9 * s:.0f} v{-34 * s:.0f}" stroke="{INK}" stroke-width="{sw * 0.6:.1f}"/>'
           f'<path d="M{x - 24 * s:.0f},{y - h - 43 * s:.0f} a{24 * s:.0f},{22 * s:.0f} 0 0 1 {48 * s:.0f},0 z" fill="{roof}" '
           f'stroke="{INK}" stroke-width="{sw * 0.8:.1f}"/>'
           f'<circle cx="{x:.0f}" cy="{y - h - 68 * s:.0f}" r="{5 * s:.1f}" fill="{INK}"/>')
    if L.night():
        ly = y - h - 26 * s
        out = (f'<path d="M{x:.0f},{ly:.0f} L{x + 700 * s:.0f},{ly - 90 * s:.0f} L{x + 700 * s:.0f},{ly + 40 * s:.0f} Z" '
               f'fill="#fff3b0" opacity="0.28"/>'
               f'<path d="M{x:.0f},{ly:.0f} L{x - 520 * s:.0f},{ly - 60 * s:.0f} L{x - 520 * s:.0f},{ly + 30 * s:.0f} Z" '
               f'fill="#fff3b0" opacity="0.18"/>' + out)
    return out


def _cottage(x, y, s=1.0):
    w, h = 110 * s, 52 * s
    return (f'<path d="M{x:.0f},{y:.0f} v{-h:.0f} h{w:.0f} v{h:.0f} z" fill="{c("tower")}" stroke="{INK}" stroke-width="5" '
            f'stroke-linejoin="round"/>'
            f'<path d="M{x - 8 * s:.0f},{y - h:.0f} l{w / 2 + 8 * s:.0f},{-34 * s:.0f} l{w / 2 + 8 * s:.0f},{34 * s:.0f} z" '
            f'fill="{c("roof")}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="M{x + 22 * s:.0f},{y - 30 * s:.0f} h{16 * s:.0f} v{14 * s:.0f} h{-16 * s:.0f} z M{x + 70 * s:.0f},{y - 30 * s:.0f} '
            f'h{16 * s:.0f} v{14 * s:.0f} h{-16 * s:.0f} z" fill="{"#ffe066" if L.night() else "#9fb8c4"}" stroke="{INK}" '
            f'stroke-width="3.5"/>'
            f'<path d="M{x + w * 0.72:.0f},{y - h - 20 * s:.0f} v{-22 * s:.0f} h{12 * s:.0f} v{30 * s:.0f}" fill="{c("tower")}" '
            f'stroke="{INK}" stroke-width="4"/>')


def _sea_stack(x, base, h, w):
    rock, rl = c("rock"), c("rock_line")
    return (f'<path d="M{x - w / 2:.0f},{base:.0f} L{x - w * 0.44:.0f},{base - h * 0.55:.0f} L{x - w * 0.28:.0f},{base - h:.0f} '
            f'L{x + w * 0.2:.0f},{base - h * 0.96:.0f} L{x + w * 0.4:.0f},{base - h * 0.5:.0f} L{x + w / 2:.0f},{base:.0f} Z" '
            f'fill="{rock}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x - w * 0.3:.0f},{base - h * 0.7:.0f} h{w * 0.4:.0f} M{x - w * 0.36:.0f},{base - h * 0.4:.0f} h{w * 0.5:.0f}" '
            f'stroke="{rl}" stroke-width="4" stroke-dasharray="18 10"/>'
            f'<path d="M{x - w * 0.28:.0f},{base - h + 2:.0f} L{x + w * 0.2:.0f},{base - h * 0.96 + 2:.0f}" stroke="{c("grass")}" '
            f'stroke-width="9" stroke-linecap="round"/>' + _splash(x - w * 0.55, base, 0.8) + _splash(x + w * 0.5, base, 0.7))


def _splash(x, y, s=1.0):
    """Rozbita vlna o skalu: biele chumace + kvapky."""
    f = L.foam()
    return (puffs([(x - 16 * s, y - 10 * s, 14 * s), (x, y - 22 * s, 18 * s), (x + 17 * s, y - 9 * s, 13 * s)], f, 4)
            + f'<circle cx="{x - 26 * s:.0f}" cy="{y - 40 * s:.0f}" r="{4 * s:.1f}" fill="{f}" stroke="{INK}" stroke-width="2.5"/>'
            f'<circle cx="{x + 22 * s:.0f}" cy="{y - 44 * s:.0f}" r="{3.5 * s:.1f}" fill="{f}" stroke="{INK}" stroke-width="2.5"/>')


def _islet(x, hz, w, h):
    return (f'<path d="M{x - w / 2:.0f},{hz + 3:.0f} Q{x - w * 0.34:.0f},{hz - h:.0f} {x - w * 0.05:.0f},{hz - h * 0.9:.0f} '
            f'Q{x + w * 0.26:.0f},{hz - h * 1.1:.0f} {x + w / 2:.0f},{hz + 3:.0f} Z" fill="{c("island")}" stroke="{INK}" '
            f'stroke-width="5" stroke-linejoin="round"/>')


def _waves(x0, x1, y0, rows, step=250, w=60, sw=7):
    f = L.foam()
    return "".join(f'<path d="M{x0 + i * step + (j % 2) * step / 2:.0f},{y0 + j * 50 + (i % 3) * 10:.0f} q{w / 2:.0f},-15 {w},0 '
                   f'q{w / 2:.0f},15 {w},0" stroke="{f}" stroke-width="{sw}" fill="none" stroke-linecap="round"/>'
                   for j in range(rows) for i in range(int((x1 - x0) / step) + 1))


def _headland(x0, x1, base, top):
    """Skalny ostroh ostrova s travnatym vrchom: sem patri majak a domcek strazcov."""
    rock, rl, g, gd = c("rock"), c("rock_line"), c("grass"), c("grass_d")
    w = x1 - x0
    pts = [(x0, base), (x0 + w * 0.05, top + 90), (x0 + w * 0.12, top + 40), (x0 + w * 0.3, top + 6), (x0 + w * 0.55, top),
           (x0 + w * 0.72, top + 18), (x0 + w * 0.86, top + 60), (x0 + w * 0.95, top + 120), (x1, base)]
    out = f'<path d="{_poly(pts)}" fill="{rock}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
    cap = pts[2:7]
    out += (f'<path d="{_poly([(x, y + 7) for x, y in cap], False)}" stroke="{g}" stroke-width="14" fill="none" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')
    for k, f in enumerate((0.32, 0.55, 0.78)):
        yy = top + (base - top) * f
        out += (f'<path d="M{x0 + w * (0.1 - f * 0.05):.0f},{yy:.0f} q{w * 0.3:.0f},{-8 - k * 3} {w * 0.8:.0f},{6:.0f}" stroke="{rl}" '
                f'stroke-width="4" fill="none" stroke-dasharray="{40 + k * 12} {18 + k * 6}"/>')
    out += "".join(f'<circle cx="{x0 + w * fx:.0f}" cy="{top + 12 + fy:.0f}" r="4" fill="{c("thrift")}" stroke="{INK}" '
                   f'stroke-width="2"/>' for fx, fy in ((0.2, 18), (0.38, 2), (0.66, 8), (0.8, 30)))
    return out + _splash(x0 + w * 0.02, base - 6, 1.0) + _splash(x1 - w * 0.03, base - 4, 0.9)


def _isle_far():
    hz = 1098
    sea, seaf = c("sea"), c("sea_far")
    out = (f'<path d="M-900,{hz} H2400 V1480 H-900 Z" fill="{sea}"/>'
           f'<path d="M-900,{hz} H2400 V{hz + 30} H-900 Z" fill="{seaf}" opacity="0.8"/>'
           f'<path d="M-900,{hz} H2400" stroke="{INK}" stroke-width="8"/>'
           + _waves(-850, 2400, hz + 52, 3, 240, 54, 6))
    out += _islet(-420, hz, 260, 46) + _islet(230, hz, 160, 30) + _islet(1900, hz, 330, 58)
    out += _headland(560, 1180, 1192, 1004)
    out += _cottage(866, 1026, 0.9) + lighthouse(800, 1012, 1.0)
    # kamenny mur strazcov okolo majaka
    out += "".join(f'<path d="M{x},{1016 + (x - 700) * 0.05:.0f} q-2,-12 10,-12 q12,0 11,12 z" fill="{c("rock")}" stroke="{INK}" '
                   f'stroke-width="3"/>' for x in range(700, 760, 20))
    out += _sea_stack(1380, 1196, 190, 92) + _sea_stack(1530, 1186, 110, 62) + _sea_stack(-160, 1180, 120, 70)
    if L.time() != "night" and L.weather() != "rain":
        out += gulls(((300, 820, 1.1), (380, 790, 0.85), (1000, 700, 0.9), (1080, 730, 0.7), (1700, 760, 1.0)))
    return out


def _thrift(x, y, w, s=1.0):
    """Travnaty vankus na skale s ruzovymi kvietkami (armeria)."""
    g, gd, pk = c("grass"), c("grass_d"), c("thrift")
    h = 18 * s
    out = (f'<path d="M{x - w / 2:.0f},{y + 4:.0f} Q{x - w * 0.42:.0f},{y - h:.0f} {x:.0f},{y - h * 1.1:.0f} '
           f'Q{x + w * 0.42:.0f},{y - h:.0f} {x + w / 2:.0f},{y + 4:.0f} Z" fill="{g}" stroke="{INK}" stroke-width="5" '
           f'stroke-linejoin="round"/>'
           f'<path d="M{x - w * 0.3:.0f},{y - h * 0.3:.0f} q{w * 0.1:.0f},{-h * 0.3:.0f} {w * 0.22:.0f},{-h * 0.2:.0f}" stroke="{gd}" '
           f'stroke-width="4" fill="none" stroke-linecap="round"/>')
    n = max(2, int(w / 34))
    for k in range(n):
        fx = x - w * 0.36 + w * 0.72 * (k + 0.5) / n
        fy = y - h * (0.95 + 0.2 * math.sin(k * 2.1))
        out += (f'<path d="M{fx:.0f},{fy + 10:.0f} v-12" stroke="{gd}" stroke-width="3.5"/>'
                f'<circle cx="{fx:.0f}" cy="{fy - 4:.0f}" r="{6 * s:.1f}" fill="{pk}" stroke="{INK}" stroke-width="2.5"/>')
    return out


def _granite(x, y, w, fill=None, line=None, lichen=True, sw=6):
    """Zaobleny zulovy balvan s lisajnikmi."""
    fill, line = fill or c("rock"), line or c("rock_line")
    h = w * 0.58
    out = (f'<path d="M{x - w / 2:.0f},{y + 8:.0f} C{x - w * 0.56:.0f},{y - h * 0.8:.0f} {x - w * 0.1:.0f},{y - h * 1.12:.0f} '
           f'{x + w * 0.16:.0f},{y - h:.0f} C{x + w * 0.46:.0f},{y - h * 0.9:.0f} {x + w * 0.6:.0f},{y - h * 0.3:.0f} '
           f'{x + w / 2:.0f},{y + 8:.0f} Z" fill="{fill}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'
           f'<path d="M{x - w * 0.2:.0f},{y - h * 0.7:.0f} q{w * 0.14:.0f},{h * 0.2:.0f} {w * 0.06:.0f},{h * 0.52:.0f}" '
           f'stroke="{line}" stroke-width="{max(3, sw - 2)}" fill="none" stroke-linecap="round"/>')
    if lichen:
        lc = c("lichen", "#e0b43c")
        out += "".join(f'<ellipse cx="{x + w * dx:.0f}" cy="{y - h * dy:.0f}" rx="{w * rr:.0f}" ry="{w * rr * 0.6:.0f}" '
                       f'fill="{lc}" opacity="0.85"/>' for dx, dy, rr in ((0.12, 0.72, 0.07), (-0.24, 0.35, 0.05), (0.3, 0.4, 0.04)))
    return out


def _lichen(x, y, s, col, r):
    """Skvrna lisajnika: 2-3 prekryte elipsy (oranzova/zlta) + par sivych bodiek."""
    out = "".join(f'<ellipse cx="{x + r.uniform(-12, 12) * s:.0f}" cy="{y + r.uniform(-4, 4) * s:.0f}" '
                  f'rx="{r.uniform(10, 22) * s:.0f}" ry="{r.uniform(5, 10) * s:.0f}" fill="{col}" opacity="0.8"/>'
                  for _ in range(r.randint(2, 3)))
    return out + "".join(f'<circle cx="{x + r.uniform(-30, 30) * s:.0f}" cy="{y + r.uniform(-10, 10) * s:.0f}" r="{2.5 * s:.1f}" '
                         f'fill="#ece8df"/>' for _ in range(3))


def _tussocks(hy, x0, x1, d0, d1, col, seed, step=(40, 90)):
    """Trsy travy roztrusene v pase pod povrchom (textura travnika)."""
    r = random.Random(seed)
    out = []
    x = x0
    while x < x1:
        d = r.uniform(d0, d1)
        s = 0.8 + 1.2 * (d - d0) / max(1.0, d1 - d0)
        y = hy(x) + d
        out.append(f'M{x - 10 * s:.0f},{y:.0f} l-5,{-16 * s:.0f} M{x:.0f},{y:.0f} l1,{-21 * s:.0f} M{x + 10 * s:.0f},{y:.0f} l6,{-15 * s:.0f}')
        x += r.randint(*step)
    return f'<path d="{" ".join(out)}" stroke="{col}" stroke-width="5" fill="none" stroke-linecap="round"/>'


def _isle_near(hy, x0, x1):
    r = random.Random(211)
    rd, gd = c("rock_d"), c("grass_d")
    out = _tussocks(hy, WX0, 2800, 40, 380, c("turf_d"), 215)
    # zulove kamene zarastene v tráve (s lisajnikmi) - hlbsie v zabere su vacsie
    x = WX0 + 30
    while x < 2800:
        d = r.uniform(70, 340)
        if not (-200 < x < 380 and d < 150):
            out += _granite(x, hy(x) + d, r.uniform(46, 90) * (0.7 + d / 300.0))
        x += r.randint(170, 330)
    # trsy pozdlz povrchu
    out += "".join(L.tuft(xx, hy(xx) + 3, 1.2).replace(c("grass"), gd) for xx in range(WX0 + 10, 2800, 70))
    # jazierko v zulovej platni (pred Bobom v 1,5 s)
    px = 960
    py = hy(px) + 96
    out += (f'<path d="{ell(px, py, 150, 38)}" fill="{c("rock")}" stroke="{INK}" stroke-width="6"/>'
            f'<path d="{ell(px, py + 3, 112, 21)}" fill="{rd}" stroke="{INK}" stroke-width="4"/>'
            f'<path d="{ell(px, py + 5, 98, 15)}" fill="{c("sea_far")}" stroke="none"/>'
            f'<path d="M{px - 70},{py + 4} q16,-7 32,0 M{px + 14},{py - 2} q14,-6 28,0" stroke="#ffffff" stroke-width="4" '
            f'fill="none" stroke-linecap="round"/>'
            + _lichen(px - 110, py - 18, 0.8, c("lichen"), r) + _lichen(px + 118, py + 6, 0.7, c("lichen"), r))
    # travnate vankuse s ruzovymi kvetmi (armeria) - pevne pri ceste v 1,5 s, inak nahodne; nie za Bobom vo frame 0
    spots = [(520, 150), (790, 120), (1180, 170)]
    x = WX0 + 40
    while x < 2800:
        w = r.randint(100, 200)
        if not (-150 < x < 330) and not (380 < x < 1300):
            spots.append((x, w))
        x += w + r.randint(120, 360)
    for sx, w in spots:
        out += _thrift(sx, hy(sx) + 2, w, 1.1 + (w - 100) / 400.0)
    # vycnievajuce skalky a balvany na povrchu
    for bx, bw in ((-2900, 150), (-2350, 110), (-1580, 170), (-980, 120), (-420, 90), (640, 110), (1330, 180),
                   (1590, 100), (2050, 150), (2560, 120)):
        out += _granite(bx, hy(bx) + 2, bw)
    return out


def _isle_bd(hor, r):
    hz = hor - STAGE_HZ["isle"]
    out = (f'<path d="M-300,{hz} H1400 V{hor + 60} H-300 Z" fill="{c("sea")}"/>'
           f'<path d="M-300,{hz} H1400 V{hz + 22} H-300 Z" fill="{c("sea_far")}" opacity="0.8"/>'
           f'<path d="M-300,{hz} H1400" stroke="{INK}" stroke-width="7"/>'
           + _waves(-260, 1400, hz + 44, max(1, int((hor - hz - 40) / 50)), 230, 50, 6))
    out += _islet(120, hz, 200, 36) + _islet(560, hz, 120, 22)
    out += _headland(720, 1300, hor + 20, hz - 110)
    out += _cottage(890, hz - 86, 0.8) + lighthouse(860, hz - 96, 0.85)
    out += _sea_stack(330, hor - 30, 150, 80)
    if L.time() != "night" and L.weather() != "rain":
        out += gulls(((260, hor - 720, 1.1), (340, hor - 760, 0.9), (620, hor - 690, 1.0)))
    return out


def _isle_ground(y, x0, x1):
    r = random.Random(223)
    out = (f'<path d="M{x0},{y} H{x1} V4200 H{x0} Z" fill="{c("turf")}" stroke="{INK}" stroke-width="9"/>'
           f'<path d="M{x0},{y + 300} H{x1} V4200 H{x0} Z" fill="{c("turf_d")}" stroke="none" opacity="0.5"/>')
    out += _tussocks(lambda x: y, x0, x1, 40, 760, c("turf_d"), 227, (36, 80))
    x = x0 + 40
    while x < x1:
        d = r.uniform(80, 700)
        out += _granite(x, y + d, r.uniform(50, 100) * (0.7 + d / 500.0))
        x += r.randint(180, 360)
    x = x0 + 60
    while x < x1:
        w = r.randint(120, 240)
        out += _thrift(x + w / 2, y + 2, w)
        x += w + r.randint(160, 420)
    return out


def _isle_dressing(sd, y, xs):
    r = random.Random(sd)
    return "".join(_thrift(x, y + 2, r.randint(70, 120), 0.9) for x in xs[1::2]) + "".join(
        _granite(x + 60, y + 3, r.randint(50, 80)) for x in xs[::2])


def _isle_fore(x0, x1, gy, r):
    w = x1 - x0
    xa, xb = x0 + (0.05 + r.random() * 0.06) * w, x1 - (0.05 + r.random() * 0.06) * w
    return _granite(xa, gy + 70, 80) + _thrift(xb, gy + 66, 150, 1.2)


# ================================================================== 2) CERVENY KANON (desert/canyon)
def _wall_x(y, edge):
    """x pravej hrany steny kanona na vyske y (lomena ciara edge = [(x, y)] zhora dolu)."""
    for (xa, ya), (xb, yb) in zip(edge, edge[1:]):
        if ya <= y <= yb:
            u = 0 if yb == ya else (y - ya) / (yb - ya)
            return xa + (xb - xa) * u
    return edge[-1][0]


def canyon_wall(x_left, edge, base, sw=6.0, band=58):
    """Stena kanona s vodorovnymi vrstvami piesocnika a tmavymi pruhmi 'puste laku'."""
    rock, rd, rlight, rl = c("rock"), c("rock_d"), c("rock_l"), c("rock_line")
    top = edge[0][1]
    shape = [(x_left, base), (x_left, top)] + edge + [(edge[-1][0], base)]
    out = f'<path d="{_poly(shape)}" fill="{rock}" stroke="none"/>'
    y, k = top, 0
    while y < base:
        yb = min(base, y + band)
        xr0, xr1 = _wall_x(y, edge), _wall_x(yb, edge)
        fill = (rock, rlight, rock, rd)[k % 4]
        out += f'<path d="M{x_left},{y:.0f} H{xr0:.0f} L{xr1:.0f},{yb:.0f} H{x_left} Z" fill="{fill}" stroke="none"/>'
        out += f'<path d="M{x_left},{y:.0f} H{xr0 - 4:.0f}" stroke="{rl}" stroke-width="{sw * 0.6:.1f}" stroke-dasharray="70 16"/>'
        y, k = yb, k + 1
    rr = random.Random(int(x_left) & 255)
    for _ in range(int((edge[0][0] - x_left) / 70)):
        xx = rr.uniform(x_left + 30, edge[0][0] - 20)
        out += (f'<path d="M{xx:.0f},{top + 6:.0f} v{rr.randint(60, 200)}" stroke="{rd}" stroke-width="{rr.randint(6, 12)}" '
                f'opacity="0.45" stroke-linecap="round"/>')
    return out + f'<path d="{_poly(shape)}" fill="none" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'


def rock_arch(x, base, w, h, sw=7.0):
    """Prirodzeny skalny oblúk: hrubsia lava noha, tenka zakrivena prava, nerovny chrbat; otvorom
    (evenodd) vidno oblohu a rovinu za nim."""
    rock, rd, rl = c("rock"), c("rock_d"), c("rock_line")

    def P(fx, fy):
        return f"{x + w * fx:.0f},{base - h * fy:.0f}"
    outer = (f"M{P(-0.5, 0)} L{P(-0.46, 0.18)} L{P(-0.5, 0.34)} L{P(-0.47, 0.56)} "
             f"C{P(-0.45, 0.9)} {P(-0.2, 1.03)} {P(0.04, 1.0)} C{P(0.2, 0.99)} {P(0.3, 0.95)} {P(0.36, 0.9)} "
             f"C{P(0.48, 0.8)} {P(0.48, 0.62)} {P(0.44, 0.48)} L{P(0.48, 0.26)} L{P(0.45, 0)} Z")
    inner = (f"M{P(-0.25, 0)} L{P(-0.24, 0.3)} C{P(-0.25, 0.62)} {P(-0.12, 0.8)} {P(0.06, 0.8)} "
             f"C{P(0.2, 0.8)} {P(0.3, 0.7)} {P(0.3, 0.5)} L{P(0.31, 0.25)} L{P(0.32, 0)} Z")
    out = f'<path d="{outer} {inner}" fill="{rock}" fill-rule="evenodd" stroke="none"/>'
    # tien: prava noha a spodok klenby
    out += (f'<path d="M{P(0.32, 0)} L{P(0.31, 0.25)} L{P(0.3, 0.5)} L{P(0.44, 0.48)} L{P(0.48, 0.26)} L{P(0.45, 0)} Z" '
            f'fill="{rd}" opacity="0.85"/>'
            f'<path d="M{P(-0.24, 0.3)} C{P(-0.25, 0.62)} {P(-0.12, 0.8)} {P(0.06, 0.8)} C{P(0.2, 0.8)} {P(0.3, 0.7)} {P(0.3, 0.5)} '
            f'L{P(0.26, 0.52)} C{P(0.25, 0.68)} {P(0.18, 0.74)} {P(0.06, 0.74)} C{P(-0.1, 0.74)} {P(-0.19, 0.6)} {P(-0.19, 0.3)} Z" '
            f'fill="{rd}" opacity="0.55"/>')
    # vrstvy piesocnika
    for fy in (0.1, 0.22, 0.36, 0.5):
        out += (f'<path d="M{P(-0.47, fy)} L{P(-0.27, fy)} M{P(0.33, fy)} L{P(0.44, fy)}" stroke="{rl}" '
                f'stroke-width="{sw * 0.55:.1f}" stroke-linecap="round" stroke-dasharray="26 10"/>')
    out += (f'<path d="M{P(-0.4, 0.74)} C{P(-0.3, 0.92)} {P(0.1, 0.94)} {P(0.32, 0.84)}" stroke="{rl}" stroke-width="{sw * 0.55:.1f}" '
            f'fill="none" stroke-dasharray="40 14"/>')
    return out + f'<path d="{outer} {inner}" fill="none" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'


def hoodoo(x, base, h, w, sw=6.0):
    """Skalna veza z kopy 'knedli' s tvrdou cepicou navrchu."""
    rock, rl, cap = c("rock"), c("rock_line"), c("rock_d")
    out, y, k = "", base, 0
    segs = 4
    for i in range(segs):
        sh = h / segs
        ww = w * (1.0 - 0.18 * i) * (0.86 if i % 2 else 1.0)
        out += (f'<path d="M{x - ww / 2:.0f},{y:.0f} C{x - ww * 0.62:.0f},{y - sh * 0.5:.0f} {x - ww * 0.4:.0f},{y - sh:.0f} {x:.0f},{y - sh:.0f} '
                f'C{x + ww * 0.4:.0f},{y - sh:.0f} {x + ww * 0.62:.0f},{y - sh * 0.5:.0f} {x + ww / 2:.0f},{y:.0f} Z" fill="{rock}" '
                f'stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')
        y -= sh * 0.9
        k += 1
    out += (f'<path d="M{x - w * 0.55:.0f},{y + 6:.0f} Q{x - w * 0.5:.0f},{y - 20:.0f} {x:.0f},{y - 22:.0f} Q{x + w * 0.5:.0f},{y - 20:.0f} '
            f'{x + w * 0.55:.0f},{y + 6:.0f} Z" fill="{cap}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')
    return out + f'<path d="M{x - w * 0.2:.0f},{base - h * 0.3:.0f} v{-h * 0.2:.0f}" stroke="{rl}" stroke-width="4"/>'


def _shimmer(x0, x1, y, n=5):
    return "".join(f'<path d="M{x0 + i * (x1 - x0) / n:.0f},{y + (i % 2) * 10} q20,-6 40,0 q20,6 40,0 q20,-6 40,0" '
                   f'stroke="#fff6e4" stroke-width="4" fill="none" opacity="0.8" stroke-linecap="round"/>' for i in range(n))


def _canyon_far():
    hz = 1122
    out = (f'<path d="M-900,{hz} H2400 V1480 H-900 Z" fill="{c("far")}"/>'
           f'<path d="M-900,{hz} H2400" stroke="{INK}" stroke-width="6"/>'
           + "".join(f'<path d="M{x},{hz + 26 + (i % 3) * 18} h{90 + (i % 2) * 70}" stroke="{c("far_line")}" stroke-width="4" '
                     f'stroke-linecap="round"/>' for i, x in enumerate(range(-860, 2400, 210))))
    # jedina maly svedok na rovnom horizonte (nie pohorie)
    out += (f'<path d="M1820,{hz + 2} L1836,{hz - 40} H1950 L1966,{hz + 2} Z" fill="{c("rock_l")}" stroke="{INK}" stroke-width="4" '
            f'stroke-linejoin="round"/>')
    out += _shimmer(-700, 300, hz - 16) + _shimmer(1150, 1750, hz - 14, 4)
    edge = [(40, 640), (70, 690), (130, 700), (170, 790), (230, 812), (270, 930), (330, 1190)]
    out += canyon_wall(-900, edge, 1190)
    out += rock_arch(790, 1172, 400, 410)
    out += f'<path d="M560,1172 q60,-26 120,-6 M900,1170 q50,-22 110,-4" stroke="{c("rock_line")}" stroke-width="4" fill="none"/>'
    out += hoodoo(1070, 1176, 190, 66) + hoodoo(1150, 1180, 130, 54) + hoodoo(1740, 1160, 110, 48)
    return out


def _scrub(x, y, s=1.0):
    """Kosodrevina/palina: zhluk malych koruniek + vetvicky."""
    g, gd = c("scrub"), c("scrub_d")
    cs = [(x - 26 * s, y - 20 * s, 20 * s), (x, y - 32 * s, 26 * s), (x + 26 * s, y - 20 * s, 19 * s), (x + 8 * s, y - 14 * s, 18 * s)]
    return (f'<path d="M{x - 10 * s:.0f},{y + 4:.0f} l-6,{-16 * s:.0f} M{x + 6 * s:.0f},{y + 4:.0f} l4,{-18 * s:.0f}" stroke="{WOOD}" '
            f'stroke-width="5" stroke-linecap="round"/>'
            + puffs(cs, g, 5)
            + "".join(f'<circle cx="{x + dx * s:.0f}" cy="{y + dy * s:.0f}" r="{3 * s:.1f}" fill="{gd}"/>'
                      for dx, dy in ((-20, -26), (4, -40), (22, -24), (-4, -22), (14, -34))))


def _ledge(x, y, w, h):
    rock, rl = c("rock"), c("rock_line")
    return (f'<path d="M{x - w / 2:.0f},{y + 6:.0f} L{x - w * 0.46:.0f},{y - h:.0f} L{x + w * 0.4:.0f},{y - h * 1.05:.0f} '
            f'L{x + w / 2:.0f},{y + 6:.0f} Z" fill="{rock}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x - w * 0.44:.0f},{y - h * 0.4:.0f} H{x + w * 0.44:.0f}" stroke="{rl}" stroke-width="4" stroke-dasharray="36 12"/>')


def _canyon_near(hy, x0, x1):
    r = random.Random(307)
    out = plates(hy, WX0, 2800, 40, 320, L.mix(c("sand"), "#ffffff", 0.2), c("crack"), 17, (64, 124), 3.5)
    for bx, w, h in ((-2700, 220, 70), (-1760, 180, 56), (-1000, 240, 80), (560, 170, 50), (1420, 240, 74), (2240, 200, 60)):
        out += _ledge(bx, hy(bx) + 2, w, h)
    x = WX0 + 120
    while x < 2800:
        if not (-160 < x < 330):
            out += _scrub(x, hy(x) + 3, r.uniform(0.8, 1.2))
        x += r.randint(260, 520)
    # kotuc vyschnutej travy (tumbleweed) na ceste
    tx = 1180
    ty = hy(tx) - 30
    out += (f'<circle cx="{tx}" cy="{ty:.0f}" r="34" fill="none" stroke="{INK}" stroke-width="6"/>'
            f'<path d="M{tx - 26},{ty - 10:.0f} q20,30 46,-4 M{tx - 20},{ty + 18:.0f} q16,-36 40,-12 M{tx - 6},{ty - 30:.0f} q-10,30 18,52" '
            f'stroke="{c("scrub_d")}" stroke-width="4" fill="none"/>')
    return out


def _canyon_bd(hor, r):
    hz = hor - STAGE_HZ["canyon"]
    out = (f'<path d="M-300,{hz} H1400 V{hor + 60} H-300 Z" fill="{c("far")}"/>'
           f'<path d="M-300,{hz} H1400" stroke="{INK}" stroke-width="6"/>' + _shimmer(300, 900, hz - 14, 4))
    edge = [(120, hz - 470), (150, hz - 420), (210, hz - 408), (250, hz - 300), (300, hz - 280), (330, hz - 140), (380, hor + 60)]
    out += canyon_wall(-300, edge, hor + 60)
    out += rock_arch(800, hz + 36, 300, 320) + hoodoo(1010, hz + 30, 150, 56)
    return out


def _canyon_ground(y, x0, x1):
    out = (f'<path d="M{x0},{y} H{x1} V4200 H{x0} Z" fill="{c("sand")}" stroke="{INK}" stroke-width="9"/>'
           f'<path d="M{x0},{y + 300} H{x1} V4200 H{x0} Z" fill="{c("sand_d")}" stroke="none" opacity="0.5"/>')
    return out + plates(lambda x: y, x0, x1, 46, 760, L.mix(c("sand"), "#ffffff", 0.2), c("crack"), 29, (80, 190), 4)


def _canyon_dressing(sd, y, xs):
    r = random.Random(sd)
    return "".join(_scrub(x, y + 3, r.uniform(0.8, 1.1)) for x in xs[::2]) + "".join(
        _ledge(x + 40, y + 2, r.randint(70, 110), r.randint(26, 40)) for x in xs[1::2])


def _canyon_fore(x0, x1, gy, r):
    w = x1 - x0
    xa, xb = x0 + (0.05 + r.random() * 0.06) * w, x1 - (0.05 + r.random() * 0.06) * w
    return _ledge(xa, gy + 70, 120, 40) + _scrub(xb, gy + 66, 1.3)


# ================================================================== 3) DZUNGLA S RUINAMI (forest/jungle)
def crown(x, y, w, h, fill, sw=6, seed=0):
    """Koruna tropickeho stromu: zjednotenie kruhov (siroka, plocha)."""
    r = random.Random(seed)
    cs = [(x + w * (i / 5.0 - 0.5), y + r.uniform(-h * 0.15, h * 0.15), h * r.uniform(0.34, 0.5)) for i in range(6)]
    cs += [(x + r.uniform(-w * 0.2, w * 0.2), y - h * 0.3, h * 0.45)]
    return puffs(cs, fill, sw)


def temple(x, base, w, h, sw=6.0):
    """Stupnovity chram (pyramida so svatynou) prerasteny machom a lianami."""
    st, sd, sl, moss, vine = c("stone"), c("stone_d"), c("stone_line"), c("moss"), c("vine")
    tiers = 5
    th = h * 0.8 / tiers
    out = ""
    for i in range(tiers):
        ww = w * (1 - i * 0.16)
        y0 = base - i * th
        out += (f'<path d="M{x - ww / 2:.0f},{y0:.0f} L{x - ww / 2 + 10:.0f},{y0 - th:.0f} H{x + ww / 2 - 10:.0f} L{x + ww / 2:.0f},{y0:.0f} Z" '
                f'fill="{st}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'
                f'<path d="M{x + ww * 0.22:.0f},{y0:.0f} L{x + ww * 0.22:.0f},{y0 - th:.0f} H{x + ww / 2 - 10:.0f} L{x + ww / 2:.0f},{y0:.0f} Z" '
                f'fill="{sd}" opacity="0.6"/>'
                f'<path d="M{x - ww / 2 + 16:.0f},{y0 - th * 0.5:.0f} H{x + ww / 2 - 16:.0f}" stroke="{sl}" stroke-width="3.5" '
                f'stroke-dasharray="26 14"/>')
    # schodisko v strede
    sw_ = w * 0.14
    top = base - tiers * th
    out += (f'<path d="M{x - sw_ / 2:.0f},{base:.0f} L{x - sw_ * 0.4:.0f},{top:.0f} H{x + sw_ * 0.4:.0f} L{x + sw_ / 2:.0f},{base:.0f} Z" '
            f'fill="{L.mix(st, "#ffffff", 0.15)}" stroke="{INK}" stroke-width="{sw * 0.8:.1f}"/>'
            + "".join(f'<path d="M{x - sw_ * 0.45:.0f},{base - k * (base - top) / 12:.0f} h{sw_ * 0.9:.0f}" stroke="{sl}" '
                      f'stroke-width="3"/>' for k in range(1, 12)))
    # svatyna so vchodom a hrebenom
    hw, hh = w * 0.3, h * 0.2
    out += (f'<path d="M{x - hw / 2:.0f},{top:.0f} V{top - hh:.0f} H{x + hw / 2:.0f} V{top:.0f} Z" fill="{st}" stroke="{INK}" '
            f'stroke-width="{sw}" stroke-linejoin="round"/>'
            f'<path d="M{x - hw * 0.16:.0f},{top:.0f} V{top - hh * 0.62:.0f} H{x + hw * 0.16:.0f} V{top:.0f} Z" fill="#3a3a32" '
            f'stroke="{INK}" stroke-width="{sw * 0.7:.1f}"/>'
            f'<path d="M{x - hw * 0.36:.0f},{top - hh:.0f} L{x - hw * 0.22:.0f},{top - hh * 1.5:.0f} H{x + hw * 0.22:.0f} '
            f'L{x + hw * 0.36:.0f},{top - hh:.0f} Z" fill="{sd}" stroke="{INK}" stroke-width="{sw * 0.8:.1f}" stroke-linejoin="round"/>')
    # mach a kriky na terasach + liany dole zo svatyne
    r = random.Random(int(x))
    for i in range(tiers):
        ww = w * (1 - i * 0.16)
        y0 = base - (i + 1) * th
        for _ in range(2):
            mx = x + r.uniform(-ww * 0.45, ww * 0.45)
            out += puffs([(mx, y0 + 2, r.uniform(10, 18)), (mx + 16, y0 + 4, r.uniform(8, 14))], moss, 4)
    out += (f'<path d="M{x + hw * 0.4:.0f},{top - hh + 4:.0f} q16,50 -6,110 q-14,40 6,80" stroke="{vine}" stroke-width="5" fill="none" '
            f'stroke-linecap="round"/>'
            f'<path d="M{x - hw * 0.44:.0f},{top - hh + 8:.0f} q-18,40 2,90" stroke="{vine}" stroke-width="5" fill="none" '
            f'stroke-linecap="round"/>')
    return out


def vine(x, y0, y1, sway=40, leaf=None, sw=6):
    """Liana visiaca zhora: vlnita ciara s lístkami."""
    leaf = leaf or c("leaf")
    col = c("vine")
    L_ = y1 - y0
    d = f"M{x:.0f},{y0:.0f} C{x + sway:.0f},{y0 + L_ * 0.35:.0f} {x - sway:.0f},{y0 + L_ * 0.65:.0f} {x + sway * 0.3:.0f},{y1:.0f}"
    out = f'<path d="{d}" stroke="{col}" stroke-width="{sw}" fill="none" stroke-linecap="round"/>'
    for k in range(1, 6):
        u = k / 6.0
        lx = x + sway * (3 * u * (1 - u) ** 2 - 3 * u * u * (1 - u)) + sway * 0.3 * u ** 3
        ly = y0 + L_ * u
        s = -1 if k % 2 else 1
        out += (f'<path d="M{lx:.0f},{ly:.0f} q{12 * s},-12 {24 * s},-4 q-10,{10} {-24 * s},4 z" fill="{leaf}" stroke="{INK}" '
                f'stroke-width="3" stroke-linejoin="round"/>')
    return out


def _canopy_top(x0, x1, edge_y, seed=3, sw=6):
    """Tmava klenba listia zhora (namiesto oblohy) so zubatym spodkom z korun."""
    r = random.Random(seed)
    cs = []
    x = x0
    while x < x1:
        cs.append((x, edge_y + r.uniform(-40, 30), r.uniform(60, 110)))
        x += r.randint(70, 130)
    rects = [(x0 - 40, -1200, x1 - x0 + 80, edge_y + 1200 - 40)]
    out = puffs(cs, c("canopy_d"), sw, rects)
    out += "".join(f'<path d="M{cx - rr * 0.4:.0f},{cy + rr * 0.3:.0f} q{rr * 0.3:.0f},{rr * 0.2:.0f} {rr * 0.6:.0f},0" stroke="{c("canopy")}" '
                   f'stroke-width="5" fill="none" stroke-linecap="round"/>' for cx, cy, rr in cs[::2])
    return out


def _jungle_far():
    X0, X1 = -900, 2400
    out = f'<path d="M{X0},-1200 H{X1} V1480 H{X0} Z" fill="{c("haze")}"/>'
    # luce svetla cez koruny
    out += "".join(f'<path d="M{x},{-100} L{x + 70},{-100} L{x + 330},{1190} L{x + 170},{1190} Z" fill="{c("ray")}" opacity="0.28"/>'
                   for x in (-300, 380, 1180, 1900))
    # vzdialena bleda vrstva stromov
    r = random.Random(71)
    far_l = ""
    x = X0
    while x < X1:
        far_l += crown(x, r.uniform(760, 900), r.uniform(220, 320), r.uniform(120, 170), c("pine_far"), 4, int(x) & 1023)
        x += r.randint(170, 260)
    out += far_l + "".join(f'<path d="M{x},{960} V1190" stroke="{c("pine_far_line")}" stroke-width="{r.randint(10, 18)}"/>'
                           for x in range(X0 + 60, X1, 190))
    out += f'<path d="M{X0},1176 H{X1} V1480 H{X0} Z" fill="{c("floor")}" stroke="{INK}" stroke-width="5"/>'
    # chram v strede
    out += temple(820, 1180, 560, 470)
    # stredna vrstva stromov po stranach (kmene s koreňmi + koruny)
    for tx, top, tw in ((-620, 520, 30), (-260, 600, 26), (60, 470, 34), (1300, 520, 32), (1560, 600, 28), (1900, 480, 36),
                        (2240, 560, 30)):
        out += (f'<path d="M{tx - tw / 2},{1182} L{tx - tw * 0.35:.0f},{top + 60} H{tx + tw * 0.35:.0f} L{tx + tw / 2},{1182} Z" '
                f'fill="{c("trunk")}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
                f'<path d="M{tx - tw * 1.4:.0f},1184 Q{tx - tw * 0.6:.0f},1170 {tx - tw * 0.4:.0f},1120 M{tx + tw * 1.4:.0f},1184 '
                f'Q{tx + tw * 0.6:.0f},1170 {tx + tw * 0.4:.0f},1120" fill="none" stroke="{INK}" stroke-width="5"/>')
        out += crown(tx, top, tw * 9, tw * 5.5, c("canopy"), 6, tx & 1023)
    # klenba listia zhora + liany
    out += _canopy_top(X0 - 60, X1 + 60, 190, 5)
    for vx, y1 in ((-500, 640), (-80, 520), (300, 760), (560, 480), (1080, 700), (1420, 560), (1760, 820), (2100, 600)):
        out += vine(vx, 170, y1, 36)
    return out + _dim(X0, -1200, X1, 1480)


def _dim(x0, y0, x1, y1):
    """Prales nema oblohu - vecer/noc sa ukaze len stmavenim celej vrstvy."""
    if L.night():
        return f'<path d="M{x0},{y0} H{x1} V{y1} H{x0} Z" fill="#1c2733" opacity="0.5"/>'
    if L.dusk():
        return f'<path d="M{x0},{y0} H{x1} V{y1} H{x0} Z" fill="#e0904a" opacity="0.16"/>'
    return ""


def banana(x, y, s=1.0, flip=1):
    """Siroke tropicke listy (banan / filodendron) zo spolocneho miesta: stopka, siroka cepel, zilky."""
    lf, ld = c("leaf"), c("leaf_d")
    out = ""
    for a, L_ in ((-72, 120), (-38, 170), (-4, 155), (32, 135), (64, 105)):
        rad = math.radians(a * flip - 90)
        ux, uy = math.cos(rad), math.sin(rad)
        nx, ny = -uy, ux
        sx, sy = x + ux * L_ * s * 0.28, y + uy * L_ * s * 0.28
        ex, ey = x + ux * L_ * s, y + uy * L_ * s
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        W = L_ * s * 0.42
        out += (f'<path d="M{x:.0f},{y:.0f} L{sx:.0f},{sy:.0f}" stroke="{ld}" stroke-width="6" stroke-linecap="round"/>'
                f'<path d="M{sx:.0f},{sy:.0f} Q{mx + nx * W:.0f},{my + ny * W:.0f} {ex:.0f},{ey:.0f} '
                f'Q{mx - nx * W:.0f},{my - ny * W:.0f} {sx:.0f},{sy:.0f} Z" fill="{lf}" stroke="{INK}" stroke-width="5" '
                f'stroke-linejoin="round"/>'
                f'<path d="M{sx:.0f},{sy:.0f} L{ex:.0f},{ey:.0f}" stroke="{ld}" stroke-width="4"/>')
        for u in (0.3, 0.52, 0.74):
            px, py = sx + (ex - sx) * u, sy + (ey - sy) * u
            k = W * 0.42 * (1 - abs(u - 0.5))
            out += (f'<path d="M{px:.0f},{py:.0f} l{(nx + ux * 0.6) * k:.0f},{(ny + uy * 0.6) * k:.0f} '
                    f'M{px:.0f},{py:.0f} l{(-nx + ux * 0.6) * k:.0f},{(-ny + uy * 0.6) * k:.0f}" stroke="{ld}" stroke-width="3"/>')
    return out


def jungle_tree(hy, x, w, sw=7):
    """Obrovsky kmen s doskovymi korenmi a lianou (koruna je nad zaberom - klenba vo far vrstve)."""
    tr, td, vn = c("trunk"), c("trunk_d"), c("vine")
    y = hy(x)
    top = y - 1700
    out = (f'<path d="M{x - w / 2:.0f},{y + 8:.0f} L{x - w * 0.36:.0f},{top:.0f} H{x + w * 0.36:.0f} L{x + w / 2:.0f},{y + 8:.0f} Z" '
           f'fill="{tr}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')
    # doskove korene
    for s in (-1, 1):
        out += (f'<path d="M{x + s * w * 0.3:.0f},{y - 160:.0f} Q{x + s * w * 0.5:.0f},{y - 40:.0f} {x + s * w * 1.5:.0f},{hy(x + s * w * 1.5) + 8:.0f} '
                f'L{x + s * w * 0.4:.0f},{y + 8:.0f} Z" fill="{tr}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')
    out += "".join(f'<path d="M{x - w * 0.2 + k * w * 0.2:.0f},{y - 120 - k * 40:.0f} v{-160 - k * 60}" stroke="{td}" stroke-width="5" '
                   f'stroke-linecap="round"/>' for k in range(3))
    # liana ovinuta okolo kmena
    out += (f'<path d="M{x - w * 0.4:.0f},{y - 60:.0f} C{x + w * 0.6:.0f},{y - 180:.0f} {x - w * 0.6:.0f},{y - 380:.0f} {x + w * 0.4:.0f},{y - 520:.0f} '
            f'C{x + w * 0.8:.0f},{y - 620:.0f} {x - w * 0.5:.0f},{y - 760:.0f} {x + w * 0.2:.0f},{y - 900:.0f}" stroke="{vn}" stroke-width="7" '
            f'fill="none" stroke-linecap="round"/>')
    # drevokazna huba
    out += (f'<path d="M{x + w * 0.36:.0f},{y - 300:.0f} q34,-4 40,14 q-20,8 -40,4 z" fill="#d9b36a" stroke="{INK}" stroke-width="4" '
            f'stroke-linejoin="round"/>')
    return out


def stela(x, y, w=92, h=260, tilt=4.0):
    """Tesana kamenna stela s glyfmi, mach navrchu."""
    st, sl, moss = c("stone"), c("stone_line"), c("moss")
    g = (f'<path d="M{-w / 2:.0f},8 V{-h:.0f} Q0,{-h - 26:.0f} {w / 2:.0f},{-h:.0f} V8 Z" fill="{st}" stroke="{INK}" stroke-width="7" '
         f'stroke-linejoin="round"/>')
    for k in range(3):
        yy = -h + 40 + k * 70
        g += (f'<path d="M{-w * 0.32:.0f},{yy} h{w * 0.64:.0f} v48 h{-w * 0.64:.0f} z" fill="none" stroke="{sl}" stroke-width="4"/>'
              f'<circle cx="{-w * 0.12:.0f}" cy="{yy + 20}" r="8" fill="none" stroke="{sl}" stroke-width="4"/>'
              f'<path d="M{w * 0.06:.0f},{yy + 12} q10,18 18,0 M{w * 0.06:.0f},{yy + 34} h18" stroke="{sl}" stroke-width="4" fill="none"/>')
    g += puffs([(-w * 0.3, -h + 2, 16), (-w * 0.05, -h - 12, 20), (w * 0.28, -h, 14)], moss, 4)
    return f'<g transform="translate({x:.0f},{y:.0f}) rotate({tilt})">{g}</g>'


def carved_block(x, y, w=110, rot=-6.0):
    st, sl, moss = c("stone"), c("stone_line"), c("moss")
    g = (f'<path d="M{-w / 2:.0f},6 V{-w * 0.8:.0f} H{w / 2:.0f} V6 Z" fill="{st}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
         f'<path d="M0,{-w * 0.4:.0f} m-22,0 a22,22 0 1 1 44,0 a14,14 0 1 1 -28,0 a6,6 0 1 1 12,0" fill="none" stroke="{sl}" '
         f'stroke-width="4"/>' + puffs([(-w * 0.3, -w * 0.8, 12), (-w * 0.1, -w * 0.84, 10)], moss, 3))
    return f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot})">{g}</g>'


def root(hy, x, ln, sw=16, bend=30):
    """Koren plaziaci sa po povrchu (obrys + drevo)."""
    pts = [(x + ln * u, hy(x + ln * u) + 6 + bend * math.sin(u * math.pi) * (0.3 if ln > 0 else -0.3)) for u in [i / 8.0 for i in range(9)]]
    d = _poly(pts, False)
    return (f'<path d="{d}" stroke="{INK}" stroke-width="{sw + 9}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" stroke="{c("trunk")}" stroke-width="{sw}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')


def _jungle_near(hy, x0, x1):
    r = random.Random(401)
    out = ""
    # lístie, mach a korienky v zemi
    fs = c("floor_sub")
    x = WX0
    while x < 2800:
        d = r.uniform(30, 380)
        y = hy(x) + d
        s = 0.9 + d / 220.0
        out += (f'<path d="M{x:.0f},{y:.0f} q{16 * s:.0f},{-13 * s:.0f} {34 * s:.0f},0 q{-16 * s:.0f},{12 * s:.0f} {-34 * s:.0f},0 z" '
                f'fill="{r.choice((c("leaf_d"), fs, c("needle"), c("leaf")))}" opacity="0.85" '
                f'transform="rotate({r.randint(-40, 40)} {x:.0f} {y:.0f})"/>')
        x += r.randint(20, 48)
    # korene krizom cez chodnik (aj mimo stromov)
    for rx_, ln in ((620, 280), (900, -220), (-300, 260), (-1900, 300), (1500, 240), (2200, -260)):
        out += root(hy, rx_, ln, 14)
    x = WX0
    while x < 2800:
        out += f'<path d="{ell(x, hy(x) + r.uniform(20, 60), r.uniform(40, 90), r.uniform(8, 14))}" fill="{c("moss")}" opacity="0.75"/>'
        x += r.randint(260, 520)
    for tx, w in ((-2900, 76), (-2150, 64), (-1380, 82), (-640, 70), (1240, 80), (1900, 68), (2580, 74)):
        out += root(hy, tx - w * 1.3, -r.randint(160, 260)) + root(hy, tx + w * 1.3, r.randint(160, 300))
        out += jungle_tree(hy, tx, w)
    out += stela(1010, hy(1010) + 4) + carved_block(500, hy(500) + 4, 96, -8) + carved_block(-1720, hy(-1720) + 4, 120, 6)
    out += carved_block(2240, hy(2240) + 4, 104, -4)
    # paprade pozdlz cesty (drobny podrast medzi velkymi listami)
    import worlds_ext as X
    x = WX0 + 30
    while x < 2800:
        out += X.fern(x, hy(x) + 5, r.uniform(0.9, 1.4), c("leaf_d"))
        x += r.randint(90, 190)
    x = WX0 + 80
    k = 0
    while x < 2800:
        if not (-200 < x < 380) and not (560 < x < 800) and not (930 < x < 1090):
            out += banana(x, hy(x) + 6, r.uniform(0.75, 1.1), 1 if k % 2 else -1)
        x += r.randint(260, 480)
        k += 1
    return out


def _jungle_bd(hor, r):
    out = f'<path d="M-300,-100 H1400 V{hor + 60} H-300 Z" fill="{c("haze")}"/>'
    out += "".join(f'<path d="M{x},-100 L{x + 60},-100 L{x + 300},{hor} L{x + 160},{hor} Z" fill="{c("ray")}" opacity="0.28"/>'
                   for x in (80, 700))
    for x in range(-280, 1400, 180):
        out += crown(x, hor - 420 + (x * 7) % 60, 260, 150, c("pine_far"), 4, x & 1023)
    out += f'<path d="M-300,{hor - 40} H1400 V{hor + 60} H-300 Z" fill="{c("floor")}" stroke="{INK}" stroke-width="5"/>'
    out += temple(560, hor - 36, 420, 360)
    for tx, top, tw in ((20, hor - 600, 34), (1040, hor - 640, 36)):
        out += (f'<path d="M{tx - tw / 2},{hor - 30} L{tx - tw * 0.35:.0f},{top + 60} H{tx + tw * 0.35:.0f} L{tx + tw / 2},{hor - 30} Z" '
                f'fill="{c("trunk")}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
                + crown(tx, top, tw * 9, tw * 5, c("canopy"), 6, tx & 1023))
    out += _canopy_top(-340, 1440, 170, 9)
    for vx, y1 in ((160, 560), (420, 420), (880, 620), (1180, 480)):
        out += vine(vx, 150, y1, 30)
    return out + _dim(-300, -100, 1400, hor + 60)


def _jungle_ground(y, x0, x1):
    r = random.Random(419)
    out = (f'<path d="M{x0},{y} H{x1} V4200 H{x0} Z" fill="{c("floor")}" stroke="{INK}" stroke-width="9"/>'
           f'<path d="M{x0},{y + 280} H{x1} V4200 H{x0} Z" fill="{c("floor_sub")}" stroke="none" opacity="0.5"/>')
    for _ in range(90):
        x, yy = r.uniform(x0, x1), y + r.uniform(20, 800)
        out += (f'<path d="M{x:.0f},{yy:.0f} q12,-10 26,0 q-12,9 -26,0 z" fill="{r.choice((c("leaf_d"), c("needle")))}" opacity="0.7" '
                f'transform="rotate({r.randint(-40, 40)} {x:.0f} {yy:.0f})"/>')
    x = x0 + 100
    while x < x1:
        out += (f'<path d="M{x},{y + 4} q60,40 150,36 q70,-2 120,30" stroke="{c("trunk")}" stroke-width="14" fill="none" '
                f'stroke-linecap="round"/>')
        x += r.randint(500, 900)
    return out


def _jungle_dressing(sd, y, xs):
    r = random.Random(sd)
    return "".join(banana(x, y + 6, r.uniform(0.45, 0.6), 1 if i % 2 else -1) for i, x in enumerate(xs[::2]))


def _jungle_fore(x0, x1, gy, r):
    w = x1 - x0
    xa, xb = x0 + (0.03 + r.random() * 0.05) * w, x1 - (0.03 + r.random() * 0.05) * w
    return banana(xa, gy + 110, 0.8, -1) + banana(xb, gy + 110, 0.9, 1)


# ================================================================== 4) GEJZIROVE POLE (hill/geyser)
def volcano(x, base, w, h, sw=6.0):
    """Jeden siroky kuzel so zarezom krateru, zlabmi a zarou v kratere."""
    cone, cl = c("cone"), c("cone_line")
    lx, rx, ty = x - w / 2, x + w / 2, base - h
    d = (f"M{lx:.0f},{base:.0f} C{lx + w * 0.2:.0f},{base - h * 0.08:.0f} {x - w * 0.12:.0f},{ty + h * 0.26:.0f} {x - w * 0.05:.0f},{ty:.0f} "
         f"L{x - w * 0.02:.0f},{ty + h * 0.04:.0f} L{x + w * 0.025:.0f},{ty + h * 0.045:.0f} L{x + w * 0.05:.0f},{ty + h * 0.01:.0f} "
         f"C{x + w * 0.12:.0f},{ty + h * 0.26:.0f} {rx - w * 0.2:.0f},{base - h * 0.08:.0f} {rx:.0f},{base:.0f} Z")
    out = f'<path d="{d}" fill="{cone}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'
    for k, f in enumerate((-0.3, -0.16, 0.1, 0.24, 0.36)):
        gx = x + w * f
        out += (f'<path d="M{x + w * f * 0.12:.0f},{ty + h * 0.08:.0f} Q{x + w * f * 0.6:.0f},{ty + h * 0.5:.0f} {gx:.0f},{base - h * 0.06:.0f}" '
                f'stroke="{cl}" stroke-width="{sw * 0.6:.1f}" fill="none" stroke-linecap="round" stroke-dasharray="{60 + k * 10} 20"/>')
    out += (f'<path d="M{x - w * 0.02:.0f},{ty + h * 0.035:.0f} L{x + w * 0.025:.0f},{ty + h * 0.04:.0f}" stroke="{c("lava")}" '
            f'stroke-width="{sw:.0f}" stroke-linecap="round" opacity="0.8"/>')
    return out


def plume(pts, fill, hl, sw=6):
    """Oblak popola/pary z bodov (x, y, r) - obrys len okolo celku + svetle temena."""
    return puffs(pts, fill, sw) + "".join(
        f'<path d="M{x - r * 0.5:.0f},{y - r * 0.45:.0f} q{r * 0.3:.0f},{-r * 0.3:.0f} {r * 0.7:.0f},{-r * 0.15:.0f}" stroke="{hl}" '
        f'stroke-width="{max(3, r * 0.08):.1f}" fill="none" stroke-linecap="round"/>' for x, y, r in pts[::2])


def steam_column(x, y, h, w=30, sw=5, drift=0.35):
    """Stlpec pary z prieduchu: prekryte chumace (ziadne 'koralky'), smerom hore sirsie a unasane vetrom."""
    pts, yy, i = [], y, 0
    while y - yy < h:
        u = (y - yy) / float(h)
        rr = w * (0.6 + 1.3 * u)
        pts.append((x + drift * h * u * u + 5 * math.sin(i * 2.1), yy - rr * 0.5, rr))
        yy -= rr * 1.05
        i += 1
    return puffs(pts, c("steam"), sw) + "".join(
        f'<path d="M{px - rr * 0.45:.0f},{py - rr * 0.4:.0f} q{rr * 0.3:.0f},{-rr * 0.25:.0f} {rr * 0.65:.0f},{-rr * 0.1:.0f}" '
        f'stroke="#ffffff" stroke-width="{max(2.5, rr * 0.07):.1f}" fill="none" stroke-linecap="round"/>' for px, py, rr in pts[1::2])


def _geyser_far():
    hz = 1150
    out = (f'<path d="M-900,{hz} H2400 V1480 H-900 Z" fill="{c("plain")}"/>'
           f'<path d="M-900,{hz} H2400" stroke="{INK}" stroke-width="6"/>'
           + "".join(f'<path d="M{x},{hz + 24 + (i % 3) * 22} q60,-10 130,2 q50,10 110,-2" stroke="{c("rock_line")}" stroke-width="4" '
                     f'fill="none" opacity="0.7"/>' for i, x in enumerate(range(-860, 2400, 260))))
    out += volcano(1010, hz + 2, 1240, 380)
    out += plume([(1008, 752, 36), (1004, 706, 44), (1016, 656, 52), (1040, 606, 60), (1076, 560, 68), (1122, 520, 74),
                  (1180, 490, 80), (1248, 470, 84), (1320, 462, 80)], c("ash"), c("ash_l"), 6)
    for sx, sh in ((-380, 230), (240, 170), (1760, 260), (2150, 180)):
        out += steam_column(sx, hz - 4, sh, 16, 4)
    return out


def geyser(x, y, h=640, sw=7):
    """Sinterovy kopcek + vystrelujuci stlpec vody (smerom hore sirsi, rozstrapkany) s parou navrchu."""
    sn, sl = c("sinter"), c("sinter_line")
    out = (f'<path d="M{x - 160},{y + 8} Q{x - 118},{y - 40} {x - 44},{y - 50} H{x + 44} Q{x + 118},{y - 40} {x + 160},{y + 8} Z" '
           f'fill="{sn}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'
           f'<path d="M{x - 118},{y - 14} q50,-18 90,-20 M{x + 30},{y - 32} q50,4 84,20" stroke="{sl}" stroke-width="5" fill="none"/>')
    top = y - 50 - h
    n = 12
    left = [(x - 24 - 50 * (i / n) ** 1.3 - 9 * math.sin(i * 1.7), y - 46 - h * i / n) for i in range(n + 1)]
    right = [(x + 24 + 50 * (i / n) ** 1.3 + 9 * math.sin(i * 1.3 + 1), y - 46 - h * i / n) for i in range(n, -1, -1)]
    col = (f'<path d="{_poly(left + right)}" fill="#eaf6fb" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'
           f'<path d="{_poly([(px + 26 + 30 * (i / n), py) for i, (px, py) in enumerate(left[1:-2])], False)}" stroke="#bfe3f0" '
           f'stroke-width="10" fill="none" stroke-linecap="round"/>')
    # rozstrek pri prieduchu: penovy lem + kvapky do stran
    splash = (f'<path d="{ell(x, y - 50, 70, 13)}" fill="#f4fbfe" stroke="{INK}" stroke-width="5"/>'
              + "".join(f'<path d="M{x + dx},{y - 50} q{dx * 0.4:.0f},-50 {dx * 0.9:.0f},-26" stroke="#dff1f8" stroke-width="7" '
                        f'fill="none" stroke-linecap="round"/>' for dx in (-60, -34, 34, 60)))
    top_pts = [(x - 80, top + 70, 64), (x, top + 10, 84), (x + 86, top + 60, 66), (x - 150, top + 120, 46), (x + 156, top + 112, 48),
               (x - 30, top - 70, 72), (x + 56, top - 112, 78), (x - 64, top - 176, 62), (x + 24, top - 226, 60)]
    drops = "".join(f'<path d="M{x + dx},{top + dy} q6,10 0,16 q-6,-6 0,-16 z" fill="#dff1f8" stroke="{INK}" stroke-width="3"/>'
                    for dx, dy in ((-130, 200), (120, 220), (-100, 300), (140, 320), (-160, 380), (90, 420)))
    return out + col + splash + plume(top_pts, c("steam"), "#ffffff", sw - 1) + drops


def hot_pool(x, y, rx=130, ry=28):
    """Horuce jazierko: hrdzavy okraj -> sinter -> tyrkys -> hlboky stred; para nad nim."""
    return (f'<path d="{ell(x, y, rx, ry)}" fill="{c("rust")}" stroke="{INK}" stroke-width="6"/>'
            f'<path d="{ell(x, y + 1, rx * 0.86, ry * 0.8)}" fill="{c("sinter")}" stroke="none"/>'
            f'<path d="{ell(x, y + 2, rx * 0.72, ry * 0.64)}" fill="{c("pool")}" stroke="none"/>'
            f'<path d="{ell(x, y + 3, rx * 0.36, ry * 0.32)}" fill="{c("pool_d")}" stroke="none"/>'
            f'<path d="M{x - rx * 0.5:.0f},{y - 2:.0f} q14,-6 28,0" stroke="#ffffff" stroke-width="4" fill="none" stroke-linecap="round"/>'
            f'<g opacity="0.85">{steam_column(x - 20, y - 12, 110, 16, 4, 0.5)}</g>')


def fumarole(x, y, s=1.0):
    crust = c("crust")
    return (f'<path d="M{x - 46 * s:.0f},{y + 4:.0f} q{46 * s:.0f},{-30 * s:.0f} {92 * s:.0f},0 z" fill="{crust}" stroke="{INK}" '
            f'stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="{ell(x, y - 6 * s, 12 * s, 5 * s)}" fill="#3a3330" stroke="{INK}" stroke-width="3"/>'
            + steam_column(x, y - 20 * s, 150 * s, 14 * s, 4))


def warning_sign(x, y):
    return (f'<path d="M{x},{y + 6} V{y - 150}" stroke="{WOOD}" stroke-width="10" stroke-linecap="round"/>'
            f'<path d="M{x},{y - 230} L{x + 46},{y - 150} H{x - 46} Z" fill="#f4d23a" stroke="#c0392b" stroke-width="9" '
            f'stroke-linejoin="round"/>'
            f'<path d="M{x},{y - 206} v34" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>'
            f'<circle cx="{x}" cy="{y - 160}" r="5" fill="{INK}"/>')


def _geyser_near(hy, x0, x1):
    r = random.Random(503)
    out = plates(hy, WX0, 2800, 36, 310, L.mix(c("ground"), "#ffffff", 0.08), c("rock_line"), 41, (90, 170), 4.5, 0.5, 0.35)
    # sirne kury a hrdzave skvrny
    x = WX0
    while x < 2800:
        y = hy(x) + r.uniform(20, 260)
        col = r.choice((c("crust"), c("rust"), c("crust")))
        out += (f'<path d="{ell(x, y, r.uniform(20, 46), r.uniform(6, 12))}" fill="{col}" opacity="0.85"/>')
        x += r.randint(90, 240)
    rk = L.mix(c("rock"), "#ffffff", 0.14)
    for bx, bw in ((-2800, 120), (-2000, 90), (-1240, 140), (-520, 80), (560, 96), (1560, 120), (2300, 110)):
        out += _granite(bx, hy(bx) + 2, bw, rk, c("rock_line"), lichen=False)
    for fx, s in ((-2400, 1.0), (-1500, 1.2), (-760, 0.9), (420, 1.0), (1760, 1.1), (2500, 0.9)):
        out += fumarole(fx, hy(fx) + 2, s)
    out += geyser(990, hy(990) + 2, 600)
    out += hot_pool(790, hy(790) + 96)
    out += warning_sign(1250, hy(1250) + 2)
    return out


def _geyser_bd(hor, r):
    hz = hor - STAGE_HZ["geyser"]
    out = (f'<path d="M-300,{hz} H1400 V{hor + 60} H-300 Z" fill="{c("plain")}"/>'
           f'<path d="M-300,{hz} H1400" stroke="{INK}" stroke-width="6"/>')
    out += volcano(640, hz + 2, 860, 330)
    out += plume([(640, hz - 350, 34), (632, hz - 392, 42), (646, hz - 440, 50), (676, hz - 488, 58), (718, hz - 530, 66),
                  (774, hz - 562, 72), (840, hz - 580, 74)], c("ash"), c("ash_l"), 6)
    out += steam_column(90, hz - 2, 200, 16, 4) + steam_column(1060, hz - 2, 240, 18, 4)
    return out


def _geyser_ground(y, x0, x1):
    out = (f'<path d="M{x0},{y} H{x1} V4200 H{x0} Z" fill="{c("ground")}" stroke="{INK}" stroke-width="9"/>'
           f'<path d="M{x0},{y + 260} H{x1} V4200 H{x0} Z" fill="{c("ground_sub")}" stroke="none" opacity="0.6"/>')
    out += plates(lambda x: y, x0, x1, 46, 760, L.mix(c("ground"), "#ffffff", 0.08), c("rock_line"), 53, (110, 230), 5, 0.5, 0.35)
    r = random.Random(59)
    for _ in range(26):
        x, yy = r.uniform(x0, x1), y + r.uniform(30, 500)
        out += f'<path d="{ell(x, yy, r.uniform(24, 56), r.uniform(7, 14))}" fill="{r.choice((c("crust"), c("rust")))}" opacity="0.75"/>'
    return out


def _geyser_dressing(sd, y, xs):
    r = random.Random(sd)
    return "".join(fumarole(x, y + 2, r.uniform(0.6, 0.8)) for x in xs[::2]) + "".join(
        _granite(x + 40, y + 3, r.randint(40, 70), c("rock"), c("rock_line"), lichen=False) for x in xs[1::2])


def _geyser_fore(x0, x1, gy, r):
    w = x1 - x0
    xa, xb = x0 + (0.05 + r.random() * 0.06) * w, x1 - (0.05 + r.random() * 0.06) * w
    return (_granite(xa, gy + 70, 90, c("rock"), c("rock_line"), lichen=False)
            + f'<path d="{ell(xb, gy + 80, 70, 14)}" fill="{c("crust")}" stroke="{INK}" stroke-width="5"/>'
            + puffs([(xb - 10, gy + 50, 18), (xb + 6, gy + 26, 22)], c("steam"), 4))


# ================================================================== 5) LADOVY SELF (snow/iceshelf)
def iceberg(x, wl, w, h, kind="table", sw=6.0):
    """Ladovec na hladine wl: tabulovy (rovny vrch, vrstvy) alebo spicaty."""
    b, bd, bl = c("berg"), c("berg_d"), c("berg_line")
    if kind == "table":
        pts = [(x - w / 2, wl), (x - w * 0.48, wl - h * 0.9), (x - w * 0.4, wl - h), (x + w * 0.3, wl - h * 0.98),
               (x + w * 0.44, wl - h * 0.92), (x + w / 2, wl)]
    else:
        pts = [(x - w / 2, wl), (x - w * 0.3, wl - h * 0.55), (x - w * 0.12, wl - h), (x + w * 0.04, wl - h * 0.7),
               (x + w * 0.22, wl - h * 0.86), (x + w * 0.38, wl - h * 0.35), (x + w / 2, wl)]
    out = f'<path d="{_poly(pts)}" fill="{b}" stroke="none"/>'
    # tienova strana (vpravo) + vrstvy snehu
    out += (f'<path d="M{x + w * 0.18:.0f},{wl:.0f} L{x + w * 0.24:.0f},{wl - h * 0.85:.0f} L{pts[-2][0]:.0f},{pts[-2][1]:.0f} '
            f'L{x + w / 2:.0f},{wl:.0f} Z" fill="{bd}" opacity="0.75"/>')
    if kind == "table":
        for f in (0.3, 0.55, 0.78):
            out += (f'<path d="M{x - w * 0.46:.0f},{wl - h * f:.0f} H{x + w * 0.45:.0f}" stroke="{bl}" stroke-width="{sw * 0.55:.1f}" '
                    f'stroke-dasharray="{w * 0.2:.0f} {w * 0.06:.0f}"/>')
    out += f'<path d="{_poly(pts)}" fill="none" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'
    # odraz/podvodna cast
    out += (f'<path d="M{x - w * 0.46:.0f},{wl + 6:.0f} H{x + w * 0.46:.0f} L{x + w * 0.3:.0f},{wl + h * 0.22:.0f} H{x - w * 0.3:.0f} Z" '
            f'fill="{b}" opacity="0.22"/>')
    return out


def low_sun(x, hz, r=74):
    """Nizke polarne slnko na horizonte + cestička svetla na vode (kresli sa PRED morom - more ho spodok zakryje)."""
    return (f'<circle cx="{x}" cy="{hz}" r="{r * 2.4:.0f}" fill="{c("sun_glow")}" opacity="0.35"/>'
            f'<circle cx="{x}" cy="{hz}" r="{r * 1.6:.0f}" fill="{c("sun_glow")}" opacity="0.45"/>'
            f'<circle cx="{x}" cy="{hz}" r="{r}" fill="{c("sun")}" stroke="{INK}" stroke-width="7"/>')


def sun_path(x, hz, y1):
    out = ""
    k = 0
    y = hz + 16
    while y < y1:
        w = 120 - k * 7
        out += (f'<path d="M{x - w / 2 + (k % 2) * 14:.0f},{y:.0f} h{max(24, w):.0f}" stroke="{c("sun")}" stroke-width="6" '
                f'stroke-linecap="round" opacity="0.85"/>')
        y += 16 + k * 2
        k += 1
    return out


def _ice_far():
    hz = 1108
    out = ""
    if L.time() in ("day", "dusk") and L.weather() in ("clear", "fog"):
        out += low_sun(720, hz)
    out += (f'<path d="M-900,{hz} H2400 V1480 H-900 Z" fill="{c("sea")}"/>'
            f'<path d="M-900,{hz} H2400 V{hz + 26} H-900 Z" fill="{c("sea_l")}" opacity="0.7"/>'
            f'<path d="M-900,{hz} H2400" stroke="{INK}" stroke-width="7"/>')
    if L.time() in ("day", "dusk") and L.weather() in ("clear", "fog"):
        out += sun_path(720, hz, 1176)
    out += iceberg(-440, 1122, 140, 30, "table", 4) + iceberg(170, 1156, 220, 130, "peak") + iceberg(990, 1150, 320, 104)
    out += iceberg(1620, 1132, 200, 48, "table", 5) + iceberg(2100, 1140, 150, 70, "peak", 5)
    r = random.Random(611)
    for _ in range(14):
        fx, fy = r.uniform(-880, 2380), r.uniform(1124, 1176)
        out += (f'<path d="{ell(fx, fy, r.uniform(16, 44), r.uniform(4, 7))}" fill="{c("berg")}" stroke="{INK}" stroke-width="3"/>')
    # okraj ladoveho sefu (za nim uz je len more)
    edge = [(x, 1180 + 6 * math.sin(x / 57.0) + (8 if (x // 120) % 3 == 0 else 0)) for x in range(-900, 2401, 30)]
    out += (f'<path d="M-900,1480 {_poly(edge, False).replace("M", "L", 1)} L2400,1480 Z" fill="{c("snow")}" stroke="none"/>'
            f'<path d="{_poly(edge, False)}" fill="none" stroke="{INK}" stroke-width="5"/>'
            f'<path d="{_poly([(x, y + 12) for x, y in edge], False)}" fill="none" stroke="{c("shade")}" stroke-width="10"/>')
    return out


def ice_block(x, y, w, h, rot=0.0, sw=6, seed=0):
    """Hranaty kus ladu: nepravidelny mnohouholnik, tmavsia bocna faza, snehova cepicka, prasklina."""
    ice, il, dk = c("ice"), c("ice_line"), c("berg_d", c("shade"))
    r = random.Random(seed)
    pts = [(-w / 2, 6), (-w * r.uniform(0.42, 0.52), -h * r.uniform(0.45, 0.7)), (-w * r.uniform(0.1, 0.3), -h),
           (w * r.uniform(0.15, 0.35), -h * r.uniform(0.82, 1.0)), (w * r.uniform(0.44, 0.52), -h * r.uniform(0.3, 0.55)),
           (w / 2, 6)]
    g = (f'<path d="{_poly(pts)}" fill="{ice}" stroke="none"/>'
         f'<path d="M{pts[3][0]:.0f},{pts[3][1]:.0f} L{pts[4][0]:.0f},{pts[4][1]:.0f} L{pts[5][0]:.0f},{pts[5][1]:.0f} '
         f'L{w * 0.12:.0f},6 L{w * 0.06:.0f},{-h * 0.5:.0f} Z" fill="{dk}" opacity="0.8"/>'
         f'<path d="M{pts[2][0]:.0f},{pts[2][1] + 3:.0f} L{pts[3][0]:.0f},{pts[3][1] + 3:.0f}" stroke="{c("snow")}" stroke-width="9" '
         f'stroke-linecap="round"/>'
         f'<path d="{_poly(pts)}" fill="none" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'
         f'<path d="M{-w * 0.2:.0f},{-h * 0.72:.0f} l{w * 0.1:.0f},{h * 0.24:.0f} l{-w * 0.06:.0f},{h * 0.2:.0f}" stroke="{il}" '
         f'stroke-width="4" fill="none" stroke-linecap="round"/>')
    return f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.0f})">{g}</g>'


def pressure_ridge(x, y, w, seed=1):
    """Tlakovy val: nahodne nakopene kry roznych velkosti (vacsie v strede)."""
    r = random.Random(seed)
    out = ""
    n = max(4, int(w / 55))
    order = sorted(range(n), key=lambda i: -abs(i - (n - 1) / 2.0))     # stredne (vyssie) kresli az nakoniec
    for i in order:
        u = 1 - abs(i - (n - 1) / 2.0) / (n / 2.0)
        bx = x - w / 2 + w * (i + 0.5) / n + r.uniform(-14, 14)
        bw, bh = r.randint(70, 120), 36 + 90 * u + r.randint(-10, 16)
        out += ice_block(bx, y + 4, bw, bh, r.uniform(-28, 28), 6, seed * 31 + i)
    return out


def flag(x, y, h=180):
    fl = c("flag")
    return (f'<path d="M{x},{y + 6} V{y - h}" stroke="#b58a52" stroke-width="7" stroke-linecap="round"/>'
            f'<path d="M{x},{y + 6} V{y - h}" stroke="{INK}" stroke-width="2" stroke-dasharray="4 26"/>'
            f'<path d="M{x + 2},{y - h} Q{x + 40},{y - h - 10} {x + 72},{y - h + 12} Q{x + 40},{y - h + 18} {x + 2},{y - h + 40} Z" '
            f'fill="{fl}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')


def _sastrugi(hy, x0, x1, seed=7, depth=(26, 360)):
    """Sastrugi: vetrom vyfukane snehove hrebienky - ostry hreben + modry tien pod nim (hlbsie = vacsie)."""
    r = random.Random(seed)
    ln, il = c("line"), c("ice_line")
    out = ""
    x = x0
    while x < x1:
        dd = r.uniform(*depth)
        y = hy(x) + dd
        k = 0.7 + 0.8 * (dd - depth[0]) / max(1.0, depth[1] - depth[0])
        w, h = r.uniform(70, 170) * k, r.uniform(10, 18) * k
        out += (f'<path d="M{x:.0f},{y:.0f} q{w * 0.45:.0f},{-h:.0f} {w:.0f},{-h * 0.35:.0f} l{w * 0.16:.0f},{h * 0.5:.0f} '
                f'q{-w * 0.6:.0f},{h * 0.5:.0f} {-w * 1.16:.0f},{-h * 0.15:.0f} Z" fill="{ln}" opacity="0.5"/>'
                f'<path d="M{x:.0f},{y:.0f} q{w * 0.45:.0f},{-h:.0f} {w:.0f},{-h * 0.35:.0f} l{w * 0.16:.0f},{h * 0.5:.0f}" '
                f'stroke="{il}" stroke-width="{4 * k:.1f}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        x += r.randint(50, 130)
    return out


def _ice_near(hy, x0, x1):
    r = random.Random(701)
    out = _sastrugi(hy, WX0, 2800, 7)
    il = c("ice_line")
    x = WX0 + 200
    while x < 2800:
        if not (-160 < x < 330):
            pts, yy = [(x, hy(x) + 8)], hy(x) + 8
            for j in range(r.randint(3, 5)):
                yy += r.randint(30, 50)
                pts.append((x + (12 if j % 2 else -10), yy))
            out += (f'<path d="{_poly(pts, False)}" stroke="{il}" stroke-width="4" fill="none" stroke-linejoin="round" '
                    f'stroke-linecap="round"/>')
        x += r.randint(420, 700)
    for px, w, sd in ((-2600, 300, 3), (-1300, 240, 5), (1230, 340, 9), (2300, 260, 11)):
        out += pressure_ridge(px, hy(px), w, sd)
    for fx in (-2000, -900, 400, 860, 2100):
        out += flag(fx, hy(fx) + 2)
    return out


def _ice_bd(hor, r):
    hz = hor - STAGE_HZ["iceshelf"]
    out = ""
    if L.time() in ("day", "dusk") and L.weather() in ("clear", "fog"):
        out += low_sun(820, hz, 64)
    out += (f'<path d="M-300,{hz} H1400 V{hor + 60} H-300 Z" fill="{c("sea")}"/>'
            f'<path d="M-300,{hz} H1400" stroke="{INK}" stroke-width="6"/>')
    if L.time() in ("day", "dusk") and L.weather() in ("clear", "fog"):
        out += sun_path(820, hz, hor - 50)
    out += iceberg(200, hz + 44, 360, 90) + iceberg(1060, hz + 52, 220, 130, "peak")
    edge = [(x, hor - 44 + 5 * math.sin(x / 50.0)) for x in range(-300, 1401, 30)]
    out += (f'<path d="M-300,{hor + 60} {_poly(edge, False).replace("M", "L", 1)} L1400,{hor + 60} Z" fill="{c("snow")}" stroke="none"/>'
            f'<path d="{_poly(edge, False)}" fill="none" stroke="{INK}" stroke-width="5"/>')
    return out


def _ice_ground(y, x0, x1):
    out = (f'<path d="M{x0},{y} H{x1} V4200 H{x0} Z" fill="{c("snow")}" stroke="{INK}" stroke-width="9"/>'
           f'<path d="M{x0},{y + 26} H{x1} V{y + 170} H{x0} Z" fill="{c("shade")}" stroke="none" opacity="0.55"/>')
    return out + _sastrugi(lambda x: y, x0, x1, 13, (40, 700))


def _ice_dressing(sd, y, xs):
    r = random.Random(sd)
    return "".join(ice_block(x, y + 2, r.randint(56, 84), r.randint(30, 52), r.uniform(-18, 18), 6, int(x)) for x in xs[::2])


def _ice_fore(x0, x1, gy, r):
    w = x1 - x0
    xa, xb = x0 + (0.05 + r.random() * 0.06) * w, x1 - (0.05 + r.random() * 0.06) * w
    return ice_block(xa, gy + 70, 90, 44, -10, 6, 3) + ice_block(xb, gy + 60, 110, 60, 12, 6, 5) + ice_block(xb + 70, gy + 72, 60, 30, -6, 6, 7)


# ================================================================== hacky volane z look.py
def style(kind_, base):
    s = dict(base)
    t = T()
    if t == "isle":
        s.update(fill=c("turf"), sub=c("turf_d"), sub_from=260, grass=False)
    elif t == "canyon":
        s.update(fill=c("sand"), sub=c("sand_d"), sub_from=270, grass=False)
    elif t == "jungle":
        s.update(fill=c("floor"), sub=c("floor_sub"), sub_from=260, grass=False)
    elif t == "geyser":
        s.update(fill=c("ground"), sub=c("ground_sub"), sub_from=250, grass=False)
    elif t == "iceshelf":
        s.update(fill=c("snow"), sub=c("shade"), sub_from=230, grass=False)
    return s


def far(p, kind_):
    body = {"isle": _isle_far, "canyon": _canyon_far, "jungle": _jungle_far, "geyser": _geyser_far,
            "iceshelf": _ice_far}[T()]()
    sun = "" if T() in ("jungle", "iceshelf") else L.far_sun(kind_)
    birds = "" if T() in ("isle", "jungle") else L.birds()
    return f'<g id="{p}_far">{sun}{body}{L.fog_far(p)}{far_clouds(p)}{birds}</g>'


def walk(kind_, hy, x0, x1):
    """Nahrada worlds_ext.walk (v dzungli by inak rastli ihlicnany)."""
    return ""


def walk_near(kind_, hy, x0, x1):
    return {"isle": _isle_near, "canyon": _canyon_near, "jungle": _jungle_near, "geyser": _geyser_near,
            "iceshelf": _ice_near}[T()](hy, x0, x1)


def backdrop(kind_, hor, r):
    return {"isle": _isle_bd, "canyon": _canyon_bd, "jungle": _jungle_bd, "geyser": _geyser_bd,
            "iceshelf": _ice_bd}[T()](hor, r)


def sky(p, sun_at, clouds, cls="sunray", hor=1290, dusk_y=None):
    """Obloha inscenovanych zaberov za jasneho dna; inak None (standard look.sky).
    Ladovy self (okrem noci): nizke slnko je v pozadi na horizonte - na oblohe len farba a pasy oblakov."""
    t = T()
    if t == "iceshelf" and L.time() != "night":
        return L.sky_rect(p) + "".join(streak(x, y, 460 * s, 36 * s, c("streak")) for x, y, s in (clouds or ()))
    if not clear_day():
        return None
    from props import sun as psun
    out = sky_rect(p)
    cl = list(clouds or ())
    if t == "isle":
        out += "".join(cumulus(x, y + 40, 300 * s, 150 * s) for x, y, s in cl)
    elif t == "geyser":
        out += "".join(puffs([(x - 50 * s, y, 34 * s), (x, y - 20 * s, 46 * s), (x + 50 * s, y, 32 * s)], c("ash_l"), 6,
                             [(x - 70 * s, y, 140 * s, 30 * s)]) for x, y, s in cl[:1])
        return out + (hazy_sun(sun_at[0], sun_at[1]) if sun_at else "")
    elif t == "jungle":
        return out                      # koruny a luce su v pozadi (backdrop)
    return out + (psun(p + "_rays", sun_at[0], sun_at[1], cls) if sun_at else "")


def ground(surface, y, x0, x1):
    fn = {("sand", "isle"): _isle_ground, ("sand", "canyon"): _canyon_ground, ("forest", "jungle"): _jungle_ground,
          ("land", "geyser"): _geyser_ground, ("snow", "iceshelf"): _ice_ground}.get((surface, T()))
    return fn(y, x0, x1) if fn else None


def dressing(surface, sd, y, xs):
    fn = {("sand", "isle"): _isle_dressing, ("sand", "canyon"): _canyon_dressing, ("forest", "jungle"): _jungle_dressing,
          ("land", "geyser"): _geyser_dressing, ("snow", "iceshelf"): _ice_dressing}.get((surface, T()))
    return fn(sd, y, xs) if fn else None


def foreground(kind_, x0, x1, gy, r):
    return {"isle": _isle_fore, "canyon": _canyon_fore, "jungle": _jungle_fore, "geyser": _geyser_fore,
            "iceshelf": _ice_fore}[T()](x0, x1, gy, r)


def mound_colors(default):
    t = T()
    if t == "isle":
        s = c("soil")
        return s, INK, L.mix(s, "#000000", 0.12)
    if t == "canyon":
        s = c("sand")
        return s, c("sand_line"), L.mix(s, "#000000", 0.08)
    if t == "jungle":
        s = c("floor")
        return s, INK, L.mix(s, "#000000", 0.14)
    if t == "geyser":
        s = c("ground")
        return s, INK, L.mix(s, "#000000", 0.18)
    return c("snow"), c("line"), c("shade")
