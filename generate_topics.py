#!/usr/bin/env python3
"""Doplni banku tem cez GitHub Models (zadarmo). Nika: TRUE CRIME / cold cases (bezpecne, faktualne)."""
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

# Nika: TRUE CRIME / cold cases -> kde ludia realne diskutuju / co pozeraju
TREND_SUBREDDITS = ['TrueCrime', 'UnresolvedMysteries', 'ColdCases', 'serialkillers', 'Casefile']
TREND_YT_QUERIES = ['true crime cold case', 'unsolved mystery case', 'famous heist']

SYSTEM = ("You are a scriptwriter for a respectful TRUE-CRIME / cold-case brand. You retell FAMOUS, "
          "widely-documented cases (heists, disappearances, unsolved mysteries, historic cases) in a "
          "serious documentary voice. STRICT SAFETY RULES: (1) ACCURACY IS SACRED - only real, "
          "widely-reported facts; never invent details, names, dates or motives. (2) NEVER accuse or name "
          "any person as guilty unless they were actually convicted; for unsolved cases say it remains "
          "unsolved. (3) Be RESPECTFUL to victims - no graphic, gory or gratuitous detail, no "
          "sensationalizing suffering. (4) Prefer older, famous, well-documented cases; avoid recent cases "
          "involving private individuals. (5) Present theories AS theories, never as fact. "
          "You output strict JSON, nothing else. THE HOOK (the very first line / segment 1) is the single most important thing in the whole video: it MUST stop the scroll within 2 seconds. Make it concrete and specific (a number, a name, a vivid image, or a sharp contradiction) and open a curiosity gap that can ONLY be closed by watching to the end. Lead with the most shocking part FIRST, never a slow setup. Forbidden hook openers: 'Did you know', 'Have you ever', 'Imagine', 'Here are', 'In this video', 'Let me tell you'.")

EXAMPLE = {
    "title": "The Man Who Vanished With $200,000",
    "segments": [
        {"text": "In 1971, a man calling himself D.B. Cooper hijacked a passenger plane.", "keywords": "vintage airplane sky"},
        {"text": "He demanded two hundred thousand dollars and four parachutes.", "keywords": "cash money stack"},
        {"text": "After releasing the passengers, he got his money.", "keywords": "airport night runway"},
        {"text": "Then, somewhere over the forests, he jumped from the plane.", "keywords": "dark forest aerial"},
        {"text": "He was never found, and the case remains unsolved to this day.", "keywords": "foggy forest trees"},
        {"text": "A man who vanished into the night, and into legend.", "keywords": "cloudy mountain sky"},
        {"text": "Follow for cases the world never forgot.", "keywords": "old case files"},
    ],
    "description": "In 1971 D.B. Cooper hijacked a plane, jumped out with the ransom, and was never found. Follow for daily cold cases!",
    "hashtags": ["#truecrime", "#dbcooper", "#unsolved", "#coldcase", "#mystery", "#shorts", "#fyp", "#casefiles"],
}


import random  # CTAS_ROTATE

CTAS = [
    "Follow for a new cold case every day.",
    "Follow if you'd have cracked this one.",
    "Follow for the cases that were never solved.",
    "Follow for daily true crime mysteries.",
    "Follow because some cases still need answers.",
]


