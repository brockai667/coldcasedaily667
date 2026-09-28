// Dokazy pre „Paper Case Files": karty na nastenke (photo/stat/note/doc/map), mosadzny spendlik, cervena snurka, peciatky,
// pisaci stroj, lupa a blesk fotoaparatu. PF.cards.make(o) -> karta { pin, out, focus, unfocus, redact, x, y, r, pinXY }.
// Karty su <g> vo vrstve M (vnutri #cf_sc_board_M, ak ho prostredie ma -> skryju sa spolu so scenou nastenky), peciatky vo vrstve F
// (#cf_sc_board_F, ak existuje), lupa a blesk vo vrstve F. Vsetko zacina skryte (opacity 0) a PF.cards.clear(t) to tam vrati (slucka).
// Ikony PF.cards.icon(meno): papierove vystrihy v boxe 200x200 so stredom 0,0 (filter #cut); neznama -> question. ID s prefixom cd_.
PF.cards = (function () {
  var TW = "font-family:'Courier New','Liberation Mono',monospace;font-weight:700;letter-spacing:0.04em", SF = "font-family:'Serif',serif";
  var INK = "#2b2320", BLACK = "#1a1512";
  var K = { cr: "#f6edd9", wh: "#fbf7ee", rd: "#d94a3b", rdD: "#a8322a", br: "#d8a94a", brD: "#a87f2e", sn: "#eef2f7", snS: "#cfd8e3", sl: "#8096b8",
    slD: "#5d6f93", mt: "#9aa3ad", mtD: "#6f7883", wd: "#9a6440", wdD: "#6b4029", or: "#e27b33", orD: "#b5561f", bl: "#3f77a8", blL: "#79acd9",
    gr: "#4f8a5a", grD: "#37664a", yl: "#f2c94c", ylD: "#d9a52c", mo: "#f3e9c8", moD: "#d6c79c", skin: "#f0d2b0" };

  // ---------- mala slovna zasoba tvarov (ikony aj karty)
  var f1 = function (v) { return Math.round(v * 10) / 10; };
  var R = function (x, y, w, h, f, rx, ex) { return '<rect x="' + f1(x) + '" y="' + f1(y) + '" width="' + f1(w) + '" height="' + f1(h) + '"' + (rx ? ' rx="' + rx + '"' : "") + ' fill="' + f + '"' + (ex || "") + '/>'; };
  var C = function (x, y, r, f, ex) { return '<circle cx="' + f1(x) + '" cy="' + f1(y) + '" r="' + f1(r) + '" fill="' + f + '"' + (ex || "") + '/>'; };
  var E = function (x, y, rx, ry, f, ex) { return '<ellipse cx="' + f1(x) + '" cy="' + f1(y) + '" rx="' + f1(rx) + '" ry="' + f1(ry) + '" fill="' + f + '"' + (ex || "") + '/>'; };
  var P = function (d, f, ex) { return '<path d="' + d + '" fill="' + f + '"' + (ex || "") + '/>'; };
  var L = function (d, c, w, ex) { return '<path d="' + d + '" fill="none" stroke="' + c + '" stroke-width="' + w + '" stroke-linecap="round" stroke-linejoin="round"' + (ex || "") + '/>'; };
  var G = function (m, ex) { return '<g' + (ex || "") + '>' + m + '</g>'; };
  var CUT = function (m) { return '<g filter="url(#cut)">' + m + '</g>'; };
  var RING = function (x, y, r, c, w) { return C(x, y, r, "none", ' stroke="' + c + '" stroke-width="' + w + '"'); };
  var T = function (x, y, s, fs, f, st, anc) { return '<text x="' + f1(x) + '" y="' + f1(y) + '" style="' + (st || TW) + ';font-size:' + f1(fs) + 'px;fill:' + f + ';text-anchor:' + (anc || "middle") + '">' + s + '</text>'; };
  var ESC = function (s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); };
  var pol = function (r, a) { a *= Math.PI / 180; return f1(r * Math.cos(a)) + " " + f1(r * Math.sin(a)); };
  var spark = function (x, y, r, f) { var q = r * 0.26; return P("M" + x + " " + (y - r) + " L" + f1(x + q) + " " + f1(y - q) + " L" + (x + r) + " " + y + " L" + f1(x + q) + " " + f1(y + q) + " L" + x + " " + (y + r) +
    " L" + f1(x - q) + " " + f1(y + q) + " L" + (x - r) + " " + y + " L" + f1(x - q) + " " + f1(y - q) + " Z", f); };
  var starD = function (ro, ri) { var d = ""; for (var k = 0; k < 5; k++) d += (k ? " L" : "M") + pol(ro, -90 + k * 72) + " L" + pol(ri, -54 + k * 72); return d + " Z"; };
  var sea = function (y, c) { return P("M-100 " + y + " Q-88 " + (y - 9) + " -75 " + y + " T-50 " + y + " T-25 " + y + " T0 " + y + " T25 " + y + " T50 " + y + " T75 " + y + " T100 " + y + " V" + (y + 22) + " H-100 Z", c); };
  var man = function (x, y, s, coat, hat) { return G(CUT(P("M-58 96 C-58 34 -34 -4 0 -4 C34 -4 58 34 58 96 Z", coat) + C(0, -46, 30, K.skin)) +
    (hat ? P("M-31 -50 C-31 -88 31 -88 31 -50 Z", hat) : ""), ' transform="translate(' + x + ' ' + y + ') scale(' + s + ')"'); };
  var tw = function (n, fs) { return n * 0.64 * fs; };   // sirka textu pisacieho stroja (Courier: 0.6em + medzera 0.04em)
  var fit = function (n, max, w) { return Math.min(max, w / (Math.max(1, n) * 0.64)); };
  var TXT = function (id, x, y, fs, f) { return '<text id="' + id + '" x="' + f1(x) + '" y="' + f1(y) + '" style="' + TW + ';font-size:' + f1(fs) + 'px;fill:' + f + '"></text>'; };

  // ---------- ikony (papierove vystrihy, 2-4 farby, stred 0,0, box 200x200)
  var ICONS = {
    tent: function () { return E(0, 66, 98, 15, K.sn) + CUT(P("M-18 -62 L72 -44 L98 60 L52 62 Z", K.orD) + P("M-88 62 L-18 -62 L52 62 Z", K.or)) +
      P("M-18 -24 L-42 62 L6 62 Z", "#3a2418") + L("M-18 -62 V-78 M72 -44 V-58", "#3a2418", 5) + L("M30 -30 L44 -12 L36 2 L50 18 L44 34", "#3a2418", 5); },
    mountain: function () { return CUT(P("M-100 72 L-46 -36 L12 72 Z", K.slD) + P("M-52 72 L30 -78 L100 72 Z", K.sl)) + P("M30 -78 L100 72 L56 72 Z", K.slD, ' opacity="0.5"') +
      P("M-46 -36 L-62 -4 L-53 -10 L-46 0 L-38 -10 L-29 -4 Z", K.sn) + P("M30 -78 L5 -32 L17 -40 L28 -26 L40 -40 L52 -32 Z", K.sn); },
    footprints: function () {
      var ft = function (x, y, m) { return G(P("M0 -28 C13 -28 17 -9 15 6 C13 21 9 30 0 30 C-9 30 -11 19 -11 6 C-11 -11 -12 -28 0 -28 Z", K.slD) + C(-7, -38, 5.5, K.slD) +
        C(1, -41, 4.5, K.slD) + C(8, -39, 4, K.slD) + C(13, -34, 3.5, K.slD) + C(16, -27, 3, K.slD), ' transform="translate(' + x + ' ' + y + ') rotate(20) scale(' + 0.85 * m + ' 0.85)"'); };
      return CUT(P("M-94 42 C-100 -12 -58 -88 12 -92 C82 -96 104 -38 96 12 C88 64 40 96 -22 94 C-70 92 -92 78 -94 42 Z", K.sn)) + ft(-39, 56, -1) + ft(9, 27, 1) + ft(-9, -27, -1) + ft(39, -56, 1); },
    snowflake: function () { var m = "";
      for (var k = 0; k < 6; k++) m += G(L("M0 0 V-86 M0 -50 L-20 -68 M0 -50 L20 -68 M0 -74 L-11 -86 M0 -74 L11 -86", K.blL, 11), ' transform="rotate(' + k * 60 + ')"');
      return CUT(m + C(0, 0, 17, K.wh)) + RING(0, 0, 17, K.blL, 4); },
    thermometer: function () { return CUT(R(-22, -94, 44, 150, K.wh, 22) + C(0, 62, 36, K.rd)) + R(-7, -46, 14, 108, K.rd, 7) + C(-10, 52, 9, "#f08a7c") +
      L("M10 -74 H17 M10 -52 H17 M10 -30 H17 M10 -8 H17 M10 14 H17", INK, 4) + L("M58 -84 V-36 M37 -72 L79 -48 M37 -48 L79 -72", K.blL, 6); },
    radiation: function () { var m = "";
      [90, 210, 330].forEach(function (a) { m += P("M" + pol(24, a - 30) + " L" + pol(80, a - 30) + " A80 80 0 0 1 " + pol(80, a + 30) + " L" + pol(24, a + 30) + " A24 24 0 0 0 " + pol(24, a - 30) + " Z", INK); });
      return CUT(C(0, 0, 96, K.yl)) + RING(0, 0, 88, INK, 4) + m + C(0, 0, 15, INK); },
    avalanche: function () { return CUT(P("M-100 80 L-24 -84 L100 80 Z", K.sl)) + P("M-24 -84 L-44 -40 L-32 -48 L-20 -34 L-6 -46 L10 -38 Z", K.sn) +
      CUT(C(12, -14, 20, K.snS) + C(38, 12, 28, K.sn) + C(10, 26, 22, K.sn) + C(62, 44, 32, K.sn) + C(26, 58, 28, K.sn) + C(-12, 56, 20, K.snS) + C(88, 66, 20, K.sn)) +
      C(60, -14, 8, K.sn) + C(84, 8, 6, K.sn) + C(-38, 20, 6, K.sn) + L("M-2 -40 L-28 -26 M20 -32 L0 -18", K.snS, 5); },
    ship: function () { return sea(62, K.bl) + CUT(P("M-94 26 H94 L74 64 H-72 Z", K.wd) + L("M-24 28 V-88 M34 28 V-84 M-90 26 L-108 12", "#3a2418", 5) +
      P("M-52 -84 H4 L8 -54 H-56 Z", K.cr) + P("M-60 -48 H12 L16 -8 H-64 Z", K.cr) + P("M38 -78 L80 -62 L90 18 H38 Z", K.cr)) + P("M34 -84 L56 -78 L34 -72 Z", K.rd); },
    waves: function () {
      var band = function (y, h, c, x0) { var d = "M" + x0 + " " + y;
        for (var x = x0; x < 100; x += 50) d += " C" + (x + 12) + " " + y + " " + (x + 16) + " " + (y - h) + " " + (x + 32) + " " + (y - h) + " C" + (x + 44) + " " + (y - h) + " " + (x + 48) + " " +
          f1(y - h * 0.45) + " " + (x + 40) + " " + f1(y - h * 0.4) + " C" + (x + 44) + " " + f1(y - h * 0.12) + " " + (x + 46) + " " + y + " " + (x + 50) + " " + y;
        return P(d + " V100 H" + x0 + " Z", c); };
      return '<svg x="-100" y="-100" width="200" height="200" viewBox="-100 -100 200 200">' + CUT(band(-24, 36, K.blL, -125) + band(22, 36, "#5a93c6", -100) + band(68, 36, K.bl, -125)) + '</svg>'; },
    lifeboat: function () { return sea(62, K.bl) + L("M-44 0 L-86 -64 M44 0 L86 -64", K.wd, 7) + E(-90, -72, 8, 17, K.wd, ' transform="rotate(-33 -90 -72)"') +
      E(90, -72, 8, 17, K.wd, ' transform="rotate(33 90 -72)"') + CUT(P("M-96 -4 H96 C88 40 60 62 0 62 C-60 62 -88 40 -96 -4 Z", K.or)) +
      P("M-93 8 H93 L89 20 H-89 Z", K.wh) + L("M-72 32 q9 10 18 0 t18 0 t18 0 t18 0 t18 0 t18 0 t18 0", "#7a3b1a", 3); },
    barrel: function () { return CUT(P("M-58 -80 C-80 -40 -80 40 -58 86 H58 C80 40 80 -40 58 -80 Z", K.wd)) +
      L("M-29 -78 C-38 -30 -38 34 -29 86 M0 -78 V86 M29 -78 C38 -30 38 34 29 86", K.wdD, 3) + L("M-71 -46 Q0 -34 71 -46 M-71 48 Q0 60 71 48", K.mtD, 10) +
      E(0, -80, 58, 14, "#c08a5c") + E(0, -80, 46, 9, "none", ' stroke="' + K.wdD + '" stroke-width="3"'); },
    logbook: function () { return CUT(R(-62, -84, 146, 176, K.cr, 6) + R(-78, -92, 146, 176, "#7a3b2e", 8)) + R(-78, -92, 24, 176, "#5a2a20", 6) +
      L("M74 -72 V76 M79 -66 V72", "#d6c8aa", 2) + R(-36, -64, 88, 44, K.cr, 4) + T(8, -32, "LOG", 30, INK, SF) +
      L("M8 6 V58 M-12 20 H28 M-15 40 Q8 66 31 40", K.br, 5) + RING(8, -1, 6, K.br, 4) + P("M30 82 V106 L38 98 L46 106 V82 Z", K.rd); },
    compass: function () { var tk = "";
      for (var k = 0; k < 8; k++) tk += "M" + pol(k % 2 ? 66 : 58, k * 45) + " L" + pol(74, k * 45) + " ";
      return RING(0, -95, 8, K.brD, 6) + CUT(C(0, 0, 90, K.br)) + C(0, 0, 76, K.cr) + L(tk, INK, 4) + T(0, -36, "N", 24, INK, SF) +
        G(P("M0 -62 L13 0 H-13 Z", K.rd) + P("M0 62 L13 0 H-13 Z", "#3a332e"), ' transform="rotate(32)"') + C(0, 0, 7, K.brD); },
    anchor: function () { return CUT(L("M0 -58 V74 M-44 -38 H44 M-74 16 Q-66 80 0 82 Q66 80 74 16", K.mt, 15) + RING(0, -74, 15, K.mt, 10) +
      P("M-82 -2 L-92 30 L-60 25 Z M82 -2 L92 30 L60 25 Z", K.mt)) + L("M-6 -56 C30 -36 -30 -6 8 12 C40 28 -12 50 6 66", "#c9a677", 6); },
    dish: function () { return CUT(P("M-12 26 L-44 92 H44 L12 26 Z", K.mtD) + G(E(6, 6, 86, 36, K.mt) + E(-2, -4, 86, 36, K.sn) + E(-2, -4, 62, 24, K.snS), ' transform="rotate(-32)"')) +
      L("M69 -48 L-41 -62 M-77 43 L-41 -62", "#3a332e", 4) + C(-41, -62, 8, "#3a332e"); },
    printout: function () { var h = "", m = "", rows = ["1 1 3 1 2", "2 1 6 1 1", "1 1 E 2 1", "1 3 Q 1 1", "2 1 U 1 3", "1 1 J 1 2", "1 2 5 1 1", "1 1 1 3 1"];
      for (var i = 0; i < 8; i++) { h += C(-66, -80 + i * 23, 4, "#cfc3a8") + C(66, -80 + i * 23, 4, "#cfc3a8"); m += T(0, -62 + i * 20, rows[i], 17, INK); }
      return CUT(R(-78, -96, 156, 192, K.wh, 3)) + R(-78, -96, 22, 192, "#ece3cf") + R(56, -96, 22, 192, "#ece3cf") + h + m +
        E(1, 2, 14, 62, "none", ' stroke="' + K.rd + '" stroke-width="5" transform="rotate(3 1 2)"'); },
    star: function () { var d = ""; for (var k = 0; k < 5; k++) d += "M0 0 L" + pol(94, -90 + k * 72) + " L" + pol(40, -54 + k * 72) + " Z ";
      return CUT(P(starD(94, 40), K.yl)) + P(d, K.ylD); },
    stopwatch: function () { var tk = "";
      for (var k = 0; k < 12; k++) tk += "M" + pol(k % 3 ? 54 : 48, k * 30) + " L" + pol(62, k * 30) + " ";
      return R(-13, -102, 26, 16, K.mt, 4) + R(-6, -88, 12, 14, K.mtD) + G(R(-7, -9, 14, 18, K.mt, 3), ' transform="translate(60 -60) rotate(45)"') + CUT(C(0, 12, 84, K.mt)) +
        C(0, 12, 70, K.cr) + G(P("M0 0 L0 -60 A60 60 0 0 1 " + pol(60, -56) + " Z", K.rd, ' opacity="0.25"') + L(tk, INK, 4) + L("M0 0 L" + pol(52, -56), K.rd, 6) + C(0, 0, 8, INK), ' transform="translate(0 12)"'); },
    satellite: function () { return G(L("M-34 0 H-24 M24 0 H34 M0 -30 V-44", K.mtD, 5) + CUT(R(-96, -20, 62, 40, K.bl, 3) + R(34, -20, 62, 40, K.bl, 3) + R(-24, -30, 48, 60, K.br, 6)) +
      L("M-80 -20 V20 M-65 -20 V20 M-50 -20 V20 M-96 0 H-34 M50 -20 V20 M65 -20 V20 M80 -20 V20 M34 0 H96", "#9cc3e6", 2) + L("M-24 -10 H24 M-24 10 H24", K.brD, 3) +
      P("M-22 -46 Q0 -24 22 -46 Z", K.sn), ' transform="rotate(-24)"'); },
    comet: function () { return P("M30 -70 C-14 -40 -60 20 -98 88 C-40 48 20 6 70 -18 Z", K.blL, ' opacity="0.8"') + P("M42 -58 C2 -30 -40 20 -70 66 C-24 36 18 4 60 -28 Z", K.mo) +
      C(52, -44, 36, "#fff6d6", ' opacity="0.3"') + CUT(C(52, -44, 24, "#fff6d6")) + spark(-48, -62, 11, K.yl) + spark(72, 52, 9, K.yl); },
    question: function () { return CUT(C(0, 0, 92, K.rd)) + L("M-32 -30 C-32 -74 38 -78 38 -34 C38 -6 2 -4 2 24", K.cr, 22) + C(2, 58, 14, K.cr); },
    magnifier: function () { return CUT(L("M30 30 L82 82", K.wdD, 26) + G(R(-10, -17, 20, 34, K.brD, 3), ' transform="translate(28 28) rotate(45)"') +
      C(-16, -16, 60, "#cfe3ee", ' stroke="' + K.br + '" stroke-width="16"')) + L("M-52 -28 A40 40 0 0 1 -28 -52", K.wh, 8); },
    envelope: function () { return CUT(R(-94, -60, 188, 124, K.cr, 6)) + L("M-90 60 L-16 6 M90 60 L16 6", "#d8c6a0", 4) + P("M-94 -58 L0 14 L94 -58 Z", "#e6d7b8") +
      L("M-92 -57 L0 14 L92 -57", "#cdb98f", 3) + C(0, 12, 20, K.rd) + RING(0, 12, 12, K.rdD, 3); },
    key: function () { return G(CUT(P("M-100 0 a34 34 0 1 0 68 0 a34 34 0 1 0 -68 0 Z M-82 0 a16 16 0 1 1 32 0 a16 16 0 1 1 -32 0 Z", K.br, ' fill-rule="evenodd"') +
      R(-36, -9, 124, 18, K.br, 5) + P("M58 8 H88 V42 H78 V28 H70 V42 H58 Z", K.br)) + R(-38, -15, 10, 30, K.brD, 3) + R(-20, -13, 8, 26, K.brD, 3), ' transform="rotate(-24)"'); },
    clock: function () { var tk = "";
      for (var k = 0; k < 12; k++) tk += "M" + pol(k % 3 ? 60 : 52, k * 30) + " L" + pol(68, k * 30) + " ";
      return CUT(C(0, 0, 94, K.wd)) + C(0, 0, 80, K.cr) + L(tk, INK, 5) + L("M0 0 L" + pol(36, -150) + " M0 0 L" + pol(58, -30), INK, 8) + L("M" + pol(12, 110) + " L" + pol(62, -70), K.rd, 3) + C(0, 0, 7, INK); },
    calendar: function () { var g = "";
      for (var i = 0; i < 12; i++) g += R(-64 + (i % 4) * 33, -10 + Math.floor(i / 4) * 30, 26, 22, "#e6dcc6", 4);
      return CUT(R(-82, -72, 164, 166, K.wh, 10)) + P("M-82 -54 a18 18 0 0 1 18 -18 h128 a18 18 0 0 1 18 18 v26 h-164 z", K.rd) + R(-48, -92, 12, 34, INK, 6) + R(36, -92, 12, 34, INK, 6) +
        g + L("M5 23 L25 39 M25 23 L5 39", K.rd, 6); },
    pin: function () { return E(0, 90, 30, 8, "#000", ' opacity="0.25"') + CUT(P("M0 90 C-14 56 -62 18 -62 -26 C-62 -62 -34 -88 0 -88 C34 -88 62 -62 62 -26 C62 18 14 56 0 90 Z", K.rd)) +
      P("M0 -88 C34 -88 62 -62 62 -26 C62 18 14 56 0 90 C20 44 40 12 40 -26 C40 -60 22 -84 0 -88 Z", K.rdD, ' opacity="0.45"') + C(0, -26, 24, K.wh); },
    eye: function () { return CUT(P("M-96 0 C-58 -60 58 -60 96 0 C58 60 -58 60 -96 0 Z", K.wh)) + C(0, 0, 38, K.bl) + C(0, 0, 18, INK) + C(12, -12, 8, K.wh) +
      L("M-96 0 C-58 -60 58 -60 96 0", INK, 8) + L("M-60 -40 L-72 -58 M-22 -52 L-26 -72 M22 -52 L26 -72 M60 -40 L72 -58", INK, 6); },
    moon: function () { return CUT(P("M24 -88 C-32 -80 -72 -32 -67 19 C-62 70 -16 99 35 90 C-5 72 -27 35 -27 -3 C-27 -42 -5 -74 24 -88 Z", K.mo)) +
      C(-50, 6, 9, K.moD) + C(-38, 48, 6, K.moD) + C(-44, -34, 6, K.moD) + spark(40, -30, 16, K.yl) + spark(62, 36, 11, K.yl); },
    lightning: function () { return CUT(C(-42, -42, 32, K.mt) + C(0, -60, 40, K.mt) + C(44, -42, 30, K.mt) + R(-76, -46, 150, 30, K.mt, 15)) + R(-68, -30, 136, 12, K.mtD, 6) +
      CUT(P("M12 -24 L-30 30 H-4 L-22 96 L38 16 H8 L28 -24 Z", K.yl)); },
    house: function () { return CUT(R(40, -78, 20, 44, "#8a4a3a") + R(-66, -12, 132, 98, K.cr) + P("M-88 -4 L0 -86 L88 -4 Z", "#b5442f")) + R(-18, 32, 36, 54, K.wd, 4) +
      C(10, 60, 3.5, INK) + R(-56, 6, 28, 26, K.yl) + R(28, 6, 28, 26, K.yl) + L("M-42 6 V32 M-56 19 H-28 M42 6 V32 M28 19 H56", "#8a4a3a", 3); },
    tree: function () { var tr = function (y, w, h) { return P("M0 " + (y - h) + " L" + (-w) + " " + y + " H" + w + " Z", K.gr) + P("M0 " + (y - h) + " L" + w + " " + y + " H0 Z", K.grD); };
      return R(-10, 62, 20, 30, K.wd) + CUT(tr(66, 78, 70) + tr(22, 60, 64) + tr(-24, 42, 70)) + P("M0 -94 L-12 -74 L-5 -78 L0 -71 L5 -78 L12 -74 Z", K.sn) +
        E(-34, 20, 16, 5, K.sn) + E(26, -26, 12, 4, K.sn) + E(-46, 64, 20, 5, K.sn) + E(44, 64, 16, 4, K.sn); },
    plane: function () { return G(CUT(P("M13 -18 L94 20 V32 L13 14 Z M-13 -18 L-94 20 V32 L-13 14 Z M11 60 L40 80 V88 L10 82 Z M-11 60 L-40 80 V88 L-10 82 Z", "#c3ccd8") +
      P("M0 -96 C11 -96 13 -78 13 -58 V66 C13 80 7 92 0 94 C-7 92 -13 80 -13 66 V-58 C-13 -78 -11 -96 0 -96 Z", K.sn)) + R(30, 8, 12, 24, K.mtD, 5) + R(-42, 8, 12, 24, K.mtD, 5) +
      P("M-7 -80 Q0 -87 7 -80 V-73 H-7 Z", K.bl), ' transform="rotate(40)"'); },
    report: function () { var ln = "";
      [-40, -22, -4, 14, 32].forEach(function (y, i) { ln += "M-50 " + y + " H" + (i === 4 ? 12 : 50) + " "; });
      return CUT(P("M-72 -94 H42 L74 -62 V94 H-72 Z", K.wh)) + P("M42 -94 V-62 H74 Z", "#e2d6bd") + R(-50, -72, 64, 12, INK, 3) + L(ln, "#8d847b", 6) +
        G(R(-34, 48, 92, 30, "none", 4, ' stroke="' + K.rd + '" stroke-width="4"') + R(-24, 58, 72, 10, K.rd, 2), ' transform="rotate(-12 12 63)"') +
        L("M-44 -104 V-58 a10 10 0 0 0 20 0 V-94 a6 6 0 0 0 -12 0 V-62", K.mt, 5); },
    person: function () { return man(0, 0, 1, "#c8703a", K.rdD); },
    group: function () { return man(-52, -6, 0.72, K.bl) + man(52, -6, 0.72, K.gr) + man(0, 14, 0.84, "#c8703a", K.rdD); },
    lock: function () { return L("M-40 -12 V-48 C-40 -98 40 -98 40 -48 V-12", K.mt, 18) + CUT(R(-66, -18, 132, 106, K.br, 14)) + R(-56, -8, 112, 8, "#e9c56a", 4) +
      C(0, 26, 14, INK) + P("M-7 30 H7 L10 60 H-10 Z", INK); },
    radio: function () { var sl = "";
      for (var y = -22; y <= 56; y += 13) sl += "M-70 " + y + " H2 ";
      return L("M44 -50 L72 -98", K.mt, 5) + C(72, -98, 6, K.mt) + CUT(R(-94, -50, 188, 132, K.wd, 14)) + R(-80, -36, 92, 104, "#ead9b4", 8) + L(sl, K.wdD, 4) +
        C(52, -6, 26, K.cr) + RING(52, -6, 26, K.wdD, 3) + L("M52 -6 L40 -26", K.rd, 4) + C(36, 50, 10, INK) + C(68, 50, 10, INK) + R(-82, 80, 22, 10, K.wdD, 3) + R(60, 80, 22, 10, K.wdD, 3); },
    camera: function () { return CUT(P("M-60 -46 L-44 -68 H44 L60 -46 Z", K.mt) + R(-94, -48, 188, 124, "#4a5360", 14)) + R(-94, -20, 188, 70, "#3a414c") + R(56, -62, 24, 12, K.rd, 3) +
      R(-82, -38, 30, 16, "#e8eef4", 3) + C(0, 14, 52, K.mt) + C(0, 14, 40, INK) + C(0, 14, 26, K.bl) + C(-9, 4, 8, K.wh, ' opacity="0.8"'); },
    skull: function () { return CUT(P("M0 -88 C56 -88 82 -48 80 -4 C78 28 62 42 50 48 L48 72 C48 86 36 92 24 92 H-24 C-36 92 -48 86 -48 72 L-50 48 C-62 42 -78 28 -80 -4 C-82 -48 -56 -88 0 -88 Z", K.cr)) +
      E(-32, 0, 22, 25, INK) + E(32, 0, 22, 25, INK) + C(-26, -8, 5, K.wh) + C(38, -8, 5, K.wh) + P("M0 24 L-11 44 H11 Z", INK) +
      L("M-34 64 H34 M-21 64 V86 M-7 64 V88 M7 64 V88 M21 64 V86", "#cdbd9c", 4); }
  };
  function icon(name) {
    if (!ICONS[name]) { if (name) console.warn("cards: neznama ikona '" + name + "' -> question"); name = "question"; }
    return "<g>" + ICONS[name]() + "</g>";
  }

  // ---------- spolocne prvky kariet: mosadzny spendlik, defs, vrstvy
  var pinHead = function (x, y, r) { return G(E(5, 8, 13, 10, "#1a0d06", ' opacity="0.4"') + C(0, 0, 15, K.br) + RING(0, 0, 13.5, "#9c7426", 3) + C(1, 2, 8, "#c99a3c") +
    E(-5, -6, 6, 4, "#fff3c4", ' opacity="0.9"'), ' transform="translate(' + f1(x) + ' ' + f1(y) + ') rotate(' + f1(r || 0) + ')"'); };
  function init() {
    if (document.getElementById("cd_cards")) return;
    var rr = PF.rnd(97), sp = "";   // opotrebovana pecatka: biela maska s ciernymi bodkami a skrabancami
    for (var i = 0; i < 120; i++) sp += C(-480 + rr() * 960, -220 + rr() * 440, 0.7 + rr() * rr() * 5, "#000");
    for (var j = 0; j < 9; j++) sp += L("M" + f1(-460 + rr() * 920) + " " + f1(-200 + rr() * 400) + " l" + f1(20 + rr() * 60) + " " + f1((rr() - 0.5) * 16), "#000", 1.4);
    document.getElementById("defs").insertAdjacentHTML("beforeend",
      '<clipPath id="cd_clipPh"><rect x="-206" y="-246" width="412" height="412"/></clipPath><clipPath id="cd_clipMap"><rect x="-214" y="-184" width="428" height="368"/></clipPath>' +
      '<linearGradient id="cd_gNight" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1d2848"/><stop offset="1" stop-color="#0d1224"/></linearGradient>' +
      '<radialGradient id="cd_gGlow"><stop offset="0" stop-color="#7688b6" stop-opacity="0.6"/><stop offset="1" stop-color="#7688b6" stop-opacity="0"/></radialGradient>' +
      '<radialGradient id="cd_gVig" r="0.72"><stop offset="0.6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.5"/></radialGradient>' +
      '<filter id="cd_strSh" filterUnits="userSpaceOnUse" x="-400" y="-400" width="1880" height="2720"><feDropShadow dx="3" dy="7" stdDeviation="2" flood-color="#1a0d06" flood-opacity="0.4"/></filter>' +
      '<filter id="cd_ink" filterUnits="userSpaceOnUse" x="-320" y="-320" width="640" height="640"><feTurbulence type="fractalNoise" baseFrequency="0.07" numOctaves="2" seed="11" result="n"/>' +
      '<feDisplacementMap in="SourceGraphic" in2="n" scale="7" xChannelSelector="R" yChannelSelector="G"/></filter>' +
      '<mask id="cd_wear" maskUnits="userSpaceOnUse" x="-700" y="-500" width="1400" height="1000"><rect x="-700" y="-500" width="1400" height="1000" fill="#fff"/>' + sp + '</mask>');
    PF.add(document.getElementById("cf_sc_board_M") || "M", '<g id="cd_M"><g id="cd_cards"></g><g id="cd_strings"></g><g id="cd_knots"></g></g>');
    PF.add(document.getElementById("cf_sc_board_F") || "F", '<g id="cd_stamps"></g>');
    PF.add("F", '<g id="cd_Fx"><g id="cd_mags"></g><rect id="cd_flash" x="-700" y="-900" width="2480" height="3720" fill="#ffffff" opacity="0"/></g>');
  }

  // ---------- obsah kariet (lokalne suradnice so stredom 0,0); typed = texty, ktore pisaci stroj dopise po pripnuti
  var SIZE = { photo: [480, 560], stat: [460, 300], note: [460, 360], doc: [460, 520], map: [480, 420] };
  var BODY = {
    photo: function (o, W, H, q, rr) {   // polaroid: biely ram, nocna "fotka" s ikonou, popis pisacim strojom
      var S = 412, x0 = -206, y0 = -246, gy = y0 + S * 0.8, cap = String(o.caption || "").toUpperCase().slice(0, 22), fs = fit(cap.length, 40, 430), st = "";
      for (var i = 0; i < 22; i++) { var sx = x0 + 8 + rr() * (S - 16), sy = y0 + 8 + rr() * S * 0.6;
        if (Math.abs(sx) > 130 || sy < y0 + 70) st += C(sx, sy, 0.9 + rr() * 2, "#fff6d6", ' opacity="' + f1(0.45 + rr() * 0.55) + '"'); }
      return { m: R(-W / 2, -H / 2, W, H, K.wh, 3) + '<g clip-path="url(#cd_clipPh)">' + R(x0, y0, S, S, "url(#cd_gNight)") + st + C(0, y0 + S * 0.48, 205, "url(#cd_gGlow)") +
          P("M-206 " + f1(gy) + " C-120 " + f1(gy - 30) + " -40 " + f1(gy + 20) + " 40 " + f1(gy - 6) + " C120 " + f1(gy - 28) + " 170 " + f1(gy + 4) + " 206 " + f1(gy - 12) + " V166 H-206 Z", "#080c1a", ' opacity="0.75"') +
          G(icon(o.icon), ' transform="translate(0 ' + f1(y0 + S * 0.48) + ') scale(1.42)"') + R(x0, y0, S, S, "url(#cd_gVig)") + P("M-206 -246 H-30 L-206 -70 Z", "#ffffff", ' opacity="0.07"') + "</g>" +
          R(x0, y0, S, S, "none", 0, ' stroke="#000" stroke-opacity="0.2" stroke-width="2"') + TXT(q + "_t0", -tw(cap.length, fs) / 2, 223 + fs * 0.3, fs, INK), typed: [[q + "_t0", cap]] };
    },
    stat: function (o, W, H, q) {        // kartoteka: velke cislo (Serif) + maly popis pisacim strojom
      var b = String(o.big == null ? "?" : o.big).slice(0, 8), sm = String(o.small || "").toUpperCase().slice(0, 18), fb = Math.min(120, 400 / (Math.max(2, b.length) * 0.6)), fs = fit(sm.length, 40, 400);
      return { m: R(-W / 2, -H / 2, W, H, K.cr, 3) + L("M-226 -46 H226 M-226 -2 H226 M-226 42 H226 M-226 86 H226 M-226 130 H226", "#a9bfd6", 2, ' opacity="0.55"') +
          L("M-226 -92 H226", "#d98b80", 3) + T(0, -4 + fb * 0.36, ESC(b), fb, K.rd, SF) + TXT(q + "_t0", -tw(sm.length, fs) / 2, 116, fs, INK), typed: [[q + "_t0", sm]] };
    },
    note: function (o, W, H, q) {        // lepiaci listok s ohnutym rohom: 1-3 riadky pisacim strojom
      var ls = (o.lines && o.lines.length ? o.lines : [o.text || "?"]).slice(0, 3).map(function (s) { return String(s).toUpperCase().slice(0, 20); });
      var n = Math.max.apply(null, ls.map(function (s) { return s.length; }).concat([4])), fs = fit(n, 46, 396), lh = fs * 1.55, x0 = -tw(n, fs) / 2, y0 = 30 - (ls.length - 1) * lh / 2 + fs * 0.3, m = "", ty = [];
      ls.forEach(function (s, i) { m += TXT(q + "_t" + i, x0, y0 + i * lh, fs, INK); ty.push([q + "_t" + i, s]); });
      return { m: P("M-230 -180 H230 V134 L184 180 H-230 Z", "#f1dc8f") + R(-230, -180, 460, 56, "#e8cf78") + CUT(P("M230 134 L184 180 L184 134 Z", "#f7e9b4")) + m, typed: ty };
    },
    doc: function (o, W, H, q, rr) {     // dokument: hlavicka, 5 riadkov "textu" ako ciary, zaciernenia (redact = indexy riadkov 0-4)
      var red = (o.redact || []).map(Number), reds = [], m = P("M-230 -260 H194 L230 -224 V260 H-230 Z", K.wh) + P("M194 -260 V-224 H230 Z", "#e2d6bd") +
        RING(-186, -206, 22, INK, 3) + P(starD(12, 5), INK, ' transform="translate(-186 -206)"') + T(-152, -195, ESC(String(o.title || "REPORT").toUpperCase().slice(0, 12)), 30, INK, TW, "start") +
        R(92, -222, 102, 30, "none", 3, ' stroke="' + K.rd + '" stroke-width="3"') + T(143, -201, "SECRET", 18, K.rd) + L("M-200 -166 H200", INK, 3) + L("M-200 -158 H200", INK, 1);
      for (var i = 0; i < 5; i++) { var y = -118 + i * 58, x = -200, end = i === 4 ? 40 : 200;
        while (x < end - 36) { var w = Math.min(end - x, 30 + rr() * 64); m += R(x, y - 6, w, 12, "#8d847b", 3); x += w + 12; }
        if (red.indexOf(i) >= 0) { m += '<g id="' + q + "_r" + i + '">' + R(-208, y - 18, x + 204, 36, BLACK, 3, ' filter="url(#cd_ink)"') + "</g>"; reds.push([q + "_r" + i, -208, y]); } }
      m += T(-200, 206, "SIGNED:", 16, "#8d847b", TW, "start") + L("M-112 202 c14 -30 26 -26 18 2 c-6 20 20 -26 34 -14 c10 8 -4 22 12 14 c12 -6 20 -16 40 -8", INK, 3) + L("M-120 214 H60", "#8d847b", 2);
      return { m: m, typed: [], reds: reds };
    },
    map: function (o, W, H, q, rr) {     // papierova mapa (mountains = vrstevnice, sea = pobrezie, sky = hviezdna mapa) + cerveny spendlik na o.place
      var kind = o.map === "sea" || o.map === "sky" ? o.map : "mountains", pl = o.place || {}, cl = function (v, a, b) { v = +v; return isNaN(v) ? 0.5 : Math.max(a, Math.min(b, v)); };
      var px = -214 + 428 * cl(pl.x, 0.07, 0.93), py = -184 + 368 * cl(pl.y, 0.2, 0.93), inner, i, k;
      var bar = G(R(0, 0, 30, 7, INK) + R(30, 0, 30, 7, "#fbf7ee", 0, ' stroke="' + INK + '" stroke-width="1.5"') + R(60, 0, 30, 7, INK) + T(0, -6, "0", 11, INK) + T(90, -6, "2 KM", 11, INK), ' transform="translate(-196 166)"');
      if (kind === "mountains") {
        var ring = function (cx, cy, n, st, ph) { var s = "";
          for (var k = n; k >= 1; k--) { var d = "";
            for (var a = 0; a < 48; a++) { var u = a * 0.1309, f = k * st * (1 + 0.12 * Math.sin(3 * u + ph) + 0.06 * Math.sin(5 * u + 2 * ph) + 0.05 * Math.sin(2 * u - ph));
              d += (a ? " L" : "M") + f1(cx + f * Math.cos(u)) + " " + f1(cy + f * Math.sin(u) * 0.82); }
            s += P(d + " Z", k === 1 ? "#c9ad76" : k === 2 ? "#d6c090" : "none", ' stroke="#9b7447" stroke-width="' + (k % 3 ? 1.7 : 3) + '"'); }
          return s; };
        inner = R(-240, -210, 480, 420, "#e8dbb6") + L("M-214 124 C-150 92 -110 150 -40 136 C30 122 60 176 130 190", "#78a6c4", 5) + ring(-70, -34, 6, 19, 0.7) + ring(140, 96, 4, 18, 2.1) +
          L("M-180 184 C-140 130 -120 70 -86 44 C-66 28 -76 2 -70 -24", "#b0452f", 3, ' stroke-dasharray="7 8"') + P("M-78 -28 l8 -14 l8 14 Z M132 92 l8 -14 l8 14 Z", INK) +
          G(P("M0 -24 L9 8 L0 2 L-9 8 Z", INK) + T(0, 24, "N", 16, INK, SF), ' transform="translate(186 -150)"') + bar;
      } else if (kind === "sea") {
        var co = "M-240 -210 H70 C50 -170 96 -140 64 -100 C34 -62 -16 -84 -40 -44 C-62 -8 -118 -26 -142 16 C-164 54 -198 40 -240 76 Z";
        inner = R(-240, -210, 480, 420, "#cfe0e0") + P(co, "none", ' stroke="#bcd4d6" stroke-width="70"') + P(co, "none", ' stroke="#a9c7cb" stroke-width="36"') + P(co, "#e9dab0", ' stroke="#8a7450" stroke-width="2.5"') +
          L("M60 40 q8 -8 16 0 t16 0 M130 100 q8 -8 16 0 t16 0 M-70 110 q8 -8 16 0 t16 0 M20 150 q8 -8 16 0 t16 0 M150 10 q8 -8 16 0 t16 0", "#7fa3ab", 2.5) +
          L("M-150 34 C-60 84 40 64 120 140 C150 166 180 170 214 176", INK, 2.5, ' stroke-dasharray="7 9" opacity="0.7"') +
          G(P("M0 -30 L7 -7 L30 0 L7 7 L0 30 L-7 7 L-30 0 L-7 -7 Z", INK) + P("M0 -30 L7 -7 L0 0 Z M30 0 L7 7 L0 0 Z M0 30 L-7 7 L0 0 Z M-30 0 L-7 -7 L0 0 Z", "#fbf7ee") +
            T(0, -36, "N", 16, INK, SF), ' transform="translate(166 -116)"') + bar;
      } else {
        var st = "", ra = "", cf = function (f) { return L("M" + f.map(function (p) { return p.join(" "); }).join(" L"), "#e9dfc4", 2, ' opacity="0.8"') + f.map(function (p) { return C(p[0], p[1], 4, "#fff6d6"); }).join(""); };
        for (i = 0; i < 70; i++) { var a = rr() * 6.2832, d = Math.sqrt(rr()) * 172; st += C(d * Math.cos(a), d * Math.sin(a), 0.8 + rr() * rr() * 3, "#fff6d6", ' opacity="' + f1(0.5 + rr() * 0.5) + '"'); }
        for (k = 0; k < 12; k++) ra += "M0 0 L" + pol(178, k * 30) + " ";
        inner = R(-240, -210, 480, 420, "#1e2a4c") + G(L(ra, "#e9dfc4", 1.2) + RING(0, 0, 60, "#e9dfc4", 1.2) + RING(0, 0, 120, "#e9dfc4", 1.2), ' opacity="0.28"') + RING(0, 0, 178, "#e9dfc4", 2.5) + st +
          cf([[-130, -40], [-96, -82], [-52, -66], [-20, -104], [28, -86]]) + cf([[44, 44], [88, 26], [130, 58], [106, 108], [60, 98], [44, 44]]) + spark(-96, -82, 12, "#fff6d6") + spark(106, 108, 10, "#fff6d6");
      }
      return { m: R(-W / 2, -H / 2, W, H, "#ecdfbf", 3) + '<g clip-path="url(#cd_clipMap)">' + inner + "</g>" +
          R(-80, -210, 160, 210, "#000", 0, ' opacity="0.04"') + R(-240, 0, 160, 210, "#000", 0, ' opacity="0.04"') + R(80, 0, 160, 210, "#000", 0, ' opacity="0.04"') +
          L("M-80 -208 V208 M80 -208 V208 M-238 0 H238", "#fffaf0", 1.5, ' opacity="0.45"') + R(-222, -192, 444, 384, "none", 0, ' stroke="#5e4b36" stroke-width="3"') +
          R(-216, -186, 432, 372, "none", 0, ' stroke="#5e4b36" stroke-width="1"') + '<g id="' + q + '_mk">' + C(px, py, 24, "none", ' stroke="' + K.rd + '" stroke-width="3" stroke-dasharray="6 5"') +
          G(ICONS.pin(), ' transform="translate(' + f1(px) + " " + f1(py - 32.4) + ') scale(0.36)"') + "</g>", typed: [], mk: [q + "_mk", px, py] };
    }
  };

  // ---------- karta
  var CARDS = [], STRS = [], STAMPS = [], MAGS = [], N = 0;
  function make(o) {
    o = o || {}; init(); N++;
    var kind = SIZE[o.kind] ? o.kind : "photo", sl = o.slot || {};
    if (kind !== o.kind) console.warn("cards: neznamy druh karty '" + o.kind + "' -> photo");
    if (Array.isArray(sl)) sl = { x: sl[0], y: sl[1], r: sl[2] };
    var s = { x: +(sl.x == null ? 540 : sl.x), y: +(sl.y == null ? 900 : sl.y), r: +(sl.r || 0) }, W = SIZE[kind][0], H = SIZE[kind][1], q = "cd_" + N;
    var b = BODY[kind](o, W, H, q, PF.rnd(4000 + N * 131)), py = -H / 2 + 24, a = s.r * Math.PI / 180, reds = b.reds || [], typed = b.typed || [];
    var pxy = [f1(s.x - py * Math.sin(a)), f1(s.y + py * Math.cos(a))]; pxy.x = pxy[0]; pxy.y = pxy[1];
    PF.add(document.getElementById("cd_cards"), '<g id="' + q + '" opacity="0" transform="translate(' + f1(s.x) + " " + f1(s.y) + ')"><g id="' + q + '_b">' +
      R(-W / 2 + 16, -H / 2 + 36, W, H, "#120a06", 4, ' id="' + q + '_ss" opacity="0" filter="url(#soft)"') + R(-W / 2 + 5, -H / 2 + 11, W, H, "#120a06", 4, ' id="' + q + '_hs" opacity="0" filter="url(#soft6)"') +
      b.m + '<g id="' + q + '_pin">' + pinHead(0, py, 0) + "</g></g></g>");
    var S0 = { tx: 0, ty: -140, r: s.r + 4, s: 1.08 };   // stav pred pripnutim (a po out/clear): vyssie, blizsie ku kamere
    PF.P(q + "_b", 0, 0, S0); PF.P(q + "_pin", 0, py, { s: 0 });
    reds.forEach(function (z) { PF.P(z[0], z[1], z[2], { sx: 0 }); });
    if (b.mk) PF.P(b.mk[0], b.mk[1], b.mk[2], { s: 0 });
    var c = { id: q, kind: kind, x: s.x, y: s.y, r: s.r, w: W, h: H, pinXY: pxy, on: false, strs: [] };
    c.pin = function (t) {               // spadne zhora (0.42 s, tien z mekkeho na tvrdy), dosadne, spendlik sa zabodne; potom pise stroj
      if (c.on) return; c.on = true;
      PF.O("#" + q, 0, 1, t, 0.08); PF.O("#" + q + "_ss", 0.6, 0, t, 0.42, "power1.in"); PF.O("#" + q + "_hs", 0, 0.5, t + 0.16, 0.26);
      PF.X(q + "_b", { ty: 0, s: 1, r: s.r }, t, 0.42, "power2.out");
      PF.X(q + "_b", { s: 0.982, r: s.r - 0.6 }, t + 0.42, 0.06, "power1.out"); PF.X(q + "_b", { s: 1, r: s.r }, t + 0.48, 0.24, "back.out(3)");
      PF.X(q + "_pin", { s: 1 }, t + 0.4, 0.22, "back.out(3.5)");
      if (b.mk) PF.X(b.mk[0], { s: 1 }, t + 0.72, 0.3, "back.out(2.6)");
      var tt = t + 0.62; typed.forEach(function (z) { tt = typewrite("#" + z[0], z[1], tt, 26) + 0.06; });
    };
    c.out = function (t) {               // odletí (0.35 s), skryje sa a vrati do stavu pred pripnutim
      if (!c.on) return; c.on = false;
      var d = s.x < 540 ? -1 : 1, z = t + 0.36;
      c.strs.forEach(function (r) { strOff(r, t, 0.15); });
      PF.X(q + "_b", { tx: d * 170, ty: -320, r: s.r + d * 22, s: 1.1 }, t, 0.35, "power2.in"); PF.O("#" + q, 1, 0, t + 0.14, 0.21);
      PF.X(q + "_b", S0, z, 0); PF.X(q + "_pin", { s: 0 }, z, 0); PF.O("#" + q + "_hs", 0.5, 0, z, 0);
      reds.forEach(function (r) { PF.X(r[0], { sx: 0 }, z, 0); }); if (b.mk) PF.X(b.mk[0], { s: 0 }, z, 0);
      typed.forEach(function (y) { PF.S("#" + y[0], { textContent: "" }, z); });
    };
    c.focus = function (t, dur) { PF.CAM(1.55, s.x, s.y, t, dur || 0.5, "power2.inOut"); };
    c.unfocus = function (t, dur) { PF.CAM(1, 540, 960, t, dur || 0.5, "power2.inOut"); };
    c.redact = function (t) { reds.forEach(function (r, i) { PF.X(r[0], { sx: 1 }, t + i * 0.16, 0.2, "power2.out"); }); };
    CARDS.push(c); return c;
  }

  // ---------- cervena snurka medzi spendlikmi (mierny previs; nad snurou kopia hlavicky spendlika = uzol)
  var xy = function (c) { var p = (c && c.pinXY) || c || [540, 960]; return [+(p[0] != null ? p[0] : p.x), +(p[1] != null ? p[1] : p.y)]; };
  function strOff(r, t, dur) {
    if (!r.on) return; r.on = false; dur = dur || 0.2;
    PF.O("#" + r.id + ", #" + r.id + "a, #" + r.id + "b", 1, 0, t, dur); PF.S("#" + r.id + "p", { attr: { "stroke-dashoffset": r.L } }, t + dur + 0.01);
  }
  function string(A, B, t, dur) {
    init(); dur = dur || 0.45;
    var r = { id: "cd_s" + (STRS.length + 1), on: true }, a = xy(A), b = xy(B), dx = b[0] - a[0], dy = b[1] - a[1], sag = 16 + Math.sqrt(dx * dx + dy * dy) * 0.07;
    PF.add(document.getElementById("cd_strings"), '<g id="' + r.id + '" opacity="0"><path id="' + r.id + 'p" d="M' + a[0] + " " + a[1] + " Q" + f1((a[0] + b[0]) / 2) + " " +
      f1((a[1] + b[1]) / 2 + 2 * sag) + " " + b[0] + " " + b[1] + '" fill="none" stroke="#c8352b" stroke-width="5" stroke-linecap="round" filter="url(#cd_strSh)"/></g>');
    PF.add(document.getElementById("cd_knots"), '<g id="' + r.id + 'a" opacity="0">' + pinHead(a[0], a[1], A && A.r) + '</g><g id="' + r.id + 'b" opacity="0">' + pinHead(b[0], b[1], B && B.r) + "</g>");
    PF.draw(r.id + "p", t, dur, "power1.inOut"); r.L = document.getElementById(r.id + "p").getAttribute("stroke-dashoffset");
    PF.S("#" + r.id + ", #" + r.id + "a", { opacity: 1 }, t); PF.S("#" + r.id + "b", { opacity: 1 }, t + dur * 0.95);
    STRS.push(r); if (A && A.strs) A.strs.push(r); if (B && B.strs) B.strs.push(r);
    return r.id;
  }
  function stringsOff(t) { STRS.forEach(function (r) { strOff(r, t, 0.2); }); }

  // ---------- peciatka: 2 ramiky + text (Courier bold), buchne (scale 2 -> 1, 0.12 s), drsny filter, opotrebovany atrament
  function stamp(text, x, y, t, o) {
    init(); o = Object.assign({ color: "#c9382d", rot: -8, size: 1, sub: "" }, o || {});
    var id = "cd_st" + (STAMPS.length + 1), s = String(text == null ? "" : text).toUpperCase(), sub = String(o.sub || "").toUpperCase(), c = o.color, z = o.size || 1;
    var fs = Math.min(92, 450 / (Math.max(1, s.length) * 0.7)), W = Math.max(1, s.length) * 0.7 * fs + 110, fs2 = sub ? Math.min(32, fs * 0.42, (W - 100) / (sub.length * 0.64)) : 0;
    var cap = fs * 0.62, H = 84 + cap + (sub ? fs2 * 0.72 + 30 : 0), by = -H / 2 + 42 + cap;
    PF.add(document.getElementById("cd_stamps"), '<g id="' + id + '" opacity="0"><g transform="translate(' + f1(x) + " " + f1(y) + ')" mask="url(#cd_wear)"><g filter="url(#rough)">' +
      R(-W / 2, -H / 2, W, H, "none", 14, ' stroke="' + c + '" stroke-width="10"') + R(-W / 2 + 15, -H / 2 + 15, W - 30, H - 30, "none", 6, ' stroke="' + c + '" stroke-width="4"') +
      T(fs * 0.05, by, ESC(s), fs, c, TW + ";letter-spacing:0.1em") +
      (sub ? L("M" + f1(-W / 2 + 38) + " " + f1(by + 17) + " H" + f1(W / 2 - 38), c, 3) + T(0, by + 30 + fs2 * 0.72, ESC(sub), fs2, c) : "") + "</g></g></g>");
    var S0 = { r: (o.rot || 0) + 7, s: 2 * z };
    PF.P(id, x, y, S0);
    PF.O("#" + id, 0, 0.92, t, 0.12, "power3.in"); PF.X(id, { r: o.rot || 0, s: z }, t, 0.12, "power3.in");
    PF.X(id, { s: z * 1.035 }, t + 0.12, 0.05, "power2.out"); PF.X(id, { s: z }, t + 0.17, 0.16, "power2.inOut");   // drobny odraz
    STAMPS.push({ id: id, on: true, S0: S0 }); return id;
  }
  function stampOff(id, t) { STAMPS.forEach(function (s) { if (s.id === id && s.on) { s.on = false; PF.O("#" + id, 0.92, 0, t, 0.25); PF.X(id, s.S0, t + 0.26, 0); } }); }

  // ---------- pisaci stroj: znak po znaku cez tl.set textContent, blikajuci blokovy kurzor, na konci zmizne; vracia cas konca
  function typewrite(sel, text, t, cps) {
    if (typeof sel === "string" && !/^[#.\[]/.test(sel) && document.getElementById(sel)) sel = "#" + sel;
    text = String(text == null ? "" : text); cps = cps || 22;
    var dt = 1 / cps, n = text.length, i;
    if (!n) { PF.S(sel, { textContent: "" }, t); return t; }
    for (i = 0; i <= n; i++) PF.S(sel, { textContent: text.slice(0, i) + (Math.floor(i * dt / 0.24) % 2 ? "" : "█") }, t + i * dt);
    PF.S(sel, { textContent: text }, t + n * dt + 0.14);
    return t + n * dt + 0.14;
  }

  // ---------- lupa (F): pride sprava zdola, jemne krouzi nad bodom, do t1 odide
  var LENS = null;
  function magnify(x, y, t0, t1) {
    init(); t1 = Math.max(t1, t0 + 0.8);
    if (!LENS) LENS = CUT(G(R(128, -21, 36, 42, K.brD, 6) + R(160, -22, 178, 44, "#6b4029", 22) + R(210, -22, 5, 44, "#4f2e1d"), ' transform="rotate(45)"') + RING(0, 0, 120, K.br, 22)) +
      RING(0, 0, 131, "#9c7426", 3) + RING(0, 0, 109, "#9c7426", 3) + C(0, 0, 108, "#dff0f7", ' fill-opacity="0.16"') +
      E(-46, -56, 40, 15, "#ffffff", ' opacity="0.5" transform="rotate(-42 -46 -56)"') + C(-80, -20, 7, "#ffffff", ' opacity="0.45"');
    var id = "cd_mg" + (MAGS.length + 1), S0 = { tx: 380, ty: 480, r: 16, s: 1.12 }, tin = Math.min(0.5, (t1 - t0) * 0.35), tout = Math.min(0.42, (t1 - t0) * 0.3), d0 = t0 + tin, d1 = t1 - tout, Pd = 1.6;
    PF.add(document.getElementById("cd_mags"), '<g id="' + id + '" opacity="0"><g id="' + id + 'x"><g id="' + id + 'y"><g transform="translate(' + f1(x) + " " + f1(y) + ')">' + LENS + "</g></g></g></g>");
    PF.P(id, x, y, S0); PF.P(id + "x", x, y); PF.P(id + "y", x, y);
    PF.O("#" + id, 0, 1, t0, 0.16); PF.X(id, { tx: 0, ty: 0, r: 0, s: 1 }, t0, tin, "power3.out");
    var k = Math.floor((d1 - d0 - Pd / 4) / Pd);   // krouzenie = dve kolmice s posunom o stvrt periody, konci vo vychodzom stave
    if (k >= 1) { PF.XY(id + "x", { tx: 10 }, d0, Pd / 2, "sine.inOut", 2 * k - 1); PF.XY(id + "y", { ty: 10 }, d0 + Pd / 4, Pd / 2, "sine.inOut", 2 * k - 1); }
    PF.X(id, S0, d1, tout, "power2.in"); PF.O("#" + id, 1, 0, t1 - 0.16, 0.16);
    MAGS.push({ id: id, t0: t0, t1: t1 }); return id;
  }
  function flash(t) { init(); PF.O("#cd_flash", 0, 0.85, t, 0.06, "power2.out"); PF.O("#cd_flash", 0.85, 0, t + 0.06, 0.24, "power1.in"); }
  function clear(t) {                    // slucka: karty odletia, snurky a peciatky zmiznu, lupa odide -> rovnaky stav ako snimok 0
    init(); CARDS.forEach(function (c) { c.out(t); }); stringsOff(t);
    STAMPS.forEach(function (s) { stampOff(s.id, t); });
    MAGS.forEach(function (m) { if (m.t0 <= t && m.t1 > t) PF.O("#" + m.id, 1, 0, t, 0.15); });
    PF.S("#cd_flash", { opacity: 0 }, t);
  }
  return { make: make, string: string, stringsOff: stringsOff, stamp: stamp, stampOff: stampOff, typewrite: typewrite, magnify: magnify, flash: flash,
    clear: clear, icon: icon, icons: Object.keys(ICONS), SIZE: SIZE };
})();
