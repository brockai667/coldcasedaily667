# -*- coding: utf-8 -*-
r"""Vyber zaberov PRIAMO Z FAKTOV (Wikipedia), nie z vymyslenych viet.

Preco: aj ked dostal maly model katalog scen, mieral fakty na zle zabery („He descends five thousand
twenty metres" — 5 020 m je NADMORSKA VYSKA, nie hlbka) a dopisoval si porovnania, ktore vo faktoch nie su.
Tato vrstva robi vyber deterministicky: kazdy fakt zo sheetu sa klasifikuje na zaber + parametre,
vyberie sa 11-13 faktov v dramaturgickom poradi a LLM uz len napise jednu vetu ku kazdemu.

Vstup: zoznam faktov (vety z Wikipedie), svet, hrdina.  Vystup: zoznam beatov {shot, params, fact}.
"""
import re

# Kazda alternativa ma hranice slova z OBOCH stran: predtym mal \b len prvy vyraz v zozname, takze
# „device" obsahovalo „ice" (= jazero), „research" „sea", „effort" „fort", „investigate" „gate".
OBJ_SYN = {                      # co v texte -> ktory z 23 kresitelnych objektov
    "stone": r"\b(?:stones?|rocks?|boulders?|megaliths?|slabs?)\b",
    # „pillar of fire" (Tunguska) nie je kamenny pilier
    "pillar": r"\b(?:pillars?(?! of (?:fire|smoke|light|flame))|columns?(?! of (?:fire|smoke|light|water|air))|"
              r"obelisks?|stelae?|monoliths?)\b",
    "meteor": r"\b(?:asteroids?|meteors?|meteorites?|meteoroids?|comets?|fireballs?|bolides?)\b",
    "book": r"\b(?:books?|codex|codices|manuscripts?|folios?|vellum|parchment)\b",
    "mountain": r"\b(?:mountains?|peaks?|summits?|hills?|plateaus?|slopes?)\b",
    "cave": r"\b(?:caves?|caverns?|grottos?|grottoes|chambers?)\b",
    "water": r"\b(?:lakes?|water|seas?|oceans?|rivers?|ponds?|glaciers?|ice)\b",
    "ship": r"\b(?:ships?|vessels?|boats?|brigantines?|schooners?)\b",
    "wreck": r"\b(?:wrecks?|shipwrecks?|hulls?)\b",
    "gear": r"\b(?:gears?|cogs?|mechanisms?)\b",
    "machine": r"\b(?:machines?|devices?|engines?|apparatus)\b",
    "skull": r"\b(?:skulls?|cranium|crania)\b",
    "bones": r"\b(?:bones?|skeletons?|remains)\b",
    "door": r"\b(?:doors?|gates?|entrances?|portals?)\b",
    "chest": r"\b(?:chests?|box|boxes|caskets?|coffers?|crates?)\b",
    "ruin": r"\b(?:ruins?|settlements?|enclosures?|temples?|forts?|fortress|sanctuary|sanctuaries)\b",
    "map": r"\b(?:maps?|charts?)\b",
    "statue": r"\b(?:statues?|figures?|idols?|sculptures?|moai)\b",
    "tunnel": r"\b(?:tunnels?|shafts?|passages?|corridors?)\b",
    "tree": r"\b(?:trees?)\b",
    "forest": r"\b(?:forests?(?! ranger)|jungles?|woods)\b",
    "car": r"\b(?:cars?|vehicles?|trucks?)\b",
    "tablet": r"\b(?:tablets?|inscriptions?|scrolls?|discs?)\b",
    "tower": r"\b(?:towers?|lighthouses?|spires?)\b",
    "coin": r"\b(?:coins?|treasures?|gold)\b",
}
REPEATABLE = ["stone", "pillar", "statue", "tower", "tree", "tablet", "coin", "skull", "fallen_tree"]
UNITS = r"(metres|meters|m|kilometres|kilometers|km|feet|foot|ft|tons|tonnes|kg|centimetres|cm)"
# pocty s ciarkou („1,000 statues") a nasobkom („80 million trees") - predtym sa chytilo len 2-4 cislice
NUM = r"(\d{1,3}(?:,\d{3})+|\d{2,4})"
MULT = r"(?:\s+(million|billion|thousand))?"
DEAD_RX = r"(skeletons?|bodies|victims|corpses|dead|remains)"
LIVING_RX = r"(people|individuals?|inhabitants|residents|villagers|workers|soldiers|men|pilgrims|persons|refugees)"


