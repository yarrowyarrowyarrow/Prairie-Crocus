// Part of the Site & Pattern 3D viewer. Loaded as an ordered CLASSIC
// script by the bootstrap in scene3d.html — it shares the global scope
// with its siblings (THREE and friends are globals set by the
// bootstrap). Do not add ES `import`/`export` here.
//
// Design principle P5 — see docs/DESIGN_PHILOSOPHY.md
//
// A tree drawn from its own crown (V3.50, F268).
//
// Read against photographs, all ten of the region's native trees had the
// wrong crown: an aspen a long pole with a dozen leaf clumps near its top, a
// paper birch a white pole with four leaders, a tamarack solid plates, a jack
// pine a narrow bottle brush. Where somebody has read a tree's crown
// (src/tree_habit.py writes a `drawn` block with body 'crown'), this chunk
// builds it from what was read: as many trunks as it has, bare as high as the
// photographs show, limbs leaving the trunk the way they go (climbing, level,
// or drooping with upturned tips), forking to shoots inside the outline that
// was read, and the shoots carrying the species' own leaf, or its needles as
// a spruce, a pine or a tamarack carries them.
//
// It is the shrubs' body (03d-woody.js) with a trunk and limbs under it: the
// forking, the leafy shoots as cards cut to their leaves' outline, the budget
// that sets how much larger than life a spray is drawn, and the ends the
// flowers go on are that chunk's, given this chunk's outline.
//
// What nothing records, and is a stated estimate here:
//  * a trunk's thickness: TRUNK_PIPE x height, shared between trunks (a 20 m
//    aspen 38 cm across at the base, an 8 m pin cherry 15 cm);
//  * how many limbs a crown has (limbCount; a conifer's whorls WHORL_GAP
//    apart), and the angle each habit leaves the trunk at (LIMB_RISE);
//  * how many sprays a shoot carries (CROWN_PER_SHOOT): more than a shrub's,
//    so the twigs do not take the leaves' budget;
//  * how long a needle spray is, in needles (SPRAY_UNIT).

// The outlines and limb habits (src/tree_habit.py SHAPES / LIMBS; a test
// holds them equal).
const CROWN_SHAPES = ['conical', 'spire', 'oval', 'rounded', 'irregular'];
const LIMB_HABITS = ['ascending', 'spreading', 'drooping'];
// Triangles one tree may spend, by detail level: [one CROWN_BUDGET_H[0] tall or
// less, one CROWN_BUDGET_H[1] tall or more]. The baked crowns' largest was 6,000.
const CROWN_BUDGET = [[0, 0], [6000, 14000], [10000, 24000]];
const CROWN_BUDGET_H = [5, 20];
// A trunk's radius at the ground: TRUNK_PIPE x the tree's height, over the
// square root of how many trunks share the crown.
const TRUNK_PIPE = 0.0095;
// The angle, in radians above level, a main limb leaves the trunk at; the bias
// its branches turn by (towards the sky, away from the middle); how far they
// may hang below level.
const LIMB_RISE = { ascending: 0.8, spreading: 0.12, drooping: -0.28 };
const LIMB_BIAS = { ascending: [0.38, 0.25], spreading: [0.06, 0.3], drooping: [-0.04, 0.35] };
const LIMB_DROOP = { ascending: 0, spreading: 0.12, drooping: 0.4 };
// A needle spray's length, in needles: a spruce frond, a pine shoot's tuft, a
// tamarack twig with its rosettes.
const SPRAY_UNIT = { frond: 16, tuft: 8, rosette: 10 };
// How much a tree's sprays face the sky rather than out from the crown: a
// conifer's fronds lie level but hang and turn at their ends, so from a
// person's height they are seen more from the side than a shrub's.
const CROWN_FACE_UP = { leaf: 0.5, frond: 0.32, tuft: 0.4, rosette: 0.4 };
// How much of WOODY_COVER a crown of each spray fills (V3.67b, an estimate read
// off the photographs): a pine's and a tamarack's crowns are open, the sky and
// their branches seen through them; filled as a spruce's, a jack pine read as a
// poplar and a tamarack as a spruce.
const CROWN_OPEN = { leaf: 1, frond: 1, tuft: 0.5, rosette: 0.45 };
// A conifer's whorls: how far apart up the trunk, in metres (never closer than
// a fortieth of the tree), and limbs to a whorl.
const WHORL_GAP = 0.4, WHORL_LIMBS = 4;
const CROWN_PER_SHOOT = 6;

