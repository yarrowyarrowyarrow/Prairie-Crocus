// Part of the Site & Pattern 3D viewer. Loaded as an ordered CLASSIC
// script by the bootstrap in scene3d.html — it shares the global scope
// with its siblings (THREE and friends are globals set by the
// bootstrap). Do not add ES `import`/`export` here.
//
// Design principle P5 — see docs/DESIGN_PHILOSOPHY.md
//
// A shrub drawn from its own numbers (V3.49, F268).
//
// The baked shrub figures are eight shapes in a few leaf classes: five to
// eleven stems as thick as an arm with leaf cards at their ends. Read against
// photographs of the region's 34 native shrubs, 23 had the wrong stems, 16
// were far too sparse and 22 had leaves the wrong size. Where somebody has
// read a shrub's leaf and habit and counted its stems (src/shrub_habit.py
// writes a `drawn` block with body 'woody'), this chunk builds the shrub from
// them: as many stems as it sends up, each forking again and again to leafy
// shoots, with its own leaf in its outline and arrangement on them. One body
// is built for a species and placed for each plant of it.
//
// What nothing records, and is derived here as a stated estimate:
//  * how thick a stem is: WOODY_PIPE, from the stem count and the crown the
//    stems share (the same crown on more stems is thinner stems);
//  * where the branches leave and how long they are: each axis carries
//    children enough to end in the shoots the leaves need, inside an outline
//    that follows from the habit (_wdEnvelope);
//  * how many leaves a shoot holds (WOODY_PER_SHOOT).
//
// A grown shrub carries tens of thousands of leaves and no budget draws them
// one by one. So the leaves are drawn a shoot at a time: a flat card the size
// of a leafy shoot, cut to the outline of the twig and its leaves by a mask
// painted here (_wdSpray), in the species' leaf outline and arrangement, the
// way the leaves of a spray lie more or less in one plane. Where the cards the
// budget buys cannot cover the crown (WOODY_COVER) at life size, they are
// drawn larger, up to WOODY_GAIN_MAX: the factor is in
// userData.woody.plan.gain. A dogwood comes out at 1 and a 4 m saskatoon,
// whose leaves are 4 cm, at about 2.

// The forms (src/shrub_habit.py FORMS; tests/test_shrub_habit.py holds them equal).
const WOODY_FORMS = ['clump', 'thicket', 'arching', 'mat'];
// Triangles one shrub may spend, by detail level: [one WOODY_BUDGET_H[0] tall
// or less, one WOODY_BUDGET_H[1] tall or more]. Stylised draws none of these.
// The baked shrub figure was held to 3,600 and a tree's largest to 6,000.
const WOODY_BUDGET = [[0, 0], [2800, 6000], [5000, 10000]];
const WOODY_BUDGET_H = [1, 4];
// How much larger than life a spray may be drawn, and the share of the crown's
// shell the drawn leaves are asked to cover.
const WOODY_GAIN_MAX = 3;
const WOODY_COVER = 0.75;
const WOODY_STEMS_MAX = 36;
// A shrub part grown is built as a smaller shrub, not as a grown one shrunk:
// at the first of these shares of its grown height that holds it, with fewer
// stems, and its leaves at their own size. Scaled down from the grown body a
// second-summer saskatoon had leaves a centimetre long.
const WOODY_TIERS = [0.4, 0.7, 1];
function _woodyTier(d) {
  const f = d.mature_h > 0 ? d.height_m / d.mature_h : 1;
  for (const t of WOODY_TIERS) if (f <= t * 1.05) return t;
  return 1;
}
// Sprays one drawn shoot carries.
const WOODY_PER_SHOOT = 3;
// A stem's radius at the ground, in metres: WOODY_PIPE x sqrt(R x H / stems).
// 25 dogwood wands on a 3 m crown come out 1.6 cm thick and a hawthorn's four
// trunks 6 cm, which is what the photographs show; nothing records either.
const WOODY_PIPE = 0.019;
// How far out the stems stand at the ground, as a share of the crown's radius.
const _WD_BASE = { clump: 0.3, thicket: 0.82, arching: 0.25, mat: 0.1 };
// Which way a branch turns from its parent: toward the sky and away from the
// shrub's middle, by form.
const _WD_BIAS = { clump: [0.25, 0.3], thicket: [0.4, 0.05], arching: [0.6, 0.2],
                   mat: [1.0, 0.1] };

const _wdClamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));

// The crown's radius at `t` of its height, 0 to 1 of its widest, by form: a
// clump is a vase, widest above the middle; a thicket stands straight-sided; an
// arching shrub is a fountain; a mat is widest on the ground.
function _wdEnvelope(form, t) {
  const dome = (t0) => Math.sqrt(Math.max(0, 1 - Math.pow((t - t0) / (1 - t0), 2)));
  if (form === 'mat') return Math.sqrt(Math.max(0, 1 - t * t));
  if (form === 'thicket') return t < 0.7 ? 1 : dome(0.7);
  const t0 = form === 'arching' ? 0.6 : 0.55, low = form === 'arching' ? 0.5 : 0.3;
  return t < t0 ? low + (1 - low) * Math.pow(t / t0, 0.7) : dome(t0);
}

