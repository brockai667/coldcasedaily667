# -*- coding: utf-8 -*-
"""Archetyp `insert`: detail SAMOTNEHO PREDMETU bez postavy.

Ked naracia hovori o veci samej - "the book had a torn page", "the clock is stopped",
"three pegs, two empty" - zaber ukaze LEN predmet (mozno v rade s chybajucimi kusmi),
volitelne s cervenou anotaciou (kruh/krizik/sipka) a kratkym cervenym popiskom.

Dve kompozicie podla stage.dominance(key):
  "bob" (maly predmet)  -> makro zaber: predmet v surovej (nie human_scale) velkosti vyplna
     zaber, na plochom pozadi (stol / stena s vesiakom / zem sveta), kamera pomaly prisuva.
  "obj" (velky predmet) -> normalna scena sveta (ako stage_shots._look), ale bez postavy.

Registruje sa do shots.SHOTS["insert"] pri importe. stage_shots.py tento modul importuje
na svojom konci, takze build_spec (ktory importuje shots hned pred stage_shots) ho najde
spolu s ostatnymi inscenovanymi archetypmi.
"""
import math
import re

import interior
import look
import props
import props_story
import shots as S
import stage as st
import stage_shots as SS
from props import INK, PAPER, RED

GY = S.GY
CW, CH = S.CW, S.CH

# Stred a rozmery pre makro kompoziciu - vlastny plochy "insert" priestor, nezavisly od sveta.
FCX, FCY = 540.0, 960.0
OBJ_CY = 800.0            # zvisly stred predmetu (hore ostava miesto na popisok, dole na titulky)
LABEL_Y = 310.0

HANGING = ("coat_hanging",)      # predmety, ktore visia na haku/vesiaku (nie na zemi/stole)

# farba zeme sveta pre makro zaber vonku (rovnaka paleta ako shots.sand_ground/snow_ground/DIRT)
_GROUND_FILL = {"snow": "#f4f4f1", "sand": "#e9d6a6", "deck": "#b98a55", "water": "#8ecae6",
                "cave": "#cdbfa6", "forest": "#cfae80", "city": "#c9a476", "library": "#c9a476"}

# 12-bodova "rucne kreslena" nepravidelnost pre wobbly kruznicu - pevne cisla, ziadny random
# (zaber sa musi zhodovat framea-po-frame pri kazdom seeku/opakovanom builde).
_WOB = (1.00, 1.05, 0.97, 1.06, 0.95, 1.04, 0.98, 1.07, 0.96, 1.03, 0.99, 1.05)

_FILL_RE = re.compile(r'fill="[^"]*"')
_STROKE_RE = re.compile(r'stroke="[^"]*"')


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _to_int(v, default):
    try:
        return int(float(str(v).replace(",", "")))
    except (TypeError, ValueError):
        return default


def _clean_label(v):
    """Popisok: najviac 3 slova, 26 znakov, VELKYMI (co cita narracia, to vidno na obraze)."""
    txt = re.sub(r"\s+", " ", str(v or "")).strip()
    if not txt:
        return ""
    words = txt.split(" ")[:3]
    return " ".join(words).upper()[:26]


def _wobble_path(cx, cy, rx, ry, rot=0.0):
    """Rucne nakreslena (mierne nepravidelna) elipsa okolo (cx,cy) - pathLength=1 pre pen()."""
    n = len(_WOB)
    a = math.radians(rot)
    ca, sa = math.cos(a), math.sin(a)

    def pt(i):
        t = 2 * math.pi * i / n
        lx, ly = math.cos(t) * rx * _WOB[i], math.sin(t) * ry * _WOB[i]
        return cx + lx * ca - ly * sa, cy + lx * sa + ly * ca

    V = [pt(i) for i in range(n)]
    M = [((V[i][0] + V[(i + 1) % n][0]) / 2, (V[i][1] + V[(i + 1) % n][1]) / 2) for i in range(n)]
    d = f"M{M[-1][0]:.1f},{M[-1][1]:.1f} "
    for i in range(n):
        d += f"Q{V[i][0]:.1f},{V[i][1]:.1f} {M[i][0]:.1f},{M[i][1]:.1f} "
    return d + "Z"


