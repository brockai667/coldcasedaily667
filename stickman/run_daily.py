#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Denny beh stickman fabriky (ColdCase): tema -> pribeh (storyboard_v3) -> video -> Buffer.

    python stickman/run_daily.py              # cely retazec vratane publikovania
    python stickman/run_daily.py --dry-run    # vyrobi video a skonci, nic nepublikuje
    python stickman/run_daily.py --topic "The Somerton Man"   # konkretna tema (test)

Pravidla:
  * Tema sa presuva do `used` az PO uspesnom publikovani. Zlyhanie = nenulovy kod, tema ostava v banke.
  * storyboard_v3 konci kodom 3 (clanok prilis kratky) alebo 2 (pribeh ma problemy / slaby kritik):
    v oboch pripadoch sa tema PRESKOCI (ide do `skipped`), nepublikuje sa nic slabe; skusia sa max 3 temy.
  * Hosting + Buffer presne ako zvysok tejto fabriky (push_to_buffer.py), jeden prispevok denne
    o STICKMAN_SLOT_LOCAL (predvolene 12:00 Europe/Bratislava).
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, REPO)

TOPICS = os.path.join(ROOT, "topics.json")
OUT = os.path.join(ROOT, "out")
SPECS = os.path.join(ROOT, "specs")
STATE = os.path.join(ROOT, "published.json")

MUSIC_CREDIT = ('Music: "Sneaky Snitch" by Kevin MacLeod (incompetech.com), '
                "licensed under Creative Commons: By Attribution 3.0")
HASHTAGS_DEFAULT = "#truecrime #coldcase #unsolved #mystery #shorts"
SLOT_LOCAL = os.environ.get("STICKMAN_SLOT_LOCAL", "12:00")     # HH:MM, Europe/Bratislava


def log(msg):
    print(msg, flush=True)


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def slugify(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


# ------------------------------------------------------------------ 1) tema
def pick_topic(bank, forced=None):
    if forced:
        return forced
    used = {u.strip().lower() for u in bank.get("used", [])} | {u.strip().lower() for u in bank.get("skipped", [])}
    # rucne vybrane temy maju prednost; `auto` (z Wikipedie cez topics_from_wiki.py) az ked sa minu
    for t in list(bank.get("topics", [])) + list(bank.get("auto", [])):
        if t.strip().lower() not in used:
            return t
    return None


# ------------------------------------------------------------------ 2) pribeh
class TopicSkip(Exception):
    """Tema sa neda spracovat na dobru epizodu (kratky clanok, problemy v pribehu) - preskoci sa, nie je to zlyhanie."""


def make_spec(topic):
    """storyboard_v3.py ako podproces (najprv pribeh, potom zabery; vlastne kola s kritikom).
    Kod 3 = clanok prilis kratky, kod 2 = ostali problemy alebo slaby pribeh -> tema sa preskoci."""
    slug = slugify(topic)
    path = os.path.join(SPECS, slug + ".json")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "storyboard_v3.py"), topic, "--show"],
                       cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1"),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    log(((r.stdout or "") + (r.stderr or "")).strip()[-3000:])
    if r.returncode in (2, 3):
        raise TopicSkip("%s (kod %d)" % (topic, r.returncode))
    if r.returncode != 0:
        raise RuntimeError("storyboard zlyhal (kod %s)" % r.returncode)
    if not os.path.exists(path):
        raise RuntimeError("storyboard nevyrobil spec: " + path)
    spec = load_json(path, {})
    if len(spec.get("lines", [])) < 8:
        raise RuntimeError("spec ma len %d viet" % len(spec.get("lines", [])))
    return path, spec


