// Part of the Site & Pattern 3D viewer. Loaded as an ordered CLASSIC
// script by the bootstrap in scene3d.html — it shares the global scope
// with its siblings (THREE and friends are globals set by the
// bootstrap). Do not add ES `import`/`export` here.
//
// Design principle P5 — see docs/DESIGN_PHILOSOPHY.md
//
// Where a flower or a fruit sits on the plant it belongs to (V3.48).
//
// Until V3.48 a bloom was put at a random spot in a disc over the plant, at a
// random height near its top, and a fruit likewise. Nothing tied either to the
// stems and leaves that were drawn. Read against photographs of the region's
// 250 natives, 83 plants had flowers hanging in the air: heads hovering above
// bare stalk tips, a shrub's flowers in a flat cap over it, berries beside the
// bush. The body is already drawn when the flowers are, so they are put on it:
//
// * a herb's flowers go on its stem tips, the highest points of its drawn body,
//   one inflorescence to a tip, the tallest tips first;
// * a shrub's or a tree's go on the outside of its crown, all the way round and
//   from a quarter of its height up, which is where a saskatoon carries them;
// * fruit goes where the flowers were.
//
// Vines and succulents keep their own anchors (22-vines.js, 24-succulents.js).
// An anchor is {x, y, z, nx, nz, top}: a point in the scene, the way out from
// the plant there, and `top` when the bloom's top is to be at the point (a
// stem's tip) and not its middle (a twig in a crown).

const _BLOOM_BODY = new Map();       // plant -> where its body was drawn
const _TIP_CACHE = new Map();        // geometry uuid -> stem tips, unit frame
const _CROWN_CACHE = new Map();      // geometry uuid -> crown points, unit frame

function bloomBodiesReset() { _BLOOM_BODY.clear(); }

// A herb's body, noted by 04-quality.js buildHerbLayer as it places it.
function noteBloomBody(p, geo, x, gy, z, sxz, sy, rotY) {
  if (!_BLOOM_BODY.has(p)) _BLOOM_BODY.set(p, { geo, x, gy, z, sxz, sy, rotY });
}

// The highest point of the body in each cell of a grid laid over it: its stem
// tips, tallest first. Points in the lower three quarters are leaves, not tips.
function _stemTips(geo) {
  let tips = _TIP_CACHE.get(geo.uuid);
  if (tips) return tips;
  const pos = geo.attributes.position, G = 9, cells = new Map();
  let top = 0;
  for (let i = 0; i < pos.count; i++) top = Math.max(top, pos.getY(i));
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
    if (y < top * 0.75) continue;
    const key = Math.floor((x + 0.5) * G) * 64 + Math.floor((z + 0.5) * G);
    const c = cells.get(key);
    if (!c || y > c.y) cells.set(key, { x, y, z });
  }
  tips = Array.from(cells.values()).sort((a, b) => b.y - a.y);
  _TIP_CACHE.set(geo.uuid, tips);
  return tips;
}

// The outermost point of a crown in each bearing and height band, from a
// quarter of the way up. Ordered so that any few of them are spread round it.
function _crownPoints(geos) {
  const key = geos.map(g => g.uuid).join('|');
  let pts = _CROWN_CACHE.get(key);
  if (pts) return pts;
  const AZ = 16, BANDS = 6, cells = new Map();
  let top = 0;
  for (const geo of geos) {
    const pos = geo.attributes.position;
    for (let i = 0; i < pos.count; i++) top = Math.max(top, pos.getY(i));
  }
  for (const geo of geos) {
    const pos = geo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
      const t = y / (top || 1);
      if (t < 0.25) continue;
      const r = Math.hypot(x, z);
      const k = Math.floor((Math.atan2(z, x) + Math.PI) / (2 * Math.PI) * AZ) % AZ
        + AZ * Math.min(BANDS - 1, Math.floor((t - 0.25) / 0.75 * BANDS));
      const c = cells.get(k);
      if (!c || r > c.r) cells.set(k, { x, y, z, r });
    }
  }
  const all = Array.from(cells.values());
  pts = [];
  for (let i = 0, j = 0; i < all.length; i++, j = (j + 5) % all.length) {
    while (all[j] === null) j = (j + 1) % all.length;
    pts.push(all[j]); all[j] = null;
  }
  _CROWN_CACHE.set(key, pts);
  return pts;
}

