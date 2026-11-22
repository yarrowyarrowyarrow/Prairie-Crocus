// Part of the Site & Pattern 3D viewer. Loaded as an ordered CLASSIC
// script by the bootstrap in scene3d.html — it shares the global scope
// with its siblings (THREE and friends are globals set by the
// bootstrap). Do not add ES `import`/`export` here.
//
// Design principle P5 — see docs/DESIGN_PHILOSOPHY.md
//
// A shrub or a tree in fruit, and through the winter (V3.63).
//
// Fruit is the strongest thing a shrub has to tell it from its neighbours from
// July to the snow: a snowberry's white berries, a highbush cranberry's red
// bunches, a currant's black strings, a saskatoon's purple clusters, a rose's
// hips. In the V3.62 re-read 24 of the 34 native shrubs had the `fruit` fault,
// and none kept its fruit into winter. The fruit was points (11-fruit.js) at
// the size of one fruit, behind the leaf cards a shrub drawn from its own
// numbers (03d-woody.js) is built of, so it was there and not seen.
//
// So a shrub with that body, or a tree with its own crown (03e-crowns.js),
// carries its fruit as cut-out cards on the ends of its outermost shoots, the
// way its flower clusters are carried since V3.49 (15c-woodybloom.js): a
// bunch of berries, a string of currants, a raceme of chokecherries, a cluster
// of hips. And where somebody read a winter photograph (`fruit_held_until`,
// schema v104), the fruit stays on the bare twigs after its season, as a
// snowberry's, a highbush cranberry's, a rose's and a hawthorn's do.
//
// What nothing records, and is a stated estimate here:
//  * how large a cluster is, by its form (WOODY_FRUIT_SIZE): one card stands
//    for a bunch, and is drawn larger than life by WOODY_FRUIT_GAIN on a shrub
//    (from its lowest to WOODY_FRUIT_GAIN_MAX at 3 m and over), and on a tree
//    by the blooms' own allowance (15b-anchors.js woodyBloomGain). At life
//    size a snowberry's bunch of 1 cm berries was a few grey pixels;
//  * how many bunches a plant in fruit carries (WOODY_FRUIT_PER_M2, over the
//    crown's surface), and the share still on it in winter (WOODY_FRUIT_HELD:
//    birds take the rest);
//  * how much darker coloured fruit is in winter (WOODY_FRUIT_WINTER): a hip
//    dries to a deeper red, a cranberry shrivels. Pale fruit (a snowberry's,
//    a silverberry's) stays as it is: darkened it was grey on the snow.
// A vine keeps its fruit on its own leaves (11-fruit.js, 22-vines.js).

// Bunches a square metre of the crown's surface, the most a plant carries, and
// the share still on its twigs in the months it holds them.
const WOODY_FRUIT_PER_M2 = 14;
const WOODY_FRUIT_MAX = 400;
const WOODY_FRUIT_HELD = 0.6;
const WOODY_FRUIT_GAIN = 1.4;
const WOODY_FRUIT_GAIN_MAX = 1.8;
const WOODY_FRUIT_WINTER = 0.8;
// A bunch's size at life size, in metres, by the species' fruit form.
const WOODY_FRUIT_SIZE = { berry: 0.035, pome: 0.05, hip: 0.055, strig: 0.07,
                           raceme: 0.1, cherry: 0.06, flat_cluster: 0.09,
                           aggregate: 0.025, strawberry: 0.025 };
// Bunches that hang from their twig rather than stand on it.
const _WF_HANGS = { strig: 1, raceme: 1, cherry: 1, berry: 1 };

// Whether `p` is in fruit in `month`: 'on' in its season, 'held' after it, up
// to and including `fruit_held_until`, across the new year where that runs on.
function fruitInSeason(p, month) {
  const fs = p.fruit_start || 0, fe = p.fruit_end || 0;
  if (!fs || !fe) return null;
  const within = (a, b) => (month - a + 12) % 12 <= (b - a + 12) % 12;
  if (within(fs, fe)) return 'on';
  const held = p.fruit_held_until || 0;
  if (held && within(fe % 12 + 1, held)) return 'held';
  return null;
}

