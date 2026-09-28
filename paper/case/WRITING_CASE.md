# Písanie spisov (UnexplainedDaily, „Paper Case Files“)

Záhada podaná ako papierový vyšetrovací spis: stôl s lampou a fasciklom, korková nástenka s dôkazmi a červenou šnúrkou,
nočná dioráma miesta činu. Spis = jeden JSON v `case/specs/<slug>.json`:
`python engine/compose_case.py case/specs/<slug>.json` → `episodes/<slug>/episode.json + script.js` → `engine/build.py`
(hlas, titulky, zvuk) → `--render` → `out/<slug>.mp4`. Kontrakt knižníc: `case/CONTRACT.md`. Vzor, ktorý používa každý
záber: `case/specs/_test_case.json` (fiktívny prípad).

## Formát jedného spisu
```json
{
 "topic": "Dyatlov Pass", "slug": "dyatlov-pass", "title": "The Dyatlov Pass Incident", "case": "047",
 "hook": "hovorená veta (1–2 krátke vety): čo sa stalo",
 "banner": ["RIADOK 1 max 18 znakov", "RIADOK 2 max 18"],
 "site": "mountains | sea | sky", "props": ["tent", "footprints"],
 "place": "URAL MOUNTAINS, USSR", "date": "FEBRUARY 1959",
 "music": "lightless (nepovinné)", "mood_music": "tense | wonder | calm | playful",
 "voice": "en-GB-RyanNeural", "rate": "-4%",
 "beats": [
  {"label": "THE CASE", "scene": "site", "line": "…", "shots": [{"t": "fx", "fx": "snow", "at": "slope", "dur": 3}]},
  {"label": "CLUE 1", "scene": "board", "line": "…", "shots": [
     {"t": "card", "kind": "photo", "icon": "tent", "caption": "CUT FROM INSIDE", "at": "tent"},
     {"t": "stamp", "text": "EVIDENCE", "at": "inside"}]},
  {"label": "CLUE 2", "line": "…", "shots": [{"t": "card", "kind": "stat", "big": "-30°C", "small": "THAT NIGHT", "at": "thirty", "string": true},
                                            {"t": "focus", "at": "socks", "dur": 1.2}]}
 ],
 "end": {"line": "otázka divákovi", "stamp": "UNSOLVED"},
 "cta": "COMMENT YOUR THEORY", "description": "1 veta", "tags": ["#unexplained", "#mystery"],
 "facts": [{"claim": "...", "source": "..."}]
}
```
- `case` = číslo spisu na štítku fascikla (inak sa dopočíta zo slugu), `topic` = nápis na okraji fascikla (max 22 znakov,
  alebo vlastný `"folder"`). `date` + `place` (max 24 znakov) napíše písací stroj na hárok v hooku, tretí riadok je `STATUS: OPEN`.
- 4–6 beatov (max 7), vety 8–16 slov, spolu ~70–100 slov (video ~30–40 s). Nadpisy beatov max 14 znakov:
  `THE CASE`, `CLUE 1`, `CLUE 2`, `THE THEORY`, `THE TWIST`, `THE REPORT`, `WITNESS`, `EVIDENCE`.
- Hook: prvá veta musí udrieť (kto, kde, kedy, čo nesedí). Banner = novinový titulok, 2 krátke riadky VEĽKÝMI.
- Fakty: len doložené, opatrne („reportedly“, „investigators said“, „one theory is“). Nadprirodzené nikdy ako fakt.
  Zdroj každého tvrdenia do `facts`.
- Koniec: otázka divákovi (teória do komentárov); `stamp` = verdikt max 12 znakov (`UNSOLVED`, `CLASSIFIED`, `CASE CLOSED`).
  `cta` = nálepka pod nadpisom (default `COMMENT YOUR THEORY`, `false` = bez nej).

## Scény
- `desk` – stôl s fasciklom a lampou (hook je vždy tu), `board` – korková nástenka (sem patria karty, pečiatky, focus),
  `site` – nočná dioráma miesta činu (hory / more / obloha).
- `scene` v beate platí od neho ďalej; prvý beat bez `scene` = `board`. Max 2–3 zmeny na video. Prechod (kraftový hárok)
  a zvuk rieši automat. Pri návrate na nástenku sú skôr pripnuté karty stále na mieste. Koniec je vždy na nástenke.
- `site` + `props` (vyber podľa prípadu) + fx miesta:
  - `mountains`: props `tent`, `footprints`, `trees`; fx `snow`, `wind`, `flicker`, `fog`, `lightning`
  - `sea`: props `ship`, `buoy`, `rocks`; fx `waves`, `fog`, `lightning`, `flicker`
  - `sky`: props `dish`, `observatory`, `trees`; fx `beam`, `flicker`, `fog`

