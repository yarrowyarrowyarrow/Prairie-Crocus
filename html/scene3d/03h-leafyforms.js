// Part of the Site & Pattern 3D viewer. Loaded as an ordered CLASSIC
// script by the bootstrap in scene3d.html — it shares the global scope
// with its siblings (THREE and friends are globals set by the
// bootstrap). Do not add ES `import`/`export` here.
//
// Design principle P5 — see docs/DESIGN_PHILOSOPHY.md
//
// The leafy body's ground-hugging and one-leaf forms (V3.67b, F268), split
// from 03c-leafy.js, which was at its ceiling: the rosettes and the carpets
// of them, the tufts, and two forms the lowest-scoring readings asked for.
//
// * A TUFT whose leaves were measured across (`blade_m`, from blade_width_mm)
//   draws them that wide: wild chives' leaves are round tubes 3 mm across,
//   and at the linear outline's width ratio a 25 cm leaf was a 1.5 cm strap.
// * An UMBRELLA (src/herb_habit.py: a colony of shoots that are each one
//   divided leaf, a sarsaparilla's): each shoot a leaf stalk with the leaf's
//   three divisions spread level at its top, five leaflets each, and the
//   flowers on stalks of their own beneath, three umbels to a stalk. Drawn as
//   one leaf on a stem it drooped to the ground in ragged arcs.
// * FRONDS (a fern's, read off photographs): a crown of fronds rising and
//   arching out, each a rachis with its pinnae in pairs, longest above the
//   middle and dwindling to the base, the ostrich fern's shuttlecock. The
//   baked fern was a bundle of stalks with a few leaf blades on them.
//
// What nothing records, and is a stated estimate here: how steeply a frond
// rises and how far it arches over (FROND_RISE, FROND_BEND), its pinna pairs
// (FROND_PAIRS) and where along it the longest are (FROND_WIDEST); how far
// an umbrella's divisions droop from level (UMBRELLA_DROOP) and how tall its
// flowering stalks stand against its leaves (UMBRELLA_FLOWERS).

const FROND_RISE = 1.35, FROND_BEND = 0.85, FROND_PAIRS = [28, 40], FROND_WIDEST = 0.62;
const UMBRELLA_DROOP = 0.16, UMBRELLA_FLOWERS = [0.5, 0.68];
// A round leaf under 1.5 cm in a rosette stands this many blade lengths out on
// its stalk (a sundew's), where a broad round leaf's is about its own (an estimate).
const SMALL_ROUND_STALK = 2.6;
// How many times more leaves a tuft of thin, measured leaves holds (an estimate
// from wild chives' photographs: a clump of forty and more).
const TUFT_THIN = 2.5;

// Leaves round one point at the ground: the outer ones low, the inner rising.
function _leafyRosette(B, P, c, n, L, r0, rng) {
  const rot = rng() * 6.283;
  for (let i = 0; i < n; i++) {
    const a = i * 2.39996 + rot, inner = i / Math.max(1, n - 1);
    const at = [c[0] + Math.cos(a) * r0 * 0.5, c[1] + 0.004, c[2] + Math.sin(a) * r0 * 0.5];
    const small = P.shape === 'orbicular' && P.L < 0.015 ? SMALL_ROUND_STALK / STALK_BASAL : 1;
    const stalk = _stalkAtGround(P.shape) * small * (1 - 0.6 * inner) * (0.8 + 0.4 * rng());
    _lbSet(B, at, a, (_LONG_STALKED[P.shape] ? 0.5 : 0.16) + 0.75 * inner * inner + rng() * 0.12,
           L * (1 - 0.3 * inner), P.shape, P.lod, rng, 0.5 + 0.24 * inner, stalk);
  }
}

// A bare flower stalk from near `c` to `h`, leaning out by `lean`.
function _leafyStalk(B, P, c, h, lean, bloom, rng) {
  const a = rng() * 6.283, shade = 0.66 + rng() * 0.1;
  const r = Math.max(0.001, Math.min(0.004, h * 0.006));
  const foot = [c[0] + Math.cos(a) * 0.008, c[1], c[2] + Math.sin(a) * 0.008];
  const top = h - (bloom.rays ? bloom.rays * 0.5 : 0);
  const tip = [c[0] + Math.cos(a) * lean, c[1] + top, c[2] + Math.sin(a) * lean];
  const mid = [(foot[0] + tip[0]) / 2 + Math.cos(a) * lean * 0.15, c[1] + top * 0.5,
               (foot[2] + tip[2]) / 2 + Math.sin(a) * lean * 0.15];
  _lbTube(B, [foot, mid, tip], r, r * 0.6, shade);
  _lbTip(B, [tip[0], c[1] + h, tip[2]], bloom, rng, shade);
}

