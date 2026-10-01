# -*- coding: utf-8 -*-
"""Reziser-kompilator pre papierovy spis (UnexplainedDaily, "Paper Case Files"): spec -> episodes/<slug>/episode.json + script.js.
  python engine/compose_case.py case/specs/<slug>.json            -> len epizoda
  python engine/compose_case.py case/specs/<slug>.json --snap 1,5  -> + build + snimky
  python engine/compose_case.py case/specs/<slug>.json --render    -> + build + render (out/<slug>.mp4)
Spec (case/CONTRACT.md sekcia 3, navod case/WRITING_CASE.md): topic, slug, title, case, hook, banner[2], site, props[], place, date,
  music|mood_music, voice, rate, beats[{label, scene?, line, shots[{t: card|stamp|focus|fx, at?, ...}]}], end{line, stamp}, cta,
  description, tags[], facts[]. Kniznice: core.js, fx.js, env_case.js (PF.envCase), cards_case.js (PF.cards); build.py sa nemeni.
Nezname veci validator opravi alebo zahodi (nic nespadne); varovania vypise na konci."""
import json
import os
import re
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")   # Windows: presmerovany vystup je cp1250
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
FACTORY = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import compose  # noqa: E402
from compose import norm, words, js, MUSIC, MOOD_MUSIC, music_vol, music_credit  # noqa: E402

# ---------- slovnik spisu (case/CONTRACT.md)
SCENES = ("desk", "board", "site")
SITES = {   # variant miesta cinu -> (props, fx sceny site)
    "mountains": (("tent", "footprints", "trees"), ("snow", "wind", "flicker", "fog", "lightning")),
    "sea": (("ship", "buoy", "rocks"), ("waves", "fog", "lightning", "flicker")),
    "sky": (("dish", "observatory", "trees"), ("beam", "flicker", "fog")),
}
SITE_ALIAS = {"mountain": "mountains", "snow": "mountains", "ocean": "sea", "water": "sea", "space": "sky", "stars": "sky"}
PROPS0 = {"mountains": ["tent", "footprints"], "sea": ["ship"], "sky": ["dish"]}
FX_ALL = {f for v in SITES.values() for f in v[1]} | {"flash", "magnify"}
KINDS = ("photo", "stat", "note", "doc", "map")
ICONS = set(("tent mountain footprints snowflake thermometer radiation avalanche ship waves lifeboat barrel logbook compass anchor dish "
             "printout star stopwatch satellite comet question magnifier envelope key clock calendar pin eye moon lightning house tree "
             "plane report person group lock radio camera skull "
             "diamond moneybag painting train car briefcase handcuffs fingerprint safe mask coin book parachute bones"   # heisty, zmiznutia (28.9.)
           ).split())
LIM = {"banner": 18, "label": 14, "caption": 22, "big": 8, "small": 18, "note": 20, "stamp": 12, "sheet": 24, "cta": 24, "folder": 22, "doc": 16}
MAX_CARDS, MAX_SHOTS, MAX_BEATS = 5, 4, 7
CHROME_SFX = dict(compose.CHROME_SFX, file=("tick.wav", 0.9))   # zvuk nadpisu beatu v chrome file (compose.py sa nemeni)
KIT = {"chrome": "file", "trans": "page", "pres": "full", "cam": "calm"}
LIBS = ["core.js", "fx.js", "env_case.js", "cards_case.js"]
# kolko s zaber drzi nastenku: dalsi zaber pocka a pred prepnutim sceny sa stihne dokoncit
BUSY = {"card": 0.55, "string": 1.0, "redact": 1.05, "stamp": 0.3, "focus": 1.45, "magnify": 1.0, "flash": 0.35, "site": 0.5}
STAMP_ROT = (-8, 7, -5, 9, -11, 6)
SAFE = re.compile(r"^[\"'(\[]*[A-Za-z]{3,}[\"')\].,!?;:]*$")   # slovo vhodne na kotvu bez `at` (TTS ho vrati samostatne)


def txt(v):
    """bezpecny text: bez znakov, ktore rozbiju HTML/SVG markup"""
    if v is None or isinstance(v, (bool, dict, list)):
        return ""
    return re.sub(r"\s+", " ", re.sub(r"[<>\\]", "", str(v)).replace("&", "+")).strip()


def up(v):
    return txt(v).upper()


def num(v, d, lo, hi):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return d
    return d if x != x else round(max(lo, min(hi, x)), 2)


def toks(line):
    """povodne tokeny vety, ktore su slovom (rovnake poradie ako words(line))"""
    return [t for t in str(line).split() if norm(t)]


