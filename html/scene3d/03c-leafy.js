// Part of the Site & Pattern 3D viewer. Loaded as an ordered CLASSIC
// script by the bootstrap in scene3d.html — it shares the global scope
// with its siblings (THREE and friends are globals set by the
// bootstrap). Do not add ES `import`/`export` here.
//
// Design principle P5 — see docs/DESIGN_PHILOSOPHY.md
//
// A wildflower drawn from its own numbers (V3.48, F268).
//
// The baked herb figures are seven shapes in three leaf sizes, stretched to a
// plant's height and width. Read against photographs of the region's natives,
// 112 plants had leaves the wrong size, 87 the wrong outline and 44 the wrong
// kind of body. Where somebody has read a plant's leaf and habit numbers
// (src/herb_habit.py writes a `drawn` block with body 'leafy'), this chunk
// builds the plant from them, in metres: the leaf at its length and outline,
// set on the stem as its arrangement says, on as many stems as it carries.
// One body is built for a species and placed for each plant of it.
//
// What nothing records, and is derived here as a stated estimate: how far
// apart the leaves sit (INTERNODE, a multiple of the leaf's length), how many
// leaves a whorl has (WHORL), how many a rosette holds (from its
// circumference), how the leaves are held, and a compound leaf's leaflet
// count. A plant carries more leaves than a budget allows, so the count is
// cut to LEAFY_BUDGET, simplest leaves first, then leaves a stem, then stems.

// The forms (src/herb_habit.py FORMS; tests/test_herb_habit.py holds them equal).
const LEAFY_FORMS = ['stems', 'colony', 'rosette', 'tuft', 'mat'];
// Triangles one plant may spend, by detail level. Stylised draws none of these.
const LEAFY_BUDGET = [0, 1800, 3200];
// Leaf spacing up a stem, as a multiple of the leaf's length.
const INTERNODE = { alternate: 0.22, opposite: 0.75, whorled: 1.0 };
// How far the outermost stem of a clump leans from upright, in radians, by habit.
const SPLAY = { erect: 0.14, clump: 0.3, ferny: 0.26, colony: 0.04 };
const WHORL = 4;
// Where a stem's side branches leave it, as shares of its height. Each ends in
// a flower cluster, as the stem's own tip does, so a stem carries one more
// cluster than it has forks (src/herb_habit.py TIPS_PER_STEM; a test holds
// the two equal).
const FORKS = { branched_above: [0.56, 0.64, 0.72],
                branched_throughout: [0.3, 0.38, 0.46, 0.54, 0.62, 0.7, 0.78] };
// Leaves whose blade stands off on a stalk: longer than the blade at the
// ground (STALK_BASAL), a third of it on a stem (STALK_STEM).
const _LONG_STALKED = { cordate: 1, reniform: 1, orbicular: 1, palmately_lobed: 1,
                        trifoliate: 1, compound_palmate: 1, ternate: 1, sagittate: 1 };
const STALK_BASAL = 1.2, STALK_STEM = 0.3;
// How far out a branch above reaches, as a share of the plant's height and
// never past its outline (V3.67, an estimate read off the asters' photographs).
const BRANCH_OPEN = 0.25;
// A ternate leaf this long is divided twice, and its stalks droop by about this
// much (a share of straight down mixed in), both estimates (V3.65).
const TERNATE_TWICE_M = 0.1, TERNATE_DROOP = 0.15;
const _stalkAtGround = (shape) => (_LONG_STALKED[shape] ? STALK_BASAL : 0);
// Where along its length a simple leaf is widest: the one cross-section a
// leaf drawn as a kite keeps.
const _PEAK_T = { lanceolate: 0.3, linear: 0.5, strap: 0.5, ovate: 0.38,
                  elliptic: 0.5, obovate: 0.66, spatulate: 0.72, orbicular: 0.5,
                  cordate: 0.3, reniform: 0.36, sagittate: 0.2, needle: 0.3,
                  awl: 0.2, scale: 0.3 };

// ── a geometry being written ────────────────────────────────────────────────
function _lbNew() { return { pos: [], col: [], idx: [], tips: [] }; }
const _lbAdd = (a, b, k) => [a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k];
const _lbMix = (a, b, ca, cb) => [a[0] * ca + b[0] * cb, a[1] * ca + b[1] * cb,
                                  a[2] * ca + b[2] * cb];
function _lbUnit(v) {
  const n = Math.hypot(v[0], v[1], v[2]) || 1;
  return [v[0] / n, v[1] / n, v[2] / n];
}
const _lbCross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
                            a[0] * b[1] - a[1] * b[0]];

// A simple leaf's half-width at `t` along it, 0 to 1 of the widest. The lance
// outline here is widest below the middle and narrows to both ends; the herb
// forms' `lance` profile is widest at the base, a triangle.
function _lbProfile(shape, t) {
  if (shape === 'lanceolate') return Math.pow(Math.sin(Math.PI * Math.pow(t, 0.6)), 0.9);
  return _leafWidth(shape, t);                    // 03-herbs.js
}

