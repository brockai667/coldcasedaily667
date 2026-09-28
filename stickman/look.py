# -*- coding: utf-8 -*-
"""LOOK epizody: dve epizody v tom istom svete nesmu vyzerat rovnako.

    LOOK = look.choose(spec, kind, variant, slug)   # deterministicky zo seedu = md5 temy
    look.set_current(LOOK)                           # od tejto chvile ho citaju vsetky moduly

Polia LOOK:
  world    hill | shore | snow | desert | sea | cave | forest | city
  terrain  varianta terenu - najvacsi viditelny rozdiel:
             shore  beach | cliffs | harbour        hill   meadow | rocky | fields
             snow   peaks | tundra | glacier        desert dunes | mesa
             forest pine | birch | fallen(Tunguska) city   street | alley | library | books
  time     day | dusk | night
  weather  clear | overcast | rain | fog   (sneh si necha svoje vlocky - dazd tam nie je)
  palette  0..2 - farby sveta (len vyplne; vsetky ciary ostavaju INK)
  decor    2-3 drobnosti sveta (lodka na horizonte, bojka, ostrov, cajky, naplavene drevo, stromy...)
  moon     crescent | full

Poradie prepisov: spec["look"] (testy) > slova v naracii > seed.
Uvod, vsetky vonkajsie zabery aj zaverecna chodza/slucka pouzivaju ten isty LOOK; blizka vrstva uvodu
sa generuje z pevneho bodu (WX0), takze frame 0 a posledny frame slucky sa stale zhoduju.
Ked LOOK nie je nastaveny (CUR is None), vsetky hooky vratia None/"" a engine kresli ako predtym.
"""
import hashlib
import math
import random
import re

from props import DIRT2, INK, LEAF, PAPER, STONE, WOOD, ell, grass

CW, CH = 1080, 1920
WX0 = -3400                 # pevny zaciatok generovania blizkej vrstvy (ako worlds_ext.WX0)

TERRAINS = {
    "shore": ("beach", "cliffs", "harbour"),
    "hill": ("meadow", "rocky", "fields"),
    "snow": ("peaks", "tundra", "glacier"),
    "desert": ("dunes", "mesa"),
    "forest": ("pine", "birch"),
    "city": ("street", "alley"),
    "sea": ("open",),
    "cave": ("cave",),
}
TIMES = ("day", "dusk", "night")
WEATHERS = ("clear", "overcast", "rain", "fog")

# Ziadne zvierata ani ludia (cajky su len vzdialene "m" ciarky na oblohe).
DECOR = {
    "shore": ("sailboat", "buoy", "island", "gulls", "driftwood"),
    "hill": ("trees", "fence", "haybales", "stonewall"),
    "snow": ("firs", "cairn", "iceblocks"),
    "desert": ("deadtree", "boulders", "duneridge"),
    "forest": ("mushrooms", "stump", "ferns"),
    "city": ("lamppost", "bench", "cart"),
}
DECOR_BLOCK = {("shore", "cliffs"): ("driftwood",), ("shore", "harbour"): ("driftwood",)}

# ------------------------------------------------------------------ slova v naracii
KW_TIME = (("night", r"\b(night|nights|midnight|dark|darkness|moon|moonlight|moonlit)\b"),
           ("dusk", r"\b(dusk|sunset|sundown|evening|twilight|nightfall|dawn|sunrise)\b"),
           ("day", r"\b(morning|noon|midday|daylight|daytime|sunny|afternoon|sunshine)\b"))
KW_WEATHER = (("rain", r"\b(storm|storms|stormy|rain|rains|raining|rainy|gale|gales|downpour|thunder|thunderstorm)\b"),
              ("fog", r"\b(fog|foggy|mist|misty|haze|hazy)\b"))
KW_TERRAIN = {
    "shore": (("cliffs", r"\b(cliff|cliffs|clifftop|island|islands|isle|isles|islet|rock|rocks|rocky|headland|crag|crags)\b"),
              ("harbour", r"\b(harbou?rs?|piers?|docks?|docked|quays?|wharf|wharves|jetty|port)\b"),
              ("beach", r"\b(beach|beaches|sand|sands|sandy)\b")),
    "hill": (("rocky", r"\b(rock|rocks|rocky|boulder|boulders|crag|crags|scree|quarry)\b"),
             ("fields", r"\b(field|fields|farm|farms|farmer|farmers|farmland|harvest|crop|crops|wheat|barley|hay)\b"),
             ("meadow", r"\b(meadow|meadows|grass|grassland|pasture|pastures)\b")),
    "snow": (("glacier", r"\b(glacier|glaciers|glacial|crevasse|crevasses|icefall)\b"),
             ("tundra", r"\b(tundra|plain|plains|steppe|arctic|siberia|siberian)\b"),
             ("peaks", r"\b(mountain|mountains|peak|peaks|summit|slope|slopes|ridge|pass)\b")),
    "desert": (("mesa", r"\b(mesa|mesas|canyon|canyons|butte|buttes|plateau|cliff|cliffs|rock|rocks)\b"),
               ("dunes", r"\b(dune|dunes|sand|sands|sandstorm)\b")),
    "forest": (("birch", r"\b(birch|birches|oak|oaks|beech|autumn|leaves|leafy)\b"),
               ("pine", r"\b(pine|pines|taiga|conifer|conifers|spruce|larch)\b")),
    "city": (("alley", r"\b(alley|alleys|alleyway|backstreet|lane|lanes)\b"),
             ("street", r"\b(street|streets|avenue|boulevard|square|road)\b")),
}

# ------------------------------------------------------------------ palety (3 na svet)
PAL = {
    # zlaty piesok + tyrkysove more | svetlosivy oblazkovy breh + sivozelene more | tmavy mokry piesok + hlboke modre more
    "shore": (
        dict(sand="#efd594", sand_line="#d6b565", sea="#62c3c0", island="#9fbfa8", rock="#cdc5b5",
             rock_line="#9d9482", grass="#8fbf5a", grass_d="#6f9d44", stone="#ddd6c7", stone_top="#c7bfae",
             stone_line="#a39b88", soil="#c8b08a"),
        dict(sand="#dcd8ce", sand_line="#b1ab9d", sea="#8db1a3", island="#a9b5a9", rock="#bebcb4",
             rock_line="#8d8b82", grass="#9cb46e", grass_d="#7c9450", stone="#d3d0c7", stone_top="#bcb8ad",
             stone_line="#9c988c", soil="#b9ab93"),
        dict(sand="#ccae80", sand_line="#a3875a", sea="#4f86bd", island="#8ea3b5", rock="#aea69b",
             rock_line="#7d7568", grass="#78a458", grass_d="#5a8440", stone="#c7c0b2", stone_top="#b0a897",
             stone_line="#8e8777", soil="#b3976c"),
    ),
    # sviezo zelena | sucha zltozelena | jesenna oranzovohneda
    "hill": (
        dict(ground="#d4e3a8", ground_sub="#b9cf8c", grass="#5f9a3e", ridge="#8fa17a", ridge2="#b3c294",
             tree="#86b25e", tree_d="#5f8a45", rock="#cbc5b7", rock_line="#968f80", field_a="#c6db93",
             field_b="#e4da90", hay="#e3c46a"),
        dict(ground="#e6dda0", ground_sub="#cfc37c", grass="#9d9a3a", ridge="#aea479", ridge2="#cbc295",
             tree="#a9ab58", tree_d="#7f8138", rock="#d0c7b1", rock_line="#9d937c", field_a="#eadc93",
             field_b="#d3c374", hay="#e8c867"),
        dict(ground="#e9c897", ground_sub="#d1a56e", grass="#b9742f", ridge="#b09277", ridge2="#cfb194",
             tree="#dc8d3b", tree_d="#a9622a", rock="#cdbfae", rock_line="#9a8a76", field_a="#eac08a",
             field_b="#d9a466", hay="#e2b35c"),
    ),
    # modrobiela | sivobiela zamracena | ruzovobiela (usvit)
    # sneh je vzdy biely - paletu nesu hory, tiene a ihlicnany (velke plochy), inak by ju vecer/noc zmazali
    "snow": (
        dict(snow="#eef5fa", shade="#c2d8e8", line="#a6c4d9", mtn_far="#c6dbea", mtn_near="#e2edf5",
             mtn_line="#7c9bb2", cap_line="#a4bfd2", pine="#3d6a5c", ice="#cbe3f1", ice_line="#779fc0"),
        dict(snow="#ecebe8", shade="#d0cfca", line="#bab9b3", mtn_far="#c2c1bb", mtn_near="#dbdad5",
             mtn_line="#86857f", cap_line="#b2b1ab", pine="#56615a", ice="#d4dade", ice_line="#88959c"),
        dict(snow="#fbf0ee", shade="#eecdd4", line="#deb2bc", mtn_far="#e7c5ce", mtn_near="#f5e0e5",
             mtn_line="#ad8692", cap_line="#d9aeb9", pine="#5e6a58", ice="#e6dbee", ice_line="#a293bb"),
    ),
    # zlta | cervenooranzova | bledobezova
    "desert": (
        dict(sand="#efd999", sand_line="#d8bc70", dune="#f3e3a9", dune_line="#c4a45f", rock="#d9a066",
             rock_line="#a8703e", far="#efe0b8"),
        dict(sand="#e9b985", sand_line="#cf9760", dune="#efc594", dune_line="#b9794a", rock="#c9784c",
             rock_line="#94502c", far="#f0cfa8"),
        dict(sand="#f1e7d0", sand_line="#dacdae", dune="#f5eddb", dune_line="#c3b18d", rock="#d7c4a1",
             rock_line="#a8936c", far="#f3ead8"),
    ),
    # tmave ihlicnany | svetla breza/jesen | spaleny les
    "forest": (
        dict(floor="#cfcb9c", floor_sub="#b09c70", needle="#a9a06e", pine="#3f5c45",
             pine_mid=("#5b7a58", "#50704f"), pine_near="#6a8a61", pine_far="#aebfa8", pine_far_line="#869a81",
             canopy="#8fb86a", canopy_d="#5f8a45"),
        dict(floor="#e6d6a6", floor_sub="#c9ad78", needle="#c9a86a", pine="#6d7f4a",
             pine_mid=("#c9a14a", "#b98c3e"), pine_near="#d49a44", pine_far="#e2d0a6", pine_far_line="#bca379",
             canopy="#e0b04c", canopy_d="#b07e2c"),
        dict(floor="#d3c6a8", floor_sub="#ad9c7c", needle="#a39676", pine="#5b5a4c",
             pine_mid=("#77766a", "#6b6a5e"), pine_near="#86846f", pine_far="#c9c6b8", pine_far_line="#9f9b8c",
             canopy="#a39a78", canopy_d="#7a7358"),
    ),
    # kremova omietka | sivy kamen | cervena tehla
    "city": (
        dict(walls=("#f2e6c8", "#ecdcb8", "#f5ecd6", "#eadfc4"), roofs=("#c98b6b", "#b87458", "#c27d5f", "#a8674c"),
             cobble="#d8d0c1", cobble_sub="#bfb5a3", cobble_line="#aea38e", skyline="#e6dfcf",
             skyline_line="#b9af9b", brick="#d9b48f", brick_line="#a88560"),
        dict(walls=("#d9d7d0", "#cfccc4", "#e3e1da", "#c8c5bc"), roofs=("#7d8a94", "#6f7b85", "#8a949c", "#5f6b75"),
             cobble="#c9c7c0", cobble_sub="#b1aea6", cobble_line="#98958c", skyline="#dcdad4",
             skyline_line="#a8a59d", brick="#bdb8ad", brick_line="#8f8a80"),
        dict(walls=("#cf8468", "#bd7258", "#d99474", "#b0674f"), roofs=("#5f5a55", "#6f6862", "#4f4a46", "#7a5548"),
             cobble="#cdbfae", cobble_sub="#b3a390", cobble_line="#9a8a76", skyline="#e3d2c4",
             skyline_line="#b89c88", brick="#c0785c", brick_line="#8f5238"),
    ),
}

CUR = None          # aktualny LOOK (dict) - nastavi build_spec cez set_current()


def _pl():
    """HiddenEarth miesta (places.py: ostrov, kanon, dzungla, gejzir, ladovy self) - lenivy import,
    places importuje look. Kazdy hacok nizsie sa ich tyka len ked je teren epizody jedno z nich."""
    import places
    return places


# ================================================================== vyber
def _h(s):
    return int(hashlib.md5(str(s).encode("utf-8")).hexdigest()[:8], 16)


def _kw_count(rx, lines):
    """Pocet zasahov v naracii; prva veta (uvod = miesto deja) sa rata dvakrat."""
    n = 0
    for i, s in enumerate(lines):
        k = len(re.findall(rx, s))
        n += k * (2 if i == 0 else 1)
    return n


def choose(spec, kind, variant="", slug=""):
    """LOOK epizody: seed = stabilny hash spec["topic"] (alebo slug), potom slova v naracii,
    nakoniec spec["look"] (prepis pre testy)."""
    spec = spec or {}
    key = str(spec.get("topic") or spec.get("slug") or slug or spec.get("title") or "episode")
    seed = _h(key.strip().lower())
    r = random.Random(seed)
    opts = TERRAINS.get(kind, ("default",))
    lk = {"world": kind}
    # poradie tahov je pevne - zmena slov v naracii nezmeni ostatne polia
    lk["palette"] = r.randrange(3)
    lk["terrain"] = r.choice(opts)
    # den prevlada (najcitatelnejsi), sumrak a noc pre atmosferu; tajomne slova v naracii noc aj tak vynutia
    lk["time"] = r.choices(TIMES, weights=(50, 28, 22))[0]
    if kind == "snow":
        lk["weather"] = r.choices(("clear", "overcast", "fog"), weights=(50, 30, 20))[0]
    else:
        lk["weather"] = r.choices(WEATHERS, weights=(40, 25, 15, 20))[0]
    lk["moon"] = r.choice(("crescent", "full"))
    ndec = r.choice((2, 3))
    pool = list(DECOR.get(kind, ()))
    order = r.sample(pool, len(pool)) if pool else []
    lk["birds"] = r.random() < 0.5
    why = {}

    lines = [str(l.get("say", "")).lower() for l in (spec.get("lines") or [])]
    # cas
    counts = [(_kw_count(rx, lines), name) for name, rx in KW_TIME]
    best = max(counts, key=lambda q: q[0]) if counts else (0, "")
    if best[0] > 0:
        lk["time"] = best[1]
        why["time"] = "narration"
    # pocasie
    counts = [(_kw_count(rx, lines), name) for name, rx in KW_WEATHER]
    best = max(counts, key=lambda q: q[0]) if counts else (0, "")
    if best[0] > 0:
        lk["weather"] = best[1]
        why["weather"] = "narration"
    # teren (pri rovnosti vyhrava skorsi zaznam: cliffs > harbour > beach ...)
    counts = [(_kw_count(rx, lines), -i, name) for i, (name, rx) in enumerate(KW_TERRAIN.get(kind, ()))]
    if counts:
        best = max(counts)
        if best[0] > 0:
            lk["terrain"] = best[2]
            why["terrain"] = "narration"
    # varianty sveta, ktore urcuje uz worlds.world_variant (Tunguska, kniznica)
    if kind == "forest" and variant == "fallen":
        lk["terrain"] = "fallen"
        why["terrain"] = "variant"
    if kind == "city" and variant in ("library", "books"):
        lk["terrain"] = variant
        why["terrain"] = "variant"
    # HiddenEarth miesta: len explicitne meno sveta (worlds.world_variant), nikdy nahodny seed
    if variant in _pl().TERRAINS.get(kind, ()):
        lk["terrain"] = variant
        why["terrain"] = "variant"
    # prepis zo spec-u (testy)
    ov = spec.get("look") or {}
    if isinstance(ov, dict):
        if (ov.get("terrain") in TERRAINS.get(kind, ()) + _pl().TERRAINS.get(kind, ())
                or (kind == "forest" and ov.get("terrain") == "fallen")):
            lk["terrain"] = ov["terrain"]
            why["terrain"] = "spec"
        if ov.get("time") in TIMES:
            lk["time"] = ov["time"]
            why["time"] = "spec"
        if ov.get("weather") in WEATHERS:
            lk["weather"] = ov["weather"]
            why["weather"] = "spec"
        if ov.get("palette") is not None:
            try:
                lk["palette"] = max(0, min(2, int(ov["palette"])))
                why["palette"] = "spec"
            except (TypeError, ValueError):
                pass
        if ov.get("moon") in ("crescent", "full"):
            lk["moon"] = ov["moon"]
    blocked = DECOR_BLOCK.get((kind, lk["terrain"]), ())
    lk["decor"] = [d for d in order if d not in blocked][:ndec]
    if isinstance(ov, dict) and isinstance(ov.get("decor"), (list, tuple)):
        lk["decor"] = [d for d in ov["decor"] if d in DECOR.get(kind, ())]
    if lk["terrain"] in _pl().ALL:
        lk["decor"] = []          # miesta maju vlastne drobnosti (places.py)
    # sneh si necha vlocky (dazd tam nie je); v pusti je "dazd/burka" piesocny opar (hmla v piesocnej farbe);
    # jaskyna a kniznica su interier - obloha sa nekresli
    if kind == "snow" and lk["weather"] == "rain":
        lk["weather"] = "overcast"
    if kind == "desert" and lk["weather"] == "rain":
        lk["weather"] = "fog"
    if kind == "cave" or (kind == "city" and lk["terrain"] == "library"):
        lk["time"], lk["weather"] = "day", "clear"
    lk["seed"] = seed
    lk["why"] = why
    return lk


