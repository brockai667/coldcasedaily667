# -*- coding: utf-8 -*-
"""Inscenovane verzie archetypov (object_reveal, spot, scale_measure).

Kontrakt z rucneho Gobekli - kazdy zaber musi mat odpoved na styri otazky:
  1. kto dominuje  (maly predmet -> Bob ~33 % vysky, predmet pri rukach;
                    velky -> presahuje ram, Bob pri spodku)
  2. fyzicky vztah (klaknut, odhrnut, naklonit sa, dotknut, zmerat tycou)
  3. pohyb kamery k veci (prisun, naklon hore, posun)
  4. vyplnena plocha (hory/ihlicnany/zaveje/vlocky podla sveta)

Registruje sa do shots.SHOTS pri importe (build_spec ho importuje hned po shots).
"""
import math

import interior
import look as LK
import props
import shots as S
import stage as st
import worlds as W
from props import BOB_H, DIRT, INK, PAPER, RED, STONE, WATER, WOOD, bone, num3d

GY = S.GY


# ------------------------------------------------------------------ spolocne
def _kind(c):
    """Svet pre pozadie/popredie: hill | snow | desert | shore | sea."""
    return W.world_kind(c.get("world"))


def _inside(c):
    """params.inside = true - zaber sa odohrava v miestnosti, nie v krajine vonku."""
    return bool((c.get("params") or {}).get("inside"))


def _action(c, default):
    a = (c.get("action") or "").strip().lower()
    return a or default


def sun_clear(box, sun=(890, 240), clouds=((210, 330, 0.9), (960, 430, 0.7))):
    """Nic cez slnko: ked vysoky predmet (obrazovkovy box x0, x1, y_top) zasahuje do slnka vpravo hore,
    slnko ide dolava hore (oblak doprava); ked zasahuje aj tam, slnko sa nekresli."""
    if not box:
        return sun, clouds
    x0, x1, yt = box

    def hit(sx, sy, r=135):
        return x1 > sx - r and x0 < sx + r and yt < sy + r
    if not hit(*sun):
        return sun, clouds
    if not hit(190, 240):
        return (190, 240), ((890, 360, 0.8),)
    return None, ((150, 330, 0.8),)


def _scene(p, c, cam_x, z, hor, world_svg, sun=(890, 240), clouds=((210, 330, 0.9), (960, 430, 0.7)), avoid=None):
    """Pozadie (obloha + hory sveta) -> kamera so svetom -> vlocky. Vrati svg (bez gold vrstvy).
    avoid = obrazovkovy box vysokeho predmetu (x0, x1, y_top) - slnko sa mu vyhne.
    params.inside: miestnost namiesto krajiny - ziadna obloha/slnko/oblaky/popredie/vlocky."""
    if _inside(c):
        return (f'<g id="{p}_bd"></g><g id="{p}_cam">'
                f'{interior.room(p, _kind(c), c.get("era"), cam_x, GY)}{world_svg}</g>')
    sun, clouds = sun_clear(avoid, sun, clouds)
    kind = _kind(c)
    bd = st.backdrop(p, kind, hor) if kind != "sea" else f'<g id="{p}_bd"></g>'
    x0, x1 = st.world_span(cam_x, z)
    fg = st.foreground(kind, x0, x1, GY, seed=len(p) + int(cam_x)) if kind != "sea" else ""
    fl = (st.flurry_svg(p) if kind == "snow" else "") + LK.rain_svg(p)
    return (f'{S.sky(p, sun, clouds, hor=hor)}{bd}'
            f'<g id="{p}_cam">{S.ground()}{S.dressing(29)}{world_svg}{fg}</g>{fl}')


def _flurry(p, c):
    """JS vlociek (sneh) a dazda (LOOK) - v miestnosti nic."""
    if _inside(c):
        return ""
    return (st.flurry_js(p) if _kind(c) == "snow" else "") + LK.fx_js(p)


def _cam_js(p, cx0, cx1, z0, z1, up0, up1, t0, t1, ease="power1.inOut"):
    D = max(0.2, t1 - t0)
    return (f'var cam = GCam("{p}_cam", {GY}, {{ x: {cx0:.1f}, z: {z0:.4f}, up: {up0:.1f}, abs: 1, bd: "{p}_bd" }});\n'
            f'tl.fromTo(cam, {{ x: {cx0:.1f}, z: {z0:.4f}, up: {up0:.1f} }}, {{ x: {cx1:.1f}, z: {z1:.4f}, up: {up1:.1f}, '
            f'duration: {D:.3f}, ease: "{ease}", immediateRender: false }}, {t0:.3f});\n')


def _word_t(c, pred):
    """Cas prveho slova vo vete, ktore splna pred(norm_slovo)."""
    for w in c.get("words") or []:
        if pred("".join(ch for ch in w["w"].lower() if ch.isalnum())):
            return w["s"]
    return None


def _prop(p, c, key=None):
    key = key or S.pkey(c)
    psvg, pw, ph = S.prop_svg(p + "_prop", key)
    scl = props.human_scale(key, pw, ph, 1.0)
    return key, psvg, pw, ph, scl


# ================================================================== object_reveal
def shot_object(p, c):
    key = S.pkey(c)
    kind = _kind(c)
    if key in ("water", "water_ice") and kind != "sea" and S.SURFACE != "water":
        return _lake(p, c, measure=False)
    dom = st.dominance(key)
    act = _action(c, "find" if dom == "bob" else "look")
    if dom == "bob" and act in ("watch", "point", "look"):
        # pozorovanie maleho predmetu: stoji nad nim a zohne sa - nie druhy rovnaky klak ako pri find
        return _watch_small(p, c, key)
    if dom == "bob" and act in ("find", "dig", "reach", "carry"):
        return _find(p, c, key, lift=(act == "carry"))
    return _look(p, c, key, act)


def _watch_small(p, c, key):
    """Maly predmet na zemi: Bob k nemu prijde, zohne sa do podrepu a pozera zblizka.
    Kamera ide dolu za jeho pohladom (prisun k predmetu).
    Vnutri na stole (TABLE_ITEMS): bez podrepu - Bob sa nad stol nakloni a ukaze/siahne."""
    key, psvg, pw, ph, scl = _prop(p, c, key)
    ow, oh = pw * scl, ph * scl
    table = _inside(c) and key in interior.TABLE_ITEMS
    if table:
        ox = 700.0
        tbl_svg, table_h, table_w = interior.table_under(p + "_tbl", ox, GY)
        BX = ox - table_w / 2 - 90
        z = st.frame_z(key, ow, oh + table_h)
        cx0 = (BX - 70 + ox + ow / 2) / 2
        cx1 = cx0 + 0.3 * (ox - cx0)
        world = (f'{tbl_svg}<g transform="translate({ox:.0f},{GY - table_h:.0f}) scale({scl:.3f})">{psvg}</g>'
                 f'{W.hero_rig(c["bob"], c.get("hero"))}')
    else:
        z = st.frame_z(key, ow, oh)
        BX = 400.0
        ox = BX + 120 + ow / 2
        cx0 = (BX - 70 + ox + ow / 2) / 2
        cx1 = cx0 + 0.3 * (ox - cx0)
        world = f'<g transform="translate({ox:.0f},{GY}) scale({scl:.3f})">{psvg}</g>{W.hero_rig(c["bob"], c.get("hero"))}'
    svg = S.svg_wrap(_scene(p, c, (cx0 + cx1) / 2, z, st.HOR, world) + S.gold_layer(p, c["gold"], ""))
    t0, t1, cu = c["t0"], c["t1"], c["cue_t"]
    js = _cam_js(p, cx0, cx1, z * 0.92, z * 1.10, st.HOR - 960, st.HOR - 960, t0, t1)
    js += (f'var rg = Rig("{c["bob"]}", {{ s: 1, x: {BX - 70:.0f}, y: {GY}, idle: 1, seed: 12, eye: 0.7 }});\n'
           f'setPose(rg, STAND, {t0:.3f});\n'
           f'tl.set(rg, {{ w: 1, wa: 1, ph: 0 }}, {t0:.3f});\n'
           f'tl.to(rg, {{ x: {BX:.0f}, ph: 4.2, duration: 0.5, ease: "none" }}, {t0:.3f});\n'
           f'tl.set(rg, {{ w: 0, wa: 0 }}, {t0 + 0.5:.3f});\n'
           f'pose(rg, LEAN_OVER, {t0 + 0.5:.3f}, 0.3);\n')
    if not table:
        js += f'pose(rg, CROUCH_LOOK, {max(t0 + 0.9, cu - 0.1):.3f}, 0.3);\n'
    js += (f'tl.set(rg, {{ eye: 1, mo: 1 }}, {cu:.3f});\n'
           f'pose(rg, {{ aR: 120, aR2: 60, head: 20 }}, {min(t1 - 0.3, cu + 0.5):.3f}, 0.25);\n')
    js += _flurry(p, c)
    js += S.js_gold(p, c, cu, "cam", gy=380)
    if c["gold"]:
        js += f'unpop(cnt, {min(t1 - 0.10, cu + 1.2):.3f}, 0.18);\n'
    return svg, js