// The crown's radius at `t` of the tree's height, 0 to 1 of its widest; none
// below `base`, the share of the height that is bare trunk.
function crownEnvelope(shape, t, base) {
  if (t < base * 0.98) return 0;
  const u = Math.min(1, Math.max(0, (t - base) / Math.max(0.05, 1 - base)));
  switch (shape) {
    case 'conical': return Math.min(1, (1 - u) * 1.06);
    case 'spire':   // narrow, with the dense club near the top a black spruce carries
      return Math.min(1, Math.pow(1 - u, 1.25) * 0.9 + 0.22 * Math.exp(-Math.pow((u - 0.86) / 0.07, 2)));
    case 'rounded': return u < 0.42 ? 0.72 + 0.28 * (u / 0.42)
      : Math.sqrt(Math.max(0, 1 - Math.pow((u - 0.42) / 0.58, 2)));
    case 'irregular': return Math.pow(Math.sin(Math.PI * Math.min(1, u * 0.86 + 0.07)), 0.45);
    default:        return Math.pow(Math.sin(Math.PI * Math.min(1, u * 0.92 + 0.05)), 0.62);  // oval
  }
}

// ── needles ─────────────────────────────────────────────────────────────────

// The mask for a needled shoot, painted at the needle's size against the
// spray's length (SPRAY_UNIT): {w, h} are the card's size in spray lengths.
const _CR_NEEDLES = new Map();
function _crNeedles(kind) {
  let sp = _CR_NEEDLES.get(kind);
  if (sp) return sp;
  const W = 128, H = 256, cv = document.createElement('canvas');
  cv.width = W; cv.height = H;
  const g = cv.getContext('2d', { willReadFrequently: true });
  g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
  g.strokeStyle = '#fff'; g.lineCap = 'round';
  const rnd = _lcg(41 + kind.length * 211);                       // 01b-surface.js
  const n = H / SPRAY_UNIT[kind];                                 // a needle, in pixels
  const line = (x0, y0, a, len, wdt) => {
    g.lineWidth = wdt; g.beginPath(); g.moveTo(x0, y0);
    g.lineTo(x0 + Math.sin(a) * len, y0 - Math.cos(a) * len); g.stroke();
  };
  // Needles all round a twig from (x0, y0) along bearing `a`, `len` long, seen
  // from above: short strokes either side, pointing forward.
  const brush = (x0, y0, a, len, step) => {
    line(x0, y0, a, len, 2.4);
    for (let s = step; s < len; s += step) {
      const x = x0 + Math.sin(a) * s, y = y0 - Math.cos(a) * s;
      for (const side of [-1, 1]) line(x, y, a + side * (0.85 + 0.3 * rnd()), n * (0.8 + 0.3 * rnd()), 1.7);
    }
  };
  if (kind === 'frond') {           // a spruce's: twiglets off a twig, every one needled
    const L = H * 0.96;
    brush(W / 2, H, 0, L, 2.6);
    for (let j = 0; j < 16; j++) {
      const f = 0.08 + 0.84 * j / 15, side = j % 2 ? 1 : -1;
      brush(W / 2, H - L * f, side * (0.9 - 0.2 * f), (W * 0.46) * (1 - 0.6 * f), 2.6);
    }
  } else if (kind === 'tuft') {     // a pine's: long needles in bundles, crowded at the shoots' ends
    const tuft = (x0, y0, a0, L) => {
      line(x0, y0, a0, L, 2.6);
      for (let i = 0; i < 46; i++) {
        const f = Math.pow(rnd(), 0.6), s = L * (0.3 + 0.7 * f);
        const x = x0 + Math.sin(a0) * s, y = y0 - Math.cos(a0) * s;
        line(x, y, a0 + (rnd() - 0.5) * (1.1 + 0.8 * (1 - f)), n * (0.85 + 0.25 * rnd()), 1.5);
      }
    };
    line(W / 2, H, 0, H * 0.45, 3);
    tuft(W / 2, H * 0.55, 0, H * 0.22);
    tuft(W / 2, H * 0.62, -0.6, H * 0.2);
    tuft(W / 2, H * 0.6, 0.6, H * 0.2);
    tuft(W / 2, H * 0.82, -0.9, H * 0.18);
    tuft(W / 2, H * 0.8, 0.9, H * 0.18);
  } else {                          // a tamarack's: soft rosettes on spurs along the twigs
    const twig = (x0, y0, a0, L, k) => {
      line(x0, y0, a0, L, 1.8);
      for (let j = 0; j < k; j++) {
        const s = L * (0.12 + 0.85 * j / Math.max(1, k - 1));
        const x = x0 + Math.sin(a0) * s, y = y0 - Math.cos(a0) * s;
        for (let i = 0; i < 18; i++) line(x, y, a0 + (rnd() - 0.5) * 2.6, n * (0.5 + 0.5 * rnd()), 1.2);
      }
    };
    twig(W / 2, H, 0, H * 0.95, 9);
    twig(W / 2, H * 0.6, -0.6, H * 0.4, 5);
    twig(W / 2, H * 0.4, 0.6, H * 0.36, 4);
  }
  sp = Object.assign(woodyMask('needle-' + kind, cv), { w: W / H, h: 1, leaves: 0 });   // 03d-woody.js
  _CR_NEEDLES.set(kind, sp);
  return sp;
}

