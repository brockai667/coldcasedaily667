#!/usr/bin/env python3
"""Doplni banku tem cez GitHub Models (zadarmo). Nika: TRUE CRIME / cold cases.
NOVY FORMAT (PRO engine, noir dizajn): tema = case + place + country + 5-6 scen
(hook/map/fact/archive/callout/cta) s presnymi queries, sync chipmi, ARCHIVE scenou
(realna dobova fotka z Wikimedia) a popisom kde sa to stalo.
Stare temy bez 'scenes' sa vyradia az ked su aspon 3 nove (den nikdy neostane bez videi)."""
import json
import os
import re
import sys

import requests
try:
    import trends                      # trend scanner (Reddit + YouTube), volitelny
except Exception:
    trends = None

ROOT = os.path.dirname(os.path.abspath(__file__))
BANK = os.path.join(ROOT, "topics_bank.json")
STATE = os.path.join(ROOT, "used_topics.json")

TARGET = int(os.environ.get("TOPICS_TARGET", "15"))
MODEL = os.environ.get("MODELS_MODEL", "openai/gpt-4o-mini")
BASE = os.environ.get("MODELS_BASE_URL", "https://models.github.ai/inference")
TOKEN = os.environ.get("MODELS_TOKEN") or os.environ.get("GITHUB_TOKEN")

TREND_SUBREDDITS = ['TrueCrime', 'UnresolvedMysteries', 'serialkillers', 'Casefile', 'Damnthatsinteresting']
TREND_YT_QUERIES = ['famous unsolved cases', 'notorious heists', 'infamous mysteries', 'famous cold cases']

SYSTEM = ("You are a scriptwriter for a respectful TRUE-CRIME / cold-case brand. You retell FAMOUS, "
          "widely-documented cases (heists, disappearances, unsolved mysteries, historic cases) in a "
          "serious documentary voice. STRICT SAFETY RULES: (1) ACCURACY IS SACRED - only real, "
          "widely-reported facts; never invent details, names, dates or motives. (2) NEVER accuse or "
          "name any person as guilty unless they were actually convicted; for unsolved cases say it "
          "remains unsolved. (3) Be respectful to victims - NO graphic or gory detail, ever. "
          "(4) Present theories AS theories. You output strict JSON, nothing else.")

EXAMPLE = {
    "title": "The Heist Hidden Behind Empty Frames",
    "place": "Boston",
    "country": "USA",
    "scenes": [
        {"role": "hook", "text": "Thirteen masterpieces vanished in one night, and the frames still hang empty.",
         "hook_top": "THE FRAMES STILL HANG EMPTY", "query": "dark museum interior night",
         "query2": "empty picture frame wall"},
        {"role": "map", "text": "It happened in Boston, at the Isabella Stewart Gardner Museum."},
        {"role": "fact", "text": "In 1990, two men dressed as police officers walked out with art worth five hundred million dollars.",
         "query": "police uniform night city", "query2": "museum corridor dark",
         "chips": [{"t": "1990", "on": "1990", "style": "white"}, {"t": "$500M IN ART", "on": "million", "style": "accent"}],
         "punch": "police"},
        {"role": "archive", "text": "The museum still displays the empty frames, waiting for the paintings to come home.",
         "archive_query": "Isabella Stewart Gardner Museum courtyard", "archive_label": "Gardner Museum · Boston"},
        {"role": "callout", "text": "Despite a ten million dollar reward, not one painting has ever been recovered.",
         "query": "case files folder desk dark", "query2": "detective desk documents night",
         "label": "NEVER RECOVERED", "sub": "$10M reward still stands", "label_on": "reward", "punch": "never"},
        {"role": "cta", "text": "Follow for a new cold case every day.",
         "query": "foggy city night aerial", "query2": "rain window night city"}
    ],
    "description": "\U0001F4CD Boston, USA - 1990. Two fake cops, 81 minutes, $500 million in stolen art. The Gardner Museum heist is still unsolved, and the empty frames still hang. Follow for daily cold cases!",
    "hashtags": ["#truecrime", "#coldcase", "#unsolved", "#heist", "#gardnermuseum", "#boston", "#mystery", "#shorts", "#fyp"],
}


