// Part of the Prairie Crocus 3D viewer. Loaded as an ordered CLASSIC
// script by the bootstrap in scene3d.html — it shares the global scope
// with its siblings (THREE and friends are globals set by the
// bootstrap). Do not add ES `import`/`export` here.
//
// Design principle P5 — see docs/DESIGN_PHILOSOPHY.md
//
// Water plants by their own parts (V3.67b, F268).
//
// Read against their photographs, seven of the twelve water plants scored 4 or
// less: 23-pond.js gave every submerged plant the same dozen slivers on the
// water, every broad-leaved emergent the same stalked blades, and none of them
// anywhere for its flowers to stand, so a milfoil's red spikes and a
// bladderwort's yellow flowers were drawn under the opaque water and a
// buckbean's raceme was white stars at random heights. This draws, from what
// is recorded of each:
//
//   submerged, its leaves finely divided (pinnatifid, bipinnate): shoot tips
//     lying on the water in whorls of thread-fine leaves, a bottlebrush each
//     (water-milfoil, bladderwort);
//   submerged, its leaves long threads (linear, 5 cm and more): streaming
//     mats of them on the surface (sago pondweed);
//   and either way its flowering stalks, standing out of the water to the
//     drawn height, the flowers on their tips (15b-anchors.js asks here);
//   floating, its fronds narrow: chains of fronds joined at right angles just
//     under the surface (ivy-leaved duckweed), not a common duckweed's pads;
//   broad-leaved, its leaf three leaflets: each leaf three oval leaflets on its
//     stalk, and leafless scapes over them for the raceme (buckbean);
//   broad-leaved, its flowers a panicle: the leaves a rosette at half the
//     plant's height, and a scape to its top with whorls of branches, the
//     flowers clustered at their ends (water-plantain);
//   broad-leaved, its flower a spike of one bract (a spathe): heart leaves on
//     stalks, and the spathe drawn here, a white blade cupped round a
//     yellow-green club (water arum).
// The arrowheads keep 23-pond.js's blades, and the pond-lily and floating
// marsh-marigold their pads.
//
// What nothing records, and is a stated estimate here: how many shoot tips
// reach the surface (POND_TIPS per square metre), how long a streaming thread
// is (POND_THREAD_M), how far a duckweed chain runs (POND_CHAIN), how tall a
// leaf stands against the plant (POND_LEAF_SHARE), and a spathe's size against
// the recorded flower width.

const POND_TIPS = 150, POND_TIPS_MAX = 34;
const POND_THREAD_M = [0.08, 0.2];
const POND_CHAIN = 4;
const POND_LEAF_SHARE = { panicle: [0.38, 0.55], raceme: [0.55, 0.85] };

let POND_ANCHORS = new Map();
function pondFormsReset() { POND_ANCHORS = new Map(); }
function pondAnchorsFor(p) {
  const a = POND_ANCHORS.get(p);
  return a && a.length ? a : null;
}

// Which of these builders draws `p`, or '' for 23-pond.js's own.
function pondFormOf(p) {
  const d = p.drawn || {};
  const shape = p.leaf_shape || '';
  if (d.body === 'submerged') {
    if (shape === 'pinnatifid' || shape === 'bipinnate') return 'feathery';
    if (shape === 'linear' && (p.leaf_size_cm || 0) >= 5) return 'threads';
    return '';
  }
  if (d.body === 'floating') return shape === 'lanceolate' || shape === 'elliptic' ? 'chains' : '';
  if (d.body === 'broadleaf') {
    if (pondOwnsFlower(p)) return 'spathe';
    if (shape === 'trifoliate') return 'trifoliate';
    if (p.flower_arch === 'umbel' || p.flower_arch === 'panicle') return 'panicle';
  }
  return '';
}

// A spike of one bract is a spadix in its spathe (a calla's): drawn here, so
// the flower layer leaves it (05-flowers.js).
function pondOwnsFlower(p) {
  return !!(p && p.drawn && p.drawn.body === 'broadleaf' && p.flower_arch === 'spike'
            && p.petal_count === 1);
}

const _pd = (B, at, T, S, L, W, shape, segs, droop, shade) =>
  _lbBlade(B, at, _lbUnit(T), _lbUnit(S), L, W, shape, segs, droop, shade);     // 03c-leafy.js

// ── submerged: what reaches the surface ─────────────────────────────────────

