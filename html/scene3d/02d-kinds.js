// html/scene3d/02d-kinds.js — what each drawn kind adds at its outline (V3.73,
// F280's third increment).
//
// src/scene_kinds.py and src/scene_site.py decide; this chunk only draws, after
// 02c-site.js, whose surfaces, ribbons and boxes it uses (02c-site.js was at
// 507 of its 520 lines). V3.72 drew the Yard palette's kinds plainly; here:
//
//   * a look per chosen surface (the owner's Q6): flagstone, pavers, gravel,
//     wood chips, stepping stones, concrete, and a deck's boards. Texture,
//     never geometry (V2.29), each painted by sitePattern;
//   * a raised bed's soil is what stands in it stands on: siteRiseAt, which
//     terrainHeightAt (02-plants.js) adds to the bare ground, so plants,
//     flowers, fruit, animals and the walker are lifted and nothing else;
//   * a pond's shore, a rain garden's and a swale's floor, a rock garden's
//     rocks (buildKindExtras), and a board or chain link fence (buildFenceKind).
//
// Every size is one stated estimate in Python, and nothing is drawn that the
// design does not record (P9): no depth for water, no deck height.

Object.assign(SURFACE_LOOK, {
  flagstone:       { rank: 5, tile: 2.0, base: '#8a857a', hard: true, pattern: 'flags',
                     stones: ['#b9ab93', '#a79f8e', '#c4b8a0', '#9d9585'] },
  pavers:          { rank: 5, tile: 1.2, base: '#6f665e', hard: true, pattern: 'bond',
                     stones: ['#a3958a', '#978a7f', '#ab9e92'] },
  gravel:          { rank: 5, tile: 1.5, base: '#b9b2a4', hard: true,
                     blobs: [[24, 6, 14, ['168,160,148', '198,192,180'], 0.2, 0.3]],
                     specks: [1800, 'rgba(112,106,96,0.55)', 0.6, 1.5] },
  wood_chips:      { rank: 5, tile: 2.0, base: '#94714f', soft: true,
                     blobs: [[30, 6, 14, ['150,112,76', '178,140,100'], 0.2, 0.3]],
                     specks: [900, 'rgba(70,48,30,0.5)', 0.8, 2.2] },
  stepping_stones: { rank: 5, tile: 1.6, base: '#7c9c62', hard: true, pattern: 'stones',
                     stones: ['#aaa498', '#b8b0a1'],
                     blobs: [[30, 10, 24, ['134,164,104', '108,142,88'], 0.14, 0.22]] },
  concrete:        { rank: 6, tile: 3.0, base: '#c3c1ba', hard: true, joints: 2,
                     specks: [500, 'rgba(140,138,130,0.35)', 0.4, 1.0] },
  // Not a kind's own look: a pond's shore and a wet kind's floor.
  shore:           { rank: 5, tile: 1.0, base: '#968e82', hard: true, pattern: 'pebbles',
                     stones: ['#b3aa9c', '#857d72', '#a49b8d', '#c2baad'] },
  rain_floor:      { rank: 4, tile: 2.0, base: '#4a4834', soft: true,
                     blobs: [[26, 8, 20, ['70,72,48', '58,60,42'], 0.2, 0.3]],
                     specks: [300, 'rgba(110,130,80,0.45)', 0.5, 1.2] },
});

// ── the painters ────────────────────────────────────────────────────────────

function _pick(rng, list) { return list[Math.floor(rng() * list.length) % list.length]; }

// Draw `paint(ox, oy)` at each of the nine offsets, so a shape crossing the
// tile's edge wraps onto the opposite one.
function _wrapped(s, paint) {
  for (const ox of [-s, 0, s]) for (const oy of [-s, 0, s]) paint(ox, oy);
}