import random  # CTAS_ROTATE

CTAS = [
    "Follow for a new cold case every day.",
    "Follow if you'd have cracked this one.",
    "Follow for the cases that were never solved.",
    "Follow for daily true crime mysteries.",
    "Follow because some cases still need answers.",
]



PERFORMANCE = (
    "\nPERFORMANCE DATA (real results - obey this, it decides reach):\n"
    "- WHAT PERFORMS (strongly prefer these): famous, notorious, widely-recognized cases - iconic unsolved mysteries, legendary heists, historic crimes with a hook people have actually heard of or a striking twist.\n"
    "- WHAT KILLS REACH (avoid): obscure individual victims nobody has heard of, generic 'the disappearance of <unknown name>', and cases with no recognizable angle. If it is not recognizable or lacks a gripping twist, skip it and pick a famous case instead.\n"
)

def build_prompt(n, existing_titles, existing_places, trending=None):
    trend_block = ""
    if trending:
        joined = chr(10).join("- " + t for t in trending)
        trend_block = (
            " WHAT REAL PEOPLE DISCUSS AND WATCH THIS WEEK (live headlines from Reddit communities and "
            "top YouTube videos in this niche): " + joined +
            " Let at least HALF of the new topics be directly inspired by a SPECIFIC item above, turned "
            "into a strong hook that STILL follows all safety rules. Do NOT copy any headline "
            "word-for-word, and NEVER mention Reddit or YouTube. "
        )
    return (
        f"Generate {n} NEW faceless short-form video topics for a respectful TRUE-CRIME brand. Each video "
        "is a cinematic MICRO-DOC of ONE famous, real, widely-documented case (TikTok / Reels / Shorts).\n"
        "Return ONLY a JSON array (no markdown). Each item EXACTLY this schema:\n"
        f"{json.dumps(EXAMPLE, ensure_ascii=False, indent=2)}\n\n"
        "Rules (PRO editing pipeline depends on these):\n"
        "- Pick a FAMOUS, REAL case: unsolved mysteries, cold cases, famous heists, notorious "
        "disappearances, historic crimes. Widely reported only - no obscure or invented cases.\n"
        "- 'place' = the city/area where it happened, 'country' = country (both REQUIRED - used for the "
        "map pin, must be findable on OpenStreetMap; e.g. 'Boston', 'USA').\n"
        "- EXACTLY 5 or 6 scenes in this order: hook, map, fact, (optional archive), callout, cta. "
        "Each scene 'text' = 1-2 short spoken sentences (serious documentary voice, no gore).\n"
        "- hook: the most gripping TRUE detail, under 14 words. 'hook_top' = the same idea compressed "
        "to MAX 6 punchy words (big kinetic text). Never start with 'Did you know'.\n"
        "- map scene 'text' MUST say where it happened: city + place, accurately.\n"
        "- fact scenes: 'chips' = 1-2 short TRUE fact-chips: {'t': 'MAX 22 CHARS', 'on': 'spoken trigger "
        "word', 'style': 'white'|'accent'}. ONLY widely-documented numbers/years (e.g. '1971', '$500M IN "
        "ART', '13 WORKS STOLEN'); if no reliable number, use a word chip (e.g. 'NEVER FOUND').\n"
        "- archive scene (include ONLY if a real archival image almost certainly exists on Wikimedia "
        "Commons): 'archive_query' = precise Commons search (famous building, wanted poster, aircraft "
        "type, historic photo - e.g. 'Isabella Stewart Gardner Museum', 'Boeing 727 Northwest Orient'), "
        "'archive_label' = short caption (max 26 chars). NEVER use victim photos.\n"
        "- callout scene: 'label' = 2-4 word on-screen label (e.g. 'NEVER RECOVERED'), 'sub' = short "
        "sub-line (max 34 chars), 'label_on' = spoken trigger word.\n"
        "- 'punch' (optional): ONE spoken word where the shot subtly zooms.\n"
        "- EVERY scene except map/archive needs 'query' = cinematic moody stock search (e.g. 'foggy city "
        "night', 'old case files desk', 'vintage police car night', 'rain window night') and 'query2' = "
        "alternative. Concrete, atmospheric, NEVER graphic or violent.\n"
        "- the LAST scene text MUST be exactly: 'Follow for a new cold case every day.'\n"
        "- SAFETY: never name anyone as guilty unless convicted; unsolved stays unsolved; theories AS "
        "theories; respectful to victims; no graphic detail; ACCURACY IS SACRED.\n"
        "- description: MUST begin with '\U0001F4CD <City>, <Country> - <Year>.' then 1-2 gripping TRUE "
        "sentences about the case, then 'Follow for daily cold cases!'\n"
        "- hashtags: 6-9 tags: #truecrime #coldcase #shorts #fyp + 2-3 specific to the case/place.\n"
        "- VARY THE TITLE FORMAT: mix a bold claim, a question and a curiosity gap; do NOT start more "
        "than one in five titles with a number; never clickbait that misleads.\n"
        f"- Do NOT reuse any of these existing titles: {existing_titles}\n"
        f"- Do NOT reuse any of these already-covered cases/places (no repeats, not even reworded): {existing_places}\n"
        + PERFORMANCE + trend_block +
        "Return ONLY the JSON array."
    )