def _find(p, c, key, lift=False):
    """Maly predmet: Bob klakne, odhrnie sneh/hlinu a predmet sa ukaze pod jeho rukami.
    Vnutri na stole (TABLE_ITEMS): predmet uz stoji na stole - rovnake spracovanie ako _watch_small
    (bez klakania). Vnutri na podlahe: bez zaveje/hliny a bez odletujucich hrudiek - Bob len klakne
    a predmet uz je vidno, prip. ho zdvihne (CARRY_UP)."""
    key, psvg, pw, ph, scl = _prop(p, c, key)
    if _inside(c) and key in interior.TABLE_ITEMS:
        return _watch_small(p, c, key)
    ow, oh = pw * scl, ph * scl
    kind = _kind(c)
    inside = _inside(c)
    z = st.frame_z(key, ow, oh)
    BX = 400.0
    ox = BX + 44 + ow / 2
    cx0 = (BX - 70 + ox + ow / 2) / 2
    cx1 = cx0 + 0.22 * (ox - cx0)
    if inside:
        world = f'<g transform="translate({ox:.0f},{GY}) scale({scl:.3f})">{psvg}</g>{W.hero_rig(c["bob"], c.get("hero"))}'
    else:
        md_w = max(160.0, ow * 0.92 + 40)
        md = st.cover_mound(p + "_md", kind, ox + ow * 0.04, GY, md_w)
        ch = st.chunks(p + "_ch", kind, 8)
        world = (f'<g transform="translate({ox:.0f},{GY}) scale({scl:.3f})">{psvg}</g>'
                 f'{md}{W.hero_rig(c["bob"], c.get("hero"))}{ch}')
    svg = S.svg_wrap(_scene(p, c, (cx0 + cx1) / 2, z, st.HOR, world) + S.gold_layer(p, c["gold"], ""))
    t0, t1, cu = c["t0"], c["t1"], c["cue_t"]
    js = _cam_js(p, cx0, cx1, z * 0.94, z * 1.06, st.HOR - 960, st.HOR - 960, t0, t1)
    js += (f'var rg = Rig("{c["bob"]}", {{ s: 1, x: {BX:.0f}, y: {GY}, idle: 1, seed: 8, eye: 0.7 }});\n'
           f'setPose(rg, LEAN_OVER, {t0:.3f});\n'
           f'pose(rg, KNEEL_A, {t0 + 0.10:.3f}, 0.26);\n')
    if inside:
        # bez zaveje/hliny: predmet uz je vidno na podlahe, Bob klaci a hned si ho vsimne
        tr = min(t1 - 0.3, max(t0 + 0.45, cu - 0.1))
        js += f'tl.set(rg, {{ eye: 1, mo: 1 }}, {tr:.3f});\n'
    else:
        js += f'var md = cNode("{p}_md", {ox:.0f}, {GY}, {{ s: 1 }});\n'
        # odhrnanie: striedanie KNEEL_B/KNEEL_A, pri kazdom zabere odletia hrudy a kopa klesne.
        # Trva vacsinu zaberu - kdekolvek sa do neho pozries, Bob klaci a odhrna.
        start = t0 + 0.38
        end = max(start + 0.9, min(t1 - 0.35, max(cu + 0.25, t0 + 0.80 * (t1 - t0))))
        n = max(2, int((end - start) / 0.40))
        per = (end - start) / n
        steps = [1 - (k + 1) / n for k in range(n)]
        for k in range(n):
            tk = start + k * per
            js += (f'pose(rg, KNEEL_B, {tk:.3f}, {per * 0.42:.3f});\n'
                   f'pose(rg, KNEEL_A, {tk + per * 0.5:.3f}, {per * 0.42:.3f});\n'
                   f'tl.to(md, {{ s: {max(0.0, steps[k]):.3f}, duration: {per * 0.45:.3f}, ease: "power2.out" }}, {tk + per * 0.2:.3f});\n')
            for j in range(2):
                i = (2 * k + j) % 8
                vx = 260 + 140 * j + 40 * k
                js += (f'ball("{p}_ch{i}", {ox - md_w * 0.18:.0f}, {GY - 40}, {vx}, {-620 - 90 * j}, 2200, '
                       f'{tk + per * 0.22 + 0.05 * j:.3f}, 0.55, {220 * (1 if j else -1)});\n')
        tr = start + n * per
        js += (f'tl.set(md, {{ o: 0 }}, {tr:.3f});\n'
               f'tl.set(rg, {{ eye: 1, mo: 1 }}, {tr:.3f});\n'
               f'shake(cam, {tr:.3f}, 9, 0.24);\n')
    if lift:
        js += f'pose(rg, CARRY_UP, {tr + 0.12:.3f}, 0.3);\n'
    else:
        # ostane klacat s rukami na naleze a pozrie sa na neho (oci a usta dokoran)
        js += f'pose(rg, {{ lean: 30, lL: 108, lR: 34, aL: 70, aL2: -10, aR: 44, aR2: 6, head: 12 }}, {tr + 0.04:.3f}, 0.22);\n'
    js += _flurry(p, c)
    js += S.js_gold(p, c, max(cu, tr - 0.1), "cam", gy=380)
    if c["gold"]:
        js += f'unpop(cnt, {min(t1 - 0.10, tr + 1.1):.3f}, 0.18);\n'
    return svg, js


def _look(p, c, key, act):
    """Velky predmet: presahuje ram, Bob pri jeho pate. Kamera ide po objekte
    (vysoky -> naklon hore, siroky -> posun), Bob sa na nom zastavi a dotkne ho."""
    key, psvg, pw, ph, scl = _prop(p, c, key)
    ow, oh = pw * scl, ph * scl
    mode = props.SIZE.get(key, ("h", 1.0))[0]
    z = st.frame_z(key, ow, oh)
    on_water = S.SURFACE == "water"
    sub = S.SUBM if on_water else 0
    ox = 700.0
    BX = ox - ow / 2 - 104                  # REACH: ruka presne na hrane objektu
    up0 = st.HOR - 960
    if mode == "h" and not on_water:
        # siroky aj vysoky predmet (tunel, jaskyna): Bob musi ostat cely v zabere, aj za cenu,
        # ze predmet viac presahuje pravy okraj
        cx0 = cx1 = min((BX - 60 + ox + ow * 0.2) / 2, BX - 60 + 460 / (z * 1.04))
        up1 = up0 + min(320.0, 0.30 * oh * z)   # naklon hore po objekte (Bob ostane nad titulkami)
    else:
        cx0 = BX + 0.46 * CW_half(z)
        cx1 = cx0 + min(ow * 0.35, 0.3 * CW_half(z) * 2)
        up1 = up0
    world = (f'<g transform="translate({ox:.0f},{GY + sub}) scale({scl:.3f})">{psvg}</g>'
             + (S.water_front(ox - ow / 2 - 70, ox + ow / 2 + 70) if on_water else "")
             + (W.hero_rig(c["bob"], c.get("hero")) if not on_water else f'<g id="{c["bob"]}_root"></g>'))
    zs, cxs = z * 0.96, (cx0 + cx1) / 2
    box = (540 + (ox - ow / 2 - cxs) * zs, 540 + (ox + ow / 2 - cxs) * zs, st.HOR - (oh - sub) * zs)
    svg = S.svg_wrap(_scene(p, c, cxs, z, st.HOR, world, avoid=box) + S.gold_layer(p, c["gold"], ""))
    t0, t1, cu = c["t0"], c["t1"], c["cue_t"]
    js = _cam_js(p, cx0, cx1, z * 0.96, z * 1.04, up0, up1, t0, t1)
    if not on_water:
        js += (f'var rg = Rig("{c["bob"]}", {{ s: 1, x: {BX - 70:.0f}, y: {GY}, idle: 1, seed: 8, eye: 0.7 }});\n'
               f'setPose(rg, STAND, {t0:.3f});\n'
               f'tl.set(rg, {{ w: 1, wa: 1, ph: 0 }}, {t0:.3f});\n'
               f'tl.to(rg, {{ x: {BX:.0f}, ph: 4.2, duration: 0.55, ease: "none" }}, {t0:.3f});\n'
               f'tl.set(rg, {{ w: 0, wa: 0 }}, {t0 + 0.55:.3f});\n'
               f'pose(rg, LOOK_UP, {t0 + 0.55:.3f}, 0.28);\n'
               f'pose(rg, REACH, {max(t0 + 0.9, cu):.3f}, 0.26);\n'
               f'tl.set(rg, {{ eye: 1, mo: 1 }}, {cu:.3f});\n'
               f'pose(rg, {{ head: -30 }}, {max(t0 + 1.1, cu + 0.3):.3f}, 0.3);\n')
    js += f'shake(cam, {cu:.3f}, 8, 0.22);\n'
    js += _flurry(p, c)
    js += S.js_gold(p, c, cu, "cam", gy=360)
    if c["gold"]:
        js += f'unpop(cnt, {min(t1 - 0.10, cu + 1.2):.3f}, 0.18);\n'
    return svg, js


def CW_half(z):
    return st.CW / 2.0 / z