def summary(lk):
    return f'look: {lk["world"]}/{lk["terrain"]}, {lk["time"]}, {lk["weather"]}, palette {lk["palette"]}'


def used(lk):
    """Co sa ulozi do spec["look_used"]."""
    return {k: lk[k] for k in ("world", "terrain", "time", "weather", "palette", "decor", "moon")}


_ORIG = {}


def _rebind(mod, name, val):
    k = (mod, name)
    if k not in _ORIG:
        _ORIG[k] = getattr(mod, name)
    setattr(mod, name, val)


def set_current(lk):
    """Nastavi LOOK a prefarbi konstanty generovanych svetov (worlds_ext) - funkcie tam citaju
    modulove konstanty pri volani. None = povodny vzhlad."""
    global CUR
    for (mod, name), v in _ORIG.items():
        setattr(mod, name, v)
    CUR = lk
    if not lk:
        return
    import worlds_ext as X
    k = lk["world"]
    if k == "forest":
        for a, b in (("FOREST_FLOOR", "floor"), ("FOREST_SUB", "floor_sub"), ("NEEDLE", "needle"), ("PINE", "pine"),
                     ("PINE_MID", "pine_mid"), ("PINE_NEAR", "pine_near"), ("PINE_FAR", "pine_far"),
                     ("PINE_FAR_LINE", "pine_far_line")):
            _rebind(X, a, col(b))
        _rebind(X, "BURNT_FLOOR", tone(X.BURNT_FLOOR))
        # paprad a trava v generovanom lese vo farbe palety (inak svietia zelenou aj v noci / v spalenom lese)
        leaf, orig_fern = col("canopy_d", tone(LEAF)), X.fern
        _rebind(X, "fern", lambda x, y, s=1.0, c=None, _f=orig_fern, _c=leaf: _f(x, y, s, c or _c))
        _rebind(X, "grass", tuft)
    elif k == "city":
        for a, b in (("WALLS", "walls"), ("ROOFS", "roofs"), ("COBBLE", "cobble"), ("COBBLE_SUB", "cobble_sub"),
                     ("COBBLE_LINE", "cobble_line"), ("SKYLINE", "skyline"), ("SKYLINE_LINE", "skyline_line")):
            _rebind(X, a, col(b))
        # v noci sa v oknach svieti
        _rebind(X, "WIN", "#f6d77a" if night() else tone(X.WIN))
        for a in ("LIB_WALL", "SHELF", "SHELF_BACK", "WOODF", "WOODF_SUB", "WOODF_LINE", "BEAM"):
            _rebind(X, a, tone(getattr(X, a)))


# ================================================================== pristup
def time():
    return CUR["time"] if CUR else "day"


def weather():
    return CUR["weather"] if CUR else "clear"


def terrain():
    return CUR["terrain"] if CUR else ""


def kind():
    return CUR["world"] if CUR else ""


def decor():
    return tuple(CUR.get("decor") or ()) if CUR else ()


def night():
    return bool(CUR) and CUR["time"] == "night"


def dusk():
    return bool(CUR) and CUR["time"] == "dusk"


def seed():
    return CUR["seed"] if CUR else 0


def pal():
    if not CUR:
        return {}
    p = PAL.get(CUR["world"])
    base = p[CUR["palette"] % len(p)] if p else {}
    x = _pl().PAL.get(CUR.get("terrain"))
    return dict(base, **x[CUR["palette"] % len(x)]) if x else base


def _rgb(c):
    c = c.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in rgb)


def mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


def tone(c):
    """Farba pod svetlom epizody: noc o ~18 % tmavsia a do modra, sumrak teplejsi,
    dazd/zamracene menej syte, hmla bledsia. INK sa nikdy netonuje."""
    if not CUR or not isinstance(c, str) or not c.startswith("#") or c.lower() == INK:
        return c
    r, g, b = _rgb(c)
    w, t = CUR["weather"], CUR["time"]
    if w in ("rain", "overcast"):
        grey = (r + g + b) / 3.0
        k, d = (0.28, 0.93) if w == "rain" else (0.16, 0.98)
        r, g, b = [(v + (grey - v) * k) * d for v in (r, g, b)]
    elif w == "fog":
        r, g, b = [v + (f - v) * 0.14 for v, f in zip((r, g, b), (236, 234, 228))]
    if t == "night":
        r, g, b = r * 0.78, g * 0.81, b * 0.90
    elif t == "dusk":
        r, g, b = r * 1.0, g * 0.955, b * 0.90
    return _hex((r, g, b))


def col(name, default=None):
    """Farba z palety sveta (tonovana podla casu/pocasia); bez LOOK-u vrati default."""
    if not CUR:
        return default
    v = pal().get(name, default)
    if v is None:
        return None
    if isinstance(v, (tuple, list)):
        return tuple(tone(x) for x in v)
    return tone(v)


def foam():
    return tone(PAPER) if CUR else PAPER


def tuft(x, y, s=1.0):
    """Trs travy vo farbe palety (props.grass kresli LEAF)."""
    g = grass(x, y, s)
    if not CUR:
        return g
    return g.replace(LEAF, col("grass", tone(LEAF)))


def tint_pebbles(svg):
    """Kamienky (props.pebbles kreslia DIRT2) vo farbe terenu epizody - na skale sive, nie piesocne."""
    if not CUR:
        return svg
    k, t = CUR["world"], terrain()
    if t in _pl().ALL:
        c = col("pebble")
    elif (k, t) in (("shore", "cliffs"), ("hill", "rocky"), ("desert", "mesa")):
        c = col("rock_line")
    elif k in ("shore", "desert"):
        c = col("sand_line", tone(DIRT2))
    else:
        c = tone(DIRT2)
    return svg.replace(f'stroke="{DIRT2}"', f'stroke="{c}"')


# ================================================================== obloha
SKY_NIGHT = "#34435c"
_CLOUD = ((-40, -6, -22, -40), (14, -38, 56, -22), (22, -46, 70, -18), (44, -8, 40, 36), (34, 10, 8, 44))
DEFAULT_WALK_CL = ((330, 470, 1.0, 1.0, 1.0), (1050, 640, 0.75, 1.0, 1.0), (1650, 430, 0.9, 1.0, 1.0))
MOON_WALK = (830, 300)
DEFAULT_BIRDS = ('<path d="M560,610 q14,-16 28,0 q14,-16 28,0 M690,560 q11,-13 22,0 q11,-13 22,0" '
                 f'fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')


def cloud_fill():
    t, w = time(), weather()
    if t == "night":
        return "#56657e" if w in ("clear", "fog") else "#4b586d"
    if t == "dusk":
        return "#fbe5cf" if w in ("clear", "fog") else "#e6cfbb"
    return {"overcast": "#ebeae5", "rain": "#c5cad1", "fog": "#f2f0ea"}.get(w, PAPER)


def cloud(x, y, s=1.0, fill=None, sx=1.0, sy=1.0):
    """Ten isty rucne kresleny oblak ako props.cloud, ale s vyplnou a natiahnutim (dlhe vecerne oblaky)."""
    fill = fill or cloud_fill()
    d = f"M{x - 90 * s * sx:.1f},{y + 30 * s * sy:.1f}" + "".join(
        f" q{a * s * sx:.1f},{b * s * sy:.1f} {c * s * sx:.1f},{e * s * sy:.1f}" for a, b, c, e in _CLOUD)
    return (f'<path d="{d} Z" fill="{fill}" stroke="{INK}" stroke-width="{max(4.5, 7 * s):.1f}" '
            f'stroke-linejoin="round"/>')


def sky_rect(p):
    """Celoplosna obloha pre sumrak/noc/zamracene/dazd/hmlu (cez ciary boil filtra presahuje ram)."""
    if not CUR or CUR["world"] == "cave":
        return ""
    t, w = time(), weather()
    R = "M-80,-80 H1160 V2000 H-80 Z"
    if t == "night":
        fill = {"rain": "#2f3a4b", "overcast": "#323f52", "fog": "#46526a"}.get(w, SKY_NIGHT)
        return f'<path d="{R}" fill="{fill}" opacity="0.94"/>'
    if t == "dusk":
        top, bot = {"rain": ("#d6bba2", "#e7dbcd"), "overcast": ("#e6c9a9", "#efe2d2"),
                    "fog": ("#efd9c0", "#f4ebdf")}.get(w, ("#f0c69c", "#f6e5cf"))
        return (f'<defs><linearGradient id="{p}_skyg" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bot}"/></linearGradient></defs>'
                f'<path d="{R}" fill="url(#{p}_skyg)" opacity="0.94"/>')
    if w == "overcast":
        return f'<path d="{R}" fill="#d6d6d1" opacity="0.5"/>'
    if w == "rain":
        return f'<path d="{R}" fill="#b1b7bf" opacity="0.62"/>'
    if w == "fog":
        return f'<path d="{R}" fill="#e4e2dc" opacity="0.45"/>'
    return _pl().sky_rect(p) if _pl().on() else ""


def dusk_sun(x, y, r=80):
    return (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r * 1.8:.0f}" fill="#f7c27e" opacity="0.30"/>'
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#f59a45" stroke="{INK}" stroke-width="8"/>')


def moon(x, y, r=58, phase=None):
    phase = phase or (CUR.get("moon") if CUR else "full")
    halo = (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r * 2.1:.0f}" fill="#fff6d8" opacity="0.07"/>'
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r * 1.5:.0f}" fill="#fff6d8" opacity="0.10"/>')
    if phase == "crescent":
        body = (f'<path d="M{x:.0f},{y - r:.0f} A{r},{r} 0 0 1 {x:.0f},{y + r:.0f} '
                f'A{r * 0.52:.0f},{r} 0 0 0 {x:.0f},{y - r:.0f} Z" fill="#fbf5df" stroke="{INK}" '
                f'stroke-width="7" stroke-linejoin="round" transform="rotate(-18 {x:.0f} {y:.0f})"/>')
    else:
        body = (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fbf5df" stroke="{INK}" stroke-width="7"/>'
                f'<circle cx="{x - r * 0.3:.0f}" cy="{y - r * 0.2:.0f}" r="{r * 0.2:.0f}" fill="#e7dfc2"/>'
                f'<circle cx="{x + r * 0.28:.0f}" cy="{y + r * 0.3:.0f}" r="{r * 0.14:.0f}" fill="#e7dfc2"/>'
                f'<circle cx="{x + r * 0.34:.0f}" cy="{y - r * 0.36:.0f}" r="{r * 0.09:.0f}" fill="#e7dfc2"/>')
    return halo + body


def stars(sd, n=12, avoid=(), y0=40, y1=720, x0=30, x1=1050):
    r = random.Random(sd)
    out, k, guard = "", 0, 0
    while k < n and guard < 600:
        guard += 1
        x, y = r.uniform(x0, x1), r.uniform(y0, y1)
        if any((x - ax) ** 2 + (y - ay) ** 2 < ar * ar for ax, ay, ar in avoid):
            continue
        k += 1
        s = r.uniform(6.0, 11.0)
        if r.random() < 0.62:
            q = s * 0.28
            out += (f'<path d="M{x:.1f},{y - s:.1f} L{x + q:.1f},{y - q:.1f} L{x + s:.1f},{y:.1f} L{x + q:.1f},{y + q:.1f} '
                    f'L{x:.1f},{y + s:.1f} L{x - q:.1f},{y + q:.1f} L{x - s:.1f},{y:.1f} L{x - q:.1f},{y - q:.1f} Z"/>')
        else:
            out += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{s * 0.36:.1f}"/>'
    return f'<g fill="#fff4cc" stroke="none">{out}</g>'


def _grey_clouds(sd, n, y0=150, y1=560, x0=70, x1=1010):
    r = random.Random(sd)
    return [(x0 + (x1 - x0) * (i + 0.5) / n + r.uniform(-50, 50), r.uniform(y0, y1), r.uniform(0.72, 1.05))
            for i in range(n)]


# horizont inscenovanych pozadi (kolko nad ciarou zeme) - nizke vecerne slnko zapada za neho
STAGE_HZ = {("shore", "beach"): 120, ("shore", "cliffs"): 300, ("shore", "harbour"): 150,
            ("hill", "meadow"): 262, ("hill", "rocky"): 290, ("hill", "fields"): 170,
            ("snow", "peaks"): 420, ("snow", "tundra"): 80, ("snow", "glacier"): 300,
            ("desert", "dunes"): 150, ("desert", "mesa"): 250}
STAGE_HZ_KIND = {"forest": 560, "city": 400, "sea": 300}


def stage_hz(hor):
    k, t = kind(), terrain()
    return hor - STAGE_HZ.get((k, t), _pl().STAGE_HZ.get(t, STAGE_HZ_KIND.get(k, 200)))


def sky(p, sun_at, clouds, cls="sunray", hor=1290, dusk_y=None):
    """Obloha inscenovanych zaberov. None = bezny den (kresli povodny kod).
    dusk_y: vyska vecerneho slnka pre zabery bez pozadia (inak zapada za horizont pozadia)."""
    if not CUR or CUR["world"] == "cave":
        return None
    t, w = time(), weather()
    if _pl().on():
        s = _pl().sky(p, sun_at, clouds, cls, hor, dusk_y)
        if s is not None:
            return s
    if t == "day" and w == "clear":
        return None
    out = sky_rect(p)
    cl = list(clouds or ())
    if w in ("overcast", "rain"):
        cl = _grey_clouds(_h(p + "cl"), 6 if w == "overcast" else 7)
    elif w == "fog":
        cl = cl[:1]
    if t == "night":
        avoid = []
        if sun_at and w != "rain":
            out += moon(sun_at[0], sun_at[1], 56)
            avoid = [(sun_at[0], sun_at[1], 130)]
        if w != "rain":
            out += stars(_h(p + "st"), 12 if w in ("clear", "fog") else 6, avoid, 40, max(200, hor - 480))
        if w == "clear":
            cl = cl[:1]
        out += "".join(cloud(x, y, s, sx=1.4, sy=0.7) if w == "clear" else cloud(x, y, s) for x, y, s in cl)
    elif t == "dusk":
        if sun_at and w in ("clear", "fog"):
            out += dusk_sun(sun_at[0], dusk_y if dusk_y is not None else stage_hz(hor) - 6)
        if w in ("clear", "fog"):
            out += "".join(cloud(x, y, s, sx=1.75, sy=0.6) for x, y, s in cl)
        else:
            out += "".join(cloud(x, y, s) for x, y, s in cl)
    else:
        out += "".join(cloud(x, y, s) for x, y, s in cl)
    return out


def walk_sun(p, cls, default):
    """Obsah skupiny {p}_sun uvodu/slucky (obrazovkove suradnice, staticky)."""
    if not CUR or CUR["world"] == "cave":
        return default
    if _pl().on():
        s = _pl().walk_sun(p, cls, default)
        if s is not None:
            return s
    t, w = time(), weather()
    if t == "night":
        s = ""
        if w != "rain":
            s += moon(MOON_WALK[0], MOON_WALK[1], 58)
            s += stars(seed() + 7, 12 if w in ("clear", "fog") else 7, [(MOON_WALK[0], MOON_WALK[1], 135)], 40, 700)
        return s
    if t == "dusk" or w != "clear":
        return ""          # vecerne slnko je vo vzdialenej vrstve (zapada za horizont)
    return default


def walk_cloud_list():
    """Oblaky vo vzdialenej vrstve uvodu/slucky: (x, y, s, sx, sy) - rovnake pre obraz aj simulaciu
    driftu v stage_shots._cloud_k."""
    if not CUR:
        return DEFAULT_WALK_CL
    t, w = time(), weather()
    if w in ("overcast", "rain"):
        r = random.Random(seed() + 3)
        return tuple((-900 + i * 175 + r.uniform(-30, 30), 360 + (i % 3) * 95 + r.uniform(-25, 25),
                      r.uniform(0.8, 1.05), 1.0, 1.0) for i in range(20))
    if w == "fog":
        return ((330, 470, 0.9, 1.0, 1.0), (1650, 430, 0.8, 1.0, 1.0))
    if t == "dusk":
        return ((250, 520, 0.95, 1.8, 0.6), (1050, 650, 0.8, 1.9, 0.55), (1700, 470, 0.9, 1.7, 0.6))
    if t == "night":
        return ((300, 520, 0.9, 1.5, 0.7), (1500, 560, 0.8, 1.6, 0.6))
    return DEFAULT_WALK_CL