// A shrub drawn from its own numbers, or a tree from its own crown.
function woodyFruitApplies(p) {
  return !!p.fruit_color && !!((window.woodyKeyFor && woodyKeyFor(p))
    || (window.crownKeyFor && crownKeyFor(p)));
}

// A bunch of the form, painted in the grey ramp the instance colour tints
// (11-fruit.js _fruitBall). The single-fruit forms there are one ball; on a
// shrub a card stands for a bunch, so these three are painted as bunches.
const _WF_TEX = new Map();
function _wfTexture(form) {
  let t = _WF_TEX.get(form);
  if (t) return t;
  if (form !== 'berry' && form !== 'pome' && form !== 'hip') {
    t = makeFruitTexture(form);                                  // 11-fruit.js
  } else {
    const s = 64, cv = document.createElement('canvas');
    cv.width = cv.height = s;
    const g = cv.getContext('2d');
    g.clearRect(0, 0, s, s);
    g.strokeStyle = '#4a4a4a'; g.lineCap = 'round'; g.lineWidth = s * 0.03;
    // [x, y, radius] of each fruit in the bunch, in card units; stalks to the top.
    const bunch = form === 'hip'
      ? [[0.36, 0.55, 0.17], [0.64, 0.6, 0.16], [0.5, 0.36, 0.15]]
      : form === 'pome'
        ? [[0.34, 0.42, 0.13], [0.6, 0.38, 0.13], [0.46, 0.62, 0.13], [0.7, 0.62, 0.12],
           [0.28, 0.68, 0.11]]
        : [[0.4, 0.4, 0.14], [0.62, 0.44, 0.14], [0.5, 0.64, 0.14], [0.3, 0.6, 0.12],
           [0.68, 0.66, 0.12]];
    for (const [x, y] of bunch) {
      g.beginPath(); g.moveTo(s * 0.5, s * 0.06); g.lineTo(x * s, y * s); g.stroke();
    }
    for (const [x, y, r] of bunch) {
      if (form === 'hip') {
        g.save(); g.translate(x * s, y * s); g.scale(1, 1.25);
        _fruitBall(g, 0, 0, r * s); g.restore();                // 11-fruit.js
      } else _fruitBall(g, x * s, y * s, r * s);
    }
    t = new THREE.CanvasTexture(cv);
    if (THREE.SRGBColorSpace) t.colorSpace = THREE.SRGBColorSpace;
  }
  // No smaller copies: averaged down, a bunch's edge falls under the cut and
  // the fruit is gone at a yard's distance, the fault the leaves had (V3.49).
  t.generateMipmaps = false;
  t.minFilter = THREE.LinearFilter;
  t.needsUpdate = true;
  _WF_TEX.set(form, t);
  return t;
}

const _WF_MATS = new Map();
function _wfMaterial(form) {
  const key = form + (sceneNight ? '|n' : '');
  let mat = _WF_MATS.get(key);
  if (mat) return mat;
  mat = new THREE.MeshStandardMaterial({ map: _wfTexture(form), alphaTest: 0.45,
                                         side: THREE.DoubleSide, roughness: 0.38,
                                         metalness: 0.0 });
  // A little of its own colour in the shade, as a petal has (15c-woodybloom.js).
  const lift = sceneNight ? '0.3' : '0.14';
  mat.onBeforeCompile = (shader) => {
    shader.fragmentShader = shader.fragmentShader.replace(
      '#include <emissivemap_fragment>',
      ['#include <emissivemap_fragment>',
       '#ifdef USE_INSTANCING_COLOR',
       '  totalEmissiveRadiance += vInstanceColor * ' + lift + ';',
       '#endif'].join('\n'));
  };
  mat.customProgramCacheKey = () => 'woodyfruit' + lift;
  _WF_MATS.set(key, mat);
  return mat;
}

