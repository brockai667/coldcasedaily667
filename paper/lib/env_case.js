// Prostredie: PAPIEROVY SPIS (Paper Case Files) - tmavy stol s lampou, korkova nastenka, nocna diorama miesta cinu. ID s prefixom cf_.
// Sceny sa postavia naraz ako skupiny <g id="cf_sc_<meno>_<B|M|F>"> (viditelna len uvodna), prepina PF.sceneSet("cf", ...):
//   desk  - stol zhora: drevo, kuzel lampy (cf_lamp), fascikel (cf_cover) s harkom (cf_sheet1..3), hrnek, ceruzka, lupa (F)
//   board - korkova nastenka cez celu obrazovku; karty (cards_case.js) idu do M na env.slot(i)
//   site  - nocna diorama podla o.site: mountains | sea | sky, rekvizity o.props, efekty env.siteFx(meno, t0, t1)
// Zony: #day vlavo hore (y 112-300), titulky od y 1566 -> tam len pozadie; obsah y 400-1480, x 60-1020.
// Slucka: nekonecne pohyby maju periody z PF.loopPeriod, efekty koncia v neutrale -> snimok PF.VO.total = snimok 0.
PF.envCase = function (o) {
  o = Object.assign({ scene: "desk", site: "mountains", caseNo: "000", title: "UNSOLVED" }, o || {});
  var SC = ["desk", "board", "site"], PROPS = { mountains: ["tent", "footprints", "trees"], sea: ["ship", "buoy", "rocks"], sky: ["dish", "observatory", "trees"] };
  if (SC.indexOf(o.scene) < 0) { console.warn("envCase: neznama scena '" + o.scene + "' -> desk"); o.scene = "desk"; }
  if (!PROPS[o.site]) { console.warn("envCase: neznamy site '" + o.site + "' -> mountains"); o.site = "mountains"; }
  var sc0 = o.scene, SITE = o.site, T = PF.tl, TOT = PF.VO.total > 0 ? PF.VO.total : 0;
  var props = (o.props || PROPS[SITE]).filter(function (p) { return PROPS[SITE].indexOf(p) >= 0; });
  var has = function (p) { return props.indexOf(p) >= 0; };

  // ---------- markup: male pomocne funkcie (SVG ako retazce)
  var f1 = function (v) { return String(Math.round(v * 10) / 10); };
  var esc = function (s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); };
  var E = function (tag, a, inner) { var s = "<" + tag; for (var k in a) if (a[k] != null) s += " " + k + '="' + a[k] + '"';
    return s + (inner == null ? "/>" : ">" + inner + "</" + tag + ">"); };
  var g = function (a, inner) { return E("g", a || {}, inner || ""); };
  var pa = function (d, fill, a) { return E("path", Object.assign({ d: d, fill: fill }, a)); };
  var re = function (x, y, w, h, fill, a) { return E("rect", Object.assign({ x: f1(x), y: f1(y), width: f1(w), height: f1(h), fill: fill }, a)); };
  var ci = function (x, y, r, fill, a) { return E("circle", Object.assign({ cx: f1(x), cy: f1(y), r: f1(r), fill: fill }, a)); };
  var el = function (x, y, rx, ry, fill, a) { return E("ellipse", Object.assign({ cx: f1(x), cy: f1(y), rx: f1(rx), ry: f1(ry), fill: fill }, a)); };
  var tx = function (x, y, s, a) { return E("text", Object.assign({ x: f1(x), y: f1(y) }, a), esc(s)); };
  var poly = function (p) { return "M" + p.map(function (q) { return f1(q[0]) + " " + f1(q[1]); }).join(" L") + " Z"; };
  var rot = function (r, x, y) { return "rotate(" + r + " " + f1(x) + " " + f1(y) + ")"; };
  var line = function (d, col, w, a) { return pa(d, "none", Object.assign({ stroke: col, "stroke-width": w, "stroke-linecap": "round" }, a)); };
  var mono = function (fs, fill, a) { return Object.assign({ "font-family": "'Courier New', 'Liberation Mono', monospace", "font-weight": 700,
    "letter-spacing": "0.04em", "font-size": fs, fill: fill || "#2b2320" }, a); };
  var serif = function (fs, fill, a) { return Object.assign({ "font-family": "Serif", "font-size": fs, fill: fill || "#2b2320" }, a); };
  var FULL = function (fill, a) { return re(-300, -300, 1680, 2520, fill, a); };   // plocha cez celu obrazovku aj pri priblizeni kamery
  var tear = function (p0, p1, amp, step, rr) {   // roztrhnuty okraj: body medzi p0 a p1 s nahodnou kolmou odchylkou
    var dx = p1[0] - p0[0], dy = p1[1] - p0[1], L = Math.hypot(dx, dy), n = Math.max(2, Math.round(L / step)), out = [];
    for (var i = 1; i < n; i++) { var d = (rr() - 0.5) * 2 * amp; out.push([p0[0] + dx * i / n - dy / L * d, p0[1] + dy * i / n + dx / L * d]); }
    return out;
  };
  var paper = function (x, y, w, h, amp, seed, edges) {   // obdlznik papiera, okraje z edges ("trbl") su roztrhnute
    var rr = PF.rnd(seed), c = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]], p = [];
    for (var i = 0; i < 4; i++) { p.push(c[i]); if ((edges || "").indexOf("trbl"[i]) >= 0) p = p.concat(tear(c[i], c[(i + 1) % 4], amp, 16, rr)); }
    return poly(p);
  };
  var pin = function (x, y, col) { return el(x + 5, y + 9, 12, 8, "#000", { opacity: 0.35 }) + ci(x, y, 12.5, col) +   // pripinacik spredu
    ci(x, y, 12.5, "none", { stroke: "#000", "stroke-opacity": 0.3, "stroke-width": 2 }) + ci(x - 4, y - 4, 4.2, "#fff", { opacity: 0.6 }); };
  var clip = function (x, y, r) { return line("M-8 18 V-36 a9 9 0 0 1 18 0 V32 a13 13 0 0 1 -26 0 V-22", "#b3bac2", 5,   // kancelarska spona
    { transform: "translate(" + x + " " + y + ") rotate(" + r + ")", "stroke-linejoin": "round", filter: "url(#cf_sh)" }); };
  var stops = function (s) { return s.map(function (q) { return '<stop offset="' + q[0] + '" stop-color="' + q[1] + '"' + (q[2] == null ? "" : ' stop-opacity="' + q[2] + '"') + "/>"; }).join(""); };
  var lin = function (id, s, a) { return E("linearGradient", Object.assign({ id: id, x1: 0, y1: 0, x2: 0, y2: 1 }, a), stops(s)); };
  var rad = function (id, s, a) { return E("radialGradient", Object.assign({ id: id }, a), stops(s)); };
  var US = function (cx, cy, r, a) { return Object.assign({ gradientUnits: "userSpaceOnUse", cx: cx, cy: cy, r: r }, a); };
  var LAMP = "#ffd9a0", NIGHT = "#03050b";
  document.getElementById("defs").insertAdjacentHTML("beforeend",
    '<filter id="cf_sh" x="-15%" y="-15%" width="130%" height="135%"><feDropShadow dx="0" dy="9" stdDeviation="4" flood-color="#0b0604" flood-opacity="0.55"/></filter>' +
    '<filter id="cf_cutN" x="-15%" y="-15%" width="130%" height="135%"><feDropShadow dx="0" dy="7" stdDeviation="3" flood-color="#02040a" flood-opacity="0.6"/></filter>' +
    '<filter id="cf_cork" x="0" y="0" width="1" height="1" color-interpolation-filters="sRGB">' +   // korok: tmave flaky + zrno (tmave a svetle bodky)
    '<feTurbulence type="fractalNoise" baseFrequency="0.011" numOctaves="2" seed="3" result="lo"/>' +
    '<feColorMatrix in="lo" type="matrix" values="0 0 0 0 0.62 0 0 0 0 0.41 0 0 0 0 0.23 2.6 0 0 0 -1.25" result="blot"/>' +
    '<feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="2" seed="8" result="hi"/>' +
    '<feColorMatrix in="hi" type="matrix" values="0 0 0 0 0.40 0 0 0 0 0.25 0 0 0 0 0.13 3.6 0 0 0 -1.95" result="dk"/>' +
    '<feColorMatrix in="hi" type="matrix" values="0 0 0 0 0.94 0 0 0 0 0.77 0 0 0 0 0.55 0 3.6 0 0 -2.1" result="lt"/>' +
    '<feMerge><feMergeNode in="SourceGraphic"/><feMergeNode in="blot"/><feMergeNode in="dk"/><feMergeNode in="lt"/></feMerge></filter>' +
    rad("cf_gLamp", [[0, LAMP, 0.5], [0.4, LAMP, 0.2], [1, LAMP, 0]], US(780, 620, 1150, { fx: 1000, fy: 110 })) +
    rad("cf_gLampB", [[0, LAMP, 0.42], [0.45, LAMP, 0.14], [1, LAMP, 0]], US(960, 120, 1300)) +
    rad("cf_gGlowL", [[0, "#ffe2b0", 0.55], [1, "#ffe2b0", 0]]) + rad("cf_gWarm", [[0, "#ffcf7a", 0.75], [1, "#ffcf7a", 0]]) +
    rad("cf_gCyan", [[0, "#bff0ff", 0.9], [1, "#bff0ff", 0]]) + rad("cf_gRedLt", [[0, "#ff6a55", 0.8], [1, "#ff6a55", 0]]) +
    rad("cf_gHalo", [[0, "#f3e9c8", 0.34], [0.3, "#f3e9c8", 0.12], [1, "#f3e9c8", 0]]) +
    rad("cf_gVigD", [[0.42, "#0b0604", 0], [0.8, "#0b0604", 0.5], [1, "#0b0604", 0.82]], US(760, 640, 1300)) +
    rad("cf_gVigB", [[0.5, "#140a05", 0], [0.85, "#140a05", 0.42], [1, "#140a05", 0.72]], US(600, 940, 1200)) +
    rad("cf_gVigS", [[0.55, NIGHT, 0], [0.9, NIGHT, 0.45], [1, NIGHT, 0.65]], US(540, 900, 1150)) +
    lin("cf_gSky", [[0, "#17203a"], [1, "#0d1224"]]) + lin("cf_gHor", [[0, "#2f3f68", 0], [1, "#2f3f68", 0.55]]) +
    lin("cf_gMist", [[0, "#5d6f96", 0], [1, "#5d6f96", 0.5]]) + lin("cf_gSnowG", [[0, "#e6ecf3"], [1, "#b9c5d4"]]) +
    lin("cf_gSea", [[0, "#1f4d6b"], [1, "#163a52"]]) + lin("cf_gLt", [[0, "#c7d3ff"], [1, "#6d80c0"]]) +
    lin("cf_gShD", [[0, "#000", 0.5], [1, "#000", 0]]) + lin("cf_gShU", [[0, "#000", 0], [1, "#000", 0.5]]));

  var LAY = { B: "", M: "", F: "" };
  var scene = function (name, parts) { ["B", "M", "F"].forEach(function (L) {
    LAY[L] += g({ id: "cf_sc_" + name + "_" + L, opacity: name === sc0 ? null : 0 }, parts[L] || ""); }); };
  var lampHead = function (id) { return el(1000, 30, 470, 340, "url(#cf_gGlowL)", { id: id }) +   // okraj lampy vpravo hore (F, rozmazany)
    g({ filter: "url(#dof)" }, el(1050, -46, 240, 128, "#17110d", { transform: rot(-26, 1050, -46) }) + el(985, 36, 170, 20, "#ffe6b8", { opacity: 0.8, transform: rot(-26, 985, 36) })); };

  // ---------- DESK: pohlad zhora; predna doska fascikla sa otvara prelozenim dolava cez chrbat (x 170)
  var wood = (function () { var rr = PF.rnd(31), m = FULL("#3b2a22"), lt = "", dk = "";
    for (var i = 0; i < 6; i++) { var x0 = -300 + i * 280; m += re(x0, -300, 280, 2520, ["#3e2c23", "#35261e", "#3a2920"][i % 3]);
      for (var k = 0; k < 9; k++) { var x = x0 + 12 + k * 30 + rr() * 10, a = 4 + rr() * 14;
        var d = "M" + f1(x) + " -300 C" + f1(x + a) + " 300 " + f1(x - a) + " 800 " + f1(x) + " 1150 S" + f1(x - a * 0.8) + " 1900 " + f1(x + a * 0.3) + " 2220";
        if (k % 3) lt += d; else dk += d; }
      m += re(x0 - 2, -300, 4, 2520, "#170f0b", { opacity: 0.8 }); }
    m += line(lt, "#4d3729", 2, { opacity: 0.5 }) + line(dk, "#281b14", 3, { opacity: 0.5 });
    [[250, 1700, 1], [900, 1600, 0.8], [620, 250, 0.9]].forEach(function (q) { for (var j = 1; j < 5; j++)
      m += el(q[0], q[1], (8 + j * 12) * q[2], (3 + j * 6) * q[2], "none", { stroke: "#26190f", "stroke-width": 2, opacity: 0.55 }); });
    return m; })();
  var FX0 = 170, FY0 = 440, FW = 740, FH = 980, FCY = FY0 + FH / 2, no = esc(o.caseNo), ttl = String(o.title).toUpperCase().trim() || "UNSOLVED", TL = [ttl];
  if (ttl.length > 13 && ttl.indexOf(" ") > 0) { var best = -1; for (var i = 0; i < ttl.length; i++)   // dlhy nazov -> 2 riadky
    if (ttl[i] === " " && (best < 0 || Math.abs(i - ttl.length / 2) < Math.abs(best - ttl.length / 2))) best = i; TL = [ttl.slice(0, best), ttl.slice(best + 1)]; }
  var tfs = Math.max(30, Math.min(TL.length > 1 ? 50 : 76, Math.floor(520 / (0.6 * Math.max(5, TL[0].length, (TL[1] || "").length)))));
  var titleM = TL.map(function (s, i) { return tx(540, TL.length > 1 ? 630 + tfs * (0.9 + i) : 686 + tfs * 0.36, s, serif(tfs, null, { "text-anchor": "middle" })); }).join("");
  var coverP = poly([[FX0, FY0 + 10], [FX0 + FW - 8, FY0 + 10], [FX0 + FW - 8, FY0 + FH], [FX0, FY0 + FH]]);
  var MINI = {   // mala fotka na harku (box 166 x 160)
    mountains: pa(poly([[0, 160], [48, 74], [76, 112], [112, 52], [166, 160]]), "#3b4a6b") + pa(poly([[48, 74], [38, 94], [60, 90]]) + poly([[112, 52], [98, 78], [128, 74]]), "#eef2f7") +
      re(0, 134, 166, 26, "#dfe6ee") + pa(poly([[66, 142], [84, 118], [102, 142]]), "#e0742c") + ci(136, 30, 11, "#f3e9c8"),
    sea: re(0, 110, 166, 50, "#1f4d6b") + ci(128, 34, 12, "#f3e9c8") + pa(poly([[34, 108], [104, 108], [96, 122], [42, 122]]), "#0b0f18") +
      pa(poly([[52, 104], [66, 50], [80, 104]]) + poly([[70, 104], [88, 60], [100, 104]]), "#d8cfb6"),
    sky: pa(poly([[0, 160], [0, 128], [166, 118], [166, 160]]), "#0b0f1a") + re(80, 88, 8, 40, "#9aa3ad") +
      el(84, 80, 38, 13, "#c3cad2", { transform: rot(32, 84, 80) }) + ci(40, 30, 2, "#fff6d6") + ci(120, 20, 2, "#fff6d6") + ci(150, 60, 1.6, "#fff6d6") };
  var sheet = g({ transform: rot(1.2, 540, 935), filter: "url(#cf_sh)" }, pa(paper(208, 474, 664, 922, 2.2, 5, "b"), "#f6edd9") +
    tx(248, 584, "CASE FILE", serif(78)) + tx(832, 580, "No. " + no, mono(34, null, { "text-anchor": "end" })) + re(248, 604, 584, 4, "#2b2320") + re(248, 613, 584, 1.6, "#2b2320") +
    [0, 1, 2].map(function (i) { var y = 700 + i * 82; return re(248, y + 16, 584, 2, "#cbbd9c") + tx(252, y, "", mono(38, null, { id: "cf_sheet" + (i + 1) })); }).join("") +
    [0.92, 0.86, 0.97, 0.5].map(function (w, i) { return re(248, 962 + i * 30, 584 * w, 10, "#c9bda3"); }).join("") +
    g({ transform: rot(-8, 410, 1214), opacity: 0.8 }, re(270, 1172, 282, 80, "none", { stroke: "#c9382d", "stroke-width": 6, rx: 6 }) +
      tx(411, 1227, "CLASSIFIED", mono(40, "#c9382d", { "text-anchor": "middle" }))) + tx(252, 1352, "FILED BY: ________", mono(24, "#7a6a55")) +
    g({ transform: rot(6, 712, 1186), filter: "url(#cf_sh)" }, re(620, 1070, 190, 226, "#fbf7ee") + re(632, 1082, 166, 160, "#17203a") +
      g({ transform: "translate(632 1082)" }, MINI[SITE]) + re(632, 1082, 166, 160, "none", { stroke: "#0d1224", "stroke-width": 2 })) + clip(704, 1064, -6));
  var cvOut = g({ id: "cf_cvOut" }, pa(coverP, "#c9a677") + re(FX0 + 16, FY0 + 26, FW - 40, FH - 42, "none", { stroke: "#a8875a", "stroke-width": 3, opacity: 0.55, rx: 6 }) +
    re(FX0 + 36, FY0 + 10, 3, FH - 10, "#a8875a", { opacity: 0.6 }) +
    g({ transform: rot(-1.5, 540, 660) }, re(250, 560, 580, 200, "#f6edd9", { filter: "url(#cf_sh)" }) + re(236, 548, 92, 30, "#efe4c4", { opacity: 0.75, transform: rot(-28, 282, 563) }) +
      re(754, 548, 92, 30, "#efe4c4", { opacity: 0.75, transform: rot(24, 800, 563) }) + tx(540, 602, "CASE FILE  No. " + no, mono(26, "#6b5a48", { "text-anchor": "middle", "letter-spacing": "0.2em" })) +
      re(282, 618, 516, 2, "#2b2320", { opacity: 0.7 }) + titleM + re(282, 740, 516, 2, "#2b2320", { opacity: 0.7 })) +
    (function () { var st = String(o.stamp || "TOP SECRET").toUpperCase(), sw = Math.max(452, st.length * 43 + 60);   // peciatka na fascikli (o.stamp, napr. UNEXPLAINED)
      return g({ transform: rot(-7, 560, 950), opacity: 0.85 }, re(560 - sw / 2, 890, sw, 112, "none", { stroke: "#c9382d", "stroke-width": 7, rx: 8 }) +
        re(560 - sw / 2 + 14, 904, sw - 28, 84, "none", { stroke: "#c9382d", "stroke-width": 3, rx: 5 }) + tx(560, 968, st, mono(62, "#c9382d", { "text-anchor": "middle", "letter-spacing": "0.1em" }))); })() +
    ci(716, 1222, 74, "none", { stroke: "#7a5230", "stroke-width": 8, opacity: 0.26 }) + line("M650 1250 a70 70 0 0 1 60 -96", "#7a5230", 5, { opacity: 0.2 }) + clip(330, FY0 + 8, 3));
  var cvIn = g({ id: "cf_cvIn", opacity: 0 }, pa(coverP, "#b99a6a") +   // vnutro dosky (po preklopeni vidno len pas pri chrbte, x 170-340)
    pa(poly([[FX0, FY0 + FH - 330], [FX0 + FW - 8, FY0 + FH - 380], [FX0 + FW - 8, FY0 + FH], [FX0, FY0 + FH]]), "#c9aa78") +
    g({ filter: "url(#cf_sh)" }, re(FX0 + 24, FY0 + 70, 150, 190, "#fbf7ee", { transform: rot(-5, FX0 + 99, FY0 + 165) }) + re(FX0 + 36, FY0 + 82, 126, 120, "#1f2a40", { transform: rot(-5, FX0 + 99, FY0 + 165) }) +
      re(FX0 + 30, FY0 + 330, 150, 120, "#f6edd9", { transform: rot(4, FX0 + 105, FY0 + 390) })));
  var bandD = "M" + (FX0 - 10) + " 1284 Q 232 1352 " + (FX0 + 126) + " " + (FY0 + FH + 10);
  var folder = g({ id: "cf_folder", transform: rot(-2, 540, 930) },
    g({ filter: "url(#cf_sh)" }, pa(poly([[FX0, FY0], [596, FY0], [614, FY0 - 42], [866, FY0 - 42], [884, FY0], [FX0 + FW, FY0], [FX0 + FW, FY0 + FH], [FX0, FY0 + FH]]), "#b08d5f") +
      re(640, FY0 - 34, 206, 28, "#efe3c6", { transform: rot(-1, 743, FY0 - 20) }) + tx(743, FY0 - 12, "CASE #" + o.caseNo, mono(22, null, { "text-anchor": "middle" }))) +
    sheet + g({ id: "cf_cover", filter: "url(#cf_sh)" }, cvOut + cvIn) +
    g({ id: "cf_band", filter: "url(#cf_sh)" }, line(bandD, "#8c2c20", 11) + line(bandD, "#c1493b", 3, { opacity: 0.7, transform: "translate(-2 -2)" })));
  var mug = g({ filter: "url(#cf_sh)" }, line("M40 578 C 0 610 10 662 58 640", "#e6dccb", 20) + ci(96, 520, 88, "#ece4d3") + ci(96, 520, 72, "#d6cab2") +
    ci(96, 520, 63, "#2b170c") + ci(96, 520, 63, "none", { stroke: "#5f3c22", "stroke-width": 6 }) + el(122, 494, 22, 9, LAMP, { opacity: 0.55, transform: rot(-40, 122, 494) }));
  var pencil = g({ transform: rot(-14, 992, 1000), filter: "url(#cf_sh)" }, re(978, 760, 28, 380, "#e2b23a") + re(978, 760, 9, 380, "#f0c85a") + re(997, 760, 9, 380, "#c28f24") +
    re(976, 722, 32, 40, "#a9b0b8") + re(976, 732, 32, 4, "#7d858f") + re(976, 748, 32, 4, "#7d858f") + pa("M976 722 v-26 a16 16 0 0 1 32 0 v26 Z", "#d77b6d") +
    pa(poly([[978, 1140], [1006, 1140], [992, 1196]]), "#e8c89a") + pa(poly([[986, 1172], [998, 1172], [992, 1196]]), "#2b2320"));
  var LX = 858, LY = 1316, LR = 94, loupeHandle = re(LX + LR + 4, LY - 17, 210, 34, "#2a1a12", { rx: 15, transform: rot(28, LX, LY) }) +
    re(LX + LR + 2, LY - 20, 38, 40, "#c99a3e", { rx: 6, transform: rot(28, LX, LY) });
  var loupe = g({ opacity: 0.45, filter: "url(#soft6)", transform: "translate(26 34)" }, ci(LX, LY, LR + 9, "none", { stroke: "#000", "stroke-width": 18 }) + loupeHandle) +
    loupeHandle + ci(LX, LY, LR, "#d9edf2", { opacity: 0.14 }) + ci(LX, LY, LR + 8, "none", { stroke: "#241a14", "stroke-width": 16 }) +
    ci(LX, LY, LR - 1, "none", { stroke: "#d8a94a", "stroke-width": 4 }) + line("M" + (LX - 60) + " " + (LY - 40) + " a72 72 0 0 1 58 -40", "#ffffff", 7, { opacity: 0.45 });
  scene("desk", { B: wood + FULL("url(#cf_gLamp)", { id: "cf_lamp" }), M: folder + mug + pencil, F: loupe + FULL("url(#cf_gVigD)") + lampHead("cf_lampGlowD") });

  // ---------- BOARD: korok cez celu obrazovku, dreveny ram, par starych vecicok mimo slotov kariet
  var cork = (function () { var rr = PF.rnd(44), m = re(30, 30, 1020, 1860, "#c58f5a", { filter: "url(#cf_cork)" }), h = "";
    for (var i = 0; i < 34; i++) h += ci(60 + rr() * 960, 60 + rr() * 1800, 1.6 + rr() * 1.4);
    m += g({ fill: "#5b3a22", opacity: 0.55 }, h);
    [[180, 520, -18], [880, 1330, 24], [600, 1170, -6]].forEach(function (q) { m += re(q[0] - 45, q[1] - 14, 90, 28, "#efe4c4", { opacity: 0.45, transform: rot(q[2], q[0], q[1]) }); });
    return m; })();
  var news = g({ transform: rot(8, 930, 210), filter: "url(#cf_sh)" }, pa(paper(812, 108, 250, 214, 7, 61, "lb"), "#e7dec8") + re(836, 130, 196, 24, "#3a332e", { opacity: 0.8 }) +
    [0, 1, 2, 3, 4].map(function (i) { return re(924, 172 + i * 22, 108, 7, "#8f877a"); }).join("") + re(836, 170, 76, 96, "#9a9384") + re(836, 284, 196, 7, "#8f877a") + pin(846, 128, "#d94a3b"));
  var card = g({ transform: rot(-7, 140, 1745), filter: "url(#cf_sh)" }, re(16, 1664, 250, 160, "#f6edd9") + re(16, 1700, 250, 3, "#d9776a", { opacity: 0.8 }) +
    [0, 1, 2, 3].map(function (i) { return re(16, 1730 + i * 23, 250, 2, "#8fb3d1", { opacity: 0.7 }); }).join("") + pin(141, 1684, "#d8a94a"));
  var frame = re(30, 30, 1020, 1860, "none", { stroke: "#1c110a", "stroke-width": 28, opacity: 0.55, filter: "url(#soft6)" }) +
    pa("M-300 -300 H1380 V2220 H-300 Z M36 36 V1884 H1044 V36 Z", "#4a3527", { "fill-rule": "evenodd" }) + re(36, 36, 1008, 1848, "none", { stroke: "#6e5140", "stroke-width": 4 }) +
    line("M0 -300 V2220 M14 -300 V2220 M1066 -300 V2220 M1080 -300 V2220 M-300 10 H1380 M-300 1906 H1380", "#3a291e", 2, { opacity: 0.8 });
  scene("board", { B: cork + news + card + pin(990, 1640, "#d94a3b") + line("M990 1646 q -34 60 -14 128", "#c8352b", 3) + frame + FULL("url(#cf_gLampB)", { id: "cf_lampB" }),
    F: FULL("url(#cf_gVigB)") + lampHead("cf_lampGlowB") });

  // ---------- SITE: spolocne kusy nocnej diorámy (B daleko / M stred / F blizko -> paralaxa kamery)
  var TW = [[1, 0.35, 2.3], [0.4, 1, 3.1], [1, 0.5, 3.9], [0.55, 1, 2.7], [1, 0.3, 4.6], [0.45, 1, 3.5]];   // blikanie hviezd: od, do, perioda
  var spark = function (x, y, r) { var k = r * 0.2; return "M" + f1(x) + " " + f1(y - r) + " Q" + f1(x + k) + " " + f1(y - k) + " " + f1(x + r) + " " + f1(y) + " Q" + f1(x + k) + " " + f1(y + k) + " " +
    f1(x) + " " + f1(y + r) + " Q" + f1(x - k) + " " + f1(y + k) + " " + f1(x - r) + " " + f1(y) + " Q" + f1(x - k) + " " + f1(y - k) + " " + f1(x) + " " + f1(y - r) + " Z"; };
  var stars = function (n, seed, y0, y1, avoid) { var rr = PF.rnd(seed), gs = ["", "", "", "", "", ""];
    for (var i = 0; i < n; i++) { var x = -150 + rr() * 1380, y = y0 + Math.pow(rr(), 1.25) * (y1 - y0), r = 1.1 + Math.pow(rr(), 4) * 3.4;
      if (!avoid || !avoid(x, y)) gs[i % 6] += r > 3.6 ? pa(spark(x, y, r * 2.6), "#fff6d6") : ci(x, y, r, "#fff6d6"); }
    return gs.map(function (s, k) { return g({ id: "cf_tw" + k, opacity: TW[k][0] }, s); }).join(""); };
  var moon = function (x, y, r) { return ci(x, y, r * 3.6, "url(#cf_gHalo)") + g({ filter: "url(#cf_cutN)", transform: rot(-10, x, y) }, ci(x, y, r, "#f3e9c8") +
    g({ fill: "#e3d6ae" }, ci(x - r * 0.3, y - r * 0.2, r * 0.23) + ci(x + r * 0.24, y + r * 0.32, r * 0.16) + ci(x + r * 0.4, y - r * 0.3, r * 0.1) + ci(x - r * 0.1, y + r * 0.52, r * 0.08))); };
  var ridge = function (keys, jag, seed) { var rr = PF.rnd(seed), p = [keys[0]];   // hreben z klucovych bodov + drobne zuby
    for (var i = 1; i < keys.length; i++) { var a = keys[i - 1], b = keys[i], n = Math.max(1, Math.round(Math.abs(b[0] - a[0]) / 36));
      for (var j = 1; j < n; j++) p.push([a[0] + (b[0] - a[0]) * j / n + (rr() - 0.5) * 12, a[1] + (b[1] - a[1]) * j / n + (rr() - 0.5) * 2 * jag]);
      p.push(b); }
    return p; };
  var range = function (keys, col, seed, snow, jag) {   // pohorie: silueta + snehove cepice (hrubsie na vrcholoch)
    var p = ridge(keys, jag || 9, seed), low = Math.max.apply(null, p.map(function (q) { return q[1]; })), rr = PF.rnd(seed + 7);
    var m = pa(poly(p.concat([[p[p.length - 1][0], 2400], [p[0][0], 2400]])), col);
    if (snow) m += pa(poly(p.concat(p.map(function (q) { return [q[0] + (rr() - 0.5) * 10, q[1] + 6 + Math.max(0, low - q[1]) * snow[1] + rr() * 18]; }).reverse())), snow[0], { opacity: snow[2] });
    return m; };
  var mist = function (y, h, op) { return re(-300, y - h, 1680, h, "url(#cf_gMist)", { opacity: op }); };
  var spruce = function (x, yb, h, col, snow) {   // smrek: zubate poschodia (papierovy vystrih) + sneh na vetvach
    var n = 6, th = h * 0.84 / n, L = [], R = [], s = "";
    for (var i = 0; i < n; i++) { var y = yb - h * 0.1 - i * th, w = h * 0.3 * (1 - i / n * 0.82), tip = [x - w, y], nt = [x - w * 0.3, y - th * 0.6], ntR = [x + w * 0.3, y - th * 0.6], tipR = [x + w, y];
      L.push(tip, nt); R.unshift(ntR, tipR);
      if (snow) s += poly([nt, tip, [x - w * 0.7, y - th * 0.14]]) + poly([ntR, tipR, [x + w * 0.7, y - th * 0.14]]); }
    return pa(poly([[x - h * 0.035, yb], [x - h * 0.035, yb - h * 0.1]].concat(L, [[x, yb - h]], R, [[x + h * 0.035, yb - h * 0.1], [x + h * 0.035, yb]])), col) +
      (snow ? pa(s, snow, { opacity: 0.85 }) : ""); };
  var flakes = function (id, n, seed, r0, r1, a) {   // vlocky: dlazdica 2040 px dvakrat pod sebou -> posun o +2040 v slucke
    var rr = PF.rnd(seed), m = "";
    for (var i = 0; i < n; i++) { var x = -150 + rr() * 1380, y = rr() * 2040, r = r0 + rr() * (r1 - r0); m += ci(x, y, r) + ci(x, y - 2040, r); }
    return g({ id: id, opacity: 0, transform: "translate(-18 0)" }, g(Object.assign({ id: id + "d", fill: "#f4f8fc" }, a), m)); };
  var fog = function (id, y, n, seed, op, dy) {   // mlha: rozmazane pasy, dlazdica 1200 trikrat vedla seba -> posun o 1200 za celu dlzku
    var rr = PF.rnd(seed), m = "";
    for (var i = 0; i < n; i++) { var x = rr() * 1200, yy = y + (rr() - 0.5) * (dy || 160), rx = 200 + rr() * 260, ry = 24 + rr() * 34;
      for (var c = -1; c <= 1; c++) m += el(x + c * 1200, yy, rx, ry, "#aebbd0"); }
    return g({ id: id, opacity: 0 }, g({ id: id + "d", filter: "url(#soft)", opacity: op }, m)); };
  var bolt = function (id, x0, x1, y1, seed) {   // blesk: zubata cesta zhora dolu + 2 vetvy
    var rr = PF.rnd(seed), d = "M" + x0 + " -60", br = "";
    for (var i = 1; i <= 12; i++) { var y = -60 + (y1 + 60) * i / 12, x = x0 + (x1 - x0) * i / 12 + (rr() - 0.5) * 80; d += " L" + f1(x) + " " + f1(y);
      if (i === 4 || i === 8) br += " M" + f1(x) + " " + f1(y) + " l" + f1((rr() - 0.3) * 130) + " " + f1(70 + rr() * 60) + " l" + f1((rr() - 0.5) * 70) + " " + f1(50 + rr() * 50); }
    return g({ id: id, opacity: 0 }, line(d + br, "#b9c8ff", 20, { opacity: 0.5, filter: "url(#soft6)" }) + line(d + br, "#fbfdff", 5, { "stroke-linejoin": "bevel" })); };
  var SKY = FULL("url(#cf_gSky)"), LT = re(-300, -300, 1680, 1560, "url(#cf_gLt)", { id: "cf_ltSky", opacity: 0 });
  var OVER = FULL("url(#cf_gVigS)") + FULL("#04060c", { id: "cf_fxDark", opacity: 0 }) + FULL("#e8eeff", { id: "cf_ltFlash", opacity: 0 });
  var site = { B: SKY, M: "", F: "" }, LIGHT = null, BEAM = null, HINGE = null;

  if (SITE === "mountains") {   // hory: stan na snehovom svahu, stopy dolu k lesu vlavo
    var tent = function () {   // oranzovy papierovy stan (3/4 pohlad), rozrezany bok, visiaci cip cf_tentFlap, svetlo vnutri cf_tentGlow
      var A = [-150, 2], B = [-60, -150], C = [28, 6], D = [152, -124], F = [218, -8];
      var Q = function (u, v) { return [(1 - u) * (1 - v) * B[0] + u * (1 - v) * D[0] + (1 - u) * v * C[0] + u * v * F[0], (1 - u) * (1 - v) * B[1] + u * (1 - v) * D[1] + (1 - u) * v * C[1] + u * v * F[1]]; };
      var gash = function (u0, u1, v, w, seed) { var rr = PF.rnd(seed), a = [Q(u0, v)], b = [];
        for (var u = u0 + 0.05; u < u1 - 0.02; u += 0.05) { a.push(Q(u, v - w * (0.5 + rr() * 0.7))); b.unshift(Q(u, v + w * (0.5 + rr() * 0.7))); }
        return poly(a.concat([Q(u1, v)], b)); };
      var g1 = gash(0.12, 0.74, 0.34, 0.06, 3), g2 = gash(0.44, 0.8, 0.64, 0.045, 4), side = poly([B, D, F, C]), front = poly([A, B, C]), door = poly([B, [-44, 4], [-78, 4]]);
      HINGE = Q(0.45, 0.4);
      return g({ id: "cf_tent", transform: "translate(650 1194) scale(0.86)" }, pa(poly([A, [-330, 30], [-60, 40], C]), "#a9b6c9", { opacity: 0.75 }) +
        line("M-60 -150 L-236 30 M152 -124 L300 -14 M-150 2 L-250 20", "#1c1a22", 2.5) + re(-242, 24, 10, 12, "#1c1a22") + re(296, -20, 10, 12, "#1c1a22") +
        g({ filter: "url(#cf_cutN)" }, pa(side, "#e0742c") + pa(front, "#b5541f") + pa(door, "#2a1409") + pa(g1 + g2, "#1a0d06") +
          g({ id: "cf_tentGlow", opacity: 0 }, el(20, -60, 330, 170, "url(#cf_gWarm)") + pa(side, "#ffbe6e", { opacity: 0.5 }) + pa(front, "#ff9e4a", { opacity: 0.45 }) + pa(g1 + g2 + door, "#ffe2a0")) +
          g({ id: "cf_tentFlap" }, pa(poly([Q(0.3, 0.4), Q(0.62, 0.41), Q(0.54, 0.63), Q(0.4, 0.6)]), "#a8481b")) +
          pa(poly([B, D, [D[0] + 6, D[1] + 13], [B[0] + 5, B[1] + 16]]), "#eef2f7") + line("M-60 -150 l-4 -14 M152 -124 l4 -14", "#1c1a22", 4)) +
        pa("M-196 16 q 40 -26 90 -8 q 60 -22 120 -2 q 50 -18 110 -4 q 40 -12 96 6 V 44 H-196 Z", "#e9eef5"));
    };
    var steps = function () { var m = "", n = 17, P0 = [575, 1238], P1 = [420, 1300], P2 = [150, 1466];   // stopy: od stanu dolu dolava, blizsie = vacsie
      for (var i = 0; i < n; i++) { var t = i / (n - 1), u = 1 - t, x = u * u * P0[0] + 2 * u * t * P1[0] + t * t * P2[0], y = u * u * P0[1] + 2 * u * t * P1[1] + t * t * P2[1];
        var dx = 2 * u * (P1[0] - P0[0]) + 2 * t * (P2[0] - P1[0]), dy = 2 * u * (P1[1] - P0[1]) + 2 * t * (P2[1] - P1[1]), L = Math.hypot(dx, dy), s = 0.55 + t * 0.9, sd = i % 2 ? 1 : -1;
        var px = x - dy / L * 9 * s * sd, py = y + dx / L * 9 * s * sd, a = f1(Math.atan2(dy, dx) * 180 / Math.PI);
        m += el(px, py, 11 * s, 5.2 * s, "#9fb0c6", { transform: rot(a, px, py) }) + el(px + 1.5, py + 1.2, 6.5 * s, 2.8 * s, "#8395ae", { transform: rot(a, px, py) }); }
      return g({ id: "cf_steps" }, m); };
    site.B += stars(160, 21, -250, 1000) + moon(812, 470, 60) + LT + bolt("cf_bolt1", 640, 560, 790, 5) + bolt("cf_bolt2", 190, 250, 900, 9) +
      range([[-300, 930], [-140, 860], [20, 770], [130, 830], [300, 690], [430, 800], [560, 745], [690, 860], [830, 790], [980, 700], [1130, 820], [1380, 880]], "#3b4a6b", 11, ["#cfd8e3", 0.42, 0.8], 12) +
      mist(1060, 320, 0.9) + range([[-300, 1080], [-80, 1000], [100, 1050], [250, 950], [390, 1020], [540, 985], [700, 1070], [840, 975], [990, 1030], [1150, 985], [1380, 1050]], "#2c3852", 13, ["#dfe6ee", 0.4, 0.85], 9) +
      [30, 80, 120, 170, 330, 380, 610, 660, 700, 900, 950, 1000].map(function (x, i) { return spruce(x, 1128 + (i % 3) * 8, 44 + (i % 4) * 9, "#1f2a40"); }).join("") + mist(1170, 200, 0.8);
    site.M += range([[-300, 1150], [-120, 1060], [60, 1110], [200, 1020], [330, 1085], [470, 1050], [610, 1100], [760, 1055], [900, 1090], [1080, 1020], [1380, 1080]], "#1f2a40", 17, ["#eef2f7", 0.5, 0.9], 7) +
      mist(1215, 140, 0.6) + pa(poly(ridge([[-300, 1262], [0, 1225], [260, 1206], [520, 1186], [760, 1160], [1000, 1140], [1380, 1112]], 3, 23).concat([[1380, 2400], [-300, 2400]])), "url(#cf_gSnowG)") +
      pa("M-300 1352 C -40 1318 220 1360 440 1336 C 640 1316 820 1330 1380 1290 L1380 1306 C 900 1350 640 1344 430 1362 C 200 1382 -60 1350 -300 1378 Z", "#c7d2df", { opacity: 0.8 }) +
      pa("M-300 1540 C 100 1500 380 1552 660 1524 C 880 1504 1100 1520 1380 1500 L1380 1522 C 1080 1548 880 1532 650 1556 C 380 1580 100 1530 -300 1574 Z", "#bcc8d6", { opacity: 0.8 }) +
      (has("trees") ? g({ filter: "url(#cf_cutN)" }, [[130, 1302, 170], [275, 1382, 190], [-10, 1452, 340], [70, 1400, 300], [190, 1436, 250]].map(function (q) { return spruce(q[0], q[1], q[2], "#141d2e", "#dfe6ee"); }).join("")) : "") +
      (has("footprints") ? steps() : "") + (has("tent") ? tent() : "") + flakes("cf_snowM", 46, 31, 1.6, 3.2) + fog("cf_fogM", 1190, 7, 41, 0.5);
    site.F += g({ filter: "url(#dof)" }, pa("M-300 1760 C 0 1650 300 1712 520 1726 C 760 1742 920 1646 1380 1664 V2400 H-300 Z", "#dfe6ee") + spruce(1110, 1966, 700, "#0b111d") + spruce(-40, 1990, 760, "#0b111d")) +
      flakes("cf_snowF", 30, 32, 3, 5.5) + flakes("cf_snowN", 10, 33, 7, 10, { filter: "url(#soft6)" }) + fog("cf_fogF", 1540, 6, 42, 0.4, 120) +
      g({ id: "cf_wind", opacity: 0 }, g({ id: "cf_windd" }, (function () { var rr = PF.rnd(71), m = "";
        for (var i = 0; i < 22; i++) { var x = rr() * 1300, y = 380 + rr() * 1250, L = 70 + rr() * 170, w = f1(2 + rr() * 3), op = (0.25 + rr() * 0.4).toFixed(2);
          [x, x - 1300].forEach(function (xx) { m += line("M" + f1(xx) + " " + f1(y) + " q" + f1(L / 2) + " -8 " + f1(L) + " 4", "#eef4fa", w, { opacity: op }); }); }
        for (i = 0; i < 40; i++) { x = rr() * 1300; y = 300 + rr() * 1500; var r = 2 + rr() * 3.5; m += ci(x, y, r, "#f4f8fc") + ci(x - 1300, y, r, "#f4f8fc"); }
        return m; })()));
    if (has("tent")) LIGHT = ["#cf_tentGlow", 0, 1, 0];
  } else if (SITE === "sea") {   // more: lod v strede, mesacna cesta, 3 pasy vln v slucke
    var waves = function (id, y, W, h, col, foam, seed) {   // pas vln: 3 hrebene na dlazdicu sirky W -> posun o -W v slucke
      var rr = PF.rnd(seed), cr = [], sum = 0, d = "M-800 2400 L-800 " + y, fm = "", x = -800;
      for (var i = 0; i < 3; i++) { cr.push([0.8 + rr() * 0.4, h * (0.7 + rr() * 0.6)]); sum += cr[i][0]; }
      while (x < 1900 + W) cr.forEach(function (c) { var w = c[0] / sum * W, b = x + w, m = x + w / 2;
        d += " Q" + f1(x + w * 0.18) + " " + f1(y - c[1] * 1.1) + " " + f1(m) + " " + f1(y - c[1]) + " Q" + f1(b - w * 0.12) + " " + f1(y - c[1] * 0.5) + " " + f1(b) + " " + f1(y);
        fm += "M" + f1(x + w * 0.1) + " " + f1(y - c[1] * 0.4) + " Q" + f1(x + w * 0.22) + " " + f1(y - c[1] * 1.02) + " " + f1(m) + " " + f1(y - c[1] * 0.96); x = b; });
      d += " L" + f1(x) + " 2400 Z";
      return g({ id: id + "o" }, g({ id: id }, pa(d, "#0a1a28", { opacity: 0.45, transform: "translate(0 10)" }) + pa(d, col) + line(fm, foam, 5, { opacity: 0.75 }))); };
    var glints = function (id, y0, y1, n, seed) {   // mesacna cesta: dve skupiny ciarok blikaju v protifaze
      var rr = PF.rnd(seed), m = ["", ""];
      for (var i = 0; i < n; i++) { var y = y0 + (y1 - y0) * i / n + rr() * 6, k = (y - 990) / 900, w = 18 + k * 230 + rr() * 40, x = 792 + (rr() - 0.5) * (40 + k * 170);
        m[i % 2] += re(x - w / 2, y, w, 3 + k * 5, "#f3e9c8", { opacity: (0.45 + rr() * 0.45).toFixed(2), rx: 2 }); }
      return g({ id: id + "a" }, m[0]) + g({ id: id + "b", opacity: 0.3 }, m[1]); };
    var sailC = "#d8cfb6", sailD = "#c3b99e", ink = "#1a1f2b", lowSail = (function () { var rr = PF.rnd(57);
      return poly([[0, -292], [190, -292], [205, -190]].concat(tear([205, -190], [-15, -190], 12, 18, rr), [[-15, -190]])); })();
    var ship = g({ id: "cf_shipBob" }, g({ id: "cf_ship", transform: "translate(372 1124) rotate(-2)", filter: "url(#cf_cutN)" },   // brigantina: 2 stazne, stvorcove plachty vpredu
      line("M96 -478 L330 -122 M-72 -512 L96 -478 M-72 -512 L-214 -76 M96 -440 L56 -58 M96 -440 L136 -58 M-72 -470 L-112 -58 M-72 -470 L-34 -58", ink, 2.2) +
      pa("M104 -452 L320 -124 L152 -118 Z", sailD) + pa("M112 -372 L262 -104 L140 -104 Z", sailD) + pa("M-72 -440 L-205 -405 Q-240 -250 -225 -95 L-72 -95 Z", sailD) +
      pa("M-140 -500 L-4 -500 L6 -448 Q-70 -440 -150 -448 Z", sailC) + pa("M30 -452 L160 -452 L176 -392 Q95 -380 14 -392 Z", sailC) +
      pa("M16 -384 L174 -384 L190 -300 Q95 -286 0 -300 Z", sailC) + pa(lowSail, sailC) + re(-78, -512, 8, 458, ink) + re(92, -478, 7, 424, ink) +
      [[8, -458, 174], [-6, -390, 202], [-18, -298, 226], [-156, -506, 162]].map(function (q) { return re(q[0], q[1], q[2], 6, ink); }).join("") +
      pa(poly([[-72, -512], [-20, -500], [-72, -492]]), "#c8352b") + line("M226 -82 L334 -124", ink, 7) +
      pa(poly([[-218, -76], [-150, -78], [-146, -58], [150, -58], [226, -84], [236, -76], [212, -34], [166, 18], [-162, 24], [-206, -8]]), ink) +
      re(-190, -46, 380, 5, "#2c3446") + [-120, -60, 0, 60, 120].map(function (x) { return ci(x, -24, 4.5, "#2d3950"); }).join("") + re(-216, -104, 4, 30, ink) +
      g({ id: "cf_lantern", opacity: 0.9 }, ci(-214, -110, 36, "url(#cf_gWarm)") + ci(-214, -110, 6.5, "#ffd27a"))));
    var rocks = g({ filter: "url(#cf_cutN)" }, pa(poly([[790, 1300], [806, 1190], [842, 1128], [896, 1090], [944, 1062], [992, 1080], [1036, 1118], [1084, 1160], [1120, 1300]]), "#141a26") +
      pa(poly([[842, 1128], [896, 1090], [944, 1062], [934, 1112], [886, 1150], [846, 1170]]), "#2a3346") + pa(poly([[690, 1300], [704, 1222], [736, 1196], [770, 1214], [788, 1300]]), "#111723") +
      pa(poly([[704, 1222], [736, 1196], [744, 1224], [716, 1240]]), "#262f42") + pa(poly([[-300, 1300], [-40, 1186], [30, 1150], [80, 1170], [120, 1300]]), "#121824") +
      pa(poly([[-40, 1186], [30, 1150], [36, 1180], [-10, 1200]]), "#252e41")) + line("M690 1236 q30 -14 60 0 t60 0 t60 0 t60 0 t60 0 t60 0 t60 0 M-60 1226 q30 -12 60 0 t60 0 t60 0", "#e8f1f5", 5, { opacity: 0.65 }) +
      g({ id: "cf_spray", opacity: 0, fill: "#eef5f8" }, ci(930, 1150, 26) + ci(900, 1128, 18) + ci(962, 1124, 20) + ci(944, 1096, 14) + ci(880, 1106, 10) + ci(984, 1100, 9));
    var buoy = g({ id: "cf_buoy", transform: "translate(878 1352) rotate(-4)", filter: "url(#cf_cutN)" }, el(0, 4, 46, 12, "#0e2233", { opacity: 0.7 }) +
      pa(poly([[-30, 0], [30, 0], [18, -74], [-18, -74]]), "#c8352b") + pa(poly([[-25, -22], [25, -22], [21, -44], [-21, -44]]), "#f1ebe0") + line("M-14 -74 L0 -110 L14 -74", ink, 4) +
      g({ id: "cf_buoyLt" }, ci(0, -114, 30, "url(#cf_gRedLt)") + ci(0, -114, 7, "#ff8a6a")) + line("M-46 6 q23 -10 46 0 t46 0", "#e8f1f5", 4, { opacity: 0.8 }));
    var seaLines = (function () { var rr = PF.rnd(19), d = ""; for (var i = 0; i < 26; i++) { var x = rr() * 1100 - 20, y = 1004 + rr() * 110, L = 30 + rr() * 90;
      d += "M" + f1(x) + " " + f1(y) + " q" + f1(L / 2) + " -5 " + f1(L) + " 0"; } return line(d, "#3a7496", 2.5, { opacity: 0.7 }); })();
    site.B += stars(140, 22, -250, 960, function (x, y) { return Math.hypot(x - 790, y - 470) < 140; }) + moon(790, 470, 64) + LT + bolt("cf_bolt1", 620, 540, 990, 6) + bolt("cf_bolt2", 190, 250, 990, 8) +
      re(-300, 990, 1680, 1410, "url(#cf_gSea)") + re(-300, 986, 1680, 6, "#4a7c99", { opacity: 0.7 }) + seaLines + glints("cf_gl0", 1000, 1100, 16, 91);
    site.M += (has("ship") ? ship : "") + waves("cf_wb1", 1112, 360, 26, "#1b4865", "#8fb6c9", 5) + glints("cf_gl1", 1112, 1230, 9, 92) + (has("rocks") ? rocks : "") +
      waves("cf_wb2", 1262, 420, 38, "#174059", "#a8c9da", 7) + glints("cf_gl2", 1262, 1420, 8, 93) + (has("buoy") ? buoy : "") + fog("cf_fogM", 1070, 7, 43, 0.5, 90);
    site.F += waves("cf_wb3", 1452, 540, 58, "#123550", "#e8f1f5", 9) + glints("cf_gl3", 1452, 1700, 7, 94) + fog("cf_fogF", 1400, 6, 44, 0.38, 120);
    if (has("ship")) LIGHT = ["#cf_lantern", 0.12, 1, 0.9];
  } else {   // nocna obloha: Mliecna cesta, radioteleskop na kopci, observatorium
    var DA = 32 * Math.PI / 180, FOC = [610 + 150 * Math.sin(DA), 960 - 150 * Math.cos(DA)], BL = 470, BEND = [FOC[0] + BL * Math.sin(DA), FOC[1] - BL * Math.cos(DA)];
    var milky = (function () { var rr = PF.rnd(29), m = "";
      for (var i = 0; i < 170; i++) m += ci(-700 + rr() * 2500, 820 + (rr() + rr() + rr() - 1.5) * 150, 0.7 + rr() * 1.3, "#fff6d6", { opacity: (0.35 + rr() * 0.55).toFixed(2) });
      return g({ transform: rot(-36, 540, 820) }, el(540, 820, 1300, 170, "#26305c", { opacity: 0.6, filter: "url(#soft)" }) + el(480, 812, 900, 100, "#434a82", { opacity: 0.45, filter: "url(#soft)" }) +
        el(620, 826, 560, 54, "#9a93c4", { opacity: 0.22, filter: "url(#soft)" }) + el(560, 842, 760, 22, "#0d1224", { opacity: 0.55, filter: "url(#soft6)" }) + m); })();
    var dish = g({ id: "cf_dish", filter: "url(#cf_cutN)" }, pa(poly([[520, 1338], [566, 1062], [582, 1062], [550, 1338]]), "#59616d") + pa(poly([[656, 1338], [606, 1062], [590, 1062], [626, 1338]]), "#6f7883") +
      line("M538 1240 L640 1140 M536 1150 L620 1240 M548 1300 L630 1300", "#59616d", 5) + re(546, 1040, 86, 26, "#7c858f") + pa(poly([[560, 1044], [548, 1000], [596, 990], [616, 1044]]), "#6f7883") +
      g({ transform: "translate(610 960) rotate(32)" }, pa("M-206 0 Q0 220 206 0 Z", "#555d69") + el(0, 0, 206, 62, "#c3cad2") + el(0, 6, 150, 44, "none", { stroke: "#9aa3ad", "stroke-width": 2.5 }) +
        el(0, 12, 90, 26, "none", { stroke: "#9aa3ad", "stroke-width": 2.5 }) + line("M0 14 L0 62 M0 14 L-146 44 M0 14 L146 44 M0 14 L-190 20 M0 14 L190 20", "#9aa3ad", 2) +
        el(0, 0, 206, 62, "none", { stroke: "#e3e8ec", "stroke-width": 4 }) + line("M-196 12 L0 -150 M196 12 L0 -150 M0 60 L0 -150", "#8a929c", 5) + re(-14, -178, 28, 40, "#6f7883", { rx: 4 }) +
        ci(0, -150, 46, "url(#cf_gCyan)", { id: "cf_feedGlow", opacity: 0 }) + g({ id: "cf_redLt" }, ci(0, -186, 18, "url(#cf_gRedLt)") + ci(0, -186, 5, "#ff6a55"))));
    var beam = g({ id: "cf_beamG", opacity: 0 }, line("M" + f1(FOC[0]) + " " + f1(FOC[1]) + " L" + f1(BEND[0]) + " " + f1(BEND[1]), "#8fdcff", 30, { opacity: 0.28, filter: "url(#soft6)" }) +
      line("M" + f1(FOC[0]) + " " + f1(FOC[1]) + " L" + f1(BEND[0]) + " " + f1(BEND[1]), "#e4f7ff", 7, { id: "cf_beamDash", "stroke-dasharray": "44 36" }) +
      g({ transform: "translate(" + f1(FOC[0]) + " " + f1(FOC[1]) + ") rotate(-58)" }, [0, 1, 2].map(function (k) {
        return line("M0 -64 Q30 0 0 64", "#c8f0ff", 5, { id: "cf_pulse" + k, opacity: 0, transform: "translate(0 0) scale(0.35)" }); }).join("")));
    var obs = g({ filter: "url(#cf_cutN)" }, re(138, 1236, 160, 104, "#4b5362") + pa("M134 1240 A84 80 0 0 1 302 1240 Z", "#9aa3ad") + pa("M134 1240 A84 80 0 0 1 218 1160 L218 1240 Z", "#7c858f") +
      pa(poly([[208, 1162], [228, 1162], [232, 1240], [204, 1240]]), "#141a26") + re(160, 1282, 26, 58, "#2c323d") + g({ id: "cf_obsLt" }, ci(262, 1284, 42, "url(#cf_gWarm)") + re(250, 1270, 24, 30, "#ffcf7a")));
    site.B += milky + stars(230, 23, -250, 1250) + re(-300, 900, 1680, 400, "url(#cf_gHor)") +
      pa("M-300 1250 C -60 1190 180 1215 400 1205 C 620 1195 800 1245 1060 1215 C 1200 1200 1300 1212 1380 1220 V2400 H-300 Z", "#1e2740") + mist(1260, 120, 0.5);
    site.M += pa("M-300 1328 C 0 1300 260 1316 480 1330 C 700 1344 900 1308 1380 1316 V2400 H-300 Z", "#121a2b") + pa("M470 1920 C 520 1700 640 1560 598 1338 L620 1338 C 690 1560 580 1720 600 1920 Z", "#1b2438") +
      (has("observatory") ? obs : "") + (has("dish") ? dish + beam : "") + fog("cf_fogM", 1290, 7, 45, 0.45, 80) +
      (has("trees") ? g({ filter: "url(#cf_cutN)" }, [[835, 1332, 150], [900, 1338, 210], [985, 1350, 280], [1062, 1332, 230], [60, 1334, 180]].map(function (q) { return spruce(q[0], q[1], q[2], "#0d1322"); }).join("")) : "");
    site.F += g({ filter: "url(#dof)" }, pa("M-300 1650 C 120 1596 460 1636 760 1618 C 980 1606 1180 1626 1380 1616 V2400 H-300 Z", "#0a0f1c") +
      line((function () { var rr = PF.rnd(81), d = ""; for (var x = -40; x < 1120; x += 18 + rr() * 16) d += "M" + f1(x) + " " + f1(1640 - Math.sin(x / 170) * 12) + " l" + f1((rr() - 0.5) * 20) + " -" + f1(20 + rr() * 34); return d; })(), "#0a0f1c", 5)) +
      fog("cf_fogF", 1560, 6, 46, 0.35, 100);
    if (has("observatory")) LIGHT = ["#cf_obsLt", 0.1, 1, 1];
    if (has("dish")) BEAM = { L: BL, feed: "#cf_feedGlow" };
  }
  site.F += OVER;
  scene("site", site);

  // ---------- vlozenie do vrstiev; navrchu F: tien lampy (cf_shade) + kraftovy harok prechodu (cf_wipe)
  var wipe = (function () { var rr = PF.rnd(808), fib = "";
    var p = [[-300, -150]].concat(tear([-300, -150], [1380, -150], 14, 22, rr), [[1380, -150], [1380, 2070]], tear([1380, 2070], [-300, 2070], 14, 22, rr), [[-300, 2070]]);
    for (var i = 0; i < 70; i++) { var x = -200 + rr() * 1480, y = -100 + rr() * 2120; fib += "M" + f1(x) + " " + f1(y) + " l" + f1(20 + rr() * 50) + " " + f1((rr() - 0.5) * 12); }
    return g({ id: "cf_wipe", opacity: 0 }, g({ id: "cf_wipeIn", transform: "translate(0 -2400)" }, re(-300, 2040, 1680, 110, "url(#cf_gShD)") + re(-300, -260, 1680, 110, "url(#cf_gShU)") +
      pa(poly(p), "#c9a677") + line(fib, "#a98a5e", 2, { opacity: 0.5 }) + re(-300, 640, 1680, 3, "#b08d5f", { opacity: 0.7 }) + re(-300, 1280, 1680, 3, "#b08d5f", { opacity: 0.7 }) +
      g({ transform: rot(-6, 540, 960), opacity: 0.8 }, re(300, 900, 480, 120, "none", { stroke: "#c9382d", "stroke-width": 7, rx: 8 }) +
        tx(540, 982, "CASE #" + o.caseNo, mono(64, "#c9382d", { "text-anchor": "middle", "letter-spacing": "0.12em" }))))); })();
  PF.add("B", g({ id: "cf_B" }, LAY.B));
  PF.add("M", g({ id: "cf_M" }, LAY.M));
  PF.add("F", g({ id: "cf_F" }, LAY.F) + g({ id: "cf_top" }, FULL("#07050a", { id: "cf_shade", opacity: 0 }) + wipe));
  var topF = function () { var f = PF.svg("F"), x = document.getElementById("cf_top"); if (f && x && f.lastElementChild !== x) f.appendChild(x); };   // nad karty/peciatky
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", topF);
  if (PF.fx && PF.fx.dust && !document.getElementById("du0")) PF.fx.dust(16, 515, "#ffe2b0");   // prach vo svetle lampy (desk, board)
  if (sc0 === "site") PF.S("#dust", { opacity: 0 }, 0);

  // ---------- pivoty a nekonecne slucky (periody delia dlzku videa)
  var slide = function (sel, dx, dy, per) { if (!TOT) return; var p = PF.loopPeriod(per);   // posun dlazdice o (dx, dy) za periodu
    T.fromTo(sel, { attr: { transform: "translate(0 0)" } }, { attr: { transform: "translate(" + dx + " " + dy + ")" }, duration: p, ease: "none", repeat: Math.round(TOT / p) - 1, immediateRender: false }, 0); };
  var sway = function (sel, a, b, per, ease) { if (!TOT) return; var p = PF.loopPeriod(per);   // tam a spat, parny pocet poloperiod
    T.fromTo(sel, a, Object.assign({ duration: p / 2, ease: ease || "sine.inOut", yoyo: true, repeat: 2 * Math.round(TOT / p) - 1, immediateRender: false }, b), 0); };
  var tr = function (s) { return { attr: { transform: s } }; };
  PF.P("cf_cover", FX0, FCY); PF.P("cf_band", 230, 1360);
  TW.forEach(function (w, k) { sway("#cf_tw" + k, { opacity: w[0] }, { opacity: w[1] }, w[2]); });
  slide("#cf_fogMd", 1200, 0, TOT); slide("#cf_fogFd", -1200, 0, TOT);
  if (SITE === "mountains") {
    slide("#cf_snowMd", 0, 2040, 13); slide("#cf_snowFd", 0, 2040, 7.5); slide("#cf_snowNd", 0, 2040, 4.6); slide("#cf_windd", 1300, 0, 0.9);
    ["cf_snowM", "cf_snowF", "cf_snowN"].forEach(function (id, i) { sway("#" + id, tr("translate(-18 0)"), tr("translate(18 0)"), 4 + i * 1.3); });
    if (HINGE) PF.P("cf_tentFlap", HINGE[0], HINGE[1]);
  } else if (SITE === "sea") {
    slide("#cf_wb1", -360, 0, 9); slide("#cf_wb2", -420, 0, 7); slide("#cf_wb3", -540, 0, 5.5);
    ["cf_wb1o", "cf_wb2o", "cf_wb3o"].forEach(function (id) { PF.P(id, 540, 1300); });
    [0, 1, 2, 3].forEach(function (k) { sway("#cf_gl" + k + "a", { opacity: 1 }, { opacity: 0.3 }, 1.6 + k * 0.3); sway("#cf_gl" + k + "b", { opacity: 0.3 }, { opacity: 1 }, 1.6 + k * 0.3); });
    if (has("ship")) { PF.P("cf_shipBob", 372, 1124); sway("#cf_ship", tr("translate(372 1124) rotate(-2)"), tr("translate(372 1118) rotate(2.2)"), 5.2); }
    if (has("buoy")) { sway("#cf_buoy", tr("translate(878 1352) rotate(-4)"), tr("translate(878 1346) rotate(5)"), 3.3); sway("#cf_buoyLt", { opacity: 1 }, { opacity: 0.15 }, 2.2, "steps(1)"); }
    if (has("rocks")) PF.P("cf_spray", 930, 1150, { s: 0.4 });
  } else {
    if (has("dish")) { sway("#cf_redLt", { opacity: 1 }, { opacity: 0.12 }, 1.8, "steps(1)"); PF.P("cf_beamG", FOC[0], FOC[1], { s: 0.02 }); }
  }

  // ---------- efekty miesta (len medzi t0..t1, koncia v neutrale)
  var odd = function (x) { var n = Math.max(1, Math.round(x)); return n % 2 ? n : n + 1; };
  var vis = function (sel, t0, t1, fi, fo) { var a = Math.min(fi, (t1 - t0) / 2), b = Math.min(fo, (t1 - t0) / 2);
    PF.O(sel, 0, 1, t0, a, "power1.out"); PF.O(sel, 1, 0, t1 - b, b, "power1.in"); };
  var nfx = 0, flick = function (sel, t0, t1, lo, hi, rest) {   // nahodne blikanie svetla, na konci pokojova hodnota
    var rr = PF.rnd(900 + 17 * nfx++), t = t0;
    while (t < t1 - 0.1) { PF.S(sel, { opacity: +(lo + (hi - lo) * (rr() < 0.45 ? rr() * 0.3 : 0.7 + rr() * 0.3)).toFixed(2) }, t); t += 0.05 + rr() * 0.18; }
    PF.S(sel, { opacity: rest }, t1); };
  var strike = function (t, id, t1) {   // blesk: 2 zablesky, obloha za hrebenmi sa rozsvieti, cela obrazovka jemne
    [[0, 0.9, 1, 0.4], [0.06, 0.15, 0, 0.06], [0.11, 1, 1, 0.5], [0.2, 0.35, 0.6, 0.14]].forEach(function (k) {
      PF.S("#cf_ltSky", { opacity: k[1] }, t + k[0]); PF.S(id, { opacity: k[2] }, t + k[0]); PF.S("#cf_ltFlash", { opacity: k[3] }, t + k[0]); });
    var d = Math.max(0.05, Math.min(0.4, t1 - t - 0.24));
    PF.O("#cf_ltSky", 0.35, 0, t + 0.24, d); PF.O(id, 0.6, 0, t + 0.24, Math.min(d, 0.25)); PF.O("#cf_ltFlash", 0.14, 0, t + 0.24, d); };
  var spray = function (t) { PF.S("#cf_spray", { opacity: 0.95 }, t); PF.X("cf_spray", { s: 1.1, ty: -46 }, t, 0.45, "power2.out");
    PF.O("#cf_spray", 0.95, 0, t + 0.2, 0.3); PF.X("cf_spray", { s: 0.4, ty: 0 }, t + 0.52, 0); };
  var FX = {
    snow: function (t0, t1) { vis("#cf_snowM, #cf_snowF, #cf_snowN", t0, t1, 0.5, 0.6); },
    wind: function (t0, t1) { vis("#cf_wind", t0, t1, 0.3, 0.4);
      if (HINGE) { var n = odd((t1 - t0 - 0.2) / 0.16); PF.XY("cf_tentFlap", { r: -16 }, t0 + 0.1, (t1 - t0 - 0.2) / (n + 1), "sine.inOut", n); } },
    fog: function (t0, t1) { vis("#cf_fogM, #cf_fogF", t0, t1, 0.9, 0.9); },
    flicker: function (t0, t1) { if (LIGHT) flick(LIGHT[0], t0, t1, LIGHT[1], LIGHT[2], LIGHT[3]); flick("#cf_fxDark", t0, t1, 0, 0.4, 0); },
    lightning: function (t0, t1) { var two = t1 - t0 > 1.6, tm = t0 + (t1 - t0) * 0.55; strike(t0 + 0.05, "#cf_bolt1", two ? tm : t1); if (two) strike(tm, "#cf_bolt2", t1); },
    waves: function (t0, t1) { var L = t1 - t0 - 0.2, n = odd(L / 0.8), hd = L / (n + 1);
      ["cf_wb1o", "cf_wb2o", "cf_wb3o"].forEach(function (id, i) { PF.XY(id, { ty: -(8 + i * 7) }, t0 + i * 0.1, hd, "sine.inOut", n); });
      if (has("ship")) PF.XY("cf_shipBob", { r: 4, ty: -10 }, t0 + 0.05, hd, "sine.inOut", n);
      if (has("rocks")) for (var tk = t0 + 0.3; tk < t1 - 0.6; tk += 1.1) spray(tk); },
    beam: function (t0, t1) { if (!BEAM) return; var n = Math.max(1, Math.round((t1 - t0) / 0.45));
      PF.O("#cf_beamG", 0, 1, t0, 0.15); PF.X("cf_beamG", { s: 1 }, t0, 0.4, "power2.out"); PF.O("#cf_beamG", 1, 0, t1 - 0.3, 0.3); PF.X("cf_beamG", { s: 0.02 }, t1, 0);
      T.fromTo("#cf_beamDash", { attr: { "stroke-dashoffset": 0 } }, { attr: { "stroke-dashoffset": -80 }, duration: (t1 - t0) / n, ease: "none", repeat: n - 1, immediateRender: false }, t0);
      for (var k = 0, tk = t0 + 0.2; tk < t1 - 0.9; k++, tk += 0.42) T.fromTo("#cf_pulse" + (k % 3), { opacity: 0.95, attr: { transform: "translate(0 0) scale(0.35)" } },
        { opacity: 0, attr: { transform: "translate(" + BEAM.L + " 0) scale(1.6)" }, duration: 0.95, ease: "power1.out", immediateRender: false }, tk);
      PF.O(BEAM.feed, 0, 1, t0, 0.2); PF.O(BEAM.feed, 1, 0, t1 - 0.3, 0.3); }
  };
  var FXOK = { mountains: ["snow", "wind", "flicker", "fog", "lightning"], sea: ["waves", "fog", "lightning", "flicker"], sky: ["beam", "flicker", "fog"] };

  // ---------- API
  var api = { kind: "case", scenes: SC.slice(), scene0: sc0, site: SITE, props: props, badgeZone: null };
  api.metric = api.metricLabel = api.show = api.metricReset = function () {};
  api.mood = function () { return function () {}; };
  var lv = 1, cur = sc0, isOpen = false;
  api.lamp = function (level, t, dur) {   // 0..1 sila lampy: kuzel + ziara, zvysok tma (cf_shade)
    level = Math.max(0, Math.min(1, level == null ? 1 : +level)); if (dur == null) dur = 0.3;
    PF.O("#cf_lamp, #cf_lampB, #cf_lampGlowD, #cf_lampGlowB", lv, level, t, dur, "power1.inOut");
    PF.O("#cf_shade", +(0.7 * (1 - lv)).toFixed(3), +(0.7 * (1 - level)).toFixed(3), t, dur, "power1.inOut");
    lv = level; };
  api.scene = function (name, t) {   // lampa stmavne, kraftovy harok zhora prekryje obraz, v t vymena, harok odide dole do t + 0.4
    if (SC.indexOf(name) < 0) { console.warn("envCase.scene: neznama scena '" + name + "'"); return; }
    if (name === cur) return;
    if (t >= 0.45) { var l0 = lv; api.lamp(l0 * 0.3, t - 0.25, 0.2); topF();
      PF.S("#cf_wipe", { opacity: 1 }, t - 0.29);
      T.fromTo("#cf_wipeIn", tr("translate(0 -2400)"), { attr: { transform: "translate(0 0)" }, duration: 0.28, ease: "power2.in", immediateRender: false }, t - 0.28);
      T.fromTo("#cf_wipeIn", tr("translate(0 0)"), { attr: { transform: "translate(0 2400)" }, duration: 0.36, ease: "power2.out", immediateRender: false }, t + 0.03);
      PF.S("#cf_wipe", { opacity: 0 }, t + 0.4); api.lamp(l0, t + 0.1, 0.3); }
    PF.sceneSet("cf", cur, false, t, 0); PF.sceneSet("cf", name, true, t, 0);
    PF.S("#dust", { opacity: name === "site" ? 0 : 1 }, t);
    cur = name; };
  api.folder = function (open, t) {   // prelozenie prednej dosky cez chrbat (sx 1 -> 0 -> -1), gumicka zosunie z rohu
    open = !!open; if (open === isOpen) return; isOpen = open;
    if (open) { PF.X("cf_band", { tx: -30, ty: 34 }, t, 0.18, "power2.in"); PF.O("#cf_band", 1, 0, t + 0.06, 0.12);
      PF.X("cf_cover", { sx: 0, sy: 1.04 }, t + 0.08, 0.2, "power2.in"); PF.S("#cf_cvOut", { opacity: 0 }, t + 0.28); PF.S("#cf_cvIn", { opacity: 1 }, t + 0.28);
      PF.X("cf_cover", { sx: -1, sy: 1 }, t + 0.28, 0.24, "power2.out");
    } else { PF.X("cf_cover", { sx: 0, sy: 1.04 }, t, 0.2, "power2.in"); PF.S("#cf_cvOut", { opacity: 1 }, t + 0.2); PF.S("#cf_cvIn", { opacity: 0 }, t + 0.2);
      PF.X("cf_cover", { sx: 1, sy: 1 }, t + 0.2, 0.24, "power2.out"); PF.O("#cf_band", 0, 1, t + 0.44, 0.12); PF.X("cf_band", { tx: 0, ty: 0 }, t + 0.44, 0.16, "power2.out");
      PF.S("#cf_sheet1, #cf_sheet2, #cf_sheet3", { textContent: "" }, t + 0.5); } };
  api.sheet = function (lines, t) {   // 1-3 riadky pisacim strojom (PF.cards.typewrite ak existuje); vracia cas konca pisania
    var tt = t, end = t;
    (lines || []).slice(0, 3).forEach(function (s, i) {
      var sel = "#cf_sheet" + (i + 1), str = String(s == null ? "" : s), fs = Math.min(38, Math.floor(584 / (0.64 * Math.max(1, str.length))));
      if (fs < 38) PF.S(sel, { attr: { "font-size": fs } }, tt);
      end = PF.cards && PF.cards.typewrite ? +PF.cards.typewrite(sel, str, tt, 22) || tt + str.length / 22 : (PF.S(sel, { textContent: str }, tt), tt + 0.3);
      tt = end + 0.18; });
    return end; };
  // sloty kariet: 2x2 mriezka + stredna (piata ide navrch); stlpce maju rovnake znamienko rotacie -> minimalne prekrytie rohov
  var SLOTS = [[300, 676, -2.5], [780, 684, 2], [300, 1204, -1.5], [780, 1210, 2.5], [540, 944, -1]];
  api.slot = function (i) { var s = SLOTS[Math.max(0, Math.min(4, i | 0))]; return { x: s[0], y: s[1], r: s[2] }; };
  api.siteFx = function (name, t0, t1) {
    if (FXOK[SITE].indexOf(name) < 0) { console.warn("envCase.siteFx: '" + name + "' nie je pre " + SITE); return; }
    FX[name](t0, Math.max(+t1 || 0, t0 + 0.5)); };
  return api;
};