// One flat blade from `A` along `T`, `S` across it, `L` long and `W` wide,
// bending away from the sky by `droop` radians over its length. `segs` 1 is a
// kite of two triangles: base, widest point, tip.
function _lbBlade(B, A, T, S, L, W, shape, segs, droop, shade) {
  let N = _lbCross(T, S);
  if (N[1] < 0) N = [-N[0], -N[1], -N[2]];
  const base = B.pos.length / 3;
  if (segs <= 1) {                       // base, the two sides at the widest, tip
    const dn = droop * 0.5, tip = _lbAdd(_lbAdd(A, T, L * Math.cos(dn)), N, -L * Math.sin(dn));
    const m = _lbAdd(_lbAdd(A, T, L * (_PEAK_T[shape] || 0.4)), N, -L * Math.sin(dn) * 0.3);
    B.pos.push(A[0], A[1], A[2], m[0] - S[0] * W / 2, m[1] - S[1] * W / 2, m[2] - S[2] * W / 2,
               m[0] + S[0] * W / 2, m[1] + S[1] * W / 2, m[2] + S[2] * W / 2,
               tip[0], tip[1], tip[2]);
    for (let i = 0; i < 12; i++) B.col.push(shade);
    B.idx.push(base, base + 1, base + 2, base + 1, base + 3, base + 2);
    return tip;
  }
  const ts = Array.from({ length: segs + 1 }, (_, i) => i / segs);
  let c = A, t = T, prev = 0;
  for (const tt of ts) {
    const dt = tt - prev;
    if (dt > 0) {
      c = _lbAdd(c, t, L * dt);
      if (droop) {
        const a = droop * dt, cs = Math.cos(a), sn = Math.sin(a);
        const t2 = _lbUnit(_lbMix(t, N, cs, -sn));
        N = _lbUnit(_lbMix(N, t, cs, sn));
        t = t2;
      }
    }
    const w = 0.5 * W * (tt <= 0 ? 0.12 : tt >= 1 ? 0.03 : _lbProfile(shape, tt));
    B.pos.push(c[0] - S[0] * w, c[1] - S[1] * w, c[2] - S[2] * w,
               c[0] + S[0] * w, c[1] + S[1] * w, c[2] + S[2] * w);
    B.col.push(shade, shade, shade, shade, shade, shade);
    prev = tt;
  }
  for (let i = 0; i < ts.length - 1; i++) {
    const a = base + i * 2;
    B.idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2);
  }
  return c;                                        // the tip
}

