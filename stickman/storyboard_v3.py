# -*- coding: utf-8 -*-
r"""Storyboard v3 — NAJPRV PRIBEH, POTOM ZABERY.

Preco: v2 skladal epizodu z „nakreslitelnych" faktov (fakt -> zaber -> jedna veta). User 26.9. vsetky ukazky zamietol:
„povedia random 4 fakty, ktore spolu nesuvisia, ziaden pribeh… opakuju sa tie iste sceny". Schvalene videa (Göbekli,
Roopkund) mali skutocny pribeh: hacik -> objav -> stupnovanie -> zvrat -> otazka.

v3:
  1. silny free model (OpenRouter, Nemotron Ultra 550B) dostane CELY clanok z Wikipedie a napise 30 s pribeh;
     ku kazdej vete vyberie jeden zaber z katalogu enginu a popise, co je vidiet,
  2. kritik (ten isty model) pribeh obodujе (hacik, nadvaznost, obraz = veta, zrozumitelnost) — slaby pribeh sa pise znova,
  3. cisla a mena sa kontroluju proti clanku, zabery proti katalogu, opakovanie scen proti poslednym epizodam.

  python storyboard_v3.py "The Flannan Isles lighthouse" --show
Kluc: OPENROUTER_API_KEY z prostredia alebo ~/.config/watch/.env (nikdy sa nevypisuje). Zaloha: Groq (storyboard_v2).
"""
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
SPECS = os.path.join(ROOT, "specs")
HISTORY = os.path.join(SPECS, "_history.json")
sys.path.insert(0, ROOT)
import storyboard as v1  # noqa: E402
import storyboard_v2 as v2  # noqa: E402

OR_URL = "https://openrouter.ai/api/v1/chat/completions"
OR_MODELS = ["nvidia/nemotron-3-ultra-550b-a55b:free", "google/gemma-4-31b-it:free", "qwen/qwen3.8-27b:free"]
# HiddenEarth: 5 nove miesta (places.py) su pre kazdy kanal - stara ColdCase obsadenie ich moze
# dostat od modelu ako hociktore ine miesto. HEROES (kip/ott/mara) su naopak LEN pre kanal
# "unexplained" (UnexplainedDaily) - stary kanal ostava presne pri povodnej sedmicke.
CHANNEL = os.environ.get("STICKMAN_CHANNEL", "coldcase")
# partia pre Unexplained: v prompte ide ROLA, nie meno (model inak pise "Kip walks..." a kontrola faktov to zrazi)
HERO_ROLE = {"kip": "a small explorer with a huge backpack and a cap",
             "ott": "a tall thin geographer with round glasses and a satchel",
             "mara": "an explorer with a ponytail, a headband and a map tube"}
WORLDS = ["hill", "shore", "sea", "snow", "desert", "cave", "forest", "city", "library",
          "island", "canyon", "jungle", "geyser", "arctic"]
HEROES = ["kip", "ott", "mara"] if CHANNEL == "unexplained" else \
    ["archaeologist", "diver", "ranger", "scientist", "sailor", "detective", "caver"]
# rotacia obsadenia (len kanal "unexplained"): work/cast_history.json v enginu, ale v repo kopii
# (priecinok "stickman", nie "_engine") stickman/cast_history.json - MIMO stickman/work/, lebo ten
# je v .gitignore a krok "persist" v stickman-unexplained.yml musi vediet subor commitnut.
CAST_HISTORY = os.path.join(ROOT, "cast_history.json") if os.path.basename(ROOT) != "_engine" \
    else os.path.join(ROOT, "work", "cast_history.json")