// A broadleaf tree's spray: three of the species' leafy shoots on a forked
// twig, so one card carries the leaves a big crown needs (a shrub's carries
// one shoot). Its size is in leaf lengths, as the shoot's is.
const _CR_BRANCHLETS = new Map();
function _crBranchlet(shape, perNode) {
  const one = _wdSpray(shape, perNode), key = one.key;
  let sp = _CR_BRANCHLETS.get(key);
  if (sp) return sp;
  const S = 256, cv = document.createElement('canvas');
  cv.width = cv.height = S;
  const g = cv.getContext('2d', { willReadFrequently: true });
  g.fillStyle = '#000'; g.fillRect(0, 0, S, S);
  const img = one.map.image, k = 0.62, w = img.width * k, h = img.height * k;
  g.strokeStyle = '#fff'; g.lineCap = 'round'; g.lineWidth = 3;
  g.beginPath(); g.moveTo(S / 2, S); g.lineTo(S / 2, S - h * 0.35); g.stroke();
  for (const [a, dy] of [[0, 0.3], [-0.62, 0.12], [0.62, 0.16]]) {
    g.save();
    g.translate(S / 2, S - h * dy); g.rotate(a);
    g.drawImage(img, -w / 2, -h, w, h);
    g.restore();
  }
  const px = img.width / one.w;                     // a leaf, in the shoot's pixels
  sp = Object.assign(woodyMask('branchlet-' + key, cv), { w: S / (px * k), h: S / (px * k), leaves: 0 });
  _CR_BRANCHLETS.set(key, sp);
  return sp;
}

// ── the plan ────────────────────────────────────────────────────────────────

function _crownPlan(d, quality) {
  const tier = _woodyTier(d);                                      // 03d-woody.js
  const H = Math.max(1, d.mature_h * tier), R = Math.max(0.3, d.mature_w / 2 * tier);
  const kind = d.spray || 'leaf', needles = kind !== 'leaf';
  const L = Math.max(0.004, d.leaf_m) * (needles ? SPRAY_UNIT[kind] : 1);
  const perNode = d.arrangement === 'opposite' ? 2 : (d.arrangement === 'whorled' ? 3 : 1);
  const spray = needles ? _crNeedles(kind) : _crBranchlet(d.leaf_shape, perNode);
  const b = CROWN_BUDGET[_wdClamp(quality, 1, 2)];
  const budget = Math.round(b[0] + (b[1] - b[0])
    * _wdClamp((H - CROWN_BUDGET_H[0]) / (CROWN_BUDGET_H[1] - CROWN_BUDGET_H[0]), 0, 1));
  // The crown's shell: its side, band by band, and half its top.
  let area = 0;
  for (let i = 0; i < 24; i++) {
    const t = (i + 0.5) / 24;
    area += 2 * Math.PI * R * crownEnvelope(d.form, t, d.clear) * H / 24;
  }
  area = area * 0.8 + Math.PI * R * R * 0.4;
  const need = WOODY_COVER * (CROWN_OPEN[kind] || 1) * area
    / (spray.w * L * spray.h * L * (spray.leafCover || spray.cover) * 0.6);
  const P = { H, R, L, shape: d.leaf_shape, form: d.form, budget, area, need, spray, tier,
              gain: 1, cards: 0, base: d.clear, faceUp: CROWN_FACE_UP[kind], trunks: Math.max(1, Math.min(12, d.trunks || 1)),
              limbs: LIMB_HABITS.indexOf(d.limbs) >= 0 ? d.limbs : 'spreading', needles };
  P.conifer = needles && (d.form === 'conical' || d.form === 'spire');
  const span = H * (1 - P.base);
  P.limbCount = P.conifer
    ? Math.min(180, WHORL_LIMBS * Math.round(span / Math.max(WHORL_GAP, H / 40)))
    : Math.round(_wdClamp(10 + 1.5 * H * (1 - 0.4 * P.base), 12, 46) * (1 + 0.12 * (P.trunks - 1)));
  _woodyCards(P, budget * 0.72);
  P.shoots = Math.max(P.limbCount * 2, Math.round(P.cards / CROWN_PER_SHOOT));
  return P;
}

