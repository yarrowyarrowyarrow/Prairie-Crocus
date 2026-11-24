// Part of the Site & Pattern 3D viewer. Loaded as an ordered CLASSIC
// script by the bootstrap in scene3d.html — it shares the global scope
// with its siblings (THREE and friends are globals set by the
// bootstrap). Do not add ES `import`/`export` here.
//
// Design principle P5 — see docs/DESIGN_PHILOSOPHY.md
//
// Flowers that hang (V3.67b, F268).
//
// Read against their photographs, the lowest-scoring wildflowers included
// every plant whose flower HANGS: prairie smoke's dusty-pink urns in threes,
// water avens' purple bells, saline shooting star's magenta darts, bog
// cranberry's pink darts on thread-thin stalks, blue clematis' bells. Each was
// drawn by 15-florets.js as a flat star facing the sky, which is the one
// thing those flowers never do, and their names in the readings were "flat
// upturned stars".
//
// A flower whose `head_attitude` is recorded `nodding` or `hanging` (the
// column a grass's head has carried since V3.51; read off the photographs) is
// drawn here instead: hanging from its stalk's tip on a short arching stalk of
// its own, turned out from the plant, as
//
//   a BELL   its petals (or sepals) cupped round its opening, which faces down,
//            narrow and a little flared at the mouth;
//   a DART   where its petals are recorded `reflexed`: swept back up over the
//            stalk, with the beak of its stamens pointing down (a shooting
//            star; a bog cranberry's is the same flower in small).
//
// What nothing records, and is a stated estimate here: how far a hanging
// flower turns out from straight down (NOD_TILT), how long its own stalk is
// (NOD_PEDICEL, in flower lengths), and how small it may be drawn: at least
// NOD_MIN_M, never more than NOD_GAIN_MAX times its width (15e-heads.js
// draws a loose cluster's showy flowers at least 2.8 cm for the same reason;
// at 2.8 prairie smoke's urns were harebells).
// On a vine a flower is drawn larger, as a shrub's are (15b-anchors.js
// woodyBloomGain): it is seen on its host from the host's distance.

const NOD_TILT = [0.25, 0.7];
const NOD_PEDICEL = 0.7;
const NOD_MIN_M = 0.024;
const NOD_GAIN_MAX = 1.8;
// A dart (a swept-back flower) may be drawn larger, up to NOD_DART_GAIN_MAX:
// at 1.8 a bog cranberry's 1 cm darts were specks over its mat (V3.67c).
const NOD_DART_GAIN_MAX = 2.4;
// A hanging flower on a bare stalk from the ground (a rosette's scape, a mat's
// pedicel) is drawn with it here, the stalk in the flower's colour mixed this
// much toward a red-brown (SCAPE_TINT): prairie smoke's, a shooting star's and
// a bog cranberry's stalks are red in their photographs. An estimate (V3.67c).
const SCAPE_TINT = '#7a4636', SCAPE_MIX = 0.6;
// Flowers on one stalk's tip, at most: a cyme's three, an umbel's few.
const NOD_PER_CLUSTER_MAX = 7;

function noddingApplies(p) {
  if (STYLISED || !p || !p.flower_color || p.inflorescence_form) return false;
  if (p.head_attitude !== 'nodding' && p.head_attitude !== 'hanging') return false;
  return p.plant_type !== 'tree' && p.plant_type !== 'shrub';
}

// ── the flower, hanging: its stalk at the origin, its opening down -Y ───────

function _nodPush(B, a, b, c) {
  const i = B.pos.length / 3;
  B.pos.push(a[0], a[1], a[2], b[0], b[1], b[2], c[0], c[1], c[2]);
  B.idx.push(i, i + 1, i + 2);
}

