// Part of the Site & Pattern 3D viewer. Loaded as an ordered CLASSIC
// script by the bootstrap in scene3d.html — it shares the global scope
// with its siblings (THREE and friends are globals set by the
// bootstrap). Do not add ES `import`/`export` here.
//
// Design principle P13 — see docs/DESIGN_PHILOSOPHY.md
//
// A shrub in flower (V3.49, F268).
//
// A saskatoon in May is white all over, and in the viewer it never was. Its
// flowers were built a floret at a time (15-florets.js), which costs about a
// hundred triangles a cluster, so a shrub carried at most ninety clusters, and
// at a shrub's distance a floret is two or three pixels. On the old stick
// figures those specks at least stood in the open; among the leaves of a shrub
// drawn from its own numbers (03d-woody.js) they were not seen at all.
//
// So a shrub with that body carries each flower cluster as one card, cut to
// the cluster's outline the way its leafy shoots are cut to their leaves': a
// column of flowers for a raceme, a cone for a panicle, a flat-topped dome for
// a corymb, one flower for a rose. A cluster is two or four triangles, so the
// shrub can carry as many as its crown has room for.
//
// What nothing records, and is a stated estimate here:
//  * how large a cluster is: woodyClusterSize, from the recorded flower width
//    and the flowers in a cluster (thirty 1.2 cm chokecherry flowers make a
//    10 cm raceme, sixty 6 mm dogwood flowers a 6 cm head, as they do);
//  * how many clusters a shrub in full flower carries (WOODY_BLOOM_PER_M2,
//    over the crown's surface);
//  * how much larger than life a cluster is drawn on a tall shrub, where a
//    cluster at its size is a few pixels: 15b-anchors.js woodyBloomGain, held
//    here to WOODY_BLOOM_GAIN_MAX.
// Fruit is not drawn here; it keeps its own layer (11-fruit.js).

// Flower clusters a square metre of the crown's surface, and the most a shrub
// may carry.
const WOODY_BLOOM_PER_M2 = 14;
const WOODY_BLOOM_MAX = 500;
const WOODY_BLOOM_GAIN_MAX = 1.5;
// The cut, as for the leaves (03d-woody.js WOODY_CUT).
const _WB_CUT = 0.4;
// Clusters that stand along an axis: drawn as two cards crossed on it, so they
// show from every side. The rest face out and up from the shoot.
const _WB_LONG = { raceme: 1, spike: 1, panicle: 1, whorl: 1 };

// A cluster's length (or width, for a flat-topped one), in metres at life
// size, from one flower's width `d` and the flowers `n` it holds.
// Where a cluster's size was read off photographs (head_length_cm and
// head_width_cm on a wildflower, V3.65), the card is drawn to it: the share of
// the card's width and height the mask's flowers fill (_wbMask), so the
// painted cluster, not the card, is the size read.
function _wbFill(arch, petals, sh) {
  if (arch === 'raceme' || (arch === 'spike' && petals >= 3))
    return [Math.min(1, 2 * Math.min(0.2, sh * 0.55) + sh), Math.min(1, 0.84 + sh)];
  if (arch === 'spike') return [Math.min(1, 2 * Math.max(0.1, Math.min(0.2, sh * 1.6))), 0.92];
  if (arch === 'panicle') return [Math.min(1, 0.77 + sh), Math.min(1, 0.9 + sh)];
  if (arch === 'corymb' || arch === 'umbel') return [Math.min(1, 0.88 + sh), Math.min(1, 0.52 + sh)];
  if (arch === 'whorl') return [Math.min(1, 0.7 + sh), Math.min(1, 0.66 + sh)];
  return [Math.min(1, 0.84 + sh), Math.min(1, 0.8 + sh)];
}
function _wbShare(share) { return Math.max(0.06, Math.min(1, Math.round(share * 16) / 16)); }