function sitePattern(g, look, s, rng) {
  const stones = look.stones || ['#999'];
  if (look.pattern === 'flags') {
    // Irregular stones: a jittered 4 x 4 lattice on a torus, each cell drawn
    // a little smaller than itself so the mortar shows between.
    const n = 4, c = s / n, k = [];
    for (let i = 0; i < n; i++) {
      k.push([]);
      for (let j = 0; j < n; j++)
        k[i].push([(rng() - 0.5) * c * 0.5, (rng() - 0.5) * c * 0.5]);
    }
    const at = (i, j) => [i * c + k[i % n][j % n][0], j * c + k[i % n][j % n][1]];
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
      const q = [at(i, j), at(i + 1, j), at(i + 1, j + 1), at(i, j + 1)];
      const mx = q.reduce((a, p) => a + p[0], 0) / 4, my = q.reduce((a, p) => a + p[1], 0) / 4;
      g.fillStyle = _pick(rng, stones);
      _wrapped(s, (ox, oy) => {
        g.beginPath();
        q.forEach(([x, y], v) => {
          const px = mx + (x - mx) * 0.9 + ox, py = my + (y - my) * 0.9 + oy;
          if (v) g.lineTo(px, py); else g.moveTo(px, py);
        });
        g.closePath(); g.fill();
      });
    }
  } else if (look.pattern === 'bond') {
    // Pavers in a running bond: each row half a paver along from the last.
    const rows = 8, per = 4, h = s / rows, w = s / per;
    for (let r = 0; r < rows; r++)
      for (let b = -1; b <= per; b++) {
        g.fillStyle = _pick(rng, stones);
        g.fillRect(b * w + (r % 2) * w / 2 + 1.5, r * h + 1.5, w - 3, h - 3);
      }
  } else if (look.pattern === 'boards') {
    // A deck's boards, one way, each a little different, with a butt joint.
    const n = 8, w = s / n;
    for (let b = 0; b < n; b++) {
      const v = Math.round((rng() - 0.5) * 24);
      g.fillStyle = 'rgba(' + (150 + v) + ',' + (118 + v) + ',' + (88 + v) + ',0.55)';
      g.fillRect(b * w + 1, 0, w - 2, s);
      g.fillStyle = 'rgba(70,52,36,0.8)';
      g.fillRect(b * w, 0, 1.5, s);
      g.fillRect(b * w, rng() * s, w, 1.5);
    }
  } else if (look.pattern === 'stones') {
    // Stepping stones in the lawn: two to a tile, offset.
    for (const [fx, fy] of [[0.27, 0.3], [0.73, 0.78]]) {
      g.fillStyle = _pick(rng, stones);
      g.beginPath();
      g.ellipse(fx * s, fy * s, s * 0.19, s * 0.14, rng() * Math.PI, 0, Math.PI * 2);
      g.fill();
      g.strokeStyle = 'rgba(80,78,70,0.6)'; g.lineWidth = 2; g.stroke();
    }
  } else if (look.pattern === 'pebbles') {
    for (let i = 0; i < 260; i++) {
      const x = rng() * s, y = rng() * s, r = 3 + rng() * 6;
      g.fillStyle = _pick(rng, stones);
      _wrapped(s, (ox, oy) => {
        g.beginPath(); g.arc(x + ox, y + oy, r, 0, Math.PI * 2); g.fill();
      });
    }
  }
}

// ── a raised bed's soil ─────────────────────────────────────────────────────

let SITE_RISES = [];

function setSiteRises(surfaces) {
  SITE_RISES = [];
  for (const s of surfaces || []) {
    if (!(s.lift_m > 0) || !s.ring || s.ring.length < 3) continue;
    const xs = s.ring.map(p => p[0]), ys = s.ring.map(p => p[1]);
    SITE_RISES.push({ ring: s.ring, lift: s.lift_m, x0: Math.min(...xs),
                      x1: Math.max(...xs), y0: Math.min(...ys), y1: Math.max(...ys) });
  }
}

function _inRing(x, y, ring) {
  let hit = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if ((yi > y) !== (yj > y) && x < xi + (y - yi) * (xj - xi) / (yj - yi)) hit = !hit;
  }
  return hit;
}

// How far a raised bed's soil stands over the ground at (x, y): 0 elsewhere.
function siteRiseAt(x, y) {
  let lift = 0;
  for (const r of SITE_RISES)
    if (x >= r.x0 && x <= r.x1 && y >= r.y0 && y <= r.y1 && _inRing(x, y, r.ring))
      lift = Math.max(lift, r.lift);
  return lift;
}

// ── shores, floors and rocks ────────────────────────────────────────────────

function _rock(x, y, r, terrain) {
  const rng = mulberry32((Math.round(x * 100) * 7919) ^ Math.round(y * 100));
  const geo = new THREE.DodecahedronGeometry(r, 0);
  geo.scale(1 + (rng() - 0.5) * 0.3, 0.55 + rng() * 0.2, 1 + (rng() - 0.5) * 0.3);
  geo.rotateY(rng() * Math.PI * 2);
  geo.translate(x, groundHeightAt(x, y, terrain) + r * 0.2, -y);   // bedded in
  return geo;
}