const _bm = new THREE.Matrix4(), _bq = new THREE.Quaternion();
const _bv = new THREE.Vector3(), _bs = new THREE.Vector3(), _bp = new THREE.Vector3();
const _bUp = new THREE.Vector3(0, 1, 0);

function _toScene(points, b, top) {
  _bq.setFromAxisAngle(_bUp, b.rotY);
  _bm.compose(_bv.set(b.x, b.gy, b.z), _bq, _bs.set(b.sxz, b.sy, b.sxz));
  return points.map((u) => {
    _bp.set(u.x, u.y, u.z).applyMatrix4(_bm);
    const dx = _bp.x - b.x, dz = _bp.z - b.z, d = Math.hypot(dx, dz) || 1;
    return { x: _bp.x, y: _bp.y, z: _bp.z, nx: top ? 0 : dx / d, nz: top ? 0 : dz / d, top };
  });
}

// The anchors for `count` blooms or fruit on plant `p`, or null when the plant's
// body is not one this chunk knows (the caller then places them as it did).
function bloomAnchors(p, count, month) {
  const own = (window.vineAnchorsFor && vineAnchorsFor(p))             // V2.89
    || (window.succulentAnchorsFor && succulentAnchorsFor(p));        // V2.93
  if (own) return own;
  const herb = _BLOOM_BODY.get(p);
  if (herb) {
    const tips = _stemTips(herb.geo);
    return tips.length ? _toScene(tips.slice(0, Math.max(1, count)), herb, true) : null;
  }
  const woody = window.vineHostOf && vineHostOf(p);
  if (!woody || !woody.geos.length) return null;
  // A shrub notes its leaves first and its stems second; out of leaf, a flower
  // is on the twigs.
  const bare = typeof leafless === 'function' && leafless(p, month);
  const geos = bare && p.plant_type === 'shrub' && woody.geos.length > 1
    ? [woody.geos[1]] : woody.geos;
  const pts = _crownPoints(geos);
  return pts.length ? _toScene(pts, woody, false) : null;
}

// How many inflorescences a shrub or tree carries: by the size of its crown,
// and never fewer than its recorded count. It was nine for every shrub, and the
// recorded counts are a forb's (14 for a saskatoon): a 4 m saskatoon in flower
// is white all over, and fourteen racemes on it are fourteen specks. A
// knee-high rose still holds about a dozen.
const WOODY_BLOOMS_MAX = 90;
function woodyBloomCount(p) {
  const c = Math.max(0.3, p.canopy_m || 1), h = Math.max(0.3, p.height_m || 1);
  return Math.max(8, p.flowering_stems || 0,
                  Math.min(WOODY_BLOOMS_MAX, Math.round(8 * c * h)));
}

// How much larger than life a shrub's or tree's flower is drawn. A big shrub
// carries thousands of flowers and ninety clusters are drawn, so each drawn one
// stands for many, the trade V2.88 made inside a cluster: at life size a 4 m
// saskatoon's flowers were single pixels and the shrub never read as in flower.
// 1 up to 1.5 m, rising to 2.5 at 6 m and over. An estimate: nothing records
// how much of a crown its flowers cover.
function woodyBloomGain(p) {
  if (p.plant_type !== 'tree' && p.plant_type !== 'shrub') return 1;
  return Math.max(1, Math.min(2.5, 1 + ((p.height_m || 1) - 1.5) / 3));
}

window.noteBloomBody = noteBloomBody;
window.bloomBodiesReset = bloomBodiesReset;
window.bloomAnchors = bloomAnchors;
window.woodyBloomCount = woodyBloomCount;
