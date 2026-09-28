# -*- coding: utf-8 -*-
"""Rychly samotest fabriky bez renderu (na lokal aj CI): syntax kniznic, validator vsetkych scenarov, banka tem.
  python engine/selftest.py            -> 0 = OK, 1 = chyba (vypise co)
Kontroluje: node --check lib/*.js | compose (validator) pre specs/*.json, factory/queue/*.json, factory/done/*.json
| kazdy scenar ma povinne kluce | sceny/recepty zname (compose hlasi varovania) | topics.json ma nepouzite temy."""
import glob
import json
import os
import subprocess
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
FACTORY = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import compose  # noqa: E402
import compose_case  # noqa: E402

errors, warns = [], []

# 1) syntax kniznic
for f in sorted(glob.glob(os.path.join(FACTORY, "lib", "*.js"))):
    r = subprocess.run(["node", "--check", f], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        errors.append(f"node --check {os.path.basename(f)}: {(r.stderr or '').strip()[:200]}")

# 2) validator + compose kazdeho scenara (bez zapisu epizody)
files = sorted(glob.glob(os.path.join(FACTORY, "specs", "*.json")) + glob.glob(os.path.join(FACTORY, "factory", "queue", "*.json")) +
               glob.glob(os.path.join(FACTORY, "factory", "done", "*.json")))
files = [f for f in files if not os.path.basename(f).startswith(("_mx_", "_test_"))]
for f in files:
    try:
        S = json.load(open(f, encoding="utf-8"))
        S.setdefault("slug", os.path.basename(f)[:-5])   # scenare vo fronte dostanu slug az od factory.py
        for k in ("title", "hook", "banner", "env", "beats", "end"):
            if k not in S:
                errors.append(f"{os.path.relpath(f, FACTORY)}: chyba kluc {k}")
        if "hero" not in S and "direction" not in S and "queue" not in f and "done" not in f:
            warns.append(f"{os.path.relpath(f, FACTORY)}: bez hero/direction (doplni ju factory.py)")
        C = compose.Composer(json.loads(json.dumps(S)))
        C.compose()
        for w in C.warn:
            warns.append(f"{os.path.relpath(f, FACTORY)}: {w}")
    except Exception as e:
        errors.append(f"{os.path.relpath(f, FACTORY)}: {type(e).__name__}: {str(e)[:160]}")

# 3) banka tem (len ak repo ma MindBlown fabriku; repo len s papierovymi spismi ma iba case/)
try:
    if not os.path.isdir(os.path.join(FACTORY, "factory")):
        raise StopIteration
    bank = json.load(open(os.path.join(FACTORY, "factory", "topics.json"), encoding="utf-8"))
    free = [t for t in bank.get("topics", []) if t not in bank.get("used", [])]
    if len(free) < 5:
        warns.append(f"topics.json: malo nepouzitych tem ({len(free)}) -> python engine/topics.py --top-up 40")
    q = glob.glob(os.path.join(FACTORY, "factory", "queue", "*.json"))
    if len(q) < 3:
        warns.append(f"fronta: len {len(q)} scenare -> dopisat davku podla factory/WRITING.md")
except StopIteration:
    print("selftest: factory/ chyba -> MindBlown banka tem a fronta preskocene (repo len s case/)")
except Exception as e:
    errors.append(f"topics.json: {e}")

print(f"selftest: {len(files)} scenarov, {len(errors)} chyb, {len(warns)} varovani")
for e in errors:
    print("  CHYBA:", e)
for w in warns:
    print("  varovanie:", w)

# 4) case-spisy (UnexplainedDaily "Paper Case Files"): validator + compose kazdeho spisu (bez zapisu epizody)
errors_case, warns_case = [], []
files_case = sorted(glob.glob(os.path.join(FACTORY, "case", "specs", "*.json")) +
                     glob.glob(os.path.join(FACTORY, "case", "queue", "*.json")) +
                     glob.glob(os.path.join(FACTORY, "case", "done", "*.json")))
files_case = [f for f in files_case if not os.path.basename(f).startswith("_test_")]
for f in files_case:
    try:
        S = json.load(open(f, encoding="utf-8"))
        C = compose_case.CaseComposer(S)
        C.compose()
        for w in C.warn:
            warns_case.append(f"{os.path.relpath(f, FACTORY)}: {w}")
    except Exception as e:
        errors_case.append(f"{os.path.relpath(f, FACTORY)}: {type(e).__name__}: {str(e)[:160]}")

print(f"selftest (case): {len(files_case)} spisov, {len(errors_case)} chyb, {len(warns_case)} varovani")
for e in errors_case:
    print("  CHYBA:", e)
for w in warns_case:
    print("  varovanie:", w)

sys.exit(1 if (errors or errors_case) else 0)