def walk_clouds(p):
    if not CUR:
        from props import cloud as pcloud
        return f'<g id="{p}_cloud">{pcloud(330, 470, 1.0)}{pcloud(1050, 640, 0.75)}{pcloud(1650, 430, 0.9)}</g>'
    if time() == "day" and weather() == "clear":
        from props import cloud as pcloud
        body = "".join(pcloud(x, y, s) for x, y, s, _a, _b in DEFAULT_WALK_CL)
    else:
        body = "".join(cloud(x, y, s, sx=a, sy=b) for x, y, s, a, b in walk_cloud_list())
    return f'<g id="{p}_cloud">{body}</g>'


def walk_cloud_spec():
    """(oblaky, slnko/mesiac (x, y, r) v obrazovke alebo None) pre stage_shots._cloud_k."""
    if not CUR:
        return DEFAULT_WALK_CL, (880.0, 330.0, 134.0)
    if _pl().on() and _pl().cloud_spec() is not None:
        return _pl().cloud_spec()
    t, w = time(), weather()
    if t == "night":
        return walk_cloud_list(), (None if w == "rain" else (float(MOON_WALK[0]), float(MOON_WALK[1]), 118.0))
    if t == "day" and w == "clear":
        return walk_cloud_list(), (880.0, 330.0, 134.0)
    return walk_cloud_list(), None


def birds():
    """Vtaky v dialke: len cez den/vecer, bez dazda; na brehu su to cajky z decor."""
    if not CUR:
        return DEFAULT_BIRDS
    if time() == "night" or weather() == "rain" or CUR["world"] == "shore":
        return ""
    return DEFAULT_BIRDS if CUR.get("birds", True) else ""


def gulls(pts):
    return "".join(f'<path d="M{x:.0f},{y:.0f} q{11 * s:.1f},{-13 * s:.1f} {22 * s:.1f},0 q{11 * s:.1f},{-13 * s:.1f} '
                   f'{22 * s:.1f},0" fill="none" stroke="{INK}" stroke-width="{5 * min(1.0, s):.1f}" '
                   f'stroke-linecap="round"/>' for x, y, s in pts)


# ------------------------------------------------------------------ dazd a hmla
def rain_on():
    return bool(CUR) and CUR["weather"] == "rain" and CUR["world"] not in ("cave", "snow")


def rain_color():
    return {"night": "#c3cfdd", "dusk": "#8e8a9a"}.get(time(), "#7c8ea3")


def rain_svg(p):
    if not rain_on():
        return ""
    import stage
    return stage.flurry_svg(p, 40, rain=True, color=rain_color())


def fx_js(p):
    """JS pocasia pre zaber (dazd). Rychlosti su nasobky vysky/TOTAL -> slucka sedi."""
    if not rain_on():
        return ""
    import stage
    return stage.flurry_js(p, 40, seed=5, rain=True)


def fog_color():
    if CUR and CUR["world"] == "desert":          # piesocny opar
        return {"night": "#8f8a86", "dusk": "#f0d9bc"}.get(time(), "#efe2c6")
    return {"night": "#8591a8", "dusk": "#f1e1cf"}.get(time(), "#efede7")


def fog_far(p):
    if not CUR or weather() != "fog":
        return ""
    return (f'<defs><linearGradient id="{p}_fogf" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{fog_color()}" stop-opacity="0"/>'
            f'<stop offset="0.35" stop-color="{fog_color()}" stop-opacity="0.5"/>'
            f'<stop offset="1" stop-color="{fog_color()}" stop-opacity="0.55"/></linearGradient></defs>'
            f'<path d="M-900,760 H2400 V1520 H-900 Z" fill="url(#{p}_fogf)"/>')


def fog_band(p, hor):
    if not CUR or weather() != "fog":
        return ""
    return (f'<defs><linearGradient id="{p}_fogb" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{fog_color()}" stop-opacity="0"/>'
            f'<stop offset="0.4" stop-color="{fog_color()}" stop-opacity="0.5"/>'
            f'<stop offset="1" stop-color="{fog_color()}" stop-opacity="0.55"/></linearGradient></defs>'
            f'<path d="M-300,{hor - 620} H1400 V{hor + 60} H-300 Z" fill="url(#{p}_fogb)"/>')


