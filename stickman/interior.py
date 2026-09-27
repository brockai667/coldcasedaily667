# -*- coding: utf-8 -*-
"""Interier pre jeden zaber (params.inside = true): miestnost v dobe a farbach sveta epizody.

Svet epizody ostava rovnaky (uvod, koniec, slucka) - miestnost je len kulisa jedneho zaberu.
Kresli sa vo world-suradniciach okolo kamery zaberu (cam_x), podlaha presne na GY:
  zadna stena (+ lamperia / zruby / omietka podla stylu), soklova lista, okno s vyhladom
  na svet epizody (more, sneh, piesok, les, mesto, kopce), dvere, drobnosti na stene, podlaha.
Styl: cottage (pobrezie/kopec, do 1950) | cabin (sneh/les) | adobe (pust) | town (mesto) |
      stone (jaskyna) | flat (moderny byt, od 1950)."""
import math

import look
from props import INK, PAPER, WOOD

M = 310.0 / 1.75          # world jednotky na meter (Bob 1,75 m = 310)

STYLES = {
    "cottage": dict(wall="#f0ece0", wains="#c3cfd3", wline="#8fa3ad", trim="#6d8793", floor="#cfae80",
                    fline="#a98655", door="#7d6a52"),
    "cabin": dict(wall="#d9b27c", wains=None, wline="#a8814f", trim="#8a6337", floor="#c49a66",
                  fline="#94703f", door="#7a5230"),
    "adobe": dict(wall="#ecd8b0", wains="#dcc394", wline="#bda57a", trim="#a57b4a", floor="#d9a878",
                  fline="#b07e52", door="#8a6337"),
    "town": dict(wall="#efe2c9", wains="#a8743f", wline="#7d5530", trim="#7d5530", floor="#c9a476",
                 fline="#96703f", door="#6f4a2a", paper="#e6d3b1"),
    "stone": dict(wall="#d8cdb8", wains=None, wline="#a5987f", trim="#8c806b", floor="#cdbfa6",
                  fline="#a5987f", door="#7a5230"),
    "flat": dict(wall="#e9e6df", wains=None, wline="#c9c4b9", trim="#ffffff", floor="#d6c09b",
                 fline="#b39a72", door="#f4f2ec"),
}


def style_for(kind, era):
    if era == "modern":
        return "flat"
    return {"cave": "stone", "snow": "cabin", "forest": "cabin", "desert": "adobe", "city": "town"}.get(kind, "cottage")