// ── the skeleton ────────────────────────────────────────────────────────────

// A round tapering stem through `pts`, `sides` faces round.
function _crTube(B, pts, r0, r1, sides, shade) {
  const base = B.pos.length / 3, n = pts.length;
  for (let i = 0; i < n; i++) {
    const d = _lbUnit(_lbAdd(pts[Math.min(n - 1, i + 1)], pts[Math.max(0, i - 1)], -1));
    const u = _lbUnit(_lbCross(d, Math.abs(d[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0]));
    const v = _lbCross(d, u), r = r0 + (r1 - r0) * Math.pow(i / Math.max(1, n - 1), 0.8);
    for (let k = 0; k < sides; k++) {
      const a = k * 6.2832 / sides, cs = Math.cos(a) * r, sn = Math.sin(a) * r;
      B.pos.push(pts[i][0] + u[0] * cs + v[0] * sn, pts[i][1] + u[1] * cs + v[1] * sn,
                 pts[i][2] + u[2] * cs + v[2] * sn);
      const c = shade * (0.85 + 0.15 * Math.cos(a));
      B.col.push(c, c, c);
    }
  }
  for (let i = 0; i < n - 1; i++) {
    for (let k = 0; k < sides; k++) {
      const a = base + i * sides + k, b = base + i * sides + (k + 1) % sides;
      B.idx.push(a, b, a + sides, b, b + sides, a + sides);
    }
  }
}

// A smooth path through `pts` at `t` 0..1 (a Catmull-Rom chain), and its direction.
function _crAt(pts, t) {
  const n = pts.length - 1, f = Math.min(n - 1e-6, Math.max(0, t * n)), i = Math.floor(f), s = f - i;
  const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(n, i + 2)];
  const out = [0, 0, 0];
  for (let k = 0; k < 3; k++) {
    out[k] = 0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * s + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * s * s
                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * s * s * s);
  }
  return out;
}
function _crDir(pts, t) {
  return _lbUnit(_lbAdd(_crAt(pts, Math.min(1, t + 0.02)), _crAt(pts, Math.max(0, t - 0.02)), -1));
}

// The trunks (and a rounded crown's leaders, which fork from one low down).
function _crTrunks(G) {
  const P = G.P, rng = G.rng, { H, R } = P, N = P.trunks;
  const r0 = Math.max(0.02, TRUNK_PIPE * H / Math.sqrt(N));
  const spread = Math.min(R * 0.25, 0.1 * Math.sqrt(N));
  const wob = P.form === 'irregular' ? 0.05 : 0.015, rot = rng() * 6.283;
  const out = [];
  const one = (base, top, r, lean, a) => {
    const pts = [];
    for (let k = 0; k <= 6; k++) {
      const t = k / 6, w = Math.sin(t * 9 + a * 3) * wob * H * t;
      pts.push([base[0] + Math.cos(a) * lean * t * t + Math.cos(a + 1.6) * w,
                base[1] + (top - base[1]) * t,
                base[2] + Math.sin(a) * lean * t * t + Math.sin(a + 1.6) * w]);
    }
    _crTube(G.S, pts, r, r * 0.1, r > 0.05 ? 8 : 6, 0.82);
    out.push({ pts, r, y0: base[1], y1: top });
  };
  for (let i = 0; i < N; i++) {
    const fr = N === 1 ? 0 : Math.sqrt((i + 0.3) / N), a = rot + i * 2.39996;
    const base = [Math.cos(a) * spread * fr, 0, Math.sin(a) * spread * fr];
    if (P.form === 'rounded' && N === 1) {           // forks into leaders above the bole
      const fork = H * Math.min(0.55, P.base + 0.12);
      one(base, fork, r0, 0, a);
      for (let j = 0; j < 3; j++) {
        const b = a + j * 2.094 + rng() * 0.4;
        one([base[0], fork * 0.97, base[2]], H * (0.86 + 0.12 * rng()), r0 * 0.62, R * 0.35, b);
      }
    } else {
      const lean = N === 1 ? H * 0.02 * rng() : H * (0.06 + 0.14 * fr);
      one(base, H * (N === 1 ? 1 : 0.84 + 0.16 * rng()), r0, lean, a);
    }
  }
  return out;
}