// One leaf of any outline. `L` is the blade's length; `lod` 0 to 2 is how much
// is spent on it. A divided leaf is its parts, each a blade in the leaf's plane.
function _lbLeaf(B, A, T, S, L, shape, lod, droop, shade) {
  const segs = lod >= 2 ? 4 : (lod === 1 ? 2 : 1);
  const part = (a, at, len, ratio, shp, sg) => {
    const cs = Math.cos(a), sn = Math.sin(a);
    _lbBlade(B, at, _lbMix(T, S, cs, sn), _lbMix(T, S, -sn, cs), len, len * ratio,
             shp, sg || 1, 0, shade);
  };
  const at = (f) => _lbAdd(A, T, L * f);
  const rib = (len) => _lbBlade(B, A, T, S, len, Math.max(0.0016, L * 0.02),
                                'linear', 1, 0, shade * 0.9);
  switch (shape) {
    case 'palmately_lobed': {          // a maple's leaf: lobes fanned from the stalk
      const n = lod ? 5 : 3;
      for (let i = 0; i < n; i++) {
        const a = (i / (n - 1) - 0.5) * 2.3;
        part(a, A, L * (1 - 0.36 * Math.abs(a) / 1.15), 0.5, 'elliptic', lod >= 2 ? 2 : 1);
      }
      return;
    }
    case 'lobed':                      // an oak's: lobes down both sides of a midrib
    case 'pinnatifid': {               // cut nearly to the midrib, the lobes narrow
      const fine = shape === 'pinnatifid';
      _lbBlade(B, A, T, S, L, L * (fine ? 0.12 : 0.3), 'elliptic', Math.min(2, segs),
               droop, shade);
      const pairs = fine ? (lod ? 4 : 3) : (lod ? 3 : 2);
      for (let k = 1; k <= pairs; k++) {
        const f = 0.1 + 0.72 * k / (pairs + 0.5);
        const len = L * (fine ? 0.3 : 0.34) * (1 - 0.4 * f);
        part(0.95, at(f), len, fine ? 0.3 : 0.55, 'elliptic');
        part(-0.95, at(f), len, fine ? 0.3 : 0.55, 'elliptic');
      }
      return;
    }
    case 'compound_pinnate': {         // leaflets in pairs along a stalk, one at the end
      const pairs = lod ? 4 : 3;
      const len = L * Math.min(0.36, 1.5 / (2 * pairs + 1));
      rib(L * 0.9);
      for (let k = 0; k < pairs; k++) {
        const f = 0.14 + 0.66 * k / Math.max(1, pairs - 1);
        part(1.05, at(f), len, 0.45, 'elliptic');
        part(-1.05, at(f), len, 0.45, 'elliptic');
      }
      part(0, at(0.86), len * 1.1, 0.45, 'elliptic');
      return;
    }
    case 'trifoliate':                 // three leaflets from one point
      for (const a of [0, 1.05, -1.05]) part(a, A, L * 0.62, 0.62, 'obovate', lod >= 2 ? 2 : 1);
      return;
    case 'compound_palmate': {         // a lupine's: narrow leaflets in a fan
      const n = lod ? 7 : 5;
      for (let i = 0; i < n; i++)
        part((i / (n - 1) - 0.5) * 2.7, A, L * 0.6, 0.24, 'elliptic');
      return;
    }
    case 'bipinnate': {                // a yarrow's: divided, and divided again
      const pairs = lod ? 6 : 5;
      rib(L * 0.92);
      for (let k = 0; k <= pairs; k++) {
        const f = 0.1 + 0.8 * k / pairs, len = L * 0.24 * (1 - 0.6 * Math.abs(f - 0.35));
        for (const a of (k === pairs ? [0] : [1.0, -1.0])) {
          part(a, at(f), len, 0.42, 'lanceolate');
          if (lod >= 2) {              // the second division
            const cs = Math.cos(a), sn = Math.sin(a);
            const mid = _lbAdd(at(f), _lbMix(T, S, cs, sn), len * 0.45);
            part(a + 0.8, mid, len * 0.45, 0.35, 'lanceolate');
            part(a - 0.8, mid, len * 0.45, 0.35, 'lanceolate');
          }
        }
      }
      return;
    }
    case 'ternate': {                  // a columbine's: three stalks of three leaflets
      // A big one (a meadow-rue's, a baneberry's, a sarsaparilla's, from
      // TERNATE_TWICE_M) divides in threes and in threes again, each stalk
      // drooping, so the leaf is a dome of small leaflets and not one flat
      // plate of nine (V3.65). How far each stalk droops is an estimate.
      // No two stalks droop alike and no two leaflets face the same way: all
      // level, a big leaf was a disc seen edge on.
      const big = L >= TERNATE_TWICE_M, twice = lod && big;
      let k = Math.abs(A[0] * 7919 + A[1] * 104729 + A[2] * 1299709) % 1000;
      const rnd = () => ((k = (k * 9301 + 49297) % 233280) / 233280);
      const tern = (A0, D, Sd, len, again) => {
        for (const a of [0, 0.95, -0.95]) {
          const cs = Math.cos(a), sn = Math.sin(a);
          const fall = big ? TERNATE_DROOP * (0.3 + 1.4 * rnd()) : 0;
          const d = _lbUnit(_lbAdd(_lbMix(D, Sd, cs, sn), [0, -1, 0], fall));
          const sd = _lbUnit(_lbMix(Sd, D, cs, -sn));
          const end = _lbAdd(A0, d, len * 0.42);
          _lbBlade(B, A0, d, sd, len * 0.42, Math.max(0.0014, L * 0.016), 'linear', 1, 0, shade * 0.9);
          if (again) { tern(end, d, sd, len * 0.5, false); continue; }
          if (!lod) { part2(d, sd, 0, end, len * 0.42, 0.8); continue; }
          for (const b of [0, 0.9, -0.9]) part2(d, sd, b, end, len * 0.36, 0.75);
        }
      };
      const part2 = (D, Sd, b, at0, len, ratio) => {
        const cs = Math.cos(b), sn = Math.sin(b), Tl = _lbMix(D, Sd, cs, sn);
        let Sl = _lbMix(D, Sd, -sn, cs);
        if (big) {                     // rolled about its own midrib
          const r = (rnd() - 0.5) * 1.6, up = _lbUnit(_lbCross(Tl, Sl));
          Sl = _lbUnit(_lbMix(Sl, up, Math.cos(r), Math.sin(r)));
        }
        _lbBlade(B, at0, Tl, Sl, len, len * ratio, 'obovate', 1, 0, shade * (big ? 0.88 + 0.24 * rnd() : 1));
      };
      tern(A, T, S, L, twice);
      return;
    }
    default:
      _lbBlade(B, A, T, S, L, leafWidthFor(shape, L), shape, segs, droop, shade);
  }
}

// What one leaf of `shape` costs at `lod`, in triangles: counted off a leaf
// actually built, so the budget cannot drift from the builder.
const _LEAF_COST = new Map();
function leafyLeafCost(shape, lod, L) {
  const big = shape === 'ternate' && (L == null || L >= TERNATE_TWICE_M);   // divided twice
  const key = shape + '|' + lod + (big ? '|big' : '');
  let c = _LEAF_COST.get(key);
  if (c == null) {
    const B = _lbNew();
    _lbLeaf(B, [0, 0, 0], [0, 1, 0], [1, 0, 0], big ? 1 : 0.05, shape, lod, 0, 1);
    c = B.idx.length / 3;
    _LEAF_COST.set(key, c);
  }
  return c;
}

