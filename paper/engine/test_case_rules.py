# -*- coding: utf-8 -*-
"""Offline test case_rules.py (ColdCase rast 19.10.): limit slov / beatov, hook bez datumu, headline, poradie tem, render 4-beat spisu.
  python engine/test_case_rules.py      -> 0 = OK     (LLM je atrapa, ziadna siet, ziaden kluc)"""
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import case_rules as cr  # noqa: E402


def _beat(label, line, cards=1):
    shots = [{"t": "card", "kind": "note", "lines": ["A NOTE"], "at": line.split()[1].strip(".,?!")} for _ in range(cards)]
    return {"label": label, "line": line, "shots": shots}


def spec(n_beats=4, long=False):
    base = "Three keepers vanished and the table was still laid for dinner"
    lines = [base + (" and nobody ever found a single trace of the men or their boat afterwards" if long else "") + f" {i}." for i in range(n_beats)]
    return {"topic": "Flannan Isles", "title": "The Flannan Isles Lighthouse Mystery", "slug": "flannan-test", "case": "901",
            "hook": "Nobody has explained why three men vanished from a locked lighthouse.", "hook_style": "shock",
            "headline": "The lighthouse that emptied overnight", "banner": ["THREE KEEPERS.", "ZERO TRACES"], "site": "sea",
            "props": ["ship"], "place": "SCOTLAND", "date": "DEC 1900", "mood_music": "tense", "voice": "en-GB-RyanNeural", "rate": "-4%",
            "beats": [_beat(("THE CASE", "CLUE 1", "CLUE 2", "CLUE 3", "CLUE 4", "THE TWIST")[min(i, 5)], ln, 1) for i, ln in enumerate(lines)],
            "end": {"line": "What do you think happened to them?", "stamp": "UNSOLVED"}, "cta": "COMMENT YOUR THEORY",
            "description": "Three lighthouse keepers vanished.", "tags": ["#unexplained", "#mystery", "#lighthouse"]}


def t_limits():
    ok = spec(4)
    ok["beats"] = [dict(b, line="Keepers vanished from the lighthouse at night; the table was still laid.") for b in ok["beats"]]
    assert cr.spoken_words(ok) <= 80, cr.spoken_words(ok)
    assert cr.problems(ok) == [], cr.problems(ok)
    big = spec(6, long=True)
    assert cr.spoken_words(big) > 80 and any("beats" in p for p in cr.problems(big)) and any("words" in p for p in cr.problems(big))


def t_trim_and_rewrite():
    S = spec(6, long=True)
    asked = []

    def llm(system, prompt):
        asked.append(prompt)
        n = prompt.count("LINE ")
        return {"hook": "What happened inside the locked lighthouse?", "lines": ["Three keepers vanished in December 1900 from a rock."] * n,
                "end_line": "Where did they go?"}
    cr.enforce(S, llm)
    assert len(S["beats"]) == cr.TARGET_BEATS, len(S["beats"])
    assert len(asked) == 1, "prepis najviac raz"
    assert cr.spoken_words(S) <= cr.SOFT_WORDS, cr.spoken_words(S)
    assert S["beats"][0]["label"] == "THE CASE" and S["beats"][-1]["label"] == "THE TWIST", "prvy a posledny beat ostavaju"
    assert S["hook_style"] in cr.HOOK_STYLES


def t_too_long_rejected():
    S = spec(4, long=True)
    try:
        cr.enforce(S, None)          # bez LLM nad tvrdym stropom
    except ValueError:
        pass
    else:
        assert cr.spoken_words(S) <= cr.HARD_WORDS, "dlhy spis bez prepisu mal byt zamietnuty"
    S2 = spec(4, long=True)
    try:
        cr.enforce(S2, lambda s, p: {"lines": ["too many words again " * 6] * 4})   # prepis nestaci
    except ValueError:
        return
    raise AssertionError("prepis, ktory stale presahuje strop, mal byt zamietnuty")


