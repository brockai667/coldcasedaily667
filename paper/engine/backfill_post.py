# -*- coding: utf-8 -*-
"""Doposlanie uz hotoveho videa na JEDNU platformu (napr. TikTok bol v case denneho behu vypnuty)
a kontrola stavu kanala v Bufferi. Spusta sa z workflow paper-case-backfill.yml - token je len
v GitHub secrets (env BUFFER_TOKEN) a nikdy sa nevypisuje.

  python paper/engine/backfill_post.py status <sluzba>
  python paper/engine/backfill_post.py post <video-bez-pripony> <sluzba> [--delay MIN] [--dir PRIECINOK]

pushed.json sa nemeni: video je tam uz oznacene ako vybavene, preto ho denny beh znova neposle."""
import datetime
import json
import os
import sys

import requests

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))          # koren repozitara (push_to_buffer.py, config.json)
sys.path.insert(0, ROOT)
import push_to_buffer as pb  # noqa: E402

SERVICES = ("tiktok", "instagram", "youtube")
CHANNEL_WANT = ("id", "name", "displayName", "service", "isDisconnected", "isLocked", "isQueuePaused")
POST_WANT = ("id", "status", "dueAt", "sentAt", "channelId", "externalLink")
PLAIN = ("SCALAR", "ENUM")


def channel_for(cfg, service):
    for c in cfg.get("buffer_channels") or []:
        if str(c.get("service", "")).lower() == service:
            return c
    raise SystemExit(f"CHYBA: v configu nie je kanal pre '{service}'")


def plain_fields(token, typename):
    """Nazvy jednoduchych poli typu (introspekcia); [] ak ju API nepovoli - vtedy sa pouzije minimum."""
    try:
        q = 'query{__type(name:"%s"){fields{name type{kind ofType{kind}}}}}' % typename
        out = []
        for f in (pb.gql(token, q).get("__type") or {}).get("fields") or []:
            t = f.get("type") or {}
            if t.get("kind") in PLAIN or (t.get("ofType") or {}).get("kind") in PLAIN:
                out.append(f["name"])
        return out
    except Exception:
        return []


def enum_values(token, typename):
    try:
        q = 'query{__type(name:"%s"){enumValues{name}}}' % typename
        return [v["name"] for v in (pb.gql(token, q).get("__type") or {}).get("enumValues") or []]
    except Exception:
        return []


def short(e):
    """Prve riadky chyby bez dlhych vypisov (odpoved API token neobsahuje)."""
    return " ".join(str(e).split())[:220]


def show_channel(token, ch):
    have = plain_fields(token, "Channel")
    fields = [f for f in CHANNEL_WANT if f in have] or ["id", "name", "service"]
    try:
        c = pb.gql(token, 'query{channel(input:{id:"%s"}){%s}}' % (ch["id"], " ".join(fields)))["channel"]
    except Exception as e:
        print(f"  kanal sa neda precitat: {short(e)}")
        return None
    info = {k: v for k, v in c.items() if k != "id"}
    print(f"  kanal {ch['id'][:8]}…: " + json.dumps(info, ensure_ascii=False))
    if c.get("isDisconnected") or c.get("isLocked"):
        print("  POZOR: kanal je odpojeny alebo zamknuty - treba ho v Bufferi znova pripojit")
    return c


