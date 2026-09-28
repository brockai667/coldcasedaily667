# -*- coding: utf-8 -*-
"""HiddenEarth: obsadenie prieskumnikov, ktore sa v epizodach strieda (kip, ott, mara).

Kazdy hrdina ma ten isty rig ako props.rig (rovnake id: root, body, lL/lL2, lR/lR2, aL/aL2, aR/aR2, head,
hat, eyeL, eyeR, mouth, mouthO), takze chodza, klak, ukazovanie aj rekvizita v ruke z engine.js funguju bez
zmeny. Odlisuju sa SILUETOU, nie farbou klobuka:
  kip   maly (mierka 0,80), velka okruhla hlava, obri batoh so spacakom nad hlavou, siltovka, cerveny sal
  ott   vysoky a chudy (1,10), dlhy trup aj ruky, ovalna plesata hlava, okruhle okuliare, fuzy, brasna
  mara  stredna (0,96), cop (povieva), celenka, tubus s mapou krizom cez chrbat, sortky, turisticke topanky

Nohy ostavaju 60 + 60 a bedro na -120 ako u Boba - pozy z engine.js (KNEEL_A, CROUCH_LOOK...) su overene
priamou kinematikou pre tieto dlzky. Mierka `k` je na celej postave okolo chodidiel (vo vnutri {p}_root,
nad {p}_body), takze chodidla aj kolena ostanu pri kazdej poze na zemi; hrubky ciar su delene k, aby na
obrazovke sedeli s ostatnymi postavami.

{p}_flap (volitelne): sal / cop / brasna - engine.js ho natoci podla fazy krokov (data-a + data-b * sin 2ph),
nie podla casu, takze neviditelna slucka ostava presna.
"""
from props import INK, PAPER, RED

EXPLORERS = ("kip", "ott", "mara")


def _limb(p, a, b, l1, l2, foot=False, extra="", upper="", shoe=""):
    """Ako limb v props.rig; shoe = topanka na konci predkolenia (kresli sa cez chodidlo)."""
    f = f'<path d="M0,{l2} h17"/>' if foot else ""
    return (f'<g id="{p}_{a}"><path d="M0,0 V{l1}"/>{upper}<g transform="translate(0,{l1})"><g id="{p}_{b}">'
            f'<path d="M0,0 V{l2}"/>{f}{shoe}{extra}</g></g></g>')


def _eyes(p, S, e1, e2, r=4.6):
    """Zrenicky + biele oci prekvapenia (engine.js im meni polomer) na (x, y)."""
    return (f'<circle id="{p}_eyeL" cx="{e1[0] - 1}" cy="{e1[1]}" r="0" fill="#fff" stroke-width="{S(3.5)}"/>'
            f'<circle id="{p}_eyeR" cx="{e2[0] - 1}" cy="{e2[1]}" r="0" fill="#fff" stroke-width="{S(3.5)}"/>'
            f'<circle cx="{e1[0]}" cy="{e1[1]}" r="{r}" fill="{INK}" stroke="none"/>'
            f'<circle cx="{e2[0]}" cy="{e2[1]}" r="{r}" fill="{INK}" stroke="none"/>')


def _mouth(p, S, d, o):
    return (f'<path id="{p}_mouth" d="{d}" stroke-width="{S(5)}"/>'
            f'<ellipse id="{p}_mouthO" cx="{o[0]}" cy="{o[1]}" rx="0" ry="0" fill="{INK}" stroke="none"/>')