# ------------------------------------------------------------------ 3) video
def make_video(spec_path):
    import build_spec
    total, slug = build_spec.build(spec_path)
    mp4 = os.path.join(OUT, slug + ".mp4")
    if not os.path.exists(mp4):
        raise RuntimeError("render nevyrobil " + mp4)
    lo = getattr(build_spec, "MIN_LEN", 24.0)
    hi = getattr(build_spec, "MAX_LEN", 34.0)
    if not (lo - 4.0 <= total <= hi + 1.0):
        raise RuntimeError("dlzka %.2f s mimo rozsahu" % total)
    return mp4, slug, total


def loop_check(mp4, slug):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "loopcheck.py"), mp4,
                        os.path.join(OUT, slug + "_loop.jpg")],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    log(out[-600:])
    if "slucka sedi" not in out:
        raise RuntimeError("slucka nesedi - video by v kanale blikalo")


# ------------------------------------------------------------------ 4) texty
def build_text(spec, cfg):
    """Titulok = spec["title"]. Popis zacina zaverecnou otazkou (otvara komentare), potom hashtagy a kredit hudby."""
    title = (spec.get("title") or spec.get("topic") or "Cold Case").strip()
    lines = spec.get("lines", [])
    question = ""
    for l in reversed(lines):
        say = (l.get("say") or "").strip()
        if say.endswith("?"):
            question = say
            break
    if not question and lines:
        question = (lines[-1].get("say") or "").strip()
    tags = cfg.get("brand_hashtags") if isinstance(cfg, dict) else None
    hashtags = " ".join(tags[:8]) if tags else HASHTAGS_DEFAULT
    if "#shorts" not in hashtags:
        hashtags += " #shorts"
    body = "\n\n".join(x for x in (question, hashtags, MUSIC_CREDIT) if x)
    return title, body


def write_sidecar(mp4, title, body):
    """Rovnaky format ako cita push_to_buffer.read_txt: 1. riadok titulok, zvysok popis."""
    with open(mp4[:-4] + ".txt", "w", encoding="utf-8") as f:
        f.write(title + "\n" + body + "\n")


# ------------------------------------------------------------------ 5) publikovanie
def next_slot():
    """Najblizsi buduci den o SLOT_LOCAL (Europe/Bratislava) -> ISO UTC pre Buffer (customScheduled)."""
    from zoneinfo import ZoneInfo
    tz = ZoneInfo("Europe/Bratislava")
    hh, mm = (SLOT_LOCAL.split(":") + ["0"])[:2]
    now = datetime.datetime.now(tz)
    for day in range(0, 3):
        t = (now + datetime.timedelta(days=day)).replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
        if t > now + datetime.timedelta(minutes=15):
            return t.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return (now + datetime.timedelta(hours=1)).astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def publish(mp4, title, body, cfg):
    """Hosting + Buffer presne tak, ako to robi zvysok fabriky (push_to_buffer.py)."""
    import push_to_buffer as P
    token = (cfg.get("buffer_token") or "").strip()
    if not token:
        raise RuntimeError("chyba buffer_token (BUFFER_TOKEN secret)")
    targets = cfg.get("buffer_channels") or []
    if not targets:
        targets = [c for c in P.get_channels(token)
                   if c.get("service", "").lower() in getattr(P, "WANT_SERVICES", ("youtube", "instagram", "tiktok"))]
    if not targets:
        raise RuntimeError("ziadne cielove kanaly")

    log("  [host] nahravam video...")
    url = P.host_video(cfg, mp4) if hasattr(P, "host_video") else P.upload_cloudinary(cfg, mp4)
    due = next_slot()
    log("  [buffer] planujem na %s UTC -> %s" % (due, ", ".join(c["service"] for c in targets)))

    yt_title = (title + " #shorts")[:100]
    ok_services, fails = [], []
    for c in targets:
        svc = c["service"].lower()
        t = yt_title if svc == "youtube" else title
        promo = cfg.get("promo_yt", "") if svc == "youtube" else cfg.get("promo_social", "")
        ok, msg = P.create_post(token, svc, c["id"], body + (promo or ""), url, t, due)
        log(("  [buffer] %-10s OK" % svc) if ok else ("  [buffer] %-10s CHYBA: %s" % (svc, str(msg)[:200])))
        (ok_services if ok else fails).append(svc)
    if not ok_services:
        raise RuntimeError("Buffer odmietol vsetky kanaly: " + "; ".join(fails))

    pushed = P.load_pushed()
    name = os.path.basename(mp4)
    pushed[name] = sorted(set(pushed.get(name, [])) | set(ok_services))
    P.save_pushed(pushed)
    return url, due, ok_services, fails