def show_posts(token, ch, limit=6):
    have = plain_fields(token, "Post")
    fields = [f for f in POST_WANT if f in have] or ["id", "status", "dueAt"]
    known = enum_values(token, "PostStatus")
    want = [s for s in ("sent", "error", "sending", "scheduled") if not known or s in known]
    tpl = ('query{posts(input:{organizationId:"%s", filter:{status:[%s]%s}, '
           'sort:[{field:dueAt,direction:desc}]}){edges{node{%s}}}}')
    try:
        org = pb.gql(token, "query{account{organizations{id}}}")["account"]["organizations"][0]["id"]
        try:
            edges = pb.gql(token, tpl % (org, ",".join(want), ', channelIds:["%s"]' % ch["id"], " ".join(fields)))["posts"]["edges"]
        except Exception:                      # filter podla kanala API nepozna -> vsetky a vyber podla channelId
            edges = pb.gql(token, tpl % (org, ",".join(want), "", " ".join(fields)))["posts"]["edges"]
            if "channelId" in fields:
                edges = [e for e in edges if e["node"].get("channelId") == ch["id"]]
    except Exception as e:
        print(f"  prispevky sa nedaju precitat: {short(e)}")
        return
    print(f"  prispevky kanala (najnovsie, {min(limit, len(edges))} z {len(edges)}):")
    for e in edges[:limit]:
        n = e["node"]
        n["id"] = str(n.get("id", ""))[:8] + "…"
        print("   ", json.dumps(n, ensure_ascii=False))


def find_file(base, name):
    for d, _dirs, files in os.walk(base):
        if name in files:
            return os.path.join(d, name)
    return None


def hosted_url(cfg, video, mp4):
    """Video uz lezi v release 'media' z denneho behu - pouzi ho; inak ho nahraj (ak je subor poruke)."""
    repo = os.environ.get("GITHUB_REPOSITORY") or cfg.get("gh_repo") or ""
    url = f"https://github.com/{repo}/releases/download/media/{video}.mp4"
    try:
        if repo and requests.head(url, allow_redirects=True, timeout=30).status_code == 200:
            print("  [host] video uz je v release -> " + url)
            return url
    except Exception:
        pass
    if not mp4:
        raise SystemExit("CHYBA: video nie je v release ani v priecinku - nie je co poslat")
    return pb.host_video(cfg, mp4)


def post(cfg, token, video, service, delay, base):
    ch = channel_for(cfg, service)
    txt = find_file(base, video + ".txt")
    if not txt:
        raise SystemExit(f"CHYBA: {video}.txt sa nenasiel v '{base}' (popis videa)")
    title, body = pb.read_txt(txt)
    if not title or not body:
        raise SystemExit("CHYBA: popis videa je prazdny")
    url = hosted_url(cfg, video, find_file(base, video + ".mp4"))
    due = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=delay)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    promo = cfg.get("promo_yt", "") if service == "youtube" else cfg.get("promo_social", "")
    q, use_title = pb.build_mutation(service)
    v = {"channelId": ch["id"], "text": body + promo, "url": url, "dueAt": due}
    if use_title:
        v["title"] = (title + " #shorts")[:100] if service == "youtube" else title
    print(f"=== {video} -> {service} ({ch.get('name', '')}) | cas {due}")
    show_channel(token, ch)
    try:
        res = pb.gql(token, q, v)["createPost"]
    except Exception as e:
        print(f"  [{service}] CHYBA: {short(e)}")
        return 1
    if res.get("message"):
        print(f"  [{service}] CHYBA: {short(res['message'])}")
        return 1
    print(f"  [{service}] do fronty OK (prispevok {str((res.get('post') or {}).get('id', ''))[:8]}…)")
    return 0


def main():
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ("status", "post"):
        print(__doc__)
        return 1
    service = (a[1] if a[0] == "status" else (a[2] if len(a) > 2 else "")).lower()
    if service not in SERVICES:
        print("CHYBA: sluzba musi byt jedna z: " + ", ".join(SERVICES))
        return 1
    cfg = pb.load_cfg()
    token = (cfg.get("buffer_token") or "").strip()
    if not token:
        print("CHYBA: chyba BUFFER_TOKEN")
        return 1
    if a[0] == "status":
        ch = channel_for(cfg, service)
        print(f"=== stav: {service} ({ch.get('name', '')})")
        show_channel(token, ch)
        show_posts(token, ch)
        return 0
    delay = int(a[a.index("--delay") + 1]) if "--delay" in a else 10
    base = a[a.index("--dir") + 1] if "--dir" in a else os.path.join(ROOT, "output")
    return post(cfg, token, a[1], service, max(5, delay), base)


if __name__ == "__main__":
    sys.exit(main())