# ================================================================== jazero v reze (watch / measure)
def _lake(p, c, measure=False):
    """Jazero v reze: brehy, voda do hlbky, lad na hladine, kostry na dne.
    watch  -> Bob sa nakloni nad breh, lad popraska a zmizne, pod nim kostry;
    measure-> Bob na brehu s tycou, sirka sipkou nad hladinou, hlbka sipkou do vody."""
    kind = _kind(c)
    frozen = kind == "snow"
    LW = 880.0 if measure else 992.0
    x0 = 300.0
    x1 = x0 + LW
    BX = x0 - 58
    # hladina na ~56 % vysky ako v ostatnych zaberoch; kotlina plytka, aby dno s kostrami
    # ostalo nad titulkami a hneda zemina nezabrala vacsinu obrazu. Bob cely v zabere.
    hor = 1080
    up = hor - 960
    if measure:
        # cele jazero aj s oboma brehmi - sirku treba vidiet od kraja po kraj
        z = 0.97 * st.CW / (LW + 240)
        cx0 = cx1 = (BX - 150 + x1 + 40) / 2
        z0, z1, up0, up1 = z * 0.98, z * 1.02, up, up
    else:
        # blizsie pri Bobovi na brehu (~22 % vysky), jazero pokracuje za pravy okraj
        z = 1.35
        cx0 = BX + (540 - 250) / z
        cx1 = cx0 + 50
        z0, z1, up0, up1 = z * 0.97, z * 1.04, up, up
    depth = 185.0 / (z * 1.04)
    under, over = st.lake_section(p, x0, x1, GY, depth, frozen=frozen, bones=6)
    pole = ""
    if measure:
        # merna tyc s cervenymi pruhmi, zvisle cez jeho ruku (HOLD_POLE: ruka ~ (63,-136) pri s=1);
        # spodok dosadne presne na dno v tom mieste
        hx, hy = BX + 63, GY - 136
        ptop = hy - 110
        pbot = st.lake_bottom(x0, x1, GY, depth)(hx) - 4
        L = pbot - ptop
        bands = "".join(f'<path d="M0,{k * 40 + 10} v20" stroke="{RED}" stroke-width="12"/>' for k in range(int(L / 40)))
        pole = (f'<g id="{p}_pole"><g transform="translate({hx:.0f},{ptop:.0f})">'
                f'<path d="M0,0 V{L:.0f}" stroke="{PAPER}" stroke-width="16" stroke-linecap="round"/>{bands}'
                f'<path d="M-8,0 V{L:.0f} M8,0 V{L:.0f}" stroke="{INK}" stroke-width="4" fill="none"/></g></g>')
    dims = ""
    depth_val = st.depth_from_text(c.get("text", "")) or (c.get("params") or {}).get("depth")
    if measure:
        ya = GY - 70
        dims += (f'<path id="{p}_wa" class="pen" pathLength="1" d="M{x0 + 10:.0f},{ya} H{x1 - 10:.0f}" fill="none" '
                 f'stroke="{RED}" stroke-width="10" stroke-linecap="round"/>'
                 f'<g id="{p}_wt" opacity="0"><path d="M{x0 + 10:.0f},{ya - 30} v60 M{x1 - 10:.0f},{ya - 30} v60" '
                 f'stroke="{RED}" stroke-width="9" stroke-linecap="round"/></g>')
    if measure and depth_val:
        # hlbka len ked ju veta naozaj spomina
        dx = (x0 + x1) / 2 + 120
        dims += (f'<path id="{p}_da" class="pen" pathLength="1" d="M{dx:.0f},{GY + 12} V{GY + depth - 22:.0f}" fill="none" '
                 f'stroke="{RED}" stroke-width="10" stroke-linecap="round"/>'
                 f'<g id="{p}_dt" opacity="0"><path d="M{dx - 30:.0f},{GY + 12} h60 M{dx - 30:.0f},{GY + depth - 22:.0f} h60" '
                 f'stroke="{RED}" stroke-width="9" stroke-linecap="round"/></g>')
    unit = ((c.get("gold") or {}).get("unit") or "m")
    dlabel = ""
    if measure and depth_val:
        dv = float(depth_val)
        txt = (f"{dv:.0f}" if abs(dv - round(dv)) < 1e-6 else f"{dv:.1f}") + f" {unit}"
        dlabel = (f'<g id="{p}_dl" opacity="0"><g transform="translate({(x0 + x1) / 2 + 230:.0f},{GY + depth * 0.62:.0f})">'
                  f'{num3d(p + "_dln", txt, 96)}</g></g>')
    world = (f'{under}{W.hero_rig(c["bob"], c.get("hero"))}{pole}{over}{dims}{dlabel}')
    # pri merani je hore zlate cislo - slnko ide dolava, aby sa s nim nebilo
    sun, clouds = (((150, 250), ((850, 420, 0.85),)) if measure else ((890, 240), ((210, 330, 0.9), (960, 430, 0.7))))
    svg = S.svg_wrap(_scene(p, c, (cx0 + cx1) / 2, z, hor, world, sun=sun, clouds=clouds)
                     + S.gold_layer(p, c["gold"], ""))
    t0, t1, cu = c["t0"], c["t1"], c["cue_t"]
    js = _cam_js(p, cx0, cx1, z0, z1, up0, up1, t0, t1)
    js += f'var rg = Rig("{c["bob"]}", {{ s: 1, x: {BX:.0f}, y: {GY}, idle: 1, seed: 11, eye: 0.7 }});\n'
    if not measure:
        # lad popraska, zakal zmizne, kostry vystupia; Bob sa nakloni nad vodu
        js += (f'setPose(rg, STAND, {t0:.3f});\n'
               f'pose(rg, LEAN_OVER, {t0 + 0.15:.3f}, 0.35);\n'
               f'var mk = node("{p}_murk", {{ o: 0.62 }}), bn = node("{p}_lkb", {{ o: 0.28 }});\n')
        # lad praska na slove o topeni/lade, kostry vystupia na slove o kostiach - nie az na konci vety
        D = t1 - t0
        tc = _word_t(c, lambda w: w.startswith(("melt", "thaw", "crack", "ice", "break"))) or (t0 + 0.30 * D)
        tc = max(t0 + 0.35, min(t1 - 1.2, tc))
        tb = _word_t(c, lambda w: w.startswith(("skelet", "bone", "bodies", "body", "remain", "show", "reveal")))
        tb = max(tc + 0.40, min(t1 - 0.65, tb or tc + 0.6))
        for k in range(4):
            js += f'(function(){{ var ck = pen("{p}_ck{k}"); tl.to(ck, {{ d: 1, duration: 0.22, ease: "power1.out" }}, {tc + k * 0.09:.3f}); }})();\n'
        if frozen:
            js += (f'var ice = node("{p}_ice", {{ o: 1 }});\n'
                   f'tl.to(ice, {{ o: 0, y: 26, duration: 0.45, ease: "power2.in" }}, {tb:.3f});\n')
        js += (f'tl.to(mk, {{ o: 0, duration: 0.55, ease: "power1.out" }}, {tb:.3f});\n'
               f'tl.to(bn, {{ o: 1, duration: 0.55, ease: "power1.out" }}, {tb:.3f});\n'
               f'tl.set(rg, {{ eye: 1, mo: 1 }}, {tb + 0.1:.3f});\n'
               f'pose(rg, {{ head: 26, lean: 40, lL: 46, lR: 34, aR: 150, aR2: 60 }}, {tb + 0.15:.3f}, 0.25);\n'
               f'shake(cam, {tb:.3f}, 8, 0.25);\n')
        if frozen:
            for k in range(4):
                js += f'tl.to(node("{p}_ck{k}", {{}}), {{ o: 0, duration: 0.3 }}, {tb + 0.1:.3f});\n'
    else:
        tw = cu
        # hlbka sa zacne kreslit tesne pred slovom o hlbke, aby "3 m" stihlo byt na obraze
        tdp = _word_t(c, lambda w: w in ("three", "deep", "depth") or w.endswith("deep")) or (cu + 0.9)
        tdp = max(tw + 0.45, min(t1 - 0.75, tdp - 0.25))
        js += (f'setPose(rg, HOLD_POLE, {t0:.3f});\n'
               f'var pl = node("{p}_pole", {{ y: -{depth * 0.35:.0f} }});\n'
               f'tl.to(pl, {{ y: 0, duration: 0.5, ease: "power2.inOut" }}, {max(t0 + 0.2, tdp - 0.45):.3f});\n'
               f'pose(rg, {{ head: 34 }}, {max(t0 + 0.2, tdp - 0.45):.3f}, 0.4);\n'
               f'var wa = pen("{p}_wa"), wt = node("{p}_wt", {{ o: 0 }});\n'
               f'tl.set(wt, {{ o: 1 }}, {tw - 0.001:.3f});\n'
               f'tl.to(wa, {{ d: 1, duration: 0.55, ease: "power1.inOut" }}, {tw:.3f});\n')
        if depth_val:
            js += (f'var da = pen("{p}_da"), dt = node("{p}_dt", {{ o: 0 }});\n'
                   f'tl.set(dt, {{ o: 1 }}, {tdp - 0.001:.3f});\n'
                   f'tl.to(da, {{ d: 1, duration: 0.4, ease: "power1.inOut" }}, {tdp:.3f});\n')
        if dlabel:
            js += (f'var dl = node("{p}_dl", {{ o: 0 }});\n'
                   f'tl.set(dl, {{ o: 1 }}, {tdp + 0.15:.3f});\n'
                   f'slamIn(dl, {tdp + 0.15:.3f}, 1.8, 1, 0.22);\n')
        js += f'tl.set(rg, {{ eye: 1, mo: 1 }}, {tdp:.3f});\n'
    js += _flurry(p, c)
    js += S.js_gold(p, c, cu, "cam", gy=300, ramp=c.get("ramp"))
    if c["gold"] and not measure:
        js += f'unpop(cnt, {min(t1 - 0.10, cu + 1.2):.3f}, 0.18);\n'
    return svg, js


# ================================================================== spot
def shot_spot(p, c):
    """Vsimne si predmet: maly -> stoji nad nim, ukaze dole a klakne k nemu;
    velky -> stoji pri jeho pate a ukazuje hore.
    Vnutri na stole (TABLE_ITEMS): bez klakania - nakloni sa a ukaze/siahne (ako _watch_small)."""
    key, psvg, pw, ph, scl = _prop(p, c)
    ow, oh = pw * scl, ph * scl
    dom = st.dominance(key)
    act = _action(c, "point")
    if dom == "bob" and act in ("find", "dig"):
        return _find(p, c, key)
    up = st.HOR - 960
    table = _inside(c) and key in interior.TABLE_ITEMS
    table_h = 0.0
    if table:
        ox = 700.0
        tbl_svg, table_h, table_w = interior.table_under(p + "_tbl", ox, GY)
        BX = ox - table_w / 2 - 90
        z = st.frame_z(key, ow, oh + table_h)
        cx0 = (BX - 70 + ox + ow / 2) / 2
        cx1 = cx0 + 0.2 * (ox - cx0)
        qx, qy = BX + 30, GY - table_h - 360
        obj = f'{tbl_svg}<g transform="translate({ox:.0f},{GY - table_h:.0f}) scale({scl:.3f})">{psvg}</g>'
    elif dom == "bob":
        z = st.frame_z(key, ow, oh)
        BX = 400.0
        ox = BX + 96 + ow / 2
        cx0 = (BX - 70 + ox + ow / 2) / 2
        cx1 = cx0 + 0.2 * (ox - cx0)
        qx, qy = BX + 30, GY - 360
        obj = f'<g transform="translate({ox:.0f},{GY}) scale({scl:.3f})">{psvg}</g>'
    else:
        z = st.frame_z(key, ow, oh)
        ox = 720.0
        BX = ox - ow / 2 - 150
        cx0 = BX + 0.40 * CW_half(z)
        cx1 = cx0 + 0.25 * CW_half(z)
        qx, qy = BX + 30, GY - 380
        obj = f'<g transform="translate({ox:.0f},{GY}) scale({scl:.3f})">{psvg}</g>'
    world = (f'{obj}'
             f'{W.hero_rig(c["bob"], c.get("hero"))}<g id="{p}_spark" opacity="0">{S.SPARK}</g>'
             f'<g id="{p}_q" opacity="0"><text x="0" y="0" class="hand" font-size="170" fill="{RED}" '
             f'text-anchor="middle">!</text></g>')
    svg = S.svg_wrap(_scene(p, c, (cx0 + cx1) / 2, z, st.HOR, world) + S.gold_layer(p, c["gold"], ""))
    t0, t1, cu = c["t0"], c["t1"], c["cue_t"]
    js = _cam_js(p, cx0, cx1, z * 0.94, z * 1.07, up, up, t0, t1)
    js += (f'var rg = Rig("{c["bob"]}", {{ s: 1, x: {BX - 60:.0f}, y: {GY}, idle: 1, seed: 3, eye: 0.6 }});\n'
           f'setPose(rg, STAND, {t0:.3f});\n'
           f'tl.set(rg, {{ w: 1, wa: 1, ph: 0 }}, {t0:.3f});\n'
           f'tl.to(rg, {{ x: {BX:.0f}, ph: 4.6, duration: 0.5, ease: "none" }}, {t0:.3f});\n'
           f'tl.set(rg, {{ w: 0, wa: 0 }}, {t0 + 0.5:.3f});\n'
           f'tl.set(rg, {{ eye: 1, mo: 1 }}, {cu:.3f});\n'
           f'tl.to(rg, {{ oy: -34, duration: 0.10, ease: "power2.out" }}, {cu:.3f});\n'
           f'tl.to(rg, {{ oy: 0, duration: 0.18, ease: "bounce.out" }}, {cu + 0.10:.3f});\n'
           f'var q = node("{p}_q", {{ x: {qx:.0f}, y: {qy:.0f}, s: 0, o: 0 }});\n'
           f'pop(q, {cu:.3f}, 0.3, 3.5);\n'
           f'tl.to(q, {{ r: 10, duration: 0.5, ease: "sine.inOut", repeat: 1, yoyo: true }}, {cu + 0.1:.3f});\n'
           f'var sp = node("{p}_spark", {{ x: {ox:.0f}, y: {GY - table_h - oh * 0.6:.0f}, s: 0, o: 0 }});\n'
           f'pop(sp, {cu + 0.06:.3f}, 0.2, 4);\n'
           f'tl.to(sp, {{ o: 0, r: 40, s: 1.5, duration: 0.3 }}, {cu + 0.28:.3f});\n'
           f'shake(cam, {cu:.3f}, 10, 0.24);\n')
    if table:
        js += (f'pose(rg, LEAN_OVER, {max(t0 + 0.6, cu - 0.2):.3f}, 0.3);\n'
               f'pose(rg, {{ aR: 120, aR2: 60, head: 20 }}, {min(t1 - 0.3, cu + 0.3):.3f}, 0.25);\n')
    elif dom == "bob":
        js += (f'pose(rg, POINT_DOWN, {cu:.3f}, 0.18);\n'
               f'pose(rg, KNEEL_A, {min(t1 - 0.45, cu + 0.55):.3f}, 0.3);\n')
    else:
        js += f'pose(rg, {{ lean: -6, aL: 160, aL2: 14, aR: -30, aR2: 20, head: -32 }}, {cu:.3f}, 0.18);\n'
    js += _flurry(p, c)
    js += S.js_gold(p, c, cu, "cam")
    return svg, js