// A shrub's crown as read off its photographs (V3.63, src/shrub_habit.py
// CROWNS; a test holds the two equal). The form says how the stems grow; the
// crown is the outline from across a yard, which until V3.63 was one vase for
// twenty of the 34 native shrubs. `clear` is the share of the height that is
// bare stem below the lowest leafy branch (a chokecherry's, a hawthorn's).
const WOODY_CROWNS = ['vase', 'rounded', 'mound', 'spreading', 'upright', 'irregular', 'mat'];
function _wdCrownEnvelope(crown, t, clear) {
  if (t < clear * 0.98) return 0;
  const u = clear > 0 ? Math.min(1, (t - clear) / Math.max(0.05, 1 - clear)) : t;
  const dome = (u0) => Math.sqrt(Math.max(0, 1 - Math.pow((u - u0) / (1 - u0), 2)));
  switch (crown) {
    case 'vase':                       // narrow at the foot, widest high up
      return u < 0.72 ? 0.22 + 0.78 * Math.pow(u / 0.72, 0.85) : dome(0.72);
    case 'rounded': {                  // a ball sitting on a short foot
      const s = Math.sqrt(Math.max(0, 1 - Math.pow(2 * u - 1, 2)));
      return u < 0.5 ? Math.max(0.42, s) : s;
    }
    case 'mound':                      // widest on the ground, low and domed
      return Math.sqrt(Math.max(0, 1 - Math.pow(u, 1.7)));
    case 'spreading':                  // broad, arching out from a narrower base
      return u < 0.55 ? 0.5 + 0.5 * Math.pow(u / 0.55, 0.6) : dome(0.55);
    case 'upright':                    // straight-sided, flat-topped
      return u < 0.82 ? 0.72 + 0.28 * Math.pow(u / 0.82, 0.4) : dome(0.82);
    case 'irregular':                  // open, with lobes and gaps
      return Math.max(0.15, Math.pow(Math.sin(Math.PI * Math.min(1, u * 0.9 + 0.06)), 0.55)
        * (0.86 + 0.14 * Math.sin(u * 17.0)));
    case 'mat': return Math.sqrt(Math.max(0, 1 - u * u));
    default: return 1;
  }
}
// Which way a branch turns, by crown: [toward the sky, away from the middle].
const _WD_CROWN_BIAS = { vase: [0.45, 0.25], rounded: [0.25, 0.3], mound: [0.1, 0.4],
                         spreading: [0.12, 0.5], upright: [0.55, 0.05],
                         irregular: [0.2, 0.35], mat: [0.05, 0.5] };
// Where a clump's stems end, by crown: [how far out, as a share of the
// radius; how much lower the outermost end than the middle one].
const _WD_CROWN_STEM = { vase: [0.85, 0.35], rounded: [0.7, 0.4], mound: [0.85, 0.62],
                         spreading: [0.95, 0.5], upright: [0.42, 0.15],
                         irregular: [0.85, 0.5], mat: [0.95, 0.8] };

// ── a leafy shoot's outline ─────────────────────────────────────────────────

// Leaves a spray holds, by how narrow the leaf is: a willow shoot the length
// of three or four of its leaves carries far more of them than a dogwood's.
function _wdSprayLeaves(shape) {
  if (shape === 'needle' || shape === 'awl' || shape === 'scale') return 64;
  if (isCompoundShape(shape) || shape === 'palmately_lobed' || shape === 'lobed') return 7;
  const r = LEAF_WIDTH_RATIO[shape] == null ? 0.4 : LEAF_WIDTH_RATIO[shape];
  return r < 0.1 ? 28 : (r < 0.3 ? 16 : (r > 0.8 ? 6 : 9));
}

// One leaf of `len` pixels, painted white, pointing up the canvas from (0, 0).
function _wdPaintLeaf(g, shape, len) {
  const ell = (l, w, y0) => { g.beginPath(); g.ellipse(0, -(y0 + l / 2), w / 2, l / 2, 0, 0, 6.2832); g.fill(); };
  const stalk = (l) => { g.beginPath(); g.moveTo(0, 0); g.lineTo(0, -l); g.stroke(); };
  const at = (y, a, f) => { g.save(); g.translate(0, -y); g.rotate(a); f(); g.restore(); };
  switch (shape) {
    case 'compound_pinnate': case 'bipinnate': case 'pinnatifid':
      stalk(len * 0.9);
      for (const f of [0.26, 0.48, 0.7])
        for (const a of [1.05, -1.05]) at(len * f, a, () => ell(len * 0.34, len * 0.16, 0));
      at(len * 0.82, 0, () => ell(len * 0.34, len * 0.16, 0));
      return;
    case 'trifoliate': case 'ternate':
      stalk(len * 0.36);
      for (const a of [0, 1.1, -1.1]) at(len * 0.36, a, () => ell(len * 0.62, len * 0.4, 0));
      return;
    case 'compound_palmate':
      stalk(len * 0.36);
      for (const a of [0, 0.6, -0.6, 1.2, -1.2]) at(len * 0.36, a, () => ell(len * 0.62, len * 0.15, 0));
      return;
    case 'palmately_lobed': case 'lobed': {       // a maple's: pointed lobes fanned from the stalk
      stalk(len * 0.25);
      const c = len * 0.48, lobes = [[0, 0.52], [0.85, 0.44], [-0.85, 0.44], [1.75, 0.3], [-1.75, 0.3]];
      g.beginPath();
      for (let i = 0; i <= 40; i++) {
        const a = -2.2 + 4.4 * i / 40;
        let r = 0.2;
        for (const [la, lr] of lobes) r = Math.max(r, lr * Math.pow(Math.max(0, Math.cos((a - la) * 1.7)), 1.5));
        g.lineTo(Math.sin(a) * r * len, -c - Math.cos(a) * r * len);
      }
      g.fill();
      return;
    }
    case 'orbicular': case 'cordate': case 'reniform':
      stalk(len * 0.2);
      ell(len * 0.8, len * 0.8 * (LEAF_WIDTH_RATIO[shape] || 0.9), len * 0.2);
      return;
  }
  // A simple leaf: two curves from the stalk to the tip, widest at its peak.
  const w = len * (LEAF_WIDTH_RATIO[shape] == null ? 0.4 : LEAF_WIDTH_RATIO[shape]) / 2;
  const pk = _PEAK_T[shape] || 0.4, k = 4 / 3;
  g.beginPath(); g.moveTo(0, 0);
  g.bezierCurveTo(w * k, -len * pk * 0.6, w * k, -len * (pk + (1 - pk) * 0.5), 0, -len);
  g.bezierCurveTo(-w * k, -len * (pk + (1 - pk) * 0.5), -w * k, -len * pk * 0.6, 0, 0);
  g.fill();
}