def _count(m, num_group=1, mult_group=2):
    """(cislo, popisok) z regex zhody; popisok „80 MILLION" pre zlate cislo, None pre rok („in 1942 people")."""
    raw = m.group(num_group)
    n = int(raw.replace(",", ""))
    mult = m.group(mult_group) if mult_group else None
    if not mult and "," not in raw and 1500 <= n <= 2099:
        return None, None
    return n, (f"{n:,} {mult.upper()}" if mult else f"{n:,}")


def _obj_near(low, pos):
    """Predmet, ktoreho sa cislo tyka: najblizsi PRED cislom („stone enclosures with pillars up to 5.5 m"
    meria piliere, nie kamen). Ked pred cislom nic nie je, prvy za nim."""
    before, after = [], []
    for obj, rx in OBJ_SYN.items():
        for m in re.finditer(rx, low):
            (before if m.start() < pos else after).append((m.start(), obj))
    if before:
        return max(before)[1]
    return min(after)[1] if after else None


def find_object(text, default="stone"):
    low = text.lower()
    # pri zhode na tom istom mieste vyhra dlhsie slovo: „shipwreck" je vrak, nie lod
    hits = [(m.start(), -len(m.group(0)), obj) for obj, rx in OBJ_SYN.items() for m in [re.search(rx, low)] if m]
    return min(hits)[2] if hits else default


CARRY_RX = r"\b(removing|removed|remove|retriev\w+|carrying|carried|hauling|hauled|lifted|recovered)\b"
# „collected" len ked zbieraju ludia - „water was collected in channels" nie je dav s kosmi
PEOPLE_RX = r"\b(tourists?|team|workers?|people|villagers|locals|researchers?|divers?|scientists?|pilgrims?|expedition|crew)\b"


def _carries(low):
    return bool(re.search(CARRY_RX, low) or (re.search(r"\bcollect\w*\b", low) and re.search(PEOPLE_RX, low)))


DIG_RX = r"\b(excavat\w*|unearth\w*|dug|dig|digging)\b"
FIND_RX = r"\b(discover\w*|rediscover\w*|found|uncover\w*|spotted|noticed|stumbled)\b"


def _cargo(low):
    """Co dav nesie v kosoch - kosti a kamen musia vyzerat inak nez hlina."""
    for k, rx in (("bones", r"\b(bones?|skeletons?|remains|skulls?|bodies)\b"), ("stone", r"\b(stones?|rocks?|rubble|blocks?)\b"),
                  ("water", r"\bwater\b"), ("soil", r"\b(soil|dirt|earth|sand)\b")):
        if re.search(rx, low):
            return k
    return None