// The leaves of a mat that no budget draws one by one: a low mound under the
// ones that are drawn, in their colour, darker as the inside of a mat is.
function _leafyUnderlay(B, R, h, rng) {
  const base = B.pos.length / 3, N = 12, rot = rng() * 6.283;
  B.pos.push(0, h, 0); B.col.push(0.5, 0.5, 0.5);
  for (const [f, y] of [[0.6, h * 0.8], [1, 0.002]]) {
    for (let i = 0; i < N; i++) {
      const a = rot + i * 6.2832 / N, r = R * f * (0.86 + 0.14 * rng());
      B.pos.push(Math.cos(a) * r, y, Math.sin(a) * r);
      B.col.push(0.46, 0.46, 0.46);
    }
  }
  for (let i = 0; i < N; i++) {
    const a = base + 1 + i, b = base + 1 + (i + 1) % N;
    B.idx.push(base, b, a, a, b, a + N, b, b + N, a + N);
  }
}

// Where `n` rosettes or tufts sit to fill a disc of radius `R`.
function _leafySpots(n, R, rr, rng) {
  if (n <= 1) return [[0, 0, 0]];
  const out = [], rot = rng() * 6.283, reach = Math.max(0, R - rr * 0.8);
  for (let i = 0; i < n; i++) {
    const f = Math.sqrt((i + 0.5) / n), a = i * 2.39996 + rot;
    out.push([Math.cos(a) * reach * f, 0, Math.sin(a) * reach * f]);
  }
  return out;
}

// Rosettes (or a carpet of them) under bare flower stalks.
function _leafyRosettes(B, P, bloom, rng) {
  const spots = _leafySpots(P.groups, P.R, P.rr, rng);
  if (P.form === 'mat') {
    const h = Math.min(0.03, P.L * 0.4);
    _leafyUnderlay(B, P.R, h, rng);
    for (const c of spots) c[1] = h * (1 - 0.9 * Math.hypot(c[0], c[2]) / P.R);
  }
  for (const c of spots) _leafyRosette(B, P, c, P.basal, P.L, 0.01, rng);
  for (let i = 0; i < P.stems; i++) {
    const c = spots[i % spots.length];
    _leafyStalk(B, P, c, P.H * (i ? 0.78 + 0.22 * rng() : 1),
                Math.min(P.R * 0.5, P.H * 0.22) * rng(), bloom, rng);
  }
}

// Narrow leaves standing up from the ground and arching over, with bare stalks.
// Where the leaves were measured across (`P.bladeW`), each is drawn that wide.
function _leafyTufts(B, P, bloom, rng) {
  const spots = _leafySpots(P.groups, P.R, P.rr, rng);
  // Leaves measured thin (chives') stand crowded: TUFT_THIN times as many.
  const n = P.bladeW ? Math.round(P.basal * TUFT_THIN) : P.basal;
  for (const c of spots) {
    const rot = rng() * 6.283;
    for (let i = 0; i < n; i++) {
      const a = i * 2.39996 + rot, out = Math.sqrt((i + 0.5) / n);
      const at = [c[0] + Math.cos(a) * 0.012 * out, 0.003, c[2] + Math.sin(a) * 0.012 * out];
      const elev = 1.45 - 0.7 * out + (rng() - 0.5) * 0.2, len = P.L * (0.7 + 0.3 * rng());
      if (P.bladeW) {
        const T = [Math.cos(a) * Math.cos(elev), Math.sin(elev), Math.sin(a) * Math.cos(elev)];
        _lbBlade(B, at, T, _lbUnit([-Math.sin(a), 0, Math.cos(a)]), len, P.bladeW, 'strap',
                 P.lod >= 1 ? 3 : 2, 0.35, 0.5 + 0.24 * rng());
        continue;
      }
      _lbSet(B, at, a, elev, len, P.shape, P.lod, rng, 0.5 + 0.24 * rng(), 0);
    }
  }
  for (let i = 0; i < P.stems; i++)
    _leafyStalk(B, P, spots[i % spots.length], P.H * (i ? 0.8 + 0.2 * rng() : 1),
                Math.min(P.R * 0.4, P.H * 0.12) * rng(), bloom, rng);
}

// ── an umbrella: shoots that are each one divided leaf ──────────────────────