def _ghost(svg):
    """Vybledny prerusovany obrys predmetu pre prazdne miesto v rade: bez vyplne, ciary zosede."""
    g = _FILL_RE.sub('fill="none"', svg)
    g = _STROKE_RE.sub(f'stroke="{INK}"', g)
    return f'<g opacity="0.25" stroke-dasharray="15 10">{g}</g>'


def _macro_scale(pw, ph):
    """Surova velkost predmetu: ~44 % vysky ramu, alebo ~78 % sirky pre ploche/siroke veci -
    berie sa mensia z oboch mierok, aby ostalo miesto na anotaciu a popisok. Ploche veci (kniha,
    debna) maju surovu vysku niekolkonasobne mensiu nez sirku - siroky ciel im da skutocnu
    velkost v zabere namiesto tenkeho pruhu v strede prazdneho ramu."""
    return min(0.72 * CW / max(1.0, pw), 0.44 * CH / max(1.0, ph))


def _wall_bg(s):
    """Stena s lamperiou (interior.STYLES) vyplnajuca cely zaber - pre veci na haku."""
    out = f'<path d="M-150,-150 H{CW + 150} V{CH + 150} H-150 Z" fill="{s["wall"]}"/>'
    if s.get("wains"):
        wy = CH * 0.60
        out += (f'<path d="M-150,{wy:.0f} H{CW + 150} V{CH + 150} H-150 Z" fill="{s["wains"]}"/>'
                + "".join(f'<path d="M{x},{wy + 14:.0f} V{CH + 120}" stroke="{s["wline"]}" stroke-width="4"/>'
                          for x in range(-150, CW + 150, 52))
                + f'<path d="M-150,{wy:.0f} H{CW + 150}" stroke="{s["trim"]}" stroke-width="16"/>'
                + f'<path d="M-150,{wy - 8:.0f} H{CW + 150}" stroke="{INK}" stroke-width="4"/>')
    return out


def _table_bg(s):
    """Drevena doska stola (interior.STYLES floor) vyplnajuca cely zaber - pre veci na stole."""
    out = f'<path d="M-150,-150 H{CW + 150} V{CH + 150} H-150 Z" fill="{s["floor"]}"/>'
    out += "".join(f'<path d="M-150,{y} H{CW + 150}" stroke="{s["fline"]}" stroke-width="5" opacity="0.55"/>'
                   for y in range(120, CH, 260))
    return out


def _ground_bg(surface):
    """Zem sveta (piesok/snih/tráva/hlina) vyplnajuca cely zaber - pre veci vonku, s kamienkami/travou.
    Farba a teren podla LOOK-u epizody (utes = trava, molo = kamenna dlazba, paleta, noc)."""
    lk = look.ground_bg(surface)
    if lk is not None:
        return lk
    fill = look.tone(_GROUND_FILL.get(surface, props.DIRT))
    out = f'<path d="M-150,-150 H{CW + 150} V{CH + 150} H-150 Z" fill="{fill}" stroke="none"/>'
    if surface == "snow":
        out += props.pebbles(7, 10, 0, CW, 220, CH - 60)
    elif surface == "sand":
        out += props.pebbles(11, 16, 0, CW, 220, CH - 60)
    elif surface not in ("deck", "water"):
        out += "".join(props.grass(x, y) for x, y in ((110, 1220), (330, 1460), (760, 1180), (960, 1440)))
        out += props.pebbles(13, 10, 0, CW, 220, CH - 60)
    return out


def _macro_bg(c, inside, hanging):
    kind = SS._kind(c)
    if inside:
        # v noci tmavsia stena/stol (miestnost podla casu epizody)
        s = look.room_style(interior.STYLES[interior.style_for(kind, c.get("era"))])
        return _wall_bg(s) if hanging else _table_bg(s)
    if hanging:
        return _wall_bg(look.room_style({"wall": "#c9b27c", "wains": None, "wline": "#8a6337", "trim": "#8a6337"}))
    return _ground_bg(S.SURFACE)