// A bell of `n` petals, 1 long and about 0.8 across its mouth: each petal a
// strip from the top down to a pointed tip, curving out at the rim.
function _nodBellGeo(n) {
  const B = { pos: [], idx: [] };
  const rings = [[0, 0.1], [-0.42, 0.25], [-0.82, 0.31], [-1, 0.37]];
  const half = Math.PI / n * 1.08;                  // a little overlap, so it is closed
  const at = (a, y, r) => [Math.cos(a) * r, y, Math.sin(a) * r];
  for (let i = 0; i < n; i++) {
    const c = i * 2 * Math.PI / n;
    for (let k = 0; k < rings.length - 1; k++) {
      const [y0, r0] = rings[k], [y1, r1] = rings[k + 1];
      const tip = k === rings.length - 2;
      const w1 = tip ? 0.15 : 1;                     // the last ring closes to the tip
      _nodPush(B, at(c - half, y0, r0), at(c, y0, r0 * 1.02), at(c - half * w1, y1, r1));
      _nodPush(B, at(c, y0, r0 * 1.02), at(c, y1, r1 * 1.03), at(c - half * w1, y1, r1));
      _nodPush(B, at(c, y0, r0 * 1.02), at(c + half, y0, r0), at(c + half * w1, y1, r1));
      _nodPush(B, at(c, y0, r0 * 1.02), at(c + half * w1, y1, r1), at(c, y1, r1 * 1.03));
    }
  }
  return _nodGeo(B);
}

// A dart: `n` petals swept back up from a ring just under the stalk, each a
// narrow blade to a point above it; the beak is its own mesh (_nodBeakGeo).
function _nodDartGeo(n) {
  const B = { pos: [], idx: [] };
  const half = Math.PI / n * 0.55;
  const at = (a, y, r) => [Math.cos(a) * r, y, Math.sin(a) * r];
  for (let i = 0; i < n; i++) {
    const c = i * 2 * Math.PI / n;
    const base = at(c, -0.3, 0.07), mid = (s) => at(c + s * half, -0.05, 0.2);
    const tip = at(c, 0.32, 0.3);
    _nodPush(B, base, mid(-1), tip);
    _nodPush(B, base, tip, mid(1));
  }
  return _nodGeo(B);
}

// The beak of a dart: a cone of stamens from the petals' ring, pointing down.
function _nodBeakGeo() {
  const B = { pos: [], idx: [] }, n = 6;
  for (let i = 0; i < n; i++) {
    const a0 = i * 2 * Math.PI / n, a1 = (i + 1) * 2 * Math.PI / n;
    _nodPush(B, [Math.cos(a0) * 0.08, -0.3, Math.sin(a0) * 0.08],
             [Math.cos(a1) * 0.08, -0.3, Math.sin(a1) * 0.08], [0, -0.78, 0]);
  }
  return _nodGeo(B);
}

// A flower's own stalk: a thin ribbon a unit long up +Y, crossed so it shows
// from every side.
function _nodStalkGeo() {
  const B = { pos: [], idx: [] };
  for (const [x, z] of [[0.5, 0], [0, 0.5]]) {
    _nodPush(B, [-x, 0, -z], [x, 0, z], [x, 1, z]);
    _nodPush(B, [-x, 0, -z], [x, 1, z], [-x, 1, -z]);
  }
  return _nodGeo(B);
}

function _nodGeo(B) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(B.pos, 3));
  g.setIndex(B.idx);
  g.computeVertexNormals();
  return g;
}

const _NOD_GEOS = new Map();
function _nodShape(kind, n) {
  const key = kind + '|' + n;
  let g = _NOD_GEOS.get(key);
  if (!g) {
    g = kind === 'bell' ? _nodBellGeo(n) : kind === 'dart' ? _nodDartGeo(n)
      : kind === 'beak' ? _nodBeakGeo() : _nodStalkGeo();
    _NOD_GEOS.set(key, g);
  }
  return g;
}

// ── where they hang ─────────────────────────────────────────────────────────

