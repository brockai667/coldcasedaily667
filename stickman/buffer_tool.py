# -*- coding: utf-8 -*-
"""Sprava fronty Buffera z GitHub Actions (token = secret BUFFER_TOKEN, lokalne nie je).
  python buffer_tool.py list                      - naplanovane posty (id, cas, kanal, zaciatok textu)
  python buffer_tool.py schema                    - nazvy mutacii API (kontrola, ci existuje deletePost)
  python buffer_tool.py delete <id> [<id>...]     - zmaze konkretne posty
  python buffer_tool.py delete-match "<text>"     - zmaze naplanovane posty, ktorych text obsahuje retazec
Token sa nikdy nevypisuje."""
import json
import os
import sys

import requests

API = "https://api.buffer.com"
TOKEN = (os.environ.get("BUFFER_TOKEN") or "").strip()


def gql(query, variables=None):
    r = requests.post(API, headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
                      json={"query": query, "variables": variables or {}}, timeout=60)
    try:
        d = r.json()
    except Exception:
        print("HTTP", r.status_code, r.text[:300])
        return None
    if "errors" in d:
        print("GraphQL chyby:", json.dumps(d["errors"], ensure_ascii=False)[:1500])
    return d.get("data")


def org_id():
    d = gql("query{account{organizations{id name}}}")
    orgs = ((d or {}).get("account") or {}).get("organizations") or []
    if not orgs:
        raise SystemExit("ziadna organizacia (zly token?)")
    return orgs[0]["id"]


def scheduled(org):
    q = ('query($o:OrganizationId!){posts(input:{organizationId:$o, filter:{status:[scheduled,sending]}, '
         'sort:[{field:dueAt,direction:asc}]}){edges{node{id status dueAt text channel{service name}}}}}')
    d = gql(q, {"o": org})
    if d is None or not d.get("posts"):
        # uzsi vyber poli (schema sa moze lisit)
        q = ('query($o:OrganizationId!){posts(input:{organizationId:$o, filter:{status:[scheduled,sending]}, '
             'sort:[{field:dueAt,direction:asc}]}){edges{node{id status dueAt text}}}}')
        d = gql(q, {"o": org}) or {}
    return [e["node"] for e in ((d.get("posts") or {}).get("edges") or [])]


def show(posts):
    if not posts:
        print("fronta je prazdna")
    for p in posts:
        ch = p.get("channel") or {}
        print(f"  {p['id']}  {p.get('dueAt')}  {ch.get('service', '?'):9} {ch.get('name', '')[:22]:22} "
              f"| {(p.get('text') or '').replace(chr(10), ' ')[:70]}")


def delete(ids):
    for pid in ids:
        # nazov/vstup mutacie: pri chybe schema vypise, co API ocakava ('schema' prikaz ukaze nazvy)
        d = gql('mutation($id:PostId!){deletePost(input:{id:$id}){__typename ... on PostActionSuccess{success} '
                '... on MutationError{message}}}', {"id": pid})
        print(f"  delete {pid}: {json.dumps(d, ensure_ascii=False)[:300]}")


def main():
    if not TOKEN:
        raise SystemExit("chyba BUFFER_TOKEN")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "schema":
        d = gql("{__schema{mutationType{fields{name args{name type{name kind ofType{name}}}}}}}") or {}
        names = [f for f in (((d.get("__schema") or {}).get("mutationType") or {}).get("fields") or [])]
        for f in names:
            if "post" in f["name"].lower() or "delete" in f["name"].lower():
                args = ", ".join(f"{a['name']}:{(a['type'].get('name') or (a['type'].get('ofType') or {}).get('name'))}"
                                 for a in f.get("args") or [])
                print(f"  {f['name']}({args})")
        return
    org = org_id()
    posts = scheduled(org)
    print(f"Naplanovane posty: {len(posts)}")
    show(posts)
    if cmd == "delete":
        delete(sys.argv[2:])
    elif cmd == "delete-match":
        needle = " ".join(sys.argv[2:]).strip().lower()
        hit = [p["id"] for p in posts if needle and needle in (p.get("text") or "").lower()]
        print(f"zhoda '{needle}': {len(hit)} postov")
        delete(hit)
        print("po zmazani:")
        show(scheduled(org))


if __name__ == "__main__":
    main()