# ================================================================== teren uvodu/slucky
def _sm(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


# y0 - rise * smooth((x - xo) / span)
TERRAIN_FN = {
    ("shore", "cliffs"): (1250, 215, 260, 1150),
    ("shore", "harbour"): (1272, 18, 0, 1600),
    ("hill", "rocky"): (1262, 380, 0, 1200),
    ("hill", "fields"): (1272, 170, 0, 1500),
    ("snow", "tundra"): (1276, 40, 0, 1600),
    ("snow", "glacier"): (1270, 240, 0, 1400),
    ("desert", "mesa"): (1280, 120, 0, 1500),
    ("forest", "birch"): (1264, 200, 0, 1400),
    ("city", "alley"): (1272, 60, 0, 1500),
}


def terrain_fn(kind_):
    """(python fn, JS vyraz) profilu pre variantu terenu, inak None (povodny profil sveta)."""
    if not CUR or kind_ != CUR["world"]:
        return None
    v = TERRAIN_FN.get((kind_, terrain())) or _pl().TERRAIN_FN.get((kind_, terrain()))
    if not v:
        return None
    y0, rise, xo, span = v
    if xo:
        return (lambda x: y0 - rise * _sm((x - xo) / float(span))), f"{y0} - {rise} * smooth((x - {xo}) / {span})"
    return (lambda x: y0 - rise * _sm(x / float(span))), f"{y0} - {rise} * smooth(x / {span})"


def style(kind_, base):
    """STYLE sveta (vypln/podklad terenu uvodu) prefarbeny paletou."""
    if not CUR or kind_ != CUR["world"]:
        return base
    if _pl().on():
        return _pl().style(kind_, base)
    s = dict(base)
    t = terrain()
    if kind_ == "shore":
        if t == "cliffs":
            s.update(fill=col("rock"), sub=None, grass=True)
        elif t == "harbour":
            s.update(fill=col("stone"), sub=None, grass=False)
        else:
            s.update(fill=col("sand"))
    elif kind_ == "hill":
        s.update(fill=col("ground"), sub=col("ground_sub"), sub_from=260)
    elif kind_ == "snow":
        s.update(fill=col("snow"), sub=col("shade") if s.get("sub") else None)
    elif kind_ == "desert":
        s.update(fill=col("sand"), sub=col("sand_line") if s.get("sub") else None)
    elif kind_ == "forest":
        if t != "fallen":
            s.update(fill=col("floor"), sub=col("floor_sub"))
        else:
            # fill = worlds_ext.BURNT_FLOOR (uz tonovany v set_current), sub je povodna konstanta zo STYLE
            s.update(sub=tone(s["sub"]) if s.get("sub") else None)
    elif kind_ == "city":
        if t not in ("library",):
            s.update(fill=col("cobble"), sub=col("cobble_sub"))
        # kniznica: WOODF/WOODF_SUB su uz tonovane v set_current
    else:
        s.update(fill=tone(s["fill"]), sub=tone(s["sub"]) if s.get("sub") else None)
    return s


# ------------------------------------------------------------------ utes (shore/cliffs)
CLIFF_XE = 1790          # hrana utesu (za majakom na 1470)
CLIFF_SL = 1440          # hladina pod utesom
CLIFF_FACE = ((0, 0), (22, 64), (10, 138), (40, 214), (30, 296), (58, 1000))


def _cliff_top(hy):
    return hy(CLIFF_XE)


def walk_skip(kind_, x):
    """True = na tomto x uz nie je povrch (za hranou utesu) - ziadna trava ani kamienky."""
    return bool(CUR) and kind_ == "shore" and terrain() == "cliffs" and x > CLIFF_XE - 30


def walk_surface(kind_, hy, x0, x1, st):
    """Vlastny obrys terenu (utes s kolmou stenou do mora), inak None."""
    if not CUR or kind_ != "shore" or terrain() != "cliffs":
        return None
    top = _cliff_top(hy)
    pts = " ".join(f"L{x},{hy(x):.1f}" for x in range(x0, CLIFF_XE, 40))
    face = " ".join(f"L{CLIFF_XE + dx},{min(top + dy, CLIFF_SL + 30):.0f}" for dx, dy in CLIFF_FACE)
    return (f'<path d="M{x0},3300 {pts} L{CLIFF_XE},{top:.1f} {face} L{CLIFF_XE + 70},3300 Z" fill="{st["fill"]}" '
            f'stroke="{INK}" stroke-width="9" stroke-linejoin="round"/>')


def _boulder(x, y, w, fill, line=None, sw=6):
    h = w * 0.62
    out = (f'<path d="M{x - w / 2:.0f},{y + 8:.0f} Q{x - w * 0.52:.0f},{y - h * 0.7:.0f} {x - w * 0.12:.0f},{y - h:.0f} '
           f'Q{x + w * 0.36:.0f},{y - h * 1.05:.0f} {x + w * 0.5:.0f},{y - h * 0.3:.0f} L{x + w * 0.54:.0f},{y + 8:.0f} Z" '
           f'fill="{fill}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')
    if line:
        out += (f'<path d="M{x - w * 0.16:.0f},{y - h * 0.72:.0f} q{w * 0.12:.0f},{h * 0.18:.0f} {w * 0.05:.0f},{h * 0.42:.0f}" '
                f'stroke="{line}" stroke-width="{max(3, sw - 2)}" fill="none" stroke-linecap="round"/>')
    return out


def _sea_rock(x, y, w, fill):
    h = w * 0.7
    return (f'<path d="M{x - w / 2:.0f},{y + 6:.0f} L{x - w * 0.36:.0f},{y - h * 0.62:.0f} L{x - w * 0.06:.0f},{y - h:.0f} '
            f'L{x + w * 0.3:.0f},{y - h * 0.8:.0f} L{x + w / 2:.0f},{y + 6:.0f} Z" fill="{fill}" stroke="{INK}" '
            f'stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x - w * 0.72:.0f},{y + 4:.0f} q{w * 0.18:.0f},-12 {w * 0.36:.0f},0 M{x + w * 0.36:.0f},{y + 4:.0f} '
            f'q{w * 0.18:.0f},-12 {w * 0.36:.0f},0" stroke="{foam()}" stroke-width="7" fill="none" stroke-linecap="round"/>')


def _cliff_near(hy, x0, x1):
    grass_c, gd = col("grass"), col("grass_d")
    rl = col("rock_line")
    top = _cliff_top(hy)
    xs = list(range(WX0, CLIFF_XE - 6, 30)) + [CLIFF_XE - 6]
    cap = "M" + " L".join(f"{x},{hy(x) + 17:.1f}" for x in xs)
    out = (f'<path d="{cap}" stroke="{grass_c}" stroke-width="26" fill="none"/>'
           f'<path d="{"M" + " L".join(f"{x},{hy(x) + 31 + 5 * math.sin(x / 37.0):.1f}" for x in xs)}" '
           f'stroke="{gd}" stroke-width="5" fill="none" stroke-linecap="round"/>')
    # vrstvy skaly (prerusovane, vlnite) - rovnobezne s povrchom
    for k in range(1, 6):
        d = 58 + k * 64
        pts = [(x, hy(x) + d + 7 * math.sin(x / 140.0 + k * 1.7)) for x in range(WX0, CLIFF_XE - 20, 30)]
        out += (f'<path d="M{" L".join(f"{a},{b:.1f}" for a, b in pts)}" stroke="{rl}" stroke-width="5" fill="none" '
                f'stroke-dasharray="{70 + k * 9} {34 + k * 5}" stroke-linecap="round"/>')
    r = random.Random(71)
    x = WX0 + 140
    while x < CLIFF_XE - 60:
        y = hy(x) + r.randint(90, 330)
        out += (f'<path d="M{x},{y} l{r.randint(12, 22)},{r.randint(18, 26)} l{r.randint(-16, -6)},{r.randint(14, 22)} '
                f'l{r.randint(10, 18)},{r.randint(12, 20)}" stroke="{rl}" stroke-width="4" fill="none" stroke-linecap="round"/>')
        x += r.randint(260, 420)
    # stena utesu: praskliny a zvisle ryhy
    out += (f'<path d="M{CLIFF_XE + 16},{top + 70:.0f} l18,40 l-10,36 M{CLIFF_XE + 30},{top + 200:.0f} l14,44 l-8,30" '
            f'stroke="{rl}" stroke-width="5" fill="none" stroke-linecap="round"/>')
    # skaly a pena pod utesom
    rock = col("rock")
    for xx, w in ((CLIFF_XE + 150, 120), (CLIFF_XE + 330, 90), (CLIFF_XE + 520, 150), (CLIFF_XE + 760, 100)):
        out += _sea_rock(xx, CLIFF_SL + 8, w, rock)
    out += "".join(f'<path d="M{CLIFF_XE + 60 + i * 150},{CLIFF_SL + 70 + (i % 2) * 40} q26,-14 52,0 q26,14 52,0" '
                   f'stroke="{foam()}" stroke-width="7" fill="none" stroke-linecap="round"/>' for i in range(7))
    out += (f'<path d="M{CLIFF_XE + 40},{CLIFF_SL + 12} q18,-22 40,-6 q16,-26 44,-4 q20,-20 44,2" stroke="{foam()}" '
            f'stroke-width="9" fill="none" stroke-linecap="round"/>')
    return out


def _cliff_back(hy):
    sea = col("sea")
    return (f'<path d="M{CLIFF_XE - 100},{CLIFF_SL} H2900 V3300 H{CLIFF_XE - 100} Z" fill="{sea}" stroke="none"/>'
            f'<path d="M{CLIFF_XE - 100},{CLIFF_SL} H2900" stroke="{INK}" stroke-width="7" fill="none"/>')


# ------------------------------------------------------------------ pristav (shore/harbour)
def _bollard(x, y, s=1.0):
    return (f'<path d="M{x - 22 * s:.0f},{y + 6:.0f} V{y - 52 * s:.0f} Q{x - 24 * s:.0f},{y - 66 * s:.0f} {x - 34 * s:.0f},{y - 70 * s:.0f} '
            f'H{x + 34 * s:.0f} Q{x + 24 * s:.0f},{y - 66 * s:.0f} {x + 22 * s:.0f},{y - 52 * s:.0f} V{y + 6:.0f} Z" '
            f'fill="#4d4d4f" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x - 12 * s:.0f},{y - 48 * s:.0f} v{36 * s:.0f}" stroke="#8a8a8c" stroke-width="4" stroke-linecap="round"/>')


def _rope_coil(x, y):
    return (f'<path d="{ell(x, y - 12, 46, 16)}" fill="none" stroke="#9a7a4a" stroke-width="8"/>'
            f'<path d="{ell(x, y - 18, 28, 10)}" fill="none" stroke="#9a7a4a" stroke-width="7"/>')


def _boat(x, wl, hull="#b5543c"):
    """Mala rybarska lodka, pociatok na hladine (x = stred, wl = hladina)."""
    return (f'<path d="M{x - 170},{wl - 62} H{x + 170} L{x + 128},{wl + 30} H{x - 132} Z" fill="{hull}" stroke="{INK}" '
            f'stroke-width="8" stroke-linejoin="round"/>'
            f'<path d="M{x - 170},{wl - 44} H{x + 170}" stroke="{PAPER}" stroke-width="6"/>'
            f'<path d="M{x - 96},{wl - 62} v-56 h92 v56" fill="#e9e1cf" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x - 78},{wl - 104} h22 v20 h-22 z M{x - 40},{wl - 104} h22 v20 h-22 z" fill="#a9c0cb" stroke="{INK}" stroke-width="4"/>'
            f'<path d="M{x + 40},{wl - 62} V{wl - 380}" stroke="{WOOD}" stroke-width="10" stroke-linecap="round"/>'
            f'<path d="M{x + 40},{wl - 350} q30,60 4,150 q-20,-70 -4,-150 z" fill="#e8dfca" stroke="{INK}" stroke-width="5" '
            f'stroke-linejoin="round"/>'
            f'<path d="M{x + 40},{wl - 372} L{x + 170},{wl - 64}" stroke="{INK}" stroke-width="3" opacity="0.7"/>')


HARBOUR_BOAT_X = 880


def _harbour_back(hy, x0, x1):
    sea = col("sea")
    xs = list(range(x0, 2801, 40))
    wl = [hy(x) - 22 for x in xs]
    band = ("M" + " L".join(f"{x},{w:.1f}" for x, w in zip(xs, wl))
            + f" L2800,{hy(2800) + 60:.1f} L{x0},{hy(x0) + 60:.1f} Z")
    boat = _boat(HARBOUR_BOAT_X, hy(HARBOUR_BOAT_X) - 22, ("#b5543c", "#3f6f8f", "#4f7a54")[CUR["palette"] % 3])
    return (boat + f'<path d="{band}" fill="{sea}" stroke="none"/>'
            + "".join(f'<path d="M{x},{hy(x) - 14:.0f} q18,-7 36,0" stroke="{foam()}" stroke-width="5" fill="none" '
                      f'stroke-linecap="round"/>' for x in range(WX0 + 60, 2800, 230)))


def _harbour_near(hy, x0, x1):
    import worlds_ext as X
    top_c, line = col("stone_top"), col("stone_line")
    xs = list(range(WX0, 2801, 40))
    out = f'<path d="M{" L".join(f"{x},{hy(x) + 15:.1f}" for x in xs)}" stroke="{top_c}" stroke-width="22" fill="none"/>'
    out += f'<path d="M{" L".join(f"{x},{hy(x) + 27:.1f}" for x in xs)}" stroke="{INK}" stroke-width="5" fill="none"/>'
    for k in range(7):
        d = 27 + (k + 1) * 64
        out += f'<path d="M{" L".join(f"{x},{hy(x) + d:.1f}" for x in xs[::3])}" stroke="{line}" stroke-width="5" fill="none"/>'
        dd = d - 64
        joints = "".join(f"M{x},{hy(x) + dd + 4:.0f} v56 " for x in range(WX0 + (k % 2) * 70, 2800, 140))
        out += f'<path d="{joints}" stroke="{line}" stroke-width="5" fill="none"/>'
    # ziadny stlpik za Bobom vo frame 0 (x -80..300)
    for bx in (-2300, -1560, -820, 420, 1120, 1760, 2380):
        out += _bollard(bx, hy(bx) + 2)
    wlb = hy(HARBOUR_BOAT_X) - 22
    out += (f'<path d="M1120,{hy(1120) - 60:.0f} Q1092,{hy(1120) - 4:.0f} {HARBOUR_BOAT_X + 168},{wlb - 56:.0f}" '
            f'stroke="#9a7a4a" stroke-width="7" fill="none" stroke-linecap="round"/>')
    out += _rope_coil(500, hy(500) + 4) + _rope_coil(-1480, hy(-1480) + 4)
    out += X.lamp_post(640, hy(640) + 2, 440, 1.0)
    if night():
        out += "".join(f'<circle cx="640" cy="{hy(640) - 400 + 28:.0f}" r="{rr}" fill="#ffd98a" opacity="{o}"/>'
                       for rr, o in ((150, 0.12), (90, 0.16), (48, 0.22)))
    return out


# ------------------------------------------------------------------ kopec: skaly / polia
def _rocky_near(hy, x0, x1):
    r = random.Random(41)
    rock, rl = col("rock"), col("rock_line")
    out = ""
    x = WX0 + 80
    while x < 2800:
        if not (-160 < x < 330) and not (1280 < x < 1680):
            w = r.randint(80, 170)
            out += _boulder(x, hy(x), w, rock, rl)
        x += r.randint(240, 460)
    sc = ""
    x = WX0
    while x < 2800:
        y = hy(x) + r.uniform(10, 70)
        w = r.uniform(12, 26)
        sc += f'<path d="M{x - w:.0f},{y + 4:.0f} l{w * 0.4:.0f},{-w * 0.7:.0f} l{w:.0f},{-w * 0.1:.0f} l{w * 0.6:.0f},{w * 0.7:.0f} z"/>'
        x += r.randint(34, 80)
    return out + f'<g fill="{rock}" stroke="{INK}" stroke-width="4" stroke-linejoin="round">{sc}</g>'


def _fence(xa, xb, hy, h=110, step=150, sw=6):
    posts, rails = "", ""
    x = xa
    while x <= xb:
        y = hy(x)
        posts += f'<path d="M{x},{y + 8:.0f} V{y - h:.0f}" stroke="{INK}" stroke-width="{sw + 8}" stroke-linecap="round"/>'
        posts += f'<path d="M{x},{y + 8:.0f} V{y - h:.0f}" stroke="{WOOD}" stroke-width="{sw + 1}" stroke-linecap="round"/>'
        x += step
    for f in (0.35, 0.75):
        pts = [(x, hy(x) - h * f) for x in range(int(xa), int(xb) + 1, 30)]
        d = "M" + " L".join(f"{a},{b:.0f}" for a, b in pts)
        rails += (f'<path d="{d}" stroke="{INK}" stroke-width="{sw + 6}" fill="none" stroke-linecap="round"/>'
                  f'<path d="{d}" stroke="#a37a4c" stroke-width="{sw}" fill="none" stroke-linecap="round"/>')
    return rails + posts


def _haybale(x, y, rr=58):
    """Okruhly balik sena: valec z boku (telo doprava) a celo so spiralou - nie debna."""
    hay = col("hay", tone("#e3c46a"))
    dk = mix(hay, "#000000", 0.28)
    sw = max(3.0, min(6.0, rr / 9.0))
    body = (f'<path d="M{x:.0f},{y - 2 * rr:.0f} H{x + rr * 1.15:.0f} Q{x + rr * 1.55:.0f},{y - rr:.0f} {x + rr * 1.15:.0f},{y + 2:.0f} '
            f'H{x:.0f} Z" fill="{mix(hay, "#000000", 0.08)}" stroke="{INK}" stroke-width="{sw:.1f}" stroke-linejoin="round"/>')
    face = f'<circle cx="{x:.0f}" cy="{y - rr:.0f}" r="{rr:.0f}" fill="{hay}" stroke="{INK}" stroke-width="{sw:.1f}"/>'
    spiral = (f'<path d="M{x:.0f},{y - rr:.0f} q{rr * 0.28:.0f},{-rr * 0.05:.0f} {rr * 0.2:.0f},{rr * 0.24:.0f} '
              f'q{-rr * 0.1:.0f},{rr * 0.34:.0f} {-rr * 0.46:.0f},{rr * 0.12:.0f} q{-rr * 0.34:.0f},{-rr * 0.3:.0f} {-rr * 0.06:.0f},{-rr * 0.62:.0f} '
              f'q{rr * 0.44:.0f},{-rr * 0.36:.0f} {rr * 0.8:.0f},{rr * 0.08:.0f}" stroke="{dk}" stroke-width="{sw * 0.7:.1f}" '
              f'fill="none" stroke-linecap="round"/>')
    return body + face + spiral


def _qpath_samples(start, segs, n=40):
    """Body kriviek M..Q..T (ako v SVG) - aby sa drobnosti postavili presne na ciaru hrebena."""
    pts = [start]
    p0, ctrl = start, None
    for seg in segs:
        if seg[0] == "Q":
            c, p1 = seg[1], seg[2]
        else:
            p1 = seg[1]
            c = (2 * p0[0] - ctrl[0], 2 * p0[1] - ctrl[1])
        for i in range(1, n + 1):
            t = i / float(n)
            pts.append(((1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * c[0] + t * t * p1[0],
                        (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * c[1] + t * t * p1[1]))
        p0, ctrl = p1, c
    return pts


def _y_on(pts, x):
    best = min(range(len(pts) - 1), key=lambda i: 0 if pts[i][0] <= x <= pts[i + 1][0] else
               min(abs(pts[i][0] - x), abs(pts[i + 1][0] - x)) + 1)
    (xa, ya), (xb, yb) = pts[best], pts[best + 1]
    u = 0.0 if xb == xa else max(0.0, min(1.0, (x - xa) / (xb - xa)))
    return ya + (yb - ya) * u


# hreben louky vo vzdialenej vrstve (worlds.world_far, kind hill) a v inscenovanom pozadi (_bd_hill)
MEADOW_FAR = _qpath_samples((-400, 1130), [("Q", (0, 930), (380, 1075)), ("T", (980, 1030)), ("T", (1600, 1090)),
                                           ("T", (2300, 1050))])


def _meadow_stage(hor):
    r1 = _qpath_samples((-300, hor - 60), [("Q", (60, hor - 230), (380, hor - 110)), ("T", (980, hor - 150)),
                                           ("T", (1500, hor - 80))])
    r2 = _qpath_samples((-300, hor - 20), [("Q", (200, hor - 110), (560, hor - 50)), ("T", (1400, hor - 60))])
    return r1, r2


def _fields_near(hy, x0, x1):
    sub = col("ground_sub")
    out = ""
    for k, d in enumerate((46, 98, 162, 240, 332)):
        pts = [(x, hy(x) + d + 5 * math.sin(x / 90.0 + k)) for x in range(WX0, 2801, 40)]
        out += f'<path d="M{" L".join(f"{a},{b:.1f}" for a, b in pts)}" stroke="{sub}" stroke-width="{5 + k}" fill="none" stroke-linecap="round"/>'
    # plot pozdlz cesty - za Bobom vo frame 0 len dva stlpiky mimo postavy
    out += _fence(WX0 + 100, -140, hy) + _fence(360, 1240, hy) + _fence(1740, 2740, hy)
    return out


# ------------------------------------------------------------------ sneh: tundra / ladovec
def _tundra_near(hy, x0, x1):
    line = col("line")
    out = ""
    x = WX0 + 40
    i = 0
    while x < 2800:
        y = hy(x) + 30 + (i % 4) * 46
        out += (f'<path d="M{x},{y:.0f} q{90 + (i % 3) * 30},-26 {200 + (i % 3) * 50},-4" fill="none" stroke="{line}" '
                f'stroke-width="7" stroke-linecap="round"/>')
        x += 190 + (i % 5) * 40
        i += 1
    return out


def _ice_block(x, y, w, h):
    ice, il = col("ice"), col("ice_line")
    return (f'<path d="M{x - w / 2:.0f},{y + 6:.0f} L{x - w * 0.44:.0f},{y - h:.0f} L{x + w * 0.36:.0f},{y - h * 1.06:.0f} '
            f'L{x + w / 2:.0f},{y + 6:.0f} Z" fill="{ice}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x - w * 0.22:.0f},{y - h * 0.8:.0f} l{w * 0.2:.0f},{h * 0.36:.0f} M{x + w * 0.1:.0f},{y - h * 0.5:.0f} '
            f'l{w * 0.16:.0f},{h * 0.3:.0f}" stroke="{il}" stroke-width="4" fill="none" stroke-linecap="round"/>')


def _glacier_near(hy, x0, x1):
    il = col("ice_line")
    out = ""
    r = random.Random(53)
    x = WX0 + 120
    while x < 2800:
        if not (-140 < x < 320):
            d = f"M{x},{hy(x) + 6:.0f}"
            yy = hy(x) + 6
            for j in range(r.randint(3, 5)):
                yy += r.randint(34, 56)
                d += f" L{x + (14 if j % 2 else -12)},{yy:.0f}"
            out += (f'<path d="{d}" stroke="{INK}" stroke-width="8" fill="none" stroke-linejoin="round" stroke-linecap="round"/>'
                    f'<path d="{d}" stroke="{il}" stroke-width="4" fill="none" stroke-linejoin="round" stroke-linecap="round" '
                    f'transform="translate(6,2)"/>')
        x += r.randint(280, 460)
    for bx, w, h in ((-1900, 120, 90), (-700, 90, 70), (520, 110, 80), (1000, 150, 110), (2100, 120, 90)):
        out += _ice_block(bx, hy(bx), w, h)
    return out


# ------------------------------------------------------------------ pust: stolove hory
def _mesa_near(hy, x0, x1):
    r = random.Random(61)
    rock, rl = col("rock"), col("rock_line")
    out = ""
    x = WX0 + 100
    while x < 2800:
        if not (-160 < x < 330) and not (1280 < x < 1680):
            out += _boulder(x, hy(x), r.randint(60, 130), rock, rl)
        x += r.randint(420, 700)
    return out


# ------------------------------------------------------------------ les: brezy
def birch(x, y, h, canopy=None, cd=None, sw=6):
    canopy = canopy or col("canopy", "#8fb86a")
    cd = cd or col("canopy_d", "#5f8a45")
    tw = max(12.0, h * 0.06)
    trunk = (f'<path d="M{x - tw / 2:.0f},{y + 6:.0f} L{x - tw * 0.35:.0f},{y - h * 0.78:.0f} L{x + tw * 0.35:.0f},{y - h * 0.78:.0f} '
             f'L{x + tw / 2:.0f},{y + 6:.0f} Z" fill="#f4f1ea" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>')
    marks = "".join(f'<path d="M{x - tw * 0.45:.0f},{y - h * f:.0f} h{tw * (0.35 + (i % 2) * 0.2):.0f}" stroke="{INK}" '
                    f'stroke-width="{max(3, sw - 2)}" stroke-linecap="round"/>' for i, f in enumerate((0.12, 0.24, 0.37, 0.5, 0.63)))
    crown = ""
    for dx, dy, rr in ((-0.16, 0.80, 0.17), (0.14, 0.84, 0.16), (0.0, 0.95, 0.17), (-0.05, 0.70, 0.15), (0.12, 0.68, 0.13)):
        crown += f'<circle cx="{x + h * dx:.0f}" cy="{y - h * dy:.0f}" r="{h * rr:.0f}"/>'
    return (trunk + marks + f'<g fill="{canopy}" stroke="{INK}" stroke-width="{sw}">{crown}</g>'
            f'<path d="M{x - h * 0.12:.0f},{y - h * 0.78:.0f} q{h * 0.05:.0f},-{h * 0.06:.0f} {h * 0.12:.0f},0" stroke="{cd}" '
            f'stroke-width="{sw - 1}" fill="none" stroke-linecap="round"/>')


def _birch_near(hy, x0, x1):
    import worlds_ext as X
    r = random.Random(23)
    out = ""
    x = WX0 + 60
    while x < x1:
        if not (-260 < x < 470):
            out += birch(x, hy(x) + 4, r.randint(320, 440))
        x += r.randint(300, 460)
    x = WX0 + 250
    while x < x1:
        out += X.log_along(hy, x, x + r.randint(220, 330), r.randint(18, 24))
        x += r.randint(1100, 1500)
    x = WX0 + 20
    while x < x1:
        out += X.fern(x, hy(x) + 4, r.uniform(0.8, 1.25), col("canopy_d", LEAF))
        if r.random() < 0.5:
            out += tuft(x + 50, hy(x + 50) + 3)
        x += r.randint(150, 260)
    return out


# ------------------------------------------------------------------ mesto: ulicka
def _crate(x, y, w=90):
    return (f'<path d="M{x - w / 2:.0f},{y + 4:.0f} V{y - w:.0f} H{x + w / 2:.0f} V{y + 4:.0f} Z" fill="#c9a26b" stroke="{INK}" '
            f'stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x - w / 2:.0f},{y - w:.0f} L{x + w / 2:.0f},{y + 4:.0f} M{x - w / 2:.0f},{y - w / 2:.0f} H{x + w / 2:.0f}" '
            f'stroke="#8a6740" stroke-width="5" fill="none"/>')


def _barrel(x, y, h=110):
    w = h * 0.7
    return (f'<path d="M{x - w / 2:.0f},{y + 4:.0f} Q{x - w * 0.62:.0f},{y - h / 2:.0f} {x - w / 2:.0f},{y - h:.0f} H{x + w / 2:.0f} '
            f'Q{x + w * 0.62:.0f},{y - h / 2:.0f} {x + w / 2:.0f},{y + 4:.0f} Z" fill="{WOOD}" stroke="{INK}" stroke-width="6" '
            f'stroke-linejoin="round"/>'
            f'<path d="M{x - w * 0.56:.0f},{y - h * 0.3:.0f} H{x + w * 0.56:.0f} M{x - w * 0.56:.0f},{y - h * 0.7:.0f} H{x + w * 0.56:.0f}" '
            f'stroke="#4a4a4a" stroke-width="6" fill="none"/>')


def _alley_near(hy, x0, x1):
    import worlds_ext as X
    r = random.Random(29)
    cl = col("cobble_line")
    out = ""
    for row in range(3):
        off = 0 if row % 2 == 0 else 22
        out += "".join(f'<path d="M{x},{hy(x) + 24 + row * 30:.0f} q11,-9 22,0" stroke="{cl}" stroke-width="4" '
                       f'fill="none" stroke-linecap="round"/>' for x in range(WX0 + off, 2800, 46))
    x = WX0 + 200
    i = 0
    while x < 2800:
        if not (-120 < x < 300) and not (1300 < x < 1700):
            out += _crate(x, hy(x), r.randint(70, 100)) if i % 2 == 0 else _barrel(x, hy(x), r.randint(90, 120))
            i += 1
        x += r.randint(380, 560)
    return out


def walk(kind_, hy, x0, x1):
    """Nahrada worlds_ext.walk pre variantu terenu (brezy, ulicka), inak None."""
    if not CUR or kind_ != CUR["world"]:
        return None
    if _pl().on():
        return _pl().walk(kind_, hy, x0, x1)
    t = terrain()
    if kind_ == "forest" and t == "birch":
        return _birch_near(hy, x0, x1)
    if kind_ == "city" and t == "alley":
        return _alley_near(hy, x0, x1)
    return None


def walk_bones():
    """Kosti v zemi uvodu kopca/puste; sopecne pole (places: geyser) ich nema."""
    return not (_pl().on() and _pl().T() == "geyser")


def walk_back(kind_, hy, x0, x1):
    """Blizka vrstva ZA terenom (more pod utesom, voda a lodka za molom)."""
    if not CUR or kind_ != CUR["world"] or kind_ != "shore":
        return ""
    t = terrain()
    if t == "cliffs":
        return _cliff_back(hy)
    if t == "harbour":
        return _harbour_back(hy, x0, x1)
    return ""


def walk_near(kind_, hy, x0, x1):
    """Prvky terenu + drobnosti (decor) v blizkej vrstve uvodu/slucky - generovane z pevneho bodu."""
    if not CUR or kind_ != CUR["world"]:
        return ""
    if _pl().on():
        return _pl().walk_near(kind_, hy, x0, x1)
    t = terrain()
    out = ""
    if kind_ == "shore" and t == "cliffs":
        out += _cliff_near(hy, x0, x1)
    elif kind_ == "shore" and t == "harbour":
        out += _harbour_near(hy, x0, x1)
    elif kind_ == "hill" and t == "rocky":
        out += _rocky_near(hy, x0, x1)
    elif kind_ == "hill" and t == "fields":
        out += _fields_near(hy, x0, x1)
    elif kind_ == "snow" and t == "tundra":
        out += _tundra_near(hy, x0, x1)
    elif kind_ == "snow" and t == "glacier":
        out += _glacier_near(hy, x0, x1)
    elif kind_ == "desert" and t == "mesa":
        out += _mesa_near(hy, x0, x1)
    return out + _decor_near(kind_, hy)


# ------------------------------------------------------------------ drobnosti (decor) - blizko
def _driftwood(x, y, L=230):
    c, d = tone("#d8cbb0"), tone("#a8977a")
    return (f'<path d="M{x - L / 2:.0f},{y - 10:.0f} Q{x:.0f},{y - 30:.0f} {x + L / 2:.0f},{y - 14:.0f}" stroke="{INK}" '
            f'stroke-width="34" fill="none" stroke-linecap="round"/>'
            f'<path d="M{x - L / 2:.0f},{y - 10:.0f} Q{x:.0f},{y - 30:.0f} {x + L / 2:.0f},{y - 14:.0f}" stroke="{c}" '
            f'stroke-width="22" fill="none" stroke-linecap="round"/>'
            f'<path d="M{x - L * 0.3:.0f},{y - 18:.0f} q{L * 0.2:.0f},-6 {L * 0.4:.0f},-4" stroke="{d}" stroke-width="4" fill="none"/>'
            f'<path d="M{x + L * 0.18:.0f},{y - 24:.0f} l26,-34 M{x + L * 0.26:.0f},{y - 40:.0f} l22,4" stroke="{INK}" '
            f'stroke-width="12" fill="none" stroke-linecap="round"/>'
            f'<path d="M{x + L * 0.18:.0f},{y - 24:.0f} l26,-34 M{x + L * 0.26:.0f},{y - 40:.0f} l22,4" stroke="{c}" '
            f'stroke-width="5" fill="none" stroke-linecap="round"/>')


def leaf_tree(x, y, h, fill=None, dark=None, sw=6):
    fill = fill or col("tree", "#86b25e")
    dark = dark or col("tree_d", "#5f8a45")
    tw = max(12.0, h * 0.07)
    return (f'<path d="M{x - tw / 2:.0f},{y + 6:.0f} L{x - tw * 0.3:.0f},{y - h * 0.55:.0f} L{x + tw * 0.3:.0f},{y - h * 0.55:.0f} '
            f'L{x + tw / 2:.0f},{y + 6:.0f} Z" fill="{WOOD}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'
            f'<path d="M{x - h * 0.3:.0f},{y - h * 0.52:.0f} q-{h * 0.1:.0f},-{h * 0.26:.0f} {h * 0.1:.0f},-{h * 0.34:.0f} '
            f'q{h * 0.06:.0f},-{h * 0.2:.0f} {h * 0.24:.0f},-{h * 0.14:.0f} q{h * 0.22:.0f},-{h * 0.02:.0f} {h * 0.2:.0f},{h * 0.2:.0f} '
            f'q{h * 0.16:.0f},{h * 0.1:.0f} {h * 0.02:.0f},{h * 0.28:.0f} q-{h * 0.2:.0f},{h * 0.12:.0f} -{h * 0.46:.0f},0 z" '
            f'fill="{fill}" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'
            f'<path d="M{x - h * 0.12:.0f},{y - h * 0.7:.0f} q{h * 0.06:.0f},-{h * 0.05:.0f} {h * 0.12:.0f},0" stroke="{dark}" '
            f'stroke-width="{sw - 1}" fill="none" stroke-linecap="round"/>')


def _stonewall(xa, xb, hy, h=64):
    fill = col("rock", tone(STONE))
    out = ""
    x = xa
    k = 0
    while x < xb:
        w = 40 + (k * 17) % 26
        for row in range(2):
            yy = hy(x) - row * h / 2
            out += (f'<path d="M{x + (row * 18):.0f},{yy + 4:.0f} q-4,-{h * 0.5:.0f} {w * 0.5:.0f},-{h * 0.5:.0f} '
                    f'q{w * 0.5:.0f},0 {w * 0.46:.0f},{h * 0.5:.0f} z" fill="{fill}" stroke="{INK}" stroke-width="5" '
                    f'stroke-linejoin="round"/>')
        x += w
        k += 1
    return out


def _fir(x, y, h):
    import worlds_ext as X
    return X.pine(x, y, h, col("pine", "#4d6b52"), 6)


def _cairn(x, y, s=1.0):
    """Mohyla z kamenov - ploche kamene na sebe, kazdy mensi."""
    fill = tone("#b9b3a6")
    out, yy = "", y
    for i, (w, hh) in enumerate(((96, 30), (76, 26), (58, 24), (40, 22), (26, 18))):
        out += (f'<path d="{ell(x + (i % 2) * 4, yy - hh * s / 2, w * s / 2, hh * s / 2)}" fill="{fill}" '
                f'stroke="{INK}" stroke-width="5"/>')
        yy -= hh * s
    return out


def _dead_tree(x, y, h=320):
    return (f'<path d="M{x},{y + 6} L{x + 4},{y - h * 0.55:.0f} M{x + 3},{y - h * 0.35:.0f} L{x - h * 0.22:.0f},{y - h * 0.62:.0f} '
            f'M{x + 4},{y - h * 0.5:.0f} L{x + h * 0.24:.0f},{y - h * 0.78:.0f} M{x + 4},{y - h * 0.55:.0f} L{x - 2},{y - h:.0f} '
            f'M{x - h * 0.12:.0f},{y - h * 0.5:.0f} l-{h * 0.12:.0f},-{h * 0.04:.0f} M{x + h * 0.14:.0f},{y - h * 0.66:.0f} l{h * 0.1:.0f},{h * 0.02:.0f}" '
            f'stroke="{INK}" stroke-width="{max(10, h * 0.05) + 6:.0f}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M{x},{y + 6} L{x + 4},{y - h * 0.55:.0f} M{x + 3},{y - h * 0.35:.0f} L{x - h * 0.22:.0f},{y - h * 0.62:.0f} '
            f'M{x + 4},{y - h * 0.5:.0f} L{x + h * 0.24:.0f},{y - h * 0.78:.0f} M{x + 4},{y - h * 0.55:.0f} L{x - 2},{y - h:.0f} '
            f'M{x - h * 0.12:.0f},{y - h * 0.5:.0f} l-{h * 0.12:.0f},-{h * 0.04:.0f} M{x + h * 0.14:.0f},{y - h * 0.66:.0f} l{h * 0.1:.0f},{h * 0.02:.0f}" '
            f'stroke="{tone("#8a6a48")}" stroke-width="{max(10, h * 0.05):.0f}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')


def _mushrooms(x, y):
    out = ""
    for dx, s in ((0, 1.0), (40, 0.7), (-34, 0.8)):
        xx = x + dx
        out += (f'<path d="M{xx - 8 * s:.0f},{y + 4} V{y - 30 * s:.0f} H{xx + 8 * s:.0f} V{y + 4} Z" fill="#f4efe2" stroke="{INK}" '
                f'stroke-width="4" stroke-linejoin="round"/>'
                f'<path d="M{xx - 30 * s:.0f},{y - 28 * s:.0f} Q{xx:.0f},{y - 70 * s:.0f} {xx + 30 * s:.0f},{y - 28 * s:.0f} Z" fill="#c8453a" '
                f'stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
                f'<circle cx="{xx - 10 * s:.0f}" cy="{y - 42 * s:.0f}" r="{5 * s:.1f}" fill="#fff"/>'
                f'<circle cx="{xx + 10 * s:.0f}" cy="{y - 38 * s:.0f}" r="{4 * s:.1f}" fill="#fff"/>')
    return out


def _bench(x, y):
    return (f'<path d="M{x - 90},{y - 50} h180 v-14 h-180 z M{x - 90},{y - 100} h180 v-12 h-180 z" fill="{WOOD}" stroke="{INK}" '
            f'stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="M{x - 76},{y + 4} V{y - 110} M{x + 76},{y + 4} V{y - 110}" stroke="#4a4a4a" stroke-width="10" stroke-linecap="round"/>')


def _cart(x, y):
    return (f'<path d="M{x - 110},{y - 60} h170 v-60 h-170 z" fill="#b98a55" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x - 110},{y - 90} h170" stroke="#8a6740" stroke-width="5"/>'
            f'<path d="M{x + 60},{y - 80} L{x + 170},{y - 30}" stroke="{WOOD}" stroke-width="10" stroke-linecap="round"/>'
            f'<circle cx="{x - 60}" cy="{y - 34}" r="36" fill="none" stroke="{INK}" stroke-width="12"/>'
            f'<circle cx="{x - 60}" cy="{y - 34}" r="36" fill="none" stroke="{WOOD}" stroke-width="5"/>'
            f'<path d="M{x - 60},{y - 70} v72 M{x - 96},{y - 34} h72" stroke="{WOOD}" stroke-width="5"/>')


def decor_item(name, x, y, near=True, scale=None):
    """Jedna drobnost sveta stojaca na (x, y). near=False: mensia verzia do pozadia."""
    s = scale if scale is not None else (1.0 if near else 0.45)
    if name == "driftwood":
        return _driftwood(x, y, 230 * s)
    if name == "trees":
        return leaf_tree(x, y, 420 * s) + leaf_tree(x + 150 * s, y, 330 * s)
    if name == "fence":
        return ""          # plot kresli _fence (potrebuje profil)
    if name == "haybales":
        return _haybale(x, y, 58 * s) + _haybale(x + 150 * s, y, 50 * s)
    if name == "firs":
        return _fir(x, y, 300 * s) + _fir(x + 120 * s, y, 230 * s)
    if name == "cairn":
        return _cairn(x, y, s)
    if name == "iceblocks":
        return (f'<g transform="translate({x:.0f},{y:.0f}) scale({s:.2f})">{_ice_block(0, 0, 120, 90)}'
                f'{_ice_block(110, 0, 80, 60)}</g>')
    if name == "deadtree":
        return _dead_tree(x, y, 320 * s)
    if name == "boulders":
        return _boulder(x, y, 130 * s, col("rock", tone(STONE)), col("rock_line")) + _boulder(x + 120 * s, y, 80 * s, col("rock", tone(STONE)))
    if name == "mushrooms":
        return _mushrooms(x, y)
    if name == "stump":
        import worlds_ext as X
        return X.stump(x, y, 60 * s, 50 * s)
    if name == "ferns":
        import worlds_ext as X
        return X.fern(x, y, 1.3 * s, col("canopy_d", LEAF)) + X.fern(x + 60 * s, y, 0.9 * s, col("canopy_d", LEAF))
    if name == "lamppost":
        import worlds_ext as X
        return X.lamp_post(x, y, 420 * s, s)
    if name == "bench":
        return _bench(x, y)
    if name == "cart":
        return _cart(x, y)
    return ""


NEAR_SLOTS = (740, -560, -1620)


def _decor_near(kind_, hy):
    out = ""
    for i, name in enumerate(decor()):
        if name in ("sailboat", "buoy", "island", "gulls", "duneridge"):
            continue
        x = NEAR_SLOTS[i % len(NEAR_SLOTS)]
        if walk_skip(kind_, x):
            continue
        if name == "fence":
            out += _fence(x - 200, x + 250, hy)
        elif name == "stonewall":
            out += _stonewall(x - 180, x + 200, hy)
        else:
            out += decor_item(name, x, hy(x) + 3)
    return out


# ================================================================== vzdialena vrstva uvodu/slucky
SHORE_HZ = {"beach": 1120, "cliffs": 1000, "harbour": 1105}
DUSK_FAR_Y = {("shore", "beach"): 1112, ("shore", "cliffs"): 992, ("shore", "harbour"): 1097,
              ("hill", "meadow"): 930, ("hill", "rocky"): 960, ("hill", "fields"): 1010,
              ("snow", "peaks"): 860, ("snow", "tundra"): 1116, ("snow", "glacier"): 900,
              ("desert", "dunes"): 1110, ("desert", "mesa"): 1080}
DUSK_FAR_Y_KIND = {"forest": 800, "city": 840, "sea": 1078}


def far_sun(kind_):
    if not CUR or kind_ in ("cave",) or time() != "dusk" or weather() not in ("clear", "fog"):
        return ""
    if kind_ == "city" and terrain() == "library":
        return ""
    y = DUSK_FAR_Y.get((kind_, terrain()), DUSK_FAR_Y_KIND.get(kind_, 1000))
    return dusk_sun(800, y, 80)


def _waves(x0, x1, y0, rows, step=250, w=60):
    return "".join(f'<path d="M{x0 + i * step + (j % 2) * step / 2:.0f},{y0 + j * 52 + (i % 3) * 12} q{w / 2:.0f},-16 {w},0 '
                   f'q{w / 2:.0f},16 {w},0" stroke="{foam()}" stroke-width="7" fill="none" stroke-linecap="round"/>'
                   for j in range(rows) for i in range(int((x1 - x0) / step) + 1))


def _stack(x, y, h, w=90):
    rock, gr = col("rock"), col("grass")
    return (f'<path d="M{x - w / 2:.0f},{y:.0f} L{x - w * 0.44:.0f},{y - h * 0.6:.0f} L{x - w * 0.22:.0f},{y - h:.0f} '
            f'L{x + w * 0.16:.0f},{y - h * 0.95:.0f} L{x + w * 0.34:.0f},{y - h * 0.5:.0f} L{x + w / 2:.0f},{y:.0f} Z" '
            f'fill="{rock}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
            f'<path d="M{x - w * 0.24:.0f},{y - h * 0.97:.0f} L{x + w * 0.14:.0f},{y - h * 0.93:.0f}" stroke="{gr}" stroke-width="10" '
            f'stroke-linecap="round"/>'
            f'<path d="M{x - w * 0.8:.0f},{y - 4:.0f} q{w * 0.2:.0f},-12 {w * 0.4:.0f},0 M{x + w * 0.4:.0f},{y - 4:.0f} '
            f'q{w * 0.2:.0f},-12 {w * 0.4:.0f},0" stroke="{foam()}" stroke-width="7" fill="none" stroke-linecap="round"/>')


def _island(x, hz, w=330, h=66):
    return (f'<path d="M{x - w / 2:.0f},{hz + 2} Q{x - w * 0.3:.0f},{hz - h:.0f} {x - w * 0.02:.0f},{hz - h * 0.88:.0f} '
            f'Q{x + w * 0.22:.0f},{hz - h * 1.1:.0f} {x + w / 2:.0f},{hz + 2} Z" fill="{col("island", tone("#9fb0a0"))}" '
            f'stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')


def _buoy(x, y, s=1.0):
    return (f'<path d="M{x - 16 * s:.0f},{y:.0f} L{x - 9 * s:.0f},{y - 48 * s:.0f} H{x + 9 * s:.0f} L{x + 16 * s:.0f},{y:.0f} Z" '
            f'fill="#d94a3a" stroke="{INK}" stroke-width="{5 * s:.1f}" stroke-linejoin="round"/>'
            f'<path d="M{x - 12 * s:.0f},{y - 22 * s:.0f} h{24 * s:.0f}" stroke="#ffffff" stroke-width="{8 * s:.1f}"/>'
            f'<path d="M{x},{y - 48 * s:.0f} v{-14 * s:.0f}" stroke="{INK}" stroke-width="{4 * s:.1f}"/>'
            f'<circle cx="{x}" cy="{y - 64 * s:.0f}" r="{6 * s:.1f}" fill="{"#ffd45a" if night() else "#f5c542"}" '
            f'stroke="{INK}" stroke-width="{3 * s:.1f}"/>'
            f'<path d="M{x - 30 * s:.0f},{y + 4:.0f} q{15 * s:.0f},-8 {30 * s:.0f},0 q{15 * s:.0f},8 {30 * s:.0f},0" stroke="{foam()}" '
            f'stroke-width="{5 * s:.1f}" fill="none" stroke-linecap="round"/>')


def _sail(x, hz, s=0.24):
    from props import p_ship_far
    return f'<g transform="translate({x},{hz - 2}) scale({s})">{p_ship_far()[0]}</g>'


def _mini_lighthouse(x, y, s=0.2):
    from props_story import p_lighthouse
    return f'<g transform="translate({x},{y}) scale({s})">{p_lighthouse()[0]}</g>'


def _far_shore():
    t = terrain()
    sea = col("sea")
    hz = SHORE_HZ.get(t, 1120)
    out = (f'<path d="M-900,{hz} H2400 V2100 H-900 Z" fill="{sea}" stroke="none" opacity="0.9"/>'
           f'<path d="M-900,{hz} H2400" stroke="{INK}" stroke-width="8" fill="none"/>'
           + _waves(-800, 2400, hz + 46, 6 if t == "cliffs" else 3))
    if t == "cliffs":
        rock, gr, rl = col("rock"), col("grass"), col("rock_line")
        # vzdialeny myS s kolmym utesom vlavo (v zaverecnej chodzi je v zabere cely)
        out += (f'<path d="M-900,{hz + 420} L-900,{hz - 150} L-420,{hz - 162} Q-200,{hz - 172} 20,{hz - 142} L62,{hz - 108} '
                f'L40,{hz - 40} L92,{hz + 30} L70,{hz + 120} L110,{hz + 420} Z" fill="{rock}" stroke="{INK}" stroke-width="6" '
                f'stroke-linejoin="round"/>'
                f'<path d="M-900,{hz - 142} L-420,{hz - 154} Q-200,{hz - 164} 16,{hz - 134}" stroke="{gr}" stroke-width="14" '
                f'fill="none" stroke-linecap="round"/>'
                f'<path d="M-600,{hz - 90} h180 M-300,{hz - 40} h220 M-700,{hz + 20} h260 M-60,{hz + 60} h110" stroke="{rl}" '
                f'stroke-width="5" fill="none" stroke-dasharray="60 30" stroke-linecap="round"/>'
                f'<path d="M40,{hz + 70} q20,-12 40,0 q20,-12 40,0" stroke="{foam()}" stroke-width="7" fill="none" stroke-linecap="round"/>')
        out += _stack(620, hz + 130, 170, 96) + _stack(1010, hz + 150, 210, 110) + _stack(1180, hz + 110, 90, 60)
    elif t == "harbour":
        stone, line = col("stone"), col("stone_line")
        out += (f'<path d="M-900,{hz + 26} H600 L630,{hz + 58} H-900 Z" fill="{stone}" stroke="{INK}" stroke-width="5" '
                f'stroke-linejoin="round"/>'
                + "".join(f'<path d="M{x},{hz + 28} v28" stroke="{line}" stroke-width="4"/>' for x in range(-860, 600, 64))
                + _mini_lighthouse(606, hz + 28, 0.19))
        for bx, s in ((180, 0.5), (390, 0.42)):
            out += (f'<g transform="translate({bx},{hz + 92}) scale({s})">'
                    f'{_boat(0, 0, ("#3f6f8f", "#b5543c", "#4f7a54")[(CUR["palette"] + bx) % 3])}</g>')
    return out


def _far_rocky():
    rock, ridge, r2 = col("rock"), col("ridge"), col("ridge2")
    r = random.Random(43)
    pts, x = [], -900
    while x <= 2400:
        pts.append((x, 1050 + r.randint(-110, 30)))
        x += r.randint(70, 140)
    d = "M-900,1460 " + " ".join(f"L{a},{b}" for a, b in pts) + " L2400,1460 Z"
    out = f'<path d="{d}" fill="{r2}" stroke="{ridge}" stroke-width="6" stroke-linejoin="round"/>'
    pts2, x = [], -900
    while x <= 2400:
        pts2.append((x, 1120 + r.randint(-60, 20)))
        x += r.randint(90, 170)
    d2 = "M-900,1460 " + " ".join(f"L{a},{b}" for a, b in pts2) + " L2400,1460 Z"
    out += f'<path d="{d2}" fill="{rock}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
    for bx in (-500, 140, 560, 980, 1500):
        out += _boulder(bx, 1150, 70, rock, col("rock_line"), 5)
    return out


def _far_fields():
    fa, fb, ridge = col("field_a"), col("field_b"), col("ridge")
    sub = col("ground_sub")
    out = ""
    for k in range(3):
        y0 = 1030 + k * 50
        pts = " ".join(f"L{x},{y0 + 20 * math.sin(x / 260.0 + k * 1.3):.0f}" for x in range(-900, 2401, 60))
        out += (f'<path d="M-900,1460 {pts} L2400,1460 Z" fill="{(fa, fb)[k % 2]}" stroke="{ridge}" stroke-width="5" '
                f'stroke-linejoin="round"/>')
        out += "".join(f'<path d="M{x},{y0 + 26 + 20 * math.sin(x / 260.0 + k * 1.3):.0f} l70,6" stroke="{sub}" stroke-width="4" '
                       f'fill="none" stroke-linecap="round"/>' for x in range(-860, 2400, 120))
    # plot a stoh na poli
    fy = 1125
    out += "".join(f'<path d="M{x},{fy + 20 * math.sin(x / 260.0 + 2.6) + 4:.0f} v-34" stroke="{INK}" stroke-width="5"/>'
                   for x in range(-900, 2400, 70))
    out += f'<path d="M-900,{fy - 18} ' + " ".join(f"L{x},{fy + 20 * math.sin(x / 260.0 + 2.6) - 18:.0f}" for x in range(-900, 2401, 60)) + \
        f'" stroke="{INK}" stroke-width="4" fill="none"/>'
    out += _haybale(700, 1085, 30) + _haybale(790, 1090, 26)
    return out


def _far_tundra():
    snow, line, mtn = col("snow"), col("line"), col("mtn_far")
    ml = col("mtn_line")
    out = (f'<path d="M-900,1134 Q-500,1096 -120,1122 T640,1116 T1500,1124 T2400,1118 V1460 H-900 Z" fill="{mtn}" '
           f'stroke="{ml}" stroke-width="5"/>'
           f'<path d="M-900,1142 H2400 V1460 H-900 Z" fill="{snow}" stroke="none"/>'
           f'<path d="M-900,1142 H2400" stroke="{ml}" stroke-width="6" fill="none"/>')
    out += "".join(f'<path d="M{x},{1170 + (i % 4) * 30} q70,-16 150,-4" stroke="{line}" stroke-width="6" fill="none" '
                   f'stroke-linecap="round"/>' for i, x in enumerate(range(-860, 2400, 190)))
    return out


def _far_glacier():
    mtn, ml, ice, il = col("mtn_far"), col("mtn_line"), col("ice"), col("ice_line")
    out = (f'<path d="M-900,1150 L-520,880 L-260,1000 L60,820 L420,980 L760,840 L1120,1010 L1500,860 L1900,1000 L2400,900 '
           f'V1460 H-900 Z" fill="{mtn}" stroke="{ml}" stroke-width="7" stroke-linejoin="round"/>')
    r = random.Random(57)
    pts, x = [], -900
    while x <= 2400:
        pts += [(x, 1040 + r.randint(-26, 26)), (x + 60, 1040 + r.randint(-40, 10))]
        x += r.randint(110, 170)
    d = "M-900,1460 " + " ".join(f"L{a},{b}" for a, b in pts) + " L2400,1460 Z"
    out += f'<path d="{d}" fill="{ice}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
    out += "".join(f'<path d="M{x},{1050 + (i % 3) * 8} l8,40 l-10,34" stroke="{il}" stroke-width="5" fill="none" '
                   f'stroke-linecap="round"/>' for i, x in enumerate(range(-860, 2400, 110)))
    out += f'<path d="M-900,1150 H2400 V1460 H-900 Z" fill="{col("snow")}" stroke="{ml}" stroke-width="5"/>'
    return out


def _far_mesa():
    rock, rl, far_ = col("rock"), col("rock_line"), col("far")
    dl = col("dune_line")
    out = ""
    for x0_, x1_, top, lean in ((-700, -80, 860, 60), (260, 820, 930, 50), (1150, 1500, 900, 40), (1800, 2300, 950, 70)):
        out += (f'<path d="M{x0_ - lean},1160 L{x0_},{top} H{x1_} L{x1_ + lean},1160 Z" fill="{rock}" stroke="{INK}" '
                f'stroke-width="6" stroke-linejoin="round"/>'
                + "".join(f'<path d="M{x0_ - lean * f + 8:.0f},{top + (1160 - top) * f:.0f} H{x1_ + lean * f - 8:.0f}" '
                          f'stroke="{rl}" stroke-width="5" fill="none" stroke-dasharray="50 22"/>' for f in (0.25, 0.5, 0.75)))
    out += (f'<path d="M-900,1150 Q-300,1130 300,1156 T1500,1148 T2400,1152 V1460 H-900 Z" fill="{far_}" stroke="{dl}" '
            f'stroke-width="6"/>')
    return out


def _far_birch():
    import worlds_ext as X
    far_, fl = col("pine_far"), col("pine_far_line")
    canopy = col("canopy")
    r = random.Random(13)
    out = ""
    pts, x = [], -900
    while x < 2400:
        rr = r.randint(40, 70)
        pts.append((x, rr))
        x += int(rr * 1.3)
    crowns = "".join(f'<circle cx="{a}" cy="{1120 - rr * 0.8:.0f}" r="{rr}"/>' for a, rr in pts)
    out += f'<g fill="{far_}" stroke="{fl}" stroke-width="5">{crowns}</g>'
    out += f'<path d="M-900,1120 H2400 V1460 H-900 Z" fill="{col("floor")}" stroke="{fl}" stroke-width="5"/>'
    x = -880
    while x < 2400:
        h = r.randint(220, 330)
        out += birch(x, 1180, h, canopy, col("canopy_d"), 5)
        x += r.randint(110, 190)
    out += f'<path d="M-900,1176 H2400 V1460 H-900 Z" fill="{tone("#dcd9b3")}" stroke="{fl}" stroke-width="5"/>'
    return out


def _far_alley():
    import worlds_ext as X
    r = random.Random(17)
    out = ""
    gb = 1186
    x = -900
    while x < 2400:
        w = r.randint(140, 210)
        h = r.randint(420, 560)
        out += X.house(x, gb, w, h, r, sw=5)
        x += w
    out += f'<path d="M-900,{gb} H2400 V1460 H-900 Z" fill="{col("cobble")}" stroke="{col("skyline_line")}" stroke-width="5"/>'
    return out


def far(p, kind_):
    """Cela vzdialena vrstva pre breh (vsetky terny) a nove varianty terenu; inak None."""
    if not CUR or kind_ != CUR["world"]:
        return None
    if _pl().on():
        return _pl().far(p, kind_)
    t = terrain()
    if kind_ == "shore":
        body = _far_shore()
    elif (kind_, t) == ("hill", "rocky"):
        body = _far_rocky()
    elif (kind_, t) == ("hill", "fields"):
        body = _far_fields()
    elif (kind_, t) == ("snow", "tundra"):
        body = _far_tundra()
    elif (kind_, t) == ("snow", "glacier"):
        body = _far_glacier()
    elif (kind_, t) == ("desert", "mesa"):
        body = _far_mesa()
    elif (kind_, t) == ("forest", "birch"):
        body = _far_birch()
    elif (kind_, t) == ("city", "alley"):
        body = _far_alley()
    else:
        return None
    return f'<g id="{p}_far">{far_sun(kind_)}{body}{far_decor(kind_)}{fog_far(p)}{walk_clouds(p)}{birds()}</g>'


def decorate_far(p, kind_, svg):
    """Doplni do existujucej vzdialenej vrstvy vecerne slnko (za scenu), drobnosti a hmlu (pred oblaky)."""
    if not CUR:
        return svg
    head = f'<g id="{p}_far">'
    if svg.startswith(head):
        svg = head + far_sun(kind_) + svg[len(head):]
    tag = f'<g id="{p}_cloud">'
    i = svg.find(tag)
    extra = far_decor(kind_) + fog_far(p)
    if i >= 0:
        svg = svg[:i] + extra + svg[i:]
    return svg


def far_decor(kind_):
    out = ""
    t = terrain()
    for name in decor():
        if kind_ == "shore":
            hz = SHORE_HZ.get(t, 1120)
            # polohy mimo morskych stlpov (utes) a vlnolamu s majakom (pristav)
            if name == "sailboat":
                big, small = {"cliffs": (840, 470), "harbour": (820, 1280)}.get(t, (1040, 300))
                out += _sail(big, hz, 0.24) + _sail(small, hz, 0.15)
            elif name == "buoy":
                out += _buoy({"cliffs": 760, "harbour": 700}.get(t, 470), hz + (160 if t == "cliffs" else 66), 0.9)
            elif name == "island":
                ix, iw = {"cliffs": (250, 260), "harbour": (1050, 300)}.get(t, (760, 330))
                out += _island(ix, hz, iw, 66)
            elif name == "gulls" and time() != "night" and weather() != "rain":
                out += gulls(((420, 640, 1.0), (500, 600, 0.8), (980, 700, 0.9), (1560, 620, 1.0)))
        elif kind_ == "hill":
            # louka ma v dialke len ciaru hrebena (bez vyplne) - drobnosti stoja presne na nej
            if t == "meadow":
                ty = (_y_on(MEADOW_FAR, 260) + 4, _y_on(MEADOW_FAR, 900) + 4)
                hy_ = (_y_on(MEADOW_FAR, 600) + 3, _y_on(MEADOW_FAR, 652) + 3)
            else:
                ty, hy_ = (1160, 1150), (1110, 1112)
            if name == "trees":
                out += leaf_tree(260, ty[0], 150, sw=5) + leaf_tree(900, ty[1], 130, sw=5)
            elif name == "haybales" and t != "fields":
                out += _haybale(600, hy_[0], 22) + _haybale(652, hy_[1], 18)
        elif kind_ == "snow":
            if name == "firs":
                out += _fir(300, 1150, 120) + _fir(980, 1146, 100)
        elif kind_ == "desert":
            if name == "deadtree":
                out += _dead_tree(920, 1150, 150)
            elif name == "duneridge":
                dl = col("dune_line", "#bda57a")
                out += (f'<path d="M-900,1130 q260,-90 560,-10 q300,70 600,-40 q300,-90 620,10 q300,80 620,-30" '
                        f'fill="none" stroke="{dl}" stroke-width="7" stroke-linecap="round"/>')
    return out


# ================================================================== inscenovane zabery: pozadie
def _bd_shore(hor):
    t = terrain()
    sea = col("sea")
    hz = stage_hz(hor)
    out = (f'<path d="M-300,{hz} H1400 V{hor + 60} H-300 Z" fill="{sea}" stroke="none" opacity="0.9"/>'
           f'<path d="M-300,{hz} H1400" stroke="{INK}" stroke-width="7" fill="none"/>'
           + "".join(f'<path d="M{x + (j % 2) * 130},{hz + 40 + j * 46 + (i % 3) * 10} q24,-12 48,0 q24,12 48,0" '
                     f'stroke="{foam()}" stroke-width="6" fill="none" stroke-linecap="round"/>'
                     for j in range(max(1, int((hor - hz) / 60))) for i, x in enumerate(range(-200, 1300, 260))))
    if t == "cliffs":
        rock, gr, rl = col("rock"), col("grass"), col("rock_line")
        out += (f'<path d="M1400,{hor + 60} L1400,{hz - 150} L1010,{hz - 138} Q880,{hz - 130} 800,{hz - 104} L824,{hz - 40} '
                f'L790,{hz + 30} L826,{hz + 110} L800,{hor + 60} Z" fill="{rock}" stroke="{INK}" stroke-width="7" '
                f'stroke-linejoin="round"/>'
                f'<path d="M1400,{hz - 142} L1010,{hz - 130} Q880,{hz - 122} 806,{hz - 98}" stroke="{gr}" stroke-width="16" '
                f'fill="none" stroke-linecap="round"/>'
                f'<path d="M880,{hz - 40} h200 M850,{hz + 50} h260 M900,{hz + 150} h220" stroke="{rl}" stroke-width="5" '
                f'fill="none" stroke-dasharray="60 26"/>')
        # morske stlpy daleko pri horizonte (male) - nie za nohami postavy
        out += _stack(260, hz + 76, 118, 70) + _stack(470, hz + 96, 76, 48)
    elif t == "harbour":
        stone, line = col("stone"), col("stone_line")
        out += (f'<path d="M-300,{hz + 36} H700 L726,{hz + 66} H-300 Z" fill="{stone}" stroke="{INK}" stroke-width="6" '
                f'stroke-linejoin="round"/>'
                + "".join(f'<path d="M{x},{hz + 38} v26" stroke="{line}" stroke-width="4"/>' for x in range(-260, 700, 60))
                + _mini_lighthouse(708, hz + 38, 0.22))
        for bx, s in ((180, 0.62), (930, 0.7)):
            out += (f'<g transform="translate({bx},{hor - 14}) scale({s})">'
                    f'{_boat(0, 0, ("#3f6f8f", "#b5543c", "#4f7a54")[(CUR["palette"] + bx) % 3])}</g>')
    return out


def _bd_hill(hor, r):
    t = terrain()
    ridge, r2 = col("ridge"), col("ridge2")
    out = ""
    if t == "rocky":
        rock = col("rock")
        pts, x = [], -300
        while x <= 1400:
            pts.append((x, hor - 170 - r.randint(0, 140)))
            x += r.randint(60, 120)
        out += (f'<path d="M-300,{hor + 60} ' + " ".join(f"L{a},{b}" for a, b in pts) + f' L1400,{hor + 60} Z" fill="{r2}" '
                f'stroke="{ridge}" stroke-width="7" stroke-linejoin="round"/>')
        pts, x = [], -300
        while x <= 1400:
            pts.append((x, hor - 60 - r.randint(0, 70)))
            x += r.randint(80, 150)
        out += (f'<path d="M-300,{hor + 60} ' + " ".join(f"L{a},{b}" for a, b in pts) + f' L1400,{hor + 60} Z" fill="{rock}" '
                f'stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>')
        for bx, w in ((120, 110), (560, 80), (960, 130)):
            out += _boulder(bx, hor - 10, w, rock, col("rock_line"), 6)
        return out
    if t == "fields":
        fa, fb, sub = col("field_a"), col("field_b"), col("ground_sub")
        for k in range(3):
            y0 = hor - 170 + k * 52
            pts = " ".join(f"L{x},{y0 + 16 * math.sin(x / 200.0 + k * 1.1):.0f}" for x in range(-300, 1401, 50))
            out += (f'<path d="M-300,{hor + 60} {pts} L1400,{hor + 60} Z" fill="{(fa, fb)[k % 2]}" stroke="{ridge}" '
                    f'stroke-width="6" stroke-linejoin="round"/>')
            out += "".join(f'<path d="M{x},{y0 + 22 + 16 * math.sin(x / 200.0 + k * 1.1):.0f} l60,4" stroke="{sub}" '
                           f'stroke-width="4" fill="none" stroke-linecap="round"/>' for x in range(-260, 1400, 110))
        out += _haybale(840, hor - 40, 44)
        return out
    # louka: dva hrebene (palety) a stromceky v dialke
    out += (f'<path d="M-300,{hor - 60} Q60,{hor - 230} 380,{hor - 110} T980,{hor - 150} T1500,{hor - 80}" '
            f'fill="none" stroke="{ridge}" stroke-width="7" stroke-linecap="round"/>'
            f'<path d="M-300,{hor - 20} Q200,{hor - 110} 560,{hor - 50} T1400,{hor - 60}" '
            f'fill="none" stroke="{r2}" stroke-width="6" stroke-linecap="round"/>')
    if "trees" not in decor():
        for x, y in ((190, hor - 150), (860, hor - 170)):
            out += (f'<path d="M{x},{y + 40} l0,-40 M{x},{y} q-26,-6 -18,-32 q18,-26 40,0 q8,26 -22,32" '
                    f'fill="none" stroke="{ridge}" stroke-width="6"/>')
    return out


def _bd_tundra(hor):
    snow, line, mtn, ml = col("snow"), col("line"), col("mtn_far"), col("mtn_line")
    hz = stage_hz(hor)
    return (f'<path d="M-300,{hz + 6} Q60,{hz - 30} 420,{hz - 4} T1100,{hz - 10} T1500,{hz} V{hor + 60} H-300 Z" fill="{mtn}" '
            f'stroke="{ml}" stroke-width="5"/>'
            f'<path d="M-300,{hz + 14} H1400 V{hor + 60} H-300 Z" fill="{snow}" stroke="none"/>'
            f'<path d="M-300,{hz + 14} H1400" stroke="{ml}" stroke-width="6" fill="none"/>'
            + "".join(f'<path d="M{x},{hz + 34 + (i % 3) * 16} q60,-12 130,-2" stroke="{line}" stroke-width="5" fill="none" '
                      f'stroke-linecap="round"/>' for i, x in enumerate(range(-240, 1400, 170))))


def _bd_glacier(hor, r):
    mtn, ml, ice, il = col("mtn_far"), col("mtn_line"), col("ice"), col("ice_line")
    out = (f'<path d="M-300,{hor + 40} L-100,{hor - 420} L140,{hor - 300} L420,{hor - 520} L700,{hor - 330} L960,{hor - 480} '
           f'L1400,{hor - 280} L1400,{hor + 40} Z" fill="{mtn}" stroke="{ml}" stroke-width="7" stroke-linejoin="round"/>')
    pts, x = [], -300
    while x <= 1400:
        pts += [(x, hor - 250 + r.randint(-20, 20)), (x + 50, hor - 250 + r.randint(-40, 0))]
        x += r.randint(90, 140)
    out += (f'<path d="M-300,{hor + 60} ' + " ".join(f"L{a},{b}" for a, b in pts) + f' L1400,{hor + 60} Z" fill="{ice}" '
            f'stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>')
    out += "".join(f'<path d="M{x},{hor - 236 + (i % 3) * 8} l10,60 l-12,50 l8,40" stroke="{il}" stroke-width="5" fill="none" '
                   f'stroke-linecap="round"/>' for i, x in enumerate(range(-260, 1400, 95)))
    out += f'<path d="M-300,{hor - 50} Q540,{hor - 70} 1400,{hor - 46} V{hor + 60} H-300 Z" fill="{col("snow")}" stroke="{ml}" stroke-width="5"/>'
    return out


def _bd_mesa(hor):
    rock, rl, far_, dl = col("rock"), col("rock_line"), col("far"), col("dune_line")
    out = ""
    for x0_, x1_, top, lean in ((-160, 360, hor - 330, 60), (640, 1160, hor - 260, 50)):
        out += (f'<path d="M{x0_ - lean},{hor + 40} L{x0_},{top} H{x1_} L{x1_ + lean},{hor + 40} Z" fill="{rock}" stroke="{INK}" '
                f'stroke-width="7" stroke-linejoin="round"/>'
                + "".join(f'<path d="M{x0_ - lean * f + 10:.0f},{top + (hor + 40 - top) * f:.0f} H{x1_ + lean * f - 10:.0f}" '
                          f'stroke="{rl}" stroke-width="6" fill="none" stroke-dasharray="60 26"/>' for f in (0.2, 0.42, 0.64)))
    out += (f'<path d="M-300,{hor - 40} Q300,{hor - 70} 700,{hor - 44} T1400,{hor - 50} V{hor + 60} H-300 Z" fill="{far_}" '
            f'stroke="{dl}" stroke-width="7"/>')
    return out


def _bd_birch(hor, r):
    out = ""
    far_, fl = col("pine_far"), col("pine_far_line")
    crowns = "".join(f'<circle cx="{x}" cy="{hor - 160 - (x * 7) % 60}" r="{70 + (x * 13) % 40}"/>' for x in range(-300, 1400, 90))
    out += f'<g fill="{far_}" stroke="{fl}" stroke-width="5">{crowns}</g>'
    out += f'<path d="M-300,{hor - 40} H1400 V{hor + 60} H-300 Z" fill="{col("floor")}" stroke="{fl}" stroke-width="5"/>'
    for x, h in ((-20, 560), (130, 470), (250, 380), (860, 430), (990, 540), (1100, 480)):
        out += birch(x, hor - 20, h)
    return out


def _bd_alley(hor, r):
    import worlds_ext as X
    out = ""
    x = -160
    while x < 1250:
        w = r.randint(170, 230)
        h = r.randint(520, 700)
        out += X.house(x, hor - 10, w, h, r, sw=6)
        x += w
    # vyvesny stit
    out += (f'<path d="M760,{hor - 420} h110" stroke="{INK}" stroke-width="8"/>'
            f'<path d="M790,{hor - 420} v30 M850,{hor - 420} v30" stroke="{INK}" stroke-width="4"/>'
            f'<path d="M770,{hor - 390} h100 v60 h-100 z" fill="{tone("#c9a24a")}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>')
    return out


def backdrop(kind_, hor, r):
    """Pozadie inscenovanych zaberov pre breh, kopec a nove varianty; inak None (povodne pozadie)."""
    if not CUR or kind_ != CUR["world"]:
        return None
    if _pl().on():
        return _pl().backdrop(kind_, hor, r)
    t = terrain()
    if kind_ == "shore":
        return _bd_shore(hor)
    if kind_ == "hill":
        return _bd_hill(hor, r)
    if (kind_, t) == ("snow", "tundra"):
        return _bd_tundra(hor)
    if (kind_, t) == ("snow", "glacier"):
        return _bd_glacier(hor, r)
    if (kind_, t) == ("desert", "mesa"):
        return _bd_mesa(hor)
    if (kind_, t) == ("forest", "birch"):
        return _bd_birch(hor, r)
    if (kind_, t) == ("city", "alley"):
        return _bd_alley(hor, r)
    return None


def backdrop_extra(p, kind_, hor):
    """Drobnosti v dialke + vecerne slnko sa kresli v sky(); tu drobnosti a hmla nad pozadim."""
    if not CUR or kind_ != CUR["world"]:
        return ""
    if _pl().on():
        return fog_band(p, hor)          # drobnosti miest su priamo v places.backdrop
    out = ""
    t = terrain()
    hz = stage_hz(hor)
    for name in decor():
        if kind_ == "shore":
            if name == "sailboat":
                out += _sail({"cliffs": 640, "harbour": 560}.get(t, 940), hz, 0.22)
            elif name == "buoy":
                out += _buoy({"harbour": 700}.get(t, 640), (hz + 70) if t != "cliffs" else (hor - 40), 0.8)
            elif name == "island":
                ix, iw = {"cliffs": (90, 200), "harbour": (400, 260)}.get(t, (150, 260))
                out += _island(ix, hz, iw, 56)
            elif name == "gulls" and time() != "night" and weather() != "rain":
                out += gulls(((300, hor - 700, 1.1), (380, hor - 740, 0.9), (620, hor - 660, 1.0)))
        elif kind_ == "hill":
            if t == "meadow":
                r1, r2 = _meadow_stage(hor)
                ty = (_y_on(r1, 190) + 4, _y_on(r1, 860) + 4)
                hy_ = (_y_on(r2, 760) + 3, _y_on(r2, 830) + 3)
            else:
                ty, hy_ = (hor - 110, hor - 130), (hor - 40, hor - 36)
            if name == "trees":
                out += leaf_tree(190, ty[0], 200, sw=6) + leaf_tree(860, ty[1], 170, sw=6)
            elif name == "haybales" and t != "fields":
                out += _haybale(760, hy_[0], 34) + _haybale(830, hy_[1], 28)
            elif name == "stonewall":
                fill = col("rock", tone(STONE))
                out += "".join(f'<path d="M{x},{hor - 24} q-3,-26 20,-26 q24,0 22,26 z" fill="{fill}" stroke="{INK}" '
                               f'stroke-width="4" stroke-linejoin="round"/>' for x in range(-280, 1400, 40))
            elif name == "fence":
                out += "".join(f'<path d="M{x},{hor - 20} v-56" stroke="{INK}" stroke-width="6"/>' for x in range(-280, 1400, 90))
                out += f'<path d="M-300,{hor - 40} H1400 M-300,{hor - 64} H1400" stroke="{INK}" stroke-width="4"/>'
        elif kind_ == "snow":
            if name == "firs":
                out += _fir(110, hor - 30, 150) + _fir(970, hor - 34, 120)
            elif name == "cairn":
                out += _cairn(820, hor - 30, 0.6)
            elif name == "iceblocks" and t != "glacier":
                out += _ice_block(300, hor - 30, 70, 50)
        elif kind_ == "desert":
            if name == "deadtree":
                out += _dead_tree(880, hor - 36, 190)
            elif name == "boulders":
                out += _boulder(200, hor - 30, 90, col("rock", tone("#d9c49a")), col("rock_line"))
            elif name == "duneridge":
                out += (f'<path d="M-300,{hor - 90} q240,-80 520,-10 q260,60 540,-30 q260,-70 560,10" fill="none" '
                        f'stroke="{col("dune_line", "#bda57a")}" stroke-width="7" stroke-linecap="round"/>')
    return out + fog_band(p, hor)


# ================================================================== inscenovane zabery: zem
def _ground_cliff(y, x0, x1):
    rock, rl = col("rock"), col("rock_line")
    g, gd = col("grass"), col("grass_d")
    out = (f'<path d="M{x0},{y} H{x1} V4200 H{x0} Z" fill="{rock}" stroke="{INK}" stroke-width="9"/>'
           f'<path d="M{x0},{y + 5} H{x1} V{y + 70} H{x0} Z" fill="{g}"/>'
           f'<path d="M{x0},{y + 70} ' + " ".join(f"L{x},{y + 70 + (10 if (x // 60) % 2 else -2)}" for x in range(x0, x1 + 1, 60))
           + f'" stroke="{gd}" stroke-width="6" fill="none" stroke-linejoin="round"/>')
    for k in range(6):
        yy = y + 150 + k * 96
        out += (f'<path d="M{x0},{yy} ' + " ".join(f"Q{x + 70},{yy + (14 if (x // 140 + k) % 2 else -12)} {x + 140},{yy}"
                                                     for x in range(x0, x1, 140))
                + f'" stroke="{rl}" stroke-width="6" fill="none" stroke-dasharray="{90 + k * 10} {40 + k * 6}" stroke-linecap="round"/>')
    out += "".join(f'<path d="M{x},{y + 200 + (i % 3) * 110} l20,26 l-12,22 l18,18" stroke="{rl}" stroke-width="5" fill="none" '
                   f'stroke-linecap="round"/>' for i, x in enumerate(range(x0 + 120, x1, 330)))
    return out


def _ground_quay(y, x0, x1):
    stone, top_c, line = col("stone"), col("stone_top"), col("stone_line")
    out = (f'<path d="M{x0},{y} H{x1} V4200 H{x0} Z" fill="{stone}" stroke="{INK}" stroke-width="9"/>'
           f'<path d="M{x0},{y + 5} H{x1} V{y + 42} H{x0} Z" fill="{top_c}"/>'
           f'<path d="M{x0},{y + 42} H{x1}" stroke="{INK}" stroke-width="5"/>')
    for k in range(9):
        yy = y + 42 + (k + 1) * 74
        out += f'<path d="M{x0},{yy} H{x1}" stroke="{line}" stroke-width="5"/>'
        out += "".join(f'<path d="M{x},{yy - 74 + 6} v62" stroke="{line}" stroke-width="5"/>'
                       for x in range(x0 + (k % 2) * 80, x1, 160))
    out += "".join(f'<path d="M{x},{y + 8} v30" stroke="{line}" stroke-width="4"/>' for x in range(x0 + 40, x1, 220))
    return out


def _ground_rocky(y, x0, x1):
    fill, sub = col("ground"), col("ground_sub")
    rock = col("rock")
    r = random.Random(47)
    out = (f'<path d="M{x0},{y} H{x1} V4200 H{x0} Z" fill="{fill}" stroke="{INK}" stroke-width="9"/>'
           f'<path d="M{x0},{y + 240} H{x1} V4200 H{x0} Z" fill="{sub}" stroke="none" opacity="0.5"/>')
    sc = ""
    for _ in range(70):
        x, yy = r.uniform(x0, x1), y + r.uniform(20, 900)
        w = r.uniform(12, 34) * (1 + (yy - y) / 900.0)
        sc += f'<path d="M{x - w:.0f},{yy + 4:.0f} l{w * 0.4:.0f},{-w * 0.7:.0f} l{w:.0f},{-w * 0.1:.0f} l{w * 0.6:.0f},{w * 0.7:.0f} z"/>'
    return out + f'<g fill="{rock}" stroke="{INK}" stroke-width="4" stroke-linejoin="round">{sc}</g>'


def _ground_fields(y, x0, x1):
    fill, sub = col("ground"), col("ground_sub")
    out = f'<path d="M{x0},{y} H{x1} V4200 H{x0} Z" fill="{fill}" stroke="{INK}" stroke-width="9"/>'
    # brazdy sa zbiehaju k horizontu = pole v perspektive
    out += "".join(f'<path d="M{540 + (x - 540) * 0.18:.0f},{y + 6} L{x},{y + 900}" stroke="{sub}" stroke-width="7" '
                   f'fill="none" stroke-linecap="round"/>' for x in range(x0, x1 + 1, 150))
    return out


def _ground_glacier(y, x0, x1):
    ice, il = col("ice"), col("ice_line")
    snow = col("snow")
    out = (f'<path d="M{x0},{y} H{x1} V4200 H{x0} Z" fill="{ice}" stroke="{INK}" stroke-width="9"/>'
           f'<path d="M{x0},{y + 5} H{x1} V{y + 40} H{x0} Z" fill="{snow}"/>')
    r = random.Random(59)
    x = x0 + 80
    while x < x1:
        d = f"M{x},{y + 40}"
        yy = y + 40
        for j in range(r.randint(3, 6)):
            yy += r.randint(40, 90)
            d += f" L{x + (16 if j % 2 else -14)},{yy}"
        out += (f'<path d="{d}" stroke="{INK}" stroke-width="7" fill="none" stroke-linejoin="round"/>'
                f'<path d="{d}" stroke="{il}" stroke-width="4" fill="none" stroke-linejoin="round" transform="translate(7,2)"/>')
        x += r.randint(260, 420)
    return out


def ground(surface, y, x0, x1):
    """Zem inscenovanych zaberov pre variant terenu; None = povodna zem (s paletou)."""
    if not CUR:
        return None
    if _pl().on():
        return _pl().ground(surface, y, x0, x1)
    k, t = kind(), terrain()
    if surface == "sand" and k == "shore":
        if t == "cliffs":
            return _ground_cliff(y, x0, x1)
        if t == "harbour":
            return _ground_quay(y, x0, x1)
        return None
    if surface == "land" and k == "hill":
        if t == "rocky":
            return _ground_rocky(y, x0, x1)
        if t == "fields":
            return _ground_fields(y, x0, x1)
        return None
    if surface == "snow" and k == "snow" and t == "glacier":
        return _ground_glacier(y, x0, x1)
    return None


def dressing(surface, sd, y, xs):
    """Drobnosti na zemi inscenovanych zaberov pre variant terenu; None = povodne."""
    if not CUR:
        return None
    if _pl().on():
        return _pl().dressing(surface, sd, y, xs)
    k, t = kind(), terrain()
    r = random.Random(sd)
    if surface == "sand" and k == "shore" and t == "cliffs":
        rock = col("rock")
        return "".join(tuft(x, y + 3, 1.2) for x in xs) + "".join(
            _boulder(x + 90, y + 2, r.randint(34, 60), rock) for x in xs[::2])
    if surface == "sand" and k == "shore" and t == "harbour":
        out = ""
        for i, x in enumerate(xs[::2]):
            out += _rope_coil(x, y + 4) if i % 2 == 0 else (
                f'<path d="M{x - 30},{y + 4} q30,-30 60,0" stroke="#4d4d4f" stroke-width="10" fill="none"/>')
        return out
    if surface == "land" and k == "hill" and t == "rocky":
        rock = col("rock")
        return "".join(_boulder(x, y + 2, r.randint(40, 80), rock, col("rock_line")) for x in xs[::2]) + "".join(
            tuft(x, y + 3) for x in xs[1::2])
    if surface == "land" and k == "hill" and t == "fields":
        return "".join(tuft(x, y + 3) + tuft(x + 36, y + 3, 0.8) for x in xs)
    if surface == "snow" and k == "snow" and t == "glacier":
        return "".join(_ice_block(x, y + 2, r.randint(50, 80), r.randint(34, 56)) for x in xs[::2])
    if surface == "sand" and k == "desert" and t == "mesa":
        rock = col("rock")
        return "".join(_boulder(x, y + 2, r.randint(40, 70), rock, col("rock_line")) for x in xs[::2])
    return None


def foreground(kind_, x0, x1, gy, r):
    """Popredie pri okrajoch obrazu pre variant terenu; None = povodne."""
    if not CUR or kind_ != CUR["world"]:
        return None
    if _pl().on():
        return _pl().foreground(kind_, x0, x1, gy, r)
    t = terrain()
    w = x1 - x0
    xa = x0 + (0.04 + r.random() * 0.10) * w
    xb = x1 - (0.04 + r.random() * 0.10) * w
    # vsetko nizko pod ciarou zeme (bliziie ku kamere) - vrch len tesne nad chodidlami, nikdy cez postavu
    # lavy okraj byva pri postave -> tam len celkom nizke veci; vyssia vec len vpravo
    if kind_ == "shore" and t == "cliffs":
        return (_boulder(xa, gy + 70, 64, col("rock"), col("rock_line")) + tuft(xa + 56, gy + 62, 1.3)
                + _boulder(xb, gy + 60, 90, col("rock"), col("rock_line")) + tuft(xb - 60, gy + 56, 1.6))
    if kind_ == "shore" and t == "harbour":
        return _rope_coil(xa, gy + 70) + _bollard(xb, gy + 80, 0.9)
    if kind_ == "hill" and t == "rocky":
        return _boulder(xa, gy + 70, 70, col("rock"), col("rock_line")) + _boulder(xb, gy + 58, 100, col("rock"))
    if kind_ == "snow" and t == "glacier":
        return _ice_block(xa, gy + 70, 80, 40) + _ice_block(xb, gy + 58, 96, 56)
    if kind_ == "desert" and t == "mesa":
        return _boulder(xa, gy + 70, 64, col("rock"), col("rock_line")) + _boulder(xb, gy + 58, 86, col("rock"))
    return None


def fore_decor(kind_, x0, x1, gy):
    """Jedna nizka drobnost sveta pri pravom okraji inscenovaneho zaberu (pod ciarou zeme, nie cez dej)."""
    if not CUR or kind_ != CUR["world"]:
        return ""
    w = x1 - x0
    x = x1 - 0.10 * w
    for name in decor():
        if name in ("driftwood", "haybales", "iceblocks", "boulders", "mushrooms", "stump", "ferns"):
            return decor_item(name, x, gy + 90, True, 0.72)
    return ""


def field_fill(surface, default):
    """Farba pola v perspektive (wide_reveal)."""
    if not CUR:
        return default
    k, t = kind(), terrain()
    if k == "shore" and t == "cliffs":
        return col("grass")
    if k == "shore" and t == "harbour":
        return col("stone")
    if surface == "sand":
        return col("sand", tone(default))
    if surface == "snow":
        return col("snow", tone(default))
    if surface == "land" and k == "hill":
        return col("ground", tone(default))
    return tone(default)


def mound_colors(kind_, default):
    """(vypln, ciara, tien) kopy nad predmetom (stage.cover_mound/chunks)."""
    if not CUR or kind_ != CUR["world"]:
        return default
    if _pl().on():
        return _pl().mound_colors(default)
    t = terrain()
    if kind_ == "shore":
        if t == "cliffs":
            s = col("soil")
            return s, INK, mix(s, "#000000", 0.12)
        s = col("sand")
        return s, col("sand_line"), mix(s, "#000000", 0.08)
    if kind_ == "desert":
        s = col("sand")
        return s, col("sand_line"), mix(s, "#000000", 0.08)
    if kind_ == "snow":
        return col("snow"), col("line", default[1]), col("shade")
    return tuple(tone(c) if c != INK else c for c in default)


# ================================================================== insert: makro zem
def ground_bg(surface):
    """Zem sveta na cely zaber (makro detail vonku); None = povodne."""
    if not CUR:
        return None
    from props import pebbles
    k, t = kind(), terrain()
    R = f'<path d="M-150,-150 H{CW + 150} V{CH + 150} H-150 Z" fill="{{}}" stroke="none"/>'
    if surface == "sand" and k == "shore":
        if t == "cliffs":
            g, gd = col("grass"), col("grass_d")
            out = R.format(g)
            # mimo popisku (hore), sipky (vlavo hore) a predmetu (stred)
            out += "".join(tuft(x, yy, 1.6) for x, yy in ((110, 1220), (330, 1480), (760, 1170), (960, 1450), (60, 700), (1020, 640)))
            out += "".join(_boulder(x, yy, w, col("rock"), col("rock_line")) for x, yy, w in ((140, 1660, 70), (930, 1580, 90)))
            return out + f'<g opacity="0.6">{pebbles(13, 8, 0, CW, 220, CH - 60).replace(DIRT2, gd)}</g>'
        if t == "harbour":
            stone, line = col("stone"), col("stone_line")
            out = R.format(stone)
            for k2, yy in enumerate(range(-40, CH + 150, 150)):
                out += f'<path d="M-150,{yy} H{CW + 150}" stroke="{line}" stroke-width="6"/>'
                out += "".join(f'<path d="M{x},{yy} v150" stroke="{line}" stroke-width="6"/>'
                               for x in range(-60 + (k2 % 2) * 120, CW + 150, 240))
            return out
        return R.format(col("sand")) + pebbles(11, 16, 0, CW, 220, CH - 60)
    if surface == "sand":
        return R.format(col("sand", tone("#e9d6a6"))) + pebbles(11, 16, 0, CW, 220, CH - 60)
    if surface == "snow":
        fill = col("ice") if t == "glacier" else col("snow")
        return R.format(fill) + pebbles(7, 10, 0, CW, 220, CH - 60)
    if surface == "land" and k == "hill":
        out = R.format(col("ground"))
        out += "".join(tuft(x, yy) for x, yy in ((110, 1220), (330, 1460), (760, 1180), (960, 1440)))
        return out + pebbles(13, 10, 0, CW, 220, CH - 60)
    return None


# ================================================================== interier (miestnost s oknom)
def room_style(s):
    """Farby miestnosti podla casu: noc = tmavsia stena aj podlaha (svieti len lampa)."""
    if not CUR:
        return s
    t = time()
    if t not in ("night", "dusk"):
        return s
    out = dict(s)
    for k, v in s.items():
        if isinstance(v, str) and v.startswith("#") and v.lower() != INK:
            r, g, b = _rgb(v)
            if t == "night":
                out[k] = _hex((r * 0.70, g * 0.72, b * 0.82))
            else:
                out[k] = _hex((r * 0.98, g * 0.93, b * 0.85))
    return out


def room_lamp(p, cam_x, gy, M):
    """V noci svieti v miestnosti lampa: teply svit na stene + mosadzna lampa na konzole."""
    if not night():
        return ""
    # visi zo stropu vysoko nad hlavou (nad "!" nad postavou aj nad dverami)
    x, y = cam_x - 150, gy - 3.1 * M
    glow = (f'<defs><radialGradient id="{p}_lampg"><stop offset="0" stop-color="#ffd98a" stop-opacity="0.55"/>'
            f'<stop offset="0.35" stop-color="#ffd98a" stop-opacity="0.26"/>'
            f'<stop offset="1" stop-color="#ffd98a" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="{x:.0f}" cy="{y + 20:.0f}" r="600" fill="url(#{p}_lampg)"/>')
    lamp = (f'<path d="M{x:.0f},{y - 600:.0f} V{y - 50:.0f}" stroke="{INK}" stroke-width="5" stroke-dasharray="10 7" fill="none"/>'
            f'<path d="M{x - 26:.0f},{y - 50:.0f} h52 l-8,20 h-36 z" fill="#b08a3e" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="M{x - 20:.0f},{y - 30:.0f} h40 v58 h-40 z" fill="#fff1c2" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M{x:.0f},{y - 14:.0f} q10,14 0,26 q-10,-12 0,-26 z" fill="#f39c34" stroke="none"/>'
            f'<path d="M{x - 26:.0f},{y + 28:.0f} h52 v10 h-52 z" fill="#b08a3e" stroke="{INK}" stroke-width="5"/>')
    return glow + lamp


def window_sky():
    if not CUR:
        return "#f7f3e8"
    t, w = time(), weather()
    if t == "night":
        return "#3b4a63"
    if t == "dusk":
        return "#f3d9b8"
    return {"overcast": "#dedcd6", "rain": "#c3c8cf", "fog": "#ebe9e3"}.get(w, "#f7f3e8")


def window_view(kind_, x0, y0, w, h):
    """Vyhlad z okna v palete a terene epizody (+ mesiac v noci); None = povodny."""
    if not CUR or kind_ != CUR["world"]:
        return None
    t = terrain()
    hz = y0 + h * 0.58
    out = ""
    if night() and weather() != "rain":
        out += moon(x0 + w * 0.7, y0 + h * 0.2, 16) + stars(seed() + 11, 4, (), y0 + 8, y0 + h * 0.4, x0 + 10, x0 + w - 10)
    elif dusk() and weather() in ("clear", "fog"):
        out += f'<circle cx="{x0 + w * 0.3:.0f}" cy="{hz - 4:.0f}" r="22" fill="#f59a45" stroke="{INK}" stroke-width="3"/>'
    if kind_ in ("shore", "sea"):
        sea = col("sea", tone("#8ecae6"))
        waves = "".join(f'<path d="M{x0 + 14 + i * 46},{hz + 22 + (i % 2) * 22} q10,-6 20,0 q10,6 20,0" fill="none" '
                        f'stroke="{foam()}" stroke-width="4" stroke-linecap="round"/>' for i in range(int(w / 46)))
        out += (f'<path d="M{x0},{hz} H{x0 + w} V{y0 + h} H{x0} Z" fill="{sea}"/>'
                f'<path d="M{x0},{hz} H{x0 + w}" stroke="{INK}" stroke-width="4"/>{waves}')
        if t == "cliffs":
            out += (f'<path d="M{x0 + w * 0.55:.0f},{y0 + h} L{x0 + w * 0.6:.0f},{hz - 40:.0f} L{x0 + w + 10:.0f},{hz - 50:.0f} '
                    f'V{y0 + h} Z" fill="{col("rock")}" stroke="{INK}" stroke-width="3"/>'
                    f'<path d="M{x0 + w * 0.6:.0f},{hz - 44:.0f} L{x0 + w + 10:.0f},{hz - 54:.0f}" stroke="{col("grass")}" stroke-width="7"/>')
        elif t == "harbour":
            out += (f'<path d="M{x0},{y0 + h - 30} H{x0 + w} V{y0 + h} H{x0} Z" fill="{col("stone")}" stroke="{INK}" stroke-width="3"/>'
                    f'<path d="M{x0 + w * 0.7:.0f},{y0 + h - 30} V{hz - 60:.0f}" stroke="{WOOD}" stroke-width="4"/>')
        elif kind_ == "shore":
            out += (f'<path d="M{x0},{y0 + h - 26} Q{x0 + w * 0.5:.0f},{y0 + h - 40} {x0 + w},{y0 + h - 22} V{y0 + h} H{x0} Z" '
                    f'fill="{col("sand")}" stroke="{INK}" stroke-width="3"/>')
        return out
    if kind_ == "hill":
        return out + (f'<path d="M{x0},{hz} Q{x0 + w * 0.35},{hz - h * 0.2} {x0 + w * 0.7},{hz - h * 0.04} T{x0 + w},{hz - h * 0.08} '
                      f'V{y0 + h} H{x0} Z" fill="{col("ground")}" stroke="{col("ridge")}" stroke-width="4"/>')
    if kind_ == "snow":
        return out + (f'<path d="M{x0},{hz + 10} L{x0 + w * 0.3},{hz - h * 0.28} L{x0 + w * 0.55},{hz - h * 0.05} '
                      f'L{x0 + w * 0.8},{hz - h * 0.32} L{x0 + w},{hz} V{y0 + h} H{x0} Z" fill="{col("mtn_near")}" '
                      f'stroke="{col("mtn_line")}" stroke-width="4"/>')
    if kind_ == "desert":
        return out + (f'<path d="M{x0},{hz} q{w * 0.3},-{h * 0.12} {w * 0.6},0 q{w * 0.2},{h * 0.08} {w * 0.4},-{h * 0.04} '
                      f'V{y0 + h} H{x0} Z" fill="{col("sand")}" stroke="{col("dune_line")}" stroke-width="4"/>')
    if kind_ == "forest":
        trees = "".join(f'<path d="M{x0 + 10 + i * 34},{hz + 6} l16,-{40 + (i % 3) * 14} l16,{40 + (i % 3) * 14} z" '
                        f'fill="{col("pine_mid")[0]}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>' for i in range(int(w / 34)))
        return out + f'<path d="M{x0},{hz} H{x0 + w} V{y0 + h} H{x0} Z" fill="{col("floor")}"/>{trees}'
    if kind_ == "city":
        roofs = "".join(f'<path d="M{x0 + i * 52},{hz + 30} V{hz - 16 - (i % 3) * 18} l26,-22 l26,22 V{hz + 30}" '
                        f'fill="{col("walls")[i % 4]}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
                        for i in range(int(w / 52) + 1))
        return out + roofs
    return None