# ================================================================== KIP - maly prieskumnik
def _kip(p, S):
    T = 84
    hair, cap, capd = "#6b4428", "#f0b429", "#c98f12"
    pack, packd, mat = "#5f8f6b", "#46705a", "#6f8fa8"
    # obri batoh od bedra az nad hlavu + spacak navrchu = "hrb" v silete
    pk = (f'<path d="M-8,-14 V-150 Q-8,-180 -36,-182 H-62 Q-92,-180 -92,-150 V-30 Q-92,-12 -72,-12 H-24 '
          f'Q-8,-12 -8,-14 Z" fill="{pack}" stroke-width="{S(7)}"/>'
          f'<path d="M-8,-126 V-150 Q-8,-180 -36,-182 H-62 Q-92,-180 -92,-150 V-126 Q-50,-108 -8,-126 Z" '
          f'fill="{packd}" stroke-width="{S(6)}"/>'
          f'<path d="M-55,-118 V-90 H-43 V-118" fill="{packd}" stroke-width="{S(5)}"/>'
          f'<path d="M-92,-78 H-102 Q-110,-78 -110,-70 V-36 Q-110,-28 -102,-28 H-92 Z" fill="{packd}" '
          f'stroke-width="{S(6)}"/>'
          f'<path d="M-86,-209 H-18 A13,13 0 0 1 -18,-183 H-86 A13,13 0 0 1 -86,-209 Z" fill="{mat}" '
          f'stroke-width="{S(6)}"/>'
          f'<path d="M-68,-208 V-184 M-36,-208 V-184" stroke="{packd}" stroke-width="{S(6)}"/>')
    # cerveny sal: koniec povieva za hlavou (v pokoji visi sikmo dole, pri chodzi sa zdvihne)
    scarf = (f'<g transform="translate(-8,-{T - 6})"><g id="{p}_flap" data-a="38" data-b="9">'
             f'<path d="M2,-6 C-16,-4 -32,12 -48,34 L-36,42 C-22,24 -10,10 4,6 Z" fill="{RED}" stroke-width="{S(5)}"/>'
             f'<path d="M-2,4 C-12,12 -20,26 -26,44 L-14,48 C-10,32 -4,20 6,12 Z" fill="{RED}" stroke-width="{S(5)}"/>'
             f'<path d="M-46,38 l-7,7 M-40,42 l-5,8 M-24,46 l-4,8 M-17,48 l-1,8" stroke-width="{S(3.5)}"/>'
             f'</g></g>')
    front = (f'<path d="M-8,-120 Q12,-100 7,-74 Q3,-40 -6,-22" stroke="{packd}" stroke-width="{S(7)}"/>'
             f'<path d="M-13,-{T + 4} Q3,-{T - 5} 18,-{T + 1} L18,-{T - 10} Q2,-{T - 19} -12,-{T - 8} Z" fill="{RED}" '
             f'stroke-width="{S(5)}"/>')
    head = (f'<path d="M-39,-76 L-57,-72 L-46,-65 L-59,-55 L-43,-52 Z" fill="{hair}" stroke-width="{S(5)}"/>'
            f'<circle cx="0" cy="-48" r="46" fill="{PAPER}"/>'
            + _eyes(p, S, (16, -57), (38, -57), 5.3)
            + f'<ellipse cx="42" cy="-37" rx="8.5" ry="5" fill="#f4a7a3" stroke="none" opacity="0.8"/>'
            + _mouth(p, S, "M13,-27 q12,7 24,-1", (26, -24))
            + f'<g id="{p}_hat"><path d="M-47,-61 C-51,-109 48,-114 47,-74 Z" fill="{cap}" stroke-width="{S(7)}"/>'
              f'<path d="M37,-73 C57,-78 79,-74 88,-65 C74,-61 53,-62 39,-66 Z" fill="{capd}" stroke-width="{S(6)}"/>'
              f'<path d="M-2,-101 Q7,-88 6,-74" stroke="{capd}" stroke-width="{S(4)}"/>'
              f'<circle cx="-2" cy="-102" r="4.2" fill="{capd}" stroke-width="{S(3.5)}"/></g>')
    thigh = f'<path d="M-11,-8 H11 L13,24 H-13 Z" fill="#c9a36a" stroke-width="{S(6)}"/>'
    shoe = f'<path d="M-7,44 H6 L7,53 Q21,54 23,62 V64 H-8 Z" fill="#7a5230" stroke-width="{S(6)}"/>'
    return dict(back="", pack=pk + scarf, front=front, head=head, thigh=thigh, shoe=shoe)


