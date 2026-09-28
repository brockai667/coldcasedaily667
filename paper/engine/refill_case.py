# -*- coding: utf-8 -*-
"""Doplnenie fronty spisov zadarmo (Groq): kym je vo fronte menej ako --target spisov, napise dalsi z banky tem case/topics.json.
  python engine/refill_case.py [--target 10] [--max 2]
  python engine/refill_case.py --top-up 20      -> doplni banku o N novych, este nepouzitych tem (LLM navrhy, bez duplicit)
  python engine/refill_case.py --list           -> vypise nepouzite temy
Spisy od Groq dostanu nazov 9NN-groq-<slug>.json -> fronta je FIFO podla nazvu, takze Claude-pisane davky (001-899)
maju vzdy prednost a Groq je len zaloha na koniec fronty. Kazdy spis prejde validatorom (CaseComposer) a tema sa oznaci pouzita.
Kluc: GROQ_API_KEY alebo MODELS_TOKEN v env (CI secret), inak FactoryAnim/.env (cita ho engine/llm.py, kluc sa nikdy nevypisuje)."""
import json
import unicodedata
import os
import re
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
FACTORY = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from compose_case import CaseComposer  # noqa: E402
from llm import llm_json  # noqa: E402

CDIR = os.path.join(FACTORY, "case")
QDIR = os.path.join(CDIR, "queue")
DDIR = os.path.join(CDIR, "done")
TOPICS = os.path.join(CDIR, "topics.json")

SYS_WRITE = """You are the head writer of ColdCaseDaily, a faceless channel of 30-40 second vertical shorts styled as a
paper investigation case file: a desk with a lamp and a kraft folder, a corkboard with pinned evidence and red string, and a
night-time diorama of the scene where it happened. Audience: curious teens and adults who like real unexplained mysteries
(ghost ships, vanishings, lights in the sky, ancient artefacts, strange sounds, unexplained events). Facts must be careful
and well documented (Wikipedia-level consensus); use cautious wording ("reportedly", "investigators said", "one theory is");
never present a supernatural explanation as fact; nothing gory, nothing invented, no numbers or studies you are not sure of.

Output ONE JSON object with EXACTLY these keys:
{
 "topic": short case name (ideally under 22 characters, it may be printed on a folder edge),
 "title": full case title, e.g. "The Dyatlov Pass Incident",
 "hook": ONE to two short spoken sentences that hit who/where/when and what does not add up - this plays first,
 "banner": ["ROW1", "ROW2"] - a two-row newspaper headline, UPPERCASE, punchy, each row under 18 characters,
 "site": one of "mountains" | "sea" | "sky" - where the events took place,
 "props": 1-3 props allowed for that site (see SITES below),
 "place": "LOCATION, COUNTRY" (UPPERCASE, under 24 characters),
 "date": "MONTH YEAR" or similar (UPPERCASE, under 24 characters),
 "mood_music": one of "tense" | "wonder" | "calm" | "playful",
 "beats": 4 to 6 beat objects (never more than 7 - see BEATS below),
 "end": {"line": "a short question inviting the viewer's own theory, about 8-12 words", "stamp": "verdict word, under 12 characters, e.g. UNSOLVED / CLASSIFIED / CASE CLOSED"},
 "cta": "COMMENT YOUR THEORY" or similar, UPPERCASE, under 24 characters,
 "description": "one sentence video description",
 "tags": ["#unexplained", "#mystery", ...] - 3 to 5 hashtags,
 "facts": [{"claim": "...", "source": "..."}, ...] - one entry per notable claim used in the beats
}

SITES (site -> allowed props -> allowed "site" fx for shots that happen while the scene is "site"):
 mountains -> props: tent, footprints, trees -> fx: snow, wind, flicker, fog, lightning
 sea       -> props: ship, buoy, rocks       -> fx: waves, fog, lightning, flicker
 sky       -> props: dish, observatory, trees -> fx: beam, flicker, fog

BEATS: each beat is one narrated sentence (8-16 words) plus its visuals:
{"label": short UPPERCASE label under 14 characters, e.g. "THE CASE", "CLUE 1", "CLUE 2", "THE THEORY", "THE TWIST", "THE REPORT", "WITNESS", "EVIDENCE",
 "scene": optional "desk" | "board" | "site" - stays the same as the previous beat if you omit it; the very first beat
   defaults to "board" if omitted; use "site" for atmosphere/scene-setting beats and "board" for evidence beats; change
   scene at most 2-3 times in the whole video,
 "line": the spoken sentence,
 "shots": 1 to 4 visuals, each one of:
   {"t":"card","kind":"photo","icon": one of the ICONS list below,"caption": UPPERCASE under 22 chars,"at": word,"string": true} - only scene "board"
   {"t":"card","kind":"stat","big": under 8 chars e.g. "-30C","9","1959","small": UPPERCASE under 18 chars,"at": word,"string": true} - only "board"
   {"t":"card","kind":"note","lines": 1-3 short UPPERCASE lines, each under 20 chars,"at": word,"string": true} - only "board"
   {"t":"card","kind":"doc","redact": 1-4 integers 0-4 (lines to black out),"at": word,"string": true} - only "board", optional "title" under 16 chars
   {"t":"card","kind":"map","map": a site name,"place": {"x": 0..1, "y": 0..1},"caption": optional UPPERCASE,"at": word} - only "board"
   {"t":"stamp","text": UPPERCASE under 12 chars e.g. "EVIDENCE","CASE CLOSED","at": word} - only "board", needs a card already pinned
   {"t":"focus","at": word,"dur": 0.6-3.0} - only "board", zooms on the last pinned card
   {"t":"fx","fx": one of that site's fx list,"at": word,"dur": seconds} - only while scene is "site"
   {"t":"fx","fx":"flash","at": word} - camera flash, works in any scene
 CRITICAL RULE: every "at" value MUST be a single word copied EXACTLY as spelled in that beat's own "line" (write numbers
 as words in the line, e.g. "minus thirty degrees", so you can anchor "at": "thirty"). Never point "at" to a word that is
 not in that line. Spread the shots of one beat across different words of the line, in the order they should appear.
 The whole video needs AT LEAST 3 "card" shots across all beats combined (5 cards is the maximum - never exceed 5); give
 the second and any later card pinned in the same visit to the board "string": true so it connects to the previous one.

ICONS (use ONLY these, exact spelling, for "kind":"photo"): tent mountain footprints snowflake thermometer radiation
avalanche ship waves lifeboat barrel logbook compass anchor dish printout star stopwatch satellite comet question
magnifier envelope key clock calendar pin eye moon lightning house tree plane report person group lock radio camera skull.

EVERY beat line must carry at least one concrete documented detail (a date, a number, a name, a place, an object); a line that
only describes mood, scenery or weather ("waves crash under a heavy fog") is forbidden. Beat labels in this order: THE CASE, CLUE 1,
CLUE 2, CLUE 3, THEORY, THE TWIST (5-6 beats; THE TWIST = the most surprising documented fact or the latest finding). Give 5-7
entries in "facts". "end"."stamp" is exactly one of UNSOLVED, SOLVED?, CASE CLOSED. The banner must be a punchy two-line headline
(e.g. "NINE HIKERS." / "NO SURVIVORS"), not a vague mood phrase.
Keep the whole spoken script (hook + beats + end line) to about 85-110 words. Only use well-established facts and cite a
real source for each claim in "facts"; if a claim or cause is disputed among researchers, say so instead of stating it as
settled. No medical or dangerous advice, no gore. Output ONE JSON object only, no extra commentary, no markdown fences."""