function _leafyUmbrella(B, P, bloom, rng) {
  const { H, R, L } = P, rot = rng() * 6.283;
  const leaves = Math.max(5, P.stems);
  const r0 = Math.max(0.0012, Math.min(0.004, H * 0.006));
  for (let i = 0; i < leaves; i++) {
    const f = Math.sqrt((i + 0.5) / leaves), a = rot + i * 2.39996;
    const bx = Math.cos(a) * R * 0.62 * f, bz = Math.sin(a) * R * 0.62 * f;
    const h = H * (i ? 0.8 + 0.2 * rng() : 1), lean = 0.06 * H * rng();
    const top = [bx + Math.cos(a) * lean, h, bz + Math.sin(a) * lean];
    const shade = 0.55 + rng() * 0.1;
    _lbTube(B, [[bx, 0, bz], [(bx + top[0]) / 2, h * 0.5, (bz + top[2]) / 2], top], r0, r0 * 0.7, shade);
    const spin = rng() * 6.283, dl = L * 0.5;
    for (let k = 0; k < 3; k++) {
      // A division: level, its tip drooping a little, five leaflets on it.
      const az = spin + k * 2.094 + (rng() - 0.5) * 0.35, len = dl * (0.9 + 0.2 * rng());
      const T = _lbUnit([Math.cos(az), -UMBRELLA_DROOP * (0.6 + 0.8 * rng()), Math.sin(az)]);
      const S = _lbUnit(_lbCross([0, 1, 0], T));
      _lbBlade(B, top, T, S, len, Math.max(0.0014, L * 0.012), 'linear', 1, 0, shade * 0.9);
      for (const [t, sd] of [[0.3, 1], [0.3, -1], [0.62, 1], [0.62, -1], [0.92, 0]]) {
        const ang = sd * 0.95, at = _lbAdd(top, T, len * t);
        const Tl = _lbUnit(_lbMix(T, S, Math.cos(ang), Math.sin(ang)));
        const Sl = _lbUnit(_lbMix(S, T, Math.cos(ang), -Math.sin(ang)));
        _lbBlade(B, at, Tl, Sl, len * 0.56, len * 0.56 * 0.72, 'ovate',
                 P.lod >= 1 ? 2 : 1, 0.25, shade * (0.9 + 0.2 * rng()));
      }
    }
  }
  // The flowers on stalks of their own, under the leaves: three umbels each.
  const scapes = Math.max(1, Math.round(P.stems / 3));
  for (let i = 0; i < scapes; i++) {
    const a = rot + 1.3 + i * 2.39996, f = 0.25 + 0.4 * Math.sqrt((i + 0.5) / scapes);
    const c = [Math.cos(a) * R * f, 0, Math.sin(a) * R * f];
    const h = H * (UMBRELLA_FLOWERS[0] + (UMBRELLA_FLOWERS[1] - UMBRELLA_FLOWERS[0]) * rng());
    const tip = [c[0], h, c[2]];
    _lbTube(B, [c, [c[0], h * 0.5, c[2]], tip], r0 * 0.8, r0 * 0.5, 0.6);
    for (let k = 0; k < 3; k++) {
      const az = k * 2.094 + rng(), ray = Math.max(0.03, L * 0.2);
      const end = [tip[0] + Math.cos(az) * ray, h + ray * 0.6, tip[2] + Math.sin(az) * ray];
      _lbTube(B, [tip, end], 0.0012, 0.001, 0.6);
      _lbTip(B, end, bloom, rng, 0.6);
    }
  }
}

// ── a fern's crown of fronds ────────────────────────────────────────────────

function _leafyFronds(B, P, rng) {
  const { H, L } = P, rot = rng() * 6.283;
  const n = Math.max(5, Math.min(12, P.stems));
  const pairs = P.lod >= 2 ? FROND_PAIRS[1] : FROND_PAIRS[0];
  for (let i = 0; i < n; i++) {
    const a = rot + i * 2.39996 + (rng() - 0.5) * 0.3, ca = Math.cos(a), sa = Math.sin(a);
    const len = L * (0.82 + 0.3 * rng()), rise = FROND_RISE - 0.12 * rng();
    const bend = FROND_BEND * (0.75 + 0.5 * rng()), shade = 0.5 + rng() * 0.14;
    const side = [-sa, 0, ca];
    // The rachis, from a crown a few centimetres across: rising at `rise`
    // radians from level and arching over by `bend` along its length.
    const K = 10, pts = [], dirs = [];
    let at = [ca * 0.03, 0.02, sa * 0.03];
    for (let k = 0; k <= K; k++) {
      const s = k / K, el = rise - bend * s * s;
      const d = [ca * Math.cos(el), Math.sin(el), sa * Math.cos(el)];
      pts.push(at); dirs.push(d);
      at = _lbAdd(at, d, len / K);
    }
    _lbTube(B, pts, Math.max(0.002, len * 0.006), 0.001, shade * 0.85);
    // The pinnae: in pairs, out to the sides in the frond's plane and a little
    // forward, longest above the middle, dwindling to the base (a plume).
    for (let j = 0; j < pairs; j++) {
      const s = 0.1 + 0.88 * j / (pairs - 1), k = Math.min(K - 1, Math.floor(s * K));
      const u = s * K - k, P0 = _lbAdd(pts[k], _lbAdd(pts[k + 1], pts[k], -1), u);
      const d = dirs[k];
      const shape = s < FROND_WIDEST ? 0.12 + 0.88 * Math.pow(s / FROND_WIDEST, 1.6)
        : 1 - 0.75 * Math.pow((s - FROND_WIDEST) / (1 - FROND_WIDEST), 1.3);
      const pl = len * 0.22 * shape;
      for (const sd of [1, -1]) {
        const T = _lbUnit([sd * side[0] + 0.35 * d[0], 0.35 * d[1] - 0.12, sd * side[2] + 0.35 * d[2]]);
        const Sx = _lbUnit(_lbCross(T, [0, 1, 0]));
        _lbBlade(B, P0, T, Sx, pl, pl * 0.4, 'lanceolate', P.lod >= 2 ? 2 : 1, 0.2,
                 shade * (0.92 + 0.12 * rng()));
      }
    }
  }
}