# ================================================================== OTT - vysoky geograf
def _ott(p, S):
    T = 116
    hair, brow = "#d8d2c6", "#9d978c"
    jk, jkd, sat, satd = "#8b6d4c", "#6d5238", "#9a6536", "#7a4c28"
    front = (f'<path d="M-19,-{T - 2} H19 L27,4 H-27 Z" fill="{jk}" stroke-width="{S(7)}"/>'
             f'<path d="M-10,-{T - 2} L2,-{T - 30} L14,-{T - 2} Z" fill="#f4f1ea" stroke-width="{S(5)}"/>'
             f'<path d="M2,-{T - 8} l-11,-6 v13 z M2,-{T - 8} l11,-6 v13 z" fill="#c0392b" stroke-width="{S(4)}"/>'
             f'<path d="M-17,-62 H-2 V-50 H-17 Z" fill="{jkd}" stroke-width="{S(4)}"/>'
             f'<path d="M-11,-62 L-8,-76" stroke="#e0a526" stroke-width="{S(5)}"/>'
             f'<circle cx="9" cy="-70" r="3.5" fill="{INK}" stroke="none"/>'
             f'<circle cx="10" cy="-44" r="3.5" fill="{INK}" stroke="none"/>'
             # brasna na remeni krizom cez hrud - kyva sa pri chodzi
             f'<g transform="translate(4,-{T - 6})"><g id="{p}_flap" data-a="4" data-b="5">'
             f'<path d="M0,0 L-30,74" stroke="{satd}" stroke-width="{S(6)}"/>'
             f'<path d="M-50,70 H-14 V100 Q-14,108 -22,108 H-42 Q-50,108 -50,100 Z" fill="{sat}" stroke-width="{S(6)}"/>'
             f'<path d="M-50,70 H-14 V84 Q-32,92 -50,84 Z" fill="{satd}" stroke-width="{S(5)}"/>'
             f'<path d="M-35,84 h6 v9 h-6 z" fill="#d8b24a" stroke-width="{S(3)}"/>'
             f'</g></g>')
    head = (f'<path d="M0,2 V-12"/>'
            f'<ellipse cx="0" cy="-53" rx="31" ry="41" fill="{PAPER}"/>'
            f'<path d="M-29,-36 C-40,-46 -40,-70 -29,-80 C-34,-68 -33,-52 -21,-40 Z" fill="{hair}" stroke-width="{S(4)}"/>'
            f'<path d="M-9,-92 q10,-6 22,-2 M-4,-94 q8,-5 16,-2" stroke-width="{S(3)}"/>'
            + _eyes(p, S, (8, -61), (29, -61), 4.4)
            + f'<path d="M1,-76 q6,-5 13,-1 M22,-76 q6,-5 13,-1" stroke="{brow}" stroke-width="{S(5.5)}"/>'
              f'<circle cx="7.5" cy="-61" r="9.5" fill="#e3f1f5" fill-opacity="0.35" stroke-width="{S(4)}"/>'
              f'<circle cx="29" cy="-61" r="9.5" fill="#e3f1f5" fill-opacity="0.35" stroke-width="{S(4)}"/>'
              f'<path d="M17,-62 q2.2,-3 2.6,0 M-2,-62 L-15,-58" stroke-width="{S(3.5)}"/>'
              f'<path d="M22,-42 C16,-48 8,-46 6,-38 C11,-40 16,-39 22,-37 C28,-39 33,-40 38,-38 C36,-46 28,-48 22,-42 Z" '
              f'fill="{hair}" stroke-width="{S(3.5)}"/>'
            + _mouth(p, S, "M16,-32 q7,4 14,-1", (23, -30))
            + f'<g id="{p}_hat"></g>')
    shoe = f'<path d="M-6,52 H5 Q19,53 21,60 V63 H-7 Z" fill="#3a3431" stroke-width="{S(5)}"/>'
    return dict(back="", pack="", front=front, head=head, thigh="", shoe=shoe)