def classify(fact, world, hero=None, main_obj=None, era0="ancient"):
    """Fakt -> (shot, params) alebo None, ked sa fakt neda nakreslit.
    main_obj = hlavny predmet temy (rozmery „Its dimensions are 23.5 cm…" patria jemu),
    era0 = doba temy pre fakty bez roku (stavba majaka z 1899 nie su „ancient workers")."""
    low = fact.lower()
    obj = find_object(fact, None)
    if obj is None and re.search(r"\b(explosion|exploded|blast|air ?burst|detonat\w*|impact event)\b", low):
        obj = "meteor"                                        # vybuch na oblohe (Tunguska)

    m_unit = re.search(r"\b([\d][\d,.]*)\s*" + UNITS + r"\b", low)
    m_many = re.search(r"\b" + NUM + MULT + r"\s+(?:\w+\s+){0,2}([a-z]+s)\b", low)   # „1,000 extant monumental statues"
    # vyvratene stromy (Tunguska): pocet stromov + ich plocha - musi ist pred kotou, inak z „2,150 km²" vyjde meranie
    if re.search(r"\b(flatten\w*|felled|knocked down|uprooted|toppled|fallen)\b", low) and re.search(r"\btrees?\b", low):
        pr = {"object": "fallen_tree"}
        m_t = re.search(r"\b" + NUM + MULT + r"\s+(?:\w+\s+)?trees\b", low)
        if m_t:
            n, lab = _count(m_t)
            if n:
                pr.update(count=n, count_label=lab)
                return "wide_reveal", pr
        return "object_reveal", pr
    m_year = re.search(r"\b(\d{3,4})\s*(?:bce|bc|ce|ad)\b|\bin (\d{4})\b", low)
    m_age = re.search(r"\b(\d[\d,]*)\s*years?\s+(?:older|earlier)\b", low)

    if re.search(r"\bno (metal|wheel|writing)|without metal|neither metal", low):
        return "no_list", {"items": ["NO METAL", "NO WHEEL", "NO WRITING"]}
    if re.search(r"\b(believe[ds]?|hypothes\w+|suggest\w*|theor\w+|interpret\w+|may have|might have|proposed|"
                 r"legend|attribut\w+|blamed|speculat\w+|feared|thought to|claims?)\b", low):
        return "theory", {"bubble": _cause(low) or obj or _key_noun(low) or "question"}
    if re.search(r"\b(museum|displayed|exhibit\w*|on display|collection|housed|archives?)\b", low):
        return "exhibit", {"object": obj or main_obj or "tablet", "label": _label(fact)}
    # nevyluštene pismo / sifra -> lupa na detail (Voynich, Rongorongo, Linear A)
    if re.search(r"\b(undeciphered|decipher\w*|cipher\w*|script|symbols?|glyphs?|unknown writing|code)\b", low) \
            and (obj or main_obj) in ("book", "tablet", "stone", "map"):
        return "detail_compare", {"object": obj if obj in ("book", "tablet", "stone", "map") else main_obj}
    if m_age:
        vs = _vs(low)
        if vs:
            return "timeline_compare", {"vs": vs, "years": int(m_age.group(1).replace(",", ""))}
    # rychlost nie je rozmer („27 km/s") - bez tohto vyjde kota metra na asteroide
    speed = re.search(r"km/s|km/h|mph|per second|per hour|\bspeed\b|velocity", low)
    # vzdialenost nie je rozmer predmetu („Pitcairn Island, 2,075 km away" -> socha 2 km vysoka)
    dist = re.search(r"\b(away|distance|nearest|from the|off the coast|miles from|km from)\b", low)
    dims = re.search(r"\b(dimensions?|measur\w*|tall|high|height|wide|width|long|length|deep|depth|diameter|"
                     r"across|size|weigh\w*)\b", low)
    if m_unit and (obj or (main_obj and dims)) and not speed and not dist:
        val = float(m_unit.group(1).replace(",", ""))
        unit = {"metres": "m", "meters": "m", "feet": "ft", "foot": "ft", "kilometres": "km", "kilometers": "km",
                "tonnes": "t", "tons": "t", "centimetres": "cm"}.get(m_unit.group(2), m_unit.group(2))
        # vyska nad morom nie je rozmer objektu - taky fakt nekreslime ako kotu
        if re.search(r"\b(above sea level|altitude|elevation)\b", low):
            return ("walk_in", {"object": obj, "year": None}) if (obj and world in ("snow", "hill")) else None
        axis = "h" if re.search(r"\b(long|length|wide|width|across|span|diameter)\b", low) else "v"
        return "scale_measure", {"object": _obj_near(low, m_unit.start()) or obj or main_obj, "value": val,
                                 "unit": unit, "axis": axis}
    # dva datumy v jednom fakte („~800 CE ... ~1800 CE") = dve skupiny tisic rokov od seba; to je pointa,
    # nie pocet lebiek - inak z genetickej analyzy vyjde pole 23 lebiek a veta o troch skupinach
    two = []
    for y, e in re.findall(r"\b(\d{3,4})\s*(bce|bc|ce|ad)\b", low):
        v = -int(y) if e in ("bce", "bc") else int(y)
        if v not in [t[0] for t in two]:
            two.append((v, f"{y} {e.upper()}"))
    if len(two) >= 2 and abs(two[1][0] - two[0][0]) >= 100:
        (a, la), (b, lb) = sorted(two[:2])
        return "timeline_compare", {"vs": la, "vs2": lb, "years": b - a}
    # mrtvi („300 skeletons") sa kreslia ako lebky, zivi („20,000 people could shelter") ako dav -
    # predtym sa aj zivi obyvatelia kreslili ako pole lebiek
    m_dead = re.search(r"\b" + NUM + MULT + r"\s+(?:\w+\s+){0,2}" + DEAD_RX + r"\b", low)
    m_living = re.search(r"\b" + NUM + MULT + r"\s+(?:\w+\s+){0,2}" + LIVING_RX + r"\b", low)
    if m_living and m_living.group(3).startswith("individual") and \
            re.search(r"\b(remains|skeletons?|bones|burials?|dna|genome\w*|ancestry)\b", low):
        m_dead, m_living = m_living, None                  # „23 individuals" v genetike kostier su mrtvi
    # niekto nieco ODNASA („a team retrieved about 30 skeletons") - to je dej, nie pole lebiek;
    # musi ist pred pocitanim, inak z vety o vynasani vyjde staticka mriezka
    if _carries(low) and world != "sea":
        pr = {"era": _era(low, era0)}
        if _cargo(low):
            pr["cargo"] = _cargo(low)
        for cnt in (m_dead, m_living, m_many):
            if cnt:
                n, lab = _count(cnt)
                if n:
                    pr["count"] = n
                    break
        return "action_crowd", pr
    if m_dead:
        n, lab = _count(m_dead)
        if n:
            return "wide_reveal", {"object": "skull", "count": n, "count_label": lab}
    # zivi ludia len ked nieco robia (ukryvali sa, utiekli, zmizli) - pocet zo scitania obyvatelov nie je pribeh
    if m_living and world != "sea" and re.search(r"\b(shelter\w*|hid|hide|hiding|fled|flee\w*|lived|vanish\w*|"
                                                 r"disappear\w*|work\w*|built|march\w*|gathered|died|killed|trapped)\b", low):
        n, lab = _count(m_living)
        if n:
            return "action_crowd", {"era": _era(low, era0), "count": n, "count_label": lab}
    if m_many and (obj in REPEATABLE or find_object(m_many.group(3), None) in REPEATABLE):
        n, lab = _count(m_many)
        if n:
            return "wide_reveal", {"object": obj if obj in REPEATABLE else find_object(m_many.group(3), "stone"),
                                   "count": n, "count_label": lab}
    # datovanie („radiocarbon dating placed them around 800 CE") -> milnik s vytesanym rokom
    m_era = re.search(r"\b(\d{3,4})\s*(bce|bc|ce|ad)\b", low)
    if m_era and re.search(r"\b(dat\w+|radiocarbon|carbon|placed|around)\b", low):
        return "timeline_compare", {"vs": f"{m_era.group(1)} {m_era.group(2).upper()}", "years": None}
    # datovanie bez „AD" („carbon-dating places its creation between 1404 and 1438")
    m_pd = re.search(r"\b(1[0-8]\d\d)\b", low)
    if m_pd and re.search(r"\b(radiocarbon|carbon[- ]dat\w*|dated|dating|dates (?:to|from|back))\b", low):
        return "timeline_compare", {"vs": f"{m_pd.group(1)} AD", "years": None}
    LAND = ("hill", "snow", "desert", "cave", "forest", "city")
    # kopanie len ked fakt naozaj hovori o vykopavke; „ranger rediscovered skeletons" nie je kopanie -
    # hrdina ich NAJDE (klakne, odhrnie sneh), co je spot s akciou find
    # hladanie bez nalezu („searched the desert but found nothing") nesmie byt zaber, kde sa predmet vynori
    neg = re.search(r"\b(no trace|no sign|nothing|never found|without (?:success|result)|failed to find|"
                    r"found no|finds? only|no remains|in vain)\b", low)
    if neg and (re.search(DIG_RX, low) or re.search(FIND_RX, low) or re.search(r"\bsearch\w*\b", low)):
        return None
    if re.search(DIG_RX, low) and world in LAND:
        return "dig", {"object": obj or "stone"}
    if re.search(FIND_RX, low):
        if hero == "archaeologist" and world in LAND and world != "snow":
            return "dig", {"object": obj or "stone"}
        if obj:
            return "spot", {"object": obj}
    if re.search(r"\b(buried|filled in|backfill\w*|abandon\w*|carried|hauled|left the)\b", low) and world != "sea":
        return "action_crowd", {"era": _era(low, era0)}
    if re.search(r"\b(built|carved|erected|raised|constructed|created|transported|moved|dragged)\b", low) \
            and world != "sea":
        return "action_crowd", {"era": _era(low, era0)}
    if obj:
        return "object_reveal", {"object": obj}
    return None