# co engine naozaj vie nakreslit - model si vybera IBA z tohto
CATALOG = {
    "walk_in": ("the main character walks through the landscape towards the place of the story",
                "object (a landmark from OBJECTS), year (optional, shown in gold)"),
    "spot": ("the character finds something: kneels and uncovers a small object, or spots a big one and points",
             "object, action (find | point), inside (true when it happens in a room)"),
    "dig": ("the character digs, the pit deepens and the object emerges from the ground", "object"),
    "descend": ("the character climbs down a shaft or dives, a ruler counts the depth - only for the character's "
                "own descent, never for victims or bodies", "value, unit (m | ft)"),
    "object_reveal": ("the object close up, the character next to it reacting (looks into it, touches it, holds it up)",
                      "object, action (watch | reach | climb | find), inside (true when it happens in a room)"),
    "detail_compare": ("a magnifying lens shows a close detail of the object (marks, strange writing, damage)",
                       "object, inside (true when it happens in a room)"),
    "insert": ("a close-up of the object ALONE, no character - the exact thing the viewer should picture: a stopped "
               "clock, a torn page, one coat on three pegs with the empty pegs circled, the words on a note",
               "object, label (1-3 words shown in red, taken from the sentence), mark (circle | cross | arrow | none), "
               "count and filled (a row of the same object: three pegs with one coat = count 3, filled 1), "
               "inside (true when it happens in a room)"),
    "scale_measure": ("the object with a red measuring line and a golden number counting up",
                      "object, value (number from the article), unit (m | cm | km | ft | t), axis (v = height | h = length)"),
    "human_stack": ("people standing on each other's shoulders next to a tall object to show its height", "object"),
    "wide_reveal": ("the camera rises and reveals dozens of copies of one object across the land",
                    "object (stone | pillar | statue | tower | tree | tablet | coin | skull | fallen_tree), count"),
    "timeline_compare": ("date signposts on the ground and a golden number of years",
                         "vs (a date like '1404 AD' or '9500 BCE'), vs2 (optional second date), years (optional)"),
    "action_crowd": ("a group of people of that era works: carries loads away, fills or builds something",
                     "era (ancient | historic | modern), cargo (soil | stone | bones | water), count (optional)"),
    "exhibit": ("the object in a glass case in a museum", "object, label"),
    "theory": ("the character wonders, a thought bubble shows one explanation people suggest",
               "bubble (one word or an object from OBJECTS)"),
    "punch": ("the character walks on, the golden word UNEXPLAINED appears", "(none)"),
    "loop_close": ("the character walks on, the open question appears in gold", "(none)"),
}

STORY_PROMPT = """You write one 30-second episode for "UnexplainedDaily", a YouTube Shorts channel of hand-drawn
stick-figure cartoons about real mysteries. Topic: {topic}

WIKIPEDIA ARTICLE (the ONLY source of facts - every name, date and number must come from here):
<<<
{article}
>>>

EXAMPLE of an approved episode on another topic - copy its length, tone and rhythm, never its content:
{example}

WRITE A STORY, NOT A LIST OF FACTS.
- 8 to 10 narration sentences, 5 to 11 words each, 70 to 82 words in total (the example has 71). Count the words.
- Natural spoken English in the present tense, with articles and full verbs, as if telling a friend what happened.
  FORBIDDEN: headline style without articles ("Inside beds unmade clock stopped", "West landing damaged railings bent").
- Shape: HOOK (first sentence: the year, the place and a concrete strange situation)
  -> DISCOVERY -> 2 or 3 stranger and stranger DETAILS -> the strongest explanation people give (one sentence,
  marked as a theory) -> the "unexplained" sentence -> an open QUESTION that makes people comment.
- Every sentence must follow from the one before (so / but / then / and). A viewer who never heard of the topic
  must understand what happened, to whom, and why it is strange.
- Keep only details that serve the mystery. No museum, tourism, anniversaries, awards or research funding
  unless they ARE the mystery. No lists of theories.
- Never invent a name, date, number, quote or detail that is not in the article. Mark legends as legends.
- The second to last sentence contains the word "unexplained". The last sentence is the open question.
- Third person storyteller. Never "I", "we", "you". Never describe the drawing ("we see", "shot", "picture").

PICTURES. For each sentence choose ONE shot that literally shows what the sentence says.
SHOT CATALOG (shot: what is drawn [params]):
{catalog}
OBJECTS that can be drawn (never anything else): {objects}
Rules for pictures:
- The first shot is walk_in. The last two are punch and loop_close.
- Choose the world (where the story happens) from: {worlds}; suggested: {world_hint}.
- Choose the main character from: {heroes}; suggested: {hero_hint}. This character investigates the mystery.{hero_rule}
- Use at most one action_crowd, at most one theory, at most one exhibit, and never the same shot twice in a row.
- Use 1 to 3 insert shots for the concrete details of the mystery (the stopped clock, the torn page, the empty pegs,
  the note) - the character does not appear in them, so the episode is not always "the detective walks and looks".
  An insert is never the first shot. Its label uses words from its own sentence (or a number), never new facts.
- Vary the pictures. Recently used a lot on this channel (use them less): {recent}.
- The sentence must NAME the object the picture draws, with the same word (the picture shows a door, so the
  sentence says "door", not "gate"). People, animals and vehicles that are not the main character or a crowd
  can not be drawn - tell the story without needing to show them.
- params.object must be the thing the sentence is about (beds -> bed, clock -> clock, oilskins -> coat, log -> book).
- A golden number appears only when the sentence says that number (scale_measure value, wide_reveal count,
  walk_in year) - never show a number the narration does not say.
- When the sentence happens indoors (a room, a lighthouse, a cabin, a house) set "inside": true on spot,
  object_reveal or detail_compare - the picture then shows a room with a window onto the landscape.

Return JSON only:
{{"title": "The ... (max 6 words, no numbers, no colon)", "world": "...", "hero": "...",
  "beats": [{{"say": "narration sentence", "shot": "walk_in", "params": {{"object": "..."}}, "see": "what the viewer sees"}}, ...]}}"""

