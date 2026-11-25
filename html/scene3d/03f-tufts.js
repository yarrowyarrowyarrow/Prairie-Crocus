// Part of the Prairie Crocus 3D viewer. Loaded as an ordered CLASSIC
// script by the bootstrap in scene3d.html — it shares the global scope
// with its siblings (THREE and friends are globals set by the
// bootstrap). Do not add ES `import`/`export` here.
//
// Design principle P5 — see docs/DESIGN_PHILOSOPHY.md
//
// A grass, sedge or rush drawn from its own blades and seed head (V3.51, F268).
//
// Every graminoid was the same baked tuft of wide dark straps under a small
// pale billboard, so the region's fifty grasses, sedges, rushes and grass-like
// water plants were one plant, and the review of their photographs scored
// them 3 of 10. Where the blades and head were read (src/grass_habit.py writes
// a `drawn` block with body `tuft`), this builds the plant in metres:
//
//   blades   its length and width, held upright, arching, drooping or flat on
//            the ground, from one crown (`bunch`) or spread over the ground in
//            separate shoots (`sod`); a leafless rush or bulrush has none and
//            its stems are its body;
//   stems    the flowering stems counted (`stems`), as tall as the plant;
//   heads    by form, at the recorded length and width, as many a stem as
//            read, held erect, nodding, hanging or from the stem's side.
//
// Three meshes a species, one material: the blades (and a rush's stems) in
// the plant's colour; the flowering stems in the plant's colour, shown only
// while the heads are; the heads in their own colour, ripening to straw and
// held on the dry stems through the winter unless they are shed (cotton,
// burs, a sweet flag's spike).
//
// Stated estimates, nothing recording them: how many blades a tuft draws for
// its budget (TUFT_BUDGET), how far a fine blade is widened so a tussock
// reads as a mass and not as hairs (TUFT_MIN_BLADE_M), how thick a stem is
// for its height (STEM_PIPE), and the angles in BLADE_HOLD.

const TUFT_FORMS = ['bunch', 'sod'];
const HEAD_FORMS = ['turkey_foot', 'open_panicle', 'contracted_spike', 'nodding_raceme',
                    'one_sided_raceme', 'bristly', 'sedge_cluster', 'rush_umbel',
                    'cattail_spike', 'cotton', 'bur', 'spadix'];
const TUFT_BUDGET = [0, 4000, 8000];       // triangles a plant: Balanced, Lifelike
// Elevation from level (radians) a blade leaves the crown at, low to high,
// and how far it bends over along its length.
const BLADE_HOLD = { upright:  { rise: [1.15, 1.5], droop: 0.35 },
                     arching:  { rise: [0.9, 1.35], droop: 1.35 },
                     drooping: { rise: [0.75, 1.2], droop: 2.1 },
                     flat:     { rise: [0.08, 0.3], droop: 0.25 } };
const TUFT_MIN_BLADE_M = 0.008;            // a blade is drawn at least this wide
const TUFT_BLADE_GAIN_MAX = 4;             // ...but never past this many times its width
const STEM_PIPE = [0.0016, 0.0042];        // a stem's radius per metre of height: leafy, leafless
const SHOOT_BLADES = 4;                    // blades a shoot of a sod carries
const STEM_LEAVES = [0.15, 0.3, 0.45];  // where up a tall grass's stem its leaves leave it
// A tall grass's leafy shoots that do not flower, a share of its flowering
// stems, standing to VEG_TALL of its height: what gives a bluejoint or a
// manna grass its leafy mass above a short basal tuft.
const VEG_SHOOTS = 1.5, VEG_TALL = 0.55;
// Heads drawn up from where they start, whose top is the plant's top.
const TIP_HEADS = { contracted_spike: 1, cattail_spike: 1, bristly: 1, one_sided_raceme: 1,
                    open_panicle: 1, nodding_raceme: 1, turkey_foot: 1, sedge_cluster: 1 };
const HEAD_STRAW = new THREE.Color('#c8b488');

// ── geometry ────────────────────────────────────────────────────────────────