def _mark(kind, cx, cy, ow, oh, pid, cue_t):
    """Cervena anotacia okolo (cx,cy) so surovou velkostou predmetu (ow,oh): kruh | krizik | sipka."""
    if kind == "circle":
        d = _wobble_path(cx, cy, ow * 0.58, oh * 0.54, rot=-4)
        svg = (f'<path id="{pid}_m0" class="pen" pathLength="1" d="{d}" fill="none" stroke="{RED}" '
               f'stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>')
        js = f'tl.to(pen("{pid}_m0"), {{ d: 1, duration: 0.36, ease: "power1.inOut" }}, {cue_t:.3f});\n'
        return svg, js
    if kind == "cross":
        x0, y0, x1, y1 = cx - ow * 0.42, cy - oh * 0.42, cx + ow * 0.42, cy + oh * 0.42
        x2, y2, x3, y3 = cx + ow * 0.42, cy - oh * 0.42, cx - ow * 0.42, cy + oh * 0.42
        svg = (f'<path id="{pid}_m0" class="pen" pathLength="1" d="M{x0:.0f},{y0:.0f} L{x1:.0f},{y1:.0f}" '
               f'fill="none" stroke="{RED}" stroke-width="11" stroke-linecap="round"/>'
               f'<path id="{pid}_m1" class="pen" pathLength="1" d="M{x2:.0f},{y2:.0f} L{x3:.0f},{y3:.0f}" '
               f'fill="none" stroke="{RED}" stroke-width="11" stroke-linecap="round"/>')
        js = (f'tl.to(pen("{pid}_m0"), {{ d: 1, duration: 0.20, ease: "power1.inOut" }}, {cue_t:.3f});\n'
              f'tl.to(pen("{pid}_m1"), {{ d: 1, duration: 0.20, ease: "power1.inOut" }}, {cue_t + 0.16:.3f});\n')
        return svg, js
    if kind == "arrow":
        # zaciatok/oblukovy bod su orezane, aby sipka nezacinala mimo ramu pri sirokych/plochych
        # veciach (debna, kniha) - musi ostat "z lavého horneho rohu", ale vidiet cely oblúk.
        sx = max(70.0, cx - min(ow * 0.85, 420.0))
        sy = max(360.0, cy - min(oh * 0.70, 420.0))
        mx = max(90.0, cx - min(ow * 0.60, 320.0))
        my = cy - min(oh * 0.56, 340.0)
        tx, ty = cx - ow * 0.18, cy - oh * 0.10
        ang = math.atan2(ty - my, tx - mx)
        ah = 36
        a1x, a1y = tx - ah * math.cos(ang - 0.5), ty - ah * math.sin(ang - 0.5)
        a2x, a2y = tx - ah * math.cos(ang + 0.5), ty - ah * math.sin(ang + 0.5)
        d = (f'M{sx:.0f},{sy:.0f} Q{mx:.0f},{my:.0f} {tx:.0f},{ty:.0f} '
             f'M{a1x:.0f},{a1y:.0f} L{tx:.0f},{ty:.0f} L{a2x:.0f},{a2y:.0f}')
        svg = (f'<path id="{pid}_m0" class="pen" pathLength="1" d="{d}" fill="none" stroke="{RED}" '
               f'stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>')
        js = f'tl.to(pen("{pid}_m0"), {{ d: 1, duration: 0.32, ease: "power1.inOut" }}, {cue_t:.3f});\n'
        return svg, js
    return "", ""


def _label(p, label, cue_t):
    if not label:
        return "", ""
    fs = S.fit_size(label, 118, 940)
    svg = (f'<g id="{p}_lab" opacity="0">'
           f'<text x="0" y="0" class="hand" font-size="{fs}" text-anchor="middle" fill="{RED}" '
           f'stroke="{PAPER}" stroke-width="{fs * 0.16:.1f}" stroke-linejoin="round" paint-order="stroke">'
           f'{_esc(label)}</text></g>')
    js = (f'var lab = node("{p}_lab", {{ x: {FCX:.0f}, y: {LABEL_Y:.0f}, s: 0, o: 0, r: -2 }});\n'
          f'tl.set(lab, {{ o: 1 }}, {cue_t - 0.001:.3f});\n'
          f'slamIn(lab, {cue_t:.3f}, 1.8, 1, 0.24);\n')
    return svg, js


