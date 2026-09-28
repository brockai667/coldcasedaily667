# „Paper Case Files" — kontrakt medzi knižnicami (nová fabrika, štýl papierového spisu)

Nová fabrika pre kanál UnexplainedDaily: záhady („Dyatlov Pass", „Mary Celeste", „Wow! signal") podané ako **papierový
vyšetrovací spis**: tmavý stôl s lampou, kraftový fascikel, korková nástenka, na ňu sa pripínajú papierové dôkazy
(polaroid ilustrácie z papiera, kartičky so štatistikou, písané poznámky, začiernené dokumenty), červená šnúrka medzi
špendlíkmi, pečiatky (CASE FILE, EVIDENCE, CLASSIFIED, UNSOLVED), písací stroj. Medzi tým „dioráma miesta činu" v noci
(hory so stanom, more s loďou, nočná obloha s rádioteleskopom) — rovnaká papierová estetika ako MindBlown
(vrstvený papier, tieň `filter="url(#cut)"`, `#rough`), ale úplne iná nálada: tma, teplé svetlo lampy, krém + kraft + červená.

Beží na existujúcom engine `paper-factory` (čítaj najprv `lib/core.js`, `engine/base.html`, pre vzor prostredia `lib/env_field.js`,
pre vzor panelu `lib/panels_stat.js`). Plátno 1080×1920, 30 fps, jediná pauznutá GSAP os `PF.tl`. Nič sa nekreslí v čase
inak než cez `PF.tl` (`PF.X/XY/O/F/AT/S`, `tl.fromTo(..., { immediateRender: false })` pri každom neskoršom fromTo na
zdieľanom prvku — inak sa FROM hodnota aplikuje od t = 0 a rozbije prvý snímok). Prvky sa registrujú `PF.P(id, cx, cy, init)`.
Vrstvy s paralaxou: `PF.add("B"|"M"|"F", markup)` (B = pozadie, M = stred, F = popredie); kamera `PF.CAM(s, px, py, t, dur, ease)`.
**Slučka:** snímok v čase `PF.VO.total` musí byť zhodný s prvým snímkom (kompilátor zavolá upratanie; každá knižnica musí
vedieť svoje veci vrátiť do stavu 0). Žiadne `Math.random` bez `PF.rnd(seed)`.

## Paleta (papier, tmavý stôl)
| Použitie | Farby |
|---|---|
| Stôl (drevo) / tieň stola | `#3b2a22` / `#2a1c16` |
| Svetlo lampy (kužeľ, radial) | `#ffd9a0` → priehľadné, vrchol opacity ~0.55 |
| Korok / tmavší korok / rám nástenky | `#c58f5a` / `#b57b48` / `#4a3527` |
| Kraft fascikel / tmavší kraft | `#c9a677` / `#b08d5f` |
| Kartička (krém) / rám polaroidu / atrament / sivá písacieho stroja | `#f6edd9` / `#fbf7ee` / `#2b2320` / `#3a332e` |
| Šnúrka / pečiatka / špendlík mosadz / špendlík červený / začiernenie | `#c8352b` / `#c9382d` / `#d8a94a` / `#d94a3b` / `#1a1512` |
| Nočná obloha (hore → dole) / mesiac / hviezdy | `#17203a` → `#0d1224` / `#f3e9c8` / `#fff6d6` |
| Sneh / sneh v tieni / hory (ďaleko → blízko) | `#eef2f7` / `#cfd8e3` / `#3b4a6b` `#2c3852` `#1f2a40` |
| More (hore → dole) / pena / loď silueta | `#1f4d6b` → `#163a52` / `#e8f1f5` / `#1a1f2b` |
| Kov (anténa, kupola) | `#9aa3ad` / `#6f7883` |
Písmo: nadpisy `"Serif"` (DM Serif Display, už v base.html), písací stroj `"Courier New", "Liberation Mono", monospace`
(bold, letter-spacing 0.04em) — bez sťahovania nových fontov. Text v SVG: `font-family` rovnako.

## Bezpečné zóny (nič sa neprekrýva s chrome)
Nadpis `#day` (vľavo hore, y 112–300) a `#hook`/`#cta` (hore, y 120–360); titulky `.cap` od y 1566 dole.
Obsah nástenky a kariet teda **y 400–1480**, x 60–1020. Pečiatka na konci môže ísť cez stred (y ~ 900–1100).

## 1. `lib/env_case.js` — prostredie (prefix ID `cf_`)
```js
var env = PF.envCase({ scene: "desk", site: "mountains", props: ["tent", "footprints"], caseNo: "047", title: "DYATLOV PASS" });
env.kind === "case"; env.scenes === ["desk", "board", "site"]; env.scene0 === "desk";
env.scene(name, t)          // prepnutie scény s prechodom (lampa stmavne 0.25 s pred t, kraftový hárok zhora prekryje, v t sa prepne,
                            // hárok odíde dole do t+0.4) — rovnaký princíp ako env_field.scene + PF.sceneSet("cf", ...)
env.folder(open, t)         // desk: otvorenie/zatvorenie fascikla (~0.5 s), otvorený = vidno krémový hárok vnútri
env.sheet(lines, t)         // desk: 1–3 riadky písacieho stroja na hárku (id textov cf_sheet1..3); ak existuje PF.cards.typewrite,
                            // použije ho, inak PF.S textContent; vracia čas konca písania
env.slot(i)                 // board: {x, y, r} pre kartu i = 0..4 (stred karty, rotácia v °), všetky v zóne y 400–1480,
                            // rozostupy tak, aby sa karty 480×560 (photo) neprekrývali: napr. (300,640,-4) (790,600,3) (300,1170,2) (790,1160,-3) (545,900,0)
env.siteFx(name, t0, t1)    // site: "snow" | "wind" | "flicker" | "lightning" | "beam" | "fog" | "waves" (podľa variantu; neznáme = nič)
env.lamp(level, t, dur)     // 0..1 sila svetla lampy (kužeľ + vinety), východzí 1
env.metric = env.metricLabel = env.show = function () {};   // kompatibilita s core/compose
```
Scény sú postavené naraz ako skupiny `<g id="cf_sc_<scene>_<L>">` v každej vrstve (viditeľná len úvodná), prepínajú sa
`PF.sceneSet("cf", name, on, t, dur)`.
- **desk**: pohľad zhora: drevo (B, jemná kresba letokruhov), kužeľ lampy z pravého horného rohu (B, radialGradient, id `cf_lamp`),
  vineta, fascikel v strede (M, ~760×1000, štítok s `CASE #` + caseNo hore, `title` na kraji, kancelárska spona, gumička),
  vo vnútri krémový hárok s hlavičkou „CASE FILE" a 3 prázdnymi riadkami `cf_sheet1..3` (písací stroj), káva kruh, ceruzka (M),
  lupa v pravom dolnom rohu (F, mimo zóny titulkov: y < 1480), drobný prach `PF.fx.dust`.
- **board**: korková nástenka cez celú obrazovku (B: korok s `feTurbulence` zrnom, drevený rám, 2–3 predpripnuté drobnosti mimo
  slotov: prázdny lístok, roh roztrhnutého papiera, špendlík), tieň lampy (vineta), F: nič alebo okraj lampy hore vpravo.
  Karty tam pridáva `cards_case.js` (do vrstvy M, cez `env.slot`).
- **site** (variant `o.site`, vyberá sa pri vytvorení, props sú predpripravené a viditeľné):
  - `mountains`: hviezdy, mesiac, vrstvené hrebene (B ďaleko, M bližšie), snehová zem (M/F), props `tent` (oranžový papierový stan
    s roztrhnutým dielcom, id `cf_tent`), `footprints` (stopy v snehu — cesta dole), `trees` (siluety smrekov). fx: snow, wind, flicker, fog, lightning.
  - `sea`: nočná obloha, mesačná cesta na vode, 3 pásy vĺn (M/F) s **horizontálnou slučkou** (kópia posunutá o šírku,
    perióda cez `PF.loopPeriod`), props `ship` (brigantína silueta s plachtami, jemné kolísanie v slučke), `buoy`, `rocks`. fx: waves (už bežia), fog, lightning, flicker.
  - `sky`: hviezdne pole (blikanie v slučke), pás Mliečnej cesty, nízky horizont kopcov, props `dish` (rádioteleskop – veľká parabola
    na veži, id `cf_dish`), `observatory` (kupola), `trees`. fx: beam (prerušovaná čiara signálu od paraboly hore + pulz), flicker, fog.
Všetky site fx sú zapnuté len medzi t0..t1 (a končia v neutrále). Nič sa nedotýka nadpisu/titulkov.

## 2. `lib/cards_case.js` — dôkazy, šnúrka, pečiatky, písací stroj (prefix ID `cd_`)
```js
var c = PF.cards.make({ id: "cd1", kind: "photo", icon: "tent", caption: "CUT FROM INSIDE", slot: env.slot(0) });
// kinds: photo (polaroid 480×560: biely rám, vnútri „fotka" = ikona na tmavom nočnom pozadí, popis dole písacím strojom, max 22 zn.),
//        stat  (kartička 460×300: big (max 8 zn., Serif 120px) + small (max 18 zn., stroj 40px)),
//        note  (lepiaci/krémový lístok 460×360: lines[] 1–3 riadky písacím strojom, max 20 zn./riadok),
//        doc   (dokument 460×520: hlavička, 5 riadkov „textu" ako čiary, redact = indexy riadkov so začiernením, ktoré sa zjaví c.redact(t)),
//        map   (papierová mapa 480×420: vrstevnice/pobrežie podľa opts.map = "mountains"|"sea"|"sky", červený krížik/špendlík na opts.place {x,y} v 0..1)
c.pin(t)                 // pripnutie: spadne zhora s tieňom, špendlík sa zabodne (0.45 s), jemný odraz; karta má rotáciu slot.r
c.out(t)                 // odletí (0.35 s) a skryje sa
c.focus(t, dur)          // PF.CAM na kartu (scale 1.55), c.unfocus(t, dur) späť na 1
c.redact(t)              // doc: čierne pásy sa zasunú (len kind doc)
c.x, c.y, c.pinXY        // stred karty a bod špendlíka (pre šnúrku)
PF.cards.string(cA, cB, t, dur)   // červená šnúrka medzi špendlíkmi (mierny previs, PF.draw), vracia id
PF.cards.stringsOff(t)
PF.cards.stamp(text, x, y, t, { color, rot, size, sub })   // pečiatka: 2 rámiky + text (Courier bold), buchne (scale 2→1, 0.12 s),
                                                            // rough filter, opacity 0.92; size 1 = ~560 px široká; vracia id
PF.cards.stampOff(id, t)
PF.cards.typewrite(sel, text, t, cps)   // po znakoch cez tl.set textContent (cps ~ 22), s kurzorom; vracia čas konca
PF.cards.magnify(x, y, t0, t1)          // lupa (F) sa priloží na bod: kruh so sklom, jemné zväčšenie obsahu pod ňou nie je nutné
PF.cards.flash(t)                       // blesk fotoaparátu: biela vrstva 0→0.85→0 za 0.3 s
PF.cards.clear(t)                       // všetky karty out, šnúrky a pečiatky preč, lupa preč (pre slučku)
PF.cards.icon(name)                     // SVG markup ikony v boxe 200×200 so stredom 0,0 (papierový výstrih, 2–4 farby, filter #cut)
```
Karty sú `<g>` v `PF.svg("M")` (paralaxa s nástenkou), pečiatky/lupa/blesk vo `PF.svg("F")`. Všetky vytvorené prvky
sú na začiatku skryté (opacity 0) a `clear` ich vráti do toho stavu.
**Ikony (minimálna sada, každá rozpoznateľná ako papierový výstrih):** tent, mountain, footprints, snowflake, thermometer, radiation,
avalanche, ship, waves, lifeboat, barrel, logbook, compass, anchor, dish, printout (papier s riadkami čísel + červený krúžok), star,
stopwatch, satellite, comet, question, magnifier, envelope, key, clock, calendar, pin, eye, moon, lightning, house, tree, plane,
report (dokument), person, group (3 siluety), lock, radio, camera, skull (jemná papierová lebka, nie horor).
Neznáma ikona → `question`.

## 3. `engine/compose_case.py` — scenár → epizóda (znovu použije `engine/build.py` bez zmien)
Spec (JSON) v `case/specs/<slug>.json`:
```json
{
 "topic": "Dyatlov Pass", "slug": "dyatlov-pass", "title": "The Dyatlov Pass Incident", "case": "047",
 "hook": "In 1959, nine hikers walked into the Ural Mountains. None of them came back.",
 "banner": ["NINE HIKERS.", "NO WITNESSES."],
 "site": "mountains", "props": ["tent", "footprints"], "place": "URAL MOUNTAINS, USSR", "date": "FEBRUARY 1959",
 "music": "lightless", "mood_music": "tense", "voice": "en-GB-RyanNeural", "rate": "-4%",
 "beats": [
  {"label": "THE CASE", "scene": "site", "line": "...", "shots": [{"t": "fx", "fx": "snow", "at": "slope", "dur": 3.0}]},
  {"label": "CLUE 1", "scene": "board", "line": "...", "shots": [
     {"t": "card", "kind": "photo", "icon": "tent", "caption": "CUT FROM INSIDE", "at": "tent", "string": true},
     {"t": "stamp", "text": "EVIDENCE", "at": "inside"}]},
  {"label": "CLUE 2", "line": "...", "shots": [{"t": "card", "kind": "stat", "big": "-30°C", "small": "THAT NIGHT", "at": "thirty", "string": true},
                                              {"t": "focus", "at": "socks", "dur": 1.2}]},
  {"label": "THEORY", "line": "...", "shots": [{"t": "card", "kind": "note", "lines": ["\"COMPELLING", "NATURAL FORCE\""], "at": "force"}]},
  {"label": "THE TWIST", "line": "...", "shots": [{"t": "card", "kind": "doc", "redact": [1, 3], "at": "modelled"}, {"t": "fx", "fx": "flash", "at": "tent"}]}
 ],
 "end": {"line": "What do you think happened on Dead Mountain?", "stamp": "UNSOLVED"},
 "cta": "COMMENT YOUR THEORY", "description": "1 veta", "tags": ["#unexplained", "#mystery"],
 "facts": [{"claim": "...", "source": "..."}]
}
```
- Kľúče beatov `b1..bN` + `end`, vety do `lines` (hook, b1.., end) ako v `compose.py`; časy slov cez `PF.at(key, word, nth)`,
  začiatky cez `PF.seg(key)[0]`. Znovu použiť z `compose.py`: `norm`, `words`, `js`, `MUSIC`, `MOOD_MUSIC`, `music_vol`, a triedu
  `Composer` (metódy `anchor`, `emit`, `fx`) — `CaseComposer(Composer)` prepíše `validate()` a `compose()`.
- Scéna beatu: `scene` platí od beatu ďalej (default = predchádzajúca; prvý beat default `board`). Hook je vždy `desk`.
- **Hook** (0 → b1): fascikel zatvorený v snímku 0; 0.35 s `env.folder(true)`; `env.sheet([date, place, "STATUS: OPEN"], 0.7)`;
  kamera pomalý nájazd 1.0 → 1.07 (`PF.CAM`), `#hook` banner viditeľný, zhasne 0.25 s pred b1. Pri b1 `env.scene(...)`.
- **Beat**: `PF.DAY(label, T.k)` (chrome `file`) + sfx `tick.wav` 0.9 a `paper.wav` 0.5 pri nadpise; zmena scény → `env.scene(name, T.k + 0.05)`
  + sfx `paper.wav` −0.25 s 0.6 + `swell.wav` 0.3 (len pri prechode na site). Zábery (`shots`) v čase slova `at` (bez `at` = rovnomerne):
  - `card` → `PF.cards.make({... slot: env.slot(i)})` kde i = poradové číslo karty vo videu (max 5; 6.+ karta → najprv `clear` starých
    kariet? nie: validator obmedzí na 5 kariet); `c.pin(t)`; sfx `paper.wav` 0.55 + `pop.wav` 0.5 (+0.25 s). Ak `"string": true` a je
    predchádzajúca karta → `PF.cards.string(prev, c, t + 0.5, 0.45)` + sfx `whoosh.wav` 0.3. Karta sa pripína len keď je scéna `board`
    (ak je scéna site, validator presunie kartu do warn a zahodí). `kind: doc` s `redact` → `c.redact(t + 0.9)` + sfx `thud.wav` 0.35.
  - `stamp` → `PF.cards.stamp(text, x, y, t, {rot})` na voľné miesto nástenky (x 540, y podľa počtu kariet; alebo nad poslednou kartou) + sfx `thud.wav` 0.55.
  - `focus` → `c.focus(t, 0.5)` na poslednú kartu a `c.unfocus(t + dur, 0.5)`.
  - `fx` → `env.siteFx(fx, t, t + dur)` (site) alebo `PF.cards.flash(t)` (+ `sparkle.wav` 0.35) / `PF.cards.magnify(x, y, t, t + dur)`.
- **Koniec**: scéna musí byť `board` (ak nie je, prepnúť 0.3 s pred T.end); `PF.cards.stamp(end.stamp, 540, 1000, at(end, 2. slovo), {size: 1.7, rot: -12})`
  + sfx `thud.wav` 0.7 + `reveal_tone.wav` 0.5 od T.end; `PF.CTA(cta, T.end + 0.6, tc - 0.05)`; slučka: `tc = min(koniec posledného slova + 0.9, T.tot - 1.3)`:
  `PF.cards.clear(tc)`, `env.scene("desk", tc + 0.15)`, `env.folder(false, tc + 0.55)`, `env.lamp(1, ...)`, kamera späť na 1.0 — snímok T.tot == snímok 0.
- Validator (nič nespadne): neznáme kinds/ikony/fx → warn + náhrada (`question`, fx vynechať), max 5 kariet, caption/big/small/lines
  orezať na limity, `at` slovo, ktoré vo vete nie je → bez kotvy (rovnomerne), scény len desk/board/site, `end.stamp` default "UNSOLVED",
  `cta` default "COMMENT YOUR THEORY".
- `episode.json` ako v `compose.py`: `title, hook: banner, voice (default en-GB-RyanNeural), rate (default "-4%"), gap 0.55, tail 1.6,
  bg "#2a1c16", accent "#c9382d", kit {chrome: "file", trans: "page", pres: "full", cam: "calm"}, libs ["core.js", "fx.js", "env_case.js", "cards_case.js"],
  description (+ tags + "Paper animation made with code."), music {file, at, vol, credit}, lines, sfx`.
- CLI rovnaké ako compose.py: `python engine/compose_case.py case/specs/<slug>.json [--snap 1,4,8] [--render]` → `episodes/<slug>/`.

## 4. Chrome `file` (v `engine/base.html` + `lib/core.js`, len pridané riadky)
- `.ck-file #hookIn`: novinový výstrižok: background `#f3ead6`, border-radius 0, `clip-path: polygon(...)` roztrhnuté okraje (10–12 bodov
  s odchýlkou 1–2 %), `border-top/bottom: 3px double var(--ink)`, padding 30px 42px 22px, `transform: rotate(-1.5deg)`, tape viditeľná.
  `.ck-file .hl`: font "Serif", 80px, ink; `.hl.b`: farba `--stamp`.
- `.ck-file #day`: vľavo (`left: 64px; right: auto; top: 112px; justify-content: flex-start`); `.dayCard`: kraft štítok `#e6d3ad`,
  font `"Courier New", "Liberation Mono", monospace` bold 74px, letter-spacing .06em, ink, `border: 3px solid var(--ink)`, radius 4px,
  padding 18px 30px 12px, `rotate(-3deg)`, `box-shadow: 0 10px 0 rgba(0,0,0,.28)`; tapes viditeľné.
- `.ck-file .strip` (titulky): background `rgba(27,22,18,.84)`, farba `#f6edd9`, Courier bold 70px, letter-spacing .03em, padding 18px 34px 12px,
  radius 6px, bez box-shadow. `.ck-file #cta .dayCard`: 34px, padding 10px 24px 6px, `rotate(2deg)`.
- `core.js` `DAY`: nová vetva `else if (c === "file")`: `tl.fromTo("#dayIn", { x: -70, opacity: 0 }, { x: 0, opacity: 1, duration: 0.24, ease: "power3.out", immediateRender: false }, t)`.
- `CHROME_SFX["file"] = ("tick.wav", 0.9)` v compose_case (compose.py sa nemení).

## Overenie
`python engine/compose_case.py case/specs/<slug>.json --snap 0,1.5,4,8,12,16,20,24,28` → `episodes/<slug>/build/snapshots` a pozrieť
každý snímok: nič sa neprekrýva, prvý = posledný snímok, karty v zóne, text čitateľný. Potom `--render` → `out/<slug>.mp4` + `_qc.jpg`.
