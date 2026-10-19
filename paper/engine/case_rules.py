# -*- coding: utf-8 -*-
"""Pravidla rastu pre spisy ColdCaseDaily (cisto offline, bez siete): dlzka, hook bez datumu, titulok-zvedavost, vyber tem.
  - video <= ~30 s: 4 beaty, 65-75 slov celeho hovoreneho textu (hook + beaty + end.line); tvrdy strop 80 (85 po jednom prepise)
  - hook nikdy nezacina rokom / datumom ("In 1959, ..."), ma vytvorit napatie alebo otazku v prvych 3 s; do spisu ide hook_style
  - "headline" = zvedavy titulok pre YouTube/TikTok (title ostava nazov pripadu pre dedup, popis a tagy)
  - poradie tem: menej zname + nebo/hory najprv, top-20 najznamejsich az nakoniec
Pouziva refill_case.write_spec (enforce) a compose_case (headline -> nazov videa); testy: engine/test_case_rules.py."""
import re

TARGET_BEATS = 4
SOFT_WORDS = 80            # nad tym sa raz pyta kratsi prepis
HARD_WORDS = 85            # po prepise nad tym spis zamietnut
MONTHS = ("january february march april june july august september october november december").split()   # bez "may" a skratiek (Jan = meno)
HOOK_STYLES = ("question", "shock", "mystery")

_NUM = re.compile(r"\d")
_LEAD = re.compile(r"^\W*(?:in|on|since|by|during|around|circa|back in|late in|early in|as of)\b", re.I)


def wcount(text):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", str(text or "")))


def end_line(S):
    e = S.get("end")
    return str(e.get("line") if isinstance(e, dict) else e or "")


def spoken_words(S):
    """pocet slov celeho hovoreneho textu (rovnako ako ho cita TTS): hook + riadky beatov + end.line"""
    n = wcount(S.get("hook")) + wcount(end_line(S))
    return n + sum(wcount(b.get("line")) for b in (S.get("beats") or []) if isinstance(b, dict))


def date_first(hook):
    """True ak hook zacina rokom / datumom: cislo alebo mesiac v prvych 3 slovach, alebo 'In/On/Since + cislo/mesiac' na zaciatku"""
    ws = re.findall(r"[A-Za-z0-9][A-Za-z0-9'\-]*", str(hook or ""))
    head = ws[:3]
    if any(_NUM.search(w) or w.lower() in MONTHS for w in head):
        return True
    return bool(_LEAD.match(str(hook or "")) and any(_NUM.search(w) or w.lower() in MONTHS for w in ws[1:4]))


def hook_style_of(S):
    st = str(S.get("hook_style") or "").strip().lower()
    if st in HOOK_STYLES:
        return st
    h = str(S.get("hook") or "").strip()
    return "question" if h.endswith("?") else "shock" if h.endswith("!") or len(h.split()) <= 8 else "mystery"


def clean_headline(S):
    """zvedavy titulok: 3-10 slov, <= 70 znakov, bez koncovej bodky a bez roku na zaciatku; inak '' (potom sa pouzije title)"""
    h = re.sub(r"\s+", " ", str(S.get("headline") or "")).strip().strip('"').rstrip(".")
    if not h or len(h) > 70 or not 3 <= wcount(h) <= 10 or date_first(h):
        return ""
    return h


def trim_beats(S, n=TARGET_BEATS):
    """viac beatov nez n: zahod ten zo stredu s najmenej kartami (pri rovnosti neskorsi); prvy a posledny (THE TWIST) ostavaju"""
    beats = [b for b in (S.get("beats") or []) if isinstance(b, dict)]
    cards = lambda b: sum(1 for s in (b.get("shots") or []) if isinstance(s, dict) and s.get("t") == "card")  # noqa: E731
    while len(beats) > n and len(beats) > 2:
        i = min(range(1, len(beats) - 1), key=lambda j: (cards(beats[j]), -j))
        beats.pop(i)
    S["beats"] = beats
    return S


def problems(S):
    """zoznam poruseni pravidiel (prazdny = OK)"""
    out = []
    nb = len(S.get("beats") or [])
    if nb > TARGET_BEATS:
        out.append(f"{nb} beats (max {TARGET_BEATS})")
    w = spoken_words(S)
    if w > SOFT_WORDS:
        out.append(f"{w} words (max {SOFT_WORDS})")
    if date_first(S.get("hook")):
        out.append("hook starts with a year/date")
    return out


REWRITE_SYS = ("You tighten spoken scripts for 30-second true-mystery shorts. Keep every fact and name, keep the key words that "
               "the visuals point to, never invent facts. Return ONLY JSON: "
               '{"hook": "...", "lines": ["...", ...], "end_line": "..."}')


