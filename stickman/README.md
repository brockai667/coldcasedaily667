# ColdCase Stickman – denná kreslená epizóda (nevyriešený prípad)

Panáčikový engine (HyperFrames + SVG rig): jeden kanál, jeden štýl (papier, čierna linka, zlaté čísla,
UNEXPLAINED + otázka, neviditeľná slučka), rôzne prostredia, rôzni hrdinovia, zábery bez postavy (insert).

## Reťazec (`run_daily.py`)
1. **Téma** – `topics.json`: `topics` (ručne vybrané), `auto` (doplnené z Wikipédie cez `topics_from_wiki.py`,
   berú sa až po ručných), `used`, `skipped`.
2. **Príbeh** – `storyboard_v3.py "<téma>"`: celý článok z Wikipédie → OpenRouter free model (Nemotron)
   napíše 8–10 viet (háčik → objav → detaily → teória → unexplained → otázka) a ku každej zvolí záber
   z katalógu enginu; kritik boduje; kontroly (čísla/mená len z článku, nakresliteľnosť, opakovanie scén).
   Kód 3 = krátky článok, kód 2 = ostali problémy alebo slabý príbeh → téma sa **preskočí** (nič slabé sa
   nepublikuje), skúsia sa max 3 témy za beh.
3. **Video** – `build_spec.py specs/<slug>.json`: Kokoro hlas po vetách, zarovnanie, staging záberov,
   `look.py` (paleta/čas/počasie/terén z témy), HyperFrames render, zvuk −16 LUFS s limiterom, loopcheck.
4. **Publikovanie** – hosting + Buffer cez `push_to_buffer.py` tejto fabriky, jeden príspevok denne
   o `STICKMAN_SLOT_LOCAL` (12:00 Europe/Bratislava). Popis = záverečná otázka + hashtagy + kredit hudby.

## GitHub Actions (`.github/workflows/stickman.yml`)
- `workflow_dispatch` s `dry_run` (vyrobí video ako artefakt, nepublikuje) a `topic`.
- Cron je zatiaľ vypnutý (komentár v yml) – zapnúť po schválenom dry-run behu.
- Secrets: `OPENROUTER_API_KEY` (**pridať**; free modely, bez platby), `MODELS_TOKEN` (Groq záloha),
  `BUFFER_TOKEN`, `CLOUDINARY_*` (už existujú pre daily.yml).
- Kokoro + Whisper modely a Chromium sa cachujú (`actions/cache`).

## Lokálne
```
python stickman/run_daily.py --dry-run --topic "The Somerton Man"
python stickman/build_spec.py stickman/specs/the-somerton-man.json   # len render hotového spec-u
```
Zdroj enginu: `C:\Users\damia\FactoryAnim\style-tests\_engine` (sync skriptom, ktorý patchuje lokálne cesty:
`llm.py`/`tts_kokoro.py` namiesto ScienceFactory, hudba v `assets/music`, `STICKMAN_SKIP_CHECK`).
