// Part of the Prairie Crocus 3D viewer. Loaded as an ordered CLASSIC
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
// on the shrub they climb: a vine in leaf clothes the side it is on. Since
// V3.67c a herbaceous vine is drawn on its host's near side, a few stems with
// a leaf at each node (VINE_SOFT_GAP), not a blanket over it.

const VINE_SHOOT_GAP = 0.3;
const VINE_SOFT_GAP = 0.6;
const VINE_CARDS_MAX = 900;
const _VINE_READ = { photo: 1, flora: 1, measured: 1 };

// Leaflets on a pinnate vine leaf, by genus, or by species where its
// photographs differ from its genus's (V3.67c). The catalogue records
// compound_pinnate for a peavine's few broad leaflets and a vetch's many narrow
// ones alike, and one painting of both made the cream peavine a vetch. Pairs, a
// leaflet's width as a share of its length, and its length as a share of the
// leaf's: estimates read off the photographs, as a tree's leaflet_pairs are
// (02-plants.js _PROF). Each leaf ends in a tendril.
const VINE_LEAFLETS = { lathyrus: [3, 0.6, 0.46], 'lathyrus venosus': [5, 0.5, 0.34],
                        vicia: [6, 0.3, 0.3] };
const _VINE_SPRAYS = new Map();
function vineLeafletSpray(p) {
  const sp0 = (p.species || '').toLowerCase(), g0 = (p.genus || '').toLowerCase();
  const genus = VINE_LEAFLETS[sp0] ? sp0 : g0;                      // the scene's, lowercased
  const row = p.leaf_shape === 'compound_pinnate' && VINE_LEAFLETS[genus];
  if (!row) return null;
  let sp = _VINE_SPRAYS.get(genus);
  if (sp) return sp;
  const [pairs, ratio, size] = row, W = 192, H = 192, len = 64, cv = document.createElement('canvas');
  cv.width = W; cv.height = H;
  const g = cv.getContext('2d', { willReadFrequently: true });
  g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
  g.fillStyle = g.strokeStyle = '#fff'; g.lineCap = 'round';
  const rnd = _lcg(71 + pairs * 13);                                    // 01b-surface.js
  const leaf = (x, y, a) => {          // a rachis, its pairs of leaflets, a tendril
    g.save(); g.translate(x, y); g.rotate(a);
    g.lineWidth = 1.6; g.beginPath(); g.moveTo(0, 0); g.lineTo(0, -len); g.stroke();
    const lf = len * size, wf = lf * ratio;
    for (let k = 0; k < pairs; k++) {
      for (const sg of [-1, 1]) {
        g.save(); g.translate(0, -len * (0.2 + 0.68 * k / Math.max(1, pairs - 1)));
        g.rotate(sg * (0.85 + 0.3 * rnd()));
        g.beginPath(); g.ellipse(0, -lf / 2, wf / 2, lf / 2, 0, 0, 6.2832); g.fill(); g.restore();
      }
    }
    g.lineWidth = 1.1; g.beginPath(); g.moveTo(0, -len);
    g.quadraticCurveTo(len * 0.2, -len * 1.15, len * 0.05, -len * 1.28); g.stroke();
    g.restore();
  };
  g.lineWidth = 2.2; g.beginPath(); g.moveTo(W / 2, H); g.lineTo(W / 2, H - len * 1.35); g.stroke();
  leaf(W / 2, H - len * 0.3, -1.0); leaf(W / 2, H - len * 0.75, 1.0);
  leaf(W / 2, H - len * 1.35, (rnd() - 0.5) * 0.3);
  const mk = woodyMask('vine-pinnate|' + genus, cv);                   // 03d-woody.js
  sp = Object.assign(mk, { w: W / len, h: H / len, leaves: 3, cluster: true, leafCover: mk.cover });
  _VINE_SPRAYS.set(genus, sp);
  return sp;
}

function vineReadFor(p) {
  return !STYLISED && p && p.plant_type === 'vine' && !!_VINE_READ[p.leaf_data_source]
    && !!p.leaf_shape && (p.leaf_size_cm || 0) > 0;
}

// The vine's leafy shoots along `paths` (22-vines.js), as one mesh. Pushes
// where its flowers may go onto `anchors` (above `floorY`).
function buildVineSprays(p, paths, rng, floorY, anchors, month) {
  const per = p.leaf_arrangement === 'opposite' ? 2 : 1;
  const cut = vineLeafletSpray(p) || _wdSpray(p.leaf_shape, per), sp = cut;   // 03d-woody.js
  const L = Math.max(0.01, (p.leaf_size_cm || 6) / 100);
  const soft = (p.foliage_type || '') === 'herbaceous';
  const w = sp.w * L, h = sp.h * L, gap = h * (soft ? VINE_SOFT_GAP : VINE_SHOOT_GAP);
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
        if (cards++ % (soft ? 2 : 4) === 0 && !run && at[1] >= floorY) {   // as many flowers on fewer shoots
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