def norm(t):
    return re.sub(r"[^a-z0-9 ]", "", str(t).lower()).strip()


def slugify(t):
    return re.sub(r"[^a-z0-9]+", "-", str(t).lower()).strip("-")[:40] or "case-file"


def queue_files():
    return sorted(f for f in os.listdir(QDIR) if f.endswith(".json")) if os.path.isdir(QDIR) else []


def next_groq_name(slug):
    nums = [int(m.group(1)) for d in (QDIR, DDIR) for f in (os.listdir(d) if os.path.isdir(d) else [])
            for m in [re.match(r"^(9\d\d)-groq-", f)] if m]
    return f"{(max(nums) + 1) if nums else 900:03d}-groq-{slug[:40]}.json"


def next_case_no():
    """dalsie volne cislo spisu (900+), nekolidujuce s cislami uz pouzitymi vo fronte/hotovych spisoch"""
    used = set()
    for d in (QDIR, DDIR):
        for f in (os.listdir(d) if os.path.isdir(d) else []):
            if f.endswith(".json"):
                try:
                    used.add(str(json.load(open(os.path.join(d, f), encoding="utf-8")).get("case")))
                except Exception:
                    pass
    n = 900
    while str(n) in used:
        n += 1
    return str(n)


# ---------- banka tem (case/topics.json: {"topics": [...], "used": [...]})

def load_bank():
    if os.path.exists(TOPICS):
        return json.load(open(TOPICS, encoding="utf-8"))
    return {"topics": [], "used": []}