// A tube along `pts` with `radii` (one a point) and `sides` faces.
function _tfTube(B, pts, radii, sides, shade) {
  const base = B.pos.length / 3, n = pts.length;
  for (let i = 0; i < n; i++) {
    const d = _lbUnit(_lbAdd(pts[Math.min(n - 1, i + 1)], pts[Math.max(0, i - 1)], -1));
    const u = _lbUnit(_lbCross(d, Math.abs(d[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0]));
    const v = _lbCross(d, u), r = radii[i];
    for (let k = 0; k < sides; k++) {
      const a = k * Math.PI * 2 / sides, cs = Math.cos(a) * r, sn = Math.sin(a) * r;
      B.pos.push(pts[i][0] + u[0] * cs + v[0] * sn, pts[i][1] + u[1] * cs + v[1] * sn,
                 pts[i][2] + u[2] * cs + v[2] * sn);
      B.col.push(shade, shade, shade);
    }
  }
  for (let i = 0; i < n - 1; i++) {
    for (let k = 0; k < sides; k++) {
      const a = base + i * sides + k, b = base + i * sides + (k + 1) % sides;
      B.idx.push(a, b, a + sides, b, b + sides, a + sides);
    }
  }
}

// A spikelet: two crossed diamonds from `at` along `D`, `len` long, `wid` wide.
function _tfSpikelet(B, at, D, len, wid, shade) {
  const S1 = _lbUnit(_lbCross(D, Math.abs(D[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0]));
  const S2 = _lbCross(D, S1);
  for (const S of [S1, S2]) {
    const b = B.pos.length / 3, m = _lbAdd(at, D, len * 0.45), t = _lbAdd(at, D, len);
    B.pos.push(at[0], at[1], at[2], m[0] - S[0] * wid / 2, m[1] - S[1] * wid / 2,
               m[2] - S[2] * wid / 2, m[0] + S[0] * wid / 2, m[1] + S[1] * wid / 2,
               m[2] + S[2] * wid / 2, t[0], t[1], t[2]);
    for (let i = 0; i < 12; i++) B.col.push(shade);
    B.idx.push(b, b + 1, b + 2, b + 1, b + 3, b + 2);
  }
}

// A thin flat ribbon from `A` to `C`, `w` wide: a panicle's branch, an awn.
function _tfThread(B, A, C, w, shade) {
  const D = _lbUnit(_lbAdd(C, A, -1));
  const S = _lbUnit(_lbCross(D, Math.abs(D[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0]));
  const b = B.pos.length / 3;
  B.pos.push(A[0] - S[0] * w / 2, A[1] - S[1] * w / 2, A[2] - S[2] * w / 2,
             A[0] + S[0] * w / 2, A[1] + S[1] * w / 2, A[2] + S[2] * w / 2,
             C[0] - S[0] * w / 4, C[1] - S[1] * w / 4, C[2] - S[2] * w / 4,
             C[0] + S[0] * w / 4, C[1] + S[1] * w / 4, C[2] + S[2] * w / 4);
  for (let i = 0; i < 12; i++) B.col.push(shade);
  B.idx.push(b, b + 1, b + 2, b + 1, b + 3, b + 2);
}

// A ball of radius `r`: an icosahedron (an octahedron when `small`), its
// points pushed out where `spiky`.
let _TF_ICO = null, _TF_OCT = null;
function _tfBall(B, c, r, shade, spiky, rng, small) {
  if (!_TF_ICO) {
    _TF_ICO = new THREE.IcosahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
    _TF_OCT = new THREE.OctahedronGeometry(1, 0).toNonIndexed().attributes.position.array;
  }
  const b = B.pos.length / 3, P = small ? _TF_OCT : _TF_ICO;
  for (let i = 0; i < P.length; i += 3) {
    const k = r * (spiky ? 0.75 + 0.5 * rng() : 0.9 + 0.2 * rng());
    B.pos.push(c[0] + P[i] * k, c[1] + P[i + 1] * k, c[2] + P[i + 2] * k);
    B.col.push(shade, shade, shade);
  }
  for (let i = 0; i < P.length / 3; i++) B.idx.push(b + i);
}

// A cylinder with rounded ends, `len` along `D` from `at`, radius `r`.
function _tfCylinder(B, at, D, len, r, sides, shade) {
  const pts = [], radii = [], prof = [0.15, 0.7, 1, 1, 0.7, 0.1];
  prof.forEach((k, i) => {
    pts.push(_lbAdd(at, D, len * i / (prof.length - 1)));
    radii.push(r * k);
  });
  _tfTube(B, pts, radii, sides, shade);
}

// Turn a direction toward the ground by `a` radians (toward -y).
function _tfBend(D, a) {
  const flat = _lbUnit([D[0] || 1e-3, 0, D[2] || 1e-3]);
  const el = Math.asin(Math.max(-1, Math.min(1, D[1]))) - a;
  return _lbUnit([flat[0] * Math.cos(el), Math.sin(el), flat[2] * Math.cos(el)]);
}

// A random direction `off` radians off `D`.
function _tfOff(D, off, rng) {
  const S1 = _lbUnit(_lbCross(D, Math.abs(D[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0]));
  const S2 = _lbCross(D, S1), a = rng() * Math.PI * 2;
  return _lbUnit(_lbAdd(_lbAdd(D, S1, Math.cos(a) * Math.tan(off)), S2, Math.sin(a) * Math.tan(off)));
}

// ── the heads ───────────────────────────────────────────────────────────────

// One stem's heads at `at`, pointing `D` (the stem's tip direction), `q`
// triangles allowed. `out` is the horizontal direction the stem leans.
function _tfHead(B, d, at, D, out, q, rng) {
  const L = d.head_m, W = Math.max(0.002, d.head_w), sh = () => 0.85 + 0.3 * rng();
  const n = Math.max(1, d.heads), f = d.head;
  if (f === 'contracted_spike') {
    const k = Math.max(6, Math.min(40, Math.round(q / 4), Math.round(L / Math.max(0.003, W * 0.35))));
    const len = Math.max(0.004, Math.min(W * 1.4, L / k * 2.6));
    for (let i = 0; i < k; i++) {
      const p = _lbAdd(at, D, L * (i / k) * 0.92), side = i % 2 ? 1 : -1;
      const sp = _lbUnit(_lbAdd(D, out, side * 0.32));
      _tfSpikelet(B, _lbAdd(p, out, side * W * 0.12), sp, len, Math.max(0.0025, W * 0.45), sh());
    }
  } else if (f === 'open_panicle' || f === 'nodding_raceme' || f === 'turkey_foot') {
    const nod = d.attitude === 'nodding' || f === 'nodding_raceme';
    const nodes = Math.max(4, Math.min(12, Math.round(q / 40)));
    const per = f === 'nodding_raceme' ? 2 : 3;
    const big = f === 'nodding_raceme';
    const spk = big ? Math.max(0.008, Math.min(0.03, W * 0.22)) : Math.max(0.005, L * 0.035);
    const tips = Math.max(1, Math.min(6, Math.floor(q / nodes / per / 6)));
    _tfThread(B, at, _lbAdd(at, D, L), 0.0012, sh());
    for (let j = 0; j < nodes; j++) {
      const t = j / nodes, p = _lbAdd(at, D, L * t);
      for (let b = 0; b < per; b++) {
        const az = rng() * Math.PI * 2;
        const side = _lbUnit([Math.cos(az), 0, Math.sin(az)]);
        const reach = (W / 2) * (1 - t * 0.75) * (0.6 + 0.5 * rng());
        let dir = _lbUnit(_lbAdd(D, side, 1.4));
        if (nod) dir = _tfBend(dir, 0.6 + 0.5 * rng());
        const end = _lbAdd(p, dir, reach);
        _tfThread(B, p, end, 0.002, sh());
        for (let s = 0; s < tips; s++) {
          const u = 0.45 + 0.55 * (s + 1) / tips, sp = _lbAdd(p, dir, reach * u);
          const hang = nod ? _tfBend(_tfOff(dir, 0.4, rng), 0.9) : _tfOff(dir, 0.35, rng);
          _tfSpikelet(B, sp, hang, spk, spk * (big ? 0.45 : 0.4), sh());
        }
      }
    }
  } else if (f === 'one_sided_raceme') {
    for (let c = 0; c < n; c++) {
      const az = rng() * Math.PI * 2, side = [Math.cos(az), 0, Math.sin(az)];
      const base = _lbAdd(at, D, -c * L * 0.5);
      const ax = _lbUnit(_lbAdd(_lbAdd(D, side, 2.4), [0, -1, 0], 0.15));
      const teeth = Math.max(8, Math.min(26, Math.round(q / n / 4)));
      _tfThread(B, base, _lbAdd(base, ax, L), 0.0012, sh());
      for (let i = 0; i < teeth; i++) {
        const p = _lbAdd(base, ax, L * (0.08 + 0.9 * i / teeth));
        _tfSpikelet(B, p, _lbUnit(_lbAdd(_tfBend(ax, 1.3), ax, 0.25)), W * 0.7, W * 0.25, sh());
      }
    }
  } else if (f === 'bristly') {
    const k = Math.max(4, Math.min(10, Math.round(q / 8)));
    for (let i = 0; i < k; i++) {
      const p = _lbAdd(at, D, L * 0.25 * i / k);
      const dir = d.attitude === 'nodding' ? _tfBend(_tfOff(D, 0.3, rng), 0.5 + rng())
                                           : _tfOff(D, 0.12, rng);
      const seed = Math.max(0.006, W * 0.5);
      _tfSpikelet(B, p, dir, seed, seed * 0.3, sh());
      // The awn: thread-thin and as long as the head, bent once.
      const a1 = _lbAdd(p, dir, seed + L * 0.45);
      const bend = _tfBend(_tfOff(dir, 0.5, rng), 0.3 + 0.5 * rng());
      _tfThread(B, _lbAdd(p, dir, seed), a1, 0.0012, sh());
      _tfThread(B, a1, _lbAdd(a1, bend, L * 0.45), 0.001, sh());
    }
  } else if (f === 'sedge_cluster') {
    const sides = q > 200 ? 6 : q > 90 ? 5 : 4;
    for (let c = 0; c < n; c++) {
      const az = rng() * Math.PI * 2, side = [Math.cos(az), 0, Math.sin(az)];
      const p = _lbAdd(at, D, -c * L * 1.1);
      let dir = D;
      if (d.attitude === 'hanging') dir = _lbUnit(_lbAdd([0, -1, 0], side, 0.35 + 0.3 * rng()));
      else if (d.attitude === 'nodding') dir = _tfBend(_lbUnit(_lbAdd(D, side, 0.6)), 1.1);
      else if (c) dir = _lbUnit(_lbAdd(D, side, 0.25));
      const start = d.attitude === 'hanging' ? _lbAdd(p, side, W * 0.6) : _lbAdd(p, side, c ? W * 0.6 : 0);
      if (d.attitude === 'hanging') _tfThread(B, p, start, 0.0012, sh());
      _tfCylinder(B, start, dir, L, W / 2, sides, sh());
    }
    if (n >= 2) _tfCylinder(B, _lbAdd(at, D, L * 0.1), D, L * 0.7, W * 0.14, 4, sh() * 0.7);
  } else if (f === 'rush_umbel' || f === 'cotton' || f === 'bur') {
    const ball = f === 'rush_umbel' ? Math.max(0.003, L / 2) : W / 2;
    const small = f === 'rush_umbel' && q < 160;
    const each = (small ? 8 : 20) + (f === 'bur' ? 0 : 2);
    // As many as read, as far as the allowance goes: a spray of a dozen
    // flowers on each of twenty-five stems is drawn as fewer, larger ones.
    const k = Math.max(1, Math.min(n, Math.floor(q / each)));
    const grow = Math.sqrt(n / k);
    for (let c = 0; c < k; c++) {
      const ray = _tfOff(D, f === 'rush_umbel' ? 0.9 : 0.6, rng);
      let p = _lbAdd(at, ray, (f === 'rush_umbel' ? W / 2 : L * 0.4) * (0.25 + 0.75 * rng()));
      if (f === 'cotton') p = _lbAdd(p, [0, -1, 0], ball * (0.8 + rng()));
      if (f === 'bur') p = _lbAdd(at, D, -c * W * 1.6);
      if (f !== 'bur') _tfThread(B, at, p, 0.001, sh());
      _tfBall(B, p, ball * grow, sh(), f !== 'cotton', rng, small);
    }
  } else if (f === 'cattail_spike') {
    _tfCylinder(B, at, D, L, W / 2, 8, sh());
    _tfCylinder(B, _lbAdd(at, D, L * 1.04), D, L * 0.6, W * 0.13, 4, sh() * 1.1);
  } else if (f === 'spadix') {
    _tfCylinder(B, at, D, L, W / 2, 7, sh());
  }
}

// ── the plant ───────────────────────────────────────────────────────────────

function _tfPlan(d, budget) {
  const leafless = d.blades === 'none';
  const stems = Math.max(1, d.stems);
  const stemTris = leafless ? 12 : 18;
  const headShare = budget * 0.38;
  const q = Math.max(16, headShare / stems);
  const bladeTris = 6;
  const blades = leafless ? 0
    : Math.max(24, Math.min(Math.floor(budget * 0.45 / bladeTris),
                            Math.round(80 + 700 * d.mature_w)));
  return { leafless, stems: Math.min(stems, Math.floor(budget * 0.25 / stemTris)) || 1,
           q, blades, gain: leafless ? 1 : Math.min(TUFT_BLADE_GAIN_MAX,
             Math.max(1, TUFT_MIN_BLADE_M / Math.max(1e-4, d.blade_w))) };
}

// Where one shoot or stem stands: in a crown for a bunch, over the whole
// ground for a sod.
function _tfSpot(d, rng) {
  const R = d.mature_w / 2 * (d.form === 'sod' ? 0.95 : 0.22);
  const r = R * Math.sqrt(rng()), a = rng() * Math.PI * 2;
  return [Math.cos(a) * r, 0, Math.sin(a) * r];
}

function _tfBlades(B, d, P, rng) {
  const hold = BLADE_HOLD[d.blades] || BLADE_HOLD.arching;
  const W = d.blade_w * P.gain;
  const crowns = d.form === 'sod' ? Math.ceil(P.blades / SHOOT_BLADES) : 1;
  const spots = Array.from({ length: crowns }, () => _tfSpot(d, rng));
  for (let i = 0; i < P.blades; i++) {
    const c = d.form === 'sod' ? spots[i % crowns]
                               : _tfSpot(d, rng);
    const az = rng() * Math.PI * 2;
    const flat = [Math.cos(az), 0, Math.sin(az)];
    const out = d.form === 'sod' ? 0.5 : Math.hypot(c[0], c[2]) / Math.max(1e-3, d.mature_w * 0.11);
    const el = hold.rise[1] - (hold.rise[1] - hold.rise[0]) * Math.min(1, out * 0.5 + rng() * 0.6);
    const T = [flat[0] * Math.cos(el), Math.sin(el), flat[2] * Math.cos(el)];
    const S = _lbUnit([-flat[2], 0, flat[0]]);
    const L = d.blade_m * (0.55 + 0.5 * rng());
    _lbBlade(B, c, T, S, L, W * (0.8 + 0.4 * rng()), 'linear', 3,
             hold.droop * (0.7 + 0.6 * rng()), 0.72 + 0.36 * rng());
  }
}

// The flowering stems into `S` (the body, for a leafless plant), their heads
// into `H`, and a grass's leaves up its stem into `Bl`: a tall grass carries
// most of its leaf on the stem, not at the ground.
function _tfStems(S, H, Bl, d, P, rng) {
  const pipe = STEM_PIPE[P.leafless ? 1 : 0];
  for (let i = 0; i < P.stems; i++) {
    const c = _tfSpot(d, rng);
    const az = Math.atan2(c[2], c[0]) + (rng() - 0.5) * 1.2;
    const out = [Math.cos(az), 0, Math.sin(az)];
    const tall = d.mature_h * (0.82 + 0.18 * rng());
    const lean = tall * (0.05 + 0.12 * rng()) * (d.form === 'sod' ? 0.5 : 1);
    const nod = d.attitude === 'nodding' && d.head !== 'sedge_cluster';
    const pts = [];
    for (let k = 0; k <= 5; k++) {
      const t = k / 5;
      let p = [c[0] + out[0] * lean * t * t, tall * t, c[2] + out[2] * lean * t * t];
      if (nod && t > 0.7) {
        const u = (t - 0.7) / 0.3;
        p = _lbAdd(_lbAdd(p, out, tall * 0.1 * u * u), [0, -1, 0], tall * 0.08 * u * u);
      }
      pts.push(p);
    }
    const r = Math.max(0.0008, Math.min(0.012, pipe * d.mature_h));
    if (Bl && d.mature_h > d.blade_m * 1.6) {
      const hold = BLADE_HOLD[d.blades] || BLADE_HOLD.arching;
      for (const t of STEM_LEAVES) {
        const at = pts[Math.round(t * 5)], az = rng() * Math.PI * 2;
        const el = Math.min(1.2, hold.rise[0] + 0.1);
        const T = [Math.cos(az) * Math.cos(el), Math.sin(el), Math.sin(az) * Math.cos(el)];
        _lbBlade(Bl, at, T, _lbUnit([-Math.sin(az), 0, Math.cos(az)]),
                 d.blade_m * (0.6 + 0.3 * rng()), d.blade_w * P.gain, 'linear', 3,
                 hold.droop * 0.9, 0.8 + 0.3 * rng());
      }
    }
    _tfTube(S, pts, pts.map((_, k) => r * (1 - 0.6 * k / 5)), 3, 0.85 + 0.2 * rng());
    // Where the head goes and which way.
    let at = pts[5], D = _lbUnit(_lbAdd(pts[5], pts[4], -1));
    if (d.attitude === 'side' || d.head === 'spadix') {
      const f = d.head === 'spadix' ? 0.6 : 0.8, j = Math.round(f * 5);
      at = pts[j];
      D = d.head === 'spadix' ? _lbUnit(_lbAdd([0, 1, 0], out, 1.1))
                              : _lbUnit(_lbAdd([0, 0.4, 0], out, 1));
    } else if (d.attitude !== 'hanging' && TIP_HEADS[d.head]) {
      // The head is the stem's top length, inside the recorded height; the
      // stem stops under it.
      at = _lbAdd(pts[5], D, -Math.min(d.head_m, tall * 0.4));
    }
    _tfHead(H, d, at, D, out, P.q, rng);
  }
}

function tuftKeyFor(p) {
  const d = p && p.drawn;
  if (STYLISED || !d || d.body !== 'tuft' || TUFT_FORMS.indexOf(d.form) < 0
      || HEAD_FORMS.indexOf(d.head) < 0) return null;
  return ['tuft', d.form, d.mature_h, d.mature_w, d.stems, d.blade_m, d.blade_w, d.blades,
          d.head, d.head_m, d.head_w, d.heads, d.attitude].join('|');
}

function _tfGeo(B, s) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(B.pos.map(x => x * s), 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(B.col, 3));
  if (B.idx.length) g.setIndex(B.idx);
  g.computeVertexNormals();
  return g;
}

// The leafy shoots that do not flower, into the body.
function _tfVegetative(B, d, P, rng) {
  if (P.leafless || d.mature_h < d.blade_m * 2.2) return;
  const hold = BLADE_HOLD[d.blades] || BLADE_HOLD.arching;
  const n = Math.round(P.stems * VEG_SHOOTS);
  for (let i = 0; i < n; i++) {
    const c = _tfSpot(d, rng), az = rng() * Math.PI * 2;
    const tall = d.mature_h * VEG_TALL * (0.6 + 0.4 * rng());
    const lean = [Math.cos(az) * tall * 0.12, 0, Math.sin(az) * tall * 0.12];
    const top = _lbAdd(_lbAdd(c, [0, tall, 0], 1), lean, 1);
    _tfTube(B, [c, _lbAdd(c, _lbAdd([0, tall * 0.5, 0], lean, 0.3), 1), top],
            [0.0015, 0.0012, 0.0008], 3, 0.9);
    for (let k = 0; k < 3; k++) {
      const at = _lbAdd(c, _lbAdd(_lbAdd(top, c, -1), [0, 0, 0], 1), 0.35 + 0.3 * k);
      const a2 = az + (k - 1) * 1.1 + (rng() - 0.5) * 0.6;
      const el = Math.min(1.25, hold.rise[0] + 0.15 * rng());
      const T = [Math.cos(a2) * Math.cos(el), Math.sin(el), Math.sin(a2) * Math.cos(el)];
      _lbBlade(B, at, T, _lbUnit([-Math.sin(a2), 0, Math.cos(a2)]),
               d.blade_m * (0.7 + 0.35 * rng()), d.blade_w * P.gain, 'linear', 3,
               hold.droop, 0.78 + 0.3 * rng());
    }
  }
}

// The body, stems and heads for the plants sharing a key, in the unit frame
// (base at 0, the plant's height 1), `v` one of its random builds.
function buildTuftGeo(p, v) {
  const d = p.drawn;
  const P = _tfPlan(d, TUFT_BUDGET[Math.max(1, Math.min(2, QUALITY))]);
  const rng = mulberry32(hashPid((p.genus || '') + (p.species || '') + d.form) + 197 * v);
  const body = _lbNew(), stems = _lbNew(), heads = _lbNew();
  if (!P.leafless) { _tfBlades(body, d, P, rng); _tfVegetative(body, d, P, rng); }
  _tfStems(P.leafless ? body : stems, heads, P.leafless ? null : body, d, P, rng);
  const s = 1 / Math.max(1e-3, d.mature_h);
  const out = { body: _tfGeo(body, s), stems: _tfGeo(stems, s), heads: _tfGeo(heads, s) };
  // As wide as the plant is recorded to spread, so it is placed at one scale.
  out.body.userData.unitHalfWidth = Math.max(1e-3, d.mature_w / 2 / Math.max(1e-3, d.mature_h));
  out.body.userData.tuft = {
    plan: P, blades: P.leafless ? 0 : body.idx.length / 3,
    stems: (P.leafless ? body : stems).idx.length / 3, heads: heads.idx.length / 3,
    triangles: (body.idx.length + stems.idx.length + heads.idx.length) / 3,
  };
  return out;
}

const TUFT_CACHE = new Map();
function getTuftArch(p, v) {
  const key = tuftKeyFor(p) + '|' + v + '|q' + QUALITY;
  if (!TUFT_CACHE.has(key)) TUFT_CACHE.set(key, buildTuftGeo(p, v));
  return TUFT_CACHE.get(key);
}

// Whether the heads stand this month, and their colour.
function tuftHeads(p, month) {
  const d = p.drawn;
  const m = month || 7;
  let on = m >= d.head_from && (d.holds || m <= d.ripe);
  // Last year's heads on the dry stems (01d-season.js says when they are).
  if (!on && d.holds && m < d.head_from) on = diedBack(p, month);
  if (!on) return null;
  const c = new THREE.Color(d.head_color);
  if (d.head === 'cotton') return c;
  const fresh = m >= d.head_from && m <= d.ripe - 2;
  const k = fresh ? 0 : (m >= d.head_from && m <= d.ripe ? 0.45 : 0.8);
  return fadeColor(c.lerp(HEAD_STRAW, k), p.opacity);
}

function buildTuftLayer(list, month, year, terrain) {
  if (!list || !list.length) return;
  const VARIANTS = 2, buckets = {};
  for (const p of list) {
    const v = hashPid(p.plant_id) % VARIANTS;
    const k = tuftKeyFor(p) + '|' + v;
    (buckets[k] = buckets[k] || { v, items: [] }).items.push(p);
  }
  for (const key in buckets) {
    const { v, items } = buckets[key];
    const arch = getTuftArch(items[0], v);
    const places = items.map(p => spreadPlacements(p, year));
    const total = places.reduce((s, pl) => s + pl.length, 0);
    const meshes = ['body', 'stems', 'heads'].map(part =>
      arch[part].attributes.position.count ? instancedMesh(arch[part], total, MATS.blade) : null);
    const names = new Array(total), ids = new Array(total);
    let idx = 0;
    items.forEach((p, ii) => {
      const c = unitXZ(arch.body, Math.max(0.1, p.canopy_m));
      const h = bodyHeightOf(p), rotY0 = (indHash(p) % 628) / 100;
      const col = bodyColor(p, month), hcol = tuftHeads(p, month);
      places[ii].forEach((pl, k) => {
        const m = pl.mul, x = p.x + pl.dx, wy = p.y + pl.dz;
        const rotY = rotY0 + (k ? pl.dx : 0), gy = terrainHeightAt(x, wy, terrain);
        meshes.forEach((mesh, j) => {
          if (!mesh) return;
          const shown = j === 0 || hcol;
          const s = shown ? m : 0.0001;
          setInst2(mesh, idx, x, gy, -wy, c * s, h * s, c * s, rotY, j === 2 ? (hcol || col) : col);
        });
        names[idx] = p.common_name || '';
        ids[idx] = p.plant_id;
        idx++;
      });
    });
    for (const mesh of meshes) {
      if (!mesh) continue;
      mesh.userData.pick = names;
      mesh.userData.pickId = ids;
      mesh.userData.part = 'tuft';
      plantsGroup.add(mesh);
    }
  }
}

window.tuftKeyFor = tuftKeyFor;
window.buildTuftGeo = buildTuftGeo;
window.buildTuftLayer = buildTuftLayer;
window.tuftHeads = tuftHeads;
