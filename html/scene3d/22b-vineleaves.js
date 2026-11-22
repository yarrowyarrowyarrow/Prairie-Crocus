// Part of the Site & Pattern 3D viewer. Loaded as an ordered CLASSIC
// script by the bootstrap in scene3d.html — it shares the global scope
// with its siblings (THREE and friends are globals set by the
// bootstrap). Do not add ES `import`/`export` here.
//
// Design principle P10 — see docs/DESIGN_PHILOSOPHY.md
//
// A vine's leaves, once they are read (V3.50, F268).
//
// Read against photographs, all five of the region's native vines were "a
// wisp at the host's foot": a few threads of single small leaves, so a blue
// clematis on a dogwood showed only the dogwood. 22-vines.js lays a vine's
// stems up the crown it climbs; where its leaves were read (leaf_data_source
// photo, flora or measured), this lays its leafy shoots along those stems as
// the shrubs' are (03d-woody.js): each a card cut to the species' own leaf,
// in its arrangement, at its size, facing out from what it climbs. Its
// flowers then go on cards too (15c-woodybloom.js), at the stems' ends.
//
// What nothing records, and is a stated estimate here: how closely the
// shoots follow one another along a stem (VINE_SHOOT_GAP, in shoot lengths).
// 0.55 until V3.65, when the peavines and vetch were still a few sprays lost
// on the shrub they climb: a vine in leaf clothes the side it is on.

const VINE_SHOOT_GAP = 0.3;
const VINE_CARDS_MAX = 900;
const _VINE_READ = { photo: 1, flora: 1, measured: 1 };

function vineReadFor(p) {
  return !STYLISED && p && p.plant_type === 'vine' && !!_VINE_READ[p.leaf_data_source]
    && !!p.leaf_shape && (p.leaf_size_cm || 0) > 0;
}

// The vine's leafy shoots along `paths` (22-vines.js), as one mesh. Pushes
// where its flowers may go onto `anchors` (above `floorY`).
function buildVineSprays(p, paths, rng, floorY, anchors, month) {
  const per = p.leaf_arrangement === 'opposite' ? 2 : 1;
  const cut = _wdSpray(p.leaf_shape, per), sp = cut;                // 03d-woody.js
  const L = Math.max(0.01, (p.leaf_size_cm || 6) / 100);
  const w = sp.w * L, h = sp.h * L, gap = h * VINE_SHOOT_GAP;
  const F = Object.assign(_lbNew(), { uv: [] });
  let cards = 0, total = 0;
  for (const pa of paths) {
    for (let j = 1; j < pa.pts.length; j++) total += pa.pts[j - 1].distanceTo(pa.pts[j]);
  }
  const step = Math.max(gap, total / VINE_CARDS_MAX);
  for (const pa of paths) {
    let next = step * rng(), dist = 0;
    for (let j = 1; j < pa.pts.length; j++) {
      const A = pa.pts[j - 1], C = pa.pts[j], N = pa.nrm[j], seg = A.distanceTo(C);
      const run = pa.gnd && pa.gnd[j];
      for (; next <= dist + seg; next += run ? step * 2.5 : step) {
        const f = seg > 0 ? (next - dist) / seg : 0;
        const at = [A.x + (C.x - A.x) * f, A.y + (C.y - A.y) * f, A.z + (C.z - A.z) * f];
        // Out from the stem and the crown it climbs, a little up, to one side;
        // on the ground (a runner, or a vine with nothing to climb) it lies
        // nearly flat, facing the sky (vine_habit.SPRAWL_HEIGHT_M).
        const side = rng() < 0.5 ? -1 : 1, low = run || !paths.climbing;
        const tg = _lbUnit([C.x - A.x, C.y - A.y, C.z - A.z]);
        const out = low ? [0, 1, 0] : [N.x, N.y, N.z];
        let T = _lbUnit([out[0] * 0.55 + tg[0] * 0.3 + side * tg[2] * 0.5,
                         (low ? 0.06 : 0.45 + out[1] * 0.4) + (rng() - 0.5) * (low ? 0.08 : 0.5),
                         out[2] * 0.55 + tg[2] * 0.3 - side * tg[0] * 0.5]);
        const Nn = low ? [0, 1, 0] : _lbUnit([out[0] + (rng() - 0.5) * 0.5, 0.35 + (rng() - 0.5) * 0.4,
                                              out[2] + (rng() - 0.5) * 0.5]);
        const dn = T[0] * Nn[0] + T[1] * Nn[1] + T[2] * Nn[2];
        T = _lbUnit(_lbAdd(T, Nn, -dn));
        const S = _lbCross(Nn, T), k = 0.85 + 0.3 * rng();
        _wdCard(F, at, T, S, w * k, h * k, 0.62 + 0.3 * rng());       // 03d-woody.js
        if (cards++ % 4 === 0 && !run && at[1] >= floorY) {
          const tip = _lbAdd(at, T, h * k * 0.9);
          anchors.push({ x: tip[0], y: tip[1], z: tip[2], nx: N.x, nz: N.z });
        }
      }
      dist += seg;
    }
  }
  if (!cards) return null;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(F.pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(F.col, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(F.uv, 2));
  g.setIndex(F.idx);
  g.computeVertexNormals();
  const mesh = instancedMesh(g, 1, surfaceMaterial(MAT_PRESETS.shrubLeaf, leafSurfaceFor(p), true, cut));
  mesh.customDepthMaterial = cut.depth;
  mesh.setMatrixAt(0, new THREE.Matrix4());
  mesh.setColorAt(0, bodyColor(p, month));                            // 01d-season.js
  mesh.userData.pick = [p.common_name || ''];
  mesh.userData.pickId = [p.plant_id];
  mesh.userData.part = 'vine';
  mesh.userData.vineCards = cards;
  return mesh;
}

window.vineReadFor = vineReadFor;
window.buildVineSprays = buildVineSprays;