def plus(base, x):
    """JS vyraz base + x (konstanty zlucene: T.b2 - 0.45)"""
    x = round(x, 2)
    return base if not x else f"{base} + {x:g}" if x > 0 else f"{base} - {-x:g}"


class CaseComposer(compose.Composer):
    # ---------- pomocne: texty
    def cut(self, where, s, n):
        """orez na n znakov (radsej na hranici slova) + varovanie"""
        if len(s) <= n:
            return s
        c = s[:n + 1]
        c = (c.rsplit(" ", 1)[0] if " " in c else c)[:n].rstrip(" ,;:-") or s[:n]
        self.warn.append(f"{where}: '{s}' ma viac nez {n} znakov -> '{c}'")
        return c

    def wrap(self, where, v, n, rows):
        """riadky poznamky: zalomenie po slovach na <= n znakov, max rows riadkov"""
        src = v if isinstance(v, list) else str(v if v is not None else "").split("\n")
        out = []
        for ln in src:
            cur = ""
            for w in up(ln).split():
                if cur and len(cur) + 1 + len(w) > n:
                    out.append(cur)
                    cur = w
                else:
                    cur = (cur + " " + w).strip()
            if cur:
                out.append(cur)
        if len(out) > rows:
            self.warn.append(f"{where}: {len(out)} riadkov > {rows} -> orezane")
            out = out[:rows]
        return [self.cut(where, x, n) for x in out] or ["?"]

    # ---------- pomocne: kotvy slov (rovnaky tvar ako Composer.anchor)
    def word(self, key, line, i):
        """kotva na i-te slovo vety -> (i, JS vyraz, sfx kotva)"""
        ws = words(line)
        w, nth = ws[i], ws[:i].count(ws[i])
        return i, f'at("{key}", "{w}"' + (f", {nth})" if nth else ")"), f"{key}:{w}" + (f"#{nth}" if nth else "")

    def near(self, line, i, lo=0):
        """index vhodneho slova (pismena, >= 3 znaky) najblizsie k i, nie pred lo"""
        tk = toks(line)
        lo = max(0, min(lo, len(tk) - 1))
        i = max(lo, min(int(i), len(tk) - 1))
        for j in sorted(range(lo, len(tk)), key=lambda j: (abs(j - i), -j)):
            if SAFE.match(tk[j]):
                return j
        return i

    def spec_at(self, key, line, at):
        """slovo `at` zo spec -> (i, JS, sfx) alebo None (slovo vo vete nie je -> bez kotvy, rovnomerne)"""
        if at is None or isinstance(at, (bool, list, dict)) or not str(at).strip():
            return None
        w, _, nth = str(at).strip().partition("#")
        if not norm(w):
            self.warn.append(f"{key}: kotva '{at}' nie je slovo")
            return None
        a = self.anchor(key, line, f"{w}#{nth if re.fullmatch(r'[0-9]{1,2}', nth) else 0}")
        if not a:
            return None
        m = re.match(r'at\("[^"]*", "([a-z0-9]+)"(?:, (\d+))?\)', a[0])
        hits = [j for j, x in enumerate(words(line)) if x == m.group(1)]
        return self.word(key, line, hits[min(int(m.group(2) or 0), len(hits) - 1)])

    def spread(self, b, shots):
        """cas zaberu = slovo vety (`at`, inak rovnomerne po slovach); chronologicke poradie, dva zabery nie na jednom slove"""
        k, line = b["key"], b["line"]
        ws = words(line)
        n = len(ws)
        lo = (2 if n >= 5 else 1 if n >= 3 else 0) if b["_switch"] else 0   # po prepnuti sceny az ked prechod odide
        for j, sh in enumerate(shots):
            a = self.spec_at(k, line, sh.get("at"))
            if a is None:
                i = self.near(line, round((j + 0.5) / len(shots) * (n - 1)), lo)
            elif a[0] >= lo:
                i = a[0]
            else:                                         # slovo pod prechodom -> jeho dalsi vyskyt, inak prve slovo po prechode
                i = next((x for x in range(lo, n) if ws[x] == ws[a[0]]), None)
                i = self.near(line, lo, lo) if i is None else i
            sh["_pos"], sh["_ord"] = i, j
        shots.sort(key=lambda s: (s["_pos"], s["_ord"]))
        for j, sh in enumerate(shots):
            if j and sh["_pos"] <= shots[j - 1]["_pos"]:
                sh["_pos"] = min(shots[j - 1]["_pos"] + 1, n - 1)
            sh["_at"] = self.word(k, line, sh["_pos"])

    # ---------- validacia a doplnenie spec
    def card_ok(self, k, sc, sh):
        W = self.warn.append
        kind = str(sh.get("kind") or "").lower()
        if kind not in KINDS:
            g = "stat" if sh.get("big") else "note" if sh.get("lines") else "doc" if sh.get("redact") else "map" if sh.get("map") else "photo"
            W(f"{k}: neznamy kind '{sh.get('kind')}' -> {g}")
            kind = g
        if sc != "board":
            W(f"{k}: karta {kind} v scene {sc} (len board) -> zahodena")
            return None
        w = f"{k} {kind}"
        o = {"t": "card", "kind": kind, "at": sh.get("at"), "string": sh.get("string") in (True, 1, "true", "yes")}
        if kind == "photo":
            ic = str(sh.get("icon") or "").lower()
            if ic not in ICONS:
                W(f"{k}: neznama ikona '{sh.get('icon')}' -> question")
                ic = "question"
            o["icon"], o["caption"] = ic, self.cut(w, up(sh.get("caption")), LIM["caption"])
        elif kind == "stat":
            o["big"] = self.cut(w, up(sh.get("big")), LIM["big"]) or "?"
            o["small"] = self.cut(w, up(sh.get("small")), LIM["small"])
        elif kind == "note":
            o["lines"] = self.wrap(w, sh.get("lines") or sh.get("text") or sh.get("caption") or "?", LIM["note"], 3)
        elif kind == "doc":
            rd = sh.get("redact") if isinstance(sh.get("redact"), list) else []
            o["redact"] = sorted({int(i) for i in rd if isinstance(i, (int, float)) and not isinstance(i, bool) and 0 <= i <= 4})[:4]
            if len(o["redact"]) < len(rd):
                W(f"{w}: redact = indexy riadkov 0-4, max 4 -> {o['redact']}")
            if txt(sh.get("title")):
                o["title"] = self.cut(w, up(sh.get("title")), LIM["doc"])
        else:                                             # map: vrstevnice/pobrezie + cerveny kriz na place {x, y} v 0..1
            m = str(sh.get("map") or "").lower()
            m = SITE_ALIAS.get(m, m)
            o["map"] = m if m in SITES else self.S["site"]
            p = sh.get("place")
            x, y = (p.get("x"), p.get("y")) if isinstance(p, dict) else (p[0], p[1]) if isinstance(p, (list, tuple)) and len(p) >= 2 else (None, None)
            o["place"] = {"x": num(x, 0.6, 0.08, 0.92), "y": num(y, 0.45, 0.08, 0.92)}
            if txt(sh.get("caption")):
                o["caption"] = self.cut(w, up(sh.get("caption")), LIM["caption"])
        return o

    def shot_ok(self, b, sh):
        """jeden zaber zo spec -> normalizovany dict, alebo None (+ varovanie)"""
        k, sc, W = b["key"], b["_scene"], self.warn.append
        if not isinstance(sh, dict):
            W(f"{k}: zaber {sh!r} nie je objekt -> preskakujem")
            return None
        t = str(sh.get("t") or sh.get("type") or "").lower()
        if t in KINDS:                                    # {"t": "photo"} = karta photo
            sh, t = dict(sh, kind=sh.get("kind") or t), "card"
        elif t in FX_ALL:                                 # {"t": "flash"} = fx flash
            sh, t = dict(sh, fx=sh.get("fx") or t), "fx"
        elif not t:
            t = "card" if sh.get("kind") else "fx" if sh.get("fx") else "stamp" if sh.get("text") else ""
        t = {"pin": "card", "evidence": "card", "zoom": "focus"}.get(t, t)
        at = sh.get("at")
        if t == "card":
            return self.card_ok(k, sc, sh)
        if t in ("stamp", "focus") and sc != "board":
            W(f"{k}: {t} v scene {sc} (len board) -> preskakujem")
            return None
        if t == "stamp":
            return {"t": "stamp", "at": at, "text": self.cut(f"{k} stamp", up(sh.get("text")), LIM["stamp"]) or "EVIDENCE"}
        if t == "focus":
            return {"t": "focus", "at": at, "dur": num(sh.get("dur"), 1.2, 0.6, 3.0)}
        if t == "fx":
            f = str(sh.get("fx") or "").lower()
            if f == "flash":
                return {"t": "fx", "fx": f, "at": at}
            if f == "magnify":
                if sc == "site":
                    W(f"{k}: magnify v scene site (len board/desk) -> preskakujem")
                    return None
                return {"t": "fx", "fx": f, "at": at, "dur": num(sh.get("dur"), 1.6, 0.6, 4.0)}
            if f in SITES[self.S["site"]][1]:
                if sc != "site":
                    W(f"{k}: fx {f} v scene {sc} (len site) -> preskakujem")
                    return None
                return {"t": "fx", "fx": f, "at": at, "dur": num(sh.get("dur"), None, 0.5, 15.0)}
            W(f"{k}: nezname fx '{sh.get('fx')}' pre site {self.S['site']} -> preskakujem")
            return None
        W(f"{k}: nezname t '{sh.get('t') or sh.get('type')}' -> preskakujem")
        return None

    def validate(self):
        S, W = self.S, self.warn.append
        # ---------- hlavicka
        S["title"] = txt(S.get("title")) or txt(S.get("topic")) or "Case File"
        S["topic"] = txt(S.get("topic")) or S["title"]
        slug = str(S.get("slug") or "")
        if not re.match(r"^[A-Za-z0-9_-]{1,80}$", slug):
            new = re.sub(r"[^a-z0-9]+", "-", (slug or S["title"]).lower()).strip("-")[:60] or "case-file"
            if slug:
                W(f"slug '{slug}' -> '{new}'")
            slug = new
        S["slug"] = slug
        S["hook"] = txt(S.get("hook"))
        if not words(S["hook"]):
            W("chyba hook -> title")
            S["hook"] = S["title"] + "."
        bn = S.get("banner")
        bn = [bn] if isinstance(bn, str) else bn if isinstance(bn, list) else []
        bn = [self.cut("banner", up(x), LIM["banner"]) for x in bn if up(x)]
        if len(bn) > 2:
            W("banner ma viac nez 2 riadky -> prve 2")
        if not bn:
            W("chyba banner -> z title")
            bn = [self.cut("banner", up(S["title"]), LIM["banner"])]
        S["banner"] = (bn + [""])[:2]
        c = re.sub(r"[^0-9A-Za-z-]", "", str(S.get("case") or ""))[:5].upper()
        S["case"] = c or f"{sum(map(ord, slug)) % 900 + 100:03d}"
        site = str(S.get("site") or "").lower()
        site = SITE_ALIAS.get(site, site)
        if site not in SITES:
            if S.get("site"):
                W(f"nezname site '{S.get('site')}' -> mountains")
            site = "mountains"
        S["site"] = site
        props = S.get("props")
        props = [props] if isinstance(props, str) else props if isinstance(props, list) else PROPS0[site]
        for p in props:
            if p not in SITES[site][0]:
                W(f"prop '{p}' nie je v site {site} ({', '.join(SITES[site][0])}) -> preskakujem")
        S["props"] = list(dict.fromkeys(p for p in props if p in SITES[site][0]))
        S["place"] = self.cut("place", up(S.get("place")), LIM["sheet"])
        S["date"] = self.cut("date", up(S.get("date")), LIM["sheet"])
        S["folder"] = self.cut("folder", up(S.get("folder") or S["topic"]), LIM["folder"])
        if not (isinstance(S.get("voice"), str) and re.match(r"^[a-z]{2,3}-[A-Z]{2,3}-\w+$", S["voice"])):
            if S.get("voice"):
                W(f"neplatny voice '{S.get('voice')}' -> en-GB-RyanNeural")
            S["voice"] = "en-GB-RyanNeural"
        if not (isinstance(S.get("rate"), str) and re.match(r"^[+-][0-9]{1,2}%$", S["rate"])):
            if S.get("rate"):
                W(f"neplatny rate '{S.get('rate')}' -> -4%")
            S["rate"] = "-4%"
        if not (isinstance(S.get("mood_music"), str) and S["mood_music"] in MOOD_MUSIC):
            if S.get("mood_music"):
                W(f"nezname mood_music '{S.get('mood_music')}' -> tense")
            S["mood_music"] = "tense"
        if S.get("music") and not (isinstance(S["music"], str) and S["music"] in MUSIC):
            W(f"neznama music '{S.get('music')}' -> podla mood_music")
            S["music"] = None
        # ---------- beaty
        raw = S.get("beats") if isinstance(S.get("beats"), list) else []
        beats = []
        for i, b in enumerate(raw):
            if isinstance(b, dict) and words(txt(b.get("line"))):
                beats.append(b)
            else:
                W(f"beat {i + 1}: chyba veta (line) -> preskakujem")
        if len(beats) > MAX_BEATS:
            W(f"{len(beats)} beatov > {MAX_BEATS} -> orezane")
            beats = beats[:MAX_BEATS]
        if not beats:
            W("ziadny platny beat -> nahradny")
            beats = [{"label": "THE CASE", "line": "The file on this case is still open.", "shots": []}]
        S["beats"] = beats
        prev = "desk"                                     # hook je vzdy stol
        for bi, b in enumerate(beats):
            k = b["key"] = f"b{bi + 1}"
            b["line"] = txt(b["line"])
            b["label"] = self.cut(f"{k} label", up(b.get("label")), LIM["label"]) or ("THE CASE" if bi == 0 else f"CLUE {bi}")
            sc = str(b.get("scene") or "").lower()
            if sc and sc not in SCENES:
                W(f"{k}: nezname scena '{b.get('scene')}' -> bez zmeny")
                sc = ""
            sc = sc or (prev if bi else "board")         # scena plati od beatu dalej; prvy beat = board
            b["_scene"], b["_switch"] = sc, sc != prev
            prev = sc
            src = b.get("shots")
            src = [src] if isinstance(src, dict) else src if isinstance(src, list) else []
            shots = [x for x in (self.shot_ok(b, sh) for sh in src) if x]
            if len(shots) > MAX_SHOTS:
                W(f"{k}: {len(shots)} zaberov > {MAX_SHOTS} -> orezane")
                shots = shots[:MAX_SHOTS]
            self.spread(b, shots)
            b["shots"] = shots
        # ---------- chronologicky cez cele video: max 5 kariet, snurka a focus potrebuju predoslu kartu, fx miesta raz za navstevu
        nc, run_fx = 0, set()
        for b in beats:
            keep = []
            if b["_switch"]:
                run_fx = set()
            for sh in b["shots"]:
                if sh["t"] == "fx" and sh["fx"] not in ("flash", "magnify"):
                    if sh["fx"] in run_fx:
                        W(f"{b['key']}: fx {sh['fx']} uz bezi v tejto scene site -> preskakujem (dlhsie = dur)")
                        continue
                    run_fx.add(sh["fx"])
                if sh["t"] == "card":
                    if nc >= MAX_CARDS:
                        W(f"{b['key']}: karta {sh['kind']} navyse -> zahodena (max {MAX_CARDS} kariet na video)")
                        continue
                    if sh["string"] and not nc:
                        W(f"{b['key']}: snurka pri prvej karte nema kam viest -> bez snurky")
                        sh["string"] = False
                    sh["ci"] = nc
                    nc += 1
                elif sh["t"] == "focus" and not nc:
                    W(f"{b['key']}: focus bez pripnutej karty -> preskakujem")
                    continue
                keep.append(sh)
            b["shots"] = keep
            est = 0.38 * len(words(b["line"])) + 0.55     # odhad dlzky beatu (s)
            use = sum(self.need(sh) for sh in keep) + (0.5 if b["_switch"] else 0)
            if keep and use > est:
                W(f"{b['key']}: zabery (~{use:.1f} s) sa do vety (~{est:.1f} s) asi nezmestia -> menej zaberov alebo dlhsia veta")
        S["_cards"] = nc
        # ---------- koniec
        end = S.get("end")
        end = {"line": end} if isinstance(end, str) else dict(end) if isinstance(end, dict) else {}
        end["line"] = txt(end.get("line"))
        if not words(end["line"]):
            W("chyba end.line -> nahradna otazka")
            end["line"] = "What do you think really happened?"
        end["stamp"] = self.cut("end.stamp", up(end.get("stamp")), LIM["stamp"]) or "UNSOLVED"
        S["end"] = end
        cta = S.get("cta")
        S["cta"] = "" if cta is False else (self.cut("cta", up(cta), LIM["cta"]) or "COMMENT YOUR THEORY")

    # ---------- casy a zabery
    def need(self, sh):
        """kolko s zaber potrebuje na dokoncenie (pred prepnutim sceny / dalsim zaberom)"""
        if sh["t"] == "card":
            return BUSY["redact"] if sh["kind"] == "doc" and sh.get("redact") else BUSY["string"] if sh["string"] else BUSY["card"]
        if sh["t"] == "fx":
            return BUSY.get(sh["fx"], BUSY["site"])
        return BUSY[sh["t"]]

    def switch_after(self, beats, bi):
        """(JS zaklad, posun) prepnutia sceny hned po beate bi, alebo None"""
        if bi + 1 < len(beats):
            return (f'T.{beats[bi + 1]["key"]}', 0.05) if beats[bi + 1]["_switch"] else None
        return ("T.end", -0.3) if beats[bi]["_scene"] != "board" else None

    def run_end(self, beats, bi):
        """(JS zaklad, posun) konca aktualnej sceny = najblizsie prepnutie po beate bi"""
        for b in beats[bi + 1:]:
            if b["_switch"]:
                return f'T.{b["key"]}', 0.05
        return ("T.end", -0.3) if beats[-1]["_scene"] != "board" else ("T.end", 0)

    def shots(self, beats, bi, scene):
        """zabery beatu (uz chronologicky); vracia pocet novych prvkov nastenky"""
        E, b = self.emit, beats[bi]
        k, lst = b["key"], b["shots"]
        nxt = f'T.{beats[bi + 1]["key"]}' if bi + 1 < len(beats) else "T.end"
        # strop kazdeho zaberu (odzadu): vsetko sa stihne pred prepnutim sceny, kamera / lupa spat do konca beatu
        caps, room = [None] * len(lst), self.switch_after(beats, bi)
        for j in reversed(range(len(lst))):
            r = room or ((nxt, 0) if lst[j]["t"] == "focus" or lst[j].get("fx") == "magnify" else None)
            if r:
                caps[j] = room = (r[0], round(r[1] - self.need(lst[j]), 2))
        tgt = [f"Math.min({sh['_at'][1]}, {plus(*caps[j])})" if caps[j] else sh["_at"][1] for j, sh in enumerate(lst)]
        free = f"T.{k} + 0.5" if b["_switch"] else None   # po prechode sceny / po predoslom zabere
        added = 0
        for j, sh in enumerate(lst):
            v, sfx = f"T.{k}_{j + 1}", sh["_at"][2]
            E(f"{v} = " + (f"Math.max({tgt[j]}, {free})" if free else tgt[j]) + ";")   # predosly zaber ma prednost
            lim = tgt[j + 1] if j + 1 < len(lst) else nxt   # dalsi zaber alebo dalsi beat
            free = plus(v, self.need(sh))
            if sh["t"] == "card":
                n = sh["ci"] + 1
                c, cid = f"C{n}", f"cd{n}"
                o = {"id": cid, "kind": sh["kind"]}
                o.update({x: sh[x] for x in ("icon", "caption", "big", "small", "lines", "redact", "title", "map", "place") if x in sh})
                E(f"var {c} = PF.cards.make({js(o)[:-1]}, slot: env.slot({sh['ci']}) }});")
                E(f"{c}.pin({v}); BOARD.push({c}.id || {js(cid)});")
                self.fx("paper.wav", sfx, 0, 0.55)
                self.fx("pinpush.wav", sfx, 0.42, 0.8)
                typed = len(str(sh.get("caption") or "")) + len(str(sh.get("small") or "")) + sum(len(str(x)) for x in (sh.get("lines") or []))
                for i in range(min(10, -(-typed // 3))):   # pisaci stroj: klik na kazde 3. pismeno (26 zn/s od +0.62)
                    self.fx("typekey.wav", sfx, round(0.62 + i * 0.115, 3), 0.5)
                added += 1
                if sh["string"] and self.last:
                    E(f"BOARD.push(PF.cards.string({self.last}, {c}, {v} + 0.5, 0.45));   // cervena snurka od predoslej karty")
                    self.fx("stringzip.wav", sfx, 0.5, 0.7)
                    added += 1
                if sh["kind"] == "doc" and sh["redact"]:
                    E(f"{c}.redact({v} + 0.9);")
                    self.fx("thud.wav", sfx, 0.9, 0.35)
                self.last = c
                self.last_kind = sh["kind"]
            elif sh["t"] == "stamp":
                rot = STAMP_ROT[self.nst % len(STAMP_ROT)]
                self.nst += 1
                SP = {"photo": (10, -60, 0.7), "doc": (10, 30, 0.7), "map": (20, -40, 0.65), "stat": (-110, -120, 0.55), "note": (-100, -150, 0.55)}
                dx, dy, size = SP.get(getattr(self, "last_kind", "photo"), SP["photo"])   # peciatka na obrazku / v rohu karty, nie cez text
                pos, size = (f"{self.last}.x + {dx}, {self.last}.y + {dy}", size) if self.last else ("540, 900", 1)
                E(f"BOARD.push(PF.cards.stamp({js(sh['text'])}, {pos}, {v}, {{ rot: {rot}, size: {size} }}));")
                self.fx("stampslam.wav", sfx, 0, 0.75)
                added += 1
            elif sh["t"] == "focus":                      # na poslednu kartu, spat skor nez pride dalsi zaber / beat
                u = f"{v}u"
                E(f"{self.last}.focus({v}, 0.5); {u} = Math.max({v} + 0.8, Math.min({v} + {sh['dur']}, {lim} - 0.55)); "
                  f"{self.last}.unfocus({u}, 0.5);")
                free = f"{u} + 0.5"
            elif sh["fx"] == "magnify":                   # lupa na poslednu kartu (board) alebo na harok (desk)
                xy = f"{self.last}.x + 30, {self.last}.y - 20" if scene == "board" and self.last else "540, 1000" if scene == "desk" else "540, 900"
                u = f"{v}u"
                E(f"{u} = Math.max({v} + 0.8, Math.min({v} + {sh['dur']}, {lim} - 0.3)); PF.cards.magnify({xy}, {v}, {u});")
                free = f"{u} + 0.1"
            elif sh["fx"] == "flash":
                E(f"PF.cards.flash({v});   // blesk fotoaparatu")
                self.fx("shutter.wav", sfx, 0, 0.7)
            else:                                         # fx miesta cinu, len kym trva scena site
                base, off = self.run_end(beats, bi)
                t1 = f"Math.min({plus(v, sh['dur'])}, {plus(base, off - 0.3)})" if sh["dur"] else plus(base, off - 0.3)
                E(f"env.siteFx({js(sh['fx'])}, {v}, Math.max({v} + 0.5, {t1}));")
        return added

    # ---------- vystup
    def compose(self):
        S = self.S
        self.validate()
        beats, end = S["beats"], S["end"]
        self.last, self.nst = None, 0                    # posledna pripnuta karta (JS premenna), pocet peciatok
        lines = {"hook": S["hook"]}
        for b in beats:
            lines[b["key"]] = b["line"]
        lines["end"] = end["line"]

        E = self.emit
        E(f"// AUTO z compose_case.py: {S['title']}  (spis #{S['case']}, site {S['site']}, kit file/page/full/calm)")
        E('var at = PF.at, s0 = function (k) { return PF.seg(k)[0]; }, TT = PF.VO.total;')
        E("var env = PF.envCase(" + js({"scene": "desk", "site": S["site"], "props": S["props"], "caseNo": S["case"], "title": S["folder"], "stamp": S.get("stamp") or "TOP SECRET"}) + ");")
        E('if (!document.getElementById("du0")) PF.fx.dust(16, 314, "#ffe2b0");   // prach vo svetle lampy (ak ho nespravilo prostredie)')
        E("var BOARD = [];   // prvky nastenky (karty, snurky, peciatky): pri odchode zo sceny board sa skryju, pri navrate ukazu")
        E('function boardVis(on, t) { BOARD.forEach(function (id) { if (id && document.getElementById(id)) PF.S("#" + id, { opacity: on ? 1 : 0 }, t); }); }')
        E("var T = {};")
        E('T.tot = TT; T.b1 = s0("b1"); T.end = s0("end");')
        for b in beats[1:]:
            E(f'T.{b["key"]} = s0("{b["key"]}");')

        # ---------- HOOK
        E("\n// ===== HOOK: stol, fascikel sa otvori, pisaci stroj (prvy snimok = posledny)")
        E('PF.CAM(1.07, 540, 940, 0, T.b1 - 0.05, "sine.inOut");   // pomaly najazd')
        E("env.folder(true, 0.35);")
        E(f'env.sheet({js([x for x in (S["date"], S["place"], "STATUS: OPEN") if x])}, 0.7);')
        tt = 0.7                                          # kliky pisacieho stroja k harku (22 zn/s, medzera 0.18 s medzi riadkami)
        for ln in [x for x in (S["date"], S["place"], "STATUS: OPEN") if x]:
            for i in range(-(-len(ln) // 3)):
                self.fx("typekey.wav", "t:0", round(tt + i * 3 / 22, 3), 0.45)
            tt += len(ln) / 22 + 0.18
        E('PF.O("#hook", 1, 0, T.b1 - 0.25, 0.22);')

        # ---------- BEATY
        cur, nb = "desk", 0                               # aktualna scena, pocet prvkov na nastenke
        for bi, b in enumerate(beats):
            k = b["key"]
            E(f"\n// ===== {b['label']}: {b['line']}")
            self.fx(CHROME_SFX["file"][0], k, 0.02, CHROME_SFX["file"][1])
            self.fx("paper.wav", k, 0.03, 0.5)
            if bi == 0:
                E(f'PF.O("#day", 0, 1, T.{k}, 0.05);')
            E(f'PF.DAY({js(b["label"])}, T.{k});')
            if b["_switch"]:
                sw = f"T.{k} + 0.05"
                E(f'env.scene({js(b["_scene"])}, {sw});')
                self.fx("paper.wav", k, -0.25, 0.6)
                if b["_scene"] == "site":
                    self.fx("swell.wav", k, -0.25, 0.3)
                if nb and cur == "board":
                    E(f"boardVis(false, {sw});   // nastenka odchadza")
                if nb and b["_scene"] == "board":
                    E(f"boardVis(true, {sw});   // navrat na nastenku")
                if bi == 0:
                    E(f"PF.CAM(1, 540, 960, {sw}, 0);   // kamera spat na celok (pod prechodom)")
                cur = b["_scene"]
            elif bi == 0:
                E(f'PF.CAM(1, 540, 960, T.{k}, 0.6, "sine.inOut");')
            nb += self.shots(beats, bi, cur)

        # ---------- KONIEC: verdikt na nastenke
        E(f"\n// ===== KONIEC: {end['line']}")
        if cur != "board":
            E('env.scene("board", T.end - 0.3);' + (" boardVis(true, T.end - 0.3);" if nb else ""))
            self.fx("paper.wav", "end", -0.55, 0.6)
        _, a2, s2 = self.word("end", end["line"], min(1, len(words(end["line"])) - 1))
        E(f"T.e1 = Math.max({a2}, T.end + 0.2);")
        E('PF.DAY("VERDICT", T.end);')
        self.fx("tick.wav", "end", 0.02, 0.9)
        E(f'PF.cards.stamp({js(end["stamp"])}, 540, 1000, T.e1, {{ size: 1.7, rot: -12 }});   // verdikt')
        self.fx("stampslam.wav", s2, 0, 0.9)
        self.fx("reveal_tone.wav", "end", 0, 0.5)

        # ---------- SLUCKA: vsetko spat do stavu snimku 0
        wl = words(end["line"])
        last, lastn = wl[-1], wl.count(wl[-1]) - 1
        E("\n// ===== SLUCKA: spat na stol, fascikel sa zatvori (snimok T.tot = snimok 0)")
        E(f'var tc = Math.min(at("end", "{last}", {lastn}, "e") + 0.9, T.tot - 1.3);')
        if S["cta"]:
            E(f'PF.CTA({js(S["cta"])}, T.end + 0.6, tc - 0.05);')
        E('PF.O("#day", 1, 0, tc, 0.3);')
        E("PF.cards.clear(tc);")
        E('env.scene("desk", tc + 0.15); PF.CAM(1, 540, 960, tc + 0.15, 0);')
        E("env.folder(false, tc + 0.55);")
        E("env.lamp(1, tc + 0.55, 0.3);")
        E('PF.O("#hook", 0, 1, T.tot - 0.8, 0.4);')

        # ---------- episode.json (rovnaky kontrakt ako compose.py)
        pool = MOOD_MUSIC[S["mood_music"]]
        mkey = S["music"] if S.get("music") else pool[int(num(S.get("music_i"), 0, 0, 99)) % len(pool)]
        mf, mat, mname = MUSIC[mkey]
        mf = os.path.join(FACTORY, "assets", "music", mf)
        tags = [x for x in S["tags"] if isinstance(x, str)] if isinstance(S.get("tags"), list) else []
        ep = {
            "title": S["title"], "hook": S["banner"], "voice": S["voice"], "rate": S["rate"], "gap": 0.55, "tail": 1.6,
            "bg": "#2a1c16", "accent": "#c9382d", "kit": dict(KIT), "libs": list(LIBS),
            "description": (str(S.get("description") or "") + "\n" + " ".join(tags)).strip(),
            "music": {"file": mf, "at": mat, "vol": music_vol(mf, mat),
                      "credit": music_credit(mname)},
            "lines": lines, "sfx": self.sfx}
        return ep, "\n".join(self.js) + "\n"


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("-"):
        print(__doc__)
        sys.exit(2)
    spec_path = os.path.abspath(sys.argv[1])
    try:
        with open(spec_path, encoding="utf-8-sig") as f:
            S = json.load(f)
    except (OSError, ValueError) as e:
        print("compose_case: spec sa neda nacitat:", spec_path, "|", e)
        sys.exit(1)
    if not isinstance(S, dict):
        print("compose_case: spec musi byt JSON objekt")
        sys.exit(1)
    C = CaseComposer(S)
    ep, script = C.compose()
    d = os.path.join(FACTORY, "episodes", S["slug"])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "episode.json"), "w", encoding="utf-8") as f:
        json.dump(ep, f, ensure_ascii=False, indent=1)
    with open(os.path.join(d, "script.js"), "w", encoding="utf-8") as f:
        f.write(script)
    print("compose_case ok:", S["slug"], "|", len(S["beats"]), "beatov |", S["_cards"], "kariet |", len(ep["sfx"]), "sfx |",
          "varovania:", C.warn or "ziadne")
    if "--snap" in sys.argv:
        i = sys.argv.index("--snap")
        times = sys.argv[i + 1] if i + 1 < len(sys.argv) else "0,2,6,10,14,18"
        subprocess.run([sys.executable, os.path.join(HERE, "snap.py"), d, times])
    elif "--render" in sys.argv:
        subprocess.run([sys.executable, os.path.join(HERE, "build.py"), d, "--render"])
    return d


if __name__ == "__main__":
    main()