function woodyClusterSize(arch, d, n) {
  if (arch === 'solitary' || arch === 'head') return d;
  if (_WB_LONG[arch]) return Math.max(d * 2.2, d * Math.pow(n, 0.8) * 0.55);
  return Math.max(d * 1.6, d * Math.sqrt(n) * (arch === 'cyme' ? 1.3 : 1.15));
}

// A shrub with its own body (03d-woody.js), a tree with its own crown
// (03e-crowns.js) and a vine whose leaves were read (22b-vineleaves.js).
function woodyBloomApplies(p) {
  const own = (window.woodyKeyFor && woodyKeyFor(p)) || (window.crownKeyFor && crownKeyFor(p))
    || (window.vineReadFor && vineReadFor(p));
  return (!!own && !!p.flower_arch && !p.inflorescence_form)
    || !!(window.denseClusterApplies && denseClusterApplies(p));   // a wildflower's spike (V3.64)
}

// One flower painted white at (x, y), `r` its radius in pixels: its petals
// where they can be told apart, a dot where they cannot.
function _wbFlower(g, x, y, r, petals, spin) {
  if (r < 3.5 || petals < 3) { g.beginPath(); g.arc(x, y, Math.max(1.2, r), 0, 6.2832); g.fill(); return; }
  const n = Math.min(12, petals);
  for (let k = 0; k < n; k++) {
    g.save();
    g.translate(x, y); g.rotate(spin + k * 6.2832 / n);
    g.beginPath(); g.ellipse(0, -r * 0.55, Math.max(1, r * Math.min(0.42, 2.4 / n)), r * 0.5, 0, 0, 6.2832);
    g.fill();
    g.restore();
  }
  g.beginPath(); g.arc(x, y, r * 0.22, 0, 6.2832); g.fill();
}