def call_model(user_text):
    r = requests.post(
        BASE.rstrip("/") + "/chat/completions",
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        json={"model": MODEL, "temperature": 0.95,
              "messages": [{"role": "system", "content": SYSTEM},
                           {"role": "user", "content": user_text}]},
        timeout=180,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Models API {r.status_code}: {r.text[:500]}")
    return r.json()["choices"][0]["message"]["content"]


def extract_json(s):
    s = s.strip()
    s = re.sub(r"^```(?:json)?", "", s).strip()
    s = re.sub(r"```$", "", s).strip()
    a, b = s.find("["), s.rfind("]")
    if a != -1 and b != -1:
        s = s[a:b + 1]
    return json.loads(s)


def valid(t):
    """Overi + doopravi NOVY format temy (scenes). Stare/nevalidne temy odmietne."""
    if not isinstance(t, dict) or not t.get("title") or not t.get("place") or not t.get("country"):
        return False
    scenes = t.get("scenes")
    if not isinstance(scenes, list) or not (4 <= len(scenes) <= 7):
        return False
    for sc in scenes:
        if not isinstance(sc, dict) or not sc.get("text"):
            return False
        sc.setdefault("role", "fact")
    roles = [sc["role"] for sc in scenes]
    scenes[0]["role"] = "hook"
    scenes[-1]["role"] = "cta"
    if "map" not in roles:
        return False
    for sc in scenes:
        if sc["role"] == "hook":
            top = re.sub(r"[^A-Za-z0-9' ]", "", str(sc.get("hook_top") or sc["text"]))
            sc["hook_top"] = " ".join(top.split()[:6]).upper()
        if sc["role"] == "archive" and not sc.get("archive_query"):
            sc["role"] = "fact"
        if sc["role"] not in ("map", "archive") and not sc.get("query"):
            sc["query"] = "foggy city night"
        if sc["role"] not in ("map", "archive") and not sc.get("query2"):
            sc["query2"] = "dark cinematic city night"
        if sc["role"] == "fact":
            chips = [c for c in (sc.get("chips") or []) if isinstance(c, dict) and c.get("t")]
            for c in chips:
                c["t"] = str(c["t"])[:24]
            sc["chips"] = chips[:2]
    t.setdefault("description", f"\U0001F4CD {t['place']}, {t['country']}. " + t["title"] + " Follow for daily cold cases!")
    t.setdefault("hashtags", ["#truecrime", "#coldcase", "#shorts", "#fyp"])
    return True


_STOP = {"why", "your", "the", "is", "a", "of", "you", "that", "are", "and", "to", "in",
         "on", "how", "this", "for", "with", "it", "its", "can", "cant", "not", "be", "do",
         "than", "them", "their", "own", "what", "when", "was", "were", "has", "have", "from",
         "more", "most", "just", "every", "an", "as", "or", "but", "so", "hidden", "secret",
         "surprising", "truth", "facts", "fact", "these", "there", "they"}


def _sig(title):
    return set(w for w in re.findall(r"[a-z]+", str(title).lower()) if len(w) > 2 and w not in _STOP)


def _too_similar(sig, existing_sigs):
    if not sig:
        return False
    for es in existing_sigs:
        if not es:
            continue
        inter = len(sig & es)
        if inter >= 3:
            return True
        if inter >= 2 and inter / (len(sig | es) or 1) >= 0.5:
            return True
    return False


def _place_key(t):
    """Normalizovany kluc pripadu: titulok+miesto (ten isty pripad sa NIKDY neopakuje)."""
    if isinstance(t, dict):
        base = str(t.get("place", "")) + " " + str(t.get("title", ""))
    else:
        base = str(t)
    return re.sub(r"[^a-z0-9]+", "", base.lower())[:60]



# --- ANTI-OPAKOVANIE (dedup): po behu odstrani z banky NEPOUZITE temy, ktore su subjektom
# prilis podobne inej teme. Signatura = title+description+hook + cisla/roky; caste niche-slova
# sa auto-ignoruju cez frekvenciu (df). Duale pravidlo: rovnaky ROK + prekrytie = dup;
# rozne roky = rozne pripady; bezrocnove niky -> silna slovna zhoda. Publikovane sa NIKDY nemazu.
_DD_STOP = set("""a an the this that these those and or but so of to in on for with at by from as is are was
were be been being it its you your they them their our we he she his her my me i do does did not no can cant
will just every most more than then there here what when why how who which while into over out up down off only
also very much many some any all if thing things way ways get make made youre follow daily wisdom mindset day
today need needs about like want wants nobody tells tell told never ever still story people world reveal
revealed discover""".split())


def _dd_sig(t):
    first = ""
    if t.get("scenes"):
        first = t["scenes"][0].get("text", "")
    elif t.get("segments"):
        first = t["segments"][0].get("text", "")
    txt = (str(t.get("title", "")) + " " + str(t.get("place", "")) + " "
           + str(t.get("description", "")) + " " + str(first))
    low = txt.lower()
    toks = set(w for w in re.findall(r"[a-z]+", low) if len(w) > 2 and w not in _DD_STOP)
    toks |= set("#" + n for n in re.findall(r"\d{2,}", low))
    return toks


def _dd_years(s):
    return set(w for w in s if len(w) == 5 and w[0] == "#" and w[1] in "12")


def _dd_dup(si, sj):
    common = si & sj
    if len(common) < 3:
        return False
    yi, yj = _dd_years(si), _dd_years(sj)
    yc = yi & yj
    if yi and yj and not yc:
        return False                                   # rozne roky = rozne pripady
    jac = len(common) / (len(si | sj) or 1)
    if yc and len(common) >= 3:
        return True                                    # spolocny rok + prekrytie
    if not (yi or yj) and len(common) >= 4 and jac >= 0.5:
        return True                                    # bezrocnove niky -> silna slovna zhoda
    return False


def _clean_bank():
    """Odstrani NEPOUZITE temy prilis podobne inej teme (ziadne opakovanie videi).
    Publikovane (used_topics) sa nikdy nemazu. Best-effort, nikdy nezhodi denny beh."""
    from collections import Counter
    bank = json.load(open(BANK, encoding="utf-8"))
    used = set(json.load(open(STATE, encoding="utf-8"))) if os.path.exists(STATE) else set()
    raws = [_dd_sig(t) for t in bank]
    df = Counter()
    for s in raws:
        for w in s:
            df[w] += 1
    cutoff = max(2, int(len(bank) * 0.25))             # slovo vo >25% tem = niche-filler -> ignoruj
    sigs = [set(w for w in s if df[w] <= cutoff) for s in raws]
    ks = [s for t, s in zip(bank, sigs) if t.get("title") in used]   # seed: vsetky publikovane
    kept, removed = [], 0
    for t, s in zip(bank, sigs):
        if t.get("title") in used:
            kept.append(t)
            continue
        if s and any(_dd_dup(s, k) for k in ks):
            removed += 1
            continue
        kept.append(t)
        ks.append(s)
    if removed:
        json.dump(kept, open(BANK, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("Dedup: odstranenych %d podobnych nepouzitych tem (ziadne opakovanie)." % removed)
    else:
        print("Dedup: ziadne podobne nepouzite temy.")



def main():
    if not TOKEN:
        print("CHYBA: chyba MODELS_TOKEN/GITHUB_TOKEN"); sys.exit(1)
    bank = json.load(open(BANK, encoding="utf-8"))
    used = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else []
    # MIGRACIA na PRO format: nepouzite temy STAREHO formatu (bez 'scenes') vyrad -
    # ale LEN ak uz mame aspon 3 nove PRO temy (den nikdy neostane bez videi)
    old = [t for t in bank if not t.get("scenes") and t["title"] not in used]
    new_unused = [t for t in bank if t.get("scenes") and t["title"] not in used]
    if old and len(new_unused) >= 3:
        bank = [t for t in bank if t.get("scenes") or t["title"] in used]
        print(f"Migracia: vyradenych {len(old)} nepouzitych tem stareho formatu.")
    titles = {t["title"] for t in bank}
    unused = [t for t in bank if t["title"] not in used]
    need = TARGET - len(unused)
    if need <= 0:
        json.dump(bank, open(BANK, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"Banka OK: {len(unused)} nepouzitych tem."); return
    print(f"Generujem ~{need} novych tem cez {MODEL}...")
    trending = []
    if trends is not None:
        try:
            trending, meta = trends.gather(TREND_SUBREDDITS, TREND_YT_QUERIES, top=18, return_meta=True)
            if trending:
                print(f"Trendy: {len(trending)} titulkov (Reddit={meta['reddit']}, YouTube={meta['youtube']}) -> temy z realneho dopytu.")
        except Exception as e:
            print("Trendy preskocene:", str(e)[:120])
    places = sorted({_place_key(t) for t in bank})
    items = extract_json(call_model(build_prompt(need + 3, sorted(titles), places, trending)))
    added = 0
    existing_sigs = [_sig(x) for x in titles]
    existing_places = {_place_key(t) for t in bank}
    for t in items:
        if not valid(t) or t["title"] in titles:
            continue
        _s = _sig(t["title"])
        if _too_similar(_s, existing_sigs):   # ta ista TEMA (iny nazov) -> preskoc (ziadne opakovanie)
            print("  preskocene (podobna tema):", t["title"]); continue
        pk = _place_key(t)
        if pk and pk in existing_places:
            print("  preskocene (pripad uz bol):", t["title"]); continue
        if t.get("scenes"):
            t["scenes"][-1]["text"] = random.choice(CTAS)  # CTAS_ROTATE: nie vzdy rovnaka veta
        bank.append(t); titles.add(t["title"]); existing_sigs.append(_s); added += 1
        if pk:
            existing_places.add(pk)
    json.dump(bank, open(BANK, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Pridanych {added} tem. Banka ma {len(bank)} tem.")


if __name__ == "__main__":
    main()
    try:
        _clean_bank()
    except Exception as _e:
        print("Dedup preskoceny:", str(_e)[:150])