// How large one hanging flower is drawn, in metres along its length.
function noddingSize(p) {
  const d = Math.max(0.15, Math.min(20, p.flower_diameter_cm || 2)) / 100;
  if (p.plant_type === 'vine') return d * woodyBloomGain(p);         // 15b-anchors.js
  const most = p.petal_shape === 'reflexed' ? NOD_DART_GAIN_MAX : NOD_GAIN_MAX;
  return Math.max(d, Math.min(NOD_MIN_M, d * most));
}

// Flowers on one stalk's tip: a solitary flower's one, a cyme's or an umbel's
// recorded count, never more than NOD_PER_CLUSTER_MAX.
function _nodPerCluster(p) {
  if (p.flower_arch === 'solitary' || p.flower_arch === 'head') return 1;
  return Math.max(1, Math.min(NOD_PER_CLUSTER_MAX, p.florets_per_head || 3));
}

// Clusters a plant carries: a vine's by the crown it covers (15c-woodybloom.js),
// a herb's as counted, a groundcover's at least one a stalk.
function _nodClusters(p) {
  if (p.plant_type === 'vine' && window.woodyBloomCards) return woodyBloomCards(p);
  return Math.max(1, p.flowering_stems || 6);
}

function buildNodding(plants, month, terrain) {
  if (!plants || !plants.length) return;
  const sets = new Map();             // kind|petals -> {xf, col, beak, names, ids}
  const stalks = { xf: [], col: [], names: [], ids: [] };
  const c = new THREE.Color(), cc = new THREE.Color(), sc = new THREE.Color();
  const Y = new THREE.Vector3(), D = new THREE.Vector3(), q = new THREE.Quaternion();
  const q2 = new THREE.Quaternion(), m = new THREE.Matrix4(), v = new THREE.Vector3();
  const s3 = new THREE.Vector3(), DOWN = new THREE.Vector3(0, -1, 0), UP = new THREE.Vector3(0, 1, 0);
  for (const p of plants) {
    if ((p.opacity ?? 1) < 0.25) continue;
    const kind = p.petal_shape === 'reflexed' ? 'dart' : 'bell';
    const petals = Math.max(3, Math.min(8, p.petal_count || 5));
    const key = kind + '|' + petals;
    let set = sets.get(key);
    if (!set) sets.set(key, set = { kind, petals, xf: [], col: [], beak: [], names: [], ids: [] });
    c.set(p.flower_color || '#ffffff');
    cc.set(p.flower_center_color || '#c9a23a');
    // Its own stalk: the flower's colour, darkened toward a stem's green; on a
    // bare scape from the ground (the body draws none, 03c-leafy.js), red-brown.
    const scape = !!(p.drawn && p.drawn.hangs && (p.drawn.form === 'rosette' || p.drawn.form === 'mat'));
    if (scape) sc.copy(c).lerp(new THREE.Color(SCAPE_TINT), SCAPE_MIX);
    else sc.copy(c).multiplyScalar(0.45).lerp(new THREE.Color('#4f6b34'), 0.45);
    const gy = terrainHeightAt(p.x, p.y, terrain);
    const L = noddingSize(p), per = _nodPerCluster(p);
    const clusters = _nodClusters(p);
    const anchors = bloomAnchors(p, clusters, month);           // 15b-anchors.js
    if (!anchors || !anchors.length) continue;
    let s = hashPid(p.plant_id || 1) >>> 0;
    const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
    const n = Math.min(clusters, p.plant_type === 'vine' ? anchors.length : clusters);
    for (let k = 0; k < n; k++) {
      const a = anchors[(k * (anchors.length % 7 ? 7 : 1) + (s % 97)) % anchors.length];   // never 2 of 14 (V3.67c)
      if (scape) {                       // up from the ground to the tip, leaning in a little
        const foot = [a.x + (p.x - a.x) * 0.15, gy + 0.002, a.z + (-p.y - a.z) * 0.15];
        D.set(a.x - foot[0], a.y - foot[1], a.z - foot[2]);
        const len = D.length(), w = Math.max(0.0012, noddingSize(p) * 0.06);
        q.setFromUnitVectors(UP, D.normalize());
        m.compose(v.set(foot[0], foot[1], foot[2]), q, s3.set(w, len, w));
        stalks.xf.push(m.clone()); stalks.col.push(sc.clone());
        stalks.names.push(p.common_name || ''); stalks.ids.push(p.plant_id);
      }
      // Out from the plant: the anchor's own way out (a vine's), else from its middle.
      let ox = a.nx, oz = a.nz;
      if (!ox && !oz) {
        const dx = a.x - p.x, dz = a.z + p.y, dd = Math.hypot(dx, dz);
        const az = dd > 0.01 ? Math.atan2(dz, dx) : rnd() * 6.283;
        ox = Math.cos(az); oz = Math.sin(az);
      }
      for (let f = 0; f < per; f++) {
        // Round the tip: the first flower out the way the plant faces, the
        // rest round it (an umbel's all the way round, a cyme's to the sides).
        const spread = per > 3 ? 6.283 / per : 1.1;
        const az = Math.atan2(oz, ox) + (f - (per - 1) / 2) * spread + (rnd() - 0.5) * 0.4;
        const hx = Math.cos(az), hz = Math.sin(az);
        const ped = L * NOD_PEDICEL * (0.8 + 0.4 * rnd());
        // The stalk rises a little out of the tip and arches over: the flower
        // hangs from its end, below and beside the tip.
        const top = [a.x + hx * ped * 0.7, a.y + ped * 0.25, a.z + hz * ped * 0.7];
        D.set(top[0] - a.x, top[1] - a.y, top[2] - a.z);
        const len = D.length();
        D.normalize();
        q.setFromUnitVectors(UP, D);
        const w = Math.max(0.0012, L * 0.05);
        m.compose(v.set(a.x, a.y, a.z), q, s3.set(w, len, w));
        stalks.xf.push(m.clone()); stalks.col.push(sc.clone());
        stalks.names.push(p.common_name || ''); stalks.ids.push(p.plant_id);
        // The flower: hanging from the stalk's end, turned out by NOD_TILT.
        const tilt = NOD_TILT[0] + (NOD_TILT[1] - NOD_TILT[0]) * rnd();
        Y.set(hx * Math.sin(tilt), -Math.cos(tilt), hz * Math.sin(tilt)).normalize();
        q.setFromUnitVectors(DOWN, Y);
        q2.setFromAxisAngle(Y, rnd() * 6.283);
        q.premultiply(q2);
        const size = L * (0.88 + 0.24 * rnd());
        m.compose(v.set(top[0], top[1], top[2]), q, s3.set(size, size, size));
        set.xf.push(m.clone()); set.col.push(c.clone()); set.beak.push(cc.clone());
        set.names.push(p.common_name || ''); set.ids.push(p.plant_id);
      }
    }
  }
  const add = (geo, xf, cols, names, ids, part) => {
    if (!xf.length) return;
    const mesh = instancedMesh(geo, xf.length, floretMaterial(), false);  // 15-florets.js
    xf.forEach((mm, i) => { mesh.setMatrixAt(i, mm); mesh.setColorAt(i, cols[i]); });
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    mesh.userData.pick = names;
    mesh.userData.pickId = ids;
    mesh.userData.part = part;
    plantsGroup.add(mesh);
  };
  for (const set of sets.values()) {
    add(_nodShape(set.kind, set.petals), set.xf, set.col, set.names, set.ids, 'floret');
    if (set.kind === 'dart') add(_nodShape('beak', 0), set.xf, set.beak, set.names, set.ids, 'floret_beak');
  }
  add(_nodShape('stalk', 0), stalks.xf, stalks.col, stalks.names, stalks.ids, 'floret_stalk');
}

window.noddingApplies = noddingApplies;
window.noddingSize = noddingSize;
window.buildNodding = buildNodding;