CRITIC_PROMPT = """You are the strict editor of a 30-second mystery cartoon drawn with stick figures. Judge this episode.

TOPIC: {topic}
EPISODE (sentence | [shot] what the viewer sees):
{beats}

The shot names in brackets are fixed templates of the animation engine - do not judge or rename them:
{catalog}
The engine can only draw these objects: {objects}. Dead people are drawn as skeletons or skulls; that is fine.

Score 0-10 each:
- hook: does the first sentence create a concrete, strange situation that makes you want to know more?
- story: does each sentence follow from the previous one, building ONE mystery (not a list of facts)?
- picture: does every picture literally show what its sentence says (same object, same action)?
- clarity: would a viewer who never heard of the topic understand what happened and why it is strange?
List the concrete problems with the WORDS of a sentence or the OBJECT of a picture (which sentence, what is wrong,
how to fix). Do not ask for new shot types, camera moves, colours or sound.
Return JSON only: {{"hook": 0, "story": 0, "picture": 0, "clarity": 0, "problems": ["..."]}}"""

FIX_PROMPT = """

YOUR PREVIOUS VERSION (keep it - it is the base):
{previous}

It had these problems:
{problems}

Return the whole episode again as JSON. Keep every sentence that is not mentioned in the problems EXACTLY as it was
(word for word, same shot, same params). Change only the sentences and pictures the problems point at, and keep
the total at 65 to 80 words."""


TIGHTEN_PROMPT = """Shorten this episode to at most 80 words in total without losing the story.
EPISODE JSON:
{previous}
Rules: keep the same number of sentences, the same order, the same shots and params, the same facts and numbers.
Only cut filler words and weak details inside the sentences; keep natural spoken English with articles and verbs.
Return the whole JSON again with the same structure."""


def _key(name):
    v = os.environ.get(name)
    if v:
        return v
    envp = os.path.join(os.path.expanduser("~"), ".config", "watch", ".env")
    if os.path.exists(envp):
        for ln in open(envp, encoding="utf-8", errors="replace"):
            if ln.strip().startswith(name + "="):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _json_from(txt, want=None):
    """JSON z odpovede, aj ked model pred nim „premysla nahlas" (Nemotron pise analyzu do content).
    Berie posledny platny objekt, ktory ma pozadovane kluce."""
    dec = json.JSONDecoder()
    best = None
    for i in [m.start() for m in re.finditer(r"\{", txt)]:
        try:
            obj, _ = dec.raw_decode(txt[i:])
        except ValueError:
            continue
        if isinstance(obj, dict) and (not want or any(k in obj for k in want)):
            best = obj
    return best


def or_chat(prompt, temperature=0.7, max_tokens=8000, want=None):
    """OpenRouter :free modely (bez platby). Kluc sa nikdy nevypisuje ani nelogguje.
    Pri 429 sa neceka - pretazenie free modelu vecer trva dlho, hned ide dalsi model."""
    import requests
    key = _key("OPENROUTER_API_KEY")
    if not key:
        return None
    h = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    for model in OR_MODELS:
        for att in range(2):
            try:
                r = requests.post(OR_URL, headers=h, timeout=300, json={
                    "model": model, "temperature": temperature, "max_tokens": max_tokens,
                    "reasoning": {"enabled": False, "exclude": True},
                    "messages": [{"role": "system", "content": "You write short mystery cartoons. Reply with ONE JSON "
                                                               "object only - no analysis, no notes before or after it."},
                                 {"role": "user", "content": prompt}]})
                if r.status_code == 429:
                    print(f"  [or] {model}: pretazeny (429), dalsi model", flush=True)
                    break
                if not r.ok:
                    print(f"  [or] {model}: HTTP {r.status_code} {r.text[:120].replace(key, '***')}", flush=True)
                    break
                txt = (r.json()["choices"][0]["message"].get("content") or "").strip()
                obj = _json_from(txt, want)
                if obj:
                    return obj
                print(f"  [or] {model}: odpoved bez JSON ({len(txt)} znakov), skusam znova", flush=True)
            except Exception as ex:
                print(f"  [or] {model}: {str(ex)[:100]}", flush=True)
                time.sleep(3)
    return None


def llm(prompt, temperature=0.7, max_tokens=8000, want=None):
    out = or_chat(prompt, temperature, max_tokens, want)
    if out is None:                                  # zaloha: Groq (slabsi, ale nech fabrika nestoji)
        print("  [llm] OpenRouter nedostupny -> Groq", flush=True)
        out = v2._llm_write(prompt, temperature=temperature, max_tokens=max_tokens)
    return out or {}