function _pondFeathery(B, p, c, y, R, rng) {
  const n = Math.max(6, Math.min(POND_TIPS_MAX, Math.round(POND_TIPS * R * R)));
  const leaf = Math.max(0.012, Math.min(0.03, (p.leaf_size_cm || 2) / 100));
  for (let i = 0; i < n; i++) {
    const a = rng() * 6.283, r = R * Math.sqrt(rng()), az = rng() * 6.283;
    const len = 0.06 + 0.07 * rng(), T = [Math.cos(az), 0.08, Math.sin(az)];
    const at = [c[0] + Math.cos(a) * r, y, c[2] + Math.sin(a) * r];
    _lbTube(B, [at, _lbAdd(at, _lbUnit(T), len)], 0.0018, 0.0012, 0.5);
    // Whorls of thread-fine leaves along it, shorter toward its tip.
    for (let w = 0, k = Math.round(len / 0.011); w < k; w++) {
      const f = (w + 0.5) / k, o = _lbAdd(at, _lbUnit(T), len * f), l = leaf * (1.1 - 0.6 * f);
      for (let j = 0; j < 5; j++) {
        const b = az + j * 1.2566 + w * 0.6, d = [Math.cos(b), 0.15 + 0.2 * rng(), Math.sin(b)];
        _pd(B, o, d, [-Math.sin(b), 0, Math.cos(b)], l, 0.0016, 'linear', 1, 0, 0.55 + 0.25 * rng());
      }
    }
  }
}

function _pondThreads(B, p, c, y, R, rng) {
  const bundles = Math.max(14, Math.min(40, Math.round(220 * R * R)));
  const drift = rng() * 6.283;                       // the way the water moves them
  for (let i = 0; i < bundles; i++) {
    const a = rng() * 6.283, r = R * 0.7 * Math.sqrt(rng());
    const o = [c[0] + Math.cos(a) * r, y, c[2] + Math.sin(a) * r];
    const dir = drift + (rng() - 0.5) * 1.1;
    for (let j = 0; j < 14; j++) {
      const b = dir + (rng() - 0.5) * 0.5;
      const L = POND_THREAD_M[0] + (POND_THREAD_M[1] - POND_THREAD_M[0]) * rng();
      _pd(B, [o[0] + (rng() - 0.5) * 0.03, y + 0.002 * rng(), o[2] + (rng() - 0.5) * 0.03],
          [Math.cos(b), 0.02, Math.sin(b)], [-Math.sin(b), 0, Math.cos(b)], L, 0.002,
          'linear', 3, 0, 0.5 + 0.3 * rng());
    }
  }
}

// Flowering stalks out of the water, to the drawn height; their tips carry the
// flowers (15b-anchors.js: a stalk's tip is where the cluster's top is).
function _pondStalks(B, p, c, y0, top, R, rng, anchors) {
  const n = Math.max(1, Math.min(8, p.flowering_stems || 3));
  for (let i = 0; i < n; i++) {
    const a = rng() * 6.283, r = R * 0.6 * Math.sqrt(rng()), lean = (rng() - 0.5) * 0.04;
    const foot = [c[0] + Math.cos(a) * r, y0, c[2] + Math.sin(a) * r];
    const tip = [foot[0] + lean, top * (0.85 + 0.15 * rng()), foot[2] + lean];
    _lbTube(B, [foot, [(foot[0] + tip[0]) / 2, (foot[1] + tip[1]) / 2, (foot[2] + tip[2]) / 2], tip],
            0.0022, 0.0014, 0.6);
    anchors.push({ x: tip[0], y: tip[1], z: tip[2], nx: 0, nz: 0, top: true });
  }
}

// ── floating: chains of narrow fronds ───────────────────────────────────────

function _pondChains(B, p, c, y, R, rng) {
  const L = Math.max(0.006, (p.leaf_size_cm || 0.8) / 100);
  const starts = Math.max(8, Math.min(40, Math.round(1.2 * R * R / (L * L * 6))));
  const frond = (at, az, depth) => {
    // Tangled a few millimetres deep, not one flat sheet: drawn on the water's
    // opaque sheet, which would hide anything under it.
    at = [at[0], y + 0.005 * rng(), at[2]];
    const T = [Math.cos(az), 0, Math.sin(az)], S = [-Math.sin(az), 0, Math.cos(az)];
    const stalk = _lbAdd(at, T, L * 0.6);
    _pd(B, at, T, S, L * 0.6, 0.0008, 'linear', 1, 0, 0.45);           // its thread of a stalk
    _pd(B, stalk, T, S, L * (0.85 + 0.3 * rng()), L * 0.32, 'lanceolate', 1, 0, 0.6 + 0.2 * rng());
    if (depth <= 0) return;
    const knot = _lbAdd(stalk, T, L * 0.3);
    for (const s of [1, -1]) if (rng() < 0.8) frond(knot, az + s * 1.5708, depth - 1);
  };
  for (let i = 0; i < starts; i++) {
    const a = rng() * 6.283, r = R * 0.8 * Math.sqrt(rng());
    frond([c[0] + Math.cos(a) * r, y, c[2] + Math.sin(a) * r], rng() * 6.283, POND_CHAIN - 1);
  }
}