# ================================================================== MARA - prieskumnicka s mapou
def _mara(p, S):
    T = 96
    hair, hair_d, band = "#a4512b", "#7d3a1c", "#2a9d8f"
    shirt, belt, shorts = "#7d9a5c", "#6b4a2e", "#cbb07c"
    tube, tcap, strap = "#b98a4e", "#7a5230", "#5e4128"
    # tubus s mapou krizom cez chrbat: spodok trci za bedrom, vrch nad lopatkou vedla copu
    back = (f'<g transform="translate(-34,-70) rotate(-34)">'
            f'<path d="M-12,-96 H12 V92 H-12 Z" fill="{tube}" stroke-width="{S(6)}"/>'
            f'<path d="M-12,-78 H12 M-12,74 H12" stroke="{tcap}" stroke-width="{S(9)}"/>'
            f'<path d="M-13,92 H13 V100 H-13 Z" fill="{tcap}" stroke-width="{S(5)}"/>'
            # z otvoreneho tubusu trci zrolovana mapa
            f'<path d="M-8,-96 V-122 H8 V-96 Z" fill="#f1e2b8" stroke-width="{S(5)}"/>'
            f'<path d="M-8,-122 q8,-12 16,0" fill="#e2cd95" stroke-width="{S(4)}"/>'
            f'<path d="M-13,-96 H13 V-104 H-13 Z" fill="{tcap}" stroke-width="{S(5)}"/></g>')
    front = (f'<path d="M-22,-{T - 4} H22 L25,-24 H-25 Z" fill="{shirt}" stroke-width="{S(7)}"/>'
             f'<path d="M-8,-{T - 4} L2,-{T - 16} L12,-{T - 4}" stroke-width="{S(4.5)}"/>'
             f'<path d="M5,-72 H18 V-61 H5 Z" fill="none" stroke="#56703f" stroke-width="{S(4)}"/>'
             f'<path d="M-26,-27 H26 V-17 H-26 Z" fill="{belt}" stroke-width="{S(5)}"/>'
             f'<path d="M4,-28 h9 v12 h-9 z" fill="#d8b24a" stroke-width="{S(3)}"/>'
             f'<path d="M12,-{T - 6} L-14,-22" stroke="{strap}" stroke-width="{S(6)}"/>')
    tail = (f'<g transform="translate(-32,-66)"><g id="{p}_flap" data-a="10" data-b="7">'
            f'<path d="M4,-4 C-22,-14 -46,0 -52,26 C-56,46 -46,62 -38,70 C-40,50 -32,30 -12,18 C-2,12 6,6 4,-4 Z" '
            f'fill="{hair}" stroke-width="{S(6)}"/>'
            f'<path d="M-40,44 q4,-16 16,-24 M-30,54 q0,-14 8,-22" stroke="{hair_d}" stroke-width="{S(3.5)}"/>'
            f'<path d="M-3,-9 L6,5" stroke="{band}" stroke-width="{S(10)}"/></g></g>')
    head = (tail
            + f'<circle cx="0" cy="-43" r="41" fill="{PAPER}"/>'
            + _eyes(p, S, (13, -51), (33, -51), 4.8)
            + f'<path d="M15,-56 l3,-6 M19,-55 l5,-4 M35,-56 l3,-6 M39,-55 l5,-4" stroke-width="{S(3.2)}"/>'
            + _mouth(p, S, "M11,-26 q11,7 22,-1", (23, -23))
            + f'<path d="M34,-66 C30,-84 12,-90 -4,-88 C-26,-86 -44,-70 -45,-46 C-45,-34 -42,-26 -38,-20 '
              f'C-34,-34 -30,-46 -22,-56 C-10,-68 16,-64 34,-66 Z" fill="{hair}" stroke-width="{S(6)}"/>'
              f'<path d="M-30,-68 q10,-10 24,-12 M-36,-50 q4,-12 14,-18" stroke="{hair_d}" stroke-width="{S(3.5)}"/>'
              f'<path d="M31,-72 C18,-92 -20,-96 -39,-70" stroke="{INK}" stroke-width="{S(14)}"/>'
              f'<path d="M31,-72 C18,-92 -20,-96 -39,-70" stroke="{band}" stroke-width="{S(8)}"/>'
            + f'<g id="{p}_hat"></g>')
    thigh = f'<path d="M-12,-8 H12 L13,26 H-13 Z" fill="{shorts}" stroke-width="{S(6)}"/>'
    shoe = (f'<path d="M-7,37 H6 V43 H-7 Z" fill="#f4f1ea" stroke-width="{S(4)}"/>'
            f'<path d="M-7,43 H6 L7,52 Q21,53 23,61 V64 H-8 Z" fill="{belt}" stroke-width="{S(6)}"/>')
    return dict(back=back, pack="", front=front, head=head, thigh=thigh, shoe=shoe)


# k = mierka postavy, torso = dlzka trupu (Bob 100), drop = rameno pod vrchom trupu, arm = rameno + predlaktie,
# fx = predne rameno posunute dopredu (velka hlava: zdvihnuta ruka pri ukazovani inak prejde cez tvar)
CAST = {
    # kip: arm predlzena z povodnych (48, 46) - to je rovnaka dlzka ako Bob (props.rig), ale kip ma
    # k=0.80 (Bob de facto k=1), takze na obrazovke vysla ukazovacia ruka (pose POINT) o 20 % kratsia
    # nez Bobovi - pri jeho velkej hlave to vyzeralo ako kusa ruky pri sale/brade, nie ako ukazovanie.
    # (60, 58) * k=0.80 = rovnaky efektivny dosah ako Bob (48, 46) * k=1 - overene snapshotom oproti
    # detektivovi v tom istom zabere ("spot"). Ostatne pozy (dig/kneel/reach/...) kip este nepouziva.
    "kip": dict(k=0.80, torso=84, drop=6, arm=(60, 58), fx=16, draw=_kip),
    "ott": dict(k=1.10, torso=116, drop=8, arm=(54, 50), fx=5, draw=_ott),
    "mara": dict(k=0.96, torso=96, drop=8, arm=(46, 44), fx=3, draw=_mara),
}