// The mask for a cluster of `arch`: `share` is one flower's width against the
// cluster's, `petals` its petal count (0: a catkin's fuzz, drawn solid).
// {key, map, test, cover}, one for each cluster that differs, kept for the session.
const _WB_MASKS = new Map();
function _wbMask(arch, petals, share) {
  const sh = _wbShare(share);
  const key = arch + '|' + Math.min(12, petals) + '|' + sh;
  let mk = _WB_MASKS.get(key);
  if (mk) return mk;
  const W = 128, cv = document.createElement('canvas');
  cv.width = cv.height = W;
  const g = cv.getContext('2d', { willReadFrequently: true });
  g.fillStyle = '#000'; g.fillRect(0, 0, W, W);
  g.fillStyle = g.strokeStyle = '#fff';
  const rnd = _lcg(23 + key.length * 131 + key.charCodeAt(0) * 7);      // 01b-surface.js
  const r = sh * W / 2;
  const put = (x, y) => _wbFlower(g, x * W, (1 - y) * W, r * (0.85 + 0.3 * rnd()), petals, rnd() * 6.283);
  // Flowers enough to fill the outline `area` (a share of the card) about once:
  // up to 140, so a cluster of many tiny flowers (a Joe-Pye weed's dome) is
  // not half bare (70 until V3.65).
  const fill = (area) => Math.max(1, Math.min(140, Math.round(area * W * W / (3.2 * r * r))));
  switch (arch) {
    case 'solitary': case 'head':
      _wbFlower(g, W / 2, W / 2, W * 0.47, petals, rnd() * 6.283);
      break;
    case 'spike':
      if (petals < 3) {                               // a catkin: one soft column
        const hw = Math.max(0.1, Math.min(0.2, sh * 1.6));
        for (let i = 0; i < 260; i++) {
          const y = 0.04 + 0.92 * rnd(), x = 0.5 + (rnd() + rnd() - 1) * hw * Math.sin(Math.PI * Math.min(1, 0.15 + y));
          g.beginPath(); g.arc(x * W, (1 - y) * W, 2.6, 0, 6.2832); g.fill();
        }
        break;
      }                                               // else as a raceme, closer set
    // falls through
    case 'raceme': {
      // Open from the foot up: the flowers smaller and closer in toward the
      // buds at the top (V3.65), where a straight column read as a bar.
      const n = fill(arch === 'spike' ? 0.34 : 0.3), off = Math.min(0.2, sh * 0.55);
      for (let i = 0; i < n; i++) {
        const y = 0.08 + 0.84 * (i + 0.5) / n, t = 1 - 0.55 * Math.pow(y, 1.5);
        _wbFlower(g, (0.5 + (i % 2 ? off : -off) * (0.6 + 0.4 * rnd()) * t) * W, (1 - y) * W,
                  r * t * (0.85 + 0.3 * rnd()), petals, rnd() * 6.283);
      }
      break;
    }
    case 'panicle':                                   // a cone, widest low down
      for (let i = 0, n = fill(0.36); i < n; i++) {
        const y = 0.05 + 0.9 * Math.pow(rnd(), 1.4);
        put(0.5 + (rnd() - 0.5) * 0.8 * Math.pow(1 - y, 0.7), y);
      }
      break;
    case 'whorl':
      for (const y of [0.2, 0.5, 0.8])
        for (let i = 0, n = Math.max(3, fill(0.1)); i < n; i++) put(0.5 + (i / (n - 1) - 0.5) * 0.7, y + (rnd() - 0.5) * 0.06);
      break;
    case 'corymb': case 'umbel':                      // flat-topped: a band across the top
      for (let i = 0, n = fill(0.36); i < n; i++) {
        const a = rnd() * 6.283, q = Math.sqrt(rnd());
        put(0.5 + Math.cos(a) * q * 0.44, 0.64 + Math.sin(a) * q * 0.26);
      }
      break;
    default:                                          // a cyme: a loose round cluster
      for (let i = 0, n = fill(0.4); i < n; i++) {
        const a = rnd() * 6.283, q = Math.sqrt(rnd());
        put(0.5 + Math.cos(a) * q * 0.42, 0.52 + Math.sin(a) * q * 0.4);
      }
  }
  const px = g.getImageData(0, 0, W, W).data;
  let on = 0;
  for (let i = 0; i < px.length; i += 4) if (px[i] > 127) on++;
  const cover = Math.max(0.02, on / (W * W)), mips = [cv];
  for (let w = W >> 1; w >= 1; w >>= 1) mips.push(_wdMip(cv, w, w, cover));   // 03d-woody.js
  const map = new THREE.CanvasTexture(cv);
  map.mipmaps = mips; map.generateMipmaps = false;
  map.minFilter = THREE.LinearMipmapLinearFilter;
  map.needsUpdate = true;
  mk = { key, map, test: _WB_CUT, cover, mat: null };
  _WB_MASKS.set(key, mk);
  return mk;
}

// Lit as a petal is (15-florets.js floretMaterial): it takes the sun, lifts a
// little in its own colour, and lets light through.
function _wbMaterial(mk) {
  if (mk.mat && mk.night === !!sceneNight) return mk.mat;
  const mat = new THREE.MeshStandardMaterial({
    roughness: 0.62, metalness: 0.0, side: THREE.DoubleSide,
    alphaMap: mk.map, alphaTest: mk.test });
  const lift = sceneNight ? '0.45' : '0.22';
  mat.onBeforeCompile = (shader) => {
    shader.fragmentShader = shader.fragmentShader.replace(
      '#include <emissivemap_fragment>',
      ['#include <emissivemap_fragment>',
       '#ifdef USE_INSTANCING_COLOR',
       '  totalEmissiveRadiance += vInstanceColor * ' + lift + ';',
       '#endif'].join('\n'));
    if (typeof applyLeafLight === 'function') applyLeafLight(shader, PETAL_TRANSLUCENCY);
  };
  mat.customProgramCacheKey = () => 'woodybloom' + lift;
  mk.mat = mat; mk.night = !!sceneNight;
  return mat;
}