// ── broad-leaved emergents ──────────────────────────────────────────────────

// A leaf on its stalk from the crown, its blade at `top`, leaning out at `az`.
function _pondLeaf(B, p, base, az, top, rng, shape, L) {
  const lean = 0.12 + 0.3 * rng(), out = top * Math.tan(lean);
  const tip = [base[0] + Math.cos(az) * out, base[1] + top, base[2] + Math.sin(az) * out];
  _lbTube(B, [base, [(base[0] + tip[0]) / 2, base[1] + top * 0.5, (base[2] + tip[2]) / 2], tip],
          0.0026, 0.002, 0.62);
  const tilt = 0.25 + 0.5 * rng();                    // the blade held out from level
  const T = [Math.cos(az) * Math.cos(tilt), Math.sin(tilt), Math.sin(az) * Math.cos(tilt)];
  const S = [-Math.sin(az), 0, Math.cos(az)];
  if (shape === 'trifoliate') {
    for (const b of [0, 1.15, -1.15]) {
      const Tb = _lbMix(T, S, Math.cos(b), Math.sin(b)), Sb = _lbMix(S, T, Math.cos(b), -Math.sin(b));
      _pd(B, tip, Tb, Sb, L * 0.8, L * 0.8 * 0.6, 'elliptic', 2, 0.15, 0.7 + 0.2 * rng());
    }
    return tip;
  }
  _pd(B, tip, T, S, L, leafWidthFor(shape, L), shape, 3, 0.2, 0.7 + 0.2 * rng());
  return tip;
}

function _pondEmergent(B, p, form, c, gy, H, rng, anchors, owned) {
  const L = Math.max(0.04, Math.min(0.3, (p.leaf_size_cm || 10) / 100));
  const C = Math.max(0.15, p.canopy_m || 0.4);
  const share = POND_LEAF_SHARE[p.flower_arch === 'umbel' ? 'panicle' : (form === 'panicle' ? 'panicle' : 'raceme')];
  const leaves = Math.max(5, Math.min(12, Math.round(4 + C * 9)));
  const shape = form === 'trifoliate' ? 'trifoliate' : (p.leaf_shape || 'ovate');
  for (let i = 0; i < leaves; i++) {
    const az = i * 2.39996 + rng() * 0.6, off = C * 0.12 * rng();
    const base = [c[0] + Math.cos(az) * off, gy, c[2] + Math.sin(az) * off];
    _pondLeaf(B, p, base, az, H * (share[0] + (share[1] - share[0]) * rng()), rng, shape, L);
  }
  const scapes = Math.max(1, Math.min(form === 'panicle' ? 2 : 4, Math.round((p.flowering_stems || 4) / (form === 'panicle' ? 7 : 1))));
  for (let i = 0; i < scapes; i++) {
    const az = rng() * 6.283, off = C * 0.1 * rng();
    const foot = [c[0] + Math.cos(az) * off, gy, c[2] + Math.sin(az) * off];
    const top = gy + H * (form === 'spathe' ? 0.55 + 0.3 * rng() : 0.9 + 0.1 * rng());
    const tip = [foot[0] + Math.cos(az) * 0.03, top, foot[2] + Math.sin(az) * 0.03];
    _lbTube(B, [foot, [(foot[0] + tip[0]) / 2, (gy + top) / 2, (foot[2] + tip[2]) / 2], tip], 0.004, 0.0025, 0.6);
    if (form === 'panicle') _pondPanicle(B, tip, top - gy, rng, anchors);
    else if (form === 'spathe') owned.push({ at: tip, az });
    else anchors.push({ x: tip[0], y: tip[1], z: tip[2], nx: 0, nz: 0, top: true });
  }
}

// A water-plantain's panicle: whorls of thin branches up the top of the scape,
// shorter toward its tip, each ending where a cluster of flowers is.
function _pondPanicle(B, tip, h, rng, anchors) {
  const tiers = 4;
  for (let t = 0; t < tiers; t++) {
    const f = t / tiers, y = tip[1] - h * 0.42 * (1 - f), len = h * 0.2 * (1 - 0.65 * f);
    const per = t === tiers - 1 ? 3 : 4 + (t % 2), rot = rng() * 6.283;
    for (let k = 0; k < per; k++) {
      const a = rot + k * 6.283 / per, rise = 0.6 + 0.25 * rng();
      const o = [tip[0], y, tip[2]];
      const end = [o[0] + Math.cos(a) * len * Math.cos(rise), y + len * Math.sin(rise),
                   o[2] + Math.sin(a) * len * Math.cos(rise)];
      _lbTube(B, [o, end], 0.0014, 0.0009, 0.62);
      anchors.push({ x: end[0], y: end[1], z: end[2], nx: Math.cos(a), nz: Math.sin(a) });
    }
  }
  anchors.push({ x: tip[0], y: tip[1], z: tip[2], nx: 0, nz: 0, top: true });
}