def t_hook_dates():
    bad = ["In 1959, nine hikers died on a Ural mountainside.", "On 15 August 1977 a telescope recorded a signal.",
           "Since the 1930s, strange lights have appeared.", "March 1876: meat fell from the sky.", "In March, a ship vanished.",
           "1959 was the year nine hikers died."]
    good = ["Nobody has explained why three keepers vanished.", "Three men vanished from a locked lighthouse.", "What did these hikers see?",
            "Nobody may ever explain this light.", "Jan Peters never came home.", "The table was still laid for dinner."]
    for h in bad:
        assert cr.date_first(h), f"mal by byt datumovy hook: {h}"
    for h in good:
        assert not cr.date_first(h), f"nema byt datumovy hook: {h}"
    S = spec(4)
    S["hook"] = "In 1900, three keepers vanished from a lighthouse."
    for b in S["beats"]:
        b["line"] = "Keepers vanished from the lighthouse; the table was still laid."
    try:
        cr.enforce(S, lambda s, p: {"hook": "In 1900 they vanished."})        # prepis hook stale zacina datumom
    except ValueError:
        pass
    else:
        raise AssertionError("hook s datumom mal byt zamietnuty")
    S = spec(4)
    S["hook"] = "In 1900, three keepers vanished from a lighthouse."
    for b in S["beats"]:
        b["line"] = "Keepers vanished from the lighthouse; the table was still laid."
    cr.enforce(S, lambda s, p: {"hook": "Three keepers vanished from a locked lighthouse."})
    assert not cr.date_first(S["hook"]) and S["hook_style"] in cr.HOOK_STYLES


def t_headline_style():
    S = spec(4)
    S["hook_style"] = "nonsense"
    S["hook"] = "What did the keepers see?"
    cr.enforce(S, None)
    assert S["hook_style"] == "question", S["hook_style"]
    assert S["headline"] == "The lighthouse that emptied overnight"
    for bad in ("Flannan", "In 1900 three men vanished", "x " * 40, ""):
        assert cr.clean_headline({"headline": bad}) == "", bad


def t_topics():
    order = cr.prefer_lesser_known(["The Dyatlov Pass Incident", "The Isdal Woman", "The Loch Ness Monster", "The Hessdalen Lights",
                                    "The Min Min Light", "The Somerton Man"])
    assert order[:2] == ["The Hessdalen Lights", "The Min Min Light"], order
    assert order[2:4] == ["The Isdal Woman", "The Somerton Man"], order
    assert set(order[4:]) == {"The Dyatlov Pass Incident", "The Loch Ness Monster"}, order
    assert sorted(order) == sorted(set(order)), "nic sa nesmie stratit"


def t_render_four_beats():
    import compose_case
    S = cr.enforce(spec(4), None)
    C = compose_case.CaseComposer(copy.deepcopy(S))
    ep, script = C.compose()
    assert len(C.S["beats"]) == 4 and script
    assert ep["title"] == "The lighthouse that emptied overnight", ep["title"]
    assert "Flannan" in ep["description"] and "#FlannanIsles" in ep["description"], ep["description"]
    assert "Kevin MacLeod" in ep["music"]["credit"] and "CC BY" in ep["music"]["credit"], "kredit hudby musi ostat v kazdom poste"
    S2 = copy.deepcopy(S)
    S2["headline"] = ""
    ep2, _ = compose_case.CaseComposer(S2).compose()
    assert ep2["title"] == "The Flannan Isles Lighthouse Mystery", "bez headline ostava title (stare spisy)"


def t_levers():
    import learn
    keep = dict(learn.CFG)
    try:
        learn.configure(os.path.join(HERE, ".."), "ColdCaseDaily")
        names = [x["name"] for x in learn.CFG["levers"]]
    finally:
        learn.CFG.clear()
        learn.CFG.update(keep)
    for n in ("hook_q_unexplained", "hook_shock", "length_25s", "lesser_known", "hook_question", "title_short"):
        assert n in names, n
    assert names[0] == "title_short" and len(names) == len(set(names))


TESTS = [t_limits, t_trim_and_rewrite, t_too_long_rejected, t_hook_dates, t_headline_style, t_topics, t_render_four_beats, t_levers]


def run():
    errs = []
    for t in TESTS:
        try:
            t()
        except Exception as e:
            import traceback
            errs.append(f"{t.__name__}: {type(e).__name__}: {str(e)[:300]}")
            traceback.print_exc()
    return errs


if __name__ == "__main__":
    errs = run()
    print("test_case_rules:", f"OK ({len(TESTS)} testov)" if not errs else f"{len(errs)} chyb")
    for e in errs:
        print("  CHYBA:", e)
    sys.exit(1 if errs else 0)