def _letter_note(label):
    """List: ked ma zaber popisok, napise sa aj rukou na papier - list "ukaze" slova."""
    if not label:
        return ""
    return (f'<text x="0" y="-50" class="hand" font-size="30" text-anchor="middle" fill="{INK}">'
            f'{_esc(label)}</text>')


def _rail_svg(x0, width, rail_y, centers):
    """Dreveny lisovy vesiak na stenu s hakmi na kazdom mieste v rade."""
    x1 = x0 + width
    plank = (f'<path d="M{x0 - 30:.0f},{rail_y - 22:.0f} H{x1 + 30:.0f} V{rail_y + 22:.0f} H{x0 - 30:.0f} Z" '
             f'fill="{props.WOOD}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
             f'<path d="M{x0 - 30:.0f},{rail_y - 8:.0f} H{x1 + 30:.0f}" stroke="{props_story.WOOD_D}" '
             f'stroke-width="4" opacity="0.6"/>')
    pegs = "".join(f'<path d="M{cx - 10:.0f},{rail_y + 18:.0f} h20 v24 q0,14 -10,14 q-10,0 -10,-14 Z" '
                   f'fill="{props_story.WOOD_D}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
                   for cx in centers)
    return plank + pegs


def _row(p, key, count, filled, mark, cue_t):
    """count >= 2: predmety vedla seba cez ~80 % sirky ramu. Prazdne miesto = prerusovany
    obrys (opacity 0.25); mark == circle ho navyse zakruzkuje (jeden po druhom, 0.12 s od seba)."""
    hanging = key in HANGING
    span = 0.80 * CW
    x0 = FCX - span / 2
    pitch = span / count
    centers = [x0 + pitch * (i + 0.5) for i in range(count)]
    svg, js = "", ""
    rail_y, base_y = 560.0, 1140.0
    if hanging:
        svg += _rail_svg(x0, span, rail_y, centers)
    k = 0
    for i, cx in enumerate(centers):
        pid = f"{p}_r{i}"
        psvg, pw, ph = S.prop_svg(pid, key)
        if hanging:
            scl = min(0.60 * pitch / max(1.0, pw), 1.5)
            oy = rail_y + 46 + ph * scl
        else:
            scl = min(0.72 * pitch / max(1.0, pw), 0.40 * CH / max(1.0, ph))
            oy = base_y
        frag = f'<g transform="translate({cx:.1f},{oy:.1f}) scale({scl:.4f})">{psvg}</g>'
        if i < filled:
            svg += frag
            continue
        svg += _ghost(frag)
        if mark == "circle":
            mcy = oy - ph * scl * 0.52
            d = _wobble_path(cx, mcy, pw * scl * 0.58, ph * scl * 0.54, rot=(-6 + 5 * i))
            mid = f"{p}_rm{i}"
            svg += (f'<path id="{mid}" class="pen" pathLength="1" d="{d}" fill="none" stroke="{RED}" '
                    f'stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>')
            t = cue_t + k * 0.12
            js += (f'tl.to(pen("{mid}"), {{ d: 1, duration: 0.28, ease: "power1.inOut" }}, {t:.3f});\n'
                   f'shake(cam, {t:.3f}, 10, 0.20);\n')
            k += 1
    return svg, js