def _cause(low):
    """Co ma byt v bubline: pricina, o ktorej sa spekuluje (hailstorm, fumes, waterspout)."""
    ADJ = {"sudden", "massive", "violent", "strange", "toxic", "deadly", "huge", "large", "small",
           "ancient", "possible", "likely", "freak", "great", "severe", "heavy",
           "that", "which", "whom", "they", "them", "this", "these", "those", "were", "been", "have",
           "because", "deliberately", "purposely", "intentionally", "apparently", "probably",
           "there", "their", "people", "group", "party"}
    # „a hailstorm killed them" / „legend says a hailstorm" / „caused by fumes"
    pats = (r"\b((?:[a-z]{4,}\s+){0,2}[a-z]{4,})\s+(?:killed|destroyed|struck|swept|trapped|buried)\b",
            r"(?:attributes?|attributed|blames?|blamed)\s+[a-z ]{0,20}?to\s+(?:a|an|the)?\s*((?:[a-z]{4,}\s+){0,2}[a-z]{4,})",
            r"(?:because of|due to|caused by)\s+(?:a|an|the)?\s*((?:[a-z]{4,}\s+){0,2}[a-z]{4,})",
            r"(?:says?|claims?|suggests?)\s+(?:a|an|the)?\s*((?:[a-z]{4,}\s+){0,2}[a-z]{4,})",
            r"\bthat\s+(?:a|an|the)?\s*((?:[a-z]{4,}\s+){0,2}[a-z]{4,})")
    for rx in pats:
        m = re.search(rx, low)
        if not m:
            continue
        words = [w for w in m.group(1).split() if w not in ADJ]
        if words:
            return words[-1]        # posledne slovo je zvycajne to podstatne (alcohol FUMES)
    return None