def save_bank(bank):
    json.dump(bank, open(TOPICS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def unused(bank):
    return [t for t in bank["topics"] if t not in bank["used"]]


def next_topic():
    bank = load_bank()
    u = unused(bank)
    if not u:
        raise SystemExit("Banka tem case/topics.json je prazdna.")
    return u[0]


def top_up(bank, n):
    """dopyta Groq o n novych, este nepouzitych zahad (bez duplicit podla normalizovaneho nazvu)"""
    have = {norm(t) for t in bank["topics"]}
    sysmsg = ("You suggest famous, well-documented real-world mysteries for a true-crime/paranormal-investigation style "
              "short video series: ghost ships, vanishings, lights in the sky, ancient artefacts, strange sounds, "
              "unexplained events. Never suggest recent tragedies with living relatives, and never frame anything as a "
              'violent crime. Return ONLY JSON: {"topics": ["The ...", ...]}.')
    prompt = (f"Propose {n + 6} NEW, mutually different famous mystery case titles (short noun phrase, 2-6 words, no "
              f"question mark), avoiding anything similar to these existing ones:\n- " + "\n- ".join(bank["topics"][-100:]))
    out = llm_json(sysmsg, prompt, temperature=0.9, max_tokens=2000)
    cand = out.get("topics", []) if isinstance(out, dict) else []
    added = 0
    for t in cand:
        t = str(t).strip().strip('"')
        if not t or norm(t) in have:
            continue
        have.add(norm(t))
        bank["topics"].append(t)
        added += 1
        if added >= n:
            break
    return added


# ---------- pisanie spisu (Groq)

_TR = {"‑": "-", "–": "-", "—": " - ", "‘": "'", "’": "'", "“": '"', "”": '"', " ": " ", "…": "..."}


def _clean(x):
    """Groq pise nezlomitelne pomlcky/uvodzovky -> ASCII (titulky, pisaci stroj, cp1250 konzola)"""
    if isinstance(x, str):
        for k, v in _TR.items():
            x = x.replace(k, v)
        return unicodedata.normalize("NFKC", x)
    if isinstance(x, list):
        return [_clean(v) for v in x]
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    return x


def write_spec(topic):
    """LLM (Groq) napise cely spis pre `topic`; doplni case/slug/voice/rate/cta/end.stamp a overi CaseComposer.validate()
    (case/WRITING_CASE.md). Vracia hotovy dict spisu (nezapisuje na disk - to robi refill())."""
    print(f"[scenarista-spis] {topic}")
    prompt = f"TOPIC: {topic}\nWrite the full case file JSON exactly as specified in the system prompt."
    S = llm_json(SYS_WRITE, prompt, temperature=0.6, max_tokens=9000, effort="medium")   # high effort = truncated JSON (400) na gpt-oss-120b
    S = _clean(S)
    if not isinstance(S, dict):
        raise ValueError("LLM nevratil JSON objekt")
    S.setdefault("topic", topic)
    S["slug"] = slugify(S.get("title") or S.get("topic") or topic)
    S["case"] = next_case_no()
    S["voice"] = "en-GB-RyanNeural"
    S["rate"] = "-4%"
    S.setdefault("cta", "COMMENT YOUR THEORY")
    end = S.get("end")
    end = {"line": end} if isinstance(end, str) else dict(end) if isinstance(end, dict) else {}
    end.setdefault("stamp", "UNSOLVED")
    S["end"] = end
    S["source"] = "groq"                              # spis od bezplatneho modelu -> pred zverejnenim skontrolovat fakty
    C = CaseComposer(json.loads(json.dumps(S)))
    C.validate()
    nb, nc = len(S.get("beats") or []), C.S.get("_cards", 0)
    if C.warn:
        print("   validator:", "; ".join(C.warn)[:300])
    if nb < 5 or nc < 3 or not str(S["end"].get("line") or "").strip():
        raise ValueError(f"slaby spis ({nb} beatov, {nc} kariet)")
    return S


def refill(target=10, maximum=2):
    os.makedirs(QDIR, exist_ok=True)
    bank = load_bank()
    if len(unused(bank)) < 5:
        print("banka tem: doplnam", top_up(bank, 30))
        save_bank(bank)
    made = 0
    while len(queue_files()) < target and made < maximum:
        free = unused(bank)
        if not free:
            print("banka tem je prazdna"); break
        topic = free[0]
        try:
            S = write_spec(topic)
            name = next_groq_name(S["slug"])
            json.dump(S, open(os.path.join(QDIR, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"[fronta] + {name} ({len(S['beats'])} beatov)")
            made += 1
        except Exception as e:
            print(f"   [refill] {topic}: {type(e).__name__}: {str(e)[:160]} -> tema preskocena")
        bank["used"].append(topic)
        save_bank(bank)
    print(f"fronta: {len(queue_files())} spisov (pridane {made})")
    return made


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--top-up" in a:
        n = int(a[a.index("--top-up") + 1])
        bank = load_bank()
        print("doplnene temy:", top_up(bank, n))
        save_bank(bank)
    elif "--list" in a:
        bank = load_bank()
        u = unused(bank)
        print(f"nepouzite temy: {len(u)} / {len(bank['topics'])}")
        for t in u:
            print("  -", t)
    else:
        target = int(a[a.index("--target") + 1]) if "--target" in a else 10
        maximum = int(a[a.index("--max") + 1]) if "--max" in a else 2
        refill(target, maximum)
