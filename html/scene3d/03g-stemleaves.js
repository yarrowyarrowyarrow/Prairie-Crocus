// Part of the Site & Pattern 3D viewer. Loaded as an ordered CLASSIC
// script by the bootstrap in scene3d.html — it shares the global scope
// with its siblings (THREE and friends are globals set by the
// bootstrap). Do not add ES `import`/`export` here.
//
// Design principle P5 — see docs/DESIGN_PHILOSOPHY.md
//
// A leafy wildflower as leafy as it is (V3.66, F268).
//
// After V3.65 the commonest fault on the 105 native wildflowers was `sparse`
// or `stem_leaves`: a bundle of thin stems with a few leaves on them, where the
// photographs show a leafy mass (the asters, the goldenrods, fireweed, the
// milk-vetches, licorice, the hedysarums). 03c-leafy.js draws each leaf the
// readings count up a stem as its own blade, and that is all the leaf there
// is: a swamp aster's six stems of 25 leaves cover about 2% of its outline.
// A stem also carries the leaves of its side shoots and axils, which nobody
// counted, and from a yard away the plant is the mass they make.
//
// So, as a shrub's leaves are (03d-woody.js, V3.49) and a mat's (V3.65), a
// leafy stem carries cut-out cards of its own leafy shoots (_wdSpray: its leaf
// outline, in its arrangement), set up the stems between the lowest leaf and
// the flowers, standing out from the stem, as many as cover its outline.
// What nothing records, and is a stated estimate here:
//  * how much of its outline a leafy wildflower covers in leaf (HERB_COVER,
//    the share a person sees filled; a shrub's is 0.75);
//  * the triangles the cards may spend, by height (HERB_CARD_BUDGET);
//  * how far larger than life a card may be drawn to cover it (HERB_GAIN_MAX).
// A stem of one or two leaves (a sarsaparilla's single umbrella, a lily's
// pair) gets none: its leaves are what the readings say they are.

const HERB_COVER = 0.4;
// Triangles for the cards at 0.3 m and at 1.5 m tall, at Balanced; Lifelike
// spends 1.6 times as many.
const HERB_CARD_BUDGET = [500, 2200];
const HERB_CARD_H = [0.3, 1.5];
const HERB_GAIN_MAX = 1.6;
const HERB_CARD_MIN_NODES = 3;
// The share of its length by width a leaf of each divided outline fills.
const _HERB_LEAF_FILL = { compound_pinnate: 0.35, bipinnate: 0.3, pinnatifid: 0.45,
                          ternate: 0.4, trifoliate: 0.5, compound_palmate: 0.4,
                          palmately_lobed: 0.55 };

// Adds `P`'s leafy-shoot cards to `C` (an _lbNew() with uv), along the stems
// 03c-leafy.js recorded in `P.paths`.
function leafyStemCards(C, P, rng) {
  if (STYLISED || !P.paths || !P.paths.length || P.nodes < HERB_CARD_MIN_NODES) return;
  const sp = _wdSpray(P.shape, P.perNode);                             // 03d-woody.js
  const L = P.L;
  // The outline a person sees, and what the counted leaves already cover.
  const area = Math.PI * P.R * (P.R + 2 * P.H) * 0.7;
  // A divided leaf is mostly the air between its leaflets (a stated estimate).
  const fill = _HERB_LEAF_FILL[P.shape] || 0.6;
  const drawn = P.stems * P.nodes * P.perNode * L * P.W * fill;
  const want = HERB_COVER * area - drawn;
  if (want <= 0) return;
  const card = sp.w * L * sp.h * L * (sp.leafCover || sp.cover) * 0.6;
  const t = Math.max(0, Math.min(1, (P.H - HERB_CARD_H[0]) / (HERB_CARD_H[1] - HERB_CARD_H[0])));
  const tris = (HERB_CARD_BUDGET[0] + (HERB_CARD_BUDGET[1] - HERB_CARD_BUDGET[0]) * t)
    * (QUALITY >= 2 ? 1.6 : 1);
  const room = Math.max(20, Math.floor(tris / 2));
  let n = Math.ceil(want / Math.max(1e-6, card));
  const gain = n > room ? Math.min(HERB_GAIN_MAX, Math.sqrt(n / room)) : 1;
  n = Math.min(room, Math.ceil(n / (gain * gain)));
  const w = sp.w * L * gain, h = sp.h * L * gain;
  const paths = P.paths, up = [0, 1, 0];
  for (let i = 0; i < n; i++) {
    const pa = paths[i % paths.length];
    const f = (Math.floor(i / paths.length) + rng()) / Math.ceil(n / paths.length);
    const a = pa.a + i * 2.39996 + (rng() - 0.5) * 0.6;
    const o = [Math.cos(a), 0, Math.sin(a)];
    // Standing out and up from the stem, the lower ones spreading wider.
    let e = 0.35 + 0.6 * f + (rng() - 0.5) * 0.3;
    // Its tip under the stem's top, or the body would be taller than the
    // plant (it is scaled to its highest point, 03c-leafy.js).
    const lim = pa.top * 0.96, hk = Math.min(h * (0.8 + 0.4 * rng()), (lim - pa.y0) * 0.9);
    if (hk <= 0.002) continue;
    const ymax = Math.max(pa.y0, Math.min(pa.y1, lim - hk * Math.sin(e)));
    const at = pa.at((pa.y0 + (ymax - pa.y0) * f) / pa.top);
    // Steeper where it would pass the plant's outline.
    const reach = Math.max(0.01, P.R - Math.hypot(at[0], at[2])) * 1.2;
    if (hk * Math.cos(e) > reach) e = Math.min(1.45, Math.acos(Math.min(1, reach / hk)));
    const T = _lbUnit(_lbMix(o, up, Math.cos(e), Math.sin(e)));
    const S = _lbUnit(_lbCross(up, o));
    const rise = Math.max(0, at[1] + hk * Math.sin(e) - lim);
    const kk = rise > 0 ? hk * Math.max(0.2, 1 - rise / (hk * Math.sin(e))) : hk;
    _wdCard(C, _lbAdd(at, T, -kk * 0.08), T, S, w * kk / h, kk, 0.5 + 0.3 * f + 0.1 * rng());
  }
  C.cut = sp;
  C.gain = gain;
}

window.leafyStemCards = leafyStemCards;