# ================================================================== scale_measure
_old_scale = S.SHOTS["scale_measure"]


def shot_scale(p, c):
    key = S.pkey(c)
    if key in ("water", "water_ice") and _kind(c) != "sea" and S.SURFACE != "water":
        return _lake(p, c, measure=True)
    dims = S._dims(c)
    if dims and _kind(c) != "sea" and S.SURFACE != "water":
        return _measure_multi(p, c, key, dims)
    if dims:
        return _old_scale(p, c)
    return _measure(p, c, key)


def _measure(p, c, key):
    """Jeden rozmer: kota priviazana k objektu vynosnymi ciarami, Bob pri objekte ukazuje na kotu.
    Maly objekt -> kamera blizko (Bob ~30 %), velky -> objekt presahuje ram."""
    key, psvg, pw, ph, scl = _prop(p, c, key)
    horiz = ((c.get("gold") or {}).get("axis") or "v").lower() == "h"
    on_water = S.SURFACE == "water"
    if not on_water:
        # rozmer z vety plati voci Bobovi (1,75 m): 5 m pilier = 2,9x Bob, 34 cm = 0,2x Bob
        vs_ = _value_scale(c, pw, ph, horiz)
        if vs_:
            scl = vs_
    ow, oh = pw * scl, ph * scl
    small = (oh if not horiz else ow) < 0.7 * BOB_H and not on_water
    sub = S.SUBM if on_water else 0
    ox = 640.0
    top = GY + sub - oh
    if horiz:
        yy = (GY - 34) if on_water else (GY + 70)
        ax0, ax1 = ox - ow / 2, ox + ow / 2
        BX = ax0 - (70 if small else 120)
        right = ax1 + 40
    else:
        ax = ox + ow / 2 + 44
        BX = ox - ow / 2 - (60 if small else 116)
        right = ax + 60
    left = BX - 70
    span = right - left
    z = min(st.frame_z(key, ow, oh), 0.88 * st.CW / span)
    if small:
        # maly predmet: kamera blizko (az ZMAX), Bob klaci pri nom - nie obrie stojace telo nad kamienkom
        z = min(st.ZMAX, max(z, 110.0 / max(1.0, oh)), 0.88 * st.CW / span, (st.HOR - 440) / 190.0)
    elif not horiz:
        # vrch objektu musi ostat pod zlatym cislom, Bob cely v obraze
        z = min(z, (st.HOR - 440) / max(1.0, oh), (st.HOR - 180) / BOB_H)
    cx0 = (left + right) / 2 - 20
    cx1 = cx0 + 30
    up = st.HOR - 960
    if horiz:
        arrow = (f'<path id="{p}_arrow" class="pen" pathLength="1" d="M{ax0:.0f},{yy} H{ax1:.0f}" fill="none" '
                 f'stroke="{RED}" stroke-width="10" stroke-linecap="round"/>'
                 f'<path id="{p}_ex0" class="pen" pathLength="1" d="M{ax0:.0f},{GY - 20} V{yy + 30}" fill="none" '
                 f'stroke="{RED}" stroke-width="7" stroke-linecap="round" opacity="0.8"/>'
                 f'<path id="{p}_ex1" class="pen" pathLength="1" d="M{ax1:.0f},{GY - 20} V{yy + 30}" fill="none" '
                 f'stroke="{RED}" stroke-width="7" stroke-linecap="round" opacity="0.8"/>')
    else:
        arrow = (f'<path id="{p}_ex0" class="pen" pathLength="1" d="M{ox + ow / 2 - 26:.0f},{GY} H{ax + 34:.0f}" '
                 f'fill="none" stroke="{RED}" stroke-width="7" stroke-linecap="round" opacity="0.8"/>'
                 f'<path id="{p}_ex1" class="pen" pathLength="1" d="M{ox + ow / 2 - 26:.0f},{top:.0f} H{ax + 34:.0f}" '
                 f'fill="none" stroke="{RED}" stroke-width="7" stroke-linecap="round" opacity="0.8"/>'
                 f'<path id="{p}_arrow" class="pen" pathLength="1" d="M{ax:.0f},{GY - 6} V{top + 6:.0f}" fill="none" '
                 f'stroke="{RED}" stroke-width="10" stroke-linecap="round"/>')
    world = (f'<g transform="translate({ox:.0f},{GY + sub}) scale({scl:.3f})">{psvg}</g>'
             + (S.water_front(ox - ow / 2 - 70, ox + ow / 2 + 70) if on_water else "")
             + arrow + (W.hero_rig(c["bob"], c.get("hero")) if not on_water else f'<g id="{c["bob"]}_root"></g>'))
    svg = S.svg_wrap(_scene(p, c, (cx0 + cx1) / 2, z, st.HOR, world) + S.gold_layer(p, c["gold"], ""))
    t0, t1, cu = c["t0"], c["t1"], c["cue_t"]
    draw = max(0.45, min(0.85, t1 - cu - 0.3))
    js = _cam_js(p, cx0, cx1, z * 0.96, z * 1.04, up, up, t0, t1)
    js += (f'var arrow = pen("{p}_arrow"), ex0 = pen("{p}_ex0"), ex1 = pen("{p}_ex1");\n'
           f'tl.to(ex0, {{ d: 1, duration: 0.22, ease: "power1.out" }}, {cu - 0.12:.3f});\n'
           f'tl.to(ex1, {{ d: 1, duration: 0.22, ease: "power1.out" }}, {cu - 0.06:.3f});\n'
           f'tl.to(arrow, {{ d: 1, duration: {draw:.3f}, ease: "power1.inOut" }}, {cu:.3f});\n')
    if not on_water and small:
        # klaci za predmetom s rukami na nom, pri kote sa na nu pozrie
        js += (f'var rg = Rig("{c["bob"]}", {{ s: 1, x: {BX:.0f}, y: {GY}, idle: 1, seed: 4, eye: 0.7 }});\n'
               f'setPose(rg, KNEEL_A, {t0:.3f});\n'
               f'pose(rg, KNEEL_B, {t0 + 0.25:.3f}, 0.2);\n'
               f'pose(rg, KNEEL_A, {t0 + 0.5:.3f}, 0.2);\n'
               f'pose(rg, {{ head: -4 }}, {cu + 0.1:.3f}, 0.25);\n'
               f'tl.set(rg, {{ eye: 1, mo: 1 }}, {cu + draw:.3f});\n')
    elif not on_water:
        js += (f'var rg = Rig("{c["bob"]}", {{ s: 1, x: {BX:.0f}, y: {GY}, idle: 1, seed: 4, eye: 0.7 }});\n'
               f'setPose(rg, REACH, {t0:.3f});\n'
               f'pose(rg, {{ head: -20 }}, {t0 + 0.2:.3f}, 0.3);\n'
               f'pose(rg, POINT, {cu:.3f}, 0.2);\n'
               f'tl.set(rg, {{ eye: 1, mo: 1 }}, {cu + draw:.3f});\n')
    js += _flurry(p, c)
    js += S.js_gold(p, c, cu, "cam", gy=330, ramp=c.get("ramp"))
    if c["gold"]:
        js += f'unpop(cnt, {min(t1 - 0.10, cu + (c.get("ramp") or 0.52) + 0.6):.3f}, 0.18);\n'
    return svg, js


def _value_scale(c, pw, ph, horiz):
    """Mierka z nameranej hodnoty: rozmer / 1,75 m * vyska Boba (orezane na 0,06-6,5 Boba)."""
    g = c.get("gold") or {}
    m = st.to_meters(g.get("count"), g.get("unit"))
    if not m or m <= 0:
        return None
    ratio = max(0.06, min(6.5, m / st.BOB_M))
    return ratio * BOB_H / max(1.0, (pw if horiz else ph))