// ── a leaf in threes, and threes again, as painted on a card ────────────────
// A meadow-rue's, a baneberry's, a sweet cicely's leaf is divided in threes and
// in threes again into many small leaflets. Painted as three broad ellipses
// (03d-woody.js's trifoliate) each leafy-shoot card on them was a clover, and
// the readings called them "big flat blob leaflets" (V3.67b). So it is three
// short stalks of three rounded leaflets each, every leaflet three-lobed.
function paintTernate(g, len) {
  const stalk = (l) => { g.beginPath(); g.moveTo(0, 0); g.lineTo(0, -l); g.stroke(); };
  const lobe = (x, y, r) => { g.beginPath(); g.arc(x, y, r, 0, 6.2832); g.fill(); };
  stalk(len * 0.2);
  for (const a of [0, 1.0, -1.0]) {
    g.save(); g.translate(0, -len * 0.2); g.rotate(a); stalk(len * 0.16);
    for (const b of [0, 0.85, -0.85]) {
      g.save(); g.translate(0, -len * 0.16); g.rotate(b);
      const r = len * 0.085;                     // a leaflet of three lobes
      lobe(0, -r * 1.9, r); lobe(-r * 0.85, -r * 1.2, r * 0.85); lobe(r * 0.85, -r * 1.2, r * 0.85);
      g.restore();
    }
    g.restore();
  }
}

// ── a trailing shoot of whorls, as painted on a card ────────────────────────
// A bedstraw's mat is trailing stems with its leaves in stars of six at every
// node, which is what it is known by. Painted in pairs (03d-woody.js, which
// paints at most two leaves a node) it was a faint carpet of clover (V3.67b).
const WHORL_LEAVES = 6;
const _WHORL_SPRAYS = new Map();
function whorlSpray(shape) {
  let sp = _WHORL_SPRAYS.get(shape);
  if (sp) return sp;
  const W = 128, H = 256, wide = 2.3, len = W / wide, cv = document.createElement('canvas');
  cv.width = W; cv.height = H;
  const g = cv.getContext('2d', { willReadFrequently: true });
  g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
  g.fillStyle = g.strokeStyle = '#fff'; g.lineCap = 'round'; g.lineWidth = 2;
  g.beginPath(); g.moveTo(W / 2, H); g.lineTo(W / 2, H * 0.1); g.stroke();
  const nodes = Math.max(2, Math.floor((H * 0.9) / (len * 1.5)));
  for (let j = 0; j < nodes; j++) {
    const y = H - len * (0.9 + 1.5 * j);
    for (let k = 0; k < WHORL_LEAVES; k++) {
      g.save(); g.translate(W / 2, y); g.rotate(k * 6.2832 / WHORL_LEAVES + j * 0.5);
      _wdPaintLeaf(g, shape, len * 0.92);                             // 03d-woody.js
      g.restore();
    }
  }
  const mk = woodyMask('whorl|' + shape, cv);
  sp = Object.assign(mk, { w: wide, h: H / len, leaves: nodes * WHORL_LEAVES, cluster: false,
                           leafCover: mk.cover });
  _WHORL_SPRAYS.set(shape, sp);
  return sp;
}

window.whorlSpray = whorlSpray;
window.paintTernate = paintTernate;
window.leafyForm = {
  umbrella: (B, P, bloom, rng) => _leafyUmbrella(B, P, bloom, rng),
  fronds: (B, P, bloom, rng) => _leafyFronds(B, P, rng),
};