def article(topic):
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    p = os.path.join(SPECS, "_articles", slug + ".txt")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read()
    title, text = v1.wiki_extract(topic, chars=12000)
    if text:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(text)
    return text


def recent_shots(n=6):
    try:
        hist = json.load(open(HISTORY, encoding="utf-8"))
    except (OSError, ValueError):
        return "nothing yet"
    cnt = {}
    for ep in hist[-n:]:
        for s in set(ep.get("shots", [])):
            if s not in ("walk_in", "punch", "loop_close"):
                cnt[s] = cnt.get(s, 0) + 1
    busy = [f"{s} (in {c} of the last {min(n, len(hist))} episodes)" for s, c in sorted(cnt.items(), key=lambda x: -x[1])
            if c >= 2]
    return ", ".join(busy) or "nothing repeated"


def remember(spec):
    try:
        hist = json.load(open(HISTORY, encoding="utf-8"))
    except (OSError, ValueError):
        hist = []
    hist.append({"topic": spec.get("topic"), "world": spec.get("world"), "hero": spec.get("hero"),
                 "shots": [l["shot"] for l in spec["lines"]]})
    json.dump(hist[-30:], open(HISTORY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def _cast_lru():
    """Kanal "unexplained": dalsi hrdina sa nevybera cez LLM ale strieda sa - vrati z HEROES toho,
    koho CAST_HISTORY ukazuje ako najdavnejsie pouziteho (alebo hocikoho, ak tam este nikto nie je),
    takze dve susedne epizody nikdy nemaju rovnaku postavu. Zapisuje sa cez _remember_cast nizsie."""
    try:
        hist = json.load(open(CAST_HISTORY, encoding="utf-8"))
    except (OSError, ValueError):
        hist = []

    def last_used(h):
        idx = [i for i, x in enumerate(hist) if x == h]
        return idx[-1] if idx else -1
    return min(HEROES, key=last_used)


def _remember_cast(hero):
    try:
        hist = json.load(open(CAST_HISTORY, encoding="utf-8"))
    except (OSError, ValueError):
        hist = []
    hist.append(hero)
    os.makedirs(os.path.dirname(CAST_HISTORY), exist_ok=True)
    json.dump(hist[-30:], open(CAST_HISTORY, "w", encoding="utf-8"))


def _object_variant(obj, say):
    """Varianta rekvizity podla vety: „supply box" nie je piratska truhla (chest -> crate),
    rozbita debna ma vlastnu kresbu (crate_broken)."""
    low = (say or "").lower()
    if obj == "chest" and re.search(r"\b(box|boxes|crate|crates|supply|supplies)\b", low) and not re.search(r"\bchest\b", low):
        obj = "crate"
    if obj == "crate" and re.search(r"\b(smashed|broken|splintered|shattered|wrecked|damaged|crushed|destroyed)\b", low):
        obj = "crate_broken"
    if obj == "tower" and re.search(r"\blighthouse", low):
        obj = "lighthouse"
    # insert-varianty: plast na vesiaku/haku (nie stojan), kniha s vytrhnutou stranou
    if obj == "coat" and re.search(r"\b(pegs?|hooks?|hang|hangs|hanging|hung|rail)\b", low):
        obj = "coat_hanging"
    if obj == "book" and re.search(r"\b(torn|ripped|missing page|page)\b", low):
        obj = "book_torn"
    # cerstva obet (dead man, bodies) nie je kostra - telo pod plachtou; kosti len ked veta hovori o kostiach
    if obj in ("skull", "bones") and re.search(r"\b(dead|bod(y|ies)|corpses?|lifeless)\b", low) \
            and not re.search(r"\b(skeletons?|bones?|skulls?)\b", low):
        obj = "body"
    return obj


_LABEL_TAIL_STOP = {"NO", "AND", "OR", "OF", "THE", "A", "AN", "IN", "ON", "AT", "TO", "WITH", "BY", "FOR", "NOT"}


def _clean_params(shot, pr, say=""):
    """Parametre len tie, ktore engine cita; objekt musi byt kreslitelny."""
    pr = dict(pr or {})
    obj = str(pr.get("object") or "").strip().lower()
    if obj and obj not in v2.OBJECTS:
        pr.pop("object", None)
    elif obj:
        pr["object"] = _object_variant(obj, say)
    if "inside" in pr:
        pr["inside"] = str(pr["inside"]).strip().lower() in ("true", "1", "yes")
    if shot == "insert":
        raw = str(pr.get("label") or "")
        # "NO EYES, NO TONGUES" -> len prva cast pred ciarkou; max 3 slova; nikdy neskoncit spojkou/clenom
        first = re.split(r"[,;:/|]", raw)[0] if len(raw.split()) > 3 else raw
        lab = re.sub(r"[^A-Za-z0-9 ]", "", first).strip().upper()
        words = lab.split()[:3]
        while words and words[-1] in _LABEL_TAIL_STOP:
            words.pop()
        pr["label"] = " ".join(words)[:26] if words else ""
        if not pr["label"]:
            pr.pop("label", None)
        mk = str(pr.get("mark") or "none").strip().lower()
        pr["mark"] = mk if mk in ("circle", "cross", "arrow", "none") else "none"
        for k in ("count", "filled"):
            try:
                pr[k] = max(0, int(float(str(pr.get(k, 1)).replace(",", ""))))
            except ValueError:
                pr[k] = 1
        pr["count"] = max(1, min(6, pr["count"]))
        pr["filled"] = max(0, min(pr["count"], pr["filled"]))
    for k in ("value", "count", "years"):
        if k in pr:
            try:
                pr[k] = float(str(pr[k]).replace(",", "")) if k == "value" else int(float(str(pr[k]).replace(",", "")))
            except ValueError:
                pr.pop(k, None)
    return pr


def _fix_unspoken(spec):
    """Zlate cislo, ktore veta nepovie, sa na obraze neukaze - deterministicky, bez dalsieho kola LLM:
    scale_measure bez povedanej hodnoty -> object_reveal; count / year / years bez opory vo vete sa zahodia."""
    for l in spec["lines"]:
        pr = dict(l.get("params") or {})
        said = v2._numbers(l["say"])

        def spoken(v):
            try:
                return float(str(v).replace(",", "")) in said
            except (TypeError, ValueError):
                return False
        if l["shot"] == "scale_measure" and not spoken(pr.get("value")):
            l["shot"] = "object_reveal"
            for k in ("value", "unit", "axis"):
                pr.pop(k, None)
            if pr.get("action") in ("measure", None, ""):
                pr["action"] = "watch"
        if l["shot"] in ("wide_reveal", "action_crowd") and pr.get("count") and not spoken(pr["count"]):
            pr.pop("count", None)
        if l["shot"] == "walk_in" and pr.get("year") and not spoken(pr["year"]):
            pr.pop("year", None)
        if l["shot"] == "timeline_compare" and pr.get("years") and not spoken(pr["years"]):
            pr.pop("years", None)
        # telo sa nevykopava ani nedviha: postava k nemu pride, ukaze a klakne (spot/object_reveal s watch)
        if pr.get("object") == "body" and pr.get("action") in ("find", "dig", "reach", "carry"):
            pr["action"] = "watch"
        # zostup do sachty (s vykrikom AAAAH) nie je zaber na obete - „buried under four meters of snow" -> insert tela
        if l["shot"] == "descend" and re.search(r"\b(bod(y|ies)|dead|victims?|missing|buried|remains|corpses?)\b", l["say"].lower()):
            l["shot"] = "insert"
            lab = next((w.upper() for w in ("buried", "missing", "found") if re.search(r"\b" + w, l["say"].lower())), "")
            pr = {"object": "body", "mark": "none", "inside": False} | ({"label": lab} if lab else {})
        # „obrovska vlna" v bubline je vlna, nie jazero
        if l["shot"] == "theory" and str(pr.get("bubble") or "").lower() in ("water", "sea", "ocean") \
                and re.search(r"\b(waves?|tsunami|swell)\b", l["say"].lower()):
            pr["bubble"] = "wave"
        # veta o obetiach (tongue/eyes/faces/bodies…) s vlozkou vody/stromu/kamena -> telo pod plachtou
        if l["shot"] in ("insert", "object_reveal", "spot", "detail_compare") \
                and pr.get("object") in ("water", "wave", "tree", "stone", "mountain", "cave", "forest", "fallen_tree") \
                and re.search(r"\b(tongues?|eyes?|faces?|bod(y|ies)|corpses?|remains|victims?)\b", l["say"].lower()):
            pr["object"] = "body"
            if l["shot"] != "insert":
                pr["action"] = "watch"
        l["params"] = pr
    # ten isty zaber dvakrat po sebe (spot, spot) -> druhy sa prepne na sesterský archetyp s rovnakym objektom
    for a, b in zip(spec["lines"], spec["lines"][1:]):
        if a["shot"] == b["shot"] and b["shot"] in ("spot", "object_reveal"):
            b["shot"] = "object_reveal" if b["shot"] == "spot" else "spot"
            b["params"].setdefault("action", "watch" if b["shot"] == "object_reveal" else "point")


def _named(obj, say, strict=False):
    """Rovnaky test ako v2.check_beats: kmen predmetu alebo synonymum vo vete (strict = cele slovo)."""
    stem = obj.rstrip("s")
    pat = (r"\b" + re.escape(stem)) if strict else (stem[:5] if len(stem) > 5 else stem)
    return bool(re.search(pat, say, re.I) or re.search(v2._SYN.get(obj, "(?!x)x"), say, re.I))


_CONT = re.compile(r"(some|others|the rest|the others|(two|three|four|five|six|seven|eight|nine|ten|\d+) "
                   r"(more|others|of them)|it|its|they|their|this|these)\b", re.I)


def _fix_unnamed(spec):
    """Zaber kresli predmet, ktory veta nepomenuje (v2 kontrola) - deterministicky, bez dalsieho kola LLM:
    1) predmet, ktory veta naozaj pomenuje (cele slovo z OBJECTS/_SYN), 2) pri pokracovacej vete
    ('Three more are found…', 'Others…') predmet predosleho zaberu. Inak ostava na modeli (kolo FIX)."""
    lines = spec["lines"]
    for i, l in enumerate(lines):
        pr = l.get("params") or {}
        obj = str(pr.get("object") or "").lower()
        if not obj or l["shot"] == "walk_in" or _named(obj, l["say"]):
            continue
        prev = str(((lines[i - 1].get("params") or {}).get("object") if i else "") or "").lower()
        found = next((o for o in v2.OBJECTS if o != obj and _named(o, l["say"], strict=True)), "")
        cont = _CONT.match(l["say"].strip())
        if prev and cont and not re.match(r"(it|its|they|their|this|these)\b", cont.group(0), re.I):
            pr["object"] = prev                      # 'Three more…', 'Others…' = ten isty predmet ako predtym
        elif found:
            pr["object"] = _object_variant(found, l["say"])
        elif prev and cont:
            pr["object"] = prev                      # zamenova veta ('Their…', 'It…') o predoslom predmete
        else:
            continue
        print(f"  [fix] zaber {i + 1}: '{obj}' -> '{pr['object']}' (veta ho pomenuje)", flush=True)
        l["params"] = pr


def check_v3(spec, text):
    """Kontroly v2 (nakreslitelnost, cisla, mena, opis kresby, prva osoba…) proti CELEMU clanku."""
    for l in spec["lines"]:
        l["fact"] = text
    probs = v2.check_beats(spec, spec["world"]) + v1.check_facts(spec) + v1.check_compare(spec) + v2.check_numbers(spec)
    # v3 ma 8-11 viet a vety do 12 slov; pocet a dlzku v2 kontroluje prisnejsie
    probs = [p for p in probs if not p.startswith("pocet zaberov")
             and not re.match(r"zaber \d+ ma (1[0-2]) slov", p)]
    n = len(spec["lines"])
    if not 8 <= n <= 11:
        probs.append(f"{n} sentences - write 8 to 10 story sentences plus punch and question")
    nw = sum(len(l["say"].split()) for l in spec["lines"])
    if nw > 80:
        probs.append(f"{nw} words in total - the hard limit is 80: cut filler words and weak details, keep the story")
    seen = [l["shot"] for l in spec["lines"]]
    for s in ("action_crowd", "theory", "exhibit"):
        if seen.count(s) > 1:
            probs.append(f"shot {s} used {seen.count(s)} times - at most once")
    for a, b in zip(seen, seen[1:]):
        if a == b and a not in ("punch", "loop_close", "insert"):
            probs.append(f"shot {a} twice in a row - vary the pictures")
    if seen.count("insert") > 3:
        probs.append(f"insert used {seen.count('insert')} times - at most 3")
    # popis v inserte nesmie pridavat fakty: kazde slovo je vo vete, alebo cislo, alebo z malej sady stavov
    OK_LABEL = {"missing", "stopped", "torn", "empty", "gone", "unknown", "locked", "open", "closed", "broken", "found",
                "no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "left", "still",
                # jednotky a skratky cisel ("36 KG" pri vete "36-kilogram", "700 M", "3 HZ")
                "kg", "g", "t", "m", "km", "cm", "mm", "ft", "mi", "mph", "kmh", "hz", "khz", "db", "c", "f", "lb",
                "lbs", "yrs", "years", "year", "days", "hours", "min", "sec", "x", "%"}
    for i, l in enumerate(spec["lines"], 1):
        if l["shot"] != "insert":
            continue
        lab = str((l.get("params") or {}).get("label") or "")
        low = l["say"].lower()
        bad = [w for w in lab.lower().split() if not (w.isdigit() or w in OK_LABEL or re.search(r"\b" + re.escape(w) + r"\w*", low))]
        if bad:
            probs.append(f"zaber {i} (insert): popis '{lab}' pouziva slova mimo vety ({', '.join(bad)}) - popis len z vety")
    return probs


def _example():
    """Schvalena epizoda (Roopkund, ENGINE_9) ako vzor dlzky a tonu - obsah sa nekopiruje."""
    try:
        ex = json.load(open(os.path.join(SPECS, "roopkund_final.json"), encoding="utf-8"))
    except (OSError, ValueError):
        return "(none)"
    beats = [{"say": l["say"], "shot": l["shot"],
              "params": {k: v for k, v in (l.get("params") or {}).items() if v not in (None, "")}}
             for l in ex["lines"]]
    return json.dumps({"title": ex.get("title"), "world": ex.get("world"), "hero": ex.get("hero"), "beats": beats},
                      ensure_ascii=False)


def _assemble(out, topic, text, world_hint, hero_hint):
    """Odpoved modelu -> spec (zabery z katalogu, params vycistene, deterministicke opravy, gold/cue/era)."""
    beats = [b for b in (out.get("beats") or []) if isinstance(b, dict) and (b.get("say") or "").strip()]
    if not beats:
        return None
    lines = []
    for b in beats:
        shot = str(b.get("shot") or "").strip()
        if shot not in CATALOG:
            shot = "object_reveal" if (b.get("params") or {}).get("object") else "theory"
        lines.append({"say": b["say"].strip(), "shot": shot, "params": _clean_params(shot, b.get("params"), b["say"]),
                      "see": str(b.get("see") or "")[:200]})
    lines[0]["shot"] = "walk_in"
    if lines[-1]["shot"] != "loop_close":
        lines[-1]["shot"] = "loop_close"
    if len(lines) > 1 and lines[-2]["shot"] != "punch":
        lines[-2]["shot"] = "punch"
    lines[-2].setdefault("params", {})["word"] = "UNEXPLAINED"
    lines[-1]["params"]["question"] = lines[-1]["say"]
    world = out.get("world") if out.get("world") in WORLDS else world_hint
    # "unexplained": hero_hint uz je LRU-rotovana postava (generate()) - LLM ju nevybera, len ju dostane
    hero = hero_hint if CHANNEL == "unexplained" else (out.get("hero") if out.get("hero") in HEROES else hero_hint)
    spec = {"title": out.get("title", ""), "topic": topic, "facts": [text], "world": world, "hero": hero,
            "lines": lines, "generator": "v3"}
    _fix_unspoken(spec)
    _fix_unnamed(spec)
    v2._derive(spec)
    return spec


def _words(spec):
    return sum(len(l["say"].split()) for l in spec["lines"])


def _as_json(spec):
    return json.dumps({"title": spec.get("title", ""), "world": spec["world"], "hero": spec["hero"],
                       "beats": [{"say": l["say"], "shot": l["shot"], "params": l["params"], "see": l.get("see", "")}
                                 for l in spec["lines"]]}, ensure_ascii=False)


def generate(topic, rounds=3):
    text = article(topic)
    if len(text) < 800:
        print(f"  !! clanok o '{topic}' je prilis kratky ({len(text)} znakov) - tema sa preskakuje", flush=True)
        raise SystemExit(3)
    world_hint, hero_hint = v1.scene_world(topic, [text], [])
    if CHANNEL == "unexplained":
        hero_hint = _cast_lru()          # rotacia namiesto LLM - fixne pre cele generovanie tejto temy
    cat = "\n".join(f"- {k}: {what} [{prm}]" for k, (what, prm) in CATALOG.items())
    heroes_txt, hero_rule = ", ".join(HEROES), ""
    if CHANNEL == "unexplained":
        heroes_txt = f"{hero_hint} ({HERO_ROLE.get(hero_hint, 'an explorer')})"
        hero_rule = (" The hero is fixed - use exactly this one. NEVER write the character's name in any sentence: "
                     "the narration is about the phenomenon; say 'the explorer', 'she' or 'he' when needed.")
    base = STORY_PROMPT.format(topic=topic, article=text[:11000], example=_example(), catalog=cat, objects=", ".join(v2.OBJECTS),
                               worlds=", ".join(WORLDS), world_hint=world_hint, heroes=heroes_txt,
                               hero_hint=hero_hint, hero_rule=hero_rule, recent=recent_shots())
    best, notes, prev_json = None, [], ""
    for rnd in range(1, rounds + 1):
        out = llm(base + (FIX_PROMPT.format(previous=prev_json, problems="\n".join(f"- {p}" for p in notes))
                          if notes else ""), want=("beats",))
        beats = [b for b in (out.get("beats") or []) if isinstance(b, dict) and (b.get("say") or "").strip()]
        if not beats:
            notes = ["return the JSON with 8-10 beats"]
            continue
        lines = []
        for b in beats:
            shot = str(b.get("shot") or "").strip()
            if shot not in CATALOG:
                shot = "object_reveal" if (b.get("params") or {}).get("object") else "theory"
            lines.append({"say": b["say"].strip(), "shot": shot, "params": _clean_params(shot, b.get("params"), b["say"]),
                          "see": str(b.get("see") or "")[:200]})
        lines[0]["shot"] = "walk_in"
        if lines[-1]["shot"] != "loop_close":
            lines[-1]["shot"] = "loop_close"
        if len(lines) > 1 and lines[-2]["shot"] != "punch":
            lines[-2]["shot"] = "punch"
        lines[-2].setdefault("params", {})["word"] = "UNEXPLAINED"
        lines[-1]["params"]["question"] = lines[-1]["say"]
        world = out.get("world") if out.get("world") in WORLDS else world_hint
        # "unexplained": hero_hint uz je LRU-rotovana postava (generate()) - LLM ju nevybera, len ju dostane
        hero = hero_hint if CHANNEL == "unexplained" else (out.get("hero") if out.get("hero") in HEROES else hero_hint)
        spec = {"title": out.get("title", ""), "topic": topic, "facts": [text], "world": world, "hero": hero,
                "lines": lines, "generator": "v3"}
        _fix_unspoken(spec)
        _fix_unnamed(spec)
        v2._derive(spec)
        probs = check_v3(spec, text)
        crit = llm(CRITIC_PROMPT.format(topic=topic, beats="\n".join(
            f"{i}. {l['say']} | [{l['shot']}] {l.get('see', '')}" for i, l in enumerate(lines, 1)),
            catalog=cat, objects=", ".join(v2.OBJECTS)),
            temperature=0.2, max_tokens=6000, want=("hook", "story"))
        scores = {k: int(crit.get(k, 0) or 0) for k in ("hook", "story", "picture", "clarity")}
        weak = [k for k, v in scores.items() if v < 7]
        print(f"  kolo {rnd}: {len(lines)} viet, {sum(len(l['say'].split()) for l in lines)} slov, kritik {scores}, "
              f"kontroly {len(probs)}", flush=True)
        notes = probs + ([f"editor: {p}" for p in (crit.get("problems") or [])[:6]] if weak else [])
        prev_json = json.dumps({"title": spec["title"], "world": world, "hero": hero,
                                "beats": [{"say": l["say"], "shot": l["shot"], "params": l["params"], "see": l.get("see", "")}
                                          for l in lines]}, ensure_ascii=False)
        score = sum(scores.values()) - 3 * len(probs)
        if best is None or score > best[0]:
            best = (score, spec, notes, scores)
        if not probs and not weak:
            break
    if not best:
        raise SystemExit("model nevratil pouzitelny pribeh")
    _, spec, notes, scores = best
    hard = [p for p in notes if not p.startswith("editor")]
    # pridlhy scenar (rec by bola nad 1,3x) -> jedno skracovacie volanie, ktore drzi vety, zabery aj cisla
    nw = _words(spec)
    if nw > 84:
        out = llm(TIGHTEN_PROMPT.format(previous=_as_json(spec)), temperature=0.3, max_tokens=6000, want=("beats",))
        cand = _assemble(out, topic, text, world_hint, hero_hint) if out else None
        if cand and len(cand["lines"]) == len(spec["lines"]):
            probs2 = check_v3(cand, text)
            print(f"  skratenie: {nw} -> {_words(cand)} slov, kontroly {len(probs2)}", flush=True)
            if _words(cand) < nw and len(probs2) <= len(hard):
                spec, hard = cand, probs2
    # brana pre fabriku: tvrde kontroly + slaby pribeh/zrozumitelnost; poznamky editora su len informacia
    # (limit 80 slov riadi FIX/TIGHTEN; do 90 slov (~32 s reci) sa hotova epizoda nezahadzuje)
    hard = [p for p in hard if not (("words in total" in p or p.startswith("slov ")) and _words(spec) <= 100)]
    problems = hard + [f"kritik {k} = {scores[k]}/10 (chcem aspon 6)" for k in ("story", "clarity") if scores.get(k, 0) < 6]
    for l in spec["lines"]:
        l.pop("fact", None)
    spec["critic"] = scores
    return spec, problems


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
    if not problems:
        remember(spec)
        if CHANNEL == "unexplained":
            _remember_cast(spec["hero"])   # len pre pouzitelnu epizodu - preskocena tema nesmie "ukradnut" tah v rotacii
    print(f"\n{spec.get('title')}  ({spec['world']}/{spec['hero']}, kritik {spec.get('critic')})  ->  {out}")
    if "--show" in sys.argv:
        for i, l in enumerate(spec["lines"], 1):
            pr = " ".join(f"{k}={v}" for k, v in (l.get("params") or {}).items() if k != "question")
            print(f" {i:2}. [{l['shot']:15}] {l['say']}\n      {pr}  | {l.get('see', '')}")
    if problems:
        print("PROBLEMY:", "; ".join(problems[:8]))
        sys.exit(2)