def _key_noun(low):
    stop = {"believe", "believed", "suggest", "theory", "theories", "hypothesis", "researchers", "scientists",
            "archaeologists", "historians", "people", "possibly", "which", "these", "those", "their"}
    cand = [w for w in re.findall(r"\b([a-z]{5,})\b", low) if w not in stop]
    return cand[-1] if cand else None


def _label(fact):
    m = re.search(r"\b(?:in|at) the ([A-Z][\w ]{3,28})", fact)
    return (m.group(1) if m else "Museum").strip()[:22]


def _vs(low):
    for k, rx in (("pyramid", r"pyramid"), ("trilith", r"stonehenge"), ("clock", r"clock|watch"),
                  ("column", r"rome|roman|greek|temple"), ("ship", r"ship")):
        if re.search(rx, low):
            return k
    m = re.search(r"older than (?:the )?([a-z][a-z \-]{2,20})", low)
    if m:
        return m.group(1).strip()
    # bez porovnania vo fakte si pyramidu nevymyslame (Cambyses: „a thousand years earlier" -> pyramida);
    # namiesto nej rok z faktu, inak nic
    y = re.search(r"\b(\d{3,4})\s*(bce|bc|ce|ad)\b", low)
    return f"{y.group(1)} {y.group(2).upper()}" if y else None


def _era(low, default="ancient"):
    if re.search(r"\b(museum|tourists?|visitors?|modern|today|researchers?|scientists?|team)\b", low):
        return "modern"
    # rok 2003 je sucasnost, nie „historic" - inak tim National Geographic nesie kose v klobukoch z 18. storocia
    if re.search(r"\b(19[5-9]\d|20\d\d)\b", low):
        return "modern"
    if re.search(r"\b(1[7-9]\d\d)\b", low):
        return "historic"
    return default