// How many bunches `p` carries this month: by the surface of its crown.
function woodyFruitCards(p, held) {
  const r = Math.max(0.15, (p.canopy_m || 1) / 2), h = Math.max(0.2, bodyHeightOf(p));
  const n = Math.round(Math.PI * r * (r + 2 * h) * 0.7 * WOODY_FRUIT_PER_M2
                       * (held ? WOODY_FRUIT_HELD : 1));
  return Math.min(WOODY_FRUIT_MAX, Math.max(6, n));
}

function buildWoodyFruit(plants, month, terrain) {
  const groups = new Map(), _c = new THREE.Color(), _hsl = {};
  for (const p of plants) {
    const state = fruitInSeason(p, month);
    if (!state) continue;
    const form = WOODY_FRUIT_SIZE[p.fruit_form] ? p.fruit_form : 'berry';
    const anchors = bloomAnchors(p, WOODY_FRUIT_MAX, month);          // 15b-anchors.js
    if (!anchors || !anchors.length) continue;
    const tree = p.drawn && p.drawn.body === 'crown';
    const shrubGain = Math.min(WOODY_FRUIT_GAIN_MAX,
                               WOODY_FRUIT_GAIN + Math.max(0, (p.height_m || 1) - 1.5) / 4);
    const size = WOODY_FRUIT_SIZE[form] * (tree ? woodyBloomGain(p) : shrubGain);
    let gr = groups.get(form);
    if (!gr) { gr = []; groups.set(form, gr); }
    const seed = hashPid(p.plant_id || 1) >>> 0;
    let s = seed;
    const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
    _c.set(p.fruit_color);
    if (state === 'held' && _c.getHSL(_hsl).l < 0.6) _c.multiplyScalar(WOODY_FRUIT_WINTER);
    const n = Math.min(anchors.length, woodyFruitCards(p, state === 'held'));
    for (let k = 0; k < n; k++) {
      const q = anchors[(k * 11 + seed) % anchors.length];
      gr.push({ x: q.x, y: q.y, z: q.z, nx: q.nx, nz: q.nz, size: size * (0.8 + 0.4 * rnd()),
                spin: rnd() * 6.283, r: _c.r, g: _c.g, b: _c.b,
                name: p.common_name || '', id: p.plant_id });
    }
  }
  const m = new THREE.Matrix4(), v = new THREE.Vector3(), c = new THREE.Color();
  const X = new THREE.Vector3(), Y = new THREE.Vector3(), Z = new THREE.Vector3();
  for (const [form, items] of groups) {
    if (!items.length) continue;
    const mesh = instancedMesh(_wbCardGeo(false), items.length, _wfMaterial(form), false);
    const names = new Array(items.length), ids = new Array(items.length);
    const hangs = !!_WF_HANGS[form];
    items.forEach((it, i) => {
      // It faces out from the plant and a little up, turned a little about
      // that; a hanging bunch hangs from the shoot's end, the others sit on it.
      Z.set(it.nx + Math.cos(it.spin) * 0.3, 0.45, it.nz + Math.sin(it.spin) * 0.3).normalize();
      Y.set(0, hangs ? -1 : 1, 0);
      X.crossVectors(Y, Z).normalize();
      Z.crossVectors(X, Y).normalize();
      m.makeBasis(X, Y, Z);
      // Just out from the last leaves, or it is behind them.
      v.set(it.x + it.nx * it.size * 0.45, it.y + (hangs ? 0 : -it.size * 0.3),
            it.z + it.nz * it.size * 0.45);
      m.setPosition(v);
      m.scale(v.set(it.size, it.size, it.size));
      mesh.setMatrixAt(i, m);
      mesh.setColorAt(i, c.setRGB(it.r, it.g, it.b));
      names[i] = it.name; ids[i] = it.id;
    });
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    mesh.userData.pick = names;
    mesh.userData.pickId = ids;
    mesh.userData.part = 'fruit_card';
    mesh.userData.fruitForm = form;
    plantsGroup.add(mesh);
  }
}

window.fruitInSeason = fruitInSeason;
window.woodyFruitApplies = woodyFruitApplies;
window.buildWoodyFruit = buildWoodyFruit;
