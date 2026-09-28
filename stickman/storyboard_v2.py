# -*- coding: utf-8 -*-
r"""Storyboard v2 pre stickman engine — OPACNE PORADIE: najprv zaber, potom veta.

Preco v2: v1 napisal lubovolny text a engine k nemu dodatocne hladal obrazok zo svojho slovnika.
User to zamietol na prvy pohlad („hovori o niecom a ukazuje uplne nieco ine"): „Crew belongings lie
undisturbed on deck" dostalo sud, „No sign of struggle" zvon. Schvalene Gobekli video vzniklo naopak —
najprv sme vymysleli zabery a text sa pisal k nim.

v2 preto dava modelu **katalog scen, ktore engine naozaj vie nakreslit**, a **zoznam 23 kresliteľnych
objektov**. Model sklada epizodu z tychto scen a az k nim pise vety. Co sa neda nakreslit, sa nepovie.

  python storyboard_v2.py "Roopkund" --show
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SPECS = os.path.join(ROOT, "specs")
os.makedirs(SPECS, exist_ok=True)
sys.path.insert(0, ROOT)
from storyboard import (wiki_extract, scene_world, _split_facts, check_facts, check_compare,  # noqa: E402
                        WPS, SPEED_BASE, TARGET_S, SYSTEM)
import storyboard as v1  # noqa: E402
import plan_beats  # noqa: E402

# ------------------------------------------------------------------ co engine vie nakreslit
# 23 objektov z props.py - NIC INE sa nakreslit neda. Ked scena pomenuje cokolvek mimo, obrazok klame.
OBJECTS = ["stone", "pillar", "mountain", "cave", "water", "ship", "wreck", "gear", "machine", "skull",
           "bones", "door", "chest", "ruin", "map", "statue", "tunnel", "tree", "forest", "car",
           "tablet", "tower", "coin", "meteor", "book", "fallen_tree",
           # predmety z pribehov (v3): bez nich engine kreslil posteľ ako knihu a plaste ako ozubene koleso
           "bed", "clock", "chair", "table", "meal", "lantern", "coat", "letter", "footprints", "rope", "boat",
           "candle", "bottle", "boot", "key", "radio", "ladder", "tent", "window", "fireplace", "crate", "crate_broken",
           "body", "wave", "lighthouse", "coat_hanging", "book_torn"]
REPEATABLE = ["stone", "pillar", "statue", "tower", "tree", "tablet", "coin", "skull", "fallen_tree"]
_SYN = {"bones": r"bone|skeleton|remains|bodies|victim", "skull": r"skull|bone|skeleton|bodies|victim|dead", "stone": r"stone|rock|slab|"
        r"boulder|megalith", "pillar": r"pillar|column|monolith|stela", "ruin": r"ruin|site|enclosure|"
        r"settlement|temple", "water": r"lake|water|sea|ice|pool|melt|frozen|glacial|thaw", "mountain": r"mountain|hill|peak|slope|plateau", "tablet": r"tablet|inscription|text|writing|record", "machine": r"machine|device|mechanism", "map": r"map|route|chart", "ship": r"ship|vessel|boat",
        "meteor": r"meteor|asteroid|comet|fireball|rock|explosion|blast",
        "book": r"book|manuscript|codex|page|vellum|script|\bcopy\b|volume|edition|rubaiyat|logbook|diary|journal",
        "chest": r"chest|box|crate|casket|coffer|trunk",
        "bed": r"bed|bunk", "clock": r"clock|time", "chair": r"chair|seat|stool", "table": r"table|desk",
        "meal": r"meal|food|dinner|breakfast|supper|lunch|plate|cup", "lantern": r"lamp|lantern|light",
        "coat": r"coat|oilskin|jacket|cloak", "letter": r"letter|note|message|log|entry|diary",
        "footprints": r"footprint|track|step|trail", "rope": r"rope|line|cable", "boat": r"boat|dinghy|raft",
        "candle": r"candle", "bottle": r"bottle|flask", "boot": r"boot|shoe", "key": r"key|lock",
        "radio": r"radio|transmitter|signal|wireless|telegraph", "ladder": r"ladder", "tent": r"tent|camp",
        "window": r"window", "fireplace": r"fire|hearth|stove",
        "door": r"door|gate|doorway|entrance|hatch", "tower": r"tower|lighthouse|spire|minaret",
        "crate": r"crate|box|supply|supplies", "crate_broken": r"crate|box|supply|supplies|wreckage|debris",
        "body": r"body|bodies|corpse|dead|victim|lifeless|\bman\b|\bwoman\b|\bmen\b",
        "wave": r"wave|waves|tsunami|swell|surge|breaker",
        "lighthouse": r"lighthouse|beacon|\blight\b|tower|lamp",
        "coat_hanging": r"coat|oilskin|jacket|cloak|pegs?|hooks?", "book_torn": r"book|page|copy|volume|manuscript",
        "fallen_tree": r"tree|forest|trunk|taiga"}   # pre wide_reveal
VS_DRAWABLE = ["pyramid", "trilith", "clock", "column", "ship"]                          # pre timeline_compare

# scena -> (co je v zabere, povinne parametre)
SCENES = {
    "walk_in":      ("the character walks through the landscape towards the place of the story",
                     {"object": "orientacny bod zo zoznamu", "year": "rok, zlate cislo (volitelne)"}),
    "insert":       ("a close-up of the object alone (no character) with a red mark and a short label",
                     {"object": "predmet zo zoznamu", "label": "1-3 slova z vety", "mark": "circle|cross|arrow|none",
                      "count": "rad rovnakych predmetov", "filled": "kolko z nich je pritomnych", "inside": "v miestnosti"}),
    "dig":          ("the character digs, the pit gets deeper and the object emerges", {"object": "co sa vynori"}),
    "descend":      ("the camera goes down a shaft, a ruler counts the metres",
                     {"value": "hlbka cislom", "unit": "m/ft"}),
    "scale_measure": ("the whole object with a red dimension line and a golden number counting up",
                      {"object": "meraný objekt", "value": "cislo", "unit": "jednotka", "axis": "v (vyska) / h (dlzka)"}),
    "human_stack":  ("three people stand on each other's shoulders next to the object, golden 1-2-3",
                     {"object": "objekt"}),
    "wide_reveal":  ("the camera flies up and reveals dozens of copies of the same object",
                     {"object": "opakovany predmet (len z REPEATABLE)", "count": "kolko ich je"}),
    "timeline_compare": ("a timeline from that date to today, a golden number of years counting up",
                         {"vs": "pyramid/trilith/clock/column/ship alebo vlastny napis", "years": "pocet rokov"}),
    "no_list":      ("three golden words crossed out in red over icons",
                     {"items": "presne tri: metal, wheel, writing"}),
    "action_crowd": ("a group of people of that era carries baskets (of soil, stones or bones) and empties them",
                     {"era": "ancient/historic/modern"}),
    "theory":       ("the character wonders, thought bubbles show the explanation people suggest",
                     {"bubble": "jedno slovo alebo objekt do bubliny"}),
    "object_reveal": ("the object up close, the character physically next to it doing the action "
                      "(looking into it, touching it, holding it up)", {"object": "objekt"}),
    "detail_compare": ("the object and a magnifying lens showing a close detail of it (strange script, marks)",
                       {"object": "predmet"}),
    "exhibit":      ("the object in a glass case in a museum, modern visitors around it",
                     {"object": "predmet", "label": "text na tabulke"}),
    "spot":         ("the character finds the object: kneels and uncovers a small one under his hands, "
                     "or spots a big one in the distance and points at it", {"object": "predmet, ktory najde"}),
    "loop_close":   ("the character shrugs, a golden question mark and the question land", {"question": "text otazky"}),
    "punch":        ("the character alone, the golden word UNEXPLAINED slams in", {"word": "zlate slovo"}),
}
_SYN["ship"] = _SYN.get("ship", "ship") + "|brigantine|schooner|vessel|barque|sloop|frigate|hull|steamer"  # Mary Celeste: brigantine
# scena -> svety, kde NEMA zmysel
BANNED = {"dig": ("sea", "shore"), "descend": ("sea", "shore"), "wide_reveal": ("sea",),
          "human_stack": ("sea",), "action_crowd": ("sea",)}

PROMPT = """Topic: {topic}