// A card a unit wide and a unit tall standing on the origin, or two crossed.
function _wbCardGeo(crossed) {
  const pos = [], uv = [], idx = [];
  for (let k = 0; k < (crossed ? 2 : 1); k++) {
    const b = pos.length / 3, cs = k ? 0 : 1, sn = k ? 1 : 0;
    for (const [u, v] of [[0, 0], [1, 0], [1, 1], [0, 1]]) {
      pos.push((u - 0.5) * cs, v, (u - 0.5) * sn); uv.push(u, v);
    }
    idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

// How many clusters a shrub in full flower carries this year: by the surface
// of its crown, and never fewer than were recorded.
function woodyBloomCards(p) {
  // A wildflower's clusters are the ones counted on it (15e-heads.js, V3.64).
  if (p.plant_type !== 'tree' && p.plant_type !== 'shrub' && p.plant_type !== 'vine') return Math.max(1, p.flowering_stems || 6);
  const r = Math.max(0.15, (p.canopy_m || 1) / 2), h = Math.max(0.2, bodyHeightOf(p));
  const byCrown = Math.round(Math.PI * r * (r + 2 * h) * 0.7 * WOODY_BLOOM_PER_M2);
  return Math.min(WOODY_BLOOM_MAX, Math.max(8, p.flowering_stems || 0, byCrown));
}

function buildWoodyBlooms(plants, month, terrain) {
  const groups = new Map(), back = [];
  const _c = new THREE.Color(), X = new THREE.Vector3(), Y = new THREE.Vector3(), Z = new THREE.Vector3();
  for (const p of plants) {
    const arch = FLORET_ARCHITECTURES.indexOf(p.flower_arch) >= 0 ? p.flower_arch : 'cyme';
    const petals = Math.max(0, Math.min(60, p.petal_count == null ? 5 : p.petal_count));
    const d = Math.max(0.15, Math.min(20, p.flower_diameter_cm || 2)) / 100;
    // A wildflower's spike is part of its height, never more than its share of it.
    const natural = Math.min(woodyClusterSize(arch, d, Math.max(1, p.florets_per_head || 1)),
      p.plant_type === 'tree' || p.plant_type === 'shrub' ? 9 : _REACH_OF_HEIGHT * Math.max(0.1, bodyHeightOf(p)));
    // A tree's clusters take the whole of 15b-anchors.js's allowance (2.5 at 6 m
    // and over): at life size a pin cherry's are pixels at a yard's distance.
    const tree = p.drawn && p.drawn.body === 'crown';
    const reach = natural * (tree ? woodyBloomGain(p) : Math.min(WOODY_BLOOM_GAIN_MAX, woodyBloomGain(p)));
    // A cluster whose length and width were read is drawn at them (V3.65),
    // never taller than its share of the plant.
    const L = p.plant_type === 'tree' || p.plant_type === 'shrub' ? 0
      : Math.min((p.head_length_cm || 0) / 100, _REACH_OF_HEIGHT * Math.max(0.1, bodyHeightOf(p)));
    const Wd = L ? Math.max(d, (p.head_width_cm || p.head_length_cm * 0.4) / 100) * L * 100 / p.head_length_cm : 0;
    const mk = _wbMask(arch, petals, d / (L ? Math.max(L, Wd) : natural));
    const fit = L ? _wbFill(arch, petals, _wbShare(d / Math.max(L, Wd))) : null;
    const anchors = bloomAnchors(p, WOODY_BLOOM_MAX, month);     // 15b-anchors.js
    // A wildflower whose body offers no tip to carry a card keeps its florets.
    if ((!anchors || !anchors.length) && window.denseClusterApplies && denseClusterApplies(p)) {
      back.push(p); continue;
    }
    if (!anchors || !anchors.length) continue;
    const key = mk.key + (_WB_LONG[arch] ? '|x' : '|o');
    let gr = groups.get(key);
    if (!gr) { gr = { mk, long: !!_WB_LONG[arch], items: [] }; groups.set(key, gr); }
    const seed = hashPid(p.plant_id || 1) >>> 0;
    let s = seed;
    const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
    _c.set(p.flower_color || '#ffffff');
    const n = Math.min(anchors.length, woodyBloomCards(p));
    for (let k = 0; k < n; k++) {
      const q = anchors[(k * 7 + seed) % anchors.length];
      // A stem tip says no way out (15b-anchors.js): out from the plant's middle.
      let nx = q.nx, nz = q.nz;
      if (!nx && !nz) { const a = Math.atan2(q.z + p.y, q.x - p.x) + (rnd() - 0.5) * 0.6; nx = Math.cos(a); nz = Math.sin(a); }
      const jit = 0.85 + 0.3 * rnd();
      const sx = fit ? Wd / fit[0] * jit : reach * jit, sy = fit ? L / fit[1] * jit : reach * jit * 1.1;
      gr.items.push({ x: q.x, y: q.y, z: q.z, nx, nz, size: sy / 1.1, sx, sy,
                      lean: (0.25 + 0.5 * rnd()) * (q.top ? 0.35 : 1), spin: rnd() * 6.283, r: _c.r, g: _c.g, b: _c.b,
                      // A poplar's, an aspen's or a birch's catkins hang (src/tree_habit.py).
                      hang: !!(p.drawn && p.drawn.catkins_hang) && petals < 3 && arch === 'spike',
                      out: tree ? 0.6 : 0.35, top: !!q.top,
                      name: p.common_name || '', id: p.plant_id });
    }
  }
  const m = new THREE.Matrix4(), v = new THREE.Vector3(), c = new THREE.Color();
  for (const gr of groups.values()) {
    const count = gr.items.length;
    if (!count) continue;
    const mesh = instancedMesh(_wbCardGeo(gr.long), count, _wbMaterial(gr.mk), false);
    const names = new Array(count), ids = new Array(count);
    gr.items.forEach((it, i) => {
      // The cluster stands on the shoot's end, leaning out from the shrub. One
      // card faces out and up; a crossed pair turns freely about its axis.
      Y.set(it.nx * it.lean, it.hang ? -1 : 1, it.nz * it.lean).normalize();
      if (gr.long) Z.set(Math.cos(it.spin), 0, Math.sin(it.spin));
      else Z.set(it.nx, 0.55, it.nz);
      X.crossVectors(Y, Z).normalize();
      Z.crossVectors(X, Y).normalize();
      m.makeBasis(X, Y, Z);
      // Its middle just past the shoot's end and a little out from the
      // shrub: a cluster stands proud of the last leaves, or it is not seen.
      v.set(it.x + it.nx * it.sx * it.out, it.y, it.z + it.nz * it.sx * it.out)
        .addScaledVector(Y, it.hang ? 0 : -it.sy * (it.top ? 0.955 : 0.27));   // a stem tip's spike ends there
      m.setPosition(v);
      m.scale(v.set(it.sx, it.sy, it.sx));
      mesh.setMatrixAt(i, m);
      mesh.setColorAt(i, c.setRGB(it.r, it.g, it.b));
      names[i] = it.name; ids[i] = it.id;
    });
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    mesh.userData.pick = names;
    mesh.userData.pickId = ids;
    mesh.userData.part = 'bloom_card';
    mesh.userData.clusterSizes = gr.items.map(it => it.size);
    plantsGroup.add(mesh);
  }
  if (back.length && window.buildFlorets) buildFlorets(back, month, terrain);
}

window.woodyBloomApplies = woodyBloomApplies;
window.woodyClusterSize = woodyClusterSize;
window.buildWoodyBlooms = buildWoodyBlooms;
