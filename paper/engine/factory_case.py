# -*- coding: utf-8 -*-
"""Cela case-fabrika (UnexplainedDaily, "Paper Case Files") jednym prikazom -> out/<slug>.mp4 (+ _qc.jpg + .txt).
  python engine/factory_case.py                 -> dalsi overeny spis z case/queue (abecedne prvy)
  python engine/factory_case.py --groq ["tema"] -> ak je fronta prazdna, spis napise bezplatny LLM (Groq cez refill_case.write_spec)
  --snap                                         -> len kontrolne snimky (engine/snap.py), bez renderu, spis ostava vo fronte
  --out <dir>                                    -> po uspesnom renderi skopiruje mp4/txt/jpg do <dir> ako case-<slug>.*
Po uspesnom renderi: spis z fronty ide do case/done, zaznam {slug, date, site, music, title} pribudne do case/history.json."""
import datetime
import json
import os
import shutil
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
import compose_case  # noqa: E402

CDIR = os.path.join(FACTORY, "case")
QDIR = os.path.join(CDIR, "queue")
DDIR = os.path.join(CDIR, "done")
HIST = os.path.join(CDIR, "history.json")


def queue_files():
    return sorted(f for f in os.listdir(QDIR) if f.endswith(".json")) if os.path.isdir(QDIR) else []


def from_queue():
    """abecedne prvy spis z case/queue (pise ho Claude v davkach), alebo None ak je fronta prazdna"""
    files = queue_files()
    if not files:
        return None
    name = files[0]
    S = json.load(open(os.path.join(QDIR, name), encoding="utf-8"))
    print(f"[fronta] {name} (zostava {len(files) - 1})")
    return name, S


def remember(S):
    hist = json.load(open(HIST, encoding="utf-8")) if os.path.exists(HIST) else []
    hist.append({"slug": S.get("slug"), "date": datetime.date.today().isoformat(), "site": S.get("site"),
                 "music": S.get("music"), "title": S.get("title")})
    json.dump(hist[-30:], open(HIST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def main():
    argv = sys.argv[1:]
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and not (i and argv[i - 1] == "--out")]
    got = from_queue()
    name = None
    if got is None:
        if "--groq" not in sys.argv:
            raise SystemExit("Fronta case/queue je prazdna. Doplnit spisy (Claude) alebo spustit s --groq.")
        import refill_case  # noqa: E402  (nacita sa az tu, aby prikaz bez --groq nepotreboval kluc)
        S = refill_case.write_spec(args[0] if args else refill_case.next_topic())
    else:
        name, S = got

    C = compose_case.CaseComposer(S)
    ep, script = C.compose()
    ep_dir = os.path.join(FACTORY, "episodes", S["slug"])
    os.makedirs(ep_dir, exist_ok=True)
    json.dump(ep, open(os.path.join(ep_dir, "episode.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(ep_dir, "script.js"), "w", encoding="utf-8").write(script)
    print(f"[compose] {S['slug']}: {len(S['beats'])} beatov, varovania: {C.warn or 'ziadne'}")
    if "--snap" in sys.argv:
        subprocess.run([sys.executable, os.path.join(HERE, "snap.py"), ep_dir, "1,4,8,12,16,20,24,28"])
        return
    r = subprocess.run([sys.executable, os.path.join(HERE, "build.py"), ep_dir, "--render"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print((r.stdout or "")[-900:] or (r.stderr or "")[-900:])
    if r.returncode == 0 and "FINAL" in (r.stdout or "") and "zvuk OK" in (r.stdout or ""):
        if "--out" in sys.argv:                       # odovzdanie publikacii: mp4 + txt + jpg
            dst = os.path.abspath(sys.argv[sys.argv.index("--out") + 1])
            os.makedirs(dst, exist_ok=True)
            for ext in (".mp4", ".txt", ".jpg"):
                src = os.path.join(FACTORY, "out", S["slug"] + ext)
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(dst, "case-" + S["slug"] + ext))
            print(f"[odovzdane] {dst}\\case-{S['slug']}.mp4")
        if name:
            os.makedirs(DDIR, exist_ok=True)
            shutil.move(os.path.join(QDIR, name), os.path.join(DDIR, name))
        remember(S)
        if S.get("source") == "groq":
            print("POZOR: spis od bezplatneho modelu - pred zverejnenim skontrolovat fakty.")
    else:
        print("CHYBA: render alebo kontrola zvuku zlyhala, spis ostava vo fronte.")
        sys.exit(1)


if __name__ == "__main__":
    main()