FACT SHEET (ground truth - every name, year and number you use must come from here):
{facts}
Do NOT state any of these as fact (disputed): {uncertain}

You are storyboarding a 30-second stick-figure cartoon. The animator can only draw the shots and the objects
listed below. Build the episode FROM THESE SHOTS, then write one narration sentence for each shot that says
exactly what the viewer sees. If a fact cannot be shown with these shots and objects, leave the fact out.

SHOTS (world of this episode: {world}, main character: {hero}; shots marked unavailable must not be used):
{scenes}

THE ONLY OBJECTS THAT CAN BE DRAWN - never name anything else in a shot:
{objects}
Repeatable objects (wide_reveal only): {repeatable}

RULES
- 11 to 13 shots. First shot is walk_in. Last shot is loop_close with an open question that invites comments.
- The second to last sentence closes the story ("And nobody knows why." style).
- 70-80 words TOTAL, each sentence 4 to 9 words, present tense, continuous story.
- The sentence is NARRATION THE VIEWER HEARS. It must be true of the picture, but it must sound like a story,
  not like a description of a drawing. NEVER mention the drawing itself: no "gauge", "arrow", "label",
  "highlighted", "red exclamation", "on screen", and never the word "Theory:" - just say what people think.
    GOOD: "He digs, and it keeps going down."        BAD: "Depth gauge drops three metres down."
    GOOD: "Some think a hailstorm killed them."      BAD: "Theory: sudden hailstorm caused deaths."
    GOOD: "In 1942, a ranger reaches a frozen lake." BAD: "In 1942 ranger arrives at icy mountain."
- The sentence may only name things from the drawable list. If it names anything else (mules, ropes, tents),
  that thing would not be on screen - rewrite the sentence without it.
- Write natural English with articles ("a ranger", "the lake"), not telegraph style.
- Use a year ONLY if the shot lists one in its parameters or the fact contains it. Never invent a year.
- Never the words "you", "your", "imagine", "subscribe". Never name the camera or the shot.
- Mark interpretations ("its discoverer believed", "some think").
- Use "theory" twice in a row when there are two competing explanations, each with its own bubble word.
- human_stack ONLY when the sentence compares the size of the object to people standing on each other.
- timeline_compare ONLY for a real age gap ("seven thousand years older than the pyramids"), never for two dates.
- Title: starts with "The", max 6 words, no numbers, no colon.