def build_prompt(n, existing_titles, trending=None):
    trend_block = ""
    if trending:
        joined = chr(10).join("- " + t for t in trending)
        trend_block = (
            " WHAT REAL PEOPLE DISCUSS AND WATCH THIS WEEK (live headlines from Reddit communities and "
            "top YouTube videos in this niche - what the audience actually cares about right now): " + joined +
            " Let at least HALF of the new topics be directly inspired by a SPECIFIC item above, turned "
            "into a strong hook that STILL follows the style and safety rules described. Do NOT copy any "
            "headline word-for-word, and NEVER mention Reddit or YouTube. "
        )
    return (
        f"Generate {n} NEW faceless short-form video topics for a respectful TRUE-CRIME / COLD-CASE brand "
        "(TikTok / Reels / YouTube Shorts).\n"
        "Focus: FAMOUS, widely-documented cases - daring heists, mysterious disappearances, unsolved "
        "historic cases, real cases that gripped the world. Mostly older / well-known.\n"
        "Return ONLY a JSON array (no markdown). Each item EXACTLY this schema:\n"
        f"{json.dumps(EXAMPLE, ensure_ascii=False, indent=2)}\n\n"
        "SAFETY RULES (critical):\n"
        "- ACCURACY IS SACRED: only real, widely-reported facts. NEVER invent names, dates, details or motives.\n"
        "- NEVER call anyone guilty unless they were actually convicted. For unsolved cases, say it stays unsolved.\n"
        "- RESPECT victims: no graphic, gory or gratuitous detail; never sensationalize suffering.\n"
        "- Prefer famous older cases; avoid recent crimes involving private individuals.\n"
        "- Present theories AS theories, never as fact.\n\n"
        "Style rules (make it PRO and gripping):\n"
        "- title: punchy and curiosity-driven, e.g. 'The Heist That Was Never Solved', 'The Plane That Vanished'.\n"
        "- 6 to 9 segments. Segment 1 is THE HOOK: a gripping true line under 14 words. Never start with 'Did you know'.\n"
        "- build the story line by line; write for a deep, serious documentary SPOKEN voiceover: short clear sentences.\n"
        "- each segment 'keywords': 1-3 ENGLISH words for real Pexels footage that VISUALLY MATCHES the line "
        "(e.g. 'foggy city night', 'old case files', 'empty road night', 'vintage police car', 'dark forest'). "
        "Cinematic and concrete, NEVER graphic or violent.\n"
        "- the SECOND-TO-LAST segment loops back to the opening hook so a rewatch feels seamless.\n"
        "- the LAST segment text MUST be exactly: 'Follow for cases the world never forgot.'\n"
        "- description: one sentence ending with 'Follow for daily cold cases!'.\n"
        "- Occasionally (about a third of the time) add ONE subtle fitting emoji at the very END of the "
        "description (e.g. 🔍, 🕯️, 🗂️). Emoji ONLY in the description text, NEVER inside any segment 'text'.\n"
        "- hashtags: 6-8 tags including #truecrime #coldcase #shorts #fyp.\n"
        "- VARY THE TITLE FORMAT: do NOT start more than one in five titles with a number "
        "(avoid the repetitive 'N things' pattern). Mix a bold claim, a question, a "
        "'why/how' angle and a curiosity gap so titles never look the same.\n"
        f"- Do NOT reuse any of these existing titles: {existing_titles}\n"
        "- Do NOT repeat the same SUBJECT, fact or concept as any existing title above, even reworded, "
        "renumbered or from a different angle. Every topic must be a genuinely DIFFERENT idea.\n"
        + trend_block +
        "STORYBOARD (visual directing, IMPORTANT): to EVERY segment ADD a field 'visual' = an object choosing HOW to visualize exactly what that line SAYS (never generic): {\"type\":\"kenburns\",\"prompt\":\"LITERAL ENGLISH image prompt naming ONE concrete, instantly recognizable subject/scene that depicts exactly what the line says (a real thing a camera could photograph; NEVER abstract, NEVER metaphors)\"} for normal lines; {\"type\":\"counter\",\"target\":1000,\"suffix\":\"x\",\"label\":\"3-4 WORD CAPTION\"} when the line contains a big number; {\"type\":\"compare\",\"small_prompt\":\"...\",\"big_prompt\":\"...\",\"small_label\":\"X\",\"big_label\":\"Y\",\"stat\":\"300x\"} for size/amount comparisons; {\"type\":\"callouts\",\"prompt\":\"subject image\",\"labels\":[\"SHORT LABEL\"]} to point at parts of a subject; {\"type\":\"lineup\",\"items\":[{\"name\":\"A\",\"prompt\":\"...\"}]} for listing 3-5 things; {\"type\":\"arrow\",\"from_prompt\":\"...\",\"to_prompt\":\"...\",\"label\":\"WHAT MOVES\"} for movement/flow. First segment gets {\"type\":\"hook\",\"prompt\":\"dramatic scene image\",\"big\":\"SHORT PUNCHY QUESTION OR CLAIM (max 5 words)\"}; last segment {\"type\":\"cta\",\"prompt\":\"iconic subject of the video\"}. Labels MUST describe what the narration says at that moment - never invent unrelated text. Image prompts must AVOID human faces and hands (AI renders them poorly) - prefer objects, anatomy, environments, close-up details; the subject must FILL the frame and be well lit. Return ONLY the JSON array."
    )


def call_model(user_text):
    r = requests.post(
        BASE.rstrip("/") + "/chat/completions",
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        json={"model": MODEL, "temperature": 0.85,
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
    if not isinstance(t, dict) or "title" not in t or "segments" not in t:
        return False
    if not isinstance(t["segments"], list) or len(t["segments"]) < 4:
        return False
    for seg in t["segments"]:
        if "text" not in seg or "keywords" not in seg:
            return False
    t.setdefault("description", t["title"] + " Follow for daily cold cases!")
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


def main():
    if not TOKEN:
        print("CHYBA: chyba MODELS_TOKEN/GITHUB_TOKEN"); sys.exit(1)
    bank = json.load(open(BANK, encoding="utf-8"))
    used = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else []
    titles = {t["title"] for t in bank}
    unused = [t for t in bank if t["title"] not in used]
    need = TARGET - len(unused)
    if need <= 0:
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
    items = extract_json(call_model(build_prompt(need + 3, sorted(titles), trending)))
    added = 0
    existing_sigs = [_sig(x) for x in titles]
    for t in items:
        if not valid(t) or t["title"] in titles:
            continue
        _s = _sig(t["title"])
        if _too_similar(_s, existing_sigs):   # ta ista TEMA (iny nazov) -> preskoc (ziadne opakovanie)
            print("  preskocene (podobna tema):", t["title"]); continue
        if t.get("segments"):
            t["segments"][-1]["text"] = random.choice(CTAS)  # CTAS_ROTATE: nie vzdy rovnaka veta
        bank.append(t); titles.add(t["title"]); existing_sigs.append(_s); added += 1
    json.dump(bank, open(BANK, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Pridanych {added} tem. Banka ma {len(bank)} tem.")


if __name__ == "__main__":
    main()