def _macro(p, c, key, label, mark, count, filled, cue_t):
    """Kompozicia A: maly predmet (dominance "bob") v surovej velkosti vyplna zaber."""
    inside = SS._inside(c)
    hanging = key in HANGING
    cam_body = _macro_bg(c, inside, hanging)
    body_js = ""
    if count >= 2:
        row_svg, row_js = _row(p, key, count, filled, mark, cue_t)
        cam_body += row_svg
        body_js += row_js
    else:
        psvg, pw, ph = S.prop_svg(p + "_obj", key)
        scl = _macro_scale(pw, ph)
        ow, oh = pw * scl, ph * scl
        ox, oy = FCX, OBJ_CY + oh / 2
        extra = _letter_note(str((c.get("params") or {}).get("note") or "")) if key == "letter" else ""   # na papier len params.note (slova listu), nie popis zaberu
        cam_body += f'<g transform="translate({ox:.1f},{oy:.1f}) scale({scl:.4f})">{psvg}{extra}</g>'
        mk_svg, mk_js = _mark(mark, ox, OBJ_CY, ow, oh, p, cue_t)
        cam_body += mk_svg
        body_js += mk_js
        if mark != "none":
            body_js += f'shake(cam, {cue_t:.3f}, 11, 0.22);\n'
    cam_body += f'<g id="{c["bob"]}_root"></g>'
    D = c["t1"] - c["t0"]
    cam_js = (f'var cam = GCam("{p}_cam", {FCY:.0f}, {{ x: {FCX:.0f}, z: 1.0, up: 0, abs: 1 }});\n'
              f'tl.fromTo(cam, {{ x: {FCX:.0f}, z: 1.0, up: 0 }}, {{ x: {FCX - 10:.0f}, z: 1.07, up: 18, '
              f'duration: {D:.3f}, ease: "sine.inOut", immediateRender: false }}, {c["t0"]:.3f});\n')
    body = f'<g id="{p}_cam">{cam_body}</g>'
    return body, cam_js + body_js


def _big(p, c, key, mark, cue_t):
    """Kompozicia B: velky predmet (dominance "obj") v normalnej scene sveta, bez postavy."""
    key, psvg, pw, ph, scl = SS._prop(p, c, key)
    ow, oh = pw * scl, ph * scl
    z = st.frame_z(key, ow, oh)
    ox = FCX
    box = (ox - ow / 2, ox + ow / 2, GY - oh)
    mk_svg, mk_js = _mark(mark, ox, GY - oh * 0.5, ow, oh, p, cue_t)
    world = (f'<g transform="translate({ox:.0f},{GY}) scale({scl:.3f})">{psvg}</g>{mk_svg}'
             f'<g id="{c["bob"]}_root"></g>')
    svg = SS._scene(p, c, ox, z, st.HOR, world, avoid=box)
    t0, t1 = c["t0"], c["t1"]
    js = SS._cam_js(p, ox, ox - 30, z * 0.94, z * 1.08, st.HOR - 960, st.HOR - 930, t0, t1)
    js += mk_js
    if mark != "none":
        js += f'shake(cam, {cue_t:.3f}, 12, 0.24);\n'
    js += SS._flurry(p, c)          # vlocky/dazd, ktore _scene nakreslil
    return svg, js


def shot_insert(p, c):
    key = c["prop"]
    params = c.get("params") or {}
    label = _clean_label(params.get("label"))
    mark = str(params.get("mark") or "none").strip().lower()
    if mark not in ("circle", "cross", "arrow", "none"):
        mark = "none"
    count = max(1, min(8, _to_int(params.get("count"), 1)))
    filled = max(0, min(count, _to_int(params.get("filled"), count)))
    cu = c["cue_t"]
    if st.dominance(key) == "obj":
        scene_svg, js = _big(p, c, key, mark, cu)
        lab_svg, lab_js = _label(p, label, cu)
        svg = S.svg_wrap(scene_svg + lab_svg + S.gold_layer(p, c["gold"], ""))
        js += lab_js + S.js_gold(p, c, cu, "cam", gy=300)
        return svg, js
    body, js = _macro(p, c, key, label, mark, count, filled, cu)
    lab_svg, lab_js = _label(p, label, cu)
    svg = S.svg_wrap(body + lab_svg + S.gold_layer(p, c["gold"], ""))
    js += lab_js + S.js_gold(p, c, cu, "cam", gy=300)
    return svg, js


S.SHOTS["insert"] = shot_insert