# ------------------------------------------------------------------ hlavny retazec
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="vyrob video, nepublikuj")
    ap.add_argument("--topic", default=None, help="konkretna tema namiesto banky")
    ap.add_argument("--spec", default=None, help="hotovy spec JSON - preskoci generovanie pribehu (test/rerun)")
    a = ap.parse_args()

    bank = load_json(TOPICS, {"used": [], "topics": []})
    if a.spec:
        spec_path = os.path.abspath(a.spec)
        spec = load_json(spec_path, {})
        topic = spec.get("topic") or os.path.basename(spec_path)
        a.topic = topic                      # hotovy spec = konkretna tema, banka sa nemeni
        log("=== SPEC: %s%s ===" % (spec_path, "  (dry-run)" if a.dry_run else ""))
    for _ in range(0 if a.spec else 3):
        topic = pick_topic(bank, a.topic)
        if not topic:
            log("Banka tem je prazdna - nic na vyrobu.")
            return 0
        log("=== TEMA: %s%s ===" % (topic, "  (dry-run)" if a.dry_run else ""))
        try:
            spec_path, spec = make_spec(topic)
            break
        except TopicSkip as e:
            log("  [spec] preskakujem: %s" % e)
            if a.topic:
                return 3
            bank.setdefault("skipped", []).append(topic)
            bank["topics"] = [t for t in bank.get("topics", []) if t != topic]
            bank["auto"] = [t for t in bank.get("auto", []) if t != topic]
            save_json(TOPICS, bank)
    else:
        if not a.spec:
            raise RuntimeError("tri temy za sebou sa nedali spracovat")
    log("  [spec] %s  (%d viet, world=%s, hero=%s, speed=%s, kritik=%s)"
        % (spec.get("title"), len(spec["lines"]), spec.get("world"), spec.get("hero"), spec.get("speed"),
           spec.get("critic")))

    import push_to_buffer as P
    cfg = P.load_cfg()
    mp4, slug, total = make_video(spec_path)
    loop_check(mp4, slug)
    title, body = build_text(spec, cfg)
    write_sidecar(mp4, title, body)
    log("  [video] %s  %.2f s" % (mp4, total))
    log("  [text ] %s | %s" % (title, body.split("\n")[0]))

    if a.dry_run:
        log("DRY-RUN: video hotove, nepublikujem, temu v banke nechavam.")
        return 0

    url, due, ok_services, fails = publish(mp4, title, body, cfg)

    if not a.topic:
        bank.setdefault("used", []).append(topic)
        bank["topics"] = [t for t in bank.get("topics", []) if t != topic]
        bank["auto"] = [t for t in bank.get("auto", []) if t != topic]
        save_json(TOPICS, bank)
    state = load_json(STATE, {"runs": []})
    state["runs"].append({"date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
                          "topic": topic, "slug": slug, "title": title, "seconds": round(total, 2),
                          "due": due, "url": url, "services": ok_services, "failed": fails,
                          "look": spec.get("look_used")})
    state["runs"] = state["runs"][-120:]
    save_json(STATE, state)
    log("HOTOVO: %s -> %s (%s)" % (title, ", ".join(ok_services), due))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
        if code:
            log("ZLYHANIE (kod %s) - tema ostava v banke." % code)
        sys.exit(code)
    except Exception:
        traceback.print_exc()
        log("ZLYHANIE - tema ostava v banke, zajtra sa skusi znova.")
        sys.exit(1)