# ------------------------------------------------------------------ vyhlad z okna
def _view(kind, x0, y0, w, h):
    """Co vidno z okna (obdlznik x0,y0,w,h): obloha papier, horizont sveta epizody
    (s LOOK-om v palete a terene epizody, v noci mesiac)."""
    lk = look.window_view(kind, x0, y0, w, h)
    if lk is not None:
        return lk
    hz = y0 + h * 0.58
    if kind in ("shore", "sea"):
        waves = "".join(f'<path d="M{x0 + 14 + i * 46},{hz + 22 + (i % 2) * 22} q10,-6 20,0 q10,6 20,0" fill="none" '
                        f'stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>' for i in range(int(w / 46)))
        return (f'<path d="M{x0},{hz} H{x0 + w} V{y0 + h} H{x0} Z" fill="#8ecae6"/>'
                f'<path d="M{x0},{hz} H{x0 + w}" stroke="{INK}" stroke-width="4"/>{waves}'
                f'<path d="M{x0 + w * 0.62},{hz} l14,-26 l22,8 l12,18 z" fill="#a39d8f" stroke="{INK}" stroke-width="3"/>')
    if kind == "snow":
        return (f'<path d="M{x0},{hz + 10} L{x0 + w * 0.3},{hz - h * 0.28} L{x0 + w * 0.55},{hz - h * 0.05} '
                f'L{x0 + w * 0.8},{hz - h * 0.32} L{x0 + w},{hz} V{y0 + h} H{x0} Z" fill="#f4f6f7" stroke="#8fa2ae" stroke-width="4"/>')
    if kind == "desert":
        return (f'<path d="M{x0},{hz} q{w * 0.3},-{h * 0.12} {w * 0.6},0 q{w * 0.2},{h * 0.08} {w * 0.4},-{h * 0.04} '
                f'V{y0 + h} H{x0} Z" fill="#e9d6a6" stroke="#bda57a" stroke-width="4"/>')
    if kind == "forest":
        trees = "".join(f'<path d="M{x0 + 10 + i * 34},{hz + 6} l16,-{40 + (i % 3) * 14} l16,{40 + (i % 3) * 14} z" '
                        f'fill="#6f8f6a" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>' for i in range(int(w / 34)))
        return f'<path d="M{x0},{hz} H{x0 + w} V{y0 + h} H{x0} Z" fill="#dcd9b3"/>{trees}'
    if kind == "city":
        roofs = "".join(f'<path d="M{x0 + i * 52},{hz + 30} V{hz - 16 - (i % 3) * 18} l26,-22 l26,22 V{hz + 30}" '
                        f'fill="#e6dfcf" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>' for i in range(int(w / 52) + 1))
        return roofs
    if kind == "cave":
        return f'<path d="M{x0},{y0} H{x0 + w} V{y0 + h} H{x0} Z" fill="#a1947d"/>'
    return (f'<path d="M{x0},{hz} Q{x0 + w * 0.35},{hz - h * 0.2} {x0 + w * 0.7},{hz - h * 0.04} T{x0 + w},{hz - h * 0.08} '
            f'V{y0 + h} H{x0} Z" fill="#cfd9a8" stroke="#a39d8f" stroke-width="4"/>')