// A smaller copy of a mask whose share of pixels over the cut is the same as
// the full one's: without it the leaves thin out and vanish with distance,
// their averaged pixels falling under the cut.
function _wdMip(src, w, h, cover) {
  const cv = document.createElement('canvas');
  cv.width = w; cv.height = h;
  const g = cv.getContext('2d', { willReadFrequently: true });
  g.imageSmoothingQuality = 'high';
  g.drawImage(src, 0, 0, w, h);
  const im = g.getImageData(0, 0, w, h), px = im.data, v = [];
  for (let i = 0; i < px.length; i += 4) v.push(px[i]);
  v.sort((a, b) => a - b);
  const at = v[Math.min(v.length - 1, Math.floor(v.length * (1 - cover)))];
  const f = Math.min(8, (WOODY_CUT * 255 + 1) / Math.max(1, at));
  for (let i = 0; i < px.length; i += 4) px[i] = px[i + 1] = px[i + 2] = Math.min(255, px[i] * f);
  g.putImageData(im, 0, 0);
  return cv;
}

// The mask for a shoot of `shape` leaves, `perNode` to a node: a twig up the
// middle of the card with its leaves either side. {key, map, depth, cover, w, h}:
// `cover` is the share of the card the leaves fill, and `w` x `h` its size in
// leaf lengths. One a shape and arrangement, kept for the session.
//
// Two layouts. Narrow leaves, needles and leaves in pairs stand along a length
// of shoot, as a willow wand's or a dogwood twig's do. Broad leaves borne
// singly are a short shoot of a few, each on its stalk and no two alike in
// size or angle: nine in two even rows read as one feather-shaped leaf, and
// crowded round a point they ran together into one lobed one.
//
// Leaves in pairs turn a quarter at each node (V3.65), as a dogwood's, a
// honeysuckle's or a cranberry's do: every other pair faces the eye and is
// drawn short, close in to the shoot. Drawn all flat, two even rows of pairs
// read as one pinnate leaf, and a dogwood could not be told from the peavine
// climbing it.
const WOODY_CUT = 0.4;
const _WD_SPRAYS = new Map();
function _wdSpray(shape, perNode) {
  const needle = shape === 'needle' || shape === 'awl' || shape === 'scale';
  const per = needle ? 2 : Math.min(2, perNode);
  const ratio = LEAF_WIDTH_RATIO[shape] == null ? 0.4 : LEAF_WIDTH_RATIO[shape];
  // Narrow but not grass-like leaves borne singly (a cherry's, a meadowsweet's)
  // cluster too: sixteen in two rows read as one feather-shaped leaf (V3.50).
  const cluster = !needle && per === 1 && (ratio >= 0.15 || isCompoundShape(shape));
  const key = (needle ? 'needle' : shape) + '|' + per;
  let sp = _WD_SPRAYS.get(key);
  if (sp) return sp;
  const W = 128, H = cluster ? 192 : 256, cv = document.createElement('canvas');
  cv.width = W; cv.height = H;
  const g = cv.getContext('2d', { willReadFrequently: true });
  g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
  g.fillStyle = g.strokeStyle = '#fff'; g.lineCap = 'round';
  const rnd = _lcg(11 + key.length * 97 + key.charCodeAt(0) * 13);      // 01b-surface.js
  const wide = needle ? 2.2 : (cluster ? 2.0 : 1.8), len = W / wide;    // one leaf, in pixels
  const K = cluster ? 6 : _wdSprayLeaves(shape), nodes = Math.max(2, Math.ceil(K / per));
  // Where the shoot's first and last leaves leave it, up the card.
  const y0 = cluster ? len * 0.12 : 3, y1 = H - len * (needle ? 0.7 : (cluster ? 1.08 : 0.9));
  g.lineWidth = 2.6;
  g.beginPath(); g.moveTo(W / 2, H); g.lineTo(W / 2, H - y1); g.stroke();
  g.lineWidth = needle ? 3 : 1.8;
  for (let j = 0; j < nodes; j++) {
    const t = j / (nodes - 1), y = y0 + (y1 - y0) * t, last = j === nodes - 1;
    for (let m = 0; m < per; m++) {
      const side = per > 1 ? (m ? 1 : -1) : (j % 2 ? 1 : -1);
      // How far a leaf stands off the shoot; the last one continues it.
      const facing = !needle && per === 2 && j % 2 === 1;          // decussate (V3.65)
      const off = cluster ? 1.15 - 0.45 * t + (rnd() - 0.5) * 0.35
        : (facing ? 0.22 + rnd() * 0.16 : 0.75 + rnd() * 0.3);
      const a = last && per === 1 ? (rnd() - 0.5) * 0.3 : side * off;
      g.save();
      g.translate(W / 2, H - y); g.rotate(a);
      if (needle) { g.beginPath(); g.moveTo(0, 0); g.lineTo(0, -len * (0.75 + 0.25 * rnd())); g.stroke(); }
      else if (cluster) {                              // on its stalk, clear of the next
        const st = len * 0.1;
        g.beginPath(); g.moveTo(0, 0); g.lineTo(0, -st); g.stroke();
        g.translate(0, -st);
        _wdPaintLeaf(g, shape, len * (0.62 + 0.3 * rnd()));
      } else _wdPaintLeaf(g, shape, len * (0.8 + 0.22 * rnd()) * (facing ? 0.75 : 1));
      g.restore();
    }
  }
  // A pair facing the eye is drawn short but is as much leaf as any other:
  // `leafCover` is the share of the card its leaves would fill laid flat, which
  // is what decides how many cards a crown needs (`cover`, what is painted,
  // keeps the smaller copies honest).
  const facingPairs = !needle && per === 2 ? Math.floor(nodes / 2) : 0;
  const painted = (nodes - facingPairs + facingPairs * 0.5625) / nodes;
  const mk = woodyMask(key, cv);
  sp = Object.assign(mk, { w: wide, h: H / len, leaves: K, cluster,
                           leafCover: Math.min(1, mk.cover / painted) });
  _WD_SPRAYS.set(key, sp);
  return sp;
}