def rewrite_prompt(S, probs):
    lines = [str(b.get("line") or "") for b in S["beats"]]
    return ("PROBLEMS: " + "; ".join(probs) + ".\nRewrite so that the TOTAL spoken text (hook + all lines + end_line) is 65-75 words. "
            "The hook must be ONE short sentence of at most 12 words that creates tension or asks a question and never starts with "
            "a year or a date (put dates in later lines). Return exactly " + str(len(lines)) + " lines, in the same order, 8-14 words each.\n"
            + "HOOK: " + str(S.get("hook") or "") + "\n" + "\n".join(f"LINE {i + 1}: {x}" for i, x in enumerate(lines))
            + "\nEND_LINE: " + end_line(S))


def apply_rewrite(S, out):
    """prepis z LLM do spisu (zachova shots / labels); nevalidny vystup spis nezmeni. Vracia True ak sa nieco zmenilo"""
    if not isinstance(out, dict):
        return False
    lines = out.get("lines")
    changed = False
    if isinstance(lines, list) and len(lines) == len(S["beats"]) and all(isinstance(x, str) and x.strip() for x in lines):
        for b, x in zip(S["beats"], lines):
            b["line"], changed = x.strip(), True
    if isinstance(out.get("hook"), str) and out["hook"].strip():
        S["hook"], changed = out["hook"].strip(), True
    if isinstance(out.get("end_line"), str) and out["end_line"].strip():
        e = S.get("end")
        S["end"] = dict(e, line=out["end_line"].strip()) if isinstance(e, dict) else {"line": out["end_line"].strip()}
        changed = True
    return changed


def enforce(S, llm=None):
    """hlavny vstup: orezanie beatov, jeden prepis (llm(system, prompt) -> dict) ak je text dlhy / hook zacina datumom,
    hook_style + headline. Vyhodi ValueError, ak spis ostane porusovat tvrde pravidla (hook s datumom, > HARD_WORDS slov)."""
    trim_beats(S)
    probs = problems(S)
    if probs and llm:
        try:
            if apply_rewrite(S, llm(REWRITE_SYS, rewrite_prompt(S, probs))):
                print("   [rules] prepis kvoli: " + "; ".join(probs))
        except Exception as e:
            print(f"   [rules] prepis zlyhal: {type(e).__name__}: {str(e)[:120]}")
        probs = problems(S)
    if date_first(S.get("hook")):
        raise ValueError(f"hook zacina datumom: {str(S.get('hook'))[:60]}")
    w = spoken_words(S)
    if w > HARD_WORDS:
        raise ValueError(f"text je prilis dlhy ({w} slov, max {HARD_WORDS})")
    if probs:
        print("   [rules] pozor (prijate): " + "; ".join(probs))
    S["hook_style"] = hook_style_of(S)
    S["headline"] = clean_headline(S)
    return S


# ---------- poradie tem: menej zname + nebo/hory najprv, top-20 najznamejsich nakoniec

FAMOUS = ["Dyatlov Pass", "Mary Celeste", "Bermuda Triangle", "Amelia Earhart", "Roswell", "D.B. Cooper", "Loch Ness",
          "Zodiac", "Jack the Ripper", "Flight 19", "Voynich", "Wow Signal", "Tunguska", "Phoenix Lights", "Nazca",
          "Roanoke", "Oak Island", "Easter Island", "Area 51", "Stonehenge", "Antikythera", "Marie Celeste", "MH370",
          "Black Dahlia", "Jimmy Hoffa", "Bigfoot", "Rendlesham"]
ANOMALY = ["light", "lights", "ufo", "sky", "sighting", "sightings", "orb", "meteor", "signal", "hum", "mountain", "mountains",
           "peak", "hikers", "climbers", "glacier", "alps", "himalaya", "pass", "airship", "contrail", "fireball", "aurora", "radar"]


def _famous_keys():
    import case_dedup
    return [case_dedup.case_key(x) for x in FAMOUS]


def topic_rank(t, famous=None):
    """0 = menej zname + nebo/hory, 1 = menej zname, 2 = top slavne"""
    import case_dedup
    famous = famous or _famous_keys()
    if case_dedup.is_dup(t, famous):
        return 2
    words = set(re.findall(r"[a-z]+", str(t).lower()))
    return 0 if words & set(ANOMALY) else 1


def prefer_lesser_known(topics):
    """stabilne zoradi temy podla topic_rank (poradie v banke ostava v ramci skupiny); nic sa nemaze"""
    fk = _famous_keys()
    return sorted(topics, key=lambda t: topic_rank(t, fk))