def _measure_multi(p, c, key, dims):
    """Viac rozmerov jedneho predmetu (34 x 18 x 9 cm): predmet v pravdivej velkosti podla
    najvacsieho rozmeru, Bob pri nom klaci s rukami na nom, vedla tri koty - kazda sa nakresli
    na svojom cisle, pod nou zlaty popisok. Kamera blizko (predmet je maly), nie zvacseny predmet."""
    key, psvg, pw, ph, scl = _prop(p, c, key)
    unit = ((c.get("gold") or {}).get("unit") or "")
    top_v = max(v for _t, v in dims)
    m = st.to_meters(top_v, unit)
    if m:
        scl = max(0.06, min(6.5, m / st.BOB_M)) * BOB_H / max(1.0, max(pw, ph))
    ow, oh = pw * scl, ph * scl
    ox = 640.0
    BX = ox - ow / 2 - 60
    H = max(oh, 40.0)
    xs = [ox + ow / 2 + 40 + i * 42 for i in range(len(dims))]
    right = xs[-1] + 40
    left = BX - 70
    z = min(st.ZMAX, 0.86 * st.CW / (right - left), (st.HOR - 520) / max(1.0, H))
    z = max(z, 0.33 * st.CH / BOB_H)
    cx0 = (left + right) / 2
    cx1 = cx0 + 10
    up = st.HOR - 960
    arrows, labels = "", ""
    for i, (_t, v) in enumerate(dims):
        h = max(18.0, H * (v / top_v))
        x = xs[i]
        arrows += (f'<path id="{p}_da{i}" class="pen" pathLength="1" d="M{x:.0f},{GY - 4} V{GY - h:.0f}" fill="none" '
                   f'stroke="{RED}" stroke-width="7" stroke-linecap="round"/>'
                   f'<g id="{p}_dt{i}" opacity="0"><path d="M{x - 12:.0f},{GY - 4} h24 M{x - 12:.0f},{GY - h:.0f} h24" '
                   f'stroke="{RED}" stroke-width="6" stroke-linecap="round"/></g>')
        txt = (f"{v:.0f}" if abs(v - round(v)) < 1e-6 else f"{v:.1f}") + (f" {unit}" if unit else "")
        labels += (f'<g id="{p}_dl{i}" opacity="0"><g transform="translate({190 + i * 350},{330 + (i % 2) * 110})">'
                   f'{num3d(p + "_dln" + str(i), txt, 104)}</g></g>')
    world = (f'<g transform="translate({ox:.0f},{GY}) scale({scl:.3f})">{psvg}</g>{arrows}'
             f'{W.hero_rig(c["bob"], c.get("hero"))}')
    svg = S.svg_wrap(_scene(p, c, (cx0 + cx1) / 2, z, st.HOR, world) + labels)
    t0, t1 = c["t0"], c["t1"]
    js = _cam_js(p, cx0, cx1, z * 0.96, z * 1.04, up, up, t0, t1)
    js += (f'var rg = Rig("{c["bob"]}", {{ s: 1, x: {BX:.0f}, y: {GY}, idle: 1, seed: 4, eye: 0.7 }});\n'
           f'setPose(rg, KNEEL_A, {t0:.3f});\n'
           f'pose(rg, KNEEL_B, {t0 + 0.2:.3f}, 0.2);\n'
           f'pose(rg, KNEEL_A, {t0 + 0.45:.3f}, 0.2);\n')
    for i, (tt, _v) in enumerate(dims):
        ta = max(t0 + 0.3, min(t1 - 0.5, tt))
        js += (f'(function(){{ var a = pen("{p}_da{i}"), d = node("{p}_dt{i}", {{ o: 0 }}), l = node("{p}_dl{i}", {{ o: 0 }});\n'
               f'tl.set(d, {{ o: 1 }}, {ta - 0.001:.3f});\n'
               f'tl.to(a, {{ d: 1, duration: 0.3, ease: "power1.inOut" }}, {ta:.3f});\n'
               f'tl.set(l, {{ o: 1 }}, {ta + 0.05:.3f});\n'
               f'slamIn(l, {ta + 0.05:.3f}, 1.8, 1, 0.22); }})();\n'
               f'pose(rg, {{ head: {-6 + 6 * i} }}, {ta:.3f}, 0.2);\n')
    js += f'tl.set(rg, {{ eye: 1, mo: 1 }}, {max(t0 + 0.3, dims[0][0]):.3f});\n'
    js += _flurry(p, c)
    return svg, js


# ================================================================== wide_reveal - miesto v perspektive
FIELD = {"snow": "#f4f4f1", "sand": "#e9d6a6", "water": WATER, "deck": "#c9a97a"}
LIFTABLE = ("skull", "bones", "coin", "tablet", "stone", "gear", "map", "chest", "object")


def shot_wide(p, c):
    """Pole v perspektive: kusy nepravidelne rozhadzane (blizsie vacsie, dalej mensie),
    niektore zapadnute do povrchu, Bob medzi nimi - nie v strede terca. Kamera zacne tesne
    pri Bobovi a odtiahne sa, aby odhalila rozsah; pri slove Bob zdvihne jeden kus."""
    import random
    key = S.pkey(c)
    if key == "object" and c.get("topic_prop"):
        key = c["topic_prop"]
    kind = _kind(c)
    fcol = LK.field_fill(S.SURFACE, FIELD.get(S.SURFACE, "#e4d2ad"))
    n = int(c.get("count") or 24)
    n = max(8, min(60, n))
    HW, YB = 800.0, 1285.0
    rnd = random.Random(17 + n)

    def depth_y(u):
        return HW + (YB - HW) * (u ** 1.25)

    def man(u):
        return 0.34 + 1.0 * u

    raw, pw, ph = props.PROPS.get(key, props.p_object)("x")
    base_s = props.human_scale(key, pw, ph, 1.0)
    ub, bxs = 0.76, 330.0
    by = depth_y(ub)
    mb = man(ub)
    liftable = key in LIFTABLE
    act = _action(c, "carry" if liftable else "look")
    lift = liftable and act == "carry"
    # kus, ktory Bob zdvihne: tesne pred jeho rukami
    lx, ly = bxs + 92 * mb, by
    items = []
    tries = 0
    while len(items) < n - (1 if lift else 0) and tries < 6000:
        tries += 1
        u = rnd.random() ** 0.85
        u = 0.04 + 0.96 * u
        y = depth_y(u)
        m = man(u)
        s = base_s * m
        w = pw * s
        x = 540 + (rnd.random() - 0.5) * (980 + 900 * u)
        if abs(x - bxs) < 150 * mb and abs(y - by) < 70 * mb:
            continue                      # nic nesmie stat v Bobovi
        if lift and abs(x - lx) < 120 * mb and abs(y - ly) < 50:
            continue
        if any(abs(x - q[0]) < 0.55 * (w + q[3]) and abs(y - q[1]) < 0.35 * (ph * s + q[4]) for q in items):
            continue
        items.append((x, y, s, w, ph * s, rnd.random() < 0.30, rnd.uniform(-14, 14)))
    field = f'<path d="M-900,{HW:.0f} H1980 V2600 H-900 Z" fill="{fcol}" stroke="{INK}" stroke-width="8"/>'
    lines = "".join(f'<path d="M-900,{HW + (YB - HW) * (k / 9) ** 1.25 + 8:.0f} H1980" stroke="#dde7ec" '
                    f'stroke-width="{3 + k * 0.6:.1f}" fill="none" opacity="0.8"/>' for k in range(1, 10)) \
        if kind == "snow" else ""
    draw = []
    for (x, y, s, w, h, sunk, rot) in items:
        g = f'<g transform="translate({x:.0f},{y:.0f}) rotate({rot:.0f}) scale({s:.3f})">{raw}</g>'
        if sunk:
            g += (f'<path d="M{x - w * 0.62:.0f},{y + 4:.0f} q{w * 0.62:.0f},-{h * 0.55:.0f} {w * 1.24:.0f},0 z" '
                  f'fill="{fcol}" stroke="{st.SNOW_BLUE if kind == "snow" else INK}" stroke-width="5"/>')
        draw.append((y, g))
    bob = f'<g id="{p}_bobw">{W.hero_rig(c["bob"], c.get("hero"))}</g>'
    draw.append((by, bob))
    liftsvg = ""
    if lift:
        liftsvg = (f'<g id="{p}_lift"><g transform="scale({base_s * mb:.3f})">{raw}</g></g>')
        draw.append((ly + 0.5, liftsvg))
    draw.sort(key=lambda q: q[0])
    bd = st.backdrop(p, kind, HW) if kind != "sea" else ""
    fl = (st.flurry_svg(p) if kind == "snow" else "") + LK.rain_svg(p)
    body = (f'{S.sky(p, (900, 230), ((210, 320, 0.9), (700, 420, 0.7)), hor=HW)}'
            f'<g id="{p}_cam">{bd}{field}{lines}{"".join(g for _y, g in draw)}</g>{fl}')
    svg = S.svg_wrap(body + S.gold_layer(p, c["gold"], ""))
    t0, t1, cu = c["t0"], c["t1"], c["cue_t"]
    D = t1 - t0
    fx0, fy0 = bxs + 70 * mb, by - 170 * mb
    js = (f'var cam = ctl({{ s: 1.34, fx: {fx0:.0f}, fy: {fy0:.0f}, shx: 0, shy: 0 }}, function (q) {{\n'
          f'  $("{p}_cam").setAttribute("transform", "translate(540,960) scale(" + q.s.toFixed(4) + ") translate(" +\n'
          f'    (-q.fx + q.shx).toFixed(2) + "," + (-q.fy + q.shy).toFixed(2) + ")"); }});\n'
          f'tl.fromTo(cam, {{ s: 1.34, fx: {fx0:.0f}, fy: {fy0:.0f} }}, {{ s: 1.0, fx: 540, fy: 960, duration: {D:.3f}, '
          f'ease: "power2.inOut", immediateRender: false }}, {t0:.3f});\n'
          f'var rg = Rig("{c["bob"]}", {{ s: {mb:.3f}, x: {bxs:.0f}, y: {by:.0f}, idle: 1, seed: 9, eye: 0.7 }});\n')
    if lift:
        # hand pri CARRY_UP ~ (22, -296) pri s=1
        hx, hy = bxs + 30 * mb, by - 350 * mb       # nad klobukom, nie cez neho
        tu = max(t0 + 0.5, min(t1 - 0.8, cu - 0.15))
        js += (f'setPose(rg, KNEEL_A, {t0:.3f});\n'
               f'pose(rg, KNEEL_B, {t0 + 0.25:.3f}, 0.2);\n'
               f'pose(rg, KNEEL_A, {t0 + 0.5:.3f}, 0.2);\n'
               f'var lf = node("{p}_lift", {{ x: {lx:.0f}, y: {ly:.0f}, r: 0 }});\n'
               f'pose(rg, CARRY_UP, {tu:.3f}, 0.32, "back.out(1.4)");\n'
               f'tl.to(lf, {{ x: {hx:.0f}, y: {hy + 20 * mb:.0f}, r: -8, duration: 0.32, ease: "back.out(1.4)" }}, {tu:.3f});\n'
               f'tl.set(rg, {{ eye: 1, mo: 1 }}, {tu:.3f});\n')
    else:
        js += (f'setPose(rg, LOOK_UP, {t0:.3f});\n'
               f'pose(rg, {{ head: -10, aL: 150, aL2: 20 }}, {cu:.3f}, 0.25);\n'
               f'tl.set(rg, {{ eye: 1, mo: 1 }}, {cu:.3f});\n')
    js += _flurry(p, c)
    js += S.js_gold(p, c, cu, None, gy=330)
    return svg, js