// The main limbs, from the top of the bare bole up each trunk, and their
// branches to the shoots the leaves need.
function _crLimbs(G, trunks) {
  const P = G.P, rng = G.rng, { H, R } = P;
  const conifer = P.conifer, whorl = conifer ? WHORL_LIMBS : 1;
  const total = trunks.reduce((s, t) => s + (t.y1 - Math.max(t.y0, P.base * H)), 0) || 1;
  const quota = P.shoots / P.limbCount;
  for (const tr of trunks) {
    const y0 = Math.max(tr.y0 + 0.05, P.base * H), y1 = tr.y1 * 0.97;
    if (y1 <= y0) continue;
    const n = Math.max(2, Math.round(P.limbCount * (y1 - y0) / total));
    const groups = Math.max(1, Math.round(n / whorl)), turn = rng() * 6.283;
    for (let gi = 0; gi < groups; gi++) {
      const f = (gi + 0.5 + (conifer ? 0 : (rng() - 0.5) * 0.6)) / groups;
      const y = y0 + (y1 - y0) * f, tf = (y - tr.y0) / Math.max(1e-3, tr.y1 - tr.y0);
      const A = _crAt(tr.pts, _wdClamp(tf, 0, 1)), rT = tr.r * (1 - 0.9 * tf);
      for (let k = 0; k < whorl; k++) {
        const a = turn + gi * 2.39996 + k * 6.2832 / whorl + (rng() - 0.5) * 0.5;
        // Upper limbs climb more than lower ones on every habit; a spruce's
        // lowest hang and its upper ones rise.
        const u = (y - P.base * H) / Math.max(1e-3, H * (1 - P.base));
        const e = LIMB_RISE[P.limbs] + u * (conifer ? 0.55 : 0.25) + (rng() - 0.5) * 0.3;
        const dir = [Math.cos(a) * Math.cos(e), Math.sin(e), Math.sin(a) * Math.cos(e)];
        let l = R * 1.05 * (0.8 + 0.3 * rng());
        for (let it = 0; it < 6; it++) {         // inside the outline at its far end
          const q = _lbAdd(A, dir, l);
          if (q[1] <= H * 1.01 && Math.hypot(q[0], q[2])
              <= R * crownEnvelope(P.form, _wdClamp(q[1] / H, 0, 1), P.base) + 0.05) break;
          l *= 0.8;
        }
        if (l < 0.12) continue;
        const E = _lbAdd(A, dir, l), sag = P.limbs === 'drooping' ? 0.16 : (P.limbs === 'spreading' ? 0.05 : 0);
        const M = _lbAdd(_lbMix(A, E, 0.5, 0.5), [0, -1, 0], l * sag);
        const tip = _lbAdd(E, [0, 1, 0], l * sag * 0.6);  // a drooping limb's tip turns up
        const pts = [A, M, tip];
        const r = Math.max(G.tube * 0.8, Math.min(rT * 0.55, 0.01 + 0.012 * l));
        if (r >= G.tube) _crTube(G.S, pts, r, r * 0.25, 5, 0.75);
        else _wdStrip(G.S, A, tip, Math.max(2 * r, G.twig), 0.75);      // 03d-woody.js
        G.shoots.push({ a: _crAt(pts, 0.7), b: tip });
        const kids = _wdClamp(Math.round(Math.sqrt(quota * 1.4)), 2, 9);
        for (let j = 0; j < kids; j++) {
          const fj = 0.2 + 0.75 * (j + 0.3 + 0.4 * rng()) / kids;
          _wdChild(G, _crAt(pts, fj), _crDir(pts, fj), l * (0.5 - 0.28 * fj) * (0.8 + 0.4 * rng()),
                   r * (1 - 0.6 * fj) * 0.6, (quota - 1) / kids, a + j * 2.39996);
        }
      }
    }
    // A leader's top, needled or leafy too.
    G.shoots.push({ a: _crAt(tr.pts, 0.9), b: tr.pts[tr.pts.length - 1] });
  }
}