// A painted mask as the material reads it: its smaller copies made here so
// each keeps its share of pixels over the cut (_wdMip), and a depth material
// so the shadow is of what is painted. Shared with 03e-crowns.js's needles.
function woodyMask(key, cv) {
  const W = cv.width, H = cv.height;
  const px = cv.getContext('2d', { willReadFrequently: true }).getImageData(0, 0, W, H).data;
  let on = 0;
  for (let i = 0; i < px.length; i += 4) if (px[i] > 127) on++;
  const cover = Math.max(0.02, on / (W * H)), mips = [cv];
  for (let w = W >> 1, h = H >> 1; ; w = Math.max(1, w >> 1), h = Math.max(1, h >> 1)) {
    mips.push(_wdMip(cv, w, h, cover));
    if (w === 1 && h === 1) break;
  }
  const map = new THREE.CanvasTexture(cv);
  map.mipmaps = mips; map.generateMipmaps = false;
  map.minFilter = THREE.LinearMipmapLinearFilter;
  map.needsUpdate = true;
  // The shadow of a card is the shadow of its leaves.
  const depth = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking,
                                              alphaMap: map, alphaTest: WOODY_CUT });
  return { key: 'cut:' + key, map, depth, test: WOODY_CUT, cover };
}

// ── the plan: what the budget buys ──────────────────────────────────────────
function _woodyPlan(d, quality) {
  const tier = _woodyTier(d);
  const H = Math.max(0.15, d.mature_h * tier), R = Math.max(0.1, d.mature_w / 2 * tier);
  const L = Math.max(0.004, d.leaf_m), shape = d.leaf_shape;
  const q = _wdClamp(quality, 1, 2), b = WOODY_BUDGET[q];
  const budget = Math.round(b[0] + (b[1] - b[0])
    * _wdClamp((H - WOODY_BUDGET_H[0]) / (WOODY_BUDGET_H[1] - WOODY_BUDGET_H[0]), 0, 1));
  const perNode = d.arrangement === 'opposite' ? 2 : (d.arrangement === 'whorled' ? 3 : 1);
  const spray = _wdSpray(shape, perNode);
  // The shell the leaves a person sees stand in: a dome's side and its top.
  const area = d.form === 'mat' ? Math.PI * R * R * 1.3 : Math.PI * R * (R + 2 * H) * 0.7;
  // Sprays that cover it at life size: each fills `cover` of its card, and is
  // seen at an angle.
  const need = WOODY_COVER * area / (spray.w * L * spray.h * L * spray.leafCover * 0.6);
  const crown = WOODY_CROWNS.indexOf(d.crown) >= 0 ? d.crown : '';
  const P = { H, R, L, shape, form: d.form, budget, area, need, spray, gain: 1, cards: 0, tier,
              crown, clear: crown ? _wdClamp(d.clear || 0, 0, 0.6) : 0,
              // A young shrub has sent up fewer of its stems.
              stems: _wdClamp(Math.round((d.stems || 1) * (0.4 + 0.6 * tier)), 1, WOODY_STEMS_MAX) };
  _woodyCards(P, budget * 0.62);
  P.shoots = Math.max(P.stems, Math.round(P.cards / WOODY_PER_SHOOT));
  return P;
}

// The sprays `tris` triangles buy, and how much larger than life they must be.
function _woodyCards(P, tris) {
  const n = Math.max(1, Math.floor(tris / 2));
  P.gain = _wdClamp(Math.sqrt(P.need / n), 1, WOODY_GAIN_MAX);
  P.cards = Math.min(n, Math.ceil(P.need / (P.gain * P.gain)));
}

// ── the skeleton ────────────────────────────────────────────────────────────