def topic_era(facts):
    """Doba celej temy pre fakty bez roku: median rokov vo faktoch (BCE zaporne)."""
    ys = []
    for f in facts:
        low = f.lower()
        ys += [-int(y) if e in ("bce", "bc") else int(y) for y, e in re.findall(r"\b(\d{3,4})\s*(bce|bc|ce|ad)\b", low)]
        ys += [int(y) for y in re.findall(r"\b(1[0-9]\d\d|20[0-2]\d)\b", low)]
    if not ys:
        return "ancient"
    ys.sort()
    med = ys[len(ys) // 2]
    return "modern" if med >= 1950 else "historic" if med >= 1700 else "ancient"


# ------------------------------------------------------------------ co postava v zabere ROBI
# Engine podla toho stavia pozu a vztah k predmetu (staging kontrakt: ziadny zaber, kde len stoji).
#   find    klakne, odhrnie sneh/hlinu, predmet sa odhali pod jeho rukami
#   dig     kope lopatou
#   measure meria pasmom/tycou
#   point   ukazuje na vec / na os
#   carry   nesie (dav s kosmi)
#   climb   splha / zlieza
#   watch   nakloni sa / pozera hore na velku vec, dotyka sa jej
#   reach   natiahne sa a zdvihne maly predmet, skuma ho v ruke
SMALL = ("skull", "bones", "coin", "tablet", "gear", "machine", "map", "chest", "book")
ACT_DEFAULT = {"dig": "dig", "descend": "climb", "spot": "find", "scale_measure": "measure", "human_stack": "climb",
               "timeline_compare": "point", "exhibit": "point", "action_crowd": "carry", "wide_reveal": "watch"}


def action_for(shot, params, fact):
    low = (fact or "").lower()
    small = str(params.get("object", "")) in SMALL
    if shot == "wide_reveal" and _carries(low):
        return "carry"
    if shot == "spot":
        # lebku najde pod rukami, lod na mori len zbada a ukaze na nu
        return "find" if small else "point"
    if shot in ACT_DEFAULT:
        return ACT_DEFAULT[shot]
    if shot != "object_reveal":
        return ""                       # walk_in, theory, no_list, punch, loop_close: archetyp si to riesi sam
    if re.search(r"\b(visible|seen|see|shows?|showing|appears?|emerg\w+|reveal\w*|melts?|clear water)\b", low):
        return "watch"
    if re.search(FIND_RX, low):
        return "find" if small else "point"
    if re.search(r"\b(lift\w*|pull\w*|retriev\w+|recover\w*|picked|holds?|held)\b", low):
        return "reach"
    if re.search(r"\b(climb\w*|ascend\w*|summit|altitude|above sea level)\b", low):
        return "climb"
    return "reach" if small else "watch"


# dramaturgia: v akom poradi maju zabery ist, ked su k dispozicii
ORDER = ["walk_in", "dig", "descend", "spot", "object_reveal", "detail_compare", "scale_measure", "human_stack",
         "wide_reveal", "timeline_compare", "no_list", "action_crowd", "exhibit", "theory", "punch", "loop_close"]
MAXN = {"scale_measure": 2, "object_reveal": 3, "spot": 3, "action_crowd": 2, "theory": 2, "exhibit": 1,
        "wide_reveal": 2, "dig": 1, "descend": 1, "timeline_compare": 2, "no_list": 1, "human_stack": 1,
        "detail_compare": 1}


STORY_HI = (r"\b(oldest|first|earliest|largest|tallest|deepest|only|never|no one|nobody|unknown|unexplained|"
            r"mystery|myster\w+|deliberately|on purpose|buried|abandon\w+|vanish\w+|disappear\w+|missing|"
            r"killed|died|dead|discover\w+|found)\b")
STORY_LO = r"\b(research\w*|study|studies|analysis|published|journal|university|conservation|tourism|funding)\b"
LOGISTICS = r"\b(trek\w*|hike|hiking|season|route|itinerary|accessible|permit\w*|ticket\w*|visitors per|opening hours)\b"


def story_score(fact):
    """Kolko pribehu fakt nesie - aby sa do epizody dostali pointy, nie metodika vyskumu."""
    low = fact.lower()
    s = 0
    s += 2 * len(re.findall(STORY_HI, low))
    s -= 2 * len(re.findall(STORY_LO, low))
    if re.search(r"\b\d[\d,.]*\s*(m|ft|metres|meters|feet|tons?|cm|km)\b", low):
        s += 3
    if re.search(r"\b(1[0-9]{3}|20\d{2}|\d{3,4}\s*(bce|bc|ce|ad))\b", low):
        s += 2
    if re.search(r"\bno (metal|wheel|writing)\b", low):
        s += 4
    ys = sorted({int(y) for y in re.findall(r"\b(\d{3,4})\s*(?:bce|bc|ce|ad)\b", low)})
    if len(ys) >= 2 and ys[-1] - ys[0] >= 100:
        s += 3                      # dve obdobia v jednom fakte = casto jadro zahady (Roopkund: 800 vs 1800)
    return s


def plan(facts, world, hero, want=11, topic=""):
    """Z faktov vyskladaj 11-13 beatov v dramaturgickom poradi."""
    beats, used, seen, rest = [], {}, set(), []
    main_obj = find_object(topic, None) if topic else None       # „The Voynich manuscript" -> book
    era0 = topic_era(facts)
    # ten isty predmet s tym istym dejom dvakrat (spot „finds bones" + object_reveal „uncovers the remains")
    # je dvakrat ta ista scena - druhy fakt ide do zvysku
    seen_oa = set()

    def _oa(shot, params, f):
        return ((str(params.get("object", "")), action_for(shot, params, f))
                if shot in ("spot", "object_reveal") else None)

    facts = sorted(facts, key=story_score, reverse=True)     # najprv pointy, potom detaily
    for f in facts:
        got = classify(f, world, hero, main_obj, era0)
        if not got:
            rest.append(f)
            continue
        shot, params = got
        key = (shot, str(params.get("object", "")))
        oa = _oa(shot, params, f)
        if used.get(shot, 0) >= MAXN.get(shot, 2) or key in seen or (oa and oa in seen_oa):
            rest.append(f)
            continue
        used[shot] = used.get(shot, 0) + 1
        seen.add(key)
        if oa:
            seen_oa.add(oa)
        beats.append({"shot": shot, "params": params, "fact": f})
    # doplnenie na plnu dlzku: zvysne fakty s kresitelnym objektom striedavo spot / object_reveal
    for f in rest:
        if len(beats) >= want - 2:
            break
        o = find_object(f, None)
        if not o:
            continue
        # vypln nesmie byt metodika ani logistika („the trek takes five days", „genome-wide analysis"):
        # z takej vety vznikne zaber, kde postava len nieco drzi a nic sa nedeje
        if story_score(f) < 0 or re.search(LOGISTICS, f.lower()):
            continue
        # vynasanie patri davu (action_crowd ma strop) - ako object_reveal by to bol Bob s kostou v ruke
        if _carries(f.lower()):
            continue
        # spot = niekto nieco NASIEL; vlastnost objektu („jazero zamrza") patri do object_reveal
        disc = re.search(r"\b(found|discover\w*|spotted|noticed|uncover\w*|revealed)\b", f.lower())
        shot = "spot" if (disc and used.get("spot", 0) < 2) else "object_reveal"
        oa = _oa(shot, {"object": o}, f)
        if (shot, o) in seen or oa in seen_oa:
            continue
        used[shot] = used.get(shot, 0) + 1
        seen.add((shot, o))
        seen_oa.add(oa)
        beats.append({"shot": shot, "params": {"object": o}, "fact": f})
    # uvodny zaber: bud existujuci walk_in, alebo ho vyrob z prveho faktu s rokom
    if not any(b["shot"] == "walk_in" for b in beats):
        yf = next((f for f in facts if re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", f)), facts[0] if facts else "")
        beats.insert(0, {"shot": "walk_in", "fact": yf,
                         "params": {"object": find_object(yf, "mountain"),
                                    "year": (re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", yf) or [None])[0]
                                    if re.search(r"\b(1[5-9]\d{2}|20\d{2})\b", yf) else None}})
    beats.sort(key=lambda b: ORDER.index(b["shot"]) if b["shot"] in ORDER else 99)
    if len(beats) > want - 2:                      # co sa nezmesti: najprv vypadnu vypnove spot/object_reveal
        keep, extra = [], []
        for b in beats:
            (extra if b["shot"] in ("spot", "object_reveal") else keep).append(b)
        room = max(0, (want - 2) - len(keep))
        beats = sorted(keep + extra[:room],
                       key=lambda b: ORDER.index(b["shot"]) if b["shot"] in ORDER else 99)[:want - 2]
    # ten isty predmet zblizka dvakrat po sebe (lebka, lebka) vyzera ako jeden zaber pusteny dvakrat -
    # ostane silnejsi fakt, ak epizode ostane aspon 9 zaberov (vratane punch + loop_close)
    close, out = ("spot", "object_reveal"), []
    for i, b in enumerate(beats):
        dropped = i - len(out)
        if (out and b["shot"] in close and out[-1]["shot"] in close
                and b["params"].get("object") == out[-1]["params"].get("object")
                and len(beats) - dropped - 1 + 2 >= 9):
            if story_score(b["fact"]) > story_score(out[-1]["fact"]):
                out[-1] = b
            continue
        out.append(b)
    beats = out
    beats.append({"shot": "punch", "params": {"word": "UNEXPLAINED"},
                  "fact": "The case has never been explained."})
    beats.append({"shot": "loop_close", "params": {"question": ""}, "fact": "Open question for the viewer."})
    for b in beats:
        a = action_for(b["shot"], b["params"], b.get("fact", ""))
        if a:
            b["params"]["action"] = a
    return beats