def rig(p, hero, prop="", held=""):
    H = CAST[hero]
    k = H["k"]

    def S(w):
        return f"{w / k:.2f}"
    d = H["draw"](p, S)
    T, (a1, a2) = H["torso"], H["arm"]
    sh = T - H["drop"]
    return (f'<g id="{p}_root" fill="none" stroke="{INK}" stroke-width="{S(9)}" stroke-linecap="round" '
            f'stroke-linejoin="round"><g transform="scale({k})"><g id="{p}_body">'
            f'{d["back"]}'
            f'<g transform="translate(0,-{sh})">{_limb(p, "aR", "aR2", a1, a2)}</g>'
            f'{_limb(p, "lR", "lR2", 60, 60, True, upper=d["thigh"], shoe=d["shoe"])}'
            f'{d["pack"]}'
            f'<path d="M0,0 V-{T}"/>'
            f'{_limb(p, "lL", "lL2", 60, 60, True, upper=d["thigh"], shoe=d["shoe"])}'
            f'{d["front"]}'
            f'<g transform="translate(0,-{T})"><g id="{p}_head">{d["head"]}</g></g>'
            f'{held}'
            f'<g transform="translate({H["fx"]},-{sh})">{_limb(p, "aL", "aL2", a1, a2, False, prop)}</g>'
            f'</g></g></g>')


# ------------------------------------------------------------------ typicke veci do ruky (rekvizita `prop`)
# kreslene vzpriamene okolo uchopu (0,0); volajuci ich posunie na koniec predlaktia a otoci podla pozy
def item(hero, S=lambda w: w):
    if hero == "kip":        # fotoaparat
        return (f'<path d="M-26,-30 H26 V6 H-26 Z" fill="#3f4a55" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
                f'<path d="M-16,-30 V-38 H0 V-30" fill="#3f4a55" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
                f'<circle cx="6" cy="-12" r="13" fill="#a9c7d8" stroke="{INK}" stroke-width="6"/>'
                f'<circle cx="2" cy="-16" r="4" fill="#ffffff" stroke="none"/>'
                f'<circle cx="-18" cy="-22" r="3" fill="{RED}" stroke="none"/>')
    if hero == "ott":        # otvoreny zapisnik
        return (f'<path d="M0,-34 L-40,-40 V6 L0,12 L40,6 V-40 Z" fill="#f4f1ea" stroke="{INK}" stroke-width="7" '
                f'stroke-linejoin="round"/>'
                f'<path d="M0,-34 V12" stroke="{INK}" stroke-width="5"/>'
                f'<path d="M-32,-26 L-8,-23 M-32,-14 L-8,-11 M-32,-2 L-14,0 M8,-23 L32,-26 M8,-11 L26,-13" '
                f'stroke="#7d8a94" stroke-width="4" stroke-linecap="round"/>'
                f'<path d="M-40,6 L0,12 L40,6 V14 L0,20 L-40,14 Z" fill="#b5543c" stroke="{INK}" stroke-width="6" '
                f'stroke-linejoin="round"/>')
    if hero == "mara":       # rozvinuta mapa s cestou a krizikom (drzi ju za lavy dolny roh - neprekryje tvar)
        return (f'<g transform="translate(46,10)">'
                f'<path d="M-50,-46 H44 V16 H-50 Z" fill="#f1e2b8" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
                f'<path d="M-50,-46 q-12,0 -12,10 v52 q0,-10 12,-10" fill="#e2cd95" stroke="{INK}" stroke-width="6"/>'
                f'<path d="M-36,4 Q-20,-30 0,-18 T30,-34" fill="none" stroke="#b5543c" stroke-width="5" '
                f'stroke-dasharray="9 8" stroke-linecap="round"/>'
                f'<path d="M24,-40 l12,12 M36,-40 l-12,12" stroke="{RED}" stroke-width="6" stroke-linecap="round"/>'
                f'<path d="M-26,-36 q10,6 22,0 M8,2 q10,-8 22,-2" fill="none" stroke="#7fa06a" stroke-width="5" '
                f'stroke-linecap="round"/></g>')
    return ""