function buildKindExtras(group, sc) {
  const t = sc.terrain || null, m = sc.month, rocks = [];
  for (const s of sc.surfaces || []) {
    if (s.shore_m && s.ring && s.ring.length >= 3)
      for (const ring of _ribbonRings(s.ring.concat([s.ring[0]]), s.shore_m))
        _surfaceMesh(group, ring, 'shore', siteMat('shore', m), t, 'shore');
    if (s.floor)
      _surfaceMesh(group, s.floor, 'rain_floor', siteMat('rain_floor', m), t, 'floor');
    for (const [x, y, r] of s.rocks || []) rocks.push(_rock(x, y, r, t));
  }
  for (const ln of sc.lines || [])
    if (ln.kind === 'strip' && ln.floor_m)
      for (const ring of _ribbonRings(ln.points || [], ln.floor_m))
        _surfaceMesh(group, ring, 'rain_floor', siteMat('rain_floor', m), t, 'floor');
  if (!rocks.length) return;
  const mesh = new THREE.Mesh(rocks.length === 1 ? rocks[0] : mergeGeometries(rocks, false),
    new THREE.MeshStandardMaterial({ color: seasonSnow(m) ? 0xd8dbe0 : 0x6f6a62,
                                     roughness: 0.95, flatShading: true }));
  mesh.name = 'rocks';
  mesh.userData.count = rocks.length;
  mesh.castShadow = mesh.receiveShadow = true;
  group.add(mesh);
}

// ── fences by kind ──────────────────────────────────────────────────────────

const _FENCE_KIND = {
  board:      { post: 0.1, colour: 0x8c7356, panel: 0x977c5e, see: 1 },
  chain_link: { post: 0.05, colour: 0x9aa0a4, panel: 0x9aa0a4, see: 0.3 },
};

// A board fence (posts and a closed panel) or a chain link fence (thin posts,
// a top rail and a see-through mesh). A rail fence, and a fence of no kind,
// stay 02c-site.js's posts and three rails: returns false for those.
function buildFenceKind(group, ln, terrain, month) {
  const k = _FENCE_KIND[ln.fence_kind];
  const pts = ln.points || [];
  if (!k || pts.length < 2) return false;
  const h = ln.height_m || 1.2, frame = [], panel = [];
  const posts = _stops(pts, 2.4);
  for (const [x, y] of posts) {
    const p = new THREE.BoxGeometry(k.post, h + 0.05, k.post);
    p.translate(x, groundHeightAt(x, y, terrain) + (h + 0.05) / 2, -y);
    frame.push(p);
  }
  for (let i = 0; i + 1 < posts.length; i++) {
    const [ax, ay] = posts[i], [bx, by] = posts[i + 1];
    if (k.see < 1) frame.push(_boxBetween(ax, ay, bx, by, terrain, h - 0.04, 0.04, 0.04));
    panel.push(_boxBetween(ax, ay, bx, by, terrain, 0.04, h - 0.08, k.see < 1 ? 0.01 : 0.03));
  }
  const add = (geos, mat, name) => {
    const mesh = new THREE.Mesh(geos.length === 1 ? geos[0] : mergeGeometries(geos, false), mat);
    mesh.name = name;
    mesh.castShadow = k.see === 1;
    mesh.receiveShadow = true;
    group.add(mesh);
  };
  add(frame, new THREE.MeshStandardMaterial({ color: k.colour, roughness: 0.9 }),
      'fences:' + ln.fence_kind);
  add(panel, new THREE.MeshStandardMaterial({ color: k.panel, roughness: 0.9,
      transparent: k.see < 1, opacity: k.see, depthWrite: k.see === 1 }),
      'fence-panels:' + ln.fence_kind);
  return true;
}

// ── an existing hedge's green (V3.75) ───────────────────────────────────────
// By what it is (src/yard_kinds.py's HEDGE_KINDS): bare and twiggy with its
// leaves down, except the cedar, which keeps them.
const HEDGE_LOOK = {
  cotoneaster: { green: 0x3f6b3c }, caragana: { green: 0x7b9446 },
  lilac: { green: 0x5c8048 }, cedar: { green: 0x35593f, evergreen: true },
  other: { green: 0x58794a },
};
function hedgeColour(key, month) {
  const look = HEDGE_LOOK[key] || HEDGE_LOOK.other;
  return (!look.evergreen && seasonLeavesDown(month)) ? 0x6f6a55 : look.green;
}