// A stem through `pts`, three-sided, `r0` thick at its foot and `r1` at its tip.
function _lbTube(B, pts, r0, r1, shade) {
  const base = B.pos.length / 3, n = pts.length;
  for (let i = 0; i < n; i++) {
    const d = _lbUnit(_lbAdd(pts[Math.min(n - 1, i + 1)], pts[Math.max(0, i - 1)], -1));
    const u = _lbUnit(_lbCross(d, Math.abs(d[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0]));
    const v = _lbCross(d, u), r = r0 + (r1 - r0) * i / Math.max(1, n - 1);
    for (let k = 0; k < 3; k++) {
      const a = k * 2.0944, cs = Math.cos(a) * r, sn = Math.sin(a) * r;
      B.pos.push(pts[i][0] + u[0] * cs + v[0] * sn, pts[i][1] + u[1] * cs + v[1] * sn,
                 pts[i][2] + u[2] * cs + v[2] * sn);
      B.col.push(shade, shade, shade);
    }
  }
  for (let i = 0; i < n - 1; i++) {
    for (let k = 0; k < 3; k++) {
      const a = base + i * 3 + k, b = base + i * 3 + (k + 1) % 3;
      B.idx.push(a, b, a + 3, b, b + 3, a + 3);
    }
  }
}

// A leaf set on a stem or at the ground: out at bearing `az`, rising `elev`
// radians from level, on a stalk where its outline has one.
function _lbSet(B, at, az, elev, L, shape, lod, rng, shade, stalk) {
  const hx = Math.cos(az), hz = Math.sin(az);
  let T = [hx * Math.cos(elev), Math.sin(elev), hz * Math.cos(elev)];
  const roll = (rng() - 0.5) * 0.5;
  let S = _lbUnit(_lbMix([-hz, 0, hx], _lbCross(T, [-hz, 0, hx]), Math.cos(roll), Math.sin(roll)));
  let A = at;
  const st = (stalk == null ? _stalkAtGround(shape) : stalk) * L;
  if (st > 0.004) {
    A = _lbBlade(B, at, T, S, st, Math.max(0.0014, L * 0.018), 'linear', 1, 0, shade * 0.88);
    // The blade is held flatter than the stalk that carries it.
    const e2 = elev * 0.35;
    T = [hx * Math.cos(e2), Math.sin(e2), hz * Math.cos(e2)];
    S = _lbUnit(_lbCross(_lbCross(T, [-hz, 0, hx]), T));
  }
  const slim = (LEAF_WIDTH_RATIO[shape] || 0.4) < 0.3;
  _lbLeaf(B, A, T, S, L * (0.85 + rng() * 0.3), shape, lod, slim ? 0.55 : 0.3,
          shade * (0.92 + rng() * 0.14));
}

// ── what the flowers need of the stem ───────────────────────────────────────
// `top`: how much of a stem's top, in metres, its flower cluster takes (no
// leaves there). `rays`: the width of a flat cluster's fan of stalks, or 0.
function _leafyBloom(p, H) {
  if (!p || !p.bloom_start) return { top: H * 0.04, rays: 0 };
  if (typeof floretsApply !== 'function' || !floretsApply(p)) return { top: H * 0.1, rays: 0 };
  const arch = FLORET_ARCHITECTURES.indexOf(p.flower_arch) >= 0 ? p.flower_arch : 'cyme';
  const reach = _inflorescence(p, arch, _drawnFlorets(p.florets_per_head), H).reach;
  if (arch === 'head' || arch === 'solitary') return { top: reach * 0.6 + 0.01, rays: 0 };
  if (arch === 'corymb' || arch === 'umbel' || arch === 'cyme')
    return { top: reach * 0.5 + 0.01, rays: reach > 0.03 ? reach : 0 };
  return { top: reach * 1.1 + 0.01, rays: 0 };
}

// A stem's top: its tip noted for the flowers, and under a flat cluster the
// fan of stalks that carries it.
function _lbTip(B, tip, bloom, rng, shade) {
  B.tips.push(tip);
  if (!bloom.rays) return;
  const node = [tip[0], tip[1] - bloom.rays * 0.5, tip[2]];
  for (let i = 0; i < 5; i++) {
    const a = i * 1.2566 + rng() * 0.6, r = bloom.rays * 0.36;
    const end = [tip[0] + Math.cos(a) * r, tip[1] - bloom.rays * 0.04, tip[2] + Math.sin(a) * r];
    const T = _lbUnit(_lbAdd(end, node, -1));
    _lbBlade(B, node, T, _lbUnit(_lbCross(T, [0, 1, 0])), Math.hypot(r, bloom.rays * 0.46),
             0.0022, 'linear', 1, 0, shade);
  }
}

// ── the plan: what the budget buys ──────────────────────────────────────────
function _leafyPlan(d, bloom, budget) {
  const H = Math.max(0.03, d.mature_h), R = Math.max(0.03, d.mature_w / 2);
  const L = Math.max(0.004, d.leaf_m), shape = d.leaf_shape;
  const W = _LONG_STALKED[shape] || isCompoundShape(shape) || shape === 'ternate'
    || shape === 'palmately_lobed' ? L * 0.9 : leafWidthFor(shape, L);
  const perNode = d.arrangement === 'opposite' ? 2 : (d.arrangement === 'whorled' ? WHORL : 1);
  const gap = L * (INTERNODE[d.arrangement] || INTERNODE.alternate);
  const P = { H, R, L, W, shape, perNode, form: d.form, stems: Math.max(1, d.stems), budget,
              nodes: 0, basal: 0, groups: 1, lod: 2, branching: d.branching,
              habit: d.habit, forkLeaves: 2 };
  const leafy = d.form === 'stems' || d.form === 'colony';
  if (leafy) {
    // The recorded count where somebody counted; else the spacing estimate.
    P.nodes = d.nodes > 0 ? Math.min(80, d.nodes)
      : Math.max(2, Math.min(40, Math.round((H * 0.9 - Math.min(bloom.top, H * 0.35)) / gap)));
    if (d.basal) P.basal = Math.max(5, Math.min(14, Math.round(Math.PI * L / (W * 0.6))));
  } else if (d.form === 'mat' && !d.basal) {
    // Sprigs a few leaves long, as many as cover the ground.
    P.sprig = Math.min(R * 0.6, Math.max(0.04, L * 3));
    P.nodes = Math.max(2, Math.min(12, Math.round(P.sprig / gap)));
    P.shoots = Math.max(8, Math.min(70, Math.round(1.6 * R * R / (P.sprig * P.sprig * 0.5))));
  } else {
    // Rosettes and tufts: as many as fill the ground the plant covers, each
    // with the leaves that go round it.
    // A crown carries a stalk or two, and no more crowns than the ground holds.
    const rr = d.form === 'tuft' ? L * 0.55 : L * (0.9 + _stalkAtGround(shape));
    const fit = Math.max(1, Math.round(0.75 * (R / rr) * (R / rr)));
    P.groups = d.form === 'mat' ? Math.min(40, fit)
      : Math.max(1, Math.min(7, fit, Math.ceil(P.stems / 2)));
    P.basal = d.form === 'tuft' ? Math.max(8, Math.min(26, Math.round(10 + 40 * rr)))
      : Math.max(5, Math.min(24, Math.round(Math.PI * rr / (W * 0.5))));
    P.rr = rr;
  }
  const stemTris = (leafy ? 12 : 12) + (bloom.rays ? 10 : 0);
  const tips = leafy ? (FORKS[P.branching] || []).length + 1 : 1;
  const cost = () => {
    const leaf = leafyLeafCost(shape, P.lod, L) + (_LONG_STALKED[shape] ? 2 : 0);
    let n = P.stems * (stemTris * (1 + (tips - 1) * 0.6) + (tips - 1) * P.forkLeaves * leaf);
    if (leafy) n += P.stems * P.nodes * perNode * leaf
      + (d.form === 'colony' ? 2 * P.stems : 1) * (P.basal ? 1 : 0) * Math.max(1, d.form === 'colony' ? 1 : P.basal) * leaf;
    else if (P.shoots) n += P.shoots * 2;                 // leaves as cards (_leafyMat)
    else n += (d.form === 'mat' ? 36 : 0) + P.groups * P.basal * leaf;
    return n;
  };
  // Cut to the budget: plainer leaves, then fewer of them, then fewer stems.
  for (let guard = 0; guard < 60 && cost() > budget; guard++) {
    if (P.lod > 0) P.lod--;
    else if (leafy && P.nodes > 4) P.nodes = Math.max(4, Math.floor(P.nodes * 0.85));
    else if (leafy && tips > 1 && P.forkLeaves > 1) P.forkLeaves = 1;
    else if (P.shoots && P.nodes > 3) P.nodes--;
    else if (P.shoots && P.shoots > 10) P.shoots = Math.max(10, Math.floor(P.shoots * 0.85));
    else if (!leafy && !P.shoots && P.basal > 5) P.basal = Math.max(5, Math.floor(P.basal * 0.85));
    else if (!leafy && !P.shoots && P.groups > 3) P.groups = Math.max(3, Math.floor(P.groups * 0.85));
    else if (P.stems > 5) P.stems = Math.max(5, Math.floor(P.stems * 0.85));
    // A leaf of many parts on a plant of many stems: fewer still, before fewer stems.
    else if (leafy && P.nodes > 2) P.nodes--;
    else if (leafy && tips > 1 && P.forkLeaves > 0) P.forkLeaves = 0;
    else if (P.stems > 3) P.stems--;
    else break;
  }
  return P;
}

// ── the forms ───────────────────────────────────────────────────────────────

// Leafy stems, from one crown (`stems`) or spread over the ground (`colony`).
function _leafyStems(B, P, bloom, rng) {
  const { H, R, L } = P, colony = P.form === 'colony';
  // The crown the stems rise from: a few centimetres, wider with more stems.
  const crown = colony ? R * 0.82 : Math.min(R * 0.5, 0.005 + 0.014 * Math.sqrt(P.stems));
  const splay = SPLAY[colony ? 'colony' : P.habit] || SPLAY.erect;
  const rot = rng() * 6.283;
  const rStem = Math.max(0.0008, Math.min(0.0045, H * 0.0022));
  for (let i = 0; i < P.stems; i++) {
    const fr = Math.sqrt((i + 0.5) / P.stems), a = i * 2.39996 + rot;
    const hi = H * (i === 0 ? 1 : 1 - 0.24 * fr * (0.4 + 0.6 * rng()));
    const bx = Math.cos(a) * crown * fr, bz = Math.sin(a) * crown * fr;
    const lean = crown * fr + Math.tan(splay * fr * (0.7 + 0.6 * rng())) * hi;
    const tx = Math.cos(a) * lean, tz = Math.sin(a) * lean;
    const top = hi - (bloom.rays ? bloom.rays * 0.5 : 0);
    const at = (t) => [bx + (tx - bx) * Math.pow(t, 1.5), top * t, bz + (tz - bz) * Math.pow(t, 1.5)];
    const shade = 0.56 + rng() * 0.1;
    _lbTube(B, [at(0), at(0.5), at(1)], rStem, rStem * 0.55, shade);
    _lbTip(B, [tx, hi, tz], bloom, rng, shade);
    if (P.basal && colony)
      for (let k = 0; k < 2; k++)
        _lbSet(B, [bx, 0.004, bz], a + 2 + k * 2.6 + rng(), 0.9, L, P.shape, P.lod, rng, 0.52);
    // Leaves from just above the ground to under the flowers; a big leaf
    // from higher, or it lies on the ground (V3.65, an estimate).
    const y0 = Math.max(P.basal ? 0.14 : 0.07, Math.min(0.4, 0.6 * L / hi)) * hi;
    const y1 = Math.max(y0 + 0.01, hi - Math.min(bloom.top, hi * 0.35) - 0.005);
    if (window.noteStemPath) noteStemPath(P, at, top, y0, y1, hi, a);   // 03g-stemleaves.js
    const whorlAt = P.perNode >= WHORL && colony;      // one whorl, at the top
    const nodes = whorlAt ? 1 : P.nodes;
    for (let j = 0; j < nodes; j++) {
      const f = whorlAt ? 1 : (nodes === 1 ? 0.5 : j / (nodes - 1));
      const p0 = at((y0 + (y1 - y0) * f) / top);
      const size = whorlAt ? L
        : L * (P.basal ? 0.8 - 0.3 * f : 0.72 + 0.28 * Math.sin(Math.PI * Math.min(1, 0.15 + f)));
      const az0 = a + (P.perNode > 1 ? j * (Math.PI / P.perNode) : j * 2.39996);
      for (let k = 0; k < P.perNode; k++)
        _lbSet(B, p0, az0 + k * 6.2832 / P.perNode,
               (whorlAt ? 0.15 + rng() * 0.15 : 0.25 + 0.5 * f + (rng() - 0.5) * 0.25)
                 + (L >= TERNATE_TWICE_M && P.shape === 'ternate' ? 0.3 : 0),   // held up, not a skirt
               size, P.shape, P.lod, rng, 0.46 + 0.28 * f, _LONG_STALKED[P.shape] ? STALK_STEM : 0);
    }
    // Side branches, each to a tip of its own.
    (FORKS[P.branching] || []).forEach((f0, n) => {
      const p0 = at(f0), ba = a + n * 2.39996 + rng();
      // A plant branched above opens into a wide top to its outline, which is
      // where its flowers are (V3.67): at 0.12 of its height the top was no
      // wider than the stems and an aster read as a column.
      const out = P.branching === 'branched_above'
        ? Math.max(hi * 0.12, Math.min(hi * BRANCH_OPEN, R * 0.85))
        : hi * 0.22 * (1 - 0.6 * f0);
      const tipY = hi * (f0 + (1 - f0) * (0.72 + 0.2 * rng()));
      const end = [p0[0] + Math.cos(ba) * out, tipY - (bloom.rays ? bloom.rays * 0.5 : 0),
                   p0[2] + Math.sin(ba) * out];
      const mid = [(p0[0] + end[0]) / 2 + Math.cos(ba) * out * 0.2, (p0[1] + end[1]) / 2,
                   (p0[2] + end[2]) / 2 + Math.sin(ba) * out * 0.2];
      _lbTube(B, [p0, mid, end], rStem * 0.5, rStem * 0.3, shade);
      _lbTip(B, [end[0], tipY, end[2]], bloom, rng, shade);
      if (window.noteBranchPath) noteBranchPath(P, p0, end, ba);    // 03g-stemleaves.js
      for (let k = 0; k < P.forkLeaves; k++)
        _lbSet(B, k ? mid : _lbMix(p0, mid, 0.5, 0.5), ba + k * 2.4, 0.55, L * 0.5,
               P.shape, P.lod, rng, 0.8, 0);
    });
  }
  if (P.basal && !colony) _leafyRosette(B, P, [0, 0, 0], P.basal, L * 1.2, crown + 0.005, rng);
}

// Leaves round one point at the ground: the outer ones low, the inner rising.
function _leafyRosette(B, P, c, n, L, r0, rng) {
  const rot = rng() * 6.283;
  for (let i = 0; i < n; i++) {
    const a = i * 2.39996 + rot, inner = i / Math.max(1, n - 1);
    const at = [c[0] + Math.cos(a) * r0 * 0.5, c[1] + 0.004, c[2] + Math.sin(a) * r0 * 0.5];
    const stalk = _stalkAtGround(P.shape) * (1 - 0.6 * inner) * (0.8 + 0.4 * rng());
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
function _leafyTufts(B, P, bloom, rng) {
  const spots = _leafySpots(P.groups, P.R, P.rr, rng);
  for (const c of spots) {
    const rot = rng() * 6.283;
    for (let i = 0; i < P.basal; i++) {
      const a = i * 2.39996 + rot, out = Math.sqrt((i + 0.5) / P.basal);
      const at = [c[0] + Math.cos(a) * 0.012 * out, 0.003, c[2] + Math.sin(a) * 0.012 * out];
      _lbSet(B, at, a, 1.45 - 0.7 * out + (rng() - 0.5) * 0.2, P.L * (0.7 + 0.3 * rng()),
             P.shape, P.lod, rng, 0.5 + 0.24 * rng(), 0);
    }
  }
  for (let i = 0; i < P.stems; i++)
    _leafyStalk(B, P, spots[i % spots.length], P.H * (i ? 0.8 + 0.2 * rng() : 1),
                Math.min(P.R * 0.4, P.H * 0.12) * rng(), bloom, rng);
}

// A mat of leafy shoots (V3.65). Until V3.65 a solid mound stood in for the
// leaves no budget could draw one by one, and every mat read as a green plate
// with sprigs round its edge (bog cranberry, bearberry, twinflower, bedstraw,
// brooklime, field chickweed). Now its leaves are cut-out cards of its own
// leafy shoots (03d-woody.js _wdSpray), as a shrub's are, lying nearly flat
// over the ground along trailing runners and heaped a little over the root,
// with the ground showing where a mat is thin. `C` takes the cards.
// What nothing records, and is a stated estimate: how much of its ground a
// mat covers (MAT_COVER, overlaps counted), how far larger than life its
// shoots may be drawn to cover it on the budget (MAT_GAIN_MAX), and how deep
// it lies.
const MAT_COVER = 1.1;
const MAT_GAIN_MAX = 2.5;
function _leafyMat(B, P, bloom, rng, C) {
  const { R, L, H } = P, rot = rng() * 6.283, ends = [];
  // As deep as a few leaves are long, and never more than 40% of its height,
  // which is mostly its flower stalks (also an estimate).
  const thick = Math.max(0.008, Math.min(H * 0.4, L * 3, 0.06));
  const lift = (f) => 0.0015 + thick * Math.max(0, 1 - f * f) * 0.8;   // the outer runners on the ground
  // The runners: thin stems from the root outward, lying on the mat.
  for (let i = 0; i < P.shoots; i++) {
    const f = Math.sqrt((i + 0.5) / P.shoots), a0 = rot + i * 2.39996;
    const sx = Math.cos(a0) * R * 0.85 * f, sz = Math.sin(a0) * R * 0.85 * f;
    const a = a0 + (rng() - 0.5) * 1.2, len = P.sprig * (0.7 + 0.6 * rng());
    const at = (t) => [sx + Math.cos(a) * len * t, lift(f) + thick * 0.2 * t, sz + Math.sin(a) * len * t];
    const T = _lbUnit(_lbAdd(at(1), at(0), -1));
    _lbBlade(B, at(0), T, _lbUnit(_lbCross(T, [0, 1, 0])), len, 0.0025, 'linear', 1, 0, 0.42);
    ends.push(at(1));
  }
  for (let i = 0; i < P.stems; i++) {
    const e = ends[(i * 7) % ends.length];
    _leafyStalk(B, P, [e[0], e[1], e[2]], (H - e[1]) * (i ? 0.8 + 0.2 * rng() : 1), 0.01, bloom, rng);
  }
  // The leafy shoots: as many as cover the mat, on what the budget leaves.
  const sp = _wdSpray(P.shape, P.perNode);                            // 03d-woody.js
  const card = sp.w * sp.h * L * L * (sp.leafCover || sp.cover);
  let n = Math.ceil(MAT_COVER * Math.PI * R * R / Math.max(1e-6, card));
  const room = Math.max(60, Math.floor((P.budget - B.idx.length / 3) / 2));
  const gain = n > room ? Math.min(MAT_GAIN_MAX, Math.sqrt(n / room)) : 1;
  n = Math.min(room, Math.ceil(n / (gain * gain)));
  const w = sp.w * L * gain, h = sp.h * L * gain;
  for (let i = 0; i < n; i++) {
    const f = Math.sqrt((i + 0.5) / n), a0 = rot + i * 2.39996 + (rng() - 0.5) * 0.3;
    const r = Math.max(0, R - h * 0.6) * f;
    const at = [Math.cos(a0) * r, lift(f) + rng() * thick * 0.3, Math.sin(a0) * r];
    // Outward along a runner, a little up, a little either way.
    const a = a0 + (rng() - 0.5) * 1.6, up = 0.12 + 0.3 * rng() * (1 - f);
    const T = _lbUnit([Math.cos(a), up, Math.sin(a)]);
    const S = _lbUnit(_lbCross([0, 1, 0], T)), k = 0.85 + 0.3 * rng();
    _wdCard(C, _lbAdd(at, T, -h * 0.25 * k), T, S, w * k, h * k, 0.6 + 0.32 * rng());
  }
  C.cut = sp;
  C.gain = gain;
}

// ── the body ────────────────────────────────────────────────────────────────

// What makes two plants' bodies the same geometry: the species' own numbers
// (not this plant's place, height or width) and how its flowers are carried.
function leafyKeyFor(p) {
  const d = p && p.drawn;
  if (STYLISED || !d || d.body !== 'leafy' || LEAFY_FORMS.indexOf(d.form) < 0) return null;
  const b = _leafyBloom(p, d.mature_h);
  return ['leafy', d.form, d.mature_h, d.mature_w, d.stems, d.leaf_m, d.leaf_shape,
          d.arrangement, d.branching, d.habit, d.nodes || 0, d.basal ? 1 : 0, b.top.toFixed(3),
          b.rays.toFixed(3)].join('|');
}

// The body for the plants sharing `key`, in the unit frame every herb is placed
// in (base at 0, height 1, `unitHalfWidth` wide), `v` one of its random builds.
function buildLeafyGeo(p, v) {
  const d = p.drawn, bloom = _leafyBloom(p, d.mature_h);
  const P = _leafyPlan(d, bloom, LEAFY_BUDGET[Math.max(1, Math.min(2, QUALITY))]);
  const rng = mulberry32(hashPid((p.genus || '') + (p.species || '') + d.form) + 131 * v);
  const B = _lbNew(), C = Object.assign(_lbNew(), { uv: [] });
  if (P.form === 'stems' || P.form === 'colony') {
    _leafyStems(B, P, bloom, rng);
    if (window.leafyStemCards) leafyStemCards(C, P, rng);           // V3.66
  }
  else if (P.form === 'tuft') _leafyTufts(B, P, bloom, rng);
  else if (P.form === 'mat' && P.shoots) _leafyMat(B, P, bloom, rng, C);
  else _leafyRosettes(B, P, bloom, rng);
  // Into the unit frame, keeping the proportions it was built at.
  let top = 0, half = 0;
  for (let i = 0; i < B.pos.length; i += 3) {
    top = Math.max(top, B.pos[i + 1]);
    half = Math.max(half, Math.abs(B.pos[i]), Math.abs(B.pos[i + 2]));
  }
  for (const t of B.tips) top = Math.max(top, t[1]);
  for (let i = 0; i < C.pos.length; i += 3) {
    top = Math.max(top, C.pos[i + 1]);
    half = Math.max(half, Math.abs(C.pos[i]), Math.abs(C.pos[i + 2]));
  }
  const s = 1 / Math.max(1e-3, top);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(B.pos.map(x => x * s), 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(B.col, 3));
  g.setIndex(B.idx);
  g.computeVertexNormals();
  // The frame is as wide as the plant is recorded to spread, whatever the body
  // fills of it, so a plant is placed at one scale up and across: three erect
  // stems are not pulled out to the ground they were spaced for.
  g.userData.unitHalfWidth = Math.max(1e-3, d.mature_w / 2 / Math.max(1e-3, d.mature_h));
  g.userData.bodyHalfWidth = half * s;
  // Where the flowers go: the stem tips, tallest first (15b-anchors.js).
  g.userData.tips = B.tips.map(t => ({ x: t[0] * s, y: t[1] * s, z: t[2] * s }))
    .sort((a, b) => b.y - a.y);
  g.userData.leafy = { triangles: (B.idx.length + C.idx.length) / 3, plan: P,
                       cards: C.idx.length / 6, gain: C.gain || 1 };
  // A mat's leafy shoots: one more mesh in the same frame, cut to its leaves.
  if (C.idx.length) {
    const cg = new THREE.BufferGeometry();
    cg.setAttribute('position', new THREE.Float32BufferAttribute(C.pos.map(x => x * s), 3));
    cg.setAttribute('color', new THREE.Float32BufferAttribute(C.col, 3));
    cg.setAttribute('uv', new THREE.Float32BufferAttribute(C.uv, 2));
    cg.setIndex(C.idx);
    cg.computeVertexNormals();
    g.userData.cards = cg;
    g.userData.cut = C.cut;
  }
  return g;
}

// The instanced mesh of a mat's leafy shoots for `total` plants of `arch`, or
// null (04-quality.js buildHerbLayer places it as it places the body).
function leafyCardsMesh(arch, total, surf) {
  const cg = arch.userData && arch.userData.cards;
  if (!cg) return null;
  const cut = arch.userData.cut;
  const mesh = instancedMesh(cg, total, surfaceMaterial(MAT_PRESETS.herbLeaf, surf, true, cut));
  mesh.customDepthMaterial = cut.depth;
  mesh.userData.part = 'mat_cards';
  return mesh;
}

window.leafyKeyFor = leafyKeyFor;
window.leafyCardsMesh = leafyCardsMesh;
window.buildLeafyGeo = buildLeafyGeo;