# ================================================================== timeline_compare pre datumy (850 CE, 9500 BCE)
def _year_of(vs):
    import re
    m = re.search(r"(\d{1,5})\s*(bce|bc|ce|ad)?\b", (vs or "").lower())
    if not m:
        return None
    y = int(m.group(1))
    if m.group(2) in ("bce", "bc"):
        y = -y
    return y


_old_timeline = S.SHOTS["timeline_compare"]


def shot_timeline(p, c):
    pm = c.get("params") or {}
    vs = str(c.get("vs") or pm.get("vs") or "")
    year = _year_of(vs)
    if year is None or not (-20000 < year < 2020):
        # pomenovana vec (Gutenberg, pyramidy, Stonehenge): ta ista os, na druhom konci
        # znama rekvizita alebo vlajka s nazvom - nie nahrobok s textom
        return _years_ago(p, c, None, None, named=vs)
    year2 = _year_of(str(pm.get("vs2") or ""))
    if year2 is not None and year2 < year:
        year, year2 = year2, year
    return _years_ago(p, c, year, year2)


def _ytxt(y):
    return f"{abs(y)}" + (" BCE" if y < 0 else "")


def _icon_scale(key, pw, ph):
    """Predmet na casovej osi je ikona znacky - pravdiva mierka, ale najviac 300 x 360."""
    s = props.human_scale(key, pw, ph, 1.0)
    return min(s, 300.0 / max(1.0, pw), 360.0 / max(1.0, ph))


def _flag(x, gy, label, left=True):
    """Vlajka na osi s nazvom veci - pre porovnanie s niecim, co sa neda nakreslit (Gutenberg).
    left=True: latka vlaje dolava (dovnutra obrazu), aby nevybehla za okraj."""
    txt = str(label or "").strip().upper()[:22]
    fs = int(min(60, 360 / (0.60 * max(1, len(txt)))))
    wc = max(220, int(0.60 * fs * len(txt)) + 70)
    d = -1 if left else 1
    return (f'<path d="M{x:.0f},{gy} V{gy - 540}" stroke="{INK}" stroke-width="10" stroke-linecap="round"/>'
            f'<path d="M{x:.0f},{gy - 530} h{d * wc} l{-d * 40},70 l{d * 40},70 h{-d * wc} z" fill="#f2e6c4" '
            f'stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>'
            f'<text x="{x + d * (wc / 2 - 12):.0f}" y="{gy - 442}" class="hand" font-size="{fs}" text-anchor="middle" '
            f'fill="{INK}" data-layout-allow-overlap>{txt}</text>')


def _era_txt(y):
    """800 -> '800 AD', -9500 -> '9500 BC' (ako chce divak, nie CE/BCE)."""
    return f"{abs(int(y))} " + ("BC" if y < 0 else "AD")


def _sign(x, gy, text, big=False):
    """Kolik so stitkom zapichnuty v zemi za skupinou - datum alebo nazov veci."""
    txt = str(text or "").strip().upper()[:22]
    fs = int(min(64 if big else 56, (380 if big else 300) / (0.60 * max(1, len(txt)))))
    wb = max(160, int(0.60 * fs * len(txt)) + 50)
    top = gy - (300 if big else 250)
    return (f'<path d="M{x:.0f},{gy + 8} V{top + 60}" stroke="{WOOD}" stroke-width="12" stroke-linecap="round"/>'
            f'<path d="M{x - wb / 2:.0f},{top} h{wb} v78 h-{wb} z" fill="#f2e6c4" stroke="{INK}" stroke-width="8" '
            f'stroke-linejoin="round"/>'
            f'<text x="{x:.0f}" y="{top + 39 + fs * 0.36:.0f}" class="hand" font-size="{fs}" text-anchor="middle" '
            f'fill="{INK}" data-layout-allow-overlap>{txt}</text>')


def _years_ago(p, c, year, year2=None, named=None):
    """Uzemneny obraz namiesto osi v oblakoch:
      vs2   -> dve skupiny (kostry/lebky) na zemi, pri kazdej kolik so stitkom '800 AD' / '1800 AD',
               medzi nimi na snehu dvojsipka a zlate '1,000 YEARS'; Bob ukazuje z jednej na druhu;
      datum -> vec so stitkom datumu + zlate 'X YEARS AGO', Bob pri nej ukazuje;
      nazov -> vlavo vec temy, vpravo znama rekvizita alebo stitok s nazvom, sipka k starsej."""
    import datetime
    pm = c.get("params") or {}
    now = datetime.date.today().year
    gold_in = c.get("gold") or {}
    key = S.pkey(c)
    if key == "object":
        key = c.get("topic_prop") or ""
    has_obj = bool(key) and key in props.PROPS and key != "object"

    def group(x):
        if not has_obj:
            return ""
        raw, pw, ph = props.PROPS[key]("x")
        s = _icon_scale(key, pw, ph)
        return f'<g transform="translate({x:.0f},{GY}) scale({s:.3f})">{raw}</g>'

    def ground_arrow(xa, xb, both):
        ya = GY + 28
        head_l = f'M{xa:.0f},{ya} l38,-22 M{xa:.0f},{ya} l38,22'
        head_r = f' M{xb:.0f},{ya} l-38,-22 M{xb:.0f},{ya} l-38,22' if both else ""
        return (f'<path id="{p}_ta" class="pen" pathLength="1" d="M{xb:.0f},{ya} H{xa:.0f}" fill="none" '
                f'stroke="{RED}" stroke-width="10" stroke-linecap="round"/>'
                f'<g id="{p}_tah" opacity="0"><path d="{head_l}{head_r}" stroke="{RED}" stroke-width="10" '
                f'stroke-linecap="round" fill="none"/></g>')

    ago, unit = None, ""
    if year2 is not None:
        XA, XB = 400.0, 1020.0
        BX = (XA + XB) / 2 + 20
        ago = float(pm.get("years") or abs(year2 - year))
        unit = str(gold_in.get("unit") or "YEARS").upper()
        world = (f'{_sign(XA, GY, _era_txt(year))}{group(XA)}{_sign(XB, GY, _era_txt(year2))}{group(XB)}'
                 f'{ground_arrow(XA + 120, XB - 120, True)}')
        cx0, cx1 = (XA + XB) / 2 + 70, (XA + XB) / 2
    elif named is None:
        XA = 520.0
        BX = XA + 250
        ago = float(now - year)
        unit = "YEARS AGO"
        world = f'{_sign(XA, GY, _era_txt(year))}{group(XA)}'
        cx0, cx1 = XA + 150, XA + 110
    else:
        XA, XB = 400.0, 1020.0
        BX = (XA + XB) / 2 + 20
        ytop = pm.get("year")
        world = (_sign(XA, GY, _era_txt(ytop)) if isinstance(ytop, (int, float)) else "") + group(XA)
        known = W.vs_known(named)
        if known:
            kb, kw, kh = known
            ks = min(420.0 / max(1.0, kh), 360.0 / max(1.0, kw))
            world += f'<g transform="translate({XB:.0f},{GY}) scale({ks:.3f})">{kb}</g>'
        else:
            world += _sign(XB, GY, named, big=True)
        world += ground_arrow(XA + 120, XB - 120, False)
        if "count" in gold_in:
            ago = float(gold_in["count"])
            unit = str(gold_in.get("unit") or "YEARS").upper()
        cx0, cx1 = (XA + XB) / 2 + 70, (XA + XB) / 2
    z0, z1 = 0.97, 1.03
    up = st.HOR - 960
    world += W.hero_rig(c["bob"], c.get("hero"))
    svg_scene = _scene(p, c, (cx0 + cx1) / 2, (z0 + z1) / 2, st.HOR, world)
    gold_svg, ago_lab = "", ""
    c2 = c
    if ago is not None:
        c2 = dict(c, gold={"count": float(ago)})
        gold_svg = S.gold_layer(p, c2["gold"], "")
        ago_lab = (f'<g id="{p}_yl" opacity="0"><g transform="translate(540,470)">'
                   f'{num3d(p + "_yln", unit, 96)}</g></g>')
    svg = S.svg_wrap(svg_scene + gold_svg + ago_lab)
    t0, t1, cu = c["t0"], c["t1"], c["cue_t"]
    D = t1 - t0
    js = _cam_js(p, cx0, cx1, z0, z1, up, up, t0, t1, ease="power1.inOut")
    js += (f'var rg = Rig("{c["bob"]}", {{ s: 1, x: {BX:.0f}, y: {GY}, idle: 1, seed: 6, eye: 0.7, flip: -1 }});\n'
           f'setPose(rg, STAND, {t0:.3f});\n'
           f'pose(rg, POINT, {t0 + 0.2:.3f}, 0.25);\n')
    if year2 is not None:
        # ukaze z jednej skupiny na druhu: najprv dolava (starsia), potom sa otoci doprava
        tturn = max(t0 + 0.9, min(t1 - 0.6, t0 + D * 0.55))
        js += (f'tl.set(rg, {{ flip: 1 }}, {tturn:.3f});\n'
               f'setPose(rg, STAND, {tturn:.3f});\n'
               f'pose(rg, POINT, {tturn + 0.02:.3f}, 0.22);\n')
    if "_ta" in world:
        js += (f'var ta = pen("{p}_ta"), tah = node("{p}_tah", {{ o: 0 }});\n'
               f'tl.to(ta, {{ d: 1, duration: {min(0.9, D * 0.4):.3f}, ease: "power2.inOut" }}, {max(t0 + 0.2, cu - 0.3):.3f});\n'
               f'tl.set(tah, {{ o: 1 }}, {max(t0 + 0.2, cu - 0.3) + min(0.9, D * 0.4):.3f});\n')
    if ago is not None:
        js += (f'var yl = node("{p}_yl", {{ o: 0 }});\n'
               f'tl.set(yl, {{ o: 1 }}, {cu + 0.05:.3f});\n'
               f'slamIn(yl, {cu + 0.05:.3f}, 1.6, 1, 0.22);\n')
        js += S.js_gold(p, c2, cu, "cam", gy=330, ramp=min(1.2, D * 0.5))
    js += _flurry(p, c)
    return svg, js