## Slovník záberov (`shots`, max 4 na beat)
- `{"t": "card", "kind": …, "at": "slovo", "string": true?}` – dôkaz sa pripne na nástenku (len `board`, max 5 kariet na video,
  poradie kariet = pozícia na nástenke). `string: true` = červená šnúrka od predošlej karty.
  - `photo`: `icon` + `caption` (max 22 znakov) – polaroid s papierovou ikonou na nočnom pozadí
  - `stat`: `big` (max 8 znakov, napr. `-30°C`, `9`, `1959`) + `small` (max 18)
  - `note`: `lines` – 1–3 riadky po max 20 znakov (dlhší text sa zalomí)
  - `doc`: `redact` – indexy riadkov 0–4, ktoré sa začiernia (+0.9 s po pripnutí), nepovinne `title` (max 16)
  - `map`: `map` (`mountains` | `sea` | `sky`, default podľa `site`), `place` `[x, y]` v 0..1 (červený krížik), nepovinne `caption`
- `{"t": "stamp", "text": "EVIDENCE", "at": …}` – pečiatka (max 12 znakov) buchne na poslednú kartu (bez karty do stredu). Len `board`.
- `{"t": "focus", "at": …, "dur": 1.2}` – kamera na poslednú kartu (0.6–3 s), potom späť. Len `board`, potrebuje kartu.
- `{"t": "fx", "fx": …, "at": …, "dur": …}`:
  - fx miesta (zoznam vyššie) – len v scéne `site`, každé raz za návštevu; `dur` v s, bez `dur` beží do konca scény
  - `flash` – blesk fotoaparátu (všade)
  - `magnify` – lupa na poslednú kartu (`board`) alebo na hárok (`desk`), `dur` 0.6–4 s (default 1.6)
- Ikony `photo`: tent mountain footprints snowflake thermometer radiation avalanche ship waves lifeboat barrel logbook compass
  anchor dish printout star stopwatch satellite comet question magnifier envelope key clock calendar pin eye moon lightning
  house tree plane report person group lock radio camera skull diamond moneybag painting train car briefcase handcuffs
  fingerprint safe mask coin book parachute bones.

## Časovanie (`at`)
- `at` = presné slovo z vety (zvládne aj predponu a spojené slová); `"slovo#1"` = jeho druhý výskyt. Čísla, na ktoré kotvíš,
  píš vo vete slovami (`minus thirty` → `"at": "thirty"`); na karte normálne (`-30°C`).
- Bez `at` alebo so slovom, ktoré vo vete nie je → záber sa rozloží rovnomerne po vete (varovanie). Zábery sa zoradia podľa
  času, dva nikdy na jedno slovo.
- Automat drží odstupy (karta 0.55 s, so šnúrkou 1 s, doc so začiernením 1.05 s), po prechode scény čaká 0.5 s, pred ďalším
  prechodom všetko dokončí a focus / lupu vráti do konca beatu. Keď sa zábery do vety nezmestia, vypíše varovanie → skráť ich
  počet alebo predĺž vetu.

## Čo robí automat sám
- Hook: zatvorený fascikel → otvorí sa, písací stroj napíše dátum a miesto, pomalý nájazd kamery, banner ako novinový výstrižok.
- Beat: kraftový štítok s nadpisom + zvuk; zvuky kariet, šnúrok, pečiatok a blesku podľa kontraktu.
- Koniec: veľká pečiatka verdiktu cez stred (pri 2. slove záverečnej vety), výzva CTA, potom návrat na stôl a fascikel sa zatvorí
  → posledný snímok = prvý (slučka).
- Validator nikdy nespadne: neznámy `kind` → odhad podľa polí, neznáma ikona → `question`, neznáme fx / scéna / typ záberu →
  vynechané; karta / pečiatka / focus mimo `board` a fx miesta mimo `site` → zahodené; 6. karta → zahodená; šnúrka pri prvej
  karte a focus bez karty → vynechané; dlhé texty orezané. Defaulty: `site` mountains, `voice` en-GB-RyanNeural, `rate` -4%,
  `mood_music` tense, `end.stamp` UNSOLVED, `cta` COMMENT YOUR THEORY.

## Kontrola pred zaradením
```
python engine/compose_case.py case/specs/<slug>.json                  # len validator + epizóda, vypíše varovania
python engine/compose_case.py case/specs/<slug>.json --snap 0,1.5,4,8,12,16,20,24,28
```
Snímky v `episodes/<slug>/build/snapshots` (prvý beh stiahne hlas cez edge-tts): nič sa neprekrýva s nadpisom (y 112–300),
výzvou ani titulkami (od y 1566), karty sú v zóne y 400–1480, text je čitateľný, prvý = posledný snímok. Potom `--render` →
`out/<slug>.mp4` + `_qc.jpg`. Nové ikony / fx / scény pridávať do `lib/` + do slovníka v `engine/compose_case.py` a sem.