// A spathe round its spadix: a white blade cupped open, a yellow-green club.
function _pondSpathes(p, owned, month, groups) {
  if (!owned.length || !p.bloom_start) return;
  const within = (month - p.bloom_start + 12) % 12 <= ((p.bloom_end || p.bloom_start) - p.bloom_start + 12) % 12;
  if (!within) return;
  const d = Math.max(0.03, Math.min(0.1, (p.flower_diameter_cm || 5) / 100)) * 1.2;
  const S = _lbNew(), K = _lbNew();
  for (const { at, az } of owned) {
    const out = [Math.cos(az) * 0.45, 0.89, Math.sin(az) * 0.45], side = [-Math.sin(az), 0, Math.cos(az)];
    _pd(S, at, out, side, d * 1.5, d, 'ovate', 3, -0.5, 1);       // cupped back, open to the sky
    const front = _lbAdd(at, [Math.cos(az), 0, Math.sin(az)], d * 0.12);
    _lbTube(K, [front, _lbAdd(front, out, d * 0.75)], d * 0.11, d * 0.08, 1);
  }
  groups.push({ B: S, color: p.flower_color || '#f4f1e6', name: p.common_name, id: p.plant_id, mat: 'petal' });
  groups.push({ B: K, color: p.flower_center_color || '#c8c45a', name: p.common_name, id: p.plant_id, mat: 'petal' });
}

// ── the layer ───────────────────────────────────────────────────────────────

// Draws `p` if one of these forms is its; returns false to leave it to 23-pond.js.
function buildPondForm(p, d, gy, rng, col, month, out) {
  const form = pondFormOf(p);
  if (!form) return false;
  const B = _lbNew(), anchors = [], owned = [];
  const c = [p.x, 0, -p.y];
  const R = Math.max(0.08, (p.canopy_m || 0.4) / 2);
  const water = gy + (d.water_m || 0);
  if (form === 'feathery' || form === 'threads') {
    (form === 'feathery' ? _pondFeathery : _pondThreads)(B, p, c, water + 0.004, R, rng);
    if (p.flower_color && p.bloom_start) {
      _pondStalks(B, p, c, water, gy + Math.max(d.height_m || 0, (d.water_m || 0) + 0.06), R, rng, anchors);
    }
  } else if (form === 'chains') {
    _pondChains(B, p, c, water + 0.003, R, rng);
  } else {
    _pondEmergent(B, p, form, c, gy, Math.max(0.1, bodyHeightOf(p)), rng, anchors, owned);
    _pondSpathes(p, owned, month, out);
  }
  // 23-pond.js's part names: shoot tips at the surface, pads on it, leaves standing.
  const part = form === 'feathery' || form === 'threads' ? 'pond_sprig'
    : form === 'chains' ? 'pond_pad' : 'pond_leaf';
  out.push({ B, color: col, name: p.common_name, id: p.plant_id, mat: 'leaf', part });
  if (anchors.length) POND_ANCHORS.set(p, anchors);
  return true;
}

// The meshes for what buildPondForm gathered: one a part, coloured whole.
function addPondForms(out) {
  for (const g of out) {
    if (!g.B.idx.length) continue;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(g.B.pos, 3));
    geo.setAttribute('color', new THREE.Float32BufferAttribute(g.B.col, 3));
    geo.setIndex(g.B.idx);
    geo.computeVertexNormals();
    const mesh = instancedMesh(geo, 1, g.mat === 'petal' ? floretMaterial() : MATS.leaf);
    mesh.setMatrixAt(0, new THREE.Matrix4());
    mesh.setColorAt(0, g.color instanceof THREE.Color ? g.color : new THREE.Color(g.color));
    mesh.userData.pick = [g.name || ''];
    mesh.userData.pickId = [g.id];
    mesh.userData.part = g.mat === 'petal' ? 'pond_spathe' : g.part;
    plantsGroup.add(mesh);
  }
}

window.pondFormsReset = pondFormsReset;
window.pondAnchorsFor = pondAnchorsFor;
window.pondOwnsFlower = pondOwnsFlower;
window.buildPondForm = buildPondForm;
window.addPondForms = addPondForms;