// ── the body ────────────────────────────────────────────────────────────────

function crownKeyFor(p) {
  const d = p && p.drawn;
  if (STYLISED || !d || d.body !== 'crown' || CROWN_SHAPES.indexOf(d.form) < 0) return null;
  return ['crown', p.genus || '', p.species || '', d.form, d.mature_h, d.mature_w, d.trunks,
          d.clear, d.limbs, d.leaf_m, d.leaf_shape, d.arrangement, d.spray, _woodyTier(d)].join('|');
}

// The tree for the plants sharing a key: {branchGeo, foliageGeo} in the unit
// frame every tree is placed in, `v` one of its individuals.
function buildCrownGeo(p, v) {
  const d = p.drawn, P = _crownPlan(d, QUALITY);
  const G = { P, S: _lbNew(), F: Object.assign(_lbNew(), { uv: [] }), shoots: [], tips: [],
              rng: mulberry32(hashPid((p.genus || '') + (p.species || '') + 'crown') + 977 * v),
              tube: Math.max(0.006, P.H * 0.0016), twig: Math.max(0.004, P.H * 0.0011),
              env: (t) => crownEnvelope(d.form, t, P.base),
              bias: LIMB_BIAS[P.limbs], droop: LIMB_DROOP[P.limbs],
              // Sprays shrink where the outline narrows, so a spire ends in a point.
              cardScale: (q) => 0.45 + 0.55 * Math.min(1, crownEnvelope(d.form,
                _wdClamp(q[1] / P.H, 0, 1), P.base) / 0.35) };
  _crLimbs(G, _crTrunks(G));
  _woodyCards(P, Math.max(400, P.budget - G.S.idx.length / 3));     // 03d-woody.js
  _woodyLeaves(G);
  let top = 0.01, half = 0.01;
  for (const B of [G.S, G.F]) {
    for (let i = 0; i < B.pos.length; i += 3) {
      top = Math.max(top, B.pos[i + 1]);
      half = Math.max(half, Math.hypot(B.pos[i], B.pos[i + 2]));
    }
  }
  const sy = 1 / top, sxz = sy * _wdClamp(P.R / half * top / P.H, 0.8, 1.25);
  const foliageGeo = _wdGeometry(G.F, sy, sxz), branchGeo = _wdGeometry(G.S, sy, sxz);
  foliageGeo.setAttribute('uv', new THREE.Float32BufferAttribute(G.F.uv, 2));
  foliageGeo.userData.crown = woodyEnds(P, G.tips, sxz, sy, P.base * 0.9);
  branchGeo.userData.crown = woodyEnds(P, G.shoots.map(s => s.b), sxz, sy, P.base * 0.9);
  for (const g of [foliageGeo, branchGeo]) g.userData.unitHalfWidth = half * sxz;
  foliageGeo.userData.cut = P.spray;
  foliageGeo.userData.woody = { triangles: (G.F.idx.length + G.S.idx.length) / 3,
                                stemTriangles: G.S.idx.length / 3, plan: P,
                                shoots: G.shoots.length, crown: true };
  return { branchGeo, foliageGeo, vertexColorBark: true };
}

// Kept with the trees' own (04-quality.js TREE_CACHE), so a scene rebuild
// keeps it and a change of detail level drops it.
function getCrownArch(p, sub) {
  const key = 'crown|' + crownKeyFor(p) + '|' + sub + '_q' + QUALITY;
  let a = TREE_CACHE.get(key);
  if (!a) { a = buildCrownGeo(p, sub); TREE_CACHE.set(key, a); }
  return a;
}

window.crownKeyFor = crownKeyFor;
window.buildCrownGeo = buildCrownGeo;
window.getCrownArch = getCrownArch;
