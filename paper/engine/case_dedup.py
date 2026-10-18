# -*- coding: utf-8 -*-
"""Jeden "kluc spisu" pre ColdCaseDaily: zisti, ci je tema uz hotova / vo fronte (aby sa temy neopakovali).
  case_key("The Flannan Isles Lighthouse Mystery") -> ("flannan", "isles")
Kluc = male pismena bez diakritiky a interpunkcie, bez stopslov (the/mystery/case/disappearance/...), prve 2 vyznamne slova.
Dva kluce sa zhoduju, ak je jeden prefixom druheho (Franklin == Franklin Expedition == Franklin's Lost Expedition).
Pouzivaju to refill_case (banka tem + Groq) aj factory_case (vyber dalsieho spisu z fronty).
  python engine/case_dedup.py            -> samotest kluca + vypis duplicit vo fronte/banke"""
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
FACTORY = os.path.dirname(HERE)
CDIR = os.path.join(FACTORY, "case")
QDIR = os.path.join(CDIR, "queue")
DDIR = os.path.join(CDIR, "done")
RDIR = os.path.join(CDIR, "queue_rejected")      # sem sa presuvaju duplicity (nikdy sa nemaze)
HIST = os.path.join(CDIR, "history.json")
TOPICS = os.path.join(CDIR, "topics.json")

STOP = set("""the a an of in on at to and or for from by with
mystery mysteries case cases file files incident incidents event events
disappearance disappearances disappearing vanishing vanishings vanish vanished
final last lost flight ghost ship ss legend legends hoax hijack hijacking theft heist robbery
expedition search curse story unsolved unexplained strange true famous phenomenon sighting
lights light forest colony""".split())


def case_key(name, n=2):
    """normalizovany kluc nazvu spisu: tuple prvych n vyznamnych slov"""
    t = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"'s\b|\u2019s\b", "", t)              # Earhart's -> earhart
    t = t.replace(".", "")                              # D.B. -> db
    words = re.findall(r"[a-z0-9]+", t)
    sig = [w for w in words if w not in STOP and len(w) > 1]
    if not sig:                                         # samé stopslova -> aspon surove slova
        sig = words
    return tuple(sig[:n])


def same(a, b):
    """kluce sa zhoduju, ak je jeden prefixom druheho"""
    if not a or not b:
        return False
    k = min(len(a), len(b))
    return a[:k] == b[:k]


def spec_keys(S):
    """vsetky kluce jedneho spisu (topic + title; slug len ak nic ine nie je)"""
    names = [S.get("topic"), S.get("title")]
    if not any(names):
        names = [str(S.get("slug") or "").replace("-", " ")]
    return [k for k in (case_key(x) for x in names if x) if k]


def _load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


def _specs(d):
    if not os.path.isdir(d):
        return
    for f in sorted(os.listdir(d)):
        if f.endswith(".json") and not f.startswith(("_test_", "_mx_")):
            S = _load(os.path.join(d, f), None)
            if isinstance(S, dict):
                yield f, S


def published_keys():
    """kluce uz hotovych spisov: case/done + case/history.json"""
    keys = []
    for _, S in _specs(DDIR):
        keys += spec_keys(S)
    for h in _load(HIST, []):
        if isinstance(h, dict):
            keys += spec_keys({"title": h.get("title"), "slug": h.get("slug")})
    return keys


def queue_keys():
    keys = []
    for _, S in _specs(QDIR):
        keys += spec_keys(S)
    return keys


def is_dup(name_or_keys, known):
    """True ak sa nazov (alebo zoznam klucov) zhoduje s niektorym zo `known`"""
    ks = name_or_keys if isinstance(name_or_keys, list) else [case_key(name_or_keys)]
    return any(same(k, o) for k in ks for o in known)


def reject_to_folder(path):
    """presun duplicitneho spisu do case/queue_rejected (nikdy nemazat)"""
    import shutil
    os.makedirs(RDIR, exist_ok=True)
    dst = os.path.join(RDIR, os.path.basename(path))
    shutil.move(path, dst)
    return dst


def clean_bank(bank, known):
    """banka tem: zahodi vnutorne duplicity (nechava prve) a temy zhodne s `known`; `used` ostane podmnozinou topics"""
    seen, out = [], []
    for t in bank.get("topics", []):
        k = case_key(t)
        if is_dup([k], known) or is_dup([k], seen):
            continue
        seen.append(k)
        out.append(t)
    bank["topics"] = out
    bank["used"] = [u for u in bank.get("used", []) if u in out]
    return bank


def _selftest():
    bad = []
    same_sets = [
        ["The Flannan Isles Lighthouse Mystery", "The Flannan Isles", "Flannan Isles"],
        ["Amelia Earhart's Final Flight", "Amelia Earhart", "Amelia Earhart's Last Flight"],
        ["The Tunguska Event", "TUNGUSKA EVENT", "Tunguska"],
        ["The Voynich Manuscript Mystery", "Voynich Manuscript"],
        ["The Phoenix Lights Incident", "The Phoenix Lights", "Phoenix Lights"],
        ["The Rendlesham Forest Incident", "Rendlesham Lights", "Rendlesham Forest"],
        ["D.B. Cooper's Disappearance", "D.B. Cooper hijacking", "D.B. Cooper"],
        ["Glenn Miller's Last Flight", "Glenn Miller disappearance 1944"],
        ["Oak Island's Money Pit", "Oak Island money pit"],
        ["The Roanoke Colony Vanishing", "Roanoke lost colony"],
        ["Franklin's Lost Expedition", "The Franklin Expedition"],
        ["The Hessdalen Lights", "Hessdalen Lights"],
        ["The Baychimo Ghost Ship", "The Ghost Ship SS Baychimo", "SS Baychimo"],
    ]
    diff = [("Flight 19", "Amelia Earhart"), ("Great Train Robbery 1963", "Great Brink's robbery 1950"),
            ("Mary Celeste", "Marfa Lights"), ("The Bermuda Triangle", "The Devil's Sea of Japan"),
            ("Oak Island's Money Pit", "Easter Island's Moai Transport"), ("Nazca Lines", "Antikythera Mechanism")]
    for grp in same_sets:
        for x in grp[1:]:
            if not same(case_key(grp[0]), case_key(x)):
                bad.append(f"mali by sa zhodovat: {grp[0]!r} / {x!r} -> {case_key(grp[0])} vs {case_key(x)}")
    for a, b in diff:
        if same(case_key(a), case_key(b)):
            bad.append(f"nemali by sa zhodovat: {a!r} / {b!r}")
    return bad


if __name__ == "__main__":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    bad = _selftest()
    print("case_key samotest:", "OK" if not bad else f"{len(bad)} chyb")
    for b in bad:
        print("  CHYBA:", b)
    pub = published_keys()
    for f, S in _specs(QDIR):
        if is_dup(spec_keys(S), pub):
            print("  fronta: duplicita hotoveho spisu:", f)
    bank = _load(TOPICS, {"topics": [], "used": []})
    for t in bank["topics"]:
        if is_dup(t, pub):
            print("  banka: uz hotova tema:", t)
    sys.exit(1 if bad else 0)