S.SHOTS["object_reveal"] = shot_object
S.SHOTS["spot"] = shot_spot
S.SHOTS["scale_measure"] = shot_scale
S.SHOTS["wide_reveal"] = shot_wide
S.SHOTS["timeline_compare"] = shot_timeline


# ================================================================== action_crowd - nosici
def _load_svg(pid, era, cargo):
    """Naklad drzany oboma rukami pred telom (sucast riga, hybe sa s nim).
    Stred (50,-40) v suradniciach bedra = presne medzi dlanami pozy HOLD.
    Moderna era = drevena debna, dávna = pleteny kos; navrchu je vidiet, co nesu."""
    if cargo == "kosti":
        # lebka a kosti trcia z nakladu - musi byt jasne, co nesu
        top = (f'<g transform="translate(-6,-24) scale(0.22)">{props.PROPS["skull"]("x")[0]}</g>'
               + bone(20, -34, -30, 0.78) + bone(-24, -30, 22, 0.72))
    elif cargo == "kamen":
        top = (f'<path d="M-26,-26 l8,-18 l22,-2 l8,18 z M4,-26 l6,-16 l18,2 l4,14 z" fill="{STONE}" '
               f'stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    else:
        top = (f'<path d="M-34,-26 q14,-26 34,-26 q22,0 34,26 z" fill="#b89e74" stroke="{INK}" '
               f'stroke-width="6" stroke-linejoin="round"/>')
    if era == "modern":
        box = (f'<path d="M-38,-26 h76 v54 h-76 z" fill="#c9a26b" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
               f'<path d="M-38,-8 h76 M-38,10 h76" stroke="#8a6740" stroke-width="5"/>')
    else:
        box = (f'<path d="M-40,-26 h80 l-12,54 h-56 z" fill="#d9b77e" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
               f'<path d="M-36,-10 h72 M-32,8 h64" stroke="#8a6740" stroke-width="5"/>')
    return f'<g id="{pid}" transform="translate(50,-40)">{top}{box}</g>'


EXTRACT_HINT = ("extract", "retriev", "remov", "carr", "haul", "lift", "recover", "exhum", "took", "take")


def shot_crowd(p, c):
    """Skupina nosi naklad. Dve situacie:
      odnasanie (extract/retrieve/remove/carry - predvolene): vyjdu od kopy s nakladom
        v rukach a odnesu ho mimo zaber, nic nesypu;
      zasypavanie (bury/fill...): prinesu naklad ku kope a vysypu ho, kopa rastie.
    Ruky su vzdy dve a vzdy na naklade (poza HOLD, naklad je sucast tela riga)."""
    text = (c.get("text") or "").lower()
    dump = any(w in text for w in S.BURY_WORDS)
    era = (c.get("era") or "ancient").strip().lower()
    if era not in ("modern", "historic"):
        era = "ancient"
    cargo = S.CARGO.get(str((c.get("params") or {}).get("cargo") or "").strip().lower(), "hlina")
    key = S.pkey(c)
    show_prop = key not in ("object", "")
    crowd = ""
    for i in range(3):
        crowd += W.crowd_rig(f"{p}c{i}", era, i, held=_load_svg(f"{p}_ld{i}", "modern" if era == "modern" else "ancient", cargo))
    t0, t1, cu = c["t0"], c["t1"], c["cue_t"]
    D = t1 - t0
    src_x = 330.0
    src = ""
    if show_prop:
        psvg, pw, ph = S.prop_svg(p + "_prop", key)
        s = min(props.human_scale(key, pw, ph, 1.0), 360.0 / max(1.0, pw))
        src = f'<g transform="translate({src_x:.0f},{GY}) scale({s:.3f})">{psvg}</g>'
    mound = ""
    if dump:
        mound = f'<g id="{p}_mnd"><g transform="translate(-120,0)">{S._crowd_mound(cargo)}</g></g>'
    pieces = ""
    for i in range(3):
        pc = ""
        for k, (dx, dy) in enumerate(((0, 0), (34, 26), (-30, 30), (10, 58))):
            if cargo == "kosti":
                pc += f'<g transform="translate({dx},{dy})">{bone(0, 0, (k * 47) % 180 - 90, 0.62)}</g>'
            elif cargo == "kamen":
                pc += (f'<path d="M{dx - 18},{dy + 8} l6,-24 l24,-4 l10,20 l-8,14 z" fill="{STONE}" stroke="{INK}" '
                       f'stroke-width="5" stroke-linejoin="round"/>')
            else:
                pc += f'<g transform="translate({dx},{dy})">{S.CLOD}</g>'
        pieces += f'<g id="{p}_po{i}" opacity="0">{pc}</g>'
    world = f'{src}{mound}{crowd}{pieces}'
    if dump:
        cx0, cx1, z = 760.0, 740.0, 1.12
    else:
        cx0, cx1, z = 640.0, 900.0, 1.10
    svg = S.svg_wrap(_scene(p, c, (cx0 + cx1) / 2, z, st.HOR, world) + S.gold_layer(p, c["gold"], ""))
    js = _cam_js(p, cx0, cx1, z, z * 1.03, st.HOR - 960, st.HOR - 960, t0, t1, ease="none")
    js += "var MB = [];\n"
    if not dump:
        # odnasaju: zacnu pri kope (vlavo) a odidu doprava mimo zaber
        for i in range(3):
            # tempo tak, aby posledny odisiel z obrazu az na konci zaberu (inak je koniec prazdny)
            xs = src_x + 150 + i * 200
            xe = xs + 820
            js += (f'MB.push(Rig("{p}c{i}", {{ s: 1.05, x: {xs:.0f}, y: {GY}, seed: {14 + i}, eye: 0.7 }}));\n'
                   f'setPose(MB[{i}], HOLD, {t0:.3f});\n'
                   f'tl.set(MB[{i}], {{ w: 1, wa: 0, A: 22, ph: {i * 1.3:.2f} }}, {t0:.3f});\n'
                   f'tl.fromTo(MB[{i}], {{ x: {xs:.0f}, ph: {i * 1.3:.2f} }}, {{ x: {xe:.0f}, ph: {i * 1.3:.2f} + OM * {D:.3f}, '
                   f'duration: {D:.3f}, ease: "none", immediateRender: false }}, {t0:.3f});\n')
    else:
        # zasypavaju: prinesu naklad sprava, zastanu pri kope a vysypu ho (naklad sa naklopi dopredu)
        XS = [720, 890, 1060]
        acts = [t0 + D * 0.44, t0 + D * 0.62, t0 + D * 0.80]
        arrive = max(0.3, acts[0] - 0.1 - t0)
        for i in range(3):
            js += (f'MB.push(Rig("{p}c{i}", {{ s: 1.05, x: {XS[i] + 600}, y: {GY}, seed: {14 + i}, eye: 0.7, flip: -1 }}));\n'
                   f'setPose(MB[{i}], HOLD, {t0:.3f});\n'
                   f'tl.set(MB[{i}], {{ w: 1, wa: 0, A: 22, ph: {i * 1.1:.2f} }}, {t0:.3f});\n'
                   f'tl.fromTo(MB[{i}], {{ x: {XS[i] + 600}, ph: {i * 1.1:.2f} }}, {{ x: {XS[i]}, ph: {i * 1.1:.2f} + OM * {arrive:.3f}, '
                   f'duration: {arrive:.3f}, ease: "power1.out", immediateRender: false }}, {t0:.3f});\n'
                   f'tl.set(MB[{i}], {{ w: 0 }}, {t0 + arrive:.3f});\n')
        for i, ts in enumerate(acts):
            bx = XS[i] - 50
            js += (f'(function(){{ var r = MB[{i}], ld = node("{p}_ld{i}", {{ x: 50, y: -40, r: 0 }});\n'
                   f'pose(r, {{ lean: 18 }}, {ts - 0.16:.3f}, 0.16);\n'
                   f'tl.to(ld, {{ r: 115, duration: 0.2, ease: "power2.in" }}, {ts - 0.12:.3f});\n'
                   f'tl.to(ld, {{ r: 0, duration: 0.3, ease: "power2.out" }}, {ts + 0.35:.3f});\n'
                   f'pose(r, {{ lean: 4 }}, {ts + 0.35:.3f}, 0.3);\n'
                   f'var po = node("{p}_po{i}", {{ o: 0 }});\n'
                   f'var pc = ctl({{ tau: -1 }}, function (st) {{\n'
                   f'  if (st.tau < 0 || st.tau > 0.55) {{ po.o = 0; return; }}\n'
                   f'  po.o = 1; po.x = {bx} - ({bx} - 520) * 1.7 * st.tau; po.y = {GY - 170} - 120 * st.tau + 0.5 * 2200 * st.tau * st.tau;\n'
                   f'  po.r = 60 * st.tau; }});\n'
                   f'tl.fromTo(pc, {{ tau: 0 }}, {{ tau: 0.55, duration: 0.55, ease: "none", immediateRender: false }}, {ts - 0.02:.3f});\n'
                   f'tl.set(pc, {{ tau: -1 }}, {ts + 0.55:.3f}); }})();\n')
        js += (f'(function(){{ var m = cNode("{p}_mnd", 400, {GY}, {{ s: 0.45 }});\n'
               + "".join(f'tl.to(m, {{ s: {0.45 + 0.19 * (k + 1):.2f}, duration: 0.3, ease: "back.out(2)" }}, {ts + 0.25:.3f});\n'
                         for k, ts in enumerate(acts))
               + '})();\n')
    js += _flurry(p, c)
    js += S.js_gold(p, c, cu, "cam")
    return svg, js


S.SHOTS["action_crowd"] = shot_crowd


# ================================================================== koniec bez strihu (punch + otazka + slucka)
def _tok(s):
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


def final_times(c):
    """Casy zaverecneho zaberu - rovnake pre obraz (shot_final_walk) aj zvuk (build_spec).
    word/tp: zlate slovo punchu a cas, kedy ho hlas povie; q_t: slam otazky na zaciatku jej vety;
    tf: texty zacnu miznut (chvilu po dozneni otazky); tz: az potom kamera priblizi na frame 0."""
    t0, total = c["t0"], c["total"]
    pc, qc = c.get("punch"), c["question"]
    q_t = max(t0 + 0.3, qc["t0"] + 0.2)
    word = tp = None
    if pc:
        g = pc.get("gold") or {}
        word = ((pc.get("params") or {}).get("word")
                or (g.get("text") if g and "items" not in g else None)
                or S._punch_word(pc.get("text", ""), pc.get("cue") or ""))
        key = _tok(word)
        for w in pc.get("words") or []:
            wk = _tok(w["w"])
            if key and (wk == key or (len(key) > 3 and key in wk)):
                tp = w["s"] - 0.02
                break
        if tp is None:
            tp = pc["cue_t"]
        tp = max(t0 + 0.15, min(q_t - 0.45, tp))
    qw = qc.get("words") or []
    q_end = qw[-1]["e"] if qw else qc["t1"] - 0.3
    tf = max(q_t + 0.8, min(q_end + 0.35, total - 1.45))
    tz = tf + 0.12
    return {"word": word, "tp": tp, "q_t": q_t, "tf": tf, "tz": tz}


def _cloud_k(hy, AV, D, total, tz):
    """Najmensie K (drift oblakov 22*d - K*d^2), pri ktorom ziaden oblak zo sveta (world_far)
    neprejde cez slnko (880,330) / mesiac - simulacia tej istej kamery ako v JS (HillShot).
    Oblaky aj slnko/mesiac su z LOOK-u epizody (look.walk_cloud_spec); bez slnka netreba nic."""
    CL, SUN = LK.walk_cloud_spec()
    if SUN is None:
        return 0.0
    SX, SY, SR = SUN

    def ok(k):
        n = int(D * 24)
        for i in range(n + 1):
            d = D - i / 24.0
            tt = total - d
            e = 0.0 if tt < tz else (1 - math.cos(math.pi * min(1.0, (tt - tz) / max(0.01, total - tz)))) / 2
            z, lead = 1.22 + 0.46 * e, 175 - 55 * e
            bx = 100 - AV * d
            cx, cy = bx + lead, hy(bx) - 315 / z
            zf = 1 + (z - 1) * 0.25
            tx, ty = 540 + (cx - 540) * 0.18, 960 + (cy - 960) * 0.18
            off = 22 * d - k * d * d
            for xc, yc, s, sx, sy in CL:
                x, y = 540 + zf * (xc + off - tx), 960 + zf * (yc - ty)
                x0, x1 = x - 120 * s * sx * zf, x + 90 * s * sx * zf
                y0, y1 = y - 65 * s * sy * zf, y + 30 * s * sy * zf
                qx, qy = min(max(SX, x0), x1), min(max(SY, y0), y1)
                if (qx - SX) ** 2 + (qy - SY) ** 2 < SR * SR:
                    return False
        return True

    for j in range(0, 121):
        for k in ((j * 0.25,) if j == 0 else (j * 0.25, -j * 0.25)):
            if ok(k):
                return k
    return 0.0


def shot_final_walk(p, c):
    """Posledne vety (punch + zaverecna otazka) su JEDEN suvisly zaber v krajine uvodu:
    Bob kraca tym istym terenom tou istou rychlostou a fazou krokov ako vo walk_in, kamera ho
    plynulo sleduje (sirsie), zlate slovo slamne na svojom slove, otazka na svojej vete, texty
    zmiznu a az potom sa kamera plynulo priblizi na presny stav frame 0 (poloha, faza, kamera,
    oblaky, slnko, duch). Ziadny strih, ziadny ponor, ziadny otras."""
    body, hy, _show, jter = S.hill_world(p, c["bob"], c["prop"], with_ghost=True, loop_cls=True,
                                         world=c.get("world"), hero=c.get("hero"), x0=-3200)
    t0, total = c["t0"], c["total"]
    D = total - t0
    AV = 1200.0 / max(0.8, c["first_dur"])
    qc = c["question"]
    ft = final_times(c)
    word, tp, q_t, tf, tz = ft["word"], ft["tp"], ft["q_t"], ft["tf"], ft["tz"]
    lines = S.wrap2(qc["text"].strip().rstrip(".!"), per=14)
    fs = S.fit_size(max(lines, key=len), 104, 940)
    gold = ""
    if word:
        gold += f'<g id="{p}_pw" opacity="0">{num3d(p + "_pwn", str(word), S.fit_size(str(word), 170, 900))}</g>'
    gold += "".join(f'<g id="{p}_ask{i}" opacity="0">{num3d(p + "_askn" + str(i), t_, fs)}</g>'
                    for i, t_ in enumerate(lines))
    svg = S.svg_wrap(body + gold)
    # v jaskyni/kniznici nie je slnko (ani oblaky) - drift ostava ako vo frame 0
    K = 0.0 if W.interior(W.world_kind(c.get("world")), walk=True) else _cloud_k(hy, AV, D, total, tz)
    js = (f'var H = HillShot("{p}", "{c["bob"]}", function () {{ var d = TM.total - CLK.t; return 22 * d - {K:.3f} * d * d; }}, '
          f'function (x) {{ return {jter}; }});\n'
          f'var rg = H.rig, cam = H.cam;\n'
          f'tl.set(rg, {{ w: 1, wa: 1, lean: 7, head: 0, ph: PH0 - OM * {D:.3f} }}, {t0 - 0.01:.3f});\n'
          f'tl.to(rg, {{ ph: PH0, duration: {D:.3f}, ease: "none" }}, {t0:.3f});\n'
          f'tl.fromTo(cam, {{ bx: {100 - AV * D:.1f} }}, {{ bx: 100, duration: {D:.3f}, ease: "none", '
          f'immediateRender: false }}, {t0:.3f});\n'
          # pocas textov sirsi zaber (krajina + texty nad hlavou), po nich plynulo do kamery frame 0
          f'tl.set(cam, {{ lead: 175, z: 1.22 }}, {t0 - 0.01:.3f});\n'
          f'tl.to(cam, {{ lead: 120, z: 1.68, duration: {total - tz:.3f}, ease: "sine.inOut" }}, {tz:.3f});\n'
          f'tl.set(H.ghost, {{ o: 1 }}, {t0 - 0.01:.3f});\n')
    if word and tp is not None:
        js += (f'var pw = node("{p}_pw", {{ x: 540, y: 628, s: 0, o: 0, r: -3 }});\n'
               f'tl.set(pw, {{ o: 1 }}, {tp - 0.001:.3f});\n'
               f'slamIn(pw, {tp:.3f}, 1.3, 1, 0.22);\n'
               f'tl.to(pw, {{ o: 0, s: 0.9, duration: 0.2, ease: "power1.in" }}, {q_t - 0.22:.3f});\n'
               f'tl.set(rg, {{ eye: 1, mo: 1 }}, {tp:.3f});\n'
               f'tl.to(rg, {{ eye: 0, mo: 0, duration: 0.25 }}, {min(q_t - 0.1, tp + 1.0):.3f});\n')
    # otazka: Bob zdvihne hlavu k textu, pred priblizenim ju vrati (frame 0 ma head 0)
    js += (f'pose(rg, {{ head: -9 }}, {q_t + 0.05:.3f}, 0.4, "sine.inOut");\n'
           f'pose(rg, {{ head: 0 }}, {tf:.3f}, 0.45, "sine.inOut");\n')
    for i, _ln in enumerate(lines):
        at = q_t + i * 0.16
        js += (f'(function(){{ var a = node("{p}_ask{i}", {{ x: 540, y: {566 + i * int(fs * 1.16)}, s: 1, o: 0 }});\n'
               f'tl.set(a, {{ o: 1 }}, {at - 0.001:.3f});\n'
               f'slamIn(a, {at:.3f}, 1.3, 1, 0.22);\n'
               f'tl.to(a, {{ o: 0, duration: 0.3, ease: "power1.in" }}, {tf + i * 0.05:.3f}); }})();\n')
    # stopy v snehu/prachu pri poslednych krokoch - rovnake ako mal povodny zaber slucky
    step = math.pi / (math.pi * 1.9)
    for k in range(1, 4):
        tk = total - k * step
        if tk <= t0 + 0.05:
            break
        x = 100 - AV * (total - tk) - 25
        js += (f'(function(){{var n = node("{p}_pf{k - 1}", {{ o: 0 }});'
               f'tl.fromTo(n, {{ x: {x:.0f}, y: {hy(x) - 8:.0f}, s: 0.35, o: 0.95 }}, '
               f'{{ x: {x - 46:.0f}, y: {hy(x) - 40:.0f}, s: 1.35, o: 0, duration: 0.5, ease: "power1.out", '
               f'immediateRender: false }}, {tk:.3f});}})();\n')
    js += LK.fx_js(p)          # dazd: kvapky v TOTAL presne ako vo frame 0
    return svg, js


S.SHOTS["final_walk"] = shot_final_walk


# ================================================================== zaplnenie ostatnych zaberov
def _furnish(fn):
    """Zabery, ktore este nie su inscenovane (theory, punch, dav...), maju zem na 1290 (GCam up 330).
    Doplni im pozadie sveta (hory/ihlicnany/duny) medzi oblohu a kameru a v snehu vlocky -
    stredne pasmo obrazu uz nie je prazdny papier."""
    def wrapped(p, c):
        svg, js = fn(p, c)
        kind = _kind(c)
        if kind == "sea" or S.SURFACE in ("deck", "water"):
            return svg, js
        tag = f'<g id="{p}_cam">'
        i = svg.find(tag)
        if i < 0:
            return svg, js
        add = st.backdrop(p, kind, 960 + 330) + (st.flurry_svg(p) if kind == "snow" else "")
        out = svg[:i] + add + svg[i:]
        # dazd (LOOK) ide PRED scenu, ale POD zlate texty (tie su na konci obrazu); v miestnosti nie je
        rain = "" if _inside(c) else LK.rain_svg(p)
        if rain:
            js_ = [out.find(f'<g id="{p}_{g}"') for g in ("cnt", "w0")]
            j = min([k for k in js_ if k > 0] or [out.rfind("</g></svg>")])
            if j > 0:
                out = out[:j] + rain + out[j:]
        return out, js + _flurry(p, c)
    return wrapped


for _k in ("theory", "punch", "human_stack", "detail_compare"):
    if _k in S.SHOTS:
        S.SHOTS[_k] = _furnish(S.SHOTS[_k])

# insert = detail SAMOTNEHO PREDMETU bez postavy (kniha s vytrhnutou stranou, zastavene
# hodiny, prazdne haky) - vid insert_shots.py; registruje sa do S.SHOTS["insert"] sam.
import insert_shots  # noqa: E402,F401