Return JSON:
{{"title": "The ...",
  "beats": [
    {{"shot": "walk_in", "params": {{"object": "mountain", "year": "1942"}},
      "say": "In 1942, a ranger climbs to a frozen lake."}},
    {{"shot": "scale_measure", "params": {{"object": "stone", "value": 5.5, "unit": "m", "axis": "v"}},
      "say": "The carved pillar stands five and a half metres."}},
    {{"shot": "loop_close", "params": {{"question": "What were they hiding it from?"}},
      "say": "What were they hiding it from?"}}
  ]}}"""


def catalogue(world):
    out = []
    for k, (what, params) in SCENES.items():
        if world in BANNED.get(k, ()):
            out.append(f"- {k}: UNAVAILABLE in this world")
            continue
        ps = "; ".join(f"{a} = {b}" for a, b in params.items())
        out.append(f"- {k}: {what}  [parametre: {ps}]")
    return "\n".join(out)


STYLE_LEAKS = (("no metal", r"\bmetal"), ("no wheel", r"\bwheel"), ("no writing", r"\bwriting"),
               ("stone tools", r"stone tools"), ("whole rings", r"\brings?\b|circular"),
               ("older than the pyramids", r"pyramid"), ("on purpose", r"deliberate|intentional|on purpose"),
               ("poking out", r"poking|protrud"), ("hiding it", r"\bhid"), ("southern turkey", r"turkey"))


# zvierata, dopravne prostriedky a nastroje, ktore engine nema - ked ich veta pomenuje, obraz klame
NOT_DRAWN = (r"\b(mules?|horses?|donkeys?|camels?|yaks?|dogs?|cats?|birds?|helicopters?|planes?|aircraft|trains?|"
             r"trucks?|cranes?|drones?|robots?|computers?|microscopes?)\b")


def check_beats(spec, world):
    """Kazdy zaber musi byt kresitelny: znama scena, povoleny objekt, vyplnene parametre."""
    p, beats = [], spec.get("lines", [])
    if not (9 <= len(beats) <= 13):
        p.append(f"pocet zaberov {len(beats)} (chcem 9-13)")
    for i, b in enumerate(beats, 1):
        sh, pr = b.get("shot"), b.get("params") or {}
        if sh not in SCENES and sh != "punch":
            p.append(f"zaber {i}: neznama scena '{sh}'")
            continue
        if sh == "punch":
            if not re.search(r"\bunexplained\b", b.get("say", ""), re.I):
                p.append(f"zaber {i} (punch): veta musi obsahovat slovo 'unexplained', to slovo sa ukaze na obraze")
            continue
        if world in BANNED.get(sh, ()):
            p.append(f"zaber {i}: '{sh}' sa vo svete {world} neda nakreslit")
        obj = str(pr.get("object", "")).lower().strip()
        if "object" in SCENES[sh][1] and obj not in OBJECTS:
            p.append(f"zaber {i} ({sh}): objekt '{obj or '-'}' nie je kresitelny, vyber zo zoznamu")
        if sh == "wide_reveal" and obj not in REPEATABLE:
            p.append(f"zaber {i}: wide_reveal vie opakovat len {', '.join(REPEATABLE)}")
        if sh == "scale_measure" and not (pr.get("value") and pr.get("unit")):
            p.append(f"zaber {i}: scale_measure potrebuje value + unit")
        if sh == "theory" and not pr.get("bubble"):
            p.append(f"zaber {i}: theory potrebuje slovo do bubliny")
        prev_obj = str(((beats[i - 2].get("params") or {}).get("object") if i > 1 else "") or "").lower()
        # hlavny predmet epizody (najcastejsi) moze veta pomenovat aj zamenom „it" (Voynich: „Yale displays it")
        objs = [str((x.get("params") or {}).get("object") or "").lower() for x in beats]
        main = max(set(o for o in objs if o), key=objs.count) if any(objs) else ""
        if obj and sh != "walk_in":                    # uvodna chodza je krajina, predmet nemusi pomenovat
            say_l = b.get("say", "")
            stem = obj.rstrip("s")
            named = re.search(stem[:5] if len(stem) > 5 else stem, say_l, re.I) or \
                re.search(_SYN.get(obj, "(?!x)x"), say_l, re.I) or \
                (obj == prev_obj and re.match(r"(it|its|they|their|this|these)\b", say_l.strip(), re.I)) or \
                (obj == prev_obj and re.match(r"(some|others|the rest|the others|(two|three|four|five|six|seven|eight|"
                                              r"nine|ten|\d+) (more|others|of them))\b", say_l.strip(), re.I)) or \
                (obj == main and re.search(r"\b(it|its)\b", say_l, re.I))
            if not named:
                p.append(f"zaber {i} kresli '{obj}', ale veta ho nepomenuje: '{say_l[:42]}'")
        n = len(b.get("say", "").split())
        if n > 11 or n < 3:
            p.append(f"zaber {i} ma {n} slov: {b.get('say', '')[:40]}")
        say = b.get("say", "")
        if re.search(r"\b(gauge|arrow|label|highlight\w*|exclamation|caption|on screen|shown|depicted|"
                     r"theory:|image|frame|camera|shots? \d+|picture|shows the)\b", say, re.I):
            p.append(f"zaber {i} popisuje kresbu, nie dej: '{say[:45]}' - prepis na vetu, ktoru divak POCUJE")
        if re.match(r"^(in \d{4}\s+)?[a-z]*\s*(ranger|archaeologist|diver|sailor|scientist)\b", say.lower()) \
                and not re.search(r"\b(a|an|the)\s+(ranger|archaeologist|diver|sailor|scientist)\b", say.lower()):
            p.append(f"zaber {i}: chyba clen pred postavou ('a ranger'), veta znie telegraficky")
    if beats:
        if beats[0].get("shot") != "walk_in":
            p.append("prvy zaber musi byt walk_in")
        if beats[-1].get("shot") != "loop_close":
            p.append("posledny zaber musi byt loop_close s otazkou")
        elif not beats[-1].get("say", "").rstrip().endswith("?"):
            p.append("posledna veta musi byt otazka do komentarov")
        else:
            # „Who caused the deadly hailstorm?" berie legendu ako fakt - otazka ma mierit na zahadu, nie na teoriu
            q = beats[-1].get("say", "").lower()
            for b in beats:
                bw = str((b.get("params") or {}).get("bubble") or "").lower()
                if b.get("shot") == "theory" and len(bw) > 3 and bw in q:
                    p.append(f"zaverecna otazka stavia na teorii '{bw}' ako na fakte - opytaj sa na samotnu zahadu")
    facts_low = " ".join(spec.get("facts", [])).lower()
    for i, b in enumerate(beats, 1):
        say_l = b.get("say", "").lower()
        m_nd = re.search(NOT_DRAWN, say_l)
        if m_nd:
            p.append(f"zaber {i}: '{m_nd.group(0)}' sa neda nakreslit - veta to nesmie pomenovat")
        if re.search(r"\b(i|we|my|our|me)\b", say_l):
            p.append(f"zaber {i}: prva osoba ('{b.get('say', '')[:40]}') - rozpravac je v tretej osobe")
        # vzorova epizoda (Göbekli) nesmie presiaknut do inej temy
        for phrase, need in STYLE_LEAKS:
            if phrase in say_l and not re.search(need, facts_low):
                p.append(f"zaber {i}: '{phrase}' je zo vzorovej epizody, fakty to nehovoria - prepis")
    he = sum(1 for b in beats if re.match(r"he\b", b.get("say", "").strip().lower()))
    if he > 2:
        p.append(f"{he} viet zacina 'He' - to je opis pohybov postavy, nie pribeh; rozpravaj fakty, "
                 f"pohyb ukaze obraz")
    for i, b in enumerate(beats, 1):
        if b.get("shot") == "action_crowd" and re.match(r"(he|she)\b", b.get("say", "").strip().lower()):
            p.append(f"zaber {i}: action_crowd je skupina ludi - podmet musi byt skupina z faktu, nie 'he'")
        if b.get("shot") == "action_crowd" and re.search(r"\bbaskets?\b", b.get("say", ""), re.I) \
                and not re.search(r"\bbaskets?\b", b.get("fact", ""), re.I):
            p.append(f"zaber {i}: kose su len kresba - povedz, co podla faktu odnasali")
        if re.search(r"\bhe (reaches|watches|points|measures|looks at)\b", b.get("say", ""), re.I):
            p.append(f"zaber {i}: veta opisuje pohyb postavy ('{b.get('say', '')[:40]}') - povedz fakt")
    w = sum(len(b.get("say", "").split()) for b in beats)
    if not (58 <= w <= 84):
        p.append(f"slov {w} (chcem 62-80 = 26-33 s)")
    return p


_NUM1 = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                    "fourteen fifteen sixteen seventeen eighteen nineteen".split())}
_NUM10 = {w: 10 * (i + 2) for i, w in enumerate("twenty thirty forty fifty sixty seventy eighty ninety".split())}


def _numbers(text):
    """Vsetky cisla vo vete - cislicami aj slovami („twenty-four", „eight hundred", „5,020")."""
    # vsetky pomlcky (aj nedelitelna U+2011 z LLM) na medzeru, inak „twenty‑three" nie je 23
    low = re.sub(r"[‐-―−-]", " ", (text or "").lower())
    out = {float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", low) if x.replace(",", "")}
    # „twenty three point five" = 23.5 (predtym 23 a 5 -> falosna chyba „cislo nie je vo fakte")
    for m in list(re.finditer(r"([a-z]+(?:\s[a-z]+)?)\s+point\s+([a-z]+)", low)):
        whole = sorted(_numbers(m.group(1)))
        frac = _NUM1.get(m.group(2))
        if whole and frac is not None and frac < 10:
            out.add(whole[-1] + frac / 10.0)
            low = low.replace(m.group(0), " ")
    total, cur, inside, prev = 0, 0, False, ""
    for w in re.findall(r"[a-z]+", low) + ["."]:
        if w in ("hundred", "thousand") and not inside and prev == "a":      # „a thousand years"
            cur, inside = 1, True
        prev = w
        if w in _NUM1 or w in _NUM10:
            cur += _NUM1.get(w, _NUM10.get(w, 0))
            inside = True
        elif w == "hundred" and inside:
            cur = max(1, cur) * 100
        elif w in ("thousand", "million") and inside:
            total += max(1, cur) * (1000 if w == "thousand" else 1000000)
            cur = 0
        elif w == "and" and inside:
            continue
        else:
            if inside:
                out.add(float(total + cur))
            total, cur, inside = 0, 0, False
    return out


def check_numbers(spec):
    """Kazde cislo vo vete musi byt vo fakte daneho zaberu (alebo v zlatom cisle).
    Model inak z „23 individuals" urobi „twenty-four bodies" a check_facts to nevidi, lebo je to slovom."""
    p = []
    # rok z ineho faktu je v poriadku (uvodna veta si berie rok objavu), ine cislo nie
    years = {n for f in spec.get("facts", []) for n in _numbers(f) if 1000 <= n <= 2100}
    for i, l in enumerate(spec.get("lines", []), 1):
        fact = l.get("fact")
        if not fact:
            continue
        ok = _numbers(fact) | years
        g = l.get("gold") or {}
        for k in ("count", "text"):
            try:
                ok.add(float(str(g.get(k)).replace(",", "")))
            except (TypeError, ValueError):
                pass
        said = _numbers(l.get("say", ""))
        bad = sorted(n for n in said if n not in ok and n != 1)
        if bad:
            p.append(f"zaber {i}: cislo {', '.join(f'{b:g}' for b in bad)} nie je vo fakte zaberu - "
                     f"pouzi presne cislo z faktu alebo ziadne")
        # zlate cislo na obraze musi zaznit aj v hlase, inak obraz ukazuje nieco ine, nez sa hovori
        gnum = None
        for k in ("count", "text"):
            try:
                gnum = float(str(g.get(k)).replace(",", ""))
                break
            except (TypeError, ValueError):
                continue
        if gnum is not None and l.get("shot") != "walk_in" and gnum not in said:
            p.append(f"zaber {i}: na obraze sa ukaze zlate {gnum:g}, ale veta to cislo nepovie - povedz ho")
    return p


WRITE_PROMPT = """Topic: {topic}

A stick-figure cartoon is already storyboarded. Each shot below is FIXED: the picture is decided, and the fact it
illustrates comes from Wikipedia. Your only job is to write the narration sentence the viewer HEARS over each shot.

STYLE REFERENCE - the approved episode about a DIFFERENT place. Copy only its rhythm and voice (short, concrete,
spoken, each line raising the stakes). NEVER reuse its facts, numbers or phrases:
  "In 1994, an archaeologist climbs a hill in southern Turkey and sees a stone poking out of the dirt. He digs.
   It keeps going down. It's a carved pillar, five and a half metres tall. And it's not alone. There are whole
   rings of them. Then they buried all of it. On purpose. And nobody knows why. What were they hiding it from?"

HARD RULES
- One sentence per shot, 3 to 11 words, present tense, natural English with articles. Short punches are welcome.
- Third person storyteller. Never "I", "we", "my", "our".
- Write it like a storyteller talking to a friend, not like a caption. The first sentence gives the year,
  the person and what they do ("In 1994, an archaeologist climbs a hill in southern Turkey").
  The middle sentences raise the stakes. Concrete nouns and verbs, no filler adjectives.
- The sentence must be true of BOTH the fact and the picture, and must flow from the previous sentence
  (and / but / so / then). Together they must read as one continuous story, not a list.
- Use ONLY what the fact says. Never add a name, year, number or comparison that is not in the fact.
- When a shot lists a number (value, count, years), the sentence MUST say exactly that number (words or digits):
  it appears on screen in gold. years=1000 between two dates -> "...a thousand years apart".
- Never describe the drawing itself (no "gauge", "arrow", "label", "highlighted", "on screen", "Theory:").
- "action" is a note for the ANIMATOR (what the character does in the picture). Do NOT narrate it:
  never write "he reaches", "he watches", "he points", "he measures". Tell the story of the FACT instead;
  the picture already shows the movement. The sentence only must not contradict the picture.
    GOOD (action=watch): "Every summer, the ice melts and the skeletons appear."
    BAD  (action=watch): "He watches the skeletons in the water."
- Shot "action_crowd" shows a GROUP of people: its subject is the group from the fact ("a team", "tourists",
  "workers"), never "he". The baskets are only how it is drawn - say what the fact says they moved.
    GOOD: "In 2003, a team hauls out thirty skeletons."   BAD: "A team lifts thirty bone-filled baskets."
- At most two sentences in the whole episode may start with "He".
- The sentence may only name things the animator can draw: the object of the shot, the character, and the landscape. Never name an animal, a vehicle, a tool or a piece of clothing that is not the shot object (no mules, horses, ropes, tents, helicopters).
- Use a year ONLY if the shot lists one in its parameters or the fact contains it. Never invent a year.
- Never the words "you", "your", "imagine", "subscribe".
- Vary the openings: at most three sentences in the whole episode may start with "And", "So" or "Then".
- Mark interpretation as interpretation ("some think", "its discoverer believed").
- Shot "punch" = the line that closes the story, 4 to 8 words, and it MUST contain the word "unexplained"
  (the word slams onto the screen in gold), e.g. "To this day, it remains unexplained."
- Shot "loop_close" = an open question, 4 to 9 words, that makes people comment. It is the last sentence.
  It asks about the central unknown of the whole story (who, why, what really happened) - never about a detail,
  and never treats a legend as fact. Example for a different story (a ship found empty): "So where did the crew go?"
- Total across all sentences: 70-80 words.
- Title: starts with "The", max 6 words, no numbers, no colon.

SHOTS (in order) - "picture" is what is drawn, "fact" is the source of truth:
{beats}

Return JSON: {{"title": "The ...", "say": ["sentence for shot 1", "sentence for shot 2", ...]}}
Exactly {n} sentences, in the same order as the shots."""


def _beats_txt(beats):
    out = []
    for i, b in enumerate(beats, 1):
        what = SCENES.get(b["shot"], ("", {}))[0]
        pr = ", ".join(f"{k}={v}" for k, v in (b.get("params") or {}).items() if v not in (None, ""))
        out.append(f"{i}. [{b['shot']}] picture: {what}" + (f" ({pr})" if pr else "") +
                   f"\n   fact: {b.get('fact', '')}")
    return "\n".join(out)


def _llm_write(prompt, effort="medium", temperature=0.6, max_tokens=4000):
    """Pisanie viet: gpt-oss s reasoning 'low' pise telegraficky („Water spans forty meters, three deep clear"),
    'medium' si vetu najprv poskladá. Bez json_object rezimu - ten na Groqu casto pada na json_validate_failed;
    JSON vytiahneme z textu sami. Ked vsetko zlyha, spadne na spolocne llm_json."""
    import time
    import requests
    cm = v1.common
    for att in range(6):
        try:
            r = requests.post(cm.BASE.rstrip("/") + "/chat/completions",
                              headers={"Authorization": f"Bearer {cm.TOKEN}", "Content-Type": "application/json"},
                              json={"model": cm.MODEL, "temperature": temperature, "max_tokens": max_tokens,
                                    "reasoning_effort": effort,
                                    "messages": [{"role": "system", "content": SYSTEM},
                                                 {"role": "user", "content": prompt}]},
                              timeout=180)
            if r.status_code == 429:
                if "per day" in r.text or "TPD" in r.text:
                    break
                try:
                    wait = min(60.0, float(r.headers.get("retry-after", 8)) + 2)
                except ValueError:
                    wait = 10.0
                time.sleep(wait)
                continue
            r.raise_for_status()
            txt = (r.json()["choices"][0]["message"].get("content") or "").strip()
            if txt:
                return cm._extract_json(txt)
        except Exception as ex:
            print(f"  [write] pokus {att + 1}: {str(ex)[:80]}", flush=True)
            time.sleep(3)
    return cm.llm_json(prompt, SYSTEM, temperature=0.5, max_tokens=1400) or {}


def generate(topic, tries=4):
    """v3: zabery vyberie plan_beats z FAKTOV, LLM uz len pise vety k hotovym zaberom."""
    # fact sheet sa uklada: kazdy novy vytah z Wikipedie rozdeli fakty inak (raz jeden geneticky fakt s dvoma
    # datumami, inokedy tri samostatne) a z toho isteho tematu vyjde zakazdym iny pribeh
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    fcache = os.path.join(SPECS, "_facts", slug + ".json")
    if os.path.exists(fcache) and not os.environ.get("SB_REFRESH"):
        facts = json.load(open(fcache, encoding="utf-8"))
        print(f"  fact sheet z cache ({len(facts)} faktov)", flush=True)
    else:
        print("  wikipedia...", flush=True)
        wtitle, extract = wiki_extract(topic)
        print(f"  podklad: {wtitle or 'NENASIEL'} ({len(extract)} znakov)", flush=True)
        raw = v1.common.llm_json(v1.FACTS_PROMPT.format(topic=topic, wtitle=wtitle or "-",
                                                        extract=extract or "(clanok sa nenasiel)"),
                                 SYSTEM, temperature=0.2, max_tokens=1200) or {}
        facts = _split_facts(raw.get("facts", raw))
        if facts:
            os.makedirs(os.path.dirname(fcache), exist_ok=True)
            json.dump(facts, open(fcache, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    world, hero = scene_world(topic, facts, [])
    beats = plan_beats.plan(facts, world, hero, topic=topic)
    print(f"  fact sheet: {len(facts)} faktov -> {len(beats)} zaberov ({world}/{hero}): "
          f"{', '.join(b['shot'] for b in beats)}", flush=True)
    if len(beats) < 9:
        # z tychto faktov sa neda nakreslit epizoda (Oak Island dal geologiu a podnebie) - ani nevolame LLM,
        # fabrika temu preskoci a zoberie dalsiu (kod 3)
        print(f"  !! len {len(beats)} kreslitelnych zaberov - tema sa preskakuje", flush=True)
        raise SystemExit(3)
    prompt = WRITE_PROMPT.format(topic=topic, beats=_beats_txt(beats), n=len(beats))

    def assemble(says, title):
        spec = {"title": title, "topic": topic, "facts": facts, "world": world, "hero": hero,
                "lines": [{"say": s, "shot": b["shot"], "params": dict(b["params"]),
                           "fact": b.get("fact", "")} for s, b in zip(says, beats)]}
        if spec["lines"] and spec["lines"][-1]["shot"] == "loop_close":
            spec["lines"][-1]["params"]["question"] = spec["lines"][-1]["say"]
        _derive(spec)
        for _l in spec["lines"]:
            if _l["shot"] == "punch":
                _l.setdefault("params", {})
        return spec

    best, last, says, title = None, None, None, ""
    for attempt in range(1, tries + 1):
        # ked su chyby len v niekolkych vetach, prepisu sa IBA tie - cely prepis zakazdym opravil jednu
        # chybu a spravil novu inde (pokus 1: chyba v 6, pokus 2: v 1, pokus 3: v 10)
        idx = _flagged(last, says) if (says and last) else None
        try:
            if idx:
                out = _llm_write(REPAIR_PROMPT.format(
                    topic=topic, numbered="\n".join(f"{i}. {s}" for i, s in enumerate(says, 1)),
                    beats="\n".join(ln for i, ln in enumerate(_beats_txt(beats).split("\n")) if i // 2 in idx),
                    fix_list=", ".join(str(i + 1) for i in sorted(idx)),
                    problems="\n".join(f"- {x}" for x in last))) or {}
                fix = out.get("fix") or {}
                new = list(says)
                for k, v in (fix.items() if isinstance(fix, dict) else []):
                    try:
                        i = int(str(k).strip().rstrip(".")) - 1
                    except ValueError:
                        continue
                    if i in idx and isinstance(v, str) and v.strip():
                        new[i] = v.strip()
                print(f"  pokus {attempt}: cielena oprava viet {sorted(i + 1 for i in idx)}", flush=True)
                says = new
            else:
                out = _llm_write(prompt if attempt == 1 else prompt + v1.FIX.format(problems="; ".join(last))) or {}
                raw_say = out.get("say", [])
                # ciste pole viet ber tak, ako prislo: _split_facts zahadzuje kratke kusy (<13 znakov),
                # takze punch „UNEXPLAINED" zmizol a pocet viet nikdy nesedel
                if isinstance(raw_say, list) and all(isinstance(s, str) for s in raw_say):
                    new = [s.strip() for s in raw_say if s and s.strip()]
                else:
                    new = [s.strip() for s in _split_facts(raw_say) if s.strip()]
                if len(new) != len(beats):
                    print(f"  pokus {attempt}: {len(new)} viet na {len(beats)} zaberov", flush=True)
                    if len(new) < len(beats):
                        last = [f"vratil si {len(new)} viet, ale zaberov je {len(beats)} - jedna veta na kazdy zaber"]
                        says = None
                        continue
                    new = new[:len(beats)]
                says, title = new, out.get("title", "") or title
        except Exception as ex:
            print(f"  pokus {attempt}: LLM zlyhalo ({str(ex)[:60]})", flush=True)
            last = last or ["skus to este raz, drz sa formatu"]
            continue
        spec = assemble(says, title)
        last = check_beats(spec, world) + check_facts(spec) + check_compare(spec) + check_numbers(spec)
        print(f"  pokus {attempt}: {len(spec['lines'])} zaberov, "
              f"{sum(len(l['say'].split()) for l in spec['lines'])} slov, "
              f"{'OK' if not last else 'problemy: ' + '; '.join(last[:4])}", flush=True)
        if not last:
            return spec, []
        if best is None or len(last) < len(best[1]):
            best = (spec, last)
    if best:
        return best
    raise SystemExit("LLM nevratil pouzitelny storyboard")


REPAIR_PROMPT = """Topic: {topic}

You wrote the narration for a stick-figure cartoon. A checker found problems in some sentences.
Rewrite ONLY sentences {fix_list}. Keep them flowing with the sentences around them.

ALL SENTENCES NOW (context):
{numbered}

THE SHOTS TO FIX (picture and fact are the source of truth):
{beats}

PROBLEMS FOUND:
{problems}

Same rules as before: 3 to 11 words, present tense, third person storyteller, natural English with articles,
only what the fact says, say the shot's number if it lists one, never narrate the character's movement,
never name anything that cannot be drawn.
Return JSON: {{"fix": {{"<sentence number>": "new sentence"}}}}"""


def _flagged(problems, says):
    """Indexy viet, ktorych sa chyby tykaju. None = chyba je globalna (dlzka, pocet viet) -> cely prepis."""
    idx = set()
    for p in problems or []:
        m = re.match(r"zaber (\d+)", p)
        if m:
            idx.add(int(m.group(1)) - 1)
            continue
        m = re.search(r"(?:meno|rok/cislo) '?([^' ]+)'? nie je", p)
        if m:
            hit = [i for i, s in enumerate(says) if m.group(1).lower() in s.lower()]
            if not hit:
                return None
            idx.update(hit)
            continue
        if p.startswith(("zaverecna otazka", "posledna veta")):
            idx.add(len(says) - 1)
            continue
        m = re.match(r"(\d+) viet zacina 'He'", p)
        if m:
            he = [i for i, s in enumerate(says) if re.match(r"he\b", s.strip().lower())]
            idx.update(he[2:] or he)
            continue
        return None
    return idx if idx and len(idx) <= max(2, len(says) // 2) else None


def _generate_v2_single_call(topic, tries=3):
    print("  wikipedia...", flush=True)
    wtitle, extract = wiki_extract(topic)
    print(f"  podklad: {wtitle or 'NENASIEL'} ({len(extract)} znakov)", flush=True)
    raw = v1.common.llm_json(v1.FACTS_PROMPT.format(topic=topic, wtitle=wtitle or "-",
                                                    extract=extract or "(clanok sa nenasiel)"),
                             SYSTEM, temperature=0.2, max_tokens=1200) or {}
    facts = _split_facts(raw.get("facts", raw))
    unc = _split_facts(raw.get("uncertain", []))
    print(f"  fact sheet: {len(facts)} faktov", flush=True)
    world, hero = scene_world(topic, facts, [])
    prompt = PROMPT.format(topic=topic, facts="\n".join(f"- {f}" for f in facts) or "- (bez podkladu)",
                           uncertain="; ".join(unc) or "(nic)", world=world, hero=hero,
                           scenes=catalogue(world), objects=", ".join(OBJECTS),
                           repeatable=", ".join(REPEATABLE))
    best, last = None, None
    for attempt in range(1, tries + 1):
        try:
            out = v1.common.llm_json(prompt if attempt == 1 else prompt + v1.FIX.format(problems="; ".join(last)),
                                     SYSTEM, temperature=0.5, max_tokens=2000) or {}
        except Exception as ex:
            print(f"  pokus {attempt}: LLM zlyhalo ({str(ex)[:60]})", flush=True)
            last = last or ["skus to este raz, drz sa formatu"]
            continue
        beats = out.get("beats") or []
        if not beats:
            continue
        spec = {"title": out.get("title", ""), "topic": topic, "facts": facts, "world": world, "hero": hero,
                "lines": [{"say": (b.get("say") or "").strip(), "shot": b.get("shot"),
                           "params": b.get("params") or {}} for b in beats if b.get("say")]}
        _derive(spec)
        for _l in spec["lines"]:
            if _l["shot"] == "punch":
                _l.setdefault("params", {})
        last = check_beats(spec, world) + check_facts(spec) + check_compare(spec)
        print(f"  pokus {attempt}: {len(spec['lines'])} zaberov, "
              f"{sum(len(l['say'].split()) for l in spec['lines'])} slov, "
              f"{'OK' if not last else 'problemy: ' + '; '.join(last[:4])}", flush=True)
        if not last:
            return spec, []
        if best is None or len(last) < len(best[1]):
            best = (spec, last)
    if best:
        return best
    raise SystemExit("LLM nevratil pouzitelny storyboard")


def _derive(spec):
    """Z parametrov doplni to, co engine cita (gold, cue, era, bubble, vs) - aby bol spec kompatibilny s v1."""
    words = sum(len(l["say"].split()) for l in spec["lines"])
    spec["speed"] = round(max(SPEED_BASE, SPEED_BASE * words / (WPS * TARGET_S)), 2)
    for l in spec["lines"]:
        pr, sh, low = l.get("params") or {}, l["shot"], l["say"].lower()
        if sh == "scale_measure" and pr.get("value"):
            l["gold"] = {"count": float(pr["value"]), "unit": pr.get("unit", "m"), "axis": pr.get("axis", "v")}
        elif sh == "walk_in" and pr.get("year"):
            l["gold"] = {"text": str(pr["year"])}
        elif sh in ("wide_reveal", "action_crowd") and pr.get("count"):
            l["gold"] = {"text": str(pr.get("count_label") or pr["count"])}
        elif sh == "timeline_compare" and pr.get("years"):
            l["gold"] = {"count": int(str(pr["years"]).replace(",", "").split()[0]), "unit": "YEARS"}
        elif sh == "no_list":
            l["gold"] = {"items": ["NO METAL", "NO WHEEL", "NO WRITING"]}
        if sh == "timeline_compare" and pr.get("vs"):
            l["vs"] = str(pr["vs"]).lower()
        if sh == "theory" and pr.get("bubble"):
            l["bubble"] = str(pr["bubble"]).lower()
        # cue = slovo vo vete, na ktorom sa ma prvok objavit
        g = l.get("gold") or {}
        target = str(g.get("text") or g.get("count") or pr.get("object") or "")
        toks = [w.strip(".,!?;:'\"") for w in l["say"].split()]
        hit = next((w for w in toks if w.lower().replace(",", "") == target.lower().replace(",", "")), None)
        l["cue"] = hit or (toks[len(toks) // 2] if toks else "")
        # era: ber aj z vety, nielen z faktu (turisti/vedci vo vete = sucasnost, nie pravek)
        if re.search(r"\b(tourists?|visitors?|researchers?|scientists?|museum|today|modern)\b", low):
            l["era"] = "modern"
        elif pr.get("era"):
            l["era"] = pr["era"]
        else:
            yr = re.search(r"\b(1[7-9]\d{2}|20\d{2})\b", low)
            l["era"] = (("modern" if re.match(r"19[5-9]|20", yr.group(1)) else "historic") if yr
                        else ("modern" if sh == "exhibit" else "ancient"))
        if sh == "punch" and pr.get("word"):
            l["gold"] = {"text": str(pr["word"]).upper()}
            l["cue"] = ""


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    topic = " ".join(args)
    spec, problems = generate(topic)
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    out = os.path.join(SPECS, slug + ".json")
    json.dump(spec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n{spec.get('title')}  ({spec['world']}/{spec['hero']}, speed {spec['speed']})  ->  {out}")
    if "--show" in sys.argv:
        for i, l in enumerate(spec["lines"], 1):
            pr = " ".join(f"{k}={v}" for k, v in (l.get("params") or {}).items())
            print(f" {i:2}. [{l['shot']:15}] {l['say']}\n      {pr}")
    if problems:
        print("PROBLEMY:", "; ".join(problems))
        sys.exit(2)