// A twig too thin for a tube: a flat strip, wide enough to be seen.
function _wdStrip(B, a, b, w, shade) {
  const T = _lbUnit(_lbAdd(b, a, -1)), len = Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
  const S = _lbUnit(_lbCross(T, Math.abs(T[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0]));
  _lbBlade(B, a, T, S, len, w, 'linear', 1, 0, shade);
}

// One axis from `o` along `dir`, `len` long and `r` thick, that must end in
// `quota` leafy shoots: it carries the children that makes, and its own outer
// part is a shoot. G gathers the stems' geometry and the shoots.
function _wdAxis(G, o, dir, len, r, quota) {
  const P = G.P, rng = G.rng, end = _lbAdd(o, dir, len);
  const shade = 0.55 + 0.4 * _wdClamp(end[1] / P.H, 0, 1);
  if (r >= G.tube) _lbTube(G.S, [o, end], r, r * 0.6, shade);
  else _wdStrip(G.S, o, end, Math.max(2 * r, G.twig), shade);
  const kids = quota > 1.5 ? _wdClamp(Math.round(Math.sqrt(quota * 1.5)), 2, 7) : 0;
  G.shoots.push({ a: _lbAdd(o, dir, len * (kids ? 0.5 : 0.12)), b: end });
  const turn = rng() * 6.283;
  for (let j = 0; j < kids; j++) {
    // Shorter and thinner toward the parent's tip.
    const f = 0.22 + 0.64 * (j + 0.3 + 0.4 * rng()) / kids;
    _wdChild(G, _lbAdd(o, dir, len * f), dir, len * (0.62 - 0.26 * f) * (0.8 + 0.4 * rng()),
             r * (1 - 0.45 * f) * 0.55, (quota - 1) / kids, turn + j * 2.39996);
  }
}

// A child axis leaving its parent at `p`, where the parent runs along `tg`:
// out at `psi` round it, turned toward the sky and away from the shrub's
// middle as its form says, and never out of the crown's outline.
function _wdChild(G, p, tg, len, r, quota, psi) {
  // A tree (03e-crowns.js) passes its own outline, bias and droop on G.
  const P = G.P, rng = G.rng, bias = G.bias || _WD_BIAS[P.form];
  const env = G.env || ((t) => _wdEnvelope(P.form, t));
  const u = _lbUnit(_lbCross(tg, Math.abs(tg[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0])), w = _lbCross(tg, u);
  const a = psi + rng() * 0.6, th = 0.55 + rng() * 0.4;
  const e = _lbMix(u, w, Math.cos(a), Math.sin(a)), out = _lbUnit([p[0], 0, p[2]]);
  let c = _lbMix(tg, e, Math.cos(th), Math.sin(th));
  if (P.form === 'mat') c = [c[0] * 0.5, Math.abs(c[1]) * 0.5, c[2] * 0.5];
  c = [c[0] + out[0] * bias[1], c[1] + bias[0], c[2] + out[2] * bias[1]];
  if (c[1] < -(G.droop || 0)) c[1] = -(G.droop || 0) + (-(G.droop || 0) - c[1]) * 0.3;
  c = _lbUnit(c);
  let l = len;
  for (let k = 0; k < 5; k++) {
    const q = _lbAdd(p, c, l);
    if (q[1] <= P.H * 1.02 && Math.hypot(q[0], q[2])
        <= P.R * env(_wdClamp(q[1] / P.H, 0, 1)) + 0.02) break;
    l *= 0.78;
  }
  _wdAxis(G, p, c, l, Math.max(0.0012, r), quota);
}

// The stems from the ground, by form, each with its branches.
function _woodyStems(G) {
  const P = G.P, rng = G.rng, { H, R } = P, N = P.stems;
  const r0 = _wdClamp(WOODY_PIPE * Math.sqrt(R * H / N), 0.0015, 0.07);
  const rb = Math.min(R * _WD_BASE[P.form], P.form === 'clump' ? 0.05 * Math.sqrt(N * H) : R)
    * (P.clear > 0.12 ? 0.5 : 1);
  const rot = rng() * 6.283, quota = P.shoots / N;
  const kids = _wdClamp(Math.round(Math.sqrt(quota * 1.5)), 2, 9);
  // A branch off a stem: longer where fewer stems share the crown.
  const reach = _wdClamp(0.9 * R / Math.sqrt(N) + 0.12 * H, 0.08 * H, 0.5 * Math.max(R, H))
    * (P.form === 'thicket' ? 0.55 : 1);
  for (let i = 0; i < N; i++) {
    // Where it stands, 0 at the middle to 1 at the edge: of a few, one is in the middle.
    const fr = Math.sqrt((i + (N < 8 ? 0 : 0.5)) / N), a = rot + i * 2.39996;
    const dx = Math.cos(a), dz = Math.sin(a), jit = 0.85 + 0.15 * rng();
    const base = [dx * rb * fr, 0, dz * rb * fr];
    // `clear`: how far up a stem its first branch leaves. A shrub in leaf is
    // leafy nearly to the ground.
    let at, clear = 0.15;
    if (P.form === 'thicket') {                   // upright, the outer ones shorter
      const h = H * (1 - 0.4 * fr * fr) * jit, lean = h * (0.03 + 0.08 * fr);
      at = (t) => [base[0] + dx * lean * t * t, h * t, base[2] + dz * lean * t * t];
      clear = 0.12;
    } else if (P.form === 'arching' || P.form === 'mat') {   // up and over, or along the ground
      const mat = P.form === 'mat', far = R * (mat ? 0.45 + 0.5 * fr : 0.45 + 0.5 * fr);
      const p1 = [dx * far * (mat ? 0.55 : 0.4), H * (mat ? 0.1 : 1.75) * jit, dz * far * (mat ? 0.55 : 0.4)];
      const p2 = [dx * far, H * (mat ? 0.12 : 0.28) * jit, dz * far];
      at = (t) => {
        const s = 1 - t;
        return [s * s * base[0] + 2 * s * t * p1[0] + t * t * p2[0],
                2 * s * t * p1[1] + t * t * p2[1],
                s * s * base[2] + 2 * s * t * p1[2] + t * t * p2[2]];
      };
      clear = 0.08;
    } else {                                      // a vase: the outer stems lean out
      // A crown that was read says how far out and how low the outer stems end.
      const cs = _WD_CROWN_STEM[P.crown] || [0.8, 0.42];
      const tipR = R * cs[0] * Math.pow(fr, 0.8), tipY = H * (0.97 - cs[1] * Math.pow(fr, 1.5)) * jit;
      at = (t) => [base[0] + (dx * tipR - base[0]) * Math.pow(t, 1.7), tipY * t,
                   base[2] + (dz * tipR - base[2]) * Math.pow(t, 1.7)];
    }
    // Bare below the lowest leafy branch where the crown says so (V3.63).
    // `clear` is a share of the HEIGHT; a leaning stem reaches it further along.
    if (P.clear > 0) {
      const share = P.clear * H / Math.max(0.01, at(1)[1]);
      clear = Math.max(clear, Math.min(0.85, share * (0.9 + 0.2 * rng())));
    }
    const pts = [0, 0.3, 0.6, 0.85, 1].map(at), tip = pts[4];
    const rs = r0 * (0.85 + 0.3 * rng());
    _lbTube(G.S, pts, rs, rs * 0.3, 0.6 + 0.3 * tip[1] / H);
    G.shoots.push({ a: at(0.82), b: tip });
    const turn = rng() * 6.283;
    for (let j = 0; j < kids; j++) {
      const f = clear + (0.95 - clear) * (j + 0.3 + 0.4 * rng()) / kids;
      const tg = _lbUnit(_lbAdd(at(Math.min(1, f + 0.05)), at(Math.max(0, f - 0.05)), -1));
      const p = at(f);
      // A mat's shoots stand up from its limbs to the top of the mound there.
      const len = P.form === 'mat'
        ? Math.max(0.15 * H, H * _wdEnvelope('mat', Math.min(1, Math.hypot(p[0], p[2]) / R)) - p[1])
        : reach * (1 - 0.35 * f);
      _wdChild(G, p, tg, len * (0.8 + 0.4 * rng()), rs * (1 - 0.6 * f) * 0.55,
               (quota - 1) / kids, turn + j * 2.39996);
    }
  }
}

// ── the leaves on the shoots ────────────────────────────────────────────────

// One spray: a card `w` wide and `h` long from `A` along `T`, `S` across it.
function _wdCard(F, A, T, S, w, h, shade) {
  const base = F.pos.length / 3, hw = w / 2;
  for (const [u, v] of [[0, 0], [1, 0], [1, 1], [0, 1]]) {
    const k = (u - 0.5) * w;
    F.pos.push(A[0] + S[0] * k + T[0] * h * v, A[1] + S[1] * k + T[1] * h * v,
               A[2] + S[2] * k + T[2] * h * v);
    const c = shade * (v ? 1.06 : 0.9);              // lighter toward its tip
    F.col.push(c, c, c); F.uv.push(u, v);
  }
  F.idx.push(base, base + 1, base + 2, base, base + 2, base + 3);
  return hw;
}

function _woodyLeaves(G) {
  const P = G.P, rng = G.rng, F = G.F, sp = P.spray;
  const w = sp.w * P.L * P.gain, h = sp.h * P.L * P.gain;
  const lens = G.shoots.map(s => Math.hypot(s.b[0] - s.a[0], s.b[1] - s.a[1], s.b[2] - s.a[2]) + h * 0.5);
  const total = lens.reduce((x, y) => x + y, 0) || 1;
  let owed = 0;
  G.shoots.forEach((s, si) => {
    owed += P.cards * lens[si] / total;
    const n = Math.floor(owed);
    if (n < 1) return;
    owed -= n;
    const dir = _lbUnit(_lbAdd(s.b, s.a, -1));
    const u = _lbUnit(_lbCross(dir, Math.abs(dir[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0])), wv = _lbCross(dir, u);
    const turn = rng() * 6.283;
    for (let k = 0; k < n; k++) {
      // The last spray continues the shoot; the others stand off round it.
      const f = n === 1 ? 0.55 : k / (n - 1), tipward = k === n - 1;
      const at = _lbMix(s.a, s.b, 1 - f * 0.9, f * 0.9);
      const psi = turn + k * 2.39996, off = tipward ? 0.15 : 0.6;
      const e = _lbMix(u, wv, Math.cos(psi), Math.sin(psi));
      const D = [dir[0] + e[0] * off, dir[1] + e[1] * off + (rng() - 0.65) * 0.35, dir[2] + e[2] * off];
      // In the crown's shade a leaf is darker: by how far out and up it is.
      const b0 = P.base == null ? 0.3 : P.base;
      const rho = Math.hypot(Math.hypot(at[0], at[2]) / P.R, (at[1] - b0 * P.H) / ((1 - b0) * P.H));
      const shade = (0.5 + 0.45 * Math.pow(_wdClamp(rho, 0, 1), 2)) * (0.92 + 0.16 * rng());
      // It faces the sky and the open side of the crown, where its light comes from.
      const out = _lbUnit([at[0], 0.001, at[2]]);
      // How much a card faces the sky rather than out (a tree's are its own).
      const up = P.faceUp == null ? 0.7 : P.faceUp, side = 1.3 - up;
      const Nn = _lbUnit([out[0] * side + (rng() - 0.5) * 0.8, up + (rng() - 0.5) * 0.6,
                          out[2] * side + (rng() - 0.5) * 0.8]);
      const dn = D[0] * Nn[0] + D[1] * Nn[1] + D[2] * Nn[2];
      const T = _lbUnit(_lbAdd(D, Nn, -dn)), S = _lbCross(Nn, T);
      // A tree's sprays are smaller where its crown narrows (03e-crowns.js).
      const ks = G.cardScale ? G.cardScale(at) : 1;
      const hh = h * ks * (0.8 + 0.4 * rng());
      _wdCard(F, at, T, S, w * ks * (0.85 + 0.3 * rng()), hh, shade);
      G.tips.push(_lbAdd(at, T, hh));
    }
  });
}

// ── the body ────────────────────────────────────────────────────────────────

// Where flowers and fruit go: the outermost third of `pts` (a plant flowers
// where its shoots reach the light, and a cluster among the leaves behind
// them would not be seen), from `floor` of the way up, into the unit frame,
// in an order that spreads any few of them round the crown (15b-anchors.js).
function woodyEnds(P, pts, sxz, sy, floor) {
  const far = (q) => Math.hypot(Math.hypot(q[0], q[2]) / P.R, q[1] / P.H);
  const cut = pts.map(far).sort((x, y) => x - y)[Math.floor(pts.length * 0.67)] || 0;
  const ends = pts.filter(q => far(q) >= cut)
    .map(q => ({ x: q[0] * sxz, y: q[1] * sy, z: q[2] * sxz }))
    .filter(e => e.y >= floor);
  const out = [];
  for (let i = 0, j = 0; i < ends.length; i++, j = (j + 37) % ends.length) {
    while (ends[j] === null) j = (j + 1) % ends.length;
    out.push(ends[j]); ends[j] = null;
  }
  return out;
}

// What makes two shrubs' bodies the same geometry: the species, its numbers and
// how far grown this one is.
function woodyKeyFor(p) {
  const d = p && p.drawn;
  if (STYLISED || !d || d.body !== 'woody' || WOODY_FORMS.indexOf(d.form) < 0) return null;
  return ['woody', p.genus || '', p.species || '', d.form, d.mature_h, d.mature_w, d.stems,
          d.leaf_m, d.leaf_shape, d.arrangement, d.crown || '', d.clear || 0,
          _woodyTier(d)].join('|');
}

function _wdGeometry(B, sy, sxz) {
  const g = new THREE.BufferGeometry(), pos = new Float32Array(B.pos.length);
  for (let i = 0; i < B.pos.length; i += 3) {
    pos[i] = B.pos[i] * sxz; pos[i + 1] = B.pos[i + 1] * sy; pos[i + 2] = B.pos[i + 2] * sxz;
  }
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(B.col, 3));
  g.setIndex(B.idx);
  g.computeVertexNormals();
  return g;
}

// The body for the shrubs sharing a key: {foliageGeo, stemGeo} in the unit
// frame every shrub is placed in (base at 0, height 1), `v` one of its random
// builds. The leaves and the stems are two meshes, as the baked shrub's are:
// the stems take the bark's colour, and stand alone when the leaves are down.
function buildWoodyGeo(p, v) {
  const d = p.drawn, P = _woodyPlan(d, QUALITY);
  const G = { P, S: _lbNew(), F: Object.assign(_lbNew(), { uv: [] }), shoots: [], tips: [],
              rng: mulberry32(hashPid((p.genus || '') + (p.species || '') + d.form) + 131 * v),
              // A branch thinner than this is a strip, and no strip is narrower than `twig`.
              tube: Math.max(0.004, P.H * 0.0022), twig: P.H * 0.0026 };
  if (P.crown) {                                  // its own outline (V3.63)
    G.env = (t) => _wdCrownEnvelope(P.crown, t, P.clear);
    G.bias = _WD_CROWN_BIAS[P.crown];
  }
  _woodyStems(G);
  // The leaves get what the stems left of the budget.
  _woodyCards(P, Math.max(200, P.budget - G.S.idx.length / 3));
  _woodyLeaves(G);
  let top = 0.01, half = 0.01;
  for (const B of [G.S, G.F]) {
    for (let i = 0; i < B.pos.length; i += 3) {
      top = Math.max(top, B.pos[i + 1]);
      half = Math.max(half, Math.hypot(B.pos[i], B.pos[i + 2]));
    }
  }
  // Into the unit frame: as tall as recorded, and as wide. The outline was
  // built to both, so the two scales differ by a few percent at most.
  const sy = 1 / top, sxz = sy * _wdClamp(P.R / half * top / P.H, 0.75, 1.3);
  const foliageGeo = _wdGeometry(G.F, sy, sxz), stemGeo = _wdGeometry(G.S, sy, sxz);
  foliageGeo.setAttribute('uv', new THREE.Float32BufferAttribute(G.F.uv, 2));
  // Where flowers and fruit go: the ends of the leafy shoots, or of the bare
  // twigs when the leaves are down, from a quarter of the way up, in an order
  // that spreads any few of them round the crown (15b-anchors.js).
  foliageGeo.userData.crown = woodyEnds(P, G.tips, sxz, sy, P.form === 'mat' ? 0 : 0.25);
  stemGeo.userData.crown = woodyEnds(P, G.shoots.map(s => s.b), sxz, sy,
                                     P.form === 'mat' ? 0 : 0.25);
  for (const g of [foliageGeo, stemGeo]) g.userData.unitHalfWidth = half * sxz;
  foliageGeo.userData.cut = P.spray;
  foliageGeo.userData.woody = { triangles: (G.F.idx.length + G.S.idx.length) / 3,
                                stemTriangles: G.S.idx.length / 3, plan: P,
                                shoots: G.shoots.length };
  return { foliageGeo, stemGeo, vertexColorBark: true };
}

// ── the shrub layer (moved here from 04-quality.js, which was at its ceiling) ─

// Shrub archetypes are profile-specific (growth form, red-stem dogwood…), so
// they're cached by (profile × variant × quality) like trees rather than the
// flat ARCH.shrub array. Each is {foliageGeo, stemGeo}: the leaves and the
// woody stems, each shaded/coloured separately.
const SHRUB_VARIANTS = 3;
const SHRUB_CACHE = new Map();
// `morph` is the species' leaf characters and `vkey` their baked-variant name
// (02-plants.js variantKeyFor), or the shrub's own key and the shrub itself
// when it is drawn from its numbers. Both belong in the cache key: they select
// a DIFFERENT geometry, so leaving them out would hand a rose the dogwood's
// leaves whenever the two shared a profile and variant.
function getShrubArch(prof, v, vkey, morph, own) {
  const key = prof.id + '_' + v + '_' + vkey + '_q' + QUALITY;
  let a = SHRUB_CACHE.get(key);
  if (a) return a;
  a = (own && buildWoodyGeo(morph, v)) ||
      (useGLB() && window.glbShrubArch && window.glbShrubArch(prof.form, vkey)) ||
      buildShrubGeo(mulberry32(13 + v * 97 + prof.id.charCodeAt(0) * 7), prof,
                    morph);
  SHRUB_CACHE.set(key, a);
  return a;
}

function buildShrubLayer(list, month, year, terrain) {
  if (!list || !list.length) return;
  const buckets = {};
  for (const p of list) {
    const prof = shrubProfileFor(p);
    const v = hashPid(p.plant_id) % SHRUB_VARIANTS;
    const own = woodyKeyFor(p);                        // its own numbers (V3.49)
    const vkey = own || variantKeyFor(p, 'shrub');
    const bark = barkClassFor(p), surf = leafSurfaceFor(p);
    const bk = prof.id + '_' + v + '_' + vkey + '_' + bark + '_' + surf;
    (buckets[bk] = buckets[bk]
      || { prof, v, vkey, bark, surf, own, morph: own ? p : morphOf(p, 'shrub'), items: [] })
      .items.push(p);
  }
  for (const key in buckets) {
    const { prof, v, vkey, morph, bark, surf, own, items } = buckets[key];
    const arch = getShrubArch(prof, v, vkey, morph, own);
    const places = items.map(p => spreadPlacements(p, year));
    const total = places.reduce((s, pl) => s + pl.length, 0);
    // Both paths carry colours (the GLB's baked shade, the procedural gradient).
    // Without `true` they were off, and no shrub drew either until V2.96 (F188).
    // A shrub drawn from its numbers wears its leaves' outline (_wdSpray).
    const cut = arch.foliageGeo.userData.cut;
    const foliage = instancedMesh(arch.foliageGeo, total,
      surfaceMaterial(MAT_PRESETS.shrubLeaf, surf, true, cut));
    if (cut) foliage.customDepthMaterial = cut.depth;
    const stems = arch.stemGeo
      ? instancedMesh(arch.stemGeo, total,
                      surfaceMaterial(MAT_PRESETS.bark, bark,
                                      !!arch.vertexColorBark))
      : null;
    // Woody stems take the species' own bark colour where the seed data has
    // one — which is how red-osier dogwood gets its red, generalised from the
    // genus special case that used to be the only way to say so.
    const stemHex = items.length && items[0].bark_color
      ? items[0].bark_color : (prof.redStems ? '#b5402e' : '#6b5236');
    const names = new Array(total), ids = new Array(total);
    let idx = 0;
    items.forEach((p, ii) => {
      const c = unitXZ(arch.foliageGeo, Math.max(0.25, p.canopy_m));
      const h = bodyHeightOf(p);
      const rotY0 = (indHash(p) % 628) / 100;
      const col = bodyColor(p, month);                 // 01d-season.js
      const scol = fadeToward(stemHex, p.opacity);
      const lf = stems && leafless(p, month) ? 0.001 : 1;   // leaves down (V3.46)
      places[ii].forEach((pl, k) => {
        const m = pl.mul, x = p.x + pl.dx, wy = p.y + pl.dz;
        const rotY = rotY0 + (k ? pl.dx : 0);
        const gy = terrainHeightAt(x, wy, terrain);
        if (!k && window.noteVineHost) {
          noteVineHost(p, [arch.foliageGeo, arch.stemGeo], x, gy, -wy, c * m, h * m, rotY);
        }
        setInst2(foliage, idx, x, gy, -wy, c * m * lf, h * m * lf, c * m * lf, rotY, col);
        if (stems) setInst2(stems, idx, x, gy, -wy, c * m, h * m, c * m, rotY, scol);
        names[idx] = p.common_name || '';
        ids[idx] = p.plant_id;
        idx++;
      });
    });
    foliage.userData.pick = names;
    foliage.userData.pickId = ids;
    // Pick from the stems too, the way trees already do from the trunk: a
    // deciduous shrub in winter is nothing BUT stems, and it should still name
    // and open on a click.
    if (stems) { stems.userData.pick = names; stems.userData.pickId = ids; }
    plantsGroup.add(foliage);
    if (stems) plantsGroup.add(stems);
  }
}

window.woodyKeyFor = woodyKeyFor;
window.buildWoodyGeo = buildWoodyGeo;