def window(p, kind, cx, sill_y, w=190, h=240, modern=False):
    """Okno na stene: vyhlad vo vyrezе (clip), ram s prieckami, parapet, zavesy (stary styl)."""
    x0, y0 = cx - w / 2, sill_y - h
    clip = f'<clipPath id="{p}_wclip"><path d="M{x0},{y0} H{x0 + w} V{sill_y} H{x0} Z"/></clipPath>'
    view = (f'<g clip-path="url(#{p}_wclip)"><path d="M{x0},{y0} H{x0 + w} V{sill_y} H{x0} Z" fill="{look.window_sky()}"/>'
            f'{_view(kind, x0, y0, w, h)}</g>')
    frame = (f'<path d="M{x0},{y0} H{x0 + w} V{sill_y} H{x0} Z" fill="none" stroke="{INK}" stroke-width="10" '
             f'stroke-linejoin="round"/>'
             f'<path d="M{cx},{y0} V{sill_y}' + ("" if modern else f' M{x0},{y0 + h * 0.5} H{x0 + w}') + '" stroke="#ffffff" '
             f'stroke-width="9"/>'
             f'<path d="M{cx},{y0} V{sill_y}' + ("" if modern else f' M{x0},{y0 + h * 0.5} H{x0 + w}') + f'" stroke="{INK}" '
             f'stroke-width="3" opacity="0.5"/>'
             f'<path d="M{x0 - 22},{sill_y} H{x0 + w + 22} V{sill_y + 16} H{x0 - 22} Z" fill="#ffffff" stroke="{INK}" '
             f'stroke-width="6" stroke-linejoin="round"/>')
    curt = "" if modern else (
        f'<path d="M{x0 - 40},{y0 - 26} H{x0 + w + 40}" stroke="{WOOD}" stroke-width="9" stroke-linecap="round"/>'
        f'<path d="M{x0 - 34},{y0 - 24} Q{x0 - 10},{y0 + h * 0.5} {x0 - 30},{sill_y + 30} H{x0 + 8} Q{x0 + 2},{y0 + h * 0.4} {x0 + 18},{y0 - 24} Z" '
        f'fill="#c98b6b" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
        f'<path d="M{x0 + w + 34},{y0 - 24} Q{x0 + w + 10},{y0 + h * 0.5} {x0 + w + 30},{sill_y + 30} H{x0 + w - 8} '
        f'Q{x0 + w - 2},{y0 + h * 0.4} {x0 + w - 18},{y0 - 24} Z" fill="#c98b6b" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    return f'<defs>{clip}</defs>{view}{frame}{curt}'


def door(cx, gy, col, modern=False):
    w, h = 170, 2.05 * M
    x0 = cx - w / 2
    planks = "" if modern else "".join(f'<path d="M{x0 + k * w / 4:.0f},{gy - 8} V{gy - h + 8:.0f}" stroke="{INK}" '
                                       f'stroke-width="3" opacity="0.35"/>' for k in range(1, 4))
    panels = "" if not modern else (f'<path d="M{x0 + 24},{gy - h + 30:.0f} h{w - 48} v{h * 0.34:.0f} h{-(w - 48)} z '
                                    f'M{x0 + 24},{gy - h * 0.5:.0f} h{w - 48} v{h * 0.38:.0f} h{-(w - 48)} z" fill="none" '
                                    f'stroke="#c9c4b9" stroke-width="4"/>')
    return (f'<path d="M{x0 - 14},{gy} V{gy - h - 14:.0f} H{x0 + w + 14} V{gy}" fill="none" stroke="{INK}" stroke-width="9" '
            f'stroke-linejoin="round"/>'
            f'<path d="M{x0},{gy} V{gy - h:.0f} H{x0 + w} V{gy} Z" fill="{col}" stroke="{INK}" stroke-width="7" '
            f'stroke-linejoin="round"/>{planks}{panels}'
            f'<circle cx="{x0 + w - 26}" cy="{gy - h * 0.48:.0f}" r="9" fill="#c9a24a" stroke="{INK}" stroke-width="4"/>')


def room(p, kind, era, cam_x, gy, skip_window=False):
    """Miestnost okolo kamery zaberu. Vracia svg vo world-suradniciach (vsetko pod predmetmi zaberu)."""
    sname = style_for(kind, era)
    s = look.room_style(STYLES[sname])          # v noci tmavsia stena aj podlaha
    modern = sname == "flat"
    x0, x1 = cam_x - 2200, cam_x + 2200
    top = gy - 3000
    out = f'<path d="M{x0},{top} H{x1} V{gy} H{x0} Z" fill="{s["wall"]}"/>'
    if sname == "cabin":
        # zruby: vodorovne brvna s koncami, suky
        for k in range(1, 40):
            y = gy - k * 70
            out += f'<path d="M{x0},{y} H{x1}" stroke="{s["wline"]}" stroke-width="6"/>'
        for i, x in enumerate(range(int(x0) + 90, int(x1), 330)):
            y = gy - 35 - (i % 7) * 70
            out += f'<path d="{_ell(x, y, 12, 7)}" fill="none" stroke="{s["wline"]}" stroke-width="4"/>'
    elif sname == "stone":
        for k in range(1, 30):
            y = gy - k * 90
            off = (k % 2) * 90
            out += f'<path d="M{x0},{y} H{x1}" stroke="{s["wline"]}" stroke-width="4" opacity="0.7"/>'
            out += "".join(f'<path d="M{x},{y} v90" stroke="{s["wline"]}" stroke-width="4" opacity="0.7"/>'
                           for x in range(int(x0) + off, int(x1), 180))
    elif sname == "town":
        out += "".join(f'<path d="M{x},{top} V{gy}" stroke="{s["paper"]}" stroke-width="18"/>'
                       for x in range(int(x0), int(x1), 64))
    elif sname == "adobe":
        out += "".join(f'<path d="M{x},{y} q30,-8 60,0" stroke="{s["wline"]}" stroke-width="4" fill="none" opacity="0.6"/>'
                       for x, y in ((cam_x - 520, gy - 520), (cam_x + 90, gy - 610), (cam_x + 520, gy - 470), (cam_x - 160, gy - 700)))
    # lamperia / sokel
    if s.get("wains"):
        wh = 0.9 * M
        out += (f'<path d="M{x0},{gy - wh:.0f} H{x1} V{gy} H{x0} Z" fill="{s["wains"]}"/>'
                + "".join(f'<path d="M{x},{gy - wh + 14:.0f} V{gy - 20}" stroke="{s["wline"]}" stroke-width="4"/>'
                          for x in range(int(x0), int(x1), 52))
                + f'<path d="M{x0},{gy - wh:.0f} H{x1}" stroke="{s["trim"]}" stroke-width="16"/>'
                + f'<path d="M{x0},{gy - wh - 8:.0f} H{x1}" stroke="{INK}" stroke-width="4"/>')
    out += (f'<path d="M{x0},{gy - 24} H{x1} V{gy} H{x0} Z" fill="{s["trim"]}" stroke="{INK}" stroke-width="5"/>')
    # dvere vlavo, okno vpravo od stredu zaberu
    out += door(cam_x - 470, gy, s["door"], modern)
    if not skip_window:
        out += window(p, kind if kind != "cave" else "cave", cam_x + 260, gy - 0.95 * M, 190, 240, modern)
    if modern:
        out += (f'<path d="M{cam_x - 330},{gy - 1.1 * M:.0f} h26 v40 h-26 z" fill="#ffffff" stroke="{INK}" stroke-width="4"/>'
                f'<path d="M{cam_x + 120},{gy - 60} h180 v-120 h-180 z" fill="#e3e1db" stroke="{INK}" stroke-width="5"/>'
                + "".join(f'<path d="M{cam_x + 134 + k * 22},{gy - 172} v104" stroke="#c9c4b9" stroke-width="5"/>'
                          for k in range(8)))
    else:
        # polica s dzbanom nad dverami (stary styl)
        out += (f'<path d="M{cam_x - 600},{gy - 2.45 * M:.0f} h260 v14 h-260 z" fill="{WOOD}" stroke="{INK}" stroke-width="5"/>'
                f'<path d="M{cam_x - 560},{gy - 2.45 * M:.0f} v-46 q20,-14 40,0 v46 z" fill="#c9d3d6" stroke="{INK}" stroke-width="4"/>')
    # v noci svieti na stene lampa (teply svit)
    out += look.room_lamp(p, cam_x, gy, M)
    # podlaha
    fl = s["floor"]
    out += (f'<path d="M{x0},{gy} H{x1} V{gy + 2600} H{x0} Z" fill="{fl}" stroke="{INK}" stroke-width="9"/>'
            + "".join(f'<path d="M{x0},{gy + h} H{x1}" stroke="{s["fline"]}" stroke-width="4" opacity="0.6"/>'
                      for h in (40, 92, 160, 248, 360, 500))
            + "".join(f'<path d="M{x},{gy} l{(x - cam_x) * 0.5:.0f},900" stroke="{s["fline"]}" stroke-width="4" '
                      f'opacity="0.45" fill="none"/>' for x in range(int(cam_x) - 1300, int(cam_x) + 1400, 230)))
    return out


def _ell(cx, cy, rx, ry):
    return f"M{cx - rx:.0f},{cy:.0f} a{rx:.0f},{ry:.0f} 0 1 0 {2 * rx:.0f},0 a{rx:.0f},{ry:.0f} 0 1 0 {-2 * rx:.0f},0"


def table_under(pid, x, gy):
    """Stol v pravdivej velkosti pod predmetom (jedlo, lampa, hodiny...). Vrati (svg, vyska dosky)."""
    import props
    svg, w, h = props.prop_svg(pid, "table")
    s = props.human_scale("table", w, h, 1.0)
    return f'<g transform="translate({x:.0f},{gy}) scale({s:.3f})">{svg}</g>', h * s, w * s


# predmety, ktore v miestnosti stoja na stole / visia na stene
TABLE_ITEMS = ("meal", "lantern", "candle", "bottle", "radio", "clock", "book", "letter", "key")
WALL_ITEMS = ("window",)
